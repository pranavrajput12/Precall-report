# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern LLM workflow orchestration platform that combines a Python FastAPI backend with a React frontend. The system enables building, testing, and monitoring multi-agent LLM workflows with comprehensive observability, evaluation, and performance optimization capabilities using CrewAI for agent orchestration.

## Development Commands

### Backend (Python)
- `pip install -r requirements.txt` - Install Python dependencies
- `uvicorn app:app --reload` - Start development server with hot reload
- `uvicorn app:app --host 0.0.0.0 --port 8100` - Start production server
- `flake8 .` - Run linting (configured to ignore E501 line length)
- `celery -A tasks worker --loglevel=info` - Start background task worker
- `redis-server` - Start Redis for caching and Celery broker

### Frontend (React)
- `npm install` - Install Node.js dependencies
- `npm start` - Start development server (proxies to backend on localhost:8100)
- `npm run build` - Build for production
- `npm test` - Run Jest tests
- `npm test -- --coverage` - Run tests with coverage report

### Development Workflow
- Backend runs on port 8100, frontend on port 3000
- Frontend proxies API calls to backend via `"proxy": "http://localhost:8100"` in package.json
- Start both services for full-stack development

## Technology Stack

### Backend Architecture
- **FastAPI** - Modern async Python web framework with automatic API docs
- **CrewAI** - Multi-agent workflow orchestration framework
- **LangChain** - LLM integration and prompt management
- **Celery + Redis** - Background task processing and caching
- **SQLite** - Configuration storage and execution history
- **Neo4j** - Graph database for complex data relationships

### Frontend Architecture
- **React 18** - UI framework with hooks and functional components
- **React Router** - Client-side routing
- **React Flow (@xyflow/react)** - Visual workflow builder and graph visualization
- **Recharts** - Data visualization and charting
- **Monaco Editor** - Code editing interface
- **Tailwind CSS** - Utility-first CSS framework
- **React Hot Toast** - Notification system

### Observability & Monitoring
- **Langtrace** - LLM observability and tracing
- **OpenTelemetry** - Comprehensive instrumentation stack
- **Sentry** - Error tracking and performance monitoring
- **Prometheus-Eval** - LLM output evaluation framework
- **Pruna AI** - Model performance optimization

## Key Architecture Patterns

### Configuration-Driven System
- All agents, prompts, tools, and workflows are JSON-configured in `/config/` directory
- Version control for configurations with rollback capabilities
- SQLite database stores configuration versions and execution history

### Multi-Agent Workflow Engine
- **Agent Definitions**: `/config/agents/` - Individual agent configurations with model selection
- **Prompt Templates**: `/config/prompts/` - Versioned prompt templates
- **Tool Configurations**: `/config/tools/` - External tool integrations
- **Workflow Definitions**: `/config/workflows/` - Multi-agent workflow orchestration

### API Structure
- **Config API** (`config_api.py`) - CRUD operations for configurations
- **Workflow API** (`app.py`) - Workflow execution and monitoring
- **Evaluation API** - LLM output quality assessment
- **Observability API** - Metrics, traces, and performance data

## File Structure

### Backend Core Files
- `app.py` - Main FastAPI application with API endpoints
- `workflow_executor.py` - Core workflow execution engine
- `config_manager.py` - Configuration management and versioning
- `workflow.py` - Workflow definition and execution logic
- `agents.py` - Agent initialization and management
- `tasks.py` - Celery background task definitions
- `evaluation_system.py` - LLM evaluation framework
- `observability.py` - Monitoring and tracing setup
- `performance_optimization.py` - Performance monitoring and optimization

### Frontend Structure
```
src/
├── components/          # Reusable UI components
├── pages/              # Route-based page components
├── App.js              # Main application with routing
└── index.js            # Application entry point
```

### Configuration Management
```
config/
├── agents/             # Agent definitions with model configurations
├── prompts/            # Prompt templates and versions
├── tools/              # Tool configurations and integrations
├── workflows/          # Workflow definitions and orchestration
├── versions/           # Configuration version history
└── config.db           # SQLite database for persistence
```

## Development Guidelines

### Python Code Standards
- Follow PEP 8 with relaxed line length (E501 ignored in .flake8)
- Use async/await patterns for FastAPI endpoints
- Implement proper error handling with Sentry integration
- Use Pydantic models for request/response validation

### React Code Standards
- Use functional components with hooks
- Follow Create React App ESLint configuration
- Use React Query for API state management
- Implement proper error boundaries

### Testing Approach
- Backend: Use FastAPI TestClient for API testing
- Frontend: Jest + React Testing Library for component testing
- Integration: Test full workflow execution end-to-end
- Evaluation: Use prometheus-eval for LLM output quality testing

## External Service Dependencies

### Required Services
- **OpenAI/Azure OpenAI** - LLM provider (configure API keys)
- **Redis** - Required for Celery task queue and caching
- **Neo4j** - Optional for advanced graph-based data storage

### Optional Monitoring Services
- **Langtrace** - LLM observability (requires API key)
- **Sentry** - Error tracking (configure SENTRY_DSN)
- **OpenTelemetry Collector** - Metrics export

## Common Development Tasks

### Adding New Agents
1. Create agent configuration in `/config/agents/`
2. Define corresponding prompts in `/config/prompts/`
3. Register agent in workflow definitions
4. Test via UI Agent Manager or API endpoints

### Workflow Debugging
- Use `/api/observability/traces` to view execution traces
- Check `/api/evaluation/reports` for output quality metrics
- Monitor performance via `/api/performance/metrics`
- View logs in observability dashboard

### Configuration Management
- All configs are versioned automatically
- Use `/api/config/rollback` to revert changes
- Export/import configurations via API for backup

## Performance Considerations

### Backend Optimization
- Use async operations for all I/O bound tasks
- Implement smart caching with Redis and semantic similarity
- Monitor LLM token usage and response times
- Use Celery for long-running workflow executions

### Frontend Performance
- Implement code splitting for large dashboards
- Use React.memo for expensive visualizations
- Optimize React Flow performance for large workflows
- Use React Query caching for API responses

## Security Notes

- Store API keys in environment variables, never in code
- Use rate limiting (SlowAPI) for public endpoints
- Implement proper CORS configuration for production
- Regular security audits of dependencies