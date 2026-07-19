import os
import wave
import logging
from pathlib import Path
from piper import PiperVoice, SynthesisConfig
from .base import BaseTTSEngine

logger = logging.getLogger(__name__)

class PiperEngine(BaseTTSEngine):
    def __init__(
        self,
        model_path: str | Path,
        config_path: str | Path | None = None,
        length_scale: float = 1.0,
        volume: float = 1.0,
        temp_dir: str | Path = "temp"
    ) -> None:
        self.model_path = Path(model_path)
        self.config_path = Path(config_path) if config_path else Path(str(model_path) + ".json")
        self.length_scale = length_scale
        self.volume = volume
        self.temp_dir = Path(temp_dir)
        self.voice: PiperVoice | None = None

    def initialize(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"[TTS ERROR] Piper voice model ONNX file not found at: {self.model_path.resolve()}.\n"
                f"Please download a Piper voice model and place it in the models directory."
            )
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"[TTS ERROR] Piper voice config JSON file not found at: {self.config_path.resolve()}.\n"
                f"Please ensure the config JSON is present alongside the model."
            )
        
        logger.info(f"[TTS] Loading Piper model from {self.model_path}")
        try:
            self.voice = PiperVoice.load(str(self.model_path), config_path=str(self.config_path))
            logger.info("[TTS] Piper model loaded successfully.")
        except Exception as e:
            logger.error(f"[TTS] Failed to load Piper model: {e}")
            raise RuntimeError(f"Failed to load Piper model: {e}") from e

    def synthesize(self, text: str) -> Path:
        if not self.voice:
            raise RuntimeError("PiperEngine is not initialized. Call initialize() first.")
        
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        
        import uuid
        temp_file_path = self.temp_dir / f"piper_{uuid.uuid4().hex}.wav"
        
        logger.info(f"[TTS] Synthesizing text: {text!r}")
        try:
            syn_config = SynthesisConfig(
                length_scale=self.length_scale,
                volume=self.volume
            )
            with wave.open(str(temp_file_path), "wb") as wav_file:
                self.voice.synthesize_wav(text, wav_file, syn_config=syn_config)
            logger.info(f"[TTS] Generated wav at {temp_file_path}")
            return temp_file_path
        except Exception as e:
            logger.error(f"[TTS] Piper synthesis failed: {e}")
            if temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception:
                    pass
            raise RuntimeError(f"Piper synthesis failed: {e}") from e

    def shutdown(self) -> None:
        self.voice = None
        logger.info("[TTS] PiperEngine shutdown complete.")
