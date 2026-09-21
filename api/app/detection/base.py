"""Shared rule interface and helpers for the detection engine."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from app.models import EventType, Incident, LogEvent, RuleId, RuleInfo, Severity, utc_z

SAMPLE_RAW_LIMIT = 5


class Rule(ABC):
    """A deterministic detector: same events → same incidents."""

    rule_id: RuleId
    title: str
    description: str
    severity: Severity

    @abstractmethod
    def detect(self, events: Sequence[LogEvent]) -> list[Incident]:
        """Return zero or more incidents for this rule only."""

    @abstractmethod
    def thresholds(self) -> dict[str, int]:
        """Public threshold values (minutes, counts) for GET /rules and evidence."""

    def info(self) -> RuleInfo:
        return RuleInfo(
            rule_id=self.rule_id,
            title=self.title,
            description=self.description,
            severity=self.severity,
            thresholds=self.thresholds(),
        )


def stable_incident_id(
    rule_id: RuleId | str,
    source_ip: str,
    window_start: datetime,
    window_end: datetime,
) -> str:
    """Deterministic id: sha256(rule_id|source_ip|window_start|window_end)[:32]."""
    rid = rule_id.value if isinstance(rule_id, RuleId) else rule_id
    payload = f"{rid}|{source_ip}|{utc_z(window_start)}|{utc_z(window_end)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def login_failures(events: Sequence[LogEvent]) -> list[LogEvent]:
    return [event for event in events if event.event_type is EventType.LOGIN_FAILURE]


def group_by_source_ip(events: Sequence[LogEvent]) -> dict[str, list[LogEvent]]:
    grouped: dict[str, list[LogEvent]] = {}
    for event in events:
        grouped.setdefault(event.source_ip, []).append(event)
    return grouped


def sort_events(events: Sequence[LogEvent]) -> list[LogEvent]:
    return sorted(
        events,
        key=lambda event: (
            event.timestamp,
            event.source_ip,
            event.username or "",
            event.raw,
        ),
    )


def distinct_usernames(events: Sequence[LogEvent]) -> list[str]:
    return sorted({event.username for event in events if event.username})


def username_failure_counts(events: Sequence[LogEvent]) -> dict[str, int]:
    counts: dict[str, int] = {}
    anonymous = 0
    for event in events:
        if event.username:
            counts[event.username] = counts.get(event.username, 0) + 1
        else:
            anonymous += 1
    ordered = {name: counts[name] for name in sorted(counts)}
    if anonymous:
        ordered["(anonymous)"] = anonymous
    return ordered


def merged_qualifying_clusters(
    events: Sequence[LogEvent],
    window: timedelta,
    qualifies: Callable[[Sequence[LogEvent]], bool],
) -> list[list[LogEvent]]:
    """Sliding windows of duration `window` that pass `qualifies`, merged if they overlap.

    A window includes endpoints: span <= window qualifies as "within T".
    Overlapping qualifying index ranges collapse into one cluster so a single
    burst yields one incident, not one per sliding step.
    """
    ordered = sort_events(events)
    n = len(ordered)
    if n == 0:
        return []

    ranges: list[tuple[int, int]] = []
    left = 0
    for right in range(n):
        while ordered[right].timestamp - ordered[left].timestamp > window:
            left += 1
        if qualifies(ordered[left : right + 1]):
            ranges.append((left, right))

    if not ranges:
        return []

    clusters: list[list[LogEvent]] = []
    cur_l, cur_r = ranges[0]
    for left_i, right_i in ranges[1:]:
        if left_i <= cur_r:
            cur_l = min(cur_l, left_i)
            cur_r = max(cur_r, right_i)
        else:
            clusters.append(ordered[cur_l : cur_r + 1])
            cur_l, cur_r = left_i, right_i
    clusters.append(ordered[cur_l : cur_r + 1])
    return clusters


def evidence_payload(
    cluster: Sequence[LogEvent],
    *,
    window_minutes: int,
    extra: dict[str, int],
) -> dict[str, object]:
    ordered = sort_events(cluster)
    window_start = ordered[0].timestamp
    window_end = ordered[-1].timestamp
    payload: dict[str, object] = {
        "source_ip": ordered[0].source_ip,
        "failure_count": len(ordered),
        "distinct_usernames": len(distinct_usernames(ordered)),
        "usernames": distinct_usernames(ordered),
        "username_failure_counts": username_failure_counts(ordered),
        "window_start": utc_z(window_start),
        "window_end": utc_z(window_end),
        "window_minutes": window_minutes,
        "sample_raw": [event.raw for event in ordered[:SAMPLE_RAW_LIMIT]],
    }
    payload.update(extra)
    return payload
