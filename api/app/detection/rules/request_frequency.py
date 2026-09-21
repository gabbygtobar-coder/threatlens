"""Request frequency: too many `request` events from one source IP in a short window."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import Any

from app.detection.base import (
    Rule,
    cluster_window_evidence,
    group_by_source_ip,
    merged_qualifying_clusters,
    request_events,
    sort_events,
    stable_incident_id,
)
from app.models import Incident, LogEvent, RuleId, Severity

REQUEST_FREQUENCY_MIN_REQUESTS = 50
REQUEST_FREQUENCY_WINDOW_MINUTES = 1


class RequestFrequencyRule(Rule):
    rule_id = RuleId.REQUEST_FREQUENCY
    title = "Request frequency"
    severity = Severity.MEDIUM

    def __init__(
        self,
        min_requests: int = REQUEST_FREQUENCY_MIN_REQUESTS,
        window_minutes: int = REQUEST_FREQUENCY_WINDOW_MINUTES,
    ) -> None:
        self.min_requests = min_requests
        self.window_minutes = window_minutes
        self.description = (
            f"At least {min_requests} request events from the same source IP "
            f"within {window_minutes} minute(s)."
        )

    def thresholds(self) -> dict[str, Any]:
        return {
            "min_requests": self.min_requests,
            "window_minutes": self.window_minutes,
        }

    def detect(self, events: Sequence[LogEvent]) -> list[Incident]:
        window = timedelta(minutes=self.window_minutes)
        incidents: list[Incident] = []
        for source_ip, group in group_by_source_ip(request_events(events)).items():
            clusters = merged_qualifying_clusters(
                group,
                window,
                lambda cluster: len(cluster) >= self.min_requests,
            )
            for cluster in clusters:
                incidents.append(self._incident(source_ip, cluster))
        return incidents

    def _incident(self, source_ip: str, cluster: Sequence[LogEvent]) -> Incident:
        ordered = sort_events(cluster)
        window_start = ordered[0].timestamp
        window_end = ordered[-1].timestamp
        resources = sorted({event.resource for event in ordered if event.resource})
        evidence = cluster_window_evidence(
            ordered,
            {
                "source_ip": source_ip,
                "request_count": len(ordered),
                "min_requests": self.min_requests,
                "window_minutes": self.window_minutes,
                "sample_resources": resources[:10],
            },
        )
        return Incident(
            id=stable_incident_id(self.rule_id, source_ip, window_start, window_end),
            rule_id=self.rule_id,
            severity=self.severity,
            title=f"High request frequency from {source_ip}",
            description=(
                f"{len(ordered)} request events from {source_ip} between "
                f"{evidence['window_start']} and {evidence['window_end']} "
                f"(threshold: {self.min_requests} requests in "
                f"{self.window_minutes} minute(s))."
            ),
            evidence=evidence,
            created_at=window_end,
        )
