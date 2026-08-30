from typing import List, Set, Dict, Any
from app.schemas.query import Citation


def compute_recall(retrieved_files: List[str], expected_files: List[str], k: int) -> float:
    """Computes Recall@K metric."""
    if not expected_files:
        return 1.0
    top_k = retrieved_files[:k]
    matches = set(top_k).intersection(set(expected_files))
    return len(matches) / len(expected_files)


def compute_precision(retrieved_files: List[str], expected_files: List[str], k: int) -> float:
    """Computes Precision@K metric."""
    if k == 0 or not retrieved_files:
        return 0.0
    top_k = retrieved_files[:k]
    matches = set(top_k).intersection(set(expected_files))
    return len(matches) / len(top_k)


def compute_mrr(retrieved_files: List[str], expected_files: List[str]) -> float:
    """Computes Mean Reciprocal Rank (MRR)."""
    expected_set = set(expected_files)
    for rank, file_path in enumerate(retrieved_files, start=1):
        if file_path in expected_set:
            return 1.0 / rank
    return 0.0


def compute_citation_accuracy(citations: List[Citation], expected_files: List[str]) -> float:
    """Computes percentage of generated citations matching expected files."""
    if not citations:
        return 0.0
    expected_set = set(f.lower() for f in expected_files)
    valid_citations = sum(1 for c in citations if any(exp in c.file_path.lower() for exp in expected_set))
    return valid_citations / len(citations)


def compute_faithfulness(answer: str, context_str: str) -> float:
    """Estimates faithfulness/groundedness score based on context overlap."""
    if not answer or not context_str:
        return 0.0
    if "does not contain sufficient information" in answer:
        return 1.0
    answer_words = set(answer.lower().split())
    context_words = set(context_str.lower().split())
    overlap = answer_words.intersection(context_words)
    return round(len(overlap) / max(1, len(answer_words)), 4)


def compute_answer_relevance(answer: str, question: str) -> float:
    """Estimates answer relevance score based on question term coverage."""
    if not answer or not question:
        return 0.0
    q_words = set(w.lower() for w in question.split() if len(w) > 3)
    if not q_words:
        return 1.0
    ans_lower = answer.lower()
    matches = sum(1 for w in q_words if w in ans_lower)
    return round(matches / len(q_words), 4)
