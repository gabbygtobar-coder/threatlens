# Fixtures

Sample **ThreatLens Auth Log (TLAL)** files for the M1 parser (and later M2 detection). These are synthetic. They are not live telemetry and M1 does not raise alerts from them.

Format recap — one event per line:

```
<timestamp> <event_type> [key=value ...]
```

`event_type` is one of `login_success`, `login_failure`, `access_denied`, `request`. `ip=` is required. `user=-` means anonymous. Lines starting with `#` are comments. JSON objects (schema field names) may appear in the same file. Full spec: [docs/log-schema.md](../docs/log-schema.md).

| Directory | File | What it contains |
| --- | --- | --- |
| `normal/` | `auth.log` | Clean office-hours activity: successful logins, page requests, one isolated typo-then-success. **20** events, **0** parse errors. |
| `bruteforce/` | `auth.log` | Burst of failed logins from a **single IP** (`203.0.113.77`) against alice (40) then bob (10). **50** `login_failure` events, **0** parse errors. Parser only — no detection in M1. |
| `mixed/` | `auth.log` | Daytime normal traffic, a 20-failure burst from `203.0.113.77`, then more normal lines (including one JSON line). **33** events, **0** parse errors, **20** failures. |
| `edge/` | `auth.log` | Malformed lines, missing fields, bad timestamps, invalid JSON/IP, plus a few valid text and JSON lines. Parser must not crash; expect both `events` and `errors`. |

Do not treat `bruteforce/` or `mixed/` as engine output. Detection is M2.
