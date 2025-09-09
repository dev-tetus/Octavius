from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LLMResponse:
    text: str
    usage_tokens: Optional[int] = None
    finish_reason: Optional[str] = None