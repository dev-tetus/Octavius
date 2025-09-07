# octavius/orchestrator/pipeline.py
from __future__ import annotations
import logging
from datetime import datetime
from typing import Callable, Optional, Protocol
import pyaudio
import numpy as np
from octavius.asr.base import Transcription,Transcriber  
from octavius.config.settings import Settings
from octavius.audio.devices import resolve_input_device
from octavius.audio.io import record_voice, record_voice_vad
from octavius.audio.vad import make_vad_params
from octavius.asr.whisper import WhisperTranscriber

logger = logging.getLogger(__name__)
class LLMFn(Protocol):
    def __call__(self, user_text: str, language: Optional[str] = None) -> str: ...

def get_llm_response(transcription: Transcription, llm_fn:LLMFn):
    try:
        assistant_text = llm_fn(
            (transcription.text or "").strip(),
            (transcription.language or None),
        )
        if assistant_text:
            return assistant_text.strip()
        else:
            logger.info("LLM devolvió respuesta vacía.")
    except Exception as e:
        logger.exception("Error en llm_fn: %s", e)

def pipeline_loop(
    settings: Settings,
    transcriber: Optional[Transcriber] = None,
    on_status: Optional[Callable[[str], None]] = None,
    on_final_text: Optional[Callable[[Transcription], None]] = None,
    llm_fn: Optional[LLMFn] = None
    ) -> None:

    p = pyaudio.PyAudio()
    try:
        device_idx = resolve_input_device(
            p,
            settings.audio.input_device,
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
                channels=settings.audio.channels,  
                vad_params=make_vad_params(settings),
            )

        else:
            logger.info("Grabando por duración fija…")
            if on_status:
                on_status("recording")
            recorded = record_voice(
                pyaudio_instance=p,
                seconds=5,  
                output_path=str(out_wav),
                input_device_index=device_idx,
                desired_rate=settings.audio.sample_rate,
                channels=settings.audio.channels,
            )

        
        _tr = transcriber or WhisperTranscriber(settings)
        for segment in recorded:
            if on_status:
                on_status("processing")
            audio = np.frombuffer(segment, dtype=np.int16).astype(np.float32) / 32768.0
            transcription = _tr.transcribe(audio)
            logger.info("Idioma detectado: %s. ASR: %s", transcription.language, transcription.text)
            if llm_fn is not None:
                llm_response = get_llm_response(transcription, llm_fn=llm_fn)
            if on_final_text:
                on_final_text(llm_response)

    finally:
        try:
            p.terminate()
        except Exception:
            logger.warning("No se pudo cerrar PyAudio limpiamente", exc_info=True)
