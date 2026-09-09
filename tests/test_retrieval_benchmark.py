import pytest
import yaml
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from researchmind.retrieval.hybrid_search import HybridSearchService
from researchmind.retrieval.lexical_retriever import LexicalRetriever
from researchmind.retrieval.semantic_retriever import SemanticRetriever
from researchmind.retrieval.embeddings.factory import get_embedding_provider
from researchmind.db.vector_store import VectorStore
from researchmind.config.settings import get_settings

BENCHMARK_FILE = Path(__file__).parent.parent / "data" / "benchmarks" / "retrieval" / "udcpr_ch8_questions.yaml"

@pytest.fixture
def benchmark_data():
    if not BENCHMARK_FILE.exists():
        pytest.skip(f"Benchmark file {BENCHMARK_FILE} not found")
    with open(BENCHMARK_FILE, "r") as f:
        return yaml.safe_load(f)

@pytest.mark.asyncio
@pytest.mark.skip(reason="Needs populated database with chunks and embeddings to run properly")
async def test_retrieval_benchmark(session: AsyncSession, benchmark_data: dict, vector_store: VectorStore):
    settings = get_settings()
    # Initialize providers
    lexical = LexicalRetriever(session)
    embedding_provider = get_embedding_provider(settings)
    semantic = SemanticRetriever(vector_store, embedding_provider, session)
    hybrid = HybridSearchService(lexical, semantic)
    
    queries = benchmark_data.get("queries", [])
    
    threshold = 0.0  # RRF score threshold placeholder
    
    for q in queries:
        results = await hybrid.search(q["query"], limit=5)
        
        # In a real run with data, we would assert:
        assert len(results) > 0, f"No results for query: {q['query']}"
        
        top_paths = [r.clause_path for r in results]
        assert q["expected_clause_path"] in top_paths, (
            f"Expected {q['expected_clause_path']} for query '{q['query']}', "
            f"got {top_paths}"
        )
        
        # We can also check RRF score threshold
        expected_res = next(r for r in results if r.clause_path == q["expected_clause_path"])
        assert expected_res.score > threshold, f"RRF score too low for {q['query']}"

