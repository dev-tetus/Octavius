from __future__ import annotations
from typing import Protocol, Iterator, Optional
from octavius.domain.models.llm_objects import LLMChunk, LLMResponse

class LLMClient(Protocol):
    """LLM boundary that works with a single prompt string and optional system prompt.
    Adapts to providers (Gemini, etc.) behind this interface.
    """

    # lifecycle
    def open(self) -> None: ...
    def close(self) -> None: ...

    # non-streaming
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse: ...

    # streaming
    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[LLMChunk]: ...
