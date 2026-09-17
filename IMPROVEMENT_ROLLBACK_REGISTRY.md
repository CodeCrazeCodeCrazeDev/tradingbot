# Improvement Rollback Registry Specification (RSI-ROLLBACK-2026)

## 1. Overview and Core Reversibility Invariant

Uncompromising system safety requires that **every single deployed improvement must be 100% reversible**. The system must retain the capability to instantaneously roll back any deployed configuration, code candidate, or parameter adjustment to its exact pre-deployment state.

The rollback mechanism (`RollbackManager` in `trading_bot/recursive_self_improvement/rollback.py`) coordinates configuration snapshotting, state restoration, and live reloading.

---

## 2. Active Rollback Registry Log

The rollback registry records every deployed version change, its pre-deployment baseline configuration file path, and its rollback recovery state.

| Rollback ID | Deployment ID | Domain Target | Snapshot File Path | Parent Commit Tag | Rollback Status | Trigger Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ROL-WM-01** | DEP-WM-20260814 | World Model | `artifacts/snapshots/wm_v1.4_config.yaml` | `git-tag-v1.4.2` | Ready | Manual / Auto |
| **ROL-RK-01** | DEP-RK-20260812 | Risk | `artifacts/snapshots/risk_v2.1_config.yaml` | `git-tag-v2.1.0` | Ready | Manual / Auto |

---

## 3. Rollback Procedures and Automated Triggers

### Automated Rollback Triggers
The rollback of a live canary or production deployment is automatically initiated within **50 milliseconds** of detecting:
1.  **Safety Violation:** Any transaction validation vetoed by the `ImmutableShield` or any attempt to alter the Safety Kernel files.
2.  **SLA Regression:** Latency threshold regression ($\ge 50\%$ increase over sandbox baseline) or thread lockouts lasting longer than **100ms**.
3.  **Realized Drawdown:** The live realized drawdown on the canary portfolio exceeding **1.5%** within any rolling 24-hour period.

### Manual Rollback Procedure
A human operator can trigger a full-system rollback at any time by executing:
```bash
python -m trading_bot.recursive_self_improvement.rollback --rollback-id ROL-WM-01
```
Upon execution, this command:
1.  Terminates active canary threads.
2.  Restores the snapshot configuration file from `Snapshot File Path`.
3.  Performs a hard reload on all system components (calling `reset()` and re-initializing the singletons).
4.  Re-attaches live market feeds to the active production version.
5.  Emits an audit log event to `audit_log.db` and the totally ordered LogAct shared transaction log.
