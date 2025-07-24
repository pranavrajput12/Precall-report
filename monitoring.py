"""
Comprehensive monitoring setup with Sentry and OpenTelemetry for CrewAI Workflow Platform.

This module provides centralized monitoring, error tracking, and observability
with production-ready configuration and automatic instrumentation.
"""

import os
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from functools import wraps

# Sentry imports
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

from config_system import config_system
from logging_config import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)


class MonitoringConfig:
    """Monitoring configuration management"""
    
    def __init__(self):
        """Initialize monitoring configuration"""
        observability_config = config_system.get("observability", {})
        
        # Sentry configuration
        self.sentry_dsn = os.getenv("SENTRY_DSN") or observability_config.get("sentry_dsn")
        self.sentry_environment = os.getenv("CREWAI_ENV", "development")
        self.sentry_release = observability_config.get("release", "1.0.0")
        self.sentry_sample_rate = observability_config.get("sentry_sample_rate", 1.0)
        self.sentry_traces_sample_rate = observability_config.get("sentry_traces_sample_rate", 0.1)
        self.sentry_profiles_sample_rate = observability_config.get("sentry_profiles_sample_rate", 0.1)
        
        # OpenTelemetry configuration
        self.otel_enabled = observability_config.get("otel_enabled", True)
        self.otel_service_name = observability_config.get("service_name", "crewai-workflow-platform")
        self.otel_service_version = observability_config.get("service_version", "1.0.0")
        self.trace_sample_rate = observability_config.get("trace_sample_rate", 1.0)
        
        # Exporter configuration
        self.exporter_type = observability_config.get("exporter", "console")  # console, jaeger, otlp
        self.jaeger_endpoint = observability_config.get("jaeger_endpoint", "http://localhost:14268/api/traces")
        self.otlp_endpoint = observability_config.get("otlp_endpoint", "http://localhost:4317")
        
        # Metrics configuration
        self.metrics_enabled = observability_config.get("metrics_enabled", True)
        self.metrics_port = observability_config.get("metrics_port", 8090)
        self.metrics_interval = observability_config.get("metrics_interval", 10)
        
        # Performance monitoring
        self.enable_performance_monitoring = observability_config.get("enable_performance_monitoring", True)
        self.slow_query_threshold = observability_config.get("slow_query_threshold", 1.0)  # seconds
        self.memory_threshold = observability_config.get("memory_threshold", 0.8)  # 80%


class SentryManager:
    """Sentry error tracking and performance monitoring"""
    
    def __init__(self, config: MonitoringConfig):
        """
        Initialize Sentry manager
        
        Args:
            config: Monitoring configuration
        """
        self.config = config
        self.initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize Sentry SDK
        
        Returns:
            bool: True if initialized successfully, False otherwise
        """
        if not self.config.sentry_dsn:
            log_warning(logger, "Sentry DSN not configured, skipping Sentry initialization")
            return False
            
        try:
            # Configure Sentry integrations
            integrations = [
                FastApiIntegration(auto_enabling_integrations=True),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(),
                LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                )
            ]
            
            # Initialize Sentry
            sentry_sdk.init(
                dsn=self.config.sentry_dsn,
                environment=self.config.sentry_environment,
                release=self.config.sentry_release,
                sample_rate=self.config.sentry_sample_rate,
                traces_sample_rate=self.config.sentry_traces_sample_rate,
                profiles_sample_rate=self.config.sentry_profiles_sample_rate,
                integrations=integrations,
                attach_stacktrace=True,
                send_default_pii=False,  # Don't send PII for privacy
                max_breadcrumbs=50,
                before_send=self._before_send_filter,
                before_send_transaction=self._before_send_transaction_filter
            )
            
            self.initialized = True
            log_info(logger, f"Sentry initialized successfully for environment: {self.config.sentry_environment}")
            
            # Test Sentry connection
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("component", "monitoring")
                scope.set_context("startup", {"timestamp": datetime.utcnow().isoformat()})
                
            return True
            
        except Exception as e:
            log_error(logger, f"Failed to initialize Sentry: {str(e)}")
            return False
    
    def _before_send_filter(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Filter events before sending to Sentry
        
        Args:
            event: Sentry event
            hint: Event hint
            
        Returns:
            Optional[Dict[str, Any]]: Filtered event or None to drop
        """
        # Filter out sensitive information
        if 'request' in event:
            headers = event['request'].get('headers', {})
            # Remove authorization headers
            if 'Authorization' in headers:
                headers['Authorization'] = '[Filtered]'
            if 'X-API-Key' in headers:
                headers['X-API-Key'] = '[Filtered]'
                
        # Filter out test events in development
        if self.config.sentry_environment == 'development':
            if event.get('transaction') and 'test' in event['transaction'].lower():
                return None
                
        return event
    
    def _before_send_transaction_filter(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Filter transactions before sending to Sentry
        
        Args:
            event: Sentry transaction event
            hint: Event hint
            
        Returns:
            Optional[Dict[str, Any]]: Filtered event or None to drop
        """
        # Skip health check transactions
        if event.get('transaction') in ['/health', '/api/health', '/metrics']:
            return None
            
        return event
    
    def capture_exception(self, exception: Exception, **kwargs) -> str:
        """
        Capture exception to Sentry
        
        Args:
            exception: Exception to capture
            **kwargs: Additional context
            
        Returns:
            str: Event ID
        """
        if not self.initialized:
            return ""
            
        with sentry_sdk.push_scope() as scope:
            for key, value in kwargs.items():
                scope.set_context(key, value)
                
            return sentry_sdk.capture_exception(exception)
    
    def capture_message(self, message: str, level: str = "info", **kwargs) -> str:
        """
        Capture message to Sentry
        
        Args:
            message: Message to capture
            level: Log level
            **kwargs: Additional context
            
        Returns:
            str: Event ID
        """
        if not self.initialized:
            return ""
            
        with sentry_sdk.push_scope() as scope:
            for key, value in kwargs.items():
                scope.set_context(key, value)
                
            return sentry_sdk.capture_message(message, level)


class OpenTelemetryManager:
    """OpenTelemetry tracing and metrics management"""
    
    def __init__(self, config: MonitoringConfig):
        """
        Initialize OpenTelemetry manager
        
        Args:
            config: Monitoring configuration
        """
        self.config = config
        self.tracer_provider = None
        self.meter_provider = None
        self.tracer = None
        self.meter = None
        self.initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize OpenTelemetry SDK
        
        Returns:
            bool: True if initialized successfully, False otherwise
        """
        if not self.config.otel_enabled:
            log_info(logger, "OpenTelemetry disabled in configuration")
            return False
            
        try:
            # Create resource
            resource = Resource.create({
                "service.name": self.config.otel_service_name,
                "service.version": self.config.otel_service_version,
                "service.instance.id": os.getenv("HOSTNAME", "unknown"),
                "deployment.environment": os.getenv("CREWAI_ENV", "development")
            })
            
            # Initialize tracing
            self._initialize_tracing(resource)
            
            # Initialize metrics
            if self.config.metrics_enabled:
                self._initialize_metrics(resource)
            
            # Auto-instrument libraries
            self._setup_auto_instrumentation()
            
            self.initialized = True
            log_info(logger, f"OpenTelemetry initialized successfully with {self.config.exporter_type} exporter")
            
            return True
            
        except Exception as e:
            log_error(logger, f"Failed to initialize OpenTelemetry: {str(e)}")
            return False
    
    def _initialize_tracing(self, resource: Resource):
        """
        Initialize OpenTelemetry tracing
        
        Args:
            resource: OpenTelemetry resource
        """
        # Create tracer provider
        self.tracer_provider = TracerProvider(
            resource=resource,
            sampler=trace.sampling.TraceIdRatioBased(self.config.trace_sample_rate)
        )
        
        # Create exporter based on configuration
        if self.config.exporter_type == "jaeger":
            exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )
        elif self.config.exporter_type == "otlp":
            exporter = OTLPSpanExporter(
                endpoint=self.config.otlp_endpoint,
                insecure=True
            )
        else:
            # Console exporter for development
            from opentelemetry.exporter.console import ConsoleSpanExporter
            exporter = ConsoleSpanExporter()
        
        # Add span processor
        span_processor = BatchSpanProcessor(exporter)
        self.tracer_provider.add_span_processor(span_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
    
    def _initialize_metrics(self, resource: Resource):
        """
        Initialize OpenTelemetry metrics
        
        Args:
            resource: OpenTelemetry resource
        """
        # Create metric readers
        readers = []
        
        if self.config.exporter_type != "console":
            # Prometheus metrics reader
            prometheus_reader = PrometheusMetricReader(port=self.config.metrics_port)
            readers.append(prometheus_reader)
        
        # Create meter provider
        self.meter_provider = MeterProvider(
            resource=resource,
            metric_readers=readers
        )
        
        # Set global meter provider
        metrics.set_meter_provider(self.meter_provider)
        
        # Get meter
        self.meter = metrics.get_meter(__name__)
    
    def _setup_auto_instrumentation(self):
        """Setup automatic instrumentation for common libraries"""
        try:
            # Instrument FastAPI
            FastAPIInstrumentor().instrument()
            
            # Instrument Redis
            RedisInstrumentor().instrument()
            
            # Instrument SQLAlchemy
            SQLAlchemyInstrumentor().instrument()
            
            # Instrument HTTP requests
            RequestsInstrumentor().instrument()
            
            log_info(logger, "Auto-instrumentation setup completed")
            
        except Exception as e:
            log_warning(logger, f"Some auto-instrumentation failed: {str(e)}")
    
    def create_span(self, name: str, **kwargs):
        """
        Create a new span
        
        Args:
            name: Span name
            **kwargs: Additional span attributes
            
        Returns:
            Span context manager
        """
        if not self.tracer:
            from contextlib import nullcontext
            return nullcontext()
            
        return self.tracer.start_as_current_span(name, attributes=kwargs)
    
    def add_span_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add event to current span
        
        Args:
            name: Event name
            attributes: Event attributes
        """
        if not self.tracer:
            return
            
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes or {})


class MonitoringManager:
    """Centralized monitoring manager"""
    
    def __init__(self):
        """Initialize monitoring manager"""
        self.config = MonitoringConfig()
        self.sentry = SentryManager(self.config)
        self.otel = OpenTelemetryManager(self.config)
        self.initialized = False
        
        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()
        
    def initialize(self) -> bool:
        """
        Initialize all monitoring systems
        
        Returns:
            bool: True if at least one system initialized successfully
        """
        sentry_ok = self.sentry.initialize()
        otel_ok = self.otel.initialize()
        
        self.initialized = sentry_ok or otel_ok
        
        if self.initialized:
            log_info(logger, "Monitoring systems initialized successfully")
            
            # Set up custom metrics if OpenTelemetry is available
            if otel_ok and self.otel.meter:
                self._setup_custom_metrics()
        else:
            log_warning(logger, "No monitoring systems could be initialized")
            
        return self.initialized
    
    def _setup_custom_metrics(self):
        """Setup custom application metrics"""
        try:
            # Request counter
            self.request_counter = self.otel.meter.create_counter(
                name="crewai_requests_total",
                description="Total number of requests processed",
                unit="1"
            )
            
            # Error counter
            self.error_counter = self.otel.meter.create_counter(
                name="crewai_errors_total",
                description="Total number of errors occurred",
                unit="1"
            )
            
            # Workflow duration histogram
            self.workflow_duration = self.otel.meter.create_histogram(
                name="crewai_workflow_duration_seconds",
                description="Duration of workflow executions",
                unit="s"
            )
            
            # Active connections gauge
            self.active_connections = self.otel.meter.create_up_down_counter(
                name="crewai_active_connections",
                description="Number of active connections",
                unit="1"
            )
            
            log_info(logger, "Custom metrics setup completed")
            
        except Exception as e:
            log_warning(logger, f"Failed to setup custom metrics: {str(e)}")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """
        Record request metrics
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: Response status code
            duration: Request duration in seconds
        """
        self.request_count += 1
        
        if hasattr(self, 'request_counter'):
            self.request_counter.add(1, {
                "method": method,
                "endpoint": endpoint,
                "status_code": str(status_code)
            })
    
    def record_error(self, error_type: str, component: str):
        """
        Record error metrics
        
        Args:
            error_type: Type of error
            component: Component where error occurred
        """
        self.error_count += 1
        
        if hasattr(self, 'error_counter'):
            self.error_counter.add(1, {
                "error_type": error_type,
                "component": component
            })
    
    def record_workflow_duration(self, workflow_id: str, duration: float, success: bool):
        """
        Record workflow execution duration
        
        Args:
            workflow_id: Workflow identifier
            duration: Execution duration in seconds
            success: Whether workflow succeeded
        """
        if hasattr(self, 'workflow_duration'):
            self.workflow_duration.record(duration, {
                "workflow_id": workflow_id,
                "success": str(success)
            })
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get monitoring health status
        
        Returns:
            Dict[str, Any]: Health status
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "monitoring_initialized": self.initialized,
            "sentry_initialized": self.sentry.initialized,
            "opentelemetry_initialized": self.otel.initialized,
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "config": {
                "sentry_environment": self.config.sentry_environment,
                "service_name": self.config.otel_service_name,
                "exporter_type": self.config.exporter_type
            }
        }


# Global monitoring manager instance
monitoring_manager = None

def get_monitoring_manager() -> MonitoringManager:
    """
    Get global monitoring manager instance
    
    Returns:
        MonitoringManager: Monitoring manager instance
    """
    global monitoring_manager
    if monitoring_manager is None:
        monitoring_manager = MonitoringManager()
    return monitoring_manager

def monitor_performance(func_name: str = None):
    """
    Decorator to monitor function performance
    
    Args:
        func_name: Optional custom function name
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = get_monitoring_manager()
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            start_time = datetime.utcnow()
            
            with manager.otel.create_span(name) as span:
                try:
                    if span:
                        span.set_attribute("function.name", name)
                        span.set_attribute("function.args_count", len(args))
                        span.set_attribute("function.kwargs_count", len(kwargs))
                    
                    result = await func(*args, **kwargs)
                    
                    if span:
                        span.set_attribute("function.success", True)
                    
                    return result
                    
                except Exception as e:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    if span:
                        span.set_attribute("function.success", False)
                        span.set_attribute("function.error", str(e))
                    
                    manager.record_error(type(e).__name__, name)
                    manager.sentry.capture_exception(e, function=name, duration=duration)
                    
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = get_monitoring_manager()
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            start_time = datetime.utcnow()
            
            with manager.otel.create_span(name) as span:
                try:
                    if span:
                        span.set_attribute("function.name", name)
                        span.set_attribute("function.args_count", len(args))
                        span.set_attribute("function.kwargs_count", len(kwargs))
                    
                    result = func(*args, **kwargs)
                    
                    if span:
                        span.set_attribute("function.success", True)
                    
                    return result
                    
                except Exception as e:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    if span:
                        span.set_attribute("function.success", False)
                        span.set_attribute("function.error", str(e))
                    
                    manager.record_error(type(e).__name__, name)
                    manager.sentry.capture_exception(e, function=name, duration=duration)
                    
                    raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator