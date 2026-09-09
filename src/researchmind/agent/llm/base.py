from abc import ABC, abstractmethod
from typing import List, Optional

from researchmind.agent.models import AgentToolSchema, LLMMessage, LLMResponse

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        system_instruction: Optional[str] = None,
        tools: Optional[List[AgentToolSchema]] = None,
    ) -> LLMResponse:
        """
        Send a chat request to the LLM.
        
        Args:
            messages: The conversation history, including function calls/responses.
            system_instruction: Optional system prompt to guide behavior.
            tools: Optional list of tools the model can invoke.
            
        Returns:
            An LLMResponse containing the model's message, text, and any function calls.
        """
        pass
