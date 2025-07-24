#!/usr/bin/env python3
"""
Test script to create a new execution with rich data to verify frontend display
"""

import asyncio
import json
import time
from datetime import datetime
from workflow_executor import workflow_executor
from config_manager import config_manager

async def run_new_test():
    """Execute a new test workflow with rich data"""
    
    print("🚀 Creating New Test Execution...")
    print("=" * 50)
    
    # Rich test data
    workflow_data = {
        "workflow_id": "default_workflow",
        "channel": "LinkedIn",
        "conversation_thread": "Hi Sarah, I noticed your work at TechFlow Solutions on AI-powered customer analytics. Your recent post about scaling ML pipelines really resonated with our challenges at Qubit Capital. Would love to connect and share insights! Delivered Avatar Sarah Johnson 14:32 Thanks for reaching out! Always happy to discuss ML scaling strategies. What specific challenges are you facing?",
        "prospect_profile_url": "https://www.linkedin.com/in/sarah-johnson-techflow/",
        "prospect_company_url": "https://www.linkedin.com/company/techflow-solutions/",
        "prospect_company_website": "www.techflow-solutions.com",
        "include_thread_analysis": True,
        "include_reply_generation": True,
        "personalization_data": {
            "explicit_questions": [
                "What ML scaling strategies work best?",
                "How do you handle data pipeline bottlenecks?"
            ],
            "implicit_needs": [
                "ML pipeline optimization",
                "customer analytics",
                "scaling challenges",
                "AI implementation"
            ]
        },
        "_executed_by": "demo_user",
        "_executed_at": datetime.now().isoformat()
    }
    
    print(f"📋 New Test Data:")
    print(f"   - Channel: {workflow_data['channel']}")
    print(f"   - Prospect: Sarah Johnson (TechFlow Solutions)")
    print(f"   - Conversation: ML pipeline discussion")
    print(f"   - Implicit Needs: {len(workflow_data['personalization_data']['implicit_needs'])} items")
    print(f"   - Explicit Questions: {len(workflow_data['personalization_data']['explicit_questions'])} items")
    print()
    
    try:
        # Execute the workflow
        print("⚙️ Executing workflow...")
        start_time = time.time()
        
        result = await workflow_executor.execute_workflow(workflow_data)
        
        execution_time = time.time() - start_time
        
        print(f"✅ Workflow completed in {execution_time:.2f}s")
        print(f"📊 Status: {result.get('status', 'unknown')}")
        
        # Check latest execution
        history = config_manager.get_execution_history(limit=1)
        latest_execution = history[0] if history else None
        
        if latest_execution:
            print(f"✅ New execution created:")
            print(f"   - ID: {latest_execution['id']}")
            print(f"   - Workflow: {latest_execution['workflow_name']}")
            print(f"   - Status: {latest_execution['status']}")
            print(f"   - Has conversation thread: {'Yes' if latest_execution.get('input_data', {}).get('conversation_thread') else 'No'}")
            print(f"   - Has personalization data: {'Yes' if latest_execution.get('input_data', {}).get('personalization_data') else 'No'}")
        
        print()
        print("🎉 New test execution complete!")
        print("📱 Refresh http://localhost:3000/all-runs to see the enhanced display")
        
        return result
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(run_new_test())
