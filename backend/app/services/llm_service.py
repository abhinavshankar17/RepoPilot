from abc import ABC, abstractmethod
from typing import List, Tuple
from app.services.chunker_service import CodeChunk
from app.models.schemas import Citation
from app.core.config import settings
from app.core.logging import logger


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_answer(self, query: str, context_chunks: List[CodeChunk]) -> Tuple[str, List[Citation]]:
        pass


class MockLLMProvider(BaseLLMProvider):
    """Fallback / Mock LLM provider that synthesizes answers directly from retrieved codebase context."""

    def generate_answer(self, query: str, context_chunks: List[CodeChunk]) -> Tuple[str, List[Citation]]:
        if not context_chunks:
            return (
                "I couldn't find any relevant code snippets in the repository to answer your question.",
                []
            )

        citations: List[Citation] = []
        summary_parts: List[str] = []

        for chunk in context_chunks:
            citations.append(Citation(
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                snippet=chunk.text[:250] + ("..." if len(chunk.text) > 250 else "")
            ))
            summary_parts.append(f"- [{chunk.file_path} L{chunk.start_line}-L{chunk.end_line}]")

        files_summary = "\n".join(summary_parts[:3])
        answer = (
            f"Based on the analysis of the codebase for query **'{query}'**, the implementation is located across key modules:\n\n"
            f"{files_summary}\n\n"
            f"Refer to the source citations below for line-by-line inspection details."
        )

        return answer, citations


def get_llm_provider() -> BaseLLMProvider:
    return MockLLMProvider()
