# octavius/infrastructure/llm/gemini.py
from __future__ import annotations
import os
import logging
from typing import Iterator, Optional

from octavius.ports.llm import LLMClient
from octavius.domain.models.llm_objects import LLMChunk, LLMResponse

logger = logging.getLogger(__name__)

class GeminiClient(LLMClient):
    """Gemini adapter that preserves legacy behavior (system_prompt, temperature, max_tokens,
    thinking_config and Google Search grounding), while conforming to LLMClient port."""

    def __init__(self, settings) -> None:
        # settings.llm is expected; be defensive with getattr defaults
        self._s = settings
        self._client = None  # google.genai.Client
        self._types = None   # google.genai.types
        # Legacy defaults (used if settings does not define them)
        self._default_model = getattr(self._s, "model", "gemini-2.5-flash")
        self._default_temp = float(getattr(self._s, "temperature", 0.6))
        self._default_max = getattr(self._s, "max_tokens", 350)
        self._system_prompt = getattr(
            self._s,
            "system_prompt",
            (
                "Eres Octavius, un asistente conversacional claro y amable."
                "Responde con texto compacto para leer en voz alta y evita tecnicismos innecesarios. "
                "No quiero saltos de línea ni nada, quiero reducir al máximo el número de tokens devueltos"
            ),
        )
        self._thinking_budget = int(getattr(self._s, "thinking_budget", 50))
        self._enable_search = bool(getattr(self._s, "enable_search", True))
        self._api_key_env = getattr(self._s, "api_key_env", None)  # e.g. "GEMINI_API_KEY"

    # ------------- lifecycle -------------

    def open(self) -> None:
        """Create the underlying google.genai client and preload types."""
        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except Exception as e:
            raise RuntimeError("google-genai SDK not available. pip install google-genai") from e

        # Resolve API key (env)
        api_key = None
        if self._api_key_env:
            api_key = os.getenv(self._api_key_env)
        # Fallbacks used by your legacy client
        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Falta la API key: define GEMINI_API_KEY o GOOGLE_API_KEY (o configura api_key_env).")

        # New SDK uses Client(); it reads env automatically, no need to pass api_key here.
        self._client = genai.Client()
        self._types = types
        logger.info("GeminiClient open: model=%s", self._default_model)

    def close(self) -> None:
        """SDK does not require explicit close; keep for symmetry."""
        self._client = None
        self._types = None

    # ------------- non-streaming -------------

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        self._ensure_ready()
        cfg = self._build_config(system_prompt)
        try:
            resp = self._client.models.generate_content(  # type: ignore[attr-defined]
                model=self._default_model,
                contents=(prompt or "").strip(),
                config=cfg,
            )
            self._log_provider_meta(resp)
            text = self._safe_text(resp)
            usage = getattr(resp, "usage_metadata", None) or getattr(resp, "usage", None)
            used = getattr(usage, "total_token_count", None) if usage else None
            finish = getattr(getattr(resp, "candidates", [None])[0], "finish_reason", None)
            finish_name = getattr(finish, "name", str(finish)) if finish is not None else None
            return LLMResponse(text=text or "", usage_tokens=used, finish_reason=finish_name)
        except Exception as e:
            logger.warning("Fallo en GeminiClient.generate: %s", e)
            return LLMResponse(text="Estoy teniendo un problema para responder ahora mismo; probemos de nuevo en un momento.")

    # ------------- streaming -------------

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[LLMChunk]:
        self._ensure_ready()
        cfg = self._build_config(system_prompt)
        idx = 0
        try:
            stream = self._client.models.generate_content(  # type: ignore[attr-defined]
                model=self._default_model,
                contents=(prompt or "").strip(),
                config=cfg,
                stream=True,
            )
            for ev in stream:
                piece = self._safe_text(ev)
                if not piece:
                    continue
                yield LLMChunk(delta=piece, index=idx, is_final=False)
                idx += 1
        except Exception as e:
            logger.warning("Fallo en GeminiClient.stream: %s", e)
        # Signal completion
        yield LLMChunk(delta="", index=idx, is_final=True)

    # ------------- helpers -------------

    def _build_config(self, system_prompt: Optional[str]):
        """Build GenerateContentConfig with system instruction, temperature, max tokens,
        thinking_config and (optionally) Google Search grounding tool."""
        assert self._types is not None
        base_instruction = (system_prompt or self._system_prompt or "").strip()

        tools = None
        if self._enable_search:
            # Enable Google Search grounding tool (same as legacy)
            tools = [self._types.Tool(google_search=self._types.GoogleSearch())]

        cfg = self._types.GenerateContentConfig(
            system_instruction=base_instruction if base_instruction else None,
            temperature=self._default_temp,
            max_output_tokens=self._default_max,
            thinking_config={"thinking_budget": self._thinking_budget},
            tools=tools,
        )
        return cfg

    def _ensure_ready(self) -> None:
        if self._client is None or self._types is None:
            raise RuntimeError("Call open() before using GeminiClient")

    def _safe_text(resp) -> str:
        """Extract text robustly from google.genai responses (final and streaming events)."""
        # Fast path: resp.text property
        try:
            if hasattr(resp, "text"):
                t = getattr(resp, "text")
                if isinstance(t, str):
                    return t.strip()
        except Exception:
            pass
        # Candidates path
        try:
            cands = getattr(resp, "candidates", None) or []
            parts_text: list[str] = []
            for cand in cands:
                content = getattr(cand, "content", None)
                if content is not None:
                    parts = getattr(content, "parts", None) or []
                    for part in parts:
                        t = getattr(part, "text", None)
                        if t:
                            parts_text.append(str(t))
            if parts_text:
                return "\n".join(p.strip() for p in parts_text if p).strip()
        except Exception:
            pass
        return ""

    def _log_provider_meta(resp) -> None:
        """Best-effort logging of finish_reason, safety ratings and usage, at DEBUG level."""
        try:
            cand0 = getattr(resp, "candidates", [None])[0]
            if cand0 is not None:
                fr = getattr(cand0, "finish_reason", None)
                if fr:
                    logger.debug("Gemini finish_reason: %s", getattr(fr, "name", fr))
                sr = getattr(cand0, "safety_ratings", None)
                if sr:
                    logger.debug("Gemini safety_ratings: %s", sr)
        except Exception:
            pass
        try:
            um = getattr(resp, "usage_metadata", None) or getattr(resp, "usage", None)
            if um:
                logger.debug("Gemini usage: %s", um)
        except Exception:
            pass
