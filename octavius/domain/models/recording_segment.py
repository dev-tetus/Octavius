from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RecordingSegment:
    """Normalized speech segment produced by the VAD.

    PCM is 16-bit mono, sampled at `sample_rate`. Timestamps are relative to the start of the segment.
    """
    pcm: bytes
    sample_rate: int
    channels: int           # always 1 (mono)
    frame_ms: int           # frame window used during VAD (10/20/30)
    start_ms: int
    end_ms: int

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)
