# RepoPilot Project Overview & Technical Architecture

RepoPilot is an end-to-end RAG-powered Developer Documentation and Codebase Copilot. It converts source code repositories into structured, retrievable, code-aware indices to provide grounded answers with exact file and line citations.

---

## 🏗️ 1. System Architecture

RepoPilot follows a decoupled, 3-tier microservice architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React 18 + Tailwind v4 UI                       │
│      (3-Panel Layout: File Tree, AI Chat with History, Code Viewer)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST
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

## 🧠 2. RAG Architecture

```
User Query
   │
   ▼
[Query Understanding & Session Memory] (Resolves ambiguous follow-up pronouns)
   │
   ▼
┌─────────────────────────────────────────┐
│        Hybrid Retrieval Engine          │
│ ┌─────────────────┐   ┌───────────────┐ │
│ │ Dense FAISS Flat│ + │ BM25 Keyword  │ │
│ └────────┬────────┘   └───────┬───────┘ │
└──────────┼────────────────────┼─────────┘
           └──────────┬─────────┘
                      ▼
           [Reciprocal Rank Fusion (RRF)]
                      │
                      ▼
        [Cross-Encoder Reranker Engine]
                      │
                      ▼
┌─────────────────────────────────────────┐
│      Structured Context Construction    │
│  + Anti-Hallucination Grounding Prompt  │
└─────────────────────┬───────────────────┘
                      │
                      ▼
              [LLM Generator]
                      │
                      ▼
     Answer + Precise Citations (Path, Symbol, Line Range)
```

---

## ⚡ 3. Ingestion & Code Parsing Pipeline

1. **Git Ingestion & Scanning**: Clones GitHub repositories with `--depth=1`. Scans directories ignoring binary assets, lockfiles, and `node_modules` while enforcing a 1MB file size limit.
2. **AST Parsing & AST Symbol Extraction**: Uses tree-sitter regex parsing to extract functions, classes, methods, imports, parameters, decorators, API routes, line ranges, and parent-child symbol relationships.
3. **Code-Aware Chunking**: Chunks strictly according to AST code boundaries (`function`, `class`, `module`) preserving line metadata instead of using fixed-size token splitting.
4. **FAISS Vector Indexing**: Generates L2-normalized embeddings stored in repository-isolated FAISS indices.
5. **Relationship Graph Construction**: Extracts structural graph nodes and edges (`IMPORTS`, `CALLS`, `DEFINES`, `EXTENDS`, `IMPLEMENTS`, `USES`, `ROUTES_TO`).

---

## 🔎 4. Retrieval & Reranking Pipeline

1. **Dense Vector Search**: Computes dot-product cosine similarity over FAISS flat IP indices.
2. **Sparse Keyword Search**: Okapi BM25 ranking tokenizing code identifiers.
3. **Reciprocal Rank Fusion (RRF)**: Combines dense vector and sparse BM25 ranks.
4. **Cross-Encoder Reranking**: Re-scores top candidates using cross-encoder relevance modeling.

---

## 🛠️ 5. Important Engineering Decisions & Trade-offs

1. **Deterministic AST Chunking vs Fixed-Token Splitting**:
   - *Decision*: Chunk strictly on code symbols (functions, classes).
   - *Trade-off*: Prevents syntax truncation and context fragmentation, though very large functions require secondary split logic.

2. **In-Memory Relationship Graph vs Neo4j**:
   - *Decision*: Implemented pure Python `RepositoryGraph` persisted as JSON.
   - *Trade-off*: Eliminates heavy Neo4j deployment dependencies while providing fast call-chain tracing for small to medium repositories.

3. **Strict Path Traversal Guard**:
   - *Decision*: Enforces `os.path.commonpath` validation on all file retrieval requests.
   - *Trade-off*: Blocks path traversal attacks (`../../etc/passwd`) while safely serving codebase files to the UI Code Explorer.

---

## ⚠️ 6. Known System Limitations

1. **Sub-symbol Splitting for Monolithic Files**: Files lacking explicit class/function definitions (e.g. single 5,000 line scripts) default to module chunking.
2. **Offline Mock Providers**: By default, evaluation tests run with offline mock embedding and completion providers for keyless reproducibility.
