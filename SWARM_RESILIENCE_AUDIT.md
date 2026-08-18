# SWARM & COLLUSION RESILIENCE AUDIT
**AlphaAlgo Evidence-Lineage Aware Consensus Architecture (UCA-2026)**
**Status:** FACT & EVIDENCE AUDIT
**Date:** 2026-03-30

---

## 1. INDEPENDENCE-AWARE CONSENSUS PRINCIPLES

[FACT] Traditional multi-agent systems assume `majority = truth` or `consensus = correctness`. In adversarial swarm scenarios, multiple colluding agents or agents relying on the same poisoned memory item render simple agent voting useless.
[PROPOSED DESIGN] AlphaAlgo replaces raw agent vote counting with **Evidence-Lineage Aware Consensus**.

### Key Distinction Matrix:
1. **Agent Agreement:** Number of distinct agent votes cast for a proposal.
2. **Evidence Agreement:** Number of supporting observation claims.
3. **Evidence Independence:** Number of distinct root observation IDs.
4. **Model Independence:** Diversity of model architectures/families contributing to reasoning.
5. **Source Independence:** Diversity of external data sources/tools providing raw signals.
6. **Reasoning Independence:** Diversity of argument paths and prompt paths.
7. **Lineage Independence:** Complete separation of evidence, memory, model, and prompt lineage.

*Invariant:* 5 agents deriving their conclusion from 1 poisoned memory item MUST be evaluated as **1 evidence lineage**, NOT 5 independent votes.

---

## 2. DIVERSITY & CORRELATION METRICS

[PROPOSED DESIGN] Consensus weight $W(C)$ for a debate outcome $C$ is calculated as:

$$W(C) = \sum_{l \in 	ext{Lineages}(C)} \operatorname{DiversityScore}(l) 	imes \operatorname{Confidence}(l)$$

Where $	ext{Lineages}(C)$ is the set of unique root evidence lineages. Colluding agents sharing the same `evidence_refs` or parent memory IDs are collapsed into a single lineage $l$, preventing "echo amplification" and false consensus attacks.

---

## 3. ADVERSARIAL SWARM TEST SCENARIOS

[PROPOSED DESIGN] The test suite validates resilience against:
- **2-3 Colluding Agents:** Colluding agents submit identical claims based on 1 shared memory item.
- **Majority Collusion (e.g. 4/5 agents compromised):** Compromised majority attempts to pass falsified proposal; rejected due to single evidence lineage.
- **Minority Byzantine Agents:** Byzantine agents submit conflicting noise; filtered via BFT evidence scoring.
- **Echo Amplification:** Agent A -> Memory -> Agent B -> Memory -> Agent C propagation collapsed to 1 lineage.
- **Sybil Agent Identities:** Creation of multiple agent instances sharing underlying model/prompt ancestry evaluated as low diversity.
