"""
Phase 3 Testing: Browser Handler Migration
Test browser commands through command_executor_v2

Test commands:
- "Open browser"
- "Open google"
- "Search Google for Python tutorials"
- "Search web for weather"
"""

import sys
sys.path.insert(0, "c:\\Users\\ashis\\OneDrive\\Desktop\\Projects\\Assistant\\ai-backend")

from core.command_executor_v2 import execute_command
from core.intent_parser import parse_intent


def test_browser_commands():
    """Test browser-related commands."""
    print("\n" + "=" * 70)
    print("PHASE 3 TESTING: Browser Handler Migration")
    print("=" * 70)
    
    test_cases = [
        {
            "command": "Open browser",
            "expected_intent": "open_website",
            "expected_status": "success",
            "description": "Opening browser without URL"
        },
        {
            "command": "Open google",
            "expected_intent": "open_website",
            "expected_status": "success",
            "description": "Opening known website (google)"
        },
        {
            "command": "Open youtube",
            "expected_intent": "open_website",
            "expected_status": "success",
            "description": "Opening known website (youtube)"
        },
        {
            "command": "Search Google for Python tutorials",
            "expected_intent": "search_web",
            "expected_status": "success",
            "description": "Web search with explicit 'Google'"
        },
        {
            "command": "Search web for weather",
            "expected_intent": "search_web",
            "expected_status": "success",
            "description": "Web search with 'web' keyword"
        },
        {
            "command": "Search for machine learning",
            "expected_intent": "search_web",
            "expected_status": "success",
            "description": "Web search with 'search for'"
        },
        {
            "command": "Open https://github.com",
            "expected_intent": "open_website",
            "expected_status": "success",
            "description": "Opening URL with protocol"
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"Test {i}: {test_case['description']}")
        print(f"Command: \"{test_case['command']}\"")
        print(f"{'=' * 70}")
        
        try:
            # First, test intent parsing
            print("\n[Intent Parser]")
            parsed = parse_intent(test_case['command'])
            print(f"  Intent: {parsed['intent']}")
            print(f"  Confidence: {parsed['confidence']}")
            print(f"  Entities: {parsed['entities']}")
            
            # Check intent matches
            if parsed['intent'] != test_case['expected_intent']:
                print(f"  ❌ FAILED: Expected intent '{test_case['expected_intent']}', got '{parsed['intent']}'")
                failed += 1
                continue
            
            # Now test command execution
            print("\n[Command Executor]")
            response = execute_command(test_case['command'])
            
            print(f"  Status: {response['status']}")
            print(f"  Reply: {response['reply']}")
            print(f"  Intent: {response.get('intent', 'N/A')}")
            if response.get('payload'):
                print(f"  Payload: {response['payload']}")
            
            # Check status matches
            if response['status'] != test_case['expected_status']:
                print(f"  ❌ FAILED: Expected status '{test_case['expected_status']}', got '{response['status']}'")
                failed += 1
                continue
            
            # Verify response structure
            if 'reply' not in response or not response['reply']:
                print("  ❌ FAILED: Missing or empty reply field")
                failed += 1
                continue
            
            print("  ✅ PASSED")
            passed += 1
            
        except Exception as e:
            print(f"  ❌ FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 3 TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(test_cases)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Browser Handler Migration Complete!")
        print("=" * 70)
        print("\nVerified functionality:")
        print("  ✅ Open browser (default to Google)")
        print("  ✅ Open known websites (google, youtube)")
        print("  ✅ Open URLs with protocol")
        print("  ✅ Web search with various patterns")
        print("  ✅ Response dict structure (status, reply, payload)")
        print("\n" + "=" * 70)
        print("READY TO PROCEED TO PHASE 4: App Handler Migration")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Manual voice test: 'Open browser'")
        print("  2. Manual voice test: 'Search Google for Python tutorials'")
        print("  3. Manual API test: POST /execute {\"message\": \"Search web for weather\"}")
        print("  4. If all manual tests pass, proceed to Phase 4")
    else:
        print("\n⚠️  STOP: Fix failures before proceeding to Phase 4")
    
    return failed == 0


if __name__ == "__main__":
    success = test_browser_commands()
    sys.exit(0 if success else 1)
