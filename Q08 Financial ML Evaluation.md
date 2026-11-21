---
type: research-record
ids: [Q08-A, Q08-B]
category: Historical Training
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q08 Financial ML Evaluation

This record establishes the evaluation and ranking framework for the bot: which ML and financial metrics to compute for every strategy, how to keep predictive accuracy and risk-adjusted performance separate, and how to rank strategies whose strengths conflict. Verified position: accuracy-style metrics (precision, recall, F1, log loss, Brier) and PnL-style metrics (Sharpe, Sortino, maximum drawdown, profit factor, expectancy, turnover) answer different questions and must be reported together; Sharpe is a noisy, distribution-sensitive statistic requiring non-IID corrections (Lo 2002) and probability statements (PSR); and ranking under conflicting objectives should be lexicographic — risk constraints first, then a statistically defensible measure, then regime worst-case — rather than a composite that hides trade-offs.

## Question IDs

- **Q08-A** — Selecting the combined metric set, and distinguishing predictive accuracy from risk-adjusted trading performance.
- **Q08-B** — Ranking strategies when one has higher total return but another lower drawdown, more consistency, or better cross-regime performance.

## Original research questions

- **Q08-A**: "Which combination of statistical ML metrics and financial performance metrics should our bot use to evaluate strategies, and how should it distinguish predictive accuracy from actual risk-adjusted trading performance?"
- **Q08-B**: "How should the bot rank strategies when one produces a higher total return but another produces a lower drawdown, more consistent results, or better performance across different market regimes?"

## Research objective

**Q08-A** must establish a standard evaluation record — a fixed schema of ML and financial metrics computed identically for every strategy on untouched data — plus an explicit separation of "does the model predict correctly?" from "does it make risk-adjusted money?". Conflating them fails both ways: a model can be accurate yet unprofitable (imbalance, asymmetric payoffs, costs), and a strategy can be profitable yet statistically indistinguishable from luck. Affects **H**, **G**, **F**, **J**.

**Q08-B** must establish a deterministic, documented ranking policy resolving conflicting objectives without ad-hoc judgment. An autonomous bot re-ranks continuously; an unstable composite silently changes capital allocation and destroys comparability. Affects **G**, **L**, **I**, **D**.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit locally:

- [ ] Which metrics exist in evaluation code (search `sharpe`, `brier`, `drawdown`, `profit_factor`, `expectancy`, `turnover`)?
- [ ] Does evaluation emit a structured record persisted per strategy version by I, or scattered logs?
- [ ] Are transaction costs/slippage modeled in H before metrics are computed?
- [ ] Any statistical correction (search `psr`, `dsr`, `probabilistic_sharpe`, `bootstrap`)? Is Sharpe annualized without autocorrelation awareness?
- [ ] How does G rank today: sort key, composite formula — documented or emergent?
- [ ] Any regime-conditional evaluation (metrics split by D's labels)? Is sklearn calibration used for meta-model probabilities?
- [ ] Do H and J share the same metric functions, pinned to reference values by tests?

## Technical concepts

- **Precision / recall / F1**: precision = share of predicted positives that are truly positive; recall = share of true positives caught; F1 = harmonic mean. In trading, precision ≈ "of trades taken, how many won". [ESTABLISHED]
- **Log loss**: −mean(y·ln p + (1−y)·ln(1−p)); a proper scoring rule minimized by true probabilities.
- **Brier score**: mean squared error of probability forecasts (Brier 1950); 0 perfect, 0.25 = always predicting 0.5 on balanced binary data. [ESTABLISHED]
- **Probability calibration**: predicted probabilities matching empirical frequencies; required before probabilities drive sizing. [ESTABLISHED]
- **Sharpe ratio (SR)**: mean excess return / return std, per period.
- **Probabilistic Sharpe Ratio (PSR)**: probability that true SR exceeds a benchmark, adjusted for skewness, kurtosis, sample length. [ESTABLISHED]
- **Deflated Sharpe Ratio (DSR)**: PSR against the expected maximum SR from luck across N trials (full treatment in [[Q05 Backtest Overfitting]]). [ESTABLISHED]
- **Non-IID Sharpe statistics**: serial correlation changes annualized Sharpe — positive autocorrelation inflates it, negative deflates (Lo 2002). [ESTABLISHED]
- **Sortino ratio**: Sharpe variant dividing by downside deviation only.
- **Maximum drawdown (MDD)**: largest peak-to-trough equity decline; the classic tail-risk metric.
- **Profit factor**: gross wins / gross losses; **expectancy**: mean return per trade; **win rate**: share of winning trades — the payoff metrics accuracy cannot see.
- **Turnover / exposure**: volume relative to equity (cost driver) and share of time in the market (risk realization).
- **Transaction costs**: commissions, spread, slippage — metrics are meaningful only net.
- **Lexicographic ranking**: filter by hard constraints, rank by the first criterion, later criteria break ties. [INTERPRETATION as recommended policy]

## Research findings

### Q08-A findings

- The two metric families measure different constructs: Brier (1950) established proper scoring rules; sklearn's evaluation/calibration docs standardize precision/recall/F1, log loss, `brier_score_loss`, reliability diagrams — these measure the *model*. Sharpe, Sortino, MDD, profit factor, expectancy, turnover measure the *trading system*; AFML's backtest-statistics chapter prescribes reporting them as a bundle, not one headline number. [ESTABLISHED — ch. 14 (not the lead's ch. 11) per the verified Wiley TOC]
- Why accuracy ≠ PnL — three mechanisms: (1) **class imbalance**: with 30% wins, a model that never trades scores 70% accuracy while earning nothing; (2) **asymmetric payoffs**: expectancy = win_rate × avg_win − loss_rate × avg_loss — 40% wins at 3:1 beats 60% wins at 1:2, invisible to accuracy; (3) **calibration for sizing**: meta-labeling sizing consumes probabilities as frequencies — an accurate but uncalibrated model mis-sizes (see [[Q07 Triple Barrier and Meta Labeling]]). [ESTABLISHED mechanisms]
- Sharpe needs corrections before supporting claims: Lo (2002, FAJ 58(4)) derives non-IID standard errors; positive serial correlation inflates annualized Sharpe; Bailey & López de Prado (Journal of Risk 15(2), 2012/2013) extend to non-normal returns with PSR = Φ((SR−SR*)·√(T−1) / √(1−γ₃·SR + (γ₄−1)/4·SR²)) and define the Sharpe Ratio Efficient Frontier. [ESTABLISHED]
- Recommended bundle [INTERPRETATION; every element established]: ML {log loss, Brier, AUC, precision, recall, F1, calibration}; PnL {net Sharpe + PSR (SR* = 0), Sortino, MDD, profit factor, expectancy, win rate, turnover, exposure}; costs {paid, spread}; regime {per-label metrics}; metadata {T, N}.- **Contested**: Sortino/Calmar-style downside metrics are popular but have a thinner statistical literature than the Sharpe family — use descriptively, not as significance gates. [INTERPRETATION]

### Q08-B findings

- Verified starting point: these conflicts are genuine trade-offs — no scalar objective yields a unique optimum when risk profiles differ; Bailey & López de Prado's SEF formalizes risk-adjusted selection under non-normal returns, supporting constraint-first ranking. [ESTABLISHED]
- Recommended lexicographic policy [INTERPRETATION, layers anchored]: (1) **constraints** — MDD cap, minimum T and trade count, turnover ceiling, owned by L; (2) **significance** — PSR ≥ target, DSR ≥ target when many strategies were tried ([[Q05 Backtest Overfitting]]); (3) **performance** — rank by net-of-cost PSR, not raw return; (4) **tie-breakers** — worst-regime Sharpe, then fold dispersion from [[Q06 Time Series Validation]], then drawdown severity.
- Significance of differences: PSR-style comparison or a paired stationary bootstrap (White's Reality Check, verified in Q05); rank flips inside the confidence band are ties — incumbent retained, preventing churn. [INTERPRETATION grounded in established tests]
- **Disagreement documented**: composite scores are common but their weights are arbitrary, hide which constraint failed, and shift under rescaling; lexicographic is transparent but coarser. Resolution: lexicographic decides; composite is reported for human review only. [INTERPRETATION]

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|---|---|---|---|---|---|---|
| 1 | The Sharpe Ratio Efficient Frontier | Bailey, López de Prado (Journal of Risk 15(2)) | 2012 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1821643 | PSR formula (skew/kurtosis); SEF for selection | Benchmark SR* choice matters | YES |
| 2 | The Statistics of Sharpe Ratios | Lo, A.W. (FAJ 58(4):36–52) | Jul/Aug 2002 | https://www.tandfonline.com/doi/abs/10.2469/faj.v58.n4.2453 | Non-IID Sharpe errors; autocorrelation bias | Needs autocorrelation estimates | YES |
| 3 | Verification of Forecasts Expressed in Terms of Probability | Brier, G.W. (Monthly Weather Review, vol. 78) | Jan 1950 | https://journals.ametsoc.org/view/journals/mwre/138/1/2009mwr2945.1.xml (citing article; original in AMS archive) | Brier score as a proper scoring rule | Predates ML usage | YES |
| 4 | Advances in Financial Machine Learning ch. 14 "Backtest Statistics" | López de Prado (Wiley) | Feb 2018 | https://www.wiley.com/en-us/shop/general-finance-investments/advances-in-financial-machine-learning-p-9781119482086 | Metric bundle; pp. 195–207 (lead's ch. 11 corrected) | Book, not paper | YES |
| 5 | Probability calibration / model evaluation docs | scikit-learn | current stable | https://scikit-learn.org/stable/modules/calibration.html | Calibration tooling; `brier_score_loss`; reliability diagrams | API drift; not finance-specific | YES |
| 6 | Backtesting | Harvey, Liu (JPM 42(1):13–28) | Fall 2015 | https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF | Multiple-testing haircuts | Needs trial census (Q05) | YES |

Notes: Source 1's SSRN record confirms the journal citation and PSR claims; source 2 is the peer-reviewed foundation. Source 3 verified through AMS-hosted literature; the original title differs slightly from the lead's wording. Source 4 verified as chapter 14 (not ch. 11) from the Wiley TOC — a documented correction. Established: metric definitions, non-IID and PSR corrections, proper-scoring rules. Experimental claims: PSR/DSR thresholds, lexicographic hierarchy. Interpretation: Sortino/Calmar descriptive; composites for human review only.

## How the technique works

**Evaluation record (Q08-A).** Inputs: net return stream R (T periods) from H under Q06's folds; predictions/probabilities (pᵢ, yᵢ) from Q07; costs; regime labels from D; trial count N from Q05's registry. Steps: (1) ML block on (yᵢ, pᵢ): log loss, Brier, AUC, precision/recall/F1 at the policy threshold, calibration summary; (2) PnL block on R: net SR and PSR = Φ((SR−SR*)·√(T−1) / √(1−γ₃·SR + (γ₄−1)/4·SR²)) with γ₃ skewness, γ₄ kurtosis raw, SR* = 0 or Q05's SR₀; Sortino via downside deviation; MDD from the running equity maximum; profit factor = Σ wins / |Σ losses|; expectancy = mean per-trade return; turnover/exposure from trade logs; (3) Lo's adjustment under serial correlation — SR_T = SR₁·√T / √(1 + 2·Σₖ(1−k/T)·ρₖ) — in practice report an interval; (4) regime block: metrics split by regime label, per-bucket T reported; (5) persist the record. Output: one record per strategy per evaluation.

**Lexicographic ranking (Q08-B).** Steps: (1) filter {MDD ≤ cap, T ≥ T_min, trades ≥ n_min, turnover ≤ cap}; (2) require PSR ≥ p_target (DSR ≥ d_target when N > 1); (3) sort by net PSR descending; (4) tie-break by worst-regime Sharpe, then fold dispersion, then MDD; (5) strategies within the confidence band are tied — incumbent retained. Output: ordered list with layer labels.

Strengths: transparent, auditable, aligned with independent risk controls. Limitations: PSR assumes a representative sample; regime splits shrink buckets; constraints need governance (L owns them). Failure: unlogged N blocks DSR; omitted costs inflate every PnL metric; missing regime labels force whole-period fallback. Cost: O(T) per metric.

## Reference implementation sketch

```python
# PSR + lexicographic ranking. numpy only. Point-in-time safe: inputs are
# realized OOS return streams and stored prediction/label pairs.
import numpy as np
from math import erf, sqrt

def _norm_cdf(x):
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))

def sharpe(r):
    return r.mean() / r.std(ddof=1)

def probabilistic_sharpe(r, sr_bench=0.0):
    """PSR (Bailey & Lopez de Prado 2012): P(true SR > sr_bench)."""
    r = np.asarray(r, float)
    T, mu, sd = len(r), r.mean(), r.std(ddof=1)
    sr = mu / sd
    d = r - mu
    g3 = (d ** 3).mean() / sd ** 3                    # skewness
    g4 = (d ** 4).mean() / sd ** 4                    # kurtosis (raw, not excess)
    denom = sqrt(max(1e-12, 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr ** 2))
    return _norm_cdf((sr - sr_bench) * sqrt(T - 1) / denom), sr

def max_drawdown(r):
    eq = np.cumprod(1.0 + r)
    return float((eq / np.maximum.accumulate(eq) - 1.0).min())

def rank_strategies(records, dd_cap=-0.20, psr_target=0.90):
    """records: dicts with 'returns' (net per-period stream) and optional
    'psr', 'worst_regime_sharpe'. Returns ranked list with layer labels."""
    eligible = []
    for rec in records:
        r = np.asarray(rec['returns'], float)
        psr = rec.get('psr') or probabilistic_sharpe(r)[0]
        mdd = max_drawdown(r)
        if mdd < dd_cap:                    # hard risk constraint (component L)
            rec['layer'] = 'excluded: drawdown'
        elif psr < psr_target:              # statistical significance layer
            rec['layer'] = 'not significant'
        else:
            rec.update(layer='ranked', psr=psr, sharpe=sharpe(r), mdd=mdd)
            eligible.append(rec)
    eligible.sort(key=lambda x: (-x['psr'],
                                 -x.get('worst_regime_sharpe', -9e9),
                                 -x['mdd']))
    return eligible

def brier(y, p):   # Brier 1950; equals sklearn.brier_score_loss
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))
```

## Application to this project

- **H** produces the record for every walk-forward run: ML block from stored predictions/labels, PnL block from simulated net returns, regime block from D's labels.
- **G** implements `rank_strategies` verbatim; layer labels are logged so every rank change is explainable.
- **L** owns constraint values (dd_cap, turnover cap) as independent configuration the selector reads but cannot modify.
- **F** reuses the same metric functions for model selection.
- **J** recomputes the identical record on live (paper) performance; divergence feeds **K** (recalibration, demotion).
- Cross-links: [[Q05 Backtest Overfitting]] supplies N/SR₀ (PSR→DSR); [[Q06 Time Series Validation]] supplies fold structure; [[Q07 Triple Barrier and Meta Labeling]] supplies calibrated probabilities and labels; [[Gate 2 Historical Training]] verifies uniform application.

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Inspect:

- [ ] Metric inventory; unit tests against reference values.
- [ ] Cost modeling in H before metrics are computed.
- [ ] Any PSR/DSR or bootstrap machinery; Sharpe annualized without autocorrelation awareness?
- [ ] Ranking logic in G: sort keys, documentation, change history.
- [ ] Record persistence: schema, storage, linkage to model versions in I.
- [ ] Regime-conditional metrics grouped by D's labels; calibration reporting for meta-model probabilities.
- [ ] Live/backtest metric reuse (shared module vs duplication).

## Recommended improvements

1. **P0 — Standard evaluation record.** Schema (ML/PnL/cost/regime/metadata) plus one shared metrics module used by H, F, G, J; persisted in I's store.
2. **P0 — Net-of-cost PnL.** Metrics computed after costs/slippage; test that zero-cost and full-cost records differ.
3. **P0 — PSR in the record.** `probabilistic_sharpe` attached to every record (plus DSR when N is available); raw Sharpe alone is not decision-grade.
4. **P1 — Lexicographic ranking.** Replace emergent sort keys with the documented hierarchy; log layer labels; constraints owned by L.
5. **P1 — Regime block.** Metrics grouped by D's regime labels; worst-regime Sharpe tie-breaker; per-bucket T reported.
6. **P2 — Difference testing.** Paired bootstrap for near-ties; within-band differences are ties (churn protection).
7. **P2 — Calibration reporting.** Brier + reliability summaries for probabilistic outputs; drift alerts wired to J.

## Dependencies

- Depends on [[Q06 Time Series Validation]] (leak-free fold streams) and [[Q07 Triple Barrier and Meta Labeling]] (labels, probabilities, calibration needs).
- Depends on [[Q05 Backtest Overfitting]] for N and SR₀ (and its bootstrap for difference tests).
- Requires component D (regime labels), H (costs, streams), L (constraint values), I (persistence); consolidated by [[Gate 2 Historical Training]].

## Acceptance criteria

- Every evaluation emits a schema-complete record; a validator rejects records missing any block or metadata (T, N, costs).
- Metric unit tests pin implementations to reference values (Brier equals sklearn's on a fixture; PSR = 0.5 when SR equals the benchmark).
- Ranking deterministic and idempotent; every rank change carries a layer label.
- No promotion without a PSR-bearing record; no record from cost-free returns; constraints read from L's config, selector cannot write them (tests).
- Threshold baseline: one full historical cycle, then set dd_cap from L's risk policy and psr_target to keep the intended candidate count, revisited each cycle.

## Risk assessment

- **Implementation**: kurtosis convention errors (excess vs raw) silently corrupt PSR — the sketch uses raw moments, matching the derivation; MDD on irregular cash flows; turnover definitions drifting between H and J.
- **Operational**: threshold churn causing reallocation noise (tie band mitigates); tiny regime buckets misleading (report bucket T).
- **Failure modes**: missing trial counts break the PSR→DSR chain; regime-label outages force whole-period fallback; uncalibrated probabilities poison the ML block and sizing.
- **Regressions**: J re-implementing H's metrics — guarded by the shared-module requirement and fixture tests.

## Implementation decision

Adopt the standard evaluation record, net-of-cost PnL metrics, PSR/DSR-bearing statistics, and lexicographic ranking with independent risk constraints for G/H/L; composite scores reporting-only. Deferred pending the local audit; reuse correct, tested metric code rather than rewriting.

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in locally after implementation:

- Files changed: (metrics module, record schema, G ranking, L config wiring)
- Tests added: (metric fixtures, PSR properties, idempotent ranking, cost assertions)
- Results: (first full-cycle records: metric ranges, chosen thresholds, ranked candidates)
- Rollback reference: (commit/tag; flag restoring previous ranking)
- Date / owner: (sign-off)

## Outstanding questions

- Exact dd_cap and psr_target — pending the baseline cycle; owned by L.
- PSR-difference vs paired bootstrap for near-tie significance — pick one after implementation experience.
- Regime-bucket weighting with unequal regime frequency.
- Composite scores for human dashboards only.

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q05 Backtest Overfitting]]
- [[Q06 Time Series Validation]]
- [[Q07 Triple Barrier and Meta Labeling]]
- [[Gate 2 Historical Training]]
