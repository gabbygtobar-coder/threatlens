# Log schema

Normalized event produced by `api/app/parsing`. This is M1 only — parsing and
shape, not detection.

## `LogEvent`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `timestamp` | timezone-aware datetime | yes | Stored/serialized as UTC ISO-8601 with `Z` |
| `source_ip` | string | yes | IPv4 or IPv6 (`ipaddress` validation) |
| `username` | string or null | no | `user=-` or omitted → `null` |
| `event_type` | enum | yes | `login_success`, `login_failure`, `access_denied`, `request` |
| `user_agent` | string or null | no | |
| `resource` | string or null | no | Path or URL |
| `status_code` | int or null | no | HTTP-like, 100–599 |
| `raw` | string | yes | Original line, for later explainability |

Geo/country fields are omitted in M1 (unused until impossible-travel work).

Pydantic model: `api/app/models.py`.

## Text format — ThreatLens Auth Log (TLAL)

A small custom auth log, one event per line. Clarity over pretending to be Splunk.

```
<timestamp> <event_type> [key=value ...]
```

Example:

```
2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10
2024-01-15T03:12:02Z login_success user=alice ip=203.0.113.10 ua="Mozilla/5.0" resource=/login status=200
2024-01-15T03:12:03Z access_denied user=bob ip=198.51.100.7 resource=/admin status=403
2024-01-15T03:12:04Z request user=- ip=192.0.2.15 resource=/health status=200
```

- **timestamp** — ISO-8601 with timezone (`Z` preferred)
- **event_type** — same enum as the schema
- **ip=** — required
- **user=** — optional; `user=-` means anonymous
- **ua=** — optional; quote values that contain spaces
- **resource=** — optional
- **status=** — optional integer
- Unknown keys are ignored
- Blank lines and `#` comments are skipped
- Malformed lines are reported in `errors` and do not abort parsing

## JSON lines

A line whose first non-whitespace character is `{` is parsed as JSON using the
normalized field names (`timestamp`, `event_type`, `source_ip`, `username`,
`user_agent`, `resource`, `status_code`). `raw` is always the original line.

```
{"timestamp":"2024-01-15T03:12:01Z","event_type":"login_failure","source_ip":"203.0.113.10","username":"alice"}
```
