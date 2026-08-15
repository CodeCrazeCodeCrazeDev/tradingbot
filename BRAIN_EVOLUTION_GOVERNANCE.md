# Brain Evolution Governance & Role Segregation
*Prepared by Software Engineer Jules (2026)*

## 1. Segregation of Roles

To prevent gaming, bias, or self-justified behavioral drift, the system enforces complete segregation of duties during brain self-evolution. The improving system is **never** its own sole judge.

```
+---------------------------+       +----------------------------+
| 1. Improvement Proposer   | ----> | 2. Experiment Executor     |
| (Proposes prompt/weights) |       | (Runs tests in sandbox)    |
+---------------------------+       +----------------------------+
                                                  |
                                                  v
+---------------------------+       +----------------------------+
| 4. Independent Verifier   | <---- | 3. Objective Evaluator     |
| (Falsification swarms)    |       | (Measures metrics, errors) |
+---------------------------+       +----------------------------+
              |
              v
+---------------------------+       +----------------------------+
| 5. Promotion Authority    | ----> | 6. Runtime System          |
| (EvolutionGate approvals) |       | (Deploys versioned code)   |
+---------------------------+       +----------------------------+
```

### A. Role Definitions
1. **Improvement Proposer**: Proposes modifications to prompts, strategy weights, or neural parameters. (Cannot run experiments or approve itself).
2. **Experiment Executor**: Sets up the shadow process, instantiates the sandbox, and executes trials. (Cannot view live production parameters).
3. **Objective Evaluator**: Computes metric outcomes, latency, and error rates against fixed, historical, non-contaminated test sets. (Cannot modify safety gates).
4. **Independent Verifier**: A separate swarm of verifiers (e.g. Risk, Liquidity, and Causal validators) that attempts to falsify the experimental findings.
5. **Promotion Authority**: Managed strictly by `EvolutionGate`. Reviews validation results, checks multi-dimensional regressions, and writes the immutable versioned artifact if approved.
6. **Runtime System**: Operates on live production feeds. Bounded by fail-closed rules and capable of immediate rollback.

---

## 2. Dynamic Promotion & Rollback Criteria

### A. Promotion Invariants
A behavioral change is promoted from Experiment to Production only when:
- **Zero Regression**: Latency (with 20% tolerance bounds), drawdowns, and calibration metrics show absolutely zero statistical regression.
- **Improved Calibration**: The calibrated uncertainty corresponds perfectly to actual precision on non-contaminated test cases.
- **Safety Clearance**: Passes 100% of the automated AST security checks recursively scanning for forbidden keywords (e.g. `eval`, `exec`, un-HMACed pickle load).

### B. Rollback Invariants
A roll-back to the stable, versioned champion baseline is triggered **immediately** if:
- Cumulative drawdowns exceed the target volatility threshold by $>10\%$.
- Model response latency spikes above the 1.2x baseline threshold.
- The independent verifier swarm raises a critical flag during live shadow execution.
- Any network, model, or bus timeout is detected.
