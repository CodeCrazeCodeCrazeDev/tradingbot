# Research-to-Code Traceability System (UCA-2026)
### Traceable Chain of Evidence: Paper Mechanism -> Code Analogues & Gap Analysis

This traceability system records the rigorous mapping between scientific research papers, their underlying mathematical principles, target AlphaAlgo files, and validation experiments to prevent recurring historical failures.

---

## 1. Traceability Registry Matrix

| Research ID | Scientific Paper | Underlying Principle | Required Assumptions | Observed Empirical Evidence | Failure Conditions | AlphaAlgo Analogue & Current File | Gap | Proposed Change | Validation Experiment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REF-01** | LogAct: Enabling Agentic Reliability via Shared Logs | Byzantine State Machine Replication | Independent failure domains; reliable network transport | 100% agreement over concurrent writes in Byzantine systems | Communication round deadlock; high network partition density | `UnifiedDecisionBus` in `trading_bot/core/unified_event_bus.py` | Missing thread-safe in-place reset methods for multi-test runs | Implement thread-safe initialization lock and cleanup hooks | Concurrency test with 50 parallel proposes during simulated restart |
| **REF-02** | SAGE: A Self-Evolving Agentic Graph-Memory Engine | Temporal Difference edge learning | Markov property of contextual transitions | Convergence of edge weights to true predictive utility | Over-smoothing; graph density explosion; orphan node sprawl | `SAGEGraphMemory` in `trading_bot/core/hms/memory.py` | Graph database file remains un-compacted over long sessions | Implement programmatic node-edge compaction and pruning thresholds | Simulation of 10,000 assertions to verify target V+E compression ratio |
| **REF-03** | AutoMem: Meta-Memory Optimization | Bayesian database schema self-migration | Sufficient statistics are representative of alpha success | 95% alignment with manual human schema indexing | Schema migration lockouts; corrupt serializations | `HierarchicalMemorySystem` in `trading_bot/core/hms/memory.py` | Schema versions are static and require manual upgrade triggers | Implement sequential auto-migrations using metadata feedback loops | Validation check of migrated database states against expected hash |
| **REF-04** | HASP: Hierarchical Agentic Skill Programs with Prescriptive Guardrails | Abstract state verification under bounds | Correct modeling of environment boundary limits | Zero model safety violations under high-volatility trials | Too conservative safety bounds, creating false alarm blocks | `SkillRouter` in `trading_bot/core/csc/router.py` | Missing class-level thread safety lock for dynamic registration | Declare class-level `_lock = threading.Lock()` to prevent collision | Test runner asserting 100% fallback to hold under > 0.3 volatility |
| **REF-05** | Skill-to-LoRA: Behavioral Adapters | Low-rank weight parameter decomposition | Local parameter space captures regime-specific behaviors | 0% regression of non-target tasks | VRAM load latency swap constraints | `SkillRouter` in `trading_bot/core/csc/router.py` | Adapters are mapped dynamically but lack hot-swap pre-warming | Pre-warm regime adapters inside dedicated cache memory | Performance run measuring VRAM swap latency under regime shift |
| **REF-06** | DiscoLoop: Loops of Discrete-Continuous Reasoning | Recurrent dynamical loop stabilization | Lyapunov stability of continuous state projections | Guaranteed symbolic planning convergence | Gradient/latent hidden-state saturation under noise | `DiscoLoopCell` in `trading_bot/core/csc/controller.py` | Discrete projection limits are static; lack adaptive decay | Implement adaptive continuous-state clipping thresholds | Continuous feed test asserting sequence convergence in < 5 hops |
| **REF-07** | AutoResearchClaw: Debating Alphas | False Discovery Rate (FDR) / Lopez de Prado DSR | Sample independence; returns have stable variance | 80% out-of-sample drawdown reduction | Infinite debate loops under non-converging metrics | `_pivot_refine_loop` in `trading_bot/core/csc/controller.py` | Lack of automated alpha debate persistence for negative results | Persist rejected debate transcripts in `RESEARCH_REJECTION_LOG.md` | Execute 100-run debate studys to verify FDR and DSR thresholds |

---

## 2. Traceability Knowledge Graph

```text
(REF-01) -- [PROVIDES] --> (CAP-006: LogAct Event Bus)
(CAP-006) -- [IMPLEMENTED_IN] --> (trading_bot/core/unified_event_bus.py)
(CAP-006) -- [VERIFIED_BY] --> (tests/test_scientific_modules.py)

(REF-02) -- [PROVIDES] --> (CAP-002: SAGE Graph Memory)
(CAP-002) -- [IMPLEMENTED_IN] --> (trading_bot/core/hms/memory.py)
(CAP-002) -- [VERIFIED_BY] --> (tests/test_hms_v5.py)

(REF-03) -- [PROVIDES] --> (CAP-003: AutoMem Optimization)
(CAP-003) -- [IMPLEMENTED_IN] --> (trading_bot/core/hms/memory.py)
(CAP-003) -- [VERIFIED_BY] --> (tests/test_hms_v5.py)

(REF-04) -- [PROVIDES] --> (CAP-004: HASP Guardrails)
(CAP-004) -- [IMPLEMENTED_IN] --> (trading_bot/core/csc/router.py)
(CAP-004) -- [VERIFIED_BY] --> (tests/test_router_v5.py)

(REF-05) -- [PROVIDES] --> (CAP-005: Skill-to-LoRA routing)
(CAP-005) -- [IMPLEMENTED_IN] --> (trading_bot/core/csc/router.py)
(CAP-005) -- [VERIFIED_BY] --> (tests/test_router_v5.py)

(REF-06) -- [PROVIDES] --> (CAP-001: 12-stage Active Inference)
(CAP-001) -- [IMPLEMENTED_IN] --> (trading_bot/core/csc/controller.py)
(CAP-001) -- [VERIFIED_BY] --> (tests/test_csc_v5.py)

(REF-07) -- [PROVIDES] --> (CAP-008: Benjamini-Hochberg FDR)
(CAP-008) -- [IMPLEMENTED_IN] --> (trading_bot/reality_gates/multiple_testing_gate.py)
(CAP-008) -- [VERIFIED_BY] --> (tests/test_scientific_modules.py)
```
