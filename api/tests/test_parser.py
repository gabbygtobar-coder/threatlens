from datetime import timezone
from pathlib import Path

import pytest

from app.models import EventType
from app.parsing import parse_line, parse_path, parse_text
from app.parsing.parser import MAX_LINE_LENGTH


def test_parse_happy_path_text_line() -> None:
    line = (
        "2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10 "
        'ua="Mozilla/5.0" resource=/login status=401'
    )
    event = parse_line(line)
    assert event.event_type is EventType.LOGIN_FAILURE
    assert event.username == "alice"
    assert event.source_ip == "203.0.113.10"
    assert event.user_agent == "Mozilla/5.0"
    assert event.resource == "/login"
    assert event.status_code == 401
    assert event.timestamp.tzinfo is not None
    assert event.timestamp.utcoffset() == timezone.utc.utcoffset(event.timestamp)
    assert event.raw == line


def test_parse_anonymous_user_and_ipv6() -> None:
    event = parse_line("2024-01-15T03:12:04Z request user=- ip=2001:db8::1 resource=/health status=200")
    assert event.username is None
    assert event.source_ip == "2001:db8::1"
    assert event.event_type is EventType.REQUEST


def test_parse_json_line() -> None:
    line = (
        '{"timestamp":"2024-01-15T03:12:01Z","event_type":"login_failure",'
        '"source_ip":"203.0.113.10","username":"alice"}'
    )
    event = parse_line(line)
    assert event.event_type is EventType.LOGIN_FAILURE
    assert event.username == "alice"
    assert event.source_ip == "203.0.113.10"
    assert event.raw == line


def test_parse_text_skips_comments_and_collects_errors() -> None:
    blob = """
# comment
2024-01-15T03:12:01Z login_success user=alice ip=203.0.113.10
not a log line

2024-01-15T03:12:02Z login_failure user=bob ip=198.51.100.20
"""
    result = parse_text(blob)
    assert [e.event_type for e in result.events] == [
        EventType.LOGIN_SUCCESS,
        EventType.LOGIN_FAILURE,
    ]
    assert len(result.errors) == 1
    assert result.errors[0].line_number == 4
    assert "not a log line" in result.errors[0].line


def test_unknown_keys_are_ignored() -> None:
    event = parse_line(
        "2024-01-15T03:12:01Z login_success user=alice ip=203.0.113.10 host=web01"
    )
    assert event.username == "alice"
    assert event.source_ip == "203.0.113.10"


def test_oversized_line_is_an_error_not_a_crash() -> None:
    huge = "x" * (MAX_LINE_LENGTH + 10)
    result = parse_text(huge)
    assert result.events == []
    assert len(result.errors) == 1
    assert "8192" in result.errors[0].reason


def test_missing_ip_and_bad_event_type_raise() -> None:
    with pytest.raises(ValueError, match="Missing required field ip="):
        parse_line("2024-01-15T03:12:01Z login_failure user=alice")
    with pytest.raises(ValueError, match="Unknown event_type"):
        parse_line("2024-01-15T03:12:01Z nope user=alice ip=203.0.113.10")


def test_normal_fixture_parses_cleanly(fixtures_dir: Path) -> None:
    result = parse_path(fixtures_dir / "normal" / "auth.log")
    assert result.errors == []
    assert len(result.events) == 20
    assert sum(1 for e in result.events if e.event_type is EventType.LOGIN_FAILURE) == 1
    assert sum(1 for e in result.events if e.event_type is EventType.LOGIN_SUCCESS) == 5


def test_bruteforce_fixture_parses_to_fifty_failures(fixtures_dir: Path) -> None:
    result = parse_path(fixtures_dir / "bruteforce" / "auth.log")
    assert result.errors == []
    failures = [e for e in result.events if e.event_type is EventType.LOGIN_FAILURE]
    assert len(result.events) == 50
    assert len(failures) == 50
    assert {e.source_ip for e in failures} == {"203.0.113.77"}
    assert {e.username for e in failures} == {"alice", "bob"}
    assert sum(1 for e in failures if e.username == "alice") == 40
    assert sum(1 for e in failures if e.username == "bob") == 10


def test_mixed_fixture_has_normal_and_failures(fixtures_dir: Path) -> None:
    result = parse_path(fixtures_dir / "mixed" / "auth.log")
    assert result.errors == []
    assert len(result.events) == 33
    failures = [e for e in result.events if e.event_type is EventType.LOGIN_FAILURE]
    assert len(failures) == 20
    assert all(e.source_ip == "203.0.113.77" for e in failures)
    assert any(e.event_type is EventType.LOGIN_SUCCESS for e in result.events)
    assert any(e.raw.startswith("{") for e in result.events)


def test_edge_fixture_does_not_crash(fixtures_dir: Path) -> None:
    result = parse_path(fixtures_dir / "edge" / "auth.log")
    assert result.errors, "edge fixture should include malformed lines"
    assert result.events, "edge fixture should still yield valid events"
    ips = {e.source_ip for e in result.events}
    assert "2001:db8::1" in ips
    assert any(e.raw.startswith("{") for e in result.events)
    reasons = " ".join(err.reason for err in result.errors)
    assert "Invalid timestamp" in reasons or "ISO-8601" in reasons
    assert "Invalid IP" in reasons
    assert "Invalid JSON" in reasons


def test_spray_fixture_parses_to_eight_users(fixtures_dir: Path) -> None:
    result = parse_path(fixtures_dir / "spray" / "auth.log")
    assert result.errors == []
    assert len(result.events) == 8
    assert all(e.event_type is EventType.LOGIN_FAILURE for e in result.events)
    assert {e.source_ip for e in result.events} == {"198.51.100.66"}
    assert {e.username for e in result.events} == {
        "alice",
        "bob",
        "carol",
        "dave",
        "erin",
        "frank",
        "grace",
        "heidi",
    }
