---
id: Q01-A
raw_question: 1
category: 1 - Market Intelligence
status: PARTIALLY COMPLETE (research + prototype verification done; repo audit and implementation tests pending)
decision: IMPLEMENT NOW (causality tests) / EXPERIMENT IN ISOLATION (HMM component)
updated: 2026-11-20
---
# Q01-A - Regime classification without future information

## Original research question
How should our ML bot identify and classify market regimes using historical information such as volatility, momentum, volume, price movement, and correlations, without accidentally using information from the future?

## Research objective
Establish (1) whether an HMM is a sound regime-classification component, (2) exactly where look-ahead enters an HMM pipeline, (3) how to update classifications bar by bar, (4) how to expose uncertainty to downstream logic.

## Existing project context
- Obsidian vault and code repository: NOT ACCESSIBLE in this session. Steps 2 and 6 of the workflow are therefore NOT DONE.
- Known only from prior notes: AI_Trading_Lab works on public 5-minute spot data (ADA, BTC, DOGE, ETH, SOL, XRP vs USDT, Binance.US), public data only, no live trading. Whether it contains any regime code is unknown.

## Technical concepts (plain language)
- **Regime**: a persistent market "mode" (e.g., calm/trending vs. volatile) that changes return/volatility behavior.
- **HMM**: assumes a hidden regime s_t that follows a Markov chain (transition matrix A) and emits observed features x_t from a regime-specific distribution (Gaussian: mean mu_k, covariance S_k). Parameters: lambda = {A, mu, sigma, pi}. Two assumptions: observations depend only on the current state; transitions depend only on the current state (Wang et al. 2020, Sec. 2.2).
- **Filtering** P(s_t | x_1..x_t): uses only the past and present. Causal. The only legitimate quantity for live or backtested decisions.
- **Smoothing** P(s_t | x_1..x_T): also uses observations after t. Fine for descriptive research, leaks future information if used for decisions.
- **Viterbi**: most likely whole state path given all observations (also non-causal).

## Research findings
1. **The standard library call is non-causal at interior points.** hmmlearn documents `viterbi` as the most likely state sequence "given all emissions" and `map` (smoothing / forward-backward) as the individually most likely states "given all emissions". `predict_proba` returns posterior state probabilities (smoothed). Any value at time t from a window extending past t uses future bars.
2. **The causal quantity is available from the same API, with one trick.** The last row of `predict_proba(X[:t+1])` equals the filtered probability at t (the backward message at the final step is 1). Verified numerically (below). hmmlearn does not expose a public forward-only filter, so use the manual recursion below (O(K^2) per bar) rather than recomputing the window each bar.
3. **Parameters are a second leak channel.** Fitting the HMM on the full history and then reading regimes inside that history leaks through mu, S, A. Parameters must be fit only on data available at the refit time.
4. **State identity is unstable across refits (label switching).** The reference paper retrains daily on a sliding window and fixes meaning with a rule (lowest-return regime = bear, highest = bull).
5. **The reference paper is a design lead, not proof.** Wang, Lin, Mikhelson (JRFM 13(12):311, 2020): Gaussian HMM (hmmlearn), 3 states, features = daily return and a volatility proxy, trained on S&P 500 ETF data (Jan 2007 - Sep 2017), tested Sep 2017 - Apr 2020. Limitations I found in the text:
   - Per-regime strategy performance was computed from regimes decoded over the training period (hindsight labels).
   - Live regime detection used a *different* mechanism (KS-fitted distributions, PDF thresholds 0.3 and 0.5, not justified in the text) rather than HMM filtered probabilities.
   - K=3 was chosen using in-sample log-likelihood (Fig. 3), which generally improves as K grows, so it cannot select K on its own.
   - One out-of-sample window (~2.6 years), equities, daily bars; includes leveraged strategies; the text I read does not discuss transaction costs.
   - Its "volatility" is a mean-squared deviation of closing prices around a 10-day moving average, which is price-scale dependent.
   Transfer to 5-minute crypto is untested.

## Verified sources
| Source | Org/Author | Date | URL | Establishes | Limits |
|---|---|---|---|---|---|
| Regime-Switching Factor Investing with Hidden Markov Models | Wang, Lin, Mikhelson; JRFM 13(12), 311 | 5 Dec 2020 | https://www.mdpi.com/1911-8074/13/12/311 (DOI 10.3390/jrfm13120311) | HMM regime-switching design, Gaussian HMM, retraining scheme, results (full text read) | Single OOS window; equities/daily; see item 5 |
| hmmlearn API reference (decode / predict_proba) | hmmlearn project | "latest" docs | https://hmmlearn.readthedocs.io/en/latest/api.html | viterbi and map decoders use all emissions; posteriors via forward-backward | Docs describe behavior; they do not warn about look-ahead |
| Rabiner (1989), Baum-Welch/Viterbi/forward papers | cited by Wang et al. | - | - | NOT independently read; only cited secondhand | - |

## How the technique works
Filtered recursion (fixed parameters), with b_j(x) the emission density of state j:

    alpha_t(j) = b_j(x_t) * sum_i alpha_{t-1}(i) * A[i, j]
    P(s_t = j | x_1..x_t) = alpha_t(j) / sum_k alpha_t(k)

Reference implementation and tests: `Q01_hmm_filter_verification.py` (same folder).

### Prototype verification (synthetic data, hmmlearn 0.3.3, 1 seed, 1 run)
Two well-separated synthetic regimes, T=3000, fit on first 2000 bars, test on the last 1000.
| Check | Result |
|---|---|
| Last row of `predict_proba(X[:t+1])` vs manual filter at 11 test points | max abs diff 1.7e-12 (equivalent) |
| Filtered vs full-sample smoothed argmax disagreement, test region | 1.8% of bars; mean abs probability difference 0.026 |
| Agreement with true regime: filtered vs smoothed | 0.983 vs 0.995 (look-ahead flatters accuracy by ~1.2 points here) |
| Viterbi labels for t<2500 after appending 500 bars | 0% changed (NOT a demonstration of instability; regimes were too easy) |
Caveats: synthetic and easy; one EM non-convergence warning was emitted during fitting; the effect size on real, ambiguous 5-minute crypto data is unknown and is likely larger.

## Application to this project (design proposal; to be validated)
1. **Observation features** (candidates, not yet tested): log return; realized variance over a trailing window; volume relative to trailing median; for alts, trailing correlation to BTC. All must be computed from bars <= t only; normalization with trailing (rolling/expanding) statistics, never global z-scores.
2. **Fit** on a trailing window ending at t_fit; **filter** with frozen parameters between refits; refit cadence and window length are open parameters to be set from a baseline experiment (see raw question 12), not guessed.
3. **Align states after each refit** (e.g., order by fitted volatility mean; log the distance between old and new emission parameters; flag a refit as invalid if state meaning changes).
4. **Choose K** by walk-forward held-out likelihood (and/or BIC), not in-sample likelihood.
5. **Emit per bar**: filtered probability vector, argmax regime, max-probability and entropy as confidence. Handling of uncertainty and switching belongs to Q02.
6. **Timing**: a regime computed at bar-close t may only influence orders at bar t+1 or later.

## Existing implementation assessment
Status: NOT ASSESSED (no repository access). Hermes must run the Phase 0 checks in `Phase0_Audit_Status.md`.

## Recommended improvements (priority order)
1. Add a causality test harness (cheap, independent of the HMM choice).
2. Prototype the filtered-HMM regime component in isolation on the project's 5-minute data, compared against a trivial baseline (e.g., rolling-volatility quantile regimes).
3. Only adopt it if it beats the baseline out-of-sample on the downstream task (Q01-B).

## Dependencies
Repo audit (Phase 0); point-in-time data handling (raw 17-18); window design (raw 11-12); Q02 for switching logic.

## Acceptance criteria
- AC1 Future-perturbation test: for random t, regime outputs for all bars <= t are identical (tolerance 1e-9) when bars after t are removed or replaced by noise.
- AC2 Equivalence test: filtered output equals last row of `predict_proba` on the truncated window (tolerance 1e-9); prototype achieved 1.7e-12.
- AC3 No global scaling: every scaler/normalizer fit uses only data <= the decision time (static check + test).
- AC4 Baseline: record expected regime duration, switch frequency, and occupancy per asset; any alert thresholds are derived from that baseline, not set arbitrarily.
- AC5 Refit alignment: state meaning preserved across refits; violations logged.

## Risk assessment
Gaussian emissions fit fat-tailed 5-minute returns poorly (hypothesis; test); intraday seasonality can masquerade as regimes; EM local optima (seed sensitivity; run multiple initializations); regimes may be partly explained by volatility alone, in which case a simpler method wins; computational cost is low.

## Implementation decision
IMPLEMENT NOW: AC1-AC3 test harness. EXPERIMENT IN ISOLATION: HMM component.

## Implementation record
No project files changed. Only the standalone verification script was run in a scratch sandbox.

## Outstanding questions
Actual project code state; real-data behavior; refit cadence; K; whether crypto 5-minute data show regimes distinguishable beyond volatility.
