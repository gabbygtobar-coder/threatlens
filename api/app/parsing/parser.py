"""ThreatLens Auth Log (TLAL) parser.

Accepts a documented custom text format and JSON lines. Malformed lines become
ParseFailure entries; they never abort the rest of the file.

Text format (one event per line):

    <timestamp> <event_type> [key=value ...]

    2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10

Timestamp is ISO-8601 with a timezone (prefer Z). Event type is one of
login_success, login_failure, access_denied, request.

Keys:
    ip        required  IPv4 or IPv6
    user      optional  username; omit or user=- for anonymous
    ua        optional  user-agent (quote if it contains spaces)
    resource  optional  path or URL
    status    optional  integer status code
    country   optional  simulated location key (ISO-like code); alias: geo=

Blank lines and lines whose first non-whitespace character is # are skipped.
JSON lines start with { and use the normalized field names (timestamp,
event_type, source_ip, username, user_agent, resource, status_code, country
or geo).
"""

from __future__ import annotations

import ipaddress
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.models import EventType, LogEvent, ParseFailure, ParseResult

MAX_LINE_LENGTH = 8192
MAX_STORED_LINE = 500

_FIELD_RE = re.compile(
    r'(?P<key>[A-Za-z_][A-Za-z0-9_]*)='
    r'(?:"(?P<quoted>(?:\\.|[^"\\])*)"|(?P<bare>\S+))'
)
_UNESCAPE_RE = re.compile(r'\\([\\"])')

_JSON_OBJECT_PREFIX = "{"


def parse_path(path: Path | str) -> ParseResult:
    """Parse a UTF-8 log file."""
    return parse_text(Path(path).read_text(encoding="utf-8"))


def parse_text(text: str) -> ParseResult:
    """Parse a multi-line log blob into events and per-line errors."""
    events: list[LogEvent] = []
    errors: list[ParseFailure] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if len(line) > MAX_LINE_LENGTH:
            errors.append(
                ParseFailure(
                    line_number=line_number,
                    line=_clip(line),
                    reason=f"Line exceeds {MAX_LINE_LENGTH} character limit",
                )
            )
            continue
        try:
            events.append(parse_line(stripped))
        except ValueError as exc:
            errors.append(
                ParseFailure(line_number=line_number, line=_clip(stripped), reason=str(exc))
            )

    return ParseResult(events=events, errors=errors)


def parse_line(line: str) -> LogEvent:
    """Parse a single non-empty log line. Raises ValueError on failure."""
    stripped = line.strip()
    if not stripped:
        raise ValueError("Empty line")
    if stripped.startswith(_JSON_OBJECT_PREFIX):
        return _parse_json_line(stripped)
    return _parse_text_line(stripped)


def _parse_text_line(line: str) -> LogEvent:
    parts = line.split(None, 2)
    if len(parts) < 2:
        raise ValueError("Line must be '<timestamp> <event_type> [key=value ...]'")

    timestamp = _parse_timestamp(parts[0])
    event_type = _parse_event_type(parts[1])
    fields = _parse_fields(parts[2] if len(parts) == 3 else "")
    # Extra keys are ignored so the format can grow without breaking M1 fixtures.

    source_ip = fields.get("ip")
    if not source_ip:
        raise ValueError("Missing required field ip=")
    source_ip = _parse_ip(source_ip)

    username = _normalize_username(fields.get("user"))
    user_agent = fields.get("ua") or None
    resource = fields.get("resource") or None
    status_code = _parse_status(fields.get("status")) if "status" in fields else None
    country = _parse_country(fields.get("country"), fields.get("geo"))

    return LogEvent(
        timestamp=timestamp,
        source_ip=source_ip,
        username=username,
        event_type=event_type,
        user_agent=user_agent,
        resource=resource,
        status_code=status_code,
        country=country,
        raw=line,
    )


def _parse_json_line(line: str) -> LogEvent:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("JSON line must be an object")

    required = ("timestamp", "event_type", "source_ip")
    missing = [key for key in required if key not in payload or payload[key] in (None, "")]
    if missing:
        raise ValueError(f"JSON missing required field(s): {', '.join(missing)}")

    timestamp = payload["timestamp"]
    if not isinstance(timestamp, str):
        raise ValueError("JSON timestamp must be an ISO-8601 string")

    return LogEvent(
        timestamp=_parse_timestamp(timestamp),
        source_ip=_parse_ip(str(payload["source_ip"])),
        username=_normalize_username(payload.get("username")),
        event_type=_parse_event_type(str(payload["event_type"])),
        user_agent=_optional_str(payload.get("user_agent")),
        resource=_optional_str(payload.get("resource")),
        status_code=_parse_status(payload.get("status_code"))
        if payload.get("status_code") is not None
        else None,
        country=_parse_country(payload.get("country"), payload.get("geo")),
        raw=line,
    )


def _parse_fields(field_str: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    pos = 0
    length = len(field_str)
    while pos < length:
        while pos < length and field_str[pos].isspace():
            pos += 1
        if pos >= length:
            break
        match = _FIELD_RE.match(field_str, pos)
        if not match:
            snippet = field_str[pos : pos + 40]
            raise ValueError(f"Invalid field syntax near {snippet!r}")
        if match.group("quoted") is not None:
            value = _UNESCAPE_RE.sub(r"\1", match.group("quoted"))
        else:
            value = match.group("bare")
        fields[match.group("key")] = value
        pos = match.end()
    return fields


def _parse_timestamp(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp {value!r} (need ISO-8601 with timezone)") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp {value!r} is missing a timezone (use Z or an offset)")
    return parsed.astimezone(timezone.utc)


def _parse_event_type(value: str) -> EventType:
    try:
        return EventType(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in EventType)
        raise ValueError(f"Unknown event_type {value!r}; expected one of: {allowed}") from exc


def _parse_ip(value: str) -> str:
    try:
        return str(ipaddress.ip_address(value))
    except ValueError as exc:
        raise ValueError(f"Invalid IP address {value!r}") from exc


def _parse_status(value: object) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError("status must be an integer")
    if isinstance(value, int):
        code = value
    elif isinstance(value, str) and value.isdigit():
        code = int(value)
    else:
        raise ValueError(f"Invalid status {value!r}")
    if not 100 <= code <= 599:
        raise ValueError(f"status {code} is outside 100–599")
    return code


def _normalize_username(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("username must be a string")
    stripped = value.strip()
    if stripped in ("", "-"):
        return None
    return stripped


def _parse_country(country: object, geo: object = None) -> str | None:
    """Optional simulated location. `country` wins over `geo`. Stored uppercase."""
    raw = country if country not in (None, "") else geo
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise ValueError("country/geo must be a string")
    stripped = raw.strip()
    if stripped in ("", "-"):
        return None
    return stripped.upper()


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("expected a string")
    stripped = value.strip()
    return stripped or None


def _clip(line: str) -> str:
    if len(line) <= MAX_STORED_LINE:
        return line
    return line[:MAX_STORED_LINE] + "…"
