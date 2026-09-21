"""Normalized security log event schema.

See docs/log-schema.md for the field list, event types, and the text log format.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class EventType(str, Enum):
    """Small closed set of auth/access event types. Detection rules come in M2."""

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
    raw: str = Field(description="Original log line, kept for explainability")

    @field_serializer("timestamp")
    def _serialize_timestamp(self, value: datetime) -> str:
        aware = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        return aware.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class ParseFailure(BaseModel):
    """A single line the parser skipped, with a reason. The process does not abort."""

    line_number: int = Field(ge=1, description="1-based line number in the input")
    line: str = Field(description="Original line (may be truncated)")
    reason: str


class ParseResult(BaseModel):
    events: list[LogEvent]
    errors: list[ParseFailure]


class ParseRequest(BaseModel):
    """JSON body for POST /parse. text/plain bodies are also accepted."""

    text: str = Field(description="Raw log text, one event per line")
