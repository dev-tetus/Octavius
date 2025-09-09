from __future__ import annotations
from typing import Iterator, Protocol

class AudioSource(Protocol):
    """Abstraction for any audio capture device/stream that yields PCM16 mono frames.

    Contract:
        - `open()` acquires the underlying resource (mic, socket, etc.).
        - `capture_stream()` yields frames as raw PCM16 MONO bytes.
        - Each frame MUST represent `frame_ms` ms at `sample_rate`.
        - `sample_rate` SHOULD be one of 8000/16000/32000/48000 (WebRTC-VAD friendly).
        - `close()` releases resources and is idempotent.
    """

    # lifecycle
    def open(self) -> None: ...
    def close(self) -> None: ...

    # capture
    def capture_stream(self) -> Iterator[bytes]: ...

    # metadata
    @property
    def sample_rate(self) -> int: ...
    @property
    def channels(self) -> int: ...
    @property
    def frame_ms(self) -> int: ...