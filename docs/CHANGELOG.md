# Changelog

All notable changes to the CrewAI Workflow Orchestration Platform will be documented in this file.

## [2025.01.22] - Latest Updates

### Added
- **All Runs Page**: Comprehensive execution viewer with search, filter, and export capabilities
- **Run Workflow Page**: Simplified interface for testing workflows with immediate feedback
- **FAQ Agent**: Intelligent FAQ management with semantic search and answer synthesis
- **Dynamic Quality Scoring**: Real-time evaluation of message quality (personalization, tone, value propositions, CTAs)
- **Response Rate Prediction**: Dynamic prediction based on message content analysis
- **Simple Observability**: Lightweight in-memory tracking replacing complex OpenTelemetry setup
- **Execution History Persistence**: JSON-based storage for workflow execution data
- **Port Configuration**: Standardized on port 8100 for backend API

### Fixed
- **Execution Counter**: Now properly initializes based on existing execution history
- **Execution Sorting**: All Runs page now shows newest executions first
- **FAQ Integration**: Fixed JSON path extraction for questions and implicit needs
- **Port Mismatch**: Resolved frontend proxy issues by aligning on port 8100
- **Quality Scores**: Replaced placeholder values with dynamic content-based evaluation

### Improved
- **Navigation**: Added "Test Workflow" button on dashboard for quick access
- **FAQ Handling**: Integrated intelligent FAQ agent for better answer quality
- **Error Handling**: Better error messages and fallback mechanisms
- **UI/UX**: Enhanced All Runs page with metrics, stats, and bulk operations

### Technical Details
- Implemented semantic search using sentence-transformers (all-MiniLM-L6-v2)
- Added content analysis for quality scoring (personalization, tone, value propositions, CTAs)
- Simplified observability to use in-memory tracking with no external dependencies
- Enhanced FAQ agent with pre-computed embeddings for sub-500ms response times

## [2025.01.19] - Initial Release

### Features
- Multi-agent workflow orchestration with CrewAI
- React-based web interface
- Redis caching with semantic similarity
- CSV-based FAQ knowledge management
- Basic execution history tracking
- Agent and workflow configuration management