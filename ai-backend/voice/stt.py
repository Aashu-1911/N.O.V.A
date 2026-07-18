"""Voice input (STT) module for Jarvis — Push-To-Talk (PTT) Refactor.

Features:
- Global low-level Windows keyboard hook using ctypes for Ctrl+Space hold/release
- Asynchronous microphone capture using sounddevice
- Whisper model transcribing local files
- Explicit UI State tracking
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
import sys

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

# Import ctypes for low-level Windows keyboard hooking
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
else:
    ctypes = None
    wintypes = None


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


class KeyboardHookListener:
    """Manages a low-level Windows keyboard hook for Ctrl+Space PTT."""
    
    def __init__(self, on_press: Callable[[], None], on_release: Callable[[], None]) -> None:
        self.on_press = on_press
        self.on_release = on_release
        self.recording_active = False
        self._thread: Optional[threading.Thread] = None
        self._hook = None
        self._hook_callback = None
        self.ctrl_held = False
        self.space_held = False

    def start(self) -> None:
        if sys.platform != "win32" or ctypes is None:
            print("[KEYBOARD] Global keyboard hook is only supported on Windows.")
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        
        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_ulonglong)
            ]

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # API settings
        SetWindowsHookEx = user32.SetWindowsHookExW
        SetWindowsHookEx.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
        SetWindowsHookEx.restype = wintypes.HHOOK

        UnhookWindowsHookEx = user32.UnhookWindowsHookEx
        UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        UnhookWindowsHookEx.restype = wintypes.BOOL

        CallNextHookEx = user32.CallNextHookEx
        CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        CallNextHookEx.restype = ctypes.c_int

        WH_KEYBOARD_LL = 13
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        WM_SYSKEYDOWN = 0x0104
        WM_SYSKEYUP = 0x0105

        def hook_proc(nCode, wParam, lParam):
            if nCode >= 0:
                kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = kb.vkCode

                is_ctrl = vk in (0x11, 0xA2, 0xA3)
                is_space = (vk == 0x20)

                if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    if is_ctrl:
                        self.ctrl_held = True
                    elif is_space:
                        self.space_held = True

                    if self.ctrl_held and self.space_held:
                        if not self.recording_active:
                            self.recording_active = True
                            self.on_press()
                elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                    if is_ctrl:
                        self.ctrl_held = False
                    elif is_space:
                        self.space_held = False

                    if not self.ctrl_held or not self.space_held:
                        if self.recording_active:
                            self.recording_active = False
                            self.on_release()

            return CallNextHookEx(self._hook, nCode, wParam, lParam)

        # Define GetModuleHandleW properly to prevent 64-bit handle truncation
        GetModuleHandle = kernel32.GetModuleHandleW
        GetModuleHandle.argtypes = [wintypes.LPCWSTR]
        GetModuleHandle.restype = wintypes.HINSTANCE

        self._hook_callback = HOOKPROC(hook_proc)
        h_mod = GetModuleHandle(None)
        
        self._hook = SetWindowsHookEx(
            WH_KEYBOARD_LL,
            self._hook_callback,
            h_mod,
            0
        )
        if not self._hook:
            # Fallback to passing 0 as the module handle (valid for WH_KEYBOARD_LL global hooks)
            self._hook = SetWindowsHookEx(
                WH_KEYBOARD_LL,
                self._hook_callback,
                0,
                0
            )
            
        if not self._hook:
            err = kernel32.GetLastError()
            print(f"[KEYBOARD] Failed to install keyboard hook! GetLastError: {err}")
            return

        print("[KEYBOARD] Global keyboard hook installed. Hold Ctrl+Space to speak.")

        # Windows Message Loop
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def stop(self) -> None:
        if sys.platform == "win32" and ctypes is not None:
            if self._hook:
                ctypes.windll.user32.UnhookWindowsHookEx(self._hook)
                self._hook = None


class VoiceInputManager:
    """Manage push-to-talk command capture and state transitions."""

    # UI States
    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_PROCESSING = "processing"
    STATE_SPEAKING = "speaking"

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
        self.wake_words = wake_words or ["hey Nova", "nova", "ok nova"]

        self._model = None
        self._callbacks: List[Callable[[str], None]] = []
        self._request_counter = 0

        self.state = self.STATE_IDLE
        self._recording_blocks: List["np.ndarray"] = []
        self._recording_stream: Optional["sd.InputStream"] = None

        # Internal queue used for events.
        self._q: "queue.Queue[tuple[str, Optional[str]]]" = queue.Queue()

    @property
    def is_listening(self) -> bool:
        return self.state == self.STATE_RECORDING

    def on_command(self, callback: Callable[[str], None]) -> None:
        self._callbacks.append(callback)

    def set_state(self, new_state: str) -> None:
        self.state = new_state
        print(f"[UI_STATE] {new_state.upper()}")

    def get_events(self) -> List[tuple[str, Optional[str]]]:
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
            self._model = whisper.load_model(self.model_name)

    def start_recording(self) -> None:
        _ensure_audio_deps()
        self.set_state(self.STATE_RECORDING)
        print("[VOICE] Recording...")
        self._recording_blocks = []

        def callback(indata, frames_count, time_info, status):
            self._recording_blocks.append(indata.copy())

        self._recording_stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            callback=callback
        )
        self._recording_stream.start()

    def stop_recording(self) -> str:
        if self._recording_stream is None:
            print("[VOICE] Warning: Stop called but recording was not active.")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                path = temp_file.name
            _write_wav(path, np.zeros((int(self.samplerate * 0.1),), dtype="float32"), samplerate=self.samplerate)
            return path

        self._recording_stream.stop()
        self._recording_stream.close()
        self._recording_stream = None

        blocks = self._recording_blocks
        self._recording_blocks = []

        if blocks:
            arr = np.concatenate(blocks, axis=0).flatten()
        else:
            arr = np.zeros((int(self.samplerate * 0.1),), dtype="float32")

        debug_dir = Path(__file__).parent.parent / "debug_audio"
        debug_dir.mkdir(exist_ok=True)
        self._request_counter += 1
        req_id = f"{self._request_counter:02d}"
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        path = str(debug_dir / f"recording_{req_id}_{timestamp_str}.wav")

        _write_wav(path, arr, samplerate=self.samplerate)
        print(f"[VOICE] Recorded audio saved to {path}")
        return path

    def transcribe_audio(self, audio_file: str, req_id: str = "unknown") -> Optional[str]:
        """Transcribe a WAV file and return cleaned text or None."""
        print(f"[VOICE] [ReqID: {req_id}] Transcribing: {audio_file}")
        t0 = time.time()
        try:
            if self._model is None:
                self._load_model()
            
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

                # Reject low-confidence/silent Whisper transcriptions (to prevent hallucinations on silence)
                if no_speech_prob > 0.6 or avg_logprob < -1.0:
                    print(f"[VOICE] [ReqID: {req_id}] Rejecting low-confidence transcript: {text!r} (no_speech_prob: {no_speech_prob:.3f}, avg_logprob: {avg_logprob:.3f})")
                    return None

            print(f"[VOICE] [ReqID: {req_id}] Transcript: {text}")
            return clean_text or None
        except Exception as exc:
            traceback.print_exc()
            return None

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

    # Continuous listening stubs for backward compatibility
    def start_listening(self, background: bool = True) -> None:
        pass

    def stop_listening(self) -> None:
        pass


def _clean_transcript(text: str) -> str:
    cleaned = text
    fillers = [r"\bum\b", r"\buh\b", r"\bmm\b", r"\berm\b", r"\bplease\b"]
    for f in fillers:
        cleaned = re.sub(f, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


__all__ = ["VoiceInputManager", "_clean_transcript", "KeyboardHookListener"]
