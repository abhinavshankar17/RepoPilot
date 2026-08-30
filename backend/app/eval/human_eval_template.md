# Human Evaluation Rubric Template

> **RepoPilot RAG Answer Quality Assessment**

This template provides a standardized rubric for developer human review of generated answers, source citations, and code flow explanations.

---

## 📋 Evaluation Criteria & Scoring (1 to 5 Scale)

| Metric | Score 1 (Poor) | Score 3 (Acceptable) | Score 5 (Excellent) |
| :--- | :--- | :--- | :--- |
| **Groundedness** | Fabricates non-existent code, files, or line numbers. | Minor ungrounded assumptions, mostly factual. | 100% grounded in retrieved repository code chunks. |
| **Correctness** | Incorrect technical explanation or wrong file location. | Partially correct, answers core question. | Completely accurate technical explanation. |
| **Citation Accuracy** | Wrong files or incorrect line ranges cited. | Relevant file cited, line range slightly offset. | Exact file, line range, and symbol cited correctly. |
| **Utility & Clarity** | Confusing, vague, or non-actionable response. | Understandable, helpful for basic navigation. | Clear, structured developer explanation with code snippets. |

---

## 📝 Evaluation Form

### Case ID: `__________________`
- **Question**: `__________________`
- **Target Repository**: `__________________`

### Evaluation Ratings:
- [ ] **Groundedness Score (1-5)**: `_____` / 5
- [ ] **Correctness Score (1-5)**: `_____` / 5
- [ ] **Citation Accuracy Score (1-5)**: `_____` / 5
- [ ] **Utility Score (1-5)**: `_____` / 5

### Evaluator Comments / Feedback:
```text
[Enter detailed reviewer notes, hallucinatory claims (if any), or line range accuracy notes]
```
