from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from octavius.memory.model.turn import Turn




class ConversationStore(ABC):
    """Groups Turn by conv_id and preserves appended orded.
    """
    @abstractmethod
    def append(self, conv_id: str, turn: "Turn") -> None: ...
    @abstractmethod
    def last_n(self, conv_id: str, n: int)-> List["Turn"]: ...
    @abstractmethod
    def all(self, conv_id: str) -> List["Turn"]: ...
    @abstractmethod
    def count(self, conv_id:str) -> int: ...
    @abstractmethod
    def clear(self, conv_id:str) -> None: ...
    