import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from researchmind.retrieval.embeddings.gemini_provider import GeminiEmbeddingProvider

@pytest.fixture
def mock_genai_client():
    with patch("researchmind.retrieval.embeddings.gemini_provider.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Mock embed_content
        mock_response = MagicMock()
        mock_response.embeddings = [MagicMock(values=[0.1] * 3072)]
        mock_client.models.embed_content.return_value = mock_response
        
        yield mock_client

@pytest.fixture
def mock_genai_client_batch():
    with patch("researchmind.retrieval.embeddings.gemini_provider.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Mock embed_content for batch
        def _mock_embed(*args, **kwargs):
            # args[1] is contents, a list of texts
            contents = kwargs.get('contents') or args[1]
            mock_response = MagicMock()
            mock_response.embeddings = [MagicMock(values=[0.1] * 3072) for _ in contents]
            return mock_response
            
        mock_client.models.embed_content.side_effect = _mock_embed
        
        yield mock_client

def test_gemini_provider_init(mock_genai_client):
    provider = GeminiEmbeddingProvider(
        api_key=SecretStr("fake-key"),
        model="gemini-embedding-2",
        dimension=3072
    )
    assert provider.model_name == "gemini-embedding-2"
    assert provider.dimension == 3072

def test_gemini_provider_init_missing_key():
    with patch.dict(os.environ, clear=True): # Ensure GEMINI_API_KEY is not in env
        with pytest.raises(ValueError, match="Missing Gemini credentials"):
            GeminiEmbeddingProvider(
                api_key=None,
                model="gemini-embedding-2",
                dimension=3072
            )

@pytest.mark.asyncio
async def test_embed_text(mock_genai_client):
    provider = GeminiEmbeddingProvider(
        api_key=SecretStr("fake-key"),
        model="gemini-embedding-2",
        dimension=3072
    )
    
    embedding = await provider.get_embeddings(["test text"])
    assert len(embedding) == 1
    assert len(embedding[0]) == 3072
    mock_genai_client.models.embed_content.assert_called_once()
    kwargs = mock_genai_client.models.embed_content.call_args.kwargs
    assert kwargs["model"] == "gemini-embedding-2"
    assert kwargs["contents"] == "test text"

@pytest.mark.asyncio
async def test_embed_batch(mock_genai_client_batch):
    provider = GeminiEmbeddingProvider(
        api_key=SecretStr("fake-key"),
        model="gemini-embedding-2",
        dimension=3072
    )
    
    texts = ["test 1", "test 2", "test 3"]
    embeddings = await provider.get_embeddings(texts)
    
    assert len(embeddings) == 3
    assert len(embeddings[0]) == 3072
    assert mock_genai_client_batch.models.embed_content.call_count == 3
    # Check the last call
    kwargs = mock_genai_client_batch.models.embed_content.call_args.kwargs
    assert kwargs["contents"] == "test 3"

@pytest.mark.asyncio
async def test_embed_text_api_error(mock_genai_client):
    mock_genai_client.models.embed_content.side_effect = Exception("API failure")
    
    provider = GeminiEmbeddingProvider(
        api_key=SecretStr("fake-key"),
        model="gemini-embedding-2",
        dimension=3072
    )
    
    with pytest.raises(Exception, match="API failure"):
        await provider.get_embeddings(["test"])
