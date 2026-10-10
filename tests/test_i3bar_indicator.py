#!/usr/bin/env python3
"""Tests for i3bar_indicator.py."""
import pytest


class TestVoiceIndicator:
    """Tests for VoiceIndicator class."""

    def test_initialization(self):
        """Should initialize without errors."""
        from macrokeyboard.i3bar_indicator import VoiceIndicator

        vi = VoiceIndicator()
        assert vi is not None

    def test_start_returns_true_on_success(self, mock_notify_send):
        """Should return True when notify-send succeeds."""
        from macrokeyboard.i3bar_indicator import VoiceIndicator

        vi = VoiceIndicator()
        result = vi.start()
        assert result is True

    def test_stop_returns_none(self):
        """Should not return anything on stop."""
        from macrokeyboard.i3bar_indicator import VoiceIndicator

        vi = VoiceIndicator()
        result = vi.stop()
        assert result is None

    def test_show_error_sends_notification(self, mock_notify_send):
        """Should send a critical notification on error."""
        from macrokeyboard.i3bar_indicator import VoiceIndicator

        vi = VoiceIndicator()
        vi.show_error("Something went wrong")
        assert vi.initialized is False  # notify-send doesn't set initialized

    def test_show_success_sends_notification(self, mock_notify_send):
        """Should send a notification with the transcribed text."""
        from macrokeyboard.i3bar_indicator import VoiceIndicator

        vi = VoiceIndicator()
        vi.show_success("Hello world")
        assert vi.initialized is False

    def test_show_success_truncates_long_text(self, mock_notify_send):
        """Should only display first 100 chars of long text."""
        import subprocess

        captured_args = []

        def capture(*args, **kwargs):
            captured_args.append(args)
            return type("P", (), {"returncode": 0})()

        from macrokeyboard.i3bar_indicator import VoiceIndicator
        import macrokeyboard.i3bar_indicator as mod

        original_run = mod.subprocess.Popen
        mod.subprocess.Popen = capture
        try:
            long_text = "a" * 200
            vi = VoiceIndicator()
            vi.show_success(long_text)
            # notify-send format: (cmd, -u, urgency, title, message)
            # captured_args[0][0] = args tuple
            last_call = captured_args[-1][0]
            assert last_call[4] == long_text[:100]
        finally:
            mod.subprocess.Popen = original_run

    def test_initialized_always_false(self):
        """notify-send mode always returns False for initialized."""
        from macrokeyboard.i3bar_indicator import VoiceIndicator

        vi = VoiceIndicator()
        assert vi.initialized is False

    def test_stop_on_already_stopped(self):
        """Should not error when stopping twice."""
        from macrokeyboard.i3bar_indicator import VoiceIndicator

        vi = VoiceIndicator()
        vi.stop()
        vi.stop()  # Second stop should not raise
