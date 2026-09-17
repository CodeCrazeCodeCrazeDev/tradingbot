# DOCUMENTATION TRACEABILITY MATRIX

Generated programmatically by `/home/jules/self_created_tools/doc_traceability.py`.

| Capability / Subsystem | Requirements Spec | Implementation File | Unit Test File | Validation File | Status | Verification |
|---|---|---|---|---|---|---|
| Cognitive System Controller | UCA V5 Specification, Cognitive System Controller Specs | `trading_bot/core/csc/controller.py` | `tests/uca_v5/test_csc_v5.py` | `tests/test_institutional_refactor.py` | implemented | verified |
| Hierarchical Memory System (SAGE) | SAGE Decomposition, Memory HMS V5 Redesign | `trading_bot/core/hms/memory.py` | `tests/uca_v5/test_hms_v5.py` | `tests/test_institutional_refactor.py` | implemented | verified |
| Unified Component Registry | Unified Component Registry specification | `trading_bot/core/unified_registry.py` | `tests/test_registry.py` | `tests/test_registry.py` | implemented | verified |
| Research OS | Research OS Spec | `trading_bot/research/research_os.py` | `tests/test_institutional_refactor.py` | `tests/test_institutional_refactor.py` | implemented | verified |
| Research Governance | Research Governance Spec | `trading_bot/research/research_governance.py` | `tests/test_institutional_refactor.py` | `tests/test_institutional_refactor.py` | implemented | verified |
