from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from .role import Role
from .utterance import Utterance

@dataclass
class Turn:
    role: Role
    text: str
    created_at: datetime = field(default_factory= datetime.now)
    tokens: int = 0
    utterance : Optional[Utterance] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
