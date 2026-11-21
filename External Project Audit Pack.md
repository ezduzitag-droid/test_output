---
type: audit-note
created: 2026-11-21
tags: [ml-trading, audit, phase-0]
---

# External Project Audit Pack

**Purpose.** The Master Execution Plan's PHASE 0 requires auditing the existing repository and its Obsidian brain before any implementation decision. That repository is not present in the sandbox where this vault was built, so every record's *Existing project context*, *Existing implementation assessment*, and *Implementation record* sections are ⛔ BLOCKED. This pack is the Phase-0 substitute: answer it locally against the real repository, then propagate the answers into the records.

**How to use.**
1. Work through areas A–M below. For each checkbox, record: evidence found (file paths, function names, config keys, test names), or `NOT FOUND`, or `NOT APPLICABLE`.
2. Open the records listed in each area and replace the ⛔ blocks with the evidence; set each *Existing implementation assessment* classification using the plan §5 STEP 6 vocabulary.
3. Re-run each record's implementation-decision taxonomy; move decisions off `DOCUMENT FOR FUTURE USE` only where the audit justifies it.
4. Log every re-classification in [[Decision Log]] and update [[Master Progress Tracker]].
5. Before any code change: preserve a recoverable checkpoint (tag/branch, export databases, note dependency versions) per plan §4.5.

---

## A. Project identity and stack

- [ ] Primary language(s) and major frameworks/versions (runtime versions recorded where?)
- [ ] Process model: single process? scheduler? workers/queues? (names + entry points)
- [ ] Storage: time-series store, object store, relational DB, file layout (schemas/locations)
- [ ] Supported exchanges/assets and timeframes (where configured)
- [ ] Entry points and run modes (backtest / paper / live switches; live is expected OFF per plan §4.7)
→ Records to update: all — this is the global context.

## B. Data ingestion and storage

- [ ] Which market-data sources are wired in (REST/WS vendors), with rate limits and auth handling
- [ ] Candle/quote schema, timestamp semantics (exchange time vs receipt time; UTC normalization)
- [ ] Missing-candle policy, duplicate-key constraints, backfill tooling
- [ ] Where raw vs normalized data is kept; any vintage/revision handling
→ [[Q09 Point in Time Features]], [[Q10 Historical Data Validation]], [[Q11 Data Freshness and Recovery]]

## C. Feature engineering

- [ ] Indicator library used (TA-Lib? pandas-ta? custom), feature list and versions
- [ ] Multi-timeframe feature construction method (merge rules, alignment)
- [ ] Any point-in-time/as-of joins; any known leakage incidents or warnings
- [ ] Feature storage and versioning (parquet per run? feature store?)
→ [[Q09 Point in Time Features]], [[Q01 HMM Market Regimes]] (candidate regime features)

## D. Regime / condition recognition

- [ ] Any existing regime logic: HMM, GMM/clustering, vol-percentile buckets, rule-based tags
- [ ] Volatility estimators in use (realized vol, ATR, Parkinson), momentum/volume features
- [ ] Regime history storage and visualization, if any
→ [[Q01 HMM Market Regimes]], [[Q02 Bayesian Regime Detection]], [[Q04 Additional Market Data Sources]]

## E. Labeling and event definition

- [ ] How historical wins/losses are defined today (fixed horizon? threshold? none?)
- [ ] Volatility scaling of targets/stops; max-holding-period handling
- [ ] Overlapping-event handling and sample weighting, if any
→ [[Q07 Triple Barrier and Meta Labeling]]

## F. Training and validation

- [ ] ML libraries; model types trained today
- [ ] CV methodology (random K-fold? TimeSeriesSplit? walk-forward? none)
- [ ] Purging/embargo logic; leakage tests; random-seed control
- [ ] Hyperparameter search scope (how many trials — matters for [[Q05 Backtest Overfitting]])
→ [[Q05 Backtest Overfitting]], [[Q06 Time Series Validation]], [[Q07 Triple Barrier and Meta Labeling]]

## G. Strategy selection and evaluation

- [ ] How strategies are enumerated, selected, and switched today
- [ ] Metrics computed (Sharpe/Sortino/drawdown/win rate…), cost model, ranking logic
- [ ] Any bandit/online-learning or regime-conditioned selection already present
→ [[Q03 Contextual Bandit Strategy Selection]], [[Q08 Financial ML Evaluation]], [[Q18 Realistic Execution Simulation]]

## H. Model management

- [ ] Artifact storage layout; any registry metadata (training data refs, params, metrics)
- [ ] Promotion/rollback procedure; who/what triggers deployment
- [ ] Reproducibility: config versioning, dataset hashing, experiment tracking
→ [[Q15 Continuous ML Pipeline]], [[Q16 Model Registry and Rollback]], [[Q17 Reproducibility and Versioning]]

## I. Monitoring and drift

- [ ] What is logged today (predictions? features? selections? outcomes?), retention
- [ ] Any drift/statistical tests or performance-degradation alarms
- [ ] Per-asset/per-strategy health segmentation; alert routing
→ [[Q12 ADWIN Concept Drift]], [[Q13 Drift Diagnosis]], [[Q14 Per Component Model Monitoring]]

## J. Risk controls

- [ ] Independent risk layer? kill switch? loss/exposure/order-rate limits and where enforced
- [ ] What happens when the ML system is unavailable or outputs are invalid
- [ ] Re-enable authorization flow after an emergency stop
→ [[Q19 Independent Risk Controls]], [[Q20 Auditability and Supervision]]

## K. Self-healing / operations

- [ ] Process supervision (systemd? supervisor? none), restart policies, heartbeats
- [ ] Retry policies (counts, backoff, jitter), circuit breakers, idempotency of jobs
- [ ] State reconciliation after restart; checkpoint/resume of long tasks
- [ ] Audit trail of operational actions (log retention, tamper resistance)
→ [[Q21 Component Health Monitoring]], [[Q22 Cascading Failure Prevention]], [[Q20 Auditability and Supervision]]

## L. Testing

- [ ] Unit/integration/regression suites and how to run them; coverage of ML logic
- [ ] Historical validation tests (leakage, chronology); failure-injection tests
→ [[Master Test Plan]], [[Q20 Auditability and Supervision]]

## M. Obsidian brain sweep (plan §3)

- [ ] Existing architecture notes and decisions related to areas A–L (list note names + dates)
- [ ] Previous research that already answers part of a question (link note → record)
- [ ] Known issues / incomplete tasks / outdated statements (list with status)
- [ ] Folder/naming conventions this vault must conform to when merged
→ All records; also reconcile folder structure at merge time.

---

**Output of the audit.** A completed copy of this pack (with evidence) plus re-classified records constitutes the plan's PHASE 0 deliverable ("existing-project audit explaining exactly what Hermes is improving"). Only then proceed to plan Phase 8 integration with the implementation backlog built from the P0/P1/P2 recommendations in the records and gates.
