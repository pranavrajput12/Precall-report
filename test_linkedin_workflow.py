"""
Test LinkedIn workflow with provided input data
"""
import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8100/api/workflow/execute"

# LinkedIn workflow input data
linkedin_input = {
    "workflow_id": "default_workflow",
    "input_data": {
        "channel": "LinkedIn",
        "conversation_thread": """Rhea Bijlani 00:45 Hi Ivy, impressed by your launch of Bridal.Global and your drive to support bridal vendors. Would love to connect on fundraising challenges. Delivered Avatar Avatar Ivy Yu 00:51 Hi Rhea,

Thank you so much for your kind message and for reaching out. I'm grateful that Bridal.Global resonated with you—it's been a long journey, and the mission to uplift authentic bridal vendors is truly close to my heart.

I'd be happy to share more about our fundraising experience and challenges so far, and I'd also love to hear what kind of companies or sectors you're currently exploring as a Research Analyst at Qubit. Looking forward to connecting and exchanging insights!""",
        "client_linkedin": "https://www.linkedin.com/in/ivysf/",
        "company_website": "http://bridal.global/",
        "company_linkedin": "https://www.linkedin.com/company/bridal-global/",
        "personalization_data": {
            "explicit_questions": ["fundraising challenges", "companies or sectors exploring"],
            "implicit_needs": ["funding support", "investor connections", "strategic advice"]
        }
    }
}

def test_linkedin_workflow():
    """Test the LinkedIn workflow"""
    print("Testing LinkedIn workflow...")
    print(f"Input data: {json.dumps(linkedin_input, indent=2)}")
    
    try:
        # Send request
        response = requests.post(API_URL, json=linkedin_input)
        response.raise_for_status()
        
        # Get response data
        result = response.json()
        print(f"\nResponse status: {response.status_code}")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Check if execution was successful
        if result.get("status") == "completed":
            print("\n✅ Workflow executed successfully!")
            
            # Extract output
            output = result.get("output", {})
            print(f"\nGenerated message: {output.get('immediate_response', {}).get('message', 'No message generated')}")
            print(f"Quality score: {output.get('quality_score', 'N/A')}")
            print(f"Predicted response rate: {output.get('predicted_response_rate', 'N/A')}")
            
            # Check follow-ups
            follow_ups = output.get("follow_up_sequence", [])
            print(f"\nFollow-up messages: {len(follow_ups)}")
            for i, followup in enumerate(follow_ups, 1):
                print(f"\nFollow-up {i} ({followup.get('timing', 'N/A')}):")
                print(f"Message: {followup.get('message', 'N/A')}")
                print(f"Word count: {followup.get('word_count', 'N/A')}")
        else:
            print(f"\n❌ Workflow failed: {result.get('error', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

def check_evaluation_dashboard():
    """Check if evaluation data appears in dashboard"""
    print("\n\nChecking evaluation dashboard...")
    
    try:
        # Get evaluation metrics
        response = requests.get("http://localhost:8100/api/evaluation/metrics")
        response.raise_for_status()
        
        metrics = response.json()
        print(f"Total evaluations: {metrics.get('total_evaluations', 0)}")
        print(f"Average quality score: {metrics.get('average_quality_score', 0)}")
        print(f"Recent evaluations: {len(metrics.get('recent_evaluations', []))}")
        
        if metrics.get('recent_evaluations'):
            print("\nMost recent evaluation:")
            recent = metrics['recent_evaluations'][0]
            print(f"- Execution ID: {recent.get('execution_id')}")
            print(f"- Quality Score: {recent.get('quality_score')}")
            print(f"- Channel: {recent.get('channel')}")
            print(f"- Timestamp: {recent.get('timestamp')}")
            
    except Exception as e:
        print(f"Failed to check evaluation dashboard: {e}")

def check_observability_dashboard():
    """Check if observability data appears in dashboard"""
    print("\n\nChecking observability dashboard...")
    
    try:
        # Get observability history
        response = requests.get("http://localhost:8100/api/observability/history?limit=10")
        response.raise_for_status()
        
        data = response.json()
        print(f"Total records: {data.get('total_records', 0)}")
        
        perf_metrics = data.get('performance_metrics', {})
        print(f"Average duration: {perf_metrics.get('average_duration_ms', 0)}ms")
        print(f"Cache hit rate: {perf_metrics.get('cache_hit_rate', 0):.2%}")
        print(f"Error rate: {perf_metrics.get('error_rate', 0):.2%}")
        
        if data.get('history'):
            print("\nMost recent observability record:")
            recent = data['history'][0]
            print(f"- Execution ID: {recent.get('execution_id')}")
            print(f"- Duration: {recent.get('duration_ms')}ms")
            print(f"- Cache hits: {recent.get('cache_hits')}")
            print(f"- Timestamp: {recent.get('timestamp')}")
            
    except Exception as e:
        print(f"Failed to check observability dashboard: {e}")

if __name__ == "__main__":
    # Test the workflow
    test_linkedin_workflow()
    
    # Wait a moment for data to be saved
    time.sleep(2)
    
    # Check dashboards
    check_evaluation_dashboard()
    check_observability_dashboard()