# Phase 6: Component Classification & Refactoring Blueprint

Categorization of all repository components according to scientific literature evidence:

| Classification | Component(s) | Scientific Literature Justification | Targeted Refactoring Action |
| :--- | :--- | :--- | :--- |
| **KEEP** | `CognitiveSystemController`, `HierarchicalMemorySystem`, `SkillRouter`, `ImmutableShield` | Grounded in Friston (2010) Active Inference, SAGE (arXiv:2605.12061), S2L (arXiv:2606.16769), HASP (arXiv:2605.17734) | Preserve core singletons and enforce thread-safe resets. |
| **REDESIGN** | `MultiAgentDebateSystem`, `BayesianDecisionEngine`, `FalsificationGate` | Grounded in AutoResearchClaw (arXiv:2605.20025), LogAct (arXiv:2605.29303), Ghahramani (2015) | Fix dictionary key syntax flaws, resolve variable scoping, and restore verifier instantiation. |
| **MERGE** | Fragmented Verifiers (`CausalVerifier`, `LiquidityVerifier`, `RegimeVerifier`, `RiskVerifier`) | Grounded in HASP (arXiv:2605.17734) and AutoResearchClaw (arXiv:2605.20025) | Consolidate into unified verification swarm pipeline under `MultiAgentDebateSystem`. |
| **REPLACE** | Legacy prompt sheets, uncalibrated heuristics | Grounded in Skill-to-LoRA (arXiv:2606.16769) | Replace static text prompts with dynamic LoRA adapter routing and program functions. |
| **REMOVE** | Duplicate sidecar databases, un-sandboxed `eval`/`exec` calls | Grounded in LogAct (arXiv:2605.29303) and Security Invariants | Purge un-sandboxed script runners and consolidate onto HMS SAGE graph substrate. |

---

# Phased Migration Plan

Phased strategy for the deployment of UCA-2026 in institutional production.

---

## 1. Stage 1: Shadow Deployment (In-Process)

Run the **Cognitive System Controller (CSC)** in a side-car container.
*   CSC receives all live data feeds.
*   CSC generates "Simulated Trades."
*   Fidelity Monitor compares CSC decisions against the Legacy system.
*   **Success Criteria**: Zero "Critical Divergence" on risk assessments.

---

## 2. Stage 2: Sandboxed Execution (Canary)

CSC is given execution authority over 5% of the total portfolio capital.
*   Execution is routed through the **Immutable Shield** (Governance Gate).
*   Any "Out of Bound" trade is automatically blocked and triggers a SocraticPO diagnostic loop.
*   **Success Criteria**: Positive **Alpha Gain** over 14 consecutive trading days.

---

## 3. Stage 3: Institutional Handover

Increase CSC capital allocation in 10% increments.
*   Continuous monitoring of the **Gain Metric** (CL-Bench).
*   Weekly "Red-Teaming" of the Governance Gate to ensure immutability.
*   **Final Action**: Decommission the 82+ redundant orchestrators and the legacy `MasterOrchestrator`.

---

## 4. Decommissioning Checklist

- [ ] Disable `master_orchestrator.py` (root).
- [ ] Delete `trading_bot/core_agent_system/master_orchestrator.py`.
- [ ] Delete all `__init__.py` files containing fragmented `Orchestrator` classes.
- [ ] Remove `np.random` from all RL scripts.
- [ ] Deprecate hard-coded `SKILL.md` files in favor of the LoRA Store.
