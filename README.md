# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot allows developers to provide any GitHub repository URL, automatically analyze and index the codebase, and ask natural-language questions with grounded code answers and precise file & line citations.

---

## ⚡ Phase 5: Embeddings & FAISS Vector Storage

Phase 5 converts code-aware chunks into vector embeddings and stores them in isolated, persistent FAISS indexes.

### Pipeline Architecture
```
Chunks (Phase 4)
   │
   ▼
[BaseEmbeddingProvider] (Configurable: Mock / OpenAI / Sentence-Transformers)
   │
   ▼
[Vector Insertion & Normalization] (L2-normalized vectors for Cosine Similarity)
   │
   ▼
[FAISS Vector Store] (IndexFlatIP) + [Metadata Store] (metadata.json)
```

---

## 🛠️ Core Vector Store Services

- **`EmbeddingProvider` Abstraction**: Switch embedding models (`mock`, `openai`, `sentence-transformers`) via `EMBEDDING_PROVIDER` environment variable without rewriting the RAG pipeline.
- **Repository Isolation**: Each repository maintains its own isolated FAISS index (`storage/vector_indices/{repository_id}/index.faiss`) and separate metadata file (`metadata.json`).
- **Disk Persistence & Reloading**: Vector indices and metadata persist to disk and automatically reload on service restart or query.
- **Core Operations**:
  - `index_repository(repository_id, chunks)`
  - `search(repository_id, query, top_k)`
  - `load_index(repository_id)`
  - `delete_index(repository_id)`

---

## 🔒 Security & Edge Case Policies

1. **No Secret Leakage**: API keys (`OPENAI_API_KEY`) are read strictly from environment variables and never exposed in logs or API responses.
2. **Duplicate Indexing Safeguard**: Re-indexing a repository clean-rebuilds the FAISS index without creating duplicate entries.
3. **Empty Repositories**: Gracefully creates 0-vector FAISS indices without throwing errors.
4. **Batch Generation**: Embeddings are generated in configurable batches to prevent API rate limit issues.

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
