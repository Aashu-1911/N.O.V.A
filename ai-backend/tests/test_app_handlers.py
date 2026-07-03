"""
Test script for app handler functions in command_executor_v2.py
"""

import sys
sys.path.insert(0, r"c:\Users\ashis\OneDrive\Desktop\Projects\Assistant\ai-backend")

from core.command_executor_v2 import handle_open_application, handle_close_application

def test_open_application():
    print("\n=== Testing handle_open_application ===")
    
    # Test with valid app name
    print("\n--- Test 1: Valid app name (notepad) ---")
    entities = {"app_name": "notepad"}
    response = handle_open_application(entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload: {response.get('payload', {})}")
    assert response['status'] in ['success', 'error'], "Should return valid status"
    assert 'notepad' in response['reply'].lower()
    print("✓ Test 1 passed")
    
    # Test with missing app name
    print("\n--- Test 2: Missing app name ---")
    entities = {}
    response = handle_open_application(entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    assert response['status'] == 'error', "Should return error for missing app name"
    assert 'could not determine' in response['reply'].lower() or "couldn't determine" in response['reply'].lower()
    print("✓ Test 2 passed")
    
    # Test with invalid app name
    print("\n--- Test 3: Invalid app name ---")
    entities = {"app_name": "nonexistentapp12345"}
    response = handle_open_application(entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    assert response['status'] in ['success', 'error'], "Should return valid status"
    print("✓ Test 3 passed")

def test_close_application():
    print("\n=== Testing handle_close_application ===")
    
    # Test with known app
    print("\n--- Test 1: Known app (notepad) ---")
    entities = {"app_name": "notepad"}
    response = handle_close_application(entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload: {response.get('payload', {})}")
    assert response['status'] in ['success', 'error'], "Should return valid status"
    assert 'notepad' in response['reply'].lower()
    print("✓ Test 1 passed")
    
    # Test with missing app name
    print("\n--- Test 2: Missing app name ---")
    entities = {}
    response = handle_close_application(entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    assert response['status'] == 'error', "Should return error for missing app name"
    assert 'could not determine' in response['reply'].lower() or "couldn't determine" in response['reply'].lower()
    print("✓ Test 2 passed")
    
    # Test with unknown app
    print("\n--- Test 3: Unknown app ---")
    entities = {"app_name": "unknownapp"}
    response = handle_close_application(entities)
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    assert response['status'] in ['success', 'error'], "Should return valid status"
    print("✓ Test 3 passed")

def test_response_format():
    print("\n=== Testing response format compliance (Requirements 5.2, 5.3) ===")
    
    # Test that both handlers return dict with required keys
    entities = {"app_name": "test"}
    
    print("\n--- Testing open_application response format ---")
    response = handle_open_application(entities)
    assert isinstance(response, dict), "Response should be a dict"
    assert 'status' in response, "Response should have 'status' key"
    assert 'reply' in response, "Response should have 'reply' key"
    assert 'payload' in response, "Response should have 'payload' key"
    assert response['status'] in ['success', 'error', 'partial'], "Status should be valid"
    print(f"✓ Response format valid: {list(response.keys())}")
    
    print("\n--- Testing close_application response format ---")
    response = handle_close_application(entities)
    assert isinstance(response, dict), "Response should be a dict"
    assert 'status' in response, "Response should have 'status' key"
    assert 'reply' in response, "Response should have 'reply' key"
    assert 'payload' in response, "Response should have 'payload' key"
    assert response['status'] in ['success', 'error', 'partial'], "Status should be valid"
    print(f"✓ Response format valid: {list(response.keys())}")

if __name__ == "__main__":
    try:
        test_open_application()
        test_close_application()
        test_response_format()
        print("\n" + "="*50)
        print("✓ ALL APP HANDLER TESTS PASSED!")
        print("="*50)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
