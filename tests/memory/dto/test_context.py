# tests/memory/dto/test_context.py
from octavius.memory.dto.context import Context
from octavius.memory.model.turn import Turn
from octavius.memory.model.role import Role
import logging
log = logging.getLogger(__name__)

def test_to_prompt_string_empty_returns_empty_string():
    ctx = Context(summary="", window=[], token_count=0)
    assert ctx.to_prompt() == ""


def test_to_prompt_string_with_summary_and_roles():
    turns = [
        Turn(role=Role.user, text="hola"),
        Turn(role=Role.assistant, text="qué tal"),
    ]
    ctx = Context(summary="resumen corto", window=turns, token_count=6)

    s = ctx.to_prompt(include_roles=True)

    assert "Previous summary: resumen corto" in s
    assert "User: hola" in s
    assert "Assistant: qué tal" in s
    assert s.strip().endswith("Assistant:")


def test_to_prompt_string_without_roles_uses_raw_text_only():
    turns = [
        Turn(role=Role.user, text="hola"),
        Turn(role=Role.assistant, text="qué tal"),
    ]
    ctx = Context(summary="resumen corto", window=turns, token_count=6)

    s = ctx.to_prompt(include_roles=False)

    assert "User: " not in s and "Assistant: " not in s
    assert "hola" in s and "qué tal" in s
    assert s.strip().endswith("Assistant:")


def test_to_prompt_string_with_tool_role_falls_back_to_literal_value():
    turns = [Turn(role=Role.tool, text="resultado de herramienta")]
    ctx = Context(summary="", window=turns, token_count=3)

    s = ctx.to_prompt(include_roles=True)

    assert "Tool: resultado de herramienta" in s
    assert s.strip().endswith("Assistant:")


def test_token_count_is_preserved_not_used_in_formatting():
    turns = [Turn(role=Role.user, text="abc")]
    ctx = Context(summary="", window=turns, token_count=123)

    s = ctx.to_prompt()
    assert ctx.token_count == 123
    assert "123" not in s
