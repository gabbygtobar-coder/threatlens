from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.detection import (
    BruteForceRule,
    CredentialSprayRule,
    DetectionEngine,
    ImpossibleTravelRule,
    RequestFrequencyRule,
    RestrictedAccessRule,
    UnusualLoginRule,
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


def _success(
    ts: datetime,
    ip: str = "203.0.113.10",
    user: str | None = "alice",
    country: str | None = None,
    resource: str = "/login",
) -> LogEvent:
    stamp = ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    name = user if user else "-"
    extra = f" country={country}" if country else ""
    raw = f"{stamp} login_success user={name} ip={ip}{extra} resource={resource} status=200"
    return LogEvent(
        timestamp=ts,
        source_ip=ip,
        username=user,
        event_type=EventType.LOGIN_SUCCESS,
        resource=resource,
        status_code=200,
        country=country,
        raw=raw,
    )


def _request(
    ts: datetime,
    ip: str = "203.0.113.99",
    resource: str = "/api/items",
) -> LogEvent:
    stamp = ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw = f"{stamp} request user=- ip={ip} resource={resource} status=200"
    return LogEvent(
        timestamp=ts,
        source_ip=ip,
        event_type=EventType.REQUEST,
        resource=resource,
        status_code=200,
        raw=raw,
    )


def _denied(
    ts: datetime,
    ip: str = "198.51.100.7",
    user: str | None = "mallory",
    resource: str = "/admin",
) -> LogEvent:
    stamp = ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    name = user if user else "-"
    raw = f"{stamp} access_denied user={name} ip={ip} resource={resource} status=403"
    return LogEvent(
        timestamp=ts,
        source_ip=ip,
        username=user,
        event_type=EventType.ACCESS_DENIED,
        resource=resource,
        status_code=403,
        raw=raw,
    )


def test_unusual_login_fires_on_fixture_not_normal(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "unusual_login" / "auth.log").events
    incidents = UnusualLoginRule().detect(events)
    assert len(incidents) == 2
    by_reason = {item.evidence["reason"]: item for item in incidents}
    assert set(by_reason) == {"off_hours", "frequency"}

    off = by_reason["off_hours"]
    assert off.rule_id is RuleId.UNUSUAL_LOGIN
    assert off.severity is Severity.MEDIUM
    assert off.status.value == "open"
    assert off.evidence["username"] == "alice"
    assert off.evidence["success_count"] == 2
    assert off.evidence["utc_hours"] == [3]
    assert off.evidence["hours_start_utc"] == 8
    assert off.evidence["hours_end_utc"] == 22
    assert off.evidence["window_start"] == "2024-03-16T03:11:04Z"
    assert off.evidence["window_end"] == "2024-03-16T03:42:18Z"
    assert "alice" in off.title
    assert len(off.evidence["sample_raw"]) == 2

    freq = by_reason["frequency"]
    assert freq.evidence["username"] == "bob"
    assert freq.evidence["success_count"] == 5
    assert freq.evidence["min_successes"] == 5
    assert freq.evidence["window_minutes"] == 10
    assert freq.evidence["window_start"] == "2024-03-16T14:10:00Z"
    assert freq.evidence["window_end"] == "2024-03-16T14:11:55Z"

    assert UnusualLoginRule().detect(parse_path(fixtures_dir / "normal" / "auth.log").events) == []


def test_unusual_login_hour_and_frequency_boundaries() -> None:
    day = datetime(2024, 3, 16, 8, 0, 0, tzinfo=UTC)
    assert UnusualLoginRule().detect([_success(day)]) == []
    just_inside = datetime(2024, 3, 16, 21, 59, 0, tzinfo=UTC)
    assert UnusualLoginRule().detect([_success(just_inside)]) == []
    at_end = datetime(2024, 3, 16, 22, 0, 0, tzinfo=UTC)
    fired = UnusualLoginRule().detect([_success(at_end)])
    assert len(fired) == 1
    assert fired[0].evidence["reason"] == "off_hours"
    before = datetime(2024, 3, 16, 7, 59, 0, tzinfo=UTC)
    assert len(UnusualLoginRule().detect([_success(before)])) == 1

    start = datetime(2024, 3, 16, 14, 0, 0, tzinfo=UTC)
    four = [_success(start + timedelta(seconds=i), user="bob") for i in range(4)]
    five = [_success(start + timedelta(seconds=i), user="bob") for i in range(5)]
    assert UnusualLoginRule().detect(four) == []
    freq = UnusualLoginRule().detect(five)
    assert len(freq) == 1
    assert freq[0].evidence["reason"] == "frequency"


def test_impossible_travel_fires_on_fixture_not_normal(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "impossible_travel" / "auth.log").events
    incidents = ImpossibleTravelRule().detect(events)
    assert len(incidents) == 1
    incident = incidents[0]
    assert incident.rule_id is RuleId.IMPOSSIBLE_TRAVEL
    assert incident.severity is Severity.HIGH
    assert incident.evidence["username"] == "alice"
    assert incident.evidence["locations"] == ["US", "JP"]
    assert incident.evidence["location_count"] == 2
    assert incident.evidence["geo_simulated"] is True
    assert "MaxMind" in incident.evidence["geo_note"]
    assert incident.evidence["window_start"] == "2024-03-16T12:00:00Z"
    assert incident.evidence["window_end"] == "2024-03-16T12:25:00Z"
    assert incident.evidence["window_minutes"] == 60
    hops = incident.evidence["hops"]
    assert hops[0]["country"] == "US"
    assert hops[1]["country"] == "JP"
    assert "simulated" in incident.title.lower()

    assert ImpossibleTravelRule().detect(parse_path(fixtures_dir / "normal" / "auth.log").events) == []


def test_impossible_travel_window_and_same_country() -> None:
    start = datetime(2024, 3, 16, 12, 0, 0, tzinfo=UTC)
    same = [
        _success(start, ip="203.0.113.10", country="US"),
        _success(start + timedelta(minutes=10), ip="203.0.113.11", country="US"),
    ]
    assert ImpossibleTravelRule().detect(same) == []

    too_wide = [
        _success(start, ip="203.0.113.10", country="US"),
        _success(start + timedelta(minutes=61), ip="198.51.100.80", country="JP"),
    ]
    assert ImpossibleTravelRule().detect(too_wide) == []

    exact = [
        _success(start, ip="203.0.113.10", country="US"),
        _success(start + timedelta(minutes=60), ip="198.51.100.80", country="JP"),
    ]
    assert len(ImpossibleTravelRule().detect(exact)) == 1

    # No country= field: simulated IP-prefix map (TEST-NET-3=US, TEST-NET-2=DE).
    prefix = [
        _success(start, ip="203.0.113.10", country=None),
        _success(start + timedelta(minutes=15), ip="198.51.100.80", country=None),
    ]
    fired = ImpossibleTravelRule().detect(prefix)
    assert len(fired) == 1
    assert fired[0].evidence["locations"] == ["US", "DE"]


def test_request_frequency_fires_on_fixture_not_normal(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "request_frequency" / "auth.log").events
    incidents = RequestFrequencyRule().detect(events)
    assert len(incidents) == 1
    incident = incidents[0]
    assert incident.rule_id is RuleId.REQUEST_FREQUENCY
    assert incident.severity is Severity.MEDIUM
    assert incident.evidence["source_ip"] == "203.0.113.99"
    assert incident.evidence["request_count"] == 50
    assert incident.evidence["min_requests"] == 50
    assert incident.evidence["window_minutes"] == 1
    assert incident.evidence["window_start"] == "2024-03-16T18:00:00Z"
    assert incident.evidence["window_end"] == "2024-03-16T18:00:49Z"
    assert "203.0.113.99" in incident.title

    assert RequestFrequencyRule().detect(parse_path(fixtures_dir / "normal" / "auth.log").events) == []


def test_request_frequency_threshold_boundaries() -> None:
    start = datetime(2024, 3, 16, 18, 0, 0, tzinfo=UTC)
    forty_nine = [_request(start + timedelta(seconds=i)) for i in range(49)]
    fifty = [_request(start + timedelta(seconds=i)) for i in range(50)]
    assert RequestFrequencyRule().detect(forty_nine) == []
    fired = RequestFrequencyRule().detect(fifty)
    assert len(fired) == 1
    assert fired[0].evidence["request_count"] == 50


def test_restricted_access_fires_on_fixture_not_normal(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "restricted_access" / "auth.log").events
    incidents = RestrictedAccessRule().detect(events)
    assert len(incidents) == 1
    incident = incidents[0]
    assert incident.rule_id is RuleId.RESTRICTED_ACCESS
    assert incident.severity is Severity.HIGH
    assert incident.evidence["source_ip"] == "198.51.100.7"
    assert incident.evidence["denial_count"] == 3
    assert incident.evidence["matched_prefixes"] == ["/admin", "/etc/passwd"]
    assert incident.evidence["resources"] == ["/admin", "/admin/users", "/etc/passwd"]
    assert incident.evidence["usernames"] == ["mallory"]
    assert incident.evidence["min_denials"] == 1
    assert "/admin" in incident.evidence["restricted_prefixes"]
    assert incident.evidence["window_start"] == "2024-03-16T15:01:02Z"
    assert incident.evidence["window_end"] == "2024-03-16T15:01:15Z"

    assert RestrictedAccessRule().detect(parse_path(fixtures_dir / "normal" / "auth.log").events) == []


def test_restricted_access_prefix_matching() -> None:
    start = datetime(2024, 3, 16, 15, 0, 0, tzinfo=UTC)
    assert RestrictedAccessRule().detect([_denied(start, resource="/inbox")]) == []
    assert RestrictedAccessRule().detect([_denied(start, resource="/administrator")]) == []
    assert len(RestrictedAccessRule().detect([_denied(start, resource="/admin")])) == 1
    assert len(RestrictedAccessRule().detect([_denied(start, resource="/admin/users")])) == 1
    assert len(RestrictedAccessRule().detect([_denied(start, resource="/secrets")])) == 1
    assert len(RestrictedAccessRule().detect([_denied(start, resource="/.env")])) == 1


def test_new_rule_fixtures_are_isolated(fixtures_dir: Path) -> None:
    """Each M3 fixture trips only its own rule when the full engine runs."""
    engine = default_engine()
    expected = {
        "unusual_login": {RuleId.UNUSUAL_LOGIN},
        "impossible_travel": {RuleId.IMPOSSIBLE_TRAVEL},
        "request_frequency": {RuleId.REQUEST_FREQUENCY},
        "restricted_access": {RuleId.RESTRICTED_ACCESS},
        "bruteforce": {RuleId.BRUTE_FORCE},
        "spray": {RuleId.CREDENTIAL_SPRAY},
        "mixed": {RuleId.BRUTE_FORCE},
        "normal": set(),
    }
    for name, rule_ids in expected.items():
        events = parse_path(fixtures_dir / name / "auth.log").events
        got = {item.rule_id for item in engine.run(events)}
        assert got == rule_ids, f"{name}: {got} != {rule_ids}"


def test_m3_incident_ids_are_deterministic(fixtures_dir: Path) -> None:
    events = parse_path(fixtures_dir / "restricted_access" / "auth.log").events
    first = RestrictedAccessRule().detect(events)[0]
    second = RestrictedAccessRule().detect(list(reversed(events)))[0]
    assert first.id == second.id
    assert len(first.id) == 32
    start = datetime(2024, 3, 16, 15, 1, 2, tzinfo=UTC)
    end = datetime(2024, 3, 16, 15, 1, 15, tzinfo=UTC)
    assert first.id == stable_incident_id(RuleId.RESTRICTED_ACCESS, "198.51.100.7", start, end)
