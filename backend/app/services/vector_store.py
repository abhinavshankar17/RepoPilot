import os
import json
import shutil
import faiss
import numpy as np
from typing import List, Tuple, Dict, Optional, Any

from app.core.config import settings
from app.core.logging import logger
from app.schemas.chunk import CodeChunk
from app.services.embedding_service import BaseEmbeddingProvider, get_embedding_provider


class FaissRepositoryIndex:
    """Encapsulates a FAISS vector index and its corresponding metadata store for a repository."""

    def __init__(self, repository_id: str, dimension: int):
        self.repository_id = repository_id
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product for L2-normalized cosine similarity
        self.metadata_store: List[Dict[str, Any]] = []

    def add_vectors(self, vectors: List[List[float]], metadata_list: List[Dict[str, Any]]) -> None:
        if not vectors:
            return
        if len(vectors) != len(metadata_list):
            raise ValueError("Vectors and metadata length mismatch.")

        vec_np = np.array(vectors, dtype=np.float32)
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vec_np)
        self.index.add(vec_np)
        self.metadata_store.extend(metadata_list)

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if self.index.ntotal == 0 or not self.metadata_store:
            return []

        q_np = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q_np)

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(q_np, k)

        results: List[Tuple[Dict[str, Any], float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx != -1 and idx < len(self.metadata_store):
                results.append((self.metadata_store[idx], float(score)))

        return results


class VectorStoreService:
    """Service managing repository-isolated FAISS vector indices and disk persistence."""

    def __init__(self, base_dir: Optional[str] = None, embedding_provider: Optional[BaseEmbeddingProvider] = None):
        self.base_dir = base_dir or settings.VECTOR_STORE_DIR
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self._indices: Dict[str, FaissRepositoryIndex] = {}

    def _get_repo_dir(self, repository_id: str) -> str:
        return os.path.join(self.base_dir, repository_id)

    def _get_index_path(self, repository_id: str) -> str:
        return os.path.join(self._get_repo_dir(repository_id), "index.faiss")

    def _get_metadata_path(self, repository_id: str) -> str:
        return os.path.join(self._get_repo_dir(repository_id), "metadata.json")

    def index_repository(self, repository_id: str, chunks: List[CodeChunk]) -> Tuple[int, int]:
        """Indexes code chunks into a repository-specific FAISS vector store and saves to disk."""
        repo_dir = self._get_repo_dir(repository_id)
        os.makedirs(repo_dir, exist_ok=True)

        dimension = self.embedding_provider.dimension
        repo_index = FaissRepositoryIndex(repository_id, dimension)

        if not chunks:
            logger.info(f"Empty chunk list for repository '{repository_id}'. Creating empty FAISS index.")
            self._save_to_disk(repository_id, repo_index)
            self._indices[repository_id] = repo_index
            return 0, dimension

        # Format texts for embedding generation
        texts = []
        metadata_list = []
        for chunk in chunks:
            import_ctx = "\n".join(chunk.imports) if chunk.imports else ""
            embed_text = f"File: {chunk.file_path} Symbol: {chunk.symbol_name} ({chunk.symbol_type})\n{import_ctx}\n{chunk.content}"
            texts.append(embed_text)
            metadata_list.append(chunk.model_dump())

        # Generate batch embeddings
        vectors = self.embedding_provider.embed_texts(texts, batch_size=32)
        repo_index.add_vectors(vectors, metadata_list)

        self._save_to_disk(repository_id, repo_index)
        self._indices[repository_id] = repo_index
        logger.info(f"Indexed {len(chunks)} chunks into FAISS vector store for repository '{repository_id}'.")
        return len(chunks), dimension

    def search(self, repository_id: str, query: str, top_k: int = 5) -> List[Tuple[CodeChunk, float]]:
        """Executes a vector similarity search on a specific repository's FAISS index."""
        if repository_id not in self._indices:
            loaded = self.load_index(repository_id)
            if not loaded:
                logger.warning(f"No FAISS index found for repository '{repository_id}'.")
                return []

        repo_index = self._indices[repository_id]
        query_vector = self.embedding_provider.embed_query(query)
        results = repo_index.search(query_vector, top_k=top_k)

        matched_chunks: List[Tuple[CodeChunk, float]] = []
        for meta, score in results:
            chunk = CodeChunk(**meta)
            matched_chunks.append((chunk, score))

        return matched_chunks

    def _save_to_disk(self, repository_id: str, repo_index: FaissRepositoryIndex) -> None:
        repo_dir = self._get_repo_dir(repository_id)
        os.makedirs(repo_dir, exist_ok=True)

        index_path = self._get_index_path(repository_id)
        metadata_path = self._get_metadata_path(repository_id)

        faiss.write_index(repo_index.index, index_path)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(repo_index.metadata_store, f, indent=2)

    def load_index(self, repository_id: str) -> bool:
        """Loads FAISS index and metadata store from disk for a repository."""
        index_path = self._get_index_path(repository_id)
        metadata_path = self._get_metadata_path(repository_id)

        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            return False

        try:
            faiss_index = faiss.read_index(index_path)
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_store = json.load(f)

            repo_index = FaissRepositoryIndex(repository_id, self.embedding_provider.dimension)
            repo_index.index = faiss_index
            repo_index.metadata_store = metadata_store

            self._indices[repository_id] = repo_index
            logger.info(f"Successfully loaded FAISS index for repository '{repository_id}' ({faiss_index.ntotal} vectors).")
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS index for repository '{repository_id}': {e}")
            return False

    def delete_index(self, repository_id: str) -> bool:
        """Deletes persistent FAISS index and removes in-memory index cache."""
        repo_dir = self._get_repo_dir(repository_id)
        if repository_id in self._indices:
            del self._indices[repository_id]

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir, ignore_errors=True)
            logger.info(f"Deleted persistent FAISS index for repository '{repository_id}'.")
            return True
        return False


vector_store_service = VectorStoreService()


def get_vector_store_service() -> VectorStoreService:
    return vector_store_service
