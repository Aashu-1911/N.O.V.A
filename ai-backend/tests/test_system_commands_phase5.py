"""
Phase 5 Task 5.3: Manual test checkpoint for system commands
Tests system commands through command_executor_v2
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.command_executor import execute_command


def test_command(command_text):
    """Test a command and print results"""
    print(f"\n{'='*60}")
    print(f"Testing: {command_text}")
    print(f"{'='*60}")
    
    try:
        result = execute_command(command_text)
        print(f"Status: {result.get('status')}")
        print(f"Reply: {result.get('reply')}")
        print(f"Intent: {result.get('intent')}")
        if result.get('payload'):
            print(f"Payload: {result.get('payload')}")
        
        # Check if successful
        if result.get('status') == 'success':
            print("✓ PASSED")
            return True
        else:
            print("✗ FAILED")
            return False
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all system command tests"""
    print("\n" + "="*60)
    print("PHASE 5 TASK 5.3: SYSTEM COMMANDS MANUAL TEST")
    print("="*60)
    
    # Test commands as specified in task 5.3
    test_commands = [
        "Lock screen",
        "Take screenshot",
        "Mute",
        "Unmute",
        "Volume up"
    ]
    
    results = []
    for command in test_commands:
        passed = test_command(command)
        results.append((command, passed))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for command, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{command:25} {status}")
    
    print(f"\nTotal: {passed_count}/{total_count} passed")
    
    if passed_count == total_count:
        print("\n✓ ALL TESTS PASSED - PHASE 5.3 COMPLETE")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - STOP AND FIX BEFORE CONTINUING")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
