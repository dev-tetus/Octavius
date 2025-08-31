import logging
from pathlib import Path
import pyaudio
from .audio.devices import list_input_devices, resolve_input_device
from .audio.io import record_voice, read_audio_metadata

from .utils.logging import setup_logging

def main() -> None:
    """Entry point for Octavius
    """
    setup_logging(level="INFO" )   # aquí activas tu config global
    logger = logging.getLogger(__name__)
    logger.info("Arrancando Octavius...")
    p = pyaudio.PyAudio()

    devices = list_input_devices(p)
    for d in devices:
        print(f"[{d.index}] {d.name} | ch:{d.max_input_channels} sr:{int(d.default_sample_rate)}")

    path = Path("./audio_files/audio_grabado.wav")
    device_idx = resolve_input_device(p, "Focusrite")
    recorded_audio_path = record_voice(p, seconds=5,  output_path=str(path), input_device_index=device_idx)
    print(f"Recorded file saved in {path.resolve()}")

    data, samplerate = read_audio_metadata(recorded_audio_path)
    logger.info(
        f"Audio has been saved at {recorded_audio_path}. "
        f"With samplerate {samplerate} and audio is {'mono' if len(data.shape) == 1 else 'stereo'}"
        )


if __name__=='__main__':
    main()
