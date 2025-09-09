from dataclasses import dataclass
@dataclass(frozen=True)
class VadParams:
    aggressiveness: int
    frame_ms: int
    silence_ms: int
    pre_speech_ms: int
    sample_rate: int    
    max_record_ms: int