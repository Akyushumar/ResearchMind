from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from researchmind.api.dependencies import get_db, get_vector_store, get_settings_dep
from researchmind.config.settings import Settings
from researchmind.db.vector_store import VectorStore
from researchmind.retrieval.lexical_retriever import LexicalRetriever
from researchmind.retrieval.semantic_retriever import SemanticRetriever
from researchmind.retrieval.hybrid_search import HybridSearchService
from researchmind.retrieval.embeddings.factory import get_embedding_provider
from researchmind.agent.models import QARequest, QAResponse
from researchmind.agent.llm.factory import get_llm_provider
from researchmind.agent.tools import AgentToolsRegistry
from researchmind.agent.dcr_agent import DCRAgent

router = APIRouter(prefix="/qa", tags=["QA Agent"])

@router.post("/", response_model=QAResponse)
async def answer_question(
    request: QARequest,
    debug: bool = Query(False, description="Include tool execution traces"),
    session: AsyncSession = Depends(get_db),
    vector_store: VectorStore = Depends(get_vector_store),
    settings: Settings = Depends(get_settings_dep)
):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Initialize retrieval services (for the tools)
    lexical = LexicalRetriever(session)
    embedding_provider = get_embedding_provider(settings)
    semantic = SemanticRetriever(vector_store, embedding_provider, session)
    hybrid = HybridSearchService(lexical, semantic)
    
    # Initialize Agent components
    tools_registry = AgentToolsRegistry(hybrid, session)
    llm_provider = get_llm_provider(settings)
    
    agent = DCRAgent(llm=llm_provider, tools_registry=tools_registry, max_tool_calls=5)
    
    try:
        response = await agent.answer(request)
        if not debug:
            response.tool_traces = None
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
