"""Unusual login: off-hours and/or high-frequency successful logins per user.

Time-of-day and frequency only. No geo, no ML, no per-user learned baseline.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, Literal

from app.detection.base import (
    Rule,
    cluster_window_evidence,
    group_by_username,
    login_successes,
    merged_qualifying_clusters,
    sort_events,
    stable_incident_id,
)
from app.models import Incident, LogEvent, RuleId, Severity

# Normal office window in UTC. Hour H is normal iff start <= H < end.
UNUSUAL_LOGIN_HOURS_START_UTC = 8
UNUSUAL_LOGIN_HOURS_END_UTC = 22
UNUSUAL_LOGIN_MIN_SUCCESSES = 5
UNUSUAL_LOGIN_WINDOW_MINUTES = 10


class UnusualLoginRule(Rule):
    rule_id = RuleId.UNUSUAL_LOGIN
    title = "Unusual login"
    severity = Severity.MEDIUM

    def __init__(
        self,
        hours_start_utc: int = UNUSUAL_LOGIN_HOURS_START_UTC,
        hours_end_utc: int = UNUSUAL_LOGIN_HOURS_END_UTC,
        min_successes: int = UNUSUAL_LOGIN_MIN_SUCCESSES,
        window_minutes: int = UNUSUAL_LOGIN_WINDOW_MINUTES,
    ) -> None:
        self.hours_start_utc = hours_start_utc
        self.hours_end_utc = hours_end_utc
        self.min_successes = min_successes
        self.window_minutes = window_minutes
        self.description = (
            f"login_success for a username outside {hours_start_utc:02d}:00–"
            f"{hours_end_utc:02d}:00 UTC, or at least {min_successes} login_success "
            f"events for the same username within {window_minutes} minutes. "
            "Time-of-day and frequency only; no geo or ML."
        )

    def thresholds(self) -> dict[str, Any]:
        return {
            "hours_start_utc": self.hours_start_utc,
            "hours_end_utc": self.hours_end_utc,
            "min_successes": self.min_successes,
            "window_minutes": self.window_minutes,
        }

    def detect(self, events: Sequence[LogEvent]) -> list[Incident]:
        successes = login_successes(events)
        incidents: list[Incident] = []
        window = timedelta(minutes=self.window_minutes)

        for username, group in group_by_username(successes).items():
            ordered = sort_events(group)
            off_hours = [event for event in ordered if self._is_off_hours(event.timestamp)]
            if off_hours:
                incidents.append(self._incident(username, off_hours, reason="off_hours"))

            clusters = merged_qualifying_clusters(
                ordered,
                window,
                lambda cluster: len(cluster) >= self.min_successes,
            )
            for cluster in clusters:
                incidents.append(self._incident(username, cluster, reason="frequency"))
        return incidents

    def _is_off_hours(self, timestamp: datetime) -> bool:
        hour = timestamp.hour
        return not (self.hours_start_utc <= hour < self.hours_end_utc)

    def _incident(
        self,
        username: str,
        cluster: Sequence[LogEvent],
        reason: Literal["off_hours", "frequency"],
    ) -> Incident:
        ordered = sort_events(cluster)
        window_start = ordered[0].timestamp
        window_end = ordered[-1].timestamp
        source_ips = sorted({event.source_ip for event in ordered})
        hours = sorted({event.timestamp.hour for event in ordered})
        evidence = cluster_window_evidence(
            ordered,
            {
                "username": username,
                "source_ips": source_ips,
                "success_count": len(ordered),
                "reason": reason,
                "utc_hours": hours,
                "hours_start_utc": self.hours_start_utc,
                "hours_end_utc": self.hours_end_utc,
                "min_successes": self.min_successes,
                "window_minutes": self.window_minutes,
            },
        )
        if reason == "off_hours":
            title = f"Off-hours login for {username}"
            description = (
                f"{len(ordered)} login_success event(s) for {username} outside "
                f"{self.hours_start_utc:02d}:00–{self.hours_end_utc:02d}:00 UTC "
                f"(hours {hours}) between {evidence['window_start']} and "
                f"{evidence['window_end']}. IPs: {', '.join(source_ips)}."
            )
        else:
            title = f"High-frequency logins for {username}"
            description = (
                f"{len(ordered)} login_success events for {username} between "
                f"{evidence['window_start']} and {evidence['window_end']} "
                f"(threshold: {self.min_successes} successes in "
                f"{self.window_minutes} minutes). IPs: {', '.join(source_ips)}."
            )
        return Incident(
            id=stable_incident_id(
                self.rule_id, f"{username}|{reason}", window_start, window_end
            ),
            rule_id=self.rule_id,
            severity=self.severity,
            title=title,
            description=description,
            evidence=evidence,
            created_at=window_end,
        )
