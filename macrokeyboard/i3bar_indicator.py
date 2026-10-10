#!/usr/bin/env python3
"""Notification indicator — replaces i3bar section with notify-send.

Shows a 'recording' notification on start, clears it on stop or error.
"""
import logging
import subprocess

logger = logging.getLogger(__name__)


class VoiceIndicator:
    """Manages voice recording notifications via notify-send."""

    def __init__(self):
        self._notif_process = None

    def start(self):
        """Show 'recording...' notification.

        Returns True on success.
        """
        try:
            self._notif_process = subprocess.Popen(
                ["notify-send", "-u", "normal", "Voice Recording", "Recording... (release key to stop)"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Voice indicator: shown via notify-send")
            return True
        except Exception as e:
            logger.warning("Failed to show notification: %s", e)
            return False

    def stop(self):
        """Clear the notification (or show 'done' if text was provided).

        Args:
            text: Optional transcribed text to show in a final notification.
        """
        if self._notif_process:
            try:
                self._notif_process.terminate()
            except Exception:
                pass
            self._notif_process = None
        logger.info("Voice indicator: hidden")

    def show_error(self, message):
        """Show a critical error notification.

        Args:
            message: Error message to display.
        """
        try:
            subprocess.Popen(
                ["notify-send", "-u", "critical", "Voice Macro Error", message],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Voice indicator: error notification shown")
        except Exception as e:
            logger.warning("Failed to show error notification: %s", e)

    def show_success(self, text):
        """Show the transcribed text notification.

        Args:
            text: Transcribed text to display.
        """
        try:
            display_text = text[:100] if len(text) > 100 else text
            subprocess.Popen(
                ["notify-send", "-u", "normal", "Voice Macro", display_text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Voice indicator: success notification shown")
        except Exception as e:
            logger.warning("Failed to show success notification: %s", e)

    @property
    def initialized(self):
        return False  # notify-send doesn't need initialization
