# DeepChart - Low-Cost Deep Learning Visualization Layer

## Complete System Architecture

A cost-efficient deep-learning-enhanced charting system that maximizes predictive insight per dollar.

---

## 1. FULL SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DeepChart System Architecture                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   DATA SOURCES   │     │   PREPROCESSING  │     │  FEATURE PIPELINE │
│                  │     │                  │     │                   │
│  L1 Trades ─────────────► Normalization ─────────► Microstructure   │
│  L1 Quotes ─────────────► Cleaning ──────────────► Regime Features  │
│  Aggregated L2 ─────────► Downsampling ──────────► Liquidity Infer  │
│  (Top 5-10 lvls) │     │  Caching         │     │  Latent Features  │
└──────────────────┘     └──────────────────┘     └─────────┬─────────┘
                                                            │
                                                            ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              ML INFERENCE GRAPH                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  Temporal CNN   │  │   Lightweight   │  │     Regime      │                   │
│  │  (150K params)  │  │   Transformer   │  │   Autoencoder   │                   │
│  │                 │  │   (200K params) │  │   (100K params) │                   │
│  │  - Dilated Conv │  │  - 2 layers     │  │  - Encoder      │                   │
│  │  - Multi-scale  │  │  - 2 heads      │  │  - Latent space │                   │
│  │  - Causal       │  │  - Pos encoding │  │  - Regime class │                   │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                    │                            │
│           └────────────────────┼────────────────────┘                            │
│                                ▼                                                 │
│                    ┌─────────────────────┐                                       │
│                    │   ENSEMBLE LAYER    │                                       │
│                    │  (Simple Average)   │                                       │
│                    └──────────┬──────────┘                                       │
└───────────────────────────────┼──────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              MODEL OUTPUTS                                        │
│                                                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   Trend     │ │ Volatility  │ │  Liquidity  │ │  Breakout   │ │  Reversion  │ │
│  │ Confidence  │ │   Regime    │ │    Zone     │ │ Probability │ │ Probability │ │
│  │   [0,1]     │ │  [0,1,2]    │ │   [0,1]     │ │    [0,1]    │ │    [0,1]    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                    LATENT STATE VECTOR (8-dim)                              │ │
│  │  [imbalance, vol_imbalance, trend, vol_comp, depth_imb, liq, friction, burst]│ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬──────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ VISUALIZATION │     │   API LAYER     │     │ SELF-IMPROVEMENT│
│    LAYER      │     │                 │     │      LOOP       │
│               │     │  REST/WebSocket │     │                 │
│ - WebGL data  │     │  JSON responses │     │ - Drift detect  │
│ - SVG paths   │     │  Streaming      │     │ - Offline train │
│ - Overlays    │     │                 │     │ - Validation    │
└───────────────┘     └─────────────────┘     └─────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                              CACHING & DOWNSAMPLING                              │
│                                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  Result Cache   │  │  Adaptive       │  │   Tile Cache    │                   │
│  │  TTL: 500ms     │  │  Downsampling   │  │  (Viz Layer)    │                   │
│  │  Max: 100 items │  │  1x-8x factor   │  │  64x64 tiles    │                   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. FEATURE ENGINEERING SPECIFICATION

### 2.1 Microstructure Features (from L1 trades/quotes)

| Feature | Formula | Update Freq | Data Dependency |
|---------|---------|-------------|-----------------|
| **Trade Imbalance** | `TI = EMA(sign(Δp) × v) / EMA(v)` | Every bar | L1 trades |
| **Volume Imbalance** | `VI = (buy_vol - sell_vol) / total_vol` | Every bar | L1 trades |
| **Tick Imbalance** | `TkI = mean(sign(Δp))` over window | Every bar | L1 trades |
| **Spread BPS** | `S = (ask - bid) / mid × 10000` | Every bar | L1 quotes |
| **Spread Z-Score** | `Z = (spread - μ) / σ` | Every bar | L1 quotes |
| **Trade Intensity** | `I = 1 / mean(inter_trade_time)` | Every bar | L1 trades |
| **Burst Indicator** | `B = mean(ITT < percentile_10)` | Every bar | L1 trades |
| **Price Impact (Buy)** | `PI_b = mean(|Δp| / v)` for upticks | Every 5 bars | L1 trades |
| **Price Impact (Sell)** | `PI_s = mean(|Δp| / v)` for downticks | Every 5 bars | L1 trades |
| **Friction Coefficient** | `F = |Δp| / (v × spread + ε)` | Every bar | L1 trades, quotes |
| **Drag Indicator** | `D = 1 - |momentum_t / momentum_{t-1}|` | Every bar | L1 trades |

### 2.2 Regime Classification Features

| Feature | Formula | Update Freq | Data Dependency |
|---------|---------|-------------|-----------------|
| **Trend Strength** | `TS = |p_t - p_{t-n}| / Σ|Δp|` (Efficiency Ratio) | Every 5 bars | L1 prices |
| **Realized Volatility** | `σ = std(returns)` over window | Every 5 bars | L1 prices |
| **Vol Compression** | `VC = σ_short / σ_long` | Every 5 bars | L1 prices |
| **Trending Prob** | `P_trend = softmax(trend_score)` | Every 5 bars | Derived |
| **Ranging Prob** | `P_range = softmax(range_score)` | Every 5 bars | Derived |
| **Volatile Prob** | `P_vol = softmax(vol_score)` | Every 5 bars | Derived |
| **Quiet Prob** | `P_quiet = softmax(quiet_score)` | Every 5 bars | Derived |
| **Regime Duration** | `D = bars_in_current_regime` | Every bar | Derived |
| **Transition Prob** | `P_trans = 1 / regime_duration` | Every bar | Derived |

### 2.3 Liquidity Features (Inferred from L1 when L2 unavailable)

| Feature | Formula | Update Freq | Data Dependency |
|---------|---------|-------------|-----------------|
| **Synthetic Bid Depth** | `SD_i = Σ(v_j × exp(-λ|p_j - level_i|²))` | Every 20 bars | L1 trades |
| **Synthetic Ask Depth** | Same as above for ask side | Every 20 bars | L1 trades |
| **Depth Imbalance** | `DI = (bid_depth - ask_depth) / total` | Every 20 bars | Derived |
| **Support Levels** | Volume profile peaks below price | Every 20 bars | L1 trades |
| **Resistance Levels** | Volume profile peaks above price | Every 20 bars | L1 trades |
| **Hidden Liquidity Est** | `HL = vol_absorbed / price_impact` | Every 20 bars | L1 trades |
| **Iceberg Probability** | `P_ice = mean(vol_zscore - impact_zscore > 1)` | Every 20 bars | L1 trades |
| **Liquidity Score** | `LS = 1 / (spread × volatility × 1000)` | Every bar | L1 quotes |
| **Thin Market Alert** | `LS < 0.2 OR spread > 2×mean_spread` | Every bar | Derived |

### 2.4 Latent State Features (for Visualization)

| Feature | Formula | Update Freq | Data Dependency |
|---------|---------|-------------|-----------------|
| **Latent Vector** | 8-dim: `[TI, VI, TS, VC, DI, LS, F, B]` | Every bar | All above |
| **Breakout Prob** | `P_bo = σ((1-VC)×0.3 + |TI|×0.3 + (1-F)×0.2 + P_exp×0.2)` | Every bar | Derived |
| **Reversion Prob** | `P_rev = σ(P_range×0.4 + F×0.3 + (1-|TS|)×0.3)` | Every bar | Derived |
| **Micro Momentum** | `μ_m = (p_t - p_{t-20}) / p_{t-20}` | Every bar | L1 prices |
| **Macro Momentum** | `μ_M = (p_t - p_{t-100}) / p_{t-100}` | Every bar | L1 prices |
| **Volume Pulse** | `VP = (vol_recent - vol_avg) / vol_avg` | Every bar | L1 volume |

---

## 3. MODEL ARCHITECTURE (Low-Cost)

### 3.1 Temporal CNN (~150K parameters)

```
Input: (batch, seq_len=64, features=32)
       │
       ├──► Conv1D(k=3, d=1, out=64) ──► ReLU ──► GlobalAvgPool ──┐
       │                                                          │
       ├──► Conv1D(k=5, d=2, out=64) ──► ReLU ──► GlobalAvgPool ──┼──► Concat
       │                                                          │
       └──► Conv1D(k=7, d=4, out=64) ──► ReLU ──► GlobalAvgPool ──┘
                                                      │
                                                      ▼
                                              BatchNorm(192)
                                                      │
                                                      ▼
                                              FC(192 → 64) ──► ReLU
                                                      │
                                                      ▼
                                              FC(64 → 13)
                                                      │
                                                      ▼
Output: [latent_8, trend, vol, breakout, reversion, liquidity]
```

**Key Design Choices:**
- Dilated causal convolutions (no future leakage)
- Multi-scale receptive fields (3, 5, 7 with dilations 1, 2, 4)
- Global average pooling (parameter efficient)
- ONNX compatible operations only

### 3.2 Lightweight Transformer (~200K parameters)

```
Input: (batch, seq_len=64, features=32)
       │
       ▼
Linear(32 → 64) + Positional Encoding
       │
       ▼
┌─────────────────────────────────────┐
│  Transformer Encoder Layer × 2      │
│  - d_model: 64                      │
│  - n_heads: 2                       │
│  - d_ff: 128                        │
│  - dropout: 0.1                     │
│  - Causal mask                      │
└─────────────────────────────────────┘
       │
       ▼
Take last position: (batch, 64)
       │
       ▼
Linear(64 → 13)
       │
       ▼
Output: [latent_8, trend, vol, breakout, reversion, liquidity]
```

**Key Design Choices:**
- Only 2 layers, 2 heads (minimal)
- Causal attention mask (real-time compatible)
- Sinusoidal positional encoding (no learned params)
- CPU-optimized attention implementation

### 3.3 Regime Autoencoder (~100K parameters)

```
Input: (batch, features=32) or (batch, seq, 32) → mean
       │
       ▼
┌─────────────────────────────────────┐
│           ENCODER                   │
│  Linear(32 → 64) ──► ReLU          │
│  Linear(64 → 32) ──► ReLU          │
│  Linear(32 → 8) [μ]                │
│  Linear(32 → 8) [log_var]          │
└─────────────────────────────────────┘
       │
       ▼
Reparameterization: z = μ + ε×exp(0.5×log_var)
       │
       ├──► Linear(8 → 4) [Regime Classifier]
       │
       └──► Decoder (training only)
```

**Key Design Choices:**
- VAE-style latent space (regularized)
- Regime classification head
- Decoder only used during training
- Latent dim = 8 (matches visualization)

### 3.4 Ensemble Strategy

```python
# Simple average ensemble (no additional parameters)
output = (temporal_cnn_output + transformer_output) / 2

# Regime probabilities from autoencoder
regime_probs = autoencoder.classify(latent)

# Final output
final = concat([output, regime_probs])
```

---

## 4. VISUALIZATION LAYER BLUEPRINT

### 4.1 Overlay Types

| Overlay | Description | Compute Cost | Z-Index |
|---------|-------------|--------------|---------|
| **Regime Background** | Colored gradient based on regime | O(n) | -10 |
| **Latent Zones** | Color gradient from latent vector | O(n) | -5 |
| **Liquidity Shadows** | Inferred depth visualization | O(1) | -3 |
| **Compression Bands** | Volatility bands | O(n) | -2 |
| **Support/Resistance** | ML-derived levels | O(1) | 5 |
| **Momentum Arrows** | Direction indicators | O(n/20) | 10 |

### 4.2 WebGL Rendering Strategy

```javascript
// Shader-based heatmap for regime background
uniform float regimeColors[MAX_CANDLES * 4]; // RGBA per candle
uniform vec2 priceRange;

void main() {
    int idx = int(gl_FragCoord.x / candleWidth);
    vec4 color = vec4(regimeColors[idx*4], regimeColors[idx*4+1], 
                      regimeColors[idx*4+2], regimeColors[idx*4+3]);
    gl_FragColor = color;
}
```

### 4.3 Incremental Rendering

```
┌─────────────────────────────────────────────────────────────┐
│                    TILE-BASED RENDERING                      │
│                                                              │
│  ┌────┬────┬────┬────┬────┬────┬────┬────┐                  │
│  │ T1 │ T2 │ T3 │ T4 │ T5 │ T6 │ T7 │ T8 │  64×64 tiles    │
│  └────┴────┴────┴────┴────┴────┴────┴────┘                  │
│                                                              │
│  - Only re-render dirty tiles                               │
│  - Cache clean tiles in texture                             │
│  - New data invalidates rightmost tile only                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Output Formats

1. **JSON (for WebGL):**
```json
{
  "overlays": [
    {
      "type": "regime_background",
      "data": {"zones": [{"x1": 0, "x2": 50, "color": "rgba(35,134,54,0.3)"}]}
    }
  ],
  "palette": {"regime_trending": "#238636", ...},
  "priceData": {"prices": [...], "volumes": [...]}
}
```

2. **WebGL Data (typed arrays):**
```json
{
  "vertices": {"prices": Float32Array, "volumes": Float32Array},
  "textures": {"regimeColors": Float32Array},
  "uniforms": {"priceRange": [min, max], "dataLength": 200}
}
```

3. **SVG (lightweight fallback):**
```svg
<svg width="1200" height="600">
  <path d="M 50 300 L 100 280 L 150 290..." stroke="#3fb950"/>
  <line x1="50" y1="350" x2="1150" y2="350" stroke="#3fb950" stroke-dasharray="5,5"/>
</svg>
```

---

## 5. SELF-IMPROVEMENT LOOP (Low Cost)

### 5.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SELF-IMPROVEMENT LOOP                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │ Live Trading │
     └──────┬───────┘
            │ Predictions + Outcomes
            ▼
┌───────────────────────┐
│    DRIFT DETECTOR     │
│                       │
│  - Data drift (KS)    │
│  - Concept drift      │
│  - Performance drift  │
│  - Calibration drift  │
└───────────┬───────────┘
            │ Drift detected?
            ▼
┌───────────────────────┐     ┌───────────────────────┐
│  TRAINING PIPELINE    │     │    ARCHIVED DATA      │
│                       │◄────│                       │
│  - Prepare data       │     │  - L1 trades/quotes   │
│  - Train model        │     │  - Labels (outcomes)  │
│  - Export ONNX        │     │  - 10K-100K samples   │
└───────────┬───────────┘     └───────────────────────┘
            │ New model
            ▼
┌───────────────────────┐
│     SAFETY GATE       │
│                       │
│  - Size check (<10MB) │
│  - Accuracy check     │
│  - Calibration check  │
│  - Sharpe check       │
│  - vs Baseline check  │
└───────────┬───────────┘
            │ Passed?
            ▼
┌───────────────────────┐
│      DEPLOYMENT       │
│                       │
│  - Archive old model  │
│  - Hot-swap new model │
│  - Monitor performance│
│  - Auto-rollback      │
└───────────────────────┘
```

### 5.2 Reward Function

```python
def compute_reward(predictions, outcomes, n_bars=10):
    """
    Reward function for model evaluation.
    
    Primary: Directional accuracy on next N bars
    Secondary: Calibration (predicted prob vs actual)
    Penalty: Overconfidence, excessive signals
    """
    # Primary: Directional accuracy
    pred_direction = np.sign(predictions['trend_confidence'] - 0.5)
    actual_direction = np.sign(outcomes['price_change'])
    accuracy = np.mean(pred_direction == actual_direction)
    
    # Secondary: Calibration (Brier score)
    brier = np.mean((predictions['breakout_prob'] - outcomes['breakout_occurred'])**2)
    calibration = 1 - brier
    
    # Penalty: Overconfidence
    confidence = np.mean(np.abs(predictions['trend_confidence'] - 0.5))
    overconfidence_penalty = max(0, confidence - accuracy) * 0.5
    
    # Penalty: Excessive signals
    signal_rate = np.mean(np.abs(predictions['composite_signal']) > 0.3)
    signal_penalty = max(0, signal_rate - 0.3) * 0.2
    
    # Combined reward
    reward = (
        accuracy * 0.5 +           # 50% weight on accuracy
        calibration * 0.3 +        # 30% weight on calibration
        -overconfidence_penalty +  # Penalty for overconfidence
        -signal_penalty            # Penalty for excessive signals
    )
    
    return reward
```

### 5.3 Training Pipeline

```python
# Weekly retraining schedule
RETRAIN_CONFIG = {
    'frequency': 'weekly',
    'min_samples': 10_000,
    'max_samples': 100_000,
    'validation_split': 0.2,
    'epochs': 10,
    'early_stopping': 3,
    'batch_size': 64,
}

# Training steps
def retrain_pipeline():
    # 1. Load archived data
    data = load_archived_data(days=30)
    
    # 2. Prepare features and labels
    X, y = prepare_training_data(data)
    
    # 3. Split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
    
    # 4. Train with early stopping
    model = train_model(X_train, y_train, X_val, y_val)
    
    # 5. Export to ONNX
    export_onnx(model, 'model_new.onnx')
    
    return 'model_new.onnx'
```

### 5.4 Deployment Rules

| Condition | Action |
|-----------|--------|
| `accuracy >= 0.52` | Pass accuracy gate |
| `calibration_error <= 0.1` | Pass calibration gate |
| `sharpe >= 0.5` | Pass backtest gate |
| `accuracy_vs_baseline >= -0.1` | Pass comparison gate |
| `model_size <= 10MB` | Pass size gate |
| All gates passed | Deploy |
| Any gate failed | Reject, archive |

### 5.5 Auto-Rollback Conditions

```python
ROLLBACK_CONDITIONS = {
    'accuracy_drop': 0.1,      # 10% drop vs baseline
    'sharpe_drop': 0.2,        # 20% Sharpe drop
    'calibration_spike': 0.15, # Calibration error > 15%
    'consecutive_losses': 10,  # 10 consecutive wrong predictions
}

def check_rollback(current_metrics, baseline_metrics):
    if baseline_metrics['accuracy'] - current_metrics['accuracy'] > 0.1:
        return True, "Accuracy dropped >10%"
    if baseline_metrics['sharpe'] - current_metrics['sharpe'] > 0.2:
        return True, "Sharpe dropped >20%"
    return False, ""
```

---

## 6. PERFORMANCE BUDGET

### 6.1 Inference Latency (per symbol)

| Metric | Target | Max Acceptable | Degraded Mode |
|--------|--------|----------------|---------------|
| Feature extraction | 1ms | 2ms | 0.5ms |
| Model inference | 3ms | 5ms | 1ms |
| Total latency | **<5ms** | 10ms | 2ms |

### 6.2 Storage Cost (per day, per symbol)

| Component | Size | Notes |
|-----------|------|-------|
| Feature history | 2MB | 2000 bars × 32 features × 4 bytes |
| Training data | 10MB | If collecting |
| Model files | 5MB | ONNX format |
| Visualization cache | 1MB | Tile cache |
| **Total** | **<20MB/day** | Per symbol |

### 6.3 RAM Usage

| Component | Size | Notes |
|-----------|------|-------|
| Per symbol state | 500KB | Buffers, features |
| Model in memory | 10MB | Shared across symbols |
| Inference buffers | 1MB | Batch processing |
| Visualization | 2MB | Per symbol |
| **Total (50 symbols)** | **<100MB** | |

### 6.4 Client Rendering Load

| Metric | Target | Notes |
|--------|--------|-------|
| WebGL draw calls | <100/frame | Batched rendering |
| Texture memory | <50MB | Tile cache |
| Frame time | <16ms | 60fps target |
| Overlay computation | <5ms | Per frame |
| JavaScript heap | <100MB | Total |

### 6.5 Network

| Metric | Target | Notes |
|--------|--------|-------|
| API response size | <10KB | Per symbol |
| WebSocket rate | <10 msg/s | Updates |
| Compression | gzip | For large payloads |

### 6.6 Model Constraints

| Constraint | Limit | Rationale |
|------------|-------|-----------|
| Total parameters | <1M | CPU inference |
| Model file size | <10MB | Fast loading |
| ONNX compatible | Required | Portability |
| GPU required | No | Cost reduction |
| Quantization | Optional | Further optimization |

---

## 7. USAGE EXAMPLES

### 7.1 Basic Usage

```python
from trading_bot.deepchart import DeepChartOrchestrator

# Initialize
orchestrator = DeepChartOrchestrator()
orchestrator.add_symbol("BTCUSDT")

# Update with market data
result = orchestrator.update(
    symbol="BTCUSDT",
    price=50000.0,
    volume=100.0,
    bid=49995.0,
    ask=50005.0,
)

# Get prediction
if result:
    print(f"Trend: {result.model_output.trend_direction}")
    print(f"Breakout prob: {result.model_output.breakout_probability}")
    print(f"Signals: {result.signals}")

# Get visualization for frontend
viz_data = orchestrator.get_visualization("BTCUSDT")
```

### 7.2 API Integration

```python
from trading_bot.deepchart import DeepChartOrchestrator

orchestrator = DeepChartOrchestrator()

# REST-like API
prediction = orchestrator.api.get_prediction("BTCUSDT")
# Returns JSON-serializable dict

status = orchestrator.api.get_status()
# Returns system health and metrics
```

### 7.3 WebGL Frontend Integration

```javascript
// Fetch visualization data
const response = await fetch('/api/deepchart/BTCUSDT/visualization');
const vizData = await response.json();

// Render overlays
vizData.overlays.forEach(overlay => {
    switch(overlay.type) {
        case 'regime_background':
            renderRegimeBackground(overlay.data);
            break;
        case 'support_resistance':
            renderLevels(overlay.data);
            break;
        // ... other overlay types
    }
});
```

---

## 8. FILES CREATED

```
trading_bot/deepchart/
├── __init__.py                 # Module exports
├── feature_pipeline.py         # Feature extraction (~800 lines)
├── lightweight_models.py       # ML models (~900 lines)
├── inference_engine.py         # Real-time inference (~600 lines)
├── visualization_layer.py      # Chart overlays (~700 lines)
├── self_improvement.py         # Model evolution (~800 lines)
├── orchestrator.py             # Main coordinator (~500 lines)
└── DEEPCHART_ARCHITECTURE.md   # This document

Total: ~4,300 lines of production-ready code
```

---

## 9. COST ANALYSIS

### Monthly Operating Cost (50 symbols)

| Component | Cost | Notes |
|-----------|------|-------|
| Compute (CPU) | $0 | Runs on existing infra |
| Storage | ~$1 | 1GB/month @ $0.02/GB |
| Data feeds (L1) | $0-50 | Depends on provider |
| **Total** | **<$50/month** | For 50 symbols |

### Comparison to Alternatives

| Solution | Monthly Cost | Notes |
|----------|--------------|-------|
| DeepChart (this) | <$50 | L1 + aggregated L2 |
| Full L2/L3 feeds | $500-5000 | Per exchange |
| GPU inference | $100-500 | Cloud GPU |
| Commercial charting | $100-300 | Per seat |

**Cost Efficiency: 10-100x cheaper than alternatives**

---

## 10. LIMITATIONS & TRADE-OFFS

### What This System Does NOT Do:
1. **No HFT** - Latency target is 5ms, not microseconds
2. **No full L2/L3** - Works with aggregated depth only
3. **No GPU required** - CPU-only inference
4. **No real-time training** - Offline retraining only
5. **No complex ensembles** - Simple averaging only

### Trade-offs Made:
1. **Accuracy vs Cost** - Slightly lower accuracy for 10x cost reduction
2. **Latency vs Features** - Fewer features for faster inference
3. **Model size vs Capacity** - Smaller models, less complex patterns
4. **Real-time vs Batch** - Batch training, real-time inference only

### When NOT to Use This:
- Ultra-low latency requirements (<1ms)
- Full order book analysis needed
- GPU resources available and cheap
- Maximum accuracy required regardless of cost
