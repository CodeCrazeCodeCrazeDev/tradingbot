# AlphaAlgo V6 Multi-Agent Architecture Audit & Capability Ownership Matrix
*Prepared by Software Engineer Jules (2026)*

## 1. Exhaustive Subsystem Inventory

This section details the complete audit of all multi-agent files, classes, and mechanisms discovered inside the AlphaAlgo codebase.

---

### A. Core Agent Classes
* **Canonical Implementation:** `MacroStrategist`, `TacticalExecutioner`, `RiskSentinel`, `DevilsAdvocate`, `RiskProsecutor`, `OverfittingProsecutor`, `LiquidityProsecutor`, `ExecutionProsecutor`, `DataProsecutor`.
* **Path:** `trading_bot/agents/multi_agent_debate.py`
* **Alternate/Archived Implementations:** Legacy modules under `trading_bot/_archive/agents/` and `trading_bot/decision_governance/`.
* **Duplicate Risk:** Low. All active code runs on the consolidated classes inside `trading_bot/agents/`.
* **Status:** Operational.

### B. Agent Factories
* **Canonical Implementation:** `create_debate_system(config: Optional[Dict] = None) -> MultiAgentDebateSystem`.
* **Path:** `trading_bot/agents/multi_agent_debate.py`
* **Duplicate Risk:** Zero. Only one factory is defined in active code.
* **Status:** Operational.

### C. Agent Registries & Controlled Objects
* **Canonical Implementation:** `UnifiedComponentRegistry` and `ControlledObjectRegistry`.
* **Path:** `trading_bot/core/unified_registry.py` and `trading_bot/neuros_evolution/controlled_objects.py`.
* **Duplicate Risk:** Zero (Systematically audited and enforced by `test_subsystem_duplicate_audit.py`).
* **Status:** Operational.

### D. System Orchestrators
* **Canonical Implementation:** `CognitiveSystemController` (CSC).
* **Path:** `trading_bot/core/csc/controller.py`
* **Alternative/Legacy Implementations:** `HivemindOrchestratorV2` (delegates to CSC) and `AAMISMasterOrchestrator` (delegates to CSC).
* **Duplicate Risk:** Zero (Enforced by static AST-level checks in `test_no_competing_orchestrators`).
* **Status:** Operational.

### E. Task Schedulers
* **Canonical Implementation:** `CMOSScheduler` (coordinating memory compaction, garbage collection, and database compaction).
* **Path:** `trading_bot/core/hms/cmos.py`
* **Status:** Operational.

### F. Debate & Consensus Engines
* **Canonical Implementation:** `HeadAI` and `MultiAgentDebateSystem`.
* **Path:** `trading_bot/agents/multi_agent_debate.py`
* **Duplicate Risk:** Zero. Only one active debate module is defined.
* **Status:** Operational.

### G. Evidence & Verification Systems
* **Canonical Implementation:** `FalsificationGate`, `VerificationSwarm`, and the specialized verifier swarm (`RiskVerifier`, `CausalVerifier`, `LiquidityVerifier`, `RegimeVerifier`).
* **Path:** `trading_bot/agents/multi_agent_debate.py` and `trading_bot/core/verification/swarm.py`.
* **Duplicate Risk:** Zero.
* **Status:** Operational.

### H. Agent Scorecards & Evaluators
* **Canonical Implementation:** `AgentScorecard` and `DebateQualityEvaluator`.
* **Path:** `trading_bot/agents/multi_agent_debate.py`
* **Duplicate Risk:** Zero.
* **Status:** Operational.

### I. Memory Systems
* **Canonical Implementation:** `HierarchicalMemorySystem` (HMS) Consolidating SAGE (`SAGEGraphMemory`) and AutoMem (`MemoryOS`).
* **Path:** `trading_bot/core/hms/memory.py`
* **Duplicate Risk:** Zero.
* **Status:** Operational.

### J. Message Buses
* **Canonical Implementation:** `UnifiedDecisionBus` (LogAct Shared-Log Backbone).
* **Path:** `trading_bot/core/unified_event_bus.py`
* **Duplicate Risk:** Zero (Bridged from legacy `EventBus` shim).
* **Status:** Operational.

### K. Planners & World Models
* **Canonical Implementation:** `UnifiedWorldModel`, `WorldModelV3`, and `FutureSimulator`/`PlanningEngine`.
* **Path:** `trading_bot/world_model/unified_world_model.py`, `trading_bot/world_model/v3_core.py`, and `trading_bot/world_model/imagination.py`.
* **Status:** Operational.

### L. Artifact Managers
* **Canonical Implementation:** `ArtifactManager` (with HMAC signature and Restricting Pickler safelist).
* **Path:** `trading_bot/security/artifact_manager.py`
* **Status:** Operational.

### M. Self-Improvement & Governance Gates
* **Canonical Implementation:** `EvolutionGate` (`trading_bot/governance/evolution_gate.py`) and CSC's `_refine_strategy`.
* **Status:** Operational.

---

## 2. Capability Ownership Matrix

| Responsibility / Capability | Canonical Owner (Production Authority) | Active Consumer Modules | Core Dependencies | Runtime Execution Path | Tests |
|---|---|---|---|---|---|
| **System Registration** | `UnifiedComponentRegistry` | CSC, Shims, Services | `threading.Lock` | Synchronous on startup | `tests/test_uca_foundations.py` |
| **Active Inference & Orchestration** | `CognitiveSystemController` | main_trading_loop, Services | HMS, SkillRouter, WorldModel, Shield | Async process loop | `tests/uca_v5/test_csc_v5.py` |
| **Memory Persistence** | `HierarchicalMemorySystem` | CSC, debate system | `SAGEGraphMemory`, `MemoryOS` | Async read/write through | `tests/stress_hms/` |
| **Shared Logging & Events** | `UnifiedDecisionBus` | CSC, services, system-wide | PriorityQueue | Async processing task | `tests/test_logact_backbone.py` |
| **Multi-Agent Debate** | `MultiAgentDebateSystem` | CSC, StrategyService | `HeadAI`, `FalsificationGate` | Async debate call | `tests/agents/test_multi_agent_debate_fix.py` |
| **Action Admissibility** | `ImmutableShield` | CSC, risk engine | `threading.Lock` | Synchronous preflight check | `tests/test_uca_foundations.py` |

---

## 3. Strict Structural Segregation

To prevent architectural regression, the following invariants are enforced:
1. **No Duplication of Core Capabilities**: There is exactly one production authority for each critical responsibility.
2. **One Registry, One Bus, One Brain**:
   - Every registration must route through `UnifiedComponentRegistry`.
   - Every system-wide event must route through `UnifiedDecisionBus`.
   - Every strategic trading or research decision must route through `CognitiveSystemController`.
