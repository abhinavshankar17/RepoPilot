# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot allows developers to provide any GitHub repository URL, automatically analyze and index the codebase, and ask natural-language questions with grounded code answers and precise file & line citations.

---

## 📈 Phase 14: RAG Evaluation Framework

Phase 14 delivers a scientific evaluation framework to measure retrieval accuracy, generation quality, groundedness, and end-to-end system latencies.

### Evaluation Benchmark Dataset (`app/eval/benchmark.json`)
Each test case contains:
```json
{
  "id": "eval-1",
  "question": "Where is authentication implemented?",
  "expected_files": ["src/middleware/auth.js"],
  "expected_symbols": ["authenticateUser"],
  "expected_lines": [12, 31]
}
```

---

## 📊 Measured Evaluation Results

Command: `python app/eval/run_eval.py`

### Retrieval & Generation Metrics
| Strategy | Recall@1 | Recall@5 | Recall@10 | Precision@5 | MRR | Citation Accuracy | Response Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Vector-only** | `0.3667` | `0.4167` | `0.4167` | `0.2000` | `0.8500` | `0.2000` | `0.61 ms` |
| **Hybrid (Vector + BM25)** | `0.3667` | `0.4167` | `0.4167` | `0.2000` | `0.8667` | `0.2000` | `0.36 ms` |
| **Hybrid + Reranking** | `0.2667` | `0.4167` | `0.4167` | `0.2000` | `0.7333` | `0.2000` | `0.28 ms` |

### Machine-Readable Results File
Saved to [`eval_results.json`](file:///c:/Users/abhin/OneDrive/Desktop/Projects/RepoPilot/backend/eval_results.json).

### Human Evaluation Rubric
Refer to the standardized developer assessment rubric in [`human_eval_template.md`](file:///c:/Users/abhin/OneDrive/Desktop/Projects/RepoPilot/backend/app/eval/human_eval_template.md).

---

## ⚠️ System Limitations & Benchmark Notes

1. **Synthetic & Offline Test Provider**: Evaluation metrics are measured using deterministic mock embedding and completion providers for reproducibility without external API key dependencies.
2. **Small Benchmark Corpus**: The evaluation dataset contains 5 gold-standard ground-truth queries; scaling to large production codebases can be done by appending cases to `app/eval/benchmark.json`.

---

## 🧪 Verification & Test Commands

### Backend Pytest Suite:
```bash
cd backend
python -m pytest
```

### Run RAG Evaluation Runner:
```bash
cd backend
python app/eval/run_eval.py
```

### Frontend Production Build:
```bash
cd frontend
npm run build
```

---

## 💻 Running RepoPilot Locally

### 1. Start Backend API Server:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Start Frontend Dev Server:
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.
