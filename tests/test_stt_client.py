#!/usr/bin/env python3
"""Tests for stt_client.py."""
import os
import requests as requests_lib

import pytest


class TestTranscribe:
    """Tests for the transcribe function."""

    def test_calls_endpoint_with_wav_file(self, tmp_wav_file, mock_requests_post):
        """Should POST the WAV file to the endpoint."""
        from macrokeyboard.stt_client import transcribe

        transcribe(tmp_wav_file)
        assert mock_requests_post.call_count == 1

    def test_returns_json_text(self, tmp_wav_file, mock_requests_post):
        """Should extract text from JSON response."""
        from macrokeyboard.stt_client import transcribe

        text = transcribe(tmp_wav_file)
        assert text == "Hello world this is a test transcription"

    def test_uses_default_endpoint(self, tmp_wav_file, mock_requests_post):
        """Should use the default endpoint when none specified."""
        from macrokeyboard.stt_client import transcribe

        transcribe(tmp_wav_file, default_endpoint="http://localhost:8000/api")

        call_args = mock_requests_post.call_args
        url = call_args[0][0]
        assert "localhost:8000" in url

    def test_uses_env_var_endpoint(self, tmp_wav_file, env_patch, mock_requests_post):
        """Should use $STT_ENDPOINT when set."""
        env_patch(STT_ENDPOINT="http://override.example.com/api")

        from macrokeyboard.stt_client import transcribe

        transcribe(tmp_wav_file)

        call_args = mock_requests_post.call_args
        url = call_args[0][0]
        assert "override.example.com" in url

    def test_env_var_overrides_default(self, tmp_wav_file, env_patch, mock_requests_post):
        """Env var STT_ENDPOINT should override default INSCRIPT."""
        env_patch(STT_ENDPOINT="http://env-var.example.com/api")

        from macrokeyboard.stt_client import transcribe

        transcribe(tmp_wav_file, default_endpoint="http://default.example.com/api")

        call_args = mock_requests_post.call_args
        url = call_args[0][0]
        assert "env-var.example.com" in url

    def test_uses_model_param(self, tmp_wav_file, mock_requests_post):
        """Should pass the model parameter."""
        from macrokeyboard.stt_client import transcribe

        transcribe(tmp_wav_file, model="large-v3")

        call_args = mock_requests_post.call_args
        data = call_args[1].get("data", {})
        assert data.get("model") == "large-v3"

    def test_uses_env_model(self, tmp_wav_file, env_patch, mock_requests_post):
        """Should use $STT_MODEL from environment."""
        env_patch(STT_MODEL="whisper-large-v3")

        from macrokeyboard.stt_client import transcribe

        transcribe(tmp_wav_file)

        call_args = mock_requests_post.call_args
        data = call_args[1].get("data", {})
        assert data.get("model") == "whisper-large-v3"

    def test_passes_language_when_set(self, tmp_wav_file, mock_requests_post):
        """Should include language in API data when specified."""
        from macrokeyboard.stt_client import transcribe

        transcribe(tmp_wav_file, language="de")

        call_args = mock_requests_post.call_args
        data = call_args[1].get("data", {})
        assert data.get("language") == "de"

    def test_does_not_include_language_when_none(self, tmp_wav_file, mock_requests_post):
        """Should not include language key when no language specified."""
        from macrokeyboard.stt_client import transcribe

        transcribe(tmp_wav_file)

        call_args = mock_requests_post.call_args
        data = call_args[1].get("data", {})
        assert "language" not in data

    def test_language_supported_for_multiple_languages(self, tmp_wav_file, mock_requests_post):
        """Should handle various language codes."""
        from macrokeyboard.stt_client import transcribe

        for lang in ["en", "fr", "pl", "ru", "ja"]:
            transcribe(tmp_wav_file, language=lang)
            call_args = mock_requests_post.call_args
            data = call_args[1].get("data", {})
            assert data.get("language") == lang

    def test_raises_file_not_found(self):
        """Should raise FileNotFoundError for non-existent file."""
        from macrokeyboard.stt_client import transcribe

        with pytest.raises(FileNotFoundError, match="not found"):
            transcribe("/nonexistent/path/audio.wav")

    def test_handles_connection_error(self, tmp_wav_file, monkeypatch):
        """Should raise on connection errors."""
        monkeypatch.setattr(
            "macrokeyboard.stt_client.requests.post",
            lambda *a, **k: (_ for _ in ()).throw(
                requests_lib.exceptions.ConnectionError("nope")
            ),
        )

        from macrokeyboard.stt_client import transcribe

        with pytest.raises(requests_lib.exceptions.ConnectionError):
            transcribe(tmp_wav_file)

    def test_handles_http_error(self, tmp_wav_file, monkeypatch):
        """Should raise on HTTP errors."""
        class MockResp:
            status_code = 500
            def raise_for_status(self):
                raise requests_lib.HTTPError("500 Error")
            def json(self):
                return {}

        monkeypatch.setattr(
            "macrokeyboard.stt_client.requests.post",
            lambda *a, **k: MockResp(),
        )

        from macrokeyboard.stt_client import transcribe

        with pytest.raises(requests_lib.HTTPError):
            transcribe(tmp_wav_file)

    def test_language_with_model(self, tmp_wav_file, mock_requests_post):
        """Should include both language and model in API call."""
        from macrokeyboard.stt_client import transcribe

        transcribe(tmp_wav_file, model="large-v3", language="de")

        call_args = mock_requests_post.call_args
        data = call_args[1].get("data", {})
        assert data.get("model") == "large-v3"
        assert data.get("language") == "de"
