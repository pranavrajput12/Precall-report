#!/usr/bin/env python3
"""
Test script to execute a workflow run and verify it appears in the frontend
"""

import asyncio
import json
import time
from datetime import datetime
from workflow_executor import workflow_executor
from config_manager import config_manager

async def run_test_workflow():
    """Execute a test workflow with Nick Rothwell / Drive Fuze data"""
    
    print("🚀 Starting Test Workflow Execution...")
    print("=" * 50)
    
    # Test data from user input
    workflow_data = {
        "workflow_id": "default_workflow",
        "channel": "LinkedIn",
        "conversation_thread": "Nick, your leadership at Drive Fuze pioneering FCA-regulated car subscriptions shows strong market insight amid funding challenges in mobility. Delivered Avatar Avatar Nick Rothwell 20:24 Thanks for connecting lets chat if you want to Delivered Avatar Nick Rothwell 20:25 nick.rothwell@drivefuze.com",
        "prospect_profile_url": "https://www.linkedin.com/in/nick-rothwell-62576a24/",
        "prospect_company_url": "https://www.linkedin.com/company/drive-fuze-ltd/",
        "prospect_company_website": "www.drivefuze.com",
        "include_thread_analysis": True,
        "include_reply_generation": True,
        "personalization_data": {
            "explicit_questions": [],
            "implicit_needs": ["car subscription", "FCA regulation", "mobility funding"]
        },
        "_executed_by": "test_user",
        "_executed_at": datetime.now().isoformat()
    }
    
    print(f"📋 Input Data:")
    print(f"   - Channel: {workflow_data['channel']}")
    print(f"   - Prospect: Nick Rothwell (Drive Fuze)")
    print(f"   - Profile: {workflow_data['prospect_profile_url']}")
    print(f"   - Company: {workflow_data['prospect_company_url']}")
    print()
    
    try:
        # Execute the workflow
        print("⚙️ Executing workflow...")
        start_time = time.time()
        
        result = await workflow_executor.execute_workflow(workflow_data)
        
        execution_time = time.time() - start_time
        
        print(f"✅ Workflow completed in {execution_time:.2f}s")
        print(f"📊 Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'error':
            print(f"❌ Error: {result.get('error_message', 'Unknown error')}")
        else:
            print(f"🎯 Results: {len(result.get('results', {}))} steps completed")
        
        print()
        print("🔍 Checking database for new execution...")
        
        # Check if execution was saved to database
        history = config_manager.get_execution_history(limit=5)
        latest_execution = history[0] if history else None
        
        if latest_execution:
            print(f"✅ Latest execution in database:")
            print(f"   - ID: {latest_execution['id']}")
            print(f"   - Workflow: {latest_execution['workflow_name']}")
            print(f"   - Status: {latest_execution['status']}")
            print(f"   - Created: {latest_execution['created_at']}")
        else:
            print("❌ No executions found in database")
            
        print()
        print("🎉 Test workflow execution complete!")
        print("📱 Check the frontend at http://localhost:3000/all-runs to see the new execution")
        
        return result
        
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(run_test_workflow())
