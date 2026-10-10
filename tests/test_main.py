#!/usr/bin/env python3
"""Tests for macrokeyboard.cli module."""
import os
import subprocess

import pytest


class TestConfig:
    """Tests for module-level configuration."""

    def test_voice_command_sentinel(self):
        """Should recognize voice_capture sentinel."""
        from macrokeyboard.cli import is_voice_command

        assert is_voice_command(["voice_capture"]) is True
        assert is_voice_command(["notify-send", "hello"]) is False
        assert is_voice_command(["bash", "-c", "echo hi"]) is False
        assert is_voice_command([]) is False
        assert is_voice_command("voice_capture") is False  # not a list

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
        assert "KEY_F2" in KEYMAP


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

    def test_voice_command_detection(self):
        """is_voice_command should correctly identify voice commands."""
        from macrokeyboard.cli import is_voice_command

        assert is_voice_command(["voice_capture"]) is True
        assert is_voice_command(["other_command"]) is False
        assert is_voice_command(["voice_capture", "extra"]) is False
        assert is_voice_command(["voice", "capture"]) is False


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
