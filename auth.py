"""
Authentication and authorization utilities
"""

import os
import jwt
import uuid
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from functools import wraps

from fastapi import HTTPException, Security, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from config_system import config_system
from logging_config import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)

# Get security settings from configuration system
ENABLE_AUTH = config_system.get("security.api_key_required", False)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token
security = HTTPBearer(auto_error=False)


# Token blacklist for revoked tokens
TOKEN_BLACKLIST = set()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token
security = HTTPBearer(auto_error=False)

class AuthManager:
    """Enhanced authentication manager for JWT tokens with refresh capability and revocation"""
    
    def __init__(self):
        # Get JWT configuration from config system
        self.secret_key = config_system.get("security.jwt_secret", os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production"))
        self.algorithm = config_system.get("security.jwt_algorithm", "HS256")
        self.access_token_expire_minutes = config_system.get("security.jwt_access_token_expire_minutes", 30)
        self.refresh_token_expire_days = config_system.get("security.jwt_refresh_token_expire_days", 7)
        self.issuer = config_system.get("security.jwt_issuer", "crewai-workflow-platform")
        self.audience = config_system.get("security.jwt_audience", "crewai-users")
        
        # Log configuration (without sensitive data)
        log_info(logger, f"Initialized AuthManager with algorithm={self.algorithm}, "
                        f"access_token_expire_minutes={self.access_token_expire_minutes}, "
                        f"refresh_token_expire_days={self.refresh_token_expire_days}")
        
    def create_access_token(self, data: Dict[str, Any], fingerprint: Optional[str] = None) -> str:
        """
        Create a JWT access token with enhanced security
        
        Args:
            data: User data to encode in the token
            fingerprint: Optional unique fingerprint (e.g., device ID, IP hash)
            
        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        
        # Add standard JWT claims
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        jti = str(uuid.uuid4())  # Unique token ID
        
        to_encode.update({
            "exp": expire,
            "iat": now,  # Issued at
            "nbf": now,  # Not valid before
            "jti": jti,  # JWT ID for revocation
            "iss": self.issuer,  # Issuer
            "aud": self.audience,  # Audience
            "type": "access"  # Token type
        })
        
        # Add fingerprint if provided
        if fingerprint:
            to_encode["fgp"] = fingerprint
            
        # Log token creation (without sensitive data)
        log_debug(logger, f"Creating access token for user {data.get('username')} with JTI {jti}")
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any], fingerprint: Optional[str] = None) -> str:
        """
        Create a JWT refresh token with longer expiration
        
        Args:
            data: User data to encode in the token (minimal)
            fingerprint: Optional unique fingerprint
            
        Returns:
            str: Encoded refresh token
        """
        # Only include essential user data
        to_encode = {
            "sub": data.get("id"),
            "username": data.get("username")
        }
        
        # Add standard JWT claims
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)
        jti = str(uuid.uuid4())
        
        to_encode.update({
            "exp": expire,
            "iat": now,
            "nbf": now,
            "jti": jti,
            "iss": self.issuer,
            "aud": self.audience,
            "type": "refresh"
        })
        
        # Add fingerprint if provided
        if fingerprint:
            to_encode["fgp"] = fingerprint
            
        log_debug(logger, f"Creating refresh token for user {data.get('username')} with JTI {jti}")
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: Optional[str] = None, fingerprint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token with enhanced security checks
        
        Args:
            token: The JWT token to verify
            token_type: Optional token type to verify ('access' or 'refresh')
            fingerprint: Optional fingerprint to verify
            
        Returns:
            Optional[Dict[str, Any]]: Decoded payload or None if invalid
        """
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": True, "verify_exp": True, "verify_aud": True}
            )
            
            # Check if token is blacklisted
            if payload.get("jti") in TOKEN_BLACKLIST:
                log_warning(logger, f"Token with JTI {payload.get('jti')} is blacklisted")
                return None
                
            # Verify token type if specified
            if token_type and payload.get("type") != token_type:
                log_warning(logger, f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
                
            # Verify fingerprint if provided
            if fingerprint and payload.get("fgp") and payload.get("fgp") != fingerprint:
                log_warning(logger, f"Token fingerprint mismatch for user {payload.get('username')}")
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            log_warning(logger, "Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            log_warning(logger, f"Invalid token: {e}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by adding its JTI to the blacklist
        
        Args:
            token: The token to revoke
            
        Returns:
            bool: True if token was revoked, False otherwise
        """
        try:
            # Decode without verification to get the JTI
            payload = jwt.decode(token, options={"verify_signature": False})
            jti = payload.get("jti")
            
            if jti:
                TOKEN_BLACKLIST.add(jti)
                log_info(logger, f"Token with JTI {jti} has been revoked")
                return True
            return False
        except Exception as e:
            log_error(logger, f"Error revoking token: {e}")
            return False
            
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_token_fingerprint(self, request: Request) -> str:
        """
        Generate a fingerprint for the request
        
        Args:
            request: The FastAPI request object
            
        Returns:
            str: A fingerprint string based on headers and IP
        """
        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
            
        # Get user agent
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Create a simple fingerprint
        fingerprint = f"{ip}:{user_agent}"
        
        # Return a hash of the fingerprint
        import hashlib
        return hashlib.sha256(fingerprint.encode()).hexdigest()


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token with enhanced security
    
    Args:
        request: The FastAPI request object for fingerprinting
        credentials: The HTTP Authorization credentials
        
    Returns:
        Optional[Dict[str, Any]]: User data if authenticated, None otherwise
    """
    # If auth is disabled, return a default user
    if not ENABLE_AUTH:
        return {"id": "default", "username": "default_user", "role": "admin"}
        
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials
    
    # Get fingerprint from request if enabled
    fingerprint = None
    if config_system.get("security.use_token_fingerprinting", False):
        fingerprint = auth_manager.get_token_fingerprint(request)
        
    # Verify token as access token
    payload = auth_manager.verify_token(token, token_type="access", fingerprint=fingerprint)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Log successful authentication
    log_info(logger, f"User {payload.get('username')} authenticated successfully")
    
    return payload


async def require_auth(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require authentication for an endpoint
    
    Args:
        request: The FastAPI request object
        current_user: The current user from get_current_user
        
    Returns:
        Dict[str, Any]: User data if authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return current_user


async def require_admin(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require admin role for an endpoint
    
    Args:
        request: The FastAPI request object
        current_user: The current user from get_current_user
        
    Returns:
        Dict[str, Any]: User data if authenticated and has admin role
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
        
    if current_user.get("role") != "admin":
        # Log unauthorized access attempt
        log_warning(logger, f"Unauthorized admin access attempt by user {current_user.get('username')}")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
        
    return current_user


def optional_auth(func):
    """
    Decorator for optional authentication
    
    This decorator allows endpoints to function with or without authentication.
    If authentication is provided and valid, the user data will be available.
    If not, the endpoint will still function but without user data.
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        try:
            # Try to get credentials from the request
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                
                # Get fingerprint if enabled
                fingerprint = None
                if config_system.get("security.use_token_fingerprinting", False):
                    fingerprint = auth_manager.get_token_fingerprint(request)
                    
                # Verify token
                payload = auth_manager.verify_token(
                    token,
                    token_type="access",
                    fingerprint=fingerprint
                )
                
                if payload:
                    # Add user to kwargs
                    kwargs["current_user"] = payload
        except Exception as e:
            # Log error but continue without user
            log_debug(logger, f"Optional auth failed: {e}")
            
        # Call the original function
        return await func(request, *args, **kwargs)
    return wrapper


# User database with more secure storage
# In a real application, this would be a database connection
class UserStore:
    """User storage with secure password handling"""
    
    def __init__(self):
        # Initialize with demo users from configuration
        self.users = {}
        self._load_demo_users()
        
    def _load_demo_users(self):
        """Load demo users from configuration"""
        # Get demo users from configuration
        demo_admin = config_system.get("security.demo_admin", {
            "id": "user_001",
            "username": "admin",
            "password": "admin123",  # This would be hashed in the config
            "role": "admin",
            "email": "admin@example.com"
        })
        
        demo_user = config_system.get("security.demo_user", {
            "id": "user_002",
            "username": "user",
            "password": "user123",  # This would be hashed in the config
            "role": "user",
            "email": "user@example.com"
        })
        
        # Add demo users with hashed passwords
        self.add_user(
            demo_admin["username"],
            demo_admin["password"],
            {
                "id": demo_admin["id"],
                "role": demo_admin["role"],
                "email": demo_admin["email"]
            }
        )
        
        self.add_user(
            demo_user["username"],
            demo_user["password"],
            {
                "id": demo_user["id"],
                "role": demo_user["role"],
                "email": demo_user["email"]
            }
        )
        
        log_info(logger, f"Loaded demo users: {', '.join(self.users.keys())}")
        
    def add_user(self, username: str, password: str, user_data: Dict[str, Any]) -> bool:
        """
        Add a new user with hashed password
        
        Args:
            username: User's username
            password: Plain text password (will be hashed)
            user_data: Additional user data
            
        Returns:
            bool: True if user was added, False if username already exists
        """
        if username in self.users:
            return False
            
        # Create user entry with hashed password
        user_entry = user_data.copy()
        user_entry["username"] = username
        user_entry["password_hash"] = auth_manager.hash_password(password)
        
        self.users[username] = user_entry
        return True
        
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        return self.users.get(username)
        
    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Verify user credentials
        
        Args:
            username: User's username
            password: Plain text password to verify
            
        Returns:
            Optional[Dict[str, Any]]: User data without password hash if verified, None otherwise
        """
        user = self.get_user(username)
        if not user:
            return None
            
        if not auth_manager.verify_password(password, user["password_hash"]):
            return None
            
        # Return user without password hash
        user_data = user.copy()
        del user_data["password_hash"]
        return user_data


# Initialize user store
user_store = UserStore()


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with username and password
    
    Args:
        username: User's username
        password: Plain text password
        
    Returns:
        Optional[Dict[str, Any]]: User data if authenticated, None otherwise
    """
    return user_store.verify_user(username, password)


def create_tokens(
    user_data: Dict[str, Any],
    request: Optional[Request] = None
) -> Tuple[str, str]:
    """
    Create access and refresh tokens for a user
    
    Args:
        user_data: User data to encode in the tokens
        request: Optional request object for fingerprinting
        
    Returns:
        Tuple[str, str]: Access token and refresh token
    """
    # Get fingerprint if enabled and request is provided
    fingerprint = None
    if config_system.get("security.use_token_fingerprinting", False) and request:
        fingerprint = auth_manager.get_token_fingerprint(request)
        
    # Create tokens
    access_token = auth_manager.create_access_token(user_data, fingerprint)
    refresh_token = auth_manager.create_refresh_token(user_data, fingerprint)
    
    return access_token, refresh_token


def refresh_access_token(
    refresh_token: str,
    request: Optional[Request] = None
) -> Optional[str]:
    """
    Refresh an access token using a refresh token
    
    Args:
        refresh_token: The refresh token
        request: Optional request object for fingerprinting
        
    Returns:
        Optional[str]: New access token if refresh token is valid, None otherwise
    """
    # Get fingerprint if enabled and request is provided
    fingerprint = None
    if config_system.get("security.use_token_fingerprinting", False) and request:
        fingerprint = auth_manager.get_token_fingerprint(request)
        
    # Verify refresh token
    payload = auth_manager.verify_token(refresh_token, token_type="refresh", fingerprint=fingerprint)
    
    if not payload:
        return None
        
    # Get user data
    username = payload.get("username")
    if not username:
        return None
        
    user = user_store.get_user(username)
    if not user:
        return None
        
    # Create new access token
    user_data = user.copy()
    if "password_hash" in user_data:
        del user_data["password_hash"]
        
    return auth_manager.create_access_token(user_data, fingerprint)