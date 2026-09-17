# 🏗️ Phase 2: First-Principles Architectural Synthesis (2026)

This document presents the first-principles architectural redesign of the AlphaAlgo system. It integrates our 100-paper structural, cognitive, and safety insights into a single, cohesive, production-grade model.

---

## 1. High-Level System Architecture Layout

The consolidated scientific architecture of AlphaAlgo is structured into five distinct, non-overlapping, and decoupled layers, operating through clean interfaces and shared infrastructure:

```
+-------------------------------------------------------------------+
|                        1. GOVERNANCE LAYER                        |
|   +--------------------------+     +--------------------------+   |
|   |   IMMUTABLE SHIELD (T7)  |     |   EVOLUTION GATE (RSEA)  |   |
|   +--------------------------+     +--------------------------+   |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                      2. STRATEGIC COGNITIVE LAYER                 |
|   +-----------------------------------------------------------+   |
|   |        COGNITIVE SYSTEM CONTROLLER (CSC / "ONE BRAIN")    |   |
|   |  - Active Inference Engine (VFE Minimization Objective)    |   |
|   |  - DiscoLoop Multi-hop Cell (Continuous/Discrete Recurrent) |   |
|   |  - Subgoal Planning & Information Folding (HIPIF)         |   |
|   +-----------------------------------------------------------+   |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        3. CAPABILITY LAYER                        |
|   +--------------------------+     +--------------------------+   |
|   |   SKILL ROUTER (S2L / V6)|     |   HASP SKILL EXECUTOR    |   |
|   |  - Dynamic LoRA Mapping  |     |  - ProgramFunctions (PF) |   |
|   +--------------------------+     +--------------------------+   |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                         4. SUBSTRATE LAYER                        |
|   +--------------------------+     +--------------------------+   |
|   |  WORLD MODEL (SCM/CWMI)  |     |   HIERARCHICAL MEMORY    |   |
|   |  - Pearlian do-calculus  |     |   - SAGE Graph Memory    |   |
|   |  - Scenario Simulation   |     |   - AutoMem Metamemory   |   |
|   +--------------------------+     +--------------------------+   |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        5. INFRASTRUCTURE LAYER                    |
|   +-----------------------------------------------------------+   |
|   |            LOGACT TRANSACTIONAL SHARED-LOG EVENT BUS      |   |
|   |   - Totally ordered, high-throughput message pipelines    |   |
|   +-----------------------------------------------------------+   |
+-------------------------------------------------------------------+
```

---

## 2. Granular Architectural Subsystems

### I. Strategic Cognitive Layer (CSC)
- **Role**: The centralized executive of the system ("One Brain"), replacing legacy scattered planner agents.
- **Boundaries**: Strictly accepts normalized inputs from the environment and proposes actions. It does not access trading sockets or memory backends directly, delegating through the Event Bus.
- **Internal Mechanisms**:
  - *Variational Free Energy Loop*: Performs inference steps to update internal belief distributions $q(s)$ and selects actions that minimize expected free energy.
  - *DiscoLoop Cell*: Drives continuous-discrete state updates through recurrence steps before outputting proposals.
  - *Information Folder*: Automatically folds completed plans to conserve context.

### II. Capability Layer (Skill Router & Executor)
- **Role**: Standardized registry of executable behaviors and adapters.
- **Boundaries**: Decoupled from the CSC. It is invoked when the CSC needs to offload specialized skills or behavioral profiles.
- **Internal Mechanisms**:
  - *Skill-to-LoRA Router*: Evaluates the task's required capabilities and routes it to the highest-scoring LoRA adapter.
  - *HASP Executor*: Executes non-bypassable `ProgramFunctions` (PFs) in a restricted python sandbox.

### III. Substrate Layer (World Model & Hierarchical Memory)
- **Role**: Environmental prediction and experience management.
- **Boundaries**: Pure state machines. They accept queries and returns predictions/evidences without initiating execution or modifying system configurations.
- **Internal Mechanisms**:
  - *SCM Predictive Engine*: Uses structural equation modeling and DAG-based do-calculus to simulate future paths.
  - *SAGE (Self-Evolving Graph-Memory)*: Maintains a dynamic knowledge graph of assertions and conceptual links.
  - *AutoMem Metamemory Optimization*: A background process running reinforcement updates on SAGE edge weights from execution success rates.

### IV. Governance Layer (Shield & Evolution Gate)
- **Role**: Ultimate safety and code evolution gatekeeper.
- **Boundaries**: Completely isolated. Represents non-bypassable checkpoints that can reject trade proposals or rollback code changes.
- **Internal Mechanisms**:
  - *Immutable Shield*: Running hard deterministic safety assertions (e.g. exposure limits) on Proposed LogAct events.
  - *RSEA Evolution Gate*: Held-out out-of-sample backtesting selection to validate and commit self-improvement modifications.

---

## 3. Reusable Abstractions & Clean Interfaces

To prevent duplicated implementations and reduce complexity, the synthesized architecture enforces four canonical interfaces:

1. **`PredictiveWorldModel` (Abstract Interface)**:
   - Methods:
     - `async predict_future(observation: Dict, action: Dict) -> Dict`
     - `async simulate_intervention(observation: Dict, do_action: Dict, latent_z: Tensor) -> Dict`
2. **`SelfEvolvingMemory` (Abstract Interface)**:
   - Methods:
     - `async retrieve_evidence_chain(query: str) -> List[Evidence]`
     - `def store_ledger_entry(entry: ResearchLedgerEntry) -> None`
     - `def optimize_metamemory(feedback: List[Dict]) -> None`
3. **`CapabilityRouter` (Abstract Interface)**:
   - Methods:
     - `async route_task(task: str, context: Dict) -> SkillRouteOutcome`
     - `def register_skill(artifact: SkillArtifact) -> None`
4. **`SafetyShield` (Abstract Interface)**:
   - Methods:
     - `async validate_action(action_type: str, proposal: Dict, context: Dict) -> GovernanceReport`
