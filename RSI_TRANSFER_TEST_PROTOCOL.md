# RSI transfer test protocol

Preregister the family of tests, assets/venues, cutoff dates and acceptance rules in `RSI_EVALUATION_CONTRACT.md` **before generating** a candidate. Transfer does not mean universal superiority: estimate risk-adjusted robustness over defensible variation and abstain under inadequate evidence. The one EURUSD replay is diagnostic only.

1. **Time:** chronological train → validation model choice → purged/embargoed rolling or expanding OOS folds → operator-custodied final holdout, without fitting calibrator or features on later outcomes. Align baseline/candidate on identical timestamps; overlap of prediction or trade exit horizon across boundaries is purged. Include prior and recent data plus untouched future-like periods.
2. **Regimes:** predeclare causal, past-only regime labels (trend/range, high/low volatility, crisis/transition), ensure minimum effective observations per panel; report no coverage as `insufficient_evidence`. No retrospective winner-only slicing.
3. **Instruments/venues:** predeclare optimized and truly unseen assets, sessions and corporate-action/survivorship handling. Common notional/exposure/currency units. If only EURUSD available do not claim cross-instrument transfer.
4. **Costs/execution:** normal and stressed observed spread, commission, borrow/funding, slippage, latency, rejection/partial-fill and capacity assumptions, with versioned source. If actual order book/broker evidence is absent mark impact/capacity unavailable, not zero. Price fill uses next executable opportunity; guard against OHLCV intrabar sequencing claims.
5. **Perturbations:** multiple precommitted seeds, starting balances, small parameter changes, missing/stale/corrupted quotes, crashes and drift; keep candidate and incumbent under same shocks. Compare failure rate and protected risk invariants, not only return.
6. **Statistical evaluation:** paired per-bar cost-adjusted delta including no-trade periods, predeclared block-bootstrap method and block sensitivity; track family-wide trials and corrected inference. Sharpe/DSR/PBO only where valid; uncertainty intervals and economic minimum must both clear contract.
7. **Final holdout:** proposer cannot read results or raw rows; operator verifier answers at most a budgeted query, emits bound attestation, records every use. Reuse leaks information even without rows; exhausted/contaminated holdouts retire or rotate under separate governance. A local file naming itself `hidden` has no trust value.

Report every dimension, including degradation in DD, CVaR, latency, complexity and costs. Apply hard constraints first and Pareto dominance next; incomparable trade-offs await explicit operator preference. Missing test coverage is not a pass.

## v2 implementation (2026-09-26)

`transfer.py::TransferEvaluator` executes the protocol end-to-end on `Scenario(label, regime, cost_multiplier, seed, frames)` panels built from the contract's `regime_panel` × `cost_multipliers` × `seeds`. Each scenario replays via the same `PairedFamilyReplay` as the main gate (identical mechanics and costs — the panel is *not* a weaker secondary simulation). `classify()` returns:

- `LOCAL` — gain only at observed settings (dies under cost stress or is absent in selection regime) → candidate rejected;
- `ROBUST` — gain only in selection regime at all declared perturbations → archived as `specialist(regime_cell)`, never champion;
- `TRANSFERABLE` — positive lower-CI in >=2/3 of regimes at observed cost → eligible to remain `challenger`/`champion` pending Pareto gates;
- `SYSTEMIC` — TRANSFERABLE plus zero regression-budget breach in every scenario.

`synthetic_market.py` supplies deterministic regime fixtures for engineering tests; per the data constraint all transfer results are fixture evidence only.
