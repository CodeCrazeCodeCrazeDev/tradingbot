# FWM: Scaling Analysis & Institutional Reality Check

## 1. Scaling Analysis

| Subsystem | Computational Req | Scaling Bottleneck | Cost Est (Monthly) |
| :--- | :--- | :--- | :--- |
| **Data Layer** | High (Tick/Book) | I/O Throughput & Storage. | $5,000 - $15,000 |
| **Representation** | Medium (Mamba) | GPU Memory (HBM3). | $2,000 - $8,000 |
| **World Model** | Extreme (Sims) | Multi-node Parallelism. | $10,000 - $30,000 |
| **Risk Veto** | Low | Latency of checks. | < $1,000 |

### Failure Modes & Research Risks
*   **Mode Collapse:** The agent-based simulation might converge on a single unrealistic behavior. *Mitigation:* Diverse curriculum and real-world anchoring.
*   **Latent Drift:** The mapping between Z-space and reality may drift over months. *Mitigation:* Continuous "Scientist" research cycles.
*   **Computational Explosion:** 10k simulations per decision might be too slow for HFT. *Mitigation:* Use surrogate models (Neural Approximators) for real-time execution.

## 2. Institutional Reality Check

### Unrealistic Assumptions
*   **Full Order Book Availability:** Retail users cannot easily get full depth for all assets.
*   **Total Agent Transparency:** We don't know the exact constraints of every Hedge Fund. We must treat these as **Latent Probabilities**.

### Components with Weak ROI
*   **Alternative Data (Satellite):** High cost, low signal-to-noise for liquid assets. *Action:* Deprioritize for MVP.
*   **Exact HFT Simulation:** Modeling HFT to the microsecond requires FPGA resources. *Action:* Use stochastic flow toxicity models instead.

## 3. Practical Institutional Redesign
To maximize performance per unit complexity:
1.  **Surrogate RSSM:** Use the heavy FWM for high-level allocation and "Scenario Planning," but use a distilled "Surrogate RSSM" for real-time execution gates.
2.  **Focus on Gamma/Vanna:** Instead of modeling every macro variable, focus on the **Dealer Hedging Layer**, as this provides the highest ROI for liquidity forecasting.
3.  **Hybrid Real-Sim Training:** Anchor the simulation in real data every N steps (Observation Re-Anchoring) to prevent the "Dreamer" from hallucinating unrealistic market paths.
