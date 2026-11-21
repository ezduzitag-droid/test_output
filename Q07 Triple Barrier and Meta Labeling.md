---
type: research-record
ids: [Q07-A, Q07-B]
category: Historical Training
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q07 Triple Barrier and Meta Labeling

This record establishes how the bot converts price history into realistic training labels and how a second-stage model decides whether to trust a proposed trade. The Triple Barrier Method (TBM) labels each event by which of three barriers the price touches first — upper at a volatility-adjusted profit target, lower at a volatility-adjusted stop-loss, vertical at maximum holding time — so labels mirror actual trade outcomes (win, loss, time-out) rather than fixed-horizon returns. Meta-labeling splits the problem: a primary model proposes the side, a secondary model outputs a probability used to accept, reject, or size the bet. Both demand overlapping-label corrections and leakage avoidance ([[Q06 Time Series Validation]]).

## Question IDs

- **Q07-A** — Constructing historical training labels with volatility-adjusted profit targets, stop-loss thresholds, and maximum holding periods (Triple Barrier Method).
- **Q07-B** — Implementing a primary prediction model plus a secondary meta-labeling model that evaluates whether a proposed trade should be accepted, rejected, or assigned a risk level.

## Original research questions

- **Q07-A**: "How should our bot construct historical training labels using volatility-adjusted profit targets, stop-loss thresholds, and maximum holding periods so that it learns from realistic winning and losing events?"
- **Q07-B**: "How could we implement a primary prediction model alongside a secondary meta-labeling model that evaluates whether a proposed strategy should be accepted, rejected, or assigned a particular risk level?"

## Research objective

**Q07-A** must establish a labeling pipeline whose labels mirror real trade outcomes — win, loss, time-out — with barrier distances scaled by ex-ante volatility so "2%" means different things in calm and turbulent markets. Mis-specified labels (fixed next-bar returns) teach noise-chasing and misrepresent risk. Affects **E**, **F**, **C**, **H**.

**Q07-B** must establish a two-stage architecture: the primary model supplies direction, the meta-model supplies conviction — accept/reject and bet sizing from a calibrated success probability. Direction accuracy and profitability differ — meta-labeling attacks the false positives that destroy risk-adjusted returns. Affects **F**, **G**, **H**, **L**.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit locally:

- [ ] How are labels produced today: fixed-horizon forward returns, sign of n-bar return, or barrier-based?
- [ ] Does a point-in-time volatility estimator exist (rolling std shifted one bar) for barrier distances?
- [ ] Any event generator (CUSUM filter, signal timestamps) defining when labeling starts?
- [ ] Any existing two-model stack — primary signal plus a filter/size model (search `meta`, `bet_size`)?
- [ ] How is class imbalance handled in F, and do any sample weights or uniqueness computations exist?
- [ ] Does labeling touch prices strictly after event time only (`shift(-k)` producing label *features* is a red flag)?
- [ ] Does simulation (H) model PT/SL exits so labels and simulation can agree, and is mlfinlab (or equivalent) available?

## Technical concepts

- **Triple Barrier Method (TBM)**: labeling by which of three barriers the price path touches first — upper (profit target), lower (stop-loss), vertical (time expiry). [ESTABLISHED]
- **Volatility-adjusted barriers**: distances as multiples of an ex-ante volatility estimate (rolling return std known at event time), keeping targets comparable across regimes.
- **Event labeling**: labels attached to discrete events (e.g., CUSUM threshold crossings) rather than every bar, reducing overlap.
- **Side-aware labeling**: with a primary model's direction (side ±1), barriers apply relative to that side and the label reduces to win/loss/timeout — the binary form meta-labeling needs.
- **Meta-labeling**: a second-stage model predicting whether the primary's signal will be profitable; outputs filter (accept/reject) and size positions. [ESTABLISHED]
- **Label imbalance**: unequal win/loss/timeout counts; unhandled, the classifier defaults to the majority class.
- **Overlapping events and concurrency**: labels spanning [t₀, t₁] share calendar time; concurrency counts how many label intervals are open at a bar.
- **Average uniqueness**: mean fraction of a label's interval during which it is concurrently open; sample weight = average uniqueness (AFML ch. 4), preventing crowded regimes from dominating training. [ESTABLISHED]
- **Calibration**: mapping raw scores to probabilities matching empirical frequencies (isotonic/Platt), required because sizing consumes probabilities as frequencies.
- **CUSUM filter**: event detector sampling bars where cumulative summed deviations exceed a threshold. [ESTABLISHED]

## Research findings

### Q07-A findings

- TBM is specified in AFML ch. 3 (sec. 3.2, "Meta-Labeling and Triple Barrier Method"): upper = profit-take, lower = stop-loss, vertical = time limit; first touch determines the label; barriers tied to volatility (e.g., symmetric ±2× daily volatility). [ESTABLISHED]
- Open-source corroboration: mlfinlab (Hudson & Thames) implements triple-barrier labeling in verified code (`mlfinlab/labeling/labeling.py`); mlfinpy's docs restate AFML ch. 3.2. [ESTABLISHED]
- Why volatility adjustment matters: fixed thresholds conflate market conditions with strategy quality; ex-ante scaling measures risk-proportional capture. [ESTABLISHED method; rationale is standard interpretation]
- Leakage rules: volatility from data strictly before t₀; the label scan uses prices strictly after t₀; ties resolve to the stop-loss (conservative convention). [INTERPRETATION]
- Overlap is inherent: many labels overlap a volatile week, so AFML ch. 4 prescribes average-uniqueness weights. Unweighted, the model overfits crowded regimes. [ESTABLISHED]
- **Disagreement documented**: timeout labels — AFML's canonical example uses the sign of the return between t₀ and t₁; some implementations use 0 (neutral) or exclude timeouts. Resolution: canonical sign for 3-class use; non-win (0) for meta-labeling; fixed once in config so training and evaluation agree. [INTERPRETATION grounded in the source discrepancy]

### Q07-B findings

- Meta-labeling is introduced in AFML ch. 3: the primary model emits side ±1; the secondary model predicts P(success | features at t₀) from side-aware binary labels; outputs filter false positives and set bet size (size = 2·P − 1 in ch. 10's framing). Benefit: precision rises (fewer false positives) at unchanged recall — fewer losing trades. [ESTABLISHED]
- Empirical corroboration (fetched in full): Hudson & Thames' "Does Meta-Labeling Add to Signal Efficacy?" (Singh & Joubert, WorldQuant University capstone) applied the full stack on S&P 500 E-mini dollar bars with two technical primaries (Bollinger mean reversion; 20/50 SMA crossover), CUSUM events, and a Random Forest meta-model: out-of-sample accuracy rose 17%→63% (mean reversion) and 48%→55% (trend), precision improved in both — results "corroborate (although with only two strategies)". Stated limitations: no bet sizing yet, weak primaries, non-comparable periods. [ESTABLISHED for the experiment; generalization beyond it is not established]
- Peer-reviewed corroboration: Joubert (2022), "Meta-Labeling: Theory and Framework", Journal of Financial Data Science 4(3):31–44 — formalizes the two-stage setup and its precision/recall threshold trade-offs. [ESTABLISHED]
- Risk-level assignment [INTERPRETATION on the established sizing principle]: calibrated p maps to (a) reject if p < p_min; (b) bet size (p − p_min)/(1 − p_min) clipped to [0,1]; (c) optional risk bands consumed by L. Thresholds are chosen once on untouched validation data (Q05-B governance).
- Prerequisites: meta-model calibration ([[Q08 Financial ML Evaluation]]), imbalance handling, uniqueness weights. [ESTABLISHED]
- **Disagreement documented**: the capstone's large gains reflect a weak primary — meta-labeling has most headroom when the primary is mediocre; AFML's framing implies smaller, cleaner gains for a good primary. Evaluate the stacked system rather than quoting capstone numbers. [INTERPRETATION]

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|---|---|---|---|---|---|---|
| 1 | Advances in Financial Machine Learning ch. 3 (3.2) | López de Prado (Wiley) | Feb 2018 | https://www.wiley.com/en-us/shop/general-finance-investments/advances-in-financial-machine-learning-p-9781119482086 | Canonical TBM + meta-labeling spec; side-aware labels; F1 rationale | Book; barrier constants are examples | YES |
| 2 | mlfinlab labeling implementation | Hudson & Thames | current master | https://github.com/hudson-and-thames/mlfinlab/blob/master/mlfinlab/labeling/labeling.py | Reference triple-barrier code (barrier touch logic, molecule processing) | License/features changed over time | YES |
| 3 | Does Meta-Labeling Add to Signal Efficacy? | Singh, Joubert (Hudson & Thames / WorldQuant U) | 2020–2022 | https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method | End-to-end empirical test: CUSUM + dollar bars + TBM + RF meta-model; OOS gains | Two strategies; no sizing; weak primaries | YES (fetched) |
| 4 | Meta-Labeling: Theory and Framework | Joubert, J.F. (J. Financial Data Science 4(3):31–44) | 2022 | https://scholar.google.com/citations?user=J-PgoMAAAAAJ | Peer-reviewed formalization of meta-labeling | Paywalled; framework, not new empirics | YES |
| 5 | mlfinpy Labelling / Sampling docs | mlfinpy project | current | https://mlfinpy.readthedocs.io/en/latest/Labelling.html ; https://mlfinpy.readthedocs.io/en/latest/Sampling.html | Restates AFML ch. 3.2; uniqueness weights | Community reimplementation | YES |

Notes: Source 1 is the primary specification all others cite, confirmed via the publisher TOC and mlfinpy. Source 3 was fetched in full; its numbers are cited with its own limitations attached. Source 4 (JFDS 4(3):31–44, 2022) confirmed via Google Scholar and an independent citing dissertation. Established: TBM mechanics, side-aware meta-labeling, uniqueness weighting, the capstone's measured results. Experimental claims: thresholds and risk bands. Interpretation: tie-breaking, timeout convention, dependence on primary quality.

## How the technique works

**Triple Barrier Method.** Inputs: chronological price series, event times t₀, ex-ante volatility σ_{t₀} (rolling std over v bars, known at t₀), multipliers k_up/k_dn, vertical horizon h. Construction: P_up = P_{t₀}·(1 + side·k_up·σ_{t₀}); P_dn = P_{t₀}·(1 − side·k_dn·σ_{t₀}); t_v = t₀ + h bars. Scan bars t₀+1…t_v: first close beyond P_up → +1 (profit touch); beyond P_dn → −1 (stop touch); expiry → vertical outcome (canonical: sign of return; side-aware binary: 0 = non-win). Persist t₁ for purging ([[Q06 Time Series Validation]]) and uniqueness weighting. Output: (t₀, t₁, label, return).

**Sample weights by average uniqueness.** For label i over [t₀ᵢ, t₁ᵢ]: concurrency c_t = number of open label intervals at bar t; u_i = mean over the span of 1/c_t; weight w_i = u_i (optionally × return attribution and time decay); pass to `model.fit(..., sample_weight=w)`.

**Meta-labeling stack.** Stage 1: primary model/rules emit side s_t at event times. Stage 2: dataset (features X_{t₀} computed only from data ≤ t₀; binary label y = profit touch or not; weights w_i); train a probabilistic classifier. Inference: meta-model outputs p; reject if p < p_min; else size b = (p − p_min)/(1 − p_min) or a risk band. Strengths: separates direction skill from conviction; reduces false positives; sizing integrates with risk controls. Limitations: inherits the primary's blind spots (side errors can only be filtered); needs enough events; calibration drifts. Failure: uncalibrated probabilities, imbalance collapse, post-t₀ leakage. Cost: one extra classifier plus an O(events × h) barrier scan.

## Reference implementation sketch

```python
# Triple Barrier labeling (AFML ch.3) + uniqueness weights. pandas/numpy only.
# Point-in-time safe: sigma uses data strictly BEFORE t0 (shift(1)); the
# label scan uses prices strictly AFTER t0.
import numpy as np
import pandas as pd

def triple_barrier(close, events, pt_mult=2.0, sl_mult=2.0, max_hold=10,
                   vol_span=20):
    """events: DataFrame indexed by event time t0, optional 'side' column
    (default +1). Returns (t0, t1, label, ret): +1 profit touch, -1 stop
    touch, 0 vertical non-win."""
    ret = close.pct_change()
    sigma = ret.rolling(vol_span).std().shift(1)          # ex-ante volatility
    out = []
    for t0, row in events.iterrows():
        side = int(row.get('side', 1))
        i0 = close.index.get_loc(t0)
        window = close.iloc[i0 + 1: i0 + 1 + max_hold]    # strictly after t0
        if window.empty or np.isnan(sigma.loc[t0]):
            continue
        p0 = close.loc[t0]
        up = p0 * (1 + side * pt_mult * sigma.loc[t0])
        dn = p0 * (1 - side * sl_mult * sigma.loc[t0])
        t_up = window.index[window >= up][0] if (window >= up).any() else None
        t_dn = window.index[window <= dn][0] if (window <= dn).any() else None
        if t_dn is not None and (t_up is None or t_dn <= t_up):   # tie -> stop
            t1, label = t_dn, -1
        elif t_up is not None:
            t1, label = t_up, 1
        else:
            t1, label = window.index[-1], 0               # vertical
        out.append({'t0': t0, 't1': t1, 'label': label,
                    'ret': side * (close.loc[t1] / p0 - 1)})
    return pd.DataFrame(out).set_index('t0')

def average_uniqueness(labeled, bar_index):
    """w_i = mean over label span of 1/concurrency (AFML ch. 4)."""
    conc = pd.Series(0.0, index=bar_index)
    for _, r in labeled.iterrows():
        conc.loc[r['t0']:r['t1']] += 1.0
    w = [(1.0 / conc.loc[r['t0']:r['t1']]).mean() for _, r in labeled.iterrows()]
    return pd.Series(w, index=labeled.index)

# Meta-labeling: y = (label == 1) on side-aware rows; then
#   clf.fit(X_meta, y, sample_weight=w) -> p = clf.predict_proba(X)[:, 1]
# Policy: reject if p < p_min, else size = (p - p_min) / (1 - p_min).
```

## Application to this project

- **E** owns the TBM pipeline: event generation, barrier configuration (k_up, k_dn, h per timeframe), labels, t₁ persistence.
- **F** trains on TBM labels with uniqueness weights and imbalance handling; for Q07-B it trains the stage-2 meta-model per primary family on side-aware binary labels.
- **G** consumes meta-model probabilities for accept/reject/risk decisions; a family is surfaced only when its meta-model is calibrated and passes the Q05/Q08 gates.
- **H** simulates exits with the same barrier rules as labeling; its per-period streams feed Q05's PBO/DSR machinery.
- **L** uses bet size / risk bands as an exposure input, bounded by its own limits.
- Cross-links: t₁ sizes Q06's purge gap; calibration metrics standardized in Q08; [[Gate 2 Historical Training]] checks agreement end to end.

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Inspect:

- [ ] Label generator identity (fixed-horizon vs barrier); are (t0, t1, label) persisted or bare labels?
- [ ] Volatility estimator: existence, span, ex-ante shift (leakage check).
- [ ] Event generator and meta-model artifacts: CUSUM/signal-time producers; second-stage classifier; calibration usage.
- [ ] Sample weights/uniqueness in the training path; imbalance handling in F configs.
- [ ] Simulation/label agreement: does H implement PT/SL exits matching the labels; any assertion.
- [ ] Config surface for multipliers/spans/holdings; mlfinlab availability and license.

## Recommended improvements

1. **P0 — TBM labeling module.** Volatility-scaled barriers, ex-ante sigma, t₁ persistence; unit tests on toy paths (touches, ties, timeouts).
2. **P0 — Leakage guardrails.** Assert sigma is ex-ante and scans use strictly post-t₀ prices; canary where corrupting post-t₀ bars must change labels but not features.
3. **P1 — Uniqueness weights.** Concurrency/average-uniqueness weights passed into all stage-2 fits; report weight distributions per run.
4. **P1 — Meta-labeling stack.** Calibrated meta-model per primary family; p_min and sizing policy fixed once on untouched validation data, then frozen.
5. **P1 — Label/simulation agreement test.** Property test that H's exit logic reproduces labels on sampled historical events within tolerance.
6. **P2 — Barrier multipliers as hyper-parameters.** Optimize (k_up, k_dn, h) inside Q06's purged-CV loop; log as trials for Q05's DSR.

## Dependencies

- Depends on component B (clean bars) and C (as-of event-time features).
- Feeds and depends on [[Q06 Time Series Validation]]: t₁ sizes the gap; event labels require interval-intersection purging.
- Consumed by [[Q05 Backtest Overfitting]] and [[Q08 Financial ML Evaluation]]; regime-conditional multipliers may depend on component D; consolidated by [[Gate 2 Historical Training]].

## Acceptance criteria

- Labeling deterministic (a test reproduces stored labels exactly) and point-in-time safe (post-t₀ corruption changes labels but not features).
- Coverage: ≥ 90% of events resolve to a label (no NaN sigma) — baseline measured on first run.
- Uniqueness: mean average-uniqueness reported per run; regression test fails on material undocumented drops (baseline first run).
- Meta-model: Brier score on untouched validation below the persistence baseline (computed from the first labeled dataset); calibration curve monotone within tolerance.
- Simulation-vs-label agreement ≥ 99% of sampled historical events (tolerance documented).

## Risk assessment

- **Implementation**: barrier-scan bugs at session boundaries; tie conventions inconsistent between labeling and simulation; concurrency cost for long horizons.
- **Operational**: too few events starve the meta-model; imbalance collapse without resampling; probability drift needs scheduled recalibration (J alert).
- **Failure modes**: silent leakage if feature lags are dropped; primary side errors propagate as losses the meta-model can only reduce.
- **Regressions**: vol span/multiplier changes without re-purging re-introduce leakage — gate config changes behind Q06's fold registry.

## Implementation decision

Adopt TBM (volatility-scaled barriers; side-aware binary labels for meta-labeling) plus uniqueness-weighted, calibrated meta-models for E/F/G. Prefer a vetted library (mlfinlab/mlfinpy) where licensing permits, else implement from AFML ch. 3–4 with the tests above. Deferred pending the local audit; timeout/tie conventions fixed once in config.

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in locally after implementation:

- Files changed: (labeling module, event generator, meta-model path, config schema)
- Tests added: (toy-path cases, tie/timeout conventions, leakage canaries, uniqueness, calibration)
- Results: (coverage %, class balance, mean uniqueness, Brier/log-loss vs baseline, stacked backtest metrics)
- Rollback reference: (commit/tag; flag to revert labeling)
- Date / owner: (sign-off)

## Outstanding questions

- Which timeout convention is more useful for this bot's holding periods — one untouched-data experiment decides.
- Should barrier multipliers differ per regime class (component D) without exploding trial counts (Q05)?
- Minimum event count for a trustworthy meta-model per family (learning curves).
- Should meta-model features include the primary model's own confidence (feedback-loop risk)?

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q05 Backtest Overfitting]]
- [[Q06 Time Series Validation]]
- [[Q08 Financial ML Evaluation]]
- [[Gate 2 Historical Training]]
