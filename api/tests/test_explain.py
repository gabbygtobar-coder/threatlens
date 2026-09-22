"""POST /explain is optional prose over incidents the engine already returned.

No live OpenAI calls. A missing key is 503. A present key uses a mocked client.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.explain import NOT_CONFIGURED_DETAIL, PROVIDER_FAILED_DETAIL, build_messages
from app.main import MAX_BODY_BYTES
from app.models import ExplainRequest
from app.rate_limit import reset_rate_limit_state

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".mjs"}

INCIDENT = {
    "id": "abc123",
    "rule_id": "brute_force",
    "severity": "high",
    "status": "open",
    "title": "Brute force from 203.0.113.77",
    "description": "50 login failures in 5 minutes.",
    "evidence": {
        "source_ip": "203.0.113.77",
        "failure_count": 50,
        "window_minutes": 5,
        "sample_raw": ["2024-03-13T02:14:01Z login_failure user=alice ip=203.0.113.77"],
    },
    "created_at": "2024-03-13T02:14:50Z",
}

EXPLAINED = (
    "The engine already flagged brute_force: 50 login failures from 203.0.113.77 "
    "inside a 5 minute window."
)


class _Response:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class FakeChatClient:
    """Stand-in for httpx.Client. Records the outbound chat-completions call."""

    calls: list[dict] = []
    response = _Response(
        200,
        {"choices": [{"message": {"content": EXPLAINED}}]},
    )
    error: Exception | None = None

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def __enter__(self) -> FakeChatClient:
        return self

    def __exit__(self, *args) -> bool:
        return False

    def post(self, url, headers=None, json=None):
        FakeChatClient.calls.append({"url": url, "headers": headers, "json": json})
        if FakeChatClient.error is not None:
            raise FakeChatClient.error
        return FakeChatClient.response


@pytest.fixture
def no_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture
def fake_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    FakeChatClient.calls = []
    FakeChatClient.response = _Response(
        200,
        {"choices": [{"message": {"content": EXPLAINED}}]},
    )
    FakeChatClient.error = None
    monkeypatch.setattr("app.explain.httpx.Client", FakeChatClient)


def test_explain_returns_503_when_key_absent(client, no_openai_key) -> None:
    response = client.post(
        "/explain",
        json={"incidents": [INCIDENT], "context": "demo"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 503
    body = response.json()
    assert body == {"detail": NOT_CONFIGURED_DETAIL}
    assert "explanation" not in body
    assert "test-key" not in response.text
    assert "203.0.113.77" not in body["detail"]
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_explain_blank_key_is_503(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "   ")
    response = client.post("/explain", json={"incidents": [INCIDENT]})
    assert response.status_code == 503
    assert "explanation" not in response.json()


def test_explain_503_does_not_call_provider(client, no_openai_key, monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("provider client should not be constructed without a key")

    monkeypatch.setattr("app.explain.httpx.Client", fail_if_called)
    response = client.post("/explain", json={"incidents": [INCIDENT]})
    assert response.status_code == 503


def test_explain_returns_provider_text_when_key_present(client, fake_openai) -> None:
    response = client.post(
        "/explain",
        json={"incidents": [INCIDENT], "context": "live detect response"},
    )
    assert response.status_code == 200
    assert response.json() == {"explanation": EXPLAINED}
    assert len(FakeChatClient.calls) == 1
    call = FakeChatClient.calls[0]
    assert call["url"] == "https://api.openai.com/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer test-key-not-real"
    assert call["json"]["model"] == "gpt-4o-mini"
    user = call["json"]["messages"][1]["content"]
    assert "203.0.113.77" in user
    assert "failure_count" in user
    assert "live detect response" in user
    assert "test-key-not-real" not in response.text


def test_prompt_forbids_inventing_threats() -> None:
    request = ExplainRequest.model_validate({"incidents": [INCIDENT], "context": "demo"})
    messages = build_messages(request)
    system = messages[0]["content"].lower()
    assert messages[0]["role"] == "system"
    assert "not a detector" in system
    assert "do not invent" in system
    assert "do not create, score" in system
    user = messages[1]["content"]
    assert "Do not invent new threats." in user
    assert "203.0.113.77" in user
    assert "failure_count" in user
    assert "50" in user


def test_explain_empty_incidents_does_not_call_provider(client, fake_openai) -> None:
    response = client.post("/explain", json={"incidents": []})
    assert response.status_code == 400
    assert response.json()["detail"] == "No incidents to explain. Refusing to invent threats."
    assert FakeChatClient.calls == []
    assert "explanation" not in response.json()


def test_explain_provider_http_error_is_502_without_fake_text(client, fake_openai) -> None:
    FakeChatClient.response = _Response(401, {"error": {"message": "bad key sk-secret"}})
    response = client.post("/explain", json={"incidents": [INCIDENT]})
    assert response.status_code == 502
    assert response.json() == {"detail": PROVIDER_FAILED_DETAIL}
    assert "sk-secret" not in response.text
    assert "explanation" not in response.json()


def test_explain_empty_provider_text_is_502(client, fake_openai) -> None:
    FakeChatClient.response = _Response(200, {"choices": [{"message": {"content": "  "}}]})
    response = client.post("/explain", json={"incidents": [INCIDENT]})
    assert response.status_code == 502
    assert response.json() == {"detail": PROVIDER_FAILED_DETAIL}


def test_explain_provider_transport_error_is_502(client, fake_openai) -> None:
    FakeChatClient.error = httpx.ConnectError("connection refused")
    response = client.post("/explain", json={"incidents": [INCIDENT]})
    assert response.status_code == 502
    assert "explanation" not in response.json()


def test_explain_rejects_invalid_body(client, no_openai_key) -> None:
    response = client.post("/explain", json={"context": "no incidents field"})
    assert response.status_code == 422
    assert "explanation" not in response.json()


def test_explain_rejects_oversized_body(client, no_openai_key) -> None:
    response = client.post(
        "/explain",
        content=b"{" + b"x" * (MAX_BODY_BYTES + 1),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413


def test_explain_cors_preflight_unchanged(client) -> None:
    response = client.options(
        "/explain",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_explain_is_rate_limited(client, no_openai_key, monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    reset_rate_limit_state()
    first = client.post("/explain", json={"incidents": [INCIDENT]})
    assert first.status_code == 503
    second = client.post("/explain", json={"incidents": [INCIDENT]})
    assert second.status_code == 429


def test_readme_marks_explain_only_done_and_not_a_detector() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "| **COMPLETE** | **M7**" in readme
    assert "OPENAI_API_KEY" in readme
    assert "never" in readme.lower()
    assert "detector" in readme.lower()
    assert "NEXT_PUBLIC" in readme
    # The old not-started row must not still mark M7 as not done.
    assert "**NOT DONE** | **M7**" not in readme


def test_web_source_does_not_read_openai_key() -> None:
    offenders: list[str] = []
    for path in (REPO_ROOT / "web").rglob("*"):
        if not path.is_file() or path.suffix not in WEB_SOURCE_SUFFIXES:
            continue
        if "node_modules" in path.parts or ".next" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "process.env.OPENAI_API_KEY" in text or "NEXT_PUBLIC_OPENAI" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []
