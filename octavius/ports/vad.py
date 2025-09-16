# octavius/application/ports/vad.py
from __future__ import annotations
from typing import Iterable, Protocol

from octavius.domain.models.recording_segment import RecordingSegment

class VADPort(Protocol):
    """Voice Activity Detector that segments speech until sustained silence.

    Contract:
      - The adapter owns any format normalization required for VAD:
        channel downmix (→ mono), resampling to target sample_rate, and framing to frame_ms.
      - `open()` prepares internal state (e.g., creates webrtcvad.Vad, derives sizes).
      - `capture_until_silence()` consumes audio from the injected AudioSource and returns
        a single speech segment (PCM16 mono) at `sample_rate`, aligned to `frame_ms`.
      - `close()` releases resources (idempotent). It may be a no-op if not needed.
    """

    # lifecycle
    def open(self,device_rate: int, device_channels: int) -> None: ...
    def close(self) -> None: ...

    # segmentation
    def capture_until_silence(self, frames: Iterable[bytes]) -> RecordingSegment: ...

    # normalized output metadata
    @property
    def sample_rate(self) -> int: ...
    @property
    def frame_ms(self) -> int: ...
