import os
from openai import AsyncOpenAI
from researchmind.retrieval.embeddings.base import BaseEmbeddingProvider

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model: str = "text-embedding-3-small", dimension: int = 1536):
        self._model = model
        self._dimension = dimension
        self.client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        # Handle empty lists gracefully
        if not texts:
            return []
            
        # Optional: chunk into batches if texts list is huge, 
        # but for typical usage standard API batches of ~2048 are usually fine.
        response = await self.client.embeddings.create(
            model=self._model,
            input=texts,
            dimensions=self._dimension if "text-embedding-3" in self._model else None
        )
        
        # Sort by index to maintain order just in case
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    @property
    def dimension(self) -> int:
        return self._dimension
        
    @property
    def model_name(self) -> str:
        return self._model

