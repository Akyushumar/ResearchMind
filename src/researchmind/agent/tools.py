import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from researchmind.retrieval.hybrid_search import HybridSearchService
from researchmind.retrieval.base import SearchMetadataFilter
from researchmind.models.clause import Clause
from researchmind.models.clause_relationship import ClauseRelationship
from researchmind.agent.models import AgentToolSchema, CanonicalEvidence

class AgentToolsRegistry:
    def __init__(self, hybrid_search: HybridSearchService, session: AsyncSession):
        self.hybrid_search = hybrid_search
        self.session = session
        
        # We store the runtime evidence map so the agent loop can fetch the canonical object
        # by the generated evidence_id
        self.evidence_cache: Dict[str, CanonicalEvidence] = {}

    def get_schemas(self) -> List[AgentToolSchema]:
        return [
            AgentToolSchema(
                name="search_regulations",
                description="Search the indexed regulatory corpus using a natural language query.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query."},
                        "limit": {"type": "integer", "description": "Max results to return."},
                        "jurisdiction_id": {"type": "string", "description": "UUID of jurisdiction to filter by. Optional."},
                        "document_version_id": {"type": "string", "description": "UUID of document version to filter by. Optional."}
                    },
                    "required": ["query"]
                }
            ),
            AgentToolSchema(
                name="get_clause",
                description="Retrieve the full details of a specific regulatory clause by its ID.",
                parameters={
                    "type": "object",
                    "properties": {
                        "clause_id": {"type": "string", "description": "The UUID of the clause to retrieve."}
                    },
                    "required": ["clause_id"]
                }
            ),
            AgentToolSchema(
                name="get_clause_children",
                description="Retrieve the immediate subordinate (child) clauses for a given clause ID.",
                parameters={
                    "type": "object",
                    "properties": {
                        "clause_id": {"type": "string", "description": "The UUID of the parent clause."}
                    },
                    "required": ["clause_id"]
                }
            ),
            AgentToolSchema(
                name="get_clause_relationships",
                description="Retrieve explicit cross-references or relationships for a given clause ID.",
                parameters={
                    "type": "object",
                    "properties": {
                        "clause_id": {"type": "string", "description": "The UUID of the clause."}
                    },
                    "required": ["clause_id"]
                }
            )
        ]

    async def execute(self, name: str, kwargs: Dict[str, Any]) -> Any:
        if name == "search_regulations":
            return await self.search_regulations(**kwargs)
        elif name == "get_clause":
            return await self.get_clause(**kwargs)
        elif name == "get_clause_children":
            return await self.get_clause_children(**kwargs)
        elif name == "get_clause_relationships":
            return await self.get_clause_relationships(**kwargs)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _record_evidence(self, ev: CanonicalEvidence) -> CanonicalEvidence:
        self.evidence_cache[ev.evidence_id] = ev
        return ev

    async def search_regulations(
        self, 
        query: str, 
        limit: int = 5, 
        jurisdiction_id: Optional[str] = None, 
        document_version_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        filters = SearchMetadataFilter(
            jurisdiction_ids=[uuid.UUID(jurisdiction_id)] if jurisdiction_id else None,
            document_version_ids=[uuid.UUID(document_version_id)] if document_version_id else None
        )
        
        # Guard limit
        limit = min(limit, 20)
        
        results = await self.hybrid_search.search(query=query, filters=filters, limit=limit)
        
        if not results:
            return []
            
        clause_ids = [r.clause_id for r in results if r.clause_id]
        clause_map = {}
        if clause_ids:
            q = select(Clause).where(Clause.id.in_(clause_ids))
            clause_res = await self.session.execute(q)
            for c in clause_res.scalars().all():
                clause_map[c.id] = c
        
        out = []
        for r in results:
            c_obj = clause_map.get(r.clause_id)
            ev = CanonicalEvidence(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                chunk_id=str(r.chunk_id),
                clause_id=str(r.clause_id),
                clause_number=c_obj.clause_number if c_obj else None,
                clause_path=r.clause_path,
                clause_type=c_obj.clause_type.value if c_obj else "unknown",
                source_text=r.content,
                page_number=c_obj.start_page if c_obj else None,
                document_version_id=str(r.document_version_id),
                retrieval_score=r.score,
                retrieval_method=r.retrieval_method
            )
            self._record_evidence(ev)
            # We return a dict for the LLM to digest easily, omitting verbose None fields if possible
            # Or just dict format
            out.append(ev.model_dump(exclude_none=True))
            
        return out

    async def get_clause(self, clause_id: str) -> Optional[Dict[str, Any]]:
        try:
            cid = uuid.UUID(clause_id)
        except ValueError:
            return {"error": "Invalid clause_id format"}
            
        q = select(Clause).where(Clause.id == cid)
        res = await self.session.execute(q)
        c = res.scalars().first()
        if not c:
            return {"error": "Clause not found"}
            
        ev = CanonicalEvidence(
            evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
            clause_id=str(c.id),
            clause_number=c.clause_number,
            clause_path=c.path,
            clause_type=c.clause_type.value,
            source_text=c.content,
            page_number=c.start_page,
            document_version_id=str(c.document_version_id),
            retrieval_method="tool:get_clause"
        )
        self._record_evidence(ev)
        
        out = ev.model_dump(exclude_none=True)
        if c.title:
            out["title"] = c.title
        return out

    async def get_clause_children(self, clause_id: str) -> List[Dict[str, Any]]:
        try:
            cid = uuid.UUID(clause_id)
        except ValueError:
            return [{"error": "Invalid clause_id format"}]
            
        q = select(Clause).where(Clause.parent_clause_id == cid).order_by(Clause.path)
        res = await self.session.execute(q)
        children = res.scalars().all()
        
        out = []
        for c in children:
            ev = CanonicalEvidence(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                clause_id=str(c.id),
                clause_number=c.clause_number,
                clause_path=c.path,
                clause_type=c.clause_type.value,
                source_text=c.content,
                page_number=c.start_page,
                document_version_id=str(c.document_version_id),
                retrieval_method="tool:get_clause_children"
            )
            self._record_evidence(ev)
            out.append(ev.model_dump(exclude_none=True))
        return out

    async def get_clause_relationships(self, clause_id: str) -> List[Dict[str, Any]]:
        try:
            cid = uuid.UUID(clause_id)
        except ValueError:
            return [{"error": "Invalid clause_id format"}]
            
        q = select(ClauseRelationship).options(selectinload(ClauseRelationship.target_clause)).where(ClauseRelationship.source_clause_id == cid)
        res = await self.session.execute(q)
        rels = res.scalars().all()
        
        out = []
        for r in rels:
            item = {
                "relationship_type": r.relationship_type.value,
                "extracted_text": r.extracted_text,
            }
            if r.target_clause:
                ev = CanonicalEvidence(
                    evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                    clause_id=str(r.target_clause.id),
                    clause_number=r.target_clause.clause_number,
                    clause_path=r.target_clause.path,
                    clause_type=r.target_clause.clause_type.value,
                    source_text=r.target_clause.content,
                    page_number=r.target_clause.start_page,
                    document_version_id=str(r.target_clause.document_version_id),
                    retrieval_method="tool:get_clause_relationships"
                )
                self._record_evidence(ev)
                item["target_evidence"] = ev.model_dump(exclude_none=True)
            out.append(item)
        return out
