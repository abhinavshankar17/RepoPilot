import math
import hashlib
from abc import ABC, abstractmethod
from typing import List
import numpy as np

from app.core.config import settings
from app.core.logging import logger


class BaseEmbeddingProvider(ABC):
    """Abstract base interface for embedding providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the vector embedding dimension."""
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generates embedding vectors for a list of text strings in batches."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generates an embedding vector for a single search query."""
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic, lightweight mock embedding provider for fast offline testing
    and fallback operation without external API dependencies.
    """

    def __init__(self, dim: int = 384):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _text_to_vector(self, text: str) -> List[float]:
        # Hash text into deterministic pseudo-vector
        vec = []
        text_bytes = text.encode("utf-8")
        for i in range(self._dim):
            h = hashlib.sha256(text_bytes + str(i).encode("utf-8")).digest()
            val = (int.from_bytes(h[:4], "big") / 2**32) * 2.0 - 1.0
            vec.append(val)

        # L2 normalize vector for cosine similarity compatibility
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        if not texts:
            return []
        
        results: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_vectors = [self._text_to_vector(t) for t in batch]
            results.extend(batch_vectors)
        return results

    def embed_query(self, query: str) -> List[float]:
        return self._text_to_vector(query)


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI API embedding provider using text-embedding-3-small or text-embedding-ada-002."""

    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME or "text-embedding-3-small"
        self._dim = 1536

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        if not texts:
            return []
        if not self.api_key:
            logger.warning("OpenAI API key missing. Falling back to MockEmbeddingProvider.")
            return MockEmbeddingProvider(self._dim).embed_texts(texts, batch_size)

        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            results = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                payload = {"input": batch, "model": self.model_name}
                response = httpx.post("https://api.openai.com/v1/embeddings", json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                vectors = [item["embedding"] for item in data["data"]]
                results.extend(vectors)
            return results
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}. Falling back to Mock embedding provider.")
            return MockEmbeddingProvider(self._dim).embed_texts(texts, batch_size)

    def embed_query(self, query: str) -> List[float]:
        res = self.embed_texts([query])
        return res[0] if res else MockEmbeddingProvider(self._dim).embed_query(query)


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Factory creating the configured embedding provider."""
    provider_name = settings.EMBEDDING_PROVIDER.lower().strip()
    
    if provider_name == "openai" and settings.OPENAI_API_KEY:
        return OpenAIEmbeddingProvider()
    
    return MockEmbeddingProvider()
