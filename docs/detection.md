# Detection engine

M2 runs **deterministic, explainable rules** over normalized `LogEvent` lists
from the M1 parser. There is no ML, no geo, and no persistence.

## How it runs

1. `POST /detect` parses the body the same way as `POST /parse`.
2. `DetectionEngine` calls every registered `Rule.detect(events)`.
3. Incidents are concatenated and sorted by `(rule_id, created_at, id)`.

Rules are independent. A burst can match more than one rule if it meets each
rule’s thresholds. The shipped fixtures are shaped so that `bruteforce/` trips
only `brute_force` and `spray/` trips only `credential_spray`.

Each rule is a class with a `detect` method. Adding a later rule (unusual
login, impossible travel, …) means a new class plus registering it in
`default_rules()` — not a rewrite of the engine.

Code: `api/app/detection/`.

## Incident model

`Incident` (`api/app/models.py`):

| Field | Notes |
| --- | --- |
| `id` | First 32 hex chars of `sha256(rule_id\|source_ip\|window_start\|window_end)`. Same events → same id. Not a random UUID. |
| `rule_id` | `brute_force` or `credential_spray` |
| `severity` | Always `high` when the rule fires (no “barely over threshold” grading in M2) |
| `status` | Always `open` (no workflow yet) |
| `title` / `description` | Human-readable summary including counts, IP, window, threshold |
| `evidence` | Structured dict (see below) |
| `created_at` | Timestamp of the **last contributing event** (window end), not wall-clock now |

`evidence` always includes:

- `source_ip`
- `failure_count`
- `distinct_usernames`
- `usernames` (sorted, omits anonymous)
- `username_failure_counts`
- `window_start` / `window_end` (UTC `Z`)
- `window_minutes` (configured T)
- `sample_raw` (up to 5 original lines, earliest first)
- the rule-specific threshold (`min_failures` or `min_usernames`)

## Rules and thresholds

GET `/rules` returns the same numbers.

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

The bruteforce fixture is 50 failures from `203.0.113.77` in 49 seconds (40
against alice, 10 against bob) — well above N=10.

### `credential_spray`

At least **M distinct usernames** with `login_failure` from the **same
`source_ip`** inside a sliding window of **T minutes**.

| Knob | Default |
| --- | --- |
| `min_usernames` (M) | **5** |
| `window_minutes` (T) | **10** |
| severity | `high` |

Anonymous events (`username` null) do not count toward M.

The spray fixture is 8 users × 1 failure from `198.51.100.66` over 3.5 minutes.
That is above M=5 and **below** brute-force N=10, so only spray fires.

## Windowing

For each source IP, events are sorted by `(timestamp, source_ip, username, raw)`.
A two-pointer pass finds every time span ≤ T that meets the count/username
threshold. Overlapping qualifying spans merge into **one** incident so a dense
burst is a single finding, not one finding per sliding step. Two bursts farther
apart than T become two incidents.

“Within T minutes” means last − first ≤ T (inclusive).

A later `login_success` does **not** reset a failure window. Only
`login_failure` events are considered.

## Limitations

- Synthetic **ThreatLens Auth Log (TLAL)** only — not syslog, not Windows Event Log.
- No unusual-login, impossible-travel, request-frequency, or restricted-access rules.
- No geolocation, no ML, no baseline of “normal” per user.
- No persistence: every `/detect` call is stateless.
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

curl -sS http://127.0.0.1:8000/rules
```
