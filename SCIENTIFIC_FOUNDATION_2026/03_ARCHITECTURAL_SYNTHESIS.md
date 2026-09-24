# Phase 3 & 4: Architectural Synthesis, Component Mapping & Refactoring Plan (2026)

This document specifies the unified scientific synthesis, dependency graph, migration pathway, risk analysis, and rollback strategy for AlphaAlgo UCA.

---

## 1. Phase 3 — Scientific Architectural Synthesis

AlphaAlgo synthesizes a **Unified Cognitive Architecture (UCA)** combining the strongest principles from all 8 mandatory post-2025 arXiv research papers:
*   **Cognitive Control Loop (`CognitiveSystemController`)**: Integrates **DiscoLoop** continuous-discrete recurrent channels with Variational Free Energy (VFE) state estimation.
*   **Skill & Behavioral Routing (`SkillRouter`)**: Couples **HASP** executable program function guardrail intercepts with **Skill-to-LoRA (S2L)** low-rank adapter selection.
*   **Hierarchical Memory Engine (`HierarchicalMemorySystem`)**: Unifies **SAGE** dynamic graph TD updates with **AutoMem** metamemory schema optimization.
*   **Multi-Agent Decision Governance (`MultiAgentDebateSystem`)**: Synthesizes **AutoResearchClaw** adversarial debate with Lopez de Prado DSR checks and **DeepWeb-Bench** Expected Calibration Error (ECE) bounds.
*   **Self-Evolution Gate (`EvolutionGate`)**: Enforces **EKSFT** token-entropy masking compliance and **RSEA** monotone safety gates.

---

## 2. Phase 4 — Refactoring Plan & System Architecture

### Dependency Graph

```
                   +---------------------------------------+
                   |    EvolutionGate (RSEA & EKSFT)      |
                   +-------------------+-------------------+
                                       |
                                       v
+------------------------------------+   +------------------------------------+
|  SkillRouter (HASP & S2L Routing)  |==>|  CognitiveSystemController (CSC)   |
+------------------------------------+   +-----------------+------------------+
                                                           |
                                                           v
+------------------------------------+   +------------------------------------+
| HierarchicalMemorySystem (SAGE)    |<==|  MultiAgentDebateSystem (AutoClaw) |
+------------------------------------+   +------------------------------------+
```

### Migration Pathway & Phased Implementation

1.  **Phase 4.1: Core Singletons Audit**: Verify single authoritative implementations for `CognitiveSystemController`, `SkillRouter`, `HierarchicalMemorySystem`, `MultiAgentDebateSystem`, and `EvolutionGate`.
2.  **Phase 4.2: Scientific Integration**: Refactor singletons to integrate continuous VFE state estimation, HASP guardrails, SAGE graph linking, and EKSFT compliance.
3.  **Phase 4.3: Automated System Verification**: Run system test suites to confirm zero regressions and 100% test pass rate.

### Risk Analysis & Rollback Strategy

| Risk Scenario | Probability | Impact | Mitigation Strategy | Rollback Action |
| :--- | :--- | :--- | :--- | :--- |
| High Volatility Loop Decoupling | Medium | High | HASP `volatility_guardrail` forces non-bypassable `HOLD` fallback. | Fallback to deterministic static risk limits. |
| Graph Compaction Lock Overhead | Low | Medium | SAGE graph compaction runs in asynchronous background workers. | Disable dynamic edge updates, reverting to static vector indexing. |
| Model Calibration Drift (ECE > 0.15) | Low | High | Post-hoc Platt Scaling recalibration pass triggered inline. | Revert to conservative flat position sizing. |

---

This specification satisfies Phase 3 and Phase 4 requirements and guides the implementation phase.
