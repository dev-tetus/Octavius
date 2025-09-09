# octavius/utils/audio_utils.py
from __future__ import annotations
from typing import Tuple
import logging
import numpy as np
import pyaudio
from octavius.utils.pa_errors import pa_error_info

logger = logging.getLogger(__name__)

# ---- math helpers -----------------------------------------------------------

def frames_per_buffer(rate: int, frame_ms: int) -> int:
    """Return number of samples per buffer for a given (rate, frame_ms)."""
    return int(rate * frame_ms / 1000)

def to_mono_int16(raw: bytes, channels: int) -> bytes:
    """Downmix interleaved PCM16 frames to mono (average across channels).
    If channels == 1, `raw` is returned unchanged.
    """
    if channels == 1:
        return raw
    x = np.frombuffer(raw, dtype=np.int16)
    if x.size == 0:
        return raw
    try:
        x = x.reshape(-1, channels).mean(axis=1)
    except ValueError:
        n = (x.size // channels) * channels
        x = x[:n].reshape(-1, channels).mean(axis=1)
    y = np.asarray(np.round(x), dtype=np.int16)
    return y.tobytes()

def resample_int16(x: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Resample int16 PCM using polyphase when available, else linear interpolation."""
    if src_rate == dst_rate:
        return x
    try:
        from scipy.signal import resample_poly  # lazy import
    except Exception:
        resample_poly = None  # type: ignore
    if resample_poly is not None:
        y = resample_poly(x.astype(np.float32), dst_rate, src_rate)
        y = np.clip(np.round(y), -32768, 32767).astype(np.int16)
        return y
    # Fallback: linear interpolation
    import numpy as _np
    t_src = _np.linspace(0.0, 1.0, num=len(x), endpoint=False, dtype=_np.float32)
    out_len = int(len(x) * dst_rate / src_rate)
    t_dst = _np.linspace(0.0, 1.0, num=out_len, endpoint=False, dtype=_np.float32)
    y = _np.interp(t_dst, t_src, x.astype(_np.float32))
    return _np.clip(_np.round(y), -32768, 32767).astype(_np.int16)

def pcm16_bytes_to_ndarray(pcm: bytes) -> np.ndarray:
    """View PCM16 mono/stereo bytes as np.int16 (no copy)."""
    if not pcm:
        return np.zeros(0, dtype=np.int16)
    return np.frombuffer(pcm, dtype=np.int16)

def int16_to_float32(x: np.ndarray) -> np.ndarray:
    """Scale int16 to float32 in [-1, 1] safely."""
    if x.dtype != np.int16:
        x = x.astype(np.int16, copy=False)
    y = x.astype(np.float32, copy=False) / 32768.0
    # sanitize edge cases
    return np.clip(np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0), -1.0, 1.0)

def ensure_float32_mono_16k_from_pcm16(pcm: bytes, sample_rate: int, channels: int = 1, frame_ms: int | None = None) -> np.ndarray:
    """Normalize PCM16 bytes → float32 mono @ 16 kHz using existing int16 helpers.

    - Reuses `to_mono_int16` (downmix) and `resample_int16` (int16-domain).
    - Converts to float32 only at the end (efficient + avoids extra rounding).
    """
    raw = pcm
    if channels != 1:
        raw = to_mono_int16(raw, channels)  

    x_i16 = pcm16_bytes_to_ndarray(raw)

    if sample_rate != 16000:
        x_i16 = resample_int16(x_i16, src_rate=sample_rate, dst_rate=16000)  

    
    if frame_ms:
        samples_per_frame = int(16000 * frame_ms / 1000)
        usable = (len(x_i16) // samples_per_frame) * samples_per_frame
        if usable:
            x_i16 = x_i16[:usable]

    return int16_to_float32(x_i16)
# ---- device probing ---------------------------------------------------------

def pick_supported_format(
    p: pyaudio.PyAudio,
    idx: int,
    desired_rate: int,
    desired_channels: int,
    fmt: int,
) -> Tuple[int, int]:
    """Probe the device for a supported (rate, channels) pair and return the first that works."""
    device_name = p.get_device_info_by_index(idx).get("name")
    attempts = [
        (desired_rate, desired_channels),
        (48000, 1), (48000, 2),
        (44100, 1), (44100, 2),
    ]
    for rate, ch in attempts:
        try:
            ok = p.is_format_supported(rate, input_device=idx, input_channels=ch, input_format=fmt)
            if ok:
                return rate, ch
        except Exception as e:
            code, name, msg = pa_error_info(e)
            logger.error("Unsupported format for device(%s) (%d Hz, %d ch) → [%s %s] %s",
                         device_name, rate, ch, name, code, msg, exc_info=False)
    raise RuntimeError(f"No format supported for device {device_name}")

