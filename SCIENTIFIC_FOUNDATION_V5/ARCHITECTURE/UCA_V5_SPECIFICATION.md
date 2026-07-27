# UCA V5 Architecture Specification (July 2026)

This document specifies the authoritative Unified Cognitive Architecture (UCA) V5, synthesized from 24 high-impact research papers.

## 1. Core Principles
- **One Brain**: A single strategic authority (CSC) governs all system actions.
- **Transactional Reliability**: All actions are serialized into an immutable Shared-Log Backbone (LogAct).
- **Evidence-First Memory**: Self-evolving graph memory (SAGE) with context-dependent validity (QKG).
- **Executable Skills**: Prompt-based skills are replaced by executable state-action programs (HASP).

## 2. Component Implementation Status

| Component | Status | Implementation File |
| :--- | :--- | :--- |
| **LogAct Backbone** | ACTIVE | `trading_bot/core/unified_event_bus.py` |
| **Immutable Shield Voter** | ACTIVE | `trading_bot/core/immutable_shield.py` |
| **SAGE Graph Memory** | ACTIVE | `trading_bot/core/hms/memory.py` |
| **CSC Active Inference** | ACTIVE | `trading_bot/core/csc/controller.py` |
| **HASP Skill Router** | ACTIVE | `trading_bot/core/csc/router.py` |

## 3. Consensus & Safety
UCA V5 utilizes a veto-based consensus model. Actions proposed to the Shared-Log are audited by registered Voters (Shield, Swarm). An action only transitions to 'APPROVED' if no voter issues a 'VETO' or 'BLOCKED' decision.
