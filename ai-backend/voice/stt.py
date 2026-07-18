"""Voice input (STT) module for Jarvis — Phase 2.

Features:
- Capture microphone audio into temporary WAV files
- Stop recording after speech ends and silence is detected
- Transcribe audio with local Whisper (base or small by default)
- Notify registered callbacks when a command is recognized

Wake words and TTS are intentionally left for a later phase.

Notes: This module prefers `whisper` (openai-whisper), `sounddevice`,
`numpy`, `soundfile`, and optionally `webrtcvad` for better speech detection.
If `soundfile` is missing, the stdlib `wave` writer is used instead.
"""
from __future__ import annotations

import os
import queue
import threading
import time
import tempfile
import traceback
import contextlib
from pathlib import Path
from typing import Callable, List, Optional
import re

try:
    import sounddevice as sd
    import numpy as np
except Exception:  # pragma: no cover - import-time guard
    sd = None  # type: ignore
    np = None  # type: ignore

try:
    import soundfile as sf
except Exception:  # pragma: no cover
    sf = None  # type: ignore

try:
    import whisper
except Exception:  # pragma: no cover
    whisper = None  # type: ignore

import wave
try:
    import webrtcvad
except Exception:  # pragma: no cover
    webrtcvad = None  # type: ignore


def _ensure_audio_deps():
    if sd is None or np is None:
        raise RuntimeError("sounddevice and numpy are required for audio capture")


def _write_wav(path: str, data: "np.ndarray", samplerate: int = 16000):
    """Write float32 numpy array as 16-bit WAV if soundfile unavailable."""
    if sf is not None:
        sf.write(path, data, samplerate)
        return

    # Fallback to wave module (mono)
    data16 = (data * 32767).astype("int16")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(data16.tobytes())


class VoiceInputManager:
    """Manage wake-word detection and command capture.

    Call `on_command(callback)` to register callbacks that receive the
    transcribed text. Callbacks are invoked with a single string argument.
    """

    def __init__(
        self,
        model_name: str = "small",
        samplerate: int = 16000,
        channels: int = 1,
        wake_words: Optional[List[str]] = None,
    ) -> None:
        self.model_name = model_name
        self.samplerate = samplerate
        self.channels = channels
        # Reserved for a later phase; not used in Phase 2 listening flow.
        self.wake_words = wake_words or ["hey jarvis", "jarvis", "ok jarvis"]

        self._model = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callbacks: List[Callable[[str], None]] = []
        self._listening = False
        self._request_counter = 0

        # Internal queue used by background thread for events.
        self._q: "queue.Queue[tuple[str, Optional[str]]]" = queue.Queue()

    @property
    def is_listening(self) -> bool:
        return self._listening

    def on_command(self, callback: Callable[[str], None]) -> None:
        self._callbacks.append(callback)

    def get_events(self) -> List[tuple[str, Optional[str]]]:
        """Drain and return queued voice events.

        Events are tuples of (event_type, payload) such as:
        - ("command", transcribed_text)
        - ("error", error_message)
        """
        events: List[tuple[str, Optional[str]]] = []
        while True:
            try:
                events.append(self._q.get_nowait())
            except queue.Empty:
                break
        return events

    def _load_model(self):
        if whisper is None:
            raise RuntimeError("Whisper is not installed. Install `openai-whisper`.")
        if self._model is None:
            # model load can be IO and CPU heavy
            self._model = whisper.load_model(self.model_name)

    def start_listening(self, background: bool = True) -> None:
        _ensure_audio_deps()
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._listening = True
        print("[VOICE] Listening thread started")

        def run_loop():
            try:
                self._load_model()
            except Exception as exc:
                self._q.put(("error", str(exc)))
                self._listening = False
                return

            while not self._stop_event.is_set():
                try:
                    self._request_counter += 1
                    req_id = f"{self._request_counter:02d}"
                    audio_path = self._record_until_silence(silence_duration=2.0, max_duration=30.0, req_id=req_id)
                    try:
                        cmd_text = self.transcribe_audio(audio_path, req_id=req_id)
                    finally:
                        with contextlib.suppress(Exception):
                            Path(audio_path).unlink(missing_ok=True)

                    if cmd_text:
                        self._q.put(("command", cmd_text))
                        for cb in list(self._callbacks):
                            try:
                                print("[VOICE] Calling callback...")
                                cb(cmd_text)
                                print("[VOICE] Callback finished.")
                            except Exception:
                                traceback.print_exc()
                        # Settling delay to prevent echo/TTS feedback from contaminating next recording
                        time.sleep(0.5)
                except Exception:
                    traceback.print_exc()
                    time.sleep(0.5)

            self._listening = False

        self._thread = threading.Thread(target=run_loop, daemon=True)
        if background:
            self._thread.start()
        else:
            run_loop()

    def stop_listening(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._listening = False

    # --- Audio capture helpers ---

    def _record_short_chunk(self, duration: float = 2.0) -> str:
        _ensure_audio_deps()
        frames = []

        def callback(indata, frames_count, time_info, status):
            if status:
                pass
            frames.append(indata.copy())

        with sd.InputStream(samplerate=self.samplerate, channels=self.channels, callback=callback):
            sd.sleep(int(duration * 1000))

        arr = np.concatenate(frames, axis=0).flatten() if frames else np.zeros((int(self.samplerate * 0.1),), dtype="float32")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            path = temp_file.name
        _write_wav(path, arr, samplerate=self.samplerate)
        return path

    def _record_until_silence(self, silence_duration: float = 2.0, max_duration: float = 30.0, req_id: str = "unknown") -> str:
        print(f"[VOICE] [ReqID: {req_id}] Waiting for speech...")
        _ensure_audio_deps()
        recording_start_time = time.time()
        block_ms = 200
        blocks = []
        started = False
        silent_ms = 0
        total_ms = 0
        speech_start_time = None
        last_speech_time = None

        def callback(indata, frames_count, time_info, status):
            blocks.append(indata.copy())

        with sd.InputStream(samplerate=self.samplerate, channels=self.channels, callback=callback):
            while total_ms < int(max_duration * 1000) and silent_ms < int(silence_duration * 1000):
                sd.sleep(block_ms)
                total_ms += block_ms
                if not blocks:
                    continue
                
                # Fix: slice samples instead of blocks to correctly monitor only recent audio
                all_samples = np.concatenate(blocks, axis=0).flatten()
                samples_needed = int(self.samplerate * block_ms / 1000)
                recent = all_samples[-samples_needed:]

                # Use WebRTC VAD if available for robust speech detection
                is_speech = False
                if webrtcvad is not None:
                    try:
                        vad = webrtcvad.Vad(2)
                        # prepare 30ms frame
                        frame_ms = 30
                        frame_len = int(self.samplerate * frame_ms / 1000)
                        if len(recent) >= frame_len:
                            frame = recent[-frame_len:]
                            pcm16 = (frame * 32767).astype("int16").tobytes()
                            is_speech = vad.is_speech(pcm16, sample_rate=self.samplerate)
                    except Exception:
                        is_speech = False
                else:
                    rms = float(np.sqrt((recent ** 2).mean()))
                    is_speech = rms > 0.01

                if is_speech:
                    now = time.time()
                    last_speech_time = now
                    if not started:
                        started = True
                        speech_start_time = now
                    silent_ms = 0
                else:
                    # Fix: increment silence counter even if speech hasn't started yet
                    # so that we exit early (after silence_duration) if no speech is detected.
                    silent_ms += block_ms

        recording_end_time = time.time()
        recording_duration = recording_end_time - recording_start_time

        if blocks:
            arr = np.concatenate(blocks, axis=0).flatten()
        else:
            arr = np.zeros((int(self.samplerate * 0.1),), dtype="float32")

        speech_end_time = last_speech_time if last_speech_time is not None else None
        silence_duration_acc = (recording_end_time - last_speech_time) if last_speech_time is not None else 0.0

        # Save to debug_audio/ folder
        debug_dir = Path(__file__).parent.parent / "debug_audio"
        debug_dir.mkdir(exist_ok=True)
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        path = str(debug_dir / f"recording_{req_id}_{timestamp_str}.wav")
        
        _write_wav(path, arr, samplerate=self.samplerate)
        file_size = os.path.getsize(path)

        rms_vol = float(np.sqrt((arr ** 2).mean()))
        peak_vol = float(np.max(np.abs(arr))) if len(arr) > 0 else 0.0

        print(f"[INSTRUMENTATION] Request ID: {req_id}")
        print(f"[INSTRUMENTATION] Recording start time: {recording_start_time}")
        print(f"[INSTRUMENTATION] Recording end time: {recording_end_time}")
        print(f"[INSTRUMENTATION] Recording duration: {recording_duration:.3f} s")
        print(f"[INSTRUMENTATION] Sample rate: {self.samplerate} Hz")
        print(f"[INSTRUMENTATION] Channel count: {self.channels}")
        print(f"[INSTRUMENTATION] Frame count: {len(arr)}")
        print(f"[INSTRUMENTATION] Number of collected blocks: {len(blocks)}")
        print(f"[INSTRUMENTATION] RMS volume: {rms_vol:.6f}")
        print(f"[INSTRUMENTATION] Peak volume: {peak_vol:.6f}")
        print(f"[INSTRUMENTATION] File size: {file_size} bytes")
        print(f"[INSTRUMENTATION] Speech start timestamp: {speech_start_time}")
        print(f"[INSTRUMENTATION] Speech end timestamp: {speech_end_time}")
        print(f"[INSTRUMENTATION] Silence duration: {silence_duration_acc:.3f} s")
        print(f"[VOICE] Recorded audio saved to {path}")
        return path

    def transcribe_audio(self, audio_file: str, req_id: str = "unknown") -> Optional[str]:
        """Transcribe a WAV file and return cleaned text or None."""
        print(f"[VOICE] [ReqID: {req_id}] Transcribing: {audio_file}")
        t0 = time.time()
        try:
            if self._model is None:
                self._load_model()
            
            # Transcription options to log
            transcribe_options = {
                "language": "en",
                "temperature": 0.0,
                "beam_size": 5,
                "fp16": True,
                "condition_on_previous_text": True,
            }
            
            try:
                result = self._model.transcribe(audio_file, **transcribe_options)
            except TypeError:
                # Fallback for mock models in tests that do not accept kwargs
                result = self._model.transcribe(audio_file, language="en")
            t1 = time.time()
            transcribe_time = t1 - t0
            
            text = result.get("text", "").strip()
            clean_text = _clean_transcript(text)
            
            print(f"[INSTRUMENTATION] [ReqID: {req_id}] Whisper model: {self.model_name}")
            print(f"[INSTRUMENTATION] [ReqID: {req_id}] Transcription options: {transcribe_options}")
            print(f"[INSTRUMENTATION] [ReqID: {req_id}] Transcription time: {transcribe_time:.3f} s")
            print(f"[INSTRUMENTATION] [ReqID: {req_id}] Raw transcript: {text!r}")
            print(f"[INSTRUMENTATION] [ReqID: {req_id}] Clean transcript: {clean_text!r}")
            
            segments = result.get("segments", [])
            if segments:
                avg_logprob = float(np.mean([s.get("avg_logprob", 0) for s in segments]))
                no_speech_prob = float(np.mean([s.get("no_speech_prob", 0) for s in segments]))
                compression_ratio = float(np.mean([s.get("compression_ratio", 0) for s in segments]))
                print(f"[INSTRUMENTATION] [ReqID: {req_id}] Avg logprob: {avg_logprob:.6f}")
                print(f"[INSTRUMENTATION] [ReqID: {req_id}] No speech prob: {no_speech_prob:.6f}")
                print(f"[INSTRUMENTATION] [ReqID: {req_id}] Compression ratio: {compression_ratio:.6f}")

                # Fix: reject low-confidence/silent Whisper transcriptions (to prevent hallucinations on silence)
                if no_speech_prob > 0.6 or avg_logprob < -1.0:
                    print(f"[VOICE] [ReqID: {req_id}] Rejecting low-confidence transcript: {text!r} (no_speech_prob: {no_speech_prob:.3f}, avg_logprob: {avg_logprob:.3f})")
                    return None

            print(f"[VOICE] [ReqID: {req_id}] Transcript: {text}")
            return clean_text or None
        except Exception as exc:
            traceback.print_exc()
            return None


def _clean_transcript(text: str) -> str:
    # basic cleanup: remove filler words and repeated whitespace
    cleaned = text
    fillers = [r"\bum\b", r"\buh\b", r"\bmm\b", r"\berm\b", r"\bplease\b"]
    for f in fillers:
        cleaned = re.sub(f, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


__all__ = ["VoiceInputManager", "_clean_transcript"]
