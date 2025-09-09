from dataclasses import dataclass


@dataclass(frozen=True)
class LLMChunk:
    delta: str
    index: int
    is_final: bool = False