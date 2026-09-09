from google import genai
from typing import List
import os

from researchmind.retrieval.embeddings.base import BaseEmbeddingProvider

class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model: str, dimension: int, api_key: str | None = None):
        self._model = model
        self._dimension = dimension
        
        resolved_key = api_key or os.environ.get("RESEARCHMIND_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Missing Gemini credentials. Please pass `api_key` or set "
                "`RESEARCHMIND_GEMINI_API_KEY` or `GEMINI_API_KEY` environment variable."
            )
            
        self.client = genai.Client(api_key=resolved_key)
        
    @property
    def dimension(self) -> int:
        return self._dimension
        
    @property
    def model_name(self) -> str:
        return self._model
        
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # The new SDK is asynchronous? No, `google-genai` provides sync client mostly but we can use run_in_executor or async client if available.
        # Actually, let's use the async client.
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Make a helper function to run synchronous genai call in executor
        def _get_embeddings():
            # In google-genai, it's client.models.embed_content
            # To handle multiple texts, we can either loop or pass a list if supported.
            results = []
            for text in texts:
                response = self.client.models.embed_content(
                    model=self._model,
                    contents=text,
                    config={"output_dimensionality": self._dimension}
                )
                results.append(response.embeddings[0].values)
            return results
            
        return await loop.run_in_executor(None, _get_embeddings)
