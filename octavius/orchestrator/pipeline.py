# octavius/orchestrator/pipeline.py
from __future__ import annotations
import logging
from datetime import datetime
from typing import Callable, Optional, Protocol
import pyaudio

from octavius.asr.base import Transcription,Transcriber  
from octavius.config.settings import Settings
from octavius.audio.devices import resolve_input_device
from octavius.audio.io import record_voice, record_voice_vad, read_audio_metadata
from octavius.audio.vad import make_vad_params
from octavius.asr.whisper import WhisperTranscriber

logger = logging.getLogger(__name__)
class LLMFn(Protocol):
    def __call__(self, user_text: str, language: Optional[str] = None) -> str: ...
    
def run_once(
    settings: Settings,
    transcriber: Optional[Transcriber] = None,
    on_status: Optional[Callable[[str], None]] = None,
    on_final_text: Optional[Callable[[Transcription], None]] = None,
    llm_fn: Optional[LLMFn] = None
    ) -> Transcription:
    """
    1) Graba WAV (con VAD si está habilitado).
    2) Transcribe con Whisper (faster-whisper) según settings.asr.
    3) Devuelve el texto transcrito.
    """
    p = pyaudio.PyAudio()
    try:
        device_idx = resolve_input_device(
            p,
            settings.audio.input_device,   # 1 | "Focusrite" | "default" | None
            desired_rate=48000,
            desired_channels=1,
            host_api_preference=["MME", "Windows DirectSound", "Windows WASAPI", "Windows WDM-KS"],
        )
        if on_status:
            on_status("listening")

        out_wav = settings.paths.audio_dir / f"octavius_{datetime.now():%Y%m%d_%H%M%S}.wav"
        if settings.vad.enabled:
            logger.info("Grabando con VAD…")
            if on_status:
                on_status("recording")
            recorded = record_voice_vad(
                pyaudio_instance=p,
                output_path=str(out_wav),
                input_device_index=device_idx,
                sample_rate=settings.audio.sample_rate,
                channels=settings.audio.channels,  # validado a mono en settings
                vad_params=make_vad_params(settings),
            )
        else:
            logger.info("Grabando por duración fija…")
            if on_status:
                on_status("recording")
            recorded = record_voice(
                pyaudio_instance=p,
                seconds=5,  # si quieres, luego lo pasamos a settings
                output_path=str(out_wav),
                input_device_index=device_idx,
                desired_rate=settings.audio.sample_rate,
                channels=settings.audio.channels,
            )

        data, sr = read_audio_metadata(recorded)
        logger.info("WAV guardado: %s | sr=%s | %s",
                    recorded, sr, "mono" if getattr(data, "ndim", 1) == 1 else "stereo")
        if on_status:
                on_status("processing")
        _tr = transcriber or WhisperTranscriber(settings)
        transcription = _tr.transcribe(recorded)
        logger.info("Idioma detectado: %s. ASR: %s", transcription.language, transcription.text)
        
        if llm_fn is not None:
            try:
                assistant_text = llm_fn(
                    (transcription.text or "").strip(),
                    (transcription.language or None),
                )
                if assistant_text:
                    logger.info("LLM → %s", assistant_text.strip())
                else:
                    logger.info("LLM devolvió respuesta vacía.")
            except Exception as e:
                logger.exception("Error en llm_fn: %s", e)
        if on_final_text:
            on_final_text(transcription)
        return transcription

    finally:
        try:
            p.terminate()
        except Exception:
            logger.warning("No se pudo cerrar PyAudio limpiamente", exc_info=True)
