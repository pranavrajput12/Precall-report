# Third-Party Integrations

This project leverages several third-party integrations to provide advanced features, observability, evaluation, and performance optimization. Below is a list of all major integrations and their roles in the system:

---

## 1. **Langtrace**
- **Purpose:** LLM observability and tracing
- **Role:** Tracks all LLM calls, token usage, and errors for debugging and monitoring.
- **Where Used:** Backend (Python), integrated with all agent and workflow executions.

## 2. **OpenTelemetry**
- **Purpose:** Distributed tracing and metrics
- **Role:** Provides end-to-end traceability across all backend services and APIs.
- **Where Used:** Backend (Python), wraps API endpoints, agent steps, and workflow execution.

## 3. **Prometheus-Eval**
- **Purpose:** LLM output evaluation
- **Role:** Automatically scores and benchmarks LLM responses for quality, relevance, and safety.
- **Where Used:** Backend (Python), used in evaluation pipelines and dashboards.

## 4. **Azure OpenAI / OpenAI**
- **Purpose:** Language model provider
- **Role:** Supplies the core LLMs for all agents and workflow steps.
- **Where Used:** Backend (Python), all agent LLM calls.

## 5. **Recharts**
- **Purpose:** Data visualization
- **Role:** Renders charts and graphs for performance, evaluation, and observability dashboards.
- **Where Used:** Frontend (React), Observability and Evals dashboards.

## 6. **React Flow**
- **Purpose:** Workflow visualization
- **Role:** Visualizes agent and workflow step dependencies and execution flow.
- **Where Used:** Frontend (React), Workflow Visualization page.

## 7. **React Hot Toast**
- **Purpose:** Notifications
- **Role:** Provides user feedback and status updates in the UI.
- **Where Used:** Frontend (React), all pages.

## 8. **React Query**
- **Purpose:** Data fetching and caching
- **Role:** Handles API calls and keeps UI in sync with backend state.
- **Where Used:** Frontend (React), all data-driven components.

## 9. **Pruna AI**
- **Purpose:** Model optimization
- **Role:** Accelerates and compresses LLMs for faster, more efficient inference.
- **Where Used:** Backend (Python), performance optimization routines.

## 10. **psutil & GPUtil**
- **Purpose:** System resource monitoring
- **Role:** Tracks CPU, memory, and GPU usage for health and performance dashboards.
- **Where Used:** Backend (Python), performance monitoring.

---

**Note:** Additional integrations (e.g., Redis, Celery, Sentry, SerpAPI) may be present for caching, background tasks, error tracking, and web search, as described in the architecture doc. 

---

## Migration Checklist
- Ensure all API keys and credentials for the following services are set up in the new environment:
  - Langtrace (LLM observability)
  - OpenTelemetry (tracing/metrics)
  - Prometheus-Eval (LLM evaluation)
  - Azure OpenAI / OpenAI (LLM provider)
  - Pruna AI (model optimization)
  - Redis (caching)
  - SQLite (local DB, or migrate to another DB if needed)
  - psutil & GPUtil (system monitoring)
- Check for any additional integrations (Celery, Sentry, SerpAPI, etc.) as described above.
- Update environment variables and `.env` files as needed. 