# Improvement Governance Specification (RSI-GOVERNANCE-2026)

## 1. The Principle of Human Supremacy

The human owner and operator is the absolute and final authority for all AlphaAlgo evolution. AlphaAlgo's autonomous recursive self-improvement is designed to support, inform, and suggest improvements, but is strictly prohibited from bypassing human approval for any high-priority or high-impact operational changes.

### Core Governance Invariants
1.  **Veto Supremacy:** A human rejection is absolute. There is no automated bypass or programmatic override of a human veto.
2.  **No Silence-as-Approval:** A timeout or lack of human response must always be interpreted as a **DENIAL**. The state remains locked.
3.  **No Success-as-Approval:** An experimental candidate displaying high virtual profitability or exceptional benchmark scores must still obtain explicit human authorization before transition.
4.  **No Self-Deception:** The self-improvement engine is structurally separate from the evaluation authority. The code modification process is prohibited from altering validation sets or evaluator weights.

---

## 2. Hard Governance Limits and Verification Gates

All proposed changes are audited and classified into strict governance categories based on their operational impact:

```
[Candidate Proposal]
         │
         ├──► Affects Live Trading, Risk, Capital, Core Architecture? ──► [Human Approval Mandatory]
         │                                                                       │
         │                                                                       ▼
         │                                                             Explicit Human Signed-Off
         │                                                                       │
         │                                                                       ▼
         │                                                              [Canary Deployment]
         │
         └──► Affects Experimental/Low-Risk Sandbox Metrics? ────────────► [Auto-Execution Allowed]
                                                                                 │
                                                                                 ▼
                                                                       Bounded Param Tuning
```

### Verification Gate Requirements
For any candidate to be recommended for human promotion, it must satisfy the following **Promotion Gate Criteria**:

| Dimension | Minimal Required Standard | Verification Method |
| :--- | :--- | :--- |
| **Statistical Significance** | $p \le 0.01$ | Wald Test / Bonferroni-adjusted multiple testing check. |
| **Robustness Impact** | Maximum drawdown remains below historical $1.2 \times \text{VaR}$ | Monte Carlo resimulation over high-volatility scenarios. |
| **Engineering Quality** | 100% unit & integration test pass rate | CI/CD test runner. |
| **Performance Gain** | $\ge 5\%$ capability index improvement | Independent evaluator comparison vs simpler baselines. |
| **Operational Reliability** | 0 critical errors or unhandled exceptions | Static AST checking & sandbox exception tracing. |

---

## 3. Anti-Self-Deception Safeguards

To prevent the improvement loops from overestimating candidate performance, the system enforces the following constraints:
*   **Purged Validation Sets:** Evaluators use strictly partitioned historical testing blocks where any training-set proximity is aggressively purged and embargoed.
*   **Hidden Stress Scenarios:** The independent evaluator retains high-risk historical stress test sets (e.g., 2010 Flash Crash, 2020 COVID crash) that are completely hidden from the candidate generation adapters.
*   **Multi-Agent Debate Disagreements:** Candidate strategies must be analyzed and approved by the Multi-Agent Debate verification swarm, requiring consensus across a minimum of **5 distinct specialized agents** (RiskVerifier, HallucinationDetector, CausalVerifier, LiquidityVerifier, RegimeVerifier).
