"""Impossible travel — SIMULATED locations, not MaxMind GeoIP.

Same username has successful logins from two different country keys within T
minutes. Location comes from fixture `country=` / `geo=` fields, or a static
TEST-NET IP-prefix map. This is a portfolio demo.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import Any

from app.detection.base import (
    Rule,
    cluster_window_evidence,
    group_by_username,
    login_successes,
    merged_qualifying_clusters,
    sort_events,
    stable_incident_id,
)
from app.models import Incident, LogEvent, RuleId, Severity, utc_z

IMPOSSIBLE_TRAVEL_WINDOW_MINUTES = 60
IMPOSSIBLE_TRAVEL_MIN_LOCATIONS = 2

# Static demo map only. Documentation must keep calling this simulated.
SIMULATED_IP_PREFIX_COUNTRY: tuple[tuple[str, str], ...] = (
    ("203.0.113.", "US"),
    ("198.51.100.", "DE"),
    ("192.0.2.", "JP"),
    ("2001:db8:", "GB"),
)

GEO_NOTE = (
    "Simulated location: fixture country=/geo= field, else a static IP-prefix "
    "map (TEST-NET / documentation ranges). Not MaxMind GeoIP."
)


def simulated_location(event: LogEvent) -> str | None:
    """Country key for an event. Explicit field wins over the IP-prefix map."""
    if event.country:
        return event.country
    ip = event.source_ip
    for prefix, country in SIMULATED_IP_PREFIX_COUNTRY:
        if ip.startswith(prefix):
            return country
    return None


class ImpossibleTravelRule(Rule):
    rule_id = RuleId.IMPOSSIBLE_TRAVEL
    title = "Impossible travel (simulated)"
    severity = Severity.HIGH

    def __init__(
        self,
        window_minutes: int = IMPOSSIBLE_TRAVEL_WINDOW_MINUTES,
        min_locations: int = IMPOSSIBLE_TRAVEL_MIN_LOCATIONS,
    ) -> None:
        self.window_minutes = window_minutes
        self.min_locations = min_locations
        self.description = (
            f"At least {min_locations} distinct simulated countries on login_success "
            f"for the same username within {window_minutes} minutes. Locations are "
            "fixture country=/geo= values or a static IP-prefix map — not GeoIP."
        )

    def thresholds(self) -> dict[str, Any]:
        return {
            "min_locations": self.min_locations,
            "window_minutes": self.window_minutes,
        }

    def detect(self, events: Sequence[LogEvent]) -> list[Incident]:
        located: list[LogEvent] = []
        for event in login_successes(events):
            if not event.username:
                continue
            if simulated_location(event) is None:
                continue
            located.append(event)

        window = timedelta(minutes=self.window_minutes)
        incidents: list[Incident] = []
        for username, group in group_by_username(located).items():
            clusters = merged_qualifying_clusters(
                group,
                window,
                lambda cluster: len(_distinct_locations(cluster)) >= self.min_locations,
            )
            for cluster in clusters:
                incidents.append(self._incident(username, cluster))
        return incidents

    def _incident(self, username: str, cluster: Sequence[LogEvent]) -> Incident:
        ordered = sort_events(cluster)
        window_start = ordered[0].timestamp
        window_end = ordered[-1].timestamp
        locations = _distinct_locations(ordered)
        hops = [
            {
                "timestamp": utc_z(event.timestamp),
                "source_ip": event.source_ip,
                "country": simulated_location(event),
            }
            for event in ordered
        ]
        source_ips = sorted({event.source_ip for event in ordered})
        evidence = cluster_window_evidence(
            ordered,
            {
                "username": username,
                "source_ips": source_ips,
                "locations": locations,
                "location_count": len(locations),
                "min_locations": self.min_locations,
                "window_minutes": self.window_minutes,
                "hops": hops,
                "geo_simulated": True,
                "geo_note": GEO_NOTE,
            },
        )
        return Incident(
            id=stable_incident_id(self.rule_id, username, window_start, window_end),
            rule_id=self.rule_id,
            severity=self.severity,
            title=f"Impossible travel (simulated) for {username}",
            description=(
                f"{username} had login_success from {len(locations)} simulated "
                f"countries ({', '.join(locations)}) within {self.window_minutes} "
                f"minutes ({evidence['window_start']} to {evidence['window_end']}). "
                f"{GEO_NOTE}"
            ),
            evidence=evidence,
            created_at=window_end,
        )


def _distinct_locations(events: Sequence[LogEvent]) -> list[str]:
    seen: list[str] = []
    for event in sort_events(events):
        loc = simulated_location(event)
        if loc and loc not in seen:
            seen.append(loc)
    return seen
