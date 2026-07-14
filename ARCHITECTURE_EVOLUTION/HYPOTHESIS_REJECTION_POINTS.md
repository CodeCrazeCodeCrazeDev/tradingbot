# Hypothesis Rejection Points - AlphaAlgo Audit 2026

This document lists where hypotheses are rejected, discarded, or moved to a dormant state.

## 1. Active Rejection
- **`trading_bot/alpha_research/self_evolving_researcher.py`**: `SelfEvolvingResearcher._kill_losers`
  - *Description*: Deletes or archives strategy candidates that fail to meet the fitness threshold during evolution.
- **`trading_bot/core/phce_d/core_types.py`**: `DecisionOutput.REFUSE`
  - *Description*: The PHCE-D engine actively rejects a trade hypothesis if it fails conservative safety or contradiction checks.
- **`trading_bot/core/verification/swarm.py`**: `EvidenceGraphGate.verify_evidence_first`
  - *Description*: Vetoes a proposal if the underlying evidence graph is fragmented or insufficient.

## 2. Decay & Retirement
- **`trading_bot/alpha_research/alpha_death_clock.py`**: Strategy decommissioning based on alpha decay.
  - *Description*: Automatically deprecates strategies whose predictive power has dropped below a statistical significance level over time.
- **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `ScientificReasoningEngine.retire_hypothesis`
  - *Description*: Step 18, transitioning a hypothesis to `REJECTED`, `DEPRECATED`, or `SUPERSEDED`.
- **`trading_bot/core/hms/memory.py`**: Memory pruning or "forgetting" logic (often implicit in graph weight decay).
