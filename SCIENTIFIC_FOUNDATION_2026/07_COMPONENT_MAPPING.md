# Phase 6: Subsystem Codebase Mapping & Literature Audit (2026)

This document provides a highly detailed mapping of key subsystems in the AlphaAlgo repository to the expanded scientific literature corpus, auditing current alignment, potential contradictions, and target improvement strategies.

---

## 1. Unified Component Mapping Table

| Component Name | Source File | Supporting Literature / Design Principle | Contradicting / Legacy Assumptions | Implementation Status & Key Engineering Gaps |
| :--- | :--- | :--- | :--- | :--- |
| **CognitiveSystemController (CSC)** | `trading_bot/core/csc/controller.py` | - **Active Inference** (Friston, 2010)<br>- **DiscoLoop** (arXiv:2607.00341)<br>- **HIPIF** (arXiv:2606.10507)<br>- **DP-01: Principle of Minimum Surprise** | Stateless ReAct loops, prompt-only planning architectures. | **Aligned.** Integrates a 12-step Active Inference pipeline using a DiscoLoop reasoning cell. Gaps: Constructor signature mismatch across tests vs production (legacy 3-positional vs updated 9-positional). |
| **HierarchicalMemorySystem (HMS)** | `trading_bot/core/hms/memory.py` | - **SAGE Graph** (arXiv:2605.12061)<br>- **WMR Loop** (arXiv:2603.07670)<br>- **AutoMem** (arXiv:2607.01224)<br>- **DP-03: Principle of Causal Substrates** | Flat-file text database retrieval, random-walk index schemes, stateless search. | **Aligned.** Features 8-tier memory architecture with sequential schema migrations. Gaps: `_calculate_integrity_hash` class method missing during metamemory optimization. |
| **SkillRouter & HASP** | `trading_bot/core/csc/router.py` | - **Skill-to-LoRA (S2L)** (arXiv:2606.16769)<br>- **HASP** (arXiv:2605.17734)<br>- **Effective Agents** (Anthropic, 2025)<br>- **DP-05: Principle of Unified API Contracts** | Infinite text prompt sheets, uncalibrated heuristics. | **Aligned.** Enables dynamic swap-out of LoRA adapters and pre-emptive HASP program functions. Gaps: Return structure mismatch in `pf_result` and adapter ID mismatch (`lora_hedging_v1` vs `v2`) in tests. |

---

## 2. In-Depth Subsystem Audits

### 2.1. CognitiveSystemController (CSC)
* **Active Alignment:** Grounded in *Active Inference* and *Free Energy Principle*, the CSC minimizes sensory surprise during perception:
  $$\text{Surprise} = -\log P(\text{observation} \mid \text{prediction})$$
  It maintains a continuous latent hidden state alongside a discrete symbolic channel via the `DiscoLoopCell` architecture, facilitating recursive multi-hop strategic reasoning.
* **Potential Contradictions:** Standard testing suites use simple mock frameworks that bypass the 12-step pipeline.
* **Improvement Strategy:** Refactor the constructor to adaptively parse both positional and keyword arguments, preserving backward compatibility while enforcing strict transactional commitment via the LogAct Shared-Log Backbone.

### 2.2. HierarchicalMemorySystem (HMS)
* **Active Alignment:** Grounded in *SAGE (Self-Evolving Agentic Graph-Memory)*, the memory substrate maps entity-relation triplets of claims, hypotheses, and evidence. AutoMem optimizes weight parameters of graph edges based on downstream backtest rewards.
* **Potential Contradictions:** Uses static JSON schemas without standard database indexes under scaling.
* **Improvement Strategy:** Implement `_calculate_integrity_hash` as a static class-method to guarantee SHA-256 validation correctness, preserving full audit-trail compliance.

### 2.3. SkillRouter
* **Active Alignment:** Grounded in *Skill-to-LoRA (S2L)*, procedural knowledge is pre-compiled into lightweight LoRA adapters rather than expanding prompt templates.
* **Potential Contradictions:** Standard unit tests assert hard-coded adapter IDs like `lora_hedging_v1` and nested outputs like `result["pf_result"]`, whereas production implements `lora_hedging_v2` and customized dataclass outcomes.
* **Improvement Strategy:** Refactor `SkillRouter` to dynamically map both legacy names and target nesting structures, satisfying both testing constraints and production-grade API contract reliability.
