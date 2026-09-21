"""Restricted access: any access_denied to a configured sensitive resource prefix."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.detection.base import (
    Rule,
    access_denied_events,
    cluster_window_evidence,
    distinct_usernames,
    group_by_source_ip,
    sort_events,
    stable_incident_id,
)
from app.models import Incident, LogEvent, RuleId, Severity

# Small allowlist of sensitive path prefixes. Match is exact or prefix + "/" or "?".
RESTRICTED_RESOURCE_PREFIXES: tuple[str, ...] = (
    "/admin",
    "/secrets",
    "/etc/passwd",
    "/.env",
)

RESTRICTED_ACCESS_MIN_DENIALS = 1


def resource_matches_restricted(
    resource: str | None,
    prefixes: Sequence[str] = RESTRICTED_RESOURCE_PREFIXES,
) -> str | None:
    """Return the matching prefix, or None. `/admin` does not match `/administrator`."""
    if not resource:
        return None
    for prefix in prefixes:
        if resource == prefix or resource.startswith(prefix + "/") or resource.startswith(
            prefix + "?"
        ):
            return prefix
    return None


class RestrictedAccessRule(Rule):
    rule_id = RuleId.RESTRICTED_ACCESS
    title = "Restricted access"
    severity = Severity.HIGH

    def __init__(
        self,
        prefixes: Sequence[str] = RESTRICTED_RESOURCE_PREFIXES,
        min_denials: int = RESTRICTED_ACCESS_MIN_DENIALS,
    ) -> None:
        self.prefixes = tuple(prefixes)
        self.min_denials = min_denials
        listed = ", ".join(self.prefixes)
        self.description = (
            f"Any access_denied to a restricted resource prefix ({listed}). "
            f"Fires at ≥ {min_denials} matching denial(s) per source IP in the batch."
        )

    def thresholds(self) -> dict[str, Any]:
        return {
            "min_denials": self.min_denials,
            "restricted_prefixes": list(self.prefixes),
        }

    def detect(self, events: Sequence[LogEvent]) -> list[Incident]:
        incidents: list[Incident] = []
        for source_ip, group in group_by_source_ip(access_denied_events(events)).items():
            matched: list[tuple[LogEvent, str]] = []
            for event in sort_events(group):
                prefix = resource_matches_restricted(event.resource, self.prefixes)
                if prefix:
                    matched.append((event, prefix))
            if len(matched) < self.min_denials:
                continue
            cluster = [event for event, _ in matched]
            prefixes = sorted({prefix for _, prefix in matched})
            incidents.append(self._incident(source_ip, cluster, prefixes))
        return incidents

    def _incident(
        self,
        source_ip: str,
        cluster: Sequence[LogEvent],
        matched_prefixes: Sequence[str],
    ) -> Incident:
        ordered = sort_events(cluster)
        window_start = ordered[0].timestamp
        window_end = ordered[-1].timestamp
        resources = sorted({event.resource for event in ordered if event.resource})
        users = distinct_usernames(ordered)
        evidence = cluster_window_evidence(
            ordered,
            {
                "source_ip": source_ip,
                "denial_count": len(ordered),
                "min_denials": self.min_denials,
                "matched_prefixes": list(matched_prefixes),
                "resources": resources,
                "usernames": users,
                "restricted_prefixes": list(self.prefixes),
            },
        )
        names = ", ".join(users) if users else "(anonymous)"
        return Incident(
            id=stable_incident_id(self.rule_id, source_ip, window_start, window_end),
            rule_id=self.rule_id,
            severity=self.severity,
            title=f"Restricted-path access denied from {source_ip}",
            description=(
                f"{len(ordered)} access_denied event(s) from {source_ip} to restricted "
                f"prefix(es) {', '.join(matched_prefixes)} "
                f"({evidence['window_start']} to {evidence['window_end']}). "
                f"Usernames: {names}. Resources: {', '.join(resources)}."
            ),
            evidence=evidence,
            created_at=window_end,
        )
