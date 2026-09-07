from datetime import date
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from researchmind.models import (
    Jurisdiction,
    Authority,
    RegulatoryDocument,
    DocumentVersion,
    Clause,
    ClauseRelationship,
    ApplicabilityRule,
    IngestionJob,
)
from researchmind.models.enums import (
    JurisdictionLevel,
    DocumentType,
    VersionStatus,
    ClauseType,
    RelationshipType,
    IngestionStage,
)

@pytest.fixture
async def jurisdiction_fixture(session: AsyncSession):
    j = Jurisdiction(name="India", code="IN", level=JurisdictionLevel.NATIONAL, country_code="IN")
    session.add(j)
    await session.commit()
    await session.refresh(j)
    return j

@pytest.fixture
async def authority_fixture(session: AsyncSession, jurisdiction_fixture):
    a = Authority(
        name="Bureau of Indian Standards",
        abbreviation="BIS",
        jurisdiction_id=jurisdiction_fixture.id,
        authority_type="standards_body",
    )
    session.add(a)
    await session.commit()
    await session.refresh(a)
    return a

@pytest.fixture
async def document_fixture(session: AsyncSession, authority_fixture, jurisdiction_fixture):
    doc = RegulatoryDocument(
        title="National Building Code",
        short_title="NBC",
        document_type=DocumentType.CODE,
        authority_id=authority_fixture.id,
        jurisdiction_id=jurisdiction_fixture.id,
        subject_area="building",
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc

@pytest.fixture
async def document_version_fixture(session: AsyncSession, document_fixture):
    ver = DocumentVersion(
        document_id=document_fixture.id,
        version_label="2016",
        year=2016,
        status=VersionStatus.ACTIVE,
    )
    session.add(ver)
    await session.commit()
    await session.refresh(ver)
    return ver

@pytest.fixture
async def clause_fixture(session: AsyncSession, document_version_fixture):
    clause = Clause(
        document_version_id=document_version_fixture.id,
        clause_number="1",
        title="General",
        content="General info",
        depth=0,
        path="1",
        clause_type=ClauseType.CLAUSE,
    )
    session.add(clause)
    await session.commit()
    await session.refresh(clause)
    return clause


@pytest.mark.asyncio
async def test_create_jurisdiction_hierarchy(session: AsyncSession):
    india = Jurisdiction(name="India", code="IN", level=JurisdictionLevel.NATIONAL, country_code="IN")
    session.add(india)
    await session.flush()
    
    wb = Jurisdiction(name="West Bengal", code="IN-WB", level=JurisdictionLevel.STATE, 
                      parent_id=india.id, country_code="IN", state_code="WB")
    session.add(wb)
    await session.flush()
    
    kgp = Jurisdiction(name="Kharagpur", code="IN-WB-KGP", level=JurisdictionLevel.MUNICIPAL,
                       parent_id=wb.id, country_code="IN", state_code="WB")
    session.add(kgp)
    await session.commit()
    
    assert kgp.parent_id == wb.id
    assert wb.parent_id == india.id


@pytest.mark.asyncio
async def test_create_document_with_version(session: AsyncSession, jurisdiction_fixture, authority_fixture):
    doc = RegulatoryDocument(
        title="Test Doc",
        short_title="TD",
        document_type=DocumentType.CODE,
        authority_id=authority_fixture.id,
        jurisdiction_id=jurisdiction_fixture.id,
        subject_area="test",
    )
    session.add(doc)
    await session.flush()
    
    ver = DocumentVersion(
        document_id=doc.id,
        version_label="v1",
        year=2024,
        status=VersionStatus.DRAFT,
    )
    session.add(ver)
    await session.commit()
    
    assert ver.document_id == doc.id


@pytest.mark.asyncio
async def test_create_clause_hierarchy(session: AsyncSession, document_version_fixture):
    part3 = Clause(
        document_version_id=document_version_fixture.id,
        clause_number="3",
        title="Development Control Rules",
        content="...",
        depth=0,
        path="3",
        clause_type=ClauseType.PART,
    )
    session.add(part3)
    await session.flush()
    
    section42 = Clause(
        document_version_id=document_version_fixture.id,
        clause_number="4.2",
        title="Setbacks",
        content="...",
        parent_clause_id=part3.id,
        depth=1,
        path="3.4.2",
        clause_type=ClauseType.SECTION,
    )
    session.add(section42)
    await session.commit()
    
    assert section42.parent_clause_id == part3.id
    assert section42.path == "3.4.2"


@pytest.mark.asyncio
async def test_create_clause_relationship(session: AsyncSession, document_version_fixture):
    c1 = Clause(
        document_version_id=document_version_fixture.id,
        clause_number="1",
        title="C1",
        content="...",
        depth=0,
        path="1",
        clause_type=ClauseType.CLAUSE,
    )
    c2 = Clause(
        document_version_id=document_version_fixture.id,
        clause_number="2",
        title="C2",
        content="...",
        depth=0,
        path="2",
        clause_type=ClauseType.CLAUSE,
    )
    session.add_all([c1, c2])
    await session.flush()
    
    rel = ClauseRelationship(
        source_clause_id=c1.id,
        target_clause_id=c2.id,
        relationship_type=RelationshipType.REFERENCES,
        context="test context",
        extracted_text="as per clause 2",
    )
    session.add(rel)
    await session.commit()
    
    assert rel.source_clause_id == c1.id
    assert rel.target_clause_id == c2.id


@pytest.mark.asyncio
async def test_create_applicability_rule(session: AsyncSession, clause_fixture, jurisdiction_fixture):
    rule = ApplicabilityRule(
        clause_id=clause_fixture.id,
        jurisdiction_id=jurisdiction_fixture.id,
        building_type="residential",
        height_max=15.0,
        effective_from=date(2016, 1, 1),
    )
    session.add(rule)
    await session.commit()
    
    assert rule.clause_id == clause_fixture.id
    assert rule.jurisdiction_id == jurisdiction_fixture.id


@pytest.mark.asyncio
async def test_create_ingestion_job(session: AsyncSession, document_version_fixture):
    job = IngestionJob(
        document_version_id=document_version_fixture.id,
        status=IngestionStage.QUEUED,
        current_stage=IngestionStage.QUEUED,
        parser_version="0.1.0",
    )
    session.add(job)
    await session.commit()
    
    assert job.document_version_id == document_version_fixture.id
