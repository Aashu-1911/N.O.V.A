"""
Phase 5 Test: System Handler Integration Tests

Tests for system handler functions in command_executor_v2:
- handle_lock_pc
- handle_screenshot
- handle_volume_control (mute/unmute/up/down)
"""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.command_executor_v2 import execute_command


def test_lock_pc():
    """Test lock PC command - NOTE: This will actually lock your PC!"""
    print("\n" + "=" * 60)
    print("TEST: Lock PC")
    print("=" * 60)
    print("WARNING: This test is commented out to prevent accidental PC lock")
    print("Uncomment the test code if you want to test it")
    
    # Uncomment to test (will lock your PC):
    # result = execute_command("lock screen")
    # print(f"Status: {result['status']}")
    # print(f"Reply: {result['reply']}")
    # print(f"Intent: {result.get('intent', 'unknown')}")
    # assert result["status"] == "success", "Lock PC failed"
    print("SKIPPED (to prevent accidental lock)")


def test_screenshot():
    """Test screenshot command"""
    print("\n" + "=" * 60)
    print("TEST: Take Screenshot")
    print("=" * 60)
    
    result = execute_command("take screenshot")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'unknown')}")
    
    if result["status"] == "success":
        filepath = result.get("payload", {}).get("filepath")
        print(f"Screenshot saved to: {filepath}")
        assert filepath is not None, "Screenshot filepath should be returned"
        assert Path(filepath).exists(), f"Screenshot file should exist at {filepath}"
    else:
        print(f"Error: {result.get('payload', {}).get('error', 'Unknown error')}")
    
    assert result["status"] == "success", "Screenshot failed"


def test_volume_mute():
    """Test volume mute command"""
    print("\n" + "=" * 60)
    print("TEST: Volume Mute")
    print("=" * 60)
    
    result = execute_command("mute")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'unknown')}")
    print(f"Action: {result.get('payload', {}).get('action', 'N/A')}")
    
    assert result["status"] == "success", "Volume mute failed"
    assert "mute" in result["reply"].lower(), "Reply should mention mute"


def test_volume_unmute():
    """Test volume unmute command"""
    print("\n" + "=" * 60)
    print("TEST: Volume Unmute")
    print("=" * 60)
    
    result = execute_command("unmute")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'unknown')}")
    print(f"Action: {result.get('payload', {}).get('action', 'N/A')}")
    
    assert result["status"] == "success", "Volume unmute failed"
    assert "unmute" in result["reply"].lower(), "Reply should mention unmute"


def test_volume_up():
    """Test volume up command"""
    print("\n" + "=" * 60)
    print("TEST: Volume Up")
    print("=" * 60)
    
    result = execute_command("volume up")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'unknown')}")
    print(f"Action: {result.get('payload', {}).get('action', 'N/A')}")
    
    assert result["status"] == "success", "Volume up failed"
    assert "increase" in result["reply"].lower() or "up" in result["reply"].lower(), "Reply should mention volume increase"


def test_volume_down():
    """Test volume down command"""
    print("\n" + "=" * 60)
    print("TEST: Volume Down")
    print("=" * 60)
    
    result = execute_command("volume down")
    print(f"Status: {result['status']}")
    print(f"Reply: {result['reply']}")
    print(f"Intent: {result.get('intent', 'unknown')}")
    print(f"Action: {result.get('payload', {}).get('action', 'N/A')}")
    
    assert result["status"] == "success", "Volume down failed"
    assert "decrease" in result["reply"].lower() or "down" in result["reply"].lower(), "Reply should mention volume decrease"


def main():
    """Run all Phase 5 system handler tests"""
    print("\n" + "=" * 60)
    print("PHASE 5 TEST SUITE: System Handler Migration")
    print("=" * 60)
    
    tests = [
        test_lock_pc,
        test_screenshot,
        test_volume_mute,
        test_volume_unmute,
        test_volume_up,
        test_volume_down,
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test in tests:
        try:
            test()
            if "lock_pc" in test.__name__:
                skipped += 1
            else:
                passed += 1
        except AssertionError as e:
            print(f"\n❌ FAILED: {test.__name__}")
            print(f"   Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR in {test.__name__}: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped} (lock_pc test - uncomment to run)")
    print(f"Total: {len(tests)}")
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
