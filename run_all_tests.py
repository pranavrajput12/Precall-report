#!/usr/bin/env python3
"""
Run all tests for the CrewAI Workflow Orchestration Platform.

This script runs all the test scripts we've created to verify our implementation:
1. test_cache_optimization.py - Tests the caching optimization features
2. test_pagination.py - Tests the pagination features
3. verify_enhanced_references.py - Verifies file references for enhanced files
"""

import os
import sys
import subprocess
import time
from typing import List, Tuple

def print_section(title: str):
    """Print a section title"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def run_test(test_script: str) -> Tuple[int, str, str, float]:
    """Run a test script and return the result"""
    print(f"\nRunning {test_script}...")
    
    start_time = time.time()
    process = subprocess.Popen(
        [sys.executable, test_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    duration = time.time() - start_time
    
    return process.returncode, stdout, stderr, duration

def main():
    """Main function"""
    print_section("RUNNING ALL TESTS")
    
    # List of test scripts to run
    test_scripts = [
        "test_cache_optimization.py",
        "test_pagination.py",
        "verify_enhanced_references.py"
    ]
    
    # Check if all test scripts exist
    missing_scripts = [script for script in test_scripts if not os.path.exists(script)]
    if missing_scripts:
        print("ERROR: The following test scripts are missing:")
        for script in missing_scripts:
            print(f"  - {script}")
        sys.exit(1)
    
    # Run each test script
    results = []
    for script in test_scripts:
        returncode, stdout, stderr, duration = run_test(script)
        results.append((script, returncode, stdout, stderr, duration))
    
    # Print summary
    print_section("TEST RESULTS SUMMARY")
    
    all_passed = True
    for script, returncode, stdout, stderr, duration in results:
        status = "✅ PASSED" if returncode == 0 else "❌ FAILED"
        if returncode != 0:
            all_passed = False
        print(f"{status} - {script} (Completed in {duration:.2f}s)")
    
    # Print detailed results
    print_section("DETAILED TEST RESULTS")
    
    for script, returncode, stdout, stderr, duration in results:
        print(f"\nResults for {script}:")
        print(f"Return Code: {returncode}")
        print(f"Duration: {duration:.2f}s")
        
        if stdout:
            print("\nStandard Output:")
            # Print only the first 20 lines and last 20 lines if output is too long
            stdout_lines = stdout.splitlines()
            if len(stdout_lines) > 40:
                print("\n".join(stdout_lines[:20]))
                print(f"\n... (truncated {len(stdout_lines) - 40} lines) ...\n")
                print("\n".join(stdout_lines[-20:]))
            else:
                print(stdout)
        
        if stderr:
            print("\nStandard Error:")
            print(stderr)
    
    # Final result
    print_section("FINAL RESULT")
    if all_passed:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()