# Changelog

All notable changes to the CrewAI Workflow Platform will be documented in this file.

## [2.1.0] - 2025-07-24

### 🎉 Major Frontend UX Improvements

#### Added
- **Smart Duplicate Detection**: Prevents running identical workflows within 5 minutes
  - Intelligent comparison of workflow inputs (excluding optional context)
  - User-friendly dialog offering to view existing results or run anyway
  - Helps prevent accidental multiple executions of same workflow

- **Real-time Execution Status Tracking**: Live feedback during workflow execution
  - "Preparing workflow..." → "Checking for duplicates..." → "Starting workflow execution..."
  - "Processing workflow response..." → "Workflow completed!" → "Redirecting..."
  - Visual loading indicators with descriptive status messages

- **Auto-redirect After Completion**: Seamless user flow
  - Automatically redirects to All Runs page 2 seconds after completion
  - Eliminates confusion about next steps after workflow execution
  - Smooth transition from execution to viewing results

#### Improved
- **React Flow Visualization**: Fixed edge creation errors and console warnings
  - Enhanced connection validation and error handling
  - Improved edge ID generation to prevent conflicts
  - Stable visualization without React Flow console errors

- **Clean User Interface**: Removed confusing UI elements
  - Hidden "Processing Time: N/A" box when no meaningful data available
  - Only shows processing time when actual timing data exists
  - Cleaner, less cluttered post-execution interface

#### Technical Enhancements
- Fixed duplicate detection API data access (`input_data` vs `inputs`)
- Improved React useCallback dependencies to prevent infinite re-renders
- Enhanced error handling throughout workflow execution flow
- Better React Query cache invalidation for real-time data updates

### 🔧 Backend Stability
- Maintained ExecutionManager atomic operations for JSON/database synchronization
- Preserved existing observability and evaluation system integrations
- Continued support for Azure OpenAI API with environment variables

### 📊 Data Management
- Added selective cleanup scripts for targeted testing
- Backup and restore functionality for execution data
- Maintained backward compatibility with existing execution records

---

## [2.0.0] - 2025-07-24

### 🚀 Major Release: Unified Data Management

#### Added
- **ExecutionManager**: Atomic operations ensuring JSON/database synchronization
- **Database Migration System**: Seamless transition from JSON-only to dual storage
- **Enhanced Observability Integration**: New executions automatically tracked
- **Evaluation System Integration**: Automatic quality assessment for all workflows
- **Improved Error Handling**: Comprehensive error tracking and recovery

#### Fixed
- **JSON/Database Synchronization**: Permanent fix for data consistency issues
- **Field Name Standardization**: Unified `output_data` vs `output` field naming
- **Transaction Management**: Rollback support for failed operations
- **Data Formatting**: Clean presentation in evaluation and observability dashboards

#### Security
- **API Key Management**: Removed hardcoded credentials, environment variables only
- **GitHub Security**: Resolved push protection issues

### 🎨 Frontend Improvements
- **Enhanced Data Display**: Formatted timestamps, status badges, and score indicators
- **Improved Navigation**: Better UX flow between pages
- **Real-time Updates**: Synchronized data across all dashboard components

---

## [1.0.0] - Initial Release

### Core Features
- Multi-agent workflow orchestration with CrewAI
- FastAPI backend with comprehensive API endpoints
- React frontend with interactive dashboard
- LinkedIn outreach automation
- FAQ knowledge base management
- Basic observability and evaluation systems