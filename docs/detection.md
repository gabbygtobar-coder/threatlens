# Detection engine

M3+ run **deterministic, explainable rules** over normalized `LogEvent` lists
from the M1 parser. There is no ML and no real geolocation. The engine itself is
still stateless; M4+ persistence is the Next.js app writing to Supabase (Option A).
M6 does not add rules.

## How it runs

1. `POST /detect` parses the body the same way as `POST /parse`.
2. `DetectionEngine` calls every registered `Rule.detect(events)`.
3. Incidents are concatenated and sorted by `(rule_id, created_at, id)`.

Rules are independent. A burst can match more than one rule if it meets each
rule’s thresholds. The shipped fixtures are shaped so that each named directory
trips **only** its own rule (and `normal/` trips none).

Each rule is a class with a `detect` method. New rules are a new class plus
registering it in `default_rules()` — not a rewrite of the engine.

Code: `api/app/detection/`.

## Incident model

`Incident` (`api/app/models.py`):

| Field | Notes |
| --- | --- |
| `id` | First 32 hex chars of `sha256(rule_id\|correlation_key\|window_start\|window_end)`. Same events → same id. Not a random UUID. |
| `rule_id` | See rules below |
| `severity` | Fixed per rule (no “barely over threshold” grading) |
| `status` | Always `open` (no workflow yet) |
| `title` / `description` | Human-readable summary including counts, keys, window, threshold |
| `evidence` | Structured dict (rule-specific; always includes `window_start` / `window_end` as UTC `Z`, `sample_raw`) |
| `created_at` | Timestamp of the **last contributing event** (window end), not wall-clock now |

## Rules and thresholds

GET `/rules` returns the same numbers (and restricted-path prefixes).

### `brute_force`

Many `login_failure` events from the **same `source_ip`** inside a sliding
window of **T minutes**.

| Knob | Default |
| --- | --- |
| `min_failures` (N) | **10** |
| `window_minutes` (T) | **5** |
| severity | `high` |

Correlation key is IP. Usernames, when present, go into evidence; they are not
required to match. Anonymous failures still count toward N.

Fixture: `fixtures/bruteforce/auth.log` — 50 failures from `203.0.113.77` in 49
seconds.

### `credential_spray`

At least **M distinct usernames** with `login_failure` from the **same
`source_ip`** inside a sliding window of **T minutes**.

| Knob | Default |
| --- | --- |
| `min_usernames` (M) | **5** |
| `window_minutes` (T) | **10** |
| severity | `high` |

Anonymous events (`username` null) do not count toward M.

Fixture: `fixtures/spray/auth.log` — 8 users × 1 failure from `198.51.100.66`
over 3.5 minutes. Below brute-force N=10, so only spray fires.

### `unusual_login`

Successful logins that are unusual by **time of day** and/or **frequency** for
a username. Not geo, not ML, not a learned per-user baseline.

Two predicates (either one fires; `evidence.reason` is `off_hours` or
`frequency`):

1. **Off-hours:** `login_success` whose UTC hour is **&lt; 08** or **≥ 22**
   (normal window is 08:00–22:00 UTC, end exclusive). One incident per username
   covering all off-hours successes in the batch.
2. **Frequency:** at least **N** `login_success` events for the **same
   username** inside **T minutes**.

Anonymous successes are ignored.

| Knob | Default |
| --- | --- |
| `hours_start_utc` | **8** |
| `hours_end_utc` | **22** |
| `min_successes` (N) | **5** |
| `window_minutes` (T) | **10** |
| severity | `medium` |

Fixture: `fixtures/unusual_login/auth.log` — alice at 03:11/03:42 UTC (off
hours); bob five daytime successes in ~2 minutes.

### `impossible_travel` (simulated)

Same username has `login_success` from **two or more distinct country keys**
inside **T minutes**.

**Locations are simulated.** This is not MaxMind GeoIP, not a real distance
calculation, and not ASN lookup. A location key is:

1. The optional `country` field on `LogEvent` (TLAL `country=` or `geo=`; JSON
   `country` or `geo`), or
2. Else a **static IP-prefix map** for documentation ranges: `203.0.113.*` →
   `US`, `198.51.100.*` → `DE`, `192.0.2.*` → `JP`, `2001:db8:*` → `GB`.

Events with no field and no prefix match are skipped. Evidence sets
`geo_simulated: true` and includes a `geo_note`.

| Knob | Default |
| --- | --- |
| `min_locations` | **2** |
| `window_minutes` (T) | **60** |
| severity | `high` |

Fixture: `fixtures/impossible_travel/auth.log` — alice `country=US` then
`geo=JP` 25 minutes later. Controls: bob two US logins; carol US→JP 2 hours
apart (outside T).

### `request_frequency`

Too many **`request`** events from the **same `source_ip`** inside **T
minutes**. Login events are ignored.

| Knob | Default |
| --- | --- |
| `min_requests` (N) | **50** |
| `window_minutes` (T) | **1** |
| severity | `medium` |

Fixture: `fixtures/request_frequency/auth.log` — 50 requests from
`203.0.113.99` in 49 seconds.

### `restricted_access`

**Policy:** fire on **any** `access_denied` whose `resource` matches a
configured sensitive prefix (exact match, or prefix followed by `/` or `?`).
`/admin` matches `/admin` and `/admin/users`, not `/administrator`.

Prefixes (code constant `RESTRICTED_RESOURCE_PREFIXES`): `/admin`, `/secrets`,
`/etc/passwd`, `/.env`.

Successful `request`s to those paths are **not** flagged — only denials. One
incident per source IP covering all matching denials in the batch.

| Knob | Default |
| --- | --- |
| `min_denials` | **1** |
| `restricted_prefixes` | `/admin`, `/secrets`, `/etc/passwd`, `/.env` |
| severity | `high` |

Fixture: `fixtures/restricted_access/auth.log` — mallory denied `/admin`,
`/admin/users`, `/etc/passwd`. bob’s `/inbox` 403 does not fire.

## Windowing

For sliding-window rules (`brute_force`, `credential_spray`, `unusual_login`
frequency, `impossible_travel`, `request_frequency`): events are sorted by
`(timestamp, source_ip, username, raw)`. A two-pointer pass finds every time
span ≤ T that meets the predicate. Overlapping qualifying spans merge into
**one** incident so a dense burst is a single finding. Two bursts farther
apart than T become two incidents.

“Within T minutes” means last − first ≤ T (inclusive).

A later `login_success` does **not** reset a failure window. Only the event
types each rule cares about are considered.

## Limitations

- Synthetic **ThreatLens Auth Log (TLAL)** only — not syslog, not Windows Event Log.
- **Impossible travel is a simulation** (fixture fields + static TEST-NET
  prefixes). There is no MaxMind DB, no real km/hour check, no VPN detection.
- Unusual login uses a global UTC office-hours window, not a per-user baseline.
- The API is still stateless: every `/detect` call is independent. Saving a run
  is a separate step in `web/` (Supabase RLS). The M5 UI only displays engine
  output and saved rows. See [auth-persistence.md](auth-persistence.md).
- Thresholds are fixed defaults (overridable in code/tests, not via API).

## Curl

```bash
# brute-force fixture
curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/bruteforce/auth.log

# credential-spray fixture
curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/spray/auth.log

curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/unusual_login/auth.log

curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/impossible_travel/auth.log

curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/request_frequency/auth.log

curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/restricted_access/auth.log

curl -sS http://127.0.0.1:8000/rules
```
