---
type: research-record
ids: [Q01-A, Q01-B]
category: Market Regimes
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q01 HMM Market Regimes

This record establishes how a hidden Markov model (HMM) should identify market regimes from historical features — volatility, momentum, volume, price movement, correlations — and how regime-conditioned strategy performance is learned and validated on unseen data. The literature is unambiguous that Markov-switching models are the canonical tool for latent market states [ESTABLISHED], but the decisive constraint is causality: at decision time the bot may use only forward-filtered probabilities over data up to that time — never smoothed probabilities, Viterbi paths, or parameters fitted beyond the decision date. Regime-conditioned strategy learning must be validated walk-forward with sample-size and label-stability checks. Causal probabilities feed components D, G, and H pending the local audit.

## Question IDs

- Q01-A — Regime identification/classification from historical information without look-ahead.
- Q01-B — Learning regime-conditioned strategy performance and validating it out-of-sample.

## Original research questions

- Q01-A: "How should our ML bot identify and classify market regimes using historical information such as volatility, momentum, volume, price movement, and correlations, without accidentally using information from the future?"
- Q01-B: "How should the bot learn which strategies perform best within each identified market regime, and how can it establish that those relationships remain effective on previously unseen historical data?"

## Research objective

**Q01-A** must establish the model class mapping features onto latent regimes, the decision-safe inference output (filtered, not smoothed), and the parameter/normalization/label handling that prevents leakage — every downstream consumer inherits any leak. Affects components B, C, D, H, I.

**Q01-B** must establish how strategy performance is conditioned on regimes, what evidence suffices for out-of-sample generalization, and the sample-size/stability/walk-forward requirements making the claim testable — selection only pays if rankings persist. Affects components F, G, H, L.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Check locally before implementation planning.

- [ ] Regime/HMM code: `hmmlearn`, `pomegranate`, `statsmodels` regime switching, custom Baum-Welch/Viterbi.
- [ ] Feature pipeline for realized vol, momentum, volume, correlations; full-sample vs trailing normalization.
- [ ] Persisted regime labels and their producing code: filtering, smoothing, or Viterbi?
- [ ] Selection conditionals keyed on regime labels; config flags for gating.
- [ ] Unit tests: determinism, refit cadence, insufficient-data edges, probability sums.
- [ ] Harness: refits inside the simulation loop, or full-sample fit replayed?
- [ ] Registry entries for regime models (window, state count, emission type, seed).
- [ ] Monitoring of regime probabilities, transition alerts, drift.
- [ ] Look-ahead-prone calls in decision paths (`decode(`, full-series `predict`).
- [ ] Availability timestamps recorded per feature feed.

## Technical concepts

- **Hidden Markov Model (HMM):** hidden state evolves as a Markov chain; observable data is emitted with state-dependent distributions.
- **Observable market features:** per-date quantities — realized vol, returns, momentum, volume changes, correlations — used to infer the hidden state.
- **Hidden market states:** unobserved regimes (calm, stress, crisis) explaining joint feature behavior.
- **Transition probabilities:** `a_ij = P(z_t = j | z_{t-1} = i)` — one-step state-change chances, in matrix A.
- **Emission probabilities:** likelihood of features given the state, typically per-state Gaussians `b_i(o) = N(o; μ_i, Σ_i)`.
- **Regime classification:** assigning dates a label, ideally with the posterior over states, not a bare label.
- **Filtering vs smoothing:** filtering computes `P(z_t | o_1:t)` from past data (causal, safe); smoothing `P(z_t | o_1:T)` uses the whole sample (non-causal, unsafe at decision time).
- **Historical regime reconstruction:** dashboards may use smoothed/Viterbi paths; backtests must rebuild labels causally.
- **Model confidence:** filtered posterior's max probability or entropy; low confidence means features fit several states equally.
- **Regime stability:** state persistence (expected dwell `1/(1 − a_ii)`) and consistent feature-to-state mapping across refits.
- **Look-ahead bias:** using anything at decision time not available then — via smoothed labels, full-sample fits, full-sample normalization.
- **Feature normalization:** standardizing with trailing/rolling statistics only.
- **Market state visualization:** stacked filtered-probability charts or time-in-state heatmaps.
- **Strategy-conditioned-on-regime learning:** a regime × strategy performance table, preferably soft-weighted.
- **Out-of-sample validation:** testing regime–strategy rankings on unused periods (walk-forward).

## Research findings

### Q01-A findings

- Markov-switching/HMM models are the established framework for latent regimes: Hamilton (1989) introduced the Markov-switching autoregression and its filter [ESTABLISHED]; Rabiner (1989) codified forward, forward-backward, Viterbi, and Baum-Welch (EM) [ESTABLISHED].
- Gaussian emissions on point-in-time features are standard: Wang, Lin and Mikhelson (2020) fit an HMM on S&P 500 ETF data, switch factor strategies by regime, and report out-of-sample gains over any single factor [ESTABLISHED as a published result; one asset class, one decade — replication required before trusting the magnitude].
- The filtering/smoothing distinction is the key look-ahead control: the forward algorithm is causal; smoother and Viterbi condition on the whole sample including the future [ESTABLISHED theory]. Many practitioner pipelines backtest on full-sample Viterbi/smoothed labels, inflating results [CONTESTED] — resolved conservatively: dashboard-only, never decision inputs.
- Parameter estimation leaks separately: a full-sample fit encodes future observations even if queried causally; walk-forward fitting on data ≤ t is required [ESTABLISHED principle; refit cadence INTERPRETATION]. Kim and Nelson (1999) treat filtered vs smoothed inference rigorously.
- Normalization must be point-in-time (trailing mean/std); Baum-Welch is scale- and outlier-sensitive, so winsorize and log-transform volume-like features [INTERPRETATION].
- Two to four states cover typical usage (Hamilton's two-state model; Hardy 2001's stock-return regimes) [ESTABLISHED as common practice]; select K by held-out likelihood/BIC per fold; handle label switching by matching emission centroids [INTERPRETATION].
- Stability is measurable: expected dwell in state i is `1/(1 − a_ii)`; too many states give short, noisy dwell — a concrete overfitting symptom [ESTABLISHED formula; thresholds INTERPRETATION].

### Q01-B findings

- Estimate the regime–strategy relationship as a performance table on training folds only: per regime and strategy, store mean/variance of PIT returns net of costs with observation counts. Soft weighting beats hard gating because hard labels flip noisily at boundaries [INTERPRETATION].
- Validation must be walk-forward: estimate the table on fold [t0, t1), test rank persistence on later folds, repeat with rolling origins. "Strategy X is best in regime R" holds only if rankings persist with a minimum per-regime observation count. Wang et al. (2020) evaluate this way, making their positive result meaningful despite single-market scope [ESTABLISHED; external validity limited].
- Labels inside validation must be causally reconstructed (Q01-A discipline); smoothed labels invalidate the test [ESTABLISHED consequence; CONTESTED in practice].
- Expect instability: state identity flips across refits; mitigate with canonical state naming, minimum dwell before computing per-regime statistics, bootstrap intervals on differences [INTERPRETATION].
- Where per-regime statistics are unreliable (rare regimes, short history), fall back to Q03's context-aware selector [INTERPRETATION].

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|-------|------------|------|-----|---------------------|-------------|----------|
| 1 | A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle | James D. Hamilton, Econometrica 57(2):357–384 | 1989-03 | https://ideas.repec.org/a/ecm/emetrp/v57y1989i2p357-84.html | Markov-switching autoregressions; the Hamilton filter for causal regime probabilities | Macro framing; two-state example | YES |
| 2 | A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition | L. R. Rabiner, Proceedings of the IEEE 77(2):257–286 | 1989-02 | https://ieeexplore.ieee.org/document/18626 | Canonical forward/backward/Viterbi/Baum-Welch definitions | Speech domain; numerics need finance adaptation | YES |
| 3 | State-Space Models with Regime Switching: Classical and Gibbs-Sampling Approaches with Applications | Chang-Jin Kim & Charles R. Nelson, MIT Press | 1999 | https://mitpress.mit.edu/9780262535502/state-space-models-with-regime-switching | Rigorous filtered-vs-smoothed treatment; Bayesian Gibbs alternative | Book-level theory; macro applications | YES |
| 4 | A Regime-Switching Model of Long-Term Stock Returns | Mary R. Hardy, North American Actuarial Journal 5(2):41–53 | 2001-04 | https://www.tandfonline.com/doi/abs/10.1080/10920277.2001.10595984 | Regime switching on stock returns for long horizons | Actuarial framing; asset-specific selection details | YES |
| 5 | hmmlearn documentation | hmmlearn maintainers | current (0.3.x) | https://hmmlearn.readthedocs.io/en/latest/ | Python HMM library, scikit-learn-style API, unsupervised inference | No point-in-time enforcement; EM needs seeding | YES |
| 6 | Regime-Switching Factor Investing with Hidden Markov Models | M. Wang, Y.-H. Lin, I. Mikhelson, J. Risk and Financial Management 13(12):311 | 2020-12 | https://www.mdpi.com/1911-8074/13/12/311 | HMM regimes driving factor-strategy switching; out-of-sample improvement reported | Single market/period; specific feature set | YES |

Most important: Hamilton (1989) originates the model class and the filter; Rabiner (1989) is the algorithm reference; Kim and Nelson (1999) the inference-discipline treatment; Wang et al. (2020) — located from an unverified lead by confirming landing metadata — is the closest verified instance of this exact use case, evidence of feasibility rather than guaranteed edge. Lead note: the original lead cited Albert & Chib (1993) as a JASA title; no such title was verifiable — the actual paper is in the Journal of Business & Economic Statistics (see Q02).

Established: Markov-switching models; the filtering/smoothing/Viterbi taxonomy; walk-forward estimation. Experimental: the benefit magnitude (one market, one period). Interpretation: refit cadence, K selection, soft weighting, centroid matching, winsorization.

## How the technique works

Latent state `z_t ∈ {1..K}` follows a Markov chain with transition matrix A; features `o_t` are emitted per state by `N(o_t; μ_i, Σ_i)`. Forward filtering: `α_t(j) = b_j(o_t) · Σ_i α_{t-1}(i) · a_ij`, normalized — exactly `P(z_t = j | o_1:t)`, the decision-time regime probability (Hamilton filter). Smoothing adds the backward recursion `β_t(i) = Σ_j a_ij · b_j(o_{t+1}) · β_{t+1}(j)`, giving `P(z_t | o_1:T)`, which conditions on future data; Viterbi is the max-product whole-sample path. Baum-Welch (EM) alternates expected state occupancies with parameter updates to locally maximize likelihood.

Required inputs: point-in-time feature matrix, refit cadence, training window. Outputs: filtered probability vector per date, argmax label, transition matrix, emission parameters, expected dwell `1/(1 − a_ii)`, confidence (max probability/entropy). Strengths: principled uncertainty, few parameters, unsupervised. Limitations: geometric durations, outlier-sensitive Gaussians, EM local optima, state identity switching across refits. Computation: O(K²T) per forward pass — trivial at daily frequency. Failure conditions: non-stationary/unnormalized features, K too large, singular covariances (need `min_covar`), data gaps, and any smoothed/Viterbi output in the decision path.

## Reference implementation sketch

```python
import numpy as np
import pandas as pd
# Requires: pip install hmmlearn (optional dependency, not part of scikit-learn)
from hmmlearn.hmm import GaussianHMM

def build_features(px: pd.DataFrame) -> pd.DataFrame:
    """px: index=date, columns=[close, volume]. Each feature at t uses data <= t."""    f = pd.DataFrame(index=px.index)
    f["ret"] = np.log(px["close"]).diff()
    f["vol"] = f["ret"].rolling(21).std() * np.sqrt(252)
    f["mom"] = px["close"].pct_change(63)
    f["volu"] = np.log(px["volume"]).diff()
    return f.dropna()

def match_states(new_means, old_means):
    """Map new-state index -> old label by nearest emission centroid (label switching)."""
    if old_means is None:
        return np.arange(new_means.shape[0])
    d = np.linalg.norm(new_means[:, None, :] - old_means[None, :, :], axis=2)
    return d.argmin(axis=1)

def walk_forward_regimes(f, n_states=3, window=252 * 8, refit_every=21, seed=0):
    """Causal HMM regimes: at date t, features/normalization use data <= t,
    parameters come from a trailing-window fit, inference is the forward filter
    only (predict_proba over the trailing window, last row). Viterbi/decode and
    smoothing are deliberately NOT used."""
    cols = [f"p_state_{k}" for k in range(n_states)]
    out = pd.DataFrame(index=f.index, columns=cols, dtype=float)
    model, old_means, order = None, None, np.arange(n_states)
    for i, d in enumerate(f.index):
        train = f.iloc[max(0, i - window): i + 1]           # strictly <= t
        X = (train - train.mean()) / train.std().replace(0, 1e-9)
        if model is None or i % refit_every == 0:           # trailing-window refit
            try:
                m = GaussianHMM(n_components=n_states, covariance_type="diag",
                                n_iter=100, min_covar=1e-6, random_state=seed)
                m.fit(X.values)
                model = m
                order = match_states(m.means_, old_means)   # keep labels stable
                old_means = m.means_.copy()
            except Exception:
                pass                                        # keep previous model
        if model is not None:
            probs = model.predict_proba(X.values)[-1]       # P(z_t | o_1:t) filter
            out.loc[d, cols] = probs[order]
    return out
# Downstream: dwell_i = 1 / (1 - transmat[i, i]); labels go through Q02 first.
```

## Application to this project

Component B: adopt trailing-window standardization and winsorization as validation checks. Component C: the sketch's feature set is the emission basis, gated by Q04-B. Component D: the walk-forward HMM engine — inputs the PIT feature matrix; outputs filtered probabilities, confidence, expected dwell. Component G: consumes filtered probabilities as soft context (never smoothed labels); the regime×strategy table is one selection input beside the Q03 bandit. Component H: must refit inside the loop — replaying precomputed full-sample labels fails the leakage test. Component I: version artifacts by (K, emission type, window, cadence, seed) plus the state mapping. Component J: monitor entropy, dwell distribution, transition drift. Component K: watchdogs for state collapse and EM non-convergence, fallback to the previous model. Component L: risk limits stay independent of classification — a mis-detected "calm" regime never lifts exposure caps. Siblings: Q02 stabilizes probabilities into decisions; Q03 uses them as context; Q04 supplies gated features; Gate 1 arbitrates.

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.**

Evidence checklist:
- Does regime-recognition code exist, and which library/model class?
- Are decision-time labels filtered, smoothed, or Viterbi — explicit in code and columns?
- Are parameters refit per fold inside the harness, or fit once outside?
- Are normalization statistics trailing-window or full-sample?
- Deterministic-seed policy and label-matching across refits present?
- Do tests cover probability validity, leakage (truncate-at-t invariance), determinism?
- Does the registry store (K, window, cadence, seed)?
- Are dwell, entropy, transition drift monitored?
- Is any selection logic keyed on regime labels, with what thresholds?
- Are underlying features certified point-in-time (Q09-type checks)?

Classification vocabulary: IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY.

## Recommended improvements

1. **P0 — Causal-only inference contract.** Split outputs into `p_regime_filtered` (decision path) and `p_regime_smoothed`/`regime_viterbi` (dashboard-only); add a leakage test: truncated-at-t outputs must equal full-pipeline outputs at t.
2. **P0 — Walk-forward fitting discipline.** Refit inside every evaluation loop on trailing data ≤ t with trailing-window normalization; no full-sample fits in decision-feeding paths.
3. **P1 — State-count governance.** Select K ∈ {2,3,4} by held-out likelihood/BIC per fold; require median dwell ≥ the measured baseline.
4. **P1 — Label stability.** Canonicalize state names by emission volatility ordering; centroid matching across refits so downstream tables never silently relabel.
5. **P2 — Monitoring and visualization.** Filtered-probability charts, dwell histograms, entropy and transition-drift metrics.

## Dependencies

Upstream: component A (point-in-time ingestion), B (normalization rules), Q04 (gated emission features). Downstream: Q02 (stability layer), Q03 (bandit context), G/H/I/J/K/L as above. External: hmmlearn (optional dependency; `statsmodels` MarkovRegression is an alternative).

## Acceptance criteria

- Leakage test passes: with data truncated at any t, all decision-path outputs equal full-pipeline outputs for t.
- Probability validity: filtered vectors sum to 1 within 1e-6; on refit failure the previous model's output is used and flagged.
- Regime persistence: median realized dwell of the accepted configuration ≥ the baseline measured on the first walk-forward run (no a-priori number).
- Per-regime sample size: every regime×strategy cell used for selection has at least the baseline count from the first walk-forward pass (initial heuristic ≥ 30, recalibrated); below it, pooled behavior.
- Runtime: refit completes within the harness budget measured on the baseline run.

## Risk assessment

Implementation risks: label switching corrupting regime×strategy tables; EM local optima or library-version changes altering states under the same seed; singular covariance; K overfit to one fold. Operational risks: production EM non-convergence; feature drift swapping state roles; data gaps; compute spikes from aggressive refits. Failure modes: crash regimes detected late (HMM lag at boundaries); excessive transitions in choppy markets (Q02's hysteresis, not the HMM, handles this). Regressions: any feature/K/window change shifts every historical label and backtest — version artifacts, rerun evaluation end-to-end.

## Implementation decision

Adopt a causal-filtered Gaussian HMM (start: K=3, diagonal covariance, trailing-window refit) as the candidate architecture for component D, conditional on the local audit, the Q02 stability layer, and component H demonstrating reliable walk-forward evaluation. Do not wire regime-conditioned selection into live choices before H reproduces historical results without leakage — mirroring the plan's warning against complex selection before reliable historical evaluation exists.

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in after local implementation:

- Files changed: <fill in>
- Tests added/run: <fill in>
- Results (leakage test, dwell baseline, walk-forward metrics): <fill in>
- Rollback reference: <fill in>
- Date: <fill in>

## Outstanding questions

- Actual asset universe? Correlation and breadth features depend on it.
- Decision cadence (daily vs intraday)? Dwell thresholds and refit cadence follow it.
- Enough strategy history per regime for Q01-B tables, or rely on Q03 initially?
- Do smoothed/Viterbi outputs currently exist in any decision path (blocked-audit item)?

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q02 Bayesian Regime Detection]]
- [[Q03 Contextual Bandit Strategy Selection]]
- [[Q04 Additional Market Data Sources]]
- [[Gate 1 Market Intelligence]]
- [[Q06 Time Series Validation]]
- [[Q09 Point in Time Features]]
