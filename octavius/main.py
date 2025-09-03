from datetime import datetime
import logging
from pathlib import Path
from typing import Optional
from octavius.asr.whisper import WhisperTranscriber
from octavius.orchestrator.pipeline import pipeline_loop
from octavius.config.settings import get_settings
from octavius.utils.logging import setup_logging
from dotenv import load_dotenv
from octavius.llm.gemini_client import GeminiClient

def main() -> int:
    """Entry point for Octavius
    """
    load_dotenv() 
    settings = get_settings()

    setup_logging(
        level=settings.logging.level,          
        log_dir=settings.paths.logs_dir,
        filename=settings.logging.file,
        max_bytes=settings.logging.rotation_mb * 1024 * 1024,
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
    log = logging.getLogger(__name__)
    log.info("Booting Octavius...")
    try:
        transcriber = WhisperTranscriber(settings)
        gpt = GeminiClient(
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            system_prompt=settings.llm.system_prompt,
        )
        while True:
            # Un turno: VAD + grabación hasta silencio + ASR
            transcription =pipeline_loop(
            transcription =pipeline_loop(
                settings,
                transcriber=transcriber,
                on_status=lambda s: log.debug("TM: %s", s),
                on_final_text=lambda tr: log.info("LLM Response -> %s", tr),
                llm_fn=gpt
            )

    except KeyboardInterrupt:
        log.info("Stopping Octavius (Ctrl+C).")
        return 0
    except Exception as exc:
        log.exception("Fatal error in main loop: %s", exc)
        return 1
    

if __name__=='__main__':
    raise SystemExit(main())
