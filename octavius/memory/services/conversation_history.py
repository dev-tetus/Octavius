from typing import List, Optional
from octavius.memory.ports.conversation_store import ConversationStore
from octavius.memory.ports.summarizer import Summarizer
from octavius.memory.model.turn import Turn
from octavius.memory.dto.context import Context

class ConversationHistory:
    """Conversation handler for:
        - Adding a Turn to conversation
        - Build context
        - Clean history
    """
    def __init__(
        self,
        store: ConversationStore,
        conv_id: str,
        summarizer: Optional[Summarizer], 
        summary_every_n_turns: int = 0, 
        summary_target_tokens: int = 200
    ) -> None:
        self._store = store
        self._cid = conv_id
        self._summarizer = summarizer
        self._summary_every_n_turns = summary_every_n_turns
        self._summary_target_tokens = summary_target_tokens
        self._summary = ""
        self._since_last_summary = 0

    def append(self, turn: Turn) -> None:
        if turn is None or not isinstance(turn.text, str) or not turn.text.strip():
            return
        self._store.append(self._cid, turn)

        if self._summary_every_n_turns > 0 and self._summarizer is not None:
            self._since_last_summary += 1
            if self._since_last_summary >= self._summary_every_n_turns:
                k = max(self._summary_every_n_turns * 2, 8)
                history_window = self._store.last_n(self._cid, k)
                try:
                    self._summary = self._summarizer.summarize(
                        history=history_window,
                        prior_summary=self._summary,
                        target_tokens=self._summary_target_tokens
                    )
                finally:
                    self._since_last_summary = 0
    
    def build_context(self, max_tokens: int) -> Context:
        
        window = self._store.last_n(self._cid, 64)          #We ask for the 64 last turns of conversation
        acc, selected = 0, []
        for t in reversed(window):
            cost = t.tokens if t.tokens > 0 else max(1, len(t.text) // 4)   #~ chars/4
            if acc + cost > max_tokens:
                break
            selected.append(t)
            acc+=cost
        selected.reverse()
        return Context(summary=self._summary, window=window, token_count=acc)
    
    def clear(self) -> None:
        self._store.clear(self._cid)
        self._summary = ""
        self._since_last_summary = 0
    
    def turns(self) -> List["Turn"]:
        return self._store.all(conv_id=self._cid)
    
    def get_summary(self) -> str:
        return self._summary
    
    def set_summary(self, text:str) -> None:
        self._summary = text or ""
