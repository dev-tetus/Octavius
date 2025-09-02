from dataclasses import dataclass
from typing import Protocol, Optional

@dataclass
class Transcription:
    text: str
    language: Optional[str] = None

class Transcriber(Protocol):
    def transcribe(self, wav_path: str, language: Optional[str] = None) -> Transcription: ...