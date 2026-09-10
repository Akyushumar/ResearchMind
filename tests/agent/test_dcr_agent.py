import pytest
import uuid
from researchmind.agent.models import (
    QARequest, QAResponse, LLMMessage, AgentToolSchema, LLMResponse
)
from researchmind.agent.dcr_agent import DCRAgent
from researchmind.agent.llm.base import BaseLLMProvider
from researchmind.agent.tools import AgentToolsRegistry

class MockLLMProvider(BaseLLMProvider):
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    async def chat(self, messages, system_instruction=None, tools=None):
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        raise Exception("Out of mock responses")

class MockToolsRegistry(AgentToolsRegistry):
    def __init__(self):
        # Don't call super().__init__ to avoid needing real dependencies
        self.evidence_cache = {}
        
    def get_schemas(self):
        return [
            AgentToolSchema(
                name="test_tool",
                description="A test tool",
                parameters={"type": "object", "properties": {}}
            )
        ]

    async def execute(self, name, kwargs):
        if name == "test_tool":
            return [{"evidence_id": "ev_1234", "text": "Mocked evidence"}]
        return []

@pytest.mark.asyncio
async def test_dcr_agent_single_turn_success():
    llm = MockLLMProvider([
        LLMResponse(
            message=LLMMessage(
                role="model",
                content='{"answer": "A regulatory answer.", "citations": [{"evidence_id": "ev_123", "clause_number": "1.2"}], "grounding_status": "grounded", "confidence": "high", "limitations": []}'
            )
        )
    ])
    
    tools = MockToolsRegistry()
    # Pre-seed cache to pass citation check
    from researchmind.agent.models import CanonicalEvidence
    tools.evidence_cache["ev_123"] = CanonicalEvidence(
        evidence_id="ev_123",
        clause_number="1.2",
        clause_path="1.2",
        clause_type="clause",
        source_text="Test",
    )
    
    agent = DCRAgent(llm, tools)
    req = QARequest(question="Test question?")
    resp = await agent.answer(req)
    
    assert resp.answer == "A regulatory answer."
    assert resp.grounding_status == "grounded"
    assert resp.confidence == "high"
    assert len(resp.citations) == 1

@pytest.mark.asyncio
async def test_dcr_agent_tool_calling_loop():
    llm = MockLLMProvider([
        LLMResponse(
            message=LLMMessage(
                role="model",
                function_call={"name": "test_tool", "args": {}}
            ),
            function_calls=[{"name": "test_tool", "args": {}}]
        ),
        LLMResponse(
            message=LLMMessage(
                role="model",
                content='{"answer": "Answer from tool.", "citations": [{"evidence_id": "ev_1234"}], "grounding_status": "grounded", "confidence": "high", "limitations": []}'
            )
        )
    ])
    
    tools = MockToolsRegistry()
    # the tool itself will return ev_1234, let's preseed cache as if the tool did it
    from researchmind.agent.models import CanonicalEvidence
    tools.evidence_cache["ev_1234"] = CanonicalEvidence(
        evidence_id="ev_1234",
        clause_number="4.5",
        clause_path="4.5",
        clause_type="clause",
        source_text="Mocked evidence",
    )
    
    agent = DCRAgent(llm, tools)
    req = QARequest(question="Test tool?")
    resp = await agent.answer(req)
    
    assert resp.answer == "Answer from tool."
    assert len(agent.traces) == 1
    assert agent.traces[0].tool_name == "test_tool"
    assert resp.grounding_status == "grounded"

@pytest.mark.asyncio
async def test_dcr_agent_invalid_citation():
    llm = MockLLMProvider([
        LLMResponse(
            message=LLMMessage(
                role="model",
                content='{"answer": "A bad answer.", "citations": [{"evidence_id": "fake_ev_999"}], "grounding_status": "grounded", "confidence": "high", "limitations": []}'
            )
        )
    ])
    
    tools = MockToolsRegistry()
    
    agent = DCRAgent(llm, tools)
    req = QARequest(question="Bad citation?")
    resp = await agent.answer(req)
    
    # Validator should catch fake citation
    assert resp.grounding_status == "validation_failed"
    assert resp.confidence == "low"
    assert len(resp.limitations) > 0
    assert "fake_ev_999" in resp.limitations[0]

