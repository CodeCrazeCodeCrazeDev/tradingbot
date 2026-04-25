"""
Regime Shift Predictor
=====================

Predicts major market regime changes before they fully materialize.

Indicators:
- Volatility regime: GARCH models, realized vs implied vol divergence
- Correlation regime: Rolling correlations, eigenvalue analysis
- Factor regime: Factor return dispersion, style drift
- Macro regime: Yield curve, inflation breakevens, FX trends
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RegimeType(Enum):
    """Types of market regimes."""
    LOW_VOL = "low_volatility"
    HIGH_VOL = "high_volatility"
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    RANGE_BOUND = "range_bound"
    CRISIS = "crisis"
    RECOVERY = "recovery"


@dataclass
class RegimePrediction:
    """Predicted regime change."""
    current_regime: RegimeType
    predicted_regime: RegimeType
    confidence: float
    time_horizon: str  # immediate, short_term, medium_term
    leading_indicators: List[str]
    estimated_probability: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_regime': self.current_regime.value,
            'predicted_regime': self.predicted_regime.value,
            'confidence': self.confidence,
            'time_horizon': self.time_horizon,
            'leading_indicators': self.leading_indicators,
            'estimated_probability': self.estimated_probability,
            'timestamp': self.timestamp.isoformat(),
        }


class RegimeShiftPredictor:
    """
    Predicts market regime shifts before they fully materialize.
    
    Uses multiple leading indicators to anticipate changes in:
    - Volatility regimes
    - Trend direction
    - Correlation structures
    - Macro conditions
    """
    
    def __init__(self, 
                 volatility_window: int = 20,
                 correlation_window: int = 60,
                 macro_window: int = 90):
        """
        Initialize predictor.
        
        Args:
            volatility_window: Window for volatility estimation
            correlation_window: Window for correlation estimation
            macro_window: Window for macro indicator analysis
        """
        self.volatility_window = volatility_window
        self.correlation_window = correlation_window
        self.macro_window = macro_window
        
        self.regime_history: List[Tuple[datetime, RegimeType]] = []
        
        logger.info("RegimeShiftPredictor initialized")
    
    def predict_volatility_regime(self,
                                 returns: List[float],
                                 implied_vol: Optional[float] = None) -> Optional[RegimePrediction]:
        """
        Predict volatility regime shift.
        
        Detects transitions between low and high volatility regimes
        using GARCH-like analysis and realized vs implied divergence.
        """
        if len(returns) < self.volatility_window * 2:
            return None
        
        # Calculate realized volatility
        recent_vol = np.std(returns[-self.volatility_window:])
        historical_vol = np.std(returns[:-self.volatility_window])
        
        # Detect regime
        vol_ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
        
        current_regime = RegimeType.HIGH_VOL if recent_vol > 0.02 else RegimeType.LOW_VOL
        
        # Predict transition
        predicted_regime = current_regime
        confidence = 0.5
        indicators = []
        
        # Volatility clustering (GARCH effect)
        recent_returns = returns[-10:]
        if any(abs(r) > 2 * recent_vol for r in recent_returns):
            if current_regime == RegimeType.LOW_VOL:
                predicted_regime = RegimeType.HIGH_VOL
                confidence = 0.7
                indicators.append("Volatility clustering detected")
        
        # Realized vs implied divergence
        if implied_vol is not None and recent_vol > 0:
            vol_premium = implied_vol / recent_vol
            if vol_premium > 1.5:  # Implied vol much higher than realized
                predicted_regime = RegimeType.HIGH_VOL
                confidence = 0.75
                indicators.append(f"High vol premium: {vol_premium:.2f}x")
        
        # Trend in volatility
        if len(returns) >= self.volatility_window * 3:
            older_vol = np.std(returns[-3*self.volatility_window:-2*self.volatility_window])
            middle_vol = np.std(returns[-2*self.volatility_window:-self.volatility_window])
            
            if middle_vol > older_vol and recent_vol > middle_vol:
                # Volatility trending up
                if current_regime == RegimeType.LOW_VOL:
                    predicted_regime = RegimeType.HIGH_VOL
                    confidence = 0.8
                    indicators.append("Volatility trending higher")
        
        if predicted_regime != current_regime or confidence > 0.6:
            return RegimePrediction(
                current_regime=current_regime,
                predicted_regime=predicted_regime,
                confidence=confidence,
                time_horizon="short_term" if confidence > 0.7 else "medium_term",
                leading_indicators=indicators,
                estimated_probability=confidence,
                timestamp=datetime.now(),
            )
        
        return None
    
    def predict_correlation_regime(self,
                                  asset_returns: Dict[str, List[float]]) -> Optional[RegimePrediction]:
        """
        Predict correlation regime shift.
        
        Detects when correlations between assets are breaking down
        or converging (all correlations → 1 in crisis).
        """
        if len(asset_returns) < 2:
            return None
        
        assets = list(asset_returns.keys())
        
        # Need sufficient data
        min_length = min(len(returns) for returns in asset_returns.values())
        if min_length < self.correlation_window:
            return None
        
        # Calculate rolling correlations
        correlations = []
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                corr = np.corrcoef(
                    asset_returns[assets[i]][-self.correlation_window:],
                    asset_returns[assets[j]][-self.correlation_window:]
                )[0, 1]
                if not np.isnan(corr):
                    correlations.append(corr)
        
        if not correlations:
            return None
        
        avg_correlation = np.mean(correlations)
        correlation_dispersion = np.std(correlations)
        
        # Detect regime
        indicators = []
        
        # High correlation regime (crisis)
        if avg_correlation > 0.8:
            current_regime = RegimeType.CRISIS
            confidence = avg_correlation
            indicators.append(f"Average correlation {avg_correlation:.2f} (crisis level)")
        # Low correlation regime (normal)
        elif avg_correlation < 0.3:
            current_regime = RegimeType.RANGE_BOUND
            confidence = 0.6
            indicators.append(f"Low correlation {avg_correlation:.2f} (diversification benefits)")
        else:
            current_regime = RegimeType.RECOVERY
            confidence = 0.5
        
        # Predict transition
        predicted_regime = current_regime
        
        # Check for rising correlations (crisis brewing)
        if len(asset_returns[assets[0]]) >= self.correlation_window * 2:
            older_corrs = []
            for i in range(len(assets)):
                for j in range(i + 1, len(assets)):
                    corr = np.corrcoef(
                        asset_returns[assets[i]][-2*self.correlation_window:-self.correlation_window],
                        asset_returns[assets[j]][-2*self.correlation_window:-self.correlation_window]
                    )[0, 1]
                    if not np.isnan(corr):
                        older_corrs.append(corr)
            
            if older_corrs:
                avg_old = np.mean(older_corrs)
                if avg_correlation > avg_old * 1.3:  # 30% increase
                    predicted_regime = RegimeType.CRISIS
                    confidence = 0.75
                    indicators.append(f"Correlation rising: {avg_old:.2f} → {avg_correlation:.2f}")
        
        if indicators:
            return RegimePrediction(
                current_regime=current_regime,
                predicted_regime=predicted_regime,
                confidence=confidence,
                time_horizon="immediate" if confidence > 0.7 else "short_term",
                leading_indicators=indicators,
                estimated_probability=confidence,
                timestamp=datetime.now(),
            )
        
        return None
    
    def predict_macro_regime(self,
                            indicators: Dict[str, float]) -> Optional[RegimePrediction]:
        """
        Predict macroeconomic regime shift.
        
        Uses yield curve, inflation data, employment figures.
        """
        leading_indicators = []
        
        # Yield curve inversion (recession predictor)
        if 'yield_10y' in indicators and 'yield_2y' in indicators:
            spread = indicators['yield_10y'] - indicators['yield_2y']
            if spread < 0:  # Inverted
                leading_indicators.append(f"Yield curve inverted: {spread:.2f}%")
                confidence = min(0.9, 0.7 + abs(spread) * 10)
                
                return RegimePrediction(
                    current_regime=RegimeType.BULL_TREND,  # Assuming we're in bull
                    predicted_regime=RegimeType.CRISIS,
                    confidence=confidence,
                    time_horizon="medium_term",
                    leading_indicators=leading_indicators,
                    estimated_probability=confidence,
                    timestamp=datetime.now(),
                )
        
        # Inflation regime
        if 'inflation' in indicators:
            inflation = indicators['inflation']
            if inflation > 0.05:  # >5% inflation
                leading_indicators.append(f"High inflation: {inflation:.1%}")
                return RegimePrediction(
                    current_regime=RegimeType.LOW_VOL,
                    predicted_regime=RegimeType.HIGH_VOL,
                    confidence=0.7,
                    time_horizon="short_term",
                    leading_indicators=leading_indicators,
                    estimated_probability=0.7,
                    timestamp=datetime.now(),
                )
        
        return None
    
    def get_composite_prediction(self,
                                 returns: List[float],
                                 asset_returns: Dict[str, List[float]],
                                 macro_indicators: Dict[str, float]) -> Optional[RegimePrediction]:
        """Get composite regime prediction combining all signals."""
        predictions = []
        
        # Volatility prediction
        vol_pred = self.predict_volatility_regime(returns)
        if vol_pred:
            predictions.append(vol_pred)
        
        # Correlation prediction
        corr_pred = self.predict_correlation_regime(asset_returns)
        if corr_pred:
            predictions.append(corr_pred)
        
        # Macro prediction
        macro_pred = self.predict_macro_regime(macro_indicators)
        if macro_pred:
            predictions.append(macro_pred)
        
        if not predictions:
            return None
        
        # Combine predictions
        highest_confidence = max(predictions, key=lambda p: p.confidence)
        
        # Check for consensus
        all_indicators = []
        for p in predictions:
            all_indicators.extend(p.leading_indicators)
        
        return RegimePrediction(
            current_regime=highest_confidence.current_regime,
            predicted_regime=highest_confidence.predicted_regime,
            confidence=highest_confidence.confidence,
            time_horizon=highest_confidence.time_horizon,
            leading_indicators=all_indicators,
            estimated_probability=highest_confidence.confidence,
            timestamp=datetime.now(),
        )
