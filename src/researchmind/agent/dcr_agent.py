import json
import time
from typing import List, Optional, Dict, Any
from pydantic import ValidationError

from researchmind.agent.models import (
    QARequest, QAResponse, StructuredAnswer, 
    ToolTrace, LLMMessage, AgentToolSchema, CanonicalEvidence
)
from researchmind.agent.llm.base import BaseLLMProvider
from researchmind.agent.tools import AgentToolsRegistry
from researchmind.agent.validator import GroundingValidator

SYSTEM_PROMPT = """You are a strictly grounded regulatory QA agent.
Your objective is to answer questions using ONLY the provided regulatory evidence.
You have access to tools to search for and retrieve specific clauses.

CRITICAL INSTRUCTIONS:
1. NEVER invent, hallucinate, or assume a clause number, page number, or regulatory requirement.
2. Every substantive claim MUST be supported by a citation to an `evidence_id` returned by a tool.
3. If the retrieved evidence does not contain the answer, you MUST state that evidence is insufficient and set your grounding_status to "insufficient_evidence".
4. Do not synthesize answers from general knowledge.
5. You can call tools sequentially to gather more information (e.g. search, then get children).

When you are ready to answer, DO NOT call any more tools. Instead, output a JSON object containing your final structured answer. The JSON must exactly match this schema:
{
    "answer": "The text of your answer",
    "citations": [
        {"evidence_id": "...", "clause_number": "...", "page_number": 123}
    ],
    "grounding_status": "grounded" | "insufficient_evidence",
    "confidence": "high" | "medium" | "low",
    "limitations": ["Any limitations or missing parts of the answer"]
}

Output ONLY valid JSON.
"""

class DCRAgent:
    def __init__(self, llm: BaseLLMProvider, tools_registry: AgentToolsRegistry, max_tool_calls: int = 5):
        self.llm = llm
        self.tools = tools_registry
        self.max_tool_calls = max_tool_calls
        self.traces: List[ToolTrace] = []

    async def answer(self, request: QARequest) -> QAResponse:
        messages: List[LLMMessage] = [
            LLMMessage(role="user", content=f"Question: {request.question}\n\nJurisdiction ID: {request.jurisdiction_id}\nDocument Version ID: {request.document_version_id}")
        ]
        
        tool_schemas = self.tools.get_schemas()
        calls_made = 0
        final_structured_answer = None

        while calls_made < self.max_tool_calls:
            try:
                llm_resp = await self.llm.chat(
                    messages=messages,
                    system_instruction=SYSTEM_PROMPT,
                    tools=tool_schemas
                )
            except Exception as e:
                # LLM Failure
                return self._create_error_response(request, str(e), "LLM API Error")
                
            messages.append(llm_resp.message)

            if llm_resp.function_calls:
                # Agent wants to call a tool
                fc = llm_resp.function_calls[0]
                name = fc["name"]
                args = fc.get("args", {})
                
                # Execute tool
                start_t = time.perf_counter()
                try:
                    result = await self.tools.execute(name, args)
                    status = "success"
                except Exception as e:
                    result = {"error": str(e)}
                    status = "error"
                latency = (time.perf_counter() - start_t) * 1000
                
                # Trace
                ev_ids = []
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict) and "evidence_id" in item:
                            ev_ids.append(item["evidence_id"])
                        elif isinstance(item, dict) and "target_evidence" in item:
                            ev_ids.append(item["target_evidence"]["evidence_id"])
                elif isinstance(result, dict) and "evidence_id" in result:
                    ev_ids.append(result["evidence_id"])
                    
                self.traces.append(ToolTrace(
                    tool_name=name,
                    arguments=args,
                    result_evidence_ids=ev_ids,
                    latency_ms=latency,
                    status=status
                ))
                
                messages.append(LLMMessage(
                    role="tool",
                    function_response={"name": name, "response": {"result": result}}
                ))
                calls_made += 1
            else:
                # Agent provided text, attempt to parse JSON
                text = llm_resp.message.content or ""
                # Clean up markdown code blocks if present
                if text.startswith("```json"):
                    text = text.replace("```json", "").replace("```", "").strip()
                elif text.startswith("```"):
                    text = text.replace("```", "").strip()
                    
                try:
                    parsed = json.loads(text)
                    final_structured_answer = StructuredAnswer(**parsed)
                    break # Successful answer
                except (json.JSONDecodeError, ValidationError) as e:
                    # Model failed to output correct schema
                    messages.append(LLMMessage(
                        role="user", 
                        content=f"Your response was not valid JSON matching the schema. Error: {str(e)}. Please output ONLY the JSON object."
                    ))
                    calls_made += 1

        if not final_structured_answer:
            final_structured_answer = StructuredAnswer(
                answer="Tool budget exhausted or model failed to produce a valid response.",
                citations=[],
                grounding_status="insufficient_evidence",
                confidence="low",
                limitations=["Budget exhausted"]
            )
            
        # Validation
        validator = GroundingValidator(self.tools.evidence_cache)
        validated_answer = validator.validate(final_structured_answer)
        
        # Build Evidence Used list
        used_ev = []
        for cit in validated_answer.citations:
            if cit.evidence_id in self.tools.evidence_cache:
                used_ev.append(self.tools.evidence_cache[cit.evidence_id])
                
        return QAResponse(
            answer=validated_answer.answer,
            citations=validated_answer.citations,
            grounding_status=validated_answer.grounding_status,
            confidence=validated_answer.confidence,
            limitations=validated_answer.limitations,
            evidence_used=used_ev,
            tool_traces=self.traces
        )
        
    def _create_error_response(self, req: QARequest, msg: str, status: str) -> QAResponse:
        return QAResponse(
            answer=msg,
            citations=[],
            grounding_status="error",
            confidence="low",
            limitations=["Execution failed"],
            evidence_used=[],
            tool_traces=self.traces
        )
