# RSI architecture: independent evidence, bounded recursion

## Current vs recommended ownership

`main.py → UnifiedTradingBot → CSC → risk/ImmutableShield → decision bus → execution` is the authoritative trading runtime (`RSI_CURRENT_STATE_AUDIT.md`). The research RSI path is separate, **non-capital-moving**. Reuse `recursive_self_improvement/rsi_loop.py` as bounded coordinator, `improvement_genome.py` for proposals, `ImprovementMemory` for research records, and `evaluation/` for replay once repaired. The verifier/contract authority must be outside candidate-write scope. `recursive_self_improvement/engine.py` old deployment is disabled, `recursive_improvement/` remains compatibility/research until reachability proves deprecation safe. CSC `execute_self_improvement_loop` heuristic is not an authorization gate. No new parallel orchestrator.

```text
[Operator locks contract + incumbent + custody of unseen holdout]
                      ↓ read-only scoped protocol
[Observer] → [Hypothesis + minimal candidate] → [candidate sandbox]
                                                  ↓ one parameter only initially
[Independent evaluator] → paired costs/net P&L → hard risk & leakage gates
                         → uncertainty + corrected trials → Pareto + ΔM
                      ↓ independent signed verifier result (otherwise deny)
[Governance] → rejected / insufficient_evidence / eligible_for_operator_review
                      ↓ future: signed human authorization
[Shadow] → [Paper] → [Canary] → [Production] → [Monitor/rollback]
```

**Trust boundary:** proposer/optimizer and evaluator cannot share write privileges or judge their own claims. Runtime shield, canonical portfolio risk service, human approval and execution paths retain veto authority. Versioned policy is fixed by operator; public hashes alone do not create isolation. Approval of an improvement proposal is never approval of an order.

## Two timescales and permissions

Fast loop: observe grounded failure → retrieve both failed/successful experiments → preregister falsifier → propose one narrow change → run independent paired evaluation → log decision, with candidate/trial/compute/time/recursion budgets. Initially only bounded strategy parameters (Level 1) tested; Levels 2 prompts/context/memory, 3 strategy logic, 4 models/policies, 5 tools/orchestration, 6 agent architecture, 7 evaluator/verifier, 8 RSI algorithm **remain proposal-only** until isolation, independent evaluator and operator governance for each level exist. Slow loop proposes improvements to search/verification process, but can never change the contract or authorize itself. Stop at diminishing returns, insufficient evidence, drift, exhausted budgets or invariants failure. Zero changes is a valid outcome.

## Independent roles

Proposer provides hypothesis, code/config diffs, predicted benefit/regressions; Experimenter executes precommitted protocol on identical histories; Verifier tries falsification and independently attests contract/data/result hashes; Risk sentinel asserts shield/risk/execution invariants; governance checks hard constraints, economic and Pareto criteria and requests human approval for any live-capital stage. Document evidence by level, including calibration, prior-regime retention and cost stress. Memory stores rejects and null outcomes, not only winners. This architecture does not imply existing code has these protections today.
