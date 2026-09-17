# Multi-Agent Trading System Architecture

## 1. System Topology Overview
The AlphaAlgo Multi-Agent Trading System is an advanced, evidence-first, peer-review-driven decision infrastructure designed to coordinate diverse intelligence viewpoints into an authoritative trading directive. It sits above the core execution layer and feeds directly into the Cognitive System Controller (CSC).

```text
                     [ Market Observation / MarketContext ]
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
      Macro Strategist       Tactical Executioner       Risk Sentinel
      (HTF Trend, S/R)       (LTF timing, Momentum)   (VIX, Exposure, Vol)
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      ▼
                        [ Head AI (Consensus Loop) ]
                                      │
                        (Adversarial Prosecution Loop)
                                      ▼
                      [ Falsification Swarm / Gates ]
                                      │
                         [ Calibrated Final Decision ]
```

## 2. Agent Roles and Core Responsibilities

### 2.1. Macro Strategist
- **Timeframe Focus:** Higher Timeframe (HTF) trends.
- **Responsibilities:** Evaluates long-term trend direction and support/resistance structures.
- **Grounded Evidence:** Checks price level offsets from support/resistance thresholds and validates with news sentiment indices.

### 2.2. Tactical Executioner
- **Timeframe Focus:** Lower Timeframe (LTF) momentum and entry timing.
- **Responsibilities:** Monitors volume ratios and local compressed volatility.
- **Grounded Evidence:** Prevents execution in low-liquidity zones or excessive local spread expansion.

### 2.3. Risk Sentinel
- **Risk Focus:** Portfolio protection and tail risk.
- **Responsibilities:** Audits current aggregate exposure, asset correlation, and system-level threat conditions (VIX).
- **Grounded Evidence:** Enforces absolute veto parameters when exposure breaches hard limits (>85%) or panic thresholds.

## 3. Consensus and Aggregation Protocol
AlphaAlgo rejects simple majority voting patterns (e.g. 2 buys vs 1 sell) as potentially catastrophic confirmation cascades. Instead, consensus is determined through:
1. **Weighted Evidence Evaluation:** Combining expertise weights, confidence vectors, and historical precision metrics.
2. **Bayesian Posterior Update:** Updating probability of strategy success conditioned on agent-level confidence likelihoods.
3. **Domain Specialist Veto:** High-conviction risk or data prosecution holds automatically take precedence over directional trades, enforcing a strict fail-closed safety posture.
