import math
import os
import json
from typing import List, Dict, Any, Tuple
from app.services.chunker_service import CodeChunk
from app.core.logging import logger


class VectorStore:
    """In-memory cosine similarity and metadata index for vector search foundation."""

    def __init__(self, repo_name: str):
        self.repo_name = repo_name
        self.chunks: List[CodeChunk] = []
        self.embeddings: List[List[float]] = []

    def add_chunks(self, chunks: List[CodeChunk], embeddings: List[List[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks count and embeddings count must match.")
        
        self.chunks.extend(chunks)
        self.embeddings.extend(embeddings)
        logger.info(f"Indexed {len(chunks)} chunks for repository '{self.repo_name}'")

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1e-9
        norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1e-9
        return dot / (norm_a * norm_b)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[CodeChunk, float]]:
        if not self.embeddings or not self.chunks:
            return []

        scores: List[Tuple[int, float]] = []
        for idx, emb in enumerate(self.embeddings):
            score = self._cosine_similarity(query_embedding, emb)
            scores.append((idx, score))

        # Sort descending by score
        scores.sort(key=lambda x: x[1], reverse=True)

        results: List[Tuple[CodeChunk, float]] = []
        for idx, score in scores[:top_k]:
            results.append((self.chunks[idx], score))

        return results


# Global in-memory vector store repository cache
STORE_CACHE: Dict[str, VectorStore] = {}


def get_vector_store(repo_name: str) -> VectorStore:
    if repo_name not in STORE_CACHE:
        STORE_CACHE[repo_name] = VectorStore(repo_name)
    return STORE_CACHE[repo_name]
