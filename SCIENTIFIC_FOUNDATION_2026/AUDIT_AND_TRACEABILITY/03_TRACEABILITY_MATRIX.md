# Documentation-to-Code Traceability Matrix
### Traceable Chain of Evidence: Specification -> Implementation -> Test -> Verification Result

This matrix records the rigorous traceability path for each system capability, including a structured Capability Knowledge Graph summary.

## Traceability Grid

| Capability ID | Capability Name | Target Subsystem | Implementation File | Verification Test Case | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CAP-001 | 12-stage Recursive Active Inference Loop | Cognitive System Controller (CSC) | `trading_bot/core/csc/controller.py -> class CognitiveSystemController` | `test_csc_v5.py / uca_v5_verification.py` | **Implemented** |
| CAP-002 | SAGE Self-Evolving Graph Memory | Hierarchical Memory System (HMS) | `trading_bot/core/hms/memory.py -> class SAGEGraphMemory` | `test_hms_v5.py -> test_hms_sage_graph_evolution` | **Implemented** |
| CAP-003 | AutoMem Meta-memory Versioning | Hierarchical Memory System (HMS) | `trading_bot/core/hms/memory.py -> HMS.optimize_metamemory` | `test_hms_v5.py -> test_hms_automem_optimization` | **Implemented** |
| CAP-004 | HASP Executable Guardrails | SkillRouter | `trading_bot/core/csc/router.py -> SkillRouter._pf_volatility_guardrail` | `test_router_v5.py -> test_router_hasp_routing` | **Implemented** |
| CAP-005 | Skill-to-LoRA Behavioral Adapters | SkillRouter | `trading_bot/core/csc/router.py -> SkillRouter.route_task` | `test_router_v5.py -> test_router_s2l_routing` | **Implemented** |
| CAP-006 | LogAct Shared-Log Backbone | Unified Event Bus | `trading_bot/core/unified_event_bus.py -> class UnifiedDecisionBus` | `test_logact_transactionality inside test_uca_v5_validation.py` | **Implemented** |
| CAP-007 | Deflated Sharpe Ratio (DSR) | Research OS | `trading_bot/research/quant_pipeline.py -> ResearchLab.calculate_dsr` | `test_advanced_quant_pipeline.py -> test_dsr_calculation` | **Implemented** |
| CAP-008 | Benjamini-Hochberg FDR Control | Research OS / Reality Gates | `trading_bot/reality_gates/multiple_testing_gate.py -> class MultipleTestingGate` | `test_fdr_control in test suites` | **Implemented** |
| CAP-009 | Dataset & Feature Lineage Tracking | Research OS | `trading_bot/research/research_os.py -> class DataLineageRegistry` | `test_research_governance.py -> test_meta_learning_and_platform_unification` | **Implemented** |
| CAP-010 | Adaptive Control Policy Engine (ACPE) | Cognitive System Controller (CSC) | `trading_bot/core/csc/acpe.py -> class AdaptiveControlPolicyEngine` | `test_acpe.py` | **Implemented** |

## Capability Knowledge Graph

```text
(DOC-2C367B) -- [SPECIFIES] --> (CAP-001)
(CAP-001) -- [VERIFIED_BY] --> (TEST-ADABE4)
(DOC-F3CA37) -- [SPECIFIES] --> (CAP-002)
(CAP-002) -- [VERIFIED_BY] --> (TEST-418EF3)
(DOC-27545C) -- [SPECIFIES] --> (CAP-003)
(CAP-003) -- [VERIFIED_BY] --> (TEST-D2BA7B)
(DOC-E48378) -- [SPECIFIES] --> (CAP-004)
(CAP-004) -- [VERIFIED_BY] --> (TEST-0D9BFB)
(DOC-57CF32) -- [SPECIFIES] --> (CAP-005)
(CAP-005) -- [VERIFIED_BY] --> (TEST-E37751)
(DOC-28D852) -- [SPECIFIES] --> (CAP-006)
(CAP-006) -- [VERIFIED_BY] --> (TEST-F780C4)
(DOC-FC5324) -- [SPECIFIES] --> (CAP-007)
(CAP-007) -- [VERIFIED_BY] --> (TEST-3709DC)
(DOC-1D8AA6) -- [SPECIFIES] --> (CAP-008)
(CAP-008) -- [VERIFIED_BY] --> (TEST-76A1EF)
(DOC-52B697) -- [SPECIFIES] --> (CAP-009)
(CAP-009) -- [VERIFIED_BY] --> (TEST-390CA1)
(DOC-6379F2) -- [SPECIFIES] --> (CAP-010)
(CAP-010) -- [VERIFIED_BY] --> (TEST-245311)
```
