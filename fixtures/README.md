# Fixtures

Sample **ThreatLens Auth Log (TLAL)** files for the parser and M2 detection engine. These are synthetic. They are not live telemetry.

Format recap — one event per line:

```
<timestamp> <event_type> [key=value ...]
```

`event_type` is one of `login_success`, `login_failure`, `access_denied`, `request`. `ip=` is required. `user=-` means anonymous. Lines starting with `#` are comments. JSON objects (schema field names) may appear in the same file. Full spec: [docs/log-schema.md](../docs/log-schema.md). Detection: [docs/detection.md](../docs/detection.md).

| Directory | File | What it contains | M2 |
| --- | --- | --- | --- |
| `normal/` | `auth.log` | Clean office-hours activity: successful logins, page requests, one isolated typo-then-success. **20** events, **0** parse errors. | No incidents |
| `bruteforce/` | `auth.log` | Burst of failed logins from a **single IP** (`203.0.113.77`) against alice (40) then bob (10). **50** `login_failure` events, **0** parse errors. | `brute_force` |
| `spray/` | `auth.log` | One failure each against **8** usernames from `198.51.100.66` over ~3.5 minutes. **8** events, **0** parse errors. Below brute-force N=10. | `credential_spray` |
| `mixed/` | `auth.log` | Daytime normal traffic, a 20-failure burst from `203.0.113.77` (alice only), then more normal lines (including one JSON line). **33** events, **0** parse errors, **20** failures. | `brute_force` |
| `edge/` | `auth.log` | Malformed lines, missing fields, bad timestamps, invalid JSON/IP, plus a few valid text and JSON lines. Parser must not crash; expect both `events` and `errors`. | No incidents |

Thresholds: brute_force = 10 failures / 5 minutes; credential_spray = 5 distinct usernames / 10 minutes.
