from collections import defaultdict, deque
from typing import Deque, Dict, List, TYPE_CHECKING
from octavius.ports.conversation_store import ConversationStore

if TYPE_CHECKING:
    from octavius.domain.models.turn import Turn

class InMemoryConversationStore(ConversationStore):
    def __init__(self, max_turns: int = 20 ) -> None:
        self._by_cid: Dict[str, Deque["Turn"]] = defaultdict(lambda: deque(maxlen=max_turns))
    
    def append(self, conv_id: str, turn: "Turn") -> None:
        self._by_cid[conv_id].append(turn)
    
    def last_n(self, conv_id: str, n: int) -> List["Turn"]:
        dq = self._by_cid[conv_id]
        return list(dq)[-n:] if n<len(dq) else list(dq)
    def all(self, conv_id: str) -> List["Turn"]:
        return list(self._by_cid[conv_id])
    def count(self, conv_id: str) -> int:
        return len(self._by_cid[conv_id])
    def clear(self, conv_id: str) -> None:
        self._by_cid.pop(conv_id, None)
    