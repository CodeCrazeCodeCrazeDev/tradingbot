# Multi-Agent Executable Architecture

This document provides a factual, evidence-based architectural audit of the multi-agent decision and reasoning ecosystems within the AlphaAlgo platform.

---

## 1. Multi-Agent Debate and Consensus Engine

### Capability
* **Description**: Multi-agent consensus through turn-based debate. Reconciles technical trend analysis, tactical execution, and risk assessment via a Bayesian synthesis and falsification framework.
* **Implementation**: `trading_bot/agents/multi_agent_debate.py`
* **Entry points**:
  - `MultiAgentDebateSystem.debate(context: MarketContext)`: Triggers the multi-turn debate process and final synthesis.
* **Consumers**:
  - `HivemindAgentManager.run_debate()` in `trading_bot/agents/__init__.py`
  - `agents_service.py` in `trading_bot/services/agents_service.py`
* **Dependencies**:
  - `numpy`, `torch`
  - `ConfidenceCalibrator` under `trading_bot/verification/confidence_calibrator.py`
  - `decision_bus` under `trading_bot/core/unified_event_bus.py`
* **State ownership**:
  - `MultiAgentDebateSystem` owns a list of historical decisions (`self.decisions`) and instances of active specialized agents (`MacroStrategist`, `TacticalExecutioner`, `RiskSentinel`, etc.).
* **Authority**:
  - **Authoritative**: `trading_bot/agents/multi_agent_debate.py` is the designated authoritative multi-agent reasoning and debate implementation.
* **Duplicate implementations**:
  - **Duplicate**: `trading_bot/decision_governance/multi_agent_debate.py` (which uses a Proposer, Challenger, Synthesizer, Arbiter structure). This duplicate remains completely offline and is not reachable from the live agent service layer.
  - **Archive**: `trading_bot/_archive/agents/multi_agent_debate.py`.
* **Runtime reachability**:
  - Fully reachable and utilized by `agents_service.py` and unit/adversarial integration tests.
* **Failure modes**:
  - **Byzantine/Contradictory Views**: Mitigated by Bayesian synthesis and the veto power of `RiskSentinel`.
  - **Silent Agents**: Mitigated by graceful degradation default arguments.
  - **Double-Counting/Out-of-Order Messages**: Mitigated by HeadAI latest-only filtering of active arguments.
* **Migration status**:
  - Complete. Authoritative path is validated with a 100% pass rate.

---

## 2. Agent Management & Hivemind Coordination

### Capability
* **Description**: Central orchestration and lifecycles of specialized planner, executor, verifier, and debate systems.
* **Implementation**: `trading_bot/agents/__init__.py` (`HivemindAgentManager`)
* **Entry points**:
  - `HivemindAgentManager.initialize()`: Boots up debate systems, executors, planners, and verifiers.
* **Consumers**:
  - Live container launchers and cluster orchestrators.
* **Dependencies**:
  - `A2AMessageBus` under `trading_bot/a2a/`
  - `World2AgentBridge` under `trading_bot/world2agent.py`
* **State ownership**:
  - `HivemindAgentManager` maintains references to live `debate_system`, `executor`, `planner`, and `verifier` instances.
* **Authority**:
  - Authoritative coordinator for all agent services.
* **Duplicate implementations**:
  - None (consolidated).
* **Runtime reachability**:
  - Active in live swarms and inter-agent communication.
* **Failure modes**:
  - **A2A Bus Outage**: Handled through asynchronous connection retries.
* **Migration status**:
  - Complete.

---

## 3. Financial Decision Boundary & Risk Authority

### Capability
* **Description**: Deterministic safety gates preventing AI reasoning systems from directly issuing live execution orders without satisfying rigid structural invariants.
* **Implementation**: `RiskVerifier` / `FalsificationGate` in `trading_bot/agents/multi_agent_debate.py` and `ImmutableShield` in `trading_bot/core/immutable_shield.py`.
* **Entry points**:
  - `RiskVerifier.verify(action, context)`
  - `ImmutableShield.validate_action(category, action_data, context)`
* **Consumers**:
  - `MultiAgentDebateSystem.debate()`
  - `CognitiveSystemController.process_market_observation()`
* **Dependencies**:
  - Deterministic portfolio parameters, daily drawdown metrics, exposure thresholds.
* **State ownership**:
  - `ImmutableShield` / `RiskVerifier` evaluate inputs against stateless rules and strict config boundaries.
* **Authority**:
  - Sovereign deterministic authority.
* **Duplicate implementations**:
  - None.
* **Runtime reachability**:
  - Executed on every proposed trade action before final consensus commitment.
* **Failure modes**:
  - **Invalid parameters**: Immediate NO_TRADE fallback.
* **Migration status**:
  - Upgraded and strictly enforced.
