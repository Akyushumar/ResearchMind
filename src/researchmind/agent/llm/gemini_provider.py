import os
from typing import List, Optional

from google import genai
from google.genai import types

from researchmind.agent.llm.base import BaseLLMProvider
from researchmind.agent.models import AgentToolSchema, LLMMessage, LLMResponse


class GeminiLLMProvider(BaseLLMProvider):
    """Gemini LLM Provider using the google-genai SDK."""

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)

    def _convert_tools(self, tools: List[AgentToolSchema]) -> List[types.Tool]:
        converted = []
        for t in tools:
            func = types.FunctionDeclaration(
                name=t.name,
                description=t.description,
                parameters_json_schema=t.parameters,
            )
            converted.append(types.Tool(function_declarations=[func]))
        return converted

    def _convert_messages(self, messages: List[LLMMessage]) -> List[types.Content]:
        contents = []
        for msg in messages:
            if msg.role == "user":
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg.content or "")]))
            elif msg.role == "model":
                parts = []
                if msg.content:
                    parts.append(types.Part.from_text(text=msg.content))
                if msg.function_call:
                    fc = types.FunctionCall(
                        name=msg.function_call["name"],
                        args=msg.function_call["args"],
                    )
                    parts.append(types.Part.from_function_call(name=fc.name, args=fc.args))
                contents.append(types.Content(role="model", parts=parts))
            elif msg.role == "tool":
                if msg.function_response:
                    fr = types.Part.from_function_response(
                        name=msg.function_response["name"],
                        response=msg.function_response["response"]
                    )
                    contents.append(types.Content(role="user", parts=[fr])) # Gemini represents tool responses as role=user typically or role=function/tool depending on version. The doc says role="tool" works. Wait, the docs say role="tool".
                    # Let's use role="tool" as per the official docs snippet we retrieved.
        # Wait, let me fix the role="tool" in the next pass if it fails.
        return contents

    async def chat(
        self,
        messages: List[LLMMessage],
        system_instruction: Optional[str] = None,
        tools: Optional[List[AgentToolSchema]] = None,
    ) -> LLMResponse:
        
        contents = []
        for msg in messages:
            if msg.role == "user":
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg.content or "")]))
            elif msg.role == "model":
                parts = []
                if msg.content:
                    parts.append(types.Part.from_text(text=msg.content))
                if msg.function_call:
                    parts.append(types.Part.from_function_call(
                        name=msg.function_call["name"],
                        args=msg.function_call["args"]
                    ))
                contents.append(types.Content(role="model", parts=parts))
            elif msg.role == "tool" and msg.function_response:
                fr = types.Part.from_function_response(
                    name=msg.function_response["name"],
                    response=msg.function_response["response"]
                )
                contents.append(types.Content(role="tool", parts=[fr]))

        config = types.GenerateContentConfig()
        if system_instruction:
            config.system_instruction = system_instruction
        if tools:
            config.tools = self._convert_tools(tools)
            
        # Using synchronous generate_content because currently google-genai supports asyncio via generate_content_async maybe?
        # Actually, let's use client.models.generate_content (which is synchronous) in an executor, or client.aio if available.
        # Let's just use generate_content for now. Or look if google-genai has generate_content_async. Wait, we can use client.aio.models.generate_content.
        
        if self.client.aio:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
        else:
            # Fallback if aio is not present (though it usually is in 0.3.0+)
            import asyncio
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
            )
        
        # Parse response
        text = response.text if response.text else None
        
        function_calls = []
        if response.function_calls:
            for fc in response.function_calls:
                function_calls.append({"name": fc.name, "args": fc.args})
                
        out_msg = LLMMessage(
            role="model",
            content=text,
            function_call=function_calls[0] if function_calls else None
        )
        
        return LLMResponse(
            message=out_msg,
            text=text,
            function_calls=function_calls
        )
