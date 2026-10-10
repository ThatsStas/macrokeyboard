### Macro Keyboard

This project transforms every USB keyboard into a macro keyboard which can run arbitrary scripts on key press (and kill them on release). It uses evdev to grab a device specified by /dev/input/ path and uses KEYMAP to create a mapping KEY <> script.

The keyboard is "grabbed" by evdev which prevents the keyboard from sending keys to the OS itself.

**Don't attach the script to your main keyboard. You won't be able to kill it afterwards.**

---

### Voice-to-Text Macro

Press a key → start recording (with a notification) → release key → transcribe via a self-hosted Whisper endpoint → copy to clipboard → paste at cursor.

**Setup:**

1. Install system dependencies:
   ```bash
   sudo apt install alsa-utils xdotool xclip
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your Whisper endpoint:
   ```bash
   export STT_ENDPOINT="http://your-whisper-host:port/v1/audio/transcriptions"
   export STT_MODEL="whisper-1"
   ```

4. Add a voice key to `KEYMAP` using the `['voice_capture']` sentinel:
   ```python
   KEYMAP = {
       'KEY_A': ['notify-send', 'hello world'],
       'KEY_F2': ['voice_capture'],  # voice macro trigger key
   }
   ```

5. Set the microphone device (edit `VOICE_DEVICE` in `run_macros.py`):
   ```python
   VOICE_DEVICE = "plughw:5,0"  # Logitech C920 webcam mic
   ```

   List available devices with `arecord -l`.

6. Run:
   ```bash
   python3 run_macros.py
   ```

**Configuration (in `run_macros.py`):**

| Variable | Purpose | Default |
|----------|---------|---------|
| `VOICE_DEVICE` | ALSA device string | `plughw:5,0` (C920 webcam) |
| `INSCRIPT` | Whisper/STT API URL | `http://localhost:8000/v1/audio/transcriptions` |

**Environment Variables:**

| Variable | Purpose | Default |
|----------|---------|---------|
| `STT_ENDPOINT` | Whisper/STT API URL (overrides INSCRIPT) | — |
| `STT_MODEL` | Model identifier | `whisper-1` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `MACRO_LOG_DIR` | Log file directory | script directory |

**Logging:**

Logs go to both stderr and `$MACRO_LOG_DIR/voice.log`. Set `LOG_LEVEL=DEBUG` for verbose output.
