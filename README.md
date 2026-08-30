# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot is an advanced developer tool that ingests GitHub repositories, parses source code using AST structure, indexes code-aware chunks in FAISS, and provides natural-language answers with exact file paths, symbol names, and line range citations.

---

## 📌 1. Problem Statement

Navigating complex or unfamiliar codebases requires manual search, constant context switching, and piecing together outdated documentation. Generic LLM chat assistants fail on codebase queries because they hallucinate non-existent files, invent arbitrary line numbers, and lack awareness of repository-specific AST structures.

RepoPilot solves this by combining AST structural parsing, hybrid vector + keyword retrieval, reranking, relationship graphs, and anti-hallucination prompts.

---

## ✨ 2. Key Features

- 📂 **AST Code Parsing & Code-Aware Chunking**: Chunks code by functions, classes, and modules instead of naive token splitting.
- ⚡ **Hybrid Retrieval Engine**: Combines dense FAISS vector search with Okapi BM25 keyword search via Reciprocal Rank Fusion (RRF).
- 🎯 **Cross-Encoder Reranking**: Re-ranks top candidates for exact identifier matching.
- 💬 **Conversation Context & Follow-Up Rewriting**: Session memory rewrites ambiguous follow-up questions ("Where is the token generated?") into standalone queries.
- 🧠 **Repository Intelligence**:
  - **Code Flow**: Traces `Route → Controller → Service → Repository → Database`.
  - **Impact Analysis**: Identifies modification impacts across imports, calls, and routes.
  - **Change Planning**: Recommends file edits while separating code evidence from LLM inferences.
- 🕸️ **Repository Relationship Graph**: Maps `IMPORTS`, `CALLS`, `DEFINES`, `EXTENDS`, `IMPLEMENTS`, `USES`, and `ROUTES_TO`.
- 🖥️ **Integrated Code Explorer**: 3-panel React UI with auto-scroll and cited line range highlighting.
- 🔒 **Production Security & Multi-Tenancy**: JWT authentication, RBAC (`user`/`admin`), multi-tenant repository isolation, SSRF URL validation, and path traversal protection.

---

## 🏗️ 3. Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React 18 Developer UI                           │
│     (Left: File Tree | Center: AI Chat | Right: Code Inspector)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST API
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend Core                          │
│ ┌───────────────────────┬──────────────────────┬─────────────────────┐ │
│ │  Repository Service   │     RAG Service      │ Intelligence Svc    │ │
│ └───────────┬───────────┴──────────┬───────────┴──────────┬──────────┘ │
│             │                      │                      │            │
│             ▼                      ▼                      ▼            │
│ ┌───────────────────────┐┌────────────────────┐┌────────────────────┐ │
│ │ AST Parser & Chunker  ││  Hybrid Retriever  ││ Relationship Graph │ │
│ └───────────────────────┘└────────────────────┘└────────────────────┘ │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Persistence
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Storage & Data Persistence                      │
│ ┌─────────────────────┐ ┌────────────────────┐ ┌────────────────────┐ │
│ │  FAISS Vector Store │ │  Repository Storage│ │ PostgreSQL / Redis │ │
│ └─────────────────────┘ └────────────────────┘ └────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 4. RAG Pipeline

1. **User Query Input**: Session service receives query and conversation history.
2. **Query Rewriting**: Ambiguous follow-ups are rewritten into self-contained search queries.
3. **Hybrid Search**: Retrieves candidates via FAISS vector similarity + Okapi BM25 keyword matching.
4. **Candidate Fusion & Reranking**: Reciprocal Rank Fusion (RRF) + Cross-Encoder re-scores candidates.
5. **Context Construction & Prompting**: Synthesizes prompt with retrieved code snippets and anti-hallucination rules.
6. **LLM Generation**: Produces answer accompanied by structured citation metadata (`file_path`, `symbol`, `start_line`, `end_line`).

---

## 🧩 5. Code Parsing Pipeline

```
GitHub Repo URL
   │
   ▼
[Git Clone & Directory Scanner] (Filters binary files, node_modules, >1MB files)
   │
   ▼
[Tree-Sitter / Regex AST Parser]
   │
   ├── Extracts: Functions, Classes, Methods, Imports, Routes, Line Ranges
   ├── Chunks: Function-level and Class-level boundaries
   └── Builds: Relationship Graph (IMPORTS, CALLS, DEFINES, USES, ROUTES_TO)
   │
   ▼
[FAISS Vector Store + Graph Storage Persistence]
```

---

## 💻 6. Tech Stack

- **Backend**: Python 3.13, FastAPI, Pydantic v2, Pytest, Uvicorn
- **Retrieval & RAG**: FAISS, rank-bm25, Cross-Encoder Reranker, Tree-Sitter
- **Database & Cache**: PostgreSQL 16, Redis 7
- **Frontend**: React 18, TypeScript, Tailwind CSS v4, Lucide Icons, Vite
- **Containerization**: Docker, Docker Compose, Nginx

---

## ⚙️ 7. Installation & Setup

### Prerequisites
- Docker & Docker Compose OR Python 3.13+ & Node.js 20+

### Quick Start with Docker Compose
```bash
# 1. Clone repository
git clone https://github.com/abhinavshankar17/RepoPilot.git
cd RepoPilot

# 2. Configure environment
cp .env.example .env

# 3. Launch services
docker-compose up -d --build
```
Access the application at `http://localhost`.

---

## 🔑 8. Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | Environment mode (`development` / `production`) |
| `JWT_SECRET` | `change-this-in-production...` | Secret key for signing JWT tokens |
| `LLM_PROVIDER` | `mock` | LLM backend (`mock` / `openai` / `ollama`) |
| `OPENAI_API_KEY` | `your-api-key` | OpenAI API key when using `openai` provider |
| `POSTGRES_HOST` | `postgres` | PostgreSQL hostname |
| `REDIS_HOST` | `redis` | Redis cache hostname |

---

## 📡 9. Key API Endpoints

- `POST /api/v1/repositories`: Ingest GitHub repository
- `GET /api/v1/repositories`: List ingested repositories
- `GET /api/v1/repositories/{id}/files/{file_path}`: Safe file retrieval with line slicing
- `POST /api/v1/repositories/{id}/query`: RAG query endpoint
- `POST /api/v1/repositories/{id}/flow`: Code Flow analysis (`Route → Controller → Database`)
- `POST /api/v1/repositories/{id}/impact`: Impact analysis for file/symbol modifications
- `POST /api/v1/repositories/{id}/change-plan`: Feature change recommendation planning

---

## ❓ 10. Example Questions

1. *"Explain the request flow for POST /api/orders."*
2. *"What could be affected if I modify auth.js?"*
3. *"I want to add Google OAuth. Which files would likely need modification?"*
4. *"Where is the token generated?"* (Follow-up query)

---

## 🖥️ 11. Developer Interface Overview

The React developer interface features a 3-panel layout:
- **Left Panel (File Explorer)**: Hierarchical file tree navigation.
- **Center Panel (AI Chat Panel)**: Conversational interface displaying Markdown responses, citations, and rewritten query badges.
- **Right Panel (Source Code Inspector)**: Integrated code viewer displaying syntax highlighting, symbol badges, line gutters, smooth auto-scroll, and cited range highlighting.

---

## 📊 12. Evaluation Methodology & Results

Measured using `python app/eval/run_eval.py` over a gold-standard benchmark dataset (`app/eval/benchmark.json`):

| Strategy | Recall@1 | Recall@5 | Recall@10 | Precision@5 | MRR | Response Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Vector-only** | `0.3667` | `0.4167` | `0.4167` | `0.2000` | `0.8500` | `0.61 ms` |
| **Hybrid (Vector + BM25)** | `0.3667` | `0.4167` | `0.4167` | `0.2000` | `0.8667` | `0.36 ms` |
| **Hybrid + Reranking** | `0.2667` | `0.4167` | `0.4167` | `0.2000` | `0.7333` | `0.28 ms` |

---

## 🔒 13. Security Considerations

1. **JWT & RBAC**: Role-based permissions (`user` vs `admin`).
2. **Multi-Tenant Repository Isolation**: Repositories scoped per owner (`storage/{owner_id}/{repo_id}/`).
3. **SSRF Defense**: Restricts GitHub cloning strictly to `https://github.com` URLs, blocking internal IP ranges.
4. **Path Traversal Protection**: Enforces strict `os.path.commonpath` verification.
5. **Zero Arbitrary Code Execution**: Static AST parsing only.

---

## ⚠️ 14. Known Limitations

- Monolithic single-file scripts lacking class/function signatures default to module-level chunking.
- Off-line evaluation defaults to keyless mock embedding providers.

---

## 🚀 15. Recommended Next Steps

- Integrate Tree-sitter native C-bindings for Rust / Go / C++ parsers.
- Add WebSocket support for streaming LLM response tokens.
- Add GitHub Webhook integration for automatic index updates on `git push`.
