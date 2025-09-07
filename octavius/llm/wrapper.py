import logging
log = logging.getLogger(__name__)
from typing import Optional, Callable

from ..memory.model.turn import Turn
from ..memory.model.role import Role
from octavius.memory.services.conversation_history import ConversationHistory

def make_llm_with_memory(
    inner_llm: Callable[[str, Optional[str]], str],
    history: ConversationHistory,
    max_ctx_tokens: int = 1200,
) -> Callable[[str, Optional[str]], str]:
    """
    Devuelve un llm_fn compatible con tu pipeline, pero con memoria:
      - append del usuario
      - build_context + render_prompt
      - llamada al LLM con el prompt completo
      - append del asistente
    """
    def llm_mem(user_text: str, language: Optional[str]) -> str:
        # 1) Guardar turno del usuario
        history.append(Turn(role=Role.user, text=user_text))

        # 2) Construir contexto (ventana + summary)
        ctx = history.build_context(max_tokens=max_ctx_tokens)
        prompt = ctx.to_prompt(include_roles=True)

        # 3) Llamar al LLM con el PROMPT COMPLETO (incluye el último user ya)
        log.info("CTX(tokens=%s):\n%s", ctx.token_count, prompt)
        reply = inner_llm(prompt, language)

        # 4) Guardar turno del asistente
        history.append(Turn(role=Role.assistant, text=reply))

        # 5) Devolver respuesta al pipeline (TTS / UI)
        return reply

    return llm_mem
