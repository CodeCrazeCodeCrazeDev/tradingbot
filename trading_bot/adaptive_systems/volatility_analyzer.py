"""
Volatility Analysis System
Advanced volatility modeling and regime detection
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy.stats import norm
from arch import arch_model
import warnings
import numpy
import pandas
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class VolatilitySignal:
    """Volatility analysis signal"""
    signal_type: str
    strength: float
    confidence: float
    timestamp: datetime
    regime: str
    volatility: float
    forecast: float
    supporting_data: Dict
    metadata: Dict

class VolatilityRegime(str):
    """Volatility regime types"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"
    BREAKOUT = "breakout"
    COMPRESSION = "compression"

class VolatilityAnalyzer:
    """
    Advanced volatility analysis system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Analysis parameters
        self.lookback_window = self.config.get('lookback_window', 100)
        self.forecast_horizon = self.config.get('forecast_horizon', 10)
        self.regime_threshold = self.config.get('regime_threshold', 0.5)
        
        # Volatility models
        self.garch_model = None
        self.realized_vol = None
        self.implied_vol = None
        
        # State tracking
        self.vol_history = []
        self.regime_history = []
        self.forecasts = []
        
        logger.info("Volatility Analyzer initialized")
    
    def analyze_volatility(self, price_data: pd.DataFrame, 
                          options_data: Optional[Dict] = None) -> List[VolatilitySignal]:
        """
        Perform comprehensive volatility analysis
        """
        signals = []
        
        if len(price_data) < self.lookback_window:
            return signals
        
        # Calculate volatility metrics
        realized_vol = self._calculate_realized_volatility(price_data)
        garch_vol = self._estimate_garch_volatility(price_data)
        regime = self._identify_volatility_regime(realized_vol, garch_vol)
        
        # Update state
        self.vol_history.append(realized_vol)
        self.regime_history.append(regime)
        
        # Generate volatility signals
        signals.extend(self._analyze_volatility_regime(regime, realized_vol))
        signals.extend(self._analyze_volatility_patterns(price_data))
        
        if options_data:
            signals.extend(self._analyze_implied_volatility(options_data))
        
        # Generate forecasts
        forecast = self._forecast_volatility(price_data)
        if forecast:
            signals.extend(self._analyze_volatility_forecast(forecast))
        
        return signals
    
    def _calculate_realized_volatility(self, price_data: pd.DataFrame) -> float:
        """
        Calculate realized volatility using multiple methods
        """
        # Log returns
        returns = np.log(price_data['close']).diff().dropna()
        
        # Standard deviation
        std_vol = returns.std() * np.sqrt(252)
        
        # Parkinson volatility (high-low based)
        if 'high' in price_data.columns and 'low' in price_data.columns:
            high_low_ratio = np.log(price_data['high'] / price_data['low'])
            parkinson_vol = np.sqrt(252 / (4 * np.log(2)) * high_low_ratio.pow(2).mean())
        else:
            parkinson_vol = std_vol
        
        # Garman-Klass volatility
        if all(col in price_data.columns for col in ['open', 'high', 'low', 'close']):
            log_hl = np.log(price_data['high'] / price_data['low']).pow(2)
            log_co = np.log(price_data['close'] / price_data['open']).pow(2)
            gk_vol = np.sqrt(252 * (0.5 * log_hl - (2 * np.log(2) - 1) * log_co).mean())
        else:
            gk_vol = std_vol
        
        # Combine estimates with weights
        weights = [0.4, 0.3, 0.3]  # Adjust weights based on data quality
        realized_vol = (weights[0] * std_vol + 
                       weights[1] * parkinson_vol + 
                       weights[2] * gk_vol)
        
        return realized_vol
    
    def _estimate_garch_volatility(self, price_data: pd.DataFrame) -> float:
        """
        Estimate volatility using GARCH model
        """
        try:
            returns = np.log(price_data['close']).diff().dropna() * 100
            
            # Initialize GARCH model if needed
            if self.garch_model is None:
                self.garch_model = arch_model(
                    returns,
                    vol='Garch', 
                    p=1, 
                    q=1,
                    dist='normal'
                )
            
            # Fit model
            res = self.garch_model.fit(disp='off')
            
            # Get volatility forecast
            forecast = res.forecast()
            conditional_vol = np.sqrt(forecast.variance.values[-1]) / 100
            
            return conditional_vol * np.sqrt(252)
            
        except Exception as e:
            logger.warning(f"GARCH estimation failed: {e}")
            return self._calculate_realized_volatility(price_data)
    
    def _identify_volatility_regime(self, realized_vol: float, 
                                  garch_vol: float) -> VolatilityRegime:
        """
        Identify current volatility regime
        """
        # Combine volatility estimates
        current_vol = (realized_vol + garch_vol) / 2
        
        # Calculate historical percentiles if available
        if len(self.vol_history) > 20:
            vol_percentile = np.percentile(self.vol_history, [20, 40, 60, 80, 90])
            
            if current_vol <= vol_percentile[0]:
                return VolatilityRegime.LOW
            elif current_vol <= vol_percentile[1]:
                return VolatilityRegime.MEDIUM
            elif current_vol <= vol_percentile[3]:
                return VolatilityRegime.HIGH
            else:
                return VolatilityRegime.EXTREME
        else:
            # Fallback to fixed thresholds
            if current_vol < 0.15:  # 15% annualized
                return VolatilityRegime.LOW
            elif current_vol < 0.25:
                return VolatilityRegime.MEDIUM
            elif current_vol < 0.35:
                return VolatilityRegime.HIGH
            else:
                return VolatilityRegime.EXTREME
    
    def _analyze_volatility_regime(self, regime: VolatilityRegime, 
                                 current_vol: float) -> List[VolatilitySignal]:
        """
        Analyze volatility regime changes and patterns
        """
        signals = []
        
        # Check for regime change
        if len(self.regime_history) > 1:
            prev_regime = self.regime_history[-2]
            
            if regime != prev_regime:
                signals.append(VolatilitySignal(
                    signal_type="regime_change",
                    strength=abs(current_vol - self.vol_history[-2]) / self.vol_history[-2],
                    confidence=0.8,
                    timestamp=datetime.now(),
                    regime=regime,
                    volatility=current_vol,
                    forecast=self.forecasts[-1] if self.forecasts else current_vol,
                    supporting_data={
                        'previous_regime': prev_regime,
                        'vol_change': current_vol - self.vol_history[-2],
                        'regime_duration': self._get_regime_duration(prev_regime)
                    },
                    metadata={'change_type': 'regime_transition'}
                ))
        
        # Analyze regime characteristics
        if regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
            signals.append(VolatilitySignal(
                signal_type="high_volatility",
                strength=min((current_vol - 0.25) / 0.25, 1.0),
                confidence=0.7,
                timestamp=datetime.now(),
                regime=regime,
                volatility=current_vol,
                forecast=self.forecasts[-1] if self.forecasts else current_vol,
                supporting_data={
                    'percentile': self._calculate_vol_percentile(current_vol),
                    'zscore': self._calculate_vol_zscore(current_vol)
                },
                metadata={'alert_type': 'risk_warning'}
            ))
        
        return signals
    
    def _analyze_volatility_patterns(self, price_data: pd.DataFrame) -> List[VolatilitySignal]:
        """
        Analyze volatility patterns and structures
        """
        signals = []
        
        # Calculate volatility of volatility
        if len(self.vol_history) > 20:
            vol_of_vol = np.std(self.vol_history[-20:]) / np.mean(self.vol_history[-20:])
            
            # Detect volatility compression
            if vol_of_vol < 0.1 and len(self.vol_history) > 2:
                vol_trend = self.vol_history[-1] - self.vol_history[-2]
                
                if vol_trend < 0:
                    signals.append(VolatilitySignal(
                        signal_type="volatility_compression",
                        strength=1.0 - vol_of_vol,
                        confidence=0.7,
                        timestamp=datetime.now(),
                        regime=VolatilityRegime.COMPRESSION,
                        volatility=self.vol_history[-1],
                        forecast=self.forecasts[-1] if self.forecasts else self.vol_history[-1],
                        supporting_data={
                            'vol_of_vol': vol_of_vol,
                            'compression_duration': self._get_compression_duration(),
                            'historical_range': [min(self.vol_history), max(self.vol_history)]
                        },
                        metadata={'pattern_type': 'compression'}
                    ))
            
            # Detect volatility breakout
            elif vol_of_vol > 0.3:
                signals.append(VolatilitySignal(
                    signal_type="volatility_breakout",
                    strength=min(vol_of_vol, 1.0),
                    confidence=0.8,
                    timestamp=datetime.now(),
                    regime=VolatilityRegime.BREAKOUT,
                    volatility=self.vol_history[-1],
                    forecast=self.forecasts[-1] if self.forecasts else self.vol_history[-1],
                    supporting_data={
                        'vol_of_vol': vol_of_vol,
                        'breakout_size': self._calculate_breakout_size(),
                        'price_correlation': self._calculate_vol_price_correlation(price_data)
                    },
                    metadata={'pattern_type': 'breakout'}
                ))
        
        return signals
    
    def _analyze_implied_volatility(self, options_data: Dict) -> List[VolatilitySignal]:
        """
        Analyze implied volatility surface
        """
        signals = []
        
        if 'atm_iv' not in options_data:
            return signals
        
        # Get ATM implied volatility
        atm_iv = options_data['atm_iv']
        
        # Compare to realized vol
        if self.vol_history:
            real_vol = self.vol_history[-1]
            vol_premium = atm_iv - real_vol
            
            if abs(vol_premium) > 0.05:  # 5% threshold
                signals.append(VolatilitySignal(
                    signal_type="vol_premium",
                    strength=min(abs(vol_premium) / 0.1, 1.0),
                    confidence=0.7,
                    timestamp=datetime.now(),
                    regime=self._identify_volatility_regime(real_vol, atm_iv),
                    volatility=real_vol,
                    forecast=atm_iv,
                    supporting_data={
                        'implied_vol': atm_iv,
                        'realized_vol': real_vol,
                        'premium': vol_premium,
                        'term_structure': self._analyze_vol_term_structure(options_data)
                    },
                    metadata={'analysis_type': 'implied_vol'}
                ))
        
        # Analyze volatility surface
        if 'surface' in options_data:
            skew_signal = self._analyze_volatility_skew(options_data['surface'])
            if skew_signal:
                signals.append(skew_signal)
        
        return signals
    
    def _forecast_volatility(self, price_data: pd.DataFrame) -> Optional[float]:
        """
        Generate volatility forecast
        """
        try:
            returns = np.log(price_data['close']).diff().dropna() * 100
            
            # Fit GARCH model
            model = arch_model(returns, vol='Garch', p=1, q=1)
            res = model.fit(disp='off')
            
            # Generate forecast
            forecast = res.forecast(horizon=self.forecast_horizon)
            vol_forecast = np.sqrt(forecast.variance.values[-1, -1]) / 100 * np.sqrt(252)
            
            self.forecasts.append(vol_forecast)
            return vol_forecast
            
        except Exception as e:
            logger.warning(f"Volatility forecast failed: {e}")
            return None
    
    def _analyze_volatility_forecast(self, forecast: float) -> List[VolatilitySignal]:
        """
        Analyze volatility forecast for signals
        """
        signals = []
        
        if not self.vol_history:
            return signals
        
        current_vol = self.vol_history[-1]
        vol_change = forecast / current_vol - 1
        
        if abs(vol_change) > 0.2:  # 20% change threshold
            signals.append(VolatilitySignal(
                signal_type="vol_forecast",
                strength=min(abs(vol_change), 1.0),
                confidence=0.6,
                timestamp=datetime.now(),
                regime=self._identify_volatility_regime(current_vol, forecast),
                volatility=current_vol,
                forecast=forecast,
                supporting_data={
                    'forecast_change': vol_change,
                    'forecast_horizon': self.forecast_horizon,
                    'confidence_interval': self._calculate_forecast_confidence(forecast)
                },
                metadata={'forecast_type': 'garch'}
            ))
        
        return signals
    
    def _get_regime_duration(self, regime: VolatilityRegime) -> int:
        """
        Calculate duration of previous regime
        """
        duration = 0
        for past_regime in reversed(self.regime_history[:-1]):
            if past_regime == regime:
                duration += 1
            else:
                break
        return duration
    
    def _get_compression_duration(self) -> int:
        """
        Calculate duration of volatility compression
        """
        if len(self.vol_history) < 3:
            return 0
        
        duration = 0
        vol_std = np.std(self.vol_history[-20:]) if len(self.vol_history) >= 20 else np.std(self.vol_history)
        
        for vol in reversed(self.vol_history[:-1]):
            if abs(vol - np.mean(self.vol_history[-20:])) < vol_std:
                duration += 1
            else:
                break
        
        return duration
    
    def _calculate_breakout_size(self) -> float:
        """
        Calculate size of volatility breakout
        """
        if len(self.vol_history) < 20:
            return 0
        
        recent_vol = self.vol_history[-1]
        vol_avg = np.mean(self.vol_history[-20:-1])
        vol_std = np.std(self.vol_history[-20:-1])
        
        return (recent_vol - vol_avg) / vol_std if vol_std > 0 else 0
    
    def _calculate_vol_price_correlation(self, price_data: pd.DataFrame) -> float:
        """
        Calculate correlation between volatility and price
        """
        if len(self.vol_history) < 20:
            return 0
        
        price_returns = np.log(price_data['close']).diff().dropna()[-20:]
        vol_changes = np.diff(self.vol_history[-21:])
        
        if len(price_returns) == len(vol_changes):
            return np.corrcoef(price_returns, vol_changes)[0, 1]
        return 0
    
    def _analyze_vol_term_structure(self, options_data: Dict) -> Dict:
        """
        Analyze volatility term structure
        """
        term_structure = {}
        
        if 'term_structure' in options_data:
            terms = options_data['term_structure']
            
            # Calculate term structure slope
            if len(terms) >= 2:
                sorted_terms = sorted(terms.items())
                slope = (sorted_terms[-1][1] - sorted_terms[0][1]) / (sorted_terms[-1][0] - sorted_terms[0][0])
                term_structure['slope'] = slope
                
                # Check for inversion
                term_structure['inverted'] = any(terms[t2] < terms[t1] 
                                               for t1, t2 in zip(sorted_terms[:-1], sorted_terms[1:]))
        
        return term_structure
    
    def _analyze_volatility_skew(self, surface: Dict) -> Optional[VolatilitySignal]:
        """
        Analyze volatility skew/smile
        """
        if not surface or 'strikes' not in surface or 'ivs' not in surface:
            return None
        
        strikes = surface['strikes']
        ivs = surface['ivs']
        
        if len(strikes) < 3 or len(ivs) < 3:
            return None
        
        # Calculate skew (difference between OTM put and call IVs)
        atm_index = len(strikes) // 2
        put_skew = ivs[0] - ivs[atm_index]
        call_skew = ivs[-1] - ivs[atm_index]
        
        # Check for significant skew
        if abs(put_skew) > 0.05 or abs(call_skew) > 0.05:
            return VolatilitySignal(
                signal_type="vol_skew",
                strength=max(abs(put_skew), abs(call_skew)) / 0.1,
                confidence=0.7,
                timestamp=datetime.now(),
                regime=VolatilityRegime.HIGH if max(abs(put_skew), abs(call_skew)) > 0.1 else VolatilityRegime.MEDIUM,
                volatility=ivs[atm_index],
                forecast=None,
                supporting_data={
                    'put_skew': put_skew,
                    'call_skew': call_skew,
                    'skew_ratio': put_skew / call_skew if call_skew != 0 else 0,
                    'smile_curvature': self._calculate_smile_curvature(strikes, ivs)
                },
                metadata={'analysis_type': 'skew'}
            )
        
        return None
    
    def _calculate_smile_curvature(self, strikes: List[float], ivs: List[float]) -> float:
        """
        Calculate volatility smile curvature
        """
        if len(strikes) < 3 or len(ivs) < 3:
            return 0
        
        # Fit quadratic function to approximate smile
        x = np.array(strikes)
        y = np.array(ivs)
        z = np.polyfit(x, y, 2)
        
        # Return quadratic coefficient (curvature)
        return z[0]
    
    def _calculate_vol_percentile(self, vol: float) -> float:
        """
        Calculate historical percentile of volatility
        """
        if not self.vol_history:
            return 0.5
        
        return np.percentile(self.vol_history, vol)
    
    def _calculate_vol_zscore(self, vol: float) -> float:
        """
        Calculate z-score of volatility
        """
        if len(self.vol_history) < 2:
            return 0
        
        vol_mean = np.mean(self.vol_history)
        vol_std = np.std(self.vol_history)
        
        return (vol - vol_mean) / vol_std if vol_std > 0 else 0
    
    def _calculate_forecast_confidence(self, forecast: float) -> Tuple[float, float]:
        """
        Calculate confidence interval for volatility forecast
        """
        if len(self.vol_history) < 30:
            return (forecast * 0.8, forecast * 1.2)
        
        # Use historical forecast error distribution
        forecast_errors = []
        for i in range(len(self.forecasts) - 1):
            if i + 1 < len(self.vol_history):
                error = (self.vol_history[i + 1] - self.forecasts[i]) / self.forecasts[i]
                forecast_errors.append(error)
        
        if forecast_errors:
            error_std = np.std(forecast_errors)
            lower = forecast * (1 - 1.96 * error_std)
            upper = forecast * (1 + 1.96 * error_std)
            return (lower, upper)
        
        return (forecast * 0.8, forecast * 1.2)
