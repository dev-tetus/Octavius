# octavius/audio/pyaudio_source.py
from __future__ import annotations
from typing import Iterator, Optional, Union
import logging
import pyaudio

from octavius.config.settings import Settings
from octavius.ports.audio_source import AudioSource
from octavius.utils.devices import resolve_input_device
from octavius.utils.audio_utils import pick_supported_format, frames_per_buffer

logger = logging.getLogger(__name__)

class PyAudioSource(AudioSource):
    """PyAudio-backed AudioSource that yields PCM16 mono frames.

    It resolves the best input device, picks a supported (rate, channels) pair,
    opens the stream and downmixes to mono if needed.
    """

    def __init__(
        self,
        settings:Settings,
        pyaudio_instance: pyaudio.PyAudio,
    ) -> None:
        self._p = pyaudio_instance
        self._input_device = settings.audio.input_device
        self._desired_rate = settings.audio.sample_rate
        self._frame_ms = settings.vad.frame_ms

        self._stream = None  # type: ignore
        self._device_index: Optional[int] = None
        self._device_rate: Optional[int] = None
        self._device_channels: Optional[int] = None
        self._fpb: Optional[int] = None

    # --- AudioSource API -----------------------------------------------------

    def open(self) -> None:
        """Open the PyAudio input stream with a supported (rate, channels)."""
        fmt = pyaudio.paInt16

        # Resolve device index from identifier (index/name/None)
        idx = resolve_input_device(
            self._p,
            self._input_device,
            desired_rate=self._desired_rate,
            desired_channels=1,  # strongly prefer mono
            host_api_preference=["MME", "Windows DirectSound", "Windows WASAPI", "Windows WDM-KS"],
            allow_system_default=True,
        )
        rate, ch = pick_supported_format(
            p=self._p,
            idx=idx,
            desired_rate=self._desired_rate,
            desired_channels=1,  # VAD wants mono; fallback to stereo if needed
            fmt=fmt,
        )
        fpb = frames_per_buffer(rate, self._frame_ms)

        stream = self._p.open(
            format=fmt,
            channels=ch,
            rate=rate,
            input=True,
            input_device_index=idx,
            frames_per_buffer=fpb,
        )

        # Save runtime facts
        self._device_index = idx
        self._device_rate = rate
        self._device_channels = ch
        self._fpb = fpb
        self._stream = stream
        logger.info("PyAudioSource opened: dev=%s rate=%d ch=%d frame_ms=%d fpb=%d",
                    idx, rate, ch, self._frame_ms, fpb)

    def close(self) -> None:
        """Close the stream."""
        try:
            if self._stream is not None:
                if self._stream.is_active():
                    self._stream.stop_stream()
                self._stream.close()
        finally:
            self._stream = None

    def capture_stream(self) -> Iterator[bytes]:
        """Yield *device-native* PCM16 frames of length ~ frame_ms."""
        assert self._stream is not None, "Call open() before capture_stream()"
        assert self._fpb is not None
        while True:
            yield self._stream.read(self._fpb, exception_on_overflow=False)

    # --- Metadata ------------------------------------------------------------

    @property
    def sample_rate(self) -> int:
        assert self._device_rate is not None, "Source not opened yet"
        return self._device_rate

    @property
    def channels(self) -> int:
        assert self._device_channels is not None, "Source not opened yet"
        return self._device_channels

    @property
    def frame_ms(self) -> int:
        return self._frame_ms
