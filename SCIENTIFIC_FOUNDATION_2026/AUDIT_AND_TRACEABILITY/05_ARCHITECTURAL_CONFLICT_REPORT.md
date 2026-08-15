# Architectural Conflict Report
### Enterprise Coherence & Anti-Fragmentation Audit

This report records potential architectural conflicts found across the 1,580+ files, confirming the single strategic authority of the target platform.

## Identified Conflicts and Resolutions

### Conflict 1: Multiple Strategic Orchestrators
* **Sources:** Historical guides in `_archive/legacy_orchestrators/`, older docs in `docs/`
* **Description:** Diverse documents described a "Multi-Agent Research Swarm" acting as an independent planner/decision-maker separate from the CSC.
* **Resolution:** **DECOMMISSIONED & SUPERSEDED.** The target authoritative architecture establishes the **Cognitive System Controller (CSC)** as the absolute sole strategic orchestrator (the "One Brain"). All alternative parallel agents, orchestrators, and brains (such as legacy aamis_v3 systems) have been completely purged or archived.

### Conflict 2: Generative Prompt Code-Mutation vs. Governance Immutability
* **Sources:** MemoHarness paper (arXiv:2607.14159)
* **Description:** The paper describes mutating raw Python harness code in real-time under LLM feedback.
* **Resolution:** **REJECTED.** Production trading systems require deterministic, immutable code configurations to satisfy security, compliance, and formal verification proofs. Any parameter adjustments must reside inside type-safe schemas parameterized strictly via our **Adaptive Control Policy Engine (ACPE)**.
