"""
Test script for task handler functions in command_executor_v2.py
"""

import sys
sys.path.insert(0, r"c:\Users\ashis\OneDrive\Desktop\Projects\Assistant\ai-backend")

from core.command_executor import execute_command

def test_add_task():
    print("\n=== Testing add_task handler ===")
    response = execute_command("Add task to test migration")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Intent: {response['intent']}")
    print(f"Payload: {response.get('payload', {})}")
    assert response['status'] == 'success', "Add task should succeed"
    assert 'test migration' in response['reply'].lower()
    print("✓ Add task test passed")

def test_show_tasks():
    print("\n=== Testing show_tasks handler ===")
    response = execute_command("Show my tasks")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Intent: {response['intent']}")
    tasks = response.get('payload', {}).get('tasks', [])
    print(f"Number of tasks: {len(tasks)}")
    assert response['status'] == 'success', "Show tasks should succeed"
    print("✓ Show tasks test passed")

def test_show_stats():
    print("\n=== Testing show_stats handler ===")
    response = execute_command("Show task statistics")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Intent: {response['intent']}")
    print(f"Payload: {response.get('payload', {})}")
    assert response['status'] == 'success', "Show stats should succeed"
    assert 'pending' in response['reply'].lower()
    assert 'completed' in response['reply'].lower()
    print("✓ Show stats test passed")

def test_complete_task():
    print("\n=== Testing complete_task handler ===")
    # First add a task to complete
    add_response = execute_command("Add task to complete test")
    assert add_response['status'] == 'success'
    
    # Now complete it
    response = execute_command("Complete task to complete test")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Intent: {response['intent']}")
    print(f"Payload: {response.get('payload', {})}")
    assert response['status'] == 'success', "Complete task should succeed"
    print("✓ Complete task test passed")

if __name__ == "__main__":
    try:
        test_add_task()
        test_show_tasks()
        test_show_stats()
        test_complete_task()
        print("\n" + "="*50)
        print("✓ ALL TESTS PASSED!")
        print("="*50)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
