import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchmind.api.dependencies import get_db
from researchmind.models.enums import IngestionStage
from researchmind.models.schemas import IngestionJobRead
from researchmind.models import IngestionJob

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])


@router.get("/jobs", response_model=list[IngestionJobRead])
async def list_jobs(
    status: IngestionStage | None = None,
    document_version_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> Sequence[IngestionJob]:
    """List ingestion jobs."""
    query = select(IngestionJob)
    if status:
        query = query.where(IngestionJob.status == status)
    if document_version_id:
        query = query.where(IngestionJob.document_version_id == document_version_id)
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=IngestionJobRead)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> IngestionJob:
    """Get ingestion job detail."""
    job = await db.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/retry", response_model=IngestionJobRead)
async def retry_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> IngestionJob:
    """Retry a failed ingestion job."""
    job = await db.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status != IngestionStage.FAILED:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
        
    job.status = IngestionStage.QUEUED
    job.current_stage = IngestionStage.QUEUED
    job.retry_count += 1
    job.error_message = None
    job.error_stage = None
    
    await db.commit()
    await db.refresh(job)
    return job
