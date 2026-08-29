from typing import List, Tuple, Dict, Optional
from rank_bm25 import BM25Okapi

from app.schemas.chunk import CodeChunk
from app.retrieval.tokenizer import CodeTokenizer
from app.core.logging import logger


class BM25Retriever:
    """BM25 Okapi keyword retriever for exact code symbol and keyword search."""

    def __init__(self, chunks: List[CodeChunk] = None):
        self.chunks: List[CodeChunk] = []
        self.bm25: Optional[BM25Okapi] = None
        if chunks:
            self.index_chunks(chunks)

    def index_chunks(self, chunks: List[CodeChunk]) -> None:
        """Indexes code chunks into BM25 Okapi search engine."""
        self.chunks = chunks
        if not chunks:
            self.bm25 = None
            return

        corpus_tokens = []
        for chunk in chunks:
            # Build search document text combining file path, symbol name, imports, and snippet content
            doc_text = f"{chunk.file_path} {chunk.symbol_name} {chunk.symbol_type} {chunk.parent_symbol or ''} {' '.join(chunk.imports)} {chunk.content}"
            tokens = CodeTokenizer.tokenize(doc_text)
            corpus_tokens.append(tokens)

        self.bm25 = BM25Okapi(corpus_tokens)
        logger.info(f"Indexed {len(chunks)} chunks into BM25 keyword retriever.")

    def search(self, query: str, top_k: int = 10) -> List[Tuple[CodeChunk, float]]:
        """Executes BM25 keyword search for query string."""
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = CodeTokenizer.tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results: List[Tuple[CodeChunk, float]] = []
        for idx in top_indices:
            results.append((self.chunks[idx], float(scores[idx])))

        return results
