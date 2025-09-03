from functools import lru_cache
import logging
import torch
import whisper
import soundfile as sf
import numpy as np
from typing import Optional
from octavius.config.settings import Settings
from .base import Transcriber, Transcription
logger = logging.getLogger(__name__)

def _normalize_device(device_str: Optional[str]) -> str:
    """
    Convierte 'auto' → 'cuda' si hay GPU, si no 'cpu'.
    Acepta ya 'cpu'/'cuda' tal cual. Cualquier otro valor cae a 'cpu'.
    """
    dev = (device_str or "auto").strip().lower()
    if dev == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if dev in ("cpu", "cuda"):
        # Si pide cuda pero no hay, forzamos cpu
        if dev == "cuda" and not torch.cuda.is_available():
            logger.warning("Se solicitó device='cuda' pero no hay GPU disponible. Usando 'cpu'.")
            return "cpu"
        return dev
    logger.warning("Device '%s' no reconocido. Usando 'cpu'.", device_str)
    return "cpu"

@lru_cache(maxsize=1)
def _get_model(model_id: str, device: str) -> whisper.Whisper:
    dev = _normalize_device(device)
    logger.info("Cargando Whisper '%s' en device='%s'…", model_id, dev)
    return whisper.load_model(model_id,dev)

def _ensure_mono_16k(path: str) -> np.ndarray:
    """
    Lee WAV → float32 mono a 16 kHz usando soundfile.
    Si llega estéreo, hace downmix. Si la tasa !=16k, levanta error (tu pipeline ya entrega 16k).
    """
    audio, sr = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)  # downmix seguro
    if sr != 16000:
        raise ValueError(f"Se esperaba 16 kHz, llegó {sr} Hz. Ajusta tu pipeline o añade resample aquí.")
    return audio

class WhisperTranscriber(Transcriber):
    def __init__(self, settings: Settings) -> None:
        a = settings.asr
        self.model = _get_model(a.model_id, a.device)
        self.language = a.language
        self.task = a.task

    def _getfp16(self):
        return bool(str(getattr(self.model, "device", "")) == "cuda" or torch.cuda.is_available())
    def transcribe_from_saved_audio(self, wav_path: str, language: Optional[str] = None) -> Transcription:
        lang = language or self.language
        audio = _ensure_mono_16k(wav_path)
        result = self.model.transcribe(
            audio,
            language=None,
            task=self.task,
            fp16=self._getfp16()
        )
        text = result["text"].strip()
        return Transcription(text=text, language=result.get("language"))
    
    def transcribe(self, audio: np.array) -> Transcription:
        result = self.model.transcribe(
            audio,
            language=None,
            task=self.task,
            fp16=self._getfp16()
        )
        text = result["text"].strip()
        return Transcription(text=text, language=result.get("language"))