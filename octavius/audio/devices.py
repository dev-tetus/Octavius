from dataclasses import dataclass
from typing import List, Optional
import pyaudio

@dataclass(frozen=True)
class DeviceInfo:
    """Device info data class
    """
    index: int
    name: str
    max_input_channels: int
    default_sample_rate: float

def list_input_devices(p: pyaudio.PyAudio) -> List[DeviceInfo]:
    """List input devices for host

    Args:
        p (pyaudio.PyAudio): PyAudio instance that provides 
        methods and attributes to record and read audio 

    Returns:
        List[DeviceInfo]: List of input devices for host
    """
    devices: List[DeviceInfo] = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get("maxInputChannels", 0) > 0:
            devices.append(
                DeviceInfo(
                    index=i,
                    name=str(info.get("name", f"dev-{i}")),
                    max_input_channels=int(info.get("maxInputChannels", 0)),
                    default_sample_rate=float(info.get("defaultSampleRate", 16000.0)),
                )
            )
    return devices

def get_default_input_device(py_audio: pyaudio.PyAudio) -> dict:
    """Returs default host input device

    Args:
        p (pyaudio.PyAudio): PyAudio instance

    Returns:
        dict: Dictionarry with default host device information
    """
    return py_audio.get_default_input_device_info()
