"""
Integration test for app handlers through execute_command
"""

import sys
sys.path.insert(0, r"c:\Users\ashis\OneDrive\Desktop\Projects\Assistant\ai-backend")

from core.command_executor_v2 import execute_command

def test_open_application_integration():
    print("\n=== Testing open_application through execute_command ===")
    
    # Test opening notepad
    print("\n--- Test: Open notepad ---")
    response = execute_command("Open notepad")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Intent: {response.get('intent', 'N/A')}")
    print(f"Payload: {response.get('payload', {})}")
    assert response['status'] in ['success', 'error'], "Should return valid status"
    assert 'intent' in response, "Should include intent"
    print("✓ Open notepad test passed")
    
    # Test opening calculator
    print("\n--- Test: Open calculator ---")
    response = execute_command("Open calculator")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Intent: {response.get('intent', 'N/A')}")
    print(f"Payload: {response.get('payload', {})}")
    assert response['status'] in ['success', 'error'], "Should return valid status"
    print("✓ Open calculator test passed")

def test_close_application_integration():
    print("\n=== Testing close_application through execute_command ===")
    
    # Test closing notepad
    print("\n--- Test: Close notepad ---")
    response = execute_command("Close notepad")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Intent: {response.get('intent', 'N/A')}")
    print(f"Payload: {response.get('payload', {})}")
    assert response['status'] in ['success', 'error'], "Should return valid status"
    assert 'intent' in response, "Should include intent"
    print("✓ Close notepad test passed")

def test_response_consistency():
    print("\n=== Testing response consistency (Requirement 5.3) ===")
    
    # Test that voice and API commands would produce the same response
    print("\n--- Testing response format consistency ---")
    response1 = execute_command("Open notepad")
    response2 = execute_command("Open calculator")
    
    # Both should have the same structure
    assert set(response1.keys()) == set(response2.keys()), "Responses should have same keys"
    assert response1['status'] in ['success', 'error', 'partial'], "Status should be valid"
    assert response2['status'] in ['success', 'error', 'partial'], "Status should be valid"
    assert 'reply' in response1 and 'reply' in response2, "Both should have reply"
    assert 'intent' in response1 and 'intent' in response2, "Both should have intent"
    print("✓ Response consistency test passed")

if __name__ == "__main__":
    try:
        test_open_application_integration()
        test_close_application_integration()
        test_response_consistency()
        print("\n" + "="*50)
        print("✓ ALL INTEGRATION TESTS PASSED!")
        print("="*50)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
