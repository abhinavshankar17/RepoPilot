# RepoPilot 🚀

> **RAG-powered Developer Documentation & Codebase Copilot**

RepoPilot allows developers to provide any GitHub repository URL, automatically analyze and index the codebase, and ask natural-language questions with grounded code answers and precise file & line citations.

---

## 🧠 Phase 12: Repository Intelligence

Phase 12 delivers 3 specialized developer intelligence services running on dedicated REST API endpoints:

### Feature 1 — Code Flow Analysis (`POST /repositories/{id}/flow`)
Traces execution flows across codebase layers: `Route → Controller → Service → Repository → Database`.
```json
{
  "flow_diagram": "Route → Controller → Service → Repository → Database",
  "steps": [
    {
      "step_number": 1,
      "layer": "Route",
      "file_path": "src/routes/order.js",
      "start_line": 10,
      "end_line": 25,
      "symbol": "createOrder"
    }
  ]
}
```

---

### Feature 2 — Impact Analysis (`POST /repositories/{id}/impact`)
Identifies downstream modification impacts across imports, references, function calls, dependent modules, and API routes.
```json
{
  "target": "User.js",
  "summary": "Modifying 'User.js' could impact 4 downstream module(s)...",
  "impacts": [
    {
      "category": "Imports",
      "file_path": "src/controllers/userController.js",
      "description": "File 'src/controllers/userController.js' explicitly imports 'User.js'."
    }
  ]
}
```

---

### Feature 3 — Change Planning (`POST /repositories/{id}/change-plan`)
Generates structured change recommendations for proposed features (e.g. `"Add Google OAuth"`) while strictly distinguishing **Verified Code Evidence** from **LLM Recommendations**.
```json
{
  "proposed_feature": "I want to add Google OAuth",
  "evidence_found": "Verified repository evidence:\n[1] File 'src/middleware/auth.js'...",
  "recommendations": [
    {
      "file_path": "src/middleware/auth.js",
      "reason": "Integrate Google OAuth handlers into existing auth implementation.",
      "confidence": "High",
      "is_new_file": false
    },
    {
      "file_path": "src/config/oauth.js",
      "reason": "Create new OAuth client configuration module.",
      "confidence": "High",
      "is_new_file": true
    }
  ]
}
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
