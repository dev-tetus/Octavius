import wave
from typing import Optional
import pyaudio

def record_voice(
        p: pyaudio.PyAudio,
        seconds: float = 5.0,
        rate: int = 16000,
        channels: int = 1,
        frame_ms: int = 30,
        output_path: str = "voice_record.wav",
        input_device_index: Optional[int] = None
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
    frame_samples = int(rate * frame_ms / 1000)
    stream = p.open(
        format=fmt,
        channels=channels,
        rate=rate,
        input=True,
        frames_per_buffer=frame_samples,
        input_device_index=input_device_index
    )

    frames: list[bytes] = []
    total_frames = int((rate*seconds) // frame_samples)

    try:
        for _ in range(total_frames):
            frames.append(stream.read(frame_samples, exception_on_overflow=False))
    finally:
        stream.stop_stream()
        stream.close()

    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(fmt))
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))
    return output_path