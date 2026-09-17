# Multi-Agent Failure Modes & Byzantine Resilience

## 1. Byzantine Fault Tolerance Design
AlphaAlgo is built to achieve Byzantine resilience against individual agent crashes, database timeout latencies, and network packet loss:
- **Fallback Sizing:** If an agent fails to respond or crashes, the system degrades gracefully by injecting an automatic defensive fallback argument (e.g. `TradeAction.HOLD` with low confidence).
- **Emergency Vetos:** If *all* core agents crash or time out, the system triggers a central emergency veto (NO_TRADE) to prevent empty decision-making or unvalidated exposure.
- **Voter Quorum:** The consensus engine dynamically evaluates the consensus level based only on active responsive agents, preventing deadlocks or stalling.

## 2. Fail-Closed Invariants
We enforce strict fail-closed safety patterns to safeguard trading capital:
1. **Spread & Liquidity Panic:** If local volatility exceeds threshold bounds or volume drops under anemic support lines, the `LiquidityVerifier` falsifies buy/sell proposals.
2. **Systemic Tail Risk:** If VIX spikes above 35.0, the `CausalVerifier` rejects directional execution.
3. **Capacity Threshold:** If portfolio exposure breaches 85%, the `RiskVerifier` vetoes further allocations.
