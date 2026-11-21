---
type: research-record
ids: [Q10-A, Q10-B]
category: Data Integrity
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q10 Historical Data Validation

Historical data validation is the automated gate deciding whether each batch of market data may enter the feature store and training pipeline. This record defines a rule catalog for the six defect classes — missing candles, duplicates, invalid prices, unusual volume, inconsistent timestamps, structural changes — plus a severity-tiered policy choosing among automatic repair, replacement retrieval, quarantine, and halting training. The verified tool landscape: pandera for dataframe schema assertions, Great Expectations (GX) for declarative expectation suites with auditable documentation, TensorFlow Data Validation (TFDV) for statistics-driven schema inference, anomalies, and training/serving skew checks; trading calendars (pandas_market_calendars) supply session-awareness generic tools lack. The plan rule — invalid data must never silently enter the training pipeline — becomes a blocking gate with reason codes, quarantine with provenance, and a fail-safe default of halting affected processes rather than imputing quietly.

## Question IDs

- **Q10-A** — Automated validation rules for the six defect classes.
- **Q10-B** — Response policy for corrupted/incomplete data: recovery, replacement, quarantine, or halt.

## Original research questions

- **Q10-A** (verbatim): "What automated validation rules should our bot enforce to detect missing market candles, duplicate records, invalid prices, unusual volume values, inconsistent timestamps, and unexpected changes in data structure?"
- **Q10-B** (verbatim): "When the bot encounters corrupted or incomplete historical information, should it attempt automatic recovery, retrieve replacement data, quarantine affected records, or stop the relevant training process until the problem is resolved?"

## Research objective

**Q10-A.** Establish a codified rule catalog — predicates with thresholds and reason codes — for each named defect class, executed automatically on every ingestion batch and rebuilt dataset. Each class damages models differently: missing candles fake flat periods; duplicates double-count; invalid prices corrupt returns and indicators; volume anomalies hide outages; timestamp inconsistencies break PIT joins (Q09); structure changes silently alter semantics. Affects A (gate before store), B, C, F, H, J (metrics), L (independent re-check).

**Q10-B.** Establish a deterministic policy mapping (defect class × severity) to an action: bounded repair, replacement retrieval, quarantine, or halting affected training/ingestion. Both wrong defaults are costly — silent imputation poisons training; halting on every anomaly starves the pipeline. Affects A, B, F, J, K (supervisor executes), L.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit locally before any implementation decision:

- [ ] Any validation module near ingestion code — checks or just logging?
- [ ] OHLC consistency checks (high ≥ max(open, close, low); low ≤ min(open, close, high); positivity) implemented?
- [ ] Gap detection: comparison against expected frequencies or trading calendars?
- [ ] Duplicate handling: unique constraints; behavior on conflicting duplicates (same key, different values)?
- [ ] Quarantine mechanism: separate store, reason codes, provenance, re-validation path?
- [ ] Severity policy: explicit repair-vs-halt rules anywhere; can training run on quarantined data?
- [ ] Tests injecting corrupted data (seeded corruption) and asserting detection; do failures alert anyone?

## Technical concepts

- **Data schema / schema validation**: declared shape (columns, dtypes, nullability, ranges) and automated checking against it.
- **Expectation**: a declarative, verifiable assertion about data (GX); an **expectation suite** collects them; results render into **Data Docs**.
- **Schema inference**: deriving a schema from observed statistics (TFDV), not declaring upfront.
- **OHLC consistency**: bar invariants — high ≥ max(open, close, low), low ≤ min(open, close, high), prices > 0, close within [low, high], volume ≥ 0.
- **Zero-volume bar**: legitimate in illiquid sessions, suspicious elsewhere — context-sensitive.
- **Spike/outlier rule**: implausible-vs-local-context test; the robust variant uses **median absolute deviation (MAD)** because market data is heavy-tailed.
- **Distribution drift**: batch statistics vs a reference window — PSI or a KS test.
- **Gap detection**: expected-but-missing bars, using bar frequency and **trading calendars** (sessions, holidays, half-days).
- **Monotonic timestamps**: strictly increasing time index per (symbol, timeframe); prerequisite for as-of joins.
- **Training-serving skew**: divergence between training-time and serving-time feature distributions (TFDV compares against training statistics).
- **Data contract**: producer-consumer agreement (schema + invariants) enforced automatically.
- **Quarantine / reason codes**: routing suspect records to an isolated store carrying failure reasons and provenance, with a re-validation path.
- **Severity tier**: anomaly classification (S1 cosmetic … S4 systemic) driving the response policy.
- **Fail-safe default**: the action under uncertainty — here, quarantine + halt rather than admit.
- **Idempotent re-validation**: re-running the identical rule set over repaired/quarantined data to decide readmission.

## Research findings

### Q10-A findings

1. **Three complementary tools cover three levels of strictness.** TFDV "can analyze training and serving data to: compute descriptive statistics, infer a schema, detect data anomalies," including training/serving drift and skew [ESTABLISHED, TFDV docs]. GX documents expectation suites as "a collection of verifiable assertions about data," with results consumable programmatically [ESTABLISHED, GX docs]. pandera provides a flexible API for validating dataframe-like objects; `DataFrameSchema` verifies columns and index, and `Check` objects are its "fundamental construct" [ESTABLISHED, pandera docs].
2. **Philosophy disagreement (documented): infer vs declare.** TFDV infers a schema from data and flags deviations; GX asks engineers to declare business-rule expectations. Market data needs both: OHLC invariants are laws (declare), volume distributions drift (infer). Resolution: hybrid per defect class [CONTESTED; resolution given].
3. **Trading-calendar awareness is a separate, necessary dependency.** pandas_market_calendars provides "over 50+ unique exchange calendars" with session schedules and holidays [ESTABLISHED]. Without it, gap detection misreports holidays, half-days, and maintenance windows as missing data [INTERPRETATION].
4. **OHLC invariants are universally checkable row-level predicates** with hard-failure semantics — a violating bar cannot describe a real trading interval [INTERPRETATION; predicates are arithmetic].
5. **Volume anomalies need context, not global rules.** Zero-volume bars are normal for illiquid sessions and pathological for liquid markets; spike detection should use robust (MAD-based) scores on a rolling window; heavy tails dominate mean/σ [INTERPRETATION].
6. **Timestamp consistency spans monotonicity, gap-vs-calendar, unit/tz uniformity, and future-dated values** (clock-skew implicated; Q09/Q11) [INTERPRETATION]; **structure-change detection is what schema tooling provides** (pandera/GX column checks; TFDV schema diffs) [ESTABLISHED]; distribution drift (PSI/KS) guards semantics shape-only checks miss [ESTABLISHED mechanism; thresholds ours].

### Q10-B findings

1. **No official source prescribes a recovery-vs-halt policy; tools only supply verdicts.** All three tools emit programmatically consumable pass/fail results (GX results, TFDV anomaly lists, pandera `SchemaErrors`), making a policy layer implementable; the policy itself is a design decision [INTERPRETATION].
2. **TFX's own pipeline pattern treats validation as a gate**: TFDV compares new data against the curated training schema and surfaces anomalies used for pipeline gating [ESTABLISHED, TFDV/TFX docs] — supporting a blocking gate, not advisory logging.
3. **Severity tiers make the dilemma deterministic** [INTERPRETATION]: S1 (isolated missing bar, single duplicate) → log, schedule backfill (Q11); S2 (gap clusters, sparse outliers) → bounded re-fetch, quarantine unrepaired rows; S3 (systematic corruption — price-scale breaks, unadjusted splits) → quarantine ranges, halt dependent training; S4 (schema break, source-wide corruption) → quarantine and halt the ingestion path.
4. **The fail-safe default is quarantine + halt, never silent imputation.** Interpolated prices are fabricated observations; tolerated fills must be flagged and excluded from labels [INTERPRETATION; operationalizes the plan rule].
5. **Quarantine design requirements** [INTERPRETATION]: separate table/folder; per-row reason codes; provenance (source, fetch time); readmission only via the same rule set; quarantine-rate metrics exported to monitoring.
6. **Replacement retrieval beats local repair when a source exists** — re-fetching preserves provenance; automatic repair limited to mechanical fixes [INTERPRETATION; synergizes with Q11-B backfill].
7. **Documented tension: strictness vs data starvation.** Over-strict rules quarantine legitimate data (holidays, illiquid zero-volume bars); under-strict rules admit corruption. Resolution: per-venue false-quarantine baselines measured over ≥ 90 days before tightening [CONTESTED; measured calibration].

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|---|---|---|---|---|---|---|
| 1 | Get started with TensorFlow Data Validation | Google (TFX team) | current docs; accessed 2026-11-21 | https://www.tensorflow.org/tfx/data_validation/get_started | Statistics, schema inference, anomaly detection; training/serving drift and skew checks | TF/TFX stack; not market-specific | YES (search-verified) |
| 2 | GX Core overview / Data Docs | Great Expectations | current docs; accessed 2026-11-21 | https://docs.greatexpectations.io/docs/0.18/reference/learn/terms/data_docs | Expectations = verifiable assertions; suites validate batches; results consumable and documented | Declarative philosophy needs upfront authoring | YES (search-verified) |
| 3 | pandera documentation | pandera (Union.ai) | current docs; accessed 2026-11-21 | https://pandera.readthedocs.io | DataFrameSchema verifies columns/index; checks as fundamental construct; flexible dataframe validation | pandas-centric; distribution checks DIY | YES (search-verified) |
| 4 | pandas_market_calendars documentation | rsheftel et al. | current docs; accessed 2026-11-21 | https://pandas-market-calendars.readthedocs.io | 50+ exchange calendars; session schedules, holidays, market times | Per-venue; 24/7 venues need custom calendars | YES (search-verified) |

**Notes.** TFDV (1) is the strongest official evidence that statistics-driven anomaly detection and skew checks belong in a blocking gate. GX (2) documents the expectation-suite model our rule catalog encodes. pandera (3) is the lightest pandas-native option for hard predicates and schema enforcement. pandas_market_calendars (4) is the only verified source covering market structure (sessions, holidays) — without it, gap detection is systematically wrong at holidays and half-days.

**Established vs experimental vs interpretation.** Established: TFDV/GX/pandera capabilities; calendar role; consumable validation results. Experimental: TFDV schema inference on 24/7 crypto data; GX Cloud freshness (commercial, not evaluated). Interpretation (ours): severity-tier policy, quarantine design, fail-safe defaults, MAD statistics, hybrid infer/declare split.

## How the technique works

**Mechanism.** Validation runs as a gate between ingestion and storage (and over rebuilt datasets): (1) parse/type-check; (2) schema validation — columns, dtypes, nullability, index uniqueness; (3) row predicates — OHLC invariants, positivity, finiteness, timestamp bounds; (4) set checks — duplicate keys, monotonic timestamps, calendar-aware gaps; (5) distribution checks — per-column statistics vs a reference window (PSI/KS); (6) emit a structured report (status, counts, ranges, reason codes); (7) route per severity: admit, quarantine, recover (Q11-B), or halt.

**Formulas.** Invariants: `high ≥ max(open, close, low)`; `low ≤ min(open, close, high)`; prices > 0; volume ≥ 0. Gap: flag when `tᵢ₊₁ − tᵢ > Δ·(1+ε)`, adjusted to session boundaries by the calendar. Robust score: `zᵣ = 0.6745·(x − median(x_w)) / MAD(x_w)` over window w. PSI over quantile bins: `PSI = Σᵢ (bᵢ − rᵢ)·ln(bᵢ/rᵢ)`; conventions treat > 0.1 as moderate, > 0.25 as major — re-baseline on this project's data [INTERPRETATION].

**Inputs:** batch; venue calendar/bar frequency; reference statistics window; versioned schema. **Outputs:** machine-readable report, quarantine entries with reason codes, admission/halt decisions, metrics. **Strengths:** deterministic coverage of all six defect classes; audit trail; mature tooling for schema/distribution layers. **Limitations:** thresholds are calibrated conventions; exotic-venue calendars need maintenance; heavy tails defeat naive z-scores; plausible fabricated data can pass all invariants. **Computational:** row predicates vectorize in numpy/pandas; gap/monotonic checks are sort-based; PSI/KS are binning + closed form — all cheap versus ingestion; TFDV adds Beam-based statistics if adopted. **Failure conditions:** wrong calendar (false gaps), wrong bar-labeling convention shifting every boundary check, contaminated reference window (drift checks learn the corruption), reason-code taxonomy drift across pipeline versions.

## Reference implementation sketch

Runnable, pandas/numpy only; `pandera`, `great-expectations`, `pandas-market-calendars` are optional upgrades. Point-in-time safe: row-local predicates only.

```python
import numpy as np
import pandas as pd

def validate_candles(df: pd.DataFrame) -> pd.DataFrame:
    """Row-level OHLCV checks. Returns quarantine rows with reason codes."""
    checks = {
        "nonpositive_price": (df[["open", "high", "low", "close"]] <= 0).any(axis=1),
        "ohlc_inconsistent": (df["high"] < df[["open", "close", "low"]].max(axis=1))
                           | (df["low"]  > df[["open", "close", "high"]].min(axis=1)),
        "negative_volume":   df["volume"] < 0,
        "nonfinite":         ~np.isfinite(df[["open", "high", "low", "close", "volume"]]).all(axis=1),
        "duplicate_key":     df.duplicated(["symbol", "ts"], keep=False),
        "future_ts":         df["ts"] > pd.Timestamp.now(),  # naive-UTC storage assumed
    }
    flags = pd.DataFrame(checks)
    bad = flags.any(axis=1)
    reasons = flags.apply(lambda r: "+".join(flags.columns[r]) or "none", axis=1)
    return df.loc[bad, ["symbol", "ts"]].assign(reason=reasons[bad])

def find_gaps(ts: pd.Series, timeframe: str = "1h") -> pd.DatetimeIndex:
    """Missing bars vs a uniform grid (fallback: under-reports at session boundaries).
    Preferred: pandas_market_calendars schedules -> mcal.date_range(sched, freq=timeframe)."""
    expected = pd.date_range(ts.min(), ts.max(), freq=timeframe)
    return expected.difference(pd.DatetimeIndex(ts.unique()))

# Policy hook (PSEUDOCODE): S1 isolated missing bar -> log + backfill (Q11);
# S2 gap cluster / sparse outliers -> re-fetch, quarantine unrepaired;
# S3 systematic price-scale break -> quarantine + halt dependent training;
# S4 schema break -> quarantine + halt ingestion path.
```

## Application to this project

- **A**: gate runs on every batch before storage; failures quarantine (never silently dropped); gate metrics exported.
- **B**: this record IS the rule set for B; normalization operates only on admitted data.
- **C**: feature builders assert inputs passed the gate version they were built against; schema bumps invalidate cached features.
- **F/H**: jobs declare their data slice; scheduler refuses/halts when it has S3/S4 quarantines — "invalid data must never silently enter the training pipeline."
- **J**: quarantine rate and per-check failures are monitored series (feeds Q21-style health).
- **K**: S1/S2 trigger Q11-B recovery automatically; S3/S4 open incidents.
- **L**: an independent validator re-runs the rules on a fresh copy to confirm the gate was not bypassed.
- **Siblings**: Q09 (validated timestamps underpin PIT joins), Q11 (freshness decides when data should exist; recovery writes must re-pass this gate), Gate 3 (integration).

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Inspect and classify:

- [ ] Which of the six defect classes have checks; which are missing?
- [ ] Quarantine store with reason codes and provenance present?
- [ ] Any non-blocking (log-only) check that should gate?
- [ ] Calendars used for gaps, or uniform-frequency assumptions?
- [ ] Conflicting duplicates detected, or only exact duplicates?
- [ ] Schema versioning and structure-change alarms?
- [ ] Seeded-corruption tests present? Is the severity policy explicit anywhere?

Classification vocabulary: IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY.

## Recommended improvements

1. **P0** — Codify the six-class rule catalog with reason codes; make the gate blocking for the feature store and training inputs.
2. **P0** — Build the quarantine store: separate store, reason codes, provenance, re-validation readmission; export quarantine-rate metrics.
3. **P1** — Calendar-aware gap detection per venue (custom calendars for 24/7 venues with maintenance windows).
4. **P1** — Distribution drift checks (PSI/KS) with per-feature reference windows and baselined thresholds.
5. **P1** — Schema versioning with structure-change alarms and cached-feature invalidation on schema bump.
6. **P2** — Adopt pandera for schema/predicate enforcement; evaluate GX suites + DataDocs; TFDV-style statistics if the stack outgrows pandas.
7. **P2** — Cross-source spot-check reconciliation for high-severity detections (source corruption vs ingestion bug).

## Dependencies

Q09 (timestamp conventions, PIT ordering), Q11 (freshness and recovery machinery), components A/B/C/F/H/J/K/L; optional packages: `pandera`, `great-expectations`, `pandas-market-calendars`, `tensorflow-data-validation`; storage with unique constraints; alerting channel.

## Acceptance criteria

1. **Gate coverage**: 100% of batches and rebuilt datasets produce a persisted validation report before any downstream read.
2. **Detection**: seeded-corruption suite injects each defect class; detection rate 100% with correct reason codes.
3. **False-quarantine baseline**: run the gate over ≥ 90 days of real per-venue data; record quarantine rate per rule; calibrate to an agreed budget (e.g., < 0.1% of legitimate bars) — measured first, not assumed.
4. **No silent path**: fault-injection plus code review prove no path writes feature/training data without a passing gate (or logged, human-approved override).
5. **Halt correctness**: injecting an S3 corruption into one symbol halts dependent training while others continue; halt and reason recorded.

## Risk assessment

- **Implementation**: wrong calendars/conventions produce false gaps at scale (alarm fatigue, then disabled checks); robust windows need per-asset-class tuning; PSI bins unstable on sparse data.
- **Operational**: quarantine growth without a repair loop; S1 alert noise; validation latency as ingestion bottleneck.
- **Failure modes**: legitimate venue changes look like S4 breaks (need managed migration); plausible corruption passes invariants; contaminated reference windows teach drift checks the corruption.
- **Regressions**: rule-set changes flip historical verdicts — version the catalog and re-run gates over existing datasets (Q17); relaxed thresholds left in code become the new silent hole.

## Implementation decision

Build the blocking gate with the full rule catalog and quarantine store first (P0), using pandas/numpy checks plus pandera for schema enforcement; defer TFDV, treat GX/DataDocs as a later upgrade. Measure false-quarantine baselines before tightening thresholds. Contingent on the local audit.

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in during implementation:

- Files changed: ____
- Tests added / results (incl. seeded-corruption suite): ____
- Threshold baselines measured (per venue/rule): ____
- Rollback reference: ____
- Date / owner: ____

## Outstanding questions

- Which venues/asset classes are traded (calendar set and volume-rule calibration).
- Acceptable false-quarantine budget per venue (business decision; baselined).
- Whether vendors provide correction feeds distinguishing repaired data (quarantine readmission).
- Retention policy for quarantined data (audit needs vs storage cost).

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

[[Q09 Point in Time Features]], [[Q11 Data Freshness and Recovery]], [[Gate 3 Data Integrity]], [[Q17 Reproducibility and Versioning]], [[Q21 Component Health Monitoring]]
