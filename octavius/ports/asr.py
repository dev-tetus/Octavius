from __future__ import annotations
from typing import Protocol, Any
from octavius.domain.models.recording_segment import RecordingSegment
from octavius.domain.models.utterance import Utterance

class ASRPort(Protocol):
    """Speech-to-text boundary; converts audio segments into text."""
    def transcribe(self, segment: RecordingSegment) -> Utterance: ...
    # Optional lifecycle for adapters that need it
    def open(self) -> None: ...
    def close(self) -> None: ...
