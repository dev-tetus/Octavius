# octavius/infrastructure/vad/webrtc_vad_adapter.py
from __future__ import annotations
from typing import Iterable, List, Iterator, Optional
import logging
import numpy as np
import webrtcvad
from octavius.config.settings import Settings
from octavius.infrastructure.vad.vad_settings import VadParams
from octavius.domain.models.recording_segment import RecordingSegment
from octavius.ports.vad import VADPort
from octavius.utils.audio_utils import to_mono_int16, resample_int16

logger = logging.getLogger(__name__)

class WebRTCVADAdapter(VADPort):
    """WebRTC-based VAD that normalizes input and segments until sustained silence.

    Responsibilities owned here:
      - Convert device-native frames → MONO int16 @ target_sample_rate.
      - Split into frame_ms windows and run webrtcvad.Vad on those frames.
      - Collect frames until 'silence_ms' of continuous non-speech is observed.
    """

    def __init__(
        self,
        vad_settings: Settings,
    ) -> None:
        """
        Args:
            audio_source: raw device frames provider (no format conversion).
            vad_settings: configuration object with attributes
                .aggressiveness, .frame_ms, .silence_ms, .pre_speech_ms, .max_record_ms 
            target_sample_rate: normalized sample rate for VAD (e.g., 16000)
        """
        self._s = self._make_vad_params(settings=vad_settings)
        # Will be set in open()
        self._vad: Optional[webrtcvad.Vad] = None
        self._dev_rate: Optional[int] = None
        self._dev_channels: Optional[int] = None
        self._frame_samples: Optional[int] = None
        self._silence_frames_needed: Optional[int] = None
        self._pre_frames: Optional[int] = None

        # carry-over buffer to avoid dropping partial frames after resampling
        self._carry: np.ndarray = np.empty(0, dtype=np.int16)

    # --------------------- VADPort API ---------------------------------------

    def open(self,device_rate: int, device_channels: int) -> None:
        """Create VAD instance and derive all runtime sizes from settings + device metadata."""
        self._vad = webrtcvad.Vad(self._s.aggressiveness)

        # Read device facts from AudioSource metadata
        self._dev_rate = device_rate
        self._dev_channels = device_channels

        # Precompute target frame sizes
        self._frame_samples = int(self._s.sample_rate * self._s.frame_ms / 1000)
        self._silence_frames_needed = max(1, int(self._s.silence_ms / self._s.frame_ms))
        self._pre_frames = max(0, int(self._s.pre_speech_ms / self._s.frame_ms))

        logger.info(
            "VAD.open: dev_rate=%s dev_ch=%s → target_rate=%d frame_ms=%d frame_samples=%d silence_frames=%d pre_frames=%d",
            self._dev_rate, self._dev_channels, self._s.sample_rate, self._s.frame_ms,
            self._frame_samples, self._silence_frames_needed, self._pre_frames,
        )

    def close(self) -> None:
        """Nothing to release here; keep idempotent."""
        self._vad = None

    def capture_until_silence(self,frames: Iterable[bytes]) -> RecordingSegment:
        """Consume device frames until silence; return a RecordingSegment with single PCM16 mono segment at target rate."""
        assert self._vad is not None, "Call open() before capture_until_silence()"
        assert self._dev_rate is not None and self._dev_channels is not None
        assert self._frame_samples is not None and self._silence_frames_needed is not None and self._pre_frames is not None

        ring: List[bytes] = []   # pre-speech buffer (frame-sized)
        speech: List[bytes] = []
        silence_count = 0
        total_ms = 0

        for raw in frames:
            for fr in self._dev_raw_to_target_frames(raw):
                if self._vad.is_speech(fr, self._s.sample_rate):
                    if self._pre_frames and ring: 
                        speech.extend(ring); ring.clear()
                    speech.append(fr); 
                    silence_count = 0
                else:
                    if speech:
                        silence_count += 1
                        if silence_count >= (self._silence_frames_needed or 1):
                            pcm = b"".join(speech)
                            seg_ms = len(speech) * self._s.frame_ms
                            return RecordingSegment(
                                pcm=pcm,
                                sample_rate=self._s.sample_rate,
                                channels=1,
                                frame_ms=int(self._s.frame_ms),
                                start_ms=0,
                                end_ms=seg_ms,
                            )
                    elif self._pre_frames:
                        ring.append(fr)
                        if len(ring) > self._pre_frames: ring.pop(0)

                total_ms += self._s.frame_ms
                if self._s.max_record_ms and total_ms >= self._s.max_record_ms:
                    pcm = b"".join(speech)
                    seg_ms = len(speech) * self._s.frame_ms
                    return RecordingSegment(
                        pcm=pcm, sample_rate=self._s.sample_rate, channels=1,
                        frame_ms=int(self._s.frame_ms), start_ms=0, end_ms=seg_ms
                    )

        # stream ended; return whatever we have
        pcm = b"".join(speech)
        seg_ms = len(speech) * self._s.frame_ms
        return RecordingSegment(
            pcm=pcm, sample_rate=self._s.sample_rate, channels=1,
            frame_ms=int(self._s.frame_ms), start_ms=0, end_ms=seg_ms
        )

    # --------------------- Helpers ------------------------------------------

    def _dev_raw_to_target_frames(self, raw: bytes) -> List[bytes]:
        """Convert device-native bytes → target-rate mono frames aligned to frame_ms."""
        assert self._dev_rate is not None and self._dev_channels is not None and self._frame_samples is not None

        # 1) downmix to mono at device rate
        mono_raw = to_mono_int16(raw, self._dev_channels)
        mono_dev = np.frombuffer(mono_raw, dtype=np.int16)

        # 2) resample to target rate
        mono_tgt = resample_int16(mono_dev, self._dev_rate, self._s.sample_rate)

        # 3) slice into fixed-size frames
        if self._carry.size:
            mono_tgt = np.concatenate([self._carry, mono_tgt])
        frm = self._frame_samples
        n = (len(mono_tgt) // frm) * frm
        if n == 0:
            self._carry = mono_tgt  # keep all as carry
            return []
        frames = mono_tgt[:n].reshape(-1, frm).astype(np.int16)
        self._carry = mono_tgt[n:]  # keep remainder for next call
        return [f.tobytes() for f in frames]
    
    def _make_vad_params(self,settings: Settings) -> VadParams:
        v, a = settings.vad, settings.audio
        return VadParams(
            aggressiveness=v.aggressiveness,
            frame_ms=v.frame_ms,
            silence_ms=v.silence_ms,
            pre_speech_ms=v.pre_speech_ms,
            sample_rate=a.sample_rate,
            max_record_ms=v.max_record_ms,
        )

    # --------------------- Metadata -----------------------------------------

    @property
    def sample_rate(self) -> int:
        """Normalized VAD output sample rate."""
        return self._s.sample_rate

    @property
    def frame_ms(self) -> int:
        return int(self._s.frame_ms)
