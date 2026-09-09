from abc import ABC, abstractmethod

class BaseEmbeddingProvider(ABC):
    """
    Abstract interface for generating embeddings.
    """
    
    @abstractmethod
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        pass
        
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embeddings produced by this provider."""
        pass
        
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name of the model being used."""
        pass

