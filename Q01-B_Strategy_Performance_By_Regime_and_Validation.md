---
id: Q01-B
raw_question: 2
category: 1 - Market Intelligence
status: PARTIALLY COMPLETE (research done; repo audit and implementation tests pending)
decision: EXPERIMENT IN ISOLATION
updated: 2026-11-20
---
# Q01-B - Learning which strategy works in which regime, and proving it holds on unseen data

## Original research question
How should the bot learn which strategies perform best within each identified market regime, and how can it establish that those relationships remain effective on previously unseen historical data?

## Research objective
Define a procedure that builds a strategy-by-regime performance map and tests whether it generalizes, while controlling selection bias from testing many strategy-regime cells.

## Existing project context
Repo and vault not accessible this session (Steps 2, 6 not done). Depends on Q01-A (causal regimes), Q02 (switching), Q03 (selection policy), Q05/Q06 (overfitting, chronological validation), Q18 (costs).

## Technical concepts
- **Regime-conditional performance**: a strategy's return statistics computed only over bars where a given regime was active.
- **Selection bias**: with S strategies and R regimes there are S x R cells; picking the best cell by in-sample score is optimistic by construction.
- **PBO / CSCV**: Bailey, Borwein, Lopez de Prado, Zhu propose estimating the probability that the in-sample-best choice underperforms out of sample, using combinatorially symmetric cross-validation; they argue that standard hold-out is unreliable for investment backtests.

## Research findings
1. **The reference design** (Wang et al. 2020): backtest six factor models over a training period, decode regimes with the HMM, compute each model's per-regime Sharpe, choose the best model per regime, then run the rotation on a later period. This is the right skeleton; its weaknesses for our purposes: the per-regime table used hindsight regime labels and a single train/test split, and live detection used a different mechanism than the one used to build the table (so the table and the live signal were not guaranteed to describe the same regimes).
2. **PBO/CSCV verified at abstract level**: framework and CSCV implementation exist and are model-free and nonparametric. I did not read the full paper this session; implementation details are to be verified in Q05.
3. **Counting units**: 5-minute bars within a regime episode are strongly autocorrelated, so sample size should be counted in regime *episodes* and evaluated with block bootstrap, not in bars. (Engineering reasoning; not source-verified.)

## Verified sources
| Source | URL | Establishes | Limits |
|---|---|---|---|
| Wang, Lin, Mikhelson, JRFM 13(12):311, 2020 | https://www.mdpi.com/1911-8074/13/12/311 | Regime-conditional strategy rotation design and its single-window result | See above |
| Bailey, Borwein, Lopez de Prado, Zhu, "The Probability of Backtest Overfitting", J. Computational Finance 20(4), 2017, DOI 10.21314/JCF.2016.322 | https://escholarship.org/uc/item/4w1110bb (preprint: https://ssrn.com/abstract=2326253) | PBO framework, CSCV, hold-out unreliable for backtests | Abstract/metadata read, not the full derivation |

## How the technique works (proposed procedure)
    for each walk-forward fold (train window -> purged/embargoed gap -> test window):
        # TRAIN
        regimes_train = filtered regime labels on train window (Q01-A)
        perf[s, r]   = net-of-cost stats of strategy s over bars in regime r  (train only)
        eligible[s,r]= episodes(s,r) and bootstrap-CI criteria satisfied (thresholds from baseline)
        mapping[r]   = argmax_s shrunk(perf[s, r]) over eligible, else fallback strategy
        # TEST (parameters frozen at train end)
        regimes_test = causal filtered labels using train-fit HMM
        returns_test = returns of mapping[regime_t] applied bar by bar, net of costs and switching costs
    aggregate returns_test across folds; compare against baselines

Baselines the regime-conditional rule must beat out of sample: (a) the single best strategy chosen in train, (b) equal-weight over strategies, (c) random mapping, (d) block-permuted regime labels (destroys regime information while preserving label statistics).
Stability check: rank correlation of per-regime strategy rankings between consecutive folds.
Overfitting control: treat each candidate mapping rule / hyperparameter setting as a trial and compute PBO via CSCV over the trial-by-time performance matrix (Q05).

## Application to this project
Gives the strategy-intelligence layer (architecture block G) a testable claim: "regime information adds net, out-of-sample value over the best single strategy". If it cannot show that, the map is not used.

## Existing implementation assessment
NOT ASSESSED (no repository access).

## Recommended improvements (priority order)
1. Build the fold harness and baselines (a)-(d) before any sophisticated mapping.
2. Add stability and PBO reporting.
3. Add shrinkage toward overall performance for sparse cells (design proposal; validate empirically).

## Dependencies
Q01-A causal regimes; Q05, Q06; Q18 cost model; at least a few candidate strategies producing comparable return series.

## Acceptance criteria
- The regime-conditional rule beats baselines (a) and (c)/(d) out of sample, net of costs, with a block-bootstrap confidence interval on the improvement that excludes zero.
- Rank stability across folds and PBO are reported; promotion thresholds are set from the baseline distribution (random-mapping / permuted-label runs), not chosen arbitrarily.
- No component of the test window influences train-window mapping (future-perturbation test).

## Risk assessment
Few regime episodes per cell; regimes drift; multiple comparisons; costs and switching can erase small edges; a single-strategy baseline may simply win (which is a valid result).

## Implementation decision
EXPERIMENT IN ISOLATION.

## Implementation record
None.

## Outstanding questions
Candidate strategy set; episode and CI criteria (to be set from baseline runs); fold geometry (raw question 12).
