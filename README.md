# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot allows developers to provide any GitHub repository URL, automatically analyze and index the codebase, and ask natural-language questions with grounded code answers and precise file & line citations.

---

## 🧩 Phase 3: Code Parsing & AST Analysis

RepoPilot analyzes code structure using AST parsing instead of treating source files as plain text.

### Modular Parser Architecture
- [`BaseLanguageParser`](file:///c:/Users/abhin/OneDrive/Desktop/Projects/RepoPilot/backend/app/parsers/base.py): Abstract base class interface.
- [`PythonASTParser`](file:///c:/Users/abhin/OneDrive/Desktop/Projects/RepoPilot/backend/app/parsers/python_parser.py): Native AST parser using Python's built-in `ast` module. Extracts classes, methods, functions, decorators, parameters, API routes (`@app.get`, `@router.post`), and line ranges.
- [`JSTSParser`](file:///c:/Users/abhin/OneDrive/Desktop/Projects/RepoPilot/backend/app/parsers/js_ts_parser.py): JavaScript / TypeScript parser extracting classes, interfaces, constructors, methods, arrow functions, exported functions, parameters, imports, and parent class relationships.
- [`GenericLanguageParser`](file:///c:/Users/abhin/OneDrive/Desktop/Projects/RepoPilot/backend/app/parsers/generic_parser.py): Parser for Java, Go, Rust, and C/C++.
- [`FallbackParser`](file:///c:/Users/abhin/OneDrive/Desktop/Projects/RepoPilot/backend/app/parsers/fallback_parser.py): Plain text fallback preserving file content in blocks when AST parsing fails or file format is unstructured.
- [`ParserRegistry`](file:///c:/Users/abhin/OneDrive/Desktop/Projects/RepoPilot/backend/app/parsers/registry.py): Centralized registry routing files to appropriate language parsers.

### Normalized `CodeSymbol` JSON Representation
```json
{
  "repository_id": "repo-123",
  "file_path": "src/middleware/auth.js",
  "language": "JavaScript",
  "symbol_type": "method",
  "symbol_name": "createUser",
  "start_line": 8,
  "end_line": 11,
  "content": "async createUser(req, res) { ... }",
  "parent_symbol": "UserController",
  "parameters": ["req", "res"],
  "decorators": [],
  "metadata": {}
}
```

---

## 🔒 Security & Protection Policies

1. **Sandboxed AST Analysis**: Static analysis only — **NEVER** executes or imports repository code.
2. **Graceful Failures**: If AST parsing encounters syntax errors, it gracefully falls back to plain text blocks without crashing.
3. **Accurate Line Ranges**: Preserves exact 1-indexed `start_line` and `end_line` metadata.

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
