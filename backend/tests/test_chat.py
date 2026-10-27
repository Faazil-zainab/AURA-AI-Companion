import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.llm_service import LLMService


class FakeAsyncClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error is not None:
            raise self.error
        return self.response


def make_client(tmp_path, fake):
    settings = Settings(database_path=tmp_path / "aura.db")
    service = LLMService(settings, http_client=fake)
    return TestClient(create_app(settings, llm_service=service)), fake


def test_chat_returns_actual_mocked_inference_and_constructs_character_prompt(tmp_path):
    fake = FakeAsyncClient(
        response=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Hello from the local model."}}]},
        )
    )

    with make_client(tmp_path, fake)[0] as client:
        response = client.post(
            "/api/v1/chat",
            headers={"X-Request-ID": "chat-request"},
            json={
                "session_id": "local-session",
                "message": "Hello",
                "history": [{"role": "assistant", "content": "Welcome."}],
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "session_id": "local-session",
        "reply": "Hello from the local model.",
        "emotion": "neutral",
        "audio_available": False,
        "request_id": "chat-request",
    }
    assert response.headers["X-Request-ID"] == "chat-request"
    url, kwargs = fake.calls[0]
    assert url == "http://127.0.0.1:8080/v1/chat/completions"
    messages = kwargs["json"]["messages"]
    assert messages[0]["role"] == "system"
    assert "AURA" in messages[0]["content"]
    assert "Welcome." in messages[1]["content"]
    assert messages[-1] == {"role": "user", "content": "Hello"}
    assert kwargs["json"]["stream"] is False


def test_gemma_compatible_prompt_mode_merges_character_prompt_into_user_turn(tmp_path):
    fake = FakeAsyncClient(
        response=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Ready."}}]},
        )
    )
    settings = Settings(
        database_path=tmp_path / "aura.db",
        llm_system_prompt_mode="merge_user",
    )
    service = LLMService(settings, http_client=fake)

    with TestClient(create_app(settings, llm_service=service)) as client:
        response = client.post(
            "/api/v1/chat",
            json={"session_id": "local-session", "message": "Hello"},
        )

    assert response.status_code == 200
    messages = fake.calls[0][1]["json"]["messages"]
    assert all(item["role"] != "system" for item in messages)
    assert messages[-1]["role"] == "user"
    assert "AURA" in messages[-1]["content"]
    assert messages[-1]["content"].endswith("Hello")


def test_chat_rejects_blank_message_without_calling_model(tmp_path):
    fake = FakeAsyncClient(response=httpx.Response(200, json={}))

    with make_client(tmp_path, fake)[0] as client:
        response = client.post(
            "/api/v1/chat",
            json={"session_id": "local-session", "message": "   "},
        )

    assert response.status_code == 422
    assert fake.calls == []


def test_chat_returns_503_on_model_timeout_and_preserves_request_id(tmp_path):
    fake = FakeAsyncClient(error=httpx.ReadTimeout("timed out"))

    with make_client(tmp_path, fake)[0] as client:
        response = client.post(
            "/api/v1/chat",
            headers={"X-Request-ID": "timeout-request"},
            json={"session_id": "local-session", "message": "Hello"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "message": "The local model server is unavailable",
        "request_id": "timeout-request",
    }
    assert response.headers["X-Request-ID"] == "timeout-request"


def test_chat_returns_503_when_model_server_is_unavailable(tmp_path):
    fake = FakeAsyncClient(error=httpx.ConnectError("connection refused"))

    with make_client(tmp_path, fake)[0] as client:
        response = client.post(
            "/api/v1/chat",
            json={"session_id": "local-session", "message": "Hello"},
        )

    assert response.status_code == 503
    assert response.json()["detail"]["message"] == "The local model server is unavailable"


def test_chat_returns_502_for_malformed_model_response(tmp_path):
    fake = FakeAsyncClient(response=httpx.Response(200, json={"choices": []}))

    with make_client(tmp_path, fake)[0] as client:
        response = client.post(
            "/api/v1/chat",
            json={"session_id": "local-session", "message": "Hello"},
        )

    assert response.status_code == 502
    assert response.json()["detail"]["message"] == (
        "The local model server returned an invalid response"
    )
