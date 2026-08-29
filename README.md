# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot allows developers to provide any GitHub repository URL, automatically analyze and index the codebase, and ask natural-language questions with grounded code answers and precise file & line citations.

---

## ⚡ Phase 8: Advanced Hybrid Retrieval & Reranking

Phase 8 upgrades the retrieval pipeline from single-stage vector search to a multi-stage Hybrid Retrieval system combining FAISS Vector Search, BM25 Keyword Search, Reciprocal Rank Fusion (RRF), and Cross-Encoder Reranking.

### Multi-Stage Retrieval Flow
```
User Query
    │
    ▼
[CodeTokenizer] (camelCase & snake_case identifier expansion)
    │
 ┌──┴────────────────────────┐
 │ Vector Search (FAISS)     │  (Semantic similarity)
 │ BM25 Keyword Search       │  (Exact symbol & identifier matching)
 └──┬────────────────────────┘
    │
    ▼
[Reciprocal Rank Fusion (RRF)] RRF(d) = 1/(60 + r_vec) + 1/(60 + r_bm25)
    │
    ▼
[Cross-Encoder Reranker] (Reranks candidates by exact symbol, coverage & structure)
    │
    ▼
[Top K Context] (Attaches vector_score, keyword_score, reranker_score, final_rank)
    │
    ▼
[Grounded LLM Answer + Source Citations]
```

---

## 📊 Measured Retrieval Benchmark Metrics

Evaluated using `python scratch/eval_retrieval.py` on exact code queries (e.g. `"Where is authenticateUser defined?"`) and semantic queries (e.g. `"Where do we verify a user's identity?"`):

| Retrieval Strategy | MRR (Mean Reciprocal Rank) | Hit Rate @ 1 | Hit Rate @ 3 |
| :--- | :---: | :---: | :---: |
| **Vector-only** | `0.5333` | `20.0%` | `100.0%` |
| **Hybrid (Vector + BM25)** | `0.9000` | `80.0%` | `100.0%` |
| **Hybrid + Reranking (Vector + BM25 + Cross-Encoder)** | **`1.0000`** | **`100.0%`** | **`100.0%`** |

---

## 🔍 Retrieval Diagnostics

Every retrieved chunk includes full diagnostic scoring transparency in metadata:
- `vector_score`: FAISS L2-normalized inner product score
- `keyword_score`: BM25 Okapi term frequency score
- `fusion_score`: Reciprocal Rank Fusion (RRF) combined score
- `reranker_score`: Cross-encoder reranker score
- `final_rank`: Final contextual rank (1..K)

---

## 🧪 Running Unit Tests

```bash
cd backend
python -m pytest
```

---

## 💻 Running the Services

### Backend:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend:
```bash
cd frontend
npm install
npm run dev
```
