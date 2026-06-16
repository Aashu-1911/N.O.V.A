from __future__ import annotations

from voice.tts import clean_response_text, split_text_for_tts, TTSManager


class DummyEngine:
    def __init__(self):
        self.spoken = []
        self.stopped = False
        self.props = {}

    def getProperty(self, name):
        if name == "voices":
            return []
        return self.props.get(name)

    def setProperty(self, name, value):
        self.props[name] = value

    def stop(self):
        self.stopped = True

    def say(self, text):
        self.spoken.append(text)

    def runAndWait(self):
        return None


if __name__ == "__main__":
    manager = TTSManager()
    manager._engine = DummyEngine()  # type: ignore[attr-defined]
    manager._ensure_engine = lambda: None  # type: ignore[method-assign]
    manager._has_coqui_available = lambda: False  # type: ignore[method-assign]

    cleaned = clean_response_text("**Done** # task added.")
    chunks = split_text_for_tts("One. Two! This is a longer sentence, with pauses.")

    manager.speak("Hello there")

    assert cleaned == "Done task added.", cleaned
    assert chunks[0] == "One.", chunks
    assert manager._engine.spoken == ["Hello there"], manager._engine.spoken
    print("TTS_TEST_OK")
    print(cleaned)
    print(chunks)