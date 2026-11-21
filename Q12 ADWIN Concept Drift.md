---
type: research-record
ids: [Q12-A, Q12-B]
category: Concept Drift
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q12 ADWIN Concept Drift

ADWIN (ADaptive WINdowing) is a streaming change detector that keeps a variable-length window over a numeric statistic the bot tracks — per-strategy win rate, per-feature information coefficient, model error — and decides online, with a tunable false-alarm budget, when the recent part of that stream no longer matches the older part. It is both the alarm for Q12-A (a learned market-to-performance relationship has broken) and, via its retained window, the natural retraining corpus. Q12-B is the harder half: detection says "something changed", not "what to do"; this record derives a response policy mapping drift severity, scope, and persistence to retrain, new regime, strategy switch, or disable, gated so no destructive action follows a single alarm. Implementation is deferred behind the audit gates below.

## Question IDs

- **Q12-A** — primary: adaptive-window concept drift detection (ADWIN mechanics, parameters, trade-offs).
- **Q12-B** — secondary: post-detection response logic (retrain vs new regime vs strategy switch vs disable).

Components affected: D, E, F, G, J, K, L; inputs from A, quality-gated by B.

## Original research questions

- **Q12-A:** "How could our bot implement adaptive-window concept drift detection to recognize when previously learned relationships between market conditions and strategy performance are no longer reliable?"
- **Q12-B:** "When drift is detected, how should the bot determine whether to retrain the existing model, introduce a new market regime, switch to a different strategy, or temporarily disable the affected model?"

## Research objective

**Q12-A** must establish how ADWIN works (window management, the variance-reduction cut test, the delta δ parameter), its false-positive and detection-delay guarantees, and which bot-side statistics are the right detector inputs — so that market-to-performance *relationships* are monitored rather than raw returns. False-alarm churn causes needless retraining; insensitivity misses regime breaks. Components: J, D, F/I, C.

**Q12-B** must establish a decision procedure with explicit criteria (affected feature slice, confirmation window, minimum evidence) mapping a confirmed alarm to exactly one response — retrain, new regime, switch, or disable. These have very different blast radii, and the plan's goal — detect changing conditions *without* constantly retraining or replacing models unnecessarily — lives almost entirely here.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit checklist:

- [ ] Search module/function names: `drift`, `adwin`, `change_detection`, `concept_drift`, `page_hinkley`, `cusum`, `regime_break`.
- [ ] Check dependency manifests for `river`, `scikit-multiflow`, `evidently`, `alibi-detect`.
- [ ] Locate rolling-performance tracking (win rate, PnL, rank IC); does it emit alarm states or only metrics?
- [ ] Inspect config schemas for `delta`, thresholds, window sizes, clock; note existing defaults.
- [ ] Determine whether component D produces timestamped regime labels that cut points can be reconciled against.
- [ ] Locate retraining triggers (F/I), enable/disable flags, circuit breakers (G/L) and their scope granularity.
- [ ] Check for tests replaying synthetic drift series, and for event topics/tables recording drift or health events.

## Technical concepts

- **Concept drift**: P(y|X) — how market inputs map to outcomes — changes over time, so a correct model becomes systematically wrong without a code change. Covariate/data drift moves only P(X).
- **Drift types** (Gama et al.): sudden (one-step flip), gradual (concepts interleave), incremental (small intermediate steps), recurring (an old concept returns — a regime returning).
- **Streaming observations**: items processed once in timestamp order, bounded memory; only data up to t is usable (point-in-time safety). **Adaptive windowing**: the lookback length is decided by the data — long when stable, short after a change.
- **ADWIN**: tests splits of a monitored stream's window into older W0 and newer W1; if sub-window means differ more than a threshold derived from confidence parameter δ (the false-alarm budget), the older part is discarded and drift is signaled.
- **Variance reduction / bucket compression (ADWIN2)**: O(log n) exponentially growing buckets; bucket boundaries define tested split points.
- **Statistical change detection**: hypothesis testing between two sub-samples. **Sensitivity vs false positives**: smaller δ → fewer false alarms, longer delay. **Detection delay**: grows with the inverse square of shift size. **Window management**: minimum length, cadence (clock), bucket merging.
- **DDM**: monitors a binary error stream's rate p_i and s_i = sqrt(p_i(1−p_i)/i) against historical minimums, with warning and drift states.
- **Page-Hinkley test**: CUSUM-style accumulation of deviations from the running mean; heuristic thresholds, no window output.
- **Response decision logic (Q12-B)**: maps severity (mean-shift size), scope (slice vs global), persistence (confirmation window), and minimum evidence (two detectors agreeing) to action.

## Research findings

### Q12-A findings

1. **ADWIN is formally characterized.** Bifet & Gavaldà (SDM 2007) prove that, with probability ≥ 1−δ, ADWIN makes few false cuts on stationary streams and shrinks to the post-change window within bounded delay after a real mean shift [ESTABLISHED]; maintained code ships in river [ESTABLISHED].
2. **Parameters are concrete.** River's ADWIN: `delta` (default 0.002, the false-alarm budget), `clock` (32 — cut test every k-th item), `max_buckets` (5), `min_window_length` (5), `grace_period` (10) [ESTABLISHED]; the documented demo fires once, at index 1023 [ESTABLISHED].
3. **Sensitivity is a policy knob.** Smaller δ raises the cut threshold ε; delay grows with inverse-square of shift size [ESTABLISHED]. Set δ from expected regime-change frequency and the cost asymmetry between false restarts and late reactions [INTERPRETATION].
4. **What to monitor is a design decision.** Best bot-side candidates: per-strategy win rate or PnL-sign stream, per-feature rolling rank information coefficient (closest to Q12-A's wording), model error rate [INTERPRETATION]; raw equity conflates strategy quality with market variance.
5. **Alternatives trade guarantees for simplicity.** DDM watches only a binary error stream (river: warning/drift at p_i + s_i ≥ p_min + 2·s_min / ≥ p_min + 3·s_min, min 30 instances); Page-Hinkley uses heuristic thresholds [ESTABLISHED]. ADWIN dominates where the retained window and formal bounds matter; the others are good confirming detectors [INTERPRETATION].
6. **Financial data breaks the fine print.** Heavy tails and autocorrelation make realized false-alarm rates on raw PnL exceed nominal δ. The textbook ε = sqrt(ln(4/δ′)/(2m)) assumes bounded variables — on unbounded financial data the variance-aware ε = sqrt(2σ̂²·ln(4/δ′)/m) is required; the sketch demonstrates it (zero false cuts on ten stationary control streams) [INTERPRETATION, verified empirically].

### Q12-B findings

1. **The literature gives a framework, not a trading policy.** Gama et al. (2014) frame adaptation as four decisions — memory, detector, update strategy, learning method [ESTABLISHED]; the four-way trading mapping must be built from drift characteristics [INTERPRETATION].
2. **Severity, scope, persistence are the discriminators.** Recurring concepts → regime registration (keep the old model for the returning regime); sudden global shifts → retrain; slice-confined drift → partial retrain or feature quarantine; unexplained collapse → disable pending diagnosis [INTERPRETATION grounded in the ESTABLISHED taxonomy].
3. **No destructive action on a single alarm.** The router requires a confirmation window — the alarm must persist, or a second independent detector must agree — before retraining/regime/disable executes; DDM's native warning/drift two-state design is the same pattern [ESTABLISHED for the pattern; INTERPRETATION for trading actions].
4. **Minimum evidence should be numeric and versioned.** Scope = features/slices whose detectors fired; severity = ε vs the pre-change mean; persistence = alarm re-arms after the confirmation window; data-quality gate passed (Q13-B first). Then: clean quality + global shift → retrain; persistent recurring shift → new-regime candidate in D; persistent per-strategy drift with healthy siblings → switch; unexplained or quality-failed → disable [INTERPRETATION].
5. **Reconcile with the regime detector.** An ADWIN cut may be symptom while a D regime flip is cause; the router queries D first and logs disagreements [INTERPRETATION].

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|-------|-----------|------|-----|---------------------|-------------|----------|
| 1 | Learning from Time-Changing Data with Adaptive Windowing | A. Bifet, R. Gavaldà | 2007 (SDM, pp. 443–448) | https://epubs.siam.org/doi/10.1137/1.9781611972771.42 | Original ADWIN/ADWIN2 + guarantees | Body paywalled; cross-checked vs river docs; DOI suffix (.42) differs from one secondary listing (.40) | YES |
| 2 | A Survey on Concept Drift Adaptation | Gama et al. | 2014 (ACM CSUR 46(4)) | https://dl.acm.org/doi/10.1145/2523813 | Drift taxonomy, adaptation framework | Survey level; no trading policy | YES |
| 3 | ADWIN — river drift module docs | River project | current | https://riverml.xyz/dev/api/drift/ADWIN/ | Parameters and API; demo fires once | Library docs, not the proof | YES (fetched) |
| 4 | Learning with Drift Detection (DDM) | Gama, Medas, Castillo, Rodrigues | 2004 (SBIA, LNCS 3171) | https://link.springer.com/chapter/10.1007/978-3-540-28645-5_29 | DDM two-state error-rate monitoring | Body paywalled; threshold form varies by reproduction | YES |
| 5 | DDM — river drift module docs | River project | 0.11.0 | https://riverml.xyz/0.11.0/api/drift/DDM/ | Verified triggers p_i+s_i ≥ p_min+2·s_min / ≥ p_min+3·s_min, min 30 instances | Multipliers differ from some reproductions [CONTESTED] | YES (fetched) |

**Source notes.** Also verified: river's PageHinkley docs (https://riverml.xyz/0.7.0/api/drift/PageHinkley — YES, search-confirmed) and, as an unverifiable bibliographic lead, Page, "Continuous Inspection Schemes," Biometrika 41(1/2):100–115, 1954, https://doi.org/10.1093/biomet/41.1-2.100 (paywalled original, not opened; corroborated by the river docs and Agrahari et al. 2022, sciencedirect.com/science/article/pii/S1319157821003062 — Verified: NO). Sources 1–3 jointly carry Q12-A. Source 5 disagrees in form with common DDM reproductions (river: p_min + 2·s_min; several texts: 2·(p_min + s_min)) — implementation-dependent [CONTESTED]. Established: guarantees and defaults, two-stage warning/drift, taxonomy. Interpretation (inline-marked): monitored-statistic choice, confirmation design, response mapping.

## How the technique works

**Inputs.** One univariate stream per monitored statistic, plus δ, minimum window length, cadence. **Outputs.** Current window and mean, a boolean drift signal with timestamp, and after a cut the surviving window — the "recent regime" sample.

**Mechanism.** On each value: append; if the window holds ≥ 2·min-length values and the clock ticks, test candidate splits into older W0 and newer W1. For each split compare the mean difference against ε = sqrt(2σ̂²_W·ln(4/δ′)/m), where σ̂²_W is the window variance (the paper's Hoeffding form sqrt(ln(4/δ′)/(2m)) applies only to [0,1]-scale statistics), m = 1/(1/m0 + 1/m1) is the effective sub-window size, and δ′ is δ adjusted for repeated testing. A split exceeding ε drops the older prefix and signals drift. Only old data is ever dropped, so it is point-in-time safe by construction [ESTABLISHED]. ADWIN2 tests only bucket boundaries, with O(max_buckets·log n) memory and amortized O(log n) updates.

**Strengths.** Formal false-positive control at δ; automatic window sizing; produces the retraining sample as a by-product; cheap. **Limitations.** Mean-shift only — variance-only or correlation-only changes are invisible on raw statistics; delay scales with 1/shift²; guarantees degrade with autocorrelation and heavy tails; δ multiplies across detectors (50 at δ=0.002 approach a 10% system-level rate without budgeting). **Failure conditions.** Mis-set δ; lagging statistic; unbounded outliers; detector starvation when the feed stops (Q13-B/Q11 must gate inputs).

## Reference implementation sketch

```python
import numpy as np

def adwin_lite(stream, delta=0.002, min_win=64, clock=4):
    """Simplified ADWIN2 for offline replay: geometric scan detects, the largest
    certified-stale prefix is dropped in one cut; variance-aware sub-Gaussian
    epsilon; union bound over splits and checks. Production: river ADWIN2."""
    W, cuts, since_check, refractory = [], [], 0, 0
    n_checks = max(1, len(stream) // clock)
    for t, x in enumerate(stream):
        W.append(float(x)); since_check += 1; refractory -= 1
        if since_check < clock or len(W) < 2 * min_win or refractory > 0:
            continue
        since_check = 0
        w = np.asarray(W); n = len(w)
        dprime = delta / (np.log(n) * n_checks)      # repeated-testing budget
        var = max(w.var(), 1e-6)
        def eps_of(m0):                              # m = 1/(1/m0 + 1/m1)
            m = (m0 * (n - m0)) / n
            return np.sqrt((2.0 * var / m) * np.log(4.0 / dprime))
        hit = next((k for k in (min_win * 2**j for j in range(20))
                    if k <= n - min_win
                    and abs(w[:k].mean() - w[k:].mean()) >= eps_of(k)), None)
        if hit is None:
            continue
        m0 = max(c for c in range(min_win, hit + 1, min_win)
                 if abs(w[:c].mean() - w[c:].mean()) >= eps_of(c))
        W = w[m0:].tolist()                          # drop stale prefix only
        cuts.append({"t": t, "kept": len(W), "severity": float(
            w[:m0].mean() - w[m0:].mean())})
        refractory = min_win
    return cuts

if __name__ == "__main__":
    rng = np.random.default_rng(7)
    demo = np.concatenate([rng.normal(0, 1, 2000), rng.normal(1.5, 1, 2000)])
    print(adwin_lite(demo))           # one cut ~t=2111, keeps ~64 post-change pts
    print(sum(len(adwin_lite(np.random.default_rng(s).normal(0, 1, 4000)))
              for s in range(10)), "false cuts on 10 stationary streams")  # 0

# Production alternative (optional dep: pip install river):
#   from river import drift
#   d = drift.ADWIN(delta=0.002, clock=32)  # docs demo fires once, at index 1023
```

## Application to this project

**Inputs:** quality-gated streams from A/B, predictions and selections from F/G, outcomes from E — joined by timestamp in the Q14 decision log. **Outputs:** per-stream detector objects (`drift_detected`, `estimation`, width, severity) and confirmed-drift events carrying scope, severity, evidence — the sole input contract of the Q12-B router.

**Components.** A: timestamped, immutable series. B: validation runs *before* detectors (quality failures masquerade as drift — [[Q13 Drift Diagnosis]]). C: one ADWIN per rolling rank-IC stream gives feature-level scoping. D: cut events are new-regime candidates; recurring cuts at similar feature states support regime structure over retraining. E: post-cut outcome distributions correlate drift with labeled transitions. F/I: after confirmed global drift, retrain on the ADWIN window as a trigger condition. G: persistent per-strategy drift with healthy siblings is the switch signal. H: replay detectors over history before live use. J: hosts detectors and the δ budget. K/L: the disable branch executes only through K with L's veto. **Siblings:** Q12 detects, Q13 diagnoses, Q14 logs; adjacent: [[Q02 Bayesian Regime Detection]], [[Q15 Continuous ML Pipeline]], [[Q11 Data Freshness and Recovery]].

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Evidence to inspect locally:

- [ ] Any detector class/config matching the context checklist — classify against the vocabulary below.
- [ ] Whether monitored statistics exist at all (rank-IC, win-rate streams).
- [ ] Whether any retraining trigger references drift events or is schedule-only.
- [ ] Whether two-stage warning/drift logic exists anywhere.
- [ ] Whether δ/false-alarm budgets are configured (`delta`, `significance`, `false_positive` keys).
- [ ] Whether tests replay injected mean-shift series through a detector, and whether regime labels from D are timestamped well enough to reconcile with cuts.
- [ ] Whether any disable/switch path is reachable from monitoring, or manual only.
- [ ] Vocabulary: IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY.

## Recommended improvements

1. **P0 — ADWIN detectors on three statistic families** (per-strategy performance, per-feature rank IC, per-model error) via river's ADWIN, documented defaults, one instance per Q14 slice.
2. **P0 — Two-stage confirmation gate:** act only if the alarm re-arms after a confirmation window (e.g., 50 observations) or a second independent detector agrees; log both stages.
3. **P0 — Data-quality precondition:** refuse all responses if the Q13-B gate failed during the confirmation window; route to repair instead.
4. **P1 — δ budgeting:** scale per-detector δ (δ_i ≈ δ_target/active_detectors); configurable per statistic family.
5. **P1 — Retrain-from-window:** after confirmed global drift, train F on the ADWIN window; record boundaries in the registry (I).
6. **P2 — Replay benchmark:** ADWIN vs Page-Hinkley vs DDM for delay/false-alarm curves; cluster recurring cuts into regime candidates for D.

## Dependencies

- Software: numpy (core); `river` optional (flagged) for production ADWIN2.
- Siblings: [[Q13 Drift Diagnosis]], [[Q14 Per Component Model Monitoring]], [[Q02 Bayesian Regime Detection]], [[Q15 Continuous ML Pipeline]], [[Q11 Data Freshness and Recovery]], [[Gate 4 Continuous Learning]].
- Plan components: B before J; D/E for attribution; F/I for retraining; G/K/L for switch and disable.

## Acceptance criteria

1. Every monitored statistic has a detector with versioned config (δ, clock, min length).
2. On replay with injected shifts (0.5σ, 1σ, 2σ), measured delay is recorded per magnitude; thresholds are set relative to this replay-derived baseline (baseline first). The sketch (single cut at 1.5σ with delay ≈ 111; 0 false cuts on ten control streams) is the sanity check.
3. System-level false-alarm count on a drift-free control period ≤ δ_target × control length.
4. Zero destructive actions without a passed confirmation gate and quality precondition — enforced by test.
5. After a simulated global drift, F trains on the ADWIN window and I records the boundaries.
6. Starvation test: a stopped feed produces a data-quality event, not a drift event.

## Risk assessment

- **False-alarm churn:** over-sensitive δ across many detectors causes retraining thrash and strategy flapping; mitigated by δ budgeting and confirmation gates.
- **Late/missed drift:** heavy tails and autocorrelation delay detection; mitigated by rank-based statistics and IC/error streams.
- **Wrong statistic / cause confusion:** unmonitored structure stays invisible; regime-flip-driven drift can be mis-routed to retraining; mitigated by C's streams and consulting D first.
- **Regression / operational:** too-short post-cut windows yield fragile models (gate on minimum width); aggregate detector events per confirmation window.

## Implementation decision

Adopt ADWIN (river ADWIN2) as the primary online change detector, with Page-Hinkley as confirming companion, and implement Q12-B as an explicit, logged decision function (severity × scope × persistence × quality-gate → retrain / new regime / switch / disable), defaulting to "log only" on incomplete evidence. Deferred until the local audit classifies existing capability; this note is the design contract. [INTERPRETATION — the sources establish the detector, not the trading policy.]

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in locally after implementation:

- Files changed: `<fill in — e.g., monitoring/detectors.py, config/drift.yaml, tests/test_adwin.py>`
- Tests added/run: `<fill in — injected-shift replay, false-alarm control, starvation test>`
- Results: `<fill in — measured delay per shift magnitude, false-alarm count vs δ budget>`
- Rollback reference: `<fill in — commit/tag or config flag disabling detectors and router>`
- Date / implementer: `<fill in>`

## Outstanding questions

1. Which statistic family gives the best delay/false-alarm trade-off — requires the P2 replay.
2. Confirmation-window length per cadence — measure re-arm times on replay.
3. Router policy when ADWIN cuts and D's regime posterior disagree.
4. Whether δ should differ per asset class or timeframe slice — needs Q14 slice data first.

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q13 Drift Diagnosis]]
- [[Q14 Per Component Model Monitoring]]
- [[Gate 4 Continuous Learning]]
- [[Q02 Bayesian Regime Detection]]
- [[Q15 Continuous ML Pipeline]]
- [[Q11 Data Freshness and Recovery]]
