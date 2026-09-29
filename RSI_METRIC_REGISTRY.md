# RSI metric registry

All rates use explicitly documented denominator, period and annualization. Missing, NaN, Inf, zero-denominator, insufficient sample, noncomparable timestamps or unknown units = **unavailable**, not zero and not passed. Use paired per-bar net returns on one common timeline (flat/abstained bars carry zero return); trade summaries are diagnostics. Portfolio convention: `equity[t+1] = equity[t]*(1 + net_portfolio_return[t])`, with capital, positions and exposure defined in the signed contract. Costs are actual or conservatively modelled; unstated spread, slippage, impact or fees block promotion eligibility.

| Metric (direction) | Definition / input | Gate role and caveat |
|---|---|---|
| Net return ↑ | `equity_end/equity_start - 1` after fees, spread, slippage, funding and impact assumptions | Primary economic outcome, paired at identical timestamps, confidence lower bound and minimum absolute effect pre-registered. |
| Mean net bar-return ↑ | arithmetic mean of full aligned series incl. zero bars | Primary paired test statistic candidate minus incumbent; cannot substitute trade-only wins. |
| Sharpe ↑ | annualized mean excess bar return / standard deviation, annualization from verified bar frequency | Diagnostics if volatility tiny or autocorrelation high; never relabel total return Sharpe. |
| Sortino ↑ | annualized mean excess return / downside deviation below stated MAR | With too few downside observations: unavailable. |
| Calmar ↑ | annualized net return / max peak-to-trough equity DD | Requires a meaningful contiguous window and DD > 0. |
| Max drawdown ↓ | `max_t(1 - equity_t/max_{s<=t} equity_s)` | Hard upper bound and baseline non-regression tolerance, using same sizing/exposure. |
| Tail loss / CVaR ↓ | empirical conditional expected loss beyond pre-registered quantile (e.g. 95%), block-aware CI | Hard gate when minimum tail sample met; else insufficient evidence. VaR is a quantile, not the same as DD. |
| Downside deviation ↓ | RMS negative deviation from MAR over aligned bars | Expose zero denominators/short histories. |
| Profit factor, expectancy, payoff ratio (diagnostic) | sum gross winning P&L / abs(sum losses), mean net P&L per trade, mean win/abs(mean loss) | Not acceptance metrics by themselves; denominator-zero is unavailable. |
| Hit rate (diagnostic) | wins/closed trades (cost-adjusted) | Never acceptance alone; near-zero trading/coverage flagged. |
| Turnover/exposure/capacity ↓ or bounds | gross traded notional/equity, time-weighted capital at risk, order size/liquidity | Compare against common baseline under locked sizing; unknown market depth blocks capacity claim. |
| ECE/Brier ↓ | ECE with fixed bins; Brier = mean `(p-y)^2`, predictions scored before outcome update | Only with timestamped out-of-sample probabilities; insufficient calibrated observations => unavailable. |
| Spread/slippage sensitivity ↓ | delta net return and tail risk between fixed base and stressed costs | Reject if advantage disappears under declared credible stress. |
| Time/regime/instrument robustness ↑ | vector of net advantage and risk differences on predeclared disjoint panels | Missing required regime/instrument => insufficient evidence, not perfect robustness. |
| Latency p95/p99, compute, memory ↓ | independent timed workloads with hardware IDs, repeats and comparable conditions | Hard upper bounds for decision latency, otherwise complexity trade-off. |
| Reliability/safety ↑ | failure rate, reject/duplicate-fill rates, invariant pass + code/dependency footprint | Critical invariant failure is veto regardless of return. |
| Complexity tax ↓ | changed LOC/files, new dependencies, complexity metric where measured, operational burden | Report full delta; accept trade-off only via versioned explicit preference and economic benefit. |

**Comparison procedure:** normalize metric directions (higher-is-better for Pareto without mutating original values); first veto hard constraints, then compute `ΔM = candidate - baseline` in original units and empirical uncertainty. `A` dominates `B` iff no optimization dimension is materially worse (locked tolerance) and at least one is materially better. Candidate dominated by incumbent rejects; incomparable candidates remain *trade-offs requiring explicit operator preferences*, not automatic approvals. A positive lower confidence bound on the predeclared paired net economic effect plus calibrated effect-size hurdle is additionally required; multiple-testing correction uses every attempted hypothesis, not only survivors. DSR/PBO are reported only when valid inputs/search universe exist. Never aggregate into arbitrary weighted score.

## Executable registry (2026-09-26)

`metric_registry.py::METRIC_REGISTRY` is the machine-enforceable version of this table: `name -> (unit, direction)` where direction ∈ {`max`, `min`, `info`}. Contracts reference only registered names; a contract that tries to redefine a direction raises `ContractError` — the registry is authoritative. `info` metrics are reported but excluded from constraint/Pareto decisions. `is_better`/`is_worse` apply direction-aware tolerances; `multi_objective.pareto_relation` and `archive.frontier` consume the same definitions so "dominance" is identical everywhere.
