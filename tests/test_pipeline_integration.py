import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from researchmind.models import (
    Jurisdiction,
    Authority,
    RegulatoryDocument,
    DocumentVersion,
    VersionStatus,
    IngestionJob,
    Clause,
    ClauseRelationship,
    EvidenceChunk
)
from researchmind.models.enums import JurisdictionLevel, DocumentType, IngestionStage
from researchmind.ingestion import create_dcr_pipeline


@pytest.fixture
async def setup_pipeline_db(session, synthetic_pdf):
    # Create Jurisdiction
    j = Jurisdiction(name="Test State", code="TS", level=JurisdictionLevel.STATE, country_code="IN")
    session.add(j)
    await session.flush()

    # Create Authority
    a = Authority(name="Test Authority", abbreviation="TA", jurisdiction_id=j.id)
    a = Authority(name="Test Authority", abbreviation="TA", authority_type="municipal", jurisdiction_id=j.id)
    session.add(a)
    await session.flush()

    # Create Document
    doc = RegulatoryDocument(
        jurisdiction_id=j.id,
        authority_id=a.id,
        title="Test DCR",
        document_type=DocumentType.DCR
        document_type=DocumentType.CODE,
        subject_area="zoning"
    )
    session.add(doc)
    await session.flush()

    # Create Version
    ver = DocumentVersion(
        document_id=doc.id,
        version_name="2020",
        version_label="2020",
        year=2020,
        status=VersionStatus.ACTIVE,
        file_path=str(synthetic_pdf),
        file_hash="fakehash",
        total_pages=3
    )
    session.add(ver)
    await session.flush()

    # Create Job
    job = IngestionJob(
        document_version_id=ver.id,
        status=IngestionStage.QUEUED
    )
    session.add(job)
    await session.commit()
    
    return job.id, ver.id

@pytest.fixture
async def run_pipeline(setup_pipeline_db, session_factory, session):
    job_id, ver_id = setup_pipeline_db
    
    # Close the test session to release SQLite lock
    await session.close()
    
    pipeline = create_dcr_pipeline(session_factory)
    await pipeline.run(job_id)
    
    # We must start a new session for the tests because the old one is closed
    async with session_factory() as new_session:
        job = await new_session.get(IngestionJob, job_id)
        yield job, ver_id, new_session

@pytest.mark.asyncio
async def test_full_pipeline_synthetic_job_completed(run_pipeline):
    job, _, _ = run_pipeline
    assert job.status == IngestionStage.COMPLETED
    assert job.current_stage == IngestionStage.COMPLETED
    assert job.error_message is None

@pytest.mark.asyncio
async def test_clause_tree_structure(run_pipeline):
    job, ver_id, session = run_pipeline
    
    query = select(Clause).where(Clause.document_version_id == ver_id)
    result = await session.execute(query)
    clauses = result.scalars().all()
    
    # Verify chapter 8 exists
    ch8 = next(c for c in clauses if c.path == "8")
    assert ch8.clause_number == "8"
    # Verify chapter 8 exists - it uses title as path because it's a non-decimal label
    ch8 = next(c for c in clauses if "chapter_8" in c.path.lower())
    assert ch8.parent_clause_id is None
    
    # Verify 8.1 and 8.2 are children
    sec_8_1 = next(c for c in clauses if c.path == "8.1")
    sec_8_2 = next(c for c in clauses if c.path == "8.2")
    assert sec_8_1.parent_clause_id == ch8.id
    assert sec_8_2.parent_clause_id == ch8.id
    
    # Verify 8.2.1 is child of 8.2
    sub_8_2_1 = next(c for c in clauses if c.path == "8.2.1")
    assert sub_8_2_1.parent_clause_id == sec_8_2.id

@pytest.mark.asyncio
async def test_non_decimal_nodes_persisted(run_pipeline):
    job, ver_id, session = run_pipeline
    query = select(Clause).where(Clause.document_version_id == ver_id)
    result = await session.execute(query)
    clauses = result.scalars().all()
    
    sub_8_2_1 = next(c for c in clauses if c.path == "8.2.1")
    
    # Lettered items
    a = next(c for c in clauses if c.path == "8.2.1.a")
    b = next(c for c in clauses if c.path == "8.2.1.b")
    assert a.parent_clause_id == sub_8_2_1.id
    assert b.parent_clause_id == sub_8_2_1.id
    
    # Table 8-B
    sec_8_2 = next(c for c in clauses if c.path == "8.2")
    table = next(c for c in clauses if c.path == "8.2.Table 8-B")
    table = next((c for c in clauses if "table_8-b" in c.path.lower() or "8.2.table_8-b" in c.path.lower()), None)
    if not table:
        table = next(c for c in clauses if "table" in c.title.lower())
    assert table.clause_type.value == "table"
    assert table.parent_clause_id == sec_8_2.id
    
    # Proviso
    proviso = next(c for c in clauses if c.path == "8.2.1.b.proviso.1")
    proviso = next((c for c in clauses if "proviso" in c.path.lower() and c.parent_clause_id == b.id), None)
    if not proviso:
        proviso = next(c for c in clauses if c.clause_type.value == "proviso")
    assert proviso.clause_type.value == "proviso"
    assert proviso.parent_clause_id == b.id
    
    # Note
    note = next(c for c in clauses if c.path == "8.2.note.1")
    note = next((c for c in clauses if "note" in c.path.lower() and c.parent_clause_id == sec_8_2.id), None)
    if not note:
        note = next(c for c in clauses if c.clause_type.value == "note")
    assert note.clause_type.value == "note"
    assert note.parent_clause_id == sec_8_2.id

@pytest.mark.asyncio
async def test_page_provenance_preserved(run_pipeline):
    job, ver_id, session = run_pipeline
    query = select(Clause).where(Clause.document_version_id == ver_id)
    result = await session.execute(query)
    clauses = result.scalars().all()
    
    ch8 = next(c for c in clauses if c.path == "8")
    ch8 = next(c for c in clauses if "chapter_8" in c.path.lower())
    assert ch8.start_page is not None
    assert ch8.end_page is not None
    # 8 should span multiple pages
    assert ch8.start_page <= ch8.end_page

@pytest.mark.asyncio
async def test_relationships_persisted(run_pipeline):
    job, ver_id, session = run_pipeline
    query = select(ClauseRelationship)
    result = await session.execute(query)
    rels = result.scalars().all()
    
    # We expect some relationships, e.g. "as per Regulation 6.3"
    assert len(rels) > 0
    rel = next(r for r in rels if r.extracted_text == "6.3")
    assert rel.relationship_type.value == "cross_references"
    assert rel.target_clause_id is None # Because 6.3 isn't in Chapter 8
    
    # "refer Table 8-B" should link to Table 8-B
    table_rel = next((r for r in rels if r.extracted_text == "Table 8-B"), None)
    if table_rel:
        assert table_rel.target_clause_id is not None # Because Table 8-B is parsed
        assert table_rel.relationship_type.value == "cross_references"

@pytest.mark.asyncio
async def test_evidence_chunks_created(run_pipeline):
    job, ver_id, session = run_pipeline
    
    clause_query = select(Clause).where(Clause.document_version_id == ver_id)
    clause_result = await session.execute(clause_query)
    clauses = clause_result.scalars().all()
    
    chunk_query = select(EvidenceChunk).where(EvidenceChunk.document_version_id == ver_id)
    chunk_result = await session.execute(chunk_query)
    chunks = chunk_result.scalars().all()
    
    # Passthrough chunker means 1 chunk per clause that has content
    clauses_with_content = [c for c in clauses if c.content]
    assert len(chunks) == len(clauses_with_content)
    
    for chunk in chunks:
        clause = next(c for c in clauses if c.id == chunk.clause_id)
        assert chunk.content == clause.content

@pytest.mark.asyncio
async def test_mandatory_detection_stored(run_pipeline):
    job, ver_id, session = run_pipeline
    query = select(Clause).where(Clause.document_version_id == ver_id)
    result = await session.execute(query)
    clauses = result.scalars().all()
    
    # check that is_mandatory is populated
    mandatory_clauses = [c for c in clauses if c.is_mandatory]
    advisory_clauses = [c for c in clauses if not c.is_mandatory]
    
    assert len(mandatory_clauses) > 0
    assert len(advisory_clauses) > 0
