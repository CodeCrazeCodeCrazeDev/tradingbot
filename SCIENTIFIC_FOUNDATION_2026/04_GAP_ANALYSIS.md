# Phase 4: Gap Analysis (Scientific vs. Actual Codebase)

This document compares the scientific foundations derived from the 16 papers against the **actual source code** of AlphaAlgo (Audited June 2026).

---

## 1. Architectural Integrity

| Subsystem | Scientific Target (Paper) | Actual Codebase Reality | Status | Scientific Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Orchestration** | Unified CSC (Effective Agents) | **82+ Disconnected Orchestrators** | **Critical Deficit** | Fragmentation causes "Functional Collapse" (Illusion of MAS). |
| **World Model** | Causal Do-Calculus (CWMI) | **Correlational Latent Dynamics** | **Needs Redesign** | Correlational models fail under market regime shifts. |
| **Planning** | Information Folding (HIPIF) | **Infinite-Append Context History** | **Missing Completely** | "Long-Horizon Mirage" - Strategic drift occurs after ~10 steps. |
| **Self-Improvement** | SocraticPO / RSEA | **Stubbed `_apply_improvements`** | **Missing Completely** | No "Gain Metric" or "Strict Gate" to validate improvements. |
| **Memory** | Hierarchical WMR Loop (Memory Survey) | **Disjoint JSON/SQLite fragments** | **Needs Improvement** | Lack of "Consolidation" leads to retrieval noise. |
| **Behaviors** | Skill-to-LoRA (S2L) | **Hard-coded prompt heuristics** | **Missing Completely** | Prompt-based skills are token-inefficient and unstable. |
| **Governance** | Immutable Safety Gate (Reward Hacking) | **Soft-coded check methods** | **Critical Deficit** | Agents can "Self-Evaluate" their way around risk limits. |

---

## 2. The "Delusion Loop" Audit

### 2.1 RL Environment Grounding
*   **Scientific Target**: Causal World Model Induction grounded in tick-level order book dynamics.
*   **Actual Reality**: `trading_bot/core_agent_system/self_play_loop.py` uses `np.random.randn()` for price simulation.
*   **Impact**: The system is currently optimizing for Gaussian Noise. Any "Alpha" discovered in this environment is a hallucination.

### 2.2 Self-Evolution Logic
*   **Scientific Target**: Monotone-Safe updates via held-out selection (RSEA).
*   **Actual Reality**: `recursive_improvement/recursive_core.py` logs improvement proposals but fails to write or validate them against a "Gain Metric."
*   **Impact**: The system "Simulates" intelligence without actually evolving.

---

## 3. Subsystem Gap Details

### 3.1 Planning & Context
*   **Gap**: The `ReActLoop` has no mechanism for **Information Folding**.
*   **Risk**: In a long-running institutional task (e.g., a 24-hour execution), the agent will lose track of its strategic goal because the context window is filled with thousands of lines of "Tool Call" logs.

### 3.2 Knowledge & Evidence
*   **Gap**: Evidence is stored as flat JSON entries in `cds_evidence_history.jsonl`.
*   **Risk**: No **Causal Evidence Graph** exists. The agent cannot traverse "Provenance" or logically link two disparate market signals (e.g., "Yield Curve Inversion" $\to$ "Recession Hypothesis" $\to$ "Hedge Portfolio").

### 3.3 Institutional Decision Making
*   **Gap**: Decisions are heuristic-based rather than **Bayesian EV-Optimized**.
*   **Risk**: The system is prone to "LLM Overconfidence." It might execute a trade with 100% sentiment but 0% statistical calibration.

---

## 4. Summary of Required Changes

1.  **Decommission 80+ Orchestrators**: Collapse all logic into the `IntegratedAgentSystem` (CSC).
2.  **Replace Random-Simulators**: Ground all learning in real tick-data and backtest results.
3.  **Implement Folding**: Add a "Folding Operator" to the `ReActLoop`.
4.  **Parameterize Skills**: Move `SKILL.md` content into LoRA adapters (S2L).
5.  **Build the Causal World Model**: Move from JEPA-only to a full SCM (Structural Causal Model) using CWMI.
6.  **Enforce the Evolution Gate**: Implement the "Strict Keep-Better Gate" from RSEA.
