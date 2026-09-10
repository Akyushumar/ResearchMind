import asyncio
import json
import yaml
import time
from pathlib import Path

from researchmind.db.engine import create_engine
from researchmind.db.session import create_session_factory
from researchmind.db.vector_store import VectorStore
from researchmind.config.settings import get_settings
from researchmind.retrieval.lexical_retriever import LexicalRetriever
from researchmind.retrieval.semantic_retriever import SemanticRetriever
from researchmind.retrieval.hybrid_search import HybridSearchService
from researchmind.retrieval.embeddings.factory import get_embedding_provider
from researchmind.agent.tools import AgentToolsRegistry
from researchmind.agent.llm.factory import get_llm_provider
from researchmind.agent.dcr_agent import DCRAgent
from researchmind.agent.models import QARequest

async def main():
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    session_factory = create_session_factory(engine)
    
    vector_store = VectorStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.qdrant_collection,
    )
    
    with open("data/benchmarks/qa/udcpr_ch8_questions.yaml", "r") as f:
        cases = yaml.safe_load(f)
        
    results = []
    
    # QA Metrics
    total = len(cases)
    answerable_total = sum(1 for c in cases if c.get("required_clauses"))
    unanswerable_total = total - answerable_total
    
    grounded_correctly = 0
    insufficient_correctly = 0
    clause_coverage_sum = 0
    citation_correctness_sum = 0
    unsupported_claim_count = 0

    async with session_factory() as session:
        lexical = LexicalRetriever(session)
        embedding_provider = get_embedding_provider(settings)
        semantic = SemanticRetriever(vector_store, embedding_provider, session)
        hybrid = HybridSearchService(lexical, semantic)
        
        tools_registry = AgentToolsRegistry(hybrid, session)
        llm = get_llm_provider(settings)
        
        # Reset cache for each agent but we can just use one agent if we clear traces
        
        for case in cases:
            # We want a fresh agent per question to isolate state and tools cache
            tools_registry = AgentToolsRegistry(hybrid, session)
            agent = DCRAgent(llm, tools_registry)

            q = case["question"]
            expected = case["expected_answer"]
            req_clauses = set(case.get("required_clauses", []))
            unsupported = case.get("unsupported_claims", [])
            
            print(f"Testing: {q}")
            
            req = QARequest(question=q)
            resp = await agent.answer(req)
            
            is_answerable = len(req_clauses) > 0
            
            # Metrics
            cited_evidence_ids = {c.evidence_id for c in resp.citations}
            cited_clause_paths = set()
            for ev in resp.evidence_used:
                if ev.evidence_id in cited_evidence_ids:
                    cited_clause_paths.add(ev.clause_path)
            
            if is_answerable:
                if resp.grounding_status == "grounded":
                    grounded_correctly += 1
                
                # Clause coverage (recall of required clauses)
                if req_clauses:
                    cov = len(req_clauses.intersection(cited_clause_paths)) / len(req_clauses)
                    clause_coverage_sum += cov
                    
                # Citation correctness (precision of cited clauses)
                if cited_clause_paths:
                    corr = len(cited_clause_paths.intersection(req_clauses)) / len(cited_clause_paths)
                    citation_correctness_sum += corr
                else:
                    citation_correctness_sum += 0
            else:
                if resp.grounding_status == "insufficient_evidence":
                    insufficient_correctly += 1
                else:
                    unsupported_claim_count += 1
                    
            results.append({
                "id": case["id"],
                "question": q,
                "expected": expected,
                "actual_answer": resp.answer,
                "grounding_status": resp.grounding_status,
                "confidence": resp.confidence,
                "citations": [c.model_dump() for c in resp.citations],
                "cited_clause_paths": list(cited_clause_paths),
                "limitations": resp.limitations,
                "tool_calls": len(resp.tool_traces) if resp.tool_traces else 0
            })
            
            # Sleep briefly to avoid API rate limits
            time.sleep(15)
            
    # Calculate final metrics
    avg_clause_coverage = clause_coverage_sum / answerable_total if answerable_total > 0 else 0
    avg_citation_correctness = citation_correctness_sum / answerable_total if answerable_total > 0 else 0
    insufficient_acc = insufficient_correctly / unanswerable_total if unanswerable_total > 0 else 0
    grounded_rate = grounded_correctly / answerable_total if answerable_total > 0 else 0
    
    metrics = {
        "total_questions": total,
        "answerable_questions": answerable_total,
        "unanswerable_questions": unanswerable_total,
        "grounded_rate": grounded_rate,
        "average_clause_coverage": avg_clause_coverage,
        "average_citation_correctness": avg_citation_correctness,
        "insufficient_evidence_accuracy": insufficient_acc,
        "unsupported_claim_count": unsupported_claim_count
    }
    
    output = {
        "metrics": metrics,
        "details": results
    }
    
    out_dir = Path("data/benchmarks/qa/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "v0.4.0.json"
    
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
        
    print(json.dumps(metrics, indent=2))
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
