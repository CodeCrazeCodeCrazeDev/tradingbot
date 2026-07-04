# Phase 6 (Part 2): Component Mapping & References

This document maps the scientific principles and implementation roadmap to specific files in the SCIENTIFIC_FOUNDATION_2026 directory and provides the final list of 16 reference papers.

---

## 1. Directory Structure Mapping

| File | Content | Scientific Source |
| :--- | :--- | :--- |
| **01_RESEARCH_SELECTION.md** | List of 16 Papers & Selection Logic | Various (Phase 1) |
| **02_RESEARCH_SYNTHESIS_MATRIX.md** | Problem-Solution-Math Matrix | All 16 Papers |
| **03_FIRST_PRINCIPLES.md** | Core Engineering Patterns | Synthesis (Phase 3) |
| **04_GAP_ANALYSIS.md** | Audit vs. Reality | Codebase Audit |
| **05_UNIFIED_ARCHITECTURE.md** | UCA-2026 Design | Synthesis (Phase 5) |
| **06_MATHEMATICAL_FOUNDATION.md** | Active Inference & Do-Calculus | Mathematical Synthesis |
| **11_MIGRATION_PLAN.md** | Roadmap, Risks, & Validation | Implementation Strategy |
| **12_REFERENCES.md** | Full Bibliography | Phase 1 Discovery |

---

## 2. Component Implementation Map (Target Files)

| UCA Component | Target Path (New Stack) | Principle |
| :--- | :--- | :--- |
| **CSC (Brain)** | `trading_bot/core/csc/controller.py` | Unified Brain / Active Inference |
| **Folding Buffer** | `trading_bot/core/csc/folding.py` | HIPIF |
| **S2L Router** | `trading_bot/core/csc/router.py` | Skill-to-LoRA |
| **SCM (World Model)** | `trading_bot/world_model/causal/scm.py` | CWMI / Do-Calculus |
| **Evidence Graph** | `trading_bot/knowledge/graph/evidence.py` | Agents-K1 |
| **Evolution Gate** | `trading_bot/governance/evolution_gate.py` | RSEA |
| **Safety Gate** | `trading_bot/governance/immutable_shield.py` | Reward Hacking Safety |

---

## 3. Final Bibliography (16 Reference Papers)

1.  **HIPIF**: *Hierarchical Planning and Information Folding for Long-Horizon LLM Agent Learning* (2026). arXiv:2606.10507.
2.  **SocraticPO**: *Policy Optimization via Interactive Guidance* (2026). arXiv:2606.09887.
3.  **Skill-to-LoRA (S2L)**: *From Using Skills to Learning Behaviors for Token-Efficient LLM Agents* (2026). arXiv:2606.16769.
4.  **Agents-K1**: *Towards Agent-native Knowledge Orchestration* (2026). arXiv:2606.13669.
5.  **Multi-Agent Transactive Memory (MATM)**: *Population-level Experience Reuse for Heterogeneous Agents* (2026). arXiv:2606.19911.
6.  **HORIZON**: *The Long-Horizon Task Mirage? Diagnosing Where and Why Agentic Systems Break* (2026). arXiv:2604.11978.
7.  **CL-Bench**: *Continual Learning Bench: Evaluating Frontier AI Systems in Real-World Stateful Environments* (2026). arXiv:2606.05661.
8.  **Self-Harness**: *AI Agents That Improve Their Own Operating Framework* (2026). arXiv:2606.07641.
9.  **RSEA**: *Recursive Self-Evolving Agents via Held-Out Selection* (2026). arXiv:2606.28374.
10. **Memory Survey**: *Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers* (2026). arXiv:2603.07670.
11. **CWMI**: *Better Decisions through the Right Causal World Model* (2025). Emergent Mind / arXiv:2509.xxxxx.
12. **Active Inference**: *Designing for Agency: Active Inference and the Free Energy Principle* (2024/2025). MIIAfrica Synthesis.
13. **Reward Hacking**: *Reward Hacking in Autonomous AI Agents That Exploit Their Own Evaluation Loop* (2026). KPSphere / Failure-First.
14. **PT-RAG**: *Parametric Knowledge Injection: Hybrid Semantic and Token-level Retrieval* (2025). arXiv:2504.xxxxx.
15. **Decision Intelligence**: *Strategic Decision Intelligence for Institutional Markets* (2025). Kinetic Consulting.
16. **Effective Agents**: *Building Effective Agents: Workflow vs. Swarm Patterns for Robust Autonomy* (2024/2025). Anthropic Best Practices.
