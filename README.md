# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot allows developers to provide any GitHub repository URL, automatically analyze and index the codebase, and ask natural-language questions with grounded code answers and precise file & line citations.

---

## 🏗️ Phase 1 Backend Architecture

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py        # GET /health
│   │   │   ├── repositories.py  # POST /repositories, GET /repositories, GET /repositories/{id}
│   │   │   └── query.py         # POST /repositories/{id}/query
│   │   └── router.py
│   ├── core/
│   │   ├── config.py            # Pydantic BaseSettings (.env integration)
│   │   └── logging.py           # Structured logging setup
│   ├── schemas/
│   │   ├── health.py            # Health check response model
│   │   ├── repository.py        # Repository request/response Pydantic models
│   │   └── query.py             # Query & citation Pydantic models
│   ├── services/
│   │   ├── repository_service.py # Business logic & dependency injection
│   │   └── query_service.py      # Business logic & query processing
│   ├── rag/                     # RAG pipeline modules (Phase 2+)
│   ├── utils/                   # Shared helpers
│   └── main.py                  # FastAPI entry point & CORS
├── tests/
│   ├── test_health.py           # Health endpoint tests
│   ├── test_repositories.py     # Repository CRUD & validation tests
│   └── test_query.py            # Query endpoint tests
├── pyproject.toml
└── requirements.txt
```

---

## 📡 API Endpoints

- `GET /health`: Operational health status.
- `POST /repositories`: Register and trigger ingestion for a GitHub repository.
- `GET /repositories`: List registered repositories.
- `GET /repositories/{repository_id}`: Retrieve repository details by ID.
- `POST /repositories/{repository_id}/query`: Natural language query for a specific repository.

---

## 🚀 Running the Backend

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Launch FastAPI Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```
Interactive OpenAPI documentation will be available at `http://127.0.0.1:8000/docs`.

### 3. Run Backend Tests

```bash
cd backend
python -m pytest
```

---

## 💻 Running the Frontend

> **Note**: Always run `npm` commands inside the `frontend/` directory!

```bash
cd frontend
npm install
npm run dev
```
Access UI at `http://localhost:5173`.
