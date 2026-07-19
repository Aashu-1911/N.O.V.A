import logging
import wave
import winsound
import time
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

class AudioPlayer:
    def __init__(self) -> None:
        self._playing = False
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def play_wav(self, file_path: str | Path) -> bool:
        """Play a WAV file and block until finished, or until stopped."""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"[AudioPlayer] File not found: {path}")
            return False

        try:
            with wave.open(str(path), "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate()
                duration = frames / float(rate)
        except Exception as e:
            logger.error(f"[AudioPlayer] Failed to read audio file header: {e}")
            return False

        with self._lock:
            self._playing = True
            self._stop_event.clear()

        try:
            logger.info(f"[AudioPlayer] Playing wav file: {path} (duration: {duration:.2f}s)")
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            
            start_time = time.time()
            while time.time() - start_time < duration:
                if self._stop_event.is_set():
                    winsound.PlaySound(None, winsound.SND_PURGE)
                    logger.info("[AudioPlayer] Playback stopped via event.")
                    break
                time.sleep(0.01)
                
            logger.info(f"[AudioPlayer] Playback finished or stopped for {path}")
            return True
        except Exception as e:
            logger.error(f"[AudioPlayer] Error during winsound audio playback: {e}")
            return False
        finally:
            with self._lock:
                self._playing = False

    def stop(self) -> None:
        """Stop playback immediately."""
        self._stop_event.set()
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
            logger.info("[AudioPlayer] winsound.PlaySound(None, SND_PURGE) called successfully.")
        except Exception as e:
            logger.error(f"[AudioPlayer] Failed to stop winsound: {e}")
