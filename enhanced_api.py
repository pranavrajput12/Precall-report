"""
Enhanced API with Observability, Evaluation, and Performance Optimization
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import existing systems
from evaluation_system import (EvaluationMetric, compare_responses,
                               evaluate_response, evaluation_system)
# Import new systems
from observability import observability_manager
from performance_optimization import (OptimizationType,
                                      optimize_system_performance,
                                      performance_optimizer)
from workflow_executor import workflow_executor

logger = logging.getLogger(__name__)


# Pydantic models for API requests
class EvaluationRequest(BaseModel):
    instruction: str
    response: str
    metric: str = "accuracy"
    reference_answer: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ComparisonRequest(BaseModel):
    instruction: str
    response_a: str
    response_b: str
    metric: str = "accuracy"
    reference_answer: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class BatchEvaluationRequest(BaseModel):
    instructions: List[str]
    responses: List[str]
    metrics: List[str] = ["accuracy", "relevance"]
    reference_answers: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


class OptimizationRequest(BaseModel):
    optimization_types: List[str] = [
        "inference_acceleration",
        "memory_optimization"]
    parameters: Optional[Dict[str, Any]] = None


class PerformanceConfigRequest(BaseModel):
    monitoring_enabled: bool = True
    optimization_level: str = "moderate"
    auto_optimize: bool = False


# Create enhanced API
def create_enhanced_api():
    """Create FastAPI app with enhanced features"""
    app = FastAPI(
        title="Enhanced CrewAI Workflow System",
        description="CrewAI workflow system with observability, evaluation, and performance optimization",
        version="2.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize systems
    @app.on_event("startup")
    async def startup_event():
        """Initialize all systems on startup"""
        try:
            # Initialize observability
            observability_manager.initialize()
            observability_manager.instrument_fastapi_app(app)

            # Initialize evaluation system
            evaluation_system.initialize()

            # Initialize performance optimizer
            performance_optimizer.initialize()

            logger.info("Enhanced API systems initialized successfully")

        except Exception as e:
            logger.error(f"Error nitialize systems: {e}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        try:
            performance_optimizer.stop_monitoring()
            logger.info("Enhanced API systems shut down successfully")
        except Exception as e:
            logger.error(f"Error ng shutdown: {e}")

    # ===================
    # OBSERVABILITY ENDPOINTS
    # ===================

    @app.get("/api/observability/traces")
    async def get_traces():
        """Get trace summary"""
        try:
            with observability_manager.trace_workflow("get_traces"):
                return observability_manager.get_trace_summary()
        except Exception as e:
            logger.error(f"Error ng traces: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/observability/metrics")
    async def get_observability_metrics():
        """Get observability metrics"""
        try:
            return {
                "traces": observability_manager.get_trace_summary(),
                "current_trace_id": (
                    observability_manager.tracer.get_current_span()
                    .get_span_context()
                    .trace_id
                    if observability_manager.tracer
                    else None
                ),
                "initialized": observability_manager.is_initialized,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error ng observability metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/observability/trace-event")
    async def record_trace_event(
            event_name: str, attributes: Dict[str, Any] = None):
        """Record a trace event"""
        try:
            from observability import record_trace_event

            record_trace_event(event_name, attributes or {})
            return {"status": "success", "event": event_name}
        except Exception as e:
            logger.error(f"Error ng trace event: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ===================
    # EVALUATION ENDPOINTS
    # ===================

    @app.post("/api/evaluation/single")
    async def evaluate_single_response(request: EvaluationRequest):
        """Evaluate a single response"""
        try:
            with observability_manager.trace_workflow("single_evaluation"):
                metric = EvaluationMetric(request.metric.lower())
                result = await evaluate_response(
                    instruction=request.instruction,
                    response=request.response,
                    metric=metric,
                    reference_answer=request.reference_answer,
                )

                return {
                    "metric": result.metric.value,
                    "score": result.score,
                    "feedback": result.feedback,
                    "confidence": result.confidence,
                    "execution_time": result.execution_time,
                    "evaluator": result.evaluator,
                    "timestamp": result.timestamp.isoformat(),
                }
        except Exception as e:
            logger.error(f"Error n single evaluation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/evaluation/compare")
    async def compare_two_responses(request: ComparisonRequest):
        """Compare two responses"""
        try:
            with observability_manager.trace_workflow("response_comparison"):
                metric = EvaluationMetric(request.metric.lower())
                result = await compare_responses(
                    instruction=request.instruction,
                    response_a=request.response_a,
                    response_b=request.response_b,
                    metric=metric,
                )

                return {
                    "metric": result.metric.value,
                    "winner": result.score,
                    "feedback": result.feedback,
                    "confidence": result.confidence,
                    "execution_time": result.execution_time,
                    "evaluator": result.evaluator,
                    "timestamp": result.timestamp.isoformat(),
                }
        except Exception as e:
            logger.error(f"Error n response comparison: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/evaluation/batch")
    async def evaluate_batch_responses(request: BatchEvaluationRequest):
        """Evaluate multiple responses in batch"""
        try:
            with observability_manager.trace_workflow("batch_evaluation"):
                metrics = [EvaluationMetric(m.lower())
                           for m in request.metrics]
                result = await evaluation_system.evaluate_batch_absolute(
                    instructions=request.instructions,
                    responses=request.responses,
                    metrics=metrics,
                    reference_answers=request.reference_answers,
                    context=request.context,
                )

                return {
                    "aggregate_score": result.aggregate_score,
                    "total_time": result.total_time,
                    "success_rate": result.success_rate,
                    "results_count": len(result.results),
                    "results": [
                        {
                            "metric": r.metric.value,
                            "score": r.score,
                            "feedback": r.feedback,
                            "confidence": r.confidence,
                            "execution_time": r.execution_time,
                        }
                        for r in result.results[:10]  # Return first 10 results
                    ],
                }
        except Exception as e:
            logger.error(f"Error n batch evaluation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/evaluation/summary")
    async def get_evaluation_summary():
        """Get evaluation summary"""
        try:
            return evaluation_system.get_evaluation_summary()
        except Exception as e:
            logger.error(f"Error ng evaluation summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/evaluation/metrics")
    async def get_available_metrics():
        """Get available evaluation metrics"""
        return {
            "metrics": [metric.value for metric in EvaluationMetric],
            "descriptions": {
                "accuracy": "Factual accuracy and correctness",
                "relevance": "Relevance to the instruction",
                "coherence": "Logical structure and clarity",
                "helpfulness": "Usefulness in addressing user needs",
                "safety": "Safety and appropriateness",
                "creativity": "Originality and creativity",
            },
        }

    # ===================
    # PERFORMANCE OPTIMIZATION ENDPOINTS
    # ===================

    @app.post("/api/optimization/optimize")
    async def optimize_system(
        request: OptimizationRequest, background_tasks: BackgroundTasks
    ):
        """Run system optimization"""
        try:
            with observability_manager.trace_workflow("system_optimization"):
                # Convert string types to enum
                optimization_types = [
                    OptimizationType(opt_type.lower())
                    for opt_type in request.optimization_types
                ]

                # Run optimization in background
                background_tasks.add_task(
                    optimize_system_performance, optimization_types
                )

                return {
                    "status": "started",
                    "optimization_types": request.optimization_types,
                    "message": "Optimization started in background",
                }
        except Exception as e:
            logger.error(f"Error ng optimization: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/optimization/model-compression")
    async def optimize_model_compression(
        model_path: str = "default_model",
        compression_ratio: float = 0.5,
        method: str = "pruning",
    ):
        """Optimize model compression"""
        try:
            with observability_manager.trace_workflow("model_compression"):
                result = await performance_optimizer.optimize_model_compression(
                    model_path=model_path,
                    compression_ratio=compression_ratio,
                    method=method,
                )

                return {
                    "optimization_type": result.optimization_type.value,
                    "original_metric": result.original_metric,
                    "optimized_metric": result.optimized_metric,
                    "improvement_ratio": result.improvement_ratio,
                    "execution_time": result.execution_time,
                    "memory_saved": result.memory_saved,
                    "success": result.success,
                    "details": result.details,
                }
        except Exception as e:
            logger.error(f"Error n model compression: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/optimization/inference-acceleration")
    async def optimize_inference_speed(
        model_name: str = "default_model", optimization_level: str = "moderate"
    ):
        """Optimize inference speed"""
        try:
            with observability_manager.trace_workflow("inference_acceleration"):
                result = await performance_optimizer.optimize_inference_acceleration(
                    model_name=model_name, optimization_level=optimization_level
                )

                return {
                    "optimization_type": result.optimization_type.value,
                    "original_latency_ms": result.original_metric * 1000,
                    "optimized_latency_ms": result.optimized_metric * 1000,
                    "speedup": result.improvement_ratio,
                    "execution_time": result.execution_time,
                    "success": result.success,
                    "details": result.details,
                }
        except Exception as e:
            logger.error(f"Error n inference acceleration: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/optimization/memory")
    async def optimize_memory(target_reduction: float = 0.3):
        """Optimize memory usage"""
        try:
            with observability_manager.trace_workflow("memory_optimization"):
                result = await performance_optimizer.optimize_memory_usage(
                    target_reduction=target_reduction
                )

                return {
                    "optimization_type": result.optimization_type.value,
                    "original_usage_percent": result.original_metric,
                    "optimized_usage_percent": result.optimized_metric,
                    "memory_saved_gb": result.memory_saved / (1024**3),
                    "improvement_ratio": result.improvement_ratio,
                    "execution_time": result.execution_time,
                    "success": result.success,
                }
        except Exception as e:
            logger.error(f"Error n memory optimization: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/optimization/summary")
    async def get_optimization_summary():
        """Get optimization summary"""
        try:
            return performance_optimizer.get_optimization_summary()
        except Exception as e:
            logger.error(f"Error ng optimization summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/optimization/performance-metrics")
    async def get_performance_metrics():
        """Get current performance metrics"""
        try:
            return performance_optimizer.get_performance_metrics()
        except Exception as e:
            logger.error(f"Error ng performance metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/optimization/types")
    async def get_optimization_types():
        """Get available optimization types"""
        return {
            "optimization_types": [
                opt_type.value for opt_type in OptimizationType],
            "descriptions": {
                "model_compression": "Reduce model size through pruning or quantization",
                "inference_acceleration": "Speed up inference through optimization",
                "memory_optimization": "Reduce memory usage and improve efficiency",
                "batch_optimization": "Optimize batch processing for better throughput",
                "caching_optimization": "Improve caching strategy for better performance",
                "kernel_optimization": "Optimize GPU kernels for better performance",
            },
        }

    # ===================
    # INTEGRATED WORKFLOW ENDPOINTS
    # ===================

    @app.post("/api/workflow/execute-with-monitoring")
    async def execute_workflow_with_monitoring(
        workflow_data: Dict[str, Any],
        enable_evaluation: bool = True,
        enable_optimization: bool = True,
    ):
        """Execute workflow with full monitoring, evaluation, and optimization"""
        try:
            with observability_manager.trace_workflow("monitored_workflow_execution"):
                # Start performance monitoring
                start_time = datetime.now()

                # Execute workflow
                result = await workflow_executor.execute_workflow(workflow_data)

                # Evaluate results if enabled
                evaluation_results = []
                if enable_evaluation and result.get("success"):
                    for agent_result in result.get("agent_results", []):
                        if agent_result.get("output"):
                            eval_result = await evaluate_response(
                                instruction=agent_result.get("task", ""),
                                response=agent_result.get("output", ""),
                                metric=EvaluationMetric.ACCURACY,
                            )
                            evaluation_results.append(
                                {
                                    "agent_id": agent_result.get("agent_id"),
                                    "score": eval_result.score,
                                    "feedback": eval_result.feedback,
                                }
                            )

                # Run optimization if enabled
                optimization_results = []
                if enable_optimization:
                    opt_results = await optimize_system_performance(
                        [
                            OptimizationType.INFERENCE_ACCELERATION,
                            OptimizationType.MEMORY_OPTIMIZATION,
                        ]
                    )
                    optimization_results = [
                        {
                            "type": opt.optimization_type.value,
                            "improvement": opt.improvement_ratio,
                            "success": opt.success,
                        }
                        for opt in opt_results
                    ]

                # Calculate total execution time
                total_time = (datetime.now() - start_time).total_seconds()

                return {
                    "workflow_result": result,
                    "evaluation_results": evaluation_results,
                    "optimization_results": optimization_results,
                    "total_execution_time": total_time,
                    "monitoring_enabled": True,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error n monitored workflow execution: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/system/health")
    async def get_system_health():
        """Get comprehensive system health status"""
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
                    "optimizations_count": len(
                        performance_optimizer.optimization_history
                    ),
                    "metrics_count": len(performance_optimizer.performance_metrics),
                },
                "system_metrics": performance_optimizer.get_performance_metrics(),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error ng system health: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return app


# Create the enhanced app
enhanced_app = create_enhanced_api()
