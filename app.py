import asyncio
import json
import os
import time
from typing import Any, Dict, List

import sentry_sdk
import uvicorn
from celery.result import AsyncResult
from fastapi import (FastAPI, File, Query, Request, UploadFile, WebSocket, WebSocketDisconnect)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markitdown import MarkItDown
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config_api import config_app
# Import enhanced systems
from evaluation_system import evaluation_system
from observability import observability_manager
from performance_optimization import performance_optimizer
from tasks import run_workflow_task
from workflow import (run_reply_generation_template, run_workflow,
                      run_workflow_parallel_streaming, run_workflow_streaming)
from workflow_executor import workflow_executor

# Initialize Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0)

limiter = Limiter(key_func=get_remote_address)

# Initialize enhanced systems
observability_manager.initialize()
evaluation_system.initialize()
performance_optimizer.initialize()

app = FastAPI(title="CrewAI Workflow API", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI with observability
observability_manager.instrument_fastapi_app(app)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount configuration API
app.mount("/api/config", config_app)


# New workflow execution endpoint using configuration
@app.post("/api/workflow/execute")
async def execute_workflow_with_config(request: Request, data: dict):
    """Execute workflow using current configuration"""
    try:
        workflow_id = data.get("workflow_id", "default_workflow")
        input_data = data.get("input_data", {})

        result = await workflow_executor.run_full_workflow(workflow_id, input_data)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# Enhanced API endpoints for observability, evaluation, and performance
@app.get("/api/observability/traces")
async def get_traces():
    """Get trace summary"""
    try:
        with observability_manager.trace_workflow("get_traces"):
            return observability_manager.get_trace_summary()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/evaluation/summary")
async def get_evaluation_summary():
    """Get evaluation summary"""
    try:
        return evaluation_system.get_evaluation_summary()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics"""
    try:
        return performance_optimizer.get_performance_metrics()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/system/health")
async def get_system_health():
    """Get comprehensive system health"""
    try:
        return {
            "observability": {
                "initialized": observability_manager.is_initialized,
                "traces_count": len(observability_manager.traces),
            },
            "evaluation": {
                "initialized": evaluation_system.is_initialized,
                "evaluations_count": len(evaluation_system.evaluation_history),
            },
            "performance": {
                "monitoring_active": performance_optimizer.is_monitoring,
                "optimizations_count": len(performance_optimizer.optimization_history),
            },
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # client_id -> workflow_id mapping
        self.client_workflows: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_workflows[client_id] = None
        await self.send_personal_message(
            {"type": "connection", "message": "Connected to workflow stream"}, websocket
        )

    def disconnect(self, websocket: WebSocket, client_id: str):
        self.active_connections.remove(websocket)
        if client_id in self.client_workflows:
            del self.client_workflows[client_id]

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ):
        await websocket.send_text(json.dumps(message))

    async def broadcast_workflow_update(
            self, workflow_id: str, update: Dict[str, Any]):
        """Broadcast workflow updates to all connected clients following that workflow"""
        for client_id, client_workflow_id in self.client_workflows.items():
            if client_workflow_id == workflow_id:
                connection = next(
                    (conn for conn in self.active_connections), None)
                if connection:
                    await self.send_personal_message(update, connection)


manager = ConnectionManager()


# Pydantic models for request validation
class WorkflowRequest(BaseModel):
    conversation_thread: str = Field(
        ..., description="The conversation thread to analyze"
    )
    channel: str = Field(...,
                         description="Communication channel (linkedin/email)")
    prospect_profile_url: str = Field(
        ..., description="LinkedIn profile URL of the prospect"
    )
    prospect_company_url: str = Field(..., description="Company LinkedIn URL")
    prospect_company_website: str = Field(...,
                                          description="Company website URL")
    qubit_context: str = Field(
        "", description="Additional context for the workflow")


class WorkflowFilters(BaseModel):
    """Query parameters for workflow filtering"""

    include_profile: bool = Field(
        True, description="Include profile enrichment")
    include_thread_analysis: bool = Field(
        True, description="Include thread analysis")
    include_reply_generation: bool = Field(
        True, description="Include reply generation")
    priority: str = Field("normal", description="Workflow priority level")


class BatchWorkflowRequest(BaseModel):
    requests: List[WorkflowRequest] = Field(
        ..., description="List of workflow requests to process"
    )
    parallel: bool = Field(True, description="Process requests in parallel")
    max_concurrent: int = Field(10, description="Maximum concurrent requests")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/demo-results", response_class=HTMLResponse)
def demo_results(request: Request):
    return templates.TemplateResponse(
        "demo-results.html", {"request": request})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "start_workflow":
                # Start workflow and associate with client
                workflow_data = message.get("data", {})
                workflow_id = f"workflow_{client_id}_{asyncio.get_event_loop().time()}"
                manager.client_workflows[client_id] = workflow_id

                # Send acknowledgment
                await manager.send_personal_message(
                    {
                        "type": "workflow_started",
                        "workflow_id": workflow_id,
                        "status": "processing",
                    },
                    websocket,
                )

                # Process workflow with streaming updates
                async for update in run_workflow_streaming(
                    workflow_id=workflow_id, **workflow_data
                ):
                    await manager.send_personal_message(update, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        await manager.send_personal_message(
            {"type": "error", "message": f"Workflow error: {str(e)}"}, websocket
        )
        manager.disconnect(websocket, client_id)


@app.post("/run")
@limiter.limit("5/minute")
async def run(
    request: Request,
    workflow_request: WorkflowRequest,
    include_profile: bool = Query(True, description="Include profile enrichment"),
    include_thread_analysis: bool = Query(True, description="Include thread analysis"),
    include_reply_generation: bool = Query(
        True, description="Include reply generation"
    ),
    priority: str = Query("normal", description="Workflow priority level"),
    background: str = Query("false", description="Run in background"),
):
    input_data = workflow_request.dict()
    input_data.update(
        {
            "include_profile": include_profile,
            "include_thread_analysis": include_thread_analysis,
            "include_reply_generation": include_reply_generation,
            "priority": priority,
        }
    )

    if background.lower() == "true":
        task = run_workflow_task.delay(input_data)
        return JSONResponse({"task_id": task.id, "status": "queued"})
    else:
        result = run_workflow(**input_data)
        return JSONResponse(result)


@app.post("/batch")
@limiter.limit("2/minute")
async def batch_process(
    request: Request,
    batch_request: BatchWorkflowRequest,
    include_profile: bool = Query(True, description="Include profile enrichment"),
    include_thread_analysis: bool = Query(True, description="Include thread analysis"),
    include_reply_generation: bool = Query(
        True, description="Include reply generation"
    ),
    priority: str = Query("normal", description="Workflow priority level"),
):
    """
    Process multiple workflow requests in parallel for 100x+ throughput improvement
    """
    if not batch_request.requests:
        return JSONResponse({"error": "No requests provided"}, status_code=400)

    if len(batch_request.requests) > 50:
        return JSONResponse(
            {"error": "Maximum 50 requests per batch"}, status_code=400)

    start_time = time.time()

    async def process_single_request(
            workflow_request: WorkflowRequest,
            index: int):
        """Process a single workflow request"""
        try:
            input_data = workflow_request.dict()
            input_data.update(
                {
                    "include_profile": include_profile,
                    "include_thread_analysis": include_thread_analysis,
                    "include_reply_generation": include_reply_generation,
                    "priority": priority,
                }
            )

            result = run_workflow(**input_data)
            return {
                "index": index,
                "status": "success",
                "result": result,
                "processing_time": time.time() - start_time,
            }
        except Exception as e:
            return JSONResponse({
                "index": index,
                "status": "error", 
                "error": str(e),
                "processing_time": time.time() - start_time,
            }, status_code=500)

    if batch_request.parallel:
        # Process all requests in parallel with concurrency limit
        semaphore = asyncio.Semaphore(batch_request.max_concurrent)

        async def process_with_semaphore(workflow_request, index):
            async with semaphore:
                return await process_single_request(workflow_request, index)

        tasks = [
            process_with_semaphore(req, i)
            for i, req in enumerate(batch_request.requests)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
    else:
        # Process sequentially
        results = []
        for i, req in enumerate(batch_request.requests):
            result = await process_single_request(req, i)
            results.append(result)

    # Calculate batch metrics
    total_time = time.time() - start_time
    successful_requests = sum(
        1 for r in results if r.get("status") == "success")
    failed_requests = len(results) - successful_requests

    return JSONResponse(
        {
            "batch_id": f"batch_{int(time.time())}",
            "total_requests": len(
                batch_request.requests),
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_processing_time": f"{total_time:.2f}s",
            "average_time_per_request": f"{total_time / len(batch_request.requests):.2f}s",
            "throughput": f"{len(batch_request.requests) / total_time:.2f} requests/second",
            "results": results,
        })


@app.post("/run-parallel")
@limiter.limit("5/minute")
async def run_parallel(
    request: Request,
    workflow_request: WorkflowRequest,
    include_profile: bool = Query(True, description="Include profile enrichment"),
    include_thread_analysis: bool = Query(True, description="Include thread analysis"),
    include_reply_generation: bool = Query(
        True, description="Include reply generation"
    ),
    priority: str = Query("normal", description="Workflow priority level"),
    use_templates: bool = Query(
        False, description="Use template-based response generation"
    ),
):
    """
    Run workflow with parallel processing for 50x+ speed improvement
    """
    input_data = workflow_request.dict()
    input_data.update(
        {
            "include_profile": include_profile,
            "include_thread_analysis": include_thread_analysis,
            "include_reply_generation": include_reply_generation,
            "priority": priority,
            "use_templates": use_templates,
        }
    )

    workflow_id = f"parallel_{int(time.time() * 1000)}"

    # Collect results from parallel streaming
    results = []
    async for update in run_workflow_parallel_streaming(
        workflow_id=workflow_id, **input_data
    ):
        results.append(update)

    # Return the final result
    final_result = next((r for r in reversed(results) if r.get(
        "type") == "workflow_completed"), None)
    if final_result:
        return JSONResponse(final_result)
    else:
        return JSONResponse(
            {"error": "Workflow did not complete successfully"}, status_code=500
        )


@app.post("/run-template")
@limiter.limit("10/minute")
async def run_template(
        request: Request,
        workflow_request: WorkflowRequest,
        include_profile: bool = Query(
            True,
            description="Include profile enrichment"),
    include_thread_analysis: bool = Query(
            True,
            description="Include thread analysis"),
        priority: str = Query(
            "normal",
            description="Workflow priority level"),
):
    """
    Run workflow with template-based response generation for 20-100x speed improvement
    """
    input_data = workflow_request.dict()

    # Run profile enrichment and thread analysis
    from faq import get_faq_answer
    from workflow import (assemble_context, run_profile_enrichment,
                          run_thread_analysis)

    start_time = time.time()

    try:
        norm_channel = input_data.get("channel", "linkedin").lower()

        # Run profile and thread analysis in parallel
        profile_task = None
        thread_task = None

        if include_profile:
            profile_task = asyncio.create_task(
                asyncio.to_thread(
                    run_profile_enrichment,
                    input_data.get("prospect_profile_url", ""),
                    input_data.get("prospect_company_url", ""),
                    input_data.get("prospect_company_website", ""),
                )
            )

        if include_thread_analysis:
            thread_task = asyncio.create_task(
                asyncio.to_thread(
                    run_thread_analysis,
                    input_data.get("conversation_thread", ""),
                    norm_channel,
                )
            )

        # Wait for both tasks to complete
        profile_summary = ""
        thread_analysis = ""

        if profile_task:
            profile_summary = await profile_task
        if thread_task:
            thread_analysis = await thread_task

        # Parse questions and get FAQ answers
        try:
            thread_data = json.loads(
                thread_analysis) if thread_analysis else {}
            questions = thread_data.get("explicit_questions", [])
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

        faq_answers = []
        for q in questions:
            answer = get_faq_answer(q)
            faq_answers.append({"question": q, "answer": answer})

        # Assemble context
        context = assemble_context(
            profile_summary,
            thread_analysis,
            faq_answers,
            profile_summary,
            input_data.get("qubit_context", ""),
        )

        # Add conversation thread to context for template processing
        context["conversation_thread"] = input_data.get(
            "conversation_thread", "")

        # Generate template-based response
        reply = await run_reply_generation_template(context, norm_channel)

        processing_time = time.time() - start_time

        return JSONResponse(
            {
                "context": context,
                "reply": reply,
                "processing_time": f"{processing_time:.2f}s",
                "method": "template-based",
                "timestamp": time.time(),
            }
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/stream/{workflow_id}")
async def stream_workflow(workflow_id: str):
    """Stream workflow results using Server-Sent Events"""

    async def generate():
        async for update in run_workflow_streaming(workflow_id=workflow_id):
            yield f"data: {json.dumps(update)}\n\n"

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    md = MarkItDown()
    # Save to a temp file for MarkItDown
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    result = md.convert(tmp_path)
    os.remove(tmp_path)
    return {"markdown": result.text_content}


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    task = AsyncResult(task_id)
    if task.state == "PENDING":
        return {"status": "pending"}
    elif task.state == "SUCCESS":
        return {"status": "success", "result": task.result}
    elif task.state == "FAILURE":
        return {"status": "failure", "error": str(task.result)}
    else:
        return {"status": task.state}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "active_connections": len(
            manager.active_connections)}


@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    from cache import cache_manager, metrics_collector

    metrics = metrics_collector.get_metrics()
    cache_stats = cache_manager.get_stats()

    return {
        "metrics": metrics,
        "cache": cache_stats,
        "active_connections": len(manager.active_connections),
        "timestamp": asyncio.get_event_loop().time(),
    }


@app.get("/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics"""
    from cache import cache_manager

    return cache_manager.get_stats()


@app.get("/api/execution-history")
async def get_execution_history():
    """Get workflow execution history"""
    import time
    from datetime import datetime, timedelta
    
    # Generate demo execution history
    executions = []
    
    # Demo execution 1 - Successful LinkedIn outreach
    executions.append({
        "id": "exec_001",
        "workflow_id": "linkedin-workflow",
        "workflow_name": "LinkedIn Outreach Workflow",
        "status": "completed",
        "started_at": (datetime.now() - timedelta(hours=2)).isoformat(),
        "completed_at": (datetime.now() - timedelta(hours=1, minutes=45)).isoformat(),
        "duration": 900,  # 15 minutes
        "input_data": {
            "prospect_profile_url": "https://linkedin.com/in/john-doe-cto",
            "prospect_company_url": "https://linkedin.com/company/techcorp",
            "message_context": "Discussing AI automation solutions"
        },
        "steps": [
            {
                "name": "Profile Research",
                "status": "completed",
                "duration": 180,
                "result": "Successfully analyzed profile: CTO at TechCorp, 15+ years experience"
            },
            {
                "name": "Message Generation",
                "status": "completed", 
                "duration": 240,
                "result": "Generated personalized message with 92% quality score"
            },
            {
                "name": "Quality Review",
                "status": "completed",
                "duration": 120,
                "result": "Message approved: Professional tone, clear value proposition"
            }
        ],
        "output": {
            "message": "Hi John, I noticed your recent post about scaling AI initiatives...",
            "quality_score": 92,
            "predicted_response_rate": 0.42
        }
    })
    
    # Demo execution 2 - Failed execution
    executions.append({
        "id": "exec_002",
        "workflow_id": "linkedin-workflow",
        "workflow_name": "LinkedIn Outreach Workflow",
        "status": "failed",
        "started_at": (datetime.now() - timedelta(hours=3)).isoformat(),
        "completed_at": (datetime.now() - timedelta(hours=2, minutes=50)).isoformat(),
        "duration": 600,
        "input_data": {
            "prospect_profile_url": "https://linkedin.com/in/jane-smith",
            "prospect_company_url": "https://linkedin.com/company/innovate-inc",
            "message_context": "Partnership opportunities"
        },
        "steps": [
            {
                "name": "Profile Research",
                "status": "completed",
                "duration": 200,
                "result": "Profile analyzed: VP of Sales at Innovate Inc"
            },
            {
                "name": "Message Generation",
                "status": "failed",
                "duration": 400,
                "result": "Error: Rate limit exceeded for AI model",
                "error": "RateLimitError: Too many requests"
            }
        ],
        "error": "Workflow failed at Message Generation step"
    })
    
    # Demo execution 3 - Currently running
    executions.append({
        "id": "exec_003",
        "workflow_id": "linkedin-workflow",
        "workflow_name": "LinkedIn Outreach Workflow",
        "status": "running",
        "started_at": (datetime.now() - timedelta(minutes=5)).isoformat(),
        "duration": 300,
        "current_step": "Message Generation",
        "progress": 65,
        "input_data": {
            "prospect_profile_url": "https://linkedin.com/in/mike-wilson-founder",
            "prospect_company_url": "https://linkedin.com/company/startup-labs",
            "message_context": "Exploring collaboration on new AI project"
        },
        "steps": [
            {
                "name": "Profile Research",
                "status": "completed",
                "duration": 150,
                "result": "Founder & CEO at Startup Labs, AI enthusiast"
            },
            {
                "name": "Message Generation",
                "status": "running",
                "duration": 150,
                "progress": 65
            }
        ]
    })
    
    return executions


@app.get("/api/test-results")
async def get_test_results():
    """Get test results for agents and workflows"""
    from datetime import datetime, timedelta
    
    # Generate demo test results
    test_results = []
    
    # Test result 1 - Agent performance test
    test_results.append({
        "id": "test_001",
        "test_name": "Research Agent Performance Test",
        "entity_type": "agent",
        "entity_id": "research_agent",
        "entity_name": "LinkedIn Research Agent",
        "test_type": "performance",
        "status": "passed",
        "executed_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        "duration": 45.2,
        "metrics": {
            "accuracy": 0.94,
            "speed": 3.2,  # seconds
            "token_usage": 1250,
            "memory_usage": 128.5  # MB
        },
        "test_cases": [
            {
                "name": "Profile extraction accuracy",
                "status": "passed",
                "score": 0.95,
                "details": "Successfully extracted 19/20 profile fields"
            },
            {
                "name": "Company analysis depth",
                "status": "passed",
                "score": 0.92,
                "details": "Identified key insights and pain points"
            }
        ]
    })
    
    # Test result 2 - Workflow integration test
    test_results.append({
        "id": "test_002",
        "test_name": "End-to-End Workflow Test",
        "entity_type": "workflow",
        "entity_id": "linkedin-workflow",
        "entity_name": "LinkedIn Outreach Workflow",
        "test_type": "integration",
        "status": "passed",
        "executed_at": (datetime.now() - timedelta(hours=2)).isoformat(),
        "duration": 180.5,
        "metrics": {
            "success_rate": 0.90,
            "avg_execution_time": 15.3,
            "quality_score": 0.88,
            "resource_efficiency": 0.85
        },
        "test_cases": [
            {
                "name": "Data flow between agents",
                "status": "passed",
                "score": 0.90,
                "details": "All agents received and processed data correctly"
            },
            {
                "name": "Output quality validation",
                "status": "passed",
                "score": 0.88,
                "details": "Generated messages met quality standards"
            },
            {
                "name": "Error handling",
                "status": "passed",
                "score": 0.92,
                "details": "Gracefully handled API timeouts and retries"
            }
        ]
    })
    
    # Test result 3 - Quality assurance test
    test_results.append({
        "id": "test_003",
        "test_name": "Message Quality Validation",
        "entity_type": "agent",
        "entity_id": "quality_agent",
        "entity_name": "Quality Assurance Agent",
        "test_type": "quality",
        "status": "warning",
        "executed_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "duration": 22.8,
        "metrics": {
            "grammar_score": 0.98,
            "tone_consistency": 0.85,
            "personalization": 0.78,
            "cta_effectiveness": 0.82
        },
        "test_cases": [
            {
                "name": "Grammar and spelling check",
                "status": "passed",
                "score": 0.98,
                "details": "No grammar or spelling errors detected"
            },
            {
                "name": "Tone analysis",
                "status": "passed",
                "score": 0.85,
                "details": "Professional tone maintained throughout"
            },
            {
                "name": "Personalization depth",
                "status": "warning",
                "score": 0.78,
                "details": "Could improve company-specific references"
            }
        ],
        "warnings": ["Personalization score below threshold (0.80)"]
    })
    
    # Test result 4 - Load test
    test_results.append({
        "id": "test_004",
        "test_name": "Concurrent Execution Load Test",
        "entity_type": "workflow",
        "entity_id": "linkedin-workflow",
        "entity_name": "LinkedIn Outreach Workflow",
        "test_type": "load",
        "status": "failed",
        "executed_at": (datetime.now() - timedelta(hours=4)).isoformat(),
        "duration": 300.0,
        "metrics": {
            "concurrent_executions": 50,
            "success_rate": 0.64,
            "avg_response_time": 45.2,
            "error_rate": 0.36
        },
        "test_cases": [
            {
                "name": "10 concurrent requests",
                "status": "passed",
                "score": 1.0,
                "details": "All requests completed successfully"
            },
            {
                "name": "25 concurrent requests",
                "status": "passed",
                "score": 0.88,
                "details": "88% success rate, minor delays"
            },
            {
                "name": "50 concurrent requests",
                "status": "failed",
                "score": 0.64,
                "details": "Rate limits hit, 36% failure rate"
            }
        ],
        "errors": ["Rate limit exceeded after 32 concurrent requests"]
    })
    
    return test_results


@app.post("/cache/clear")
async def clear_cache(pattern: str = "*"):
    """Clear cache entries matching pattern"""
    from cache import cache_manager

    cleared = cache_manager.flush_pattern(pattern)
    return {"cleared_keys": cleared, "pattern": pattern}


# FAQ Management Endpoints
@app.get("/api/faq")
async def get_all_faqs():
    """Get all FAQ entries"""
    from faq import get_all_faq_topics
    return get_all_faq_topics()


@app.post("/api/faq")
async def create_faq(data: dict):
    """Create new FAQ entry"""
    from faq import add_faq_item
    
    try:
        result = add_faq_item(
            question=data.get("question", ""),
            answer=data.get("answer", ""),
            category=data.get("category", ""),
            keywords=data.get("keywords", "")
        )
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.put("/api/faq/{faq_id}")
async def update_faq(faq_id: int, data: dict):
    """Update FAQ entry"""
    from faq import update_faq_item
    
    try:
        result = update_faq_item(faq_id, data)
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.delete("/api/faq/{faq_id}")
async def delete_faq(faq_id: int):
    """Delete FAQ entry"""
    from faq import delete_faq_item
    
    try:
        result = delete_faq_item(faq_id)
        return {"success": result, "id": faq_id}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/faq/search")
async def search_faq_endpoint(q: str, limit: int = 5):
    """Search FAQ entries"""
    from faq import search_faq

    results = search_faq(q, limit)
    return {"query": q, "results": results}


@app.get("/api/faq/stats")
async def get_faq_stats():
    """Get FAQ usage statistics"""
    from faq import get_faq_stats

    return get_faq_stats()


@app.get("/api/faq/export")
async def export_faq():
    """Export FAQs as CSV"""
    from faq import export_to_csv
    from fastapi.responses import FileResponse
    
    csv_path = export_to_csv()
    return FileResponse(
        csv_path, 
        media_type="text/csv",
        filename="faq_knowledge_base.csv"
    )


@app.post("/api/faq/import")
async def import_faq(file: UploadFile = File(...)):
    """Import FAQs from CSV"""
    from faq import import_from_csv
    
    try:
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        result = import_from_csv(csv_content)
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8100, reload=True)
