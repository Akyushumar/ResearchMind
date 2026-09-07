import pytest
import tempfile
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
import fitz

from researchmind.models import IngestionJob, DocumentVersion, RegulatoryDocument, Jurisdiction, Authority
from researchmind.models.enums import IngestionStage, JurisdictionLevel, DocumentType, VersionStatus
from researchmind.ingestion.parsers.pdf_parser import PDFParser

@pytest.fixture
async def document_version_fixture(session: AsyncSession):
    j = Jurisdiction(name="India", code="IN", level=JurisdictionLevel.NATIONAL, country_code="IN")
    session.add(j)
    await session.flush()
    
    a = Authority(name="BIS", abbreviation="BIS", jurisdiction_id=j.id, authority_type="standards_body")
    session.add(a)
    await session.flush()
    
    doc = RegulatoryDocument(
        title="Test Doc",
        short_title="TD",
        document_type=DocumentType.CODE,
        authority_id=a.id,
        jurisdiction_id=j.id,
        subject_area="test",
    )
    session.add(doc)
    await session.flush()
    
    ver = DocumentVersion(
        document_id=doc.id,
        version_label="2024",
        year=2024,
        status=VersionStatus.DRAFT,
    )
    session.add(ver)
    await session.commit()
    await session.refresh(ver)
    return ver

@pytest.mark.asyncio
async def test_ingestion_job_creation(session: AsyncSession, document_version_fixture):
    job = IngestionJob(
        document_version_id=document_version_fixture.id,
        status=IngestionStage.QUEUED,
        current_stage=IngestionStage.QUEUED,
        parser_version="0.1.0",
    )
    session.add(job)
    await session.commit()
    assert job.status == IngestionStage.QUEUED

@pytest.mark.asyncio
async def test_ingestion_job_stage_transition(session: AsyncSession, document_version_fixture):
    job = IngestionJob(
        document_version_id=document_version_fixture.id,
        status=IngestionStage.QUEUED,
        current_stage=IngestionStage.QUEUED,
        parser_version="0.1.0",
    )
    session.add(job)
    await session.commit()
    
    job.current_stage = IngestionStage.PARSING
    await session.commit()
    assert job.current_stage == IngestionStage.PARSING

@pytest.mark.asyncio
async def test_ingestion_job_failure(session: AsyncSession, document_version_fixture):
    job = IngestionJob(
        document_version_id=document_version_fixture.id,
        status=IngestionStage.FAILED,
        current_stage=IngestionStage.PARSING,
        error_stage=IngestionStage.PARSING,
        error_message="Failed to parse PDF: corrupted file",
        parser_version="0.1.0",
    )
    session.add(job)
    await session.commit()
    assert job.status == IngestionStage.FAILED
    assert job.error_message == "Failed to parse PDF: corrupted file"

@pytest.mark.asyncio
async def test_ingestion_job_retry(session: AsyncSession, document_version_fixture):
    job = IngestionJob(
        document_version_id=document_version_fixture.id,
        status=IngestionStage.FAILED,
        current_stage=IngestionStage.PARSING,
        error_stage=IngestionStage.PARSING,
        error_message="Failed",
        parser_version="0.1.0",
        retry_count=0,
    )
    session.add(job)
    await session.commit()
    
    job.status = IngestionStage.QUEUED
    job.retry_count += 1
    job.error_message = None
    job.error_stage = None
    await session.commit()
    
    assert job.status == IngestionStage.QUEUED
    assert job.retry_count == 1
    assert job.error_message is None

@pytest.mark.asyncio
async def test_pdf_parser_basic():
    # Create a simple test PDF using pymupdf
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        temp_pdf = f.name
        
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Test clause 1.1\nThis is test content.", fontsize=12)
    doc.save(temp_pdf)
    doc.close()
    
    parser = PDFParser()
    parsed_doc = await parser.parse(Path(temp_pdf))
    
    assert parsed_doc.total_pages == 1
    assert len(parsed_doc.pages) == 1
    page1 = parsed_doc.pages[0]
    assert "Test clause 1.1" in page1.text
    assert len(page1.blocks) > 0
    
    # Cleanup
    Path(temp_pdf).unlink()
