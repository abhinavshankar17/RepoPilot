from typing import List, Dict, Tuple, Any, Optional
from app.schemas.chunk import CodeChunk
from app.schemas.query import Citation, QueryResponse
from app.services.repository_service import RepositoryService, get_repository_service
from app.services.vector_store import VectorStoreService, get_vector_store_service
from app.retrieval.hybrid_retriever import HybridRetriever, get_hybrid_retriever
from app.retrieval.query_rewriter import QueryRewriter, get_query_rewriter
from app.services.session_service import SessionService, get_session_service
from app.services.llm_service import BaseLLMProvider, get_llm_provider
from app.core.logging import logger


class RAGService:
    """Service orchestrating session management, query rewriting, hybrid context retrieval, LLM generation, and source mapping."""

    SYSTEM_PROMPT = (
        "You are RepoPilot, an expert AI assistant specializing in analyzing codebase repositories.\n"
        "Your task is to answer questions about the codebase strictly using the provided context chunks.\n"
        "\n"
        "STRICT CITATION AND GROUNDING CONSTRAINTS:\n"
        "1. Base your answer ONLY on the code chunks provided below.\n"
        "2. Do NOT fabricate or invent file names, line numbers, or code symbols.\n"
        "3. All citation metadata MUST originate directly from the supplied context headers ([Chunk N: file_path Lstart-Lend]).\n"
        "4. If the provided context does NOT contain enough information to answer the question, state explicitly:\n"
        "   'The provided repository context does not contain sufficient information to answer your question.'\n"
        "5. Always reference the exact source file path and line numbers when explaining code functionality."
    )

    def __init__(
        self,
        repo_service: Optional[RepositoryService] = None,
        vector_store_svc: Optional[VectorStoreService] = None,
        hybrid_retriever: Optional[HybridRetriever] = None,
        query_rewriter: Optional[QueryRewriter] = None,
        session_service: Optional[SessionService] = None,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        self.repo_service = repo_service or get_repository_service()
        self.vector_store_svc = vector_store_svc or get_vector_store_service()
        self.hybrid_retriever = hybrid_retriever or get_hybrid_retriever()
        self.query_rewriter = query_rewriter or get_query_rewriter()
        self.session_svc = session_service or get_session_service()
        self.llm_provider = llm_provider or get_llm_provider()

    @classmethod
    def build_context_string(cls, chunks_with_scores: List[Tuple[CodeChunk, float]]) -> str:
        """Formats retrieved code chunks into a structured LLM context string."""
        if not chunks_with_scores:
            return "NO CONTEXT AVAILABLE."

        context_parts = []
        for idx, (chunk, score) in enumerate(chunks_with_scores, start=1):
            parent_info = f" (Parent: {chunk.parent_symbol})" if chunk.parent_symbol else ""
            imports_info = f"\nImports Context: {', '.join(chunk.imports)}" if chunk.imports else ""

            header = f"[Chunk {idx}: {chunk.file_path} L{chunk.start_line}-L{chunk.end_line}]"
            meta = f"Language: {chunk.language} | Symbol: {chunk.symbol_name} ({chunk.symbol_type}){parent_info} | Score: {score:.4f}{imports_info}"
            body = f"Code Content:\n{chunk.content}"

            context_parts.append(f"{header}\n{meta}\n{body}")

        return "\n\n".join(context_parts)

    @classmethod
    def build_user_prompt(cls, query: str, context_str: str) -> str:
        """Constructs the user prompt containing query and retrieved codebase context."""
        return (
            f"User Question: {query}\n\n"
            f"Retrieved Codebase Context:\n"
            f"============================\n"
            f"{context_str}\n"
            f"============================\n\n"
            f"Provide a clear, grounded technical explanation referencing the source files and lines above."
        )

    @classmethod
    def map_sources(cls, chunks_with_scores: List[Tuple[CodeChunk, float]]) -> List[Citation]:
        """Maps retrieved chunks to precise citation source metadata."""
        sources = []
        for chunk, score in chunks_with_scores:
            snippet_text = chunk.content[:350] + ("..." if len(chunk.content) > 350 else "")
            sources.append(Citation(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                symbol=chunk.symbol_name,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                language=chunk.language,
                score=round(score, 4),
                snippet=snippet_text
            ))
        return sources

    def answer_question(
        self,
        repo_id: str,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5
    ) -> QueryResponse:
        """Executes RAG generation pipeline with session history resolution and query rewriting."""
        repo = self.repo_service.get_repository_by_id(repo_id)
        if not repo:
            raise KeyError(f"Repository with ID '{repo_id}' not found.")

        # 1. Manage session ID and retrieve bounded history
        active_session_id = self.session_svc.get_or_create_session_id(session_id)
        history = self.session_svc.get_recent_history(active_session_id)

        # 2. Rewrite query if follow-up
        rewritten_q = self.query_rewriter.rewrite_query(query, history)
        logger.info(f"RAG query processing: repo_id='{repo_id}', session_id='{active_session_id}', original='{query}', rewritten='{rewritten_q}'")

        # 3. Perform hybrid retrieval using rewritten_query
        retrieved_tuples = self.hybrid_retriever.retrieve(repo_id, rewritten_q, top_k=top_k, strategy="hybrid_rerank")
        chunks_with_scores = [(chunk, diag.get("reranker_score", diag.get("vector_score", 0.0))) for chunk, diag in retrieved_tuples]

        # 4. Build context string and user prompt
        context_str = self.build_context_string(chunks_with_scores)
        user_prompt = self.build_user_prompt(rewritten_q, context_str)

        # 5. Generate LLM completion or insufficient context fallback
        if not chunks_with_scores:
            answer = "The provided repository context does not contain sufficient information to answer your question."
            sources = []
        else:
            answer = self.llm_provider.generate(user_prompt, system_prompt=self.SYSTEM_PROMPT)
            sources = self.map_sources(chunks_with_scores)

        # 6. Save turn to session history
        self.session_svc.add_turn(active_session_id, query, answer)

        return QueryResponse(
            repository_id=repo_id,
            session_id=active_session_id,
            original_query=query,
            rewritten_query=rewritten_q,
            answer=answer,
            citations=sources
        )


rag_service = RAGService()


def get_rag_service() -> RAGService:
    return rag_service
