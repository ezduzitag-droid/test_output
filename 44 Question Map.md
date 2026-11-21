---
type: tracking-note
created: 2026-11-21
tags: [ml-trading, tracker, checklist]
---

# 44 Question Map

Compliance checklist required by plan §15: every one of the 44 research questions must receive independent treatment inside its parent record (`Qxx-A` / `Qxx-B` sections). The [[Master Progress Tracker]] mirrors the record-level status; this note mirrors the question-level status.

**How to read the table:** *Parent record* is the wiki-link to the investigation note. *Research* status is per-question evidence that the question was separately researched and answered. *Impl.* is the implementation status inherited from the record's ⛔ blocked decision (all `DFU` = DOCUMENT FOR FUTURE USE, pending local audit of the external repository).

| ID | Parent record | Question (short form) | Research | Impl. |
|---|---|---|---|---|
| Q01-A | [[Q01 HMM Market Regimes]] | Identify/classify market regimes from volatility, momentum, volume, price movement, correlations — without look-ahead | ✅ | DFU |
| Q01-B | [[Q01 HMM Market Regimes]] | Learn which strategies perform best per regime; validate on previously unseen data | ✅ | DFU |
| Q02-A | [[Q02 Bayesian Regime Detection]] | Distinguish genuine regime change from temporary fluctuation; filtered probabilities, confidence thresholds | ✅ | DFU |
| Q02-B | [[Q02 Bayesian Regime Detection]] | Handle uncertain conditions; prevent excessive strategy switching | ✅ | DFU |
| Q03-A | [[Q03 Contextual Bandit Strategy Selection]] | Contextual bandit for strategy/model selection; reward calculation | ✅ | DFU |
| Q03-B | [[Q03 Contextual Bandit Strategy Selection]] | Explore alternatives without repeatedly selecting poor/untested strategies | ✅ | DFU |
| Q04-A | [[Q04 Additional Market Data Sources]] | Additional sources (IV, options, volume, liquidity, breadth) for earlier regime recognition | ✅ | DFU |
| Q04-B | [[Q04 Additional Market Data Sources]] | Test whether added indicators genuinely improve classification vs overfitting | ✅ | DFU |
| Q05-A | [[Q05 Backtest Overfitting]] | Measure and control probability of overfitting from continuous experimentation | ✅ | DFU |
| Q05-B | [[Q05 Backtest Overfitting]] | Maintain completely untouched holdout periods across repeated discovery | ✅ | DFU |
| Q06-A | [[Q06 Time Series Validation]] | Rolling training + forward-testing windows; evaluation strictly after training period | ✅ | DFU |
| Q06-B | [[Q06 Time Series Validation]] | Choose training/test window lengths and time gaps from timeframe/horizon/regime speed | ✅ | DFU |
| Q07-A | [[Q07 Triple Barrier and Meta Labeling]] | Labels from volatility-adjusted profit target, stop-loss, max holding period | ✅ | DFU |
| Q07-B | [[Q07 Triple Barrier and Meta Labeling]] | Primary model + secondary meta-labeling: accept / reject / risk-assign | ✅ | DFU |
| Q08-A | [[Q08 Financial ML Evaluation]] | Combine statistical ML + financial metrics; accuracy vs risk-adjusted performance | ✅ | DFU |
| Q08-B | [[Q08 Financial ML Evaluation]] | Rank strategies across return, drawdown, consistency, regime coverage | ✅ | DFU |
| Q09-A | [[Q09 Point in Time Features]] | Strictly point-in-time reconstruction of every training example | ✅ | DFU |
| Q09-B | [[Q09 Point in Time Features]] | Synchronize multi-exchange/asset/timeframe data; publication delays, revisions | ✅ | DFU |
| Q10-A | [[Q10 Historical Data Validation]] | Automated rules: missing candles, duplicates, invalid prices, volume, timestamps, schema | ✅ | DFU |
| Q10-B | [[Q10 Historical Data Validation]] | Corrupted/incomplete data: recover vs replace vs quarantine vs halt | ✅ | DFU |
| Q11-A | [[Q11 Data Freshness and Recovery]] | Freshness thresholds per market/asset/timeframe; detect stalled-but-healthy pipeline | ✅ | DFU |
| Q11-B | [[Q11 Data Freshness and Recovery]] | Automated recovery: retries, reconnects, backfill, verification | ✅ | DFU |
| Q12-A | [[Q12 ADWIN Concept Drift]] | Adaptive-window concept-drift detection for learned relationships | ✅ | DFU |
| Q12-B | [[Q12 ADWIN Concept Drift]] | Post-drift decision: retrain / new regime / switch strategy / disable model | ✅ | DFU |
| Q13-A | [[Q13 Drift Diagnosis]] | Independent feature-drift and prediction-drift monitoring; significance tests | ✅ | DFU |
| Q13-B | [[Q13 Drift Diagnosis]] | Distinguish harmless change vs genuine concept drift vs data-pipeline failure | ✅ | DFU |
| Q14-A | [[Q14 Per Component Model Monitoring]] | What to record (inputs, features, predictions, selections, outcomes) for diagnosis | ✅ | DFU |
| Q14-B | [[Q14 Per Component Model Monitoring]] | Per-asset/regime/timeframe/strategy health; isolate failing component | ✅ | DFU |
| Q15-A | [[Q15 Continuous ML Pipeline]] | Continuous pipeline: discover opportunities → train challengers → validate → compare | ✅ | DFU |
| Q15-B | [[Q15 Continuous ML Pipeline]] | Acceptance criteria before a challenger replaces the champion | ✅ | DFU |
| Q16-A | [[Q16 Model Registry and Rollback]] | Complete model registry: lineage, metadata, evaluation history, deployment status | ✅ | DFU |
| Q16-B | [[Q16 Model Registry and Rollback]] | Automatic promotion and immediate rollback mechanics | ✅ | DFU |
| Q17-A | [[Q17 Reproducibility and Versioning]] | Data versioning + experiment tracking for exact reproducibility | ✅ | DFU |
| Q17-B | [[Q17 Reproducibility and Versioning]] | Orchestration/recovery of failed or interrupted experiments without corruption | ✅ | DFU |
| Q18-A | [[Q18 Realistic Execution Simulation]] | Simulate spreads, fees, slippage, partial fills, delays in historical testing | ✅ | DFU |
| Q18-B | [[Q18 Realistic Execution Simulation]] | Compare backtest execution assumptions against paper-trading results | ✅ | DFU |
| Q19-A | [[Q19 Independent Risk Controls]] | Independent risk controls that stop trading on losses/anomalies/corruption | ✅ | DFU |
| Q19-B | [[Q19 Independent Risk Controls]] | Recover unhealthy components without re-enabling trading or bypassing limits | ✅ | DFU |
| Q20-A | [[Q20 Auditability and Supervision]] | Testing/validation procedures before accepting new strategies, models, changes | ✅ | DFU |
| Q20-B | [[Q20 Auditability and Supervision]] | Permanent audit trail of decisions, updates, failures, recovery actions | ✅ | DFU |
| Q21-A | [[Q21 Component Health Monitoring]] | Per-component health incl. detecting running-but-stalled processes | ✅ | DFU |
| Q21-B | [[Q21 Component Health Monitoring]] | Auto-restart, state restore, task reconciliation, consistency verification | ✅ | DFU |
| Q22-A | [[Q22 Cascading Failure Prevention]] | Retry limits, backoff+jitter, circuit breakers, failure isolation | ✅ | DFU |
| Q22-B | [[Q22 Cascading Failure Prevention]] | Temporary vs permanent vs cascading failures; graceful recovery, no retry loops | ✅ | DFU |

**Research-status legend:** ✅ = question was separately researched, has its own findings subsection and recommendations inside the parent record, and passed the post-generation validation script. ⛔ = blocked (none in this run). Re-audit after the local Phase-0 audit if any record's findings are revised.
