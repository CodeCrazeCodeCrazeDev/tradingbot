# AUTHORITY AND TRUST-BOUNDARY DISCOVERY MAP
**AlphaAlgo Security & Governance Authority Mapping (UCA-2026)**
**Status:** FACT & EVIDENCE AUDIT
**Date:** 2026-03-30

---

## 1. EXECUTIVE SUMMARY & DISCOVERY METHODOLOGY

[FACT] This discovery document provides a complete repository-wide audit of all capability management, security enforcement, governance, memory, risk, and execution mechanisms in AlphaAlgo.
[EVIDENCE] Analyzed all active non-archived Python code files across `trading_bot/core`, `trading_bot/agents`, `trading_bot/governance`, `trading_bot/risk`, `trading_bot/security`, and `trading_bot/systems_ai`.
[INFERENCE] Prior to consolidation, the codebase contained fragmented authorities across memory storage, risk calculation, agent lifecycle, and governance gates.
[PROPOSED DESIGN] Define exact, non-bypassable single enforcement authorities for every security-sensitive operation across the 21 capability domains.

---

## 2. CAPABILITY-BY-CAPABILITY AUTHORITY ANALYSIS

### 1. Agent Identity
- **OWNER:** `trading_bot/agents/multi_agent_debate.py::TradingAgent` & `AgentRole`
- **CALLERS:** `HivemindAgentManager`, debate protocols, strategic swarms.
- **MUTATION PATHS:** Set during `TradingAgent.__init__(name, role, system_prompt, capabilities)`.
- **TRUST BOUNDARY:** In-process Python object initialization.
- **BYPASS PATHS:** Direct instantiation of `TradingAgent` without registration in `HivemindAgentManager`; string spoofing in `AgentArgument.agent_name`.
- **DUPLICATE AUTHORITIES:** `trading_bot/intelligence_core/agent_army.py::Agent`, `trading_bot/foundation_agents/multi_agent/agent_swarm.py::Agent`.
- **FAILURE MODE:** Identity spoofing, impersonation across debate rounds.

### 2. Agent Registration
- **OWNER:** `trading_bot/agents/multi_agent_debate.py::HivemindAgentManager`
- **CALLERS:** Initialization scripts, orchestration loops.
- **MUTATION PATHS:** `register_agent(agent: TradingAgent)`.
- **TRUST BOUNDARY:** Local dictionary mapping in `self.agents`.
- **BYPASS PATHS:** Agents can be created directly and pass arguments to `synthesize_decision()` without registering in `HivemindAgentManager`.
- **DUPLICATE AUTHORITIES:** `trading_bot/core/service_registry.py::ServiceRegistry`, `trading_bot/system_registry.py::SystemRegistry`.
- **FAILURE MODE:** Unregistered agent execution, shadow agent execution.

### 3. Capability Assignment
- **OWNER:** `trading_bot/agents/multi_agent_debate.py::TradingAgent.capabilities`
- **CALLERS:** `TradingAgent.__init__`, strategy planners.
- **MUTATION PATHS:** `capabilities: Set[str]` assigned at init or mutated directly via `agent.capabilities.add(...)`.
- **TRUST BOUNDARY:** In-memory set attribute.
- **BYPASS PATHS:** Direct dictionary or attribute mutation; capability check omitted in execution loops.
- **DUPLICATE AUTHORITIES:** `trading_bot/foundation_agents/multi_agent/agent_swarm.py::AgentCapability`.
- **FAILURE MODE:** Unauthorized capability escalation, privilege confusion.

### 4. Authorization
- **OWNER:** `trading_bot/core/immutable_shield.py::ImmutableShield`
- **CALLERS:** `CognitiveSystemController`, execution manager.
- **MUTATION PATHS:** `validate_action(action, context)` returns `GovernanceDecision`.
- **TRUST BOUNDARY:** Singleton check gate.
- **BYPASS PATHS:** Direct execution calls to broker connectors bypassing `ImmutableShield`; mock shield objects in test fixtures.
- **DUPLICATE AUTHORITIES:** `trading_bot/governance/production_gate.py::ProductionAcceptanceGate`, `trading_bot/gets/core/governance_promotion.py::GovernancePromotionLayer`.
- **FAILURE MODE:** Non-compliant order authorization, unverified trade submission.

### 5. Inter-Agent Messaging
- **OWNER:** `trading_bot/core/unified_event_bus.py::UnifiedDecisionBus`
- **CALLERS:** `CognitiveSystemController`, debate agents, event listeners.
- **MUTATION PATHS:** `publish(event: UnifiedEvent)`, `publish_decision(...)`.
- **TRUST BOUNDARY:** Priority queue and pub/sub subscriber list in-memory.
- **BYPASS PATHS:** Direct function calls between agents (`agentA.interact(agentB)`); unauthenticated `DebateRound` argument lists.
- **DUPLICATE AUTHORITIES:** `trading_bot/core/event_bus.py::EventBus`, `trading_bot/foundation_agents/multi_agent/agent_swarm.py::AgentMessage`.
- **FAILURE MODE:** Message replay, message forgery, unauthorized cross-talk.

### 6. Persistent Memory
- **OWNER:** `trading_bot/core/hms/memory.py::HierarchicalMemorySystem`
- **CALLERS:** `CognitiveSystemController`, research agents, market observers.
- **MUTATION PATHS:** `store_memory()`, `save()`, SQLite/JSON persistence.
- **TRUST BOUNDARY:** Local filesystem storage paths (`temp_hms/`, `alpha_brain_memory.db`).
- **BYPASS PATHS:** Direct writes to SQLite databases (`alpha_brain_memory.db`, `perplexity_trading_memory.db`); direct dictionary manipulation in `TradingAgent.private_memory`.
- **DUPLICATE AUTHORITIES:** `trading_bot/foundation_agents/cognitive_core/memory_system.py::MemorySystem`, `trading_bot/intelligence_core/structural_memory.py::StructuralMemory`.
- **FAILURE MODE:** Poisoned memory injection, unverified knowledge persistence.

### 7. Memory Promotion
- **OWNER:** `trading_bot/core/hms/memory.py::SAGEGraphMemory` & `HierarchicalMemorySystem`
- **CALLERS:** Strategic reasoners, knowledge consolidation loops.
- **MUTATION PATHS:** `add_evidence()`, `consolidate_working_memory()`.
- **TRUST BOUNDARY:** Internal graph density and edge weight calculations.
- **BYPASS PATHS:** Direct graph edge addition (`graph.add_edge(...)`); repetition of unverified claims across agents ("echo amplification").
- **DUPLICATE AUTHORITIES:** `trading_bot/_archive/aamis_v3/superintelligence/memory_systems.py::MemoryConsolidation`.
- **FAILURE MODE:** False consensus promotion, persistent echo amplification.

### 8. Provenance
- **OWNER:** `trading_bot/agents/multi_agent_debate.py::ProvenanceDataSchema`
- **CALLERS:** `synthesize_decision()`, `RiskVerifier`, debate auditors.
- **MUTATION PATHS:** `ProvenanceDataSchema` dataclass instantiation during debate synthesis.
- **TRUST BOUNDARY:** Cryptographic hash generation in `_compute_hash()`.
- **BYPASS PATHS:** Missing provenance checks on raw memory retrievals; incomplete evidence references in decision logs.
- **DUPLICATE AUTHORITIES:** `COGNITIVE_PROVENANCE.md` (documentation-only), `trading_bot/gets/core/governance_promotion.py::AuditTrail`.
- **FAILURE MODE:** Unattributable decision synthesis, loss of falsification history.

### 9. Governance
- **OWNER:** `trading_bot/governance/evolution_gate.py::EvolutionGate`
- **CALLERS:** `SelfImprovementLoop`, model promotion pipelines, strategy optimization.
- **MUTATION PATHS:** `validate_evolution(candidate_id, candidate_config, baseline_config)`.
- **TRUST BOUNDARY:** Metric evaluation logic comparing candidate vs. baseline.
- **BYPASS PATHS:** Direct update of configuration files; overriding threshold arguments in local function calls.
- **DUPLICATE AUTHORITIES:** `trading_bot/intelligence_core/governance.py::GovernanceLayer`, `trading_bot/governance.py::GovernanceManager`.
- **FAILURE MODE:** Unauthorized self-evolution, benchmark gaming, metric manipulation.

### 10. Risk Authorization
- **OWNER:** `trading_bot/risk/MASTER_risk_manager.py::MasterRiskManager` & `trading_bot/risk/unified_risk_manager.py::UnifiedRiskManager`
- **CALLERS:** `CognitiveSystemController`, order execution pipelines.
- **MUTATION PATHS:** `assess_risk()`, `calculate_position_size()`, `check_portfolio_risk()`.
- **TRUST BOUNDARY:** In-code hardcoded risk thresholds and account metrics.
- **BYPASS PATHS:** Calling `UnifiedRiskManager` instead of `MasterRiskManager` or vice versa; mock risk managers (`MockRiskManager`) left active in execution contexts.
- **DUPLICATE AUTHORITIES:** `trading_bot/risk/unified_risk_manager.py`, `trading_bot/risk/MASTER_risk_manager.py`, `trading_bot/risk/advanced_risk_manager.py`.
- **FAILURE MODE:** Dual-authority divergence, unhedged leverage exposure, black swan vulnerability.

### 11. Execution Authorization
- **OWNER:** `trading_bot/core/csc/controller.py::CognitiveSystemController`
- **CALLERS:** Main trading loops, autonomous execution pipelines.
- **MUTATION PATHS:** `synthesize_decision()`, position sizer calculations (`final_qty = base_qty * slippage_penalty`).
- **TRUST BOUNDARY:** Multi-step pipeline passing through `ImmutableShield` and `MasterRiskManager`.
- **BYPASS PATHS:** Direct broker initialization and trade submission (`broker.submit_order()`) bypassing CSC.
- **DUPLICATE AUTHORITIES:** `trading_bot/execution/advanced_execution.py::HFTExecutionEngine`, `trading_bot/radar_ai/agents/execution_agent.py::ExecutionAgent`.
- **FAILURE MODE:** Unauthorized market orders, direct AI trade submission.

### 12. Agent Creation / Spawning
- **OWNER:** `trading_bot/agents/multi_agent_debate.py::HivemindAgentManager`
- **CALLERS:** Setup scripts, multi-agent debate orchestrator.
- **MUTATION PATHS:** Direct instantiation of `TradingAgent(...)`.
- **TRUST BOUNDARY:** None currently (any python code can instantiate `TradingAgent`).
- **BYPASS PATHS:** Arbitrary code execution can spawn new `TradingAgent` instances without authorization or resource limits.
- **DUPLICATE AUTHORITIES:** `trading_bot/intelligence_core/agent_army.py::AgentArmy`.
- **FAILURE MODE:** Unauthorized self-replication, resource exhaustion, Sybil agent creation.

### 13. Process Creation
- **OWNER:** System OS / Python `subprocess` / `multiprocessing`
- **CALLERS:** Various scripts (`run_aletheia.py`, background services).
- **MUTATION PATHS:** `os.system`, `subprocess.Popen`, `subprocess.run`.
- **TRUST BOUNDARY:** Host OS process boundary.
- **BYPASS PATHS:** Unrestricted direct use of `subprocess` in modules without sandbox interception.
- **DUPLICATE AUTHORITIES:** None.
- **FAILURE MODE:** Arbitrary shell command execution, background process persistence.

### 14. Filesystem Access
- **OWNER:** Standard Python I/O (`open`, `pathlib`, `shutil`)
- **CALLERS:** All storage, logging, and checkpointing modules.
- **MUTATION PATHS:** `open(..., 'w')`, SQLite connections.
- **TRUST BOUNDARY:** File permissions on host machine.
- **BYPASS PATHS:** Direct file writes outside designated data/checkpoint directories.
- **DUPLICATE AUTHORITIES:** None.
- **FAILURE MODE:** Arbitrary file overwrite, governance policy modification.

### 15. Network Access
- **OWNER:** Python `requests`, `aiohttp`, broker SDKs, news connectors.
- **CALLERS:** Market data fetchers, news scrapers, API clients.
- **MUTATION PATHS:** HTTP GET/POST, WebSocket connections.
- **TRUST BOUNDARY:** Network firewall / OS sockets.
- **BYPASS PATHS:** Unrestricted outbound network access from any agent module.
- **DUPLICATE AUTHORITIES:** None.
- **FAILURE MODE:** Data exfiltration, unauthorized API command execution, SSRF.

### 16. Credential Access
- **OWNER:** Environment variables (`.env`), `trading_bot/core/secureconfig.py`
- **CALLERS:** Broker connectors, API clients.
- **MUTATION PATHS:** `os.getenv()`.
- **TRUST BOUNDARY:** Process environment memory.
- **BYPASS PATHS:** Direct `os.environ` access by any untrusted agent module.
- **DUPLICATE AUTHORITIES:** `trading_bot/security/complete_security_system.py`.
- **FAILURE MODE:** Credential theft, API key leak across agent logs.

### 17. Self-Modification
- **OWNER:** `trading_bot/systems_ai/self_improvement.py::SelfImprovementLoop`
- **CALLERS:** Autonomous self-evolution scripts.
- **MUTATION PATHS:** Code modification, prompt tuning, hyperparameter updating.
- **TRUST BOUNDARY:** Structural sandboxing validation gates in `self_improvement.py`.
- **BYPASS PATHS:** Direct file edits to core modules; dynamic code execution (`eval`, `exec`).
- **DUPLICATE AUTHORITIES:** `trading_bot/recursive_self_improvement/`.
- **FAILURE MODE:** Evaluator manipulation, safety gate removal, arbitrary code modification.

### 18. Evaluation
- **OWNER:** `trading_bot/governance/evolution_gate.py::EvolutionGate`
- **CALLERS:** Self-improvement loop, candidate validators.
- **MUTATION PATHS:** `validate_evolution()`.
- **TRUST BOUNDARY:** Baseline comparison logic.
- **BYPASS PATHS:** Modifying metric calculations in candidate configs; self-reported metric inflation.
- **DUPLICATE AUTHORITIES:** `trading_bot/governance/production_gate.py`.
- **FAILURE MODE:** Benchmark gaming, reward hacking, false promotion.

### 19. Deployment
- **OWNER:** `trading_bot/governance/production_gate.py::ProductionAcceptanceGate`
- **CALLERS:** CI/CD scripts, launch orchestrators.
- **MUTATION PATHS:** `evaluate_release_readiness()`.
- **TRUST BOUNDARY:** Metric checks and test pass requirements.
- **BYPASS PATHS:** Manual deployment scripts bypassing gate checks.
- **DUPLICATE AUTHORITIES:** `trading_bot/gets/core/governance_promotion.py`.
- **FAILURE MODE:** Deployment of unverified or compromised models to live trading.

### 20. Audit Logging
- **OWNER:** `trading_bot/security/audit_logging.py::AuditLogger`
- **CALLERS:** Risk managers, governance gates, decision bus.
- **MUTATION PATHS:** `log_event()`, SQLite database writes (`audit_log.db`).
- **TRUST BOUNDARY:** Append-only log files/DB.
- **BYPASS PATHS:** Direct database modification; skipping audit log calls in custom routines.
- **DUPLICATE AUTHORITIES:** `trading_bot/foundation_agents/safety/audit_logger.py::AuditLogger`, `trading_bot/security/advanced_security.py::AuditLogger`.
- **FAILURE MODE:** Loss of decision provenance, audit trail tampering.

### 21. Emergency Shutdown (Kill Switch)
- **OWNER:** `trading_bot/core/emergency_kill_switch.py::EmergencyKillSwitch`
- **CALLERS:** Master risk manager, human supervisor, automated anomaly detectors.
- **MUTATION PATHS:** `trigger_kill_switch(reason, level)`.
- **TRUST BOUNDARY:** Class-level singleton state.
- **BYPASS PATHS:** Inconsistent checking of `can_trade()` across execution paths; duplicate kill switch implementations.
- **DUPLICATE AUTHORITIES:** `trading_bot/_archive/aamis_v3/meta/meta_systems.py::FailSafeKillSwitchSystem`, `trading_bot/core/circuit_breaker.py`.
- **FAILURE MODE:** Failure to halt live trading during black swan or compromise events.

---

## 3. ARCHITECTURAL FRAGMENTATION & DUPLICATION SUMMARY

[EVIDENCE] The discovery audit revealed major duplicate authorities that must be consolidated:
1. **Memory:** `HierarchicalMemorySystem` vs `MemorySystem` (foundation_agents) vs `StructuralMemory`.
2. **Risk:** `MasterRiskManager` vs `UnifiedRiskManager` vs `AdvancedRiskManager`.
3. **Governance & Evolution:** `EvolutionGate` vs `ProductionAcceptanceGate` vs `GovernancePromotionLayer`.
4. **Audit Logging:** 3 distinct `AuditLogger` implementations across `security/`, `foundation_agents/`, and `advanced_security.py`.
5. **Agent Identity & Swarms:** `TradingAgent` (multi_agent_debate) vs `Agent` (agent_army) vs `Agent` (agent_swarm).

---

## 4. CONSOLIDATION TARGETS FOR PHASE 16

[PROPOSED DESIGN] Under Phase 16, the repository will enforce **ONE authoritative implementation** per capability:
- **Identity & Messaging:** `TradingAgent` + `UnifiedDecisionBus` with signed payload verification.
- **Persistent Memory:** `HierarchicalMemorySystem` with `ProvenanceAwareMemoryRecord` and SAGE graph.
- **Governance & Evolution:** `EvolutionGate` + Hardened Root Governance.
- **Risk Authorization:** `MasterRiskManager` (incorporating deterministic limits).
- **Execution Boundary:** `CognitiveSystemController` + `ImmutableShield`.
- **Audit Logging:** `trading_bot/security/audit_logging.py::AuditLogger`.
- **Emergency Shutdown:** `trading_bot/core/emergency_kill_switch.py::EmergencyKillSwitch`.
