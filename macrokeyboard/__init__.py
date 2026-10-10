"""MacroKeyboard — transform any USB keyboard into a macro keyboard."""
from macrokeyboard.voice_capture import VoiceCapture
from macrokeyboard.paste_text import copy_and_paste, paste_at_cursor, copy_to_clipboard
from macrokeyboard.stt_client import transcribe
from macrokeyboard.i3bar_indicator import VoiceIndicator

__all__ = [
    "VoiceCapture",
    "VoiceIndicator",
    "copy_and_paste",
    "paste_at_cursor",
    "copy_to_clipboard",
    "transcribe",
]
