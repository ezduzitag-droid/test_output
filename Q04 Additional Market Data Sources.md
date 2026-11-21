---
type: research-record
ids: [Q04-A, Q04-B]
category: Market Regimes
status: RESEARCH COMPLETE
implementation: DOCUMENT FOR FUTURE USE (pending local audit)
created: 2026-11-21
---

# Q04 Additional Market Data Sources

This record establishes which additional data sources — implied volatility, options signals, volume, liquidity, breadth — could improve regime recognition before price alone reveals it, and how to prove a candidate improves classification rather than adding overfittable variables. Verified evidence: implied volatility is forward-looking with an official definition (CBOE's VIX methodology), and research links it to future return distributions; daily liquidity proxies (Amihud, Corwin–Schultz) and order-flow imbalance have documented constructions; evaluation tooling (MI, permutation importance) is established, but the decisive test is walk-forward ablation on regime quality. The asset universe is unspecified: recommendations are conditional on asset class and the availability/latency audit below. Affects A, B, C, D, H.

## Question IDs

- Q04-A — Which additional data sources (implied volatility, options, volume, liquidity, breadth) could improve early regime recognition.
- Q04-B — How to evaluate whether additional indicators genuinely improve regime classification instead of adding overfitting-prone complexity.

## Original research questions

- Q04-A: "Which additional market data sources, including implied volatility, options prices, trading volume, liquidity, and market breadth, could improve our bot's ability to recognize market conditions before they become obvious in historical price movements?"
- Q04-B: "How should the bot evaluate whether additional market indicators genuinely improve regime classification, rather than simply introducing more variables that increase training complexity and overfitting?"

## Research objective

**Q04-A** must establish candidate sources with verified constructions, availability/latency/PIT requirements, and which are plausibly leading (not coincident), as testable hypotheses; price-only recognition lags, so forward-looking inputs gain lead time only with honest timestamps. Affects components A, B, C, D.

**Q04-B** must establish a pipeline comparing classifier quality with and without each candidate, screening statistics (mutual information, permutation importance, mRMR-style redundancy control) and their pitfalls, and accept/reject rules on walk-forward behavior; added variables multiply HMM parameters, and noisy features degrade the causal probabilities Q02/Q03 use. Affects components C, D, F, H.

## Existing project context — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Check locally before implementation planning.

- [ ] Current feeds (A): assets, fields, history depth, availability timestamps.
- [ ] Implied-volatility/options handling (`vix`, `implied`, `option`, `IV`, `skew`) anywhere.
- [ ] Breadth computations (`advance`, `decline`, `above_ma`); constituent universe defined?
- [ ] Liquidity proxies (`amihud`, `illiq`, `spread`, `bid_ask`, `depth`, `imbalance`).
- [ ] Does the project trade one asset, a universe, or derivatives — decides which sources apply.
- [ ] Feature-validation code (B): any selection/importance/ablation harness?
- [ ] scikit-learn version (mutual_info_classif / permutation_importance availability).
- [ ] Latency handling: as-of joins and availability columns, or naive date-key merges?
- [ ] Test template asserting PIT safety per new feature?
- [ ] Monitoring of missing/late data rates for external feeds?

## Technical concepts

- **Implied volatility:** the volatility reproducing an option's market price in a pricing model; forward-looking.
- **VIX:** CBOE's 30-day volatility expectation implied by S&P 500 index options, computed model-free across strikes [per CBOE methodology].
- **Options-derived information:** term structure, skew (put/call asymmetry), put/call ratios.
- **Market breadth:** advance/decline, fraction of constituents above a moving average, new highs minus lows.
- **Volume profiles:** traded-volume distribution; daily features: log volume changes, volume vs trailing average.
- **Liquidity measures:** Amihud's illiquidity (|return| per dollar volume), Corwin–Schultz spread estimate; intraday: order-book depth and order-flow imbalance.
- **Asset correlations:** rolling average pairwise correlation; rises in stress.
- **Market-wide indicators:** credit spreads, curve shape, currency indices — can lead equity or crypto regimes.
- **Publication latency:** delay between the moment a datum describes and when it becomes obtainable; ignoring it creates look-ahead.
- **Mutual information (MI):** nonparametric feature–target dependence; k-NN estimation in scikit-learn.
- **Permutation importance:** held-out performance drop when one feature is shuffled, on the fitted model.
- **mRMR:** minimum redundancy–maximum relevance selection (described method here; lead, no primary citation).
- **Ablation-based comparison:** fit the classifier with and without a candidate; compare held-out quality on folds.
- **Cross-validated feature addition:** add candidates under walk-forward CV; accept only consistent held-out improvement.
- **Multiple-testing risk:** screening many features guarantees chance winners; require cross-fold consistency and rationale.

## Research findings

### Q04-A findings

- Implied volatility is the best-verified candidate. CBOE defines VIX as a 30-day expected-volatility measure computed model-free from S&P 500 index options, with published, updated methodology [ESTABLISHED — the CBOE Volatility Index Methodology document (dated 2026-02 per metadata) and the CBOE VIX white paper hosted by OIC]. The feature at t must be the value available at the decision timestamp — retrofitting the daily close later is look-ahead [ESTABLISHED definition; PIT INTERPRETATION].
- Predictive power: Banerjee, Doran and Peterson (2007, JBF) study implied volatility and future portfolio returns within a literature where VIX predicts index returns, concentrated at extreme VIX levels; implied volatility also forecasts realized volatility better than lagged realized volatility. Net: strong support as a volatility-regime feature; weaker support for return predictability [CONTESTED] [ESTABLISHED].
- Liquidity is measurable from daily data: Amihud (2002) defines illiquidity as the daily average of |return|/dollar volume, priced into returns [ESTABLISHED]; Corwin and Schultz (2012) estimate spreads from two-day daily high/low prices [ESTABLISHED]. Page-listing discrepancy: 719–760 (Wiley) vs 719–759. Cont, Kukanov and Stoikov establish a linear order-flow-imbalance vs price-change relation, slope inversely proportional to depth — valuable only with L2 data [ESTABLISHED; conditional on data availability].
- Breadth, volume profiles, and cross-market indicators are practitioner-standard but lacked a verifiable primary citation: hypotheses for the Q04-B gate, not established predictors [INTERPRETATION]. Options signals need options markets; breadth a constituent universe; order-book measures intraday feeds; crypto lacks traditional breadth — substitutes (funding rates, open interest) only after an audit [INTERPRETATION]. Every external feed needs an availability timestamp and as-of join; feeds published after the decision timestamp must be lagged — a misjoined "forward-looking" feature is a look-ahead device [ESTABLISHED PIT principle; latencies measured locally].

### Q04-B findings

- Screening has official implementations: scikit-learn documents `mutual_info_classif` (k-NN MI for a discrete target) and permutation importance (held-out drop under shuffling) [ESTABLISHED — official docs]. Pitfalls: MI is biased upward in small samples; compute per fold against PIT labels, never full-sample; permutation importance measures contribution to the fitted model, not trading outcomes [ESTABLISHED properties; discipline INTERPRETATION]. mRMR-style redundancy control lacks a verified primary source (lead; Verified: NO) — substitute: rank by MI/permutation importance, drop features highly correlated with selected ones before ablation [INTERPRETATION].
- The decisive test is ablation: refit the Q01 HMM (fixed K, window, seed) with and without the candidate across folds; compare held-out likelihood, median dwell, separation, confidence, downstream strategy-separation where computable. Inclusion requires consistent cross-fold improvement without degrading dwell stability [INTERPRETATION on ESTABLISHED components].
- Guard complexity: each continuous feature adds two emission parameters per state (diagonal covariance) — with K=3, ten extra features mean sixty parameters. Acceptance weights parsimony: fewer features with economic rationale, stable cross-validated improvement, full re-evaluation after any change since all labels shift [ESTABLISHED arithmetic; thresholds INTERPRETATION].
- Screening must respect temporal structure: random-split CV inflates importance via leakage; only walk-forward splits per [[Q06 Time Series Validation]] standards are trustworthy [ESTABLISHED principle].

## Verified sources

| # | Title | Author/Org | Date | URL | What it establishes | Limitations | Verified |
|---|-------|------------|------|-----|---------------------|-------------|----------|
| 1 | Volatility Index Methodology — Cboe Volatility Index (VIX) | Cboe Global Markets | 2026-02 | https://cdn.cboe.com/resources/indices/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf | Official model-free VIX construction | Methodology doc, not predictive evidence | YES |
| 2 | The CBOE Volatility Index – VIX (white paper) | CBOE/OIC | n.d. | https://www.optionseducation.org/getmedia/5d6a69e4-8a3a-449d-8fef-be10638919c7/vixwhite.pdf | VIX purpose and formula | Publication date unverified from metadata | YES |
| 3 | Illiquidity and stock returns: cross-section and time-series effects | Yakov Amihud, Journal of Financial Markets 5(1):31–56 | 2002-01 | https://www.sciencedirect.com/science/article/pii/S1386418101000246 | Amihud illiquidity ratio; liquidity priced in returns | Equity evidence; noisy for high-volume assets | YES |
| 4 | A Simple Way to Estimate Bid-Ask Spreads from Daily High and Low Prices | S. A. Corwin & P. Schultz, Journal of Finance 67(2) | 2012 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2012.01729.x | Spread estimation from daily OHLC | Page-listing discrepancy 759 vs 760 | YES |
| 5 | The Price Impact of Order Book Events | R. Cont, A. Kukanov, S. Stoikov — arXiv:1011.6402 | 2010 / 2014 | https://arxiv.org/abs/1011.6402 | Linear order-flow-imbalance vs price relation | Journal metadata not re-verified; needs order-book data | YES |
| 6 | Implied volatility and future portfolio returns | P. S. Banerjee, J. S. Doran, D. R. Peterson, Journal of Banking & Finance 31(10):3183–3199 | 2007-10 | https://econpapers.repec.org/RePEc:eee:jbfina:v:31:y:2007:i:10:p:3183-3199 | IV/VIX related to future portfolio returns, at extremes | Magnitudes contested; equity-index scope | YES |
| 7 | scikit-learn: mutual_info_classif / permutation feature importance | scikit-learn developers | current | https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.mutual_info_classif.html | Official MI and permutation-importance estimators | k-NN MI bias in small samples; model-relative | YES |

Most important: the CBOE documents fix what implied volatility is and how it is computed; Amihud (2002) and Corwin & Schultz (2012) make liquidity measurable from likely-existing daily OHLCV; Cont et al. defines the order-flow signal should order-book data arrive; Banerjee et al. (2007) anchors the IV-leads-returns question; scikit-learn pages standardize screening.

Established: VIX construction; daily liquidity estimators; order-flow imbalance relation; IV–return relationship (contested magnitude); MI/permutation tooling. Experimental: whether any improve this project's classification — what the Q04-B pipeline must demonstrate locally. Interpretation: breadth/correlation/cross-market features, mRMR substitution, ablation rules, parsimony weighting, asset-class conditionality.

## How the technique works

Feature constructions (Q04-A). Amihud: `ILLIQ_t = mean(|r_d| / DV_d)` over a window (r log return, DV dollar volume); higher means volume moves price more. Corwin–Schultz: with `β = (ln(H_t/L_t))² + (ln(H_{t+1}/L_{t+1}))²` and `γ = (ln(max(H_t,H_{t+1})/min(L_t,L_{t+1})))²`, compute `α = (√(2β) − √β)/(3 − 2√2) − √(γ/(3 − 2√2))` and spread `S = 2(e^α − 1)/(1 + e^α)`, floored at zero and averaged. Order-flow imbalance aggregates signed order-book events; Cont et al.'s law: `Δp ≈ λ · OFI`, `λ ∝ 1/depth`. VIX features: level, daily change, term-structure ratio.

Evaluation pipeline (Q04-B). Step 1 — PIT labels: causal labels on training folds (Q01 discipline). Step 2 — screening: per fold, MI of each candidate against labels plus permutation importance on a reference classifier; de-correlate. Step 3 — ablation: refit with and without the candidate; compare held-out likelihood, median dwell, confidence, separation. Step 4 — accept only consistent cross-fold improvement with economic rationale.

Inputs: candidate feeds with availability timestamps; the PIT feature matrix; a fixed, seeded classifier. Outputs: screening tables, per-fold ablation results, registry entries. Strengths: measurable, fold-consistent. Limitations: MI bias in short folds; ablation compute per candidate; acceptance rules can be overfit. Computation: negligible; HMM refits dominate. Failure: non-PIT labels; lookahead joins; thresholds tuned on selection folds (nested or held out).

## Reference implementation sketch

```python
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif

def amihud_illiq(px: pd.DataFrame, window: int = 21) -> pd.Series:
    """Amihud (2002): mean(|ret| / dollar volume) over a window; data <= t only."""
    r = np.log(px["close"]).diff()
    dv = px["close"] * px["volume"]
    return (r.abs() / dv).rolling(window).mean()

def corwin_schultz(px: pd.DataFrame, window: int = 21) -> pd.Series:
    """Corwin & Schultz (2012) two-day high-low spread estimator (daily OHLC)."""
    h, l = np.log(px["high"]), np.log(px["low"])
    beta = (h - l).pow(2) + (h - l).pow(2).shift(1)      # two consecutive days
    gamma = (h.rolling(2).max() - l.rolling(2).min()).pow(2)
    den = 3.0 - 2.0 * np.sqrt(2.0)
    alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / den - np.sqrt(gamma / den)
    s = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    return s.clip(lower=0.0).rolling(window).mean()      # negative spreads floored

def align_as_of(features: pd.DataFrame, feed: pd.Series,
                feed_available: pd.Series) -> pd.Series:
    """PIT join: value known at t = last feed value whose availability <= t."""
    f = pd.DataFrame({"value": feed, "avail": feed_available}).sort_values("avail")
    idx = f.avail.searchsorted(features.index, side="right") - 1
    return f.value.iloc[idx.clip(lower=0)].set_axis(features.index)

def mi_screen(X: pd.DataFrame, labels: pd.Series, seed: int = 0) -> pd.Series:
    """Per-fold MI screening; labels MUST be causal regime labels for the fold."""
    Xf = X.loc[labels.index].ffill().dropna()
    labels = labels.loc[Xf.index]
    mi = mutual_info_classif(Xf.values, labels.values,
                             discrete_features=False, random_state=seed)
    return pd.Series(mi, index=Xf.columns).sort_values(ascending=False)
# Next: seeded ablation — refit the Q01 HMM with/without each candidate;
# accept consistent held-out wins only.
```

## Application to this project

Component A: adopted sources enter ingestion with availability timestamps and freshness checks. Component B: validation extends to new feeds (range checks, stale alarms, as-of join tests). Component C: the builders enter a feature registry recording source, construction, availability handling, and the admitting Q04-B verdict. Component D: the emission vector expands only through the gate; keep it parsimonious (4–8 features). Component H: the ablation harness reuses Q01-B's walk-forward machinery, measuring classifier quality and downstream strategy-separation consistently. Component J: monitor feed latency, stale rates, feature drift. F/G: context expansion (Q03) inherits gated features only. Siblings: Q01 consumes the emissions; Q02's confidence moves with feature quality; Q03 takes accepted features; Gate 1 records decisions.

## Existing implementation assessment — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Classification: **UNKNOWN — requires local audit.**

Evidence checklist:
- Which source families (IV/VIX, options, volume, liquidity, breadth, order-book) exist?
- Availability timestamps recorded, or value-timestamp merges (look-ahead hazard)?
- Any importance/ablation harness using walk-forward splits?
- scikit-learn MI/permutation tooling available?
- Order-book or intraday feeds exist (decides Cont et al. applicability)?
- Feature registry with provenance and accept/reject records?
- Missing/stale-rate monitoring for external feeds?
- Asset universe documented for the conditionality?

Classification vocabulary: IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY.

## Recommended improvements

1. **P0 — Availability timestamps and as-of joins for every external feed.** No candidate enters via naive date-key merges; PIT join test per feed.
2. **P0 — Feature gate as a standing harness.** Screening plus seeded ablation as a repeatable job storing artifacts in I.
3. **P1 — Daily liquidity features first.** Amihud and Corwin–Schultz use likely-existing data; admit through the gate before new feeds.
4. **P1 — Implied-volatility features where an options market exists.** Level/change (term structure if available); skip classes without listed options.
5. **P2 — Breadth/correlation features** once a universe and cross-asset panel exist; same gate. **P2 — Order-book signals** only if intraday acquisition is approved; otherwise Cont et al. stays design literature.

## Dependencies

Upstream: A (feeds + timestamps), Q01 (causal labels and the classifier ablated), Q06-type walk-forward standards. Downstream: C (feature registry), D (emission vector), Q02/Q03 (confidence and context), H (ablation). External: scikit-learn (verified tooling); no new libraries mandatory.

## Acceptance criteria

- PIT join test passes for every feed: deleting data with availability after t leaves the feature value at t unchanged.
- Gate artifacts exist: per-fold screening tables and ablation results per accepted feature, with seed, fold boundaries, classifier hash.
- Consistency rule: accepted features improve the primary ablation metric on a majority of folds without degrading median dwell — fold count and metric set by the first full gate run.
- Parsimony: total emission-feature count stays within the budget recorded at baseline.
- Feed health: missing/stale rates per source monitored, baselined on the first ingestion month.

## Risk assessment

Implementation risks: lookahead joins making candidates look predictive (P0 tests mitigate); MI bias in short folds; ablation thresholds re-tuned until a favorite passes (freeze the rule); unit/currency mismatches in dollar volume. Operational risks: feed outages and staleness (VIX holidays, constituent churn); feature drift after market-structure changes; less stable EM refits. Failure modes: a "leading" feature actually coincident adds noise without lead time; correlated additions (VIX, realized vol) duplicate an axis; an unrepresentative universe misleads breadth. Regressions: any feature-set change shifts every label — rerun the full Q01→Q02→Q03 chain after each admission.

## Implementation decision

Adopt gated, evidence-first onboarding: start with daily liquidity estimators and (where applicable) implied volatility, admitted only after the gate shows consistent held-out improvement; breadth and order-book sources follow only if infrastructure exists. Recommendations stay conditional on the asset universe and availability/latency audit; no source is adopted on literature claims alone.

## Implementation record — BLOCKED

⛔ **BLOCKED — external repository not available in this sandbox.** Fill in after local implementation:

- Files changed: <fill in>
- Tests added/run: <fill in>
- Results (gate artifacts, accepted/rejected features, feed-health baseline): <fill in>
- Rollback reference: <fill in>
- Date: <fill in>

## Outstanding questions

- What exactly does the project trade (asset classes, venues, instruments)? Recommendations are conditional on this.
- Which external feeds are obtainable at acceptable cost and latency?
- What folds and metrics will the standing gate use, and who owns the acceptance rule?
- Without an options market, which substitutes (funding rates, open interest, volatility proxies) should the gate evaluate first?

## Research status

RESEARCH COMPLETE — implementation pending local audit.

## Related notes

- [[Q01 HMM Market Regimes]]
- [[Q02 Bayesian Regime Detection]]
- [[Q03 Contextual Bandit Strategy Selection]]
- [[Gate 1 Market Intelligence]]
- [[Q06 Time Series Validation]]
- [[Q09 Point in Time Features]]
