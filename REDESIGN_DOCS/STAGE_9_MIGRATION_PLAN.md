# Stage 9: Migration Plan - "Project Singularity"

## Phase 1: Foundation (Zero-Downtime)
1.  **Initialize Central State**: Deploy the ACID-compliant state store (PostgreSQL/Redis).
2.  **Deploy Unified Message Bus**: Standardize all communication on a single low-latency bus (e.g., NATS or gRPC).
3.  **Implement Integrated Brain Service (IBS)**: Create the skeleton for the unified brain that delegates to legacy orchestrators initially.

## Phase 2: World Model Consolidation
1.  **Unified Encoder**: Create the `UniversalStateEncoder` and map perception from all modules to it.
2.  **Shadow World Model**: Deploy the JEPA-SCM hybrid in "observation-only" mode.
3.  **Uncertainty Alignment**: Calibrate the IBS to recognize uncertainty signals from the new model.

## Phase 3: Orchestrator Decommissioning (Serial Migration)
1.  **Safety First**: Migrate `MSOS` governance into the IBS `GovernanceEngine`.
2.  **Intelligence Migration**: Move `AAMIS v3` and `Aletheia` reasoning logic into the IBS `HierarchicalPlanner`.
3.  **Discovery Migration**: Consolidate `AADS` and `AutonomousSuperintelligence` into the unified `EvolutionEngine`.
4.  **Learning Migration**: Integrate `MarketStudent/Teacher` into the IBS system-wide learning engine.

## Phase 4: Grounding & Realism
1.  **Kill the Noise**: Replace all Gaussian noise generators with historical tick data streamers.
2.  **Backtest Integration**: Point the `ExperimentManager` to the `RigorousBacktester`.
3.  **Institutional Hardening**: Finalize IBKR and Binance execution paths for cross-platform parity.

## Phase 5: Production Cutover
1.  **Shadow Testing**: Run the fully unified IBS in shadow mode for 100 hours of live market data.
2.  **Canary Rollout**: Migrate 5% of capital to the IBS.
3.  **Full Singularity**: Decommission all legacy orchestrators and files (`_archive/`).

## Rollback Strategy
*   **Versioned State**: Every migration step includes a database snapshot.
*   **Legacy Wrappers**: IBS can "hot-swap" back to a legacy orchestrator if specific capability benchmarks drop.
*   **Kill Switch**: Immediate return to 100% manual governance if any L0 constraint is violated.
