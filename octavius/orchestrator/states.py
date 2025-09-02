from enum import Enum, auto

class TMState(Enum):
    IDLE = auto()        # Sistema cargado pero aún no escuchando
    LISTENING = auto()   # Esperando comienzo de voz (VAD)
    RECORDING = auto()   # Capturando audio hasta silencio o timeout
    PROCESSING = auto()  # ASR (y luego LLM en modo charla) en progreso
    SPEAKING = auto()    # Reproduciendo TTS (si está habilitado)
    STOPPED = auto()   