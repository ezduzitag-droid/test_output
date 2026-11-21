---
id: PHASE0
status: BLOCKED (no repository or vault access in this session)
updated: 2026-11-20
---
# Phase 0 - Existing project audit: status

## What I could not do
Search the Obsidian vault, inspect the code, run existing tests, record a baseline, or create a checkpoint. None of these were available. No claims are made about what the project already implements.

## What is known (from prior notes only)
AI_Trading_Lab: public 5-minute spot data for ADA, BTC, DOGE, ETH, SOL, XRP vs USDT (Binance.US preferred), 12-24 months, public data only, no credentials, no live trading, no fabricated data or silent gap filling.

## Checklist Hermes must run before accepting any Q01 recommendation
1. List repo tree; identify data ingestion, feature code, any regime/HMM code, backtest engine, strategy definitions, model storage.
2. Run the existing test suite; save output as the baseline (`Testing and Validation/00_BASELINE`).
3. Grep for global scalers/normalizers (`StandardScaler`, `.mean()`, `.std()` over full frames), `shift(-n)`, `predict_proba`, `.predict(` on full arrays, `fit` on full history.
4. Create a git tag or backup before any change.
5. Record findings in `Architecture/00_PROJECT_AUDIT` and update the tracker.
