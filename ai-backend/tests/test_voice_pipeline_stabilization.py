import time
import pytest
import logging
from config import VOICE_CONFIG
from voice.stt import VoiceInputManager
from voice.metrics import VOICE_METRICS, request_context, RequestMetrics, log_accepted_request
from services.ollama_service import OllamaClient, OllamaConnectionError
import httpx

logging.basicConfig(level=logging.INFO)

# Mock Whisper model output
class MockWhisperModel:
    def __init__(self, text, avg_logprob, no_speech_prob):
        self.text = text
        self.avg_logprob = avg_logprob
        self.no_speech_prob = no_speech_prob

    def transcribe(self, audio_file, **kwargs):
        return {
            "text": self.text,
            "segments": [
                {
                    "avg_logprob": self.avg_logprob,
                    "no_speech_prob": self.no_speech_prob,
                    "compression_ratio": 1.2
                }
            ]
        }


def test_transcript_validation_intent_override():
    """Verify that valid commands with poor speech probability are still accepted via intent-override."""
    vm = VoiceInputManager(model_name="tiny")
    
    # 1. "mute volume" has a known intent (volume_control) - should be accepted despite high silence probability (exceeds max_no_speech = 0.85)
    vm._model = MockWhisperModel("mute volume", -0.2, 0.95)
    res = vm.transcribe_audio("dummy.wav", req_id="test_override_1")
    assert res == "mute volume"
    assert request_context.metrics.validation_reason == ""
    assert "Accepted despite" in request_context.metrics.acceptance_reason

    # 2. "Open Telegram" has a known app name - should be accepted despite poor logprob (below min_logprob = -1.5)
    vm._model = MockWhisperModel("Open Telegram", -1.8, 0.1)
    res = vm.transcribe_audio("dummy.wav", req_id="test_override_2")
    assert res.lower() == "open telegram"
    assert "Accepted despite" in request_context.metrics.acceptance_reason

    # 3. Unrecognized garbage query with high silence probability should be rejected
    vm._model = MockWhisperModel("some random noise here", -0.2, 0.90)
    res = vm.transcribe_audio("dummy.wav", req_id="test_override_3")
    assert res is None
    assert "exceeds threshold" in request_context.metrics.validation_reason


def test_transcript_validation_hallucination_rejection():
    """Verify that pure hallucinations or empty transcripts are always rejected."""
    vm = VoiceInputManager(model_name="tiny")

    # 1. Silence hallucination pattern should be rejected
    vm._model = MockWhisperModel("Thank you for watching.", -0.1, 0.2)
    res = vm.transcribe_audio("dummy.wav", req_id="test_halluc_1")
    assert res is None
    assert "hallucinated" in request_context.metrics.validation_reason

    # 2. Empty clean transcript should be rejected
    vm._model = MockWhisperModel("  ", -0.1, 0.2)
    res = vm.transcribe_audio("dummy.wav", req_id="test_halluc_2")
    assert res is None
    assert "Empty transcript" in request_context.metrics.validation_reason


def test_ollama_http_500_retries(monkeypatch):
    """Verify that Ollama connection errors (500, timeouts) are retried correctly."""
    call_count = 0

    def mock_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        response = httpx.Response(500, request=httpx.Request("POST", url))
        raise httpx.HTTPStatusError("Internal Server Error", request=response.request, response=response)

    # We mock httpx.stream to check retry count
    original_stream = httpx.stream
    class MockStreamContext:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            mock_post("http://localhost:11434/api/chat")
        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    monkeypatch.setattr(httpx, "stream", MockStreamContext)
    
    client = OllamaClient()
    
    # Enable quick retries via config mapping
    VOICE_CONFIG["retry_delay"] = 0.05  # speed up tests
    
    with pytest.raises(Exception) as excinfo:
        client.send_message("hello")
        
    # Check that it raised the mapped exception and call count is 3
    assert call_count == 3
    VOICE_CONFIG["retry_delay"] = 0.25


def test_diagnostics_mode(capsys):
    """Verify that diagnostics output prints correct blocks when enabled."""
    VOICE_CONFIG["diagnostics"] = True
    
    vm = VoiceInputManager(model_name="tiny")
    vm._model = MockWhisperModel("Take screenshot", -0.1, 0.1)
    
    vm.transcribe_audio("dummy.wav", req_id="test_diag")
    
    # Manually trigger logging as in full pipeline flow
    log_accepted_request(request_context.metrics)
    
    captured = capsys.readouterr()
    
    assert "VOICE DIAGNOSTICS" in captured.out
    assert "Transcript:          Take screenshot" in captured.out
    assert "Whisper latency:" in captured.out

    # Disable diagnostics again
    VOICE_CONFIG["diagnostics"] = False


def test_rolling_statistics():
    """Verify rolling statistics counter updates and resets size."""
    VOICE_METRICS.commands = []
    VOICE_METRICS.command_counter = 0
    
    # Add 105 commands
    for i in range(105):
        VOICE_METRICS.add_command(
            accepted=(i % 2 == 0),
            transcription_time=0.1,
            synthesis_time=0.2,
            execution_time=0.05,
            total_latency=0.35
        )
        
    assert len(VOICE_METRICS.commands) == 100
    assert VOICE_METRICS.command_counter == 105
