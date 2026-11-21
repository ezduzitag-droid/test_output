---
type: research-record
ids: [Q13-A, Q13-B]
category: Concept Drift
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q13 Drift Diagnosis

Drift detection (Q12) says "something changed"; diagnosis says *what*, *where*, and *whether it matters*. Q13-A is the measurement layer: monitoring feature drift (input distributions moving) and prediction drift (the model's output distribution moving) as two independent streams, with statistical tests and thresholds that separate "worth investigating" from noise — two-sample Kolmogorov–Smirnov (KS), Population Stability Index (PSI), Jensen–Shannon distance, and Wasserstein distance. Q13-B is the interpretation layer: a data-quality failure, a benign market shift the model still handles, and genuine concept drift (the input-to-outcome relationship breaking) produce overlapping alarms, so a fixed decision tree — quality checks first, then feature/prediction drift, then the performance combination — must run before any retraining or strategy replacement. A critical documented fact: mainstream drift tooling silently filters nulls and infinities before testing, so it is structurally blind to the most common pipeline failures unless quality checks run as a separate, prior gate.

## Question IDs

- **Q13-A** — primary: independent feature-drift and prediction-drift monitoring; tests and thresholds for "significant enough to investigate".
- **Q13-B** — secondary: benign market change vs genuine concept drift vs data-pipeline failure, before retraining or strategy replacement.

Components affected: B, C, F, G, J, K, L.

## Original research questions

- **Q13-A:** "How should our bot monitor feature drift and prediction drift independently, and which statistical tests or thresholds should determine whether an observed change is significant enough to investigate?"
- **Q13-B:** "How should the bot distinguish between harmless market changes, genuine concept drift, and underlying data-pipeline failures before deciding whether model retraining or strategy replacement is necessary?"

## Research objective

**Q13-A** must establish the drift definitions and why feature and prediction drift are measured independently; the standard two-sample tests, their documented defaults and thresholds; and the traps (p-values collapsing as n grows, binning and scale dependence) that break naive thresholding. This sets the sensitivity of the whole pipeline: too loose misses breakages; too tight investigates noise forever.

**Q13-B** must establish an ordered procedure that first rules out data-quality anomalies (engineering bugs, not market phenomena), then classifies remaining alarms by the joint pattern of feature drift, prediction drift, outcome/target drift, and realized performance — ending in benign shift (log only), concept drift (route to Q12-B), or pipeline failure (route to K for repair, never to retraining). Retraining on corrupted data makes the model worse; replacing a strategy because of a broken feed destroys a working edge.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit checklist:

- [ ] Search for validation code (`validate`, `schema`, `quality`, `expectations`, `pandera`) and whether it runs before drift tooling.
- [ ] Search for drift tests: `ks_2samp`, `psi`, `population_stability`, `jensenshannon`, `wasserstein`, `kl_divergence`.
- [ ] Check dependency manifests for `evidently`, `alibi-detect`, and the scipy version in use.
- [ ] Determine whether feature drift and prediction drift are computed on separate monitored columns or blended into one stream.
- [ ] Locate the reference-window definition (training snapshot vs rolling baseline) and whether it is versioned with the model registry.
- [ ] Check whether drift computations silently drop null/NaN/stale rows (the documented trap below).
- [ ] Look for rolling performance tracking per model/strategy that a diagnosis tree could join with drift flags, plus tests covering each test with synthetic shifts.

## Technical concepts

- **Feature drift (covariate/data drift)**: the distribution P(X) of model inputs changes relative to a reference period; does not by itself prove the learned relationship broke.
- **Prediction drift**: the distribution of model outputs (scores, probabilities, position sizes) changes; a downstream symptom with many causes.
- **Concept drift**: the conditional relationship P(y|X) changes — same inputs, different outcomes (a factor stops predicting or inverts). The feature-vs-concept distinction is exactly the Q13-B arbitration problem.
- **Target drift**: the distribution of realized outcomes y changes, with or without relationship change; needs outcome data.
- **Data-quality anomaly**: nulls, schema violations, unit errors, stale timestamps, feed gaps — an engineering problem that mimics drift; detected by dedicated checks, not distribution tests.
- **Reference vs detection window**: the two samples any two-sample test compares; the reference is ideally the training data, versioned per model; point-in-time safety requires no overlap and no silent re-anchoring.
- **Two-sample KS test**: compares empirical CDFs; statistic = maximum CDF gap; p-value = chance probability of that gap under equal distributions.
- **PSI**: credit-scoring shift index, Σ (aᵢ − eᵢ)·ln(aᵢ/eᵢ) over bins; binning-dependent; interpreted via industry bands.
- **Jensen–Shannon distance**: symmetric, always-finite divergence between discretized distributions; bounded [0, 1] with log base 2.
- **Wasserstein distance (earth mover's distance)**: minimal mass × distance to reshape one distribution into the other; works on raw univariate samples without binning; keeps original units, so needs per-feature normalization.
- **Effect size vs p-value**: p-values shrink toward zero with n regardless of effect size; thresholds must sit on the statistic itself at large n. **False alarms / multiplicity**: N features × M slices inflate alarm rates; dataset-level share rules control it.

## Research findings

### Q13-A findings

1. **Feature and prediction drift are the same computation on different columns — which is why they must be wired separately.** Evidently runs one shared per-column algorithm over "features, prediction, or target" [ESTABLISHED]. A pipeline fault shifts features and predictions together; genuine concept drift can move predictions without features (or vice versa) — only the independent pair gives Q13-B its discriminating information [INTERPRETATION on the documented mechanics].
2. **Test selection by sample size has a documented default.** Evidently: reference ≤1,000 observations — KS for numerical, chi-squared for categorical, z-score proportion for binary, at 0.95 confidence; above 1,000 — Wasserstein for numerical, Jensen–Shannon for categorical/low-cardinality, threshold 0.1 on the distance value; PSI and KL opt-in [ESTABLISHED]. The vendor's published comparison corroborates JS stability at large n and Wasserstein above ~1,000 observations [ESTABLISHED as vendor recommendation].
3. **KS has a documented large-n trap.** scipy's `ks_2samp` uses exact p-values when both samples are under 10,000 observations and warns that "numerical errors may accumulate for large sample sizes" [ESTABLISHED]. P-values shrink toward zero with n regardless of effect size, so at trading-data scale the statistic (max CDF gap) with an effect-size threshold must gate "investigate" [INTERPRETATION on practice].
4. **PSI thresholds are industry convention, not statistics — [CONTESTED].** The 0.1/0.25 bands come from Siddiqi's credit-scorecard practice; a peer-reviewed examination (Taplin et al., *Risks*, 2019) treats PSI as an industry standard while criticizing its properties [ESTABLISHED that the bands are conventions; CONTESTED whether they suit trading features]. PSI is binning-dependent, so binning must be fixed and versioned with the reference window [INTERPRETATION].
5. **JS and Wasserstein are complementary.** JS is bounded, symmetric, finite even for disjoint supports (scipy documents 0 identical, 1.0 disjoint at base 2); Wasserstein works on raw samples without binning and preserves units, but needs per-feature normalization (reference IQR or MAD) [ESTABLISHED properties; INTERPRETATION for the normalization convention].
6. **Thresholds should be two-layered, and multiplicity is real.** Layer 1: documented defaults (p < 0.05 small data; distance > 0.1 large data; PSI bands). Layer 2: per-feature effect-size thresholds calibrated by replaying history (record null distributions over stable periods) — no source can set these for a specific bot [INTERPRETATION]. 100 features at p < 0.05 yield ~5 spurious alarms per run; Evidently's dataset-level rule (flag only if some share of columns drift) is the documented control [ESTABLISHED that such rules exist].

### Q13-B findings

1. **Drift tests are structurally blind to the most common pipeline failures — documented, not opinion.** Evidently filters out empty/infinite values before testing and recommends separate null-share tests [ESTABLISHED]. A broken feed producing NaNs or stale repeated values can pass a drift battery while destroying inputs. The tree must run quality checks first: null share, schema match, timestamp freshness, range sanity [INTERPRETATION on the ESTABLISHED behavior; freshness interacts with [[Q11 Data Freshness and Recovery]]].
2. **The three failure classes differ in what moves** [INTERPRETATION on ESTABLISHED definitions]. *Pipeline failure*: quality gate fails; distributions may look shifted because of dead values; repair (K), never retrain. *Benign market change*: quality clean, feature/prediction drift present, performance within control limits — only P(X) moved; log, propose a regime candidate to D, no retrain. *Genuine concept drift*: quality clean, prediction drift present, performance degraded beyond control limits — P(y|X) moved; route to Q12-B.
3. **The performance-plus-pattern matrix disambiguates residual cases.** Performance degraded with no drift flags points to target drift or exogenous factors (costs, capacity, sizing); prediction drift with performance intact is an early warning — monitor, don't act. Each cell of the (quality, feature-drift, prediction-drift, performance) cube maps to exactly one routing decision [INTERPRETATION].
4. **Confirmation and taxonomy close the loop.** Verdicts leading to retraining or replacement require persistence across a confirmation window and consistency with Q12's alarms [INTERPRETATION]. Gama et al.'s covariate/concept/target-shift taxonomy maps directly: covariate-only → adapt memory; concept shift → adapt model; target shift → re-examine regimes and labeling (component E) [ESTABLISHED taxonomy; INTERPRETATION mapping].
5. **Documented disagreement: vendor defaults vs classical practice.** Evidently's large-data defaults (Wasserstein/JS) diverge from the credit-risk PSI convention. Resolution: PSI for reporting and categorical stability with versioned binning; normalized Wasserstein/JS for automated gating; KS for small-sample checks [INTERPRETATION; the disagreement itself is factual].

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|-------|-----------|------|-----|---------------------|-------------|----------|
| 1 | Data drift — Evidently documentation | Evidently AI | current | https://docs.evidentlyai.com/metrics/explainer_drift | Shared per-column algorithm; defaults by sample size; null/inf filtering; dataset-level rules | Vendor docs; PSI bands not restated | YES (fetched) |
| 2 | Which test is the best? Comparing 5 drift-detection methods | Evidently AI | 2022-06 | https://www.evidentlyai.com/blog/data-drift-detection-large-datasets | JS stability at large n; method-selection reasoning | Vendor benchmark, synthetic data | YES |
| 3 | scipy.stats.ks_2samp — SciPy manual | SciPy project | v1.18 | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ks_2samp.html | KS semantics; exact-below-10k rule; large-sample warning | Docs, not a drift tutorial | YES (fetched) |
| 4 | scipy.spatial.distance.jensenshannon — SciPy manual | SciPy project | current | https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.jensenshannon.html | JS distance properties; base-2 bounds | Requires pre-discretized inputs | YES (fetched) |
| 5 | scipy.stats.wasserstein_distance — SciPy manual | SciPy project | current | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wasserstein_distance.html | Wasserstein-1 on raw samples, no binning | Scale-dependent, no normalization | YES (fetched) |
| 6 | Credit Risk Scorecards | N. Siddiqi | 2006 (Wiley) | (bibliographic; ISBN 978-0-471-75451-2) | Origin convention for PSI and the 0.1/0.25 bands | Book not opened — lead; bands corroborated by #7 and secondary sources | NO |

**Source notes.** Also verified: Taplin, Hunt & Wright, "A New Measure of Population Stability for Model Monitoring," *Risks* 7(2):53, 2019 (https://www.mdpi.com/2227-9091/7/2/53 — peer-reviewed PSI critique), Gama et al. 2014 (https://dl.acm.org/doi/10.1145/2523813 — shift taxonomy), and Müller et al. 2024, "Open-Source Drift Detection Tools in Action" (search-confirmed metadata only). Sources 1, 3–5 are the load-bearing four: defaults, the KS large-n trap, JS/Wasserstein properties, and the null-filtering behavior carrying Q13-B. The PSI bands are [CONTESTED] as conventions. Experimental claims: the Evidently blog comparison (synthetic vendor benchmark). Interpretation: two-layer thresholds, the decision matrix, multiplicity handling, method-choice resolution.

## How the technique works

**Inputs.** Per monitored column (feature, prediction, realized outcome): a reference sample R (training rows, versioned per model) and a detection sample C (recent w observations), quality-gated; per-column metadata and thresholds. **Outputs.** Per column: {test, statistic, verdict, effect size, severity band}; per run: one of {BENIGN_SHIFT, CONCEPT_DRIFT, PIPELINE_FAILURE, TARGET_DRIFT, INSUFFICIENT_DATA} plus an evidence trace.

**Mechanism.** (1) Quality gate: null share, schema, freshness, range — fail → PIPELINE_FAILURE. (2) Test selection: |R| ≤ 1000 → KS; > 1000 → Wasserstein normalized by reference IQR; categorical → JS on fixed support; optional PSI with versioned quantile bins. (3) Verdicts: statistic vs threshold (p-value only as secondary evidence at small n). (4) Join with rolling performance z-score (Q14 metrics). (5) Route per the matrix above; persistence required before any Q12-B action.

**Formulas.** PSI = Σᵢ (aᵢ − eᵢ)·ln(aᵢ/eᵢ); KS statistic D = maxₓ |F̂_R(x) − F̂_C(x)|; JS distance = sqrt(½KL(P‖M) + ½KL(Q‖M)), M = ½(P+Q), log base 2, bounded [0,1]; Wasserstein-1 = ∫|F_R⁻¹(u) − F_C⁻¹(u)|du, reported as W₁/IQR(R).

**Strengths.** Standard, testable, cheap; two independent evidence streams localize problems; quality-first ordering removes the most dangerous failure mode. **Limitations.** Univariate tests miss correlation drift; binning and window choices materially change results; thresholds are conventions or must be calibrated; JS needs fixed category support; Wasserstein needs normalization. **Failure conditions.** Silent reference re-anchoring; overlapping windows (breaks point-in-time safety); new categories breaking JS comparability; multiplicity flooding; a quality gate blind to valid-looking stale data (hence the mandatory freshness check, [[Q11 Data Freshness and Recovery]]).

## Reference implementation sketch

```python
import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon

def psi(expected, actual, bins=10):
    """Population Stability Index; quantile bins fixed by the reference window."""
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    a = np.clip(actual, edges[0], edges[-1])          # open outer bins
    e = np.histogram(expected, edges)[0] / len(expected)
    a = np.histogram(a, edges)[0] / len(a)
    e, a = np.clip(e, 1e-6, None), np.clip(a, 1e-6, None)  # avoid log(0)
    return float(np.sum((a - e) * np.log(a / e)))

def js_distance(expected, actual, bins=20):
    lo = min(expected.min(), actual.min())
    hi = max(expected.max(), actual.max())
    e = np.histogram(expected, bins, (lo, hi))[0].astype(float)
    a = np.histogram(actual, bins, (lo, hi))[0].astype(float)
    return float(jensenshannon(e, a, base=2))         # 0 same .. 1 disjoint

def drift_battery(ref, cur):
    """ref must end strictly before cur begins (point-in-time safe)."""
    ks, p = stats.ks_2samp(ref, cur)
    iqr = stats.iqr(ref)
    w1 = stats.wasserstein_distance(ref, cur)
    return {"ks_stat": float(ks), "ks_p": float(p),
            "psi": psi(ref, cur),                     # 0.1/0.25 bands (convention)
            "js_distance": js_distance(ref, cur),     # >0.1 investigate (default)
            "w1_norm": float(w1 / iqr) if iqr > 0 else float("nan")}

if __name__ == "__main__":
    rng = np.random.default_rng(11)
    ref = rng.normal(0.0, 1.0, 2500)
    for label, cur in [("benign", rng.normal(0.05, 1.0, 2500)),
                       ("drift", rng.normal(0.60, 1.2, 2500))]:
        print(label, drift_battery(ref, cur))
# Routing (Q13-B): quality gate FIRST (tooling like Evidently filters nulls/inf
# before tests -> run null-share/freshness checks separately), then combine
# feature/prediction drift flags with the performance z-score.
```

## Application to this project

**Inputs:** versioned reference windows from F/I, detection windows from the Q14 decision log, quality metadata from B. **Outputs:** per-column drift verdicts; per-run diagnosis class with evidence trace; routing events for Q12-B's router, component K (repair), and component D (regime candidates).

**Components.** A: feed anomalies surface at the quality gate before becoming fake drift. B: hosts the quality checks — this record defines their minimum set. C: owns per-feature batteries and versions binning/edges. D: BENIGN_SHIFT and TARGET_DRIFT verdicts are regime-candidate inputs. E: TARGET_DRIFT triggers label review. F: CONCEPT_DRIFT verdicts are the only sanctioned retraining requests. G: replacement proposals must cite CONCEPT_DRIFT plus per-slice health ([[Q14 Per Component Model Monitoring]]). H: the battery over replayed history produces calibration baselines. J: hosts batteries and schedules. K: PIPELINE_FAILURE routing ends here. L: vetoes automated retrain/replace during live positions. **Siblings:** Q12 alarms, Q13 diagnoses, Q14 logs; adjacent: [[Q11 Data Freshness and Recovery]], [[Q02 Bayesian Regime Detection]], [[Q15 Continuous ML Pipeline]].

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Evidence to inspect locally:

- [ ] Whether a reference-window mechanism exists and is versioned per model (vs a silently re-anchored rolling baseline).
- [ ] Whether KS/PSI/JS/Wasserstein implementations exist and whether thresholds are configurable.
- [ ] Whether feature and prediction drift are computed independently today.
- [ ] Whether a data-quality gate runs before drift tests, covering null share, schema, freshness, range — and whether invalid rows are silently dropped inside any drift computation.
- [ ] Whether performance metrics are joined with drift flags anywhere.
- [ ] Whether dataset-level share rules, multiplicity control, or recorded diagnosis verdicts exist.
- [ ] Vocabulary: IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY.

## Recommended improvements

1. **P0 — Stand up the quality gate before any drift battery:** null share, schema/type, timestamp freshness, range sanity; gate failure routes to K and blocks all drift-based responses.
2. **P0 — Run feature and prediction drift as independent monitored columns** with Evidently-compatible defaults (KS ≤1000 reference obs; normalized Wasserstein/JS >1000; 0.1 distance threshold).
3. **P1 — Calibrate per-feature effect-size thresholds by replay** and store them per feature with the model version.
4. **P1 — Code the diagnosis matrix:** one verdict class with evidence; disallow retrain/replace requests lacking a persisted CONCEPT_DRIFT verdict.
5. **P1 — Multiplicity control:** dataset-level share rule (e.g., ≥20% of a slice's columns) or per-test scaling; log raw and gated verdicts.
6. **P2 — Version PSI binning and reserve PSI for reporting;** add one multivariate proxy (rolling feature-correlation distance).

## Dependencies

- Software: numpy, scipy (`ks_2samp`, `wasserstein_distance`, `iqr`, `jensenshannon`); `evidently` optional (flagged).
- Siblings: [[Q12 ADWIN Concept Drift]], [[Q14 Per Component Model Monitoring]], [[Q11 Data Freshness and Recovery]], [[Q02 Bayesian Regime Detection]], [[Q15 Continuous ML Pipeline]], [[Gate 4 Continuous Learning]].
- Plan components: B hosts the gate; F/I provide reference windows; K routes repairs; L vetoes.

## Acceptance criteria

1. Every monitored column has a documented test, threshold, and reference-window version; a test asserts reference and detection windows never overlap (point-in-time proof).
2. The quality gate catches injected faults (null flood, stale timestamps, unit-shifted values) and routes to PIPELINE_FAILURE before any drift verdict.
3. Unit tests cover every relevant (quality, feature-drift, prediction-drift, performance) combination, each producing the documented verdict.
4. Per-feature replay-derived null distributions are stored; "investigate" thresholds are stated relative to them (baseline first). The sketch output (benign: KS p≈0.16, PSI≈0.005, JS≈0.06; drift: PSI≈0.34, JS≈0.26) is the sanity check.
5. On a stable control period, gated "investigate" verdicts occur at or below the calibrated rate.
6. No retraining/replacement request without a persisted CONCEPT_DRIFT verdict that survived the confirmation window (enforced by test).

## Risk assessment

- **Retraining on corrupted data:** prevented by quality-first ordering; residual risk from valid-looking stale data — mitigated by the freshness check (Q11).
- **Threshold miscalibration:** conventions may misfire on trading features; mitigated by replay calibration and stored null distributions.
- **Multiplicity flooding / benign-shift misclassification:** alert fatigue and retraining churn; mitigated by share rules, requiring performance degradation plus persistence in CONCEPT_DRIFT evidence.
- **Silent reference drift:** automatic re-anchoring hides cumulative change; reference windows are versioned with model versions.
- **Regression risk:** post-incident threshold tightening can mask genuine drift; log every threshold change with its motivating incident.

## Implementation decision

Implement the two-layer design: a mandatory data-quality gate (B), independent feature/prediction drift batteries with documented defaults, a coded diagnosis matrix producing exactly one verdict with an evidence trace, and routing — CONCEPT_DRIFT → Q12-B, PIPELINE_FAILURE → K, benign/target verdicts → D/E as logged information. PSI only for reporting, given the contested bands. Deferred until the local audit classifies existing capability; this note is the design contract. [INTERPRETATION]

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in locally after implementation:

- Files changed: `<fill in — e.g., validation/quality_gate.py, monitoring/drift_battery.py, config/diagnosis.yaml>`
- Tests added/run: `<fill in — quality-gate fault injection, matrix coverage, calibration replay>`
- Results: `<fill in — per-feature null distributions, chosen thresholds, control-period false-alarm counts>`
- Rollback reference: `<fill in — commit/tag or config flag disabling battery and matrix>`
- Date / implementer: `<fill in>`

## Outstanding questions

1. Per-feature thresholds after replay calibration (baselines measured locally first).
2. Whether multivariate/correlation drift checks justify a dedicated detector or are covered by Q12's IC-stream monitoring.
3. Optimal detection-window length per cadence — needs Q14 slice data and replay.
4. How TARGET_DRIFT verdicts should update component E's labeling definitions without corrupting historical labels.

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q12 ADWIN Concept Drift]]
- [[Q14 Per Component Model Monitoring]]
- [[Gate 4 Continuous Learning]]
- [[Q11 Data Freshness and Recovery]]
- [[Q02 Bayesian Regime Detection]]
- [[Q15 Continuous ML Pipeline]]
