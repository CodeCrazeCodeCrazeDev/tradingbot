# AlphaAlgo Human Governance Model (2026)

## 1. Principles of Autonomy
Recursive self-improvement must not lead to unrestricted autonomous deployment. We define four explicit **Autonomy Levels** that govern what actions AlphaAlgo can perform autonomously, and what changes require human review and underwritten approval.

---

## 2. Autonomy Level Matrix

| Autonomy Level | Target Domains | Allowed Actions | Governance Gate | Human Role |
| :--- | :--- | :--- | :--- | :--- |
| **Level 0: Autonomous Research** | Hypothesis generation, Question formulating, Sandbox simulation, Draft code synthesis | Inspect code, generate hypotheses, propose experiments, run sandbox backtests, compile reports. | SRE Step 19, HMS T0-T7 memory | None (Fully autonomous research logging). |
| **Level 1: Autonomous with Gates** | Workflow optimization, internal testing, non-critical database tuning | Optimize non-critical code, refactor local tests, adjust RAM window size. | Immutable safety and regression gates | Passive oversight (Audit logs). |
| **Level 2: Human Approval Required** | Trading policy logic, risk/drawdown limits, strategy-selection, agent routing | Promote new models, adjust execution thresholds, deploy strategy candidates to production, alter portfolio weights. | Joint Red/Blue report, Evolutionary Gate | **Active approval required** (Signed human gate). |
| **Level 3: Permanently Protected** | Risk controls, emergency shutoff, authorization rules, provenance trackers | Propose changes for human review only. No direct modification allowed. | Constitutional safety invariants | **Ultimate authority** (No autonomous execution allowed). |

---

## 3. Human Approval Workflow (Level 2)
When a proposed improvement target resides inside the Level 2 boundary, the system automatically halts the production promotion queue and triggers the human review pipeline:

```
[Level 2 Proposed Improvement]
               ↓
    [Adversarial Verification] (Red / Blue Report)
               ↓
     [Generate Change Report] (Lineage & Evidence)
               ↓
     [Human Review Dashboard] (Trigger notification)
               ↓
        [Human Approval]  ───(REJECT)───> [Archived in Failures]
               │
           (APPROVE)
               ▼
       [Shadow Deployment] (Telemetry logging)
               ▼
     [Production Promotion]
```

---

## 4. Constitutional Constraints
The following files, properties, and values are classified as **Level 3 - Permanently Protected** and can never be autonomously modified:
- **Capital limits:** Maximum single-trade exposure, total portfolio leverage, and currency allocation ratios.
- **Emergency shutdown mechanisms:** Exchange/broker disconnection thresholds and active risk-kill triggers.
- **Audit mechanisms:** SAGE lineage database, signed Git diff metadata, and structural ledger archives in HMS.
- **Approval rules:** The contents of this document (`HUMAN_GOVERNANCE_MODEL.md`) and related safety schemas.
