import hashlib
import json
import logging
import os
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """
    Enhanced Redis cache manager with advanced features
    """

    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )

        # Test connection
        try:
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except redis.ConnectionError:
            logger.error("Failed to connect to Redis")
            self.redis_client = None

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key from function arguments"""
        # Create a string representation of all arguments
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        # Hash it to create a consistent key
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None

        try:
            cached_value = self.redis_client.get(key)
            if cached_value:
                return json.loads(cached_value)
        except (redis.RedisError, json.JSONDecodeError):
            logger.error(f"Cache get error: {e}")

        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False

        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except (redis.RedisError, json.JSONEncodeError):
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError:
            logger.error(f"Cache delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except redis.RedisError:
            logger.error(f"Cache exists error: {e}")
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
        except redis.RedisError:
            logger.error(f"Cache flush pattern error: {e}")
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
        except redis.RedisError:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


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
                logger.info(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.info(f"Cache miss for {func.__name__}, result cached")

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
                logger.info(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.info(f"Cache miss for {func.__name__}, result cached")

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

        except redis.RedisError:
            logger.error(f"Rate limiter error: {e}")
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
        except redis.RedisError:
            logger.error(f"Metrics increment error: {e}")

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
        except redis.RedisError:
            logger.error(f"Metrics timing error: {e}")

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

        except redis.RedisError:
            logger.error(f"Get metrics error: {e}")
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
                self.logger.info(
                    "Semantic similarity model loaded successfully")
            except Exception as e:
                self.logger.warning(
                    f"Failed to load semantic similarity model: {e}")
                self.similarity_model = None
        else:
            self.similarity_model = None

    # Include all the methods from WorkflowCache
    def cache_profile_data(
        self, profile_url: str, company_url: str, data: Dict, ttl: int = 7200
    ):
        """Cache profile enrichment data (2 hours TTL)"""
        key = f"profile:{hashlib.md5(f'{profile_url}:{company_url}'.encode()).hexdigest()}"
        return self.redis.setex(key, ttl, json.dumps(data))

    def get_cached_profile_data(
        self, profile_url: str, company_url: str
    ) -> Optional[Dict]:
        """Get cached profile enrichment data"""
        key = f"profile:{hashlib.md5(f'{profile_url}:{company_url}'.encode()).hexdigest()}"
        cached_data = self.redis.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None

    def cache_faq_answer(self, question: str, answer: str, ttl: int = 86400):
        """Cache FAQ answers (24 hours TTL)"""
        key = f"faq:{hashlib.md5(question.encode()).hexdigest()}"
        return self.redis.setex(key, ttl, answer)

    def get_cached_faq_answer(self, question: str) -> Optional[str]:
        """Get cached FAQ answer"""
        key = f"faq:{hashlib.md5(question.encode()).hexdigest()}"
        return self.redis.get(key)

    def cache_workflow_result(
            self,
            workflow_id: str,
            result: Dict,
            ttl: int = 3600):
        """Cache complete workflow results (1 hour TTL)"""
        key = f"workflow_result:{workflow_id}"
        return self.redis.setex(key, ttl, json.dumps(result))

    def get_cached_workflow_result(self, workflow_id: str) -> Optional[Dict]:
        """Get cached workflow result"""
        key = f"workflow_result:{workflow_id}"
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
            logger.error(f"Error generating embedding: {e}")
            return None

    def _find_similar_cached_results(
        self, conversation_thread: str, channel: str, threshold: float = None
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
                    self.logger.warning(
                        f"Error processing cached embedding {key}: {e}")
                    continue

            if best_result:
                self.logger.info(
                    f"Found similar cached result with {best_similarity:.3f} similarity"
                )
                return best_result

        except Exception as e:
            self.logger.error(f"Error in semantic similarity search: {e}")

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
    ):
        """Cache workflow result with semantic embedding"""
        # Standard caching
        self.cache_workflow_result(workflow_id, result)

        # Semantic caching
        if self.similarity_model:
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

                    # Store with TTL
                    self.redis.setex(
                        embedding_key, 7200, json.dumps(
                            embedding_data)  # 2 hours
                    )

                    self.logger.info(
                        f"Cached semantic embedding for {workflow_id}")
            except Exception as e:
                self.logger.error(f"Error caching semantic embedding: {e}")


# Update the global cache instance
workflow_cache = SmartWorkflowCache(cache_manager.redis_client)
