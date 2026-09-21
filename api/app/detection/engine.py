"""Run registered detection rules and aggregate incidents."""

from __future__ import annotations

from collections.abc import Sequence

from app.detection.base import Rule
from app.detection.rules.brute_force import BruteForceRule
from app.detection.rules.credential_spray import CredentialSprayRule
from app.detection.rules.impossible_travel import ImpossibleTravelRule
from app.detection.rules.request_frequency import RequestFrequencyRule
from app.detection.rules.restricted_access import RestrictedAccessRule
from app.detection.rules.unusual_login import UnusualLoginRule
from app.models import Incident, LogEvent, RuleInfo


def default_rules() -> list[Rule]:
    return [
        BruteForceRule(),
        CredentialSprayRule(),
        UnusualLoginRule(),
        ImpossibleTravelRule(),
        RequestFrequencyRule(),
        RestrictedAccessRule(),
    ]


class DetectionEngine:
    """Runs each rule in registration order and returns a stable incident list.

    Sort key: (rule_id, created_at, id). Rules are independent — the same burst
    can match more than one rule if it meets each rule's thresholds.
    """

    def __init__(self, rules: Sequence[Rule] | None = None) -> None:
        self.rules: list[Rule] = list(rules) if rules is not None else default_rules()

    def run(self, events: Sequence[LogEvent]) -> list[Incident]:
        incidents: list[Incident] = []
        for rule in self.rules:
            incidents.extend(rule.detect(events))
        incidents.sort(key=lambda item: (item.rule_id.value, item.created_at, item.id))
        return incidents

    def rule_info(self) -> list[RuleInfo]:
        return [rule.info() for rule in self.rules]


def default_engine() -> DetectionEngine:
    return DetectionEngine()
