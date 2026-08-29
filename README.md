# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot allows developers to provide any GitHub repository URL, automatically analyze and index the codebase, and ask natural-language questions with grounded code answers and precise file & line citations.

---

## 🖥️ Phase 10: React Developer Interface

Phase 10 delivers a 3-panel developer-tool UI tailored for code navigation, natural language codebase exploration, and source citation verification.

```
┌──────────────────────────────────────────────────────────┐
│ RepoPilot                         Repository: project ▼ │
├──────────────┬─────────────────────────┬─────────────────┤
│              │                         │                 │
│ File Explorer│       AI Chat           │    Sources      │
│              │                         │                 │
│ src/         │ User:                  │ auth.js         │
│ ├── api      │ How does auth work?    │ Lines 12–31     │
│ ├── models   │                         │                 │
│ ├── routes   │ AI response...         │ routes.js       │
│ └── services │                         │ Lines 44–57     │
│              │                         │                 │
└──────────────┴─────────────────────────┴─────────────────┘
```

### UI Features
1. **Header Bar**: Brand title, active repository dropdown selector, repository ingestion modal trigger, and API status indicator.
2. **Left Panel (File Explorer)**: Browses repository files with filter search, language badges, and direct selection.
3. **Center Panel (AI Chat)**:
   - Natural language codebase Q&A.
   - Multi-turn conversation history with session memory (`session_id`).
   - Markdown rendering (`react-markdown`) and code syntax formatting.
   - Context-resolved query rewriting indicator badge.
   - Suggested developer question shortcuts.
4. **Right Panel (Sources & Code Inspector)**:
   - **Tab 1 (Citations)**: Clickable source citation cards (`file_path`, `symbol`, `start_line`, `end_line`, `score`, `snippet`).
   - **Tab 2 (Code Inspector)**: Raw source code viewer fetched from backend (`GET /repositories/{id}/files/{file_path}`) with line range highlighting.

---

## 🛠️ Architecture Overview

```
React 18 + TypeScript + Vite
        │ (fetch API via src/services/api.ts)
        ▼
FastAPI Backend (app/main.py)
        │
        ├── Ingestion & Scanning (app/services/ingestion_service.py)
        ├── Code AST Parsers (app/parsers/)
        ├── Code-Aware Chunker (app/services/chunker_service.py)
        ├── FAISS Vector Store & Embeddings (app/services/vector_store.py)
        ├── Hybrid Retriever & Cross-Encoder Reranker (app/retrieval/)
        └── Grounded RAG Generator (app/services/rag_service.py)
```

---

## 🧪 Verification & Test Commands

### Backend Pytest Suite:
```bash
cd backend
python -m pytest
```

### Frontend Type Check & Production Build:
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
