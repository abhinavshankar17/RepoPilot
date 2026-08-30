# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot allows developers to provide any GitHub repository URL, automatically analyze and index the codebase, and ask natural-language questions with grounded code answers and precise file & line citations.

---

## 🕸️ Phase 13: Repository Relationship Graph

Phase 13 introduces a lightweight, in-memory directed relationship graph to complement FAISS vector embeddings with deterministic AST structural dependencies.

### Supported Edge Relationships
- `IMPORTS`: File importing a module or source file
- `CALLS`: Function or method invoking another symbol
- `DEFINES`: File defining a class, function, or interface
- `EXTENDS`: Class extending a parent class
- `IMPLEMENTS`: Class implementing an interface
- `USES`: Controller/Service utilizing a repository or database module
- `ROUTES_TO`: API route mapping to a controller handler function

```
[auth.js] ──DEFINES──> [authenticateUser()] ──CALLS──> [verifyToken()]
   │                                                        ▲
   └──────────────IMPORTS───────────────────────────────────┘
```

---

## 🔒 Evidence Demarcation Policy

RepoPilot explicitly demarcates evidence sources in intelligence reports:
- **Vector Evidence**: Semantic similarity candidates retrieved from FAISS vector indices.
- **Relationship/Graph Evidence**: Deterministic AST dependency edges (`IMPORTS`, `CALLS`, `DEFINES`, `EXTENDS`, `IMPLEMENTS`, `USES`, `ROUTES_TO`).

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
