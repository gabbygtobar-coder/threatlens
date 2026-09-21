from pathlib import Path

from app.main import MAX_BODY_BYTES


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_parse_plain_text(client) -> None:
    body = "2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10\nnot valid\n"
    response = client.post("/parse", content=body, headers={"content-type": "text/plain"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["events"]) == 1
    assert payload["events"][0]["event_type"] == "login_failure"
    assert payload["events"][0]["timestamp"] == "2024-01-15T03:12:01Z"
    assert len(payload["errors"]) == 1
    assert payload["errors"][0]["line_number"] == 2


def test_parse_json_envelope(client) -> None:
    response = client.post(
        "/parse",
        json={"text": "2024-01-15T03:12:01Z login_success user=alice ip=203.0.113.10"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["events"]) == 1
    assert payload["events"][0]["username"] == "alice"
    assert payload["errors"] == []


def test_parse_empty_body(client) -> None:
    response = client.post("/parse", content=b"", headers={"content-type": "text/plain"})
    assert response.status_code == 200
    assert response.json() == {"events": [], "errors": []}


def test_parse_rejects_oversized_body(client) -> None:
    response = client.post(
        "/parse",
        content=b"x" * (MAX_BODY_BYTES + 1),
        headers={"content-type": "text/plain"},
    )
    assert response.status_code == 413


def test_parse_rejects_invalid_json_envelope(client) -> None:
    response = client.post("/parse", json={"logs": "nope"})
    assert response.status_code == 400


def test_parse_bruteforce_fixture_via_api(client, fixtures_dir: Path) -> None:
    text = (fixtures_dir / "bruteforce" / "auth.log").read_text(encoding="utf-8")
    response = client.post("/parse", json={"text": text})
    assert response.status_code == 200
    payload = response.json()
    assert payload["errors"] == []
    assert len(payload["events"]) == 50
    assert all(event["event_type"] == "login_failure" for event in payload["events"])
