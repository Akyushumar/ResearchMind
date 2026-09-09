import hashlib
import uuid
from typing import Sequence

import pymupdf  # fitz
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchmind.api.dependencies import get_db, get_settings_dep
from researchmind.config.settings import Settings
from researchmind.models.enums import DocumentType, IngestionStage
from researchmind.models.schemas import (
    DocumentVersionCreate,
    DocumentVersionRead,
    IngestionJobRead,
    RegulatoryDocumentCreate,
    RegulatoryDocumentRead,
)
from researchmind.models import DocumentVersion, IngestionJob, RegulatoryDocument
from researchmind.ingestion import create_dcr_pipeline

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/", response_model=RegulatoryDocumentRead, status_code=201)
async def create_document(
    doc_in: RegulatoryDocumentCreate, db: AsyncSession = Depends(get_db)
) -> RegulatoryDocumentRead:
    """Create a new regulatory document."""
    doc = RegulatoryDocument(**doc_in.model_dump())
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


@router.get("/", response_model=list[RegulatoryDocumentRead])
async def list_documents(
    jurisdiction_id: uuid.UUID | None = None,
    authority_id: uuid.UUID | None = None,
    document_type: DocumentType | None = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> Sequence[RegulatoryDocument]:
    """List regulatory documents."""
    query = select(RegulatoryDocument)
    if jurisdiction_id:
        query = query.where(RegulatoryDocument.jurisdiction_id == jurisdiction_id)
    if authority_id:
        query = query.where(RegulatoryDocument.authority_id == authority_id)
    if document_type:
        query = query.where(RegulatoryDocument.document_type == document_type)
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{document_id}", response_model=RegulatoryDocumentRead)
async def get_document(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> RegulatoryDocument:
    """Get document detail with versions."""
    query = select(RegulatoryDocument).where(RegulatoryDocument.id == document_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post(
    "/{document_id}/versions/", response_model=DocumentVersionRead, status_code=201
)
async def create_document_version(
    document_id: uuid.UUID,
    version_in: DocumentVersionCreate,
    db: AsyncSession = Depends(get_db),
) -> DocumentVersion:
    """Create a document version."""
    query = select(RegulatoryDocument).where(RegulatoryDocument.id == document_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    version = DocumentVersion(
        document_id=document_id,
        **version_in.model_dump(exclude={"document_id"}),
    )
    db.add(version)
    await db.flush()
    await db.refresh(version)
    return version


@router.post("/{document_id}/versions/{version_id}/upload", response_model=IngestionJobRead)
async def upload_document_version_file(
    request: Request,
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> IngestionJob:
    """Upload file for a version and start ingestion job."""
    query = select(DocumentVersion).where(
        DocumentVersion.id == version_id, DocumentVersion.document_id == document_id
    )
    result = await db.execute(query)
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    # Save file
    file_dir = settings.upload_dir / str(document_id) / str(version_id)
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / file.filename
    
    content = await file.read()
    file_path.write_bytes(content)
    
    # Compute SHA-256
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Get page count
    try:
        with pymupdf.open(file_path) as pdf_doc:
            total_pages = pdf_doc.page_count
    except Exception:
        total_pages = 0
        
    version.file_path = str(file_path)
    version.file_hash = file_hash
    version.total_pages = total_pages
    
    # Create ingestion job
    job = IngestionJob(
        document_version_id=version_id,
        status=IngestionStage.QUEUED,
    )
    db.add(job)
    await db.flush()
    await db.commit()  # Ensure job is committed before background task accesses it
    await db.refresh(job)
    
    # Add background task
    pipeline = create_dcr_pipeline(request.app.state.session_factory)
    background_tasks.add_task(pipeline.run, job.id)
    
    return job


@router.get("/{document_id}/versions/{version_id}", response_model=DocumentVersionRead)
async def get_document_version(
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentVersion:
    """Get version detail."""
    query = select(DocumentVersion).where(
        DocumentVersion.id == version_id, DocumentVersion.document_id == document_id
    )
    result = await db.execute(query)
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version
