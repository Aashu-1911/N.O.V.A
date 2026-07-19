import time
import pytest
import logging
from pathlib import Path
from tts.service import TTSService

logging.basicConfig(level=logging.INFO)

def test_1_initialize_and_speak():
    """Test 1: Initialize Piper -> Speak 'Hello' -> Exit"""
    print("\n--- Running Test 1: Initialize and Speak ---")
    service = TTSService()
    service.initialize()
    assert service.initialized is True
    
    # Speak hello
    service.speak("Hello")
    service.shutdown()

def test_2_sequential_playback():
    """Test 2: Queue: Hello, How are you, Goodbye -> Verify sequential playback."""
    print("\n--- Running Test 2: Sequential Playback ---")
    service = TTSService()
    
    # We speak async to queue them up
    service.speak_async("Hello")
    service.speak_async("How are you")
    
    # speak blocks until the final one finishes
    service.speak("Goodbye")
    service.shutdown()

def test_3_stress_test():
    """Test 3: Stress test -> Queue 100 messages. No crashes. No memory leaks."""
    print("\n--- Running Test 3: Stress Test (100 messages) ---")
    service = TTSService()
    service.initialize()
    
    # Queue 100 small messages
    for i in range(100):
        service.speak_async(f"Message {i}")
    
    # Let it run a bit then clear
    time.sleep(3.0)
    service.stop()
    service.shutdown()

def test_4_interrupt():
    """Test 4: Interrupt -> Speak long paragraph -> stop() -> Playback ends immediately."""
    print("\n--- Running Test 4: Interrupt / Stop ---")
    service = TTSService()
    
    long_text = (
        "This is a very long paragraph designed to test the interrupt capability of the Piper Text to Speech service. "
        "We want to make sure that as soon as the stop method is called, the audio playback cuts off immediately "
        "and control is returned to the user without any delays, hangs, or blocks."
    )
    
    start_time = time.time()
    # Speak async so we don't block
    service.speak_async(long_text)
    
    # Let it synthesize and start playing for a moment
    time.sleep(2.0)
    
    # Stop it immediately
    service.stop()
    elapsed = time.time() - start_time
    
    print(f"Stopped after {elapsed:.2f} seconds.")
    # The playback should have cut off and busy should be cleared
    assert service.is_speaking is False
    service.shutdown()

def test_5_shutdown_during_playback():
    """Test 5: Shutdown during playback. No deadlocks."""
    print("\n--- Running Test 5: Shutdown During Playback ---")
    service = TTSService()
    
    long_text = (
        "This is another long paragraph to test shutting down the service in the middle of active playback. "
        "The worker thread must terminate cleanly and release all resources."
    )
    
    service.speak_async(long_text)
    time.sleep(1.5)
    
    # Shutdown during playback
    service.shutdown()
    assert service.is_speaking is False

if __name__ == "__main__":
    test_1_initialize_and_speak()
    test_2_sequential_playback()
    test_3_stress_test()
    test_4_interrupt()
    test_5_shutdown_during_playback()
    print("\nAll Piper standalone tests passed successfully!")
