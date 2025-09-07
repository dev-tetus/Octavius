# octavius/llm/gemini_client.py
from __future__ import annotations
import datetime
import logging
import os
from typing import Optional

from google import genai
from google.genai import types  # GenerateContentConfig y tipos relacionados

log = logging.getLogger(__name__)

class GeminiClient:
    """
    Adaptador mínimo para conversación texto→texto usando Google GenAI SDK.
    Cumple la firma LLMFn: __call__(user_text: str, language: Optional[str]) -> str
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.6,
        max_tokens: int = 350,
        system_prompt: Optional[str] = None,
    ) -> None:
        # El SDK leerá la API key del entorno (GEMINI_API_KEY o GOOGLE_API_KEY) si no se pasa.
        # Validamos para evitar errores silenciosos.
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            raise RuntimeError("Falta la API key: define GEMINI_API_KEY o GOOGLE_API_KEY en el entorno.")

        self.client = genai.Client()  # usa la key del entorno
        self.model = model

        base_instruction = system_prompt or (
            "Eres Octavius, un asistente conversacional claro y amable."
            "Responde con texto compacto para leer en voz alta y evita tecnicismos innecesarios. "
            "No quiero saltos de línea ni nada, quiero reducir al máximo el número de tokens devueltos"
        )
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        
        self.base_config = types.GenerateContentConfig(
            system_instruction=base_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
            thinking_config={"thinking_budget": 50},
            tools=[grounding_tool]
        )

    def __call__(self, user_text: str, language: Optional[str] = None) -> str:
        text = (user_text or "").strip()
        if not text:
            return "¿Podrías repetirlo con otras palabras?"
        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=text,
                config=self.base_config,
            )
            try:
                if getattr(resp, "candidates", None):
                    fr = getattr(resp.candidates[0], "finish_reason", None)
                    log.debug("Gemini finish_reason: %s", getattr(fr, "name", fr))
                    sr = getattr(resp.candidates[0], "safety_ratings", None)
                    if sr:
                        # Evita volcados enormes
                        log.debug("Gemini safety_ratings (c0): %s", sr)
                um = getattr(resp, "usage_metadata", None) or getattr(resp, "usage", None)
                if um:
                    # Campos típicos: prompt_token_count, candidates_token_count, total_token_count
                    try:
                        log.debug("Gemini usage: %s", um)
                    except Exception:
                        pass
            except Exception:
                pass
            # Atajo de la SDK: resp.text trae el primer texto útil.
            out = (getattr(resp, "text", None) or "").strip()
            if not out and getattr(resp, "candidates", None):
                parts_text: list[str] = []
                for cand in resp.candidates or []:
                    fr = getattr(cand, "finish_reason", None)
                    if fr:
                        log.debug("Gemini finish_reason: %s", getattr(fr, "name", fr))
                    content = getattr(cand, "content", None)
                    if content and getattr(content, "parts", None):
                        for part in content.parts:
                            t = getattr(part, "text", None)
                            if t:
                                parts_text.append(t)
                out = "\n".join(p.strip() for p in parts_text if p).strip()
            if not out:
                try:
                    sr = getattr(resp, "candidates", [None])[0]
                    sr = getattr(sr, "safety_ratings", None)
                    if sr:
                        log.debug("Gemini safety_ratings: %s", sr)
                except Exception:
                    pass
                return "No estoy seguro ahora mismo; ¿puedes reformularlo?"

            return out
        except Exception as e:
            log.warning("Fallo en GeminiClient: %s", e)
            return "Estoy teniendo un problema para responder ahora mismo; probemos de nuevo en un momento."
