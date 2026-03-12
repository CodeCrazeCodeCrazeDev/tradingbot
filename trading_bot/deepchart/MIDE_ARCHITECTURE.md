# Market Intent Decomposition Engine (MIDE)
## Causal Market Cognition Layer for AlphaAlgo

---

## EXECUTIVE SUMMARY

MIDE is a **causal market cognition layer** that decomposes every market moment into a probability-weighted mixture of latent participant intents using only cheap data. This is NOT a prediction engine. This is NOT an indicator system. MIDE infers **WHY** price is behaving the way it is—not just how.

**Core Output**: A 5-dimensional probability simplex representing the current intent mixture at every timestep.

---

## 1. FORMAL SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MARKET INTENT DECOMPOSITION ENGINE (MIDE)                 │
└─────────────────────────────────────────────────────────────────────────────┘

DATA INGESTION
├── L1 Trades (price, volume, time)
├── Best Bid/Ask (price, size)
├── Spread (derived)
└── Partial L2 (optional, top 5 levels)
         │
         ▼
FEATURE EXTRACTION (12 Observable Features)
├── Price Response Per Unit Volume (ρ)
├── Spread-Crossing Frequency (f_cross)
├── Reaction Half-Life (τ_1/2)
├── Volume Entropy (H_v)
├── Price Curvature vs Volume (κ)
├── Micro-Friction Persistence (φ)
├── Execution Efficiency vs Volatility (η)
├── Trade Arrival Irregularity (ψ)
├── Size Clustering Coefficient (γ)
├── Quote Imbalance Persistence (ω)
├── Aggressor Ratio Asymmetry (α)
└── Momentum Decay Rate (λ_m)
         │
         ▼
INTENT ENCODER (Hybrid GRU-TCN, ~85K params)
├── TCN Branch: Dilated Conv, k=3, d=[1,2,4,8]
├── GRU Branch: 2-layer, hidden=32
├── Attention Branch: 1-head, d=32
└── Fusion: Concat(96) → FC(32) → FC(5) → Softmax
         │
         ▼
CONSISTENCY & TRANSITION CONSTRAINTS
├── Transition Matrix T[5×5]
├── Impossible State Suppression
└── Temporal Smoothing
         │
         ▼
INTENT MOMENTUM & DECAY
├── Momentum Accumulator
├── Persistence Scoring
└── Exhaustion Detection
         │
         ▼
STATE AGGREGATION → IntentState
         │
         ├──→ OUTPUT APIs
         ├──→ VISUALIZATION CONSUMERS
         └──→ STRATEGY CONSUMERS
```

---

## 2. CANONICAL LATENT INTENTS (5 MANDATORY)

| Intent | Symbol | Description | Observable Signatures |
|--------|--------|-------------|----------------------|
| **Urgent Directional** | π₁ | Informed trader with time pressure | High spread-crossing, large price impact |
| **Passive Accumulation** | π₂ | Patient institutional flow | Low impact per volume, persistent imbalance |
| **Mechanical Flow** | π₃ | Algorithmic rebalancing, TWAP/VWAP | Regular intervals, size clustering |
| **Exploitative** | π₄ | Market makers, stat-arb | Spread-sensitive, mean-reverting |
| **Noise** | π₅ | Retail, uninformed | High entropy, no persistence |

**Output**: π(t) = [π₁, π₂, π₃, π₄, π₅] where Σπᵢ = 1

---

## 3. OBSERVABLE FEATURE SPECIFICATION

### 3.1 Price Response Per Unit Volume (ρ)
```
ρ(t) = |Δp(t)| / (v(t) + ε)
Normalized: Z-score over 100-bar window
Update: Every trade
Source: L1 trades
Intent: High ρ → Urgent; Low ρ → Passive
```

### 3.2 Spread-Crossing Frequency (f_cross)
```
f_cross = count(trades crossing spread) / count(all trades)
Window: 20 bars
Source: L1 trades + quotes
Intent: High → Urgent; Low → Passive/Mechanical
```

### 3.3 Reaction Half-Life (τ_1/2)
```
After burst (vol > 2×EMA), find time for 50% price reversion
τ_1/2 = EMA over 10 bursts
Source: L1 trades
Intent: Short → Urgent (permanent); Long → Noise (temporary)
```

### 3.4 Volume Entropy (H_v)
```
H_v = -Σ p_k × log(p_k) / log(K), K=10 bins
Window: 50 bars
Source: L1 trades
Intent: High → Noise; Low → Mechanical
```

### 3.5 Price Curvature vs Volume (κ)
```
Fit p(v) = a×v² + b×v + c; κ = 2a
Window: 30 bars
Source: L1 trades
Intent: κ>0 → Urgent; κ<0 → Passive; κ≈0 → Mechanical
```

### 3.6 Micro-Friction Persistence (φ)
```
friction = |Δp| / (spread × volume + ε)
φ = autocorr(friction, lag=1)
Source: L1 trades + quotes
Intent: High φ → Institutional; Low φ → Noise
```

### 3.7 Execution Efficiency vs Volatility (η)
```
efficiency = |p(t) - p(t-n)| / Σ|Δp|
η = corr(efficiency, volatility) over 50 bars
Intent: η>0 → Urgent; η<0 → Passive
```

### 3.8 Trade Arrival Irregularity (ψ)
```
ψ = CV(inter_arrival_times) = std/mean
Window: 50 trades
Intent: Low ψ → Mechanical; High ψ → Noise
```

### 3.9 Size Clustering Coefficient (γ)
```
γ = max(cluster_counts) / total_trades
Window: 100 trades
Intent: High γ → Mechanical; Low γ → Noise
```

### 3.10 Quote Imbalance Persistence (ω)
```
imbalance = (bid_size - ask_size) / (bid_size + ask_size)
ω = sign consistency over 20 bars
Intent: High ω → Passive; Low ω → Noise
```

### 3.11 Aggressor Ratio Asymmetry (α)
```
α = (buy_aggressor - sell_aggressor) / total
Intent: |α|>0.3 → Urgent; |α|<0.1 → Mechanical
```

### 3.12 Momentum Decay Rate (λ_m)
```
Fit: momentum(t+k) = momentum(t) × exp(-λ_m × k)
Intent: Low λ_m → Urgent; High λ_m → Noise
```

---

## 4. INTENT INFERENCE MODEL

### Architecture: Hybrid GRU-TCN (~85K params)

```
Input: (batch, seq=64, features=12)
       │
       ├─→ TCN: Dilated Conv k=3, d=[1,2,4,8], out=32
       ├─→ GRU: 2-layer, hidden=32
       └─→ Attention: 1-head, d=32, causal
       │
       └─→ Concat(96) → FC(32) → LayerNorm → ReLU → FC(5) → Softmax
       │
Output: [π₁, π₂, π₃, π₄, π₅], Σ=1
```

**Why Sufficient**: TCN captures local patterns, GRU captures state evolution, Attention identifies pivotal moments. Each branch serves distinct purpose.

**Calibration**: Temperature-scaled softmax, ECE < 0.05

---

## 5. INTENT CONSISTENCY & TRANSITION LOGIC

### Transition Matrix T
```
        Urgent  Passive  Mech.  Exploit.  Noise
Urgent    0.70    0.10   0.05     0.05    0.10
Passive   0.10    0.65   0.10     0.05    0.10
Mech.     0.05    0.10   0.70     0.05    0.10
Exploit.  0.10    0.10   0.05     0.60    0.15
Noise     0.10    0.10   0.15     0.15    0.50
```

### Constraint Application
```
π_constrained = α × π_raw + (1-α) × (T @ π_prev)
α ∈ [0.3, 0.7] based on confidence
```

### Impossible State Rules
1. Urgent + Passive cannot both exceed 0.4
2. Exploitative requires spread > 1.5σ OR volume spike
3. Noise floor minimum 0.05
4. Mechanical requires CV(arrivals) < 0.3

---

## 6. INTENT MOMENTUM & PERSISTENCE

### Momentum Accumulator
```
momentum[i] = 0.9 × momentum[i] + 0.1 × (π[i] - π_prev[i])
```

### Persistence Scoring
```
persistence[i] = count(π[i] > 0.3) / lookback
lookback = 20 bars
```

### Exhaustion Detection
```
exhaustion[i] = 1 - (momentum[i] / max_momentum[i])
when persistence > 0.7 AND momentum declining
```

### Intent Phases
- **Emerging**: persistence < 0.3, momentum > 0
- **Sustained**: persistence > 0.7, exhaustion < 0.3
- **Exhausting**: persistence > 0.7, exhaustion > 0.3
- **Fading**: exhaustion > 0.7

---

## 7. VISUALIZATION GRAMMAR

### Intent Ribbon
- Horizontal ribbon below price chart
- 5 stacked bands, height ∝ probability
- Bottom to top: Noise → Exploit. → Mech. → Passive → Urgent

### Color Mapping
- Urgent: Red (220, 50, 50)
- Passive: Blue (50, 100, 200)
- Mechanical: Gray (128, 128, 128)
- Exploitative: Yellow (230, 180, 50)
- Noise: Light gray (200, 200, 200)

### Opacity = Confidence
```
opacity = 0.3 + 0.7 × (max(π) - second_max(π))
```

### Slope = Momentum
- Arrows above ribbon indicate momentum direction
- Size ∝ |momentum|

### Transition Markers
- Vertical dashed line when dominant intent changes
- Color gradient from old to new intent

---

## 8. STRATEGY & EXECUTION INTEGRATION

### Entry Gating
```python
def should_enter(intent_state, signal):
    if intent_state.dominant == 'exploitative' and π[3] > 0.4:
        return False  # Likely mean reversion
    if intent_state.dominant == 'noise' and π[4] > 0.5:
        return False  # No edge
    if intent_state.dominant == 'urgent' and π[0] > 0.4:
        return True   # Momentum entry
    if intent_state.dominant == 'passive' and persistence > 0.5:
        return True   # Institutional flow
```

### Exit Timing
- Exit when supporting intent exhausted (exhaustion > 0.7)
- Exit when exploitative emerges (π[3] > 0.5)
- Exit when confidence drops (< 0.1)

### Position Sizing
```
size_mult = confidence × stability × intent_mult × (1 - exhaustion)
intent_mult: urgent=1.2, passive=1.0, mech=0.8, exploit=0.6, noise=0.5
```

### Execution Aggressiveness
- Urgent dominant: Aggressive TWAP, urgency=0.8
- Passive dominant: Passive POV, urgency=0.3
- Mechanical dominant: Scheduled TWAP, urgency=0.5
- Exploitative dominant: Very passive, urgency=0.2

---

## 9. SELF-IMPROVEMENT & VALIDATION

### Labeling Logic
Labels derived from post-event response quality:
- Price continuation after 10 bars → Urgent correct
- Price stability with volume → Passive correct
- Regular execution pattern → Mechanical correct
- Mean reversion → Exploitative correct
- Random walk → Noise correct

### Offline Retraining
- Frequency: Weekly
- Min samples: 50,000 bars
- Validation: 20% holdout
- Early stopping: 3 epochs

### Drift Detection
- KS test on feature distributions
- ECE monitoring (threshold: 0.08)
- Accuracy drop > 5% triggers retrain

### Shadow Evaluation
- New model runs in parallel for 48 hours
- Compare: accuracy, calibration, stability
- Promote only if all metrics improve

### Auto-Rollback
- Accuracy drop > 10% vs baseline
- ECE spike > 0.15
- 10 consecutive wrong dominant predictions

---

## 10. PERFORMANCE & COST BUDGET

| Metric | Target | Max Acceptable |
|--------|--------|----------------|
| Inference latency | <2ms | 5ms |
| RAM per symbol | <200KB | 500KB |
| State history | 100 bars | 200 bars |
| Model size | <1MB | 2MB |
| Retraining cost | <10 min | 30 min |
| Signal staleness | <50ms | 100ms |

---

## 11. FAILURE MODES & SAFEGUARDS

### False Intent Inference
- **Regime shock**: Sudden volatility spike misclassified as Urgent
  - Mitigation: Volatility-adjusted thresholds
- **Thin markets**: Low volume misclassified as Passive
  - Mitigation: Volume floor requirement
- **News events**: Spike misclassified as Exploitative
  - Mitigation: News calendar integration

### Degenerate States
- **Uniform distribution**: All intents ≈ 0.2
  - Mitigation: Increase temperature, flag as uncertain
- **Stuck state**: Same dominant for >100 bars
  - Mitigation: Decay persistence, force re-evaluation

### Over-Smoothing Risks
- **Missed transitions**: Smoothing hides real changes
  - Mitigation: Adaptive α based on feature volatility
- **Lagged response**: Intent changes detected late
  - Mitigation: Fast EMA in volatile regimes

### Regime Shock Behavior
- **Flash crash**: All features spike simultaneously
  - Mitigation: Circuit breaker, output "unknown" state
- **Liquidity vacuum**: No trades for extended period
  - Mitigation: Staleness flag, decay all intents to noise

---

## 12. IMPLEMENTATION FILES

```
trading_bot/deepchart/
├── intent_decomposition_core.py    # Data structures, enums
├── intent_feature_extractor.py     # 12 observable features
├── intent_inference_engine.py      # GRU-TCN encoder
├── intent_transition_logic.py      # Constraints, smoothing
├── intent_momentum_tracker.py      # Persistence, exhaustion
├── intent_orchestrator.py          # Master coordinator
└── MIDE_ARCHITECTURE.md            # This document
```

---

## 13. USAGE EXAMPLE

```python
from trading_bot.deepchart import IntentOrchestrator

# Initialize
mide = IntentOrchestrator()

# Update with market data
intent_state = mide.update(
    price=50000.0,
    volume=100.0,
    bid=49995.0,
    ask=50005.0,
    bid_size=50.0,
    ask_size=30.0,
    timestamp=time.time()
)

# Access intent mixture
print(f"Simplex: {intent_state.simplex}")
print(f"Dominant: {intent_state.dominant_intent}")
print(f"Confidence: {intent_state.confidence}")
print(f"Phase: {intent_state.get_intent_phase('urgent')}")

# Strategy integration
if intent_state.is_actionable(threshold=0.4):
    size_mult = compute_size_multiplier(intent_state)
    exec_params = get_execution_params(intent_state)
```
