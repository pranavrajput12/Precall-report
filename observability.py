"""
Enhanced Observability & Traceability System
Integrates Langtrace, OpenTelemetry, and custom metrics for comprehensive monitoring
"""

import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

# Langtrace imports
from langtrace_python_sdk import langtrace
# OpenTelemetry imports
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import \
    OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Local imports

logger = logging.getLogger(__name__)


class ObservabilityManager:
    """Comprehensive observability system with tracing, metrics, and monitoring"""

    def __init__(self):
        self.tracer = None
        self.meter = None
        self.metrics = {}
        self.traces = []
        self.is_initialized = False

    def initialize(self):
        """Initialize all observability components"""
        if self.is_initialized:
            return

        try:
            # Initialize OpenTelemetry
            self._setup_opentelemetry()

            # Initialize Langtrace
            self._setup_langtrace()

            # Setup custom metrics
            self._setup_custom_metrics()

            # Instrument frameworks
            self._instrument_frameworks()

            self.is_initialized = True
            logger.info("Observability system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize observability: {e}")

    def _setup_opentelemetry(self):
        """Setup OpenTelemetry tracing and metrics"""
        # Configure trace provider
        trace.set_tracer_provider(TracerProvider())

        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv(
                "OTEL_EXPORTER_OTLP_ENDPOINT",
                "http://localhost:4317"),
            headers=self._get_otlp_headers(),
        )

        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

        # Configure metrics
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(
                endpoint=os.getenv(
                    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
                ),
                headers=self._get_otlp_headers(),
            ),
            export_interval_millis=5000,
        )

        metrics.set_meter_provider(
            MeterProvider(
                metric_readers=[metric_reader]))
        self.meter = metrics.get_meter(__name__)

    def _setup_langtrace(self):
        """Setup Langtrace for LLM observability"""
        api_key = os.getenv("LANGTRACE_API_KEY")
        if api_key:
            langtrace.init(api_key=api_key)
            logger.info("Langtrace initialized with API key")
        else:
            # Initialize without API key for local development
            langtrace.init()
            logger.info("Langtrace initialized in local mode")

    def _setup_custom_metrics(self):
        """Setup custom metrics for CrewAI workflow monitoring"""
        if not self.meter:
            return

        # Workflow metrics
        self.metrics["workflow_duration"] = self.meter.create_histogram(
            "workflow_duration_seconds",
            description="Duration of workflow execution",
            unit="s",
        )

        self.metrics["workflow_success"] = self.meter.create_counter(
            "workflow_success_total",
            description="Total number of successful workflow executions",
        )

        self.metrics["workflow_errors"] = self.meter.create_counter(
            "workflow_errors_total", description="Total number of workflow errors")

        # Agent metrics
        self.metrics["agent_execution_time"] = self.meter.create_histogram(
            "agent_execution_time_seconds",
            description="Time taken for agent execution",
            unit="s",
        )

        self.metrics["agent_token_usage"] = self.meter.create_histogram(
            "agent_token_usage_total", description="Total tokens used by agents")

        # LLM metrics
        self.metrics["llm_requests"] = self.meter.create_counter(
            "llm_requests_total", description="Total number of LLM requests"
        )

        self.metrics["llm_response_time"] = self.meter.create_histogram(
            "llm_response_time_seconds", description="LLM response time", unit="s")

        # Cache metrics
        self.metrics["cache_hits"] = self.meter.create_counter(
            "cache_hits_total", description="Total number of cache hits"
        )

        self.metrics["cache_misses"] = self.meter.create_counter(
            "cache_misses_total", description="Total number of cache misses"
        )

    def _instrument_frameworks(self):
        """Instrument FastAPI, requests, and Redis"""
        try:
            # Instrument requests
            RequestsInstrumentor().instrument()

            # Instrument Redis
            RedisInstrumentor().instrument()

            logger.info("Framework instrumentation completed")

        except Exception as e:
            logger.warning(f"Framework instrumentation failed: {e}")

    def _get_otlp_headers(self) -> Dict[str, str]:
        """Get OTLP headers from environment"""
        headers_str = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
        headers = {}

        if headers_str:
            for header in headers_str.split(","):
                if "=" in header:
                    key, value = header.split("=", 1)
                    headers[key.strip()] = value.strip()

        return headers

    @contextmanager
    def trace_workflow(self, workflow_name: str, **attributes):
        """Context manager for tracing workflow execution"""
        if not self.tracer:
            yield
            return

        with self.tracer.start_as_current_span(
            f"workflow.{workflow_name}", attributes=attributes
        ) as span:
            start_time = time.time()
            success = False

            try:
                yield span
                success = True

            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

            finally:
                duration = time.time() - start_time
                span.set_attribute("workflow.duration", duration)
                span.set_attribute("workflow.success", success)

                # Record metrics
                if self.metrics.get("workflow_duration"):
                    self.metrics["workflow_duration"].record(
                        duration, {"workflow": workflow_name}
                    )

                if success and self.metrics.get("workflow_success"):
                    self.metrics["workflow_success"].add(
                        1, {"workflow": workflow_name})
                elif not success and self.metrics.get("workflow_errors"):
                    self.metrics["workflow_errors"].add(
                        1, {"workflow": workflow_name})

    @contextmanager
    def trace_agent(
            self,
            agent_id: str,
            task_description: str = "",
            **attributes):
        """Context manager for tracing agent execution"""
        if not self.tracer:
            yield
            return

        with self.tracer.start_as_current_span(
            f"agent.{agent_id}",
            attributes={
                "agent.id": agent_id,
                "agent.task": task_description,
                **attributes,
            },
        ) as span:
            start_time = time.time()

            try:
                yield span

            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

            finally:
                duration = time.time() - start_time
                span.set_attribute("agent.execution_time", duration)

                # Record metrics
                if self.metrics.get("agent_execution_time"):
                    self.metrics["agent_execution_time"].record(
                        duration, {"agent_id": agent_id}
                    )

    @contextmanager
    def trace_llm_request(
            self,
            model: str,
            prompt_tokens: int = 0,
            **attributes):
        """Context manager for tracing LLM requests"""
        if not self.tracer:
            yield
            return

        with self.tracer.start_as_current_span(
            f"llm.request",
            attributes={
                "llm.model": model,
                "llm.prompt_tokens": prompt_tokens,
                **attributes,
            },
        ) as span:
            start_time = time.time()

            try:
                yield span

                # Record successful request
                if self.metrics.get("llm_requests"):
                    self.metrics["llm_requests"].add(
                        1, {"model": model, "status": "success"}
                    )

            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)

                # Record failed request
                if self.metrics.get("llm_requests"):
                    self.metrics["llm_requests"].add(
                        1, {"model": model, "status": "error"}
                    )

                raise

            finally:
                duration = time.time() - start_time
                span.set_attribute("llm.response_time", duration)

                # Record metrics
                if self.metrics.get("llm_response_time"):
                    self.metrics["llm_response_time"].record(
                        duration, {"model": model})

    def record_cache_hit(self, cache_type: str, key: str):
        """Record cache hit metric"""
        if self.metrics.get("cache_hits"):
            self.metrics["cache_hits"].add(1, {"cache_type": cache_type})

        if self.tracer:
            with self.tracer.start_as_current_span("cache.hit") as span:
                span.set_attributes(
                    {"cache.type": cache_type, "cache.key": key, "cache.result": "hit"}
                )

    def record_cache_miss(self, cache_type: str, key: str):
        """Record cache miss metric"""
        if self.metrics.get("cache_misses"):
            self.metrics["cache_misses"].add(1, {"cache_type": cache_type})

        if self.tracer:
            with self.tracer.start_as_current_span("cache.miss") as span:
                span.set_attributes(
                    {"cache.type": cache_type, "cache.key": key, "cache.result": "miss"}
                )

    def record_token_usage(
        self, agent_id: str, prompt_tokens: int, completion_tokens: int
    ):
        """Record token usage metrics"""
        total_tokens = prompt_tokens + completion_tokens

        if self.metrics.get("agent_token_usage"):
            self.metrics["agent_token_usage"].record(
                total_tokens, {"agent_id": agent_id}
            )

        if self.tracer:
            with self.tracer.start_as_current_span("tokens.usage") as span:
                span.set_attributes(
                    {
                        "tokens.agent_id": agent_id,
                        "tokens.prompt": prompt_tokens,
                        "tokens.completion": completion_tokens,
                        "tokens.total": total_tokens,
                    }
                )

    def get_trace_summary(self) -> Dict[str, Any]:
        """Get summary of recent traces"""
        return {
            "total_traces": len(self.traces),
            "recent_traces": self.traces[-10:] if self.traces else [],
            "timestamp": datetime.now().isoformat(),
        }

    def instrument_fastapi_app(self, app):
        """Instrument FastAPI application"""
        if not self.is_initialized:
            self.initialize()

        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumentation completed")
        except Exception as e:
            logger.warning(f"FastAPI instrumentation failed: {e}")


# Global observability manager instance
observability_manager = ObservabilityManager()


# Decorator for tracing functions
def trace_function(span_name: str = None, **span_attributes):
    """Decorator for tracing function execution"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not observability_manager.is_initialized:
                return func(*args, **kwargs)

            name = span_name or f"{func.__module__}.{func.__name__}"

            with observability_manager.tracer.start_as_current_span(
                name, attributes=span_attributes
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    span.set_status(
                        trace.Status(
                            trace.StatusCode.ERROR,
                            str(e)))
                    span.record_exception(e)
                    span.set_attribute("function.success", False)
                    raise

        return wrapper

    return decorator


# Utility functions
def get_current_trace_id() -> Optional[str]:
    """Get current trace ID"""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None


def add_trace_attribute(key: str, value: Any):
    """Add attribute to current span"""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        span.set_attribute(key, value)


def record_trace_event(name: str, attributes: Dict[str, Any] = None):
    """Record event in current span"""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        span.add_event(name, attributes or {})
