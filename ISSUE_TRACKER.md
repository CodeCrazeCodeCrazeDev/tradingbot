# ISSUE TRACKER

| ID | Title | Severity | Category | Impact | Status |
|---|---|---|---|---|---|
| SEC-001 | Unsafe `pickle` Deserialization | Critical | Security | RCE Risk | Resolved |
| SEC-004 | Unsafe `eval()` Usage | High | Security | Code Injection | Resolved |
| ARCH-001 | Competing Orchestrators | High | Architecture | Split-Brain Decisions | Resolved |
| ARCH-003 | Redundant Registry Implementations | Medium | Architecture | Confusion | Resolved |
| DATA-001 | Missing Schema Validation | Medium | Data | Corruption Risk | Resolved |
| INT-001 | "Delusion Loop" (Random Simulation) | Critical | Intelligence | Hallucinated Alpha | Resolved |
| REL-004 | Inconsistent Error Recovery | Medium | Reliability | System Instability | Resolved |

## Notes on Resolution
- **SEC-001**: Hardened python pickle deserialization inside `trading_bot/ml/online_learning.py` using `RestrictedUnpickler` restricting global loading to only safe numpy, pandas, and local modules.
- **SEC-004**: Hardened python eval/exec inside `trading_bot/security/safe_eval.py` restricting dunder attributes and unapproved functions.
- **ARCH-001 & ARCH-003**: Enforced single orchestrator and registry registry-enforcement rules inside `trading_bot/core/unified_registry.py`.
- **DATA-001**: Implemented thorough schemas validation with look-ahead/bad-tick validators inside `trading_bot/data/validate.py`.
- **INT-001**: Cleaned out random delusion loops by verifying real Active Inference and SAGE memory calculations.
- **REL-004**: Stabilized loop execution, ensuring correct trade positional arguments for rejections in `trading_bot/core/csc/controller.py`.
