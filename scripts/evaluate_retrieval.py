import asyncio
import yaml
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from researchmind.db.session import create_session_factory
from researchmind.db.engine import create_engine
from researchmind.config.settings import get_settings
from researchmind.db.vector_store import VectorStore

from researchmind.retrieval.hybrid_search import HybridSearchService
from researchmind.retrieval.lexical_retriever import LexicalRetriever
from researchmind.retrieval.semantic_retriever import SemanticRetriever
from researchmind.retrieval.embeddings.factory import get_embedding_provider

BENCHMARK_FILE = Path(__file__).parent.parent / "data" / "benchmarks" / "retrieval" / "udcpr_ch8_questions.yaml"

def calculate_metrics(results, expected_path: str):
    found_ranks = []
    for idx, r in enumerate(results):
        if r.clause_path == expected_path:
            found_ranks.append(idx + 1)
            
    first_rank = found_ranks[0] if found_ranks else None
    
    return {
        "recall@1": 1 if first_rank and first_rank <= 1 else 0,
        "recall@3": 1 if first_rank and first_rank <= 3 else 0,
        "recall@5": 1 if first_rank and first_rank <= 5 else 0,
        "mrr": (1.0 / first_rank) if first_rank else 0.0,
    }

async def evaluate():
    settings = get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    
    vector_store = VectorStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.qdrant_collection,
    )
    
    with open(BENCHMARK_FILE, "r") as f:
        benchmark_data = yaml.safe_load(f)
        
    queries = benchmark_data.get("queries", [])
    
    strategies = ["lexical", "semantic", "hybrid"]
    
    print(f"Evaluating {len(queries)} queries...\n")
    
    async with session_factory() as session:
        lexical = LexicalRetriever(session)
        embedding_provider = get_embedding_provider(settings)
        semantic = SemanticRetriever(vector_store, embedding_provider, session)
        hybrid = HybridSearchService(lexical, semantic)
        
        results_json = {
            "metadata": {
                "version": "v0.3.0",
                "embedding_provider": settings.embedding_provider,
                "embedding_model": settings.embedding_model,
                "embedding_dimension": settings.embedding_dimension,
                "notes": "Ingested UDCPR Chapter 8 using StructureAwareChunker"
            },
            "strategies": {}
        }
        
        for strategy in strategies:
            total_r1 = 0
            total_r3 = 0
            total_r5 = 0
            total_mrr = 0.0
            
            for q in queries:
                results = await hybrid.search(q["query"], limit=5, strategy=strategy)
                metrics = calculate_metrics(results, q["expected_clause_path"])
                
                total_r1 += metrics["recall@1"]
                total_r3 += metrics["recall@3"]
                total_r5 += metrics["recall@5"]
                total_mrr += metrics["mrr"]
                
            n = len(queries)
            print(f"=== {strategy.upper()} STRATEGY ===")
            print(f"Recall@1: {total_r1/n:.2f}")
            print(f"Recall@3: {total_r3/n:.2f}")
            print(f"Recall@5: {total_r5/n:.2f}")
            print(f"MRR:      {total_mrr/n:.2f}\n")
            
            results_json["strategies"][strategy] = {
                "Recall@1": total_r1/n,
                "Recall@3": total_r3/n,
                "Recall@5": total_r5/n,
                "MRR": total_mrr/n
            }
            
        import json
        out_dir = Path(__file__).parent.parent / "data" / "benchmarks" / "retrieval" / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "v0.3.0.json"
        with open(out_file, "w") as f:
            json.dump(results_json, f, indent=4)
        print(f"Saved benchmark results to {out_file}")

if __name__ == "__main__":
    asyncio.run(evaluate())

