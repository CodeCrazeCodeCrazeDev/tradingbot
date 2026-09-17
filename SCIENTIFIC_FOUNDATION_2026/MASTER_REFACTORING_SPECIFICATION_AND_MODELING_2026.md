# Phase 6: Refactoring Specification & System Modeling (UCA-2026)

This document contains the complete engineering blueprints, system modeling diagrams, interface contracts, and lifecycle strategies for AlphaAlgo's Unified Scientific Architecture (UCA-2026). It serves as the mandatory, peer-reviewed engineering contract before any code changes are committed to the production repository.

---

# 1. Refactoring Recommendations (Scientific Evidence)

## 1.1. Components to KEEP
*   **ImmutableShield (`trading_bot/core/immutable_shield.py`)**:
    - *Rationale*: Crucial protection against reward hacking and specification gaming (*Reward Hacking safeguards*, DeepMind 2024). It serves as the final non-bypassable governance boundary.
*   **AdaptiveControlPolicyEngine (`trading_bot/core/csc/acpe.py`)**:
    - *Rationale*: Provides sub-millisecond dynamic parameter tuning based on Active Inference surprise feedback loops.

## 1.2. Components to REDESIGN
*   **CognitiveSystemController (`trading_bot/core/csc/controller.py`)**:
    - *Redesign Objective*: Standardize the initialization signature to adaptively resolve legacy parameter bindings, ensure class-level singleton isolation using `_instance`, and strictly bind the 12-step Active Inference pipeline to Causal World Model simulation rollouts (*Active Inference*, Friston 2010; *CWMI*, Li 2025).
*   **EvolutionGate (`trading_bot/governance/evolution_gate.py`)**:
    - *Redesign Objective*: Accept both `threshold` and `improvement_threshold` dynamically, and enforce strict, multi-metric monotone-safe gating over drawdown, calibration error, and latency limits (*RSEA*, arXiv:2606.28374; *CL-Bench*, arXiv:2606.05661).

## 1.3. Components to MERGE
*   **SkillRouter & HASPExecutor (`trading_bot/core/csc/router.py`)**:
    - *Merge Objective*: Consolidate prompt-based routing and low-rank adapter selection into a single authoritative module returning the subscriptable, attribute-accessible `SkillRouteOutcome` dataclass contract (*Skill-to-LoRA*, arXiv:2606.16769).

## 1.4. Components to REPLACE
*   **Fragmented JSON Evidence Logs**:
    - *Replacement Objective*: Replace with the structured, relational `SAGEGraphMemory` tracking claiming, hypothesis, and evidence nodes (*Agents-K1*, arXiv:2606.13669).

## 1.5. Components to ARCHIVE
*   **JEPA World Model Stubs**:
    - *Archive Objective*: Move older non-causal joint-embedding predictive architecture stubs to `_archive/` as they fail to represent interventional do-calculus futures under structural breaks.

## 1.6. Components to DELETE
*   **Duplicate 'agents 2/' and 'advanced_systems 2/' directories**:
    - *Delete Objective*: Completely purge these legacy copy artifacts to prevent import conflicts and maintain 100% namespace cleanliness.

---

# 2. Capability Ownership Matrix

| Core Capability | Owning Class / Component | Source Code File | Scientific Authority |
| :--- | :--- | :--- | :--- |
| **Surprise Perception** | `CognitiveSystemController` | `trading_bot/core/csc/controller.py` | *Active Inference* (Friston, 2010) |
| **Causal Evidence Retrieval** | `HierarchicalMemorySystem` | `trading_bot/core/hms/memory.py` | *Agents-K1* (arXiv:2606.13669) |
| **Low-Rank Skill Selection** | `SkillRouter` | `trading_bot/core/csc/router.py` | *Skill-to-LoRA* (arXiv:2606.16769) |
| **Multi-Hop Reasoning** | `DiscoLoopCell` | `trading_bot/core/csc/controller.py` | *DiscoLoop* (arXiv:2607.00341) |
| **Counterfactual Simulation** | `UnifiedWorldModel` | `trading_bot/world_model/unified_world_model.py` | *CWMI* (arXiv:2605.22119) |
| **Monotone-Safe Gating** | `EvolutionGate` | `trading_bot/governance/evolution_gate.py` | *RSEA* (arXiv:2606.28374) |
| **Adversarial Red-Teaming** | `VerificationSwarm` | `trading_bot/core/verification/swarm.py` | *SocraticPO* (arXiv:2606.09887) |
| **Immutable Governance Gate** | `ImmutableShield` | `trading_bot/core/immutable_shield.py` | *Reward Hacking* (DeepMind, 2024) |

---

# 3. System Modeling & Graphs

## 3.1. Dependency Graph (Architecture Subsystems)
```
     [ImmutableShield (Gate)]
               ↑
     [EvolutionGate (Monotone)]
               ↑
  [CognitiveSystemController (Brain)] ──→ [VerificationSwarm (Critics)]
        │                 │
        ↓                 ↓
 [SkillRouter]     [HierarchicalMemorySystem (SAGE)]
        │                 │
        ↓                 ↓
 [S2L Adapters]     [Causal World Model (SCM)]
```

## 3.2. Control Flow Graph (12-step Active Inference Loop)
```
 [Start: Observation Ingestion]
               │
               ▼
   [Step 1: Calculate Surprise] ──→ Update Variational Free Energy (VFE)
               │
               ▼
   [Step 2: SAGE Evidence Query] ──→ Traverses Entity-Relation Graph (HMS)
               │
               ▼
   [Step 3: HASP Pre-emption] ──→ Interrupt if high-priority volatility guardrail
               │
               ▼
   [Step 4: DiscoLoop Reasoning] ──→ Recurrent Continuous-Discrete update steps
               │
               ▼
   [Step 5: Multi-Hypothesis Gen] ──→ Propose competing Bear, Bull, Range scenarios
               │
               ▼
   [Step 6: Causal SCM Simulation] ──→ Interventional do-calculus rollouts
               │
               ▼
   [Step 7: Pivot / Refine Loop] ──→ If failure rate > 0.4, pivot to safe hedging
               │
               ▼
   [Step 8: Minimize Expected FE] ──→ Select policy that minimizes EFE bounds
               │
               ▼
   [Step 9: Propose LogAct Trade] ──→ Push transactional proposal to UnifiedEventBus
               │
               ▼
   [Step 10: Verification Swarm] ──→ Decentralized critics vote to approve/falsify
               │
               ▼
   [Step 11: Shield Validation] ──→ Final immutable compliance constraints check
               │
               ▼
   [Step 12: HIPIF Information Folding] ──→ Compress step history; store in HMS Ledger
               │
               ▼
  [Commit: Push Execution log to Bus]
```

## 3.3. Data Flow Graph (Pipeline Processing)
```
[Raw Tick Feed] ──→ [NormalizedMarketContext] ──→ [Surprise Formula] ──→ [VFE Score]
                                                            │
                                                            ▼
[Causal SCM SGraph] ←── [SAGE Evidence Nodes] ←── [Epistemic Target]
        │
        ▼
[Counterfactual Simulations] ──→ [Expected Free Energy] ──→ [Optimal Action Selection]
                                                                        │
                                                                        ▼
[Commit Ledger Entry] ←── [HIPIF Folding Operator] ←── [Approved Trade Proposal]
```

---

# 4. Layered Architecture Diagram

```
+-------------------------------------------------------------------------+
|                  Layer 6: Governance & Evolution Gate                   |
|  - RSEA Monotone Gating    - Held-out Backtests     - EKSFT Compliance   |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    Layer 5: Cognitive Decision Loop                     |
|  - Active Inference Core   - 12-step Pipeline       - Multi-Hypothesis  |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                      Layer 4: Memory & Knowledge                        |
|  - SAGE Graph Memory       - WMR Operating Loop     - Transactive Store |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                      Layer 3: Skill & Adapters                          |
|  - SkillRouter             - S2L LoRA Weights       - HASP Programmatic |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                       Layer 2: Execution & Risk                         |
|  - ImmutableShield         - UnifiedEventBus        - LogAct Backbone   |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                   Layer 1: Connectivity & Broker                        |
|  - MT5 Interface           - Level 2 Depth          - Database Engine   |
+-------------------------------------------------------------------------+
```

---

# 5. Authoritative Interface Contracts

To guarantee DP-05 (Unified API Contracts) and eliminate key guessing, all communication between subsystems must utilize these strongly-typed python objects.

## 5.1. Market Context Contract
```python
@dataclass(frozen=True)
class NormalizedMarketContext:
    timestamp: datetime
    symbol: str
    price: float
    volatility: float
    spread: float
    l2_bid_depth: float
    l2_ask_depth: float
    atr_period: float = 14.0
    features: List[float] = field(default_factory=list)
```

## 5.2. Skill Router Outcome Contract
```python
class SkillRouteOutcome(dict):
    """Canonical return API shape for all SkillRouter routing actions with dual dict/object interface."""
    def __init__(self, status: str, action: Optional[str] = None, adapter_id: Optional[str] = None, reason: Optional[str] = None, result: Optional[Any] = None, pf_result: Optional[Any] = None):
        super().__init__()
        self["status"] = status
        self["action"] = action
        self["adapter_id"] = adapter_id
        self["reason"] = reason or ""
        self["result"] = result or {}
        self["pf_result"] = pf_result or result or {}

    @property
    def status(self) -> str:
        return self["status"]

    @property
    def adapter_id(self) -> Optional[str]:
        return self["adapter_id"]
```

## 5.3. Evolutionary Metrics Contract
```python
@dataclass(frozen=True)
class EvolutionMetrics:
    reward: float
    calibration: float  # (1 - Expected Calibration Error)
    robustness: float   # Out-Of-Distribution baseline performance
    latency: float      # Average controller decision speed in milliseconds
    safety_score: float # Zero-violation compliance rate
    gain: float = 0.0   # CL-Bench Gain Metric (G)
```

---

# 6. Deployment & Lifecycle Strategies

## 6.1. Migration Strategy (Zero-Downtime)
1.  **Phase A (Shadow Mode)**:
    Deploy the modernized `CognitiveSystemController` (CSC) in a separate "Shadow Thread." Feed it live market observations, compute Variational Free Energy, simulate counterfactual paths, and fold memories, but route executions to `NullExecutor`. Verify shadow decision equivalence against production legacy systems.
2.  **Phase B (Canary Promotion)**:
    Promote the UCA-2026 stack to 10% of portfolio volume. Enforce monotone safety checks over continuous 48-hour periods.
3.  **Phase C (Full Transition)**:
    Deprecate legacy routing prompts and heuristic decision scripts, pointing all active accounts to the UCA-2026 loop.

## 6.2. Rollback Strategy (Fail-Closed)
*   **Trigger Conditions**:
    - Any safety_score < 1.0.
    - Expected Calibration Error (ECE) increases by > 5%.
    - Systemic latency spikes > 20ms over a 10-observation window.
*   **Rollback Procedure**:
    The system triggers a fail-closed rollback script:
    1. Instantly routes all open positions to neutral hedges or exits.
    2. Modifies symlinks to reference the immutable, cached `main_original.py` baseline.
    3. Triggers Git revert on production branches and shuts down the self-modification daemon.

## 6.3. Validation Strategy
Every capability update or programmatic self-edit must be verified by running:
1.  **AST Pre-Execution Scan**: Ensure syntax validity before code committing.
2.  **Regression Benchmarks**: Run the 12-step test suite (`tests/test_csc_v5.py`).
3.  **Monotone-Safety Validation**: Run the `EvolutionGate` evaluation on held-out files to ensure no protected metric is degraded.
