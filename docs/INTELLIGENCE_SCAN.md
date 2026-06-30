# PHASE 1 — Repository Intelligence Scan: AlphaAlgo

## 1. Repository Structure Analysis

### 1.1 Core Folders & Architecture
- **`trading_bot/`**: The primary source directory.
    - **`core_agent_system/`**: Hierarchical agent orchestration (MasterOrchestrator, USIS).
    - **`autonomous_superintelligence/`**: Self-management, code modification, and research engines.
    - **`recursive_improvement/`**: The Unified RSIE for autonomous system evolution.
    - **`ml/`**: Advanced machine learning (Transformers, RL, GNN, Neuro-symbolic).
    - **`risk/` & `risk_management/`**: Portfolio and trade risk control.
    - **`execution/`**: Broker adapters and order management.
    - **`radar_ai/`**: Evaluation, hivemind, and "Apollo/Foundry" research components.
    - **`alpha_evolve/`**: Strategy genome and evolutionary discovery.
    - **`world_model/`**: Latent dynamics and market simulation.
    - **`governance/`**: Safety boundaries and anti-reward hacking.
- **`backtesting/`**: Backtesting engines and performance validation.
- **`knowledge/`**: Persistent intelligence storage (SQLite, Knowledge Graphs).
- **`api/` & `web/`**: REST interfaces and dashboard.
- **`deploy/`**: Infrastructure-as-Code (Railway, Render, Docker).

### 1.2 Technology Stack
- **Languages**: Python 3.12+ (100% of core logic).
- **Deep Learning**: PyTorch, Transformers, ONNX Runtime.
- **Data Science**: NumPy, Pandas, Scipy, Statsmodels.
- **Infrastructure**: Redis, Kafka, ZeroMQ (Messaging); ClickHouse, MongoDB, SQLAlchemy (Persistence).
- **Web/API**: FastAPI, Uvicorn, Dash/Plotly (Dashboard).
- **Trading Platform**: MetaTrader5 (Primary Broker), Binance, IBKR (Adapters).
- **DevOps**: Docker, Pytest, APScheduler.

### 1.3 Deployment Architecture
- **Cloud Readiness**: Optimized for Linux (Railway/Render) with Docker support.
- **Windows Dependency**: Legacy MT5 adapter requires Windows; Cloud execution uses IBKR/Binance.
- **Modular Scalability**: Microservices-ready via ZeroMQ and Kafka integration.

## 2. System Map (Architecture Graph)

### 2.1 Control Flow (Top-Down)
1. **`MasterOrchestrator`**: Single source of truth for global system state.
2. **`IntegratedAgentSystem`**: Dispatches tasks to specific agent roles.
3. **`SelfCoordinatingCore`**: Manages agent collaboration and tool selection.
4. **`GovernanceSystem`**: Final gate for all actions (Safety/Policy).

### 2.2 Data Flow (End-to-End)
1. **`DataFeeds`**: Real-time tick/orderbook data ingestion.
2. **`WorldModel`**: Latent representation and predictive modeling.
3. **`SignalDiscovery`**: Identification of alpha invariants.
4. **`StrategyEngine`**: Translation of signals into trade logic.
5. **`RiskEngine`**: Position sizing and VaR enforcement.
6. **`TradeExecutor`**: Deployment to brokers via specific adapters.

### 2.3 Recursive Feedback
- **`RSIE`**: Monitors execution -> Evolves hyperparameters/workflow -> Deploys back to Orchestrator.
- **`SelfPlayLoop`**: RL training on historical/simulated data to refine model weights.

## 3. Intelligence Observations

### 3.1 Module Communication
- **Hierarchical Communication**: Top-down task delegation from Master to Sub-Agents.
- **Swarm Intelligence**: Peer-to-peer consensus in the Expert Layer (USIS).
- **Event-Driven**: Extensive use of background loops and async messaging.

### 3.2 Technical Debt & Risks
- **Fragmentation**: Recent consolidation has improved this, but legacy `agents 2/` and `trading_bot/agents/` still exist as stubs/shadows.
- **Complexity**: Deep recursion and circular dependencies (WorldModel <-> Simulation) can lead to initialization race conditions.
- **Simulation Bias**: The "Delusion Loop" (training on noise) is a high-priority risk.
- **Mock Overload**: Many advanced "Superintelligence" features were stubs before recent RSIE/USIS implementations; some deep research modules may still be simulated.

### 3.3 Scalability
- **Horizontal**: High. Agents can be distributed via ZeroMQ/Kafka.
- **Vertical**: High. Transformer models are Recurrent-Depth optimized for varying compute budgets.
