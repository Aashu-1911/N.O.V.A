"""
Integration test for media commands through execute_command
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.command_executor import execute_command


def test_play_music_command():
    """Test playing music through execute_command."""
    print("\n=== Test: Play Music Command ===")
    
    command = "Play Bohemian Rhapsody"
    response = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Intent: {response.get('intent')}")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload: {response.get('payload', {})}")
    
    assert response["intent"] == "media_control"
    assert response["status"] == "success"
    assert "Playing" in response["reply"]
    
    print("✓ Test passed")


def test_pause_command():
    """Test pause through execute_command."""
    print("\n=== Test: Pause Command ===")
    
    command = "Pause"
    response = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Intent: {response.get('intent')}")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    
    assert response["intent"] == "media_control"
    assert response["status"] == "success"
    assert "paused" in response["reply"].lower()
    
    print("✓ Test passed")


def test_next_command():
    """Test next track through execute_command."""
    print("\n=== Test: Next Track Command ===")
    
    command = "Next track"
    response = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Intent: {response.get('intent')}")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    
    assert response["intent"] == "media_control"
    assert response["status"] == "success"
    assert "next" in response["reply"].lower()
    
    print("✓ Test passed")


def test_previous_command():
    """Test previous track through execute_command."""
    print("\n=== Test: Previous Track Command ===")
    
    command = "Previous track"
    response = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Intent: {response.get('intent')}")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    
    assert response["intent"] == "media_control"
    assert response["status"] == "success"
    assert "previous" in response["reply"].lower()
    
    print("✓ Test passed")


def test_resume_command():
    """Test resume through execute_command."""
    print("\n=== Test: Resume Command ===")
    
    command = "Resume"
    response = execute_command(command)
    
    print(f"Command: {command}")
    print(f"Intent: {response.get('intent')}")
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    
    assert response["intent"] == "media_control"
    assert response["status"] == "success"
    assert "resumed" in response["reply"].lower()
    
    print("✓ Test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Media Integration Tests - Phase 6")
    print("=" * 60)
    
    try:
        test_play_music_command()
        test_pause_command()
        test_next_command()
        test_previous_command()
        test_resume_command()
        
        print("\n" + "=" * 60)
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
