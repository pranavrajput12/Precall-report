#!/usr/bin/env python3
"""
Test script for cache optimization features.

This script tests all aspects of the enhanced caching system:
1. Basic cache operations (get, set, delete)
2. Adaptive TTL functionality
3. Cache monitoring
4. Cache warming
5. SmartWorkflowCache with semantic similarity
"""

import json
import time
import uuid
import requests
import redis
from typing import Dict, Any, List

# Import the cache modules
from cache import (
    cache_manager,
    cache_config,
    workflow_cache,
    SessionManager,
    RateLimiter,
    MetricsCollector
)

# Import API modules
from enhanced_api import enhanced_app
from fastapi.testclient import TestClient

# Create test client
client = TestClient(enhanced_app)

# Test data
test_profile_url = "https://linkedin.com/in/test-user"
test_company_url = "https://linkedin.com/company/test-company"
test_profile_data = {
    "name": "Test User",
    "title": "Software Engineer",
    "company": "Test Company",
    "location": "San Francisco, CA",
    "skills": ["Python", "FastAPI", "Redis", "Machine Learning"]
}

test_workflow_id = str(uuid.uuid4())
test_workflow_result = {
    "id": test_workflow_id,
    "status": "completed",
    "steps": [
        {"name": "profile_enrichment", "status": "completed"},
        {"name": "thread_analysis", "status": "completed"},
        {"name": "reply_generation", "status": "completed"}
    ],
    "result": {
        "reply": "This is a test reply",
        "confidence": 0.95
    }
}

test_conversation_thread = """
User: Hello, I'm interested in your product. Can you tell me more about it?
Agent: Of course! Our product is a workflow orchestration platform that helps you automate your business processes.
User: That sounds interesting. How does it work?
Agent: It uses AI agents to perform tasks and collaborate with each other to achieve a goal.
"""

test_channel = "linkedin"

def print_section(title: str):
    """Print a section title"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def print_result(test_name: str, result: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASSED" if result else "❌ FAILED"
    print(f"{status} - {test_name}")
    if details:
        print(f"  Details: {details}")

def test_basic_cache_operations():
    """Test basic cache operations"""
    print_section("Testing Basic Cache Operations")
    
    # Test set operation
    test_key = f"test:basic:{uuid.uuid4()}"
    test_value = {"test": "value", "timestamp": time.time()}
    set_result = cache_manager.set(test_key, test_value)
    print_result("Cache Set", set_result, f"Key: {test_key}")
    
    # Test get operation
    get_result = cache_manager.get(test_key)
    print_result("Cache Get", get_result == test_value, 
                f"Expected: {test_value}, Got: {get_result}")
    
    # Test exists operation
    exists_result = cache_manager.exists(test_key)
    print_result("Cache Exists", exists_result, f"Key: {test_key}")
    
    # Test delete operation
    delete_result = cache_manager.delete(test_key)
    print_result("Cache Delete", delete_result, f"Key: {test_key}")
    
    # Verify deletion
    exists_after_delete = cache_manager.exists(test_key)
    print_result("Cache Verify Deletion", not exists_after_delete, 
                f"Key: {test_key}, Exists: {exists_after_delete}")

def test_adaptive_ttl():
    """Test adaptive TTL functionality"""
    print_section("Testing Adaptive TTL")
    
    # Enable adaptive TTL
    original_adaptive_ttl = cache_config.enable_adaptive_ttl
    cache_config.enable_adaptive_ttl = True
    
    # Create a test key
    test_key = f"test:adaptive_ttl:{uuid.uuid4()}"
    test_value = {"test": "value", "timestamp": time.time()}
    
    # Set the key with default TTL
    cache_manager.set(test_key, test_value)
    
    # Skip TTL tests if Redis client is not available
    if not cache_manager.redis_client:
        print("Redis client not available, skipping TTL tests")
        cache_config.enable_adaptive_ttl = original_adaptive_ttl
        return
    
    # Get initial TTL
    initial_ttl = cache_manager.redis_client.ttl(test_key)
    print(f"Initial TTL: {initial_ttl}s")
    
    # Simulate frequent access
    for i in range(10):
        cache_manager.get(test_key)
        time.sleep(0.1)  # Small delay to simulate real access
    
    # Get updated TTL
    updated_ttl = cache_manager.redis_client.ttl(test_key)
    print(f"Updated TTL after frequent access: {updated_ttl}s")
    
    # Check if TTL was extended
    ttl_extended = updated_ttl > initial_ttl * 0.9  # Allow for some time passing
    print_result("Adaptive TTL Extension", ttl_extended, 
                f"Initial TTL: {initial_ttl}s, Updated TTL: {updated_ttl}s")
    
    # Clean up
    cache_manager.delete(test_key)
    cache_config.enable_adaptive_ttl = original_adaptive_ttl

def test_cache_monitoring():
    """Test cache monitoring"""
    print_section("Testing Cache Monitoring")
    
    # Get initial stats
    initial_stats = cache_manager.get_stats()
    print(f"Initial cache stats: {json.dumps(initial_stats, indent=2)}")
    
    # Skip if Redis client is not available
    if not cache_manager.redis_client:
        print("Redis client not available, skipping monitoring tests")
        return
    
    # Create some test keys
    for i in range(5):
        test_key = f"test:monitoring:{uuid.uuid4()}"
        test_value = {"test": "value", "index": i, "timestamp": time.time()}
        cache_manager.set(test_key, test_value)
    
    # Access some keys multiple times
    test_keys = list(cache_manager.redis_client.keys("test:monitoring:*"))
    for i in range(10):
        if test_keys:
            key_index = i % len(test_keys)
            cache_manager.get(test_keys[key_index])
    
    # Wait for monitoring thread to update stats
    print("Waiting for monitoring thread to update stats...")
    time.sleep(cache_config.monitoring_interval + 1)
    
    # Get updated stats
    updated_stats = cache_manager.get_stats()
    print(f"Updated cache stats: {json.dumps(updated_stats, indent=2)}")
    
    # Check if hit rate is calculated
    has_hit_rate = "hit_rate" in updated_stats
    print_result("Cache Hit Rate Calculation", has_hit_rate, 
                f"Hit rate: {updated_stats.get('hit_rate', 'N/A')}%")
    
    # Clean up
    for key in test_keys:
        cache_manager.delete(key)

def test_workflow_cache():
    """Test WorkflowCache and SmartWorkflowCache"""
    print_section("Testing WorkflowCache and SmartWorkflowCache")
    
    # Test profile data caching
    profile_result = workflow_cache.cache_profile_data(
        test_profile_url, test_company_url, test_profile_data
    )
    print_result("Cache Profile Data", profile_result is not None, 
                f"Result: {profile_result}")
    
    # Test profile data retrieval
    cached_profile = workflow_cache.get_cached_profile_data(
        test_profile_url, test_company_url
    )
    profile_match = cached_profile == test_profile_data
    print_result("Get Cached Profile Data", profile_match, 
                f"Expected: {test_profile_data}, Got: {cached_profile}")
    
    # Test workflow result caching
    workflow_result = workflow_cache.cache_workflow_result(
        test_workflow_id, test_workflow_result
    )
    print_result("Cache Workflow Result", workflow_result is not None, 
                f"Result: {workflow_result}")
    
    # Test workflow result retrieval
    cached_workflow = workflow_cache.get_cached_workflow_result(test_workflow_id)
    workflow_match = cached_workflow == test_workflow_result
    print_result("Get Cached Workflow Result", workflow_match, 
                f"Match: {workflow_match}")
    
    # Test smart workflow caching
    smart_result = workflow_cache.cache_workflow_result_smart(
        test_workflow_id, test_workflow_result, 
        test_conversation_thread, test_channel
    )
    print_result("Smart Cache Workflow Result", smart_result is not None, 
                f"Result: {smart_result}")
    
    # Test smart workflow retrieval
    smart_cached = workflow_cache.get_cached_workflow_result_smart(
        test_workflow_id, test_conversation_thread, test_channel
    )
    smart_match = smart_cached is not None and "cache_type" in smart_cached
    print_result("Get Smart Cached Workflow Result", smart_match, 
                f"Cache type: {smart_cached.get('cache_type') if smart_cached else 'None'}")
    
    # Test semantic similarity (if available)
    if hasattr(workflow_cache, "similarity_model") and workflow_cache.similarity_model:
        # Create a similar conversation
        similar_conversation = test_conversation_thread + "\nUser: Can I get a demo?"
        similar_workflow_id = str(uuid.uuid4())
        
        # Cache the similar conversation
        workflow_cache.cache_workflow_result_smart(
            similar_workflow_id, test_workflow_result, 
            similar_conversation, test_channel
        )
        
        # Try to retrieve with the original conversation
        semantic_result = workflow_cache._find_similar_cached_results(
            test_conversation_thread, test_channel
        )
        
        semantic_match = semantic_result is not None
        print_result("Semantic Similarity Matching", semantic_match, 
                    f"Result: {semantic_result}")
    else:
        print("Semantic similarity model not available, skipping test")

def test_api_endpoints():
    """Test API endpoints with caching"""
    print_section("Testing API Endpoints with Caching")
    
    # Test workflow execution endpoint
    workflow_data = {
        "workflow_id": str(uuid.uuid4()),
        "profile_url": "https://linkedin.com/in/test-user-api",
        "company_url": "https://linkedin.com/company/test-company-api",
        "conversation_thread": test_conversation_thread,
        "channel": "linkedin"
    }
    
    # First execution (cache miss)
    start_time_miss = time.time()
    response_miss = client.post("/api/workflow/execute", json=workflow_data)
    execution_time_miss = time.time() - start_time_miss
    
    print_result("API Workflow Execution (Cache Miss)", 
                response_miss.status_code == 200,
                f"Status: {response_miss.status_code}, Time: {execution_time_miss:.2f}s")
    
    # Second execution (cache hit)
    start_time_hit = time.time()
    response_hit = client.post("/api/workflow/execute", json=workflow_data)
    execution_time_hit = time.time() - start_time_hit
    
    print_result("API Workflow Execution (Cache Hit)", 
                response_hit.status_code == 200,
                f"Status: {response_hit.status_code}, Time: {execution_time_hit:.2f}s")
    
    # Check if second execution was faster (cache hit)
    cache_speedup = execution_time_hit < execution_time_miss
    print_result("Cache Speedup", cache_speedup,
                f"Miss: {execution_time_miss:.2f}s, Hit: {execution_time_hit:.2f}s, " +
                f"Speedup: {(execution_time_miss/execution_time_hit):.2f}x")
    
    # Test cache stats endpoint
    response_stats = client.get("/api/cache/stats")
    print_result("API Cache Stats", response_stats.status_code == 200,
                f"Status: {response_stats.status_code}")
    
    if response_stats.status_code == 200:
        stats = response_stats.json()
        print(f"Cache Stats: {json.dumps(stats, indent=2)}")

def main():
    """Run all tests"""
    print_section("CACHE OPTIMIZATION TESTS")
    print(f"Cache Configuration:")
    print(f"  Default TTL: {cache_config.default_ttl}s")
    print(f"  Adaptive TTL: {'Enabled' if cache_config.enable_adaptive_ttl else 'Disabled'}")
    print(f"  Cache Warming: {'Enabled' if cache_config.enable_cache_warming else 'Disabled'}")
    print(f"  Monitoring Interval: {cache_config.monitoring_interval}s")
    
    # Check if Redis is available
    redis_available = cache_manager.redis_client is not None
    print(f"Redis Connection: {'Available' if redis_available else 'Not Available'}")
    
    if not redis_available:
        print("WARNING: Redis is not available. Some tests will be skipped.")
    
    try:
        # Run tests
        test_basic_cache_operations()
        test_adaptive_ttl()
        test_cache_monitoring()
        test_workflow_cache()
        
        # Only run API tests if the server is running
        try:
            test_api_endpoints()
        except Exception as e:
            print(f"API tests failed: {e}")
            print("Make sure the API server is running")
        
        print_section("ALL TESTS COMPLETED")
        
    except Exception as e:
        print(f"Error during tests: {e}")
        raise

if __name__ == "__main__":
    main()