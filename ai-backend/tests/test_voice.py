from __future__ import annotations

import os
import tempfile
import wave

from voice import VoiceInputManager


class DummyModel:
    def transcribe(self, audio_file, language="en"):
        return {"text": "  add a task to buy milk tomorrow  "}


def _make_silent_wav(path: str, samplerate: int = 16000, seconds: float = 0.25) -> None:
    frame_count = int(samplerate * seconds)
    silence = b"\x00\x00" * frame_count
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(samplerate)
        wav_file.writeframes(silence)


if __name__ == "__main__":
    manager = VoiceInputManager()
    manager._model = DummyModel()  # type: ignore[attr-defined]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_path = temp_file.name

    try:
        _make_silent_wav(temp_path)
        text = manager.transcribe_audio(temp_path)
        assert text == "add a task to buy milk tomorrow", text
        print("VOICE_TEST_OK")
        print(text)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
