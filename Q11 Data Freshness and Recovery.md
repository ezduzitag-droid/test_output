---
type: research-record
ids: [Q11-A, Q11-B]
category: Data Integrity
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q11 Data Freshness and Recovery

Data freshness monitoring answers "is the data still arriving?"; data recovery answers "how do we get it back safely when it stops?". This record defines per-(venue, symbol, timeframe) freshness thresholds from bar period, session schedules, and an ingest-latency buffer, evaluated only while the session is open so expected gaps (weekends, holidays, maintenance) are never mistaken for staleness. It then defines the recovery loop: bounded jittered retries (per the canonical AWS analysis), reconnection, calendar-driven backfill via idempotent upserts, verification via the Q10 gate and source reconciliation. A recurring verified theme: process health and data health differ — a pipeline can run green while its source silently stops sending, so freshness must be measured on the data itself (age of the newest event timestamp) — the pattern GX formalizes as a freshness dimension and Flink via stalled watermarks.

## Question IDs

- **Q11-A** — Freshness thresholds per market/asset/timeframe; silent-stall detection.
- **Q11-B** — Automated recovery: retries, reconnection, backfill, verification.

## Original research questions

- **Q11-A** (verbatim): "How should our bot calculate acceptable data freshness thresholds for each market, asset, and timeframe, and how should it recognize when an otherwise healthy data pipeline has stopped receiving updated information?"
- **Q11-B** (verbatim): "What automated recovery process should occur when historical data collection or market-data ingestion fails, including retrying requests, reconnecting sources, backfilling missing records, and verifying recovered information?"

## Research objective

**Q11-A.** Establish a per-source formula for "how old may the newest record be before we call this stale", conditioned on session state, plus a stall detector measuring data arrival, not process liveness. Both failure directions are expensive: weekend alerts are fatigue; missed stalls mean training (or trading) on stale features diverging from the market. Affects A, B, F, J, K, L.

**Q11-B.** Establish the recovery sequence — classify failure, retry with bounded jittered backoff, reconnect, backfill, verify — including idempotent write semantics and trustworthy verification. Naive recovery creates the defects Q10 hunts (retry duplicates, abandoned gaps, corrupted backfills); hammering a rate-limited API risks bans. Affects A, B, J, K, L.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit locally before implementation:

- [ ] Freshness checks at all (age of newest record), or only process-liveness?
- [ ] Heartbeats / last-success timestamps distinct from the newest event timestamp?
- [ ] Session awareness: any code distinguishing "market closed" from "stale"?
- [ ] Retry logic: exponential? Jitter? Caps? 429/Retry-After honored?
- [ ] Stream consumers: heartbeat timeouts, resubscribe, REST-snapshot reconciliation after reconnect?
- [ ] Backfill machinery: gap detection, chunking, rate limiting; idempotent upserts (unique key)?
- [ ] Recovery verification (re-validation, reconciliation)? After N failures: breaker/alert/halt, no infinite loops?

## Technical concepts

- **Data freshness**: age of the newest ingested event vs a per-source expectation. **Staleness**: freshness exceeding its threshold.
- **Expected gap**: absence of records explained by the market calendar (closed session, holiday, maintenance) — not staleness.
- **Freshness SLA/SLO**: threshold plus required attainment.
- **Trading calendar / session schedule**: per-venue open/close, holidays, half-days (pandas_market_calendars domain).
- **Heartbeat**: periodic proof a producer/consumer is alive — distinct from **data arrival**, which proves delivery.
- **Watermark**: Flink's "all events up to time X have arrived" tracker; stalled means no new data.
- **Silent failure**: pipeline healthy while no data flows — what Q11-A must catch.
- **Exponential backoff**: multiplying wait by a constant after each failure, up to a cap. **Jitter**: randomness flattening synchronized retry spikes ("thundering herd"); variants: **full** (sleep uniform in [0, backoff]), **equal**, **decorrelated**.
- **Circuit breaker**: after repeated failures, stop calling the source for a cool-down; bounded retries: max attempts/time, then escalation.
- **Idempotency**: the same write twice has the effect of once — what makes retry-then-backfill safe. **Upsert**: insert-or-update on a key.
- **Backfill**: inserting missing historical ranges. **Recovery verification / reconciliation**: re-validating recovered data and comparing store vs source by counts or checksums.
- **Rate limit / Retry-After**: server-imposed request caps; HTTP 429 may carry a delay the client must honor.

## Research findings

### Q11-A findings

1. **Freshness is a recognized first-class data-quality dimension.** GX documents "Validate data freshness with GX… catch staleness issues early," with per-dataset thresholds [ESTABLISHED, GX freshness docs].
2. **The correct staleness signal is the age of the newest event timestamp.** Flink grounds event time ("the time that each individual event occurred on its producing device") vs the machine's clock; a stalled stream is the maximum event time ceasing to advance [ESTABLISHED, Flink docs; stall interpretation ours]. A running process with no new rows is the silent failure in question [INTERPRETATION].
3. **Session-awareness must be built into thresholds**: a freshness limit only applies while the session is open [ESTABLISHED calendars: schedules for 50+ venues]. Crypto venues are 24/7 but have maintenance windows — each needs its own expected-gap model [INTERPRETATION].
4. **A workable threshold formula** [INTERPRETATION]: `limit(venue, symbol, timeframe) = K × bar_period + ingest_buffer`, K ≈ 2–3, buffer = observed p99 receive latency. A 1-minute crypto candle might get ~3 minutes; a daily candle is judged vs the expected post-close update time. Baselined from real arrival distributions before freezing.
5. **Group-level reasoning separates single-asset from venue-wide stalls** [INTERPRETATION]: many symbols stale on one venue → connection/venue down; one symbol stale while peers flow → symbol-specific (halt, delisting).
6. **Escalation uses consecutive missed windows** [INTERPRETATION]: the alert ladder (warn → page → suspend) grows with the miss counter, so blips never page.
7. **Documented disagreement on alerting basis:** pipeline exceptions are cheap but blind to silent stalls; GX argues freshness belongs in data validation. Resolution: keep both, but only the data-age check may declare staleness [CONTESTED; resolution given].

### Q11-B findings

1. **Bounded exponential backoff with jitter is the verified retry standard.** The AWS analysis (Brooker, 2015): capped backoff alone leaves synchronized retry clusters, while **full jitter** performed best in simulations — "reduced our call count by more than half" — and "should be considered a standard approach for remote clients" [ESTABLISHED, AWS blog].
2. **Idempotent writes make retries and backfills safe.** PostgreSQL defines `INSERT ... ON CONFLICT DO UPDATE` as UPSERT guaranteeing "an atomic INSERT or UPDATE outcome" [ESTABLISHED, PostgreSQL docs]. Keying candles on (symbol, event_ts, timeframe) means retried requests or repeated backfills can never duplicate rows [key design INTERPRETATION].
3. **Rate-limit compliance is part of retry design**: honor `Retry-After`, chunk backfills, pace under documented limits; violations risk API bans turning an outage into a week-long gap [INTERPRETATION].
4. **Reconnection follows snapshot-then-delta** [INTERPRETATION; common venue-stream pattern]: fetch a REST snapshot, resume the stream, reconcile the disconnect gap; heartbeat timeouts catch connected-but-silent streams.
5. **Backfill is calendar-driven and oldest-first** [INTERPRETATION]: scan expected-vs-actual bars using session calendars, prioritize oldest gaps, fetch chunked and rate-limited, write idempotently.
6. **Recovery verification reuses the validation gate**: recovered ranges pass the Q10 rules; reconcile vs source (counts, checksums); spot-check high-severity ranges vs a secondary vendor; rows carry provenance [INTERPRETATION].
7. **Retry limits close the loop** [INTERPRETATION]: after N attempts the loop stops — source marked down, breaker opens, supervisor escalates; escalations log the failure class.
8. **Documented tension: automatic overwrite vs vintage preservation** — Q09 established corrections must be versioned or training data silently changes. Resolution: restating upserts append new versions; plain upserts only for never-existing rows [CONTESTED; resolution given].

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|---|---|---|---|---|---|---|
| 1 | Validate data freshness with GX | Great Expectations | current docs; accessed 2026-11-21 | https://docs.greatexpectations.io/docs/reference/learn/data_quality_use_cases/freshness | Freshness/staleness as a first-class checkable dimension; per-dataset thresholds | Generic; no trading-calendar awareness | YES (search-verified) |
| 2 | Exponential Backoff and Jitter | Marc Brooker (AWS Architecture Blog) | 2015-03-04 | https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter | Capped backoff alone insufficient; full jitter best in simulations (>50% call-count reduction) | Simulation-based (OCC setting); not market-specific | YES (fetched) |
| 3 | INSERT — PostgreSQL docs | PostgreSQL Global Development Group | current docs; accessed 2026-11-21 | https://www.postgresql.org/docs/current/sql-insert.html | `ON CONFLICT DO UPDATE` = atomic UPSERT, the primitive for idempotent ingestion | SQL-specific; append-versioned designs need careful conflict targets | YES (search-verified) |
| 4 | pandas_market_calendars documentation | rsheftel et al. | current docs; accessed 2026-11-21 | https://pandas-market-calendars.readthedocs.io | Session schedules, holidays, 50+ calendars — basis for expected-gap logic | Calendars must match venues traded; 24/7 venues need custom ones | YES (search-verified) |
| 5 | Timely Stream Processing | Apache Flink | stable docs; accessed 2026-11-21 | https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time | Event time vs processing time; event time authoritative; watermarks | Streaming vocabulary; stall→staleness mapping is ours | YES (search-verified) |

**Notes.** AWS (2) is the retry backbone: simulation-backed, directly implementable. PostgreSQL (3) authoritatively defines the atomic upsert making retry-and-backfill idempotent. GX (1) shows freshness checks are mainstream practice. pandas_market_calendars (4) separates expected gaps from true staleness; Flink (5) makes "the newest event stopped advancing" measurable.

**Established vs experimental vs interpretation.** Established: jittered bounded backoff; atomic upsert; freshness as a checkable dimension; session schedules; event-time semantics. Experimental: vendor-specific reconnection/correction behaviors (verify per API). Interpretation (ours): threshold formula, miss-counter escalation, stall classification, snapshot-then-delta recovery, verification protocol, versioned recovery upserts.

## How the technique works

**Freshness checker (Q11-A).** Per (venue, symbol, timeframe): (1) query `max(event_ts)`; (2) ask the calendar whether a session is open; (3) if closed → report `EXPECTED_GAP`, reset counters; (4) if open → compute `age = now − max(event_ts)` in bar units vs `limit = K × bar_period + ingest_buffer`; (5) if exceeded, increment the consecutive-miss counter and apply the alert ladder; (6) per-venue group stats (fraction stale) classify single-asset vs venue-wide stalls. Process metrics are kept; only data age may declare staleness.

**Recovery loop (Q11-B).** (1) Classify the failure (network, auth, rate limit, malformed data, outage); (2) retry transient classes with bounded full-jitter backoff: `sleep = random_uniform(0, min(cap, base × 2^attempt))`, honoring `Retry-After`; (3) on exhaustion open a breaker and escalate; (4) on disconnect: reconnect with heartbeat timeouts, resubscribe, fetch a REST snapshot, reconcile the gap; (5) calendar-driven backfill of missing ranges, oldest first, chunked, rate-limited; (6) idempotent upserts keyed on (symbol, event_ts, timeframe); (7) verify: re-run the Q10 gate, reconcile counts/checksums vs source, spot-check vs a secondary vendor; (8) record provenance and a recovery report. **Strengths:** bounded, safe, auditable. **Limitations:** needs correct calendars/clocks; cannot recover source-side losses; verification thresholds need baselining. **Computational:** freshness is one aggregate query per slice; backfill is network-bound (rate limits dominate). **Failure conditions:** wrong idempotency key (duplicates), clock skew (false freshness), calendar errors (false gaps), a source serving wrong data (only cross-source checks catch it).

## Reference implementation sketch

Runnable core, pandas + stdlib; the storage snippet is PostgreSQL SQL. Point-in-time safe: never fabricates values; recovered rows keep provenance.

```python
import random, time
import pandas as pd

def staleness_bars(last_event_ts, now_ts, timeframe, session_open):
    """Freshness in bar units. None when market closed: an expected gap, NOT staleness.
    limit = K * bar_period + ingest_buffer (K~2-3; buffer = observed p99 ingest latency)."""
    if not session_open:                 # calendar state injected by the caller
        return None
    return (now_ts - last_event_ts) / pd.Timedelta(timeframe)

class TransientError(Exception): ...    # network/timeout/retryable-429 classes

def retry_call(fn, *, base=0.5, cap=60.0, max_attempts=6):
    """Bounded exponential backoff with FULL jitter (Brooker, AWS Architecture Blog 2015)."""
    for attempt in range(max_attempts):
        try:
            return fn()
        except TransientError:
            if attempt == max_attempts - 1:
                raise                    # escalate: mark source down, open breaker, alert
            time.sleep(random.uniform(0, min(cap, base * 2 ** attempt)))

# Idempotent ingestion write (PostgreSQL): a repeated backfill can never duplicate rows.
# With append-versioned storage (Q09), the conflict handler INSERTs a new version row
# instead of mutating the old one, so corrections stay point-in-time separable.
UPSERT = """
INSERT INTO candles (symbol, event_ts, timeframe, open, high, low, close, volume,
                     source, ingested_at, recovered)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now(), TRUE)
ON CONFLICT (symbol, event_ts, timeframe) DO UPDATE
SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
    close = EXCLUDED.close, volume = EXCLUDED.volume, ingested_at = now();
"""
```

## Application to this project

- **A**: every fetch uses bounded jittered retries (Retry-After aware); streams get heartbeat timeouts and snapshot-then-delta reconnects; writes are idempotent upserts on (symbol, event_ts, timeframe).
- **B**: recovered ranges re-enter the Q10 gate; freshness and validation share the calendar module.
- **C/F**: feature jobs declare a maximum tolerable data age; the scheduler refuses stale slices; training waits for freshness SLAs, suspending retraining rather than training on stale data.
- **J**: freshness metrics (age, miss counters, backfill rates) feed Q21-style health.
- **K**: the supervisor runs recovery automatically for S1/S2 stalls; S3/S4 escalate to incidents (Q10-B tiers).
- **L**: an independent check recomputes data age before action and vetoes stale features.
- **Siblings**: Q09 (recovery upserts append versions; `ingested_at` is Q09's `available_ts`), Q10 (verdicts define "recovered"), Gate 3 (integration).

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Inspect and classify:

- [ ] Freshness measured on data age, or only process liveness?
- [ ] Calendar/session awareness in monitoring or scheduling code?
- [ ] Retry quality: bounded, jittered, Retry-After honored, no unbounded loops?
- [ ] Stream reconnect logic and post-reconnect reconciliation?
- [ ] Backfill automation (trigger, chunking, oldest-first, rate limiting)?
- [ ] Idempotent write keys (unique constraints) in the storage schema?
- [ ] Recovery verification (re-validation, reconciliation) and escalation behavior logged?

Classification vocabulary: IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY.

## Recommended improvements

1. **P0** — Calendar-aware freshness checker with per-(venue, timeframe) thresholds, baselined from observed arrival latencies before enforcement.
2. **P0** — Idempotent writes everywhere: unique key (symbol, event_ts, timeframe) + upsert semantics, proven by a duplicate-detection test.
3. **P0** — Replace unbounded/linear retries with bounded exponential backoff + full jitter + Retry-After + breaker.
4. **P1** — Automated gap-driven backfill: calendar scan → oldest-first chunked fetch → idempotent upsert → re-validation, with a per-run recovery report.
5. **P1** — Stream-recovery path: heartbeat timeouts, resubscribe, REST snapshot reconciliation after reconnect.
6. **P1** — Group-level stall classification (symbol vs venue) and the consecutive-miss alert ladder.
7. **P2** — Secondary-source reconciliation for high-severity recoveries and periodic cross-source spot checks.

## Dependencies

Q09 (availability timestamps, versioned writes), Q10 (gate for recovery admission), components A/B/F/J/K/L; pandas_market_calendars (or equivalent); unique constraints; NTP-synchronized hosts; per-vendor rate-limit docs.

## Acceptance criteria

1. **Stall detection**: fault-injection stopping data for a 1-minute-candle symbol during an open session fires the alarm within `limit + one evaluation interval`; the same test during a closed session alerts nothing.
2. **Idempotency**: running recovery twice over the same missing range yields zero duplicate and zero lost rows (key-based assertions).
3. **Retry behavior**: injected transient failures show exponential, randomized sleep growth, hard stop at max_attempts, escalation logged; no request storms.
4. **Recovery verification**: every automated recovery produces a report with ranges filled, Q10 verdicts per range, reconciliation deltas vs source; recovered rows carry provenance.
5. **Baseline-first thresholds**: per-(venue, timeframe) limits derived from ≥ 30 days of observed arrival distributions, reviewed before enforcement.

## Risk assessment

- **Implementation**: wrong session calendars produce false gaps and useless backfills; clock skew distorts age computation; K too aggressive → fatigue, too lax → hidden stalls; idempotency-key omissions create subtle duplicates.
- **Operational**: backfills hammering rate limits (bans); recovery storms after an outage (needs pacing); breakers flapping on marginal sources.
- **Failure modes**: a source serving plausible wrong data (only cross-source checks catch it); recovery overwriting corrected history if versioning absent; recovered rows breaking PIT ordering.
- **Regressions**: changing freshness limits or key schemas silently alters alerting and dedup — version these configs and re-run fault-injection suites (Q17).

## Implementation decision

Adopt calendar-aware freshness thresholds (baselined, then enforced), bounded full-jitter retries with breaker, idempotent upserts everywhere, and automated backfill with mandatory re-validation and reconciliation. If the audit confirms unique-constraint capability, build on it; otherwise migrate storage first. Contingent on the local audit.

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in during implementation:

- Files changed: ____
- Tests added / results (incl. fault-injection and idempotency suites): ____
- Baseline measurements (arrival latency, freshness limits): ____
- Rollback reference: ____
- Date / owner: ____

## Outstanding questions

- Rate limits and reconnection semantics of each API used.
- Custom calendars/maintenance windows for the 24/7 venues traded.
- Whether any required data has a second vendor available (reconciliation coverage).
- How long corrected vintages are kept (with Q17).

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

[[Q09 Point in Time Features]], [[Q10 Historical Data Validation]], [[Gate 3 Data Integrity]], [[Q17 Reproducibility and Versioning]], [[Q21 Component Health Monitoring]]
