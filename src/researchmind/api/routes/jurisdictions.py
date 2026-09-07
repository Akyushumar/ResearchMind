import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchmind.api.dependencies import get_db
from researchmind.models.enums import JurisdictionLevel
from researchmind.models.schemas import JurisdictionCreate, JurisdictionRead
from researchmind.models import Jurisdiction

router = APIRouter(prefix="/api/v1/jurisdictions", tags=["jurisdictions"])


@router.post("/", response_model=JurisdictionRead)
async def create_jurisdiction(
    jur_in: JurisdictionCreate, db: AsyncSession = Depends(get_db)
) -> Jurisdiction:
    """Create a new jurisdiction."""
    if jur_in.parent_id:
        parent = await db.get(Jurisdiction, jur_in.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent jurisdiction not found")
            
    jur = Jurisdiction(**jur_in.model_dump())
    db.add(jur)
    await db.flush()
    await db.refresh(jur)
    return jur


@router.get("/", response_model=list[JurisdictionRead])
async def list_jurisdictions(
    level: JurisdictionLevel | None = None,
    parent_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> Sequence[Jurisdiction]:
    """List jurisdictions."""
    query = select(Jurisdiction)
    if level:
        query = query.where(Jurisdiction.level == level)
    if parent_id:
        query = query.where(Jurisdiction.parent_id == parent_id)
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{jurisdiction_id}", response_model=JurisdictionRead)
async def get_jurisdiction(
    jurisdiction_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Jurisdiction:
    """Get jurisdiction detail."""
    jur = await db.get(Jurisdiction, jurisdiction_id)
    if not jur:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")
    return jur


@router.get("/{jurisdiction_id}/hierarchy", response_model=list[JurisdictionRead])
async def get_jurisdiction_hierarchy(
    jurisdiction_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[Jurisdiction]:
    """Get full path to root jurisdiction."""
    jur = await db.get(Jurisdiction, jurisdiction_id)
    if not jur:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")
        
    path = []
    current = jur
    while current:
        path.insert(0, current)
        if current.parent_id:
            current = await db.get(Jurisdiction, current.parent_id)
        else:
            current = None
            
    return path
