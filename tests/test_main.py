#!/usr/bin/env python3
"""Tests for macrokeyboard.cli module."""
import os
import subprocess

import pytest


class TestConfig:
    """Tests for module-level configuration."""

    def test_voice_command_sentinel_no_config(self):
        """Should recognize bare voice_capture sentinel."""
        from macrokeyboard.cli import is_voice_command

        is_voice, config = is_voice_command(["voice_capture"])
        assert is_voice is True
        assert config == {}

    def test_voice_command_with_language_config(self):
        """Should recognize voice_capture with language config."""
        from macrokeyboard.cli import is_voice_command

        is_voice, config = is_voice_command(["voice_capture", {"language": "de"}])
        assert is_voice is True
        assert config == {"language": "de"}

    def test_voice_command_with_other_config(self):
        """Should forward arbitrary config dicts."""
        from macrokeyboard.cli import is_voice_command

        is_voice, config = is_voice_command(["voice_capture", {"language": "fr", "model": "large"}])
        assert is_voice is True
        assert config == {"language": "fr", "model": "large"}

    def test_non_voice_command_returns_false(self):
        """Non-voice commands should return (False, {})."""
        from macrokeyboard.cli import is_voice_command

        for cmd in [
            ["notify-send", "hello"],
            ["bash", "-c", "echo hi"],
            [],
        ]:
            is_voice, config = is_voice_command(cmd)
            assert is_voice is False
            assert config == {}

    def test_invalid_input_returns_false(self):
        """Non-list and malformed inputs should return (False, {})."""
        from macrokeyboard.cli import is_voice_command

        is_voice, config = is_voice_command("voice_capture")  # not a list
        assert is_voice is False
        assert config == {}

        is_voice, config = is_voice_command(["voice_capture", "extra"])  # string instead of dict
        assert is_voice is False
        assert config == {}

        is_voice, config = is_voice_command(["voice", "capture"])  # not the sentinel
        assert is_voice is False
        assert config == {}

    def test_dev_path_configured(self):
        """DEV_PATH should be a valid-looking device path."""
        from macrokeyboard.cli import DEV_PATH

        assert DEV_PATH.startswith("/dev/")
        assert "event" in DEV_PATH

    def test_voice_device_configured(self):
        """VOICE_DEVICE should be a valid ALSA device string."""
        from macrokeyboard.cli import VOICE_DEVICE

        assert "hw:" in VOICE_DEVICE

    def test_default_keymap(self):
        """KEYMAP should have expected default entries."""
        from macrokeyboard.cli import KEYMAP

        assert "KEY_A" in KEYMAP
        voice_keys = [k for k, v in KEYMAP.items() if isinstance(v, list) and len(v) >= 1 and v[0] == "voice_capture"]
        assert len(voice_keys) >= 2, "Should have at least 2 voice keys in KEYMAP"


class TestSetupLogging:
    """Tests for logging setup."""

    def test_setup_logging(self, tmp_path):
        """Should create log file and handlers."""
        from macrokeyboard.cli import setup_logging

        os.makedirs(str(tmp_path / "test_dir"), exist_ok=True)
        import macrokeyboard.cli as mod

        original_dir = mod._LOG_DIR
        mod._LOG_DIR = str(tmp_path / "test_dir")
        try:
            setup_logging()
            log_file = mod._LOG_FILE
            assert os.path.isfile(log_file)
        finally:
            mod._LOG_DIR = original_dir


class TestVoicePipeline:
    """Tests for voice pipeline functions."""

    def test_voice_command_detection_no_language(self):
        """Bare voice_capture returns empty config."""
        from macrokeyboard.cli import is_voice_command

        is_voice, config = is_voice_command(["voice_capture"])
        assert is_voice is True
        assert config == {}

    def test_voice_command_detection_language(self):
        """voice_capture with language config extracts it."""
        from macrokeyboard.cli import is_voice_command

        is_voice, config = is_voice_command(["voice_capture", {"language": "de"}])
        assert is_voice is True
        assert config["language"] == "de"

    def test_voice_command_detection_multi_language(self):
        """Should handle arbitrary config keys."""
        from macrokeyboard.cli import is_voice_command

        config = {"language": "pl", "foo": "bar"}
        is_voice, result = is_voice_command(["voice_capture", config])
        assert is_voice is True
        assert result == config


class TestStopAll:
    """Tests for the stop_all cleanup function."""

    def test_stop_all_cleans_subprocesses(self):
        """stop_all should clear the running dict."""
        from macrokeyboard.cli import running, stop_all

        running["TEST_KEY"] = subprocess.Popen(["sleep", "9999"])
        assert len(running) == 1

        stop_all()

        assert len(running) == 0
        # Cleanup again should be safe
        stop_all()


class TestHandleSigint:
    """Tests for signal handler."""

    def test_handle_sigint_exists(self):
        """Should have a signal handler registered."""
        import signal

        from macrokeyboard.cli import handle_sigint

        # Should raise SystemExit(0) because handle_sigint calls sys.exit(0)
        with pytest.raises(SystemExit) as exc_info:
            handle_sigint(signal.SIGINT, None)
        assert exc_info.value.code == 0


class TestMain:
    """Tests for the main function."""

    def test_main_exists(self):
        """main() function should be callable."""
        from macrokeyboard.cli import main

        assert callable(main)

    def test_cli_module_import(self):
        """Should be able to import macrokeyboard.cli."""
        import macrokeyboard.cli as cli

        assert hasattr(cli, "main")
        assert hasattr(cli, "KEYMAP")
        assert hasattr(cli, "DEV_PATH")
