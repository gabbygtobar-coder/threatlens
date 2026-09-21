"""Credential spray: many usernames failing from one IP within a short window."""

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

SPRAY_MIN_USERNAMES = 5
SPRAY_WINDOW_MINUTES = 10


class CredentialSprayRule(Rule):
    rule_id = RuleId.CREDENTIAL_SPRAY
    title = "Credential spray"
    severity = Severity.HIGH

    def __init__(
        self,
        min_usernames: int = SPRAY_MIN_USERNAMES,
        window_minutes: int = SPRAY_WINDOW_MINUTES,
    ) -> None:
        self.min_usernames = min_usernames
        self.window_minutes = window_minutes
        self.description = (
            f"At least {min_usernames} distinct usernames with login_failure from the "
            f"same source IP within {window_minutes} minutes."
        )

    def thresholds(self) -> dict[str, int]:
        return {
            "min_usernames": self.min_usernames,
            "window_minutes": self.window_minutes,
        }

    def detect(self, events: Sequence[LogEvent]) -> list[Incident]:
        window = timedelta(minutes=self.window_minutes)
        incidents: list[Incident] = []
        for source_ip, group in group_by_source_ip(login_failures(events)).items():
            clusters = merged_qualifying_clusters(
                group,
                window,
                lambda cluster: len(distinct_usernames(cluster)) >= self.min_usernames,
            )
            for cluster in clusters:
                incidents.append(self._incident(source_ip, cluster))
        return incidents

    def _incident(self, source_ip: str, cluster: Sequence[LogEvent]) -> Incident:
        window_start = cluster[0].timestamp
        window_end = cluster[-1].timestamp
        users = distinct_usernames(cluster)
        evidence = evidence_payload(
            cluster,
            window_minutes=self.window_minutes,
            extra={"min_usernames": self.min_usernames},
        )
        return Incident(
            id=stable_incident_id(self.rule_id, source_ip, window_start, window_end),
            rule_id=self.rule_id,
            severity=self.severity,
            title=f"Credential spray from {source_ip}",
            description=(
                f"{len(users)} distinct usernames failed login from {source_ip} between "
                f"{evidence['window_start']} and {evidence['window_end']} "
                f"(threshold: {self.min_usernames} usernames in {self.window_minutes} minutes). "
                f"Usernames: {', '.join(users)}."
            ),
            evidence=evidence,
            created_at=window_end,
        )
