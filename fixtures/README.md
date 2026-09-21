# Fixtures

Sample **ThreatLens Auth Log (TLAL)** files for the parser and detection engine. These are synthetic. They are not live telemetry.

The Analyze page loads copies of the same files from `web/public/samples/` (not invented SOC events).

Format recap — one event per line:

```
<timestamp> <event_type> [key=value ...]
```

`event_type` is one of `login_success`, `login_failure`, `access_denied`, `request`. `ip=` is required. `user=-` means anonymous. Optional `country=` / `geo=` is a **simulated** location key for `impossible_travel` (not MaxMind). Lines starting with `#` are comments. JSON objects (schema field names) may appear in the same file. Full spec: [docs/log-schema.md](../docs/log-schema.md). Detection: [docs/detection.md](../docs/detection.md).

| Directory | File | What it contains | Detects |
| --- | --- | --- | --- |
| `normal/` | `auth.log` | Clean office-hours activity: successful logins, page requests, one isolated typo-then-success. **20** events, **0** parse errors. | No incidents |
| `bruteforce/` | `auth.log` | Burst of failed logins from a **single IP** (`203.0.113.77`) against alice (40) then bob (10). **50** `login_failure` events. | `brute_force` |
| `spray/` | `auth.log` | One failure each against **8** usernames from `198.51.100.66` over ~3.5 minutes. Below brute-force N=10. | `credential_spray` |
| `unusual_login/` | `auth.log` | alice two `login_success` at 03:xx UTC (off-hours); bob five daytime successes in ~2 minutes; carol one daytime success. **10** events. | `unusual_login` |
| `impossible_travel/` | `auth.log` | alice `country=US` then `geo=JP` 25 minutes later; bob two US logins; carol US→JP 2 hours apart. **Simulated geo.** **8** events. | `impossible_travel` |
| `request_frequency/` | `auth.log` | 50 `request` events from `203.0.113.99` in 49 seconds, plus a few other IPs. **54** events. | `request_frequency` |
| `restricted_access/` | `auth.log` | mallory `access_denied` to `/admin`, `/admin/users`, `/etc/passwd`; bob denied `/inbox`. **6** events. | `restricted_access` |
| `mixed/` | `auth.log` | Daytime normal traffic, a 20-failure burst from `203.0.113.77` (alice only), then more normal lines (including one JSON line). **33** events, **20** failures. | `brute_force` |
| `edge/` | `auth.log` | Malformed lines, missing fields, bad timestamps, invalid JSON/IP, plus a few valid text and JSON lines. Parser must not crash; expect both `events` and `errors`. | Not used as a detection fixture |

Thresholds: brute_force = 10 failures / 5 minutes; credential_spray = 5 distinct usernames / 10 minutes; unusual_login = outside 08:00–22:00 UTC **or** 5 successes / 10 minutes; impossible_travel = 2 simulated countries / 60 minutes; request_frequency = 50 requests / 1 minute; restricted_access = any `access_denied` to `/admin`, `/secrets`, `/etc/passwd`, `/.env`.
