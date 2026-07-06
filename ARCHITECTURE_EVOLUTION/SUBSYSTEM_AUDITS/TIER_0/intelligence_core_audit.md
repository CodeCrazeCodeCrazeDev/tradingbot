# Subsystem Audit: intelligence_core

## 1. Scientific Audit
- **Purpose**: Self-auditing quant research lab, hypothesis generation and testing.
- **Architecture**: Orchestrator-based (missing ResearchOrchestrator file), agent army (60 agents).
- **Algorithms**: Hypothesis testing, adversarial hardening, structural memory.
- **Strengths**: Specialized agents, focus on hypothesis quality over model quality.
- **Weaknesses**: Missing core files (ResearchOrchestrator), redundancy with other research/learning modules.
- **Technical Debt**: Fragmentation into many small files without clear coordination.
- **Duplication**: Overlaps with `research_lab`, `research`, `learning`.
- **Scientific Gaps**: Lacks formal integration with Active Inference; hypothesis engine is separate from World Model V3.

## 2. One Brain Compliance
- **CSC Integration**: NO.
- **HMS Integration**: NO (uses `structural_memory.py` locally).
- **Decision Bus Integration**: NO.
- **Immutable Shield Integration**: NO.

## 3. Decision
- **Decision**: REFACTOR & MERGE
- **Justification**: Logic should be integrated as "Research Skills" within the CSC and HMS tiers. The Agent Army should be registered in the Unified Component Registry.
