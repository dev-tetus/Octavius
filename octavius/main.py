# octavius/cli/main.py
from __future__ import annotations
from dotenv import load_dotenv
import logging
import sys
import pyaudio

from octavius.config.settings import Settings, get_settings
from octavius.utils.logging import setup_logging

# Ports (interfaces)
from octavius.ports.audio_source import AudioSource
from octavius.ports.vad import VADPort
from octavius.ports.asr import ASRPort
from octavius.ports.llm import LLMClient

# Adapters (implementations)
from octavius.infrastructure.audio.pyaudio_source import PyAudioSource
from octavius.infrastructure.vad.vad import WebRTCVADAdapter
from octavius.infrastructure.asr.whisper import WhisperTranscriber
from octavius.infrastructure.llm.gemini import GeminiClient
from octavius.infrastructure.memory.in_memory_conversation_store import InMemoryConversationStore

# Domain services
from octavius.domain.services.conversation_history import ConversationHistory
from octavius.domain.services.turn_manager import TurnManager

log = logging.getLogger("octavius.cli")


def configure_logging(settings) -> None:
    """Console + file logging as per settings."""
    setup_logging(
        level=settings.logging.level,
        log_dir=settings.paths.logs_dir,
        filename=settings.logging.file,
        max_bytes=settings.logging.rotation_mb * 1024 * 1024,
        console=True,
        console_level="INFO",
        file_level="DEBUG",
        console_only_prefixes=["octavius", "__main__"],
        module_levels={
            "httpx": "INFO",
            "httpcore": "INFO",
            "google_genai": "DEBUG",
            "google_genai.models": "DEBUG",
            "asyncio": "WARNING",
        },
        disable_propagation=["httpx", "httpcore"],
    )


# -------------------- Builders --------------------

def build_source(pa: pyaudio.PyAudio, settings:Settings) -> AudioSource:
    """Instantiate the audio input adapter (device-native frames)."""
    return PyAudioSource(
        pyaudio_instance=pa,
        settings=settings
        
    )


def build_vad(settings:Settings) -> VADPort:
    """Instantiate the VAD adapter (owns downmix/resample/framing)."""
    return WebRTCVADAdapter(
        vad_settings=settings       
    )


def build_asr(settings:Settings) -> ASRPort:
    """Instantiate the ASR adapter (consumes RecordingSegment)."""
    return WhisperTranscriber(settings.asr)


def build_llm(settings:Settings) ->LLMClient:
    """Instantiate the LLM client adapter."""
    return GeminiClient(settings.llm)


def build_history(settings:Settings) -> ConversationHistory:
    """Instantiate conversation store + history service."""
    # Fallback robusto si no hay sección específica en settings
    max_turns = (
        getattr(getattr(settings, "memory", None), "max_turns", None)
        or getattr(settings, "max_turns", None)
        or 16
    )
    store = InMemoryConversationStore(max_turns=max_turns)
    history = ConversationHistory(store=store, conv_id="default", summarizer=None)
    return history


# -------------------- App entrypoint --------------------

def main() -> None:
    load_dotenv()
    s = get_settings()
    configure_logging(s)

    pa = pyaudio.PyAudio()

    # Build all adapters/services (no side effects yet)
    src = build_source(pa=pa, settings=s)
    vad = build_vad(settings=s, target_rate=s.audio.sample_rate)
    asr = build_asr(settings=s)
    llm = build_llm(settings=s)
    history = build_history(settings=s)

    try:
        # ---- Open lifecycle explicitly (in order) ----
        src.open()
        log.info("AudioSource opened: rate=%dHz ch=%d frame=%dms",
                 src.sample_rate, src.channels, src.frame_ms)

        vad.open(
            device_rate=src.sample_rate,
            device_channels=src.channels
        )
        log.info("VAD opened: target_rate=%dHz frame=%dms",
                 vad.sample_rate, vad.frame_ms)

        if hasattr(asr, "open") and callable(getattr(asr, "open")):
            asr.open()

        if hasattr(llm, "open") and callable(getattr(llm, "open")):
            llm.open()

        # ---- Inject into TurnManager (already-opened deps) ----
        tm = TurnManager(
            audio=src,                # o audio_source=src según tu firma
            vad=vad,
            asr=asr,
            llm_client=llm,
            history=history,
            llm_system_prompt=getattr(s.llm, "system_prompt", None),
            llm_max_tokens_context=getattr(s.llm, "max_tokens", None) or 2048,
        )

        # ---- Run one conversational turn ----
        result = tm.run_forever()
       

    finally:
        # ---- Close in reverse order (idempotent/safe) ----
        try:
            if hasattr(llm, "close") and callable(getattr(llm, "close")):
                llm.close()
        except Exception:
            log.exception("LLM close failed")

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
