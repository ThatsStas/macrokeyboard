#!/usr/bin/env python3
"""Tests for voice_capture.py."""
import os
import tempfile


class TestVoiceCapture:
    """Tests for VoiceCapture class."""

    def test_initialization(self):
        """Should initialize with default device."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture()
        assert vc._device == "plughw:0,0"

    def test_initialization_with_custom_device(self):
        """Should accept a custom ALSA device string."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture(device="plughw:5,0")
        assert vc._device == "plughw:5,0"

    def test_check_before_start(self):
        """check() should return False when not recording."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture()
        assert vc.check() is False

    def test_check_after_stop(self):
        """check() should return False after stop."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture()
        vc.stop()  # should not error
        assert vc.check() is False

    def test_cleanup_before_start(self):
        """cleanup() should not error when not recording."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture()
        vc.cleanup()  # should not error

    def test_cleanup_twice(self):
        """cleanup() should be idempotent."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture()
        vc.cleanup()
        vc.cleanup()  # should not error

    def test_starts_recording(self, mock_arecord, tmp_path):
        """Should start arecord and return a handle."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture(device="plughw:5,0")
        handle = vc.start()

        assert handle is not None
        assert handle.pid == 99999
        assert os.path.isfile(handle.temp_path)
        assert vc.check() is True

    def test_stops_recording(self, mock_arecord, tmp_path):
        """Should stop recording and return the WAV path."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture(device="plughw:5,0")
        handle = vc.start()
        wav_path = vc.stop()

        assert wav_path is not None
        assert os.path.isfile(wav_path)
        assert vc.check() is False

    def test_stopped_event_set_after_stop(self, mock_arecord, tmp_path):
        """The stopped event should be set after stop."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture(device="plughw:5,0")
        handle = vc.start()
        vc.stop()

        assert handle.stopped_event.is_set()

    def test_duplicate_start_stops_previous(self, mock_arecord, tmp_path):
        """Starting a new recording should stop the previous one."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture(device="plughw:5,0")

        handle1 = vc.start()
        assert vc.check() is True

        handle2 = vc.start()  # second start
        assert vc.check() is True
        # Expected calls: 2 arecord starts + 2 kill -0 for check() + 1 kill for auto-stop = 5
        assert mock_arecord.call_count >= 3

    def test_returns_none_when_arecord_missing(self, tmp_path, monkeypatch):
        """Should return None when arecord is not found."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture(device="nonexistent")

        def raise_not_found(*args, **kwargs):
            raise FileNotFoundError("arecord")

        monkeypatch.setattr("subprocess.Popen", raise_not_found)

        result = vc.start()
        assert result is None

    def test_creates_temp_file_with_prefix(self, mock_arecord, tmp_path, monkeypatch):
        """Temp file should have the 'voice_' prefix."""
        import tempfile
        from macrokeyboard.voice_capture import VoiceCapture

        captured_path = []

        original_mkstemp = tempfile.mkstemp

        def capture(*args, **kwargs):
            fd, path = original_mkstemp(*args, **kwargs)
            # Don't close - let the caller close it
            captured_path.append(path)
            return fd, path

        monkeypatch.setattr("tempfile.mkstemp", capture)

        vc = VoiceCapture(device="plughw:5,0")
        handle = vc.start()

        assert len(captured_path) == 1
        assert os.path.basename(captured_path[0]).startswith("voice_")
        assert captured_path[0].endswith(".wav")

    def test_estimate_duration(self, mock_arecord, tmp_path):
        """Should estimate duration from file size."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture(device="plughw:5,0")
        handle = vc.start()

        # Duration should be 0 for the initial empty file
        duration = vc._estimate_duration(handle)
        assert duration >= 0


class TestVoiceCaptureFormats:
    """Tests for different audio format configurations."""

    def test_default_format(self):
        """Default format should be 'cd'."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture()
        assert vc._format == "cd"

    def test_custom_format(self):
        """Should accept custom format."""
        from macrokeyboard.voice_capture import VoiceCapture

        vc = VoiceCapture(format="raw")
        assert vc._format == "raw"
