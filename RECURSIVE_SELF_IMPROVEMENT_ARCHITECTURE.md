# Recursive Self-Improvement Architecture & Segregation of Authority

This document defines the authoritative architecture of AlphaAlgo's recursive self-improvement pipeline, specifically enforcing strict separation of proposal from execution authority.

---

## 1. Segregation of Authority Pattern

The core failure mode of recursive self-improving systems is "unrestricted recursive self-modification." If an intelligence layer has the power to both propose changes to its code and approve them for deployment, it can:
1. Rewrite its own safety constraints.
2. Exploit the evaluation harness (reward-hacking).
3. Cascade errors unchecked through the system.

AlphaAlgo enforces a non-bypassable, multi-stage segregation model where the Proposing Agent has zero promotion or deployment authority.

```
       [Research / Proposer Agent]
                    │
                    ▼ (Proposes Improvement)
          [Disposable Sandbox]
                    │
                    ▼ (Compiles / Runs Virtual Trials)
          [Self-Critic Engine] ── (Self-Correction Loop)
                    │
                    ▼ (Passes Critic)
         [Adversarial Red Team] ── (Falsification Scenarios)
                    │
                    ▼ (Robust to Hacks)
       [Independent Evaluator Harness] ── (Walk-Forward out-of-sample)
                    │
                    ▼ (Zero-Regression on Protected Metrics)
      [Immutable Governance Gate (Shield)]
                    │
                    ▼ (Requires Signature)
         [Human approval (Optional)]
                    │
                    ▼ (Committed)
       [Versioned Artifact Registry]
                    │
                    ▼ (Staged)
          [Deployment Controller]
                    │
                    ▼ (Canary & Active Guardrails)
          [Live Production Environment] <──> [Active Rollback Monitor]
```

---

## 2. Process Phase-Gates

### Phase 1: Proposal Generation
The active Research Agent identifies a capability gap, formulates an architectural hypothesis, and compiles an improvement proposal.
*   **Gate Constraint**: The proposal must include a versioned **Improvement Genome** block.

### Phase 2: Sandboxed Isolation
The proposed code changes are checked out and compiled inside a highly isolated `multiprocessing.Process` sandbox or a temporary container with strict network and CPU limits.
*   **Gate Constraint**: Execution is terminated with SIGTERM if it exceeds a hard-coded wall-clock timeout.

### Phase 3: Recursive Self-Criticism
The proposing agent is forced to execute an internal critique loop against the compiled results, answering strict falsification and leakage questions (see `SELF_CRITIC_ARCHITECTURE.md`).

### Phase 4: Adversarial Red-Teaming
A separate, non-cooperative Red Team agent attempts to break the proposal by generating hostile market ticks, extreme liquidity drains, and reward-hacking payloads (see `RED_TEAM_BLUE_TEAM_ARCHITECTURE.md`).

### Phase 5: Independent Evaluation
An immutable validation harness evaluates the candidate using walk-forward testing over untouched out-of-sample datasets.
*   **Gate Constraint**: The evaluation code and dataset splits are completely read-only and cannot be altered by the proposing agent.

### Phase 6: Immutable Governance Gate (Shield)
The `EvolutionGate` and `ImmutableShield` verify that all protected metrics (drawdown, calibration, latency, safety score) have zero regression.
*   **Gate Constraint**: Any single metric regression results in immediate and absolute rejection.

### Phase 7: Versioned Deployment & Rollback Canary
If approved, the candidate is stored in the **Artifact Registry** as a versioned genome. It is deployed as a canary (e.g. 5% exposure). If any active HASP risk program triggers or performance drifts, the deployment controller triggers an immediate, atomic rollback to the parent version.
