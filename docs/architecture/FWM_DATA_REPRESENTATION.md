# FWM: Multi-Layer Data & Representation Architecture

## 1. The Data Layer: Latent Signal Mapping

| Source | Why It Exists | Latent Information Revealed | Status |
| :--- | :--- | :--- | :--- |
| **Tick Data** | High-fidelity price movement. | Aggressive vs. Passive flow imbalance. | **Essential** |
| **Full Depth Order Book** | Snapshot of available liquidity. | Information asymmetry and spoofing/layering. | **Essential** |
| **Options Greeks / Flow** | Hedging requirements of dealers. | **Dealer Gamma / Vanna / Charm** - The "Gravity" of the market. | **Essential** |
| **Macro / Econ Calendars** | Fundamental drivers. | Central Bank reaction function anchors. | **Essential** |
| **Alternative Data** | Satellite, Credit Card, Sentiment. | Early signals of consumer behavior and supply chain. | Optional (Alpha) |
| **Cross-Asset Flows** | Inter-market relationships. | Systemic risk contagion and carry-trade dynamics. | **Essential** |

## 2. Representation Learning Layer: Hybrid Mamba-Transformer (HMT)

### Evaluation of Architectures
*   **Transformers:** Excellent for global attention and regime matching. *Weakness:* Quadratic scaling limits tick-level processing.
*   **Mamba (State-Space Models):** Linear scaling with time. Excellent for long-horizon sequence modeling (continuous market flow).
*   **Contrastive Learning:** Vital for learning regime embeddings that are invariant to noise.

### Proposed Architecture: The "Cognitive Filter"
We implement a **Dual-Path Representation** system:

1.  **Fast Path (Mamba):** Processes raw tick and order book data to maintain a real-time "Micro-State" embedding. This path handles millisecond-level noise.
2.  **Global Path (Transformer):** Processes sampled Micro-States along with Macro, Options, and Flow data. It builds a global context embedding that captures the **Regime**.

### Modalities
*   **Numeric:** OHLCV, Greek surfaces, Macro stats.
*   **Structured:** Order book levels, economic calendars.
*   **Textual:** News feeds, Twitter, Central Bank speeches (via LLM-based summary embeddings).

## 3. The Latent State Vector (S_t)
The result is a unified, high-dimensional latent vector containing:
*   `z_liquidity`: Real-time liquidity fragility.
*   `z_positioning`: Estimated crowdedness of current trend.
*   `z_regime`: Soft-max distribution over known market regimes.
*   `z_causal`: Impact scores of macro variables on current price action.
