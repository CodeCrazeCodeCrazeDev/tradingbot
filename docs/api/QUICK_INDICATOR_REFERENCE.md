# AlphaAlgo Quick Indicator Reference

## 🚀 Quick Start

```python
from trading_bot.indicators import (
    AdvancedTechnicalIndicators,
    AdvancedMLIndicators,
    AdvancedLiquidityIndicators,
    AdvancedStatisticalIndicators
)

# Initialize
tech = AdvancedTechnicalIndicators()
ml = AdvancedMLIndicators()
liq = AdvancedLiquidityIndicators()
stat = AdvancedStatisticalIndicators()

# Calculate
tech_result = tech.calculate_all(df)
ml_signal = ml.generate_signal(df, features)
liq_analysis = liq.analyze_liquidity(df)
stat_analysis = stat.analyze(df)
```

---

## 📊 Indicator Cheat Sheet

### Technical Indicators

| Indicator | When to Use | Interpretation |
|-----------|-------------|----------------|
| **Hurst** | Regime detection | < 0.5 = Mean-revert, > 0.5 = Trend |
| **FRAMA** | Dynamic trend | Faster than EMA in trends |
| **SuperTrend** | Trend following | Direction: 1=up, -1=down |
| **KAMA** | Noisy markets | Adapts to market efficiency |
| **TTM Squeeze** | Breakout trading | squeeze_on=1 → Breakout coming |
| **Kalman** | Noise reduction | Smoothest trendline |

### AI/ML Signals

| System | Purpose | Key Output |
|--------|---------|------------|
| **Meta-Learning** | Model weighting | Ensemble prediction |
| **RARL** | Regime adaptation | Action per regime |
| **XAI** | Explainability | SHAP values |
| **Transformer** | Pattern recognition | Probability + attention |
| **Ensemble** | Model blending | Weighted prediction |
| **HMM** | Regime classification | State probabilities |
| **Copula** | Asset correlation | Tail dependence |

### Liquidity Indicators

| Indicator | Signal | Action |
|-----------|--------|--------|
| **Iceberg** | Hidden orders | Follow institutional flow |
| **Absorption** | > 1.2 | Support (buy) |
| **Absorption** | < 0.8 | Resistance (sell) |
| **CVD Alignment** | > 0.8 | Strong directional flow |
| **TIB** | Imbalance bars | Trade with imbalance |
| **Volume Heatmap** | High activity zones | Key price levels |
| **Order Book** | Imbalance > 0.2 | Bullish bias |

### Statistical Models

| Model | Use Case | Interpretation |
|-------|----------|----------------|
| **Cointegration** | Pairs trading | p-value < 0.05 = cointegrated |
| **Z-Score** | Mean reversion | ±2 = entry, ±0.5 = exit |
| **Kalman** | Trend smoothing | Follow filtered line |
| **HMM** | Regime detection | Bull/bear/neutral state |

---

## 🎯 Trading Scenarios

### Scenario 1: Trend Trading
```python
# Check trend strength
hurst = tech_result['hurst_exponent'].iloc[-1]
supertrend_dir = tech_result['supertrend_direction'].iloc[-1]
regime = ml_signal.regime

if hurst > 0.6 and supertrend_dir == 1 and regime == 'trending':
    # Strong uptrend confirmed
    action = 'BUY'
```

### Scenario 2: Mean Reversion
```python
# Check mean reversion setup
zscore = stat_analysis['zscore']
absorption = liq_analysis['absorption_ratio']

if zscore < -2 and absorption > 1.2:
    # Oversold + support = buy
    action = 'BUY'
elif zscore > 2 and absorption < 0.8:
    # Overbought + resistance = sell
    action = 'SELL'
```

### Scenario 3: Breakout Trading
```python
# Check for breakout
ttm_squeeze = tech_result['ttm_squeeze_on'].iloc[-1]
cvd_alignment = liq_analysis['cvd_alignment']

if ttm_squeeze == 1 and cvd_alignment > 0.7:
    # Compression + aligned flow = breakout imminent
    action = 'PREPARE_ENTRY'
```

### Scenario 4: Institutional Flow
```python
# Follow smart money
icebergs = liq_analysis['icebergs_detected']
latest_iceberg = liq_analysis['latest_iceberg']

if icebergs > 0 and latest_iceberg.side == 'buy':
    # Institutional accumulation detected
    action = 'BUY'
```

---

## 🔍 Confidence Scoring Formula

```python
def calculate_confidence(tech, ml, liq, stat):
    """Calculate overall signal confidence."""
    
    # Layer weights
    w_tech = 0.25
    w_ml = 0.30
    w_liq = 0.25
    w_stat = 0.20
    
    # Technical score
    tech_score = (
        (1 if tech['hurst_exponent'] > 0.6 else 0) * 0.3 +
        (1 if tech['supertrend_direction'] == 1 else 0) * 0.4 +
        (1 if tech['ttm_squeeze_on'] == 0 else 0) * 0.3
    )
    
    # ML score
    ml_score = ml.probability
    
    # Liquidity score
    liq_score = (
        liq['cvd_alignment'] * 0.5 +
        (1 if liq['absorption_ratio'] > 1.0 else 0) * 0.5
    )
    
    # Statistical score
    stat_score = (
        (1 if abs(stat['zscore']) < 2 else 0) * 0.5 +
        (1 if stat.get('regime_confidence', 0) > 0.7 else 0) * 0.5
    )
    
    # Final confidence
    confidence = (
        w_tech * tech_score +
        w_ml * ml_score +
        w_liq * liq_score +
        w_stat * stat_score
    )
    
    return confidence
```

---

## ⚡ Performance Tips

### 1. Caching
```python
# Cache expensive calculations
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_hurst(prices_tuple):
    prices = pd.Series(prices_tuple)
    return HurstExponent().calculate(prices)
```

### 2. Vectorization
```python
# Use numpy for speed
import numpy as np

# Instead of loops
zscore = (series - series.rolling(20).mean()) / series.rolling(20).std()
```

### 3. Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor

def calculate_all_indicators(df):
    with ThreadPoolExecutor(max_workers=4) as executor:
        tech_future = executor.submit(tech.calculate_all, df)
        ml_future = executor.submit(ml.generate_signal, df, features)
        liq_future = executor.submit(liq.analyze_liquidity, df)
        stat_future = executor.submit(stat.analyze, df)
        
        return {
            'technical': tech_future.result(),
            'ml': ml_future.result(),
            'liquidity': liq_future.result(),
            'statistical': stat_future.result()
        }
```

---

## 🐛 Common Issues & Solutions

### Issue 1: NaN Values
```python
# Solution: Check data length
if len(df) < 50:
    logger.warning("Insufficient data for indicators")
    return None

# Fill NaN with forward fill
result = result.fillna(method='ffill')
```

### Issue 2: Slow Performance
```python
# Solution: Reduce calculation frequency
if len(df) % 10 == 0:  # Calculate every 10 bars
    indicators = calculate_all_indicators(df)
```

### Issue 3: Memory Usage
```python
# Solution: Use rolling windows
df = df.tail(1000)  # Keep only last 1000 bars
```

---

## 📈 Integration Example

```python
class AlphaAlgoBrain:
    """Complete integration example."""
    
    def __init__(self):
        self.tech = AdvancedTechnicalIndicators()
        self.ml = AdvancedMLIndicators()
        self.liq = AdvancedLiquidityIndicators()
        self.stat = AdvancedStatisticalIndicators()
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """Complete market analysis."""
        
        # Layer 1: Technical
        tech_result = self.tech.calculate_all(df)
        
        # Layer 2: ML
        features = self._extract_features(tech_result)
        ml_signal = self.ml.generate_signal(df, features)
        
        # Layer 3: Liquidity
        liq_analysis = self.liq.analyze_liquidity(df)
        
        # Layer 4: Statistical
        stat_analysis = self.stat.analyze(df)
        
        # Fusion
        confidence = self._calculate_confidence(
            tech_result, ml_signal, liq_analysis, stat_analysis
        )
        
        return {
            'signal': 'BUY' if confidence > 0.7 else 'SELL' if confidence < 0.3 else 'HOLD',
            'confidence': confidence,
            'technical': tech_result,
            'ml': ml_signal,
            'liquidity': liq_analysis,
            'statistical': stat_analysis,
            'shap_values': ml_signal.shap_values,
            'regime': ml_signal.regime
        }
    
    def _extract_features(self, tech_result: pd.DataFrame) -> Dict:
        """Extract features for ML."""
        return {
            'rsi': tech_result.get('rsi', pd.Series([50])).iloc[-1],
            'macd': tech_result.get('macd', pd.Series([0])).iloc[-1],
            'hurst': tech_result.get('hurst_exponent', pd.Series([0.5])).iloc[-1],
            'volume_ratio': 1.0
        }
    
    def _calculate_confidence(self, tech, ml, liq, stat) -> float:
        """Calculate overall confidence."""
        return calculate_confidence(tech, ml, liq, stat)
```

---

## 🎓 Learning Path

### Beginner
1. Start with basic technical indicators (Hurst, SuperTrend)
2. Understand z-score for mean reversion
3. Learn CVD for flow analysis

### Intermediate
4. Implement RARL for regime adaptation
5. Use ensemble blending
6. Apply cointegration for pairs trading

### Advanced
7. Deploy meta-learning system
8. Integrate transformers
9. Build complete explainable AI pipeline

---

## 📞 Support

**Documentation:** See `ALPHAALGO_UNIFIED_INDICATOR_MAP.md`  
**Implementation:** See `INDICATOR_IMPLEMENTATION_COMPLETE.md`  
**API Reference:** See inline docstrings in modules

**Quick Test:**
```bash
cd "c:\Users\peterson\trading bot"
python -m trading_bot.indicators.advanced_technical
python -m trading_bot.indicators.advanced_ml
python -m trading_bot.indicators.advanced_liquidity
python -m trading_bot.indicators.advanced_statistical
```

---

**Version:** 2.0.0  
**Last Updated:** 2025-01-14  
**Status:** Production Ready ✅
