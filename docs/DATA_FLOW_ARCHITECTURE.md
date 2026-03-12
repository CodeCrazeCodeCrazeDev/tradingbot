# Unified Trading System - Complete Data Flow Architecture

## Master Data Flow Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        EXTERNAL DATA SOURCES                                ║
║  [Exchanges] [Brokers] [News APIs] [Social] [Alt Data] [Blockchain]        ║
╚══════════════════════╦═══════════════════════════════════════════════════════╝
                       ║
                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 0: INFRASTRUCTURE                                                      │
│ ┌─────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐       │
│ │ CPU/Memory  │ │ Network I/O  │ │ Disk I/O    │ │ GPU (if avail)   │       │
│ │ Monitoring  │ │ Rate Limits  │ │ Storage Mgr │ │ ML Acceleration  │       │
│ └──────┬──────┘ └──────┬───────┘ └──────┬──────┘ └────────┬─────────┘       │
│        └───────────────┴────────────────┴─────────────────┘                  │
│                         │ health_metrics, resource_status                     │
└─────────────────────────┼────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: OBSERVABILITY                                                       │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐      │
│ │ Logging  │ │ Metrics  │ │ Tracing  │ │ Alerting │ │ Dashboard     │      │
│ │ log_sys  │ │ telemetry│ │ observ.  │ │ alerts/  │ │ visualization │      │
│ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬───────┘      │
│      └─────────────┴────────────┴────────────┴───────────────┘               │
│                    │ logs, metrics, traces, alerts                            │
│                    │ (monitors ALL layers bidirectionally)                    │
└────────────────────┼─────────────────────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: CONNECTIVITY & INGESTION                                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │                    CONNECTION MANAGER                            │         │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      │         │
│  │  │ WebSocket │ │ REST API  │ │ FIX Proto │ │ Streaming │      │         │
│  │  │ Collector │ │ Collector │ │ Bridge    │ │ Feeds     │      │         │
│  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘      │         │
│  │        └──────────────┴─────────────┴─────────────┘             │         │
│  └────────────────────────────┬────────────────────────────────────┘         │
│                               ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │                    BROKER ADAPTERS                               │         │
│  │  ┌─────┐ ┌────────┐ ┌─────────┐ ┌────┐ ┌──────────┐           │         │
│  │  │ MT5 │ │ Alpaca │ │ Binance │ │ IB │ │ Simulate │           │         │
│  │  └──┬──┘ └───┬────┘ └────┬────┘ └─┬──┘ └────┬─────┘           │         │
│  │     └─────────┴──────────┴────────┴──────────┘                  │         │
│  └────────────────────────────┬────────────────────────────────────┘         │
│                               │                                              │
│  Output: raw_market_events, raw_trades, raw_quotes, raw_orderbook            │
└───────────────────────────────┼──────────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: DATA FOUNDATION                                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ NORMALIZER                                                    │            │
│  │  raw_events ──► Timestamp Align ──► Sequence Validate         │            │
│  │              ──► Schema Normalize ──► Quality Flag             │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ DATA STORES                                                   │            │
│  │  ┌──────────┐ ┌──────────────┐ ┌─────────────┐               │            │
│  │  │ Hot Data │ │ Feature Store│ │ Cold Archive│               │            │
│  │  │ (Redis)  │ │ (computed)   │ │ (S3/Disk)  │               │            │
│  │  └────┬─────┘ └──────┬───────┘ └─────────────┘               │            │
│  │       └──────────────┘                                        │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ FEATURE ENGINEERING                                           │            │
│  │  OHLCV ──► Technical Indicators ──► Derived Features          │            │
│  │        ──► Orderbook Features ──► Sentiment Scores            │            │
│  │        ──► Macro Features ──► Alternative Data Features       │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             │                                                │
│  Output: MarketData, FeatureVector, OrderBookState, SentimentScore           │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: INTELLIGENCE CORE                                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ REGIME DETECTION                                              │            │
│  │  FeatureVector ──► HMM / Clustering ──► MarketRegime          │            │
│  │  (trending_up, trending_down, ranging, volatile, crisis)      │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ ML MODEL ENSEMBLE                                             │            │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │            │
│  │  │ Transformer  │ │ LSTM/GRU     │ │ XGBoost      │          │            │
│  │  │ Attention    │ │ Sequence     │ │ Gradient     │          │            │
│  │  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘          │            │
│  │         └────────────────┴────────────────┘                   │            │
│  │                          ▼                                    │            │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │            │
│  │  │ RL Agent     │ │ Meta-Learn   │ │ Quantum Opt  │          │            │
│  │  │ (CQL/IQL)   │ │ (MAML)       │ │ (QAOA)       │          │            │
│  │  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘          │            │
│  │         └────────────────┴────────────────┘                   │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ MULTIMODAL FUSION                                             │            │
│  │  Price predictions + NLP sentiment + Chart patterns           │            │
│  │  + Orderflow signals + Macro indicators                       │            │
│  │  ──► Attention-weighted fusion ──► Unified Prediction         │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ REASONING ENGINE                                              │            │
│  │  Prediction ──► Chain-of-Thought ──► Causal Analysis          │            │
│  │            ──► Counterfactual ──► Confidence Calibration       │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             │                                                │
│  Output: Prediction, MarketRegime, ConfidenceScore, ReasoningChain           │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: SIGNAL GENERATION                                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ STRATEGY ENGINE                                               │            │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │            │
│  │  │ Trend Follow │ │ Mean Revert  │ │ Momentum     │          │            │
│  │  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘          │            │
│  │  ┌──────┴───────┐ ┌──────┴───────┐ ┌──────┴───────┐          │            │
│  │  │ Arbitrage    │ │ Market Make  │ │ Stat Arb     │          │            │
│  │  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘          │            │
│  │         └────────────────┴────────────────┘                   │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ SIGNAL BLENDER                                                │            │
│  │  Strategy signals ──► Weight by regime ──► Filter by quality  │            │
│  │  ──► Confidence threshold ──► Dedup ──► Rank by strength      │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ OPPORTUNITY SCANNER                                           │            │
│  │  Market inefficiencies + Institutional footprints             │            │
│  │  + Volatility events + Correlation breakdowns                 │            │
│  │  ──► Scored opportunities ──► Merge with strategy signals     │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             │                                                │
│  Output: TradingSignal[] (symbol, direction, confidence, strength,           │
│          stop_loss, take_profit, reasoning, regime, source)                   │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 6: RISK & SAFETY                                                       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ PRE-TRADE RISK CHECK (Gate 1)                                 │            │
│  │  Signal ──► Position size limit? ──► Daily loss limit?        │            │
│  │         ──► Max drawdown? ──► Correlation exposure?           │            │
│  │         ──► Leverage limit? ──► Sector concentration?         │            │
│  │                                                               │            │
│  │  PASS ──► continue          FAIL ──► REJECT signal            │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ POSITION SIZING                                               │            │
│  │  Signal + Portfolio state ──► Kelly Criterion                 │            │
│  │  ──► Risk Parity adjustment ──► Volatility scaling            │            │
│  │  ──► Max position cap ──► Final size                          │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ CIRCUIT BREAKERS                                              │            │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐  │            │
│  │  │ Daily loss > 5% │ │ Drawdown > 20%  │ │ Error rate > X │  │            │
│  │  │ ──► HALT        │ │ ──► REDUCE SIZE │ │ ──► PAUSE      │  │            │
│  │  └─────────────────┘ └─────────────────┘ └────────────────┘  │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ REALITY GATES                                                 │            │
│  │  Signal ──► Sanity check prices ──► Validate market hours     │            │
│  │         ──► Check liquidity ──► Verify spread acceptable      │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             │                                                │
│  Output: RiskApprovedSignal (original signal + position_size +               │
│          risk_score + stop_loss_adjusted + risk_metrics)                      │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 7: DECISION VERIFICATION                                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ MULTI-AGENT DEBATE                                            │            │
│  │                                                               │            │
│  │  RiskApprovedSignal ──► distributed to N agents               │            │
│  │                                                               │            │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │            │
│  │  │ Bull     │  │ Bear     │  │ Neutral  │  │ Devil's  │     │            │
│  │  │ Advocate │  │ Advocate │  │ Analyst  │  │ Advocate │     │            │
│  │  │ score:+  │  │ score:-  │  │ score:0  │  │ score:?  │     │            │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │            │
│  │       └──────────────┴────────────┴──────────────┘            │            │
│  │                      ▼                                        │            │
│  │              Consensus Engine                                 │            │
│  │              (weighted vote)                                  │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ ADVERSARIAL VALIDATION                                        │            │
│  │  Consensus ──► Overfit check ──► Exploit detection            │            │
│  │           ──► Regime robustness ──► Tail risk check           │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             │                                                │
│  Output: VerifiedDecision (action, confidence, consensus_score,              │
│          agent_votes, adversarial_score, final_recommendation)               │
│                                                                              │
│  Decision: EXECUTE | REJECT | REDUCE_SIZE | DEFER                            │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 8: EXECUTION                                                           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ ORDER CONSTRUCTION                                            │            │
│  │  VerifiedDecision ──► Select order type (limit/market/stop)   │            │
│  │  ──► Set price levels ──► Apply slippage model                │            │
│  │  ──► Choose execution algorithm                               │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ EXECUTION ALGORITHMS                                          │            │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐ ┌─────────┐        │            │
│  │  │ TWAP │ │ VWAP │ │ POV  │ │ Adaptive │ │ Iceberg │        │            │
│  │  └──┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘ └────┬────┘        │            │
│  │     └─────────┴────────┴──────────┴────────────┘              │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ SMART ORDER ROUTER                                            │            │
│  │  Order ──► Check venues ──► Compare liquidity                 │            │
│  │        ──► Estimate impact ──► Route to best venue            │            │
│  │        ──► Submit to broker ──► Track fill                    │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ POSITION MANAGER                                              │            │
│  │  Fill ──► Update positions ──► Track P&L                      │            │
│  │       ──► Monitor stop/target ──► Manage exits                │            │
│  │       ──► Trail stops ──► Partial profit taking               │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             │                                                │
│  Output: ExecutionResult (order_id, fill_price, fill_qty,                    │
│          slippage, commission, position_update, pnl)                          │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 9: ORCHESTRATION                                                       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ MASTER ORCHESTRATOR                                           │            │
│  │                                                               │            │
│  │  Manages the complete tick cycle:                             │            │
│  │                                                               │            │
│  │  1. Receive market tick from Layer 2/3                        │            │
│  │  2. Route to Layer 4 for intelligence                         │            │
│  │  3. Collect signals from Layer 5                              │            │
│  │  4. Send through Layer 6 risk gates                           │            │
│  │  5. Verify via Layer 7 multi-agent debate                     │            │
│  │  6. Execute via Layer 8                                       │            │
│  │  7. Record results, update state                              │            │
│  │  8. Feed back to Layer 4 for learning                         │            │
│  │                                                               │            │
│  │  Also manages:                                                │            │
│  │  - Session lifecycle (pre-market, market, post-market)        │            │
│  │  - Strategy activation/deactivation                           │            │
│  │  - Mode switching (aggressive ↔ defensive)                    │            │
│  │  - Auto-optimization cycles                                   │            │
│  │  - Emergency stop coordination                                │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             │                                                │
│  Output: SystemState, SessionMetrics, StrategyPerformance                    │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 10: GOVERNANCE & HUMAN CONTROL                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ APPROVAL WORKFLOW                                             │            │
│  │                                                               │            │
│  │  ┌─────────────────────────────────────────────────┐          │            │
│  │  │ G0: Fully Autonomous                             │          │            │
│  │  │  confidence > 0.9 AND risk_score < 0.3           │          │            │
│  │  │  ──► Auto-execute                                │          │            │
│  │  ├─────────────────────────────────────────────────┤          │            │
│  │  │ G1: Semi-Autonomous                              │          │            │
│  │  │  confidence 0.6-0.9 OR risk_score 0.3-0.7        │          │            │
│  │  │  ──► System approves with logging                │          │            │
│  │  ├─────────────────────────────────────────────────┤          │            │
│  │  │ G2: Human Required                               │          │            │
│  │  │  confidence < 0.6 OR risk_score > 0.7            │          │            │
│  │  │  ──► Queue for human approval                    │          │            │
│  │  └─────────────────────────────────────────────────┘          │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ AUDIT & COMPLIANCE                                            │            │
│  │  Every action ──► Immutable audit log                         │            │
│  │  ──► Compliance check ──► Regulatory reporting                │            │
│  │  ──► Trade journal entry ──► Performance attribution          │            │
│  └──────────────────────────┬───────────────────────────────────┘            │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │ KILL SWITCH                                                   │            │
│  │  Emergency ──► Cancel all orders ──► Close all positions      │            │
│  │           ──► Halt all layers ──► Notify human                │            │
│  └──────────────────────────────────────────────────────────────┘            │
│                                                                              │
│  Output: AuditRecord, ComplianceReport, GovernanceDecision                   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Data Flow: Single Trade Lifecycle

### Phase 1: Data Ingestion (Layers 0-3)

```
External Exchange (Binance)
    │
    ▼
[Layer 0] Infrastructure checks network, allocates resources
    │
    ▼
[Layer 1] Observability starts trace ID: TRC-20260206-001
    │
    ▼
[Layer 2] WebSocket receives raw tick:
    │   {
    │     "symbol": "BTCUSDT",
    │     "price": 50200.00,
    │     "volume": 1.5,
    │     "timestamp": 1738857600000
    │   }
    │
    ▼
[Layer 3] Normalizer produces:
        MarketData {
          symbol: "BTCUSDT"
          open: 50150.00
          high: 50250.00
          low: 50100.00
          close: 50200.00
          volume: 1500.0
          timeframe: M1
          features: {
            rsi_14: 62.5
            macd_signal: 0.0012
            bb_position: 0.65
            atr_14: 350.0
            volume_ratio: 1.2
            orderbook_imbalance: 0.15
            sentiment_score: 0.6
          }
        }
```

### Phase 2: Analysis & Intelligence (Layer 4)

```
MarketData + FeatureVector
    │
    ▼
[Regime Detection]
    │   regime: TRENDING_UP (confidence: 0.82)
    │
    ▼
[ML Ensemble]
    │   ┌─ Transformer: +0.72 (bullish)
    │   ├─ LSTM:        +0.68 (bullish)
    │   ├─ XGBoost:     +0.75 (bullish)
    │   ├─ RL Agent:    +0.65 (bullish)
    │   └─ Meta-Learn:  +0.70 (bullish)
    │
    │   Ensemble prediction: +0.70 (bullish)
    │
    ▼
[Multimodal Fusion]
    │   Price model:    0.70 (weight: 0.30)
    │   Sentiment:      0.60 (weight: 0.15)
    │   Orderflow:      0.72 (weight: 0.15)
    │   Chart pattern:  0.65 (weight: 0.10)
    │   Fundamental:    0.55 (weight: 0.15)
    │   On-chain:       0.68 (weight: 0.05)
    │
    │   Fused score: 0.66
    │
    ▼
[Reasoning Engine]
    │   Chain-of-thought:
    │   1. Regime is trending up (strong)
    │   2. Volume confirms trend (1.2x average)
    │   3. RSI not overbought (62.5 < 70)
    │   4. Orderbook shows buy pressure (+0.15 imbalance)
    │   5. Sentiment supportive (0.6)
    │   Conclusion: BUY with 0.66 confidence
    │
    Output: Prediction {
      direction: BUY
      confidence: 0.66
      regime: TRENDING_UP
      reasoning: [5 steps]
    }
```

### Phase 3: Signal Generation (Layer 5)

```
Prediction + MarketData
    │
    ▼
[Strategy Engine]
    │   ┌─ Trend Following:  BUY  (conf: 0.72)
    │   ├─ Momentum:         BUY  (conf: 0.68)
    │   ├─ Mean Reversion:   HOLD (conf: 0.40)
    │   └─ Stat Arb:         BUY  (conf: 0.55)
    │
    ▼
[Signal Blender]
    │   Regime-weighted blend (trending_up favors trend/momentum):
    │   Trend: 0.72 × 0.40 = 0.288
    │   Momentum: 0.68 × 0.30 = 0.204
    │   Mean Rev: 0.40 × 0.10 = 0.040
    │   Stat Arb: 0.55 × 0.20 = 0.110
    │   Blended confidence: 0.642
    │
    ▼
[Opportunity Scanner]
    │   No additional opportunities detected
    │
    Output: TradingSignal {
      signal_id: "SIG-20260206-001"
      symbol: "BTCUSDT"
      direction: BUY
      confidence: 0.642
      strength: MODERATE
      stop_loss: 49500.0  (ATR-based: price - 2×ATR)
      take_profit: 51250.0 (1.5:1 R:R)
      regime: TRENDING_UP
      source: ENSEMBLE
      reasoning: "Trend + momentum convergence in uptrend"
    }
```

### Phase 4: Risk Assessment (Layer 6)

```
TradingSignal
    │
    ▼
[Pre-Trade Risk Check]
    │   ✓ Position size within 10% limit
    │   ✓ Daily loss at 1.2% (limit: 5%)
    │   ✓ Drawdown at 8% (limit: 20%)
    │   ✓ Correlation exposure OK
    │   ✓ Leverage at 1.5x (limit: 5x)
    │   Result: PASS
    │
    ▼
[Position Sizing]
    │   Capital: $10,000
    │   Risk per trade: 2% = $200
    │   Stop distance: $700 (50200 - 49500)
    │   Kelly fraction: 0.12
    │   Volatility-adjusted: 0.08
    │   Position size: $200 / $700 = 0.286 BTC
    │   Capped at: 0.20 BTC (max position rule)
    │
    ▼
[Circuit Breakers]
    │   ✓ No circuit breakers triggered
    │
    ▼
[Reality Gates]
    │   ✓ Price within expected range
    │   ✓ Market hours: YES
    │   ✓ Spread: 0.01% (acceptable)
    │   ✓ Liquidity: sufficient
    │
    Output: RiskApprovedSignal {
      ...original signal...
      position_size: 0.20 BTC
      risk_amount: $140
      risk_score: 0.35
      risk_reward_ratio: 1.5
    }
```

### Phase 5: Decision Verification (Layer 7)

```
RiskApprovedSignal
    │
    ▼
[Multi-Agent Debate]
    │
    │   Bull Advocate:    EXECUTE  (score: 0.78)
    │     "Strong trend, volume confirms, risk controlled"
    │
    │   Bear Advocate:    CAUTION  (score: 0.42)
    │     "RSI approaching overbought, resistance at 50500"
    │
    │   Neutral Analyst:  EXECUTE  (score: 0.65)
    │     "Favorable risk/reward, regime supports"
    │
    │   Devil's Advocate: EXECUTE  (score: 0.60)
    │     "No critical flaws found in thesis"
    │
    │   Consensus: EXECUTE (weighted: 0.64)
    │
    ▼
[Adversarial Validation]
    │   ✓ Not overfit (pattern diversity OK)
    │   ✓ No exploit detected
    │   ✓ Regime-robust (tested across 3 regimes)
    │   ✓ Tail risk acceptable
    │
    Output: VerifiedDecision {
      action: EXECUTE
      confidence: 0.64
      consensus_score: 0.64
      agent_votes: {bull: 0.78, bear: 0.42, neutral: 0.65, devil: 0.60}
      adversarial_score: 0.88
    }
```

### Phase 6: Execution (Layer 8)

```
VerifiedDecision
    │
    ▼
[Order Construction]
    │   Order type: LIMIT (confidence < 0.8)
    │   Price: 50200.00 (current ask)
    │   Quantity: 0.20 BTC
    │   Algorithm: Adaptive
    │
    ▼
[Execution Algorithm: Adaptive]
    │   Phase 1: Place limit at 50195 (slightly below ask)
    │   Phase 2: Wait 5s... not filled
    │   Phase 3: Adjust to 50200 (at ask)
    │   Phase 4: Filled 0.15 BTC @ 50200
    │   Phase 5: Remaining 0.05 BTC @ 50202 (market)
    │
    ▼
[Smart Order Router]
    │   Venue: Binance (best liquidity)
    │   Submitted via broker adapter
    │
    ▼
[Position Manager]
    │   New position opened:
    │   BTCUSDT LONG 0.20 BTC @ avg 50200.50
    │   Stop loss set: 49500.00
    │   Take profit set: 51250.00
    │
    Output: ExecutionResult {
      order_id: "ORD-20260206-001"
      fill_price: 50200.50
      fill_qty: 0.20
      slippage: 0.001%
      commission: $2.01
      status: FILLED
    }
```

### Phase 7: Orchestration & Feedback (Layer 9)

```
ExecutionResult
    │
    ▼
[Master Orchestrator]
    │   ✓ Trade recorded in session
    │   ✓ Portfolio state updated
    │   ✓ Risk metrics recalculated
    │   ✓ Performance metrics updated
    │
    │   Feedback loop:
    │   ExecutionResult ──► Layer 4 (update ML models)
    │                  ──► Layer 5 (update strategy weights)
    │                  ──► Layer 6 (update risk state)
    │
    │   Session state:
    │   {
    │     trades_today: 3
    │     win_rate_today: 0.67
    │     pnl_today: +$45.20
    │     open_positions: 1
    │   }
```

### Phase 8: Governance & Audit (Layer 10)

```
All actions from above
    │
    ▼
[Audit Logger]
    │   Immutable record:
    │   {
    │     trace_id: "TRC-20260206-001"
    │     signal_id: "SIG-20260206-001"
    │     order_id: "ORD-20260206-001"
    │     timestamp: "2026-02-06T16:00:00Z"
    │     action: "BUY"
    │     symbol: "BTCUSDT"
    │     quantity: 0.20
    │     price: 50200.50
    │     risk_score: 0.35
    │     consensus_score: 0.64
    │     governance_tier: "G1_SEMI_AUTONOMOUS"
    │     approved_by: "system_rules"
    │     reasoning: "Trend + momentum convergence"
    │   }
    │
    ▼
[Compliance Check]
    │   ✓ Within position limits
    │   ✓ Within daily trade count
    │   ✓ No wash trading detected
    │   ✓ Regulatory compliant
    │
    ▼
[Trade Journal]
        Entry saved for post-trade analysis
```

---

## Feedback Loops (Continuous Learning)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOPS                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ LOOP 1: Immediate (per-tick)                             │    │
│  │  Execution result ──► Update position P&L                │    │
│  │  ──► Recalculate risk metrics ──► Adjust stops           │    │
│  │  Latency: <100ms                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ LOOP 2: Short-term (per-trade)                           │    │
│  │  Trade outcome ──► Update strategy weights               │    │
│  │  ──► Adjust signal confidence thresholds                 │    │
│  │  ──► Update regime detection                             │    │
│  │  Latency: seconds                                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ LOOP 3: Medium-term (daily)                              │    │
│  │  Daily performance ──► Retrain online models             │    │
│  │  ──► Update risk parameters ──► Rebalance portfolio      │    │
│  │  ──► Adjust execution algorithms                         │    │
│  │  Latency: minutes                                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ LOOP 4: Long-term (weekly/monthly)                       │    │
│  │  Performance review ──► Full model retraining            │    │
│  │  ──► Strategy evolution ──► Architecture optimization    │    │
│  │  ──► Hyperparameter search ──► Backtest validation       │    │
│  │  Latency: hours                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ LOOP 5: Evolutionary (continuous)                        │    │
│  │  Market regime shifts ──► Adapt entire system            │    │
│  │  ──► Discover new alpha ──► Genetic strategy evolution   │    │
│  │  ──► Self-improvement proposals ──► Human approval       │    │
│  │  Latency: days to weeks                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cross-Layer Communication Patterns

```
┌──────────────────────────────────────────────────────────────────┐
│                 COMMUNICATION PATTERNS                            │
│                                                                  │
│  1. TOP-DOWN (Command flow)                                      │
│     Layer 10 ──► Layer 9 ──► Layer 8 ──► ... ──► Layer 0         │
│     "Governance commands flow downward"                          │
│                                                                  │
│  2. BOTTOM-UP (Data flow)                                        │
│     Layer 0 ──► Layer 1 ──► Layer 2 ──► ... ──► Layer 10         │
│     "Market data flows upward through processing"                │
│                                                                  │
│  3. LATERAL (Peer communication)                                 │
│     Layer 4 ◄──► Layer 5  (intelligence ↔ signals)               │
│     Layer 6 ◄──► Layer 7  (risk ↔ decision)                      │
│     Layer 8 ◄──► Layer 6  (execution ↔ risk monitoring)          │
│                                                                  │
│  4. BROADCAST (System-wide events)                               │
│     Layer 1 ──► ALL  (observability monitors everything)         │
│     Layer 10 ──► ALL (emergency stop reaches all layers)         │
│     Layer 6 ──► ALL  (circuit breaker halts everything)          │
│                                                                  │
│  5. FEEDBACK (Learning loops)                                    │
│     Layer 8 ──► Layer 4  (execution results → model updates)     │
│     Layer 8 ──► Layer 5  (trade outcomes → strategy weights)     │
│     Layer 8 ──► Layer 6  (fills → risk state updates)            │
│     Layer 10 ──► Layer 4 (human feedback → model corrections)    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Types at Each Layer Boundary

```
Layer 0 → 1:  HealthMetrics, ResourceStatus, SystemLoad
Layer 1 → 2:  LogEntry, MetricPoint, TraceSpan, Alert
Layer 2 → 3:  RawMarketEvent, RawTrade, RawQuote, RawOrderBook
Layer 3 → 4:  MarketData, FeatureVector, OrderBookState, SentimentScore
Layer 4 → 5:  Prediction, MarketRegime, ConfidenceScore, ReasoningChain
Layer 5 → 6:  TradingSignal (direction, confidence, stops, reasoning)
Layer 6 → 7:  RiskApprovedSignal (signal + position_size + risk_metrics)
Layer 7 → 8:  VerifiedDecision (action, consensus, adversarial_score)
Layer 8 → 9:  ExecutionResult (fills, slippage, commission, position)
Layer 9 → 10: SessionMetrics, StrategyPerformance, SystemState
Layer 10 → 9: GovernanceDecision (approve/reject/halt), PolicyUpdate
```

---

## Emergency Data Flow (Kill Switch)

```
EMERGENCY TRIGGER (any source)
    │
    ├──► Layer 10: Governance logs emergency
    │       │
    │       ▼
    ├──► Layer 9: Orchestrator halts all cycles
    │       │
    │       ▼
    ├──► Layer 8: Cancel ALL open orders
    │       │     Close ALL positions (market orders)
    │       ▼
    ├──► Layer 7: Reject ALL pending decisions
    │       │
    │       ▼
    ├──► Layer 6: Activate maximum risk protection
    │       │
    │       ▼
    ├──► Layer 5: Stop ALL signal generation
    │       │
    │       ▼
    ├──► Layer 4: Pause ALL model inference
    │       │
    │       ▼
    ├──► Layer 3: Flush data buffers
    │       │
    │       ▼
    ├──► Layer 2: Maintain connections (for order cancellation)
    │       │
    │       ▼
    ├──► Layer 1: Log everything, send alerts
    │       │
    │       ▼
    └──► Layer 0: Report final system state
    
    Total emergency shutdown time target: < 5 seconds
```

---

*Generated: 2026-02-06*
*System: Unified Trading System v3.0*
*Modules: 194 | Layers: 11 | Files: 3,150+*
