---
type: research-record
ids: [Q02-A, Q02-B]
category: Market Regimes
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q02 Bayesian Regime Detection

This record establishes how the bot distinguishes genuine regime changes from temporary fluctuations and acts on regime probabilities without thrashing. Regime inference should be Bayesian posteriors computed causally (Hamilton filter; Gibbs variants); decision rules are a separate layer with calibrated thresholds, hysteresis, minimum persistence, and switching-cost awareness. BOCPD adds an exact online posterior over how long the current regime has run. Uncertainty should modulate selection (fractional allocation, abstain zones) rather than force hard switches. Feeds component D and the decision layer before G, pending the local audit.

## Question IDs

- Q02-A — Distinguishing genuine regime changes from temporary fluctuations using filtered probabilities, confidence thresholds, and causality-safe techniques.
- Q02-B — Handling uncertain conditions and preventing excessive strategy switching when signals are inconsistent or fast-moving.

## Original research questions

- Q02-A: "How can our bot distinguish genuine market regime changes from temporary price fluctuations, and should it use filtered probabilities, confidence thresholds, or other techniques to avoid accidentally using future information?"
- Q02-B: "How should the ML system handle uncertain market conditions and prevent excessive switching between strategies when market signals are inconsistent or rapidly changing?"

## Research objective

**Q02-A** must establish what "genuine regime change" means operationally (a posterior-level event, not an indicator tripwire), which probability objects are causal, and how thresholds are calibrated so delay and false-switch rate are measured, not guessed. Affects components B, C, D, H, I.

**Q02-B** must establish how noisy posteriors become stable decisions, how churn is bounded, and how uncertainty propagates to selection — fractional exposure, abstention, or damped adjustment. Affects components D, G, H, J, L.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Check locally before implementation planning.

- [ ] Code producing regime probabilities (`predict_proba`, MarkovRegression, changepoint detectors) — which object is stored/used?
- [ ] Threshold logic on probabilities (`> 0.5`, `argmax`, `threshold`) in regime/selection modules; configurable?
- [ ] Hysteresis/debounce/dwell logic (state machines, consecutive-period counters).
- [ ] Strategy-switch path: does evaluation accounting model switch cost (fees, slippage)?
- [ ] Historical regime-label columns: generated causally (see Q01 audit)?
- [ ] Monitoring of switch counts, flip-flop rates, posterior entropy?
- [ ] Tests asserting stable periods produce zero switches?
- [ ] Configuration surface for thresholds/persistence parameters (versioned?).
- [ ] Existing changepoint dependencies (`ruptures`, CUSUM, `bayesian_changepoint`).
- [ ] Harness replay of candidate decision rules over historical probability series without leakage.

## Technical concepts

- **Bayesian inference:** updating beliefs by multiplying a prior by a likelihood; the output is a distribution.
- **Posterior probabilities:** `P(z_t | o_1:t)` — belief in each regime given data so far; the causal object from the Hamilton filter.
- **Probabilistic regime classification:** labels as posterior draws (or argmax with confidence), never certainties.
- **Uncertainty estimation:** how split the posterior is — filtered entropy, top-two margin, Gibbs intervals.
- **Regime transition confidence:** posterior mass assigned to a candidate new regime at t; the switch trigger.
- **Changepoint probability:** posterior probability that a distribution change occurred at t (BOCPD).
- **Hazard function:** in BOCPD, prior probability `H(r)` that a run ends at length r; encodes regime persistence.
- **False regime changes:** false-positive switches later revealed as noise; measurable against retrospective labels.
- **Decision thresholds:** posterior levels (act when `P ≥ θ`) calibrated so precision/recall meet targets.
- **Hysteresis:** two-threshold state machine (Schmitt trigger): enter above a high threshold, leave below a lower one.
- **Minimum persistence:** a switch is valid only after the condition holds k periods.
- **Switching costs:** explicit cost of changing strategy (fees, slippage, re-learning); decide net of it.
- **Abstain zone:** band where the posterior is too uninformative to act; hold allocation.
- **Fractional allocation / damping:** expose per posterior mass; move part-way toward targets per period.
- **Downstream effect of uncertainty:** classifier noise becomes churn unless converted into softer actions.

## Research findings

### Q02-A findings

- Bayesian regime inference is established: Albert and Chib (1993) give Gibbs-sampling inference for AR series with Markov mean/variance shifts [ESTABLISHED]; Kim and Nelson (1999) extend it to state-space models and codify filtered/smoothed discipline [ESTABLISHED]; Hamilton (1989) supplies the online filter [ESTABLISHED].
- Citation correction (lead disagreement): the lead cited "Albert & Chib 1993, Bayesian Analysis of K-Parameter Markov Switching Models, JASA". No such JASA title was verifiable; the verified paper is "Bayes Inference via Gibbs Sampling of Autoregressive Time Series Subject to Markov Mean and Variance Shifts", Journal of Business & Economic Statistics 11(1):1–15, 1993 [CONTESTED] lead metadata — resolved to the verified citation.
- Filtered probabilities are necessary but insufficient: the filter is causal but reacts to every observation, so a bare 0.5 crossing still whipsaws; discrimination needs threshold level, persistence, an explicit changepoint model [INTERPRETATION on cited filter mechanics].
- BOCPD (Adams & MacKay 2007, arXiv:0710.3742, 19 October 2007) maintains an exact online posterior over run length via message passing, is modular over conjugate models, and yields an explicit changepoint probability [ESTABLISHED as stated in the paper]. Applying it to markets is not settled — it answers "did the distribution change?", not "which named regime?" — so it is a monitoring layer, not a replacement [INTERPRETATION]. Pitfalls: hazard priors must encode plausible durations; heavy tails need a suitable likelihood.
- Thresholds should be calibrated: define "genuine change" retrospectively (long-dwell states or crisis windows), sweep θ, measure delay and false-switch count, pick the knee, validate out-of-sample [INTERPRETATION procedure; measurement objects ESTABLISHED].
- Documented tension: practitioner discussion (Quant SE, 2014) stresses that regime models switch too often or too late live, while papers present filters as sufficient. Resolution: filters are evidence; decision rules are a separate, tested layer [CONTESTED] academic framing vs practitioner experience.

### Q02-B findings

- Hysteresis is the standard control-engineering answer to noisy switching: two thresholds `θ_hi > θ_lo`, enter above `θ_hi`, leave below `θ_lo`. No verified primary financial source for hysteresis-on-posteriors; adopted as engineering judgment on the documented whipsaw concern [INTERPRETATION].
- Minimum persistence (k consecutive periods) composes with hysteresis: one removes boundary chatter, the other single-observation spikes. Both calibrated by the Q02-A loop [INTERPRETATION].
- Switching costs belong in the decision rule: switch only when expected improvement over expected dwell exceeds modeled cost (fees + slippage + evaluation noise) [INTERPRETATION grounded in H's accounting].
- Uncertainty-aware mechanisms: abstain zone (no action when max posterior < θ_lo); fractional allocation per filtered probabilities; partial adjustment of desired changes. Sticky-transition priors (sticky HDP-HMM) reduce chatter but were not verified — lead, Verified: NO [INTERPRETATION].
- Excessive switching corrupts more than fees: interrupted per-strategy samples degrade Q01-B's regime×strategy table and Q03's reward signal. Churn limits are first-class [INTERPRETATION].
- When features disagree (volatility says stress, trend says calm), posterior entropy is the right aggregator: high entropy means genuine discrimination failure — abstain or damp, never force a choice [INTERPRETATION].

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|-------|------------|------|-----|---------------------|-------------|----------|
| 1 | Bayes Inference via Gibbs Sampling of Autoregressive Time Series Subject to Markov Mean and Variance Shifts | J. H. Albert & S. Chib, Journal of Business & Economic Statistics 11(1):1–15 | 1993 | https://www.jstor.org/stable/1391303 | Full-Bayesian (Gibbs) regime inference | Two-state AR framing; not online | YES |
| 2 | Bayesian Online Changepoint Detection | R. P. Adams & D. J. C. MacKay, arXiv:0710.3742 | 2007-10-19 | https://arxiv.org/abs/0710.3742 | Exact online run-length posterior; explicit changepoint probability | Independence within run; hazard prior chosen; no market demo | YES |
| 3 | State-Space Models with Regime Switching | C.-J. Kim & C. R. Nelson, MIT Press | 1999 | https://mitpress.mit.edu/9780262535502/state-space-models-with-regime-switching | Filtered-vs-smoothed discipline; Gibbs inference | Book-level theory | YES |
| 4 | A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle | J. D. Hamilton, Econometrica 57(2):357–384 | 1989-03 | https://www.jstor.org/stable/1912559 | The Hamilton filter producing causal regime probabilities | Reacts to every observation; needs decision layer | YES |
| 5 | Regime-Switching Model for detecting market shifts (practitioner discussion) | Quantitative Finance Stack Exchange | 2014-06-25 | https://quant.stackexchange.com/questions/12793/regime-switching-model-for-detecting-market-shifts | Practitioner concern: over-switching and lag in live use | Community Q&A; anecdotal | YES |

Most important: Adams & MacKay (2007) is the only verified source with an exact online run-length posterior and explicit changepoint probability — the backbone of Q02-A. Albert & Chib (1993) and Kim & Nelson (1999) establish regime inference as a Bayesian posterior problem; Hamilton (1989) supplies the causal filter. The Quant SE thread is the deliberate practitioner counterweight motivating the decision layer.

Established: posterior regime inference; causal filtering; BOCPD recursion. Experimental: BOCPD on financial data; sticky-transition extensions (lead, Verified: NO). Interpretation: calibration, hysteresis/persistence mechanics, switching-cost rules, abstain zones, fractional allocation, entropy abstention.

## How the technique works

Bayesian regime posterior. The Hamilton filter yields `p_t(j) = P(z_t = j | o_1:t)` via `α_t(j) = b_j(o_t) Σ_i α_{t-1}(i) a_ij` (normalized); switch decisions compare the candidate's posterior mass to thresholds. Uncertainty: entropy `H_t = −Σ_j p_t(j) log p_t(j)`, top-two margin.

BOCPD. Track posterior `R_t(r)` over run length r. Growth probability `(1 − H(r_prev)) · R_{t-1}(r_prev) · π(x_t | r_prev)` extends the run; changepoint probability `Σ_{r_prev} H(r_prev) · R_{t-1}(r_prev) · π(x_t | r_prev)` starts a new run at r = 0; normalize over r. Output: `R_t(0)` and the run-length distribution; `H(r)` encodes prior regime duration.

Decision layer (Q02-B). Hysteresis state machine: state = new-regime when `p_t ≥ θ_hi` persists k periods; reverts when `p_t ≤ θ_lo` for k periods; otherwise hold. With switch cost c, switch only when expected improvement over expected dwell exceeds c.

Inputs: causal probability series (Q01) or streaming observations (BOCPD); threshold/persistence parameters; switch-cost estimate. Outputs: stable state per date, changepoint probability, uncertainty metrics, switch log. Strengths: separates evidence from decision; all quantities causal; churn bounded. Limitations: overfittable parameters; hysteresis trades delay for stability; BOCPD assumes i.i.d. within a run; persistence delays fast crashes. Computation: O(K) per bar; BOCPD O(t) per step — negligible daily. Failure: thresholds tuned on one period reused in another; miscalibration after feature drift; hazard priors far from realized durations.

## Reference implementation sketch

```python
import numpy as np
import pandas as pd

def regime_decision_layer(p: pd.Series, theta_hi=0.70, theta_lo=0.40,
                          min_persist=3, switch_cost=0.0) -> pd.DataFrame:
    """Hysteresis + minimum persistence on a causal regime-probability series.
    p[t] must be P(candidate regime | data up to t) — filtered only.
    Point-in-time safe: state at t depends strictly on p[<= t]."""
    state, persist, cost_paid = 0, 0, 0.0
    switches = []
    out = pd.DataFrame(index=p.index,
                       columns=["state", "switch", "entropy", "abstain"], dtype=float)
    for t, prob in p.items():
        if not state:                                   # currently OUT of regime
            persist = persist + 1 if prob >= theta_hi else 0
            if persist >= min_persist:
                state, persist, cost_paid = 1, 0, cost_paid + switch_cost
                switches.append(t)
        else:                                           # currently IN regime
            persist = persist + 1 if prob <= theta_lo else 0
            if persist >= min_persist:
                state, persist = 0, 0
                switches.append(t)
        probs = np.array([1.0 - prob, prob])            # 2-state entropy proxy
        out.loc[t] = [state, 0.0,
                      float(-(probs * np.log(probs + 1e-12)).sum()),
                      float(theta_lo < prob < theta_hi)]
    for t in switches:
        out.loc[t, "switch"] = 1.0
    print(f"switches={len(switches)}, cost_paid={cost_paid:.4f}, "
          f"abstain_bars={int(out['abstain'].sum())}")
    return out

# Calibration loop (offline): (1) retrospective truth labels (long-dwell HMM
# states / crisis windows); (2) sweep theta_hi [0.5,0.9], theta_lo [0.2,0.6],
# min_persist [1,10]; (3) score delay and false switches on held-out folds;
# (4) pick the knee; re-validate on the next fold. BOCPD: port the recursion
# from Adams & MacKay (2007) or a community package (optional dependency).
```

## Application to this project

Component D: the decision layer consumes Q01's probabilities and emits stable states plus uncertainty metrics; BOCPD is a parallel monitor, not a second switch. Component G: selection receives hysteresis-stabilized states, fractional weights, or abstention — mode is configuration, versioned in I. Component H: every rule variant (θ_hi, θ_lo, k, switch_cost) is evaluated walk-forward, reporting churn, delay, and net performance vs the raw classifier. Component J: log switch counts, flip-flop rates, entropy, threshold breaches; alert when switching exceeds baseline. Component L: risk limits can force de-risking regardless of regime state; the regime layer never overrides them. Siblings: Q01 supplies probabilities; Q03 needs stable context (thrashing makes bandit rewards unlearnable); Q04 features enter only via its gate; Gate 1 records the flow.

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.**

Evidence checklist:
- Do thresholds on regime probabilities exist — calibrated or hardcoded?
- Any hysteresis/debounce/persistence logic around state changes?
- Is switching cost modeled in the evaluation accounting, and where?
- Is posterior entropy (or any uncertainty proxy) computed and stored?
- Are switch counts/flip-flop rates monitored or alerted?
- Do tests pin zero switches on stable periods?
- Is any changepoint detector already a dependency?
- Can the harness replay decision rules on historical probability series without leakage?
- Is there a versioned config surface for θ_hi/θ_lo/k/switch_cost?
- Does any code switch on single-bar crossings (the pattern this replaces)?

Classification vocabulary: IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY.

## Recommended improvements

1. **P0 — Separate evidence from decision.** Only the hysteresis/persistence layer produces executable states; no strategy code reads raw probabilities for switching.
2. **P0 — Calibrate, don't guess.** Threshold sweep against retrospective truth on walk-forward folds; store delay/false-switch curves in I.
3. **P1 — Switching-cost-aware decisions.** Include modeled switch cost in the rule; report net-of-churn performance everywhere.
4. **P1 — Abstain and damp.** Abstain zone plus partial-adjustment damping: uncertain periods produce reduced, not thrashing, actions.
5. **P2 — BOCPD monitor; sticky-transition research.** BOCPD behind a flag; sticky priors as a classifier-side complement (lead, unverified).

## Dependencies

Upstream: Q01 (causal probabilities), B/H (retrospective truth and replay), A (availability timestamps). Downstream: Q03 (stable context), G (selection modes), J (churn monitoring). External: none beyond numpy/pandas; optional BOCPD flagged in the sketch.

## Acceptance criteria

- Causality test: layer output at t unchanged when any data after t is deleted.
- Stability test: zero switches on a synthetic stationary series under calibrated defaults.
- Calibration artifact: delay and false-switch curves over the grid on ≥ 3 walk-forward folds; chosen parameters at the knee.
- Churn bound: realized switch frequency ≤ the calibrated baseline (first calibration run; no a-priori number).
- Cost accounting: every evaluation reports net performance including modeled switch cost, gross reported separately.

## Risk assessment

Implementation risks: threshold grid overfit to one period; entropy proxy misdefined beyond two states; persistence counters mis-resetting on refits; Q01 label mismatch corrupting the probability series. Operational risks: detection delay in fast crashes — mitigated by L acting within one bar; stale thresholds after miscalibration. Failure modes: flip-flop inside the abstain band (bounded by persistence on both edges); chronic HMM/BOCPD disagreement (rule: HMM decides, BOCPD alerts). Regressions: threshold changes shift every downstream backtest — version parameters, rerun evaluations fully.

## Implementation decision

Adopt a Bayesian decision layer on Q01's filtered probabilities: calibrated thresholds, hysteresis, minimum persistence, switching-cost awareness, abstain zones, damped allocation. BOCPD is a monitoring module behind a feature flag. Implementation is contingent on the local audit and H's replay; no switch logic reaches live selection before calibration artifacts exist.

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in after local implementation:

- Files changed: <fill in>
- Tests added/run: <fill in>
- Results (calibration curves, churn baseline, delay/false-switch metrics): <fill in>
- Rollback reference: <fill in>
- Date: <fill in>

## Outstanding questions

- Which retrospective "genuine change" definition is the calibration standard (long-dwell states vs crisis windows vs drawdowns)?
- What is the true per-switch cost (fees + slippage + operational risk) for the project's assets?
- Should abstention zero exposure or hold previous allocation? Needs a policy decision with risk sign-off.
- Can the risk layer act faster than the regime layer when they disagree?

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q01 HMM Market Regimes]]
- [[Q03 Contextual Bandit Strategy Selection]]
- [[Q04 Additional Market Data Sources]]
- [[Gate 1 Market Intelligence]]
- [[Q06 Time Series Validation]]
- [[Q09 Point in Time Features]]
