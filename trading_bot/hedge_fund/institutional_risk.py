"""
Institutional Risk Management
=============================
Comprehensive risk management for hedge funds:
- Value at Risk (VaR) - Parametric, Historical, Monte Carlo
- Stress Testing & Scenario Analysis
- Liquidity Risk Management
- Counterparty Risk
- Margin Management
- Greeks & Sensitivity Analysis
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    from scipy import stats
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class VaRMethod(Enum):
    """VaR calculation methods"""
    PARAMETRIC = "parametric"
    HISTORICAL = "historical"
    MONTE_CARLO = "monte_carlo"
    CORNISH_FISHER = "cornish_fisher"


class StressScenario(Enum):
    """Predefined stress scenarios"""
    MARKET_CRASH_2008 = "market_crash_2008"
    FLASH_CRASH_2010 = "flash_crash_2010"
    COVID_CRASH_2020 = "covid_crash_2020"
    RATE_SHOCK_UP = "rate_shock_up"
    RATE_SHOCK_DOWN = "rate_shock_down"
    CURRENCY_CRISIS = "currency_crisis"
    CREDIT_CRISIS = "credit_crisis"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_BREAKDOWN = "correlation_breakdown"


class RiskLevel(Enum):
    """Risk levels"""
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class VaRResult:
    """VaR calculation result"""
    method: VaRMethod
    confidence_level: float
    time_horizon_days: int
    var_amount: float
    var_percentage: float
    expected_shortfall: float  # CVaR
    portfolio_value: float
    calculation_date: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'method': self.method.value,
            'confidence_level': f"{self.confidence_level * 100:.0f}%",
            'time_horizon': f"{self.time_horizon_days} days",
            'var_amount': round(self.var_amount, 2),
            'var_percentage': f"{self.var_percentage * 100:.2f}%",
            'expected_shortfall': round(self.expected_shortfall, 2),
            'es_percentage': f"{self.expected_shortfall / self.portfolio_value * 100:.2f}%",
            'portfolio_value': round(self.portfolio_value, 2)
        }


@dataclass
class StressTestResult:
    """Stress test result"""
    scenario: StressScenario
    portfolio_impact: float
    impact_percentage: float
    positions_affected: Dict[str, float]
    risk_level: RiskLevel
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scenario': self.scenario.value,
            'portfolio_impact': round(self.portfolio_impact, 2),
            'impact_percentage': f"{self.impact_percentage * 100:.2f}%",
            'risk_level': self.risk_level.value,
            'recommendations': self.recommendations
        }


@dataclass
class ScenarioAnalysis:
    """Custom scenario analysis"""
    scenario_name: str
    market_shocks: Dict[str, float]  # Asset -> shock %
    factor_shocks: Dict[str, float]  # Factor -> shock %
    correlation_changes: Dict[str, float]
    volatility_multiplier: float
    portfolio_impact: float
    probability: float


@dataclass
class LiquidityRisk:
    """Liquidity risk metrics"""
    symbol: str
    avg_daily_volume: float
    position_size: float
    days_to_liquidate: float
    liquidation_cost: float
    liquidity_score: float  # 0-100
    
    @property
    def is_illiquid(self) -> bool:
        return self.days_to_liquidate > 5 or self.liquidity_score < 30


@dataclass
class CounterpartyRisk:
    """Counterparty risk exposure"""
    counterparty_id: str
    counterparty_name: str
    exposure_type: str  # derivatives, lending, prime broker
    gross_exposure: float
    net_exposure: float
    collateral_held: float
    credit_rating: str
    probability_of_default: float
    loss_given_default: float
    expected_loss: float
    
    @property
    def uncollateralized_exposure(self) -> float:
        return max(0, self.net_exposure - self.collateral_held)


class VaREngine:
    """
    Value at Risk Engine
    Multiple VaR calculation methodologies
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.confidence_levels = config.get('confidence_levels', [0.95, 0.99])
        self.time_horizons = config.get('time_horizons', [1, 10])  # days
        self.num_simulations = config.get('num_simulations', 10000)
        
        # History
        self.var_history: List[VaRResult] = []
        
        logger.info("VaR Engine initialized")
    
    def calculate_parametric_var(
        self,
        portfolio_value: float,
        portfolio_volatility: float,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> VaRResult:
        """Calculate parametric (variance-covariance) VaR"""
        if not NUMPY_AVAILABLE:
            return VaRResult(
                method=VaRMethod.PARAMETRIC,
                confidence_level=confidence_level,
                time_horizon_days=time_horizon,
                var_amount=portfolio_value * 0.02,
                var_percentage=0.02,
                expected_shortfall=portfolio_value * 0.025,
                portfolio_value=portfolio_value,
                calculation_date=datetime.now()
            )
        
        # Z-score for confidence level
        z_score = stats.norm.ppf(confidence_level)
        
        # Scale volatility for time horizon
        scaled_vol = portfolio_volatility * np.sqrt(time_horizon)
        
        # VaR
        var_pct = z_score * scaled_vol
        var_amount = portfolio_value * var_pct
        
        # Expected Shortfall (CVaR)
        es_multiplier = stats.norm.pdf(z_score) / (1 - confidence_level)
        es_pct = scaled_vol * es_multiplier
        es_amount = portfolio_value * es_pct
        
        result = VaRResult(
            method=VaRMethod.PARAMETRIC,
            confidence_level=confidence_level,
            time_horizon_days=time_horizon,
            var_amount=var_amount,
            var_percentage=var_pct,
            expected_shortfall=es_amount,
            portfolio_value=portfolio_value,
            calculation_date=datetime.now()
        )
        
        self.var_history.append(result)
        return result
    
    def calculate_historical_var(
        self,
        portfolio_value: float,
        historical_returns: np.ndarray,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> VaRResult:
        """Calculate historical simulation VaR"""
        if not NUMPY_AVAILABLE or len(historical_returns) == 0:
            return self.calculate_parametric_var(
                portfolio_value, 0.15, confidence_level, time_horizon
            )
        
        # Scale returns for time horizon
        if time_horizon > 1:
            # Use overlapping returns
            scaled_returns = np.array([
                np.sum(historical_returns[i:i+time_horizon])
                for i in range(len(historical_returns) - time_horizon + 1)
            ])
        else:
            scaled_returns = historical_returns
        
        # VaR as percentile
        var_pct = np.percentile(scaled_returns, (1 - confidence_level) * 100)
        var_amount = portfolio_value * abs(var_pct)
        
        # Expected Shortfall
        tail_returns = scaled_returns[scaled_returns <= var_pct]
        es_pct = np.mean(tail_returns) if len(tail_returns) > 0 else var_pct
        es_amount = portfolio_value * abs(es_pct)
        
        result = VaRResult(
            method=VaRMethod.HISTORICAL,
            confidence_level=confidence_level,
            time_horizon_days=time_horizon,
            var_amount=var_amount,
            var_percentage=abs(var_pct),
            expected_shortfall=es_amount,
            portfolio_value=portfolio_value,
            calculation_date=datetime.now()
        )
        
        self.var_history.append(result)
        return result
    
    def calculate_monte_carlo_var(
        self,
        portfolio_value: float,
        expected_return: float,
        volatility: float,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> VaRResult:
        """Calculate Monte Carlo VaR"""
        if not NUMPY_AVAILABLE:
            return self.calculate_parametric_var(
                portfolio_value, volatility, confidence_level, time_horizon
            )
        
        # Simulate returns
        dt = time_horizon / 252  # Annualized
        drift = (expected_return - 0.5 * volatility ** 2) * dt
        diffusion = volatility * np.sqrt(dt)
        
        random_returns = np.random.normal(0, 1, self.num_simulations)
        simulated_returns = drift + diffusion * random_returns
        
        # Portfolio values
        simulated_values = portfolio_value * np.exp(simulated_returns)
        simulated_pnl = simulated_values - portfolio_value
        
        # VaR
        var_amount = np.percentile(simulated_pnl, (1 - confidence_level) * 100)
        var_pct = abs(var_amount) / portfolio_value
        
        # Expected Shortfall
        tail_pnl = simulated_pnl[simulated_pnl <= var_amount]
        es_amount = abs(np.mean(tail_pnl)) if len(tail_pnl) > 0 else abs(var_amount)
        
        result = VaRResult(
            method=VaRMethod.MONTE_CARLO,
            confidence_level=confidence_level,
            time_horizon_days=time_horizon,
            var_amount=abs(var_amount),
            var_percentage=var_pct,
            expected_shortfall=es_amount,
            portfolio_value=portfolio_value,
            calculation_date=datetime.now()
        )
        
        self.var_history.append(result)
        return result
    
    def calculate_component_var(
        self,
        weights: Dict[str, float],
        covariance: np.ndarray,
        portfolio_value: float,
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """Calculate component VaR for each position"""
        if not NUMPY_AVAILABLE:
            return {s: portfolio_value * 0.01 for s in weights}
        
        symbols = list(weights.keys())
        w = np.array([weights[s] for s in symbols])
        
        # Portfolio variance
        port_var = w @ covariance @ w
        port_vol = np.sqrt(port_var)
        
        # Marginal VaR
        marginal_var = covariance @ w / port_vol
        
        # Component VaR
        z_score = stats.norm.ppf(confidence_level)
        component_var = {}
        
        for i, symbol in enumerate(symbols):
            comp_var = w[i] * marginal_var[i] * z_score * portfolio_value
            component_var[symbol] = comp_var
        
        return component_var


class StressTestEngine:
    """
    Stress Testing Engine
    Predefined and custom stress scenarios
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Predefined scenario shocks
        self.scenario_shocks = {
            StressScenario.MARKET_CRASH_2008: {
                'equity': -0.50,
                'credit': -0.30,
                'volatility': 3.0,
                'correlation': 0.9
            },
            StressScenario.FLASH_CRASH_2010: {
                'equity': -0.10,
                'volatility': 2.5,
                'liquidity': -0.50
            },
            StressScenario.COVID_CRASH_2020: {
                'equity': -0.35,
                'oil': -0.70,
                'volatility': 4.0,
                'credit': -0.20
            },
            StressScenario.RATE_SHOCK_UP: {
                'rates': 0.02,  # 200bp
                'bonds': -0.15,
                'equity': -0.10
            },
            StressScenario.RATE_SHOCK_DOWN: {
                'rates': -0.01,  # -100bp
                'bonds': 0.10,
                'banks': -0.20
            },
            StressScenario.CURRENCY_CRISIS: {
                'fx': -0.20,
                'em_equity': -0.30,
                'volatility': 2.0
            },
            StressScenario.CREDIT_CRISIS: {
                'credit_spreads': 0.05,  # 500bp widening
                'high_yield': -0.25,
                'banks': -0.30
            },
            StressScenario.LIQUIDITY_CRISIS: {
                'liquidity': -0.70,
                'small_cap': -0.25,
                'spreads': 0.03
            },
            StressScenario.VOLATILITY_SPIKE: {
                'volatility': 3.0,
                'equity': -0.15,
                'correlation': 0.8
            },
            StressScenario.CORRELATION_BREAKDOWN: {
                'correlation': -0.5,  # Correlations flip
                'diversification': -0.30
            }
        }
        
        # History
        self.stress_test_history: List[StressTestResult] = []
        
        logger.info("Stress Test Engine initialized")
    
    def run_stress_test(
        self,
        scenario: StressScenario,
        positions: Dict[str, Dict[str, Any]],
        portfolio_value: float
    ) -> StressTestResult:
        """Run a predefined stress scenario"""
        shocks = self.scenario_shocks.get(scenario, {})
        
        # Calculate impact on each position
        position_impacts = {}
        total_impact = 0
        
        for symbol, pos in positions.items():
            quantity = pos.get('quantity', 0)
            price = pos.get('current_price', 0)
            asset_class = pos.get('asset_class', 'equity')
            sector = pos.get('sector', 'general')
            
            # Determine applicable shock
            shock = shocks.get(asset_class, shocks.get('equity', -0.10))
            
            # Apply sector-specific adjustments
            if sector in shocks:
                shock = shocks[sector]
            
            # Calculate impact
            position_value = quantity * price
            impact = position_value * shock
            
            position_impacts[symbol] = impact
            total_impact += impact
        
        # Determine risk level
        impact_pct = abs(total_impact) / portfolio_value if portfolio_value > 0 else 0
        
        if impact_pct < 0.05:
            risk_level = RiskLevel.LOW
        elif impact_pct < 0.10:
            risk_level = RiskLevel.MODERATE
        elif impact_pct < 0.20:
            risk_level = RiskLevel.ELEVATED
        elif impact_pct < 0.30:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            scenario, impact_pct, position_impacts
        )
        
        result = StressTestResult(
            scenario=scenario,
            portfolio_impact=total_impact,
            impact_percentage=impact_pct,
            positions_affected=position_impacts,
            risk_level=risk_level,
            recommendations=recommendations
        )
        
        self.stress_test_history.append(result)
        return result
    
    def run_all_scenarios(
        self,
        positions: Dict[str, Dict[str, Any]],
        portfolio_value: float
    ) -> Dict[StressScenario, StressTestResult]:
        """Run all predefined stress scenarios"""
        results = {}
        
        for scenario in StressScenario:
            results[scenario] = self.run_stress_test(
                scenario, positions, portfolio_value
            )
        
        return results
    
    def run_custom_scenario(
        self,
        scenario_name: str,
        shocks: Dict[str, float],
        positions: Dict[str, Dict[str, Any]],
        portfolio_value: float
    ) -> ScenarioAnalysis:
        """Run a custom stress scenario"""
        position_impacts = {}
        total_impact = 0
        
        for symbol, pos in positions.items():
            quantity = pos.get('quantity', 0)
            price = pos.get('current_price', 0)
            
            # Apply shock if symbol or asset class matches
            shock = shocks.get(symbol, shocks.get(pos.get('asset_class', ''), 0))
            
            position_value = quantity * price
            impact = position_value * shock
            
            position_impacts[symbol] = impact
            total_impact += impact
        
        return ScenarioAnalysis(
            scenario_name=scenario_name,
            market_shocks=shocks,
            factor_shocks={},
            correlation_changes={},
            volatility_multiplier=1.0,
            portfolio_impact=total_impact,
            probability=0.05  # Default 5% probability
        )
    
    def _generate_recommendations(
        self,
        scenario: StressScenario,
        impact_pct: float,
        position_impacts: Dict[str, float]
    ) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if impact_pct > 0.20:
            recommendations.append("CRITICAL: Consider immediate position reduction")
            recommendations.append("Implement portfolio hedges (puts, VIX calls)")
        
        if impact_pct > 0.10:
            recommendations.append("Review and tighten stop-loss levels")
            recommendations.append("Increase cash allocation")
        
        # Scenario-specific recommendations
        if scenario == StressScenario.LIQUIDITY_CRISIS:
            recommendations.append("Reduce positions in illiquid assets")
            recommendations.append("Ensure adequate cash reserves")
        
        if scenario == StressScenario.VOLATILITY_SPIKE:
            recommendations.append("Consider volatility hedges")
            recommendations.append("Reduce gross exposure")
        
        if scenario == StressScenario.CORRELATION_BREAKDOWN:
            recommendations.append("Review diversification assumptions")
            recommendations.append("Consider tail risk hedges")
        
        # Position-specific
        worst_positions = sorted(
            position_impacts.items(),
            key=lambda x: x[1]
        )[:3]
        
        for symbol, impact in worst_positions:
            if impact < -0.05:  # 5% threshold
                recommendations.append(f"Consider reducing {symbol} exposure")
        
        return recommendations


class MarginManager:
    """
    Margin Management System
    Tracks margin requirements and utilization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Margin parameters
        self.initial_margin_rate = config.get('initial_margin', 0.50)  # 50%
        self.maintenance_margin_rate = config.get('maintenance_margin', 0.25)  # 25%
        self.margin_call_buffer = config.get('margin_call_buffer', 0.05)  # 5%
        
        # Current state
        self.total_margin_requirement = 0.0
        self.available_margin = 0.0
        self.margin_utilization = 0.0
        
        # Position margins
        self.position_margins: Dict[str, Dict[str, float]] = {}
        
        logger.info("Margin Manager initialized")
    
    def calculate_margin_requirement(
        self,
        positions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate total margin requirement"""
        total_initial = 0.0
        total_maintenance = 0.0
        
        for symbol, pos in positions.items():
            quantity = abs(pos.get('quantity', 0))
            price = pos.get('current_price', 0)
            position_value = quantity * price
            
            # Get asset-specific margin rates
            asset_class = pos.get('asset_class', 'equity')
            margin_rate = self._get_margin_rate(asset_class)
            
            initial_margin = position_value * margin_rate['initial']
            maintenance_margin = position_value * margin_rate['maintenance']
            
            self.position_margins[symbol] = {
                'position_value': position_value,
                'initial_margin': initial_margin,
                'maintenance_margin': maintenance_margin
            }
            
            total_initial += initial_margin
            total_maintenance += maintenance_margin
        
        self.total_margin_requirement = total_initial
        
        return {
            'total_initial_margin': total_initial,
            'total_maintenance_margin': total_maintenance,
            'position_margins': self.position_margins
        }
    
    def _get_margin_rate(self, asset_class: str) -> Dict[str, float]:
        """Get margin rates by asset class"""
        rates = {
            'equity': {'initial': 0.50, 'maintenance': 0.25},
            'futures': {'initial': 0.10, 'maintenance': 0.05},
            'options': {'initial': 1.00, 'maintenance': 1.00},  # Full premium
            'forex': {'initial': 0.02, 'maintenance': 0.01},  # 50:1 leverage
            'crypto': {'initial': 0.50, 'maintenance': 0.40},
            'bonds': {'initial': 0.10, 'maintenance': 0.05}
        }
        return rates.get(asset_class, rates['equity'])
    
    def check_margin_call(
        self,
        equity: float,
        margin_requirement: float
    ) -> Tuple[bool, float]:
        """Check if margin call is triggered"""
        self.available_margin = equity - margin_requirement
        self.margin_utilization = margin_requirement / equity if equity > 0 else 1.0
        
        # Margin call if utilization exceeds threshold
        margin_call_threshold = 1 - self.margin_call_buffer
        is_margin_call = self.margin_utilization > margin_call_threshold
        
        shortfall = max(0, margin_requirement - equity * margin_call_threshold)
        
        return is_margin_call, shortfall
    
    def get_margin_status(self, equity: float) -> Dict[str, Any]:
        """Get current margin status"""
        return {
            'total_margin_requirement': self.total_margin_requirement,
            'available_margin': self.available_margin,
            'margin_utilization': f"{self.margin_utilization * 100:.1f}%",
            'equity': equity,
            'excess_margin': max(0, equity - self.total_margin_requirement),
            'buying_power': (equity - self.total_margin_requirement) / self.initial_margin_rate
        }


class InstitutionalRiskManager:
    """
    Master Institutional Risk Manager
    Coordinates all risk management components
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Components
        self.var_engine = VaREngine(config.get('var', {}))
        self.stress_engine = StressTestEngine(config.get('stress', {}))
        self.margin_manager = MarginManager(config.get('margin', {}))
        
        # Risk limits
        self.limits = {
            'max_var_95': config.get('max_var_95', 0.02),  # 2% daily VaR
            'max_var_99': config.get('max_var_99', 0.05),  # 5% daily VaR
            'max_leverage': config.get('max_leverage', 2.0),
            'max_concentration': config.get('max_concentration', 0.10),
            'max_sector_exposure': config.get('max_sector_exposure', 0.25),
            'max_drawdown': config.get('max_drawdown', 0.15),
            'max_correlation': config.get('max_correlation', 0.7)
        }
        
        # Counterparty exposures
        self.counterparty_exposures: Dict[str, CounterpartyRisk] = {}
        
        # Liquidity metrics
        self.liquidity_metrics: Dict[str, LiquidityRisk] = {}
        
        # Current risk state
        self.current_risk_level = RiskLevel.LOW
        self.risk_alerts: List[Dict[str, Any]] = []
        
        logger.info("Institutional Risk Manager initialized")
    
    def run_full_risk_assessment(
        self,
        positions: Dict[str, Dict[str, Any]],
        portfolio_value: float,
        portfolio_volatility: float,
        historical_returns: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Run comprehensive risk assessment"""
        results = {
            'timestamp': datetime.now(),
            'portfolio_value': portfolio_value,
            'var_analysis': {},
            'stress_tests': {},
            'margin_status': {},
            'liquidity_analysis': {},
            'counterparty_analysis': {},
            'risk_alerts': [],
            'overall_risk_level': RiskLevel.LOW
        }
        
        # VaR Analysis
        for conf in [0.95, 0.99]:
            for horizon in [1, 10]:
                var_result = self.var_engine.calculate_parametric_var(
                    portfolio_value, portfolio_volatility, conf, horizon
                )
                results['var_analysis'][f'var_{int(conf*100)}_{horizon}d'] = var_result.to_dict()
        
        # Historical VaR if data available
        if historical_returns is not None and len(historical_returns) > 0:
            hist_var = self.var_engine.calculate_historical_var(
                portfolio_value, historical_returns, 0.95, 1
            )
            results['var_analysis']['historical_var_95_1d'] = hist_var.to_dict()
        
        # Stress Tests
        stress_results = self.stress_engine.run_all_scenarios(
            positions, portfolio_value
        )
        results['stress_tests'] = {
            s.value: r.to_dict() for s, r in stress_results.items()
        }
        
        # Margin Status
        margin_req = self.margin_manager.calculate_margin_requirement(positions)
        results['margin_status'] = self.margin_manager.get_margin_status(portfolio_value)
        
        # Liquidity Analysis
        results['liquidity_analysis'] = self._analyze_liquidity(positions)
        
        # Check limits and generate alerts
        alerts = self._check_risk_limits(results, portfolio_value)
        results['risk_alerts'] = alerts
        self.risk_alerts = alerts
        
        # Determine overall risk level
        results['overall_risk_level'] = self._determine_risk_level(results)
        self.current_risk_level = results['overall_risk_level']
        
        return results
    
    def _analyze_liquidity(
        self,
        positions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze portfolio liquidity"""
        liquidity_metrics = {}
        total_illiquid = 0
        
        for symbol, pos in positions.items():
            quantity = abs(pos.get('quantity', 0))
            price = pos.get('current_price', 0)
            avg_volume = pos.get('avg_volume', 1000000)
            
            position_value = quantity * price
            
            # Days to liquidate (assuming 10% of ADV)
            daily_liquidation = avg_volume * price * 0.10
            days_to_liquidate = position_value / daily_liquidation if daily_liquidation > 0 else 999
            
            # Liquidation cost (market impact)
            participation_rate = position_value / (avg_volume * price) if avg_volume > 0 else 1
            liquidation_cost = 0.001 + 0.01 * np.sqrt(participation_rate) if NUMPY_AVAILABLE else 0.01
            
            # Liquidity score
            if days_to_liquidate < 1:
                liquidity_score = 100
            elif days_to_liquidate < 3:
                liquidity_score = 80
            elif days_to_liquidate < 5:
                liquidity_score = 60
            elif days_to_liquidate < 10:
                liquidity_score = 40
            else:
                liquidity_score = 20
            
            metric = LiquidityRisk(
                symbol=symbol,
                avg_daily_volume=avg_volume,
                position_size=position_value,
                days_to_liquidate=days_to_liquidate,
                liquidation_cost=liquidation_cost,
                liquidity_score=liquidity_score
            )
            
            self.liquidity_metrics[symbol] = metric
            liquidity_metrics[symbol] = {
                'days_to_liquidate': round(days_to_liquidate, 1),
                'liquidation_cost': f"{liquidation_cost * 100:.2f}%",
                'liquidity_score': liquidity_score,
                'is_illiquid': metric.is_illiquid
            }
            
            if metric.is_illiquid:
                total_illiquid += position_value
        
        return {
            'position_liquidity': liquidity_metrics,
            'total_illiquid_value': total_illiquid,
            'portfolio_liquidity_score': np.mean([
                m.liquidity_score for m in self.liquidity_metrics.values()
            ]) if self.liquidity_metrics and NUMPY_AVAILABLE else 50
        }
    
    def _check_risk_limits(
        self,
        results: Dict[str, Any],
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """Check risk limits and generate alerts"""
        alerts = []
        
        # VaR limits
        var_95 = results['var_analysis'].get('var_95_1d', {})
        if var_95:
            var_pct = float(var_95.get('var_percentage', '0%').replace('%', '')) / 100
            if var_pct > self.limits['max_var_95']:
                alerts.append({
                    'type': 'VAR_BREACH',
                    'severity': 'HIGH',
                    'message': f"95% VaR ({var_pct*100:.1f}%) exceeds limit ({self.limits['max_var_95']*100:.1f}%)",
                    'action': 'Reduce risk exposure'
                })
        
        # Stress test alerts
        for scenario, result in results['stress_tests'].items():
            if result['risk_level'] in ['high', 'critical']:
                alerts.append({
                    'type': 'STRESS_TEST',
                    'severity': result['risk_level'].upper(),
                    'message': f"Stress scenario '{scenario}' shows {result['impact_percentage']} impact",
                    'action': '; '.join(result['recommendations'][:2])
                })
        
        # Margin alerts
        margin = results['margin_status']
        utilization = float(margin.get('margin_utilization', '0%').replace('%', ''))
        if utilization > 80:
            alerts.append({
                'type': 'MARGIN_WARNING',
                'severity': 'HIGH' if utilization > 90 else 'MEDIUM',
                'message': f"Margin utilization at {utilization:.1f}%",
                'action': 'Reduce positions or add capital'
            })
        
        # Liquidity alerts
        liquidity = results['liquidity_analysis']
        if liquidity.get('portfolio_liquidity_score', 100) < 50:
            alerts.append({
                'type': 'LIQUIDITY_WARNING',
                'severity': 'MEDIUM',
                'message': f"Portfolio liquidity score: {liquidity['portfolio_liquidity_score']:.0f}/100",
                'action': 'Review illiquid positions'
            })
        
        return alerts
    
    def _determine_risk_level(
        self,
        results: Dict[str, Any]
    ) -> RiskLevel:
        """Determine overall risk level"""
        alerts = results['risk_alerts']
        
        critical_count = sum(1 for a in alerts if a['severity'] == 'CRITICAL')
        high_count = sum(1 for a in alerts if a['severity'] == 'HIGH')
        medium_count = sum(1 for a in alerts if a['severity'] == 'MEDIUM')
        
        if critical_count > 0:
            return RiskLevel.CRITICAL
        elif high_count >= 2:
            return RiskLevel.HIGH
        elif high_count >= 1 or medium_count >= 3:
            return RiskLevel.ELEVATED
        elif medium_count >= 1:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    def add_counterparty_exposure(
        self,
        counterparty_id: str,
        name: str,
        exposure_type: str,
        gross_exposure: float,
        net_exposure: float,
        collateral: float,
        credit_rating: str
    ):
        """Add counterparty exposure"""
        # Estimate PD from rating
        pd_by_rating = {
            'AAA': 0.0001, 'AA': 0.0005, 'A': 0.001,
            'BBB': 0.005, 'BB': 0.02, 'B': 0.05,
            'CCC': 0.15, 'CC': 0.30, 'C': 0.50
        }
        pd = pd_by_rating.get(credit_rating, 0.01)
        lgd = 0.45  # Standard LGD assumption
        
        self.counterparty_exposures[counterparty_id] = CounterpartyRisk(
            counterparty_id=counterparty_id,
            counterparty_name=name,
            exposure_type=exposure_type,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            collateral_held=collateral,
            credit_rating=credit_rating,
            probability_of_default=pd,
            loss_given_default=lgd,
            expected_loss=net_exposure * pd * lgd
        )
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get risk summary"""
        return {
            'current_risk_level': self.current_risk_level.value,
            'active_alerts': len(self.risk_alerts),
            'var_history_count': len(self.var_engine.var_history),
            'stress_test_count': len(self.stress_engine.stress_test_history),
            'counterparty_count': len(self.counterparty_exposures),
            'total_counterparty_exposure': sum(
                c.net_exposure for c in self.counterparty_exposures.values()
            ),
            'limits': self.limits
        }
