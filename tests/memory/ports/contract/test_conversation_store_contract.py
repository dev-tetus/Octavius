import pytest
from typing import Callable
from octavius.memory.ports.conversation_store import ConversationStore
from octavius.memory.model.turn import Turn
from octavius.memory.model.role import Role

@pytest.mark.contract
class ConversationStoreContract:
    """Contrato que toda implementación de ConversationStore debe cumplir."""

    @pytest.fixture
    def make_store(self) -> Callable[[], ConversationStore]:
        """Cada implementación concreta debe sobrescribir este fixture."""
        raise NotImplementedError

    def _mk(self, i: int) -> Turn:
        return Turn(role=Role.user, text=f"t{i}")

    def test_append_order_last_n_all_count_clear(self, make_store):
        store = make_store()
        cid = "c1"
        for i in range(1, 7):
            store.append(cid, self._mk(i))

        assert store.count(cid) == 6
        assert [t.text for t in store.all(cid)] == ["t1", "t2", "t3", "t4", "t5", "t6"]
        assert [t.text for t in store.last_n(cid, 3)] == ["t4", "t5", "t6"]

        store.clear(cid)
        assert store.count(cid) == 0
        assert store.all(cid) == []

    def test_last_n_more_than_available_returns_all(self, make_store):
        store = make_store()
        cid = "c2"
        for i in range(1, 4):
            store.append(cid, self._mk(i))
        assert [t.text for t in store.last_n(cid, 10)] == ["t1", "t2", "t3"]
