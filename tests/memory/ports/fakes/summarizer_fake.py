# tests/memory/ports/fakes/summarizer_fake.py
from dataclasses import dataclass
from typing import List

from octavius.memory.ports.summarizer import Summarizer


@dataclass
class FakeSummarizer(Summarizer):
    """
    Summarizer de prueba:
      - Cuenta cuántas veces se llamó.
      - Guarda el tamaño de la ventana recibida y los últimos parámetros.
      - Devuelve un resumen trivial: prior_summary | último_texto (si existen).
    """
    calls: int = 0
    last_history_len: int = 0
    last_prior_summary: str = ""
    last_target_tokens: int = 0
    raise_on_call: bool = False  # si quieres simular fallo en tests

    def summarize(self, history: List["Turn"], prior_summary: str, target_tokens: int) -> str:  # type: ignore[name-defined]
        if self.raise_on_call:
            raise RuntimeError("FakeSummarizer forced failure")

        self.calls += 1
        self.last_history_len = len(history)
        self.last_prior_summary = prior_summary
        self.last_target_tokens = target_tokens

        tail = history[-1].text.strip() if history else ""
        base = prior_summary.strip() if prior_summary else ""

        if base and tail:
            return f"{base}|{tail}"
        return base or tail
