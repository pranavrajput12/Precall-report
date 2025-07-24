"""
Enhanced API with Observability, Evaluation, and Performance Optimization
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pagination import pagination_params, Paginator

# Import existing systems
from evaluation_system import (EvaluationMetric, compare_responses,
                               evaluate_response, evaluation_system)
# Import new systems
from observability import observability_manager
from performance_optimization import (OptimizationType,
                                      optimize_system_performance,
                                      performance_optimizer)
from workflow_executor import workflow_executor
from logging_config import log_info, log_error, log_warning, log_debug
from config_manager import config_manager

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
    """
    Create FastAPI app with enhanced features.
    
    This function initializes a FastAPI application with enhanced features including:
    - CORS middleware configuration
    - Observability instrumentation
    - Evaluation system integration
    - Performance optimization
    - Structured error handling
    
    The function sets up event handlers for startup and shutdown, and defines
    all API endpoints for the enhanced functionality.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
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
        """
        Initialize all systems on startup.
        
        This event handler is triggered when the FastAPI application starts up.
        It initializes the following systems:
        - Observability manager for tracing and monitoring
        - Evaluation system for response quality assessment
        - Performance optimizer for system optimization
        
        Exceptions during initialization are caught and logged, allowing the
        application to start even if some systems fail to initialize.
        """
        try:
            # Initialize observability
            observability_manager.initialize()
            observability_manager.instrument_fastapi_app(app)

            # Initialize evaluation system
            evaluation_system.initialize()

            # Initialize performance optimizer
            performance_optimizer.initialize()

            log_info(logger, "Enhanced API systems initialized successfully")

        except Exception as e:
            log_error(logger, "Error initializing systems", e)

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        try:
            performance_optimizer.stop_monitoring()
            log_info(logger, "Enhanced API systems shut down successfully")
        except Exception as e:
            log_error(logger, "Error during shutdown", e)

    # ===================
    # OBSERVABILITY ENDPOINTS
    # ===================

    @app.get("/api/observability/traces")
    async def get_traces():
        """
        Get trace summary from the observability system and execution history.
        
        This endpoint retrieves a summary of all traces collected by the
        observability system and includes recent execution history data.
        
        Returns:
            dict: Summary of collected traces and recent executions
            
        Raises:
            HTTPException: If an error occurs while retrieving traces
        """
        try:
            with observability_manager.trace_workflow("get_traces"):
                # Get observability traces
                trace_summary = observability_manager.get_trace_summary()
                
                # Get recent execution history to supplement traces
                recent_executions = config_manager.get_execution_history(limit=50)
                
                # Convert executions to trace format
                recent_traces = []
                for execution in recent_executions:
                    recent_traces.append({
                        "trace_id": execution['id'],
                        "workflow_name": execution.get('workflow_name', 'Unknown'),
                        "status": execution.get('status', 'unknown'),
                        "execution_time": execution.get('execution_time', 0),
                        "timestamp": execution.get('created_at', ''),
                        "agent_id": execution.get('agent_id', ''),
                        "error_message": execution.get('error_message', ''),
                        "quality_score": execution.get('output', {}).get('quality_score'),
                        "predicted_response_rate": execution.get('output', {}).get('predicted_response_rate')
                    })
                
                # Merge with existing trace summary
                if 'recent_traces' not in trace_summary:
                    trace_summary['recent_traces'] = []
                trace_summary['recent_traces'].extend(recent_traces)
                
                # Update metrics
                total_traces = len(recent_traces)
                errors = len([t for t in recent_traces if t['status'] == 'error'])
                avg_time = sum(t['execution_time'] for t in recent_traces) / total_traces if total_traces > 0 else 0
                
                trace_summary.update({
                    'total_traces': total_traces,
                    'errors': errors,
                    'avg_execution_time': avg_time
                })
                
                return trace_summary
        except Exception as e:
            log_error(logger, "Error getting traces", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/observability/metrics")
    async def get_observability_metrics():
        """
        Get comprehensive observability metrics.
        
        This endpoint retrieves metrics from the observability system, including:
        - Trace summaries
        - Current trace context
        - System initialization status
        - Timestamp of the metrics collection
        
        Returns:
            dict: Observability metrics and status information
            
        Raises:
            HTTPException: If an error occurs while retrieving metrics
        """
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
            log_error(logger, "Error getting observability metrics", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/observability/trace-event")
    async def record_trace_event(
            event_name: str, attributes: Dict[str, Any] = None):
        """
        Record a custom trace event in the observability system.
        
        This endpoint allows recording custom events in the tracing system,
        which can be used to mark important points in the application flow
        or to add custom attributes to traces.
        
        Args:
            event_name (str): Name of the event to record
            attributes (Dict[str, Any], optional): Additional attributes to attach to the event
            
        Returns:
            dict: Status of the event recording operation
            
        Raises:
            HTTPException: If an error occurs while recording the event
        """
        try:
            from observability import record_trace_event

            record_trace_event(event_name, attributes or {})
            return {"status": "success", "event": event_name}
        except Exception as e:
            log_error(logger, "Error recording trace event", e)
            raise HTTPException(status_code=500, detail=str(e))

    # ===================
    # EVALUATION ENDPOINTS
    # ===================

    @app.post("/api/evaluation/single",
              summary="Evaluate a single response",
              description="Evaluate the quality of a single response based on specified metrics",
              response_model=Dict[str, Any],
              responses={
                  200: {"description": "Response evaluated successfully"},
                  400: {"description": "Invalid request parameters"},
                  500: {"description": "Internal server error"}
              })
    async def evaluate_single_response(request: EvaluationRequest):
        """
        Evaluate a single response based on specified metrics.
        
        This endpoint evaluates the quality of a response to a given instruction
        using the specified evaluation metric. It can optionally compare against
        a reference answer for more accurate evaluation.
        
        Args:
            request (EvaluationRequest): The evaluation request containing:
                - instruction: The instruction or question given to the model
                - response: The response to evaluate
                - metric: The evaluation metric to use (accuracy, relevance, etc.)
                - reference_answer: Optional reference answer for comparison
                - context: Optional additional context for evaluation
                
        Returns:
            dict: Evaluation results including:
                - metric: The evaluation metric used
                - score: Numerical score (0-1)
                - feedback: Textual feedback explaining the score
                - confidence: Confidence level in the evaluation
                - execution_time: Time taken for evaluation
                - evaluator: The evaluator model used
                - timestamp: When the evaluation was performed
                
        Raises:
            HTTPException: If evaluation fails or parameters are invalid
        """
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
            log_error(logger, "Error in single evaluation", e)
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
            log_error(logger, "Error in response comparison", e)
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
            log_error(logger, "Error in batch evaluation", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/evaluation/summary",
             summary="Get evaluation summary with pagination",
             description="Retrieve evaluation summary with pagination support")
    async def get_evaluation_summary(
        pagination: dict = Depends(pagination_params)
    ):
        """
        Get evaluation summary with pagination
        
        Args:
            pagination: Pagination parameters (page, page_size)
            
        Returns:
            PaginatedResponse: Paginated evaluation summary
            
        Raises:
            HTTPException: If an error occurs while retrieving the summary
        """
        try:
            # Get all evaluation history from evaluation system
            all_evaluations = evaluation_system.evaluation_history
            
            # Get execution history to supplement evaluation data
            execution_history = config_manager.get_execution_history(limit=100)
            
            # Convert execution history to evaluation format
            execution_evaluations = []
            for execution in execution_history:
                output = execution.get('output', {})
                quality_score = output.get('quality_score')
                predicted_rate = output.get('predicted_response_rate')
                
                if quality_score is not None:
                    execution_evaluations.append({
                        "metric": "quality_score",
                        "score": quality_score,
                        "feedback": f"Workflow execution quality assessment",
                        "confidence": predicted_rate if predicted_rate else 0.8,
                        "execution_time": execution.get('execution_time', 0),
                        "evaluator": "workflow_system",
                        "timestamp": execution.get('created_at', ''),
                        "execution_id": execution.get('id', ''),
                        "workflow_name": execution.get('workflow_name', 'Unknown')
                    })
            
            # Combine evaluation system data with execution data
            combined_evaluations = all_evaluations + execution_evaluations
            total_evaluations = len(combined_evaluations)
            
            if total_evaluations == 0:
                return {
                    "items": [],
                    "pagination": {
                        "total": 0,
                        "page": pagination["page"],
                        "page_size": pagination["page_size"],
                        "total_pages": 0,
                        "has_next": False,
                        "has_prev": False
                    },
                    "summary": {
                        "message": "No evaluation results available"
                    }
                }
            
            # Calculate averages
            numeric_scores = []
            execution_times = []
            
            for r in combined_evaluations:
                # Handle both evaluation objects and dictionaries
                if hasattr(r, 'score'):
                    score = r.score
                    exec_time = r.execution_time
                else:
                    score = r.get('score', 0)
                    exec_time = r.get('execution_time', 0)
                    
                if isinstance(score, (int, float)):
                    numeric_scores.append(score)
                if isinstance(exec_time, (int, float)):
                    execution_times.append(exec_time)
            
            avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Group by metric
            metric_stats = {}
            for result in combined_evaluations:
                # Handle both evaluation objects and dictionaries
                if hasattr(result, 'metric'):
                    metric = result.metric.value
                    score = result.score
                else:
                    metric = result.get('metric', 'unknown')
                    score = result.get('score', 0)
                    
                if metric not in metric_stats:
                    metric_stats[metric] = {
                        "count": 0, "avg_score": 0, "scores": []
                    }
                
                metric_stats[metric]["count"] += 1
                if isinstance(score, (int, float)):
                    metric_stats[metric]["scores"].append(score)
            
            # Calculate averages for each metric
            for metric, stats in metric_stats.items():
                if stats["scores"]:
                    stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"])
            
            # Create detailed evaluation list for pagination
            detailed_evaluations = []
            
            # Add evaluation system results
            for r in all_evaluations:
                detailed_evaluations.append({
                    "metric": r.metric.value,
                    "score": r.score,
                    "feedback": r.feedback,
                    "confidence": r.confidence,
                    "execution_time": r.execution_time,
                    "evaluator": r.evaluator,
                    "timestamp": r.timestamp.isoformat()
                })
            
            # Add execution evaluations
            for r in execution_evaluations:
                detailed_evaluations.append(r)
            
            # Apply pagination to detailed evaluations
            paginated_response = Paginator.paginate_list(
                items=detailed_evaluations,
                page=pagination["page"],
                page_size=pagination["page_size"]
            )
            
            # Add summary statistics to response
            result = paginated_response.dict()
            result["summary"] = {
                "total_evaluations": total_evaluations,
                "average_score": avg_score,
                "average_execution_time": avg_execution_time,
                "metric_statistics": metric_stats
            }
            
            return result
        except Exception as e:
            log_error(logger, "Error getting evaluation summary", e)
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
            log_error(logger, "Error during optimization", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/optimization/model-compression",
              summary="Optimize model compression",
              description="Compress a model to reduce its size while maintaining performance",
              response_model=Dict[str, Any],
              responses={
                  200: {"description": "Model compression completed successfully"},
                  400: {"description": "Invalid compression parameters"},
                  500: {"description": "Internal server error"}
              })
    async def optimize_model_compression(
        model_path: str = "default_model",
        compression_ratio: float = 0.5,
        method: str = "pruning",
    ):
        """
        Optimize model compression to reduce model size.
        
        This endpoint compresses a machine learning model to reduce its size
        while attempting to maintain its performance. Various compression
        methods are supported, including pruning, quantization, and distillation.
        
        Args:
            model_path (str): Path to the model to compress. Defaults to "default_model".
            compression_ratio (float): Target compression ratio (0.0-1.0). Defaults to 0.5.
            method (str): Compression method to use. Defaults to "pruning".
                
        Returns:
            dict: Compression results including:
                - optimization_type: Type of optimization performed
                - original_metric: Original model size or performance metric
                - optimized_metric: Compressed model size or performance metric
                - improvement_ratio: Ratio of improvement
                - execution_time: Time taken for compression
                - memory_saved: Amount of memory saved
                - success: Whether compression was successful
                - details: Additional details about the compression
                
        Raises:
            HTTPException: If model compression fails
        """
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
            log_error(logger, "Error in model compression", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/optimization/inference-acceleration",
              summary="Optimize inference speed",
              description="Accelerate model inference speed through various optimization techniques",
              response_model=Dict[str, Any],
              responses={
                  200: {"description": "Inference acceleration completed successfully"},
                  400: {"description": "Invalid acceleration parameters"},
                  500: {"description": "Internal server error"}
              })
    async def optimize_inference_speed(
        model_name: str = "default_model", optimization_level: str = "moderate"
    ):
        """
        Optimize inference speed to accelerate model predictions.
        
        This endpoint applies various optimization techniques to accelerate
        model inference speed, such as operator fusion, kernel optimization,
        and hardware-specific optimizations.
        
        Args:
            model_name (str): Name of the model to optimize. Defaults to "default_model".
            optimization_level (str): Level of optimization to apply. Defaults to "moderate".
                Options include "light", "moderate", "aggressive".
                
        Returns:
            dict: Acceleration results including:
                - optimization_type: Type of optimization performed
                - original_latency_ms: Original inference latency in milliseconds
                - optimized_latency_ms: Optimized inference latency in milliseconds
                - speedup: Speedup factor achieved
                - execution_time: Time taken for optimization
                - success: Whether acceleration was successful
                - details: Additional details about the acceleration
                
        Raises:
            HTTPException: If inference acceleration fails
        """
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
            log_error(logger, "Error in inference acceleration", e)
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
            log_error(logger, "Error in memory optimization", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/optimization/summary",
             summary="Get optimization summary with pagination",
             description="Retrieve optimization summary with pagination support")
    async def get_optimization_summary(
        pagination: dict = Depends(pagination_params)
    ):
        """
        Get optimization summary with pagination
        
        Args:
            pagination: Pagination parameters (page, page_size)
            
        Returns:
            PaginatedResponse: Paginated optimization summary
            
        Raises:
            HTTPException: If an error occurs while retrieving the summary
        """
        try:
            # Get all optimization history
            all_optimizations = performance_optimizer.optimization_history
            
            # Get summary statistics (not paginated)
            total_optimizations = len(all_optimizations)
            successful = sum(1 for opt in all_optimizations if opt.success)
            success_rate = successful / total_optimizations if total_optimizations > 0 else 0
            
            # Create detailed optimization list for pagination
            detailed_optimizations = [
                {
                    "optimization_type": opt.optimization_type.value,
                    "original_metric": opt.original_metric,
                    "optimized_metric": opt.optimized_metric,
                    "improvement_ratio": opt.improvement_ratio,
                    "execution_time": opt.execution_time,
                    "memory_saved": opt.memory_saved,
                    "success": opt.success,
                    "details": opt.details,
                    "timestamp": opt.timestamp.isoformat()
                }
                for opt in all_optimizations
            ]
            
            # Apply pagination to detailed optimizations
            paginated_response = Paginator.paginate_list(
                items=detailed_optimizations,
                page=pagination["page"],
                page_size=pagination["page_size"]
            )
            
            # Add summary statistics to response
            result = paginated_response.dict()
            result["summary"] = {
                "total_optimizations": total_optimizations,
                "successful_optimizations": successful,
                "success_rate": success_rate,
                "optimization_types": list(set(opt.optimization_type.value for opt in all_optimizations))
            }
            
            return result
        except Exception as e:
            log_error(logger, "Error getting optimization summary", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/optimization/performance-metrics")
    async def get_performance_metrics():
        """Get current performance metrics"""
        try:
            return performance_optimizer.get_performance_metrics()
        except Exception as e:
            log_error(logger, "Error getting performance metrics", e)
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
    
    @app.get("/api/execution-history",
             summary="Get workflow execution history with pagination",
             description="Retrieve workflow execution history with pagination support")
    async def get_execution_history(
        pagination: dict = Depends(pagination_params)
    ):
        """
        Get workflow execution history with pagination
        
        Args:
            pagination: Pagination parameters (page, page_size)
            
        Returns:
            PaginatedResponse: Paginated execution history
            
        Raises:
            HTTPException: If an error occurs while retrieving the history
        """
        try:
            # Get total count for pagination
            total_count = config_manager.get_execution_history_count()
            
            # Calculate offset based on pagination parameters
            page = pagination["page"]
            page_size = pagination["page_size"]
            offset = (page - 1) * page_size
            
            # Get execution history with pagination
            execution_history = config_manager.get_execution_history(
                limit=page_size,
                offset=offset
            )
            
            # Create paginated response
            paginated_response = {
                "items": execution_history,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": page * page_size < total_count,
                    "has_prev": page > 1
                }
            }
            
            return paginated_response
        except Exception as e:
            log_error(logger, "Error getting execution history", e)
            raise HTTPException(status_code=500, detail=str(e))

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
            log_error(logger, "Error in monitored workflow execution", e)
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

    # Configuration endpoints
    @app.get("/api/config/agents",
             summary="Get all agent configurations",
             description="Retrieve all agent configurations")
    async def get_agents():
        """
        Get all agent configurations
        
        Returns:
            List of agent configurations
        """
        try:
            agents = config_manager.list_agents()
            return [{"id": agent.id, "name": agent.name, "role": agent.role, 
                    "goal": agent.goal, "backstory": agent.backstory,
                    "created_at": agent.created_at, "updated_at": agent.updated_at,
                    "version": agent.version} for agent in agents]
        except Exception as e:
            log_error(logger, "Error getting agents", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/config/prompts",
             summary="Get all prompt templates",
             description="Retrieve all prompt templates")
    async def get_prompts():
        """
        Get all prompt templates
        
        Returns:
            List of prompt templates
        """
        try:
            prompts = config_manager.list_prompts()
            return [{"id": prompt.id, "name": prompt.name, "description": prompt.description,
                    "category": prompt.category, "channel": prompt.channel,
                    "created_at": prompt.created_at, "updated_at": prompt.updated_at,
                    "version": prompt.version} for prompt in prompts]
        except Exception as e:
            log_error(logger, "Error getting prompts", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/test-results",
             summary="Get test results",
             description="Retrieve test results for entities")
    async def get_test_results(entity_type: str = "agent", entity_id: str = "default", limit: int = 10):
        """
        Get test results for an entity
        
        Args:
            entity_type: Type of entity (agent, prompt, workflow)
            entity_id: ID of the entity
            limit: Maximum number of results to return
            
        Returns:
            List of test results
        """
        try:
            results = config_manager.get_test_results(entity_type, entity_id, limit)
            return results
        except Exception as e:
            log_error(logger, "Error getting test results", e)
            raise HTTPException(status_code=500, detail=str(e))

    return app


# Create the enhanced app
app = create_enhanced_api()
