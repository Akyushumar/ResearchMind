from researchmind.config.settings import Settings
from .base import BaseEmbeddingProvider
from .openai_provider import OpenAIEmbeddingProvider
from .gemini_provider import GeminiEmbeddingProvider

def get_embedding_provider(settings: Settings) -> BaseEmbeddingProvider:
    provider = settings.embedding_provider.lower()
    
    if provider == "gemini":
        return GeminiEmbeddingProvider(
            model=settings.embedding_model,
            dimension=settings.embedding_dimension,
            api_key=settings.gemini_api_key
        )
    elif provider == "openai":
        return OpenAIEmbeddingProvider(
            model=settings.embedding_model,
            dimension=settings.embedding_dimension,
            api_key=settings.openai_api_key
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")

