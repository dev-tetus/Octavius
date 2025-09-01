from datetime import datetime
import logging
from pathlib import Path
import pyaudio
from .audio.devices import list_input_devices, resolve_input_device
from .audio.io import record_voice, read_audio_metadata
from .config.settings import get_settings
from .utils.logging import setup_logging

def main() -> None:
    """Entry point for Octavius
    """
    settings = get_settings()

    setup_logging(
        level=settings.logging.level,
        log_dir=settings.paths.logs_dir,
        filename=settings.logging.file,
        max_bytes=settings.logging.rotation_mb*1024*1024
        )

    logger = logging.getLogger(__name__)
    logger.info("Booting Octavius...")

    p = pyaudio.PyAudio()

    # devices = list_input_devices(p)
    # for d in devices:
    #     print(f"[{d.index}] {d.name} | ch:{d.max_input_channels} sr:{int(d.default_sample_rate)}")

    target_device = settings.audio.input_device
    device_idx = resolve_input_device(p, target_device)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = settings.paths.audio_dir/f"octavius_{ts}.wav"
    
    recorded_audio_path = record_voice(p, seconds=5,  output_path=str(path), input_device_index=device_idx, desired_rate=settings.audio.sample_rate,channels=settings.audio.channels)
    print(f"Recorded file saved in {path.resolve()}")

    data, samplerate = read_audio_metadata(recorded_audio_path)
    logger.info(
        f"Audio has been saved at {recorded_audio_path}. "
        f"With samplerate {samplerate} and audio is {'mono' if len(data.shape) == 1 else 'stereo'}"
        )
    p.terminate()


if __name__=='__main__':
    raise SystemExit(main())
