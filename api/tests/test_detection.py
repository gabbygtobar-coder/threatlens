from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.detection import (
    BruteForceRule,
    CredentialSprayRule,
    DetectionEngine,
    default_engine,
)
from app.detection.base import stable_incident_id
from app.models import EventType, LogEvent, RuleId, Severity
from app.parsing import parse_path

UTC = timezone.utc


def _failure(
    ts: datetime,
    ip: str = "203.0.113.77",
    user: str | None = "alice",
) -> LogEvent:
    stamp = ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    name = user if user else "-"
    raw = f"{stamp} login_failure user={name} ip={ip} resource=/login status=401"
    return LogEvent(
        timestamp=ts,
        source_ip=ip,
        username=user,
        event_type=EventType.LOGIN_FAILURE,
        resource="/login",
        status_code=401,
        raw=raw,
    )


def _burst(count: int, *, start: datetime, ip: str, user: str, step_seconds: int = 1) -> list[LogEvent]:
    return [_failure(start + timedelta(seconds=i * step_seconds), ip=ip, user=user) for i in range(count)]


def test_brute_force_fires_on_bruteforce_fixture(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "bruteforce" / "auth.log").events
    incidents = BruteForceRule().detect(events)
    assert len(incidents) == 1
    incident = incidents[0]
    assert incident.rule_id is RuleId.BRUTE_FORCE
    assert incident.severity is Severity.HIGH
    assert incident.status.value == "open"
    assert incident.evidence["source_ip"] == "203.0.113.77"
    assert incident.evidence["failure_count"] == 50
    assert incident.evidence["distinct_usernames"] == 2
    assert incident.evidence["usernames"] == ["alice", "bob"]
    assert incident.evidence["username_failure_counts"] == {"alice": 40, "bob": 10}
    assert incident.evidence["min_failures"] == 10
    assert incident.evidence["window_minutes"] == 5
    assert incident.evidence["window_start"] == "2024-03-13T02:14:01Z"
    assert incident.evidence["window_end"] == "2024-03-13T02:14:50Z"
    assert len(incident.evidence["sample_raw"]) == 5
    assert all("login_failure" in line for line in incident.evidence["sample_raw"])
    assert "203.0.113.77" in incident.title
    assert "50 login_failure" in incident.description


def test_brute_force_does_not_fire_on_normal_fixture(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "normal" / "auth.log").events
    assert BruteForceRule().detect(events) == []


def test_credential_spray_does_not_fire_on_normal_fixture(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "normal" / "auth.log").events
    assert CredentialSprayRule().detect(events) == []


def test_credential_spray_fires_on_spray_fixture(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "spray" / "auth.log").events
    incidents = CredentialSprayRule().detect(events)
    assert len(incidents) == 1
    incident = incidents[0]
    assert incident.rule_id is RuleId.CREDENTIAL_SPRAY
    assert incident.severity is Severity.HIGH
    assert incident.status.value == "open"
    assert incident.evidence["source_ip"] == "198.51.100.66"
    assert incident.evidence["failure_count"] == 8
    assert incident.evidence["distinct_usernames"] == 8
    assert incident.evidence["usernames"] == [
        "alice",
        "bob",
        "carol",
        "dave",
        "erin",
        "frank",
        "grace",
        "heidi",
    ]
    assert incident.evidence["min_usernames"] == 5
    assert incident.evidence["window_minutes"] == 10
    assert incident.evidence["window_start"] == "2024-03-15T03:00:00Z"
    assert incident.evidence["window_end"] == "2024-03-15T03:03:30Z"
    assert len(incident.evidence["sample_raw"]) == 5
    assert "198.51.100.66" in incident.title


def test_spray_fixture_does_not_trip_brute_force(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "spray" / "auth.log").events
    assert BruteForceRule().detect(events) == []


def test_bruteforce_fixture_does_not_trip_spray(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "bruteforce" / "auth.log").events
    assert CredentialSprayRule().detect(events) == []


def test_mixed_fixture_trips_brute_force_only(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "mixed" / "auth.log").events
    brute = BruteForceRule().detect(events)
    spray = CredentialSprayRule().detect(events)
    assert len(brute) == 1
    assert brute[0].evidence["failure_count"] == 20
    assert brute[0].evidence["usernames"] == ["alice"]
    assert spray == []


def test_engine_aggregates_and_is_deterministic(fixtures_dir: Path) -> None:
    brute_events = parse_path(fixtures_dir / "bruteforce" / "auth.log").events
    spray_events = parse_path(fixtures_dir / "spray" / "auth.log").events
    combined = list(reversed(brute_events + spray_events))
    engine = default_engine()
    first = engine.run(combined)
    second = engine.run(list(reversed(combined)))
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]
    assert [item.rule_id for item in first] == [RuleId.BRUTE_FORCE, RuleId.CREDENTIAL_SPRAY]


def test_incident_id_is_hash_of_rule_ip_window(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "bruteforce" / "auth.log").events
    incident = BruteForceRule().detect(events)[0]
    start = datetime(2024, 3, 13, 2, 14, 1, tzinfo=UTC)
    end = datetime(2024, 3, 13, 2, 14, 50, tzinfo=UTC)
    assert incident.created_at == end
    assert incident.id == stable_incident_id(RuleId.BRUTE_FORCE, "203.0.113.77", start, end)
    assert len(incident.id) == 32


def test_brute_force_threshold_boundaries() -> None:
    start = datetime(2024, 3, 13, 2, 0, 0, tzinfo=UTC)
    ip = "203.0.113.50"
    nine = _burst(9, start=start, ip=ip, user="alice")
    ten = _burst(10, start=start, ip=ip, user="alice")
    assert BruteForceRule().detect(nine) == []
    fired = BruteForceRule().detect(ten)
    assert len(fired) == 1
    assert fired[0].evidence["failure_count"] == 10

    # 10 events whose span is just over 5 minutes: no window of 10 fits in T.
    wide = _burst(10, start=start, ip=ip, user="alice", step_seconds=34)
    # 9 * 34s = 306s > 300s
    assert (wide[-1].timestamp - wide[0].timestamp) > timedelta(minutes=5)
    assert BruteForceRule().detect(wide) == []

    # Exactly 5 minutes from first to last still counts as within the window.
    exact = _burst(10, start=start, ip=ip, user="alice", step_seconds=0)
    exact[-1] = _failure(start + timedelta(minutes=5), ip=ip, user="alice")
    assert len(BruteForceRule().detect(exact)) == 1


def test_spray_threshold_boundaries() -> None:
    start = datetime(2024, 3, 15, 3, 0, 0, tzinfo=UTC)
    ip = "198.51.100.9"
    users = ["alice", "bob", "carol", "dave", "erin"]
    four = [_failure(start + timedelta(seconds=i), ip=ip, user=users[i]) for i in range(4)]
    five = [_failure(start + timedelta(seconds=i), ip=ip, user=users[i]) for i in range(5)]
    assert CredentialSprayRule().detect(four) == []
    fired = CredentialSprayRule().detect(five)
    assert len(fired) == 1
    assert fired[0].evidence["distinct_usernames"] == 5


def test_engine_with_no_rules_returns_nothing() -> None:
    start = datetime(2024, 3, 13, 2, 0, 0, tzinfo=UTC)
    events = _burst(20, start=start, ip="203.0.113.1", user="alice")
    assert DetectionEngine(rules=[]).run(events) == []
