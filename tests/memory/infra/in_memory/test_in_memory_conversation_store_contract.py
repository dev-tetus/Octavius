import pytest
from tests.memory.ports.contract.test_conversation_store_contract import ConversationStoreContract
from octavius.memory.infra.in_memory_conversation_store import InMemoryConversationStore

class TestInMemoryConversationStore(ConversationStoreContract):
    @pytest.fixture
    def make_store(self):
        return lambda: InMemoryConversationStore(max_turns=50)
