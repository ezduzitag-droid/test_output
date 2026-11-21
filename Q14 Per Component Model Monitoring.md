---
type: research-record
ids: [Q14-A, Q14-B]
category: Concept Drift
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q14 Per Component Model Monitoring

Per-component model monitoring is the *substrate* every other monitoring technique depends on: Q12's detectors and Q13's diagnosis are only as good as the evidence recorded about what the bot saw, computed, decided, and achieved. Q14-A defines the continuous record — an append-only decision log capturing historical inputs, processed features, predictions, strategy selections, and realized outcomes, with explicit schema, retention, and sampling rules modeled on documented cloud-provider prediction-logging practice. Q14-B defines the *aggregation* of that record into hierarchical health views — system, model, strategy, and per-asset/per-regime/per-timeframe slices — so a failing component can be isolated at the smallest possible scope, using alerting discipline borrowed from Google's SRE practice (alert on symptoms, confirm across short and long windows, never restart the world because one slice degraded). The two questions are one system: without A's log, B's slices are uncomputable; without B's slice structure, A's log is only an archive.

## Question IDs

- **Q14-A** — primary: what to continuously record (inputs, features, predictions, strategy selections, realized outcomes) so performance changes can be explained.
- **Q14-B** — secondary: per-component health monitoring (assets, regimes, timeframes, strategies) and isolation without system-wide shutdown.

Components affected: A–L — the log is the shared evidence store.

## Original research questions

- **Q14-A:** "What information should our bot continuously record about historical inputs, processed features, model predictions, strategy selections, and realized outcomes so that it can identify exactly why its performance changes?"
- **Q14-B:** "How should the bot monitor model health separately for individual assets, market regimes, timeframes, and strategies so that a failing component can be isolated without unnecessarily shutting down the entire system?"

## Research objective

**Q14-A** must establish the decision-log columns; what is captured at full fidelity versus sampled; retention; and the join keys that let any performance change be attributed to a feature, model version, strategy, or data feed. "Identify exactly why" requires counterfactual-grade evidence: without recorded predictions and the feature vectors behind them, analysis can correlate but cannot attribute.

**Q14-B** must establish the slice taxonomy (asset × regime × timeframe × strategy × model version), per-slice health metrics with minimum sample sizes, the alerting policy (symptoms, not causes; multiwindow confirmation), and the isolation ladder (slice disable → strategy pause → system halt) with sibling-health checks preventing overreaction. The alternative to slicing is binary — everything works or everything stops — exactly the "unnecessarily shutting down the entire system" the question forbids.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit checklist:

- [ ] Locate any existing decision/trade log (search `prediction_log`, `decision_log`, `trade_journal`, `outcomes`, `journal`) and compare fields against the five field groups below.
- [ ] Check whether records carry attribution keys: UTC timestamp + bar index, asset, timeframe, regime label, strategy id, model version, feature-schema version.
- [ ] Check whether raw inputs are stored in full or referenced by hash/source-version, and whether a sampling policy exists for high-frequency captures.
- [ ] Determine whether outcome joins exist (prediction row linked to realized outcome) or predictions and outcomes live in unjoined silos.
- [ ] Inspect retention/deletion behavior and whether aggregated rollups already exist.
- [ ] Look for per-slice metric computation: group-by (strategy, asset, regime, timeframe) win rate / PnL / Sharpe, plus enable/disable surfaces (per-slice vs global, manual vs automatable).
- [ ] Check for alerting code, confirmation windows, and tests verifying log completeness (every prediction row eventually gets an outcome row).

## Technical concepts

- **Model monitoring**: continuous automated comparison of a deployed model's inputs, outputs, and outcomes against expectations set at training time; distinct from offline backtesting (H).
- **Prediction/feature logging**: recording, per inference, the inputs (or their identity), the feature vector with schema version, the model version, and the output; AWS SageMaker Data Capture is the documented reference implementation (endpoint inputs and inference outputs captured to storage with a configurable sampling percentage) [ESTABLISHED].
- **Decision log**: this project's superset — also records strategy selection (chosen strategy, candidate scores, reason code) and the later realized outcome.
- **Realized outcomes**: post-trade results (per-unit return after costs/slippage, win flag, holding period) joined back to the causing decision row.
- **Slice**: one cell of {asset} × {regime} × {timeframe} × {strategy} × {model version}; the unit at which health is computed.
- **Hierarchical aggregation**: rollups slice → strategy → component → system, so degradation is located at the smallest failing level.
- **Model health profile**: per-model (and per-slice) expected metric ranges recorded at deployment — the contract monitoring checks against; model cards (Mitchell et al. 2019) are the documented per-model reporting pattern including slice-level breakdowns [ESTABLISHED].
- **Performance deterioration**: realized metrics breaching the profile floor — the symptom alerts are built on.
- **Alert conditions**: predicates over rollups; per SRE practice, fire on user-visible symptoms with multiwindow confirmation, not on every cause-level anomaly [ESTABLISHED].
- **Burn rate (SRE)**: how fast a system consumes its error budget relative to plan; the multiwindow multi-burn-rate pattern (short AND long window both over threshold) is the documented anti-flap compromise [ESTABLISHED].
- **Isolation policy**: ordered rules mapping a confirmed failing slice to the smallest effective disable, with sibling checks and an escalation ladder.
- **Sampling and retention**: what fraction of high-volume raw captures to keep and for how long; sampling must never apply to decision-level rows [INTERPRETATION].

## Research findings

### Q14-A findings

1. **The documented reference pattern captures inputs and outputs together, at the point of inference.** SageMaker Data Capture "logs the inputs to your endpoint and the inference outputs" to storage in JSON-lines form with configurable capture/sampling percentage [ESTABLISHED]. Generalized lesson: one atomic row per decision, written synchronously, never reconstructed later from dashboards [ESTABLISHED pattern; INTERPRETATION for the strictness].
2. **AWS's guidance enumerates the needed monitoring dimensions.** AWS Prescriptive Guidance lists data quality, model quality, bias drift, and feature-attribution drift; the Well-Architected ML lens prescribes drift detection and distribution monitoring to handle degradation [ESTABLISHED]. Translation: per-decision quality flags, per-slice outcome metrics, drift-relevant distributions (Q13), attribution fields [INTERPRETATION mapping].
3. **"Identify exactly why" forces five field groups.** (a) *Identity*: UTC timestamp, bar index, asset, timeframe, feed id/version, raw-input content hash (store the hash, not the payload — what makes raw-input retention affordable) [INTERPRETATION]. (b) *Processing*: feature vector + feature-schema version + transformation parameters. (c) *Decision*: model id/version, raw score, probability, predicted target, position size, strategy id, candidate scores, selection reason code, regime label at decision time, data-quality flags at decision time. (d) *Outcome (joined later)*: trade id, realized return after costs/slippage, win flag, holding period, outcome timestamp. (e) *Context*: regime label series and market snapshot identifiers for later reattribution (component D).
4. **Sampling must be policy, not accident.** SageMaker documents sampling percentage as a first-class capture knob [ESTABLISHED]. Safe division: decision-level rows are never sampled (they are the audit trail); only high-volume raw-input captures may be sampled [INTERPRETATION grounded in the documented knob].
5. **Retention is two-tiered, and model cards are the documentation twin.** Full-fidelity recent window (covering the slowest diagnosis loop, e.g., 90–180 days) + permanent per-slice daily rollups + permanent model-version metadata; the full log is archived but must stay replayable for H [INTERPRETATION]. Mitchell et al. define structured per-model reporting including per-slice evaluation breakdowns [ESTABLISHED]; the Q14-B health profile is its operational twin [INTERPRETATION link].

### Q14-B findings

1. **Alert on symptoms, not causes — documented SRE discipline that transfers directly.** The SRE book prescribes paging on symptoms rather than causes; the Workbook defines SLIs as ratios of good events to total events, with alerts tied to error-budget consumption [ESTABLISHED]. Trading translation: the symptom is realized per-slice performance breaching its profile floor; cause-level signals (feature drift, latency) feed diagnosis, not pages [INTERPRETATION mapping].
2. **Multiwindow, multi-burn-rate confirmation is the documented anti-flap pattern.** The Workbook fires only when both a short window and a long window (long = 12× short) exceed their burn-rate thresholds (worked examples: burn rate 14.4 over 1h+5min; 6 over 6h+30min for a 99.9% SLO) [ESTABLISHED]. Trading adaptation: per-slice performance error budgets; alert only when e.g. 5-day AND 60-day burn rates both breach — killing single-bad-day panic disables [ESTABLISHED pattern; INTERPRETATION for the specific windows].
3. **Slices need minimum evidence before they can be judged.** A 10-trade slice has a win-rate estimate with a ±~30-point confidence band; isolating on it is noise-chasing. Minimum sample sizes per slice (advisory ≥30, isolation ≥100 decisions) recorded per slice and enforced by alert logic [INTERPRETATION; binomial sampling variance ESTABLISHED].
4. **The isolation ladder answers "without shutting down the entire system".** (1) Disable the failing slice — only if sibling slices of the same strategy remain healthy; (2) pause the strategy — only if no slice is healthy and another strategy can absorb the mandate (G); (3) system halt — reserved for L on global criteria (total drawdown, data-integrity compromise), never reachable from a single slice's alarm. Every isolation event writes back to the log with its evidence trace [INTERPRETATION structure].
5. **Metrics and axes must be consistent and versioned.** Win rate, average edge after costs, estimated Sharpe (small-n caveat), calibration of predicted-vs-realized probabilities, data-quality pass rate, time-since-last-trade (a slice that stops trading is also failing) — identical definitions at every level [INTERPRETATION]. Slices keyed by model version mean a retrained model opens a new lineage; regime labels can be revised, so rollups must be recomputable from the immutable log [INTERPRETATION].

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|-------|-----------|------|-----|---------------------|-------------|----------|
| 1 | Monitoring (ML operations planning) | AWS Prescriptive Guidance | current | https://docs.aws.amazon.com/prescriptive-guidance/latest/ml-operations-planning/monitoring.html | Four monitoring dimensions: data quality, model quality, bias drift, feature attribution | Generic MLOps framing; page body fetch blocked — content confirmed via search index | YES (search-confirmed) |
| 2 | ML Lens BP04: Monitor, detect, and handle model degradation | AWS Well-Architected | current | https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/mlperf06-bp04.html | Drift detection and distribution monitoring best practice | Architecture-lens guidance, not a logging spec | YES (search-confirmed) |
| 3 | Data Capture — Amazon SageMaker AI | AWS | current | https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor-data-capture.html | Reference prediction-logging pattern: inputs + outputs, JSON-lines, sampling percentage | Field-level schema not opened (fetch blocked) | YES (search-confirmed) |
| 4 | Chapter 5 — Alerting on SLOs | Google SRE Workbook | 2018 | https://sre.google/workbook/alerting-on-slos | SLI = good/total events; burn rate; multiwindow multi-burn-rate thresholds | Cloud-service framing; thresholds are worked examples | YES (fetched) |
| 5 | Chapter 6 — Monitoring Distributed Systems | Google SRE Book | 2016 | https://sre.google/sre-book/monitoring-distributed-systems | Symptoms-vs-causes alerting doctrine; pages vs tickets | Infrastructure-era examples | YES (search-confirmed) |
| 6 | Model Cards for Model Reporting | M. Mitchell et al. | 2019 (FAT* '19, pp. 220–229) | https://arxiv.org/abs/1810.03993 | Structured per-model documentation incl. per-slice breakdowns | Documentation pattern, not a monitoring algorithm | YES |

**Source notes.** AWS sources (1–3) were confirmed via search index after bot-protection blocked direct fetches — flagged rather than silently upgraded; the SRE chapters (4–5) were read in full. Established: capture pattern, sampling knob, monitoring dimensions, SLO/burn-rate alerting, model cards. Experimental claims: none relied on. Interpretation: the field list, never-sample-decisions rule, minimum sample sizes, the isolation ladder.

## How the technique works

**Inputs.** Decision events (F/G at decision time) and outcome events (fills later); health profiles and thresholds; the slice taxonomy from D. **Outputs.** The immutable decision log; per-slice and rolled-up health metrics; confirmed isolation actions with evidence traces; the evidence substrate Q12/Q13 query.

**Mechanism.** (1) *Capture*: at decision time, synchronously write identity, processing, decision, and context groups; outcomes join asynchronously by key. (2) *Aggregate*: on schedule, compute per-slice metrics over trailing windows; maintain slice → strategy → system rollups; recompute from the log on demand. (3) *Evaluate*: compare metrics to the profile via burn-rate logic — short (e.g., 5-day) AND long (e.g., 60-day) windows must both breach. (4) *Isolate*: on confirmed breach, run the ladder — slice disable → strategy pause → (only L) system halt — each gated by sibling checks and minimum evidence. (5) *Record*: every alert and action appends to the log with its evidence trace.

**Formulas.** Slice win rate ŵ = wins/n with standard error sqrt(ŵ(1−ŵ)/n) — the minimum-evidence rule follows directly; burn rate = actual bad-event rate / allowed rate; alert iff burn_rate_short > b AND burn_rate_long > b; estimated Sharpe = mean(edge)/std(edge)·sqrt(annualization).

**Strengths.** Attribution-grade evidence; isolation at minimal blast radius; consistent metrics across levels; replayability for H; the same log feeds Q13 without new instrumentation. **Limitations.** Write/storage cost at intraday cadences (mitigated by hash-referenced raw inputs); outcome-join latency (open positions leave rows pending); regime-label revisions force rollup recomputation; combinatorial slice explosion — most slices are sparse, hence minimum evidence. **Failure conditions.** Silent logging failure (bot trades, log empty — needs the completeness monitor); clock skew breaking joins; schema evolution without versioning; sampling applied to decision rows; outcome misattribution (manual fills matched to bot decisions).

## Reference implementation sketch

```python
import numpy as np
import pandas as pd

def sharpe(s):
    sd = s.std(ddof=1)
    return float(s.mean() / sd * np.sqrt(252)) if sd > 0 else np.nan

def slice_health(log, min_trades=30, wr_floor=0.45):
    """Health rollup per (strategy, asset, regime, timeframe) slice.
    Point-in-time safe: caller passes only rows with date <= t."""
    ok = log[log["data_quality_ok"]]
    g = ok.groupby(["strategy", "asset", "regime", "timeframe"]).agg(
        trades=("edge_realized", "size"),
        win_rate=("edge_realized", lambda s: (s > 0).mean()),
        avg_edge=("edge_realized", "mean"),
        sharpe_est=("edge_realized", sharpe),
        models=("model_version", "nunique"))
    g["healthy"] = (g["trades"] >= min_trades) & (g["win_rate"] >= wr_floor)
    return g[~g["healthy"]].sort_values("trades", ascending=False)

if __name__ == "__main__":
    rng = np.random.default_rng(3)
    cells = [("momo", "ES", "trend"), ("momo", "ES", "range"),
             ("momo", "AAPL", "trend"), ("meanrev", "ES", "trend"),
             ("meanrev", "ES", "range"), ("meanrev", "AAPL", "trend")]
    frames = []
    for strat, asset, regime in cells:
        # exactly one degraded slice in the demo data
        wr = 0.30 if (strat, asset, regime) == ("meanrev", "ES", "trend") else 0.58
        frames.append(pd.DataFrame({
            "date": pd.date_range("2026-06-01", periods=100, freq="D"),
            "strategy": strat, "asset": asset, "regime": regime,
            "timeframe": "1d", "model_version": "v3",
            "data_quality_ok": True,
            "edge_realized": rng.normal(wr - 0.5, 0.02, 100)}))
    log = pd.concat(frames, ignore_index=True)
    print(slice_health(log))   # flags only meanrev/ES/trend
    # Isolation ladder (Q14-B): disable the failing slice only if siblings of
    # that strategy stay healthy; pause the strategy only if NO slice is
    # healthy; system halt is owned by independent risk controls (L) alone.
```

## Application to this project

**Inputs:** decision events (F/G/E), outcome events (fills), regime labels (D), quality flags (B), model metadata (I). **Outputs:** the decision log (consumed by Q12's detector streams and Q13's batteries); health rollups and profiles; isolation actions routed through K with L's override; the archive for H's replays.

**Components.** A: feed identity and content hashes enter the log at ingestion. B: quality flags are logged per decision — they let Q13-B rule pipeline failures in or out later. C: feature vectors + schema version per row; retraining reference windows (F/I) cite the log. D: regime labels logged at decision time and immutable, so reattribution is recomputable when D improves. E: outcome labels join by trade id. F/I: every row carries model_version; the registry stores each version's health profile. G: candidate scores and reason codes per selection — without them, "why did the bot pick this strategy" is unanswerable. H: replay evaluation reads the log directly. J: hosts rollups and burn-rate alerts. K: executes ladder steps 1–2. L: owns step 3 and vetoes K's automated actions. **Siblings:** Q12 consumes log-derived streams, Q13 runs batteries over log columns, Q14 defines the slices both use; adjacent: [[Q15 Continuous ML Pipeline]], [[Q11 Data Freshness and Recovery]], [[Q02 Bayesian Regime Detection]].

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Evidence to inspect locally:

- [ ] Existence and schema of any decision/prediction/trade log (fields vs the five field groups).
- [ ] Whether predictions and realized outcomes are joinable by stable keys, and whether outcome rows are orphaned.
- [ ] Whether model_version, feature_schema_version, and regime labels are stamped on every decision row.
- [ ] Whether per-slice (asset/regime/timeframe/strategy) metric computation exists today.
- [ ] Whether health profiles/thresholds exist (config or registry).
- [ ] Whether enable/disable controls are per-slice, per-strategy, or global-only, and whether alerting uses any confirmation window.
- [ ] Whether a completeness monitor (outcome rows vs prediction rows) exists.
- [ ] Vocabulary: IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY.

## Recommended improvements

1. **P0 — Define and version the decision-log schema** (five field groups), synchronous writes at decision time; decision rows never sampled, never mutated.
2. **P0 — Build the per-slice health rollup** (strategy × asset × regime × timeframe, keyed by model version) with minimum evidence (advisory ≥30, isolation ≥100) and two-tier retention.
3. **P0 — Add a log-completeness monitor:** every prediction row terminates in an outcome or a documented non-fill; a silent logging break must page.
4. **P1 — Multiwindow confirmation for isolation alerts** (5-day AND 60-day burn-rate breach against the slice's profile).
5. **P1 — Codify the isolation ladder** (slice disable → strategy pause → system halt) with sibling-health preconditions, evidence traces, and L as sole owner of the global halt.
6. **P1/P2 — Publish per-model health profiles at deploy time** (model-card style) and **keep rollups a pure function of the immutable log** so regime revisions (D) can reattribute history.

## Dependencies

- Software: pandas/numpy (core rollups); a partitioned append-only store (parquet/object storage); no optional ML dependency required.
- Siblings: [[Q12 ADWIN Concept Drift]], [[Q13 Drift Diagnosis]], [[Q15 Continuous ML Pipeline]], [[Q11 Data Freshness and Recovery]], [[Q02 Bayesian Regime Detection]], [[Gate 4 Continuous Learning]].
- Plan components: F/G/E produce events; J hosts; K/L act; I stores profiles; H replays.

## Acceptance criteria

1. Schema test: every decision row contains all five field groups with non-null identity keys; violations fail CI.
2. Join-integrity test: over any replayed period, prediction rows resolve to outcome rows or documented non-fills at or above a replay-derived baseline (baseline first; the criterion is *no silent orphans*).
3. Rollup test: slice rollups are reproducible from the log (pure function) and match a hand-computed fixture slice.
4. Isolation test: a simulated failing slice triggers slice-level disable only, siblings untouched; an all-slices failure escalates to strategy pause; no single-slice event can reach system halt (enforced by test).
5. Confirmation test: a one-day breach fires no isolation alert; a sustained short+long-window breach does.
6. Retention test: archive/rollup jobs never delete decision rows with unresolved outcomes.

## Risk assessment

- **Silent logging failure (highest-impact failure mode):** the whole stack goes blind while the bot trades; mitigated by the completeness monitor (P0.3).
- **Storage growth / write cost:** mitigated by hash-referenced raw inputs, sampling limited to raw captures, partitioned archives.
- **Over/under-isolation:** sparse slices misjudged as failing, or confirmation windows delaying action on a truly broken strategy; mitigated by minimum-evidence gating, multiwindow confirmation, and L's independent global criteria.
- **Schema drift / clock skew:** unversioned feature/model changes and timestamp skew corrupt attribution; mitigated by versioned schemas, UTC discipline, monotonic bar indexes, and CI checks.

## Implementation decision

Implement the decision log (Q14-A) as the foundational P0, immediately followed by per-slice rollups and the isolation ladder (Q14-B), because Q12 and Q13 are unimplementable as specified without this evidence layer. Adopt the AWS capture pattern (inputs+outputs per decision; sampling for raw captures only) and the SRE alerting discipline (symptoms, multiwindow confirmation); treat model cards as the deploy-time documentation contract. Deferred until the local audit classifies existing capability; this note is the design contract. [INTERPRETATION]

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in locally after implementation:

- Files changed: `<fill in — e.g., logging/decision_log.py, schemas/decision_log.v1.avro, monitoring/rollups.py, monitoring/isolation.py>`
- Tests added/run: `<fill in — schema CI test, join-integrity replay, isolation ladder, confirmation windows>`
- Results: `<fill in — baseline join rate, rollup compute time, isolation drill outcomes>`
- Rollback reference: `<fill in — commit/tag or config flag disabling rollups and the ladder>`
- Date / implementer: `<fill in>`

## Outstanding questions

1. Exact retention windows for full-fidelity rows — establish from local data volumes first.
2. Minimum sample sizes per slice (30/100 are proposed starting points) — calibrate against actual slice sparsity.
3. How pending (open-position) rows should enter win-rate metrics without biasing short windows.
4. Whether regime-label revisions (D) should retrigger rollups automatically or via a reviewed job.

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q12 ADWIN Concept Drift]]
- [[Q13 Drift Diagnosis]]
- [[Gate 4 Continuous Learning]]
- [[Q15 Continuous ML Pipeline]]
- [[Q11 Data Freshness and Recovery]]
- [[Q02 Bayesian Regime Detection]]
