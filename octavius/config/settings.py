from functools import lru_cache
import os
import platform
from pydantic import BaseModel, field_validator, model_validator
from typing import Any, Dict, Literal, Optional
from pathlib import Path
import yaml


class AppSettings(BaseModel):
    name:str ="octavius"
    env: Literal["dev", "test","prod"] = "dev"

class PathsSettings(BaseModel):
    base_dir: Path
    logs_dir: Path
    audio_dir: Path
    @field_validator("base_dir", check_fields=True)
    def _to_path(cls, v): return Path(v).resolve()
    @field_validator("logs_dir","audio_dir", check_fields=True)
    def _rel(cls, v): return Path(v)
    def finalize(self):
        self.logs_dir = (self.base_dir / self.logs_dir).resolve()
        self.audio_dir = (self.base_dir / self.audio_dir).resolve()
class LoggingSettings(BaseModel):
    level: Literal["DEBUG","INFO","WARN","ERROR"] = "INFO"
    file: str = "octavius.log"
    rotation_mb: int = 10

class AudioSettings(BaseModel):
    input_device: str = "default"
    sample_rate: int = 16000
    channels: Literal[1,2] = 1
    chunk_size: int = 1024

class AsrSettings(BaseModel):
    engine: Literal["whisper"] = "whisper"
    implementation: Literal["faster-whisper", "whisper.cpp", "openai"] = "faster-whisper"
    model_id: Literal["tiny", "base", "small", "medium", "large-v3"] = "small"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    compute_type: Literal["int8", "int8_float32", "int16", "float16", "float32"] = "int8"
    language: Literal["es", "en", "fr"] = "es"
    task: Literal["transcribe", "translate"] = "transcribe"
    chunk_seconds: int = 30

    @field_validator("chunk_seconds")
    @classmethod
    def _val_chunk(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("asr.chunk_seconds debe ser > 0")
        return v

class VadSettings(BaseModel):
    enabled: bool = True
    aggressiveness: int = 2
    frame_ms: int = 30
    silence_ms: int = 800
    pre_speech_ms: int = 300
    max_record_ms: int = 15000

    @field_validator("aggressiveness")
    @classmethod
    def _val_aggr(cls, v: int) -> int:
        if v not in (0, 1, 2, 3):
            raise ValueError("vad.aggressiveness must be between 0..3")
        return v

    @field_validator("frame_ms")
    @classmethod
    def _val_frame(cls, v: int) -> int:
        if v not in (10, 20, 30):
            raise ValueError("vad.frame_ms must be 10, 20 or 30 ms")
        return v

    @field_validator("silence_ms", "pre_speech_ms", "max_record_ms")
    @classmethod
    def _val_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("vad.* must be > 0")
        return v

class LLMSettings(BaseModel):
    provider: Literal["gemini", "openai", "ollama", "groq"] = "gemini"
    model: str = "gemini-2.5-flash"
    temperature: float = 0.6
    max_tokens: int = 350
    system_prompt: Optional[str] = None
    api_key_env: str = "GEMINI_API_KEY"  # name of env var holding the key
    
    @field_validator("temperature")
    @classmethod
    def _val_temp(cls, v: float) -> float:
        if not (0.0 <= v <= 2.0):
            raise ValueError("llm.temperature debe estar entre 0.0 y 2.0")
        return v

    @field_validator("max_tokens")
    @classmethod
    def _val_tokens(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("llm.max_tokens debe ser > 0")
        return v

class Settings(BaseModel):
    app: AppSettings
    paths: PathsSettings
    logging: LoggingSettings
    audio: AudioSettings
    asr: AsrSettings
    vad: VadSettings
    llm: LLMSettings
    def ensure_directories(self):
        self.paths.finalize()
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        self.paths.audio_dir.mkdir(parents=True, exist_ok=True)
    
    @model_validator(mode="after")
    def _check_vad_compat(self):
        # Coherencia VAD ↔ audio
        if self.vad.enabled:
            if self.audio.channels != 1:
                raise ValueError("VAD requiere audio.channels = 1 (mono).")
            if self.audio.sample_rate not in (8000, 16000, 32000, 48000):
                raise ValueError("VAD soporta sample_rate 8k/16k/32k/48k.")
        return self

PROFILES_DIR = Path(__file__).parent / "profiles"

def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _detect_default_profile() -> str:
    text = f'{" ".join(platform.uname())} and {platform.machine()}'.lower()
    print(text)
    if "orangepi" in text or "rk3588" in text: return "opi5"
    if "raspberry" in text or any(t in text for t in ["armv7","aarch64","arm64"]): return "rpi4"
    if "windows" in text: return "pc"
    return "pc"

def _profile_file(profile: str) -> Path:
    return PROFILES_DIR / f"device.{profile}.yaml"

def _env_overrides(prefix="OCTAVIUS__") -> Dict[str,Any]:
    out: Dict[str,Any] = {}
    for k,v in os.environ.items():
        if not k.startswith(prefix): continue
        path = k[len(prefix):].lower().split("__")
        ref = out
        for part in path[:-1]:
            ref = ref.setdefault(part, {})
        if v.isdigit(): val: Any = int(v)
        elif v.lower() in {"true","false"}: val = v.lower()=="true"
        else: val = v
        ref[path[-1]] = val
    return out

def _deep_merge(a: Dict[str,Any], b: Dict[str,Any]) -> Dict[str,Any]:
    out = dict(a)
    for k,v in b.items():
        out[k] = _deep_merge(a[k], v) if isinstance(v,dict) and k in a and isinstance(a[k],dict) else v
    return out

def _load_layers(profile:Optional[str])-> Dict[str,Any]:
    cfg = _load_yaml(PROFILES_DIR / "base.yaml")
    p = profile or os.getenv("OCTAVIUS_PROFILE") or _detect_default_profile()
    pf = _profile_file(p)
    if pf.exists(): cfg = _deep_merge(cfg, _load_yaml(pf))
    cfg = _deep_merge(cfg, _env_overrides())
    return cfg


@lru_cache(maxsize=1)
def get_settings(profile: Optional[str] = None) -> Settings:
    raw = _load_layers(profile)
    s = Settings(**raw)
    s.ensure_directories()
    return s