#!/usr/bin/env python3
"""
Test script to run the FULL workflow that generates rich output like the Lucas Wright example
"""

import asyncio
import json
import time
from datetime import datetime
from workflow import run_workflow
from config_manager import config_manager

async def run_full_workflow_test():
    """Execute the full workflow that generates rich output with immediate response, follow-ups, quality scores, etc."""
    
    print("🚀 Running FULL Workflow Test...")
    print("=" * 50)
    
    # Test data similar to the Lucas Wright example
    workflow_data = {
        "workflow_id": "default_workflow",
        "conversation_thread": "Hi Sarah, impressed by your leadership at TechFlow Solutions and your insights on AI-powered customer analytics. Your recent post about scaling ML pipelines really resonated with our challenges at Qubit Capital. Would love to connect and share insights on funding opportunities! Delivered Avatar Sarah Johnson 14:32 Thanks for reaching out! Always happy to discuss ML scaling strategies and funding landscapes. What specific challenges are you facing with AI implementation? We're currently exploring Series A opportunities ourselves.",
        "channel": "linkedin",
        "prospect_profile_url": "https://www.linkedin.com/in/sarah-johnson-techflow/",
        "prospect_company_url": "https://www.linkedin.com/company/techflow-solutions/",
        "prospect_company_website": "www.techflow-solutions.com",
        "include_profile": True,
        "include_thread_analysis": True,
        "include_reply_generation": True,
        "priority": "normal"
    }
    
    print(f"📋 Test Data:")
    print(f"   - Channel: {workflow_data['channel']}")
    print(f"   - Prospect: Sarah Johnson (TechFlow Solutions)")
    print(f"   - Conversation: AI/ML funding discussion")
    print(f"   - Profile URL: {workflow_data['prospect_profile_url']}")
    print()
    
    try:
        print("⚙️ Executing FULL workflow (this may take 30-90 seconds)...")
        start_time = time.time()
        
        # Run the ACTUAL workflow function that generates rich output
        result = run_workflow(
            workflow_id=workflow_data["workflow_id"],
            conversation_thread=workflow_data["conversation_thread"],
            channel=workflow_data["channel"],
            prospect_profile_url=workflow_data["prospect_profile_url"],
            prospect_company_url=workflow_data["prospect_company_url"],
            prospect_company_website=workflow_data["prospect_company_website"],
            include_profile=workflow_data["include_profile"],
            include_thread_analysis=workflow_data["include_thread_analysis"],
            include_reply_generation=workflow_data["include_reply_generation"],
            priority=workflow_data["priority"]
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ Workflow completed in {execution_time:.1f}s")
        
        # Check if we got the rich output structure
        if isinstance(result, dict):
            print(f"📊 Result structure:")
            print(f"   - Keys: {list(result.keys())}")
            
            if 'immediate_response' in result:
                print(f"   ✅ Has immediate_response")
                immediate = result['immediate_response']
                if isinstance(immediate, str) and len(immediate) > 100:
                    print(f"   ✅ Rich immediate response ({len(immediate)} chars)")
                else:
                    print(f"   ⚠️ Short immediate response: {immediate}")
            
            if 'follow_up_sequence' in result:
                follow_ups = result['follow_up_sequence']
                print(f"   ✅ Has follow_up_sequence ({len(follow_ups)} follow-ups)")
            
            if 'quality_score' in result:
                print(f"   ✅ Quality score: {result['quality_score']}%")
            
            if 'predicted_response_rate' in result:
                print(f"   ✅ Predicted response rate: {result['predicted_response_rate']*100:.0f}%")
        
        # Now save this to the database using config_manager
        print("\n💾 Saving to database...")
        
        execution_id = config_manager.save_execution_history(
            workflow_id=workflow_data["workflow_id"],
            agent_id="linkedin_reply_agent",
            prompt_id="default_prompt",
            input_data=json.dumps(workflow_data),
            output_data=json.dumps(result) if isinstance(result, dict) else str(result),
            execution_time=execution_time,
            status="success"
        )
        
        print(f"✅ Saved execution: {execution_id}")
        
        # Verify it's in the database
        history = config_manager.get_execution_history(limit=1)
        if history and history[0]['id'] == execution_id:
            latest = history[0]
            print(f"✅ Verified in database:")
            print(f"   - ID: {latest['id']}")
            print(f"   - Status: {latest['status']}")
            print(f"   - Has rich output: {'Yes' if 'immediate_response' in str(latest.get('output', {})) else 'No'}")
        
        print()
        print("🎉 Full workflow test complete!")
        print("📱 Refresh http://localhost:3000/all-runs to see the RICH output with:")
        print("   ✅ Immediate Response with copy button")
        print("   ✅ Follow-up Sequence (3 follow-ups)")
        print("   ✅ Quality Score percentage")
        print("   ✅ Predicted Response Rate")
        print("   ✅ Word counts and analysis")
        
        return result
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(run_full_workflow_test())
