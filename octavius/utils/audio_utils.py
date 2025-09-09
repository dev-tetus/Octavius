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
