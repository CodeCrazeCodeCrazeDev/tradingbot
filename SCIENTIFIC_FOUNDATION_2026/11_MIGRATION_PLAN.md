# Phase 6 (Part 5): Migration Plan

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
