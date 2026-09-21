"""Normalized security log event schema and detection incident models.

See docs/log-schema.md for the field list, event types, and the text log format.
See docs/detection.md for incident shape, rule IDs, and thresholds.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def utc_z(value: datetime) -> str:
    """Serialize a datetime as UTC ISO-8601 with a Z suffix."""
    aware = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class EventType(str, Enum):
    """Small closed set of auth/access event types."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    ACCESS_DENIED = "access_denied"
    REQUEST = "request"


class LogEvent(BaseModel):
    """One normalized event produced by the parser."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(description="Timezone-aware event time (UTC in fixtures)")
    source_ip: str = Field(description="Client IPv4 or IPv6 address")
    username: str | None = Field(
        default=None, description="Actor username; null if omitted or user=-"
    )
    event_type: EventType
    user_agent: str | None = Field(default=None, description="Client user-agent, if present")
    resource: str | None = Field(default=None, description="Path or URL, if present")
    status_code: int | None = Field(default=None, description="HTTP-like status, if present")
    country: str | None = Field(
        default=None,
        description=(
            "Simulated location key from TLAL country=/geo= or JSON country/geo. "
            "Not MaxMind GeoIP — used by the impossible_travel demo rule."
        ),
    )
    raw: str = Field(description="Original log line, kept for explainability")

    @field_serializer("timestamp")
    def _serialize_timestamp(self, value: datetime) -> str:
        return utc_z(value)


class ParseFailure(BaseModel):
    """A single line the parser skipped, with a reason. The process does not abort."""

    line_number: int = Field(ge=1, description="1-based line number in the input")
    line: str = Field(description="Original line (may be truncated)")
    reason: str


class ParseResult(BaseModel):
    events: list[LogEvent]
    errors: list[ParseFailure]


class ParseRequest(BaseModel):
    """JSON body for POST /parse and POST /detect. text/plain bodies are also accepted."""

    text: str = Field(description="Raw log text, one event per line")


class RuleId(str, Enum):
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_SPRAY = "credential_spray"
    UNUSUAL_LOGIN = "unusual_login"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    REQUEST_FREQUENCY = "request_frequency"
    RESTRICTED_ACCESS = "restricted_access"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    OPEN = "open"


class Incident(BaseModel):
    """One detection finding. Same events always produce the same incident payload.

    `id` is a 32-character SHA-256 prefix of
    ``rule_id|correlation_key|window_start|window_end`` (UTC Z timestamps), not a
    random UUID. The correlation key is typically a source IP or username.

    `created_at` is the last contributing event's timestamp (the window end), not
    wall-clock now, so the result is reproducible.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    rule_id: RuleId
    severity: Severity
    status: IncidentStatus = IncidentStatus.OPEN
    title: str
    description: str
    evidence: dict[str, Any] = Field(
        description=(
            "Structured proof: correlation keys, counts, window_start/end, "
            "thresholds, sample_raw, etc."
        )
    )
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime) -> str:
        return utc_z(value)


class DetectResult(BaseModel):
    events_count: int
    incidents: list[Incident]
    parse_errors: list[ParseFailure]


class RuleInfo(BaseModel):
    rule_id: RuleId
    title: str
    description: str
    severity: Severity
    thresholds: dict[str, Any]


class RulesResponse(BaseModel):
    rules: list[RuleInfo]
