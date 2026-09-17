# AlphaAlgo Unified Scientific Architecture Synthesis & Repo-Level Flows (2026)

This document is the authoritative Phase 3 (Scientific Synthesis) specification for AlphaAlgo UCA. It synthesizes the theoretical findings of 16 research papers into a single cohesive, zero-redundancy engineering design, maps authoritative subsystem ownership, and provides 10 detailed ASCII repository flow graphs.

---

## 1. Unified Architecture Principles
To resolve conflicting assumptions across the 16 referenced preprints, UCA-2026 establishes the following core synthesis rules:
- **Rule 1 (Single Authoritative Owner)**: Every strategic capability is owned by exactly one module. There are no competing orchestrators or Registries.
- **Rule 2 (Falsification First)**: Direct supervised execution is advisory. The default action is NO-TRADE. Trade proposals must survive verification swarm peer-review before commit.
- **Rule 3 (Dual-Channel Coherence)**: Reasoning does not rely on flat text prompts (Loss-in-the-Middle). The internal reasoning core loops continuous latent states and discrete symbolic embeddings (DiscoLoop).

---

## 2. Master Subsystem Ownership Matrix

| Subsystem Domain | Authoritative Class / Interface | Source File Path | Responsibility |
| :--- | :--- | :--- | :--- |
| **Cognitive OS & Pipeline** | `CognitiveSystemController` | `trading_bot/core/csc/controller.py` | Runs the 12-step Active Inference pipeline and minimizes Variational Free Energy. |
| **Causal Memory Substrate** | `HierarchicalMemorySystem` | `trading_bot/core/hms/memory.py` | Owns all memory tiers (SAGE Graph + AutoMem) and handles schema migrations. |
| **Procedural Routing** | `SkillRouter` | `trading_bot/core/csc/router.py` | Translates strategic tasks to executable program functions (HASP) or LoRA adapters (S2L). |
| **Verification & Swarm** | `VerificationSwarm` | `trading_bot/core/verification/swarm.py` | Falsifies or validates proposed actions using specialized verifier nodes. |
| **Monotone Policy Gate** | `EvolutionGate` | `trading_bot/governance/evolution_gate.py`| Gates promotion of self-evolved weights using the CL-Bench Gain Metric. |

---

## 3. Repository-Level Flow Graphs

### 3.1. Cognitive Pipeline (12-Step Active Inference)
```
  [Market Observation]
         │
         ▼
  1. Calculate Surprise ──> 2. Traverse SAGE Graph ──> 3. HASP PF Pre-emption
                                                              │
                                                              ▼
  6. Interventional Sim <── 5. Competing Hypotheses <── 4. DiscoLoop Reasoning
         │
         ▼
  7. Pivot/Refine Loop  ──> 8. VFE Minimization     ──> 9. LogAct proposal
                                                              │
                                                              ▼
  12. HIPIF History     <── 11. Immutable Shield    <── 10. Swarm Audit
```

### 3.2. Memory Flow (Hierarchical Memory System)
```
  [Working Memory (DiscoLoop)] ──> [Episodic Ledger Entry] ──> [SAGE Graph Substrate]
                                                                      │
                                                                      ▼
  [Meta-Memory Optimizer]      <── [Task Reward feedback]  <── [AutoMem Optimization]
```

### 3.3. Reasoning Flow (DiscoLoop Recurrence)
```
        [Continuous Hidden State (h_k)]
                   │
                   ▼
       [Continuous Block Update]
                   │
                   ├─────────────────────────────┐
                   ▼                             ▼
       [Quantize Projection]          [Realignment Factor alpha]
                   │                             │
                   ▼                             ▼
        [Discrete Token (e_k)]  ──────> [Realignment Interpolation]
                                                 │
                                                 ▼
                                    [Final Hidden State (h_k+1)]
```

### 3.4. Planning Flow (AutoResearchClaw Pivot/Refine)
```
  [Proposed Plan] ──> [Causal World Simulation] ──> [Failure Rate > 0.4?]
                                                            │
                                              ┌─────────────┴─────────────┐
                                              ▼ Yes                       ▼ No
                                    [Trigger Pivot]               [Execute Plan]
                                              │
                                              ▼
                                   [Hedge/Alternate Plan]
```

### 3.5. Learning Flow (EKSFT Selective Training)
```
  [Supervised Data] ──> [Calculate Token Entropy] ──> [Calculate KL Divergence]
                                                             │
                                               ┌─────────────┴─────────────┐
                                               ▼ Exceeds Threshold?        ▼ Within Bounds
                                        [Apply Token Mask]          [Calculate CE Loss]
                                               │                             │
                                               └─────────────┬───────────────┘
                                                             ▼
                                                    [Parameter Update]
```

### 3.6. Execution Flow (LogAct Shared Log)
```
  [CSC Trade Proposal] ──> [UnifiedEventBus Queue] ──> [Audit Phase (Voter Gather)]
                                                               │
                                                 ┌─────────────┴─────────────┐
                                                 ▼ All Voters Approve?       ▼ Veto Received
                                          [LogAct Commit]             [LogAct Veto]
                                                 │                           │
                                                 ▼                           ▼
                                          [Place Order]               [Reject Trade]
```

### 3.7. Governance Flow (Immutable Shield)
```
  [LogAct Audit] ──> [Query Immutable Shield] ──> [Verify Hard Risk Bounds]
                                                         │
                                           ┌─────────────┴─────────────┐
                                           ▼ Approved                  ▼ Violated
                                    [Forward to Swarm]          [Veto Proposal]
```

### 3.8. Evaluation Flow (DeepWeb-Bench Calibration)
```
  [Agent Predictions] ──> [Compare to Real Outcomes] ──> [Expected Calibration Error]
                                                                  │
                                                                  ▼
                                                      [Adjust Base Likelihood]
```

### 3.9. Evolution Flow (RSEA Monotone Safety Gate)
```
  [Candidate Weight (v2)] ──> [Validate EKSFT Limits] ──> [Measure CL-Bench Gain G]
                                                                  │
                                                    ┌─────────────┴─────────────┐
                                                    ▼ Gain > 0.05 & No Reg      ▼ Regression
                                             [Promote to v2]             [Rollback to v1]
```

### 3.10. SAGE Causal Substrates Graph Flow
```
  [New Fact (Triplet)] ──> [Register SAGE Nodes] ──> [Evaluate Edge Weight]
                                                            │
                                              ┌─────────────┴─────────────┐
                                              ▼ Performance Reward > 0    ▼ Low Utility
                                       [Strengthen Edge]           [Prune Edge]
```
