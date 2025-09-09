from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from octavius.domain.models.turn import Turn


class Summarizer(ABC):
    @abstractmethod
    def summarize(self, history: list["Turn"], prior_summary:str, target_tokens: int) -> str: ...
    