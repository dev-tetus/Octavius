from __future__ import annotations

# Subconjunto útil (añade más si los necesitas)
PA_ERROR_NAMES = {
    -10000: "paNotInitialized",
    -9999:  "paUnanticipatedHostError",
    -9998:  "paInvalidChannelCount",
    -9997:  "paInvalidSampleRate",
    -9996:  "paInvalidDevice",
    -9995:  "paInvalidFlag",
    -9994:  "paSampleFormatNotSupported",
    -9993:  "paBadIODeviceCombination",
    -9992:  "paInsufficientMemory",
    -9991:  "paBufferTooBig",
    -9990:  "paBufferTooSmall",
    -9989:  "paNullCallback",
    -9988:  "paBadStreamPtr",
    -9987:  "paTimedOut",
    -9986:  "paInternalError",
    -9985:  "paDeviceUnavailable",
}

def pa_error_info(exc: Exception) -> tuple[int | None, str, str]:
    """
    Returns (code, name, message) from a PyAudio/PortAudio exception.
    If code cannot be extracted, code=None and name="Unknown".
    """
    code = None
    msg = str(exc)
    if getattr(exc, "args", None):
        if len(exc.args) >= 1 and isinstance(exc.args[0], (int,)):
            code = exc.args[0]
        if len(exc.args) >= 2 and isinstance(exc.args[1], str):
            msg = exc.args[1]
    name = PA_ERROR_NAMES.get(code, "Unknown")
    return code, name, msg