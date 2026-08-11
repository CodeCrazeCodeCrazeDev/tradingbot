# AlphaAlgo Improvement Lineage and Versioning

## 1. Lineage Philosophy
Every deployed modification, model configuration, and strategy promotion must maintain complete, uninterrupted **parent-to-child lineage**.

If a strategy is promoted or a policy is tuned, the system must be capable of tracing its origin back to the exact observation, hypothesis, experiment, and raw evidence packages that justified the change.

---

## 2. Lineage Representation

Every change is modeled as a node inside a directed acyclic lineage graph, containing:

- **Parent Version:** The ID/version of the system before modification.
- **Child Version:** The newly minted version of the system/module.
- **Derivation Path:** The explicit SRE steps traversed to validate the change.
- **Data Provenance:** MD5/SHA-256 hashes of all datasets, code diffs, and evidence packets used.
- **Actor Trace:** Identifiers of all agents, critics, and human reviewers that participated.

```
                  [Parent: v5.4.1 (Clean Baseline)]
                                │
                        (SRE 19-Step Loop)
                                │
            [Child Proposal: imp-9f82d1e2-csc (v5.4.2-shadow)]
                                │
               (Shadowing & Telemetry Verification)
                                │
               [Promoted: v5.4.2 (Production Active)]
```

---

## 3. Versioning Tree & Rollback System

### 3.1 Strict Rollback Guarantee
No production promotion is allowed without the simultaneous creation of a signed **Rollback Artifact**. The rollback artifact contains the exact backup of the parent version's codebase state and serialized metadata, guaranteeing a 100% deterministic restore path.

### 3.2 State Rollback Matrix

| Current State | Transition Trigger | Failure/Drift Event | Target Rollback Version | Rollback Latency |
| :--- | :--- | :--- | :--- | :--- |
| `SHADOW` | Telemetry drift detected | Validation failure | Immediate un-register from Shadow lane | $< 1\text{ second}$ |
| `ACTIVE` | High alpha decay / drawdowns | $5\%$ rolling 24-hr loss | Stop strategy; restore baseline parent version | $< 5\text{ seconds}$ |
| `INSTITUTIONALIZED` | Concept drift / Regime shift | Systematic failure | Demote to `SUPERSEDED` / `DEPRECATED` | Requires Level 2 review |

---

## 4. Architectural Invariant Checks
Automated system tests check the lineage graph for any anomalies:
- **Circular Lineage:** Verifying that a child version cannot act as its own ancestor.
- **Orphan Versions:** Verifying that no active strategy or policy exists without a valid parent lineage path.
- **Signature Breakage:** Any mismatch in the SHA-256 hashes of the derivation path triggers a system-wide security alert and halts active training loops.
