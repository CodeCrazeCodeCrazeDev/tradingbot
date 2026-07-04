# Codebase Mapping & Architectural Audit: AlphaAlgo (2026)

This document maps the verified scientific principles to the AlphaAlgo codebase and identifies the specific gaps to be addressed during refactoring.

---

## 1. Scientific Mapping Matrix

| Research Paper/Topic | Engineering Principle | Target Codebase Subsystem | Status |
| :--- | :--- | :--- | :--- |
| **HIPIF** | Information Folding | `trading_bot/core_agent_system/react_loop.py` | **Missing**: Context is infinite-append; no folding operator. |
| **SocraticPO** | Interactive Guidance | `trading_bot/core_agent_system/self_play_loop.py` | **Missing**: Scalar rewards only; no diagnostic teacher. |
| **Skill-to-LoRA** | Behavioral LoRA | `trading_bot/core_agent_system/tool_registry.py` | **Missing**: Prompt-based skills only; no LoRA routing. |
| **Agents-K1** | Causal Evidence Graph | `trading_bot/core_agent_system/cds/evidence_graph.py`| **Incomplete**: Basic graph exists; lacks causal/multihop logic. |
| **MATM** | Transactive Memory | `trading_bot/core_agent_system/memory_system.py` | **Missing**: Isolated agent memory; no population-level reuse. |
| **HORIZON** | Failure Attribution | `trading_bot/core/validation.py` | **Missing**: No systematic failure-type mapping. |
| **CL-Bench** | Gain Metric | `trading_bot/core/validation.py` | **Missing**: No comparison against stateless baseline. |
| **Self-Harness** | Harness Optimization | `trading_bot/core_agent_system/tool_registry.py` | **Missing**: Static tool definitions; no self-optimization. |
| **RSEA** | Monotone-Safe Gate | `trading_bot/_archive/recursive_improvement/` | **Stubbed**: Implementation in `recursive_core.py` is incomplete. |
| **CWMI** | Causal World Model | `trading_bot/world_model/` | **Needs Redesign**: Currently correlational; needs SCM/Do-calculus. |
| **Active Inference** | VFE Objective | `trading_bot/core_agent_system/integrated_system.py` | **Missing**: No unified variational objective. |
| **Reward Hacking** | Immutable Shield | `trading_bot/core_agent_system/governance_system.py` | **Fragmented**: Multi-layer checks exist but are bypassable. |
| **Strategic DI** | Bayesian EV | `trading_bot/core_agent_system/cds/` | **Needs Improvement**: Decision logic lacks calibration/EV optimization. |
| **Effective Agents** | Workflow Patterns | `trading_bot/core_orchestrator.py` | **Violated**: 82+ orchestrators create a "Swarm Mirage." |

---

## 2. Identified High-Priority Defects

### 2.1 The "Delusion Loop" (Scientific Failure)
*   **Location**: `trading_bot/core_agent_system/self_play_loop.py`
*   **Audit**: Uses `np.random.randn()` for price, momentum, and outcomes.
*   **Requirement**: Replace Gaussian noise with high-fidelity backtest replays and real market observations.

### 2.2 The Orchestration Explosion (Architectural Fragmentation)
*   **Location**: Entire repository (260+ orchestrator references).
*   **Audit**: Massive redundancy (e.g., `SafeOrchestrator`, `AnalysisOrchestrator`, `MasterOrchestrator`, `MetaOrchestrator`).
*   **Requirement**: Collapse every orchestrator into the `IntegratedAgentSystem` (CSC).

### 2.3 Stubbed Self-Improvement (Implementation Gap)
*   **Location**: `trading_bot/_archive/recursive_improvement/recursive_core.py`
*   **Audit**: `_apply_improvements` and `_measure_performance` are placeholders.
*   **Requirement**: Implement the RSEA "Strict Gate" and Socratic feedback loops.

### 2.4 Context-Window Rot (Strategic Drift)
*   **Location**: `trading_bot/core_agent_system/react_loop.py`
*   **Audit**: No mechanism for Information Folding (HIPIF).
*   **Requirement**: Implement a `FoldingOperator` to compress history every $N$ steps or upon subgoal completion.

---

## 3. Redundant Components for Decommissioning

1.  `trading_bot/core/orchestrator.py` (Redundant)
2.  `trading_bot/core/safeorchestrator.py` (Redundant)
3.  `trading_bot/core/analysis_orchestrator.py` (Redundant)
4.  `trading_bot/core_agent_system/meta_orchestrator.py` (Redundant)
5.  `trading_bot/core_agent_system/self_coordinating_core.py` (Redundant)
6.  `trading_bot/core_agent_system/coordination_core.py` (Redundant)
7.  `trading_bot/world_model/simulation_orchestrator.py` (Redundant)
