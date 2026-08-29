# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot allows developers to provide any GitHub repository URL, automatically analyze and index the codebase, and ask natural-language questions with grounded code answers and precise file & line citations.

---

## 🎯 Phase 7: Precise Source Citations & Safe Source Retrieval

Phase 7 guarantees that every generated answer is directly traceable to exact codebase files, line numbers, and symbols, and provides a secure file content inspection API.

### Citation Schema
```json
{
  "chunk_id": "src/middleware/auth.js:authenticateUser:12-31",
  "file_path": "src/middleware/auth.js",
  "symbol": "authenticateUser",
  "start_line": 12,
  "end_line": 31,
  "language": "JavaScript",
  "score": 0.9123,
  "snippet": "function authenticateUser(req, res) { ..."
}
```

---

## 🔒 Security & Source File Retrieval API

### Endpoint: `GET /repositories/{repository_id}/files/{file_path:path}`
Safely retrieves raw source code from an ingested repository with optional line range slicing (`?start_line=10&end_line=40`).

### Security Protections
1. **Path Traversal Guard**: Prevents path traversal attacks (`../`, `..\`) by validating that target files resolve strictly inside the isolated storage root (`storage/{repository_id}/`).
2. **Access Control**: Rejects requests attempting to access system files or files outside the repository boundary with `403 Forbidden`.
3. **Citation Grounding**: Prompt engineering constrains LLM output so citation metadata originates **strictly** from retrieved vector chunks header tags `[Chunk N: file_path Lstart-Lend]`.

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
