from __future__ import annotations
from octavius.utils.pa_errors import pa_error_info
import pyaudio
import logging
import numpy as np
import soundfile as sf
logger = logging.getLogger(__name__)

try:
    from scipy.signal import resample_poly
except Exception:
    logger.exception("resample_poly could not be resolved")
    resapmle_poly = None

def _to_mono_int16(pcm_bytes: bytes, channels:int) ->  np.ndarray:
    x = np.frombuffer(pcm_bytes, dtype=np.int16)
    if channels == 1:
        return x
    x = x.reshape(-1, channels).mean(axis=1)
    return np.asarray(np.round(x), dtype=np.int16)

def _resample_int16(x:np.ndarray, src_rate:int, dst_rate:int) -> np.ndarray:
    if src_rate == dst_rate:
        return x
    if resample_poly is not None:
        y = resample_poly(x.astype(np.float32), dst_rate, src_rate)
        y = np.clip(np.round(y), -32768, 32767).astype(np.int16)
        return y
    t_src = np.linspace(0.0, 1.0, num=len(x), endpoint=False, dtype=np.float32)
    out_len = int(len(x) * dst_rate / src_rate)
    t_dst = np.linspace(0.0, 1.0, num=out_len, endpoint=False, dtype=np.float32)
    y = np.interp(t_dst, t_src, x.astype(np.float32))
    return np.clip(np.round(y), -32768, 32767).astype(np.int16)

def _open_stream(
    p: pyaudio.PyAudio,
    fmt:pyaudio.paInt16,
    channels:int,
    rate:int,
    frame_samples:int,
    input_device_index:int
    ) -> pyaudio.PyAudio.Stream:
    return p.open(
        format=fmt,
        channels=channels,
        rate=rate,
        input=True,
        frames_per_buffer=frame_samples,
        input_device_index=input_device_index
    )
def _pick_supported_format(
    p: pyaudio.PyAudio,
    idx:int,
    desired_rate:int,
    desired_channels:int,
    fmt: int
    ) -> tuple(int,int):
    device_name = p.get_device_info_by_index(idx).get("name")
    attempts = [
        (desired_rate, desired_channels),
        (48000, 1),
        (48000, 2),
        (44100, 1),
        (44100, 2),
    ]
    for rate, ch in attempts:
        try:
            ok = p.is_format_supported(rate,
                                       input_device=idx,
                                       input_channels=ch,
                                       input_format=fmt)
            if ok:
                logger.info("Supported format for device (%s): %d Hz, %d ch", device_name, rate, ch)
                return rate, ch
        except Exception as e:
            code, name, msg = pa_error_info(e)
            logger.error("Unsupported format for device(%s) (%d Hz, %d ch) → [%s %s] %s",
                           device_name, rate, ch, name, code, msg, exc_info=False)
    raise RuntimeError(f"No format supported for device {device_name}")

def _write_audio(
    path: str,
    rate:int,
    audio_ndarray:np.ndarray
) -> bool:
    """Write audio file at path

    Args:
        path (str): Path for audio to be saved
        rate (int): Desired rate for audio
        fmt (int): Sample format
        audio_ndarray (np.ndarray): NumPy array with audio content

    Returns:
        int: Returns Treu if all good, False otherwise
    """
    try:
        if audio_ndarray.dtype == np.int16:
            sf.write(file=path, data=audio_ndarray,samplerate=rate,subtype=sf.default_subtype('WAV'))
            return True
        else:
            sf.write(file=path, data=audio_ndarray, samplerate=rate)
            
            return True
    except Exception as e:
        logger.exception("Error encounter while writing WAV file at %s: %s", path, e)
        return False

def record_voice(
        p: pyaudio.PyAudio,
        seconds: float = 5.0,
        desired_rate: int = 16000,
        channels: int = 1,
        frame_ms: int = 30,
        output_path: str = "voice_record.wav",
        input_device_index: int|None = None
) -> str:
    """_summary_

    Args:
        p (pyaudio.PyAudio): PyAudio instance
        seconds (float, optional): Duration of recording in seconds. Defaults to 5.0.
        rate (int, optional): Sample rate of recording. Defaults to 16000.
        channels (int, optional): Number of channels to capture 
        1: Mono
        2: Stereo.Defaults to 1.
        frame_ms (int, optional): _description_. Defaults to 30.
        output_path (str, optional): Path for recording to be saved. Defaults to "voice_record.wav".
        input_device_index (Optional[int], optional): Input device to be used. Defaults to None.

    Returns:
        str: Audio recorded path 
    """
    fmt = pyaudio.paInt16
    frame_samples = int(desired_rate * frame_ms / 1000)

    device_rate, device_channels = _pick_supported_format(p, input_device_index, desired_rate, channels,fmt)
    stream = _open_stream(p, fmt, device_channels, device_rate, frame_samples, input_device_index)

    frames: list[bytes] = []
    total_frames = int((device_rate*seconds) // frame_samples)

    try:
        for _ in range(total_frames):
            frames.append(stream.read(frame_samples, exception_on_overflow=False))
    finally:
        if stream.is_active():
            stream.stop_stream()
        stream.close()
    
    raw = b"".join(frames)

    mono = _to_mono_int16(raw, channels=device_channels)

    mono16 = _resample_int16(mono, src_rate=device_rate, dst_rate=desired_rate)

    is_saved = _write_audio(output_path, desired_rate, mono16)
    if is_saved:
        return output_path
    else:
        logger.info("Audio not saved")
        raise RuntimeError("Audio not saved")

def read_audio_metadata(audio_path: str) -> tuple(np.ndarray, int):
    return sf.read(audio_path)