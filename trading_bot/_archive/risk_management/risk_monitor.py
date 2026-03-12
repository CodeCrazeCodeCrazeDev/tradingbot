"""
Elite Trading Bot - Risk Monitor

This module provides real-time risk monitoring capabilities for the Elite Trading Bot,
including VaR calculation, drawdown monitoring, and stress testing.
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
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class RiskEventType(enum.Enum):
    """Types of risk events."""
    VAR_BREACH = "var_breach"                    # VaR limit exceeded
    DRAWDOWN_ALERT = "drawdown_alert"           # Drawdown threshold exceeded
    CORRELATION_SPIKE = "correlation_spike"      # High correlation detected
    VOLATILITY_SPIKE = "volatility_spike"       # Volatility spike detected
    LIQUIDITY_CRISIS = "liquidity_crisis"       # Liquidity shortage
    CONCENTRATION_RISK = "concentration_risk"    # Position concentration risk
    LEVERAGE_BREACH = "leverage_breach"         # Leverage limit exceeded
    STRESS_TEST_FAIL = "stress_test_fail"       # Stress test failure
    BLACK_SWAN_EVENT = "black_swan_event"       # Extreme market event
    SYSTEM_FAILURE = "system_failure"           # System/connectivity failure


@dataclass
class RiskThreshold:
    """Risk threshold configuration."""
    name: str
    threshold_type: str        # "absolute", "percentage", "percentile"
    warning_level: float       # Warning threshold
    critical_level: float      # Critical threshold
    lookback_period: int = 30  # Days to look back
    enabled: bool = True
    description: str = ""


@dataclass
class RiskEvent:
    """Risk event notification."""
    id: str
    event_type: RiskEventType
    severity: str              # "warning", "critical", "emergency"
    timestamp: datetime
    message: str
    current_value: float
    threshold_value: float
    affected_positions: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class VaRCalculator:
    """
    Value at Risk calculator using multiple methodologies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize VaR calculator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("VaRCalculator initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "confidence_levels": [0.95, 0.99],  # 95% and 99% confidence
            "holding_periods": [1, 5, 10],      # 1, 5, and 10 day holding periods
            "lookback_window": 252,             # 1 year of data
            "min_observations": 30,             # Minimum observations required
            "monte_carlo_simulations": 10000,   # Number of MC simulations
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def calculate_parametric_var(self, 
                                returns: pd.Series,
                                confidence_level: float = 0.95,
                                holding_period: int = 1) -> float:
        """
        Calculate parametric VaR assuming normal distribution.
        
        Args:
            returns: Historical returns series
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            holding_period: Holding period in days
            
        Returns:
            VaR value (negative number representing loss)
        """
        if len(returns) < self.config["min_observations"]:
            return 0.0
        
        # Calculate mean and standard deviation
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Calculate z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)
        
        # Calculate VaR
        var = mean_return + z_score * std_return
        
        # Adjust for holding period (square root of time rule)
        var = var * np.sqrt(holding_period)
        
        return var
    
    def calculate_historical_var(self, 
                                returns: pd.Series,
                                confidence_level: float = 0.95,
                                holding_period: int = 1) -> float:
        """
        Calculate historical VaR using empirical distribution.
        
        Args:
            returns: Historical returns series
            confidence_level: Confidence level
            holding_period: Holding period in days
            
        Returns:
            VaR value
        """
        if len(returns) < self.config["min_observations"]:
            return 0.0
        
        # Sort returns
        sorted_returns = returns.sort_values()
        
        # Find percentile
        percentile = (1 - confidence_level) * 100
        var = np.percentile(sorted_returns, percentile)
        
        # Adjust for holding period
        var = var * np.sqrt(holding_period)
        
        return var
    
    def calculate_monte_carlo_var(self, 
                                 returns: pd.Series,
                                 confidence_level: float = 0.95,
                                 holding_period: int = 1) -> float:
        """
        Calculate Monte Carlo VaR using simulation.
        
        Args:
            returns: Historical returns series
            confidence_level: Confidence level
            holding_period: Holding period in days
            
        Returns:
            VaR value
        """
        if len(returns) < self.config["min_observations"]:
            return 0.0
        
        # Estimate parameters
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Generate random scenarios
        np.random.seed(42)  # For reproducibility
        simulated_returns = np.random.normal(
            mean_return, 
            std_return, 
            self.config["monte_carlo_simulations"]
        )
        
        # Calculate cumulative returns for holding period
        if holding_period > 1:
            cumulative_returns = []
            for _ in range(self.config["monte_carlo_simulations"]):
                period_returns = np.random.normal(mean_return, std_return, holding_period)
                cumulative_return = np.prod(1 + period_returns) - 1
                cumulative_returns.append(cumulative_return)
            simulated_returns = np.array(cumulative_returns)
        
        # Calculate VaR
        percentile = (1 - confidence_level) * 100
        var = np.percentile(simulated_returns, percentile)
        
        return var
    
    def calculate_expected_shortfall(self, 
                                   returns: pd.Series,
                                   confidence_level: float = 0.95,
                                   holding_period: int = 1) -> float:
        """
        Calculate Expected Shortfall (Conditional VaR).
        
        Args:
            returns: Historical returns series
            confidence_level: Confidence level
            holding_period: Holding period in days
            
        Returns:
            Expected Shortfall value
        """
        if len(returns) < self.config["min_observations"]:
            return 0.0
        
        # Calculate historical VaR first
        var = self.calculate_historical_var(returns, confidence_level, holding_period)
        
        # Find returns worse than VaR
        tail_returns = returns[returns <= var]
        
        if len(tail_returns) > 0:
            expected_shortfall = tail_returns.mean()
        else:
            expected_shortfall = var
        
        return expected_shortfall


class DrawdownMonitor:
    """
    Monitors portfolio drawdown and triggers alerts.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize drawdown monitor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Tracking variables
        self.peak_value = 0.0
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        self.drawdown_start_date: Optional[datetime] = None
        self.drawdown_duration = timedelta(0)
        
        logger.info("DrawdownMonitor initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "warning_threshold": 5.0,    # 5% drawdown warning
            "critical_threshold": 10.0,  # 10% drawdown critical
            "emergency_threshold": 20.0, # 20% drawdown emergency
            "duration_warning_days": 30, # 30 days in drawdown warning
            "recovery_threshold": 0.5,   # 0.5% recovery to reset alerts
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def update(self, current_value: float, timestamp: datetime) -> List[RiskEvent]:
        """
        Update drawdown monitor with current portfolio value.
        
        Args:
            current_value: Current portfolio value
            timestamp: Current timestamp
            
        Returns:
            List of risk events triggered
        """
        events = []
        
        # Update peak value
        if current_value > self.peak_value:
            self.peak_value = current_value
            
            # Check if we're recovering from drawdown
            if self.current_drawdown > self.config["recovery_threshold"]:
                # Still in significant drawdown
                pass
            else:
                # Reset drawdown tracking
                self.drawdown_start_date = None
                self.drawdown_duration = timedelta(0)
        
        # Calculate current drawdown
        if self.peak_value > 0:
            self.current_drawdown = ((self.peak_value - current_value) / self.peak_value) * 100
        else:
            self.current_drawdown = 0.0
        
        # Update max drawdown
        self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
        
        # Track drawdown duration
        if self.current_drawdown > 0 and self.drawdown_start_date is None:
            self.drawdown_start_date = timestamp
        
        if self.drawdown_start_date is not None:
            self.drawdown_duration = timestamp - self.drawdown_start_date
        
        # Check thresholds and generate events
        if self.current_drawdown >= self.config["emergency_threshold"]:
            events.append(self._create_drawdown_event(
                "emergency", 
                self.current_drawdown,
                timestamp
            ))
        elif self.current_drawdown >= self.config["critical_threshold"]:
            events.append(self._create_drawdown_event(
                "critical", 
                self.current_drawdown,
                timestamp
            ))
        elif self.current_drawdown >= self.config["warning_threshold"]:
            events.append(self._create_drawdown_event(
                "warning", 
                self.current_drawdown,
                timestamp
            ))
        
        # Check duration threshold
        if (self.drawdown_duration.days >= self.config["duration_warning_days"] and 
            self.current_drawdown > 1.0):
            
            events.append(RiskEvent(
                id=f"dd_duration_{uuid.uuid4().hex[:8]}",
                event_type=RiskEventType.DRAWDOWN_ALERT,
                severity="warning",
                timestamp=timestamp,
                message=f"Prolonged drawdown: {self.drawdown_duration.days} days in {self.current_drawdown:.2f}% drawdown",
                current_value=self.drawdown_duration.days,
                threshold_value=self.config["duration_warning_days"],
                recommended_actions=[
                    "Review trading strategy",
                    "Consider reducing position sizes",
                    "Analyze market conditions"
                ]
            ))
        
        return events
    
    def _create_drawdown_event(self, severity: str, drawdown_pct: float, timestamp: datetime) -> RiskEvent:
        """Create a drawdown risk event."""
        threshold_map = {
            "warning": self.config["warning_threshold"],
            "critical": self.config["critical_threshold"],
            "emergency": self.config["emergency_threshold"]
        }
        
        actions_map = {
            "warning": [
                "Monitor closely",
                "Review open positions",
                "Consider reducing risk"
            ],
            "critical": [
                "Reduce position sizes",
                "Close losing positions",
                "Implement hedging"
            ],
            "emergency": [
                "Stop trading immediately",
                "Close all positions",
                "Preserve capital",
                "Review risk management"
            ]
        }
        
        return RiskEvent(
            id=f"dd_{severity}_{uuid.uuid4().hex[:8]}",
            event_type=RiskEventType.DRAWDOWN_ALERT,
            severity=severity,
            timestamp=timestamp,
            message=f"{severity.title()} drawdown: {drawdown_pct:.2f}% from peak",
            current_value=drawdown_pct,
            threshold_value=threshold_map[severity],
            recommended_actions=actions_map[severity],
            metadata={
                "peak_value": self.peak_value,
                "drawdown_duration_days": self.drawdown_duration.days,
                "max_drawdown": self.max_drawdown
            }
        )


class StressTest:
    """
    Performs stress testing on portfolio positions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize stress test.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("StressTest initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "scenarios": {
                "market_crash": {"equity_shock": -0.20, "volatility_multiplier": 2.0},
                "currency_crisis": {"fx_shock": -0.15, "correlation_increase": 0.3},
                "liquidity_crisis": {"bid_ask_widening": 3.0, "volume_reduction": 0.5},
                "interest_rate_shock": {"rate_change": 0.02, "duration_impact": True},
                "black_swan": {"extreme_shock": -0.35, "correlation_breakdown": True}
            },
            "confidence_level": 0.99,
            "monte_carlo_runs": 1000,
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def run_scenario_test(self, 
                         positions: Dict[str, Any],
                         scenario_name: str,
                         market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Run a specific stress test scenario.
        
        Args:
            positions: Portfolio positions
            scenario_name: Name of scenario to test
            market_data: Historical market data
            
        Returns:
            Stress test results
        """
        if scenario_name not in self.config["scenarios"]:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.config["scenarios"][scenario_name]
        results = {
            "scenario": scenario_name,
            "timestamp": datetime.now(),
            "total_loss": 0.0,
            "position_impacts": {},
            "risk_metrics": {},
            "passed": True
        }
        
        total_portfolio_value = sum(pos.get("market_value", 0) for pos in positions.values())
        
        for pos_id, position in positions.items():
            symbol = position.get("symbol", "")
            market_value = position.get("market_value", 0)
            direction = position.get("direction", "long")
            
            # Apply scenario shocks
            position_loss = 0.0
            
            if "equity_shock" in scenario:
                shock = scenario["equity_shock"]
                if direction == "long":
                    position_loss += market_value * shock
                else:
                    position_loss -= market_value * shock  # Short benefits from decline
            
            if "fx_shock" in scenario and "USD" in symbol:
                shock = scenario["fx_shock"]
                position_loss += market_value * shock
            
            if "extreme_shock" in scenario:
                shock = scenario["extreme_shock"]
                position_loss += market_value * shock
            
            results["position_impacts"][pos_id] = {
                "symbol": symbol,
                "market_value": market_value,
                "estimated_loss": position_loss,
                "loss_percentage": (position_loss / market_value) * 100 if market_value > 0 else 0
            }
            
            results["total_loss"] += position_loss
        
        # Calculate risk metrics
        results["risk_metrics"] = {
            "total_loss_pct": (results["total_loss"] / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0,
            "worst_position_loss": min(impact["estimated_loss"] for impact in results["position_impacts"].values()) if results["position_impacts"] else 0,
            "positions_at_risk": len([impact for impact in results["position_impacts"].values() if impact["estimated_loss"] < -1000])
        }
        
        # Determine if stress test passed (loss < 15% of portfolio)
        loss_threshold = 0.15  # 15% loss threshold
        results["passed"] = abs(results["risk_metrics"]["total_loss_pct"]) < (loss_threshold * 100)
        
        return results
    
    def run_all_scenarios(self, 
                         positions: Dict[str, Any],
                         market_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
        """
        Run all stress test scenarios.
        
        Args:
            positions: Portfolio positions
            market_data: Historical market data
            
        Returns:
            Dictionary of scenario -> results
        """
        all_results = {}
        
        for scenario_name in self.config["scenarios"]:
            try:
                results = self.run_scenario_test(positions, scenario_name, market_data)
                all_results[scenario_name] = results
            except Exception as e:
                logger.error(f"Error running scenario {scenario_name}: {e}")
                all_results[scenario_name] = {
                    "scenario": scenario_name,
                    "error": str(e),
                    "passed": False
                }
        
        return all_results


class RiskMonitor:
    """
    Main risk monitoring system that coordinates all risk monitoring components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize risk monitor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Initialize components
        self.var_calculator = VaRCalculator(self.config.get("var_config"))
        self.drawdown_monitor = DrawdownMonitor(self.config.get("drawdown_config"))
        self.stress_test = StressTest(self.config.get("stress_test_config"))
        
        # Risk thresholds
        self.thresholds = self._create_default_thresholds()
        
        # Event tracking
        self.active_events: List[RiskEvent] = []
        self.event_history: List[RiskEvent] = []
        self.event_handlers: List[Callable[[RiskEvent], None]] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.last_update: Optional[datetime] = None
        
        logger.info("RiskMonitor initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "update_interval_seconds": 60,    # Update every minute
            "max_active_events": 100,        # Maximum active events
            "max_event_history": 1000,       # Maximum event history
            "enable_real_time_monitoring": True,
            "enable_stress_testing": True,
            "stress_test_interval_hours": 6, # Run stress tests every 6 hours
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _create_default_thresholds(self) -> Dict[str, RiskThreshold]:
        """Create default risk thresholds."""
        return {
            "var_95": RiskThreshold(
                name="VaR 95%",
                threshold_type="percentage",
                warning_level=3.0,
                critical_level=5.0,
                description="1-day VaR at 95% confidence"
            ),
            "var_99": RiskThreshold(
                name="VaR 99%",
                threshold_type="percentage",
                warning_level=5.0,
                critical_level=8.0,
                description="1-day VaR at 99% confidence"
            ),
            "drawdown": RiskThreshold(
                name="Portfolio Drawdown",
                threshold_type="percentage",
                warning_level=5.0,
                critical_level=10.0,
                description="Portfolio drawdown from peak"
            ),
            "leverage": RiskThreshold(
                name="Portfolio Leverage",
                threshold_type="absolute",
                warning_level=2.0,
                critical_level=3.0,
                description="Portfolio leverage ratio"
            ),
            "concentration": RiskThreshold(
                name="Position Concentration",
                threshold_type="percentage",
                warning_level=15.0,
                critical_level=25.0,
                description="Largest single position weight"
            ),
            "correlation": RiskThreshold(
                name="Average Correlation",
                threshold_type="absolute",
                warning_level=0.7,
                critical_level=0.85,
                description="Average correlation between positions"
            )
        }
    
    def start_monitoring(self):
        """Start real-time risk monitoring."""
        self.monitoring_active = True
        logger.info("Risk monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time risk monitoring."""
        self.monitoring_active = False
        logger.info("Risk monitoring stopped")
    
    def update_risk_assessment(self, 
                             portfolio_value: float,
                             positions: Dict[str, Any],
                             market_data: Dict[str, pd.DataFrame]) -> List[RiskEvent]:
        """
        Update comprehensive risk assessment.
        
        Args:
            portfolio_value: Current portfolio value
            positions: Portfolio positions
            market_data: Market data for analysis
            
        Returns:
            List of new risk events
        """
        new_events = []
        current_time = datetime.now()
        
        try:
            # Update drawdown monitoring
            drawdown_events = self.drawdown_monitor.update(portfolio_value, current_time)
            new_events.extend(drawdown_events)
            
            # Calculate portfolio returns for VaR
            if market_data:
                portfolio_returns = self._calculate_portfolio_returns(positions, market_data)
                
                # Check VaR thresholds
                var_events = self._check_var_thresholds(portfolio_returns, portfolio_value)
                new_events.extend(var_events)
                
                # Check correlation risk
                correlation_events = self._check_correlation_risk(positions, market_data)
                new_events.extend(correlation_events)
                
                # Check concentration risk
                concentration_events = self._check_concentration_risk(positions, portfolio_value)
                new_events.extend(concentration_events)
            
            # Run stress tests periodically
            if self._should_run_stress_test():
                stress_events = self._run_periodic_stress_test(positions, market_data)
                new_events.extend(stress_events)
            
            # Add new events to active list
            self.active_events.extend(new_events)
            self.event_history.extend(new_events)
            
            # Manage event lists size
            self._manage_event_lists()
            
            # Trigger event handlers
            for event in new_events:
                self._trigger_event_handlers(event)
            
            self.last_update = current_time
            
        except Exception as e:
            logger.error(f"Error in risk assessment update: {e}")
            
            # Create system failure event
            system_event = RiskEvent(
                id=f"sys_error_{uuid.uuid4().hex[:8]}",
                event_type=RiskEventType.SYSTEM_FAILURE,
                severity="critical",
                timestamp=current_time,
                message=f"Risk monitoring system error: {str(e)}",
                current_value=0,
                threshold_value=0,
                recommended_actions=["Check system logs", "Restart risk monitoring"]
            )
            new_events.append(system_event)
        
        return new_events
    
    def _calculate_portfolio_returns(self, 
                                   positions: Dict[str, Any],
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
        
        for position in positions.values():
            symbol = position.get("symbol")
            weight = position.get("weight", 0) / 100  # Convert percentage to decimal
            
            if symbol in market_data and weight > 0:
                returns = market_data[symbol]['close'].pct_change().fillna(0)
                portfolio_returns += returns * weight
                total_weight += weight
        
        return portfolio_returns.dropna()
    
    def _check_var_thresholds(self, 
                            portfolio_returns: pd.Series,
                            portfolio_value: float) -> List[RiskEvent]:
        """Check VaR threshold breaches."""
        events = []
        
        if len(portfolio_returns) < 30:
            return events
        
        current_time = datetime.now()
        
        # Calculate VaR at different confidence levels
        var_95 = abs(self.var_calculator.calculate_historical_var(portfolio_returns, 0.95)) * 100
        var_99 = abs(self.var_calculator.calculate_historical_var(portfolio_returns, 0.99)) * 100
        
        # Check 95% VaR threshold
        threshold_95 = self.thresholds["var_95"]
        if var_95 >= threshold_95.critical_level:
            events.append(RiskEvent(
                id=f"var95_critical_{uuid.uuid4().hex[:8]}",
                event_type=RiskEventType.VAR_BREACH,
                severity="critical",
                timestamp=current_time,
                message=f"95% VaR breach: {var_95:.2f}% > {threshold_95.critical_level}%",
                current_value=var_95,
                threshold_value=threshold_95.critical_level,
                recommended_actions=["Reduce portfolio risk", "Hedge positions", "Review position sizes"]
            ))
        elif var_95 >= threshold_95.warning_level:
            events.append(RiskEvent(
                id=f"var95_warning_{uuid.uuid4().hex[:8]}",
                event_type=RiskEventType.VAR_BREACH,
                severity="warning",
                timestamp=current_time,
                message=f"95% VaR warning: {var_95:.2f}% > {threshold_95.warning_level}%",
                current_value=var_95,
                threshold_value=threshold_95.warning_level,
                recommended_actions=["Monitor closely", "Consider risk reduction"]
            ))
        
        # Check 99% VaR threshold
        threshold_99 = self.thresholds["var_99"]
        if var_99 >= threshold_99.critical_level:
            events.append(RiskEvent(
                id=f"var99_critical_{uuid.uuid4().hex[:8]}",
                event_type=RiskEventType.VAR_BREACH,
                severity="critical",
                timestamp=current_time,
                message=f"99% VaR breach: {var_99:.2f}% > {threshold_99.critical_level}%",
                current_value=var_99,
                threshold_value=threshold_99.critical_level,
                recommended_actions=["Immediate risk reduction", "Close high-risk positions"]
            ))
        
        return events
    
    def _check_correlation_risk(self, 
                              positions: Dict[str, Any],
                              market_data: Dict[str, pd.DataFrame]) -> List[RiskEvent]:
        """Check for high correlation risk."""
        events = []
        
        if len(positions) < 2:
            return events
        
        # Calculate correlation matrix
        symbols = [pos.get("symbol") for pos in positions.values() if pos.get("symbol")]
        
        if len(symbols) < 2:
            return events
        
        returns_data = {}
        for symbol in symbols:
            if symbol in market_data:
                returns = market_data[symbol]['close'].pct_change().dropna()
                if len(returns) > 20:
                    returns_data[symbol] = returns
        
        if len(returns_data) < 2:
            return events
        
        # Create correlation matrix
        returns_df = pd.DataFrame(returns_data).dropna()
        if len(returns_df) < 10:
            return events
        
        corr_matrix = returns_df.corr()
        
        # Calculate average correlation (excluding diagonal)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        correlations = corr_matrix.where(mask).stack().dropna()
        
        if len(correlations) > 0:
            avg_correlation = correlations.abs().mean()
            
            threshold = self.thresholds["correlation"]
            current_time = datetime.now()
            
            if avg_correlation >= threshold.critical_level:
                events.append(RiskEvent(
                    id=f"corr_critical_{uuid.uuid4().hex[:8]}",
                    event_type=RiskEventType.CORRELATION_SPIKE,
                    severity="critical",
                    timestamp=current_time,
                    message=f"High correlation risk: {avg_correlation:.3f} > {threshold.critical_level}",
                    current_value=avg_correlation,
                    threshold_value=threshold.critical_level,
                    recommended_actions=["Diversify positions", "Reduce correlated holdings", "Add uncorrelated assets"]
                ))
            elif avg_correlation >= threshold.warning_level:
                events.append(RiskEvent(
                    id=f"corr_warning_{uuid.uuid4().hex[:8]}",
                    event_type=RiskEventType.CORRELATION_SPIKE,
                    severity="warning",
                    timestamp=current_time,
                    message=f"Elevated correlation: {avg_correlation:.3f} > {threshold.warning_level}",
                    current_value=avg_correlation,
                    threshold_value=threshold.warning_level,
                    recommended_actions=["Monitor correlation levels", "Consider diversification"]
                ))
        
        return events
    
    def _check_concentration_risk(self, 
                                positions: Dict[str, Any],
                                portfolio_value: float) -> List[RiskEvent]:
        """Check for position concentration risk."""
        events = []
        
        if not positions or portfolio_value <= 0:
            return events
        
        # Find largest position
        largest_position_value = 0
        largest_position_symbol = ""
        
        for position in positions.values():
            market_value = position.get("market_value", 0)
            if market_value > largest_position_value:
                largest_position_value = market_value
                largest_position_symbol = position.get("symbol", "")
        
        # Calculate concentration percentage
        concentration_pct = (largest_position_value / portfolio_value) * 100
        
        threshold = self.thresholds["concentration"]
        current_time = datetime.now()
        
        if concentration_pct >= threshold.critical_level:
            events.append(RiskEvent(
                id=f"conc_critical_{uuid.uuid4().hex[:8]}",
                event_type=RiskEventType.CONCENTRATION_RISK,
                severity="critical",
                timestamp=current_time,
                message=f"Critical concentration risk: {largest_position_symbol} {concentration_pct:.1f}% > {threshold.critical_level}%",
                current_value=concentration_pct,
                threshold_value=threshold.critical_level,
                affected_positions=[largest_position_symbol],
                recommended_actions=["Reduce largest position", "Diversify portfolio", "Implement position limits"]
            ))
        elif concentration_pct >= threshold.warning_level:
            events.append(RiskEvent(
                id=f"conc_warning_{uuid.uuid4().hex[:8]}",
                event_type=RiskEventType.CONCENTRATION_RISK,
                severity="warning",
                timestamp=current_time,
                message=f"High concentration: {largest_position_symbol} {concentration_pct:.1f}% > {threshold.warning_level}%",
                current_value=concentration_pct,
                threshold_value=threshold.warning_level,
                affected_positions=[largest_position_symbol],
                recommended_actions=["Monitor position size", "Consider partial reduction"]
            ))
        
        return events
    
    def _should_run_stress_test(self) -> bool:
        """Check if it's time to run periodic stress test."""
        if not self.config["enable_stress_testing"]:
            return False
        
        if self.last_update is None:
            return True
        
        hours_since_last = (datetime.now() - self.last_update).total_seconds() / 3600
        return hours_since_last >= self.config["stress_test_interval_hours"]
    
    def _run_periodic_stress_test(self, 
                                positions: Dict[str, Any],
                                market_data: Dict[str, pd.DataFrame]) -> List[RiskEvent]:
        """Run periodic stress test."""
        events = []
        
        try:
            # Run all stress test scenarios
            stress_results = self.stress_test.run_all_scenarios(positions, market_data)
            
            current_time = datetime.now()
            
            # Check for failed scenarios
            for scenario_name, results in stress_results.items():
                if not results.get("passed", True):
                    loss_pct = results.get("risk_metrics", {}).get("total_loss_pct", 0)
                    
                    events.append(RiskEvent(
                        id=f"stress_fail_{uuid.uuid4().hex[:8]}",
                        event_type=RiskEventType.STRESS_TEST_FAIL,
                        severity="critical" if abs(loss_pct) > 20 else "warning",
                        timestamp=current_time,
                        message=f"Stress test failure: {scenario_name} scenario shows {loss_pct:.1f}% loss",
                        current_value=abs(loss_pct),
                        threshold_value=15.0,
                        recommended_actions=[
                            "Review portfolio composition",
                            "Implement hedging strategies",
                            "Reduce risk exposure",
                            "Diversify holdings"
                        ],
                        metadata={"scenario": scenario_name, "full_results": results}
                    ))
        
        except Exception as e:
            logger.error(f"Error running stress test: {e}")
        
        return events
    
    def _manage_event_lists(self):
        """Manage size of event lists."""
        # Remove resolved events from active list
        self.active_events = [event for event in self.active_events if not event.resolved]
        
        # Limit active events
        if len(self.active_events) > self.config["max_active_events"]:
            self.active_events = self.active_events[-self.config["max_active_events"]:]
        
        # Limit event history
        if len(self.event_history) > self.config["max_event_history"]:
            self.event_history = self.event_history[-self.config["max_event_history"]:]
    
    def _trigger_event_handlers(self, event: RiskEvent):
        """Trigger registered event handlers."""
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    def register_event_handler(self, handler: Callable[[RiskEvent], None]):
        """Register an event handler."""
        self.event_handlers.append(handler)
    
    def acknowledge_event(self, event_id: str) -> bool:
        """Acknowledge a risk event."""
        for event in self.active_events:
            if event.id == event_id:
                event.acknowledged = True
                return True
        return False
    
    def resolve_event(self, event_id: str) -> bool:
        """Resolve a risk event."""
        for event in self.active_events:
            if event.id == event_id:
                event.resolved = True
                return True
        return False
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk monitoring summary."""
        return {
            "monitoring_active": self.monitoring_active,
            "last_update": self.last_update,
            "active_events": len(self.active_events),
            "unacknowledged_events": len([e for e in self.active_events if not e.acknowledged]),
            "critical_events": len([e for e in self.active_events if e.severity == "critical"]),
            "current_drawdown": self.drawdown_monitor.current_drawdown,
            "max_drawdown": self.drawdown_monitor.max_drawdown,
            "drawdown_duration_days": self.drawdown_monitor.drawdown_duration.days,
            "recent_events": self.active_events[-5:] if self.active_events else []
        }
