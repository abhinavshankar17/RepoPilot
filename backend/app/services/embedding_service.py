from abc import ABC, abstractmethod
from typing import List
import math
import random
from app.core.config import settings
from app.core.logging import logger


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic mock embedding provider for lightweight testing without heavy model downloads."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _text_to_vector(self, text: str) -> List[float]:
        # Generate pseudo-deterministic vector based on text characters
        seed = sum(ord(c) for c in text)
        random.seed(seed)
        vec = [random.uniform(-1.0, 1.0) for _ in range(self.dimension)]
        # Normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._text_to_vector(query)


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Factory function for selecting the configured embedding provider."""
    # For initial foundation setup, default to MockEmbeddingProvider to ensure immediate runnability
    return MockEmbeddingProvider()
