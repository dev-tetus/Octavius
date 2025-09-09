# octavius/cli/main.py
from __future__ import annotations
from dotenv import load_dotenv
import logging
import sys
import pyaudio

from octavius.config.settings import get_settings
from octavius.domain.services.turn_manager import TurnManager
from octavius.utils.logging import setup_logging
# Ports (interfaces)
from octavius.ports.audio_source import AudioSource
from octavius.ports.vad import VADPort
from octavius.ports.asr import ASRPort

# Adapters (implementations)
from octavius.infrastructure.audio.pyaudio_source import PyAudioSource
from octavius.infrastructure.vad.vad import WebRTCVADAdapter
from octavius.infrastructure.asr.whisper import WhisperTranscriber

# Orchestration
# from octavius.domain.services.turn_manager import TurnManager

log = logging.getLogger("octavius.cli")



def build_source(pa: pyaudio.PyAudio, settings) -> AudioSource:
    """Instantiate the audio input adapter (device-native frames)."""
    return PyAudioSource(
        pyaudio_instance=pa,
        input_device=settings.audio.input_device_index,  # can be None
        desired_rate=settings.audio.sample_rate,         # just a hint for device probing
        frame_ms=settings.vad.frame_ms,                  # device read granularity
    )


def build_vad(settings, target_rate: int) -> VADPort:
    """Instantiate the VAD adapter (owns downmix/resample/framing)."""
    return WebRTCVADAdapter(
        vad_settings=settings,
        target_sample_rate=target_rate,
    )


def build_asr(settings) -> ASRPort:  # pyright: ignore[reportUndefinedVariable]
    """Instantiate the ASR adapter (consumes RecordingSegment)."""
    return WhisperTranscriber(settings.asr)  # your existing adapter


def main() -> None:
    load_dotenv() 
    s = get_settings()
    setup_logging(
        level=s.logging.level,          
        log_dir=s.paths.logs_dir,
        filename=s.logging.file,
        max_bytes=s.logging.rotation_mb * 1024 * 1024,
        console=True,
        # Nuevas opciones:
        console_level="INFO",                  # consola más silenciosa
        file_level="DEBUG",                    # archivo detallado
        console_only_prefixes=["octavius", "__main__"],  # muestra solo mis logs en consola
        module_levels={
            "httpx": "INFO",
            "httpcore": "INFO",
            "google_genai": "DEBUG",
            "google_genai.models": "DEBUG",
            "asyncio": "WARNING",
        },
        disable_propagation=["httpx", "httpcore"],       # por si aún “rebotan”
    )

    pa = pyaudio.PyAudio()
    src = build_source(pa, s)
    vad = build_vad(s, target_rate=s.audio.sample_rate)
    asr = build_asr(s)

    try:
        # --- Open resources in main (explicit lifecycle) --------------------
        src.open()
        log.info("AudioSource opened: rate=%dHz ch=%d frame=%dms", src.sample_rate, src.channels, src.frame_ms)

        vad.open(
            device_rate=src.sample_rate,
            device_channels=src.channels,
            device_frame_ms=src.frame_ms,
        )
        log.info("VAD opened: target_rate=%dHz frame=%dms", vad.sample_rate, vad.frame_ms)

        # (Optional) if your ASR exposes open/close, do it here
        if hasattr(asr, "open") and callable(getattr(asr, "open")):
            asr.open()

        # --- Build TurnManager with already-opened dependencies -------------
        tm = TurnManager(
            audio_source=src,
            vad=vad,
            asr=asr,
            llm=None,  # add your LLM adapter later if you want
        )

        # --- Run one turn (speak + silence → ASR) ---------------------------
        result = tm.run_once()
        log.info("ASR: %s", result.asr_text)
        if result.llm_text:
            log.info("LLM: %s", result.llm_text)

    finally:
        # --- Close in reverse order -----------------------------------------
        try:
            if hasattr(asr, "close") and callable(getattr(asr, "close")):
                asr.close()
        except Exception:
            log.exception("ASR close failed")

        try:
            vad.close()
        except Exception:
            log.exception("VAD close failed")

        try:
            src.close()
        except Exception:
            log.exception("AudioSource close failed")

        pa.terminate()


if __name__ == "__main__":
    
    main()
