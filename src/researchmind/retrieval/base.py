import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class SearchResult:
    chunk_id: uuid.UUID
    clause_id: uuid.UUID
    document_version_id: uuid.UUID
    clause_path: str
    content: str
    hierarchy_context: Optional[str]
    score: float
    retrieval_method: str  # e.g., 'lexical', 'semantic', 'hybrid'


@dataclass
class SearchMetadataFilter:
    document_version_ids: list[uuid.UUID] | None = None
    jurisdiction_ids: list[uuid.UUID] | None = None
    clause_types: list[str] | None = None


class BaseRetriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, filters: SearchMetadataFilter | None = None, limit: int = 10) -> list[SearchResult]:
        pass

