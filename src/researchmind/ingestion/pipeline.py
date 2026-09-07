import asyncio
import time
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchmind.config.logging import get_logger
from researchmind.models import DocumentVersion, IngestionJob, Clause, ClauseRelationship, EvidenceChunk
from researchmind.models.enums import IngestionStage
from researchmind.ingestion.base import (
    ClauseChunker,
    ClauseExtractor,
    DocumentParser,
    DocumentStructure,
    EvidenceChunkData,
    ExtractedClause,
    ExtractedRelationship,
    ParsedDocument,
    RelationshipExtractor,
    StructureDetector,
)

logger = get_logger(__name__)


class IngestionPipeline:
    """Orchestrates the document ingestion pipeline with job tracking."""

    def __init__(
        self,
        parser: DocumentParser,
        structure_detector: StructureDetector,
        clause_extractor: ClauseExtractor,
        relationship_extractor: RelationshipExtractor,
        chunker: ClauseChunker,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.parser = parser
        self.structure_detector = structure_detector
        self.clause_extractor = clause_extractor
        self.relationship_extractor = relationship_extractor
        self.chunker = chunker
        self.session_factory = session_factory

    async def run(self, job_id: uuid.UUID) -> None:
        """Run the full ingestion pipeline for a given job."""
        async with self.session_factory() as session:
            job = await session.get(IngestionJob, job_id)
            if not job:
                logger.error("ingestion_job_not_found", job_id=str(job_id))
                return

            doc_version = await session.get(DocumentVersion, job.document_version_id)
            if not doc_version or not doc_version.file_path:
                await self._fail_job(session, job, "Document version or file path missing", IngestionStage.QUEUED)
                return

            file_path = Path(doc_version.file_path)

            try:
                # Stage 1: Parsing
                await self._update_job_stage(session, job_id, IngestionStage.PARSING)
                start_time = time.time()
                parsed = await self._run_parsing(file_path)
                logger.info("ingestion_stage_completed", job_id=str(job_id), stage=IngestionStage.PARSING.value, duration_ms=(time.time() - start_time) * 1000)

                # Stage 2: Structuring
                await self._update_job_stage(session, job_id, IngestionStage.STRUCTURING)
                start_time = time.time()
                structure = await self._run_structuring(parsed)
                logger.info("ingestion_stage_completed", job_id=str(job_id), stage=IngestionStage.STRUCTURING.value, duration_ms=(time.time() - start_time) * 1000)

                # Stage 3: Extracting Metadata / Clauses
                await self._update_job_stage(session, job_id, IngestionStage.EXTRACTING_METADATA)
                start_time = time.time()
                clauses = await self._run_clause_extraction(structure)
                clause_path_map = await self._persist_clauses(session, doc_version.id, clauses)
                logger.info("ingestion_stage_completed", job_id=str(job_id), stage=IngestionStage.EXTRACTING_METADATA.value, duration_ms=(time.time() - start_time) * 1000)

                # Stage 4: Relationships
                await self._update_job_stage(session, job_id, IngestionStage.EXTRACTING_RELATIONSHIPS)
                start_time = time.time()
                relationships = await self._run_relationship_extraction(clauses)
                await self._persist_relationships(session, relationships, clause_path_map)
                logger.info("ingestion_stage_completed", job_id=str(job_id), stage=IngestionStage.EXTRACTING_RELATIONSHIPS.value, duration_ms=(time.time() - start_time) * 1000)

                # Stage 5: Chunking
                await self._update_job_stage(session, job_id, IngestionStage.CHUNKING)
                start_time = time.time()
                chunks = await self._run_chunking(clauses)
                await self._persist_chunks(session, chunks, clause_path_map, doc_version.id)
                logger.info("ingestion_stage_completed", job_id=str(job_id), stage=IngestionStage.CHUNKING.value, duration_ms=(time.time() - start_time) * 1000)

                # Finalize
                await self._update_job_stage(session, job_id, IngestionStage.COMPLETED)

            except Exception as e:
                logger.error(
                    "ingestion_stage_failed",
                    job_id=str(job_id),
                    stage=job.current_stage.value,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                await self._fail_job(session, job, str(e), job.current_stage)

    async def _run_parsing(self, file_path: Path) -> ParsedDocument:
        return await self.parser.parse(file_path)

    async def _run_structuring(self, parsed: ParsedDocument) -> DocumentStructure:
        return await self.structure_detector.detect(parsed)

    async def _run_clause_extraction(self, structure: DocumentStructure) -> list[ExtractedClause]:
        return await self.clause_extractor.extract(structure)

    async def _run_relationship_extraction(self, clauses: list[ExtractedClause]) -> list[ExtractedRelationship]:
        return await self.relationship_extractor.extract(clauses)

    async def _run_chunking(self, clauses: list[ExtractedClause]) -> list[EvidenceChunkData]:
        return await self.chunker.chunk(clauses)

    async def _persist_clauses(self, session: AsyncSession, document_version_id: uuid.UUID, clauses: list[ExtractedClause]) -> dict[str, uuid.UUID]:
        """Persist extracted clauses to DB. Returns mapping of clause_path -> clause_id."""
        path_map = {}
        for ec in clauses:
            clause = Clause(
                document_version_id=document_version_id,
                clause_number=ec.clause_number,
                title=ec.title,
                content=ec.content,
                depth=ec.depth,
                path=ec.path,
                clause_type=ec.clause_type,
                is_mandatory=ec.is_mandatory,
                start_page=ec.start_page,
                end_page=ec.end_page,
            )
            session.add(clause)
            await session.flush()
            path_map[ec.path] = clause.id
            
            if ec.children:
                child_map = await self._persist_clauses(session, document_version_id, ec.children)
                path_map.update(child_map)
                
        await session.commit()
        return path_map

    async def _persist_relationships(self, session: AsyncSession, relationships: list[ExtractedRelationship], clause_path_map: dict[str, uuid.UUID]) -> None:
        for rel in relationships:
            source_id = clause_path_map.get(rel.source_clause_path)
            if not source_id:
                continue
                
            # target_id resolution is complex in practice, skipping full resolution here
            # assuming target_reference could be resolved to an ID
            
            # db_rel = ClauseRelationship(
            #     source_clause_id=source_id,
            #     # target_clause_id=...
            #     relationship_type=rel.relationship_type,
            #     context=rel.context,
            #     extracted_text=rel.target_reference,
            #     confidence=rel.confidence
            # )
            # session.add(db_rel)
        # await session.commit()
        pass

    async def _persist_chunks(self, session: AsyncSession, chunks: list[EvidenceChunkData], clause_path_map: dict[str, uuid.UUID], document_version_id: uuid.UUID) -> None:
        for c in chunks:
            clause_id = clause_path_map.get(c.clause_path)
            if not clause_id:
                continue
            chunk = EvidenceChunk(
                clause_id=clause_id,
                document_version_id=document_version_id,
                chunk_index=c.chunk_index,
                content=c.content,
                token_count=c.token_count,
                source_text=c.source_text,
                start_page=c.start_page,
                end_page=c.end_page,
                bbox_json=c.bbox,
            )
            session.add(chunk)
        await session.commit()

    async def _update_job_stage(self, session: AsyncSession, job_id: uuid.UUID, stage: IngestionStage, **kwargs) -> None:
        job = await session.get(IngestionJob, job_id)
        if job:
            job.current_stage = stage
            if stage == IngestionStage.COMPLETED:
                job.status = IngestionStage.COMPLETED
            elif stage == IngestionStage.FAILED:
                job.status = IngestionStage.FAILED
            for k, v in kwargs.items():
                setattr(job, k, v)
            await session.commit()

    async def _fail_job(self, session: AsyncSession, job: IngestionJob, error_msg: str, error_stage: IngestionStage) -> None:
        job.status = IngestionStage.FAILED
        job.error_message = error_msg
        job.error_stage = error_stage
        await session.commit()
