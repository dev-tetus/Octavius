from __future__ import annotations
from enum import Enum

class TurnState(str, Enum):
    """High-level turn states for logging/telemetry."""
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"  # optional, used on exceptions
