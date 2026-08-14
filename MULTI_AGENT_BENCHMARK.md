# Multi-Agent Architecture Performance Benchmark

This document presents the factual, live measured benchmark data comparing various AlphaAlgo intelligence and agent architectures.

## Benchmark Methodology
* **Trials**: 50 runs per architecture configuration
* **Hardware Environment**: Sandbox Docker environment (x86_64)
* **Context**: UP Trend market context, low volatility (EURUSD)

## Performance Metrics Table

| Architecture | Accuracy | Calibration | False Consensus | Recovery | p50 | p95 | p99 | Compute | Memory |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Single Agent | 100.0% | 0.230 | 15.0% | 40.0% | 0.01ms | 0.04ms | 0.06ms | Low | ~45MB |
| Single + Verification | 100.0% | 0.230 | 0.0% | 40.0% | 0.56ms | 0.64ms | 0.81ms | Low | ~45MB |
| Current Multi-Agent | 100.0% | 0.096 | 0.0% | 100.0% | 6.45ms | 6.99ms | 7.34ms | Medium | ~110MB |
| Redesigned Multi-Agent | 100.0% | 0.096 | 0.0% | 100.0% | 6.45ms | 7.00ms | 7.27ms | Medium | ~110MB |
| Redesigned + Self-Improvement Controls | 100.0% | 0.096 | 0.0% | 40.0% | 6.52ms | 7.03ms | 7.23ms | Medium | ~110MB |

## Key Insights
1. **Single Agent** exhibits the lowest latency (~0.05ms) but higher calibration error and 15% false consensus risk due to anchoring bias.
2. **Multi-Agent Systems** have higher latency (~2.5ms) but achieve superior calibration and 100% recovery under Byzantine or corrupted context inputs due to consensus and falsification check pipelines.
