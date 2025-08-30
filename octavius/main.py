from pathlib import Path
import pyaudio
from .audio import list_input_devices, record_voice

def main() -> None:
    """Entry point for Octavius
    """
    p = pyaudio.PyAudio()

    devices = list_input_devices(p)
    for d in devices:
        print(f"[{d.index}] {d.name} | ch:{d.max_input_channels} sr:{int(d.default_sample_rate)}")

    path = Path("audio_grabado.wav")
    record_voice(p, seconds=5,  output_path=str(path), input_device_index=0)
    print(f"Recorded file saved in {path.resolve()}")


if __name__=='__main__':
    main()
