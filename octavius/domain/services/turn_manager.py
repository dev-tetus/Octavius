from __future__ import annotations
import signal
from dataclasses import dataclass
from typing import Callable, Optional, Iterator
import logging

from octavius.domain.models.utterance import Utterance
from octavius.ports.audio_source import AudioSource
from octavius.ports.vad import VADPort
from octavius.ports.asr import ASRPort
from octavius.ports.llm import LLMClient
from octavius.domain.services.conversation_history import ConversationHistory
from octavius.domain.models.turn import Turn, Role
from octavius.domain.models.llm_objects import LLMResponse
from octavius.domain.models.turn_state import TurnState

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class TurnResult:
    asr_text: Optional[str]
    llm_text: Optional[str]
    segment_ms: Optional[int]
    raw_asr: Optional[Utterance] = None
    raw_llm: Optional[LLMResponse] = None

class TurnManager:
    """Single-turn orchestrator following your class diagram."""

    def __init__(
        self,
        *,
        audio: AudioSource,
        vad: VADPort,
        asr: ASRPort,
        llm_client: LLMClient,
        history: ConversationHistory,
        llm_system_prompt: Optional[str] = None,
        llm_max_tokens_context: int = 2048,
    ) -> None:
        self._audio = audio
        self._vad = vad
        self._asr = asr
        self._llm = llm_client
        self._history = history
        self._sys_prompt = llm_system_prompt
        self._ctx_budget = llm_max_tokens_context
        self._log = logger
        self._state: TurnState = TurnState.IDLE

    # -------- state handling --------

    @property
    def state(self) -> TurnState:
        return self._state

    def _set_state(self, new_state: TurnState) -> None:
        """Atomically set and log state; fire callback if provided."""
        if new_state is self._state:
            return
        self._state = new_state
        self._log.info("[state] %s", new_state.value)

    def run_once(self) -> TurnResult:
        frames = self._audio.capture_stream()
        return self._run_once_with_frames(frames)
    
        # ---------------- Long-running loop ----------------

    def run_forever(
        self,
        *,
        on_result: Optional[Callable[[TurnResult], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        install_signal_handlers: bool = True,
    ) -> None:
        """Keep running turns (listen → VAD → ASR → LLM) until SIGINT/SIGTERM.

        Args:
            on_result: optional callback invoked after each successful turn.
            on_error: optional callback invoked on exceptions (loop continues).
            install_signal_handlers: if True, temporarily install SIGINT/SIGTERM
                handlers that request a graceful stop (recommended for CLI apps).
        """
        assert self._audio is not None and self._vad is not None, "Dependencies not set"
        stop_flag = {"stop": False}

        def _mark_stop(signum, frame):
            self._log.info("Received signal %s → stopping after current turn", signum)
            stop_flag["stop"] = True

        prev_handlers = {}
        if install_signal_handlers:
            for sig_name in ("SIGINT", "SIGTERM"):
                sig = getattr(signal, sig_name, None)
                if sig is not None:
                    prev_handlers[sig] = signal.getsignal(sig)
                    signal.signal(sig, _mark_stop)

        # Reuse a single frames iterator bound to the open AudioSource.
        self._set_state(TurnState.IDLE)
        frames: Iterator[bytes] = self._audio.capture_stream()
        try:
            while not stop_flag["stop"]:
                try:
                    result = self._run_once_with_frames(frames)
                    if on_result:
                        on_result(result)
                except KeyboardInterrupt:
                    # Fallback if signal handlers are not installed.
                    self._log.info("KeyboardInterrupt → stopping")
                    break
                except Exception as e:
                    self._set_state(TurnState.ERROR)
                    self._log.exception("Unexpected error in run_forever loop: %s", e)
                    if on_error:
                        try:
                            on_error(e)
                        except Exception:
                            self._log.exception("on_error callback raised")
                    self._set_state(TurnState.IDLE)
                    # continue loop after reporting the error
        finally:
            # Restore previous handlers
            if install_signal_handlers:
                for sig, handler in prev_handlers.items():
                    try:
                        signal.signal(sig, handler)
                    except Exception:
                        pass

    # -------------- internal helper (shared by run_once / run_forever) -----

    def _run_once_with_frames(self, frames: Iterator[bytes]) -> TurnResult:
        """Core single-turn logic that consumes a persistent frames iterator."""
        self._set_state(TurnState.LISTENING)
        segment = self._vad.capture_until_silence(frames)  # RecordingSegment

        if not segment.pcm:
            self._log.warning("Empty segment from VAD; returning early")
            self._set_state(TurnState.IDLE)
            return TurnResult(asr_text=None, llm_text=None, segment_ms=None)
        self._set_state(TurnState.TRANSCRIBING)
        transcription = self._asr.transcribe(segment)  # Transcription
        user_text = transcription.raw_text or ""
        self._history.append(Turn(role=Role.user, text=user_text))
        self._set_state(TurnState.PROCESSING)
        ctx = self._history.build_context(max_tokens=self._ctx_budget)
        prompt = ctx.to_prompt()
        self._log.info("%s",prompt)

        llm_resp = self._llm.generate(prompt, system_prompt=self._sys_prompt)
        assistant_text = llm_resp.text or ""
        self._history.append(Turn(role=Role.assistant, text=assistant_text))
        self._log.info("ASR: %s", user_text)
        self._log.info("LLM: %s", assistant_text)
        self._set_state(TurnState.IDLE)
        return TurnResult(
            asr_text=user_text,
            llm_text=assistant_text,
            segment_ms=segment.duration_ms,
            raw_asr=transcription,
            raw_llm=llm_resp,
        )

