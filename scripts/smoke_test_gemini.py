import asyncio
from pathlib import Path

from researchmind.config.settings import get_settings
from researchmind.retrieval.embeddings.gemini_provider import GeminiEmbeddingProvider
from researchmind.db.vector_store import VectorStore
from qdrant_client.http.models import Distance

async def main():
    print("--- Running Gemini Smoke Test ---")
    settings = get_settings()
    
    # Initialize Provider
    provider = GeminiEmbeddingProvider(
        model=settings.embedding_model,
        dimension=settings.embedding_dimension,
        api_key=settings.gemini_api_key
    )
    
    # Fake one chunk
    test_text = "This is a smoke test clause about building regulations."
    
    print(f"Generating embedding for model: {provider.model_name} ...")
    embeddings = await provider.get_embeddings([test_text])
    vec = embeddings[0]
    
    print(f"Vector length: {len(vec)}")
    assert len(vec) == 3072, f"Expected 3072, got {len(vec)}"
    
    # Insert to Qdrant
    vector_store = VectorStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name="smoke_test_collection"
    )
    vector_store.ensure_collection(vector_size=3072, distance=Distance.COSINE)
    
    # Fake EvidenceChunk object
    class FakeChunk:
        def __init__(self):
            import uuid
            self.id = uuid.uuid4()
            self.clause_id = uuid.uuid4()
            self.document_version_id = uuid.uuid4()
            self.jurisdiction_id = uuid.uuid4()
            self.clause_path = "smoke.test.1"
            self.chunk_type = "clause"
            self.topic = "smoke test"
            self.content = test_text
            self.hierarchy_context = "Part 1 > Smoke Test"
            self.start_page = 1
            self.end_page = 1
            
    chunk = FakeChunk()
    
    print("Inserting to Qdrant...")
    vector_store.upsert_chunks([chunk], embeddings)
    
    print("Retrieving from Qdrant via semantic search...")
    # Semantic search
    query_embeddings = await provider.get_embeddings(["What are the building regulations?"])
    results = vector_store.search(query_embeddings[0], limit=1)
    
    print(f"Found {len(results)} results")
    assert len(results) == 1
    
    res = results[0]
    print(f"Score: {res.score}")
    print(f"Provenance clause_path: {res.payload.get('clause_path')}")
    assert res.payload.get("clause_path") == "smoke.test.1"
    
    print("Smoke test PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
