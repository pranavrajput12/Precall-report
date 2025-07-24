"""
Input Validation Module for CrewAI Workflow Orchestration Platform.

This module provides standardized input validation for API endpoints,
with comprehensive validation rules and error messages.
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Callable
from pydantic import BaseModel, Field, validator, ValidationError

from error_handling import ValidationError as AppValidationError
from logging_config import log_error, log_warning, log_debug
import logging

logger = logging.getLogger(__name__)

# Common validation patterns
URL_PATTERN = r"^https?://[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+(:\d+)?(\/\S*)?$"
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
LINKEDIN_PROFILE_PATTERN = r"^https?://(www\.)?linkedin\.com/in/[\w\-]+/?$"
LINKEDIN_COMPANY_PATTERN = r"^https?://(www\.)?linkedin\.com/company/[\w\-]+/?$"

# Validation functions
def validate_url(url: str, pattern: str = URL_PATTERN) -> bool:
    """
    Validate URL format.
    
    Args:
        url (str): URL to validate
        pattern (str, optional): Regex pattern to use. Defaults to URL_PATTERN.
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(re.match(pattern, url))

def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email (str): Email to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(re.match(EMAIL_PATTERN, email))

def validate_linkedin_profile(url: str) -> bool:
    """
    Validate LinkedIn profile URL format.
    
    Args:
        url (str): LinkedIn profile URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(re.match(LINKEDIN_PROFILE_PATTERN, url))

def validate_linkedin_company(url: str) -> bool:
    """
    Validate LinkedIn company URL format.
    
    Args:
        url (str): LinkedIn company URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(re.match(LINKEDIN_COMPANY_PATTERN, url))

def validate_json(json_str: str) -> bool:
    """
    Validate JSON format.
    
    Args:
        json_str (str): JSON string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except Exception:
        return False

# Validation decorators
def validate_request_data(validation_func: Callable):
    """
    Decorator to validate request data.
    
    Args:
        validation_func (Callable): Function to validate request data
        
    Returns:
        Callable: Decorated function
    """
    async def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request data from args or kwargs
            request_data = None
            for arg in args:
                if hasattr(arg, "json"):
                    try:
                        request_data = await arg.json()
                        break
                    except Exception:
                        pass
            
            if request_data is None:
                for key, value in kwargs.items():
                    if key in ["data", "request_data", "body"]:
                        request_data = value
                        break
            
            # Validate request data
            if request_data:
                try:
                    validation_func(request_data)
                except AppValidationError as e:
                    raise e
                except Exception as e:
                    log_error(logger, f"Validation error: {str(e)}")
                    raise AppValidationError(f"Invalid request data: {str(e)}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Validation models
class WorkflowRequestValidator(BaseModel):
    """Validator for workflow execution requests"""
    workflow_id: str = Field(..., min_length=1, max_length=100)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("workflow_id")
    def workflow_id_must_be_valid(cls, v):
        """Validate workflow_id"""
        if not v or not isinstance(v, str):
            raise ValueError("workflow_id must be a non-empty string")
        return v
    
    @validator("input_data")
    def input_data_must_be_dict(cls, v):
        """Validate input_data"""
        if not isinstance(v, dict):
            raise ValueError("input_data must be a dictionary")
        return v

class ProfileEnrichmentValidator(BaseModel):
    """Validator for profile enrichment requests"""
    prospect_profile_url: str = Field(..., min_length=10)
    prospect_company_url: str = Field(..., min_length=10)
    prospect_company_website: str = Field(..., min_length=10)
    
    @validator("prospect_profile_url")
    def profile_url_must_be_valid(cls, v):
        """Validate prospect_profile_url"""
        if not validate_linkedin_profile(v):
            raise ValueError("Invalid LinkedIn profile URL")
        return v
    
    @validator("prospect_company_url")
    def company_url_must_be_valid(cls, v):
        """Validate prospect_company_url"""
        if not validate_linkedin_company(v):
            raise ValueError("Invalid LinkedIn company URL")
        return v
    
    @validator("prospect_company_website")
    def website_must_be_valid(cls, v):
        """Validate prospect_company_website"""
        if not validate_url(v):
            raise ValueError("Invalid company website URL")
        return v

class ThreadAnalysisValidator(BaseModel):
    """Validator for thread analysis requests"""
    conversation_thread: str = Field(..., min_length=1)
    channel: str = Field(..., min_length=1)
    
    @validator("conversation_thread")
    def thread_must_not_be_empty(cls, v):
        """Validate conversation_thread"""
        if not v or not isinstance(v, str):
            raise ValueError("conversation_thread must be a non-empty string")
        return v
    
    @validator("channel")
    def channel_must_be_valid(cls, v):
        """Validate channel"""
        if v.lower() not in ["linkedin", "email"]:
            raise ValueError("channel must be 'linkedin' or 'email'")
        return v.lower()

class ReplyGenerationValidator(BaseModel):
    """Validator for reply generation requests"""
    thread_analysis: Dict[str, Any] = Field(...)
    profile_data: Dict[str, Any] = Field(...)
    channel: str = Field(...)
    
    @validator("thread_analysis")
    def thread_analysis_must_be_valid(cls, v):
        """Validate thread_analysis"""
        if not isinstance(v, dict):
            raise ValueError("thread_analysis must be a dictionary")
        
        required_keys = ["qualification_stage", "summary", "tone", "questions"]
        for key in required_keys:
            if key not in v:
                raise ValueError(f"thread_analysis missing required key: {key}")
        
        return v
    
    @validator("profile_data")
    def profile_data_must_be_valid(cls, v):
        """Validate profile_data"""
        if not isinstance(v, dict):
            raise ValueError("profile_data must be a dictionary")
        return v
    
    @validator("channel")
    def channel_must_be_valid(cls, v):
        """Validate channel"""
        if v.lower() not in ["linkedin", "email"]:
            raise ValueError("channel must be 'linkedin' or 'email'")
        return v.lower()

# Validation functions for API endpoints
def validate_workflow_request(data: Dict[str, Any]):
    """
    Validate workflow execution request.
    
    Args:
        data (Dict[str, Any]): Request data
        
    Raises:
        AppValidationError: If validation fails
    """
    try:
        WorkflowRequestValidator(**data)
    except ValidationError as e:
        error_details = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in error_details]
        raise AppValidationError(f"Invalid workflow request: {', '.join(error_messages)}")

def validate_profile_enrichment(data: Dict[str, Any]):
    """
    Validate profile enrichment request.
    
    Args:
        data (Dict[str, Any]): Request data
        
    Raises:
        AppValidationError: If validation fails
    """
    try:
        ProfileEnrichmentValidator(**data)
    except ValidationError as e:
        error_details = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in error_details]
        raise AppValidationError(f"Invalid profile enrichment request: {', '.join(error_messages)}")

def validate_thread_analysis(data: Dict[str, Any]):
    """
    Validate thread analysis request.
    
    Args:
        data (Dict[str, Any]): Request data
        
    Raises:
        AppValidationError: If validation fails
    """
    try:
        ThreadAnalysisValidator(**data)
    except ValidationError as e:
        error_details = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in error_details]
        raise AppValidationError(f"Invalid thread analysis request: {', '.join(error_messages)}")

def validate_reply_generation(data: Dict[str, Any]):
    """
    Validate reply generation request.
    
    Args:
        data (Dict[str, Any]): Request data
        
    Raises:
        AppValidationError: If validation fails
    """
    try:
        ReplyGenerationValidator(**data)
    except ValidationError as e:
        error_details = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in error_details]
        raise AppValidationError(f"Invalid reply generation request: {', '.join(error_messages)}")