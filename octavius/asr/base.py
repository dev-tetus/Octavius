from dataclasses import dataclass
from typing import Protocol, Optional
import numpy as np
@dataclass
class Transcription:
    text: str
    language: Optional[str] = None

class Transcriber(Protocol):
    def transcribe_from_saved_audio(self, wav_path: str, language: Optional[str] = None) -> Transcription: ...

    def transcribe(self, audio: np.array)->Transcription:... 