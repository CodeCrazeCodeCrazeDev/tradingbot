# ADR 0003: Cost-Aware Research Planner and Resource Scheduling
## Status: Approved

### Context
Continuous evolutionary search is highly computationally intensive. Unchecked background execution of genetic mutations (CMA-ES, NSGA-II) could consume substantial CPU and GPU resources, starving the real-time predictive models, causal world simulators, and order-routing systems required by live trading modules.

### Decision
We will implement a dual-layer resource management framework:
1. **Cost-Aware Research Planner (CARP)**: Every proposed experiment is pre-evaluated to calculate its expected return on engineering investment (EROI). If an experiment's expected Sharpe improvement does not justify its predicted compute cost (GPU/CPU hours), the CARP rejects or deprioritizes the experiment before execution.
2. **Compute Resource Scheduler (CRS)**: The CRS manages hardware limits during execution. Live trading and prediction models are pinned to High CPU priority and reserved cores. L2 and L3 sandboxed experiments are pinned to restricted core affinities (cooperative multi-tasking) and limited to Process Class Idle/Low. GPU VRAM partitions are strictly enforced (hard-capped at 30% for background research).

### Consequences
* **Production Integrity**: Guarantees that live quantitative trading execution never suffers from latency inflation or out-of-memory (OOM) crashes due to background research workloads.
* **Economic Efficiency**: Aligns background compute expenditures with expected quantitative and strategic benefits.
* **Execution Delay**: Lower-priority experiments may experience substantial queue delay during periods of high market volatility when the trading engine is running heavy trajectory simulations.
