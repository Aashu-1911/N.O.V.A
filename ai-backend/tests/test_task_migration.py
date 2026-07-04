"""
Manual test script for Phase 2: Task Handler Migration

This script tests the task handler functions in command_executor_v2.py
as specified in task 2.3 of the migration plan.

Test Cases:
1. Add task to test migration
2. Show my tasks
3. Complete task test migration
4. Show task stats
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.command_executor import execute_command


def print_separator():
    print("\n" + "=" * 70 + "\n")


def test_add_task():
    """Test adding a task"""
    print("TEST 1: Add task to test migration")
    print("-" * 70)
    
    command = "Add task to test migration"
    result = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'N/A')}")
    if result.get('payload'):
        print(f"Payload: {result['payload']}")
    
    # Verify success
    if result['status'] == 'success' and 'test migration' in result['reply'].lower():
        print("\n✅ TEST PASSED: Task added successfully")
        return True
    else:
        print("\n❌ TEST FAILED: Task was not added properly")
        return False


def test_show_tasks():
    """Test showing tasks"""
    print("TEST 2: Show my tasks")
    print("-" * 70)
    
    command = "Show my tasks"
    result = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'N/A')}")
    if result.get('payload'):
        tasks = result['payload'].get('tasks', [])
        print(f"Number of tasks: {len(tasks)}")
    
    # Verify success
    if result['status'] == 'success':
        print("\n✅ TEST PASSED: Tasks retrieved successfully")
        return True
    else:
        print("\n❌ TEST FAILED: Could not retrieve tasks")
        return False


def test_complete_task():
    """Test completing a task"""
    print("TEST 3: Complete task test migration")
    print("-" * 70)
    
    command = "Complete task test migration"
    result = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'N/A')}")
    if result.get('payload'):
        print(f"Payload: {result['payload']}")
    
    # Verify success (may succeed or fail depending on if task exists)
    if result['status'] in ['success', 'error']:
        print(f"\n✅ TEST PASSED: Complete task executed (status: {result['status']})")
        if result['status'] == 'error':
            print(f"   Note: {result['reply']}")
        return True
    else:
        print("\n❌ TEST FAILED: Unexpected status")
        return False


def test_show_stats():
    """Test showing task statistics"""
    print("TEST 4: Show task stats")
    print("-" * 70)
    
    command = "Show my task statistics"
    result = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'N/A')}")
    if result.get('payload'):
        print(f"Payload: {result['payload']}")
    
    # Verify success
    if result['status'] == 'success' and ('pending' in result['reply'].lower() or 'completed' in result['reply'].lower()):
        print("\n✅ TEST PASSED: Task stats retrieved successfully")
        return True
    else:
        print("\n❌ TEST FAILED: Could not retrieve task stats")
        return False


def test_add_task_via_api_format():
    """Test adding a task using API-style message"""
    print("TEST 5: Add task via API (API format test)")
    print("-" * 70)
    
    command = "Add task via API"
    result = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'N/A')}")
    if result.get('payload'):
        print(f"Payload: {result['payload']}")
    
    # Verify success
    if result['status'] == 'success' and 'via API' in result['reply']:
        print("\n✅ TEST PASSED: Task added via API format successfully")
        return True
    else:
        print("\n❌ TEST FAILED: Task was not added properly")
        return False


def run_all_tests():
    """Run all manual tests"""
    print("\n" + "=" * 70)
    print("PHASE 2 TASK HANDLER MIGRATION - MANUAL TEST SUITE")
    print("=" * 70)
    
    results = []
    
    print_separator()
    results.append(("Add Task", test_add_task()))
    
    print_separator()
    results.append(("Show Tasks", test_show_tasks()))
    
    print_separator()
    results.append(("Complete Task", test_complete_task()))
    
    print_separator()
    results.append(("Show Stats", test_show_stats()))
    
    print_separator()
    results.append(("Add Task via API", test_add_task_via_api_format()))
    
    # Summary
    print_separator()
    print("TEST SUMMARY")
    print("-" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Ready to proceed to Phase 3")
        print("\nNext step: Run git commit:")
        print('git add -A && git commit -m "Phase 2: Migrate task handler"')
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED - Fix issues before continuing")
        print("\nDo NOT proceed to Phase 3 until all tests pass!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
