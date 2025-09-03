from __future__ import annotations
import math
from typing import Iterator, Optional
from octavius.utils.pa_errors import pa_error_info
import pyaudio
import logging
import numpy as np
import soundfile as sf
from octavius.audio.vad import WebRTCVAD, VadParams
logger = logging.getLogger(__name__)
try:
    from scipy.signal import resample_poly
except Exception:
    logger.exception("resample_poly could not be resolved")
    resample_poly = None

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
    # else:
        # raise RuntimeError("Couldn't resample...")
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
            sf.write(file=path, data=audio_ndarray,samplerate=rate,subtype='PCM_16')
            return True
        else:
            sf.write(file=path, data=audio_ndarray, samplerate=rate)
            
            return True
    except Exception as e:
        logger.exception("Error encounter while writing WAV file at %s: %s", path, e)
        return False

def record_voice(
        pyaudio_instance: pyaudio.PyAudio,
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
    device_rate, device_channels = _pick_supported_format(pyaudio_instance, input_device_index, desired_rate, channels,fmt)
    frame_samples = int(device_rate * frame_ms / 1000)

    stream = _open_stream(pyaudio_instance, fmt, device_channels, device_rate, frame_samples, input_device_index)

    frames: list[bytes] = []
    total_frames = int((device_rate*seconds) // frame_samples)

    try:
        for _ in range(total_frames):
            frames.append(stream.read(frame_samples, exception_on_overflow=True))
    finally:
        if stream.is_active():
            stream.stop_stream()
        stream.close()
    
    raw = b"".join(frames)

    mono = _to_mono_int16(raw, channels=device_channels)

    mono16 = _resample_int16(mono, src_rate=device_rate, dst_rate=desired_rate)
    yield mono16.tobytes()
    
    

def read_audio_metadata(audio_path: str) -> tuple(np.ndarray, int):
    return sf.read(audio_path)

def _bytes_to_mono_bytes(pcm_bytes: bytes, channels: int) -> bytes:
    """Convierte bytes PCM16 con N canales a mono (promedio) y devuelve bytes PCM16 mono."""
    arr_mono = _to_mono_int16(pcm_bytes, channels=channels)
    return arr_mono.tobytes()

def _frame_generator(
    p: pyaudio.PyAudio,
    input_device_index: Optional[int],
    sample_rate: int,
    device_channels: int,
    frame_ms: int,
) -> Iterator[bytes]:
    """
    Genera frames PCM16 MONO del tamaño EXACTO que WebRTC-VAD espera.
    Abre el dispositivo con sus canales nativos y downmixa a mono.
    """
    fmt = pyaudio.paInt16
    frame_samples = int(sample_rate * frame_ms / 1000)

    # Leemos en bloques un poco más grandes para amortiguar llamadas a read():
    read_ms = max(frame_ms * 4, 120)
    read_samples = int(sample_rate * read_ms / 1000)

    # Abrimos con los canales QUE SOPORTA el dispositivo
    stream = _open_stream(
        p=p,
        fmt=fmt,
        channels=device_channels,
        rate=sample_rate,
        frame_samples=read_samples,
        input_device_index=input_device_index,
    )

    pending = bytearray()
    # El VAD quiere MONO: 1 canal * 2 bytes
    subframe_bytes = frame_samples * 1 * 2

    try:
        first = True
        while True:
            chunk = stream.read(read_samples, exception_on_overflow=True)
            # Si el dispositivo no es mono, convertimos aquí a mono
            if device_channels != 1:
                chunk = _bytes_to_mono_bytes(chunk, device_channels)
            # Si ya es mono, chunk queda tal cual
            pending.extend(chunk)

            if first: first = False
            while len(pending) >= subframe_bytes:
                yield bytes(pending[:subframe_bytes])
                del pending[:subframe_bytes]
    finally:
        stream.stop_stream()
        stream.close()

def record_voice_vad(
    pyaudio_instance: pyaudio.PyAudio,
    output_path: str,
    input_device_index: Optional[int],
    sample_rate: int,          # destino deseado (coincide con settings.audio.sample_rate)
    channels: int,             # validado a 1 en settings cuando VAD.enabled
    vad_params: VadParams,
) -> str:
    """
    Graba hasta silencio continuo (WebRTC VAD), convierte a mono/int16 si hace falta,
    re-muestrea al sample_rate deseado y escribe WAV reutilizando tus helpers.
    """
    fmt = pyaudio.paInt16
   

    # Abrimos el dispositivo en un formato soportado (idealmente mono)
    device_rate, device_channels = _pick_supported_format(
        p=pyaudio_instance,
        idx=input_device_index,
        desired_rate=sample_rate,
        desired_channels=channels,  # VAD => 1
        fmt=fmt
    )
    

    # Generador de frames al ritmo REAL del dispositivo
    frames_iter = _frame_generator(
        p=pyaudio_instance,
        input_device_index=input_device_index,
        sample_rate=device_rate,
        device_channels=device_channels,
        frame_ms=vad_params.frame_ms,
    )
    
    aligned_vad = VadParams(
        aggressiveness=vad_params.aggressiveness,
        frame_ms=vad_params.frame_ms,
        silence_ms=vad_params.silence_ms,
        pre_speech_ms=vad_params.pre_speech_ms,
        sample_rate=device_rate,        # <-- CLAVE: alinea al stream (48k aquí)
        max_record_ms=vad_params.max_record_ms,
    )
    # Ejecuta VAD hasta silencio
    vad = WebRTCVAD(aligned_vad)
    while True:
        frames, _stopped_by_silence = vad.capture_until_silence(frames_iter)
        if frames and _stopped_by_silence:

            logger.debug("VAD capturó %d frames (~%.2fs), stopped_by_silence=%s",
                len(frames), len(frames) * vad_params.frame_ms / 1000.0, _stopped_by_silence)
        
            raw = b"".join(frames)

            mono = _to_mono_int16(raw, channels=device_channels)

            mono16 = _resample_int16(np.frombuffer(raw, dtype=np.int16), src_rate=device_rate, dst_rate=sample_rate)
            yield mono16.tobytes()
