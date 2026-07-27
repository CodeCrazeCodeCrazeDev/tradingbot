# Unified Comparison & Conflict Analysis Matrix (V5)

This matrix maps the 28 core research papers (16 Foundation + 12 New) across AlphaAlgo's functional domains to identify synergies, overlaps, and conflicts.

## 1. Domain Mapping Matrix

| Domain | Foundation Papers (2026) | New Papers (V5 Update) | V5 Evolutionary Decision |
| :--- | :--- | :--- | :--- |
| **Planning** | HIPIF | DeepInsight | **HIPIF + DeepInsight**: Insight-aware hierarchical planning. |
| **Verification** | SocraticPO, Reward Hacking | Formal Proof Search | **Formal Verification Layer**: Shift to provable invariants. |
| **Self-Improvement**| RSEA, Self-Harness | Hyperagents, LSE | **Metacognitive Hyperagents**: Self-internalized evolution. |
| **Knowledge** | Agents-K1, PT-RAG | Quantum KG | **Quantum KG**: Replace static KGs with context-validity. |
| **Coordination** | MATM, Effective Agents | LogAct, CORAL, HyEvo | **LogAct + CORAL**: Shared-log consensus evolution. |
| **Memory** | Memory Survey | (Integrated in LogAct) | **LogAct Shared Logs**: Transactional state memory. |
| **World Model** | CWMI (Causal) | (Integrated in Hyperagents) | **SCM V5**: Causal World Model with self-refinement. |
| **Harness Opt** | Self-Harness | Meta-Harness | **Meta-Harness**: Autonomous wrapper optimization. |
| **Tool Use** | (Baseline Tools) | Meta-Harness, ReTool | **Strategic Tool Integration**: RL-trained tool selection. |
| **Efficiency** | Skill-to-LoRA (S2L) | Grow, Don't Overwrite | **Function-Preserving Growth**: Capacity expansion vs adapters. |
| **Benchmarking** | CL-Bench, HORIZON | FIRE | **Unified Suite**: Expand with Domain (FIRE) + Horizon (HORIZON). |

## 2. Capability Matrix

| Capability | Foundation Strategy | V5 Strategy (Synthesis) | Gain |
| :--- | :--- | :--- | :--- |
| **Strategic Drift** | Information Folding | Insight-Aware Folding | Higher coherence in multi-day sessions. |
| **Hallucination** | SFT/RL Alignment | Formal Invariant Checking | Zero-tolerance for logic errors. |
| **Regime Shift** | Causal Induction | Context-Sensitive QKG | Elimination of regime-based evidence noise. |
| **Self-Modification** | Outer-loop Prompting | Metacognitive Code-rewrite | Faster, deeper self-optimization. |
| **Reliability** | Exception Handling | Shared-Log Consensus | Guaranteed state recovery / transactional safety. |
| **Learning** | Passive RAG | Trained Evolution Policy | Online adaptation as a first-class skill. |

## 3. Missing Capability Analysis

Despite 28 papers, the following gaps are identified for AlphaAlgo V5:
1. **Multi-Asset Synchronization**: Most papers focus on single-task/domain. V5 needs explicit cross-asset causal modeling.
2. **Latency-Aware Planning**: Synthesis focuses on "correctness"; production requires "speed-correctness" trade-offs (E.g., HFT-aware reasoning).
3. **Institutional Auditability**: While LogAct provides logs, V5 needs a "Human-in-the-loop" transparency layer for the Hyperagent's meta-modifications.
