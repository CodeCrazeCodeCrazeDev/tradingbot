# Multi-Agent Executable Architecture

## Executive Summary
This document serves as the authoritative, grounded architectural blueprint mapping out the multi-agent system execution flows, capability boundaries, message protocols, and lifecycles within AlphaAlgo's Cognitive Decision System.

## Architecture Map

### 1. Capability: Strategic Reasoning & Consensus
- **Authoritative Implementation**: `MultiAgentDebateSystem` in `trading_bot/agents/multi_agent_debate.py`
- **Entry Points**: `debate(self, topic: Any, context: Optional[MarketContext] = None) -> FinalDecision`
- **Consumers**: `CognitiveSystemController` (Tier-0 brain)
- **Dependencies**: `HeadAI`, `TradingAgent` (specialized sub-agents), `FalsificationGate`, `DebateQualityEvaluator`
- **State Ownership**: Immutable historical log of previous decisions stored locally on the system instance (`self.decisions`).
- **Duplicate Implementations**: None (Consolidated during V6 stabilization).
- **Runtime Reachability**: Reached in production paths when resolving directional trading proposals.
- **Failure Modes**:
  - *Byzantine Agent response*: Isolated via robust verification and individual agent scorecards.
  - *All agents crashed*: Fail-closed fallback immediately triggers `_trigger_emergency_no_trade`, returns `TradeAction.NO_TRADE` with zero confidence.
- **Migration Status**: Completed and verified.

### 2. Capability: Bayesian Evidence Synthesis
- **Authoritative Implementation**: `HeadAI` in `trading_bot/agents/multi_agent_debate.py`
- **Entry Points**: `synthesize_decision(self, arguments, context, debate_rounds, scorecards=None) -> FinalDecision`
- **Consumers**: `MultiAgentDebateSystem`
- **Dependencies**: `ConfidenceCalibrator`
- **State Ownership**: Stateless, acts purely as an analytical execution pipeline.
- **Authority**: Authoritative consensus evaluation authority.
- **Duplicate Implementations**: None.
- **Failure Modes**: Missing risk sentinel response handled via fallback defaults.

### 3. Capability: Risk Boundary Verification
- **Authoritative Implementation**: `RiskVerifier` in `trading_bot/agents/multi_agent_debate.py`
- **Entry Points**: `verify(self, action: TradeAction, context: MarketContext) -> RiskVerifierOutcome`
- **Consumers**: `MultiAgentDebateSystem` and `test_multi_agent_adversarial.py` unit tests.
- **Dependencies**: `MarketContext`, `RiskVerifierOutcome`
- **State Ownership**: Stateless boundary engine.
- **Authority**: Hard guardrail verifying portfolio exposure, VIX levels, and correlation boundaries.
- **Duplicate Implementations**: Duplicate implementations at the bottom of `multi_agent_debate.py` and top of legacy tests have been completely consolidated into the single authoritative class definition at line 238 of `multi_agent_debate.py`.
- **Migration Status**: Completed and verified.

---

## Complete Execution Flow Sequence
```text
Market Context Input
  │
  ├─► Integrity Validation Gates (current_price, volatility, exposure bounds)
  │     [Fail-closed on malformed data]
  │
  ├─► Multi-Agent Parallel Analysis (Macro, Tactical, Risk Sentinel)
  │     [Fallback Defaults handle crashes / timeout / exceptions]
  │
  ├─► Bayesian Calibration & Consensus Resolution (HeadAI)
  │     [Posterior calculation based on weighted scorecards]
  │
  ├─► Post-Hoc Quality Review & Provenance Record
  │     [19-field ledger entry tracking git commit and features hash]
  │
  └─► Execution / Fail-Closed Trade Recommendation
```
