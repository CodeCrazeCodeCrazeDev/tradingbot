# Research Synthesis & SOTA Benchmarking

## 1. Core Principles (Derived from SCIENTIFIC_FOUNDATION_2026)
- **Active Inference (VFE Minimization)**: Governing framework for all decision loops.
- **Hierarchical Planning with Information Folding (HIPIF)**: Strategic compression for long-horizon planning.
- **Skill-to-LoRA (S2L)**: Transitioning from discrete functions to adaptive model parameters.
- **Entropy-KL Selective Fine-Tuning (EKSFT)**: Safe, monotone-improving self-evolution.

## 2. Institutional Standards
- **Risk**: Moving from static VaR/CVaR to **Dynamic Active Inference Risk Control** (treating risk as unexpected Free Energy).
- **Execution**: Implementation of **Multi-Agent Transactive Memory** for institutional order flow intelligence.

## 3. Capability Gaps vs. SOTA
- **Industry SOTA (Jane Street/Citadel/Two Sigma)**: High-performance C++, sub-microsecond latency, deep integration of ML into the entire order book pipeline.
- **AlphaAlgo Alpha**: High-level Python intelligence, strong reasoning (Chain-of-Thought), but currently higher latency and fragmented state.
- **Target**: Evolve to **"Reasoning-Fast Execution" hybrid**, where the CSC handles strategic planning while specialized C++/Rust-accelerated adapters (Tier 1) handle realtime execution.

## 4. Benchmark KPIs
Baseline KPIs to be measured:
- **Decision Latency**: Time from signal to CSC-verified plan.
- **Planning Depth**: Number of recursive steps before strategic "folding".
- **Monotone Improvement**: Verification of RSEA Evolution Gate across 100+ epochs.
- **Uncertainty Calibration**: Expected Calibration Error (ECE) of the GWM.
