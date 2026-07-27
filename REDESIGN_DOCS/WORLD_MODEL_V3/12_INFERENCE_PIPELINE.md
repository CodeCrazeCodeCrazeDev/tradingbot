# 12_INFERENCE_PIPELINE.md - Real-Time Execution and Constraints

## Objective
Design the pipeline for low-latency, real-time future simulation and decision support.

## 1. Inference Architecture

### A. The "Predictive Tick" Loop
1.  **Ingest:** Subscribe to ZMQ/Redis stream of live market updates.
2.  **Encode:** Map raw data to latent state $z_t$ (1-5ms).
3.  **Update Beliefe:** Pass $z_t$ through the **Mamba SSM** to update the internal temporal state (2-10ms).
4.  **Detect Trigger:** Determine if the state change warrants a new simulation (e.g., price move > threshold, regime shift).

### B. The "Simulation Burst"
If triggered:
1.  **Generate Scenarios:** Parallel rollout of $N$ trajectories (Diffusion or Trajectory Transformer) on GPU (20-50ms).
2.  **Apply Interventions:** For each candidate plan, apply $do$-calculus to the trajectories (10ms).
3.  **Evaluate Risk:** Calculate CVaR and Expected Utility for each plan (5ms).

## 2. Latency Constraints
Institutional trading requires low-latency planning.
*   **Target Tactical Latency:** < 100ms for full scenario generation and ranking.
*   **Throughput:** Must handle 1,000+ state updates per second for multi-asset monitoring.

## 3. Optimization Strategies

### A. Model Quantization
*   Use FP16 or INT8 quantization for the Mamba/Transformer weights.
*   Utilize TensorRT or ONNX Runtime for optimized GPU kernels.

### B. KV-Caching for Transformers
*   Maintain the Key-Value cache for the relational transformer layers to avoid redundant computation during multi-step rollouts.

### C. Mamba Associative Scan
*   Leverage the associative scan property of Mamba to process history in $O(\log N)$ or update the state in $O(1)$ relative to history length.

### D. Speculative Simulation
*   Pre-compute the most likely "Next State" trajectories *before* a new tick arrives, and then "correct" them using the actual data (Active Inference).

## 4. Hardware Requirements
*   **GPU:** NVIDIA A100/H100 or high-end consumer GPU (RTX 4090) for local simulation.
*   **RAM:** 64GB+ for high-frequency history buffering.
*   **Network:** Low-latency 10GbE for market data ingest.

## 5. Failover & Reliability
*   **Degraded Mode:** If latency exceeds 200ms, the engine switches to a "Fast Linear" transition model (bypassing the full Diffusion simulation).
*   **State Recovery:** In case of crash, the engine hot-loads the last temporal state and belief distribution from the **HMS Working Memory**.
