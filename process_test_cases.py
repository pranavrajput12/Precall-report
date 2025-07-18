import csv
import json
import requests
import time
from datetime import datetime

def extract_test_case(row):
    """Extract test case data from CSV row"""
    input_text = row['Input']
    
    # Parse the input text to extract components
    lines = input_text.split('\n')
    
    # Extract conversation thread
    conversation_thread = ""
    client_linkedin = ""
    company_website = ""
    company_linkedin = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith('Conversation thread - '):
            conversation_thread = line.replace('Conversation thread - ', '')
        elif line.startswith('Client linkedin - '):
            client_linkedin = line.replace('Client linkedin - ', '')
        elif line.startswith('Company website - '):
            company_website = line.replace('Company website - ', '')
        elif line.startswith('Company linkedin - '):
            company_linkedin = line.replace('Company linkedin - ', '')
    
    return {
        "conversation_thread": conversation_thread,
        "channel": "LinkedIn",
        "prospect_profile_url": client_linkedin,
        "prospect_company_url": company_linkedin,
        "prospect_company_website": company_website,
        "qubit_context": "Qubit Capital investment focus and AI-driven fundraising platform"
    }

def run_workflow_test_case(test_case, case_number):
    """Run a single test case through the workflow"""
    print(f"\n🚀 Running Test Case {case_number}...")
    print(f"Prospect: {test_case['prospect_profile_url']}")
    
    try:
        response = requests.post(
            'http://localhost:8100/run',
            json=test_case,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test Case {case_number} completed successfully!")
            print(f"Execution ID: {result.get('execution_id', 'N/A')}")
            return True
        else:
            print(f"❌ Test Case {case_number} failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test Case {case_number} failed with exception: {str(e)}")
        return False

def main():
    # Read the CSV file
    test_cases = []
    
    with open('/Users/pronav/Downloads/Pre-Call Agent Replies.csv', 'r', encoding='latin-1') as file:
        reader = csv.DictReader(file)
        for row in reader:
            test_case = extract_test_case(row)
            if test_case['conversation_thread'] and test_case['prospect_profile_url']:
                test_cases.append(test_case)
    
    print(f"📊 Found {len(test_cases)} test cases to process")
    
    # Process test cases in batches
    batch_size = 3
    successful_runs = 0
    
    for i in range(0, len(test_cases), batch_size):
        batch = test_cases[i:i+batch_size]
        print(f"\n🔄 Processing Batch {(i//batch_size) + 1} ({len(batch)} test cases)")
        
        for j, test_case in enumerate(batch):
            case_number = i + j + 1
            success = run_workflow_test_case(test_case, case_number)
            if success:
                successful_runs += 1
            
            # Small delay between requests
            time.sleep(2)
        
        # Longer delay between batches
        if i + batch_size < len(test_cases):
            print(f"⏳ Waiting 5 seconds before next batch...")
            time.sleep(5)
    
    print(f"\n🎉 Processing complete!")
    print(f"✅ Successful runs: {successful_runs}/{len(test_cases)}")
    print(f"📈 Success rate: {(successful_runs/len(test_cases)*100):.1f}%")
    
    # Check execution history
    try:
        response = requests.get('http://localhost:8100/api/execution-history')
        if response.status_code == 200:
            executions = response.json()
            print(f"\n📋 Current execution history: {len(executions)} records")
        else:
            print(f"\n❌ Failed to fetch execution history: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Error fetching execution history: {str(e)}")

if __name__ == "__main__":
    main() 