"""
Elite Trading Bot - Black Swan Protection

This module provides protection against extreme market events (black swan events)
through early warning systems, tail risk hedging, and emergency protocols.
"""

import enum
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import uuid
import asyncio

import numpy as np
import pandas as pd
try:
    from scipy import stats
except ImportError:
    scipy = None
from scipy.stats import jarque_bera, anderson
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class BlackSwanEventType(enum.Enum):
    """Types of black swan events."""
    MARKET_CRASH = "market_crash"                    # Severe market decline
    FLASH_CRASH = "flash_crash"                     # Rapid price collapse
    LIQUIDITY_EVAPORATION = "liquidity_evaporation" # Market liquidity disappears
    CORRELATION_BREAKDOWN = "correlation_breakdown"  # Historical correlations fail
    VOLATILITY_EXPLOSION = "volatility_explosion"   # Extreme volatility spike
    GAP_RISK = "gap_risk"                           # Large price gaps
    CURRENCY_CRISIS = "currency_crisis"             # Currency collapse
    CREDIT_CRISIS = "credit_crisis"                 # Credit market freeze
    SYSTEMIC_RISK = "systemic_risk"                 # System-wide failure
    TAIL_RISK_EVENT = "tail_risk_event"             # Statistical tail event


class ProtectionLevel(enum.Enum):
    """Protection activation levels."""
    NORMAL = "normal"           # Normal market conditions
    ELEVATED = "elevated"       # Heightened risk detected
    HIGH = "high"              # High risk - activate hedges
    CRITICAL = "critical"      # Critical risk - emergency protocols
    EMERGENCY = "emergency"    # Black swan event - full protection


@dataclass
class TailRiskMetrics:
    """Tail risk measurement metrics."""
    var_95: float = 0.0          # 95% Value at Risk
    var_99: float = 0.0          # 99% Value at Risk
    expected_shortfall_95: float = 0.0  # Expected Shortfall at 95%
    expected_shortfall_99: float = 0.0  # Expected Shortfall at 99%
    skewness: float = 0.0        # Distribution skewness
    kurtosis: float = 0.0        # Distribution kurtosis
    jarque_bera_stat: float = 0.0  # Jarque-Bera test statistic
    jarque_bera_pvalue: float = 1.0  # Jarque-Bera p-value
    anderson_stat: float = 0.0   # Anderson-Darling test statistic
    tail_ratio: float = 0.0      # Ratio of tail events
    max_drawdown_1d: float = 0.0 # Maximum 1-day drawdown
    max_drawdown_5d: float = 0.0 # Maximum 5-day drawdown


@dataclass
class BlackSwanAlert:
    """Black swan event alert."""
    id: str
    event_type: BlackSwanEventType
    protection_level: ProtectionLevel
    timestamp: datetime
    message: str
    probability: float           # Estimated probability of event
    severity_score: float        # Severity score (0-100)
    affected_assets: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    tail_metrics: Optional[TailRiskMetrics] = None
    market_indicators: Dict[str, float] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False


class TailRiskAnalyzer:
    """
    Analyzes tail risk and detects potential black swan events.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize tail risk analyzer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("TailRiskAnalyzer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "lookback_window": 252,        # 1 year of data
            "min_observations": 50,        # Minimum observations required
            "tail_threshold": 0.05,        # 5% tail threshold
            "extreme_threshold": 0.01,     # 1% extreme threshold
            "volatility_window": 20,       # Volatility calculation window
            "correlation_window": 60,      # Correlation window
            "gap_threshold": 0.02,         # 2% gap threshold
            "volume_threshold": 2.0,       # 2x normal volume threshold
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def calculate_tail_metrics(self, returns: pd.Series) -> TailRiskMetrics:
        """
        Calculate comprehensive tail risk metrics.
        
        Args:
            returns: Return series
            
        Returns:
            TailRiskMetrics object
        """
        if len(returns) < self.config["min_observations"]:
            return TailRiskMetrics()
        
        # Clean returns
        returns = returns.dropna()
        
        # Basic VaR calculations
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Expected Shortfall (Conditional VaR)
        tail_95 = returns[returns <= var_95]
        tail_99 = returns[returns <= var_99]
        
        es_95 = tail_95.mean() if len(tail_95) > 0 else var_95
        es_99 = tail_99.mean() if len(tail_99) > 0 else var_99
        
        # Distribution moments
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        try:
            # Normality tests
            jb_stat, jb_pvalue = jarque_bera(returns)
        except Exception:
            jb_stat, jb_pvalue = 0.0, 1.0
            ad_result = anderson(returns, dist='norm')
            ad_stat = ad_result.statistic
        except Exception:
            ad_stat = 0.0
        
        # Tail ratio (extreme events / total events)
        extreme_threshold = np.percentile(returns, 1)
        tail_events = len(returns[returns <= extreme_threshold])
        tail_ratio = tail_events / len(returns) if len(returns) > 0 else 0.0
        
        # Rolling maximum drawdowns
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        
        max_dd_1d = drawdowns.min()
        
        # 5-day rolling drawdown
        if len(returns) >= 5:
            returns_5d = returns.rolling(5).sum()
            cumulative_5d = (1 + returns_5d).cumprod()
            rolling_max_5d = cumulative_5d.expanding().max()
            drawdowns_5d = (cumulative_5d - rolling_max_5d) / rolling_max_5d
            max_dd_5d = drawdowns_5d.min()
        else:
            max_dd_5d = max_dd_1d
        
        return TailRiskMetrics(
            var_95=var_95,
            var_99=var_99,
            expected_shortfall_95=es_95,
            expected_shortfall_99=es_99,
            skewness=skewness,
            kurtosis=kurtosis,
            jarque_bera_stat=jb_stat,
            jarque_bera_pvalue=jb_pvalue,
            anderson_stat=ad_stat,
            tail_ratio=tail_ratio,
            max_drawdown_1d=max_dd_1d,
            max_drawdown_5d=max_dd_5d
        )
    
    def detect_volatility_regime_change(self, 
                                      returns: pd.Series,
                                      window: int = 20) -> Tuple[bool, float]:
        """
        Detect volatility regime changes that may signal black swan events.
        
        Args:
            returns: Return series
            window: Rolling window for volatility calculation
            
        Returns:
            Tuple of (regime_change_detected, current_volatility_percentile)
        """
        if len(returns) < window * 2:
            return False, 0.0
        
        # Calculate rolling volatility
        rolling_vol = returns.rolling(window).std()
        
        if len(rolling_vol.dropna()) < window:
            return False, 0.0
        
        # Current volatility
        current_vol = rolling_vol.iloc[-1]
        
        # Historical volatility distribution
        historical_vol = rolling_vol.dropna()[:-1]  # Exclude current observation
        
        # Calculate percentile of current volatility
        vol_percentile = stats.percentileofscore(historical_vol, current_vol) / 100
        
        # Detect regime change (volatility above 95th percentile)
        regime_change = vol_percentile > 0.95
        
        return regime_change, vol_percentile
    
    def detect_correlation_breakdown(self, 
                                   returns_dict: Dict[str, pd.Series],
                                   window: int = 60) -> Tuple[bool, float]:
        """
        Detect correlation breakdown that may signal systemic risk.
        
        Args:
            returns_dict: Dictionary of asset returns
            window: Rolling window for correlation calculation
            
        Returns:
            Tuple of (breakdown_detected, correlation_change_magnitude)
        """
        if len(returns_dict) < 2:
            return False, 0.0
        
        # Align returns
        returns_df = pd.DataFrame(returns_dict).dropna()
        
        if len(returns_df) < window * 2:
            return False, 0.0
        
        # Calculate rolling correlations
        recent_corr = returns_df.tail(window).corr()
        historical_corr = returns_df.iloc[:-window].corr()
        
        # Extract upper triangle (excluding diagonal)
        mask = np.triu(np.ones_like(recent_corr, dtype=bool), k=1)
        
        recent_corrs = recent_corr.where(mask).stack().dropna()
        historical_corrs = historical_corr.where(mask).stack().dropna()
        
        if len(recent_corrs) == 0 or len(historical_corrs) == 0:
            return False, 0.0
        
        # Calculate change in average correlation
        recent_avg = recent_corrs.mean()
        historical_avg = historical_corrs.mean()
        
        correlation_change = abs(recent_avg - historical_avg)
        
        # Detect breakdown (correlation change > 0.3)
        breakdown_detected = correlation_change > 0.3
        
        return breakdown_detected, correlation_change
    
    def detect_gap_risk(self, 
                       price_data: pd.DataFrame,
                       gap_threshold: float = 0.02) -> List[Dict[str, Any]]:
        """
        Detect price gaps that may indicate black swan events.
        
        Args:
            price_data: OHLC price data
            gap_threshold: Minimum gap size to detect
            
        Returns:
            List of gap events
        """
        gaps = []
        
        if len(price_data) < 2:
            return gaps
        
        # Calculate gaps between close and next open
        prev_close = price_data['close'].shift(1)
        current_open = price_data['open']
        
        gap_size = (current_open - prev_close) / prev_close
        
        # Find significant gaps
        significant_gaps = gap_size[abs(gap_size) > gap_threshold]
        
        for timestamp, gap in significant_gaps.items():
            gaps.append({
                'timestamp': timestamp,
                'gap_size': gap,
                'gap_direction': 'up' if gap > 0 else 'down',
                'severity': 'extreme' if abs(gap) > 0.05 else 'significant'
            })
        
        return gaps
    
    def calculate_black_swan_probability(self, 
                                       tail_metrics: TailRiskMetrics,
                                       market_indicators: Dict[str, float]) -> float:
        """
        Calculate probability of black swan event based on multiple factors.
        
        Args:
            tail_metrics: Tail risk metrics
            market_indicators: Additional market indicators
            
        Returns:
            Black swan probability (0-1)
        """
        probability_factors = []
        
        # Factor 1: Extreme tail risk
        if tail_metrics.var_99 < -0.05:  # 5% daily loss at 99% confidence
            probability_factors.append(0.3)
        elif tail_metrics.var_99 < -0.03:
            probability_factors.append(0.15)
        
        # Factor 2: High kurtosis (fat tails)
        if tail_metrics.kurtosis > 10:
            probability_factors.append(0.25)
        elif tail_metrics.kurtosis > 5:
            probability_factors.append(0.1)
        
        # Factor 3: Negative skewness
        if tail_metrics.skewness < -2:
            probability_factors.append(0.2)
        elif tail_metrics.skewness < -1:
            probability_factors.append(0.1)
        
        # Factor 4: Non-normal distribution
        if tail_metrics.jarque_bera_pvalue < 0.01:
            probability_factors.append(0.15)
        
        # Factor 5: High tail ratio
        if tail_metrics.tail_ratio > 0.05:
            probability_factors.append(0.2)
        
        # Factor 6: Market stress indicators
        vix_level = market_indicators.get('vix', 20)
        if vix_level > 40:
            probability_factors.append(0.3)
        elif vix_level > 30:
            probability_factors.append(0.15)
        
        # Factor 7: Credit spreads
        credit_spread = market_indicators.get('credit_spread', 100)
        if credit_spread > 500:  # 5% spread
            probability_factors.append(0.25)
        elif credit_spread > 300:
            probability_factors.append(0.1)
        
        # Combine factors (not simply additive to avoid over-weighting)
        if not probability_factors:
            return 0.0
        
        # Use geometric mean to combine probabilities
        combined_prob = np.prod([1 - p for p in probability_factors])
        black_swan_prob = 1 - combined_prob
        
        # Cap at reasonable maximum
        return min(black_swan_prob, 0.8)


class HedgingStrategy:
    """
    Implements tail risk hedging strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize hedging strategy.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Active hedges
        self.active_hedges: Dict[str, Dict[str, Any]] = {}
        
        logger.info("HedgingStrategy initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "max_hedge_allocation": 0.05,    # 5% max allocation to hedges
            "hedge_rebalance_threshold": 0.02, # 2% threshold for rebalancing
            "put_option_delta": -0.2,        # Target delta for put options
            "volatility_target": 0.15,       # 15% volatility target
            "correlation_hedge_threshold": 0.7, # Correlation threshold for hedging
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def calculate_hedge_allocation(self, 
                                 portfolio_value: float,
                                 protection_level: ProtectionLevel,
                                 tail_metrics: TailRiskMetrics) -> Dict[str, float]:
        """
        Calculate optimal hedge allocation based on protection level and tail risk.
        
        Args:
            portfolio_value: Current portfolio value
            protection_level: Current protection level
            tail_metrics: Tail risk metrics
            
        Returns:
            Dictionary of hedge allocations
        """
        allocations = {}
        
        # Base allocation based on protection level
        base_allocation_map = {
            ProtectionLevel.NORMAL: 0.01,      # 1%
            ProtectionLevel.ELEVATED: 0.02,    # 2%
            ProtectionLevel.HIGH: 0.03,        # 3%
            ProtectionLevel.CRITICAL: 0.04,    # 4%
            ProtectionLevel.EMERGENCY: 0.05,   # 5%
        }
        
        base_allocation = base_allocation_map.get(protection_level, 0.01)
        
        # Adjust based on tail risk metrics
        risk_multiplier = 1.0
        
        # Increase allocation for extreme tail risk
        if tail_metrics.var_99 < -0.05:
            risk_multiplier *= 1.5
        elif tail_metrics.var_99 < -0.03:
            risk_multiplier *= 1.2
        
        # Increase allocation for high kurtosis
        if tail_metrics.kurtosis > 10:
            risk_multiplier *= 1.3
        elif tail_metrics.kurtosis > 5:
            risk_multiplier *= 1.1
        
        # Calculate final allocation
        total_hedge_allocation = min(
            base_allocation * risk_multiplier,
            self.config["max_hedge_allocation"]
        )
        
        # Distribute across hedge types
        allocations = {
            "put_options": total_hedge_allocation * 0.4,      # 40% to put options
            "volatility_hedge": total_hedge_allocation * 0.3, # 30% to vol hedge
            "correlation_hedge": total_hedge_allocation * 0.2, # 20% to correlation hedge
            "tail_risk_fund": total_hedge_allocation * 0.1,   # 10% to tail risk fund
        }
        
        return allocations
    
    def generate_hedge_recommendations(self, 
                                     portfolio_positions: Dict[str, Any],
                                     protection_level: ProtectionLevel,
                                     tail_metrics: TailRiskMetrics) -> List[Dict[str, Any]]:
        """
        Generate specific hedge recommendations.
        
        Args:
            portfolio_positions: Current portfolio positions
            protection_level: Current protection level
            tail_metrics: Tail risk metrics
            
        Returns:
            List of hedge recommendations
        """
        recommendations = []
        
        # Put option hedges for equity exposure
        equity_exposure = sum(
            pos.get("market_value", 0) 
            for pos in portfolio_positions.values() 
            if pos.get("asset_class") == "equity"
        )
        
        if equity_exposure > 0 and protection_level in [ProtectionLevel.HIGH, ProtectionLevel.CRITICAL, ProtectionLevel.EMERGENCY]:
            recommendations.append({
                "hedge_type": "put_options",
                "underlying": "SPY",  # S&P 500 ETF
                "strategy": "protective_puts",
                "allocation": equity_exposure * 0.02,  # 2% of equity exposure
                "target_delta": self.config["put_option_delta"],
                "expiration": "1-3 months",
                "rationale": "Protect against equity market decline"
            })
        
        # Volatility hedge
        if tail_metrics.kurtosis > 5 or protection_level == ProtectionLevel.EMERGENCY:
            recommendations.append({
                "hedge_type": "volatility",
                "instrument": "VIX_calls",
                "strategy": "long_volatility",
                "allocation": 10000,  # Fixed dollar amount
                "target_strike": "20-30",
                "expiration": "1-2 months",
                "rationale": "Benefit from volatility spikes during market stress"
            })
        
        # Currency hedge for international exposure
        fx_exposure = sum(
            pos.get("market_value", 0) 
            for pos in portfolio_positions.values() 
            if pos.get("currency", "USD") != "USD"
        )
        
        if fx_exposure > 0 and protection_level in [ProtectionLevel.CRITICAL, ProtectionLevel.EMERGENCY]:
            recommendations.append({
                "hedge_type": "currency",
                "strategy": "fx_hedge",
                "allocation": fx_exposure * 0.5,  # Hedge 50% of FX exposure
                "instruments": ["USD_futures", "FX_forwards"],
                "rationale": "Protect against currency crisis"
            })
        
        # Correlation hedge
        if protection_level == ProtectionLevel.EMERGENCY:
            recommendations.append({
                "hedge_type": "correlation",
                "strategy": "uncorrelated_assets",
                "allocation": 20000,  # Fixed dollar amount
                "instruments": ["Gold", "Treasury_bonds", "Commodities"],
                "rationale": "Diversify into uncorrelated assets during correlation breakdown"
            })
        
        return recommendations


class EmergencyProtocol:
    """
    Implements emergency protocols for black swan events.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize emergency protocol.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Protocol state
        self.protocol_active = False
        self.activation_time: Optional[datetime] = None
        self.executed_actions: List[str] = []
        
        logger.info("EmergencyProtocol initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "auto_execute_threshold": ProtectionLevel.CRITICAL,
            "max_position_reduction": 0.5,     # Max 50% position reduction
            "emergency_cash_target": 0.2,      # Target 20% cash
            "stop_loss_tightening": 0.5,       # Tighten stops by 50%
            "correlation_threshold": 0.8,      # High correlation threshold
            "liquidity_threshold": 0.1,        # 10% of normal volume
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def activate_protocol(self, 
                         protection_level: ProtectionLevel,
                         black_swan_alert: BlackSwanAlert) -> List[str]:
        """
        Activate emergency protocol based on protection level.
        
        Args:
            protection_level: Current protection level
            black_swan_alert: Black swan alert that triggered protocol
            
        Returns:
            List of actions to execute
        """
        actions = []
        
        if protection_level == ProtectionLevel.EMERGENCY:
            actions.extend(self._emergency_actions(black_swan_alert))
        elif protection_level == ProtectionLevel.CRITICAL:
            actions.extend(self._critical_actions(black_swan_alert))
        elif protection_level == ProtectionLevel.HIGH:
            actions.extend(self._high_risk_actions(black_swan_alert))
        
        self.protocol_active = True
        self.activation_time = datetime.now()
        self.executed_actions.extend(actions)
        
        return actions
    
    def _emergency_actions(self, alert: BlackSwanAlert) -> List[str]:
        """Generate emergency-level actions."""
        return [
            "STOP_ALL_TRADING",
            "CLOSE_HIGH_RISK_POSITIONS",
            "ACTIVATE_HEDGES",
            "INCREASE_CASH_ALLOCATION",
            "TIGHTEN_STOP_LOSSES",
            "NOTIFY_RISK_MANAGER",
            "PREPARE_LIQUIDITY_RESERVES",
            "MONITOR_COUNTERPARTY_RISK"
        ]
    
    def _critical_actions(self, alert: BlackSwanAlert) -> List[str]:
        """Generate critical-level actions."""
        return [
            "REDUCE_POSITION_SIZES",
            "ACTIVATE_PROTECTIVE_HEDGES",
            "TIGHTEN_RISK_LIMITS",
            "INCREASE_MONITORING_FREQUENCY",
            "PREPARE_CONTINGENCY_PLANS",
            "REVIEW_CORRELATION_EXPOSURE"
        ]
    
    def _high_risk_actions(self, alert: BlackSwanAlert) -> List[str]:
        """Generate high-risk-level actions."""
        return [
            "INCREASE_CASH_BUFFER",
            "REVIEW_POSITION_CONCENTRATION",
            "ACTIVATE_VOLATILITY_HEDGES",
            "ENHANCE_MONITORING",
            "PREPARE_RISK_REDUCTION_PLAN"
        ]
    
    def deactivate_protocol(self) -> Dict[str, Any]:
        """
        Deactivate emergency protocol and return summary.
        
        Returns:
            Protocol execution summary
        """
        summary = {
            "activation_time": self.activation_time,
            "deactivation_time": datetime.now(),
            "duration": datetime.now() - self.activation_time if self.activation_time else timedelta(0),
            "executed_actions": self.executed_actions.copy(),
            "total_actions": len(self.executed_actions)
        }
        
        # Reset state
        self.protocol_active = False
        self.activation_time = None
        self.executed_actions.clear()
        
        return summary


class BlackSwanProtector:
    """
    Main black swan protection system that coordinates all protection components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize black swan protector.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Initialize components
        self.tail_analyzer = TailRiskAnalyzer(self.config.get("tail_analyzer_config"))
        self.hedging_strategy = HedgingStrategy(self.config.get("hedging_config"))
        self.emergency_protocol = EmergencyProtocol(self.config.get("emergency_config"))
        
        # Protection state
        self.current_protection_level = ProtectionLevel.NORMAL
        self.active_alerts: List[BlackSwanAlert] = []
        self.alert_history: List[BlackSwanAlert] = []
        
        # Event handlers
        self.alert_handlers: List[Callable[[BlackSwanAlert], None]] = []
        
        logger.info("BlackSwanProtector initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "monitoring_enabled": True,
            "auto_hedge_enabled": True,
            "auto_protocol_enabled": False,  # Require manual activation
            "alert_cooldown_minutes": 30,    # Cooldown between similar alerts
            "max_active_alerts": 50,         # Maximum active alerts
            "max_alert_history": 500,        # Maximum alert history
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def analyze_black_swan_risk(self, 
                               portfolio_returns: pd.Series,
                               market_data: Dict[str, pd.DataFrame],
                               market_indicators: Dict[str, float]) -> Tuple[ProtectionLevel, List[BlackSwanAlert]]:
        """
        Analyze black swan risk and generate alerts.
        
        Args:
            portfolio_returns: Portfolio return series
            market_data: Market data for analysis
            market_indicators: Additional market indicators
            
        Returns:
            Tuple of (protection_level, new_alerts)
        """
        new_alerts = []
        
        if not self.config["monitoring_enabled"]:
            return self.current_protection_level, new_alerts
        try:
        
            # Calculate tail risk metrics
            tail_metrics = self.tail_analyzer.calculate_tail_metrics(portfolio_returns)
            
            # Detect volatility regime changes
            vol_regime_change, vol_percentile = self.tail_analyzer.detect_volatility_regime_change(portfolio_returns)
            
            # Detect correlation breakdown
            if len(market_data) > 1:
                returns_dict = {}
                for symbol, data in market_data.items():
                    if 'close' in data.columns:
                        returns_dict[symbol] = data['close'].pct_change().dropna()
                
                corr_breakdown, corr_change = self.tail_analyzer.detect_correlation_breakdown(returns_dict)
            else:
                corr_breakdown, corr_change = False, 0.0
            
            # Detect gap risk
            gap_events = []
            for symbol, data in market_data.items():
                if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
                    symbol_gaps = self.tail_analyzer.detect_gap_risk(data)
                    gap_events.extend(symbol_gaps)
            
            # Calculate black swan probability
            black_swan_prob = self.tail_analyzer.calculate_black_swan_probability(tail_metrics, market_indicators)
            
            # Determine protection level
            new_protection_level = self._determine_protection_level(
                tail_metrics, vol_percentile, corr_breakdown, gap_events, black_swan_prob
            )
            
            # Generate alerts based on detected risks
            if vol_regime_change and vol_percentile > 0.95:
                new_alerts.append(self._create_alert(
                    BlackSwanEventType.VOLATILITY_EXPLOSION,
                    new_protection_level,
                    f"Volatility explosion detected: {vol_percentile:.1%} percentile",
                    black_swan_prob,
                    tail_metrics,
                    market_indicators
                ))
            
            if corr_breakdown:
                new_alerts.append(self._create_alert(
                    BlackSwanEventType.CORRELATION_BREAKDOWN,
                    new_protection_level,
                    f"Correlation breakdown detected: {corr_change:.3f} change",
                    black_swan_prob,
                    tail_metrics,
                    market_indicators
                ))
            
            if gap_events:
                extreme_gaps = [g for g in gap_events if g['severity'] == 'extreme']
                if extreme_gaps:
                    new_alerts.append(self._create_alert(
                        BlackSwanEventType.GAP_RISK,
                        new_protection_level,
                        f"Extreme price gaps detected: {len(extreme_gaps)} events",
                        black_swan_prob,
                        tail_metrics,
                        market_indicators
                    ))
            
            if black_swan_prob > 0.3:
                new_alerts.append(self._create_alert(
                    BlackSwanEventType.TAIL_RISK_EVENT,
                    new_protection_level,
                    f"High black swan probability: {black_swan_prob:.1%}",
                    black_swan_prob,
                    tail_metrics,
                    market_indicators
                ))
            
            # Update protection level
            self.current_protection_level = new_protection_level
            
            # Add alerts to active list
            self.active_alerts.extend(new_alerts)
            self.alert_history.extend(new_alerts)
            
            # Manage alert lists
            self._manage_alert_lists()
            
            # Trigger alert handlers
            for alert in new_alerts:
                self._trigger_alert_handlers(alert)
            
        except Exception as e:
            logger.error(f"Error in black swan risk analysis: {e}")
            
            # Create system error alert
            error_alert = self._create_alert(
                BlackSwanEventType.SYSTEMIC_RISK,
                ProtectionLevel.ELEVATED,
                f"Black swan monitoring system error: {str(e)}",
                0.0,
                TailRiskMetrics(),
                market_indicators
            )
            new_alerts.append(error_alert)
        
        return self.current_protection_level, new_alerts
    
    def _determine_protection_level(self, 
                                  tail_metrics: TailRiskMetrics,
                                  vol_percentile: float,
                                  corr_breakdown: bool,
                                  gap_events: List[Dict[str, Any]],
                                  black_swan_prob: float) -> ProtectionLevel:
        """Determine appropriate protection level based on risk factors."""
        
        # Start with normal level
        level_score = 0
        
        # Tail risk factors
        if tail_metrics.var_99 < -0.08:  # 8% daily loss
            level_score += 4  # Emergency
        elif tail_metrics.var_99 < -0.05:  # 5% daily loss
            level_score += 3  # Critical
        elif tail_metrics.var_99 < -0.03:  # 3% daily loss
            level_score += 2  # High
        elif tail_metrics.var_99 < -0.02:  # 2% daily loss
            level_score += 1  # Elevated
        
        # Kurtosis (fat tails)
        if tail_metrics.kurtosis > 15:
            level_score += 3
        elif tail_metrics.kurtosis > 10:
            level_score += 2
        elif tail_metrics.kurtosis > 5:
            level_score += 1
        
        # Volatility regime
        if vol_percentile > 0.99:
            level_score += 3
        elif vol_percentile > 0.95:
            level_score += 2
        elif vol_percentile > 0.90:
            level_score += 1
        
        # Correlation breakdown
        if corr_breakdown:
            level_score += 2
        
        # Gap risk
        extreme_gaps = len([g for g in gap_events if g['severity'] == 'extreme'])
        if extreme_gaps > 0:
            level_score += min(extreme_gaps, 3)
        
        # Black swan probability
        if black_swan_prob > 0.5:
            level_score += 3
        elif black_swan_prob > 0.3:
            level_score += 2
        elif black_swan_prob > 0.1:
            level_score += 1
        
        # Map score to protection level
        if level_score >= 8:
            return ProtectionLevel.EMERGENCY
        elif level_score >= 6:
            return ProtectionLevel.CRITICAL
        elif level_score >= 4:
            return ProtectionLevel.HIGH
        elif level_score >= 2:
            return ProtectionLevel.ELEVATED
        else:
            return ProtectionLevel.NORMAL
    
    def _create_alert(self, 
                     event_type: BlackSwanEventType,
                     protection_level: ProtectionLevel,
                     message: str,
                     probability: float,
                     tail_metrics: TailRiskMetrics,
                     market_indicators: Dict[str, float]) -> BlackSwanAlert:
        """Create a black swan alert."""
        
        severity_map = {
            ProtectionLevel.NORMAL: 0,
            ProtectionLevel.ELEVATED: 25,
            ProtectionLevel.HIGH: 50,
            ProtectionLevel.CRITICAL: 75,
            ProtectionLevel.EMERGENCY: 100
        }
        
        action_map = {
            ProtectionLevel.ELEVATED: ["Monitor closely", "Review risk exposure"],
            ProtectionLevel.HIGH: ["Activate hedges", "Reduce position sizes", "Increase cash buffer"],
            ProtectionLevel.CRITICAL: ["Implement protective hedges", "Reduce leverage", "Prepare contingency plans"],
            ProtectionLevel.EMERGENCY: ["Execute emergency protocol", "Stop trading", "Preserve capital"]
        }
        
        return BlackSwanAlert(
            id=f"bs_{event_type.value}_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            protection_level=protection_level,
            timestamp=datetime.now(),
            message=message,
            probability=probability,
            severity_score=severity_map.get(protection_level, 0),
            recommended_actions=action_map.get(protection_level, []),
            tail_metrics=tail_metrics,
            market_indicators=market_indicators.copy()
        )
    
    def get_hedge_recommendations(self, 
                                portfolio_positions: Dict[str, Any],
                                portfolio_value: float) -> List[Dict[str, Any]]:
        """Get current hedge recommendations."""
        if not self.config["auto_hedge_enabled"]:
            return []
        
        # Get latest tail metrics from active alerts
        latest_tail_metrics = TailRiskMetrics()
        for alert in reversed(self.active_alerts):
            if alert.tail_metrics:
                latest_tail_metrics = alert.tail_metrics
                break
        
        return self.hedging_strategy.generate_hedge_recommendations(
            portfolio_positions,
            self.current_protection_level,
            latest_tail_metrics
        )
    
    def execute_emergency_protocol(self, alert: BlackSwanAlert) -> List[str]:
        """Execute emergency protocol for black swan event."""
        if not self.config["auto_protocol_enabled"]:
            return ["Emergency protocol requires manual activation"]
        
        return self.emergency_protocol.activate_protocol(
            self.current_protection_level,
            alert
        )
    
    def _manage_alert_lists(self):
        """Manage size of alert lists."""
        # Remove resolved alerts from active list
        self.active_alerts = [alert for alert in self.active_alerts if not alert.resolved]
        
        # Limit active alerts
        if len(self.active_alerts) > self.config["max_active_alerts"]:
            self.active_alerts = self.active_alerts[-self.config["max_active_alerts"]:]
        
        # Limit alert history
        if len(self.alert_history) > self.config["max_alert_history"]:
            self.alert_history = self.alert_history[-self.config["max_alert_history"]:]
    
    def _trigger_alert_handlers(self, alert: BlackSwanAlert):
        """Trigger registered alert handlers."""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    def register_alert_handler(self, handler: Callable[[BlackSwanAlert], None]):
        """Register an alert handler."""
        self.alert_handlers.append(handler)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a black swan alert."""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve a black swan alert."""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.resolved = True
                return True
        return False
    
    def get_protection_summary(self) -> Dict[str, Any]:
        """Get comprehensive protection summary."""
        return {
            "current_protection_level": self.current_protection_level.value,
            "active_alerts": len(self.active_alerts),
            "unacknowledged_alerts": len([a for a in self.active_alerts if not a.acknowledged]),
            "emergency_protocol_active": self.emergency_protocol.protocol_active,
            "monitoring_enabled": self.config["monitoring_enabled"],
            "auto_hedge_enabled": self.config["auto_hedge_enabled"],
            "auto_protocol_enabled": self.config["auto_protocol_enabled"],
            "recent_alerts": [
                {
                    "id": alert.id,
                    "type": alert.event_type.value,
                    "level": alert.protection_level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "probability": alert.probability
                }
                for alert in self.active_alerts[-5:]
            ]
        }
