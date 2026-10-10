#!/usr/bin/env python3
"""Macro keyboard CLI — keyboard event dispatcher with voice-to-text support."""
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time

# Package imports
from macrokeyboard.voice_capture import VoiceCapture
from macrokeyboard.i3bar_indicator import VoiceIndicator
from macrokeyboard.stt_client import transcribe as stt_transcribe
from macrokeyboard.paste_text import copy_and_paste
from evdev import InputDevice, categorize, ecodes


# ============================================================================
# Configuration
# ============================================================================

DEV_PATH = "/dev/input/by-id/usb-You_Streamdeck-event-kbd"

# Log file path
_LOG_DIR = os.environ.get("MACRO_LOG_DIR", os.path.dirname(os.path.abspath(__file__)))
_LOG_FILE = os.path.join(_LOG_DIR, "voice.log")

# Voice command sentinel
VOICE_COMMAND = ["voice_capture"]

# Voice device (ALSA)
VOICE_DEVICE = "plughw:5,0"

# Default STT endpoint
INSCRIPT = "http://10.0.0.93:9001/v1/audio/transcriptions"

# Default KEYMAP — customize as needed.
# Voice keys: ['voice_capture'] or ['voice_capture', {'language': 'de'}]
# KEYMAP = {
#     "KEY_A": ["notify-send", "hello world"],
#     "KEY_F2": ["voice_capture"],
#     "KEY_F3": ["voice_capture", {'language': 'de'}],
# }

KEYMAP = {
    "KEY_A": ["notify-send", "hello world"],
    "KEY_PASTE": ["voice_capture"],
    "KEY_CUT": ["voice_capture", {'language': 'de'}],
}


# ============================================================================
# Logging
# ============================================================================


def setup_logging():
    """Configure logging to both stderr and a log file."""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    os.makedirs(_LOG_DIR, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)

    try:
        file_handler = logging.FileHandler(_LOG_FILE)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        logging.getLogger().info("Logging to %s", _LOG_FILE)
    except OSError as e:
        logging.warning("Could not open log file %s: %s", _LOG_FILE, e)


# ============================================================================
# Globals
# ============================================================================

running = {}
voice_processes = {}
voice_capture = VoiceCapture(device=VOICE_DEVICE)
i3bar_indicator = VoiceIndicator()
device = None


# ============================================================================
# Notifications
# ============================================================================


def notify_error(title, message):
    """Send a critical i3/notification popup."""
    try:
        subprocess.run(
            ["notify-send", "-u", "critical", title, message],
            capture_output=True,
            timeout=3,
        )
    except Exception as e:
        logging.warning("Failed to send notification: %s", e)


# ============================================================================
# Voice pipeline
# ============================================================================


def run_voice_pipeline(keyname, wav_path, lang_config):
    """Transcribe → copy → paste. Runs in a background thread.

    Args:
        keyname: Key that triggered this.
        wav_path: Path to recorded WAV file.
        lang_config: Dict with language hint, e.g. {'language': 'de'}.
    """
    logging.info("[VOICE] %s → starting transcription pipeline", keyname)

    language = lang_config.get("language") if lang_config else None

    try:
        i3bar_indicator.stop()

        logging.info("[VOICE] %s → submitting to STT endpoint%s",
                     keyname, f" (language={language})" if language else "")
        text = stt_transcribe(wav_path, default_endpoint=INSCRIPT, language=language)

        if not text:
            logging.warning("[VOICE] %s → empty transcription", keyname)
            i3bar_indicator.show_error("Empty transcription result")
            copy_and_paste("")
            voice_processes.pop(keyname, None)
            return

        logging.info("[VOICE] %s → transcribed: %s", keyname, text)
        copy_and_paste(text)
        logging.info("[VOICE] %s → done", keyname)
        i3bar_indicator.show_success(text)

    except FileNotFoundError as e:
        logging.error("[VOICE] %s → %s", keyname, e)
        i3bar_indicator.show_error(f"File not found: {e}")
    except Exception as e:
        logging.error("[VOICE] %s → pipeline error: %s", keyname, e, exc_info=True)
        i3bar_indicator.show_error(f"Error: {e}")
    finally:
        voice_processes.pop(keyname, None)
        if wav_path and os.path.isfile(wav_path):
            try:
                os.unlink(wav_path)
                logging.info("[VOICE] %s → cleaned up %s", keyname, wav_path)
            except OSError:
                pass


def is_voice_command(cmd):
    """Check if a command is the voice_capture sentinel.

    Returns a tuple (is_voice, config) where config is a dict of options
    (e.g. {'language': 'de'}) or empty dict if none specified.
    """
    if not isinstance(cmd, list):
        return False, {}

    # Exactly ['voice_capture'] — voice with no config
    if cmd == VOICE_COMMAND:
        return True, {}

    # ['voice_capture', {...}] — voice with options
    if len(cmd) == 2 and cmd[0] == "voice_capture" and isinstance(cmd[1], dict):
        return True, cmd[1]

    return False, {}


# ============================================================================
# Key event handlers
# ============================================================================


def on_key_down(keyname, cmd):
    """Handle key press."""
    is_voice, lang_config = is_voice_command(cmd)

    if is_voice:
        logging.info("[VOICE] %s pressed → start recording%s",
                     keyname, f" (language={lang_config.get('language')})" if lang_config else "")

        if keyname in voice_processes:
            logging.warning("[VOICE] %s already has an active voice process", keyname)
            voice_processes[keyname]["capture"].cleanup()
            i3bar_indicator.stop()

        handle = voice_capture.start()
        if not handle:
            logging.error("[VOICE] %s → failed to start recording", keyname)
            i3bar_indicator.show_error("Failed to start recording — check microphone")
            return

        voice_processes[keyname] = {
            "handle": handle,
            "capture": voice_capture,
            "lang_config": lang_config,
        }
        i3bar_indicator.start()
        logging.info("[VOICE] %s → recording started (PID %d)", keyname, handle.pid)
    else:
        if keyname not in running:
            logging.info("[%s] pressed → start script", keyname)
            running[keyname] = subprocess.Popen(cmd)


def on_key_up(keyname, cmd):
    """Handle key release."""
    is_voice, lang_config = is_voice_command(cmd)

    if is_voice:
        logging.info("[VOICE] %s released → stop recording", keyname)

        entry = voice_processes.get(keyname)
        if not entry:
            logging.warning("[VOICE] %s released but no active recording", keyname)
            return

        capture = entry["capture"]
        handle = entry["handle"]

        wav_path = capture.stop()
        if not wav_path:
            logging.error("[VOICE] %s → failed to stop recording", keyname)
            i3bar_indicator.show_error("Failed to stop recording")
            voice_processes.pop(keyname, None)
            i3bar_indicator.stop()
            return

        thread = threading.Thread(
            target=run_voice_pipeline,
            args=(keyname, wav_path, lang_config),
            daemon=True,
            name=f"voice-pipeline-{keyname}",
        )
        thread.start()
        logging.info("[VOICE] %s → pipeline thread started", keyname)
    else:
        proc = running.pop(keyname, None)
        if proc:
            logging.info("[%s] released → stop script", keyname)
            proc.terminate()


# ============================================================================
# Cleanup
# ============================================================================


def stop_all():
    """Terminate all subprocesses and clean up voice state."""
    for key, proc in list(running.items()):
        logging.info("Stopping subprocess for %s", key)
        try:
            proc.terminate()
        except Exception as e:
            logging.error("Error terminating %s: %s", key, e)
    running.clear()

    try:
        voice_capture.cleanup()
        logging.info("Voice recording stopped")
    except Exception as e:
        logging.error("Error stopping voice capture: %s", e)

    voice_processes.clear()

    try:
        i3bar_indicator.stop()
        logging.info("i3bar indicator hidden")
    except Exception as e:
        logging.error("Error hiding indicator: %s", e)


def handle_sigint(signum, frame):
    """Graceful shutdown on SIGINT/SIGTERM."""
    logging.info("Received signal %s — shutting down...", signum)
    stop_all()
    global device
    if device:
        try:
            device.ungrab()
            logging.info("Device ungrabbed.")
        except Exception:
            pass
    sys.exit(0)


# ============================================================================
# Main
# ============================================================================


def main():
    """Entry point."""
    setup_logging()
    logging.info("Macro keyboard started — monitoring %s", DEV_PATH)

    global device
    device = InputDevice(DEV_PATH)
    logging.info("Opened %s (%s)", device.path, device.name)

    device.grab()
    logging.info("Keyboard grabbed — key events intercepted")

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    try:
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                keyevent = categorize(event)
                keyname = (
                    keyevent.keycode[0]
                    if isinstance(keyevent.keycode, (list, tuple))
                    else keyevent.keycode
                )

                if keyname not in KEYMAP:
                    continue

                cmd = KEYMAP[keyname]

                if keyevent.keystate == keyevent.key_down:
                    on_key_down(keyname, cmd)
                elif keyevent.keystate == keyevent.key_up:
                    on_key_up(keyname, cmd)

    finally:
        logging.info("Shutdown — cleaning up...")
        stop_all()
        try:
            device.ungrab()
            logging.info("Device ungrabbed.")
        except Exception:
            pass


if __name__ == "__main__":
    main()
