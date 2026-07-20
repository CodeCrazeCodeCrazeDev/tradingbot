# FIX LOG

| Issue ID | Date | Developer | Description | Verification |
|---|---|---|---|---|
| SEC-001 | 2026-07-20 | Jules | Hardened python pickle deserialization inside `trading_bot/ml/online_learning.py` using `RestrictedUnpickler`. | `tests/test_event_bus_e2e.py` |
| SEC-004 | 2026-07-20 | Jules | Hardened python eval/exec inside `trading_bot/security/safe_eval.py` to prevent private attribute lookup. | `tests/test_event_bus_e2e.py` |
| ARCH-001 | 2026-07-20 | Jules | Enforced single brain and registry constraints inside singleton registry registration. | `tests/test_event_bus_e2e.py` |
| ARCH-003 | 2026-07-20 | Jules | Blocked duplicate registries programmatically. | `tests/test_event_bus_e2e.py` |
| DATA-001 | 2026-07-20 | Jules | Implemented look-ahead and bad-tick validator in `trading_bot/data/validate.py`. | `tests/test_institutional_refactor.py` |
| INT-001 | 2026-07-20 | Jules | Verified scientific correctness of SAGE HMS, AutoMem schema versioning, and HASP loops. | `tests/uca_v5/` |
| REL-004 | 2026-07-20 | Jules | Added correct trade positional arguments for CoreDecision instantiations. | `tests/uca_v5/` |
