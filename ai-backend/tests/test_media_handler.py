"""
Test media handler functions in command_executor_v2.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.command_executor_v2 import handle_media_control, handle_play_music


def test_play_music():
    """Test playing music with a query."""
    print("\n=== Test: Play Music ===")
    
    entities = {
        "media_action": "play",
        "media_query": "Bohemian Rhapsody"
    }
    
    response = handle_media_control(entities)
    
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload: {response.get('payload', {})}")
    
    assert response["status"] == "success", f"Expected success, got {response['status']}"
    assert "Playing" in response["reply"], f"Expected 'Playing' in reply, got {response['reply']}"
    assert response["payload"]["action"] == "play"
    assert response["payload"]["query"] == "Bohemian Rhapsody"
    
    print("✓ Test passed")


def test_pause():
    """Test pausing media."""
    print("\n=== Test: Pause Media ===")
    
    entities = {
        "media_action": "pause"
    }
    
    response = handle_media_control(entities)
    
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload: {response.get('payload', {})}")
    
    assert response["status"] == "success"
    assert "paused" in response["reply"].lower()
    assert response["payload"]["action"] == "pause"
    
    print("✓ Test passed")


def test_next_track():
    """Test next track."""
    print("\n=== Test: Next Track ===")
    
    entities = {
        "media_action": "next"
    }
    
    response = handle_media_control(entities)
    
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload: {response.get('payload', {})}")
    
    assert response["status"] == "success"
    assert "next" in response["reply"].lower()
    assert response["payload"]["action"] == "next"
    
    print("✓ Test passed")


def test_previous_track():
    """Test previous track."""
    print("\n=== Test: Previous Track ===")
    
    entities = {
        "media_action": "previous"
    }
    
    response = handle_media_control(entities)
    
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload: {response.get('payload', {})}")
    
    assert response["status"] == "success"
    assert "previous" in response["reply"].lower()
    assert response["payload"]["action"] == "previous"
    
    print("✓ Test passed")


def test_resume():
    """Test resume media."""
    print("\n=== Test: Resume Media ===")
    
    entities = {
        "media_action": "resume"
    }
    
    response = handle_media_control(entities)
    
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload: {response.get('payload', {})}")
    
    assert response["status"] == "success"
    assert "resumed" in response["reply"].lower()
    assert response["payload"]["action"] == "resume"
    
    print("✓ Test passed")


def test_play_music_alias():
    """Test handle_play_music alias function."""
    print("\n=== Test: Play Music Alias ===")
    
    entities = {
        "media_query": "Shape of You"
    }
    
    response = handle_play_music(entities)
    
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    print(f"Payload: {response.get('payload', {})}")
    
    assert response["status"] == "success"
    assert "Playing" in response["reply"]
    assert response["payload"]["action"] == "play"
    assert response["payload"]["query"] == "Shape of You"
    
    print("✓ Test passed")


def test_missing_action():
    """Test error handling when action is missing."""
    print("\n=== Test: Missing Action ===")
    
    entities = {}
    
    response = handle_media_control(entities)
    
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    
    assert response["status"] == "error"
    assert "couldn't determine" in response["reply"].lower()
    
    print("✓ Test passed")


def test_play_without_query():
    """Test error handling when playing without query."""
    print("\n=== Test: Play Without Query ===")
    
    entities = {
        "media_action": "play"
    }
    
    response = handle_media_control(entities)
    
    print(f"Status: {response['status']}")
    print(f"Reply: {response['reply']}")
    
    assert response["status"] == "error"
    assert "specify what you want to play" in response["reply"].lower()
    
    print("✓ Test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Media Handler Tests - Phase 6")
    print("=" * 60)
    
    try:
        test_play_music()
        test_pause()
        test_next_track()
        test_previous_track()
        test_resume()
        test_play_music_alias()
        test_missing_action()
        test_play_without_query()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
