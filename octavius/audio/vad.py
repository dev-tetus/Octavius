import math
import time
from typing import Iterable, List, Tuple
from octavius.config.settings import Settings
import webrtcvad

from dataclasses import dataclass
import logging
logger = logging.getLogger(__name__)
@dataclass(frozen=True)
class VadParams:
    aggressiveness: int
    frame_ms: int
    silence_ms: int
    pre_speech_ms: int
    sample_rate: int     # viene de settings.audio.sample_rate
    max_record_ms: int

def make_vad_params(settings: Settings) -> VadParams:
    v, a = settings.vad, settings.audio
    return VadParams(
        aggressiveness=v.aggressiveness,
        frame_ms=v.frame_ms,
        silence_ms=v.silence_ms,
        pre_speech_ms=v.pre_speech_ms,
        sample_rate=a.sample_rate,
        max_record_ms=v.max_record_ms,
    )

class WebRTCVAD:
    """
    Detector de actividad de voz basado en WebRTC.
    - NO define defaults: todo viene en VadParams (derivado de Settings).
    - Trabaja con frames PCM16 MONO de longitud EXACTA:
        frame_bytes = (sample_rate * frame_ms / 1000) * 2
    - Devuelve (frames_recortados, parado_por_silencio)
    """

    def __init__(self, params: VadParams) -> None:
        # Validaciones mínimas (fail-fast)
        if params.sample_rate not in (8000, 16000, 32000, 48000):
            raise ValueError("VAD soporta sample_rate 8k/16k/32k/48k.")
        if params.frame_ms not in (10, 20, 30):
            raise ValueError("VAD frame_ms debe ser 10, 20 o 30 ms.")
        if not (0 <= params.aggressiveness <= 3):
            raise ValueError("VAD aggressiveness debe ser 0..3.")

        self.params = params
        self.vad = webrtcvad.Vad(params.aggressiveness)

        # Tamaño exacto de frame en bytes (PCM16 mono = 2 bytes por muestra)
        self.frame_bytes = int(params.sample_rate * params.frame_ms / 1000) * 2

        # Cuentas derivadas
        self._silence_frames_needed = max(1, math.ceil(params.silence_ms / params.frame_ms))
        self._prespeech_frames = max(1, math.ceil(params.pre_speech_ms / params.frame_ms))
        self._max_frames = max(1, math.ceil(params.max_record_ms / params.frame_ms))

    def is_speech(self, frame: bytes) -> bool:
        """Devuelve True si el frame contiene voz (según WebRTC)."""
        if len(frame) != self.frame_bytes:
            # Frame incorrecto: lo ignoramos para evitar falsos negativos.
            return False
        return self.vad.is_speech(frame, self.params.sample_rate)

    def capture_until_silence(
        self, frames: Iterable[bytes]
    ) -> Tuple[List[bytes], bool]:
        """
        Consume un iterador/generador de frames (bytes) y devuelve:
          - lista de frames recortados que incluyen pre_speech + habla,
          - bandera True si la parada fue por silencio, False si por límite (max_record_ms).

        Contrato del iterador:
          - Debe producir frames PCM16 MONO de longitud EXACTA = self.frame_bytes.
        """
        pre_roll: List[bytes] = []   # buffer previo (pre_speech)
        captured: List[bytes] = []   # frames finales a devolver
        started = False
        silence_count = 0
        total_frames = 0
        deadline = time.monotonic() + (self.params.max_record_ms / 1000.0)
        while True:
            try:
                fr = next(frames)  # consumimos explícitamente el generador
            except StopIteration:
                # El generador se agotó
                logger.debug("VAD: generador se agotó. %d frames", total_frames)
                return (captured if started else pre_roll), False
            total_frames += 1
            if time.monotonic() >= deadline:
                logger.debug("VAD: timeout por reloj tras %d frames", total_frames)
                return (captured if started else pre_roll), False
            if len(fr) != self.frame_bytes:
                continue

            talking = self.vad.is_speech(fr, self.params.sample_rate)
            if not started:
                # Antes de detectar voz, mantenemos un buffer pre-roll
                pre_roll.append(fr)
                if len(pre_roll) > self._prespeech_frames:
                    pre_roll.pop(0)

                if talking:
                    # Arranque de voz: volcamos pre-roll + primer frame de voz
                    captured.extend(pre_roll)
                    captured.append(fr)
                    started = True
                    silence_count = 0
            else:
                captured.append(fr)
                if talking:
                    silence_count = 0
                else:
                    silence_count += 1
                    if silence_count >= self._silence_frames_needed:
                        logger.debug("VAD: salida por silencio tras %d frames", total_frames)
                        # Parada por silencio sostenido
                        return captured, True

            # Seguridad: límite duro de grabación
            if total_frames >= self._max_frames:
                logger.debug("VAD: salida por tope de frames (%d)", total_frames)
                return (captured if started else pre_roll), False

           