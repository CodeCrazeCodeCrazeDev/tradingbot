# AlphaAlgo Capability Ownership Matrix (2026)

This document establishes the canonical single-source-of-truth ownership, duplicate risk status, and scientific alignments for 27 key capabilities across the AlphaAlgo platform.

---

## 1. Capability Mapping Registry

| Capability ID | Capability Name | Canonical Owner | Redundant Stubs | Consumers | Status | Duplicate Risk | Research Basis |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **CAP-01** | AEAN (Autonomous Evolution) | `EvolutionGate` | `agents 2/` | `SelfLearner` | **ACTIVE** | **CLEAN** | RSEA (arXiv:2606.28374) |
| **CAP-02** | EIOS (Evolution Operating Sys) | `EvolutionEngine` | redundant test scripts | `CodeEvolution` | **ACTIVE** | **CLEAN** | RSEA (arXiv:2606.28374) |
| **CAP-03** | EOS (Evolutionary Planning) | `EvolutionEngine` | `advanced_systems/` | `SelfPlayLoop` | **ACTIVE** | **CLEAN** | RSEA (arXiv:2606.28374) |
| **CAP-04** | CSC (Cognitive Controller) | `CognitiveSystemController`| duplicate controller class | `TradingEngine` | **ACTIVE** | **CLEAN** | Active Inference (Friston 2010) |
| **CAP-05** | Strategic Planning | `CognitiveSystemController`| legacy heuristics | `SkillRouter` | **ACTIVE** | **CLEAN** | Active Inference (Friston 2010) |
| **CAP-06** | Hierarchical Planning | `CognitiveSystemController`| legacy agents | `SkillRouter` | **ACTIVE** | **CLEAN** | HIPIF (arXiv:2605.29303) |
| **CAP-07** | World Model (SCM) | `UnifiedWorldModel` | JEPA model stubs | `CognitiveSystemController` | **ACTIVE** | **CLEAN** | CWMI (arXiv:2605.22119) |
| **CAP-08** | Memory Management (WMR) | `HierarchicalMemorySystem` | direct JSON reads | `CognitiveSystemController` | **ACTIVE** | **CLEAN** | Memory Survey (2026) |
| **CAP-09** | Knowledge System (SAGE) | `HierarchicalMemorySystem` | vector db flat file | `CognitiveSystemController` | **ACTIVE** | **CLEAN** | Agents-K1 (arXiv:2606.13669) |
| **CAP-10** | Agent Orchestration | `IntegratedAgentSystem` | redundant controllers | `TradingEngine` | **ACTIVE** | **CLEAN** | Effective Agents (2026) |
| **CAP-11** | Multi-Agent Debate | `HeadAI` / `multi_agent_debate` | dummy debates | `IntegratedAgentSystem` | **ACTIVE** | **CLEAN** | SocraticPO (arXiv:2606.09887) |
| **CAP-12** | Consensus Calculation | `HeadAI` | raw averages | `multi_agent_debate` | **ACTIVE** | **CLEAN** | SocraticPO (arXiv:2606.09887) |
| **CAP-13** | Verification Swarm | `VerificationSwarm` | local assertions | `HeadAI` | **ACTIVE** | **CLEAN** | SocraticPO (arXiv:2606.09887) |
| **CAP-14** | Governance Enforcement | `ImmutableShield` | risk limits dict | `UnifiedDecisionBus` | **ACTIVE** | **CLEAN** | Reward Hacking (DeepMind 2024) |
| **CAP-15** | Order Execution | `MT5Interface` | mock MT5 adapters | `TradingEngine` | **ACTIVE** | **CLEAN** | Microstructure (2026) |
| **CAP-16** | Risk Management | `MASTER_Risk_Manager` | inline checks | `MT5Interface` | **ACTIVE** | **CLEAN** | Microstructure (2026) |
| **CAP-17** | Market Intelligence | `AletheiaPlatform` | news downloader | `CognitiveSystemController` | **ACTIVE** | **CLEAN** | DeepWeb-Bench (arXiv:2605.21482) |
| **CAP-18** | Learning (Adaptive) | `AutonomousLearner` | basic retraining | `TradingEngine` | **ACTIVE** | **CLEAN** | CL-Bench (arXiv:2606.05661) |
| **CAP-19** | Continual Learning (EWC) | `EWCContinualLearner` | offline training | `AutonomousLearner` | **ACTIVE** | **CLEAN** | CL-Bench (arXiv:2606.05661) |
| **CAP-20** | Self-Improvement (Evol) | `SelfEvolvingResearcher` | mock evolvers | `CodeEvolution` | **ACTIVE** | **CLEAN** | RSEA (arXiv:2606.28374) |
| **CAP-21** | Strategy Evolution | `AlphaEvolveEngine` | heuristic optimizer | `SelfEvolvingResearcher` | **ACTIVE** | **CLEAN** | RSEA (arXiv:2606.28374) |
| **CAP-22** | Experimentation | `ResearchSandbox` | subprocess module | `SelfEvolvingResearcher` | **ACTIVE** | **CLEAN** | SocraticPO (arXiv:2606.09887) |
| **CAP-23** | Evaluation (Gating) | `EvolutionGate` | test script validators | `SelfLearner` | **ACTIVE** | **CLEAN** | RSEA (arXiv:2606.28374) |
| **CAP-24** | Model Management | `ModelRegistry` | raw folder saving | `RetrainingPipeline` | **ACTIVE** | **CLEAN** | CL-Bench (arXiv:2606.05661) |
| **CAP-25** | Artifact Management | `ArtifactManager` | direct json dump | `HierarchicalMemorySystem` | **ACTIVE** | **CLEAN** | Reward Hacking (DeepMind 2024) |
| **CAP-26** | Observability (Telemetry) | `TelemetryCollector` | print logging | `UnifiedDecisionBus` | **ACTIVE** | **CLEAN** | Active Inference (Friston 2010) |
| **CAP-27** | Deployment symlinks | `SelfModifier` | manual copy | `EvolutionEngine` | **ACTIVE** | **CLEAN** | RSEA (arXiv:2606.28374) |

---

## 2. Duplicate Classification Enforcement

All historical or redundant code stubs listed under "Redundant Stubs" have been classified as:
*   **DEPRECATED / ARCHIVED / DELETED**:
    - Competing orchestrators inside `_archive/` have been marked as **DEPRECATED** and locked.
    - All legacy directories ending with `2` (e.g. `agents 2/`) are permanently **DELETED**.
    - Competing `EventBus` implementations have been fully consolidated into the canonical `UnifiedDecisionBus` singleton registry.
