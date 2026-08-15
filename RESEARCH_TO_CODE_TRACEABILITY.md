# RESEARCH_TO_CODE_TRACEABILITY.md

This document maps the verified scientific principles from the eight mandatory reference papers to their actual production implementation files in the AlphaAlgo system.

---

## 1. Traceability Matrix

| Scientific Paper | arXiv ID | Transferable Principle | Target Codebase Implementation | Verification Test File |
| :--- | :--- | :--- | :--- | :--- |
| **EKSFT** | `2605.29303` | Selective token fine-tuning using predictive entropy and KL-divergence thresholds. | `trading_bot/core/csc/acpe.py` | `tests/uca_v5/test_acpe.py` |
| **DiscoLoop** | `2607.00341` | Mixed discrete-continuous recurrence loop state tracking. | `trading_bot/core/csc/controller.py` | `tests/uca_v5/test_csc_v5.py` |
| **AutoMem** | `2607.01224` | Automated metamemory schema utility optimization based on task performance. | `trading_bot/core/hms/memory.py` | `tests/uca_v5/test_hms_v5.py` |
| **SAGE** | `2605.12061` | Dynamic outcome-driven edge weight updates and node compaction. | `trading_bot/core/hms/memory.py` | `tests/uca_v5/test_hms_v5.py` |
| **NanoResearch** | `2605.10813` | Co-evolution of skills, experience memory, and preference policy. | `trading_bot/core/csc/router.py` | `tests/uca_v5/test_router_v5.py` |
| **AutoResearchClaw** | `2605.20025` | Self-healing critique-refinement (Pivot/Refine) and multi-agent debate. | `trading_bot/core/csc/controller.py` | `tests/uca_v5/test_csc_v5.py` |
| **HASP** | `2605.17734` | Deterministic, non-bypassable Skill Program executable guardrails. | `trading_bot/core/csc/router.py` | `tests/uca_v5/test_router_v5.py` |
| **DeepWeb-Bench** | `2605.21482` | Bayesian calibration of decision confidence against true accuracy. | `trading_bot/core/csc/controller.py` | `tests/uca_v5/test_csc_contract_and_determinism.py` |

---

## 2. Explicit Scientific Mapping Records

### A. ARXIV-2605.29303 (EKSFT) Mapping
- **Extracted Principle**: Masking tokens with high entropy or high KL relative to a frozen reference model to protect model exploration.
- **Hypothesis**: Masking volatile transitions during the fine-tuning of the Adaptive Control Policy Engine (ACPE) prevents policy collapse under extreme market shifts.
- **Mechanism of Implementation**: Calculated inside `AdaptiveControlPolicyEngine.tune_policy()` dynamically. It drops policy updates for states with high transition entropy.
- **Expected Measurable Effect**: Latency remains sub-millisecond, and the policy maintains statistical stability under volatility shocks.

### B. ARXIV-2607.00341 (DiscoLoop) Mapping
- **Extracted Principle**: Maintaining a dual working memory containing discrete symbolic subgoals and continuous latent variables.
- **Hypothesis**: Dual recurrence prevents localized representation errors and logical fragmentation in multi-hop reasoning.
- **Mechanism of Implementation**: Implemented inside `CognitiveSystemController._run_active_inference()`. The discrete working memory stores regime state tokens, and the continuous state tracks portfolio drawdowns.
- **Expected Measurable Effect**: 100% logic verification rate on sequential dependency tasks.

### C. ARXIV-2607.01224 (AutoMem) Mapping
- **Extracted Principle**: Metamemory optimization using feedback to automatically update memory index schemas.
- **Hypothesis**: Systematically updating database schemas based on trade outcomes minimizes RAG retrieval overhead.
- **Mechanism of Implementation**: Implemented inside `HierarchicalMemorySystem.optimize_metamemory()`. Schema versions are incremented dynamically, and unused entities are compacted.
- **Expected Measurable Effect**: Less memory consumption and decreased retrieval overhead.

### D. ARXIV-2605.17734 (HASP) Mapping
- **Extracted Principle**: Deterministic program functions intercepting state logic.
- **Hypothesis**: Hard-coded safety guardrails prevent instruction drift and LLM overconfidence in highly volatile regimes.
- **Mechanism of Implementation**: Implemented inside `SkillRouter.route_task()` as non-bypassable executable Python trigger functions.
- **Expected Measurable Effect**: Vetoes orders immediately when risk bounds are breached, regardless of conversational advice.
