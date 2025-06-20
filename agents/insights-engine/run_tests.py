#!/usr/bin/env python3
"""
Test Runner for Insights Engine Agent
Runs comprehensive test suite including unit and integration tests
"""

import subprocess
import sys
import os
from pathlib import Path

def get_venv_python():
    """Get the virtual environment Python path"""
    project_root = Path(__file__).parent.parent.parent
    venv_python = project_root / "project_venv" / "bin" / "python"
    
    if not venv_python.exists():
        print("❌ Virtual environment not found. Expected at:", venv_python)
        print("Make sure you're running from the correct directory.")
        return None
    
    return str(venv_python)

def run_test_suite(test_file, suite_name):
    """Run a specific test suite"""
    python_path = get_venv_python()
    if not python_path:
        return False
    
    print(f"\n🚀 Running {suite_name}")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            [python_path, test_file],
            cwd=Path(__file__).parent,
            capture_output=False,  # Show output in real time
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {suite_name}: {e}")
        return False

def main():
    """Main test runner"""
    print("🧪 Insights Engine Agent - Comprehensive Test Suite")
    print("=" * 60)
    print("This will run all utility and integration tests for the insights-engine.\n")
    
    # Change to insights-engine directory
    os.chdir(Path(__file__).parent)
    
    # Track results
    results = {}
    
    # Run utility tests
    print("📋 Test Plan:")
    print("1. Unit tests for statistical utilities")
    print("2. Unit tests for data processing utilities")
    print("3. Unit tests for recommendation builder utilities")
    print("4. Unit tests for BigQuery operations utilities")
    print("5. Integration tests for complete agent workflow")
    print("6. End-to-end pipeline validation")
    
    # Run utility tests
    results['utilities'] = run_test_suite('test_utils.py', 'Utility Tests (Statistical, Data Processing, Recommendation Builder, BigQuery Ops)')
    
    # Run integration tests
    results['integration'] = run_test_suite('test_integration.py', 'Integration Tests (Full Agent Workflow)')
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    total_suites = len(results)
    passed_suites = sum(1 for passed in results.values() if passed)
    
    for suite_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{suite_name.capitalize()} Tests: {status}")
    
    print(f"\nOverall Results: {passed_suites}/{total_suites} test suites passed")
    
    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED! The insights-engine is ready for deployment.")
        print("\nNext steps:")
        print("- Implement REST API endpoints")
        print("- Test with real data from other agents")
        print("- Run linting and validation checks")
        return True
    else:
        print(f"\n❌ {total_suites - passed_suites} test suite(s) failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)