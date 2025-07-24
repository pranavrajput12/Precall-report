#!/usr/bin/env python3
"""
Test script for pagination features.

This script tests the pagination functionality in the API endpoints:
1. /api/test-results
2. /api/performance/metrics
3. /api/evaluation/summary
4. /api/optimization/summary
"""

import json
import time
import requests
from typing import Dict, Any, List
from pprint import pprint

# Import API modules
from enhanced_api import enhanced_app
from fastapi.testclient import TestClient

# Create test client
client = TestClient(enhanced_app)

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

def test_pagination_endpoint(endpoint: str, name: str):
    """Test pagination for a specific endpoint"""
    print(f"\nTesting pagination for {name} ({endpoint}):")
    
    # Test default pagination (page 1, default page size)
    response_default = client.get(endpoint)
    print_result(f"{name} - Default Pagination", 
                response_default.status_code == 200,
                f"Status: {response_default.status_code}")
    
    if response_default.status_code == 200:
        data_default = response_default.json()
        has_pagination = "pagination" in data_default
        print_result(f"{name} - Has Pagination Info", has_pagination)
        
        if has_pagination:
            pagination = data_default["pagination"]
            print(f"  Pagination: {json.dumps(pagination, indent=2)}")
            
            # Check pagination fields
            has_required_fields = all(field in pagination for field 
                                     in ["page", "page_size", "total", "total_pages"])
            print_result(f"{name} - Has Required Pagination Fields", has_required_fields)
            
            # Test with explicit page and page_size
            page = 1
            page_size = 5
            response_custom = client.get(f"{endpoint}?page={page}&page_size={page_size}")
            
            print_result(f"{name} - Custom Pagination", 
                        response_custom.status_code == 200,
                        f"Status: {response_custom.status_code}")
            
            if response_custom.status_code == 200:
                data_custom = response_custom.json()
                
                if "pagination" in data_custom:
                    custom_pagination = data_custom["pagination"]
                    correct_page = custom_pagination.get("page") == page
                    correct_size = custom_pagination.get("page_size") == page_size
                    
                    print_result(f"{name} - Correct Page", correct_page, 
                                f"Expected: {page}, Got: {custom_pagination.get('page')}")
                    print_result(f"{name} - Correct Page Size", correct_size, 
                                f"Expected: {page_size}, Got: {custom_pagination.get('page_size')}")
                    
                    # If there are multiple pages, test page 2
                    if custom_pagination.get("total_pages", 0) > 1:
                        page2 = 2
                        response_page2 = client.get(f"{endpoint}?page={page2}&page_size={page_size}")
                        
                        print_result(f"{name} - Page 2 Access", 
                                    response_page2.status_code == 200,
                                    f"Status: {response_page2.status_code}")
                        
                        if response_page2.status_code == 200:
                            data_page2 = response_page2.json()
                            
                            if "pagination" in data_page2:
                                page2_pagination = data_page2["pagination"]
                                correct_page2 = page2_pagination.get("page") == page2
                                
                                print_result(f"{name} - Correct Page 2", correct_page2, 
                                            f"Expected: {page2}, Got: {page2_pagination.get('page')}")
                                
                                # Check that data is different between pages
                                if "data" in data_custom and "data" in data_page2:
                                    data_different = data_custom.get("data") != data_page2.get("data")
                                    print_result(f"{name} - Different Data Between Pages", 
                                                data_different)
            
            # Test invalid page
            invalid_page = 9999
            response_invalid = client.get(f"{endpoint}?page={invalid_page}")
            
            # Should either return a 404 or a valid response with empty data
            valid_response = (response_invalid.status_code == 404 or 
                             (response_invalid.status_code == 200 and 
                              "data" in response_invalid.json() and 
                              len(response_invalid.json().get("data", [])) == 0))
            
            print_result(f"{name} - Invalid Page Handling", valid_response,
                        f"Status: {response_invalid.status_code}")

def main():
    """Run all tests"""
    print_section("PAGINATION TESTS")
    
    # Endpoints to test
    endpoints = [
        ("/api/test-results", "Test Results"),
        ("/api/performance/metrics", "Performance Metrics"),
        ("/api/evaluation/summary", "Evaluation Summary"),
        ("/api/optimization/summary", "Optimization Summary")
    ]
    
    try:
        # Test each endpoint
        for endpoint, name in endpoints:
            test_pagination_endpoint(endpoint, name)
        
        print_section("ALL PAGINATION TESTS COMPLETED")
        
    except Exception as e:
        print(f"Error during tests: {e}")
        raise

if __name__ == "__main__":
    main()