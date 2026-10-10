#!/usr/bin/env python3
"""Paste transcribed text: copy to clipboard and/or type at cursor via xdotool."""
import logging
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

CHUNK_SIZE = 50  # characters per xdotool type command


def xclip_available():
    """Check if xclip is installed."""
    return os.path.isfile("/usr/bin/xclip")


def xdotool_available():
    """Check if xdotool is installed."""
    return os.path.isfile("/usr/bin/xdotool")


def copy_to_clipboard(text):
    """Copy text to clipboard via xclip.

    Returns True on success, False if xclip is unavailable.
    """
    if not xclip_available():
        logger.warning("xclip not found — skipping clipboard copy")
        return False

    try:
        proc = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=5,
        )
        if proc.returncode == 0:
            logger.info("Copied to clipboard")
            return True
        else:
            logger.error("xclip failed: %s", proc.stderr.decode().strip())
            return False
    except subprocess.TimeoutExpired:
        logger.error("xclip timed out")
        return False
    except Exception as e:
        logger.error("xclip error: %s", e)
        return False


def paste_at_cursor(text):
    """Type text at the current cursor position using xdotool.

    Splits long text into chunks to avoid xdotool truncation.
    Returns True on success, False if xdotool is unavailable.
    """
    if not xdotool_available():
        logger.error("xdotool not found — cannot paste")
        return False

    if not text:
        logger.warning("Empty text — nothing to paste")
        return False

    try:
        # Split into chunks
        chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        total_pasted = 0
        for chunk in chunks:
            proc = subprocess.run(
                ["xdotool", "type", "--clearmodifiers", "--", chunk],
                capture_output=True,
                timeout=10,
            )
            if proc.returncode == 0:
                total_pasted += len(chunk)
            else:
                logger.error("xdotool chunk failed (exit %d): %s", proc.returncode, proc.stderr.decode().strip())
                raise RuntimeError(f"xdotool chunk failed: {proc.stderr.decode().strip()}")

        logger.info("Pasted %d chars at cursor in %d chunks", total_pasted, len(chunks))
        return True
    except subprocess.TimeoutExpired:
        logger.error("xdotool timed out")
        return False
    except Exception as e:
        logger.error("xdotool paste error: %s", e)
        return False


def copy_and_paste(text):
    """Copy to clipboard AND type at cursor.

    Returns True if at least one operation succeeded.
    """
    if not text:
        logger.warning("Empty text — nothing to copy or paste")
        return False

    clipboard_ok = copy_to_clipboard(text)
    paste_ok = paste_at_cursor(text)

    if clipboard_ok and paste_ok:
        logger.info("Done: copied and pasted %d chars", len(text))
        return True
    elif paste_ok:
        logger.info("Done: pasted %d chars (clipboard skipped)", len(text))
        return True
    elif clipboard_ok:
        logger.warning("Done: copied to clipboard but paste failed")
        return False
    else:
        logger.error("Both clipboard copy and paste failed")
        return False
