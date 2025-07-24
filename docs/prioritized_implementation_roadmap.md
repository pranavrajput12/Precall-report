# Prioritized Implementation Roadmap

This document provides a prioritized roadmap of specific fixes for the CrewAI Workflow Orchestration Platform, organized by priority, risk level, and implementation phase. Each fix includes specific code locations, implementation details, and testing requirements.

## Priority Levels

- **P0**: Critical - Must be fixed immediately (security issues, data integrity)
- **P1**: High - Should be fixed in the next release (major bugs, performance issues)
- **P2**: Medium - Should be fixed in upcoming releases (usability issues, minor bugs)
- **P3**: Low - Can be fixed when time permits (cosmetic issues, nice-to-have improvements)

## Risk Levels

- **R0**: No Risk - No potential to break existing functionality
- **R1**: Low Risk - Minimal potential to affect existing functionality
- **R2**: Medium Risk - Some potential to affect existing functionality
- **R3**: High Risk - Significant potential to affect existing functionality

## Phase 1: Documentation and Low-Risk Improvements (Weeks 1-2)

### 1. Fix Error Message Typos in enhanced_api.py (P2, R0)

**Location**: `enhanced_api.py` lines 111, 110, 123, 143, etc.

**Issue**: Typos in error messages like "Error nitialize systems" and "Error ng shutdown"

**Fix**:
```python
# Before
logger.error(f"Error nitialize systems: {e}")

# After
logger.error(f"Error initializing systems: {e}")

# Before
logger.error(f"Error ng shutdown: {e}")

# After
logger.error(f"Error during shutdown: {e}")
```

**Testing**: Verify log messages are correct when errors occur

### 2. Standardize Logging Format (P2, R0)

**Location**: All Python files

**Issue**: Inconsistent logging formats and levels

**Fix**:
```python
# Create a logging configuration file
# logging_config.py
import logging
import logging.config

def configure_logging():
    logging_config = {
        'version': 1,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'filename': 'logs/app.log',
                'maxBytes': 10485760,
                'backupCount': 10
            }
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }
    logging.config.dictConfig(logging_config)
```

**Testing**: Verify logs have consistent format across all components

### 3. Add Missing Code Comments (P3, R0)

**Location**: All Python files

**Issue**: Inconsistent or missing code comments

**Fix**: Add docstrings and comments to functions and complex code sections

**Example**:
```python
def normalize_channel(channel):
    """
    Normalize channel name to standard format.
    
    Args:
        channel (str): The input channel name to normalize
        
    Returns:
        str: Normalized channel name ('linkedin' or 'email')
        
    Raises:
        ValueError: If the channel is not recognized
    """
    c = channel.strip().lower()
    if c in ["linkedin", "linked in", "li"]:
        return "linkedin"
    elif c in ["email", "mail"]:
        return "email"
    else:
        raise ValueError(f"Unknown channel: {channel}")
```

**Testing**: Code review to verify comment quality and coverage

### 4. Update API Documentation (P2, R0)

**Location**: `app.py` and `enhanced_api.py`

**Issue**: Incomplete API documentation

**Fix**: Add comprehensive OpenAPI documentation for all endpoints

**Example**:
```python
@app.post("/api/workflow/execute", 
          summary="Execute a workflow with configuration",
          description="Execute a workflow using the specified configuration and input data",
          response_model=WorkflowExecutionResponse,
          responses={
              200: {"description": "Workflow executed successfully"},
              400: {"description": "Invalid input data"},
              500: {"description": "Internal server error"}
          })
async def execute_workflow_with_config(
    request: Request, 
    data: WorkflowExecuteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Execute a workflow using the current configuration.
    
    The workflow_id specifies which workflow to execute, and input_data
    provides the necessary inputs for the workflow.
    """
    # Implementation...
```

**Testing**: Verify API documentation is complete and accurate

## Phase 2: Configuration Externalization (Weeks 3-4)

### 1. Create Configuration System (P1, R1)

**Location**: New file `config_system.py`

**Issue**: Hardcoded configuration values throughout the codebase

**Fix**:
```python
# config_system.py
import os
import json
from typing import Any, Dict, Optional
from pathlib import Path

class ConfigSystem:
    """Centralized configuration system with layered fallbacks"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.env_prefix = "CREWAI_"
        self.config_cache = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from files"""
        try:
            # Load base configuration
            base_config_path = self.config_dir / "base_config.json"
            if base_config_path.exists():
                with open(base_config_path, "r") as f:
                    self.config_cache = json.load(f)
            
            # Load environment-specific configuration
            env = os.getenv(f"{self.env_prefix}ENV", "development")
            env_config_path = self.config_dir / f"{env}_config.json"
            if env_config_path.exists():
                with open(env_config_path, "r") as f:
                    env_config = json.load(f)
                    # Merge with base config
                    self._deep_merge(self.config_cache, env_config)
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    def _deep_merge(self, base: Dict, override: Dict):
        """Deep merge two dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallbacks"""
        # Try environment variable first
        env_key = f"{self.env_prefix}{key.upper().replace('.', '_')}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_value(env_value)
        
        # Try config cache
        parts = key.split(".")
        config = self.config_cache
        for part in parts:
            if isinstance(config, dict) and part in config:
                config = config[part]
            else:
                return default
        return config
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        # Try to convert to appropriate type
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

# Global instance
config_system = ConfigSystem()
```

**Testing**: 
- Verify configuration loading from files and environment variables
- Test fallback behavior
- Ensure default values match current hardcoded values

### 2. Externalize LLM Configuration in agents.py (P1, R2)

**Location**: `agents.py` lines 16-28

**Issue**: Hardcoded LLM configuration

**Fix**:
```python
# Before
llm = AzureChatOpenAI(
    openai_api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    deployment_name=AZURE_OPENAI_DEPLOYMENT,
    openai_api_version=AZURE_OPENAI_API_VERSION,
    temperature=0.3,
    max_tokens=2048,
    streaming=True,
    model_kwargs={
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    },
)

# After
from config_system import config_system

llm = AzureChatOpenAI(
    openai_api_key=config_system.get("azure.openai.api_key", AZURE_OPENAI_API_KEY),
    azure_endpoint=config_system.get("azure.openai.endpoint", AZURE_OPENAI_ENDPOINT),
    deployment_name=config_system.get("azure.openai.deployment", AZURE_OPENAI_DEPLOYMENT),
    openai_api_version=config_system.get("azure.openai.api_version", AZURE_OPENAI_API_VERSION),
    temperature=config_system.get("llm.temperature", 0.3),
    max_tokens=config_system.get("llm.max_tokens", 2048),
    streaming=config_system.get("llm.streaming", True),
    model_kwargs={
        "top_p": config_system.get("llm.top_p", 0.9),
        "frequency_penalty": config_system.get("llm.frequency_penalty", 0.1),
        "presence_penalty": config_system.get("llm.presence_penalty", 0.1)
    },
)
```

**Testing**:
- Verify LLM works with default configuration
- Test with different configuration values
- Ensure backward compatibility

### 3. Externalize Quality Thresholds in output_quality.py (P2, R1)

**Location**: `output_quality.py` lines 21-26

**Issue**: Hardcoded quality thresholds

**Fix**:
```python
# Before
def __init__(self):
    self.quality_thresholds = {
        "excellent": 0.85,
        "good": 0.70,
        "acceptable": 0.55,
        "poor": 0.40,
    }

# After
from config_system import config_system

def __init__(self):
    self.quality_thresholds = {
        "excellent": config_system.get("quality.thresholds.excellent", 0.85),
        "good": config_system.get("quality.thresholds.good", 0.70),
        "acceptable": config_system.get("quality.thresholds.acceptable", 0.55),
        "poor": config_system.get("quality.thresholds.poor", 0.40),
    }
```

**Testing**:
- Verify quality assessment works with default thresholds
- Test with different threshold values
- Ensure backward compatibility

### 4. Create Default Configuration Files (P1, R0)

**Location**: New files in `config/` directory

**Issue**: Missing configuration files with default values

**Fix**:
```json
// config/base_config.json
{
  "llm": {
    "temperature": 0.3,
    "max_tokens": 2048,
    "streaming": true,
    "top_p": 0.9,
    "frequency_penalty": 0.1,
    "presence_penalty": 0.1
  },
  "quality": {
    "thresholds": {
      "excellent": 0.85,
      "good": 0.70,
      "acceptable": 0.55,
      "poor": 0.40
    }
  },
  "cache": {
    "ttl": {
      "profile_enrichment": 7200,
      "thread_analysis": 3600,
      "reply_generation": 1800
    }
  },
  "api": {
    "cors": {
      "allowed_origins": ["http://localhost:3000", "http://localhost:8100"]
    }
  }
}
```

**Testing**:
- Verify configuration files are loaded correctly
- Test with different configuration values
- Ensure backward compatibility

## Phase 3: Error Handling Improvements (Weeks 5-6)

### 1. Create Standardized Error Handling (P1, R1)

**Location**: New file `error_handling.py`

**Issue**: Inconsistent error handling across the codebase

**Fix**:
```python
# error_handling.py
from typing import Dict, Any, Optional, Type
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base application error class"""
    status_code: int = 500
    error_code: str = "internal_error"
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API response"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }
    
    def log(self, log_level: int = logging.ERROR):
        """Log the error with appropriate level"""
        logger.log(log_level, f"{self.error_code}: {self.message}", extra={"details": self.details})

class ValidationError(AppError):
    """Validation error"""
    status_code = 400
    error_code = "validation_error"

class NotFoundError(AppError):
    """Resource not found error"""
    status_code = 404
    error_code = "not_found"

class AuthenticationError(AppError):
    """Authentication error"""
    status_code = 401
    error_code = "authentication_error"

class AuthorizationError(AppError):
    """Authorization error"""
    status_code = 403
    error_code = "authorization_error"

class ConfigurationError(AppError):
    """Configuration error"""
    status_code = 500
    error_code = "configuration_error"

class ExternalServiceError(AppError):
    """External service error"""
    status_code = 502
    error_code = "external_service_error"

def handle_app_error(error: AppError) -> HTTPException:
    """Convert AppError to FastAPI HTTPException"""
    error.log()
    return HTTPException(
        status_code=error.status_code,
        detail=error.to_dict()
    )

def safe_execute(func, error_message: str, fallback_value: Any = None):
    """Safely execute a function with error handling"""
    try:
        return func()
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}")
        return fallback_value
```

**Testing**:
- Verify error handling works correctly
- Test with different error types
- Ensure proper error logging

### 2. Implement Error Handling in API Endpoints (P1, R2)

**Location**: `app.py` and `enhanced_api.py`

**Issue**: Inconsistent error handling in API endpoints

**Fix**:
```python
# Before
@app.post("/api/workflow/execute")
async def execute_workflow_with_config(
    request: Request, 
    data: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        workflow_id = data.get("workflow_id", "default_workflow")
        input_data = data.get("input_data", {})
        
        # Add user info to input data for audit trail
        input_data["_executed_by"] = current_user.get("username", "unknown")
        input_data["_executed_at"] = datetime.now().isoformat()

        result = await workflow_executor.run_full_workflow(workflow_id, input_data)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# After
from error_handling import ValidationError, NotFoundError, handle_app_error

@app.post("/api/workflow/execute")
async def execute_workflow_with_config(
    request: Request, 
    data: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        # Validate input
        if not data:
            raise ValidationError("Request body is required")
            
        workflow_id = data.get("workflow_id")
        if not workflow_id:
            raise ValidationError("workflow_id is required")
            
        input_data = data.get("input_data", {})
        
        # Add user info to input data for audit trail
        input_data["_executed_by"] = current_user.get("username", "unknown")
        input_data["_executed_at"] = datetime.now().isoformat()

        # Check if workflow exists
        if not await workflow_executor.workflow_exists(workflow_id):
            raise NotFoundError(f"Workflow '{workflow_id}' not found")

        result = await workflow_executor.run_full_workflow(workflow_id, input_data)
        return JSONResponse(result)
    except ValidationError as e:
        raise handle_app_error(e)
    except NotFoundError as e:
        raise handle_app_error(e)
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        error = AppError(f"Failed to execute workflow: {str(e)}")
        raise handle_app_error(error)
```

**Testing**:
- Verify API endpoints handle errors correctly
- Test with different error scenarios
- Ensure proper error responses

### 3. Add Input Validation (P1, R1)

**Location**: `app.py` and `enhanced_api.py`

**Issue**: Missing input validation

**Fix**:
```python
# Before
class WorkflowRequest(BaseModel):
    conversation_thread: str = Field(
        ..., 
        description="The conversation thread to analyze",
        min_length=1,
        max_length=50000
    )
    channel: str = Field(
        ...,
        description="Communication channel (linkedin/email)",
        pattern="^(linkedin|email)$"
    )
    # ...

# After
from pydantic import BaseModel, Field, validator

class WorkflowRequest(BaseModel):
    conversation_thread: str = Field(
        ..., 
        description="The conversation thread to analyze",
        min_length=1,
        max_length=50000
    )
    channel: str = Field(
        ...,
        description="Communication channel (linkedin/email)",
        pattern="^(linkedin|email)$"
    )
    prospect_profile_url: str = Field(
        ..., 
        description="LinkedIn profile URL of the prospect",
        pattern="^https?://(www\\.)?linkedin\\.com/in/[\\w-]+/?\\s*$"
    )
    prospect_company_url: str = Field(
        ..., 
        description="Company LinkedIn URL",
        pattern="^https?://(www\\.)?linkedin\\.com/company/[\\w-]+/?\\s*$"
    )
    prospect_company_website: str = Field(
        ...,
        description="Company website URL",
        pattern="^https?://[\\w.-]+\\.[\\w.-]+.*$"
    )
    qubit_context: str = Field(
        "", 
        description="Additional context for the workflow",
        max_length=5000
    )
    
    @validator('conversation_thread')
    def validate_conversation_thread(cls, v):
        if not v.strip():
            raise ValueError("Conversation thread cannot be empty")
        return v
    
    @validator('prospect_profile_url', 'prospect_company_url', 'prospect_company_website')
    def validate_urls(cls, v):
        # Additional validation beyond regex pattern
        if "linkedin.com" not in v and "linkedin" in v:
            raise ValueError("Invalid LinkedIn URL format")
        return v
```

**Testing**:
- Verify input validation works correctly
- Test with valid and invalid inputs
- Ensure proper error messages

## Phase 4: Security Enhancements (Weeks 7-8)

### 1. Fix CORS Configuration (P0, R2)

**Location**: `app.py` lines 134-142 and `enhanced_api.py` lines 75-81

**Issue**: Insecure CORS configuration with wildcard origins

**Fix**:
```python
# Before - app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# After - app.py
from config_system import config_system

allowed_origins = config_system.get("api.cors.allowed_origins", ["http://localhost:3000", "http://localhost:8100"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent"],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=3600,
)
```

**Testing**:
- Verify CORS works correctly for allowed origins
- Test with different origins
- Ensure proper CORS headers

### 2. Enhance JWT Implementation (P1, R2)

**Location**: `auth.py`

**Issue**: JWT implementation without proper expiration and refresh

**Fix**:
```python
# Add to auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Optional

# Configuration
SECRET_KEY = config_system.get("auth.secret_key", "your-secret-key")  # Should be properly secured
ALGORITHM = config_system.get("auth.algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = config_system.get("auth.access_token_expire_minutes", 30)
REFRESH_TOKEN_EXPIRE_DAYS = config_system.get("auth.refresh_token_expire_days", 7)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def create_access_token(data: dict):
    """Create a new access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create a new refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Dict:
    """Verify a token and return its payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Get the current user from the token"""
    return verify_token(token, "access")

# Add refresh token endpoint
@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh an access token using a refresh token"""
    payload = verify_token(refresh_token, "refresh")
    
    # Create a new access token
    new_access_token = create_access_token({
        "sub": payload["sub"],
        "username": payload["username"],
        "role": payload["role"]
    })
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
```

**Testing**:
- Verify token creation and validation
- Test token expiration
- Ensure refresh token works correctly

## Phase 5: Performance Optimizations (Weeks 9-10)

### 1. Implement Pagination for Large Datasets (P1, R1)

**Location**: Various API endpoints in `app.py` and `enhanced_api.py`

**Issue**: No pagination for large datasets

**Fix**:
```python
# Add to app.py
from fastapi import Query

@app.get("/api/execution-history")
async def get_execution_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("started_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)")
):
    """Get execution history with pagination"""
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count
    total_count = len(execution_history)
    
    # Sort execution history
    sorted_history = sorted(
        execution_history,
        key=lambda x: x.get(sort_by, ""),
        reverse=(sort_order.lower() == "desc")
    )
    
    # Get paginated results
    paginated_history = sorted_history[offset:offset + page_size]
    
    return {
        "items": paginated_history,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }
```

**Testing**:
- Verify pagination works correctly
- Test with different page sizes and page numbers
- Ensure proper sorting

### 2. Optimize Caching Strategy (P1, R2)

**Location**: `cache.py`

**Issue**: Inefficient caching without proper invalidation

**Fix**:
```python
# Add to cache.py
from config_system import config_system
import hashlib
import time
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheItem:
    """Cache item with TTL and metadata"""
    def __init__(self, value: Any, ttl: int, metadata: Optional[Dict] = None):
        self.value = value
        self.expiry = time.time() + ttl
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.access_count = 0
    
    def is_expired(self) -> bool:
        """Check if the item is expired"""
        return time.time() > self.expiry
    
    def access(self):
        """Record an access to this item"""
        self.access_count += 1

class EnhancedCache:
    """Enhanced cache with TTL, stats, and invalidation"""
    def __init__(self):
        self._cache: Dict[str, CacheItem] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "invalidations": 0
        }
        self._max_size = config_system.get("cache.max_size", 1000)
        self._cleanup_interval = config_system.get("cache.cleanup_interval", 60)
        self._last_cleanup = time.time()
    
    def _generate_key(self, key_prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments"""
        # Create a string representation of args and kwargs
        args_str = str(args) if args else ""
        kwargs_str = str(sorted(kwargs.items())) if kwargs else ""
        
        # Create a hash of the combined string
        key_data = f"{key_prefix}:{args_str}:{kwargs_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache"""
        self._maybe_cleanup()
        
        if key in self._cache:
            item = self._cache[key]
            if item.is_expired():
                # Remove expired item
                del self._cache[key]
                self._stats["evictions"] += 1
                self._stats["misses"] += 1
                return None
            
            # Record hit and access
            item.access()
            self._stats["hits"] += 1
            return item.value
        
        self._stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int, metadata: Optional[Dict] = None) -> None:
        """Set a value in the cache with TTL"""
        self._maybe_cleanup()
        
        # Check if we need to evict items
        if len(self._cache) >= self._max_size:
            self._evict_items()
        
        self._cache[key] = CacheItem(value, ttl, metadata)
    
    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache key"""
        if key in self._cache:
            del self._cache[key]
            self._stats["invalidations"] += 1
            return True
        return False
    
    def invalidate_by_prefix(self, prefix: str) -> int:
        """Invalidate all keys with a specific prefix"""
        count = 0
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]
            count += 1
        
        self._stats["invalidations"] += count
        return count
    
    def _maybe_cleanup(self) -> None:
        """Perform cleanup if needed"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup()
            self._last_cleanup = current_time
    
    def _cleanup(self) -> None:
        """Remove expired items from cache"""
        keys_to_delete = [k for k, v in self._cache.items() if v.is_expired()]
        for key in keys_to_delete:
            del self._cache[key]
            self._stats["evictions"] += 1
    
    def _evict_items(self) -> None:
        """Evict items to make space"""
        # Strategy: Remove least recently used items
        if not self._cache:
            return
        
        # Sort by access count and creation time
        sorted_items = sorted(
            self._cache.items(),
            key=lambda