from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

import pyaudio
import logging

logger = logging.getLogger(__name__)


# --- Data model --------------------------------------------------------------

@dataclass(frozen=True)
class DeviceInfo:
    index: int
    name: str
    max_input_channels: int
    default_sample_rate: float
    host_api: str


# --- Discovery ---------------------------------------------------------------

def _host_api_name(p: pyaudio.PyAudio, host_api_index: int) -> str:
    try:
        return p.get_host_api_info_by_index(host_api_index)["name"]
    except Exception:
        return "unknown"


def list_input_devices(p: pyaudio.PyAudio) -> List[DeviceInfo]:
    devices: List[DeviceInfo] = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        max_in = int(info.get("maxInputChannels", 0))
        if max_in > 0:
            devices.append(
                DeviceInfo(
                    index=i,
                    name=str(info.get("name", f"dev-{i}")),
                    max_input_channels=max_in,
                    default_sample_rate=float(info.get("defaultSampleRate", 16000.0)),
                    host_api=_host_api_name(p, info.get("hostApi", 0)),
                )
            )
    return devices


def get_default_input_device(p: pyaudio.PyAudio) -> Optional[DeviceInfo]:
    try:
        d = p.get_default_input_device_info()
    except Exception:
        return None
    return DeviceInfo(
        index=int(d["index"]),
        name=str(d.get("name", "default")),
        max_input_channels=int(d.get("maxInputChannels", 0)),
        default_sample_rate=float(d.get("defaultSampleRate", 16000.0)),
        host_api=_host_api_name(p, d.get("hostApi", 0)),
    )


# --- Capability probing ------------------------------------------------------

def _supports(p: pyaudio.PyAudio, dev_index: int, rate: int, channels: int) -> bool:
    try:
        ok = p.is_format_supported(
            rate,
            input_device=dev_index,
            input_channels=channels,
            input_format=pyaudio.paInt16,
        )
        return bool(ok)
    except Exception:
        return False


# --- Scoring & resolution ----------------------------------------------------

def _build_host_rank(preference: List[str]) -> dict:
    # Crea un ranking {nombre: peso} a partir del orden dado
    rank = {}
    weight = len(preference)
    for name in preference:
        rank[name] = weight
        weight -= 1
    return rank


def _score_device(
    p: pyaudio.PyAudio,
    dev: DeviceInfo,
    desired_rate: Optional[int],
    desired_channels: Optional[int],
    host_rank: dict,
) -> int:
    score = 0
    score += host_rank.get(dev.host_api, 0)

    if desired_rate:
        if int(dev.default_sample_rate) == int(desired_rate):
            score += 2
        elif abs(dev.default_sample_rate - desired_rate) <= 2000:
            score += 1

    if desired_rate and desired_channels:
        if _supports(p, dev.index, desired_rate, desired_channels):
            score += 3

    if dev.max_input_channels >= 1:
        score += 1

    return score


def resolve_input_device(
    p: pyaudio.PyAudio,
    identifier: Union[int, str, None],
    desired_rate: Optional[int] = 48000,
    desired_channels: Optional[int] = 1,
    host_api_preference: Optional[List[str]] = None,
    allow_system_default: bool = True,
) -> int:
    """
    Resuelve el índice del mejor dispositivo de entrada.

    - `host_api_preference`: orden de preferencia de Host API.
      EJ para tu caso: ["MME", "Windows DirectSound", "Windows WASAPI", "Windows WDM-KS"]
      (por defecto usamos este orden).

    - Si `identifier` es int → se respeta tal cual.
    - Si es "default" → devuelve el índice por defecto del sistema (si se permite).
    - Si es str → filtra por substring del nombre y elige por score.
    - Si es None → elige el mejor por score entre todos.
    """
    devices = list_input_devices(p)
    if not devices:
        raise ValueError("No hay dispositivos de entrada disponibles.")

    if isinstance(identifier, int):
        if any(d.index == identifier for d in devices):
            return identifier
        raise ValueError(f"Identifier {identifier} no es un índice válido de entrada.")

    # Ranking de host APIs
    if host_api_preference is None:
        host_api_preference = ["MME", "Windows DirectSound", "Windows WASAPI", "Windows WDM-KS"]
    host_rank = _build_host_rank(host_api_preference)

    # (2) Default del sistema
    if isinstance(identifier, str) and identifier.strip().lower() == "default":
        if allow_system_default:
            d = get_default_input_device(p)
            if d is not None:
                logger.info("Usando 'default': #%d | %s | %s | defSR=%.0f",
                            d.index, d.name, d.host_api, d.default_sample_rate)
                return d.index
            logger.warning("No hay 'default' del sistema; eligiendo por score…")
        else:
            logger.info("Ignorando 'default' por configuración; eligiendo por score…")

    if isinstance(identifier, str) and identifier.strip():
        needle = identifier.lower()
        candidates = [d for d in devices if needle in d.name.lower()]
        if not candidates:
            raise ValueError(f"No se encontró dispositivo que contenga «{identifier}».")
    else:
        candidates = devices

    # (4) Ordena por score
    scored = [(_score_device(p, d, desired_rate, desired_channels, host_rank), d) for d in candidates]
    scored.sort(key=lambda t: t[0], reverse=True)
    best_score, best = scored[0]

    return best.index
