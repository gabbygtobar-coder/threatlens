"""Brute-force login: many failures from one IP within a short window."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta

from app.detection.base import (
    Rule,
    distinct_usernames,
    evidence_payload,
    group_by_source_ip,
    login_failures,
    merged_qualifying_clusters,
    stable_incident_id,
)
from app.models import Incident, LogEvent, RuleId, Severity

BRUTE_FORCE_MIN_FAILURES = 10
BRUTE_FORCE_WINDOW_MINUTES = 5


class BruteForceRule(Rule):
    rule_id = RuleId.BRUTE_FORCE
    title = "Brute-force login"
    severity = Severity.HIGH

    def __init__(
        self,
        min_failures: int = BRUTE_FORCE_MIN_FAILURES,
        window_minutes: int = BRUTE_FORCE_WINDOW_MINUTES,
    ) -> None:
        self.min_failures = min_failures
        self.window_minutes = window_minutes
        self.description = (
            f"At least {min_failures} login_failure events from the same source IP "
            f"within {window_minutes} minutes."
        )

    def thresholds(self) -> dict[str, int]:
        return {
            "min_failures": self.min_failures,
            "window_minutes": self.window_minutes,
        }

    def detect(self, events: Sequence[LogEvent]) -> list[Incident]:
        window = timedelta(minutes=self.window_minutes)
        incidents: list[Incident] = []
        for source_ip, group in group_by_source_ip(login_failures(events)).items():
            clusters = merged_qualifying_clusters(
                group,
                window,
                lambda cluster: len(cluster) >= self.min_failures,
            )
            for cluster in clusters:
                incidents.append(self._incident(source_ip, cluster))
        return incidents

    def _incident(self, source_ip: str, cluster: Sequence[LogEvent]) -> Incident:
        window_start = cluster[0].timestamp
        window_end = cluster[-1].timestamp
        evidence = evidence_payload(
            cluster,
            window_minutes=self.window_minutes,
            extra={"min_failures": self.min_failures},
        )
        users = distinct_usernames(cluster)
        names = ", ".join(users) if users else "(none)"
        return Incident(
            id=stable_incident_id(self.rule_id, source_ip, window_start, window_end),
            rule_id=self.rule_id,
            severity=self.severity,
            title=f"Brute-force login from {source_ip}",
            description=(
                f"{len(cluster)} login_failure events from {source_ip} between "
                f"{evidence['window_start']} and {evidence['window_end']} "
                f"(threshold: {self.min_failures} failures in {self.window_minutes} minutes). "
                f"Usernames: {names}."
            ),
            evidence=evidence,
            created_at=window_end,
        )
