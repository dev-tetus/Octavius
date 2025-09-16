from __future__ import annotations
from typing import List, TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from octavius.domain.models.turn import Turn




class ConversationStore(Protocol):
    """Groups Turn by conv_id and preserves appended orded.
    """
    def append(self, conv_id: str, turn: "Turn") -> None: ...
    def last_n(self, conv_id: str, n: int)-> List["Turn"]: ...
    def all(self, conv_id: str) -> List["Turn"]: ...
    def count(self, conv_id:str) -> int: ...
    def clear(self, conv_id:str) -> None: ...

    