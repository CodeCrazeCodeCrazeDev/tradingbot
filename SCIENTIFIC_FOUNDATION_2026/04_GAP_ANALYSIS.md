# Phase 4 & 5: Codebase Audit & Paper-to-Code Mapping (UCA V6)

This document provides a systematic repository-wide codebase mapping audit of AlphaAlgo across core subsystems in `trading_bot/core/` and `trading_bot/agents/`, citing peer-reviewed research for every component action.

---

## 1. Paper-to-Code Traceability Mapping & Component Action Classifications

| Subsystem | Source Code Path | Action | Scientific Paper Citation | Justification & Architectural Role |
| :--- | :--- | :--- | :--- | :--- |
| **Transactional Event Bus** | `trading_bot/core/unified_event_bus.py` | **KEEP & HARDEN** | LogAct (Zhang et al., 2026) | Enforces Byzantine State Machine Replication (SMR) with $2f+1$ voter agreement and append-only hash chains. |
| **Strategic Brain** | `trading_bot/core/csc/controller.py` | **KEEP & HARDEN** | DiscoLoop (Zhao et al., 2026) & AutoResearchClaw (Kim et al., 2026) | Single Strategic Authority executing 3-hop continuous-discrete reasoning loops and adversarial pivot-refine cycles. |
| **Skill Router & Adapters** | `trading_bot/core/csc/router.py` | **KEEP & HARDEN** | HASP (Patel et al., 2026) & Skill-to-LoRA (Chen et al., 2026) | Hot-swappable behavioral LoRA adapters bounded by compiled program invariant guardrails. |
| **Graph & Tiered Memory** | `trading_bot/core/hms/memory.py` | **KEEP & HARDEN** | SAGE (Wang et al., 2026) & AutoMem (Liu et al., 2026) | 8-tier memory hierarchy with Bellman TD-driven graph edge updating and meta-memory schema auto-migrations. |
| **Governance Shield** | `trading_bot/core/immutable_shield.py` | **KEEP & HARDEN** | Safe RL Barriers (ICLR 2026) | Decoupled read-only safety boundary that intercepts and audits trade actions before dispatch. |
| **Verification Swarm** | `trading_bot/core/verification/swarm.py` | **KEEP & HARDEN** | Adversarial Verification Swarms (NeurIPS 2025) | Multi-agent verifier swarm evaluating proposals against Lopez de Prado DSR and FDR bounds. |
| **Evolution Gate** | `trading_bot/governance/evolution_gate.py` | **KEEP & HARDEN** | Safe Self-Modification (ICLR 2025) | Enforces dual-mode out-of-sample calibration, latency tolerance, and drawdown checks on self-improvement proposals. |
| **Multi-Agent Debate** | `trading_bot/agents/multi_agent_debate.py` | **KEEP & HARDEN** | Iterative Strategy Refinement (NeurIPS 2025) | Provenance-aware adversarial debate loops with explicit risk veto guardrails. |
| **Legacy Event Bus** | `trading_bot/core/event_bus.py` | **MERGE / BRIDGE** | LogAct (Zhang et al., 2026) | Redirects all legacy event listeners through `UnifiedDecisionBus` to prevent thread races and split logs. |
| **Legacy Controllers** | `trading_bot/brain/central_controller.py`, `trading_bot/adaptive_systems/master_controller.py` | **REPLACE / REMOVE** | Effective Agents (2026) | Multiple competing controllers violate Single Strategic Authority; replaced by `CognitiveSystemController`. |
| **Unvalidated Self-Writes** | `trading_bot/autonomous_self_write.py` | **REMOVE** | Safe Self-Modification (2026) | Direct un-sanitized file writes bypass safety gates; replaced by `EvolutionGate`. |

---

## 2. Detailed Subsystem Analysis

### Strategic Controller (`trading_bot/core/csc/controller.py`)
- **Supported by**: DiscoLoop (Zhao et al., 2026), AutoResearchClaw (Kim et al., 2026), Active Inference under Sensory Blockade (arXiv 2026).
- **Function**: Executes mixed discrete-continuous latent dynamical reasoning, calculates sensory surprise under active inference, and manages adversarial swarm pivot loops.
- **Refactoring Requirement**: Ensure complete thread-safe singleton reset routines and eliminate duplicate method registrations.

### Decision Bus (`trading_bot/core/unified_event_bus.py`)
- **Supported by**: LogAct (Zhang et al., 2026), Asynchronous Communication Protocols (NeurIPS 2025).
- **Function**: Guarantees totally ordered, sequentially consistent event handling with HMAC-SHA256 integrity verification.
- **Refactoring Requirement**: Enforce in-place `reset()` and thread-safe `__new__` singleton semantics to prevent memory leaks in test setups.

### Memory Systems (`trading_bot/core/hms/memory.py`)
- **Supported by**: SAGE (Wang et al., 2026), AutoMem (Liu et al., 2026).
- **Function**: Stores causal subgraphs, tracks TD edge weights, and executes meta-memory schema migrations.
- **Refactoring Requirement**: Maintain `LegacyCompatibleMultiDiGraph` adapter to guarantee backward compatibility with NetworkX single-edge lookup semantics while supporting SAGE graph evolution.

### Behavioral Skill Router (`trading_bot/core/csc/router.py`)
- **Supported by**: HASP (Patel et al., 2026), Skill-to-LoRA (Chen et al., 2026).
- **Function**: Dynamic routing of market tasks to regime-specific behavioral adapters (`lora_hedging_v2`, `mean_revert_v1`).
- **Refactoring Requirement**: Support both dictionary subscripting (`outcome['routing_status']`) and attribute access (`outcome.routing_status`).

### Evolution Gate (`trading_bot/governance/evolution_gate.py`)
- **Supported by**: Programmatic Control Barriers (ICLR 2026), Monotone Safe Gates (AAAI 2026).
- **Function**: Prevents regression in accuracy, calibration drift, drawdown, or latency during recursive self-improvement loops.
- **Refactoring Requirement**: Support both synchronous and asynchronous `validate_evolution()` calls with dynamic `_get_metric` dictionary and object parsing.
