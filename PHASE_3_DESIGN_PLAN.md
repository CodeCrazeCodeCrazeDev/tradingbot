# Phase 3 Design Plan: AlphaAlgo Hardening & Validation

## 1. Safety & Governance Architecture

### 1.1 Improvement Gatekeeper
- **Location:** `trading_bot/core/improvement/gatekeeper.py`
- **Design:** A deterministic validation engine that intercepts every `ImprovementRecord`.
- **Validation Criteria:**
    - **Code:** Syntax check, complexity check (max 15), and mandatory unit test pass.
    - **Models:** Latent stability must not degrade > 5% vs production.
    - **Strategies:** Backtest required with realistic costs (Sharpe > 1.2, DD < 15%).

### 1.2 Shadow Deployment System
- **Location:** `trading_bot/core/deployment/shadow.py`
- **Design:** Enables side-by-side execution of a `ShadowCandidate` against the `Production` model.
- **Workflow:**
    1. `MTASH` receives market data.
    2. Calls `Production.think()` (Trade-enabled).
    3. Calls `ShadowCandidate.think()` (Monitoring-only).
    4. Records performance Delta.
    5. Promotion occurs after 100 samples if Shadow ROI > Production ROI.

### 1.3 Rollback System
- **Location:** `trading_bot/core/deployment/rollback.py`
- **Design:** Git-like versioning for system weights and configuration.
- **Components:** `StateSnapshot` (Weights + Config + Performance Metrics), `RollbackRegistry`.

---

## 2. Unified Swarm Intelligence (USIS) Integration

- **Micro Layer:** Lightweight agents detecting anomalies and local patterns.
- **Expert Layer:** Heavyweight agents (Quant, Macro, Risk) using the upgraded WorldModel.
- **Consensus Controller:**
    - Uses **Historical Accuracy Weighting** (decaying average of last 30 days).
    - Implements **Disagreement Veto**: If Quant and Risk agents disagree > 80%, force a `HOLD`.

---

## 3. Risk Analysis

| Risk | Impact | Mitigation Strategy |
|------|--------|---------------------|
| **Autonomous Rollback Loops** | System instability / Version oscillation | Implement a "Rejected Version Cache" (Merkle Proof) to prevent re-promoting failed logic. |
| **Shadow Divergence** | Inaccurate validation of recurrent models | State Re-anchoring: Periodically sync the Shadow model's internal hidden state with Production state. |
| **Data Leakage in GP Loop** | Over-optimistic alpha discovery | "Wait-and-Verify" validation: Discovered equations are held in purgatory for 24h of real-time data before promotion. |

---

## 4. Validation Criteria (Phase 3)

1. **Architecture:** No legacy services (agents, agents2, old ai) should appear in `ServiceRegistry.get_status()`.
2. **Intelligence:** IB-WorldModel must show > 15% reduction in latent drift during simulated noise injection.
3. **Trading:** Symbolic alpha must maintain > 70% of IS performance during OOS testing.
4. **Safety:** All autonomous code modifications must be blocked if `pytest` fails.

---
**Status:** Initializing Phase 3.1.
