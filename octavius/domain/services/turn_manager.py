from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Iterator
import logging

from octavius.ports.audio_source import AudioSource
from octavius.ports.vad import VADPort
from octavius.ports.asr import ASRPort
from octavius.domain.models.utterance import Utterance

log = logging.getLogger(__name__)

@dataclass(frozen=True)
class TurnResult:
    asr_text: Optional[str]
    llm_text: Optional[str]
    segment_ms: Optional[int]
    raw_asr: Optional[Utterance] = None

class TurnManager:
    """Coordinates one conversational turn using already-opened dependencies."""

    def __init__(self, *, audio_source: AudioSource, vad: VADPort, asr: ASRPort, llm=None) -> None:
        self._src = audio_source
        self._vad = vad
        self._asr = asr
        self._llm = llm  # optional; not used yet

    def run_once(self) -> TurnResult:
        """Capture speech until silence, send to ASR, and (optionally) to LLM."""
        frames: Iterator[bytes] = self._src.capture_stream()
        segment = self._vad.capture_until_silence(frames)  # RecordingSegment

        if not segment.pcm:
            log.warning("Empty segment from VAD")
            return TurnResult(asr_text=None, llm_text=None, segment_ms=None)

        asr_out: Utterance = self._asr.transcribe(segment)
        return TurnResult(
            asr_text=asr_out.text if asr_out else None,
            llm_text=None,  # integrate LLM later
            segment_ms=segment.duration_ms,
            raw_asr=asr_out,
        )
