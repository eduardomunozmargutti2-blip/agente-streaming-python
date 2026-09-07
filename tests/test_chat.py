from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import main


def make_chunk(content):
    delta = SimpleNamespace(content=content)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


class FakeStream:
    def __init__(self, chunks):
        self._chunks = chunks

    def __aiter__(self):
        return self._iter()

    async def _iter(self):
        for chunk in self._chunks:
            yield chunk


class FakeClient:
    def __init__(self, chunks):
        async def create(**_kwargs):
            return FakeStream(chunks)

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    return TestClient(main.app)


def test_chat_streams_tokens(client, monkeypatch):
    chunks = [make_chunk("Olá"), make_chunk(None), make_chunk(" mundo")]
    monkeypatch.setattr(main, "get_client", lambda: FakeClient(chunks))

    response = client.post("/chat", json={"prompt": "oi"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "Olá mundo"


def test_chat_reports_openai_error(client, monkeypatch):
    class FailingClient:
        def __init__(self):
            async def create(**_kwargs):
                raise RuntimeError("boom")

            self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))

    monkeypatch.setattr(main, "get_client", lambda: FailingClient())

    response = client.post("/chat", json={"prompt": "oi"})

    assert response.status_code == 200
    assert "[Erro na geração OpenAI: boom]" in response.text


def test_chat_sse_streams_events(client, monkeypatch):
    monkeypatch.setattr(main, "get_client", lambda: FakeClient([make_chunk("Olá")]))

    response = client.post("/chat/sse", json={"prompt": "oi"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == 'data: {"content": "Olá"}\n\ndata: [DONE]\n\n'


def test_chat_requires_prompt(client):
    assert client.post("/chat", json={}).status_code == 422
    assert client.post("/chat", json={"prompt": ""}).status_code == 422


def test_chat_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = TestClient(main.app).post("/chat", json={"prompt": "oi"})

    assert response.status_code == 500
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_health(client):
    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert body["api_key_configured"] is True


def test_index_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "PoC" in response.text
