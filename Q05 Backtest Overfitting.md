---
type: research-record
ids: [Q05-A, Q05-B]
category: Historical Training
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q05 Backtest Overfitting

When a bot continuously tests strategies, indicators, and parameter combinations against the same history, the best reported result is inflated by chance — backtest overfitting — and ordinary metrics stop being trustworthy. The verified counter-measures are: (1) Combinatorially Symmetric Cross-Validation (CSCV) and its Probability of Backtest Overfitting (PBO), which quantify how often the in-sample winner ranks mediocre out-of-sample; (2) the Deflated Sharpe Ratio (DSR), the probability that true skill is positive after correcting for trial count, trial variance, and non-normal returns; (3) multiple-testing haircuts (Harvey & Liu) and White's Reality Check bootstrap; and (4) holdout discipline — an append-only trials registry, single-use validation periods, and a final locked test set evaluated exactly once per candidate. Together these let the system claim, with quantified confidence, that a selected relationship is reproducible rather than a historical coincidence.

## Question IDs

- **Q05-A** — Measuring and controlling the probability of overfitting during continuous strategy/indicator/parameter search.
- **Q05-B** — Maintaining untouched historical evaluation periods so new strategies are not repeatedly optimized against the same validation data.

## Original research questions

- **Q05-A**: "How can our ML training system measure and control the probability of overfitting when it continuously tests different strategies, indicators, parameters, and combinations of market conditions?"
- **Q05-B**: "How should the bot maintain completely untouched historical evaluation periods so that newly discovered strategies are not repeatedly optimized against the same validation data?"

## Research objective

**Q05-A** must establish a quantitative, automatable estimate of overfitting probability for every batch of trials, plus thresholds that gate promotion. An autonomous searcher is structurally a multiple-hypothesis-testing machine: uncorrected selection systematically prefers lucky configurations. Affects **F** (trials are generated), **G** (rankings corrupted by inflated metrics), **H** (return streams feeding the corrections), **I** (trial-count persistence), **L** (unbiased estimates for sizing).

**Q05-B** must establish partition governance that keeps at least one historical period statistically fresh per strategy family and records which data informed which decisions; validation data lose diagnostic power once they influence design. Affects **H** (partitioning, enforcement), **G** (promotion consumes untouched data only), **I** (registry lineage), and **B** (no future statistics leak into holdouts).

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit locally:

- [ ] Does an append-only trials ledger exist (strategy, parameters, code version, seed, evaluation window per trial)?
- [ ] Which parameter-optimization loops run in F (grid/Optuna/`itertools.product`) and how many trials per run?
- [ ] Is a fixed validation dataset or date range reused by every experiment (hardcoded dates, one shared split)?
- [ ] Any CSCV/PBO/DSR/PSR/Reality-Check/haircut code or imports (search `pbo`, `deflated`, `psr`, `haircut`)?
- [ ] Is a locked test period configured (`holdout_start/end`) and enforced against evaluation code?
- [ ] Does promotion in G use raw in-sample or single-validation metrics today?
- [ ] Does monitoring (J) track how often each historical window has been used for evaluation?

## Technical concepts

- **Backtest overfitting**: fitting one historical sample's quirks; performance that will not persist live. [ESTABLISHED]
- **Selection bias**: reporting only the best of many tried variants inflates results even when each backtest is honest.
- **Multiple hypothesis testing**: N tried strategies raise the chance of spurious winners (5% per test ⇒ ~5 false winners per 100 trials).
- **Researcher degrees of freedom**: implicit choices (features, lookbacks, filters) multiplying effective trials beyond the explicit grid.
- **Data snooping**: reusing one dataset for inference and model choice, contaminating later findings.
- **White's Reality Check**: bootstrap test of whether the best of many rules beats a benchmark after accounting for the whole set tried. [ESTABLISHED]
- **CSCV**: resampling the performance history into S blocks and evaluating every symmetric train/test half-split. [ESTABLISHED]
- **PBO**: fraction of CSCV combinations where the in-sample champion's out-of-sample rank falls below the median; near 0.5+ means selection is worse than guessing. [ESTABLISHED]
- **Sharpe ratio (SR)**: mean excess return divided by return standard deviation.
- **Deflated Sharpe Ratio (DSR)**: probabilistic Sharpe evaluated against the expected maximum SR obtainable by luck across N correlated trials. [ESTABLISHED]
- **Haircut Sharpe**: Harvey–Liu multiple-testing penalty subtracted from an observed SR. [ESTABLISHED]
- **Holdout discipline**: append-only **trials registry** (every trial logged, never deleted); **single-use holdout** (each period informs at most one promotion per family); **final locked test set** (dated segment evaluated once, then retired from tuning).

## Research findings

### Q05-A findings

- CSCV/PBO verified: the (T×N) matrix of per-period returns is cut into S even blocks; every train/test half-combination is enumerated; PBO is the share of combinations where the in-sample best strategy's out-of-sample rank falls below the median. PBO rises with the number of tried configurations and shorter samples; high-PBO strategies tend to degrade after deployment. [ESTABLISHED]
- DSR verified: benchmark SR₀ = √V·[(1−γ)·Φ⁻¹(1−1/N) + γ·Φ⁻¹(1−1/(N·e))] where V is the variance of the N trials' Sharpes and γ ≈ 0.5772; then DSR = Φ((SR̂−SR₀)·√(T−1) / √(1−γ₃·SR̂ + (γ₄−1)/4·SR̂²)) with skewness γ₃, kurtosis γ₄. When many candidates are similar, the best is probably luck. [ESTABLISHED]
- Harvey & Liu ("Backtesting", JPM 2015) scale t-statistic thresholds across N trials (haircut Sharpe, published MATLAB code) and argue even honest single backtests deserve haircuts. White (2000) supplies the econometric ancestor — the Reality Check bootstrap — later refined by Hansen's SPA test (lead; full bibliographic details unverified this session). [ESTABLISHED]
- **Disagreement documented**: Harvey–Liu need an explicit trial census and a significance target; Bailey et al. need the cross-trial variance of Sharpes; practitioners also disagree on counting trials (raw grid entries vs deduplicated effective configurations). Resolution: log both a raw and a deduplicated effective N; use the conservative value in DSR. [INTERPRETATION]
- Limitations: PBO is sensitive to block count S and short samples (original authors recommend S ≥ 16); PBO and DSR measure selection risk, not market risk — a low-PBO strategy can still lose money. [ESTABLISHED]

### Q05-B findings

- Repeated evaluation degrades a period: once it influences design it is no longer out-of-sample. CSCV shows even standard k-fold inflates financial performance through overlap leakage; the purge/embargo machinery belongs to [[Q06 Time Series Validation]] — this record adds the governance layer above it. [ESTABLISHED]
- The registry is the practical enabler: DSR requires N, and N is knowable only if every trial is logged at run time. Harvey & Liu note researchers undercount trials; an autonomous bot can log exhaustively. [ESTABLISHED]
- Single-use policy [INTERPRETATION]: three chronological segments (train/validation/locked test) plus rotation — one validation consumption per family per design generation; after a promotion the locked set is the only clean arbiter, used exactly once; then new untouched data must accumulate before the next locked evaluation.
- No peer-reviewed holdout fraction exists; regime coverage matters more than calendar share — choose splits covering all regime classes (component D), and baseline empirically per timeframe. [INTERPRETATION]

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|---|---|---|---|---|---|---|
| 1 | The Probability of Backtest Overfitting | Bailey, Borwein, López de Prado, Zhu (J. Computational Finance) | Apr 2017 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253 ; PDF https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf | Defines CSCV and PBO; overfitting probability vs trials | Sensitive to S, sample length; SSRN fetch blocked (403) | YES |
| 2 | The Deflated Sharpe Ratio | Bailey, López de Prado (J. Portfolio Management) | Sep 2014 | https://scholar.google.com/citations?user=5JB7RscAAAAJ | DSR formula; expected-max-Sharpe benchmark; skew/kurtosis fix | Needs accurate N and cross-trial variance | YES |
| 3 | Backtesting | Harvey, Liu (JPM 42(1):13–28) | Fall 2015 | https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF | Multiple-testing haircuts; t-stat thresholds; code | Needs explicit trial census | YES |
| 4 | A Reality Check for Data Snooping | White, H. (Econometrica 68(5):1097–1126) | Sep 2000 | https://www.ssc.wisc.edu/~bhansen/718/White2000.pdf | Bootstrap test for superior predictive ability | Computationally heavy; lower power than SPA | YES |
| 5 | Advances in Financial Machine Learning (TOC) | López de Prado, M. (Wiley) | Feb 2018 | https://www.wiley.com/en-us/shop/general-finance-investments/advances-in-financial-machine-learning-p-9781119482086 | Backtest-statistics authority; ch. 14 pp. 195–207 | Book, not peer-reviewed paper | YES |

Notes: Source 1 was located via four independent results (SSRN listing, author's own PDF, a university repository, secondary summaries); SSRN itself blocked the automated fetch, so the abstract rests on that corroboration. Source 2 was confirmed through the author's Google Scholar profile and independent citations; source 3 directly at the Duke-hosted PDF. Hansen (2005) "A Test for Superior Predictive Ability" is a **lead — Verified: NO** (title/author/year confirmed in search, journal details not). Established: PBO mechanics, DSR formula, haircut logic, Reality Check. The holdout rotation is engineering interpretation built on these peer-reviewed foundations.

## How the technique works

**CSCV/PBO.** Inputs: `perf` matrix (T periods × N tried configurations, per-period returns) and S (≥16 recommended). Steps: (1) cut T rows into S contiguous blocks; (2) enumerate all C(S, S/2) combinations — each combination is the in-sample half, its complement the out-of-sample half (combinatorially symmetric); (3) find the in-sample Sharpe winner n*; (4) compute n*'s out-of-sample relative rank λ = (rank−1)/(N−1); (5) count a degradation event when λ ≤ 0.5; (6) PBO = events / C(S, S/2). Outputs: PBO ∈ [0,1] and the OOS rank-frequency distribution. Failure conditions: unlogged trials (wrong N), insufficient history for S blocks.

**DSR.** Inputs: best SR̂, T, γ₃, γ₄, N, V. Compute SR₀ as above, then DSR = Φ((SR̂−SR₀)·√(T−1) / √(1−γ₃·SR̂ + (γ₄−1)/4·SR̂²)); output is the confidence that the champion's true Sharpe exceeds what luck among N trials would deliver. Failure: zero cross-trial variance degenerates SR₀; registry gaps corrupt N.

**Control policy** [INTERPRETATION with established components]: promote only if PBO ≤ threshold (baseline first), DSR ≥ 0.90 (initial experimental value), and the untouched holdout was cleared once. Cost: O(C(S,S/2)·N) Sharpe evaluations — trivial.

## Reference implementation sketch

```python
# CSCV Probability of Backtest Overfitting (Bailey et al. 2017). numpy only.
# Point-in-time safe: inputs are realized per-period return streams of
# already-trained configurations, produced chronologically (see Q06); this
# function fits nothing, so it cannot look ahead.
import numpy as np
from itertools import combinations

def _sharpe(r):                      # r: (periods, strategies)
    sd = r.std(axis=0, ddof=1)
    sd[sd == 0] = np.nan
    return r.mean(axis=0) / sd

def _rank_avg(a):                    # average ranks 1..n, no scipy needed
    order = np.argsort(np.nan_to_num(a, nan=np.nanmin(a) - 1))
    ranks = np.empty(len(a), float)
    ranks[order] = np.arange(1, len(a) + 1)
    return ranks

def blocks_of(T, S):
    e = np.linspace(0, T, S + 1).astype(int)
    return [np.arange(e[i], e[i + 1]) for i in range(S)]

def probability_of_backtest_overfitting(perf, S=16):
    """PBO = fraction of CSCV combos where the in-sample best strategy's
    out-of-sample relative rank is below the median."""
    T = perf.shape[0]
    blocks = blocks_of(T, S)
    degraded = combos = 0
    for train_blocks in combinations(range(S), S // 2):
        te = [b for b in range(S) if b not in train_blocks]
        tr = np.concatenate([blocks[b] for b in train_blocks])
        te = np.concatenate([blocks[b] for b in te])
        sr_is = _sharpe(perf[tr])
        if np.isnan(sr_is).all():
            continue
        winner = int(np.nanargmax(sr_is))
        sr_oos = _sharpe(perf[te])
        ranks = _rank_avg(sr_oos)
        degraded += (ranks[winner] - 1) / (len(ranks) - 1) <= 0.5
        combos += 1
    return degraded / max(combos, 1)
```

## Application to this project

- **F**: every trial writes a registry record (config hash, code version, data snapshot, seed, per-period stream) at trial time; the streams are CSCV's input matrix.
- **G**: promotion gates call the PBO function over the candidate family's streams and DSR for the champion; failed strategies never reach live trading.
- **H**: owns the three-segment chronology of Q05-B and refuses evaluation against segments marked spent.
- **I**: stores lineage so N can be recomputed and audits stay possible.
- **J/K**: alert on registry write failures (a silent gap corrupts all corrections) and on live performance falling outside the backtest distribution.
- **L**: sizes positions from DSR-deflated, not raw, Sharpe estimates.
- Siblings: [[Q06 Time Series Validation]] produces honest streams; [[Q07 Triple Barrier and Meta Labeling]] defines labels; [[Q08 Financial ML Evaluation]] consumes DSR/PSR; [[Gate 2 Historical Training]] consolidates.

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Inspect:

- [ ] Trials registry existence, field completeness, append-only enforcement.
- [ ] Any CSCV/PBO implementation, and whether it is tested against a synthetic case with known PBO.
- [ ] Any DSR/PSR code, and whether N comes from the registry rather than a constant.
- [ ] Whether evaluation code can read/write the locked test segment; any guard.
- [ ] Whether promotion (G) consults any overfitting statistic today.
- [ ] Whether per-period return streams are persisted per trial (CSCV needs them) or only summary metrics.
- [ ] Evidence of holdout reuse: the same validation date range recurring across experiment logs.

## Recommended improvements

1. **P0 — Trials registry.** Append-only store written at trial time; no selection code runs without it.
2. **P0 — CSCV/PBO gate.** Implement the snippet in G; require PBO ≤ threshold (baseline first) before any family is promoted.
3. **P0 — DSR thresholds.** Compute SR₀ from registry-derived N and Sharpe variance; require DSR ≥ 0.90 until re-baselined after ~3 months of registry data.
4. **P1 — Holdout governance.** Enforce the three-segment chronology with spent-segment flags and a CI test that evaluation against a spent segment raises.
5. **P1 — Effective trial counting.** Deduplicate near-identical configurations; log raw and effective N; use the conservative value.
6. **P2 — Reality Check cross-check.** Add a White bootstrap or Harvey–Liu haircut when PBO and DSR disagree materially.

## Dependencies

- Requires [[Q06 Time Series Validation]]: streams must come from purged chronological evaluation or PBO/DSR inherit leakage bias.
- Requires [[Q07 Triple Barrier and Meta Labeling]]: labels define what a trial's return stream means.
- Consumed by [[Q08 Financial ML Evaluation]]: DSR feeds ranking; PSR machinery is shared.
- Registry design touches components I and L; consolidated by [[Gate 2 Historical Training]].

## Acceptance criteria

- Every executed trial yields a registry row with config hash, code version, seed, and per-period stream coverage ≥ 90% (baseline measured before the final target is fixed).
- PBO computable for any family within the experiment pipeline's runtime budget (benchmark on a 16-block, 100-strategy matrix; set the budget from the first run).
- DSR reported beside every candidate's raw Sharpe; raw-Sharpe-only promotion structurally impossible (CI test).
- A test asserts evaluation against a spent segment raises; zero violations in log audits.
- Threshold baseline: run one full historical cycle with the registry in place, measure PBO/DSR distributions, set promotion thresholds from that distribution (defaults 0.5 / 0.90 until it exists).

## Risk assessment

- **Implementation**: wrong N or V silently corrupts DSR; S too large for available history makes PBO noisy; registry write failures create invisible trials.
- **Operational**: over-conservative gates stall discovery; registry growth needs housekeeping; PBO cost grows with N.
- **Failure modes**: silent fallback to raw Sharpe on missing stats deps; a renamed family evading the one-evaluation rule (use canonical family keys).
- **Regressions**: result caching reusing spent segments — guard with integration tests after pipeline changes.

## Implementation decision

Adopt the trials registry, CSCV/PBO gating, DSR thresholds, and three-segment holdout governance as the target design for F/G/H/I, deferred pending the local audit; extend existing capability where found. White/Harvey–Liu machinery is a secondary cross-check only (P2).

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in locally after implementation:

- Files changed: (paths + purpose)
- Tests added: (IDs and assertions)
- Results: (first-run PBO/DSR values, thresholds set, registry coverage %)
- Rollback reference: (commit/tag or feature flag)
- Date / owner: (sign-off)

## Outstanding questions

- How to define "effectively independent" trials for DSR's N when grid entries are highly correlated?
- Compute PBO per family or per experiment batch?
- Registry retention policy balancing auditability and storage?
- Does the locked test set need a regime-diversity check before consumption (component D interaction)?

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q06 Time Series Validation]]
- [[Q07 Triple Barrier and Meta Labeling]]
- [[Q08 Financial ML Evaluation]]
- [[Gate 2 Historical Training]]
