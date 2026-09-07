import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchmind.api.dependencies import get_db
from researchmind.models.schemas import ClauseRead, ClauseRelationshipRead
from researchmind.models import Clause, ClauseRelationship

router = APIRouter(prefix="/api/v1/clauses", tags=["clauses"])


@router.get("/{clause_id}", response_model=ClauseRead)
async def get_clause(clause_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Clause:
    """Get clause detail."""
    clause = await db.get(Clause, clause_id)
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    return clause


@router.get("/{clause_id}/children", response_model=list[ClauseRead])
async def get_clause_children(
    clause_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Sequence[Clause]:
    """Get child clauses."""
    query = (
        select(Clause)
        .where(Clause.parent_clause_id == clause_id)
        .order_by(Clause.clause_number)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{clause_id}/path", response_model=list[ClauseRead])
async def get_clause_path(
    clause_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[Clause]:
    """Get full path to root clause."""
    clause = await db.get(Clause, clause_id)
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
        
    path = []
    current = clause
    while current:
        path.insert(0, current)
        if current.parent_clause_id:
            current = await db.get(Clause, current.parent_clause_id)
        else:
            current = None
            
    return path


@router.get("/{clause_id}/relationships", response_model=dict[str, list[ClauseRelationshipRead]])
async def get_clause_relationships(
    clause_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> dict[str, list[ClauseRelationshipRead]]:
    """Get all relationships for a clause."""
    outgoing_query = select(ClauseRelationship).where(
        ClauseRelationship.source_clause_id == clause_id
    )
    incoming_query = select(ClauseRelationship).where(
        ClauseRelationship.target_clause_id == clause_id
    )
    
    outgoing_result = await db.execute(outgoing_query)
    incoming_result = await db.execute(incoming_query)
    
    return {
        "outgoing": list(outgoing_result.scalars().all()),
        "incoming": list(incoming_result.scalars().all()),
    }
