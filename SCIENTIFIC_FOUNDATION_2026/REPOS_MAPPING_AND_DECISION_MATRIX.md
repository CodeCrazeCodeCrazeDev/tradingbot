# Repository Mapping, Gap Analysis & Integration Decision Matrix
## AlphaAlgo Scientific Upgrade Portfolio (UCA-2026 / V6 Standard)

This document establishes the **Repository Mapping**, **Gap Analysis**, and **Integration Decision Matrix** for AlphaAlgo. In accordance with the strict evidence-first workflow, no subsystem remains unmapped.

---

## Part 1: Subsystem-to-Paper Mapping

Every major subsystem of AlphaAlgo is audited, mapping its current capabilities, supporting literature, and contradicting/competing papers (guaranteeing zero duplicate architectures).

### Subsystem 1: Cognitive System Controller (CSC)
- **Files**: `trading_bot/core/csc/controller.py`
- **Current Capability**: Implements a 12-stage Active Inference sequence using discrete-continuous latent state recurrence (DiscoLoop).
- **Supporting Papers**:
  - `REG-051` (Friston, 2010): Establishes the mathematical bounds for Variational Free Energy minimization.
  - `REG-001` (Quiet-STaR): Supports "think-before-speaking" quiet planning.
  - `REG-003` (Tree-of-Thought): Informs the backtracking heuristics.
- **Contradicting Papers**:
  - Naive feed-forward architectures that assert decision making without state recurrence.
- **Replacement/Improvement Candidate**: Improve reasoning backtracking loops inside `_pivot_refine_loop` using `REG-003` state-value BFS search, rather than single-shot rollouts.
- **ROI**: High.

### Subsystem 2: Skill Router (HASP & S2L)
- **Files**: `trading_bot/core/csc/router.py`
- **Current Capability**: Selects and routes strategic tasks to executable Program Functions (PFs) or Skill-to-LoRA adapters.
- **Supporting Papers**:
  - `REG-005` (Self-Discover): Composition of task-specific structures.
  - `REG-019` (Constrained Policy Optimization): Trust-region safety bounds.
- **Contradicting Papers**:
  - Unconstrained heuristic routers that violate safety bounds.
- **Improvement Opportunity**: Integrate analytical trust-region safety constraints into the router's decision vector using `REG-019` math.
- **ROI**: Medium.

### Subsystem 3: Multi-Agent Debate & Swarm Verification
- **Files**: `trading_bot/agents/multi_agent_debate.py`, `trading_bot/core/verification/swarm.py`
- **Current Capability**: Runs multi-agent debate and falsification verifiers to check proposal validity.
- **Supporting Papers**:
  - `REG-041` (Byzantine-Robust Consensus): Informs our voting algorithms.
  - `REG-017` (GRPO): Normalizes group-relative advantages.
  - `REG-031` (Let's Verify Step-by-Step): Process-based step verifiers.
- **Contradicting Papers**:
  - Naive majority vote models that suffer from Byzantine collusion.
- **Improvement Opportunity**: Implement a Byzantine fault tolerant voting threshold and group advantage normalization.
- **ROI**: High (Resolves current test scope NameErrors and unbound variables).

### Subsystem 4: Hierarchical Memory System (HMS & CMOS)
- **Files**: `trading_bot/core/hms/memory.py`, `trading_bot/core/hms/cmos.py`
- **Current Capability**: Handles SAGE evidence graphs, ontology, and episodic recall with deterministic schema integrity.
- **Supporting Papers**:
  - `REG-093` (SAGE Evidence Graph): Semantic graphs for evidential retrieval.
  - `REG-004` (Graph-of-Thoughts): Non-linear thought combinations.
- **Contradicting Papers**:
  - Naive vector search caches without semantic structure.
- **Improvement Opportunity**: Structured memory hashing and verification.
- **ROI**: Medium.

---

## Part 2: Gap Analysis (Technical Debt & Scientific Limitations)

Our recursive repository audit identified the following critical gaps, mapped strictly to research evidence:

1. **Unclosed/Duplicate Agent Definitions and String Values**
   - *Weakness*: Tests were crashing because `AgentScorecard` was missing, and Byzantine test values passed strings as TradeAction or Conviction.
   - *Evidence Mapping*: `REG-041` (Byzantine-Robust Consensus) and `REG-045` (Silent Agent Recovery) prove that a robust multi-agent system *must* dynamically unpack, validate, and recover malformed inputs.
2. **Double Event-Bus Queue Cleanup Bug**
   - *Weakness*: E2E test was throwing `ValueError: task_done() called too many times` under missing voter conditions.
   - *Evidence Mapping*: `REG-042` (Consensus under Network Partitions) proves that queue state transitions must be mathematically invariant and managed uniformly by the loop lifecycle (not individual conditional code blocks).

---

## Part 3: Integration Decision Matrix

Every proposed improvement is evaluated rigorously to prioritize high-ROI, non-redundant changes first.

| Target Subsystem | Supporting Paper IDs | Files to Change | Expected Benefit | Complexity | Engineering Risk | ROI | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Multi-Agent Debate** | `REG-041`, `REG-045` | `multi_agent_debate.py` | Resolves Byzantine value crashes & NameErrors | Low | Low | **Extremely High** | **Rank 1** |
| **Unified Event Bus** | `REG-042` | `unified_event_bus.py` | Eliminates double task_done() queue failures | Low | Low | **Extremely High** | **Rank 2** |
| **Cognitive Controller** | `REG-001`, `REG-003` | `controller.py` | Supports backtracking / self-correcting loops | Medium | Medium | **High** | **Rank 3** |
| **Skill Router** | `REG-019` | `router.py` | Analytical trust-region constraint matching | High | Medium | **Medium** | **Rank 4** |
