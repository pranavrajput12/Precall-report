#!/usr/bin/env python3
"""
Test script for CrewAI workflow with email sequence data
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow import run_workflow
from config_manager import ConfigManager

def test_email_sequence_workflow():
    """Test the workflow with email sequence data"""
    
    print("🚀 Starting CrewAI Workflow Test - Email Sequence")
    print("=" * 60)
    
    # Email sequence input data
    input_data = {
        "channel": "Email",
        "conversation_thread": """Hi Freya,

Thanks for reaching out.

Yes, we are currently experiencing some capital-related roadblocks, so I'd definitely be interested in hearing more about what you have in mind.

Looking forward to your thoughts!

Best regards,

Francesco

On Tue, 6 May 2025 at 10:30, Freya Jones freya@seedfundraisingplatformhub.com wrote: Hi Francesco,

I've been following Click-match's journey in the sports tech space. Your focus on connecting players through personalized services is impressive.

However, many companies like yours face hurdles in securing funding to scale operations. Are you currently experiencing any capital roadblocks?

P.S. I'd love to hear your thoughts!

Let's Grow Together ! Freya Jones Venture Scout Qubit Capital

Is this something you're not interested in? Just say so and I'll take my hive elsewhere.

-- Francesco Tozzi Spadoni Lorella

Founder & CEO @ click-match www.click-match.com Tel: 0041779060890""",
        "client_linkedin": "https://www.linkedin.com/in/ftsl/",
        "company_website": "http://click-match.com",
        "company_linkedin": "https://www.linkedin.com/company/click-match/"
    }
    
    print("📧 Input Data:")
    print(f"   Channel: {input_data['channel']}")
    print(f"   Client LinkedIn: {input_data['client_linkedin']}")
    print(f"   Company Website: {input_data['company_website']}")
    print(f"   Company LinkedIn: {input_data['company_linkedin']}")
    print(f"   Conversation Length: {len(input_data['conversation_thread'])} characters")
    print()
    
    try:
        start_time = datetime.now()
        print("⏳ Running workflow...")
        
        # Run the workflow
        result = run_workflow(
            conversation_thread=input_data['conversation_thread'],
            channel=input_data['channel'],
            prospect_profile_url=input_data['client_linkedin'],
            prospect_company_url=input_data['company_linkedin'],
            prospect_company_website=input_data['company_website']
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print("✅ Workflow completed successfully!")
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        print()
        
        # Save to database first
        print("💾 Saving to database...")
        config_manager = ConfigManager()
        
        # Prepare input data for saving
        input_data_for_db = {
            "channel": input_data['channel'],
            "conversation_thread": input_data['conversation_thread'],
            "client_linkedin": input_data['client_linkedin'],
            "company_website": input_data['company_website'],
            "company_linkedin": input_data['company_linkedin']
        }
        
        execution_id = config_manager.save_execution_history(
            workflow_id=f"email_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_id="email_reply_agent",
            prompt_id="default_prompt",
            input_data=json.dumps(input_data_for_db),
            output_data=json.dumps(result) if isinstance(result, dict) else str(result),
            execution_time=execution_time,
            status="success"
        )
        
        print(f"✅ Saved execution: {execution_id}")
        print()
        
        # Display results
        print("📋 WORKFLOW RESULTS:")
        print("=" * 40)
        
        if isinstance(result, dict):
            # Display immediate response
            if 'immediate_response' in result:
                print("💬 Immediate Response:")
                print(result['immediate_response'])
                print()
            
            # Display follow-up sequence
            if 'follow_up_sequence' in result:
                print("📨 Follow-up Sequence:")
                for i, follow_up in enumerate(result['follow_up_sequence'], 1):
                    print(f"   {i}. {follow_up}")
                print()
            
            # Display quality metrics
            if 'quality_score' in result:
                print(f"⭐ Quality Score: {result['quality_score']}")
            
            if 'predicted_response_rate' in result:
                print(f"📈 Predicted Response Rate: {result['predicted_response_rate']}")
            
            print()
            
        else:
            print("📄 Raw Result:")
            print(result)
            print()
        
        # Verify database save
        print("🔍 Verifying database save...")
        config_manager = ConfigManager()
        recent_executions = config_manager.get_execution_history(limit=1)
        
        if recent_executions:
            latest = recent_executions[0]
            print(f"✅ Latest execution saved with ID: {latest['id']}")
            print(f"   Status: {latest['status']}")
            print(f"   Execution time: {latest['execution_time']:.2f}s")
            
            # Check if output contains our expected data
            output = latest.get('output', {})
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except:
                    pass
            
            if isinstance(output, dict):
                if output.get('quality_score'):
                    print(f"   Quality score: {output['quality_score']}")
                if output.get('predicted_response_rate'):
                    print(f"   Predicted response rate: {output['predicted_response_rate']}")
        else:
            print("❌ No recent executions found in database")
        
        print()
        print("🎉 Email sequence test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_email_sequence_workflow()
    sys.exit(0 if success else 1)
