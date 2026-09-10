from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid

class CanonicalEvidence(BaseModel):
    """Canonical representation of retrieved regulatory evidence."""
    evidence_id: str
    chunk_id: Optional[str] = None
    clause_id: Optional[str] = None
    clause_number: Optional[str] = None
    clause_path: str
    clause_type: str
    source_text: str
    page_number: Optional[int] = None
    document_version_id: Optional[str] = None
    regulatory_document_id: Optional[str] = None
    jurisdiction_id: Optional[str] = None
    retrieval_score: Optional[float] = None
    retrieval_method: Optional[str] = None

class Citation(BaseModel):
    evidence_id: str
    clause_number: Optional[str] = None
    page_number: Optional[int] = None

class StructuredAnswer(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    grounding_status: str = "grounded" # grounded, insufficient_evidence, validation_failed, error
    confidence: str = "high" # high, medium, low
    limitations: List[str] = Field(default_factory=list)

class ToolTrace(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result_evidence_ids: List[str]
    latency_ms: float
    status: str

class AgentToolSchema(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class LLMMessage(BaseModel):
    """Internal representation of an LLM conversation turn."""
    role: str # "user", "model", "tool"
    content: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None # {"name": str, "args": dict}
    function_response: Optional[Dict[str, Any]] = None # {"name": str, "response": dict}

class LLMResponse(BaseModel):
    message: LLMMessage
    text: Optional[str] = None
    function_calls: List[Dict[str, Any]] = Field(default_factory=list)

class QARequest(BaseModel):
    question: str
    jurisdiction_id: Optional[uuid.UUID] = None
    document_version_id: Optional[uuid.UUID] = None

class QAResponse(BaseModel):
    answer: str
    citations: List[Citation]
    grounding_status: str
    confidence: str
    limitations: List[str]
    evidence_used: List[CanonicalEvidence]
    tool_traces: Optional[List[ToolTrace]] = None
