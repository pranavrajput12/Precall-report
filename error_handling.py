"""
Standardized Error Handling for CrewAI Workflow Orchestration Platform.

This module provides a consistent approach to error handling across the application,
with standardized error classes, logging, and conversion to API responses.
"""

from typing import Dict, Any, Optional, Type, Callable
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
import logging
import traceback
import json
from functools import wraps

from config_system import config_system
from logging_config import log_error, log_warning, log_info, log_debug

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base application error class for standardized error handling"""
    status_code: int = 500
    error_code: str = "internal_error"
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize application error.
        
        Args:
            message (str): Human-readable error message
            details (Optional[Dict[str, Any]], optional): Additional error details. Defaults to None.
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary for API response.
        
        Returns:
            Dict[str, Any]: Error details in a standardized format
        """
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }
    
    def log(self, log_level: int = logging.ERROR):
        """
        Log the error with appropriate level.
        
        Args:
            log_level (int, optional): Logging level. Defaults to logging.ERROR.
        """
        details_str = json.dumps(self.details) if self.details else ""
        error_msg = f"{self.error_code}: {self.message}"
        if details_str:
            error_msg += f" - Details: {details_str}"
        log_error(logger, error_msg)


class ValidationError(AppError):
    """Validation error for invalid input data"""
    status_code = 400
    error_code = "validation_error"


class NotFoundError(AppError):
    """Resource not found error"""
    status_code = 404
    error_code = "not_found"


class AuthenticationError(AppError):
    """Authentication error for invalid credentials"""
    status_code = 401
    error_code = "authentication_error"


class AuthorizationError(AppError):
    """Authorization error for insufficient permissions"""
    status_code = 403
    error_code = "authorization_error"


class ConfigurationError(AppError):
    """Configuration error for missing or invalid configuration"""
    status_code = 500
    error_code = "configuration_error"


class ExternalServiceError(AppError):
    """External service error for failures in external dependencies"""
    status_code = 502
    error_code = "external_service_error"


class RateLimitError(AppError):
    """Rate limit exceeded error"""
    status_code = 429
    error_code = "rate_limit_exceeded"


class WorkflowError(AppError):
    """Workflow execution error"""
    status_code = 500
    error_code = "workflow_error"


def handle_app_error(error: AppError) -> HTTPException:
    """
    Convert AppError to FastAPI HTTPException.
    
    Args:
        error (AppError): Application error
        
    Returns:
        HTTPException: FastAPI HTTP exception
    """
    error.log()
    return HTTPException(
        status_code=error.status_code,
        detail=error.to_dict()
    )


def safe_execute(func: Callable, error_message: str, fallback_value: Any = None, 
                 error_class: Type[AppError] = AppError, log_exception: bool = True):
    """
    Safely execute a function with standardized error handling.
    
    Args:
        func (Callable): Function to execute
        error_message (str): Error message if function fails
        fallback_value (Any, optional): Value to return if function fails. Defaults to None.
        error_class (Type[AppError], optional): Error class to use. Defaults to AppError.
        log_exception (bool, optional): Whether to log the exception. Defaults to True.
        
    Returns:
        Any: Function result or fallback value
    """
    try:
        return func()
    except Exception as e:
        if log_exception:
            log_error(logger, f"{error_message}: {str(e)}", exc_info=True)
        return fallback_value


def error_handler(app):
    """
    Register global exception handlers for FastAPI application.
    
    Args:
        app: FastAPI application
    """
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, error: AppError):
        """Handle application errors"""
        error.log()
        return JSONResponse(
            status_code=error.status_code,
            content=error.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, error: Exception):
        """Handle generic exceptions"""
        # Log the error with traceback
        log_error(logger, f"Unhandled exception: {str(error)}", exc_info=True)
        
        # Determine if we should show detailed errors
        debug_mode = config_system.get("app.debug", False)
        
        error_detail = {
            "error": "internal_error",
            "message": "An unexpected error occurred"
        }
        
        if debug_mode:
            # Convert details to string to avoid type errors
            error_detail["details"] = json.dumps({
                "exception": str(error),
                "traceback": traceback.format_exc()
            })
        
        return JSONResponse(
            status_code=500,
            content=error_detail
        )


def error_handling_middleware(app):
    """
    Add error handling middleware to FastAPI application.
    
    Args:
        app: FastAPI application
    """
    @app.middleware("http")
    async def error_logging_middleware(request: Request, call_next):
        """Log errors and handle exceptions in middleware"""
        try:
            return await call_next(request)
        except Exception as e:
            # Log the error
            log_error(logger, f"Error in request: {request.url.path}", error=e, exc_info=True)
            
            # Determine if we should show detailed errors
            debug_mode = config_system.get("app.debug", False)
            
            error_detail = {
                "error": "internal_error",
                "message": "An unexpected error occurred"
            }
            
            if debug_mode:
                # Convert details to string to avoid type errors
                error_detail["details"] = json.dumps({
                    "exception": str(e),
                    "traceback": traceback.format_exc()
                })
            
            return JSONResponse(
                status_code=500,
                content=error_detail
            )


def with_error_handling(error_message: str, error_class: Type[AppError] = AppError):
    """
    Decorator for functions to add standardized error handling.
    
    Args:
        error_message (str): Error message if function fails
        error_class (Type[AppError], optional): Error class to use. Defaults to AppError.
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AppError as e:
                # Re-raise application errors
                raise e
            except Exception as e:
                # Convert other exceptions to AppError
                log_error(logger, f"{error_message}: {str(e)}", exc_info=True)
                raise error_class(f"{error_message}: {str(e)}")
        return wrapper
    return decorator