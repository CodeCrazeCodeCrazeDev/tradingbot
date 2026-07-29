# ISSUE TRACKER: ALPHALGO ELITE SYSTEM
======================================

| Issue ID | Severity | Category | Description | Status | Target File | Verified |
|---|---|---|---|---|---|---|
| **AUD-001** | Critical | Ingestion | Data Init Double-Header File Corruption | **RESOLVED** | `trading_bot/data/__init__.py` | Yes |
| **AUD-002** | Critical | Broker | MT5 Interface Double-Header Syntax Error | **RESOLVED** | `trading_bot/data/mt5.py` | Yes |
| **AUD-003** | High | Validation | DataValidator Duplicate Headers & Missing Imports | **RESOLVED** | `trading_bot/data/validate.py` | Yes |
| **AUD-004** | Critical | Routing | SkillRouter File Top Syntax Corruption | **RESOLVED** | `trading_bot/core/csc/router.py` | Yes |
| **AUD-005** | High | Governance | EvolutionGate Method Duplication & Syntax Crash | **RESOLVED** | `trading_bot/governance/evolution_gate.py` | Yes |
| **AUD-006** | High | Mocking | World Model Mock MagicMock Comparison Type Error | **RESOLVED** | `trading_bot/core/csc/controller.py` | Yes |
| **AUD-007** | Medium | Ingestion | Unexpected MagicMock in Controller Quantity Selection | **RESOLVED** | `trading_bot/core/csc/controller.py` | Yes |
| **AUD-008** | High | Event Bus | Missing 'import time' in Unified Event Bus | **RESOLVED** | `trading_bot/core/unified_event_bus.py` | Yes |
| **AUD-009** | High | Strategic | CognitiveSystemController Argument Signature Mismatch | **RESOLVED** | `trading_bot/core/csc/controller.py` | Yes |
| **AUD-010** | Medium | Strategic | CognitiveSystemController Missing _instance singleton | **RESOLVED** | `trading_bot/core/csc/controller.py` | Yes |
| **AUD-011** | Medium | Testing | UnboundLocalError in Test Fixture Event Bus Controls | **RESOLVED** | `tests/uca_v5/test_csc_v5.py` | Yes |
| **AUD-012** | High | Memory | HierarchicalMemorySystem Missing Integrity Hash Method | **RESOLVED** | `trading_bot/core/hms/memory.py` | Yes |
| **AUD-013** | High | Governance | EvolutionGate Keyword Argument Crash | **RESOLVED** | `trading_bot/governance/evolution_gate.py` | Yes |
| **AUD-014** | High | Core | Synchronous Awaiting TypeError in Pivot Refine Logic | **RESOLVED** | `trading_bot/core/csc/controller.py` | Yes |
| **AUD-015** | High | Governance | Synchronous validate_evolution Calling Mismatch | **RESOLVED** | `trading_bot/governance/evolution_gate.py` | Yes |
| **AUD-016** | Medium | Core | Duplicate Keyword Argument confidence in Hypothesis Gen | **RESOLVED** | `trading_bot/core/csc/hypothesis.py` | Yes |
| **AUD-017** | Low | Namespace | Redundant 'agents 2/' Directory Namespace Pollution | **RESOLVED** | `agents 2/` | Yes |
| **AUD-018** | Low | Namespace | Redundant 'advanced_systems 2/' Directory Namespace | **RESOLVED** | `advanced_systems 2/` | Yes |
| **AUD-019** | High | Governance | Missing Protected Metric Ingestion inside RSEA Gate | **RESOLVED** | `trading_bot/governance/evolution_gate.py` | Yes |
| **AUD-020** | Medium | Core | Undefined Name 'provenance' in Controller | **RESOLVED** | `trading_bot/core/csc/controller.py` | Yes |
| **AUD-021** | Medium | Core | Double Truncated Class Definition in Unified Event Bus | **RESOLVED** | `trading_bot/core/unified_event_bus.py` | Yes |
| **AUD-022** | Medium | Threading | Unsafe Threading Singleton Locks in Memory OS | **RESOLVED** | `trading_bot/core/hms/memory.py` | Yes |
| **AUD-023** | Low | Testing | Broken Import Reference in Weekly Tests conftest | **RESOLVED** | local virtualenv | Yes |
| **AUD-024** | Medium | Core | Missing Async Safeguards in SAGE Retrieval | **RESOLVED** | `trading_bot/core/csc/controller.py` | Yes |
| **AUD-025** | Low | Routing | Duplicate ChameleonStr Declarations in Skill Router | **RESOLVED** | `trading_bot/core/csc/router.py` | Yes |
| **AUD-026** | Low | Core | Hard Threshold Fallback Volatility Logic | **RESOLVED** | `trading_bot/core/csc/router.py` | Yes |
| **AUD-027** | Low | Ingestion | Missing Logger Setup in Broker Interfaces | **RESOLVED** | `broker/broker_interface.py` | Yes |
| **AUD-028** | Low | Memory | SAGE Graphml IO Unhandled Warnings | **RESOLVED** | `trading_bot/core/hms/memory.py` | Yes |
| **AUD-029** | Medium | Governance | EKSFT compliance validation loop missing | **RESOLVED** | `trading_bot/governance/evolution_gate.py` | Yes |
| **AUD-030** | Medium | Core | AdaptiveControlPolicyEngine Fallback Bounds | **RESOLVED** | `trading_bot/core/csc/acpe.py` | Yes |
| **AUD-031** | Medium | Event Bus | Shared Log Event Queue Overfill | **RESOLVED** | `trading_bot/core/unified_event_bus.py` | Yes |
| **AUD-032** | High | Routing | S2L Adapter Mismatch between v1 and v2 | **RESOLVED** | `trading_bot/core/csc/router.py` | Yes |
