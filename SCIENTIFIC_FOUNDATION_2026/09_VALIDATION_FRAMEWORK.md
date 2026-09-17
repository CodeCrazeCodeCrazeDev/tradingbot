# Phase 6 (Part 3): Validation & Recursive Self-Improvement Safety Framework (2026)

This document establishes the scientific metrics, recursive self-critique structures, improvement genome specifications, and non-bypassable safety gates governing autonomous self-improvement loops in AlphaAlgo.

---

## 1. Intelligence & Reliability Metrics

### 1.1 Gain Metric (CL-Bench)
Isolates genuine online learning from pre-trained static capabilities.
$$G = \text{Perf}(\text{Stateful Agent}) - \text{Perf}(\text{Stateless Baseline})$$

### 1.2 Fidelity Metric (World Model)
Measures the accuracy of causal interventional predictions against real-world occurrences.
$$\mathcal{L}_{fidelity} = \left| P(y \mid do(x))_{\text{imagined}} - P(y \mid do(x))_{\text{actual}} \right|$$

### 1.3 Horizon Limit (HORIZON Break Level)
Identifies the maximum sequence length (or time-horizon steps) before strategic planning collapses.
$$\text{Horizon Limit} = \max \left\{ s : P(\text{Success} \mid s) > 0.9 \right\}$$

### 1.4 Expected Calibration Error (ECE)
Measures the alignment of the agent's probability/confidence estimates with actual empirical frequencies.
$$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{n} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$

---

## 2. Non-Bypassable Recursive Self-Improvement Safety Gates

Recursive self-improvement must be tightly constrained to prevent specification gaming, reward hacking, and alignment drift. The system enforces a strict, multi-stage, sequential promotion pipeline:

```
[Improvement Proposal]
          ↓
[Isolated Sandbox]
          ↓
[Static Analysis]
          ↓
[Automated Test Suite]
          ↓
[Scientific Evaluation (FDR / DSR)]
          ↓
[Independent Validation]
          ↓
[Adversarial Red Team Isolation]
          ↓
[Safety Verification Gate (Invariant Check)]
          ↓
[HUMAN GATEKEEPER APPROVAL (Non-Bypassable)]
          ↓
[Versioned Artifact Generation]
          ↓
[Canary / Shadow Evaluation Mode]
          ↓
[Continuous Telemetry Monitoring]
          ↓
[Final Promotion] / [Automatic Rollback]
```

### Absolute Invariant Safety Constraints
1.  **Separation of Optimizing and Evaluating Authorities**: The agent proposing the code mutation is mathematically blocked from grading its own work. The evaluator, multiple testing gates, and safety verification engines must remain completely outside the optimization loop.
2.  **No Self-Approval/Self-Deployment**: Any code or structural parameter change proposed by an agent is strictly set to an unapproved state. Under no circumstances can an agent self-approve, self-commit, or self-deploy code modifications directly to active production systems.

---

## 3. Recursive Self-Critique & Multi-Agent Debate Structure

To validate any major proposed improvement, AlphaAlgo institutes an adversarial four-role critique cycle before requesting human gatekeeper approval:

1.  **Improvement Agent (The Proposer)**: Constructs the strongest evidence-based argument for the proposed mutation, presenting simulation trajectories and expected benefits.
2.  **Critic Agent (The Challenger)**: Actively identifies scientific weaknesses, model over-fitting, hidden assumptions, performance regressions, and unnecessary complexity.
3.  **Adversarial Red Team (The Attacker)**: Actively attempts to exploit the proposed mutation, introducing out-of-distribution market noise, adversarial tick data, and extreme leverage stress to break the candidate system.
4.  **Independent Evaluator (The Judge)**: Evaluates the structured evidence without being involved in proposal generation, calculating multiple testing FDR bounds and Deflated Sharpe Ratios.

---

## 4. The AlphaAlgo Improvement Genome Specification

AlphaAlgo models its state as a versioned, multi-attribute "Improvement Genome" representation, ensuring that any candidate architecture mutation is fully versioned, testable, and roll-backable:

```json
{
  "genome_version": "1.0.4",
  "parent_sha256": "88bdb1ee061805561a337108992a7f053bb0022d",
  "attributes": {
    "architecture_topology": "One_Brain_Unified_CSC_V6",
    "agent_topology": {
      "active_orchestrator": "CognitiveSystemController",
      "voters": ["ImmutableShield", "RiskFortress", "ComplianceGate"]
    },
    "reasoning": "DiscoLoopCell_Continuous_Discrete",
    "planning": "HIPIF_Information_Folding",
    "memory_tier_config": {
      "SAGE": "SAGEGraphMemory_TD_Learning",
      "AutoMem": "Bayesian_Schema_Self_Migration"
    },
    "world_model": "Pearl_SCM_Interventional_do_calculus",
    "learning": "Conservative_Q_Learning_Offline",
    "strategy_discovery": "CMA_ES_Island_Evolver",
    "governance": "ImmutableShield_Veto_Consensus"
  }
}
```

### Multi-Objective Fitness Evaluation Formula
Mutated genomes are evaluated using a multi-objective fitness score ($\mathcal{F}$), preventing the system from over-optimizing for raw trading returns at the expense of safety, complexity, and latency:

$$\mathcal{F} = w_1 \cdot \text{Sharpe} + w_2 \cdot \text{ECE}^{-1} - w_3 \cdot \text{Complexity} - w_4 \cdot \text{Latency} - w_5 \cdot \text{RegressionRate}$$

Where:
*   $\text{Complexity}$ is measured by total active code statement count and logical branching depth.
*   $\text{Latency}$ is measured by average tick processing time in milliseconds.
*   $\text{RegressionRate}$ is the percentage of failures on historic validation task libraries.
*   $\text{ECE}^{-1}$ rewards well-calibrated confidence outputs.
