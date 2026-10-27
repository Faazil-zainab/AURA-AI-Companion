"""Opt-in test for a real llama.cpp server; never downloads a model."""

import os

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.mark.integration
def test_real_llama_server_chat():
    if os.getenv("AURA_RUN_LLM_INTEGRATION") != "1":
        pytest.skip("Set AURA_RUN_LLM_INTEGRATION=1 to test a running local server")

    settings = get_settings()
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/chat",
            json={
                "session_id": "integration-session",
                "message": "Reply with one short greeting.",
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reply"]
    assert body["audio_available"] is False
