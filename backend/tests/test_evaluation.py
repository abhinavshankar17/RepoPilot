import os
import pytest
from app.eval.metrics import (
    compute_recall,
    compute_precision,
    compute_mrr,
    compute_citation_accuracy,
    compute_faithfulness,
    compute_answer_relevance,
)
from app.eval.profiler import LatencyProfiler
from app.eval.run_eval import run_evaluation
from app.schemas.query import Citation


def test_metric_calculations():
    retrieved = ["src/auth.py", "src/user.py", "src/db.py"]
    expected = ["src/auth.py"]

    assert compute_recall(retrieved, expected, k=1) == 1.0
    assert compute_recall(retrieved, expected, k=3) == 1.0
    assert compute_precision(retrieved, expected, k=1) == 1.0
    assert compute_precision(retrieved, expected, k=3) == 1 / 3
    assert compute_mrr(retrieved, expected) == 1.0

    retrieved_miss = ["src/other.py", "src/auth.py"]
    assert compute_mrr(retrieved_miss, expected) == 0.5


def test_citation_accuracy_and_groundedness():
    citations = [
        Citation(
            chunk_id="c1",
            file_path="src/auth.py",
            symbol="auth",
            start_line=1,
            end_line=10,
            language="Python",
            score=0.9,
            snippet="def auth(): pass"
        )
    ]
    acc = compute_citation_accuracy(citations, ["src/auth.py"])
    assert acc == 1.0

    faith = compute_faithfulness("JWT authentication is used in src/auth.py", "JWT authentication is used in src/auth.py")
    assert faith > 0.5

    relev = compute_answer_relevance("Authentication is in src/auth.py", "Where is authentication implemented?")
    assert relev > 0.0


def test_latency_profiler():
    profiler = LatencyProfiler()
    with profiler.measure("retrieval_latency_ms"):
        sum(range(1000))

    summary = profiler.get_summary()
    assert "retrieval_latency_ms" in summary
    assert summary["retrieval_latency_ms"] >= 0.0


def test_run_evaluation_machine_readable_output():
    results = run_evaluation()

    assert "evaluation_timestamp" in results
    assert "benchmark_dataset_size" in results
    assert "system_latencies" in results
    assert "strategies" in results

    assert "vector_only" in results["strategies"]
    assert "hybrid" in results["strategies"]
    assert "hybrid_rerank" in results["strategies"]

    # Verify machine-readable JSON file exists on disk
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_path = os.path.join(backend_dir, "eval_results.json")
    assert os.path.isfile(json_path)
