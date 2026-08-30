import time
from typing import Dict, Any
from contextlib import contextmanager


class LatencyProfiler:
    """Measures precise execution latencies across RAG pipeline stages."""

    def __init__(self):
        self.metrics: Dict[str, float] = {
            "indexing_time_ms": 0.0,
            "embedding_time_ms": 0.0,
            "retrieval_latency_ms": 0.0,
            "reranking_latency_ms": 0.0,
            "llm_latency_ms": 0.0,
            "total_response_latency_ms": 0.0,
        }

    @contextmanager
    def measure(self, stage_name: str):
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.metrics[stage_name] = round(elapsed_ms, 2)

    def get_summary(self) -> Dict[str, float]:
        return dict(self.metrics)
