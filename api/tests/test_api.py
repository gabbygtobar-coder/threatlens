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


def test_rules_lists_thresholds(client) -> None:
    response = client.get("/rules")
    assert response.status_code == 200
    payload = response.json()
    by_id = {rule["rule_id"]: rule for rule in payload["rules"]}
    assert set(by_id) == {
        "brute_force",
        "credential_spray",
        "unusual_login",
        "impossible_travel",
        "request_frequency",
        "restricted_access",
    }
    assert by_id["brute_force"]["severity"] == "high"
    assert by_id["brute_force"]["thresholds"] == {"min_failures": 10, "window_minutes": 5}
    assert by_id["credential_spray"]["severity"] == "high"
    assert by_id["credential_spray"]["thresholds"] == {"min_usernames": 5, "window_minutes": 10}
    assert by_id["unusual_login"]["severity"] == "medium"
    assert by_id["unusual_login"]["thresholds"] == {
        "hours_start_utc": 8,
        "hours_end_utc": 22,
        "min_successes": 5,
        "window_minutes": 10,
    }
    assert by_id["impossible_travel"]["severity"] == "high"
    assert by_id["impossible_travel"]["thresholds"] == {
        "min_locations": 2,
        "window_minutes": 60,
    }
    assert "simulated" in by_id["impossible_travel"]["title"].lower()
    assert by_id["request_frequency"]["severity"] == "medium"
    assert by_id["request_frequency"]["thresholds"] == {
        "min_requests": 50,
        "window_minutes": 1,
    }
    assert by_id["restricted_access"]["severity"] == "high"
    assert by_id["restricted_access"]["thresholds"]["min_denials"] == 1
    assert by_id["restricted_access"]["thresholds"]["restricted_prefixes"] == [
        "/admin",
        "/secrets",
        "/etc/passwd",
        "/.env",
    ]


def test_detect_empty_body(client) -> None:
    response = client.post("/detect", content=b"", headers={"content-type": "text/plain"})
    assert response.status_code == 200
    assert response.json() == {"events_count": 0, "incidents": [], "parse_errors": []}


def test_detect_bruteforce_fixture(client, fixtures_dir: Path) -> None:
    text = (fixtures_dir / "bruteforce" / "auth.log").read_text(encoding="utf-8")
    response = client.post("/detect", json={"text": text})
    assert response.status_code == 200
    payload = response.json()
    assert payload["events_count"] == 50
    assert payload["parse_errors"] == []
    assert len(payload["incidents"]) == 1
    incident = payload["incidents"][0]
    assert incident["rule_id"] == "brute_force"
    assert incident["severity"] == "high"
    assert incident["status"] == "open"
    assert incident["evidence"]["source_ip"] == "203.0.113.77"
    assert incident["evidence"]["failure_count"] == 50
    assert "sample_raw" in incident["evidence"]
    assert incident["created_at"] == "2024-03-13T02:14:50Z"


def test_detect_normal_fixture_has_no_incidents(client, fixtures_dir: Path) -> None:
    text = (fixtures_dir / "normal" / "auth.log").read_text(encoding="utf-8")
    response = client.post("/detect", content=text, headers={"content-type": "text/plain"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["events_count"] == 20
    assert payload["incidents"] == []
    assert payload["parse_errors"] == []


def test_detect_spray_fixture(client, fixtures_dir: Path) -> None:
    text = (fixtures_dir / "spray" / "auth.log").read_text(encoding="utf-8")
    response = client.post("/detect", json={"text": text})
    assert response.status_code == 200
    payload = response.json()
    assert payload["events_count"] == 8
    assert payload["parse_errors"] == []
    assert len(payload["incidents"]) == 1
    incident = payload["incidents"][0]
    assert incident["rule_id"] == "credential_spray"
    assert incident["evidence"]["distinct_usernames"] == 8
    assert incident["evidence"]["min_usernames"] == 5


def test_detect_keeps_parse_errors(client) -> None:
    body = "2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10\nnot valid\n"
    response = client.post("/detect", content=body, headers={"content-type": "text/plain"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["events_count"] == 1
    assert len(payload["parse_errors"]) == 1
    assert payload["incidents"] == []


def test_detect_rejects_oversized_body(client) -> None:
    response = client.post(
        "/detect",
        content=b"x" * (MAX_BODY_BYTES + 1),
        headers={"content-type": "text/plain"},
    )
    assert response.status_code == 413


def test_detect_unusual_login_fixture(client, fixtures_dir: Path) -> None:
    text = (fixtures_dir / "unusual_login" / "auth.log").read_text(encoding="utf-8")
    response = client.post("/detect", json={"text": text})
    assert response.status_code == 200
    payload = response.json()
    assert payload["events_count"] == 10
    assert payload["parse_errors"] == []
    reasons = {item["evidence"]["reason"] for item in payload["incidents"]}
    assert reasons == {"off_hours", "frequency"}
    assert all(item["rule_id"] == "unusual_login" for item in payload["incidents"])


def test_detect_impossible_travel_fixture(client, fixtures_dir: Path) -> None:
    text = (fixtures_dir / "impossible_travel" / "auth.log").read_text(encoding="utf-8")
    response = client.post("/detect", json={"text": text})
    assert response.status_code == 200
    payload = response.json()
    assert payload["events_count"] == 8
    assert payload["parse_errors"] == []
    assert len(payload["incidents"]) == 1
    incident = payload["incidents"][0]
    assert incident["rule_id"] == "impossible_travel"
    assert incident["evidence"]["geo_simulated"] is True
    assert incident["evidence"]["locations"] == ["US", "JP"]


def test_detect_request_frequency_fixture(client, fixtures_dir: Path) -> None:
    text = (fixtures_dir / "request_frequency" / "auth.log").read_text(encoding="utf-8")
    response = client.post("/detect", json={"text": text})
    assert response.status_code == 200
    payload = response.json()
    assert payload["events_count"] == 54
    assert payload["parse_errors"] == []
    assert len(payload["incidents"]) == 1
    assert payload["incidents"][0]["rule_id"] == "request_frequency"
    assert payload["incidents"][0]["evidence"]["request_count"] == 50


def test_detect_restricted_access_fixture(client, fixtures_dir: Path) -> None:
    text = (fixtures_dir / "restricted_access" / "auth.log").read_text(encoding="utf-8")
    response = client.post("/detect", json={"text": text})
    assert response.status_code == 200
    payload = response.json()
    assert payload["events_count"] == 6
    assert payload["parse_errors"] == []
    assert len(payload["incidents"]) == 1
    assert payload["incidents"][0]["rule_id"] == "restricted_access"
    assert payload["incidents"][0]["evidence"]["denial_count"] == 3
