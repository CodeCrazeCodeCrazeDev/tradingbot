# GETS: Governed Evolving Time-Series Foundation System

A hierarchical temporal intelligence stack that extracts edge from the structure of agreement, disagreement, stability, and uncertainty across multiple foundation time-series models—operating under strict governance with bounded, auditable, reversible evolution.

## Architecture Overview

GETS consists of five layers with strict separation of concerns:

```
Layer 1: Temporal Perception
    ↓
Layer 2: Forecast & Representation  
    ↓
Layer 3: Self-Diagnosis
    ↓
Layer 4: Controlled Evolution  (SANDBOX ONLY)
    ↓
Layer 5: Governance & Promotion
```

**Core Principle:**
- **Inference** (live): predicts, embeds, scores uncertainty—never rewrites itself
- **Adaptation** (offline): studies failures, proposes improvements
- **Evolution** (sandbox): tests mutations, validates changes
- **Promotion** (governance): audited, champion-challenger validated upgrades only

## Quick Start

```python
from trading_bot.gets import create_gets, GETSConfig
from trading_bot.gets.integration import MarketDataAdapter
from trading_bot.gets.types import ForecastHorizon

# Create and initialize GETS
gets = create_gets()
gets.initialize()

# Create market data
market_data = MarketDataAdapter.from_price_dict(
    price_data={
        'open': 150.0, 'high': 152.5, 'low': 149.5, 'close': 151.0,
        'volume': 1000000, 'spread': 0.001, 'volatility': 0.25
    },
    symbol="AAPL"
)

# Generate signal
signal = gets.generate_signal(market_data, ForecastHorizon.SHORT)

print(f"Direction: {signal.direction}")
print(f"Confidence: {signal.confidence:.2%}")
print(f"Expected Edge: {signal.expected_edge:.4f}")
print(f"Governance Decision: {signal.governance_decision.name}")
```

## The Five Layers

### Layer 1: Temporal Perception

Foundation model inference layer supporting:

| Model | Role | Best For |
|-------|------|----------|
| **Kronos** | Market-sequence encoder | OHLCV forecasting, volatility features |
| **TimesFM 2.5** | Long-context forecaster | Regime memory, scenario generation |
| **Moirai 2.0** | Multivariate forecaster | Cross-asset consistency, portfolio context |
| **TinyTimeMixers** | Fast inference | Execution-time decisions, CPU fallback |

**Key Capabilities:**
- Multi-horizon probabilistic forecasts (quantile fan)
- Latent temporal embeddings
- Volatility path predictions
- Regime state encodings
- Synthetic K-line generation for stress testing

### Layer 2: Forecast & Representation

Trading-native multi-task heads on frozen foundation backbones:

**Prediction Heads:**
- Expected signed return (direction + magnitude)
- Volatility forecast (realized vs implied)
- Drawdown risk probability
- Rank score across assets (pairwise)
- Probability of move exceeding cost threshold
- Regime label classification
- Execution difficulty score
- **Edge-after-cost** (primary trading signal)

**Regime-Conditioned Adapters:**
- LoRA adapters by asset class
- Adapters by timeframe
- Adapters by volatility regime
- Adapters by venue type

**Multi-Task Loss Functions:**
- Standard MSE/quantile loss
- Pairwise ranking loss
- Top-k hit optimization
- Information coefficient objective
- Long-short spread objective

### Layer 3: Self-Diagnosis

Introspection engine that validates every forecast:

**Per-Forecast Diagnostics:**
1. **Forecast Stability Testing** - Perturbation sensitivity analysis
2. **Model Disagreement Topology** - Cross-model divergence as signal
3. **Evidence Sufficiency Check** - Data quality thresholds
4. **Contradiction Detection** - Sign conflict identification
5. **Regime Mismatch Assessment** - Out-of-regime confidence discounting
6. **Calibration Drift Detection** - Predicted vs realized tracking
7. **Execution Feasibility Check** - Edge > cost, liquidity sufficiency

**Disagreement Geometry:**
The system extracts edge from model disagreement patterns:

| Pattern | Interpretation |
|---------|---------------|
| Kronos ↑ vs TimesFM ↓ | Short momentum vs long mean-reversion |
| Moirai high variance | Cross-asset uncertainty elevated |
| TTM stable, others volatile | Local predictability, structural uncertainty |
| All models converging | High-confidence consensus (crowding warning) |
| Uncertainty fan expanding | Information entropy increasing |

### Layer 4: Controlled Evolution

**SANDBOX ONLY** - Live system never self-modifies.

**Failure Analysis Pipeline:**
- Cluster failed predictions by regime, horizon, asset
- Root-cause decomposition
- Blind spot identification per model

**Mutation Proposal Engine:**
- LoRA rank adjustments
- Adapter alpha tuning
- Head architecture mutations
- Fusion weight rebalancing

**Champion-Challenger Testing:**
- Hold-out period backtesting
- Paper trading validation
- Statistical significance testing
- Drawdown stress testing
- Cross-regime validation

### Layer 5: Governance & Promotion

**Promotion Gates:**
1. Statistical Validation (1000+ OOS predictions, significant IC improvement)
2. Regime Coverage (all major regimes)
3. Risk Controls Review (max drawdown validation)
4. Execution Reality Check (edge > cost verified)
5. Rollback Readiness (complete backup state)

**Audit Trail:**
- Immutable hash-chained promotion records
- Full provenance tracking
- Human-in-the-loop option
- One-click rollback capability

## Safety Architecture

**The System Must Never:**

1. ❌ Rewrite live execution logic (all changes through promotion pipeline)
2. ❌ Change risk controls automatically (explicit governance approval required)
3. ❌ Learn from contaminated labels (strict temporal cross-validation)
4. ❌ Promote without statistical proof (champion-challenger required)
5. ❌ Optimize RMSE/MAE alone (trading-relevant objectives only)
6. ❌ Average across incompatible regimes (regime-conditioned adapters mandatory)
7. ❌ Ignore execution costs (edge-after-cost head required)

## Integration

### Decision Governance System (DGS)

GETS integrates with the existing 7-layer DGS:

```python
from trading_bot.gets.integration import create_integrated_gets

gets, dgs_adapter, trading_bridge = create_integrated_gets(
    config=None,
    enable_dgs=True,
    enable_trading_bridge=True
)
```

### Trading Execution

Convert GETS signals to orders:

```python
order = trading_bridge.signal_to_order(
    signal,
    portfolio_value=100000.0,
    current_position=0.0
)
```

## Configuration

```python
from trading_bot.gets.types import GETSConfig

config = GETSConfig(
    # Foundation models
    kronos_enabled=True,
    timesfm_enabled=True,
    moirai_enabled=True,
    ttm_enabled=True,
    
    # LoRA adapters
    use_lora_adapters=True,
    lora_rank=8,
    lora_alpha=16.0,
    
    # Diagnosis thresholds
    stability_threshold=0.7,
    evidence_threshold=0.6,
    regime_mismatch_threshold=0.8,
    
    # Evolution
    sandbox_path="./gets_sandbox",
    min_backtest_samples=1000,
    significance_threshold=0.05,
    
    # Governance
    require_human_promotion=True,
    audit_storage_path="./gets_audit",
    max_drawdown_tolerance=0.15,
    
    # Integration
    decision_governance_integration=True
)
```

## Example Usage

See `example_usage.py` for comprehensive examples:
- Basic signal generation
- Custom configuration
- Full DGS integration
- Evolution workflow
- Multi-horizon analysis

## Directory Structure

```
trading_bot/gets/
├── __init__.py              # Package initialization
├── types.py                 # Core data types and enums
├── gets_system.py           # Main system orchestrator
├── integration.py           # External system integration
├── example_usage.py         # Usage examples
├── core/
│   ├── __init__.py
│   ├── temporal_perception.py      # Layer 1
│   ├── forecast_representation.py  # Layer 2
│   ├── self_diagnosis.py           # Layer 3
│   ├── controlled_evolution.py   # Layer 4
│   └── governance_promotion.py   # Layer 5
```

## Success Metrics

**Forecast Quality (Secondary):**
- RMSE/MAE by horizon
- Quantile calibration error

**Decision Quality (Primary):**
- Information coefficient (IC)
- Edge-after-cost hit rate
- Abstention accuracy

**System Health:**
- Disagreement topology stability
- Calibration drift rate
- Promotion frequency (should be rare)
- Rollback frequency (should be very rare)

**Trading Performance:**
- Sharpe ratio by regime
- Max drawdown recovery time
- Capacity utilization
- Cost-adjusted returns

## License

Part of the AlphaAlgo trading system.
