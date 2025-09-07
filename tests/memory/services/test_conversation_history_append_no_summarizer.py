from octavius.memory.infra.in_memory_conversation_store import InMemoryConversationStore
from octavius.memory.services.conversation_history import ConversationHistory
from octavius.memory.model.turn import Turn
from octavius.memory.model.role import Role


def test_append_ignores_blank_text_and_preserves_order():
    store = InMemoryConversationStore(max_turns=10)
    h = ConversationHistory(store=store, conv_id="c1", summarizer=None)

    h.append(Turn(role=Role.user, text="   "))
    assert h.turns() == []

    h.append(Turn(role=Role.user, text="a"))
    h.append(Turn(role=Role.assistant, text="b"))
    h.append(Turn(role=Role.user, text="c"))

    texts = [t.text for t in h.turns()]
    assert texts == ["a", "b", "c"]


def test_get_set_summary_without_summarizer_and_clear():
    store = InMemoryConversationStore(max_turns=10)
    h = ConversationHistory(store=store, conv_id="c2",summarizer=None)

    assert h.get_summary() == ""

    h.set_summary("resumen manual")
    assert h.get_summary() == "resumen manual"

    h.append(Turn(role=Role.user, text="hola"))
    assert h.turns() != []
    h.clear()
    assert h.turns() == []
    assert h.get_summary() == ""
