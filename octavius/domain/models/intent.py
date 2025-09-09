from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass(frozen=True)
class Intent:
    name:str
    confidence: float
    slots: Dict[str, Any]  =field(default_factory=dict)
    