#!/usr/bin/env python3
"""Audio recording via ALSA arecord — start, stop, and manage recording sessions."""
import logging
import os
import subprocess
import tempfile
import threading
import time

logger = logging.getLogger(__name__)


class RecordingHandle:
    """Handle for an active recording session."""

    def __init__(self, pid, temp_path, stopped_event):
        self.pid = pid
        self.temp_path = temp_path
        self.stopped_event = stopped_event


class VoiceCapture:
    """Manages audio recording via ALSA arecord."""

    def __init__(self, device="plughw:0,0", timeout=60, format="cd"):
        """Initialize the voice capture.

        Args:
            device: ALSA device string (e.g. 'plughw:5,0' for C920 webcam mic)
            timeout: Maximum recording duration in seconds (default 60)
            format: Audio format preset — 'cd' (44100Hz 16-bit stereo) or 'raw'
        """
        self._handle = None
        self._device = device
        self._timeout = timeout
        self._format = format

    def start(self):
        """Start recording.

        Returns a RecordingHandle on success, or None on failure.
        """
        if self._handle and not self._handle.stopped_event.is_set():
            logger.warning("Recording already in progress — aborting previous")
            self.stop()

        mic_device = self._device

        # Format options for arecord
        format_opts = {
            "cd": ["-f", "S16_LE", "-r", "44100", "-c", "2"],
            "raw": ["-f", "S16_LE", "-r", "16000", "-c", "1"],
        }
        fmt = format_opts.get(self._format, format_opts["cd"])

        # Create temp file for recording
        fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="voice_")
        os.close(fd)
        logger.info("Recording to: %s", temp_path)

        try:
            cmd = ["arecord", "-D", mic_device] + fmt + ["-t", "wav", temp_path]
            logger.info("Starting arecord: %s", " ".join(cmd))

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )

            stopped_event = threading.Event()
            handle = RecordingHandle(pid=proc.pid, temp_path=temp_path, stopped_event=stopped_event)
            self._handle = handle

            logger.info("Recording started (PID %d, device %s)", proc.pid, mic_device)
            return handle

        except FileNotFoundError:
            logger.error("arecord not found — is alsa-utils installed?")
            os.unlink(temp_path)
            return None
        except Exception as e:
            logger.error("Failed to start recording: %s", e)
            os.unlink(temp_path)
            return None

    def stop(self):
        """Stop recording.

        Returns the WAV file path, or None on failure.
        """
        if not self._handle or self._handle.stopped_event.is_set():
            logger.warning("No active recording to stop")
            return None

        handle = self._handle

        try:
            proc = subprocess.Popen(
                ["kill", str(handle.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.wait(timeout=3)
            logger.info("arecord process terminated (PID %d)", handle.pid)

        except Exception:
            # Process might already be dead
            pass

        # Wait a moment for file to be flushed
        time.sleep(0.2)

        # Check file exists and get stats
        temp_path = handle.temp_path
        try:
            if os.path.isfile(temp_path):
                size = os.path.getsize(temp_path)
                duration = self._estimate_duration(handle)
                logger.info(
                    "Recording stopped: %d bytes, ~%.1fs, path=%s",
                    size, duration, temp_path,
                )
                handle.stopped_event.set()
                self._handle = None
                return temp_path
            else:
                logger.error("Recording file not found: %s", temp_path)
                return None
        except OSError as e:
            logger.error("Failed to stat recording file: %s", e)
            return None

    def check(self):
        """Check if recording is still active.

        Returns True if recording is in progress, False otherwise.
        """
        if not self._handle or self._handle.stopped_event.is_set():
            return False
        try:
            proc = subprocess.Popen(
                ["kill", "-0", str(self._handle.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.wait()
            return proc.returncode == 0
        except Exception:
            return False

    def _estimate_duration(self, handle):
        """Estimate recording duration from file size.

        For CD-quality 16-bit stereo: ~172 KB/s
        """
        try:
            if os.path.isfile(handle.temp_path):
                size = os.path.getsize(handle.temp_path)
                # WAV header is 44 bytes, plus 4 bytes/sec for 16-bit stereo 44.1kHz
                bytes_per_sec = 44100 * 2 * 2  # 44.1kHz, 16-bit, stereo = 176400 bytes/sec
                return (size - 44) / bytes_per_sec if size > 44 else 0
        except OSError:
            pass
        return 0

    def cleanup(self):
        """Force-stop recording and clean up temp file."""
        if self._handle:
            self.stop()
            if self._handle and os.path.isfile(self._handle.temp_path):
                try:
                    os.unlink(self._handle.temp_path)
                    logger.info("Cleaned up temp recording: %s", self._handle.temp_path)
                except OSError:
                    pass
            self._handle = None
