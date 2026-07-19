import os
import queue
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .base import BaseTTSEngine
from .piper_engine import PiperEngine
from .audio_player import AudioPlayer

logger = logging.getLogger(__name__)

# Default Configuration options (can be overridden via environment variables)
DEFAULT_MODEL_DIR = Path(__file__).parent / "models"
VOICE_MODEL = os.getenv("VOICE_MODEL", str(DEFAULT_MODEL_DIR / "en_US-lessac-medium.onnx"))
VOICE_CONFIG = os.getenv("VOICE_CONFIG", str(DEFAULT_MODEL_DIR / "en_US-lessac-medium.onnx.json"))
SPEECH_RATE = float(os.getenv("SPEECH_RATE", "1.0"))
OUTPUT_SAMPLE_RATE = int(os.getenv("OUTPUT_SAMPLE_RATE", "22050"))
TEMP_DIRECTORY = os.getenv("TEMP_DIRECTORY", "temp")


@dataclass(order=True)
class _SpeechRequest:
    priority_value: int
    sequence: int
    text: str
    done_event: Optional[threading.Event] = None
    metrics: Optional[Any] = None


class TTSService:
    def __init__(self, engine: Optional[BaseTTSEngine] = None) -> None:
        self.engine = engine or PiperEngine(
            model_path=VOICE_MODEL,
            config_path=VOICE_CONFIG,
            length_scale=SPEECH_RATE,
            volume=1.0,
            temp_dir=TEMP_DIRECTORY
        )
        self._player = AudioPlayer()
        self._queue: queue.PriorityQueue[_SpeechRequest] = queue.PriorityQueue()
        self._sequence = 0
        self._worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._busy = threading.Event()
        self._lock = threading.RLock()
        
        self.initialized = False
        self._stop_requested = False
        self._volume = 1.0

    @property
    def is_speaking(self) -> bool:
        return self._busy.is_set()

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, float(value)))
        if hasattr(self.engine, "volume"):
            self.engine.volume = self._volume

    def initialize(self) -> None:
        with self._lock:
            if self.initialized:
                return
            logger.info("[TTS] Initializing Piper...")
            self.engine.initialize()
            self.initialized = True
            logger.info("[TTS] Model loaded")

    def _ensure_worker(self) -> None:
        with self._lock:
            if self._worker and self._worker.is_alive():
                return

            self._stop_event.clear()
            self._stop_requested = False
            
            if not self.initialized:
                self.initialize()

            self._worker = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker.start()
            logger.info("[TTS] Worker started")

    def _worker_loop(self) -> None:
        logger.info("[TTS] Worker loop started.")
        while not self._stop_event.is_set():
            try:
                request = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            self._stop_requested = False
            self._busy.set()
            temp_file_path: Optional[Path] = None
            metrics = request.metrics
            
            try:
                logger.info(f"[TTS] Worker dequeued item: {request.text!r}")
                if metrics:
                    metrics.synthesis_start = time.time()
                
                temp_file_path = self.engine.synthesize(request.text)
                
                if metrics:
                    metrics.synthesis_end = time.time()
                    metrics.synthesis_time = metrics.synthesis_end - metrics.synthesis_start
                
                if self._stop_requested or self._stop_event.is_set():
                    logger.info("[TTS] Playback stopped during synthesis.")
                else:
                    logger.info("[TTS] Playing audio")
                    if metrics:
                        metrics.playback_start = time.time()
                    
                    self._player.play_wav(temp_file_path)
                    
                    if metrics:
                        metrics.playback_end = time.time()
                        metrics.playback_time = metrics.playback_end - metrics.playback_start
                        metrics.total_latency = metrics.playback_end - metrics.pipeline_start
                    logger.info("[TTS] Playback finished")

            except Exception as e:
                logger.error(f"[TTS] Error during synthesis/playback: {e}")
            finally:
                if temp_file_path and temp_file_path.exists():
                    try:
                        logger.info("[TTS] Cleaning temp file")
                        temp_file_path.unlink()
                    except Exception as e:
                        logger.error(f"[TTS] Failed to delete temp WAV file: {e}")
                
                self._busy.clear()
                logger.info("[TTS] Idle")
                
                if metrics:
                    from voice.metrics import log_accepted_request
                    try:
                        log_accepted_request(metrics)
                    except Exception as le:
                        logger.error(f"[TTS] Failed to log accepted request metrics: {le}")
                
                if request.done_event:
                    request.done_event.set()
        
        logger.info("[TTS] Worker loop exited.")

    def speak(self, text: str, priority: str = "normal") -> None:
        """Speak text synchronously (blocks until playback finishes)."""
        self._ensure_worker()
        self._drain_queue()
        done_event = threading.Event()
        self._enqueue(text, priority=priority, done_event=done_event)
        done_event.wait(timeout=30.0)

    def speak_async(self, text: str, priority: str = "normal") -> None:
        """Speak text asynchronously (returns immediately)."""
        self._ensure_worker()
        self._enqueue(text, priority=priority, done_event=None)

    def interrupt_and_speak(self, text: str) -> None:
        """Stop current speech immediately and speak new text."""
        self._ensure_worker()
        self.stop()
        self._enqueue(text, priority="urgent", done_event=None)

    def stop(self) -> None:
        """Immediately stop playback and clear the queue."""
        self._stop_requested = True
        self._drain_queue()
        self._player.stop()
        self._busy.clear()
        logger.info("[TTS] Playback stopped immediately and queue cleared.")

    def shutdown(self) -> None:
        """Gracefully shut down the TTS service, stopping playback and joining the worker."""
        self._stop_event.set()
        self.stop()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=2.0)
        self.engine.shutdown()
        self.initialized = False
        logger.info("[TTS] Service shutdown complete.")

    def synthesize(self, text: str) -> str:
        """Synthesize text to a WAV file and return the path."""
        if not self.initialized:
            self.initialize()
        path = self.engine.synthesize(text)
        return str(path)

    def play_audio(self, file_path: str) -> None:
        self._player.play_wav(file_path)

    def _enqueue(self, text: str, priority: str, done_event: Optional[threading.Event]) -> None:
        priority_value = self._priority_value(priority)
        with self._lock:
            self._sequence += 1
            from voice.metrics import request_context
            metrics = getattr(request_context, "metrics", None)
            if metrics:
                metrics.tts_queue_length = self._queue.qsize()
            request = _SpeechRequest(
                priority_value=priority_value,
                sequence=self._sequence,
                text=text,
                done_event=done_event,
                metrics=metrics
            )
            self._queue.put(request)

    def _drain_queue(self) -> None:
        with self._lock:
            while True:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

    def _priority_value(self, priority: str) -> int:
        mapping = {
            "urgent": 0,
            "high": 1,
            "normal": 2,
            "low": 3,
        }
        return mapping.get(priority, 2)
