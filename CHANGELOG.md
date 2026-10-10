# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-10

### Added

- Core macro keyboard engine using `evdev` to grab keyboard devices and run scripts on key press/release
- Voice-to-text macro: press a key to record, release to transcribe and paste
- ALSA audio recording via `arecord` with configurable device
- Whisper/STT endpoint integration (configurable URL, no auth required)
- Clipboard copy and xdotool-based paste with chunked typing support
- i3bar/notify-send recording indicator
- Comprehensive logging to stderr and file
- Error notifications via `notify-send`
- Full test suite with pytest
- Modern Python project setup with `pyproject.toml`
- CLI entry point via `macrokeyboard` command

### Configuration

- `DEV_PATH`: Keyboard device path (e.g. `/dev/input/by-id/...`)
- `KEYMAP`: Key-to-command mapping
- `VOICE_DEVICE`: ALSA device for recording (e.g. `plughw:5,0`)
- `INSCRIPT`: Default STT endpoint URL
- `STT_ENDPOINT` / `STT_MODEL`: Environment variable overrides

### Requirements

- System: `alsa-utils`, `xdotool`, `xclip` (optional)
- Python: `evdev`, `requests`
