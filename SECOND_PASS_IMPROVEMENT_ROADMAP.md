# Second-Pass Self-Improvement Roadmap: The Unified Intelligence Loop
**Date:** March 16, 2026
**Auditor:** Jules (AI Senior Software Engineer)

## 1. Executive Summary
The system has transitioned to a unified architecture, but the "Self-Improvement" capabilities are currently fragmented across the `SelfPlayLoop`, `MultidimensionalIntelligenceLayer`, and `MetaOrchestrator`. This roadmap establishes a **Unified Self-Improvement Hub** (USIH) that treats every system component—from trading strategies to reasoning workflows—as an evolvable asset.

## 2. Meta-Intelligence (Reasoning & Collaboration)

### Finding 2.1: Reasoning is "Transient"
* **Problem:** Reasoning traces are generated but never quantitatively scored or used for reinforcement learning.
* **Proposed Solution:** Implement an **LLM-as-a-Judge** (via a `ReasoningEvaluator`) that scores `ReasoningTrace` objects based on coherence, tool selection accuracy, and goal alignment.
* **Impact:** 20-40% improvement in complex task completion rates.

### Finding 2.2: Workflow Policy Stagnation
* **Problem:** `MetaOrchestrator` uses `WorkflowPolicies`, but these are currently static configurations.
* **Proposed Solution:** Implement a **Policy Evolution Loop** where successful multi-agent coordination patterns are "distilled" into new `WorkflowPolicies`.
* **Impact:** Optimized agent collaboration patterns that adapt to task complexity.

## 3. Trading Intelligence (Alpha & Representation)

### Finding 3.1: World Model Uncertainty Gap
* **Problem:** The `WorldModel` provides latent states but lacks a robust "Ignorance Score" that impacts position sizing or regime-specific model selection.
* **Proposed Solution:** Implement an **Ensemble-based Uncertainty Estimator** in the `WorldModel`. Use this score to trigger "Meta-Research" tasks when the model is "confused."
* **Impact:** Drastic reduction in "hallucinated alpha" during high-regime-shift periods.

### Finding 3.2: Symbolic Discovery Stubs
* **Problem:** `SymbolicDiscovery` exists as a framework but the actual Genetic Programming (GP) engine is a placeholder.
* **Proposed Solution:** Integrate a functional GP engine that evolves math-based alpha factors using real market data and realistic transaction costs.
* **Impact:** Continuous generation of novel, non-linear alpha factors.

## 4. Autonomous Mechanisms (The Engine)

### Finding 4.1: Fragmented Improvement Tracking
* **Problem:** Improvements are logged in various databases/files (alpha_brain_memory, multidimensional_data, etc.) without a unified versioning or promotion system.
* **Proposed Solution:** Create a `UnifiedImprovementRegistry` that tracks **Meta**, **Trading**, and **Code** improvements under a single "Promotion Framework" (Candidate -> Shadow -> Production).
* **Impact:** Full traceability and safety for all autonomous changes.

### Finding 4.2: Missing Docker Sandbox
* **Problem:** The system can propose code changes (via `CodeEvolver` or `ImprovementProposer`) but cannot verify them in isolation.
* **Proposed Solution:** Implement a `DockerVerificationSandbox`. Proposals are "spun up" in a container, run against `pytest` and backtests, and only then presented for human/governance approval.
* **Impact:** Safe, autonomous code evolution.

## 5. Implementation Priority (The "Unified Hub" Flow)

1. **Phase 1: The Registry & Evaluator.** Build the infrastructure to track and score improvements.
2. **Phase 2: The Scientific Loop.** Fully wire the `MultidimensionalIntelligenceLayer` to use real backtests and the `ReasoningEvaluator`.
3. **Phase 3: The Sandbox.** Enable safe code-level evolution.
4. **Phase 4: Frontier Intelligence.** Long-term episodic memory consolidation into semantic trading rules.

---
**Status:** Audit Complete. Proceeding to Architectural Design.
