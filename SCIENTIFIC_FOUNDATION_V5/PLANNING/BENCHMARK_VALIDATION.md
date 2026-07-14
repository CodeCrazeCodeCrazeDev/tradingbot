# Phase 4: Benchmark & Validation Plan (UCA V5)

## 1. Benchmark Suite

| Benchmark | Focus | Metric | Target |
| :--- | :--- | :--- | :--- |
| **CL-Bench** | Continual Learning | Gain Metric (G) | $G > 0.10$ |
| **DeepWeb-Bench** | Derivation Depth | Reasoning Hops | $\ge 3$ verified hops |
| **FIRE** | Financial Reasoning | Alignment | $> 85\%$ vs. Institutional Expert |
| **HORIZON** | Long-horizon | Coherence | Zero-drift over 48h session |
| **Latency SLA** | Performance | Milliseconds | $< 500ms$ (End-to-End) |

## 2. Validation Plan (V-Model)

### 2.1 Unit Validation
- **DiscoLoop**: Verify $h_{t+1}$ incorporates $e_t$ projection without gradient explosion.
- **LogAct**: Verify total ordering of 1000 concurrent action proposals.
- **SAGE**: Verify triplet extraction and incremental graph update.

### 2.2 Integration Validation
- **CSC + HASP**: Verify that high-volatility PFs (HASP) correctly override CSC decisions.
- **CSC + SAGE**: Verify multi-hop evidence retrieval informs hypothesis ranking.
- **CSC + EvolutionGate**: Verify that regression-inducing weights are rejected by RSEA.

### 2.3 Institutional Validation (`tests/uca_v5_validation.py`)
Final release gate:
1.  **Safety**: 100% pass on Immutable Shield risk bounds.
2.  **Accuracy**: Brier Score < 0.15 on regime classification.
3.  **Reliability**: Deterministic state recovery from log replay.
