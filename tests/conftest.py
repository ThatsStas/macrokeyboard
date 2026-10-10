#!/usr/bin/env python3
"""Shared fixtures for all tests."""
import os
import tempfile
import shutil

import pytest


@pytest.fixture()
def tmp_wav_file():
    """Create a minimal valid WAV file for testing."""
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="test_")
    os.close(fd)

    # Write a minimal WAV header (44 bytes)
    with open(path, "wb") as f:
        f.write(b"RIFF")  # RIFF header
        f.write(b"\x00" * 4)  # file size placeholder
        f.write(b"WAVE")  # WAVE format
        f.write(b"fmt ")  # fmt chunk
        f.write(b"\x10" * 4)  # chunk size (16)
        f.write(b"\x01\x00")  # audio format (PCM)
        f.write(b"\x01\x00")  # channels (1)
        f.write(b"\x80\x3c\x00\x00")  # sample rate (15360)
        f.write(b"\x00\x70\x01\x00")  # byte rate (28800)
        f.write(b"\x02\x00")  # block align (2)
        f.write(b"\x10\x00")  # bits per sample (16)
        f.write(b"data")  # data chunk
        f.write(b"\x00" * 4)  # chunk size placeholder

    yield path

    os.unlink(path)


@pytest.fixture()
def tmp_json_file(tmp_path):
    """Create a temporary JSON file."""
    path = tmp_path / "test.json"
    yield path


@pytest.fixture()
def i3bar_config():
    """Return a minimal i3bar config dict for testing."""
    return {
        "sections": [
            {"name": "network", "full_text": "WiFi", "separator": True},
            {"name": "sys_tray", "full_text": "", "separator": False},
        ],
    }


@pytest.fixture()
def env_patch(monkeypatch):
    """Convenience fixture to patch environment variables."""

    def _patch(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)

    return _patch


@pytest.fixture()
def mock_xclip(monkeypatch):
    """Mock xclip availability."""
    monkeypatch.setattr("os.path.isfile", lambda path: True if path == "/usr/bin/xclip" else False)


@pytest.fixture()
def no_xclip(monkeypatch):
    """Ensure xclip appears unavailable."""
    monkeypatch.setattr("os.path.isfile", lambda path: False)


@pytest.fixture()
def mock_xdotool(monkeypatch):
    """Mock xdotool availability."""
    monkeypatch.setattr("os.path.isfile", lambda path: True if path == "/usr/bin/xdotool" else False)


@pytest.fixture()
def no_xdotool(monkeypatch):
    """Ensure xdotool appears unavailable."""
    monkeypatch.setattr("os.path.isfile", lambda path: False)


@pytest.fixture()
def mock_notify_send(monkeypatch):
    """Mock subprocess for notify-send."""
    mock = monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: type("P", (), {"returncode": 0})(),
    )
    return mock


@pytest.fixture()
def mock_xclip_process(monkeypatch):
    """Mock xclip subprocess call."""
    mock = monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: type("P", (), {"returncode": 0, "stderr": b""})(),
    )
    return mock


@pytest.fixture()
def mock_xclip_timeout(monkeypatch):
    """Mock xclip subprocess call with timeout."""
    import subprocess as sp

    def _raise(*args, **kwargs):
        raise sp.TimeoutExpired("xclip", 5)

    monkeypatch.setattr("subprocess.run", _raise)
    return _raise


@pytest.fixture()
def mock_xdotool_process(monkeypatch):
    """Mock xdotool subprocess call."""
    mock = monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: type("P", (), {"returncode": 0, "stderr": b""})(),
    )
    return mock


@pytest.fixture()
def mock_xdotool_error(monkeypatch):
    """Mock xdotool subprocess call that fails."""
    mock = monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: type("P", (), {"returncode": 1, "stderr": b"xdotool error"})(),
    )
    return mock


@pytest.fixture()
def mock_xdotool_timeout(monkeypatch):
    """Mock xdotool subprocess call with timeout."""
    import subprocess as sp

    def _raise(*args, **kwargs):
        raise sp.TimeoutExpired("xdotool", 10)

    monkeypatch.setattr("subprocess.run", _raise)
    return _raise


@pytest.fixture()
def mock_arecord(monkeypatch, tmp_path):
    """Mock arecord subprocess calls."""
    class FakeRecorder:
        def __init__(self):
            self.call_count = 0
            self._alive = False

        def _make_proc(self, returncode=0):
            return type("P", (), {"pid": 99999, "wait": lambda *a, **k: None, "returncode": returncode})()

        def __call__(self, cmd, *args, **kwargs):
            self.call_count += 1
            if not cmd:
                return self._make_proc()

            if cmd[0] == "kill" and "-0" in cmd:
                return self._make_proc(0 if self._alive else 1)

            if cmd[0] == "kill":
                self._alive = False
                return self._make_proc()

            if cmd[0] == "arecord":
                self._alive = True
                return self._make_proc()

            return self._make_proc()

        def run(self, cmd, *args, **kwargs):
            self(cmd, *args, **kwargs)
            return type("P", (), {"returncode": 0, "stderr": b""})()

    recorder = FakeRecorder()
    monkeypatch.setattr("subprocess.Popen", recorder)
    monkeypatch.setattr("subprocess.run", recorder.run)
    return recorder


@pytest.fixture()
def mock_requests_post(monkeypatch):
    """Mock requests.post for STT endpoint testing.

    Returns a callable mock that tracks calls and returns a response.
    """
    class MockResponse:
        status_code = 200
        text = "Hello world this is a test transcription"
        headers = {"Content-Type": "application/json"}
        def json(self):
            return {"text": "Hello world this is a test transcription"}
        def raise_for_status(self):
            return None

    mock_resp = MockResponse()

    class MockPost:
        call_count = 0
        call_args = None
        calls = []

        def __call__(self, *a, **k):
            self.call_count += 1
            self.call_args = (a, k)
            self.calls.append((a, k))
            return mock_resp

    mock_post = MockPost()
    # Patch at the module level used by stt_client
    monkeypatch.setattr("macrokeyboard.stt_client.requests.post", mock_post)
    return mock_post
