# CSC reward feedback

Reward policy version: `csc-rewards-v1`.

CSC remains the only decision authority. Reward records are diagnostic
evidence, not approval, sizing, vetoes, execution, or automatic model updates.
They have stable content IDs, source/evidence IDs, provenance, named objectives
with units and directions, missing values, blockers, and sample weights.
There is no scalar sum that lets profit buy its way past a safety failure.
Reward functions and their version are code, not candidate-tunable parameters.

The audit also found older scalar reward implementations in
`learning/multi_objective_rl.py`, `core_agent_system/rewards.py`,
`evolution_layer/reward_model.py`, and
`alphaalgo_v2/reward_engine/immutable_rewards.py`. They mix profit, penalties,
and performance into local scores. They were not added to the canonical
assembly: this implementation uses CSC feedback and the existing canonical
RSI evaluator instead of giving those modules another optimization authority.

## Implemented paths

| Path | Feedback | Integration |
| --- | --- | --- |
| CSC settlement | gross return, explicit costs, net return, matched baseline advantage | `record_outcome` persists rewards inside `DECISION_OUTCOME` and returns them to callers |
| Paper execution settlement | recorded entry/exit fill costs and commissions, net PnL, matched always-long outcome | paper runner replays durable fill receipts through `PaperSettlementFeedback` and `CSC.record_paper_settlement` into idempotent `PAPER_SETTLEMENT` audit events |
| Prediction | Brier loss and improvement against a constant 0.5 forecast | same matched settlement event; shared settlements receive weight `1/N` |
| Canonical RSI | economic, risk, robustness and operational improvement vectors from the existing metric registry; separate evaluation credit | `engine_v2._finish` writes the projection beside the independent verdict in the hash-chained evidence ledger |
| Research | credit for a resolved, attributable paired experiment, whether confirmed or falsified; measured compute seconds | `ResearchEngine.evaluate_strategy` hashes arrays/settings before evaluation, stores reward on the report and KG claim, and feeds the bounded research-ordering policy |
| MSOS survival | gross-return drawdown and 95% tail loss over the supplied settlement window | `MSOSRewardAdvisor` is attached by canonical assembly even when optional directional advisors are pruned |

Repeated research arrays/settings have the same evidence identity even if the
question is renamed. Policy credit is deduplicated by identity, source and
reward version; KG rehydration restores it. The policy's existing maximum
priority adjustment remains ±0.15. This does not make related experiments
statistically independent or replace multiple-testing correction.

RSI objectives come from **the existing independent evaluator**. Rejected or
inconclusive candidates cannot earn evaluation credit by showing profit alone.
An eligible verdict still means operator review, never deployment. This change
does not edit RSI contracts, evaluator, anti-gaming rules, archive, order
authorization, or risk limits. Paper adapter instrumentation adds reference
metadata to receipts without changing fill pricing or order policy.
RSI verdicts do not identify data origin by
themselves, so their reward projection reports `unknown` rather than claiming
synthetic replay was observed live.

The MSOS integration imports only a subordinate diagnostic adapter. Its
legacy capital governor, exposure multipliers and trading permission system
are not attached. It reads `self_state.settled_outcomes`; absent/invalid
settlements produce `missing_data`. Repeating a window repeats its reward ID.
Its drawdown is a window statistic on gross price returns, **not account risk**.
Existing risk, shield and governance boundaries remain responsible for risk.

## Data requirements and honest limitations

Current CSC price-based settlements do not provide measured execution costs,
paired baseline returns or an explicit observation origin. Those fields remain
missing/unknown in rewards. To record a cost-aware trade reward, the trusted
settlement caller supplies `cost_return`, `baseline_net_return`,
`outcome_origin`, and `constraints_satisfied`. Returns and costs must use the
same notional and horizon. Never subtract costs twice from an already net
return. A confidence score, trade approval, simulated future or lack of trades
does not earn economic reward.

### Actual paper-fill settlement

`PaperBrokerAdapter` stamps each fill with its reference mark, spread,
slippage, per-unit commission schedule, order type, market-data source, and
the fixed benchmark ID `always_long_same_fills_v1`. The mark is captured at
fill time, including delayed fills; it is not the stale signal-time price.
The typed receipt and decoder preserve this metadata across restarts.

The observer reads canonical SQLite fill receipts and matches opposing
quantities FIFO per instrument, currency and contract multiplier. Scaling in,
partial closes and reversal residuals retain their individual entry references.
Commission is allocated proportionally to matched quantity. Each matched lot
is scored as:

```
notional = matched_quantity * contract_size * entry_reference_mark
gross_pnl = direction * matched_quantity * contract_size * (exit_mark - entry_mark)
net_pnl = direction * matched_quantity * contract_size * (exit_fill - entry_fill)
          - allocated_entry_commission - allocated_exit_commission
cost_return = (gross_pnl - net_pnl) / notional
```

Spread/slippage already affect fill prices and are never deducted twice.
Returns use reference entry notional in quote currency; they are not leveraged
account-equity returns. For the paired baseline, a hypothetical BUY at the
entry mark and SELL at the exit mark use the exact same quantities, fill
interval, recorded cost schedules and commissions. This is explicitly
**counterfactual**, not a second executed strategy or a whole-period passive
portfolio benchmark. Its equal-cost timing-matched comparison isolates
directional advantage; it does not prove selection skill or statistical edge.

`PAPER_SETTLEMENT` events link opening decisions, both orders and both fill
keys. Their deterministic IDs are inserted atomically into the existing audit
table. Repeated polls, duplicate reports and restarts cannot earn more credit;
conflicting evidence under an existing ID fails. No extra reward ledger or
order-submission path is introduced.

Price-forecast closures still use `DECISION_OUTCOME`. They are not executed
exit receipts and do not earn this economic feedback. Pending/unfilled orders,
open residual inventory and rejected orders do not create fill settlements.
Old receipts without reference metadata, unsupported limit-order benchmarks,
or inconsistent cost evidence stay incomplete rather than inheriting today's
settings. The observer does not flatten positions or infer successful exits.
It does not mark all governance constraints satisfied merely because fills exist.

The paper runner synchronizes feedback on startup, after cycles/operator
commands, and before shutdown, and reports counts under `economic_rewards`
in its snapshot. To score the persisted execution feedback:

```bash
python scripts/score_paper_run.py --state-dir var/paper_run_p4 --fill-rewards
```

This produces `fill_reward_score.json` without reading the decision journal
or mapping sparse decisions onto arbitrary source bars. Cash totals stay
separate by currency. A zero-settlement report is not a profitability verdict.
Only newly generated receipts have the required cost metadata.

Research callers must identify the data source through `origin` and label the
dataset. Supported origins distinguish historical, paper, live, synthetic and
simulated data. Synthetic/simulated experiments retain diagnostics but receive
no real-evidence research credit. A pre-scoring content hash establishes
replay identity. A sealed diagnostic contract referencing that hash is queued
before evaluation and its seal is verified when issuing reward. The contract
and claim use the existing buffered research audit path, whose durability
depends on the runtime draining/persisting it. This does not attest an untouched holdout, independence,
causality, or statistical significance. That remains the sealed evaluator's job.

## Other places rewards belong

| Area | Appropriate target | Current status |
| --- | --- | --- |
| World model | decoded future market target versus matched persistence; forecast error at a fixed horizon | `forecast_reward` helper added and tested; not connected to latent-only training |
| Execution | measured fill costs, latency and failures versus precommitted budgets | paper market-fill costs and matched baseline wired; live receipt, latency and failure-budget adapters remain separate work |
| Learning safety | attempts to update despite an existing MSOS freeze/quarantine | `firewall_reward` adapter added and tested; no bypass/unfreeze action |
| Advisors | incremental performance versus an ablated CSC on matched decisions | existing reliability/contribution evidence remains the source; no reward merely for emitting BUY/SELL |
| Abstention | realized opportunity cost versus a precommitted alternative with matched risk/costs | no reward for being flat alone; avoids training permanent abstention |
| Data quality | verified freshness, missingness and leakage violations | retain hard validity gates; do not turn missing data into zeros or rewards |

The world model currently reports latent quantities, so latent cosine and
simulated reward are not treated as observed trading utility. A trained flag
alone is insufficient to authorize forecasting or trading claims.

## Verification

Run the focused reward and existing integration regressions:

```bash
.venv/Scripts/python.exe -m pytest tests/rsi/test_reward_feedback.py \
  tests/rsi/test_cycle.py tests/rsi/test_multi_objective_gates.py \
  tests/core/test_csc_feedback_loop.py tests/core/test_csc_research.py \
  tests/core/test_research_os.py -q --no-cov -p no:cacheprovider
```

Paper receipt integration:

```bash
.venv/Scripts/python.exe -m pytest tests/execution/test_paper_feedback.py \
  tests/execution/test_paper_cost_model.py \
  tests/foundation/test_persistence_repository.py \
  tests/foundation/test_execution_bridge_typed.py \
  tests/execution/test_fault_gate.py -q --no-cov -p no:cacheprovider
```

These verify reward semantics, persistence/replay, duplicate evidence,
missing/nonfinite values, baseline/cost accounting, and preservation of the
canonical RSI gate. They do not establish profitability or reward calibration
on prospective market outcomes.
