"""
Portfolio-Level Risk Management

Advanced risk management with portfolio VaR, stress testing,
correlation monitoring, and dynamic position sizing.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging
import numpy as np

logger = logging.getLogger(__name__)


class RiskMetricType(Enum):
    """Types of risk metrics"""
    VALUE_AT_RISK = "var"
    CONDITIONAL_VAR = "cvar"
    BETA = "beta"
    CORRELATION = "correlation"
    CONCENTRATION = "concentration"
    LEVERAGE = "leverage"
    STRESS_TEST = "stress_test"


@dataclass
class PortfolioPosition:
    """Portfolio position with risk attributes"""
    symbol: str
    size: float
    entry_price: float
    current_price: float
    beta: float
    sector: str
    volatility: float
    notional_value: float
    unrealized_pnl: float
    weight: float  # Portfolio weight


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    portfolio_var_1d: float  # 1-day VaR
    portfolio_var_1d_pct: float
    conditional_var: float
    portfolio_beta: float
    gross_exposure: float
    net_exposure: float
    concentration_risk: float
    correlation_risk: float
    stress_test_loss: float
    max_drawdown_current: float
    sharpe_ratio: float
    information_ratio: float


@dataclass
class StressScenario:
    """Stress test scenario"""
    name: str
    description: str
    market_shock: Dict[str, float]
    expected_loss: float
    expected_loss_pct: float
    recovery_time_days: int
    probability: float


class PortfolioRiskManager:
    """
    Portfolio-level risk management with advanced analytics.
    """
    
    def __init__(
        self,
        confidence_level: float = 0.95,
        var_time_horizon_days: int = 1,
        enable_stress_testing: bool = True,
        max_correlation_threshold: float = 0.8
    ):
        self.confidence_level = confidence_level
        self.var_horizon = var_time_horizon_days
        self.enable_stress_testing = enable_stress_testing
        self.max_correlation = max_correlation_threshold
        
        # Portfolio state
        self.positions: Dict[str, PortfolioPosition] = {}
        self.portfolio_value: float = 0.0
        self.cash: float = 0.0
        
        # Historical data for VaR calculation
        self.returns_history: deque = deque(maxlen=252)
        
        # Correlation matrix
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        # Stress scenarios
        self.stress_scenarios: List[StressScenario] = []
        self._init_stress_scenarios()
        
    def _init_stress_scenarios(self) -> None:
        """Initialize standard stress scenarios"""
        
        self.stress_scenarios = [
            StressScenario(
                name="2008_financial_crisis",
                description="Global financial crisis scenario",
                market_shock={
                    'equities': -0.50,
                    'credit': -0.30,
                    'volatility': 3.0,
                    'correlations': 0.9
                },
                expected_loss=0.0,
                expected_loss_pct=0.0,
                recovery_time_days=180,
                probability=0.01
            ),
            StressScenario(
                name="2020_covid_crash",
                description="COVID-19 market crash",
                market_shock={
                    'equities': -0.35,
                    'commodities': -0.25,
                    'volatility': 2.5
                },
                expected_loss=0.0,
                expected_loss_pct=0.0,
                recovery_time_days=90,
                probability=0.02
            ),
            StressScenario(
                name="interest_rate_shock",
                description="Sudden interest rate increase",
                market_shock={
                    'rates': 0.03,
                    'bonds': -0.15,
                    'equities': -0.20,
                    'real_estate': -0.25
                },
                expected_loss=0.0,
                expected_loss_pct=0.0,
                recovery_time_days=60,
                probability=0.05
            ),
            StressScenario(
                name="liquidity_crisis",
                description="Systemic liquidity freeze",
                market_shock={
                    'liquidity': -0.80,
                    'spreads': 5.0,
                    'all_assets': -0.15
                },
                expected_loss=0.0,
                expected_loss_pct=0.0,
                recovery_time_days=30,
                probability=0.03
            )
        ]
    
    def add_position(self, position: PortfolioPosition) -> None:
        """Add or update a position"""
        self.positions[position.symbol] = position
        self._recalculate_portfolio_value()
        
    def remove_position(self, symbol: str) -> None:
        """Remove a position"""
        if symbol in self.positions:
            del self.positions[symbol]
            self._recalculate_portfolio_value()
    
    def _recalculate_portfolio_value(self) -> None:
        """Recalculate total portfolio value"""
        positions_value = sum(
            p.notional_value for p in self.positions.values()
        )
        self.portfolio_value = positions_value + self.cash
        
        if self.portfolio_value > 0:
            for p in self.positions.values():
                p.weight = p.notional_value / self.portfolio_value
    
    def calculate_portfolio_metrics(self) -> RiskMetrics:
        """Calculate comprehensive portfolio risk metrics"""
        
        var = self._calculate_var()
        cvar = self._calculate_cvar()
        portfolio_beta = self._calculate_portfolio_beta()
        gross, net = self._calculate_exposures()
        concentration = self._calculate_concentration_risk()
        correlation_risk = self._calculate_correlation_risk()
        
        stress_loss = 0.0
        if self.enable_stress_testing:
            stress_results = self.run_stress_tests()
            stress_loss = max(r['expected_loss_pct'] for r in stress_results)
        
        max_dd = self._calculate_current_drawdown()
        sharpe = self._calculate_sharpe_ratio()
        info_ratio = self._calculate_information_ratio()
        
        return RiskMetrics(
            portfolio_var_1d=var,
            portfolio_var_1d_pct=var / self.portfolio_value if self.portfolio_value > 0 else 0,
            conditional_var=cvar,
            portfolio_beta=portfolio_beta,
            gross_exposure=gross,
            net_exposure=net,
            concentration_risk=concentration,
            correlation_risk=correlation_risk,
            stress_test_loss=stress_loss,
            max_drawdown_current=max_dd,
            sharpe_ratio=sharpe,
            information_ratio=info_ratio
        )
    
    def _calculate_var(self, method: str = 'historical') -> float:
        """Calculate Value at Risk"""
        
        if len(self.returns_history) < 30:
            return self._parametric_var()
        
        returns = np.array(self.returns_history)
        var_percentile = (1 - self.confidence_level) * 100
        var = np.percentile(returns, var_percentile)
        
        return abs(var) * self.portfolio_value
    
    def _parametric_var(self) -> float:
        """Calculate parametric VaR"""
        portfolio_vol = self._estimate_portfolio_volatility()
        z_score = 1.645 if self.confidence_level == 0.95 else 2.33
        time_factor = np.sqrt(self.var_horizon / 252)
        
        return self.portfolio_value * z_score * portfolio_vol * time_factor
    
    def _calculate_cvar(self) -> float:
        """Calculate Conditional VaR"""
        if len(self.returns_history) < 30:
            return self._calculate_var() * 1.3
        
        returns = np.array(self.returns_history)
        var_percentile = (1 - self.confidence_level) * 100
        var_threshold = np.percentile(returns, var_percentile)
        
        tail_returns = returns[returns <= var_threshold]
        if len(tail_returns) > 0:
            return abs(np.mean(tail_returns)) * self.portfolio_value
        
        return self._calculate_var() * 1.3
    
    def _calculate_portfolio_beta(self) -> float:
        """Calculate portfolio beta to market"""
        if not self.positions:
            return 0.0
        
        return sum(p.beta * p.weight for p in self.positions.values())
    
    def _calculate_exposures(self) -> Tuple[float, float]:
        """Calculate gross and net exposure"""
        long = sum(p.notional_value for p in self.positions.values() if p.size > 0)
        short = sum(abs(p.notional_value) for p in self.positions.values() if p.size < 0)
        return long + short, long - short
    
    def _calculate_concentration_risk(self) -> float:
        """Calculate concentration risk using Herfindahl index"""
        if not self.positions or self.portfolio_value == 0:
            return 0.0
        
        herfindahl = sum(p.weight ** 2 for p in self.positions.values())
        n = len(self.positions)
        
        if n > 1:
            min_herf = 1 / n
            max_herf = 1.0
            return max(0, min(1, (herfindahl - min_herf) / (max_herf - min_herf)))
        
        return 1.0
    
    def _calculate_correlation_risk(self) -> float:
        """Calculate portfolio correlation risk"""
        if len(self.positions) < 2:
            return 0.0
        
        correlations = []
        symbols = list(self.positions.keys())
        
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr = self._get_correlation(sym1, sym2)
                correlations.append(abs(corr))
        
        return np.mean(correlations) if correlations else 0.0
    
    def _get_correlation(self, sym1: str, sym2: str) -> float:
        """Get correlation between symbols"""
        if sym1 in self.correlation_matrix and sym2 in self.correlation_matrix[sym1]:
            return self.correlation_matrix[sym1][sym2]
        return 0.5
    
    def _calculate_current_drawdown(self) -> float:
        return 0.0  # Would track from historical peaks
    
    def _estimate_portfolio_volatility(self) -> float:
        """Estimate portfolio volatility"""
        if not self.positions:
            return 0.0
        
        weights = np.array([p.weight for p in self.positions.values()])
        vols = np.array([p.volatility for p in self.positions.values()])
        
        # Simplified: weighted average
        return np.sum(weights * vols)
    
    def _calculate_sharpe_ratio(self) -> float:
        return 1.0  # Would calculate from historical returns
    
    def _calculate_information_ratio(self) -> float:
        return 0.5  # Would calculate from tracking error
    
    def run_stress_tests(self) -> List[Dict]:
        """Run all stress test scenarios"""
        results = []
        
        for scenario in self.stress_scenarios:
            result = self._run_single_stress_test(scenario)
            results.append(result)
        
        return results
    
    def _run_single_stress_test(self, scenario: StressScenario) -> Dict:
        """Run a single stress test scenario"""
        
        total_loss = 0.0
        position_losses = []
        
        for position in self.positions.values():
            # Determine shock based on position attributes
            shock = scenario.market_shock.get('equities', -0.20)
            
            # Adjust for beta
            effective_shock = shock * position.beta
            
            # Calculate loss
            loss = position.notional_value * effective_shock
            total_loss += loss
            
            position_losses.append({
                'symbol': position.symbol,
                'notional': position.notional_value,
                'shock': effective_shock,
                'loss': loss,
                'loss_pct': effective_shock
            })
        
        loss_pct = total_loss / self.portfolio_value if self.portfolio_value > 0 else 0
        
        return {
            'scenario': scenario.name,
            'description': scenario.description,
            'expected_loss': total_loss,
            'expected_loss_pct': loss_pct,
            'recovery_time_days': scenario.recovery_time_days,
            'position_breakdown': position_losses,
            'probability': scenario.probability
        }
    
    def check_position_risk_limits(
        self,
        symbol: str,
        proposed_size: float,
        proposed_price: float,
        beta: float = 1.0,
        sector: str = 'unknown'
    ) -> Tuple[bool, List[str], float]:
        """Check if proposed position passes risk limits"""
        
        violations = []
        
        proposed_notional = abs(proposed_size * proposed_price)
        new_portfolio_value = self.portfolio_value + proposed_notional
        
        # Position size limit
        position_pct = proposed_notional / new_portfolio_value if new_portfolio_value > 0 else 0
        if position_pct > 0.10:  # 10% single position limit
            violations.append(f"Position size {position_pct:.1%} exceeds 10% limit")
        
        # Sector concentration
        sector_exposure = sum(
            p.notional_value for p in self.positions.values()
            if p.sector == sector
        ) / new_portfolio_value if new_portfolio_value > 0 else 0
        
        new_sector_exposure = sector_exposure + (proposed_notional / new_portfolio_value if new_portfolio_value > 0 else 0)
        if new_sector_exposure > 0.30:
            violations.append(f"Sector exposure {new_sector_exposure:.1%} exceeds 30% limit")
        
        # Portfolio heat
        if symbol not in self.positions and len(self.positions) >= 10:
            violations.append("Maximum portfolio heat reached (10 positions)")
        
        # Calculate adjusted size
        adjusted_size = proposed_size
        if violations:
            # Scale down to meet constraints
            adjusted_size = proposed_size * 0.7
        
        passed = len(violations) == 0
        return passed, violations, adjusted_size
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        
        metrics = self.calculate_portfolio_metrics()
        stress_results = self.run_stress_tests() if self.enable_stress_testing else []
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'portfolio_value': self.portfolio_value,
            'position_count': len(self.positions),
            'risk_metrics': {
                'var_1d': metrics.portfolio_var_1d,
                'var_1d_pct': metrics.portfolio_var_1d_pct,
                'cvar': metrics.conditional_var,
                'portfolio_beta': metrics.portfolio_beta,
                'gross_exposure': metrics.gross_exposure,
                'net_exposure': metrics.net_exposure,
                'concentration_risk': metrics.concentration_risk,
                'correlation_risk': metrics.correlation_risk,
                'max_stress_loss': metrics.stress_test_loss,
                'sharpe_ratio': metrics.sharpe_ratio
            },
            'stress_test_results': stress_results,
            'position_breakdown': [
                {
                    'symbol': p.symbol,
                    'weight': p.weight,
                    'beta': p.beta,
                    'sector': p.sector,
                    'unrealized_pnl': p.unrealized_pnl
                }
                for p in self.positions.values()
            ],
            'recommendations': self._generate_risk_recommendations(metrics)
        }
    
    def _generate_risk_recommendations(self, metrics: RiskMetrics) -> List[str]:
        """Generate risk management recommendations"""
        
        recommendations = []
        
        if metrics.portfolio_var_1d_pct > 0.02:  # 2% daily VaR
            recommendations.append("High daily VaR - consider reducing position sizes")
        
        if metrics.concentration_risk > 0.5:
            recommendations.append("High concentration risk - add diversification")
        
        if metrics.correlation_risk > 0.7:
            recommendations.append("High correlation risk - positions may move together in stress")
        
        if metrics.portfolio_beta > 1.5:
            recommendations.append("High portfolio beta - sensitive to market movements")
        
        if metrics.stress_test_loss > 0.15:
            recommendations.append(f"Severe stress loss potential ({metrics.stress_test_loss:.1%}) - review tail risk")
        
        return recommendations
