#!/usr/bin/env python3
"""Tests for paste_text.py."""
import pytest
from macrokeyboard.paste_text import copy_and_paste, copy_to_clipboard, paste_at_cursor


class TestCopyToClipboard:
    """Tests for copy_to_clipboard function."""

    def test_returns_false_when_no_xclip(self, no_xclip):
        """Should return False when xclip is not available."""
        result = copy_to_clipboard("test text")
        assert result is False

    def test_returns_true_on_success(self, mock_xclip, mock_xclip_process):
        """Should return True when xclip succeeds."""
        result = copy_to_clipboard("test text")
        assert result is True

    def test_returns_false_on_timeout(self, no_xclip, mock_xclip, mock_xclip_timeout):
        """Should return False when xclip times out."""
        result = copy_to_clipboard("test text")
        assert result is False

    def test_returns_false_on_error(self, no_xclip, mock_xclip):
        """Should return False when xclip returns non-zero."""
        fake_result = type("P", (), {"returncode": 1, "stderr": b"error"})()
        import subprocess

        def mock_run(*args, **kwargs):
            return fake_result

        import macrokeyboard.paste_text as mod

        original_run = subprocess.run
        subprocess.run = mock_run
        try:
            result = copy_to_clipboard("test text")
            assert result is False
        finally:
            subprocess.run = original_run


class TestPasteAtCursor:
    """Tests for paste_at_cursor function."""

    def test_returns_false_when_no_xdotool(self, no_xdotool):
        """Should return False when xdotool is not available."""
        result = paste_at_cursor("test text")
        assert result is False

    def test_returns_false_for_empty_text(self, mock_xdotool):
        """Should return False when text is empty."""
        result = paste_at_cursor("")
        assert result is False

    def test_returns_true_on_success(self, mock_xdotool, mock_xdotool_process):
        """Should return True when xdotool succeeds."""
        result = paste_at_cursor("hello world")
        assert result is True

    def test_handles_long_text(self, mock_xdotool, mock_xdotool_process):
        """Should handle long text (multi-chunk)."""
        long_text = "a" * 200  # 200 chars = 4 chunks of 50
        result = paste_at_cursor(long_text)
        assert result is True

    def test_returns_false_on_xdotool_error(self, mock_xdotool, mock_xdotool_error):
        """Should return False when xdotool fails."""
        result = paste_at_cursor("test")
        assert result is False

    def test_returns_false_on_xdotool_timeout(self, mock_xdotool, mock_xdotool_timeout):
        """Should return False when xdotool times out."""
        result = paste_at_cursor("test")
        assert result is False


class TestCopyAndPaste:
    """Tests for copy_and_paste function (combined)."""

    def test_returns_false_for_empty_text(self, no_xclip, no_xdotool):
        """Should return False when text is empty."""
        result = copy_and_paste("")
        assert result is False

    def test_returns_true_when_both_succeed(self, mock_xclip, mock_xclip_process, mock_xdotool, mock_xdotool_process):
        """Should return True when both operations succeed."""
        result = copy_and_paste("hello")
        assert result is True

    def test_returns_true_when_only_paste_succeeds(self, no_xclip, mock_xdotool, mock_xdotool_process):
        """Should return True when only paste succeeds."""
        result = copy_and_paste("hello")
        assert result is True

    def test_returns_false_when_only_clipboard_succeeds(self, mock_xclip, mock_xclip_process, no_xdotool):
        """Should return False (clipboard only, no paste)."""
        result = copy_and_paste("hello")
        assert result is False

    def test_returns_false_when_neither_succeeds(self, no_xclip, no_xdotool):
        """Should return False when both tools are unavailable."""
        result = copy_and_paste("hello")
        assert result is False
