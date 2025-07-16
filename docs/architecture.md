# System Architecture

## Overview

This document describes the high-level architecture of the platform, including its main components, data flow, and integration points.

---

## 1. **Component Diagram**

```
+-------------------+      +-------------------+      +-------------------+
|    Frontend (UI)  |<---->|    FastAPI App    |<---->|   Database/Cache  |
|  (React, Recharts)|      | (Python, Uvicorn) |      | (SQLite, Redis)   |
+-------------------+      +-------------------+      +-------------------+
         |                        |                          |
         |                        |                          |
         v                        v                          v
+-------------------+      +-------------------+      +-------------------+
|  Observability    |      |   Evaluation      |      | Performance       |
|  Dashboards       |      |   Dashboards      |      | Monitoring        |
+-------------------+      +-------------------+      +-------------------+
```

---

## 2. **Main Components**

- **Frontend (React):**
  - Agent Manager, Workflow Editor, Observability & Evals Dashboards
  - Data visualization (Recharts, React Flow)
  - Real-time notifications (React Hot Toast)

- **Backend (FastAPI):**
  - API endpoints for config, workflow execution, observability, evaluation, optimization
  - Integrates with Langtrace, OpenTelemetry, Prometheus-Eval, Pruna AI, etc.
  - Versioned config management (SQLite)

- **Database/Cache:**
  - SQLite for configs, version history, execution logs
  - Redis for caching and rate limiting

---

## 3. **Data Flow**

1. **User interacts with UI** (e.g., runs a workflow, tests an agent)
2. **Frontend calls FastAPI endpoints** (e.g., /api/workflow/execute)
3. **Backend executes workflow**:
   - Loads agent/prompt/workflow config
   - Runs LLM calls, tracks traces, collects metrics
   - Stores execution/test results in DB
4. **Observability & Evals**:
   - Traces and metrics sent to dashboards
   - Evaluation results visualized in UI
5. **Performance Monitoring**:
   - System health and optimization data shown in real time

---

## 4. **Integration Points**
- **Langtrace & OpenTelemetry:** Observability/tracing
- **Prometheus-Eval:** LLM output evaluation
- **Pruna AI:** Model optimization
- **Azure OpenAI/OpenAI:** LLM provider
- **Recharts/React Flow:** Visualization

---

## 5. **Extensibility**
- Add new agents, models, or tools via config and UI
- Plug in new LLM providers or evaluation frameworks
- Extend dashboards with new metrics or charts 

---

## 6. Migration & Handover Notes
- Review the main components and data flow above to understand the system structure.
- All configuration (agents, prompts, workflows) is managed via the `config/` directory and SQLite DB.
- Observability, evaluation, and performance monitoring are integrated via Langtrace, OpenTelemetry, Prometheus-Eval, and Pruna AI.
- For API endpoints and backend logic, see `app.py`, `main.py`, and `workflow_executor.py`.
- For UI and workflow editing, see `src/components/` and `src/pages/`.
- See the README and `/docs` for migration steps and further knowledge transfer guidance.
- Check the 'Pending Tasks & Open Issues' section in the README for any unresolved items before starting migration. 