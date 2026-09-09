import asyncio
import json
import uuid
import time
from pathlib import Path

from researchmind.config.settings import get_settings
from researchmind.db.engine import create_engine
from researchmind.db.session import create_session_factory
from researchmind.db.vector_store import VectorStore
from researchmind.retrieval.embeddings.factory import get_embedding_provider
from researchmind.models.enums import DocumentType, JurisdictionLevel
from researchmind.models import RegulatoryDocument, DocumentVersion, Authority, Jurisdiction, EvidenceChunk
from researchmind.ingestion.pipeline import create_dcr_pipeline, IngestionJob, IngestionStage
from sqlalchemy import select

from qdrant_client.http.models import Distance

async def ensure_db_records(session):
    # Just grab or create some base records to attach the document to
    india = await session.scalar(select(Jurisdiction).where(Jurisdiction.code == "IN"))
    if not india:
        india = Jurisdiction(name="India", code="IN", level=JurisdictionLevel.NATIONAL, country_code="IN")
        session.add(india)
        await session.flush()
        
    bis = await session.scalar(select(Authority).where(Authority.abbreviation == "BIS"))
    if not bis:
        bis = Authority(
            name="Bureau of Indian Standards",
            abbreviation="BIS",
            jurisdiction_id=india.id,
            authority_type="Standardization Body"
        )
        session.add(bis)
        await session.flush()
        
    doc = await session.scalar(select(RegulatoryDocument).where(RegulatoryDocument.short_title == "UDCPR"))
    if not doc:
        doc = RegulatoryDocument(
            title="Unified Development Control and Promotion Regulations",
            short_title="UDCPR",
            document_type=DocumentType.CODE,
            authority_id=bis.id,
            jurisdiction_id=india.id,
            subject_area="building_regulation",
        )
        session.add(doc)
        await session.flush()
        
    return doc, india

async def main():
    print("--- Starting UDCPR Chapter 8 Ingestion ---")
    settings = get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    
    vector_store = VectorStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.qdrant_collection
    )
    
    # 1. Initialize Qdrant Collection with 3072 dimension
    vector_store.ensure_collection(vector_size=settings.embedding_dimension, distance=Distance.COSINE)
    
    # 2. Setup the Pipeline
    pipeline = create_dcr_pipeline(session_factory)
    
    # Check if PDF exists
    pdf_path = Path("data/corpus/udcpr_2020.pdf")
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        return
        
    # 3. Create Document Version and Job
    async with session_factory() as session:
        doc, jurisdiction = await ensure_db_records(session)
        
        doc_version = DocumentVersion(
            document_id=doc.id,
            version_label="2020",
            year=2020,
            status="ACTIVE",
            file_path=str(pdf_path),
        )
        session.add(doc_version)
        await session.flush()
        
        job = IngestionJob(
            document_version_id=doc_version.id,
            current_stage=IngestionStage.QUEUED
        )
        session.add(job)
        await session.commit()
        
        job_id = job.id
        doc_version_id = doc_version.id
        jurisdiction_id = jurisdiction.id

    # 4. Run the Pipeline
    print(f"Running pipeline for job {job_id}...")
    await pipeline.run(job_id)
    
    # 5. Fetch generated chunks from DB
    async with session_factory() as session:
        chunks = (await session.execute(
            select(EvidenceChunk).where(EvidenceChunk.document_version_id == doc_version_id)
        )).scalars().all()
        
    print(f"\nPipeline finished. Extracted {len(chunks)} chunks.")
    if len(chunks) == 0:
        print("No chunks generated. Exiting.")
        return
        
    # 6. Generate Embeddings and Upsert
    print("Initializing Embedding Provider...")
    provider = get_embedding_provider(settings)
    print(f"Using {provider.model_name} (dim: {provider.dimension})")
    
    # Update jurisdiction_id on chunks before upsert so vector store can pick it up
    for c in chunks:
        c.jurisdiction_id = jurisdiction_id

    # Batch embeddings to avoid API rate limits/timeouts
    print("Generating embeddings...")
    batch_size = 50
    all_embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c.content for c in batch]
        print(f"  Embedding batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch)} chunks)")
        emb = await provider.get_embeddings(texts)
        all_embeddings.extend(emb)
        # Small sleep just in case
        time.sleep(1)
        
    print(f"Generated {len(all_embeddings)} embeddings.")
    
    # Upsert to Qdrant
    print("Upserting to Qdrant...")
    vector_store.upsert_chunks(chunks, all_embeddings)
    
    # Update chunks in DB to indicate successful embedding
    async with session_factory() as session:
        for c in chunks:
            # We can re-fetch or just run an update
            pass
            
        from sqlalchemy import update
        await session.execute(
            update(EvidenceChunk)
            .where(EvidenceChunk.document_version_id == doc_version_id)
            .values(
                embedding_model=provider.model_name,
                embedding_dimension=provider.dimension,
                embedding_status='completed'
            )
        )
        await session.commit()
        
    # 7. Print Statistics
    async with session_factory() as session:
        from sqlalchemy import func
        from researchmind.models import Clause
        total_clauses = await session.scalar(select(func.count(Clause.id)).where(Clause.document_version_id == doc_version_id))
        total_chunks = await session.scalar(select(func.count(EvidenceChunk.id)).where(EvidenceChunk.document_version_id == doc_version_id))
        successful_emb = await session.scalar(select(func.count(EvidenceChunk.id)).where(EvidenceChunk.embedding_status == 'completed'))
        
    qdrant_points = vector_store.count()
    
    print("\n--- Ingestion Consistency Report ---")
    print(f"Number of clauses: {total_clauses}")
    print(f"Number of evidence chunks: {total_chunks}")
    print(f"Chunks with successful embeddings: {successful_emb}")
    print(f"Number of Qdrant points: {qdrant_points}")
    print(f"Embedding model: {provider.model_name}")
    print(f"Embedding dimension: {provider.dimension}")
    print(f"Failed embeddings: {total_chunks - successful_emb}")
    
    print("\nIngestion complete.")

if __name__ == "__main__":
    asyncio.run(main())
