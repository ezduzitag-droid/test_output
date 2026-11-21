---
type: research-record
ids: [Q09-A, Q09-B]
category: Data Integrity
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q09 Point in Time Features

Point-in-time (PIT) reconstruction builds historical training data so every example contains only information actually published at the decision moment it represents. It establishes the two-timestamp model (event time plus availability time), the as-of "last known value" join as the sanctioned read, bitemporal/vintage storage for corrections, and alignment rules for multi-exchange, multi-timeframe, and external-indicator data. Most consequential verified finding: even a purpose-built feature store such as Feast can return backfilled and corrected values in its default offline point-in-time join unless availability-time filtering is enabled — a naive "historical" query is not safe by default. The record prescribes a single sanctioned PIT join utility, completed-bar gating for multi-timeframe features, and training/serving parity tests. Implementation is blocked pending a local audit of ingestion and feature code.

## Question IDs

- **Q09-A** — Strictly point-in-time reconstruction of historical market conditions.
- **Q09-B** — Synchronization across exchanges, assets, timeframes, and external indicators (publication delays, timestamp conventions, corrections).

## Original research questions

- **Q09-A** (verbatim): "How should our bot reconstruct historical market conditions using strictly point-in-time data so that every training example contains only information that would actually have been available at that moment?"
- **Q09-B** (verbatim): "How should the system synchronize historical information from multiple exchanges, assets, timeframes, and external indicators while accounting for publication delays, timestamps, and corrected historical records?"

## Research objective

**Q09-A.** Establish the storage schema and join algorithm guaranteeing that a training row assembled at decision time t contains only facts whose availability timestamp is ≤ t, with a defined treatment of later corrections. Future-information leakage inflates backtests invisibly — it makes results look better, not worse — a standard cause of paper-profitable models failing live. Affects A (availability metadata), B, C (main consumer), D, E (label timing), F, H (simulation replays PIT reads).

**Q09-B.** Establish how facts from different venues, assets, timeframes, and providers land on one time axis with per-source publication-delay models, and how corrections avoid destroying history or leaking backward. A multi-source panel is joinable only if timestamps are normalized and each source's lag from "event happened" to "value published" lives in data, not memory. Affects A, B, C, F, H, I (versioning), J (parity).

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit locally before any implementation decision:

- [ ] Joins between features and labels/decisions: lagged (`merge_asof`, `shift(1)`) or raw equality joins on bar timestamps?
- [ ] Separate ingest/availability timestamp stored beside the venue event timestamp?
- [ ] Macro/external indicators: vintages stored, or only the latest revised series?
- [ ] Multi-timeframe features: `resample` + one-bar shift or completed-bar gating?
- [ ] Timestamp hygiene: UTC, epoch units (s vs ms), tz conventions, open-time vs close-time bar labels per venue.
- [ ] Corrections appended as versions, or overwriting historical candles in place?
- [ ] Leakage tests (online-vs-offline parity, lookahead) and purge/embargo in walk-forward CV?

## Technical concepts

- **Point-in-time (PIT) correctness / historical reconstruction**: rebuilding past states so each decision time sees only then-available facts.
- **As-of join (point-in-time join)**: attaches to each decision time the newest row at or before it — pandas `merge_asof`; **last-known-value (LKV) join** is the feature-store name; **TTL** is a maximum feature age, older values becoming missing.
- **Event timestamp** vs **publication/availability timestamp**: when the fact occurred (bar close, macro quarter) vs when it first became knowable (release, ingest). Both required.
- **Historical feature store**: offline (training) and online (serving) stores kept consistent; **feature materialization** persists precomputed features at fixed timestamps so both read identical objects; divergence is **training-serving skew**.
- **Future-information leakage / lookahead bias**: using at t anything knowable only after t (restatements, full-sample normalization, overlapping labels, trading a bar on its own close). **Survivorship bias**: delisted assets missing from the historical universe.
- **Data revisions/corrections**: later restatements of published values, handled by **bitemporal modeling** (each fact carries valid time and transaction time), **vintage data** (a series exactly as released on a past date — ALFRED), and **SCD Type 2** (new record with effective ranges per change).
- **Multi-timeframe features**: lower-timeframe bars aggregated upward (**resampling**), usable only when all constituent bars have closed (**completed-bar gating**).
- **Exchange timestamp differences and clock skew**: venues differ in open-time vs close-time bar labels, epoch units, tz conventions; skew is the gap between venue event clocks and local ingest clocks.
- **Forward-fill vs backfill**: propagate the last known value forward vs pull future values backward (backfill is leakage by construction; banned in features).
- **Watermark**: Flink's "all events up to time X have arrived" marker; stalled means no new data (reused by Q11).

## Research findings

### Q09-A findings

1. **Two timestamps are the load-bearing design.** Feast joins features onto an *entity dataframe* (decision events with event timestamps), scanning "backward in time from the entity dataframe timestamp up to a maximum of the TTL" [ESTABLISHED, Feast docs].
2. **The default PIT join is not leakage-safe.** Feast's docs state the join constrains only the event timestamp and uses `created_timestamp` merely for dedup, so "a value that was backfilled or corrected *after* an entity dataframe timestamp can still be returned for it"; `filter_by_created_timestamp=True` adds `created_timestamp <= entity_timestamp` to keep backfilled values from leaking and mimic online-store behavior (NULLs excluded; not all stores support it) [ESTABLISHED, Feast docs].
3. **As-of joins are a solved primitive.** `pandas.merge_asof`: `direction='backward'` (default) takes the last right row with key ≤ left key; `tolerance` expires distant matches; `allow_exact_matches` controls the ≤ boundary; `by` groups entities; frames must be sorted ascending [ESTABLISHED, pandas docs].
4. **Macro data is the canonical vintage case.** ALFRED (St. Louis Fed) "allows you to retrieve each economic data release (vintage) that was available on a specific date in history" [ESTABLISHED]. Backtesting 2010 decisions on today's revised CPI is leakage by definition.
5. **Event time, not processing time, is the anchor.** Flink: event time is "the time that each individual event occurred on its producing device," embedded in the record — not the executing machine's clock [ESTABLISHED, Flink docs].
6. **Corrections belong in versioned storage.** Kimball's SCD Type 2 "adds a new dimension record" per change with effective ranges so history "can be preserved faithfully" [ESTABLISHED]. Safe read: latest version with availability time ≤ decision time.
7. **Leakage extends beyond late corrections** — full-sample normalization statistics, overlapping labels without purge/embargo, trading a bar on its own close [INTERPRETATION; handled by design rules and tests].
8. **Documented disagreement:** some practitioners accept latest-revision tables for exploratory research. Resolved by dual reads — vintage read for training, current read for research — not by weakening the training guarantee [CONTESTED; resolution given].

### Q09-B findings

1. **Each source needs its own publication-delay model.** Exchange candles arrive seconds after bar close; macro series weeks after the reference period [ESTABLISHED for macro via ALFRED's framing; exchange latencies measured from ingest logs, not assumed — INTERPRETATION].
2. **Timestamp normalization is the prerequisite for cross-source joins**: UTC, explicit epoch units, one tz convention, per-venue bar-labeling conventions recorded; conventions differ and must be verified per API [INTERPRETATION; verification outstanding].
3. **Cross-source alignment is an as-of problem**: per-source LKV reads onto a common decision grid (`merge_asof` with `by=` for entities) [ESTABLISHED mechanics; application INTERPRETATION].
4. **Clock skew is measurable and worth recording.** Storing venue event time and local receive time per fact turns skew into a computable series; drifting gaps flag infrastructure problems [INTERPRETATION; reused in Q11].
5. **Multi-timeframe sync requires completed-bar gating**: a decision at t may only consume a higher-timeframe bar whose interval ended ≤ t (one-bar shift after resample) [INTERPRETATION; arithmetic uncontroversial].
6. **Corrected exchange history is real.** Venues restate candles after incidents; Feast's `created_timestamp` design exists because backfilled rows arrive out of order [ESTABLISHED]. Consequence: append-versioned storage, never overwrites.
7. **Conflicting facts across sources need an explicit precedence policy** — a primary source per asset, others as corroboration; this is policy, not data [INTERPRETATION].
8. **Dedup semantics come from the join**: backward direction resolves duplicate right-side keys to the most recent qualifying row [ESTABLISHED, pandas docs]; storage should still enforce a unique (entity, event_ts, version) key.

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|---|---|---|---|---|---|---|
| 1 | Point-in-time joins | Feast (feature store docs) | undated; accessed 2026-11-21 | https://docs.feast.dev/getting-started/concepts/point-in-time-joins | Entity-dataframe PIT join; TTL; backfill/correction leak risk and filter remedy | Feast-specific; flag unsupported by some offline stores | YES (fetched) |
| 2 | pandas.merge_asof API reference | pandas development team | current docs; accessed 2026-11-21 | https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html | As-of semantics: direction, tolerance, allow_exact_matches, `by`, sorted requirement | Caller must sort/normalize dtypes | YES (fetched) |
| 3 | ALFRED | Federal Reserve Bank of St. Louis | ongoing since 2006; accessed 2026-11-21 | https://alfred.stlouisfed.org/ | Vintage economic data: "each economic data release (vintage) that was available on a specific date in history" | Macro series only | YES (fetched) |
| 4 | Timely Stream Processing | Apache Flink | stable docs; accessed 2026-11-21 | https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time | Event time vs processing time; watermarks | Streaming framing; batch translation is ours | YES (search-verified) |
| 5 | Slowly Changing Dimensions | Ralph Kimball (Kimball Group) | Sep 2008 | https://www.kimballgroup.com/2008/09/slowly-changing-dimensions/ | SCD Types 1–3; Type 2 preserves history with effective ranges | Warehousing terminology | YES (fetched) |

**Notes.** Feast (1) is the centerpiece: official documentation describing the backfill/correction leakage trap and its remedy, justifying the two-timestamp design. pandas (2) gives implementable semantics, including tolerance-as-TTL. ALFRED (3) proves "what was known then" is retrievable for macro data; Kimball (5) names the versioned-storage pattern; Flink (4) supplies the event-time vocabulary Q11 reuses.

**Established vs experimental vs interpretation.** Established: two-timestamp PIT joins with TTL; the default-join backfill leak and its filter; as-of semantics; vintage retrieval for macro; SCD Type 2; event-time anchoring. Experimental/edge: `filter_by_created_timestamp` support varies by offline store; venue correction behavior varies by vendor. Interpretation (ours): completed-bar gating as a hard rule, skew monitoring, source precedence policy, dual-read design, deferring a feature-store product until scale demands it.

## How the technique works

**Mechanism.** Store every fact keyed by (entity, event_ts, version) with `event_ts` and `available_ts`. A PIT read for decision time t: (1) filter facts with `available_ts <= t` (Feast's `filter_by_created_timestamp` analogue); (2) per (entity, event_ts) keep the row with greatest `available_ts` (SCD Type 2 style); (3) as-of join onto the decision grid via `merge_asof(direction='backward', by=entity)`; (4) drop matches older than the feature TTL, turning staleness into explicit NaN; (5) emit the feature vector with provenance.

**Formula.** LKV(e, f, t) = value of f in the row maximizing `available_ts` subject to `event_ts <= t` and `available_ts <= t`. Completed-bar gate: a bar covering [s, s+Δ) is admissible at t iff s+Δ ≤ t.

**Inputs:** decision grid; fact tables with both timestamps; per-feature TTLs; venue metadata. **Outputs:** a leakage-free feature matrix with provenance. **Strengths:** blocks the dominant leakage class; reproducible across train and serve; staleness explicit. **Limitations:** storage grows with versions; guarantee is only as honest as `available_ts`; label overlap needs separate handling. **Computational:** `merge_asof` is a linear two-pointer merge after sorting; version resolution a groupby-argmax; cost driver is version scanning, bounded by an (entity, event_ts) index. **Failure conditions:** unsorted keys (error), mixed tz/epoch units (silent misalignment), dishonest `available_ts` (silent leakage), in-place corrections, DST bugs.

## Reference implementation sketch

Runnable; pandas only. Demonstrates the visibility filter, TTL, and correction-aware read.

```python
import pandas as pd

# Two-timestamp schema: WHEN it happened + WHEN we knew it. Third row = later correction.
signals = pd.DataFrame({
    "event_ts":     pd.to_datetime(["2024-06-03 09:30", "2024-06-03 09:35",
                                    "2024-06-03 09:35"]),
    "available_ts": pd.to_datetime(["2024-06-03 09:33", "2024-06-03 09:41",
                                    "2024-06-03 09:47"]),
    "rsi14":        [31.2, 27.8, 27.9],
}).sort_values("available_ts")

decisions = pd.DataFrame({
    "decision_ts": pd.to_datetime(["2024-06-03 09:38", "2024-06-03 09:45",
                                   "2024-06-03 09:50"]),
}).sort_values("decision_ts")

# PIT join: last signal KNOWN at or before each decision time; never look forward.
joined = pd.merge_asof(
    decisions, signals,
    left_on="decision_ts", right_on="available_ts",
    direction="backward",            # backward = past only -> blocks lookahead
    tolerance=pd.Timedelta("2h"),    # features older than the TTL expire -> NaN
)
print(joined[["decision_ts", "rsi14"]])

# Bitemporal read: the version of a fact that was CURRENT at an arbitrary moment.
def pit_value(df, event_col, known_col, value_col, event_ts, asof_ts):
    visible = df[(df[event_col] == event_ts) & (df[known_col] <= asof_ts)]
    return visible.loc[visible[known_col].idxmax(), value_col] if len(visible) else None

assert pit_value(signals, "event_ts", "available_ts", "rsi14",
                 pd.Timestamp("2024-06-03 09:35"),
                 pd.Timestamp("2024-06-03 09:45")) == 27.8  # correction NOT yet visible
```

## Application to this project

- **A**: every fact written with `event_ts` + `available_ts`, source, and venue convention metadata; corrections appended as versions.
- **B**: normalizes tz/epoch units before the PIT store; validates `available_ts >= event_ts` (Q10).
- **C/D**: features and regime indicators materialize only via the sanctioned PIT join; completed-bar gating; no `bfill`.
- **E**: labels use returns strictly after decision time, attached at decision time.
- **F/G/H**: training consumes PIT snapshots; simulation replays identical LKV reads; selection metadata versioned with datasets.
- **I**: feature definitions and dataset versions pinned (Q17).
- **J/K/L**: monitoring compares live features against PIT reads (parity feeds Q21); supervisor halts on gate failures; risk layer vetoes signals failing parity.
- **Siblings**: Q10 validates the two timestamps; Q11 keeps `available_ts` truthful and repairs gaps idempotently; Gate 3 integrates.

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Inspect and classify:

- [ ] Any table storing both event and availability timestamps?
- [ ] Do feature/decision joins lag features or use equality joins?
- [ ] Macro indicators stored as vintages or single revised series?
- [ ] Corrections appended or overwriting?
- [ ] Leakage tests present? Purge/embargo in CV?
- [ ] Multi-timeframe features gated on completed bars?
- [ ] Timestamp normalization centralized or ad hoc?

Classification vocabulary: IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY.

## Recommended improvements

1. **P0** — Add `available_ts` to every ingested fact; enforce `available_ts >= event_ts` at write time.
2. **P0** — Implement one sanctioned PIT join utility (merge_asof-based, TTL, entity grouping); ban equality joins between features and decision rows.
3. **P1** — Preserve vintages: append a version per correction; expose "vintage read" (PIT) and "current read" (research) APIs.
4. **P1** — Enforce completed-bar gating for multi-timeframe features with unit tests over partial windows.
5. **P1** — Add purge/embargo to walk-forward CV for overlapping labels.
6. **P2** — Add training/serving parity tests: sampled live vectors must equal PIT reconstruction.
7. **P2** — Adopt `created_timestamp` filtering semantics if a feature-store product is later added.

## Dependencies

Q10 (timestamp validation), Q11 (freshness of `available_ts`, idempotent recovery), components A–J as mapped; storage with unique constraints on (entity, event_ts, version); NTP-synchronized clocks.

## Acceptance criteria

1. A leakage audit over every training dataset returns **zero** rows where any used fact's `available_ts > decision_ts` (audit first to establish the current violation baseline).
2. PIT-utility unit tests cover: exact boundary match, TTL expiry → NaN, correction visibility before/after `available_ts`, per-entity grouping, unsorted-input error.
3. Zero feature rows derived from uncompleted bars (independent calendar-based checker on sampled dates).
4. Parity: for ≥ 100 sampled serving timestamps, live feature vectors equal PIT reconstruction within a documented epsilon.
5. Every dataset version records the feature-definition and PIT-utility versions used (Q17 linkage).

## Risk assessment

- **Implementation**: `available_ts` recorded after batching delays (overstating availability); tz/epoch bugs misalign joins silently; over-tight TTLs create false NaNs.
- **Operational**: storage growth; join latency on large panels; migrating single-timestamp tables may require re-collection.
- **Failure modes**: availability columns exist but are not filtered (the Feast-documented trap); a repair job overwrites vintages; CV overlap persists despite correct features.
- **Regressions**: swapping join implementations or bar-labeling conventions can reintroduce leakage — require parity tests and dataset re-approval (Q17).

## Implementation decision

Adopt the two-timestamp PIT layer and a single sanctioned as-of join utility as a prerequisite for further model training; preserve vintages; defer a feature-store product until scale justifies it. Contingent on the local audit.

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in during implementation:

- Files changed: ____
- Tests added / results: ____
- Datasets rebuilt or re-approved: ____
- Rollback reference: ____
- Date / owner: ____

## Outstanding questions

- Bar-labeling convention (open vs close time) and correction behavior per venue API.
- Publication-lag table (event → availability) for each external indicator family consumed.
- Whether ingest logs reach far enough back to reconstruct `available_ts`.
- Purge/embargo lengths per timeframe (empirical; baselined with Q17/H).

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

[[Q10 Historical Data Validation]], [[Q11 Data Freshness and Recovery]], [[Gate 3 Data Integrity]], [[Q17 Reproducibility and Versioning]], [[Q21 Component Health Monitoring]]
