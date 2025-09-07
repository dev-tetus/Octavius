from dataclasses import dataclass
from typing import List
from ..model.turn import Turn

@dataclass
class Context:
    summary: str
    window: List["Turn"]
    token_count: int = 0

    def to_prompt(self, include_roles: bool = True) -> str:
        if not self.window and not self.summary:
            return ""
        lines = []
        if self.summary:
            lines.append(f"Previous summary: {self.summary}")
        for t in self.window:
            if include_roles:
                who = {"user":"User", "assistant": "Assistant"}.get(t.role.value, t.role.value)
                lines.append(f"{who}: {t.text}")
            else:
                lines.append(t.text)
        lines.append("Assistant:")
        return "\n".join(lines)