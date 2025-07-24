"""
Enhanced Redis connection and configuration management for CrewAI Workflow Platform.

This module provides robust Redis connectivity with automatic failover,
connection pooling, and health monitoring.
"""

import os
import json
import redis
import logging
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
from contextlib import contextmanager

from config_system import config_system
from logging_config import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis configuration management"""
    
    def __init__(self):
        """Initialize Redis configuration"""
        cache_config = config_system.get("cache", {})
        
        # Connection settings
        self.redis_url = cache_config.get("redis_url", "redis://localhost:6379/0")
        self.host = cache_config.get("host", "localhost")
        self.port = cache_config.get("port", 6379)
        self.db = cache_config.get("db", 0)
        self.password = cache_config.get("password", None)
        self.username = cache_config.get("username", None)
        
        # Connection pool settings
        self.max_connections = cache_config.get("max_connections", 20)
        self.connection_timeout = cache_config.get("connection_timeout", 5)
        self.socket_timeout = cache_config.get("socket_timeout", 5)
        self.retry_on_timeout = cache_config.get("retry_on_timeout", True)
        
        # Cache settings
        self.default_ttl = cache_config.get("default_ttl", 3600)
        self.key_prefix = cache_config.get("key_prefix", "crewai:")
        
        # Health check settings
        self.health_check_interval = cache_config.get("health_check_interval", 30)
        self.max_retries = cache_config.get("max_retries", 3)
        self.retry_delay = cache_config.get("retry_delay", 1)
        
        # Fallback settings
        self.enable_fallback = cache_config.get("enable_fallback", True)
        self.fallback_type = cache_config.get("fallback_type", "memory")  # memory or none
        
        # Environment overrides
        if os.getenv("REDIS_URL"):
            self.redis_url = os.getenv("REDIS_URL")
        if os.getenv("REDIS_PASSWORD"):
            self.password = os.getenv("REDIS_PASSWORD")


class RedisManager:
    """Enhanced Redis connection manager with failover support"""
    
    def __init__(self):
        """Initialize Redis manager"""
        self.config = RedisConfig()
        self.redis_client = None
        self.connection_pool = None
        self.is_connected = False
        self.last_health_check = None
        self.fallback_cache = {} if self.config.enable_fallback else None
        
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Redis connection with retry logic"""
        try:
            # Create connection pool
            if self.config.redis_url:
                # Use URL-based connection
                self.connection_pool = redis.ConnectionPool.from_url(
                    self.config.redis_url,
                    max_connections=self.config.max_connections,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.connection_timeout,
                    retry_on_timeout=self.config.retry_on_timeout
                )
            else:
                # Use individual parameters
                self.connection_pool = redis.ConnectionPool(
                    host=self.config.host,
                    port=self.config.port,
                    db=self.config.db,
                    password=self.config.password,
                    username=self.config.username,
                    max_connections=self.config.max_connections,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.connection_timeout,
                    retry_on_timeout=self.config.retry_on_timeout
                )
            
            # Create Redis client
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            self.redis_client.ping()
            self.is_connected = True
            self.last_health_check = datetime.utcnow()
            
            log_info(logger, f"Redis connection established: {self.config.redis_url}")
            
        except Exception as e:
            log_error(logger, f"Failed to connect to Redis: {str(e)}")
            self.is_connected = False
            
            if self.config.enable_fallback:
                log_warning(logger, "Using fallback caching mechanism")
    
    def _get_key(self, key: str) -> str:
        """
        Get prefixed cache key
        
        Args:
            key: Original key
            
        Returns:
            str: Prefixed key
        """
        return f"{self.config.key_prefix}{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """
        Serialize value for storage
        
        Args:
            value: Value to serialize
            
        Returns:
            str: Serialized value
        """
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value)
        else:
            return json.dumps(value, default=str)
    
    def _deserialize_value(self, value: str) -> Any:
        """
        Deserialize value from storage
        
        Args:
            value: Serialized value
            
        Returns:
            Any: Deserialized value
        """
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    def health_check(self) -> bool:
        """
        Perform Redis health check
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if self.redis_client:
                self.redis_client.ping()
                self.is_connected = True
                self.last_health_check = datetime.utcnow()
                return True
        except Exception as e:
            log_error(logger, f"Redis health check failed: {str(e)}")
            self.is_connected = False
            
        return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Any: Cached value or default
        """
        try:
            if self.is_connected and self.redis_client:
                redis_key = self._get_key(key)
                value = self.redis_client.get(redis_key)
                
                if value is not None:
                    return self._deserialize_value(value.decode('utf-8'))
                    
        except Exception as e:
            log_warning(logger, f"Redis get failed for key '{key}': {str(e)}")
            
        # Fallback to memory cache
        if self.fallback_cache is not None:
            return self.fallback_cache.get(key, default)
            
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if ttl is None:
            ttl = self.config.default_ttl
            
        try:
            if self.is_connected and self.redis_client:
                redis_key = self._get_key(key)
                serialized_value = self._serialize_value(value)
                
                if ttl > 0:
                    result = self.redis_client.setex(redis_key, ttl, serialized_value)
                else:
                    result = self.redis_client.set(redis_key, serialized_value)
                    
                if result:
                    # Also store in fallback cache
                    if self.fallback_cache is not None:
                        self.fallback_cache[key] = value
                    return True
                    
        except Exception as e:
            log_warning(logger, f"Redis set failed for key '{key}': {str(e)}")
            
        # Fallback to memory cache
        if self.fallback_cache is not None:
            self.fallback_cache[key] = value
            return True
            
        return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = False
        
        try:
            if self.is_connected and self.redis_client:
                redis_key = self._get_key(key)
                result = self.redis_client.delete(redis_key)
                success = bool(result)
                
        except Exception as e:
            log_warning(logger, f"Redis delete failed for key '{key}': {str(e)}")
            
        # Also delete from fallback cache
        if self.fallback_cache is not None and key in self.fallback_cache:
            del self.fallback_cache[key]
            success = True
            
        return success
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            if self.is_connected and self.redis_client:
                redis_key = self._get_key(key)
                return bool(self.redis_client.exists(redis_key))
                
        except Exception as e:
            log_warning(logger, f"Redis exists check failed for key '{key}': {str(e)}")
            
        # Check fallback cache
        if self.fallback_cache is not None:
            return key in self.fallback_cache
            
        return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern
        
        Args:
            pattern: Key pattern
            
        Returns:
            List[str]: Matching keys
        """
        try:
            if self.is_connected and self.redis_client:
                redis_pattern = self._get_key(pattern)
                keys = self.redis_client.keys(redis_pattern)
                # Remove prefix from keys
                prefix_len = len(self.config.key_prefix)
                return [key.decode('utf-8')[prefix_len:] for key in keys]
                
        except Exception as e:
            log_warning(logger, f"Redis keys search failed for pattern '{pattern}': {str(e)}")
            
        # Fallback cache
        if self.fallback_cache is not None:
            import fnmatch
            return [key for key in self.fallback_cache.keys() if fnmatch.fnmatch(key, pattern)]
            
        return []
    
    def flush_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Key pattern
            
        Returns:
            int: Number of keys deleted
        """
        keys_to_delete = self.keys(pattern)
        deleted_count = 0
        
        for key in keys_to_delete:
            if self.delete(key):
                deleted_count += 1
                
        return deleted_count
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get Redis server information
        
        Returns:
            Dict[str, Any]: Server information
        """
        try:
            if self.is_connected and self.redis_client:
                info = self.redis_client.info()
                return {
                    "redis_version": info.get("redis_version", "unknown"),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "keyspace": info.get("db0", {}),
                    "uptime": info.get("uptime_in_seconds", 0)
                }
        except Exception as e:
            log_error(logger, f"Failed to get Redis info: {str(e)}")
            
        return {
            "status": "disconnected",
            "fallback_active": self.fallback_cache is not None,
            "fallback_keys": len(self.fallback_cache) if self.fallback_cache else 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        stats = {
            "connected": self.is_connected,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "connection_pool_created_connections": 0,
            "connection_pool_available_connections": 0,
            "fallback_enabled": self.config.enable_fallback,
            "fallback_keys": len(self.fallback_cache) if self.fallback_cache else 0
        }
        
        # Add connection pool stats if available
        if self.connection_pool:
            try:
                stats["connection_pool_created_connections"] = self.connection_pool.created_connections
                stats["connection_pool_available_connections"] = len(self.connection_pool._available_connections)
            except Exception:
                pass  # Ignore if stats not available
                
        # Add Redis server info
        stats.update(self.get_info())
        
        return stats
    
    @contextmanager
    def pipeline(self):
        """
        Redis pipeline context manager
        
        Yields:
            redis.Pipeline: Redis pipeline
        """
        if self.is_connected and self.redis_client:
            pipeline = self.redis_client.pipeline()
            try:
                yield pipeline
                pipeline.execute()
            except Exception as e:
                log_error(logger, f"Redis pipeline error: {str(e)}")
                raise
        else:
            # Mock pipeline for fallback
            class MockPipeline:
                def execute(self):
                    return []
                    
            yield MockPipeline()


# Global Redis manager instance
redis_manager = None

def get_redis_manager() -> RedisManager:
    """
    Get global Redis manager instance
    
    Returns:
        RedisManager: Redis manager instance
    """
    global redis_manager
    if redis_manager is None:
        redis_manager = RedisManager()
    return redis_manager