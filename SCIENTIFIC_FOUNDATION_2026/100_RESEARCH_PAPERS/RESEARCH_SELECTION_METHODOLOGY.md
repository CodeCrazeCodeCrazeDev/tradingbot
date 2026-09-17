# 🧬 Research Selection & Novelty Gate Methodology

This document outlines the strict scientific selection criteria and automated checks used to build AlphaAlgo's 100-paper portfolio.

---

## 1. Automated Novelty Gate Filter
To protect the integrity of AlphaAlgo's scientific baseline, we enforced a strict **zero-reuse policy**. A paper is flagged as `STATUS = UNVERIFIED` and rejected if it overlaps with any previously consumed paper.

### 🚫 Filtered (Previously Consumed) Corpus
The following 38 identifiers were explicitly blacklisted from selection:
- Active Inference
- Agents-K1
- AutoMem
- AutoResearchClaw
- CL-Bench
- CW-AE-009
- CW-CA-002
- CW-MA-006
- CW-MM-003
- CW-MS-007
- CW-PF-004
- CW-RL-005
- CW-SR-010
- CW-V-008
- CW-WM-001
- CWMI
- DAPO
- DeepWeb-Bench
- DiscoLoop
- EKSFT
- Effective Agents
- HASP
- HIPIF
- HORIZON
- IW-SFT
- MATM
- Memory Survey
- NanoResearch
- PSFT
- PT-RAG
- RSEA
- Reward Hacking
- S2L
- SAGE
- Self-Harness
- Skill-to-LoRA
- SocraticPO
- Strategic DI

---

## 2. Selection Strategy by Capability Coverage
Rather than pulling papers randomly, we built a balanced research portfolio across the nine core domains of the AlphaAlgo system.

- **Intelligence Architecture**: Ensuring robust agent coordination, state isolation, and multi-agent consensus.
- **Reasoning**: Hardening step-by-step verification and process-level auditing.
- **Learning**: Optimizing reinforcement learning algorithms with entropy bounds.
- **World Models**: Ensuring causal consistency under extreme regime shifts.
- **Scientific Intelligence**: Guaranteeing monotone-safe evolution without overfitting.
- **Strategy Intelligence**: Allowing symbolic program search with hard security syntax constraints.
- **Financial Intelligence**: Utilizing tick-level OFI and microstructure signals.
- **Safety / Governance**: Mitigating specification gaming and reward hacking.
- **Systems Engineering**: Implementing thread-safe singletons and bounded latency.

---
*Generated: August 2026*
