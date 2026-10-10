#!/usr/bin/env python3
"""Submit audio to a Whisper/STT endpoint and return transcribed text.

Supports both OpenAI-compatible JSON responses and plain text responses.
"""
import json
import logging
import os
import requests

logger = logging.getLogger(__name__)


def transcribe(audio_path, endpoint=None, model=None, default_endpoint=None):
    """Transcribe audio file by POSTing to the STT endpoint.

    Args:
        audio_path: Path to the WAV audio file.
        endpoint: STT endpoint URL. Checked in order: argument,
                  $STT_ENDPOINT env var, default_endpoint fallback.
        model: Model name. Defaults to $STT_MODEL env var, 'whisper-1'.
        default_endpoint: Module-level default (used by run_macros via INSCRIPT).

    Returns:
        The transcribed text string.

    Raises:
        Exception on network errors, HTTP errors, or parse failures.
    """
    endpoint = endpoint or os.environ.get("STT_ENDPOINT") or default_endpoint or "http://localhost:8000/v1/audio/transcriptions"
    model = model or os.environ.get("STT_MODEL", "whisper-1")

    logger.info("Submitting %s to %s (model=%s)", audio_path, endpoint, model)

    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
            data = {"model": model, "response_format": "json"}

            logger.info("POST %s with model=%s", endpoint, model)
            resp = requests.post(endpoint, files=files, data=data, timeout=120)
            resp.raise_for_status()
            logger.info("Received response (status %d)", resp.status_code)

    except requests.exceptions.Timeout:
        logger.error("STT request timed out after 120s")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error("Could not connect to STT endpoint %s: %s", endpoint, e)
        raise
    except requests.exceptions.HTTPError as e:
        logger.error("STT endpoint returned error: %s", e)
        raise
    except requests.exceptions.RequestException as e:
        logger.error("STT request failed: %s", e)
        raise

    # Parse response — try JSON first, fall back to plain text
    try:
        content_type = resp.headers.get("Content-Type", "")
        if "json" in content_type:
            result = resp.json()
            # OpenAI-compatible response: {"text": "..."}
            if isinstance(result, dict) and "text" in result:
                text = result["text"]
                logger.info("Transcription (JSON): %s", text)
                return text
            # Some endpoints return {"transcript": "..."}
            if isinstance(result, dict) and "transcript" in result:
                text = result["transcript"]
                logger.info("Transcription (JSON transcript): %s", text)
                return text
            logger.warning("JSON response has no 'text' or 'transcript' key: %s", result)
            return json.dumps(result)

        # Try parsing as JSON anyway (some endpoints send text/plain with JSON body)
        try:
            result = resp.json()
            if isinstance(result, dict) and "text" in result:
                text = result["text"]
                logger.info("Transcription (JSON fallback): %s", text)
                return text
        except (json.JSONDecodeError, ValueError):
            pass

        # Plain text response
        text = resp.text.strip()
        logger.info("Transcription (plain text): %s", text)
        return text

    except json.JSONDecodeError:
        # Final fallback: raw text
        logger.warning("Response is not JSON, using raw text")
        return resp.text.strip()
