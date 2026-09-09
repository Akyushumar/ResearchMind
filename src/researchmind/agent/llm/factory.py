from researchmind.agent.llm.base import BaseLLMProvider
from researchmind.agent.llm.gemini_provider import GeminiLLMProvider
from researchmind.config.settings import Settings

def get_llm_provider(settings: Settings) -> BaseLLMProvider:
    """Factory function to get the configured LLM provider."""
    if settings.llm_provider.lower() == "gemini":
        return GeminiLLMProvider(
            model_name=settings.llm_model,
            api_key=settings.gemini_api_key
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
