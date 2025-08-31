from dataclasses import dataclass
from multiprocessing import Value
from typing import List, Optional, Union
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


def resolve_input_device(
    p: pyaudio.PyAudio,
    identifier: Union[int,str]
) -> int:
    """Resolves device input

    Args:
        p (pyaudio.PyAudio): PyAudio instance
        identifier (Union[int,str]): Device identifier, could be an integer or string 

    Returns:
        int: Returns index for device in host
    """

    devices = list_input_devices(p)

    #if identifier is an integer
    if isinstance(identifier,int):
        if(d.index == identifier for d in devices):
            return identifier
        raise ValueError(f"Identifier {identifier} not a valid input device")
    
    #identifier is a string
    device_name = identifier.lower()
    candidates = [d for d in devices if device_name in d.name.lower()]
    if not candidates:
        raise ValueError(f"Could not find an input device containing \"'{identifier}'\"")
    
    candidates.sort(key=lambda d: (d.default_sample_rate, d.max_input_channels), reverse=True)
    best = candidates[0]
    return best.index