"""
Elite Trading Bot - Risk Engine

This module provides the core risk management engine for the Elite Trading Bot,
implementing comprehensive risk assessment, monitoring, and control mechanisms.
"""

import enum
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import uuid

import numpy as np
import pandas as pd
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class RiskLevel(enum.Enum):
    """Risk levels for trades and portfolio."""
    VERY_LOW = "very_low"      # Very low risk (0-10%)
    LOW = "low"                # Low risk (10-25%)
    MODERATE = "moderate"      # Moderate risk (25-50%)
    HIGH = "high"              # High risk (50-75%)
    VERY_HIGH = "very_high"    # Very high risk (75-90%)
    EXTREME = "extreme"        # Extreme risk (90%+)


@dataclass
class RiskMetrics:
    """Risk metrics for a trade or portfolio."""
    var_1d: float              # 1-day Value at Risk
    var_5d: float              # 5-day Value at Risk
    expected_shortfall: float   # Expected Shortfall (CVaR)
    max_drawdown: float        # Maximum drawdown
    sharpe_ratio: float        # Sharpe ratio
    sortino_ratio: float       # Sortino ratio
    volatility: float          # Annualized volatility
    beta: Optional[float] = None  # Beta vs benchmark
    correlation: Optional[float] = None  # Correlation with market
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskLimits:
    """Risk limits configuration."""
    max_position_size_pct: float = 5.0      # Max position size as % of portfolio
    max_sector_exposure_pct: float = 20.0    # Max sector exposure
    max_single_loss_pct: float = 2.0        # Max single trade loss
    max_daily_loss_pct: float = 5.0         # Max daily portfolio loss
    max_drawdown_pct: float = 10.0          # Max portfolio drawdown
    max_leverage: float = 3.0               # Maximum leverage
    min_liquidity_ratio: float = 0.1        # Minimum cash/liquidity ratio
    max_correlation: float = 0.7            # Max correlation between positions
    var_limit_pct: float = 3.0              # VaR limit as % of portfolio
    concentration_limit_pct: float = 25.0   # Max concentration in single asset


@dataclass
class TradeRisk:
    """Risk assessment for a single trade."""
    trade_id: str
    symbol: str
    direction: str             # "long" or "short"
    entry_price: float
    position_size: float
    stop_loss: float
    take_profit: Optional[float]
    risk_amount: float         # Dollar risk amount
    risk_pct: float           # Risk as % of portfolio
    reward_risk_ratio: float   # Reward to risk ratio
    probability_success: Optional[float] = None  # Estimated probability of success
    expected_value: Optional[float] = None       # Expected value of trade
    risk_level: RiskLevel = RiskLevel.MODERATE
    confidence: float = 0.5    # Confidence in risk assessment
    notes: str = ""


@dataclass
class PortfolioRisk:
    """Risk assessment for entire portfolio."""
    total_value: float
    cash_balance: float
    total_exposure: float
    leverage: float
    var_1d: float
    var_5d: float
    expected_shortfall: float
    max_drawdown: float
    current_drawdown: float
    volatility: float
    sharpe_ratio: float
    beta: Optional[float] = None
    largest_position_pct: float = 0.0
    sector_concentrations: Dict[str, float] = field(default_factory=dict)
    correlation_risk: float = 0.0
    liquidity_ratio: float = 1.0
    risk_level: RiskLevel = RiskLevel.MODERATE
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskAlert:
    """Risk alert notification."""
    id: str
    alert_type: str           # "limit_breach", "high_correlation", "drawdown", etc.
    severity: RiskLevel
    message: str
    affected_positions: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False


class RiskEngine:
    """
    Core risk management engine that assesses, monitors, and controls
    trading risks across individual trades and portfolio level.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize risk engine.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Risk limits
        self.risk_limits = RiskLimits(**self.config.get("risk_limits", {}))
        
        # Active positions and trades
        self.active_positions: Dict[str, Dict[str, Any]] = {}
        self.trade_history: List[TradeRisk] = []
        self.portfolio_history: List[PortfolioRisk] = []
        
        # Risk alerts
        self.active_alerts: List[RiskAlert] = []
        self.alert_history: List[RiskAlert] = []
        
        # Portfolio metrics
        self.current_portfolio_risk: Optional[PortfolioRisk] = None
        
        logger.info("RiskEngine initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "portfolio_value": 100000.0,  # Default portfolio value
            "risk_free_rate": 0.02,       # Risk-free rate for Sharpe calculation
            "confidence_level": 0.95,     # Confidence level for VaR
            "lookback_days": 252,         # Lookback period for risk calculations
            "rebalance_threshold": 0.05,  # Portfolio rebalance threshold
            "correlation_window": 60,     # Days for correlation calculation
            "volatility_window": 30,      # Days for volatility calculation
            "enable_stress_testing": True,  # Enable stress testing
            "enable_real_time_monitoring": True,  # Enable real-time monitoring
            "alert_cooldown_minutes": 30,  # Cooldown period for duplicate alerts
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def assess_trade_risk(self, 
                         trade_id: str,
                         symbol: str,
                         direction: str,
                         entry_price: float,
                         position_size: float,
                         stop_loss: float,
                         take_profit: Optional[float] = None,
                         market_data: Optional[pd.DataFrame] = None) -> TradeRisk:
        """
        Assess risk for a proposed trade.
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading symbol
            direction: Trade direction ("long" or "short")
            entry_price: Entry price
            position_size: Position size in dollars
            stop_loss: Stop loss level
            take_profit: Optional take profit level
            market_data: Optional market data for analysis
            
        Returns:
            TradeRisk assessment
        """
        # Calculate risk amount
        if direction == "long":
            risk_per_share = entry_price - stop_loss
        else:
            risk_per_share = stop_loss - entry_price
        
        shares = position_size / entry_price
        risk_amount = abs(risk_per_share * shares)
        
        # Calculate risk as percentage of portfolio
        portfolio_value = self.config["portfolio_value"]
        risk_pct = (risk_amount / portfolio_value) * 100
        
        # Calculate reward-to-risk ratio
        reward_risk_ratio = 1.0  # Default
        if take_profit is not None:
            if direction == "long":
                reward_per_share = take_profit - entry_price
            else:
                reward_per_share = entry_price - take_profit
            
            reward_amount = reward_per_share * shares
            if risk_amount > 0:
                reward_risk_ratio = reward_amount / risk_amount
        
        # Estimate probability of success (simplified model)
        probability_success = self._estimate_trade_probability(
            symbol, direction, entry_price, stop_loss, take_profit, market_data
        )
        
        # Calculate expected value
        expected_value = None
        if probability_success is not None and take_profit is not None:
            win_amount = abs((take_profit - entry_price) * shares)
            loss_amount = risk_amount
            expected_value = (probability_success * win_amount) - ((1 - probability_success) * loss_amount)
        
        # Determine risk level
        risk_level = self._categorize_risk_level(risk_pct)
        
        # Calculate confidence in assessment
        confidence = 0.7  # Base confidence
        if market_data is not None and len(market_data) > 30:
            confidence = 0.8  # Higher confidence with more data
        
        # Create trade risk assessment
        trade_risk = TradeRisk(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            risk_pct=risk_pct,
            reward_risk_ratio=reward_risk_ratio,
            probability_success=probability_success,
            expected_value=expected_value,
            risk_level=risk_level,
            confidence=confidence,
            notes=f"Risk assessment for {symbol} {direction} trade"
        )
        
        return trade_risk
    
    def _estimate_trade_probability(self, 
                                  symbol: str,
                                  direction: str,
                                  entry_price: float,
                                  stop_loss: float,
                                  take_profit: Optional[float],
                                  market_data: Optional[pd.DataFrame]) -> Optional[float]:
        """
        Estimate probability of trade success.
        
        Args:
            symbol: Trading symbol
            direction: Trade direction
            entry_price: Entry price
            stop_loss: Stop loss level
            take_profit: Take profit level
            market_data: Market data for analysis
            
        Returns:
            Estimated probability of success (0.0 to 1.0) or None
        """
        if market_data is None or len(market_data) < 20:
            return None
        
        # Calculate historical win rate for similar setups
        df = market_data.copy()
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        # Calculate volatility
        volatility = df['returns'].std() * np.sqrt(252)  # Annualized
        
        # Calculate distance to targets as multiples of daily volatility
        daily_vol = df['close'].rolling(20).std().iloc[-1]
        
        if daily_vol == 0:
            return 0.5  # Default probability
        
        # Distance to stop loss and take profit in volatility units
        stop_distance = abs(entry_price - stop_loss) / daily_vol
        
        if take_profit is not None:
            target_distance = abs(take_profit - entry_price) / daily_vol
        else:
            target_distance = stop_distance * 2  # Assume 2:1 RR
        
        # Simple probability model based on volatility-adjusted distances
        # Closer stops have higher hit probability, farther targets have lower hit probability
        base_probability = 0.5
        
        # Adjust based on stop distance (closer stops = higher probability of being hit)
        stop_adjustment = -0.1 * (stop_distance - 1.0)  # Penalty for wide stops
        
        # Adjust based on target distance (farther targets = lower probability)
        target_adjustment = -0.05 * (target_distance - 2.0)  # Penalty for ambitious targets
        
        # Adjust based on trend (simplified)
        recent_trend = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
        
        if direction == "long" and recent_trend > 0:
            trend_adjustment = 0.1  # Bonus for trading with trend
        elif direction == "short" and recent_trend < 0:
            trend_adjustment = 0.1  # Bonus for trading with trend
        else:
            trend_adjustment = -0.05  # Penalty for trading against trend
        
        # Calculate final probability
        probability = base_probability + stop_adjustment + target_adjustment + trend_adjustment
        
        # Clamp to reasonable range
        probability = max(0.2, min(0.8, probability))
        
        return probability
    
    def _categorize_risk_level(self, risk_pct: float) -> RiskLevel:
        """Categorize risk level based on risk percentage."""
        if risk_pct <= 0.5:
            return RiskLevel.VERY_LOW
        elif risk_pct <= 1.0:
            return RiskLevel.LOW
        elif risk_pct <= 2.0:
            return RiskLevel.MODERATE
        elif risk_pct <= 3.0:
            return RiskLevel.HIGH
        elif risk_pct <= 5.0:
            return RiskLevel.VERY_HIGH
        else:
            return RiskLevel.EXTREME
    
    def assess_portfolio_risk(self, 
                            positions: Dict[str, Dict[str, Any]],
                            market_data: Dict[str, pd.DataFrame]) -> PortfolioRisk:
        """
        Assess overall portfolio risk.
        
        Args:
            positions: Dictionary of position_id -> position_info
            market_data: Dictionary of symbol -> market data
            
        Returns:
            PortfolioRisk assessment
        """
        portfolio_value = self.config["portfolio_value"]
        
        # Calculate basic portfolio metrics
        total_exposure = sum(pos.get("market_value", 0) for pos in positions.values())
        cash_balance = portfolio_value - total_exposure
        leverage = total_exposure / portfolio_value if portfolio_value > 0 else 0
        
        # Calculate position concentrations
        largest_position_pct = 0
        sector_concentrations = {}
        
        for pos in positions.values():
            position_pct = (pos.get("market_value", 0) / portfolio_value) * 100
            largest_position_pct = max(largest_position_pct, position_pct)
            
            # Sector concentration (simplified - would need sector mapping)
            sector = pos.get("sector", "Unknown")
            sector_concentrations[sector] = sector_concentrations.get(sector, 0) + position_pct
        
        # Calculate portfolio returns for risk metrics
        portfolio_returns = self._calculate_portfolio_returns(positions, market_data)
        
        # Calculate VaR and other risk metrics
        var_1d, var_5d = self._calculate_var(portfolio_returns)
        expected_shortfall = self._calculate_expected_shortfall(portfolio_returns)
        max_drawdown, current_drawdown = self._calculate_drawdown(portfolio_returns)
        volatility = self._calculate_volatility(portfolio_returns)
        sharpe_ratio = self._calculate_sharpe_ratio(portfolio_returns)
        
        # Calculate correlation risk
        correlation_risk = self._calculate_correlation_risk(positions, market_data)
        
        # Calculate liquidity ratio
        liquidity_ratio = cash_balance / portfolio_value if portfolio_value > 0 else 0
        
        # Determine overall risk level
        risk_factors = [
            leverage > self.risk_limits.max_leverage,
            largest_position_pct > self.risk_limits.max_position_size_pct,
            current_drawdown > self.risk_limits.max_drawdown_pct,
            abs(var_1d) > self.risk_limits.var_limit_pct,
            correlation_risk > self.risk_limits.max_correlation,
            liquidity_ratio < self.risk_limits.min_liquidity_ratio
        ]
        
        risk_score = sum(risk_factors) / len(risk_factors)
        
        if risk_score <= 0.2:
            risk_level = RiskLevel.LOW
        elif risk_score <= 0.4:
            risk_level = RiskLevel.MODERATE
        elif risk_score <= 0.6:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH
        
        # Create portfolio risk assessment
        portfolio_risk = PortfolioRisk(
            total_value=portfolio_value,
            cash_balance=cash_balance,
            total_exposure=total_exposure,
            leverage=leverage,
            var_1d=var_1d,
            var_5d=var_5d,
            expected_shortfall=expected_shortfall,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            largest_position_pct=largest_position_pct,
            sector_concentrations=sector_concentrations,
            correlation_risk=correlation_risk,
            liquidity_ratio=liquidity_ratio,
            risk_level=risk_level
        )
        
        # Store current portfolio risk
        self.current_portfolio_risk = portfolio_risk
        self.portfolio_history.append(portfolio_risk)
        
        # Keep history manageable
        if len(self.portfolio_history) > 1000:
            self.portfolio_history = self.portfolio_history[-1000:]
        
        return portfolio_risk
    
    def _calculate_portfolio_returns(self, 
                                   positions: Dict[str, Dict[str, Any]],
                                   market_data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Calculate portfolio returns time series."""
        if not positions or not market_data:
            return pd.Series(dtype=float)
        
        # Get common date range
        all_dates = None
        for symbol, data in market_data.items():
            if all_dates is None:
                all_dates = data.index
            else:
                all_dates = all_dates.intersection(data.index)
        
        if all_dates is None or len(all_dates) < 2:
            return pd.Series(dtype=float)
        
        # Calculate weighted returns
        portfolio_returns = pd.Series(0.0, index=all_dates)
        total_weight = 0
        
        for pos_id, pos in positions.items():
            symbol = pos.get("symbol")
            weight = pos.get("weight", 0)  # Position weight in portfolio
            
            if symbol in market_data and weight > 0:
                returns = market_data[symbol]['close'].pct_change().fillna(0)
                portfolio_returns += returns * weight
                total_weight += weight
        
        # Normalize if needed
        if total_weight > 0:
            portfolio_returns = portfolio_returns / total_weight
        
        return portfolio_returns.dropna()
    
    def _calculate_var(self, returns: pd.Series) -> Tuple[float, float]:
        """Calculate Value at Risk."""
        if len(returns) < 10:
            return 0.0, 0.0
        
        confidence_level = self.config["confidence_level"]
        
        # 1-day VaR
        var_1d = np.percentile(returns, (1 - confidence_level) * 100)
        
        # 5-day VaR (assuming independence)
        var_5d = var_1d * np.sqrt(5)
        
        return var_1d * 100, var_5d * 100  # Convert to percentage
    
    def _calculate_expected_shortfall(self, returns: pd.Series) -> float:
        """Calculate Expected Shortfall (Conditional VaR)."""
        if len(returns) < 10:
            return 0.0
        
        confidence_level = self.config["confidence_level"]
        var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
        
        # Expected Shortfall is the mean of returns below VaR threshold
        tail_returns = returns[returns <= var_threshold]
        
        if len(tail_returns) > 0:
            return tail_returns.mean() * 100  # Convert to percentage
        else:
            return var_threshold * 100
    
    def _calculate_drawdown(self, returns: pd.Series) -> Tuple[float, float]:
        """Calculate maximum and current drawdown."""
        if len(returns) < 2:
            return 0.0, 0.0
        
        # Calculate cumulative returns
        cumulative = (1 + returns).cumprod()
        
        # Calculate running maximum
        running_max = cumulative.expanding().max()
        
        # Calculate drawdown
        drawdown = (cumulative - running_max) / running_max
        
        max_drawdown = drawdown.min() * 100  # Convert to percentage
        current_drawdown = drawdown.iloc[-1] * 100
        
        return max_drawdown, current_drawdown
    
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility."""
        if len(returns) < 2:
            return 0.0
        
        return returns.std() * np.sqrt(252) * 100  # Annualized percentage
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0.0
        
        risk_free_rate = self.config["risk_free_rate"]
        excess_returns = returns.mean() * 252 - risk_free_rate  # Annualized
        volatility = returns.std() * np.sqrt(252)
        
        if volatility > 0:
            return excess_returns / volatility
        else:
            return 0.0
    
    def _calculate_correlation_risk(self, 
                                  positions: Dict[str, Dict[str, Any]],
                                  market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate correlation risk between positions."""
        if len(positions) < 2:
            return 0.0
        
        symbols = [pos.get("symbol") for pos in positions.values() if pos.get("symbol")]
        
        if len(symbols) < 2:
            return 0.0
        
        # Calculate correlation matrix
        returns_data = {}
        for symbol in symbols:
            if symbol in market_data:
                returns = market_data[symbol]['close'].pct_change().dropna()
                returns_data[symbol] = returns
        
        if len(returns_data) < 2:
            return 0.0
        
        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_data).dropna()
        
        if len(returns_df) < 10:
            return 0.0
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        
        # Calculate average absolute correlation (excluding diagonal)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        correlations = corr_matrix.where(mask).stack().dropna()
        
        if len(correlations) > 0:
            return correlations.abs().mean()
        else:
            return 0.0
    
    def check_risk_limits(self, 
                        trade_risk: TradeRisk,
                        portfolio_risk: Optional[PortfolioRisk] = None) -> List[RiskAlert]:
        """
        Check if trade or portfolio violates risk limits.
        
        Args:
            trade_risk: Trade risk assessment
            portfolio_risk: Optional portfolio risk assessment
            
        Returns:
            List of risk alerts
        """
        alerts = []
        
        # Check trade-level limits
        if trade_risk.risk_pct > self.risk_limits.max_single_loss_pct:
            alert = RiskAlert(
                id=f"alert_{uuid.uuid4().hex[:8]}",
                alert_type="single_trade_risk",
                severity=RiskLevel.HIGH,
                message=f"Trade {trade_risk.trade_id} exceeds single trade risk limit: {trade_risk.risk_pct:.2f}% > {self.risk_limits.max_single_loss_pct}%",
                affected_positions=[trade_risk.trade_id],
                recommended_actions=["Reduce position size", "Tighten stop loss", "Cancel trade"]
            )
            alerts.append(alert)
        
        if trade_risk.reward_risk_ratio < 1.5:
            alert = RiskAlert(
                id=f"alert_{uuid.uuid4().hex[:8]}",
                alert_type="poor_risk_reward",
                severity=RiskLevel.MODERATE,
                message=f"Trade {trade_risk.trade_id} has poor risk-reward ratio: {trade_risk.reward_risk_ratio:.2f}",
                affected_positions=[trade_risk.trade_id],
                recommended_actions=["Improve take profit target", "Tighten stop loss", "Reconsider trade"]
            )
            alerts.append(alert)
        
        # Check portfolio-level limits
        if portfolio_risk is not None:
            if portfolio_risk.leverage > self.risk_limits.max_leverage:
                alert = RiskAlert(
                    id=f"alert_{uuid.uuid4().hex[:8]}",
                    alert_type="excessive_leverage",
                    severity=RiskLevel.HIGH,
                    message=f"Portfolio leverage exceeds limit: {portfolio_risk.leverage:.2f}x > {self.risk_limits.max_leverage}x",
                    recommended_actions=["Reduce position sizes", "Close some positions", "Increase cash allocation"]
                )
                alerts.append(alert)
            
            if portfolio_risk.largest_position_pct > self.risk_limits.max_position_size_pct:
                alert = RiskAlert(
                    id=f"alert_{uuid.uuid4().hex[:8]}",
                    alert_type="position_concentration",
                    severity=RiskLevel.MODERATE,
                    message=f"Largest position exceeds limit: {portfolio_risk.largest_position_pct:.2f}% > {self.risk_limits.max_position_size_pct}%",
                    recommended_actions=["Reduce largest position", "Diversify holdings", "Rebalance portfolio"]
                )
                alerts.append(alert)
            
            if abs(portfolio_risk.current_drawdown) > self.risk_limits.max_drawdown_pct:
                alert = RiskAlert(
                    id=f"alert_{uuid.uuid4().hex[:8]}",
                    alert_type="excessive_drawdown",
                    severity=RiskLevel.VERY_HIGH,
                    message=f"Portfolio drawdown exceeds limit: {abs(portfolio_risk.current_drawdown):.2f}% > {self.risk_limits.max_drawdown_pct}%",
                    recommended_actions=["Stop trading", "Reduce risk", "Review strategy", "Consider hedging"]
                )
                alerts.append(alert)
            
            if abs(portfolio_risk.var_1d) > self.risk_limits.var_limit_pct:
                alert = RiskAlert(
                    id=f"alert_{uuid.uuid4().hex[:8]}",
                    alert_type="var_breach",
                    severity=RiskLevel.HIGH,
                    message=f"Portfolio VaR exceeds limit: {abs(portfolio_risk.var_1d):.2f}% > {self.risk_limits.var_limit_pct}%",
                    recommended_actions=["Reduce portfolio risk", "Hedge positions", "Increase diversification"]
                )
                alerts.append(alert)
        
        # Add alerts to active list
        self.active_alerts.extend(alerts)
        self.alert_history.extend(alerts)
        
        # Keep alert history manageable
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        return alerts
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary."""
        summary = {
            "timestamp": datetime.now(),
            "portfolio_risk": self.current_portfolio_risk,
            "active_alerts": len(self.active_alerts),
            "risk_limits": self.risk_limits,
            "recent_trades": len(self.trade_history[-10:]),
            "risk_metrics": {}
        }
        
        if self.current_portfolio_risk:
            summary["risk_metrics"] = {
                "risk_level": self.current_portfolio_risk.risk_level.value,
                "leverage": self.current_portfolio_risk.leverage,
                "var_1d": self.current_portfolio_risk.var_1d,
                "current_drawdown": self.current_portfolio_risk.current_drawdown,
                "sharpe_ratio": self.current_portfolio_risk.sharpe_ratio,
                "largest_position_pct": self.current_portfolio_risk.largest_position_pct
            }
        
        return summary
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a risk alert."""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                logger.info(f"Risk alert {alert_id} acknowledged")
                return True
        
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark a risk alert as resolved."""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.resolved = True
                logger.info(f"Risk alert {alert_id} resolved")
                return True
        
        return False
    
    def get_active_alerts(self, severity: Optional[RiskLevel] = None) -> List[RiskAlert]:
        """Get active risk alerts, optionally filtered by severity."""
        if severity is None:
            return [alert for alert in self.active_alerts if not alert.resolved]
        else:
            return [alert for alert in self.active_alerts 
                   if not alert.resolved and alert.severity == severity]
