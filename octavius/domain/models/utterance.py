from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from .intent import Intent

@dataclass(frozen=True)
class Utterance:
    raw_text: str
    lang: str = "auto"
    intent: Optional[Intent]  =None
    slots: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    asr_confidence: Optional[float] = None