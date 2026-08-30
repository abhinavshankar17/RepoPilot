import os
import sys
import json
import time
import shutil
import tempfile
from typing import List, Dict, Any

# Ensure backend path is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.schemas.chunk import CodeChunk
from app.services.embedding_service import MockEmbeddingProvider
from app.services.vector_store import VectorStoreService
from app.retrieval.hybrid_retriever import HybridRetriever
from app.services.rag_service import RAGService
from app.services.llm_service import MockLLMProvider
from app.eval.profiler import LatencyProfiler
from app.eval.metrics import (
    compute_recall,
    compute_precision,
    compute_mrr,
    compute_citation_accuracy,
    compute_faithfulness,
    compute_answer_relevance,
)


def load_benchmark_dataset() -> List[Dict[str, Any]]:
    benchmark_path = os.path.join(os.path.dirname(__file__), "benchmark.json")
    with open(benchmark_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_sample_chunks(repo_id: str) -> List[CodeChunk]:
    return [
        CodeChunk(
            chunk_id="c-auth",
            repository_id=repo_id,
            file_path="src/middleware/auth.js",
            language="JavaScript",
            symbol_type="function",
            symbol_name="authenticateUser",
            start_line=12,
            end_line=31,
            content="export function authenticateUser(req, res, next) { const token = req.headers.authorization; if (verifyToken(token)) return next(); }",
            imports=["import { verifyToken } from './jwt';"]
        ),
        CodeChunk(
            chunk_id="c-jwt",
            repository_id=repo_id,
            file_path="src/middleware/jwt.js",
            language="JavaScript",
            symbol_type="function",
            symbol_name="verifyToken",
            start_line=1,
            end_line=15,
            content="export function verifyToken(token) { return jwt.verify(token, secret); }",
            imports=["import jwt from 'jsonwebtoken';"]
        ),
        CodeChunk(
            chunk_id="c-db",
            repository_id=repo_id,
            file_path="src/db/connection.py",
            language="Python",
            symbol_type="function",
            symbol_name="init_db_connection",
            start_line=5,
            end_line=25,
            content="def init_db_connection(host, port):\n    return psycopg2.connect(host=host, port=port)",
            imports=["import psycopg2"]
        ),
        CodeChunk(
            chunk_id="c-user",
            repository_id=repo_id,
            file_path="src/controllers/user.js",
            language="JavaScript",
            symbol_type="function",
            symbol_name="createUser",
            start_line=10,
            end_line=40,
            content="export function createUser(req, res) { return db.users.insert(req.body); }",
            imports=[]
        ),
        CodeChunk(
            chunk_id="c-order",
            repository_id=repo_id,
            file_path="src/services/order.py",
            language="Python",
            symbol_type="class",
            symbol_name="OrderService",
            start_line=10,
            end_line=45,
            content="class OrderService:\n    def create_order(self, user_id, items):\n        pass",
            imports=[]
        )
    ]


def run_evaluation() -> Dict[str, Any]:
    temp_dir = tempfile.mkdtemp()
    try:
        repo_id = "eval-repo-001"
        profiler = LatencyProfiler()

        # 1. Profile Indexing & Embedding Latency
        with profiler.measure("indexing_time_ms"):
            vec_svc = VectorStoreService(base_dir=temp_dir, embedding_provider=MockEmbeddingProvider(dim=64))
            chunks = build_sample_chunks(repo_id)

            with profiler.measure("embedding_time_ms"):
                vec_svc.index_repository(repo_id, chunks)

        retriever = HybridRetriever(vector_store_svc=vec_svc)
        rag_svc = RAGService(vector_store_svc=vec_svc, hybrid_retriever=retriever, llm_provider=MockLLMProvider())
        benchmark = load_benchmark_dataset()

        strategies = ["vector_only", "hybrid", "hybrid_rerank"]
        results_by_strategy: Dict[str, Any] = {}

        for strat in strategies:
            r1_list, r5_list, r10_list = [], [], []
            p5_list, mrr_list = [], []
            cit_acc_list, faith_list, rel_list = [], [], []

            t_retrieval_ms, t_rerank_ms, t_llm_ms, t_total_ms = 0.0, 0.0, 0.0, 0.0

            for item in benchmark:
                q = item["question"]
                exp_files = item["expected_files"]

                start_total = time.perf_counter()

                # Retrieval
                start_ret = time.perf_counter()
                retrieved_tuples = retriever.retrieve(repo_id, q, top_k=10, strategy=strat)
                t_retrieval_ms += (time.perf_counter() - start_ret) * 1000.0

                retrieved_files = [c.file_path for c, _ in retrieved_tuples]

                # Compute Retrieval Metrics
                r1_list.append(compute_recall(retrieved_files, exp_files, k=1))
                r5_list.append(compute_recall(retrieved_files, exp_files, k=5))
                r10_list.append(compute_recall(retrieved_files, exp_files, k=10))
                p5_list.append(compute_precision(retrieved_files, exp_files, k=5))
                mrr_list.append(compute_mrr(retrieved_files, exp_files))

                # Generation & LLM Completion
                start_llm = time.perf_counter()
                chunks_with_scores = [(c, diag.get("reranker_score", 0.0)) for c, diag in retrieved_tuples[:5]]
                context_str = rag_svc.build_context_string(chunks_with_scores)
                user_prompt = rag_svc.build_user_prompt(q, context_str)
                answer = rag_svc.llm_provider.generate(user_prompt, system_prompt=rag_svc.SYSTEM_PROMPT)
                citations = rag_svc.map_sources(chunks_with_scores)
                t_llm_ms += (time.perf_counter() - start_llm) * 1000.0

                t_total_ms += (time.perf_counter() - start_total) * 1000.0

                cit_acc_list.append(compute_citation_accuracy(citations, exp_files))
                faith_list.append(compute_faithfulness(answer, context_str))
                rel_list.append(compute_answer_relevance(answer, q))

            num_q = len(benchmark)
            results_by_strategy[strat] = {
                "retrieval_metrics": {
                    "Recall@1": round(sum(r1_list) / num_q, 4),
                    "Recall@5": round(sum(r5_list) / num_q, 4),
                    "Recall@10": round(sum(r10_list) / num_q, 4),
                    "Precision@5": round(sum(p5_list) / num_q, 4),
                    "MRR": round(sum(mrr_list) / num_q, 4),
                },
                "generation_metrics": {
                    "CitationAccuracy": round(sum(cit_acc_list) / num_q, 4),
                    "Faithfulness": round(sum(faith_list) / num_q, 4),
                    "AnswerRelevance": round(sum(rel_list) / num_q, 4),
                },
                "latency_metrics": {
                    "retrieval_latency_ms": round(t_retrieval_ms / num_q, 2),
                    "llm_latency_ms": round(t_llm_ms / num_q, 2),
                    "total_response_latency_ms": round(t_total_ms / num_q, 2),
                }
            }

        final_output = {
            "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "benchmark_dataset_size": len(benchmark),
            "system_latencies": profiler.get_summary(),
            "strategies": results_by_strategy
        }

        # Save to machine-readable JSON output file
        output_file = os.path.join(backend_dir, "eval_results.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2)

        return final_output

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    res = run_evaluation()
    print("=== MEASURED RAG EVALUATION RESULTS ===")
    print(json.dumps(res, indent=2))
