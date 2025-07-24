import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Mapping, Optional

import redis

# Import standardized logging configuration
from logging_config import log_info, log_error, log_warning, log_debug
from config_system import config_system

logger = logging.getLogger(__name__)


class CacheConfig:
    """Configuration for cache settings loaded from config system"""
    
    def __init__(self):
        # Load cache settings from configuration
        cache_config = config_system.get("cache", {})
        
        # Default TTL values (in seconds)
        self.default_ttl = cache_config.get("default_ttl", 3600)  # 1 hour
        self.profile_ttl = cache_config.get("profile_ttl", 7200)  # 2 hours
        self.faq_ttl = cache_config.get("faq_ttl", 86400)  # 24 hours
        self.workflow_ttl = cache_config.get("workflow_ttl", 3600)  # 1 hour
        self.session_ttl = cache_config.get("session_ttl", 3600)  # 1 hour
        
        # Semantic similarity settings
        self.similarity_threshold = cache_config.get("similarity_threshold", 0.85)
        self.similarity_model = cache_config.get("similarity_model", "all-MiniLM-L6-v2")
        
        # Cache monitoring settings
        self.enable_monitoring = cache_config.get("enable_monitoring", True)
        self.monitoring_interval = cache_config.get("monitoring_interval", 60)  # 1 minute
        
        # Cache warming settings
        self.enable_cache_warming = cache_config.get("enable_cache_warming", False)
        self.warming_interval = cache_config.get("warming_interval", 3600)  # 1 hour
        
        # Adaptive TTL settings
        self.enable_adaptive_ttl = cache_config.get("enable_adaptive_ttl", True)
        self.min_ttl = cache_config.get("min_ttl", 300)  # 5 minutes
        self.max_ttl = cache_config.get("max_ttl", 86400 * 7)  # 7 days
        self.ttl_multiplier = cache_config.get("ttl_multiplier", 2.0)
        
        # Cache eviction policy
        self.eviction_policy = cache_config.get("eviction_policy", "lru")
        self.max_memory = cache_config.get("max_memory", "100mb")
        
        log_info(logger, "Cache configuration loaded")


# Global cache configuration
cache_config = CacheConfig()


class CacheManager:
    """
    Enhanced Redis cache manager with advanced features including:
    - Adaptive TTL based on access patterns
    - Comprehensive cache monitoring
    - Configurable cache settings
    - Optimized cache eviction policies
    """

    def __init__(self):
        # Initialize Redis client
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        
        # Initialize cache metrics
        self.hit_count = 0
        self.miss_count = 0
        self.access_counts = {}  # Track access frequency by key
        self.last_access_time = {}  # Track last access time by key
        
        # Set up monitoring thread if enabled
        if cache_config.enable_monitoring:
            self.monitoring_thread = threading.Thread(
                target=self._monitor_cache_performance,
                daemon=True
            )
            self.is_monitoring = True
        else:
            self.monitoring_thread = None
            self.is_monitoring = False

        # Test connection
        try:
            self.redis_client.ping()
            log_info(logger, "Redis connection established successfully")
            
            # Configure Redis with the eviction policy from config
            if cache_config.eviction_policy:
                try:
                    self.redis_client.config_set(
                        "maxmemory-policy",
                        cache_config.eviction_policy
                    )
                    self.redis_client.config_set(
                        "maxmemory",
                        cache_config.max_memory
                    )
                    log_info(logger, f"Redis configured with eviction policy: {cache_config.eviction_policy}")
                except redis.RedisError as e:
                    log_warning(logger, f"Failed to set Redis eviction policy: {e}")
            
            # Start monitoring thread if enabled
            if self.monitoring_thread:
                self.monitoring_thread.start()
                log_info(logger, "Cache monitoring started")
                
        except redis.ConnectionError:
            log_error(logger, "Failed to connect to Redis")
            self.redis_client = None
            self.is_monitoring = False

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a consistent cache key from function arguments.
        
        This method creates a deterministic cache key by combining a prefix with
        the function arguments. The key is hashed using MD5 to ensure a fixed length
        and to avoid any special characters that might cause issues with Redis.
        
        Args:
            prefix (str): A prefix to identify the type of cached data
            *args: Positional arguments to include in the key
            **kwargs: Keyword arguments to include in the key
            
        Returns:
            str: A hexadecimal MD5 hash that serves as the cache key
        """
        # Create a string representation of all arguments
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        # Hash it to create a consistent key
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Retrieves a value from the Redis cache by key. The value is assumed to be
        JSON-serialized and will be deserialized before returning. If the Redis
        client is not available or any error occurs, None is returned.
        
        This method also tracks access patterns for adaptive TTL and cache warming.
        
        Args:
            key (str): The cache key to retrieve
            
        Returns:
            Optional[Any]: The deserialized cached value, or None if not found or on error
            
        Raises:
            No exceptions are raised; errors are logged and None is returned
        """
        if not self.redis_client:
            return None

        try:
            cached_value = self.redis_client.get(key)
            if cached_value:
                # Track access for adaptive TTL
                self.access_counts[key] = self.access_counts.get(key, 0) + 1
                self.last_access_time[key] = time.time()
                
                # If adaptive TTL is enabled, extend TTL for frequently accessed keys
                if cache_config.enable_adaptive_ttl:
                    access_count = self.access_counts.get(key, 0)
                    if access_count > 5:  # Only extend TTL for frequently accessed keys
                        current_ttl = self.redis_client.ttl(key)
                        if current_ttl > 0:  # Only adjust if key exists and has TTL
                            # Calculate new TTL based on access frequency
                            new_ttl = min(
                                current_ttl * 1.5,  # Increase TTL by 50%
                                cache_config.max_ttl
                            )
                            self.redis_client.expire(key, int(new_ttl))
                            log_debug(logger, f"Extended TTL for frequently accessed key {key}: {current_ttl}s -> {int(new_ttl)}s")
                
                # Increment hit counter
                self.hit_count += 1
                
                return json.loads(cached_value)
            else:
                # Increment miss counter
                self.miss_count += 1
        except (redis.RedisError, json.JSONDecodeError) as e:
            log_error(logger, "Cache get error", e)

        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache with TTL (Time-To-Live).
        
        Stores a value in the Redis cache with the specified key and TTL.
        The value is JSON-serialized before storage. If the Redis client
        is not available or any error occurs, False is returned.
        
        This method implements adaptive TTL based on configuration settings.
        
        Args:
            key (str): The cache key to store the value under
            value (Any): The value to store (must be JSON-serializable)
            ttl (int, optional): Time-to-live in seconds. Defaults to 3600 (1 hour).
            
        Returns:
            bool: True if the value was successfully stored, False otherwise
            
        Raises:
            No exceptions are raised; errors are logged and False is returned
        """
        if not self.redis_client:
            return False

        # Use default TTL from config if specified
        if ttl == 3600 and cache_config.default_ttl != 3600:
            ttl = cache_config.default_ttl
            
        # Apply adaptive TTL if enabled
        if cache_config.enable_adaptive_ttl:
            # Check if this is a frequently accessed key
            access_count = self.access_counts.get(key, 0)
            if access_count > 0:
                # Adjust TTL based on access frequency
                ttl_multiplier = min(access_count / 5, cache_config.ttl_multiplier)
                ttl = min(
                    int(ttl * ttl_multiplier),
                    cache_config.max_ttl
                )
                ttl = max(ttl, cache_config.min_ttl)  # Ensure minimum TTL
                log_debug(logger, f"Using adaptive TTL for key {key}: {ttl}s (access count: {access_count})")

        try:
            serialized_value = json.dumps(value, default=str)
            result = self.redis_client.setex(key, ttl, serialized_value)
            
            # Initialize access tracking for new keys
            if key not in self.access_counts:
                self.access_counts[key] = 0
            if key not in self.last_access_time:
                self.last_access_time[key] = time.time()
                
            return result
        except (redis.RedisError, TypeError, ValueError) as e:
            log_error(logger, "Cache set error", e)
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError as e:
            log_error(logger, "Cache delete error", e)
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except redis.RedisError as e:
            log_error(logger, "Cache exists error", e)
            return False

    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except redis.RedisError as e:
            log_error(logger, "Cache flush pattern error", e)
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get(
                    "used_memory_human",
                    "N/A"),
                "connected_clients": info.get(
                    "connected_clients",
                    0),
                "total_commands_processed": info.get(
                    "total_commands_processed",
                    0),
                "keyspace_hits": info.get(
                    "keyspace_hits",
                    0),
                "keyspace_misses": info.get(
                    "keyspace_misses",
                    0),
                "hit_rate": self._calculate_hit_rate(info),
            }
        except redis.RedisError as e:
            log_error(logger, "Cache stats error", e)
            return {"status": "error", "error": str(e)}

    def _calculate_hit_rate(self, info: Mapping[str, Any]) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0
        
    def _monitor_cache_performance(self):
        """
        Monitor cache performance in a background thread.
        
        This method runs in a separate thread and periodically:
        1. Collects cache performance metrics
        2. Logs cache statistics
        3. Identifies hot keys (frequently accessed)
        4. Adjusts TTL for frequently accessed keys
        5. Pre-warms cache for predictable access patterns
        """
        while self.is_monitoring:
            try:
                # Sleep at the beginning to allow initial setup
                time.sleep(cache_config.monitoring_interval)
                
                if not self.redis_client:
                    continue
                    
                # Get cache stats
                stats = self.get_stats()
                
                # Log cache performance
                hit_rate = stats.get("hit_rate", 0)
                log_info(logger, f"Cache performance: {hit_rate:.1f}% hit rate, "
                         f"{stats.get('keyspace_hits', 0)} hits, "
                         f"{stats.get('keyspace_misses', 0)} misses")
                
                # Identify hot keys (frequently accessed)
                hot_keys = sorted(
                    self.access_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]  # Top 10 most accessed keys
                
                if hot_keys:
                    log_debug(logger, f"Hot keys: {', '.join([k for k, _ in hot_keys[:5]])}")
                
                # Adjust TTL for frequently accessed keys if adaptive TTL is enabled
                if cache_config.enable_adaptive_ttl and hot_keys:
                    for key, count in hot_keys:
                        try:
                            # Get current TTL
                            current_ttl = self.redis_client.ttl(key)
                            if current_ttl > 0:  # Only adjust if key exists and has TTL
                                # Calculate new TTL based on access frequency
                                # More frequently accessed keys get longer TTL
                                new_ttl = min(
                                    current_ttl * cache_config.ttl_multiplier,
                                    cache_config.max_ttl
                                )
                                self.redis_client.expire(key, int(new_ttl))
                                log_debug(logger, f"Adjusted TTL for hot key {key}: {current_ttl}s -> {int(new_ttl)}s")
                        except redis.RedisError:
                            pass
                
                # Pre-warm cache if enabled
                if cache_config.enable_cache_warming:
                    self._warm_cache()
                    
                # Clean up old entries in access tracking
                current_time = time.time()
                keys_to_remove = []
                for key, last_access in list(self.last_access_time.items()):
                    # Remove tracking for keys not accessed in the last day
                    if current_time - last_access > 86400:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    if key in self.access_counts:
                        del self.access_counts[key]
                    if key in self.last_access_time:
                        del self.last_access_time[key]
                
                if keys_to_remove:
                    log_debug(logger, f"Cleaned up tracking for {len(keys_to_remove)} inactive keys")
                    
            except Exception as e:
                log_error(logger, f"Cache monitoring error: {str(e)}")
                
    def _warm_cache(self):
        """
        Pre-warm cache for predictable access patterns.
        
        This method identifies patterns in cache access and pre-loads
        data that is likely to be accessed soon.
        """
        if not self.redis_client:
            return
            
        try:
            # Simple implementation: refresh TTL for recently accessed keys
            recent_keys = list(self.last_access_time.items())
            recent_keys.sort(key=lambda x: x[1], reverse=True)  # Sort by most recent access
            
            # Refresh TTL for top 20 most recently accessed keys
            for key, _ in recent_keys[:20]:
                if self.redis_client and self.redis_client.exists(key):
                    # Get current TTL
                    current_ttl = self.redis_client.ttl(key)
                    if 0 < current_ttl < cache_config.default_ttl / 2:
                        # If TTL is less than half the default, refresh it
                        self.redis_client.expire(key, cache_config.default_ttl)
                        log_debug(logger, f"Refreshed TTL for key {key}")
        except Exception as e:
            log_error(logger, f"Cache warming error: {str(e)}")


# Global cache instance
cache_manager = CacheManager()


# Cache decorators
def cache_result(ttl: int = 3600, key_prefix: str = "default"):
    """
    Decorator to cache function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                log_info(logger, f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            log_info(logger, f"Cache miss for {func.__name__}, result cached")

            return result

        return wrapper

    return decorator


def async_cache_result(ttl: int = 3600, key_prefix: str = "default"):
    """
    Decorator to cache async function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                log_info(logger, f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            log_info(logger, f"Cache miss for {func.__name__}, result cached")

            return result

        return wrapper

    return decorator


# Specialized cache functions for workflow data
class WorkflowCache:
    """Specialized caching for workflow-related data"""

    @staticmethod
    def cache_profile_data(
        profile_url: str, company_url: str, data: Dict, ttl: int = 7200
    ):
        """Cache profile enrichment data (2 hours TTL)"""
        key = f"profile:{hashlib.md5(f'{profile_url}:{company_url}'.encode()).hexdigest()}"
        return cache_manager.set(key, data, ttl)

    @staticmethod
    def get_cached_profile_data(
            profile_url: str,
            company_url: str) -> Optional[Dict]:
        """Get cached profile enrichment data"""
        key = f"profile:{hashlib.md5(f'{profile_url}:{company_url}'.encode()).hexdigest()}"
        return cache_manager.get(key)

    @staticmethod
    def cache_faq_answer(question: str, answer: str, ttl: int = 86400):
        """Cache FAQ answers (24 hours TTL)"""
        key = f"faq:{hashlib.md5(question.encode()).hexdigest()}"
        return cache_manager.set(key, answer, ttl)

    @staticmethod
    def get_cached_faq_answer(question: str) -> Optional[str]:
        """Get cached FAQ answer"""
        key = f"faq:{hashlib.md5(question.encode()).hexdigest()}"
        return cache_manager.get(key)

    @staticmethod
    def cache_workflow_result(workflow_id: str, result: Dict, ttl: int = 3600):
        """Cache complete workflow results (1 hour TTL)"""
        key = f"workflow_result:{workflow_id}"
        return cache_manager.set(key, result, ttl)

    @staticmethod
    def get_cached_workflow_result(workflow_id: str) -> Optional[Dict]:
        """Get cached workflow result"""
        key = f"workflow_result:{workflow_id}"
        return cache_manager.get(key)


# Session management
class SessionManager:
    """Manage user sessions with Redis"""

    @staticmethod
    def create_session(
            user_id: str,
            session_data: Dict,
            ttl: int = 3600) -> str:
        """Create a new session"""
        session_id = hashlib.md5(
            f"{user_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()
        key = f"session:{session_id}"

        session_data.update(
            {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
            }
        )

        cache_manager.set(key, session_data, ttl)
        return session_id

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict]:
        """Get session data"""
        key = f"session:{session_id}"
        return cache_manager.get(key)

    @staticmethod
    def update_session(
            session_id: str,
            updates: Dict,
            ttl: int = 3600) -> bool:
        """Update session data"""
        key = f"session:{session_id}"
        session_data = cache_manager.get(key)

        if session_data:
            session_data.update(updates)
            session_data["last_activity"] = datetime.now().isoformat()
            return cache_manager.set(key, session_data, ttl)

        return False

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete session"""
        key = f"session:{session_id}"
        return cache_manager.delete(key)


# Rate limiting
class RateLimiter:
    """Redis-based rate limiter"""

    @staticmethod
    def is_allowed(identifier: str, limit: int, window: int) -> bool:
        """
        Check if request is allowed based on rate limit

        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
        """
        if not cache_manager.redis_client:
            return True  # Allow if Redis is not available

        try:
            key = f"rate_limit:{identifier}"
            current_time = datetime.now()

            # Use Redis pipeline for atomic operations
            pipe = cache_manager.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time.timestamp() - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time.timestamp())
                      : current_time.timestamp()})
            pipe.expire(key, window)

            results = pipe.execute()
            current_requests = results[1]

            return current_requests < limit

        except redis.RedisError as e:
            log_error(logger, "Rate limiter error", e)
            return True  # Allow if error occurs


# Metrics collection
class MetricsCollector:
    """Collect and store metrics in Redis"""

    @staticmethod
    def increment_counter(metric_name: str, value: int = 1) -> None:
        """Increment a counter metric"""
        if not cache_manager.redis_client:
            return

        try:
            key = f"metrics:counter:{metric_name}"
            cache_manager.redis_client.incrby(key, value)
        except redis.RedisError as e:
            log_error(logger, "Metrics increment error", e)

    @staticmethod
    def record_timing(metric_name: str, duration: float) -> None:
        """Record timing metric"""
        if not cache_manager.redis_client:
            return

        try:
            key = f"metrics:timing:{metric_name}"
            current_time = datetime.now().timestamp()
            cache_manager.redis_client.zadd(key, {str(current_time): duration})

            # Keep only last 1000 entries
            cache_manager.redis_client.zremrangebyrank(key, 0, -1001)
        except redis.RedisError as e:
            log_error(logger, "Metrics timing error", e)

    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Get all metrics"""
        if not cache_manager.redis_client:
            return {}

        try:
            metrics = {}

            # Get counters
            counter_keys = cache_manager.redis_client.keys("metrics:counter:*")
            for key in counter_keys:
                metric_name = key.replace("metrics:counter:", "")
                metrics[f"counter_{metric_name}"] = cache_manager.redis_client.get(
                    key)

            # Get timing averages
            timing_keys = cache_manager.redis_client.keys("metrics:timing:*")
            for key in timing_keys:
                metric_name = key.replace("metrics:timing:", "")
                values = cache_manager.redis_client.zrange(
                    key, 0, -1, withscores=True)
                if values:
                    avg_duration = sum(float(score)
                                       for _, score in values) / len(values)
                    metrics[f"timing_{metric_name}_avg"] = round(
                        avg_duration, 2)

            return metrics

        except redis.RedisError as e:
            log_error(logger, "Get metrics error", e)
            return {}


# Export instances
workflow_cache = WorkflowCache()
session_manager = SessionManager()
rate_limiter = RateLimiter()
metrics_collector = MetricsCollector()

# Add semantic similarity imports
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    SEMANTIC_SIMILARITY_AVAILABLE = True
except ImportError:
    SEMANTIC_SIMILARITY_AVAILABLE = False
    logging.warning(
        "Semantic similarity dependencies not available. Install sentence-transformers and scikit-learn for enhanced caching."
    )


class SmartWorkflowCache:
    """Enhanced workflow cache with semantic similarity matching"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)

        # Initialize semantic similarity model if available
        if SEMANTIC_SIMILARITY_AVAILABLE:
            try:
                self.similarity_model = SentenceTransformer("all-MiniLM-L6-v2")
                self.similarity_threshold = 0.85  # 85% similarity threshold
                log_info(self.logger,
                    "Semantic similarity model loaded successfully")
            except Exception as e:
                log_warning(self.logger,
                    f"Failed to load semantic similarity model: {e}")
                self.similarity_model = None
        else:
            self.similarity_model = None

    # Include all the methods from WorkflowCache
    def cache_profile_data(
        self, profile_url: str, company_url: str, data: Dict, ttl: int = 7200
    ):
        """Cache profile enrichment data with configurable TTL"""
        if self.redis is None:
            return None
            
        # Use profile TTL from config if default is used
        if ttl == 7200 and cache_config.profile_ttl != 7200:
            ttl = cache_config.profile_ttl
            
        key = f"profile:{hashlib.md5(f'{profile_url}:{company_url}'.encode()).hexdigest()}"
        
        # Track access for adaptive TTL
        cache_manager.access_counts[key] = cache_manager.access_counts.get(key, 0) + 1
        cache_manager.last_access_time[key] = time.time()
        
        try:
            return self.redis.setex(key, ttl, json.dumps(data))
        except Exception as e:
            log_warning(self.logger, f"Cache storage failed: {e}")
            return None

    def get_cached_profile_data(
        self, profile_url: str, company_url: str
    ) -> Optional[Dict]:
        """Get cached profile enrichment data"""
        if self.redis is None:
            return None
            
        key = f"profile:{hashlib.md5(f'{profile_url}:{company_url}'.encode()).hexdigest()}"
        
        # Track access for adaptive TTL
        if self.redis.exists(key):
            cache_manager.access_counts[key] = cache_manager.access_counts.get(key, 0) + 1
            cache_manager.last_access_time[key] = time.time()
            
            # If adaptive TTL is enabled, extend TTL for frequently accessed keys
            if cache_config.enable_adaptive_ttl:
                access_count = cache_manager.access_counts.get(key, 0)
                if access_count > 5:  # Only extend TTL for frequently accessed keys
                    current_ttl = self.redis.ttl(key)
                    if current_ttl > 0:  # Only adjust if key exists and has TTL
                        # Calculate new TTL based on access frequency
                        new_ttl = min(
                            current_ttl * 1.5,  # Increase TTL by 50%
                            cache_config.max_ttl
                        )
                        self.redis.expire(key, int(new_ttl))
                        log_debug(logger, f"Extended TTL for frequently accessed profile: {current_ttl}s -> {int(new_ttl)}s")
        
        try:
            cached_data = self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            log_warning(self.logger, f"Cache retrieval failed: {e}")
        return None

    def cache_faq_answer(self, question: str, answer: str, ttl: int = 86400):
        """Cache FAQ answers with configurable TTL"""
        if self.redis is None:
            return None
            
        # Use FAQ TTL from config if default is used
        if ttl == 86400 and cache_config.faq_ttl != 86400:
            ttl = cache_config.faq_ttl
            
        key = f"faq:{hashlib.md5(question.encode()).hexdigest()}"
        
        # Track access for adaptive TTL
        cache_manager.access_counts[key] = cache_manager.access_counts.get(key, 0) + 1
        cache_manager.last_access_time[key] = time.time()
        
        return self.redis.setex(key, ttl, answer)

    def get_cached_faq_answer(self, question: str) -> Optional[str]:
        """Get cached FAQ answer"""
        if self.redis is None:
            return None
            
        key = f"faq:{hashlib.md5(question.encode()).hexdigest()}"
        
        # Track access for adaptive TTL
        if self.redis.exists(key):
            cache_manager.access_counts[key] = cache_manager.access_counts.get(key, 0) + 1
            cache_manager.last_access_time[key] = time.time()
            
            # If adaptive TTL is enabled, extend TTL for frequently accessed keys
            if cache_config.enable_adaptive_ttl:
                access_count = cache_manager.access_counts.get(key, 0)
                if access_count > 5:  # Only extend TTL for frequently accessed keys
                    current_ttl = self.redis.ttl(key)
                    if current_ttl > 0:  # Only adjust if key exists and has TTL
                        # Calculate new TTL based on access frequency
                        new_ttl = min(
                            current_ttl * 1.5,  # Increase TTL by 50%
                            cache_config.max_ttl
                        )
                        self.redis.expire(key, int(new_ttl))
                        log_debug(logger, f"Extended TTL for frequently accessed FAQ: {current_ttl}s -> {int(new_ttl)}s")
        
        return self.redis.get(key)

    def cache_workflow_result(
            self,
            workflow_id: str,
            result: Dict,
            ttl: int = 3600):
        """Cache complete workflow results with configurable TTL"""
        if self.redis is None:
            return None
            
        # Use workflow TTL from config if default is used
        if ttl == 3600 and cache_config.workflow_ttl != 3600:
            ttl = cache_config.workflow_ttl
            
        key = f"workflow_result:{workflow_id}"
        
        # Track access for adaptive TTL
        cache_manager.access_counts[key] = cache_manager.access_counts.get(key, 0) + 1
        cache_manager.last_access_time[key] = time.time()
        
        return self.redis.setex(key, ttl, json.dumps(result))

    def get_cached_workflow_result(self, workflow_id: str) -> Optional[Dict]:
        """Get cached workflow result"""
        if self.redis is None:
            return None
            
        key = f"workflow_result:{workflow_id}"
        
        # Track access for adaptive TTL
        if self.redis.exists(key):
            cache_manager.access_counts[key] = cache_manager.access_counts.get(key, 0) + 1
            cache_manager.last_access_time[key] = time.time()
            
            # If adaptive TTL is enabled, extend TTL for frequently accessed keys
            if cache_config.enable_adaptive_ttl:
                access_count = cache_manager.access_counts.get(key, 0)
                if access_count > 5:  # Only extend TTL for frequently accessed keys
                    current_ttl = self.redis.ttl(key)
                    if current_ttl > 0:  # Only adjust if key exists and has TTL
                        # Calculate new TTL based on access frequency
                        new_ttl = min(
                            current_ttl * 1.5,  # Increase TTL by 50%
                            cache_config.max_ttl
                        )
                        self.redis.expire(key, int(new_ttl))
                        log_debug(logger, f"Extended TTL for frequently accessed workflow {workflow_id}: {current_ttl}s -> {int(new_ttl)}s")
        
        cached_data = self.redis.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None

    def _get_conversation_embedding(
        self, conversation_text: str
    ) -> Optional[np.ndarray]:
        """Get embedding for conversation text"""
        if not self.similarity_model:
            return None

        try:
            # Clean and normalize text
            clean_text = conversation_text.strip().lower()
            if len(clean_text) < 10:  # Too short for meaningful embedding
                return None

            embedding = self.similarity_model.encode([clean_text])
            return embedding[0]
        except Exception as e:
            log_error(logger, "Error generating embedding", e)
            return None

    def _find_similar_cached_results(
        self, conversation_thread: str, channel: str, threshold: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Find cached results for similar conversations"""
        if not self.similarity_model:
            return None

        threshold = threshold or self.similarity_threshold

        try:
            # Get embedding for current conversation
            current_embedding = self._get_conversation_embedding(
                conversation_thread)
            if current_embedding is None:
                return None

            # Get all cached embeddings for this channel
            pattern = f"embedding:{channel}:*"
            cached_keys = self.redis.keys(pattern)

            if not cached_keys:
                return None

            best_similarity = 0
            best_result = None

            for key in cached_keys:
                try:
                    # Get cached embedding
                    cached_embedding_data = self.redis.get(key)
                    if not cached_embedding_data:
                        continue

                    cached_data = json.loads(cached_embedding_data)
                    cached_embedding = np.array(cached_data["embedding"])

                    # Calculate similarity
                    similarity = cosine_similarity(
                        current_embedding.reshape(1, -1),
                        cached_embedding.reshape(1, -1),
                    )[0][0]

                    if similarity > threshold and similarity > best_similarity:
                        best_similarity = similarity
                        # Get the actual cached result
                        result_key = cached_data["result_key"]
                        cached_result = self.redis.get(result_key)
                        if cached_result:
                            result_data = json.loads(cached_result)
                            result_data["similarity_score"] = similarity
                            result_data["semantic_cache_hit"] = True
                            best_result = result_data

                except Exception as e:
                    log_warning(self.logger,
                        f"Error processing cached embedding {key}: {e}")
                    continue

            if best_result:
                log_info(self.logger,
                    f"Found similar cached result with {best_similarity:.3f} similarity")
                return best_result

        except Exception as e:
            log_error(self.logger, "Error in semantic similarity search", e)

        return None

    def get_cached_workflow_result_smart(
        self, workflow_id: str, conversation_thread: str, channel: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached workflow result with semantic similarity fallback"""
        # First try exact cache match
        exact_result = self.get_cached_workflow_result(workflow_id)
        if exact_result:
            exact_result["cache_type"] = "exact"
            return exact_result

        # Then try semantic similarity
        similar_result = self._find_similar_cached_results(
            conversation_thread, channel)
        if similar_result:
            similar_result["cache_type"] = "semantic"
            return similar_result

        return None

    def cache_workflow_result_smart(
        self,
        workflow_id: str,
        result: Dict[str, Any],
        conversation_thread: str,
        channel: str,
        ttl: int = 3600
    ):
        """Cache workflow result with semantic embedding and configurable TTL"""
        if self.redis is None:
            return None
            
        # Use workflow TTL from config if default is used
        if ttl == 3600 and cache_config.workflow_ttl != 3600:
            ttl = cache_config.workflow_ttl
            
        # Standard caching
        self.cache_workflow_result(workflow_id, result, ttl)

        # Semantic caching
        if self.similarity_model and self.redis:
            try:
                embedding = self._get_conversation_embedding(
                    conversation_thread)
                if embedding is not None:
                    # Store embedding with reference to result
                    embedding_key = f"embedding:{channel}:{workflow_id}"
                    result_key = f"workflow_result:{workflow_id}"

                    embedding_data = {
                        "embedding": embedding.tolist(),
                        "result_key": result_key,
                        "conversation_preview": conversation_thread[:200],
                        "timestamp": time.time(),
                    }

                    # Store with TTL - use double the workflow TTL for embeddings
                    embedding_ttl = min(ttl * 2, cache_config.max_ttl)
                    self.redis.setex(
                        embedding_key, embedding_ttl, json.dumps(embedding_data)
                    )

                    # Track access for adaptive TTL
                    cache_manager.access_counts[embedding_key] = cache_manager.access_counts.get(embedding_key, 0) + 1
                    cache_manager.last_access_time[embedding_key] = time.time()

                    log_info(self.logger,
                        f"Cached semantic embedding for {workflow_id} with TTL {embedding_ttl}s")
            except Exception as e:
                log_error(self.logger, "Error caching semantic embedding", e)


# Update the global cache instance
workflow_cache = SmartWorkflowCache(cache_manager.redis_client)
