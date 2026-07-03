"""
Direct test of task handler functions in command_executor_v2.py
Tests handlers directly with correct entities to verify implementation.
"""

import sys
sys.path.insert(0, r"c:\Users\ashis\OneDrive\Desktop\Projects\Assistant\ai-backend")

from core.command_executor_v2 import (
    handle_add_task,
    handle_show_tasks,
    handle_complete_task,
    handle_show_stats
)

def test_handle_add_task_direct():
    print("\n=== Testing handle_add_task directly ===")
    entities = {
        "task_name": "Test implementation task",
        "date": None,
        "category": None,
        "priority": "high"
    }
    response = handle_add_task(entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload keys: {response.get('payload', {}).keys()}")
    
    assert response['status'] == 'success', "Add task should succeed"
    assert 'Test implementation task' in response['reply']
    assert response['payload']['task_name'] == 'Test implementation task'
    print("✓ Direct handle_add_task test passed")

def test_handle_show_tasks_direct():
    print("\n=== Testing handle_show_tasks directly ===")
    entities = {"include_completed": False}
    response = handle_show_tasks(entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Tasks count: {len(response.get('payload', {}).get('tasks', []))}")
    
    assert response['status'] == 'success', "Show tasks should succeed"
    assert 'tasks' in response.get('payload', {})
    print("✓ Direct handle_show_tasks test passed")

def test_handle_show_stats_direct():
    print("\n=== Testing handle_show_stats directly ===")
    entities = {}
    response = handle_show_stats(entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Stats: {response.get('payload', {})}")
    
    assert response['status'] == 'success', "Show stats should succeed"
    assert 'pending' in response['payload']
    assert 'completed' in response['payload']
    assert 'pending' in response['reply'].lower()
    print("✓ Direct handle_show_stats test passed")

def test_handle_complete_task_direct():
    print("\n=== Testing handle_complete_task directly ===")
    # First add a task
    add_entities = {"task_name": "Task to be completed"}
    add_response = handle_add_task(add_entities)
    assert add_response['status'] == 'success'
    task_id = add_response['payload']['id']
    print(f"Added task with ID: {task_id}")
    
    # Now complete it using the exact task name
    complete_entities = {"task_name": "Task to be completed"}
    response = handle_complete_task(complete_entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    
    assert response['status'] == 'success', "Complete task should succeed"
    assert response['payload']['completed'] == True
    print("✓ Direct handle_complete_task test passed")

def test_error_handling():
    print("\n=== Testing error handling ===")
    
    # Test add_task without task_name
    response = handle_add_task({})
    print(f"Add without task_name - Status: {response['status']}")
    assert response['status'] == 'error'
    
    # Test complete_task without task identifier
    response = handle_complete_task({})
    print(f"Complete without identifier - Status: {response['status']}")
    assert response['status'] == 'error'
    
    # Test complete_task with non-existent task
    response = handle_complete_task({"task_name": "nonexistent_task_xyz123"})
    print(f"Complete non-existent - Status: {response['status']}")
    assert response['status'] == 'error'
    
    print("✓ Error handling tests passed")

if __name__ == "__main__":
    try:
        test_handle_add_task_direct()
        test_handle_show_tasks_direct()
        test_handle_show_stats_direct()
        test_handle_complete_task_direct()
        test_error_handling()
        
        print("\n" + "="*60)
        print("✓ ALL DIRECT HANDLER TESTS PASSED!")
        print("="*60)
        print("\nTask 2.1 Implementation Verified:")
        print("  ✓ handle_add_task() implemented with business logic")
        print("  ✓ handle_show_tasks() implemented")
        print("  ✓ handle_complete_task() implemented")
        print("  ✓ handle_show_stats() implemented")
        print("  ✓ Imports from managers.task_manager working")
        print("  ✓ Returns manual dict format")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
