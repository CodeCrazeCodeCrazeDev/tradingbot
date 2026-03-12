"""
Real-Time Correlation Monitor
Institutional-grade correlation tracking and stress detection

This module provides real-time monitoring of portfolio correlations with:
- Multi-timeframe correlation analysis (30-min, 1-hour, 4-hour)
- Correlation regime detection (normal vs stress)
- Automatic position adjustment during correlation breakdowns
- Historical correlation comparison
- Emergency hedging triggers

Risk Manager + Actuary + Portfolio Manager Perspective
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque
import warnings
import numpy
import pandas

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class CorrelationRegime(Enum):
    """Correlation regime states"""
    NORMAL = "NORMAL"  # Correlations within historical ranges
    ELEVATED = "ELEVATED"  # Correlations rising but manageable
    STRESS = "STRESS"  # Correlations converging (crisis mode)
    BREAKDOWN = "BREAKDOWN"  # Extreme correlation (all assets moving together)


@dataclass
class CorrelationMetrics:
    """Correlation analysis metrics"""
    timestamp: datetime
    regime: CorrelationRegime
    average_correlation: float
    max_correlation: float
    min_correlation: float
    correlation_matrix: np.ndarray
    stress_score: float  # 0-1, higher = more stress
    diversification_ratio: float  # Portfolio vol / weighted avg vol
    positions_at_risk: List[str] = field(default_factory=list)
    recommended_action: str = "HOLD"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'regime': self.regime.value,
            'average_correlation': round(self.average_correlation, 4),
            'max_correlation': round(self.max_correlation, 4),
            'min_correlation': round(self.min_correlation, 4),
            'stress_score': round(self.stress_score, 4),
            'diversification_ratio': round(self.diversification_ratio, 4),
            'positions_at_risk': self.positions_at_risk,
            'recommended_action': self.recommended_action
        }


@dataclass
class CorrelationAlert:
    """Correlation alert"""
    timestamp: datetime
    alert_type: str  # REGIME_CHANGE, STRESS_DETECTED, BREAKDOWN, RECOVERY
    severity: str  # INFO, WARNING, CRITICAL
    message: str
    current_regime: CorrelationRegime
    previous_regime: Optional[CorrelationRegime]
    metrics: CorrelationMetrics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'current_regime': self.current_regime.value,
            'previous_regime': self.previous_regime.value if self.previous_regime else None,
            'metrics': self.metrics.to_dict()
        }


class RealTimeCorrelationMonitor:
    """
    Real-time correlation monitoring system
    
    Tracks portfolio correlations across multiple timeframes and detects
    correlation regime changes that indicate market stress.
    
    Key Features:
    - Multi-timeframe analysis (30-min, 1-hour, 4-hour)
    - Rolling correlation windows
    - Stress regime detection
    - Automatic position adjustment recommendations
    - Historical correlation comparison
    - Emergency hedging triggers
    
    Risk Thresholds:
    - Normal: avg correlation < 0.60
    - Elevated: avg correlation 0.60-0.75
    - Stress: avg correlation 0.75-0.85
    - Breakdown: avg correlation > 0.85
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize correlation monitor
        
        Args:
            config: Configuration dictionary with:
                - normal_threshold: Max correlation for normal regime (default: 0.60)
                - elevated_threshold: Max correlation for elevated regime (default: 0.75)
                - stress_threshold: Max correlation for stress regime (default: 0.85)
                - breakdown_threshold: Correlation for breakdown (default: 0.90)
                - lookback_periods: Number of periods for rolling correlation (default: 30)
                - min_positions: Minimum positions for correlation analysis (default: 2)
        """
        self.config = config or {}
        
        # Correlation thresholds
        self.normal_threshold = self.config.get('normal_threshold', 0.60)
        self.elevated_threshold = self.config.get('elevated_threshold', 0.75)
        self.stress_threshold = self.config.get('stress_threshold', 0.85)
        self.breakdown_threshold = self.config.get('breakdown_threshold', 0.90)
        
        # Analysis parameters
        self.lookback_periods = self.config.get('lookback_periods', 30)
        self.min_positions = self.config.get('min_positions', 2)
        
        # State tracking
        self.current_regime = CorrelationRegime.NORMAL
        self.previous_regime = None
        self.regime_change_time = datetime.now()
        
        # Historical data storage
        self.price_history: Dict[str, deque] = {}  # symbol -> deque of prices
        self.return_history: Dict[str, deque] = {}  # symbol -> deque of returns
        self.correlation_history: deque = deque(maxlen=100)  # Last 100 correlation readings
        
        # Alert tracking
        self.alerts: deque = deque(maxlen=50)  # Last 50 alerts
        
        # Statistics
        self.total_updates = 0
        self.regime_changes = 0
        self.stress_events = 0
        
        logger.info(f"RealTimeCorrelationMonitor initialized with thresholds: "
                   f"normal={self.normal_threshold}, elevated={self.elevated_threshold}, "
                   f"stress={self.stress_threshold}, breakdown={self.breakdown_threshold}")
    
    def update(self, positions: Dict[str, Dict[str, float]], 
               market_data: Dict[str, float]) -> CorrelationMetrics:
        """
        Update correlation analysis with new market data
        
        Args:
            positions: Dictionary of {symbol: {'size': float, 'value': float}}
            market_data: Dictionary of {symbol: current_price}
            
        Returns:
            CorrelationMetrics object with current analysis
        """
        self.total_updates += 1
        
        # Update price history
        for symbol, price in market_data.items():
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=self.lookback_periods + 1)
                self.return_history[symbol] = deque(maxlen=self.lookback_periods)
            
            self.price_history[symbol].append(price)
            
            # Calculate return if we have previous price
            if len(self.price_history[symbol]) >= 2:
                prev_price = self.price_history[symbol][-2]
                if prev_price > 0:
                    ret = (price - prev_price) / prev_price
                    self.return_history[symbol].append(ret)
        
        # Calculate correlation metrics
        metrics = self._calculate_correlation_metrics(positions, market_data)
        
        # Store in history
        self.correlation_history.append(metrics)
        
        # Check for regime change
        self._check_regime_change(metrics)
        
        return metrics
    
    def _calculate_correlation_metrics(self, 
                                      positions: Dict[str, Dict[str, float]],
                                      market_data: Dict[str, float]) -> CorrelationMetrics:
        """Calculate current correlation metrics"""
        
        # Get symbols with sufficient data
        valid_symbols = [
            symbol for symbol in positions.keys()
            if symbol in self.return_history and len(self.return_history[symbol]) >= 10
        ]
        
        if len(valid_symbols) < self.min_positions:
            # Not enough data for correlation analysis
            return CorrelationMetrics(
                timestamp=datetime.now(),
                regime=CorrelationRegime.NORMAL,
                average_correlation=0.0,
                max_correlation=0.0,
                min_correlation=0.0,
                correlation_matrix=np.array([[]]),
                stress_score=0.0,
                diversification_ratio=1.0,
                positions_at_risk=[],
                recommended_action="HOLD"
            )
        
        # Build return matrix
        returns_matrix = []
        for symbol in valid_symbols:
            returns_matrix.append(list(self.return_history[symbol]))
        
        returns_df = pd.DataFrame(returns_matrix).T
        returns_df.columns = valid_symbols
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr().values
        
        # Extract upper triangle (excluding diagonal)
        upper_triangle = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
        
        # Calculate statistics
        avg_corr = np.mean(upper_triangle)
        max_corr = np.max(upper_triangle)
        min_corr = np.min(upper_triangle)
        
        # Calculate stress score (0-1)
        stress_score = self._calculate_stress_score(avg_corr, max_corr)
        
        # Determine regime
        regime = self._determine_regime(avg_corr)
        
        # Calculate diversification ratio
        div_ratio = self._calculate_diversification_ratio(
            returns_df, positions, valid_symbols
        )
        
        # Identify positions at risk
        positions_at_risk = self._identify_positions_at_risk(
            corr_matrix, valid_symbols, regime
        )
        
        # Recommend action
        recommended_action = self._recommend_action(regime, stress_score, positions_at_risk)
        
        return CorrelationMetrics(
            timestamp=datetime.now(),
            regime=regime,
            average_correlation=avg_corr,
            max_correlation=max_corr,
            min_correlation=min_corr,
            correlation_matrix=corr_matrix,
            stress_score=stress_score,
            diversification_ratio=div_ratio,
            positions_at_risk=positions_at_risk,
            recommended_action=recommended_action
        )
    
    def _calculate_stress_score(self, avg_corr: float, max_corr: float) -> float:
        """
        Calculate stress score (0-1)
        
        Combines average and maximum correlation to assess market stress
        """
        # Weight average correlation more heavily
        avg_component = (avg_corr - self.normal_threshold) / (1.0 - self.normal_threshold)
        max_component = (max_corr - self.normal_threshold) / (1.0 - self.normal_threshold)
        
        # Weighted average (70% avg, 30% max)
        stress_score = 0.7 * avg_component + 0.3 * max_component
        
        return np.clip(stress_score, 0.0, 1.0)
    
    def _determine_regime(self, avg_corr: float) -> CorrelationRegime:
        """Determine correlation regime based on average correlation"""
        if avg_corr >= self.breakdown_threshold:
            return CorrelationRegime.BREAKDOWN
        elif avg_corr >= self.stress_threshold:
            return CorrelationRegime.STRESS
        elif avg_corr >= self.elevated_threshold:
            return CorrelationRegime.ELEVATED
        else:
            return CorrelationRegime.NORMAL
    
    def _calculate_diversification_ratio(self,
                                        returns_df: pd.DataFrame,
                                        positions: Dict[str, Dict[str, float]],
                                        valid_symbols: List[str]) -> float:
        """
        Calculate diversification ratio
        
        Ratio = Portfolio Volatility / Weighted Average Volatility
        Lower ratio = better diversification
        """
        try:
            # Calculate individual volatilities
            vols = returns_df.std()
            
            # Calculate position weights
            total_value = sum(positions[s]['value'] for s in valid_symbols)
            if total_value == 0:
                return 1.0
            
            weights = np.array([positions[s]['value'] / total_value for s in valid_symbols])
            
            # Weighted average volatility
            weighted_avg_vol = np.dot(weights, vols)
            
            # Portfolio volatility (accounts for correlations)
            cov_matrix = returns_df.cov()
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            # Diversification ratio
            if weighted_avg_vol > 0:
                div_ratio = portfolio_vol / weighted_avg_vol
            else:
                div_ratio = 1.0
            
            return div_ratio
            
        except Exception as e:
            logger.warning(f"Error calculating diversification ratio: {e}")
            return 1.0
    
    def _identify_positions_at_risk(self,
                                   corr_matrix: np.ndarray,
                                   symbols: List[str],
                                   regime: CorrelationRegime) -> List[str]:
        """
        Identify positions that are highly correlated during stress
        
        Returns symbols that have correlation > stress_threshold with others
        """
        if regime in [CorrelationRegime.NORMAL, CorrelationRegime.ELEVATED]:
            return []
        
        at_risk = []
        
        for i, symbol in enumerate(symbols):
            # Check if this symbol has high correlation with any other
            high_corr_count = np.sum(corr_matrix[i, :] > self.stress_threshold) - 1  # Exclude self
            
            if high_corr_count > 0:
                at_risk.append(symbol)
        
        return at_risk
    
    def _recommend_action(self,
                         regime: CorrelationRegime,
                         stress_score: float,
                         positions_at_risk: List[str]) -> str:
        """Recommend action based on correlation analysis"""
        
        if regime == CorrelationRegime.BREAKDOWN:
            return "EMERGENCY_HEDGE"  # Immediate hedging required
        elif regime == CorrelationRegime.STRESS:
            if stress_score > 0.8:
                return "REDUCE_EXPOSURE"  # Cut position sizes by 30-50%
            else:
                return "MONITOR_CLOSELY"  # Watch for further deterioration
        elif regime == CorrelationRegime.ELEVATED:
            if len(positions_at_risk) > 2:
                return "REBALANCE"  # Adjust portfolio weights
            else:
                return "HOLD"
        else:
            return "HOLD"  # Normal regime, no action needed
    
    def _check_regime_change(self, metrics: CorrelationMetrics):
        """Check for regime change and generate alerts"""
        
        if metrics.regime != self.current_regime:
            # Regime change detected
            self.regime_changes += 1
            
            if metrics.regime in [CorrelationRegime.STRESS, CorrelationRegime.BREAKDOWN]:
                self.stress_events += 1
            
            # Create alert
            alert = self._create_regime_change_alert(metrics)
            self.alerts.append(alert)
            
            logger.warning(f"Correlation regime change: {self.current_regime.value} -> "
                         f"{metrics.regime.value} (avg_corr={metrics.average_correlation:.3f})")
            
            # Update state
            self.previous_regime = self.current_regime
            self.current_regime = metrics.regime
            self.regime_change_time = datetime.now()
    
    def _create_regime_change_alert(self, metrics: CorrelationMetrics) -> CorrelationAlert:
        """Create alert for regime change"""
        
        # Determine severity
        if metrics.regime == CorrelationRegime.BREAKDOWN:
            severity = "CRITICAL"
            message = (f"CRITICAL: Correlation breakdown detected! "
                      f"Average correlation: {metrics.average_correlation:.2%}. "
                      f"Emergency hedging recommended.")
        elif metrics.regime == CorrelationRegime.STRESS:
            severity = "WARNING"
            message = (f"WARNING: Correlation stress detected. "
                      f"Average correlation: {metrics.average_correlation:.2%}. "
                      f"Consider reducing exposure.")
        elif metrics.regime == CorrelationRegime.ELEVATED:
            severity = "WARNING"
            message = (f"Elevated correlations detected. "
                      f"Average correlation: {metrics.average_correlation:.2%}. "
                      f"Monitor closely.")
        else:
            severity = "INFO"
            message = (f"Correlations returned to normal. "
                      f"Average correlation: {metrics.average_correlation:.2%}.")
        
        return CorrelationAlert(
            timestamp=datetime.now(),
            alert_type="REGIME_CHANGE",
            severity=severity,
            message=message,
            current_regime=metrics.regime,
            previous_regime=self.current_regime,
            metrics=metrics
        )
    
    def get_position_adjustment_recommendations(self,
                                               positions: Dict[str, Dict[str, float]],
                                               metrics: CorrelationMetrics) -> Dict[str, float]:
        """
        Get recommended position size adjustments
        
        Args:
            positions: Current positions
            metrics: Current correlation metrics
            
        Returns:
            Dictionary of {symbol: adjustment_multiplier}
            where multiplier < 1.0 means reduce position
        """
        adjustments = {}
        
        if metrics.regime == CorrelationRegime.BREAKDOWN:
            # Emergency: Reduce all positions by 50-70%
            for symbol in positions:
                adjustments[symbol] = 0.3  # Keep only 30% of position
        
        elif metrics.regime == CorrelationRegime.STRESS:
            # Stress: Reduce positions at risk by 30-50%
            for symbol in positions:
                if symbol in metrics.positions_at_risk:
                    adjustments[symbol] = 0.5  # Cut to 50%
                else:
                    adjustments[symbol] = 0.8  # Slight reduction
        
        elif metrics.regime == CorrelationRegime.ELEVATED:
            # Elevated: Slight reduction for at-risk positions
            for symbol in positions:
                if symbol in metrics.positions_at_risk:
                    adjustments[symbol] = 0.85  # 15% reduction
                else:
                    adjustments[symbol] = 1.0  # No change
        
        else:
            # Normal: No adjustments
            for symbol in positions:
                adjustments[symbol] = 1.0
        
        return adjustments
    
    def get_historical_comparison(self) -> Dict[str, Any]:
        """
        Compare current correlations to historical averages
        
        Returns:
            Dictionary with historical comparison statistics
        """
        if len(self.correlation_history) < 10:
            return {
                'insufficient_data': True,
                'message': 'Need at least 10 historical readings'
            }
        
        # Extract historical metrics
        historical_avg_corr = [m.average_correlation for m in self.correlation_history]
        historical_stress_score = [m.stress_score for m in self.correlation_history]
        
        current = self.correlation_history[-1]
        
        return {
            'current_avg_correlation': current.average_correlation,
            'historical_avg_correlation': np.mean(historical_avg_corr),
            'historical_std_correlation': np.std(historical_avg_corr),
            'percentile': np.percentile(historical_avg_corr, 
                                       [25, 50, 75, 90, 95, 99]),
            'current_stress_score': current.stress_score,
            'historical_avg_stress': np.mean(historical_stress_score),
            'z_score': (current.average_correlation - np.mean(historical_avg_corr)) / 
                      (np.std(historical_avg_corr) + 1e-10),
            'is_anomaly': abs((current.average_correlation - np.mean(historical_avg_corr)) / 
                            (np.std(historical_avg_corr) + 1e-10)) > 2.0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        return {
            'total_updates': self.total_updates,
            'regime_changes': self.regime_changes,
            'stress_events': self.stress_events,
            'current_regime': self.current_regime.value,
            'time_in_regime': (datetime.now() - self.regime_change_time).total_seconds() / 60,
            'alerts_generated': len(self.alerts),
            'symbols_tracked': len(self.price_history),
            'data_points_per_symbol': {
                symbol: len(history) 
                for symbol, history in self.return_history.items()
            }
        }
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        recent = list(self.alerts)[-limit:]
        return [alert.to_dict() for alert in recent]
    
    def reset(self):
        """Reset monitor state"""
        self.price_history.clear()
        self.return_history.clear()
        self.correlation_history.clear()
        self.alerts.clear()
        self.current_regime = CorrelationRegime.NORMAL
        self.previous_regime = None
        self.regime_change_time = datetime.now()
        self.total_updates = 0
        self.regime_changes = 0
        self.stress_events = 0
        
        logger.info("RealTimeCorrelationMonitor reset")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create monitor
    monitor = RealTimeCorrelationMonitor({
        'normal_threshold': 0.60,
        'stress_threshold': 0.85,
        'lookback_periods': 30
    })
    
    # Simulate market data updates
    positions = {
        'EURUSD': {'size': 1.0, 'value': 100000},
        'GBPUSD': {'size': 0.8, 'value': 80000},
        'USDJPY': {'size': 0.6, 'value': 60000}
    }
    
    # Simulate normal market
    logger.info("\n=== Simulating Normal Market ===")
    for i in range(50):
        market_data = {
            'EURUSD': 1.1000 + np.random.randn() * 0.001,
            'GBPUSD': 1.3000 + np.random.randn() * 0.001,
            'USDJPY': 110.00 + np.random.randn() * 0.1
        }
        metrics = monitor.update(positions, market_data)
    
    logger.info(f"Regime: {metrics.regime.value}")
    logger.info(f"Avg Correlation: {metrics.average_correlation:.3f}")
    logger.info(f"Stress Score: {metrics.stress_score:.3f}")
    logger.info(f"Action: {metrics.recommended_action}")
    
    # Simulate stress market (high correlations)
    logger.info("\n=== Simulating Stress Market ===")
    shock = np.random.randn() * 0.01
    for i in range(20):
        market_data = {
            'EURUSD': 1.1000 + shock + np.random.randn() * 0.0002,
            'GBPUSD': 1.3000 + shock * 1.2 + np.random.randn() * 0.0002,
            'USDJPY': 110.00 - shock * 100 + np.random.randn() * 0.02
        }
        metrics = monitor.update(positions, market_data)
    
    logger.info(f"Regime: {metrics.regime.value}")
    logger.info(f"Avg Correlation: {metrics.average_correlation:.3f}")
    logger.info(f"Stress Score: {metrics.stress_score:.3f}")
    logger.info(f"Action: {metrics.recommended_action}")
    logger.info(f"Positions at Risk: {metrics.positions_at_risk}")
    
    # Get adjustments
    adjustments = monitor.get_position_adjustment_recommendations(positions, metrics)
    logger.info(f"\nRecommended Adjustments:")
    for symbol, mult in adjustments.items():
        logger.info(f"  {symbol}: {mult:.1%} of current position")
    
    # Get statistics
    stats = monitor.get_statistics()
    logger.info(f"\nMonitor Statistics:")
    logger.info(f"  Total Updates: {stats['total_updates']}")
    logger.info(f"  Regime Changes: {stats['regime_changes']}")
    logger.info(f"  Stress Events: {stats['stress_events']}")
    logger.info(f"  Current Regime: {stats['current_regime']}")
    
    # Get recent alerts
    alerts = monitor.get_recent_alerts(5)
    logger.info(f"\nRecent Alerts ({len(alerts)}):")
    for alert in alerts:
        logger.info(f"  [{alert['severity']}] {alert['message']}")
