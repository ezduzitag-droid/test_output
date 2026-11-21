---
type: research-record
ids: [Q06-A, Q06-B]
category: Historical Training
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q06 Time Series Validation

This record establishes the chronological validation architecture for the bot: train on the past, evaluate only on the future, never the reverse. Financial data are serially dependent, so standard k-fold cross-validation lets the model peek at information that occurred after its training events, producing optimistic scores that evaporate live. The verified toolkit: walk-forward (rolling-origin) evaluation since Tashman 2000; scikit-learn's `TimeSeriesSplit` with its `gap` parameter; and López de Prado's purged K-fold CV with embargo for overlapping financial labels. For Q06-B, no universal window lengths exist: sizes and gaps must be derived from the trading timeframe, the label horizon, usable sample count, and regime rotation speed. Affects components F and H, and the honesty of everything downstream.

## Question IDs

- **Q06-A** — Implementing rolling historical training and forward-testing windows so each model is evaluated against market information that occurred strictly after its training period.
- **Q06-B** — Determining training-window lengths, test-window lengths, and time gaps from trading timeframe, prediction horizon, and regime-change speed.

## Original research questions

- **Q06-A**: "How should our bot implement rolling historical training and forward-testing windows so that each model is evaluated against market information that occurred after its training period?"
- **Q06-B**: "How should the bot determine appropriate training-window lengths, test-window lengths, and time gaps based on the trading timeframe, prediction horizon, and speed at which market conditions change?"

## Research objective

**Q06-A** must establish one validation primitive used everywhere: a splitter guaranteeing train indices precede test indices, removing training samples whose labels overlap the test period (purging), and blocking a margin after the test period (embargo). An optimistic splitter silently invalidates model comparison, promotion gates, and risk sizing. Affects **F** (training loop), **H** (simulation replays walk-forward), **G** (comparable scores), **I** (retraining cadence mirrors fold schedule).

**Q06-B** must establish a derivation methodology instead of magic numbers: sizes and gaps anchored to the label horizon, trading timeframe, data needed to cover several regimes, and the sample count for stable estimation. Too-short windows destabilize models; too-long windows dilute regime shifts; too-small gaps leak overlapping labels. Affects **F**, **C**, **H**, **D**.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Audit locally:

- [ ] Which splitter does F use today (`KFold`, `TimeSeriesSplit`, custom indices, none)? Any `shuffle=True` on time-ordered data?
- [ ] Any hand-rolled rolling/expanding window loops, and do they enforce strict `train_end < test_start`?
- [ ] Are labels window-based (forward returns over h bars)? Any purge/embargo logic (search `purge`, `embargo`, `gap`)?
- [ ] Are features normalized per fold from training data only, or globally (global scaling leaks future statistics into past folds)?
- [ ] Are window lengths/gaps named config parameters (`train_window`, `test_window`, `embargo_bars`) or hard-coded integers?
- [ ] Does walk-forward retraining exist in production (I) or only in backtests?
- [ ] Do tests assert chronological integrity, and is fold metadata logged for reproducibility?

## Technical concepts

- **Time-series cross-validation**: CV respecting temporal order; sklearn's `TimeSeriesSplit` is the expanding-window variant (fold k trains on the first k blocks, tests on block k+1). [ESTABLISHED]
- **Walk-forward validation**: re-estimating at rolling origins and testing over the following period, then rolling forward; Tashman (2000) formalized origins, horizons, re-estimation. [ESTABLISHED]
- **Expanding vs rolling training windows**: expanding uses all history (more data, possibly stale patterns); rolling keeps a fixed recent window (`max_train_size`) that adapts to regime change.
- **Chronological holdout**: a never-touched final segment for one-shot evaluation (governance in [[Q05 Backtest Overfitting]]).
- **Purging**: removing training samples whose label intervals overlap the test interval. [ESTABLISHED]
- **Embargo**: excluding a buffer of training samples immediately after a test span, absorbing residual autocorrelation when later folds train there. [ESTABLISHED]
- **Label overlap leakage**: corruption when training and test labels share calendar time; with h-bar labels, up to h−1 boundary samples are contaminated. [ESTABLISHED]
- **Prediction horizon (h)**: how far ahead the model predicts, in bars; the minimum defensible gap and embargo.
- **Purged K-fold CV**: López de Prado's finance adaptation — random folds kept, train sets purged by label overlap and embargoed after test; for optimization loops, while walk-forward stays the final-evaluation tool. [ESTABLISHED]
- **Uncorrelated-errors condition**: Bergmeir & Benítez's result that plain k-fold is valid for time series only when model errors are uncorrelated. [ESTABLISHED]

## Research findings

### Q06-A findings

- Walk-forward (rolling-origin) evaluation is the forecasting-industry standard: Tashman (2000) documents its design choices (origin spacing, test length, number of origins, re-estimation policy). Every test observation lies strictly after every training observation by construction — the direct implementation of Q06-A. [ESTABLISHED]
- `TimeSeriesSplit` semantics verified from official documentation: train sets are supersets of previous ones (expanding); `max_train_size` implements rolling windows; `test_size` fixes test spans; `gap` (added v0.24) excludes samples at the end of each train set before the test set; samples must be equally spaced. Limitation: `gap` purges only the boundary interval, not label-aware overlaps. [ESTABLISHED]
- AFML ch. 7 ("Cross-Validation in Finance": 7.4 Purged K-Fold CV, 7.4.1 Purging the Training Set, 7.5 Bugs in Sklearn's Cross-Validation) specifies purge/embargo for overlapping financial labels and documents concrete sklearn CV bugs for finance. Purged K-fold suits optimization loops; walk-forward suits final evaluation (it never trains on future data). [ESTABLISHED]
- Bergmeir & Benítez (2012) show by simulation that plain k-fold is not automatically wrong for time series: when model errors are uncorrelated, k-fold can outperform holdout by using more training data per fold. Often misread as "k-fold is fine for time series." [ESTABLISHED]
- **Disagreement documented**: Bergmeir & Benítez's permissive result and López de Prado's strict purge/embargo differ in assumptions, not conclusions — B&B's condition (uncorrelated errors) fails for triple-barrier labels (see [[Q07 Triple Barrier and Meta Labeling]]), which are serially dependent by construction. Resolution: plain k-fold only for diagnostics passing a residual-autocorrelation test (e.g., Ljung–Box); production financial models use purged walk-forward or purged K-fold. [INTERPRETATION grounded in both sources]
- Engineering consequence: one splitter class with purge/embargo parameters, used everywhere, so a single tested code path enforces chronology for both search loops (purged K-fold) and final evaluation (walk-forward). [INTERPRETATION]

### Q06-B findings

- No peer-reviewed source prescribes universal window lengths; Tashman frames origins, test length, and horizon as per-application design choices, and later work (Hansen 2011 — lead, journal details unverified) shows results depend materially on the split. The answer is a derivation procedure, not constants. [ESTABLISHED]
- Derivation procedure [INTERPRETATION, each anchor established]: (1) set gap g = label horizon h, embargo e = max(h, 1% of sample length — AFML's heuristic, then re-baseline); (2) estimate average regime duration d from component D's labels; (3) test window t = min(significance need, d/2), where significance need comes from inverting the √T standard-error scaling of the target metric (Sharpe SE ≈ √((1+SR²/2)/T), AFML ch. 14 statistics); (4) training width w from a learning curve — the smallest width where validation score plateaus; (5) verify w covers ≥ 5 occurrences of each regime class; (6) walk-forward once; if fold scores are unstable, double t before touching w.
- Expanding vs rolling [INTERPRETATION]: rolling suits regime-switching markets (stale regimes contaminate estimates); expanding suits stable relationships and small archives. Default rolling, with an expanding experiment at baseline time to decide empirically.
- Origin spacing: Tashman treats origin intervals as a design choice; for compute-bound ML, spacing equals the retraining cadence owned by component I. [ESTABLISHED anchor, INTERPRETATION for the cadence link]

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|---|---|---|---|---|---|---|
| 1 | TimeSeriesSplit API docs | scikit-learn | current stable | https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html | Exact semantics of `n_splits`, `max_train_size`, `test_size`, `gap` (v0.24+); equal-spacing caveat | Boundary-only gap; not label-aware | YES (fetched) |
| 2 | Advances in Financial Machine Learning ch. 7 | López de Prado (Wiley) | Feb 2018 | https://www.wiley.com/en-us/shop/general-finance-investments/advances-in-financial-machine-learning-p-9781119482086 ; listing https://www.oreilly.com/library/view/advances-in-financial/9781119482086/c07.xhtml | Purged K-fold CV, embargo, sklearn CV bugs for finance | Book; code must be written from spec | YES |
| 3 | On the use of cross-validation for time series predictor evaluation | Bergmeir, Benítez (Information Sciences 191:192–213) | May 2012 | https://www.sciencedirect.com/science/article/abs/pii/S0020025511006773 | When k-fold is valid for time series (uncorrelated errors) | Condition often fails in finance; frequently overgeneralized | YES |
| 4 | Out-of-sample tests of forecasting accuracy: an analysis and review | Tashman, L.J. (Int. J. Forecasting 16(4):437–450) | Oct 2000 | https://www.researchgate.net/publication/223319987_Out-of-sample_tests_of_forecasting_accuracy_An_analysis_and_review | Walk-forward (rolling-origin) design vocabulary and guidelines | Pre-ML era; qualitative guidance | YES |
| 5 | Choice of Sample Split in Out-of-Sample Forecast Evaluation | Hansen, P.R. | 2011 | (lead; journal/volume not confirmed this session) | Split choice materially affects evaluation | Bibliographic details incomplete | NO — lead |

Notes: Source 1 was fetched directly — it is the authority for the sketch's API semantics. Source 2's chapter structure was confirmed from publisher and O'Reilly listings. Source 3 is the peer-reviewed counterweight preventing over-hasty purge-everywhere rules; source 4 grounds walk-forward vocabulary. Established: API semantics, purge/embargo specification, uncorrelated-errors condition, walk-forward structure. The window-derivation procedure is an experimental engineering synthesis explicitly flagged as interpretation.

## How the technique works

**Purged walk-forward splitter.** Inputs: sample count n, folds k, test window t, gap g ≥ h, embargo e, rolling flag with width w. Steps: (1) place k test windows end-to-end at the data's end, each length t; (2) fold i trains on [train_start, test_startᵢ − g), with train_start 0 (expanding) or test_startᵢ − g − w (rolling); (3) remove any training sample whose label interval [t₀, t₀+h) intersects the test window — implied by the gap for contiguous labels, but event-based labels (Q07) need interval intersection; (4) maintain spent intervals [test_startᵢ, test_endᵢ + e) that later folds exclude from training; (5) yield (train, test) pairs. Outputs: folds where no training label overlaps any test label and every test index postdates every train index.

**Why purging is not optional.** A sample labeled at t₀ with h-bar horizon contains information from bars t₀+1…t₀+h; if a test observation falls inside, the training label partially observes the test outcome, inflating CV scores by exactly the market's serial dependence. Gap g = h removes boundary cases; embargo protects folds whose training resumes after a test span.

**Window selection (Q06-B)** runs the six-step derivation above. Computational requirements: training cost × k folds; index arithmetic O(n). Failure conditions: archives shorter than ~ (w + k·(t+e)) cannot support honest walk-forward and must not inform promotion; archive gaps break the equal-spacing assumption (component B must flag them).

## Reference implementation sketch

```python
# Purged walk-forward splitter with label-horizon gap and embargo.
# numpy only. Point-in-time safe by construction: every test index postdates
# every (non-purged) train index, and later folds exclude earlier test spans
# plus the embargo buffer. sklearn's TimeSeriesSplit(gap=...) is the
# production alternative for the contiguous-label case.
import numpy as np

class PurgedWalkForward:
    def __init__(self, n_splits=5, test_size=None, gap=1, embargo=0,
                 rolling_width=None):
        self.k, self.t = n_splits, test_size
        self.g, self.e, self.w = gap, embargo, rolling_width

    def split(self, n):
        t = self.t or n // (self.k + 1)
        spent = []                       # (start, end) unusable-later zones
        for i in range(self.k):
            test_end = n - (self.k - 1 - i) * t
            test_start = test_end - t
            train_end = test_start - self.g           # purge gap >= horizon
            train_start = 0 if self.w is None else max(0, train_end - self.w)
            if train_end - train_start < 1:
                continue
            train = np.arange(train_start, train_end)
            mask = np.ones(len(train), bool)
            for s0, s1 in spent:                      # purge+embargo old tests
                lo, hi = np.searchsorted(train, [s0, s1])
                mask[lo:hi] = False
            yield train[mask], np.arange(test_start, test_end)
            spent.append((test_start, test_end + self.e))

    def get_n_splits(self, n=None):
        return self.k

# for tr, te in PurgedWalkForward(5, gap=h, embargo=e).split(len(X)):
#     model.fit(X[tr], y[tr]); scores.append(model.score(X[te], y[te]))
# Event labels (Q07): replace the gap step by interval-intersection purging.
```

## Application to this project

- **F** consumes `PurgedWalkForward` for all training; hyper-parameter search uses a purged-K-fold extension of the same class.
- **H** replays walk-forward folds to emit the per-period streams consumed by [[Q05 Backtest Overfitting]] (CSCV/PBO) and the metrics of [[Q08 Financial ML Evaluation]]; fold boundaries are persisted for reproducibility.
- **C** must fit scalers/filters inside each fold's training span only — global scaling leaks future statistics into past folds.
- **D** supplies regime-duration statistics for the derivation and receives fold-level regime composition back.
- **I** retrains at the walk-forward origin cadence and records which fold dates trained each model version.
- Siblings: [[Q07 Triple Barrier and Meta Labeling]] defines h and event-interval purging; [[Gate 2 Historical Training]] verifies the chain is chronological end to end.

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.** Inspect:

- [ ] Splitter identity in F; presence of `shuffle=True` on chronological data (automatic fail).
- [ ] Any purge/embargo code (gap, label-horizon-aware removal) and whether unit-tested.
- [ ] Feature-scaling scope: per-fold fitting vs whole-dataset fitting (leak detector).
- [ ] Window/gap config surface: named parameters, defaults satisfying gap ≥ label horizon.
- [ ] Walk-forward in production: retraining cadence vs evaluation fold spacing.
- [ ] Fold metadata persistence enabling reproducible evaluations and Q05's input matrix.
- [ ] Dataset-length guards refusing to train when history is too short for configured windows.

## Recommended improvements

1. **P0 — Single purge/embargo splitter.** Implement `PurgedWalkForward` plus a purged-K-fold variant as the only permitted splitters; CI rule rejecting `shuffle=True` CV on chronological data.
2. **P0 — Gap anchored to label horizon.** Configure gap = h everywhere; interval-intersection purging once event labels (Q07) exist.
3. **P1 — Per-fold feature fitting.** Fit scalers inside folds in C; leakage test training on shuffled targets must yield near-chance scores.
4. **P1 — Window derivation job.** Automate the six-step procedure per timeframe; emit signed recommendations into config before constants freeze.
5. **P1 — Fold metadata persistence.** Log fold boundaries per model version (feeds Q05's CSCV matrix).
6. **P2 — Ljung–Box gate** for any plain-k-fold diagnostic exception, per Bergmeir & Benítez's condition.

## Dependencies

- Requires component B (gap-free bar archive) and component D (regime labels) for derivation.
- Requires [[Q07 Triple Barrier and Meta Labeling]] for h and event-interval purging.
- Feeds [[Q05 Backtest Overfitting]] (streams) and [[Q08 Financial ML Evaluation]] (fold metrics); touches C and I; consolidated by [[Gate 2 Historical Training]].

## Acceptance criteria

- Leakage suite passes: train indices strictly precede test indices; no train label interval intersects any test label interval; a model fit on purely future data scores near chance (leakage canary).
- Config validation asserts gap = label horizon and embargo ≥ 1% of sample length unless re-baselined.
- A signed window-derivation artifact (w, t, g, e) exists per timeframe before any promotion uses those windows; stored by I.
- Fold-level metric dispersion reported with every evaluation (never pooled only); acceptable dispersion baselined on the first full walk-forward run.
- One walk-forward pass completes within the pipeline's runtime SLA (measured, not assumed).

## Risk assessment

- **Implementation**: interval-intersection purging off-by-one errors; rolling width defined in bars vs dates; sklearn version drift (gap exists since v0.24 — pin or vendor).
- **Operational**: training cost × k folds; purge/embargo shrinks effective training data on small archives.
- **Failure modes**: silent leakage via globally fitted preprocessing; archive gaps breaking equal spacing; timezone/session errors shifting fold boundaries.
- **Regressions**: cached normalized datasets re-introducing leakage — guarded by the canary test in CI.

## Implementation decision

Adopt purged walk-forward as the mandatory evaluation primitive and purged K-fold as the search-loop primitive, both from one tested splitter module with gap ≥ label horizon and embargo defaults; window lengths derived per timeframe, not hard-coded. Deferred pending the local audit; extend an existing splitter rather than replace it, then re-run the leakage suite.

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in locally after implementation:

- Files changed: (splitter module, config schema, F/H call sites)
- Tests added: (chronological order, overlap purge, leakage canary, embargo regression)
- Results: (first walk-forward run: folds, per-fold scores, derived w/t/g/e)
- Rollback reference: (commit/tag; fallback splitter flag)
- Date / owner: (sign-off)

## Outstanding questions

- Exact embargo rule per bar frequency (AFML's 1% is a heuristic needing empirical re-baselining).
- Purged K-fold on a coarse grid plus walk-forward only for finalists, to control compute?
- Handling instruments with different session calendars (multi-asset case).
- Whether component J's drift metrics justify adaptive rolling width w.

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q05 Backtest Overfitting]]
- [[Q07 Triple Barrier and Meta Labeling]]
- [[Q08 Financial ML Evaluation]]
- [[Gate 2 Historical Training]]
