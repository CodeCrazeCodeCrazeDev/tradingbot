"""
Overnight Risk Simulation
Gap modeling, exposure trimming, and scenario testing for overnight positions
"""

import asyncio
import logging
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from enum import auto
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class GapScenario(Enum):
    """Gap scenario types"""
    NORMAL = "normal"
    MODERATE_GAP = "moderate_gap"
    LARGE_GAP = "large_gap"
    EXTREME_GAP = "extreme_gap"
    BLACK_SWAN = "black_swan"
    FLASH_CRASH = "flash_crash"
    LIMIT_UP = "limit_up"
    LIMIT_DOWN = "limit_down"


@dataclass
class GapEvent:
    """Historical gap event"""
    date: datetime
    symbol: str
    open_price: float
    prev_close: float
    gap_pct: float
    scenario: GapScenario
    cause: Optional[str] = None


@dataclass
class OvernightPosition:
    """Position held overnight"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    beta: float = 1.0
    sector: Optional[str] = None
    
    @property
    def exposure(self) -> float:
        return abs(self.market_value)


@dataclass
class SimulationResult:
    """Result of overnight risk simulation"""
    scenario: GapScenario
    gap_pct: float
    portfolio_pnl: float
    portfolio_pnl_pct: float
    worst_position: str
    worst_position_pnl: float
    positions_at_risk: int
    margin_call_risk: bool
    recommended_action: str
    confidence: float


@dataclass
class OvernightRiskReport:
    """Comprehensive overnight risk report"""
    timestamp: datetime
    total_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    positions: List[OvernightPosition]
    simulations: List[SimulationResult]
    var_95: float
    var_99: float
    expected_shortfall: float
    recommendations: List[str]
    risk_score: float  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_exposure': self.total_exposure,
            'net_exposure': self.net_exposure,
            'var_95': self.var_95,
            'var_99': self.var_99,
            'expected_shortfall': self.expected_shortfall,
            'risk_score': self.risk_score,
            'recommendations': self.recommendations,
            'simulations': [
                {
                    'scenario': s.scenario.value,
                    'gap_pct': s.gap_pct,
                    'portfolio_pnl': s.portfolio_pnl,
                    'portfolio_pnl_pct': s.portfolio_pnl_pct
                }
                for s in self.simulations
            ]
        }


class OvernightRiskSimulator:
    """
    Overnight risk simulation and gap modeling system
    """
    
    # Historical gap statistics by scenario
    GAP_DISTRIBUTIONS = {
        GapScenario.NORMAL: {'mean': 0.0, 'std': 0.005, 'probability': 0.70},
        GapScenario.MODERATE_GAP: {'mean': 0.0, 'std': 0.015, 'probability': 0.20},
        GapScenario.LARGE_GAP: {'mean': 0.0, 'std': 0.03, 'probability': 0.07},
        GapScenario.EXTREME_GAP: {'mean': 0.0, 'std': 0.05, 'probability': 0.025},
        GapScenario.BLACK_SWAN: {'mean': -0.10, 'std': 0.10, 'probability': 0.005},
        GapScenario.FLASH_CRASH: {'mean': -0.15, 'std': 0.05, 'probability': 0.001},
        GapScenario.LIMIT_UP: {'mean': 0.10, 'std': 0.02, 'probability': 0.002},
        GapScenario.LIMIT_DOWN: {'mean': -0.10, 'std': 0.02, 'probability': 0.002},
    }
    
    # Sector correlations during stress
    SECTOR_STRESS_CORRELATIONS = {
        'technology': 1.2,
        'financials': 1.3,
        'healthcare': 0.8,
        'utilities': 0.6,
        'consumer_staples': 0.7,
        'consumer_discretionary': 1.1,
        'energy': 1.4,
        'materials': 1.2,
        'industrials': 1.0,
        'real_estate': 1.1,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Risk parameters
        self.max_overnight_exposure = self.config.get('max_overnight_exposure', 100000)
        self.max_single_position_pct = self.config.get('max_single_position_pct', 0.20)
        self.var_confidence = self.config.get('var_confidence', 0.95)
        self.margin_requirement = self.config.get('margin_requirement', 0.25)
        
        # Simulation settings
        self.num_simulations = self.config.get('num_simulations', 10000)
        self.include_correlations = self.config.get('include_correlations', True)
        
        # Historical data
        self.gap_history: List[GapEvent] = []
        
        # Auto-trim settings
        self.auto_trim_enabled = self.config.get('auto_trim_enabled', True)
        self.trim_threshold_risk_score = self.config.get('trim_threshold_risk_score', 70)
        
        logger.info("Overnight risk simulator initialized")
        
    def add_gap_history(self, events: List[GapEvent]):
        """Add historical gap events for calibration"""
        self.gap_history.extend(events)
        logger.info(f"Added {len(events)} gap events to history")
        
    def simulate_gap(self, scenario: GapScenario, symbol: Optional[str] = None) -> float:
        """
        Simulate a gap based on scenario
        
        Returns:
            Gap percentage (e.g., -0.05 for -5% gap)
        """
        dist = self.GAP_DISTRIBUTIONS[scenario]
        gap = np.random.normal(dist['mean'], dist['std'])
        
        # Apply symbol-specific adjustments if available
        if symbol and self.gap_history:
            symbol_gaps = [g.gap_pct for g in self.gap_history if g.symbol == symbol]
            if symbol_gaps:
                historical_vol = np.std(symbol_gaps)
                gap *= (historical_vol / dist['std']) if dist['std'] > 0 else 1
                
        return gap
    
    def simulate_correlated_gaps(
        self,
        positions: List[OvernightPosition],
        scenario: GapScenario
    ) -> Dict[str, float]:
        """
        Simulate correlated gaps across positions
        """
        gaps = {}
        
        # Base market gap
        market_gap = self.simulate_gap(scenario)
        
        for position in positions:
            # Apply beta
            position_gap = market_gap * position.beta
            
            # Apply sector stress correlation
            if position.sector and self.include_correlations:
                sector_mult = self.SECTOR_STRESS_CORRELATIONS.get(position.sector.lower(), 1.0)
                if scenario in [GapScenario.BLACK_SWAN, GapScenario.FLASH_CRASH, GapScenario.EXTREME_GAP]:
                    position_gap *= sector_mult
                    
            # Add idiosyncratic component
            idio_gap = np.random.normal(0, 0.01)
            position_gap += idio_gap
            
            gaps[position.symbol] = position_gap
            
        return gaps
    
    def calculate_portfolio_pnl(
        self,
        positions: List[OvernightPosition],
        gaps: Dict[str, float]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate portfolio P&L given gaps
        
        Returns:
            Tuple of (total_pnl, position_pnls)
        """
        position_pnls = {}
        total_pnl = 0
        
        for position in positions:
            gap = gaps.get(position.symbol, 0)
            new_price = position.current_price * (1 + gap)
            pnl = (new_price - position.current_price) * position.quantity
            position_pnls[position.symbol] = pnl
            total_pnl += pnl
            
        return total_pnl, position_pnls
    
    def run_monte_carlo(
        self,
        positions: List[OvernightPosition]
    ) -> List[float]:
        """
        Run Monte Carlo simulation for overnight risk
        
        Returns:
            List of simulated portfolio P&Ls
        """
        pnls = []
        
        for _ in range(self.num_simulations):
            # Select scenario based on probability
            scenario = self._select_scenario()
            
            # Simulate gaps
            gaps = self.simulate_correlated_gaps(positions, scenario)
            
            # Calculate P&L
            total_pnl, _ = self.calculate_portfolio_pnl(positions, gaps)
            pnls.append(total_pnl)
            
        return pnls
    
    def _select_scenario(self) -> GapScenario:
        """Select scenario based on probability distribution"""
        rand = np.random.random()
        cumulative = 0
        
        for scenario, dist in self.GAP_DISTRIBUTIONS.items():
            cumulative += dist['probability']
            if rand <= cumulative:
                return scenario
                
        return GapScenario.NORMAL
    
    def run_scenario_analysis(
        self,
        positions: List[OvernightPosition]
    ) -> List[SimulationResult]:
        """
        Run deterministic scenario analysis
        """
        results = []
        total_value = sum(p.market_value for p in positions)
        
        for scenario in GapScenario:
            # Use mean gap for deterministic analysis
            dist = self.GAP_DISTRIBUTIONS[scenario]
            
            # Simulate with mean + 1 std for conservative estimate
            gaps = {}
            for position in positions:
                gap = dist['mean'] + dist['std'] * position.beta
                if position.sector:
                    sector_mult = self.SECTOR_STRESS_CORRELATIONS.get(position.sector.lower(), 1.0)
                    gap *= sector_mult
                gaps[position.symbol] = gap
                
            total_pnl, position_pnls = self.calculate_portfolio_pnl(positions, gaps)
            
            # Find worst position
            worst_symbol = min(position_pnls, key=position_pnls.get) if position_pnls else ""
            worst_pnl = position_pnls.get(worst_symbol, 0)
            
            # Count positions at risk
            at_risk = sum(1 for pnl in position_pnls.values() if pnl < -total_value * 0.01)
            
            # Check margin call risk
            margin_call = abs(total_pnl) > total_value * (1 - self.margin_requirement)
            
            # Determine recommended action
            action = self._get_recommended_action(scenario, total_pnl, total_value)
            
            results.append(SimulationResult(
                scenario=scenario,
                gap_pct=dist['mean'] + dist['std'],
                portfolio_pnl=total_pnl,
                portfolio_pnl_pct=total_pnl / total_value if total_value > 0 else 0,
                worst_position=worst_symbol,
                worst_position_pnl=worst_pnl,
                positions_at_risk=at_risk,
                margin_call_risk=margin_call,
                recommended_action=action,
                confidence=1 - dist['probability']
            ))
            
        return results
    
    def _get_recommended_action(
        self,
        scenario: GapScenario,
        pnl: float,
        total_value: float
    ) -> str:
        """Get recommended action based on scenario impact"""
        pnl_pct = pnl / total_value if total_value > 0 else 0
        
        if scenario in [GapScenario.BLACK_SWAN, GapScenario.FLASH_CRASH]:
            if pnl_pct < -0.10:
                return "REDUCE_ALL_POSITIONS"
            elif pnl_pct < -0.05:
                return "REDUCE_HIGH_BETA"
        elif scenario in [GapScenario.EXTREME_GAP, GapScenario.LIMIT_DOWN]:
            if pnl_pct < -0.05:
                return "HEDGE_OR_REDUCE"
        elif scenario == GapScenario.LARGE_GAP:
            if pnl_pct < -0.03:
                return "CONSIDER_HEDGING"
                
        return "MONITOR"
    
    def calculate_var(self, pnls: List[float], confidence: float = 0.95) -> float:
        """Calculate Value at Risk"""
        return -np.percentile(pnls, (1 - confidence) * 100)
    
    def calculate_expected_shortfall(self, pnls: List[float], confidence: float = 0.95) -> float:
        """Calculate Expected Shortfall (CVaR)"""
        var = self.calculate_var(pnls, confidence)
        tail_losses = [p for p in pnls if p <= -var]
        return -np.mean(tail_losses) if tail_losses else var
    
    def generate_risk_report(
        self,
        positions: List[OvernightPosition]
    ) -> OvernightRiskReport:
        """
        Generate comprehensive overnight risk report
        """
        # Calculate exposures
        long_exposure = sum(p.market_value for p in positions if p.quantity > 0)
        short_exposure = abs(sum(p.market_value for p in positions if p.quantity < 0))
        total_exposure = long_exposure + short_exposure
        net_exposure = long_exposure - short_exposure
        
        # Run Monte Carlo
        pnls = self.run_monte_carlo(positions)
        
        # Calculate risk metrics
        var_95 = self.calculate_var(pnls, 0.95)
        var_99 = self.calculate_var(pnls, 0.99)
        expected_shortfall = self.calculate_expected_shortfall(pnls, 0.95)
        
        # Run scenario analysis
        simulations = self.run_scenario_analysis(positions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            positions, total_exposure, var_99, simulations
        )
        
        # Calculate risk score (0-100)
        risk_score = self._calculate_risk_score(
            total_exposure, var_99, expected_shortfall, simulations
        )
        
        return OvernightRiskReport(
            timestamp=datetime.now(),
            total_exposure=total_exposure,
            net_exposure=net_exposure,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            positions=positions,
            simulations=simulations,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=expected_shortfall,
            recommendations=recommendations,
            risk_score=risk_score
        )
    
    def _generate_recommendations(
        self,
        positions: List[OvernightPosition],
        total_exposure: float,
        var_99: float,
        simulations: List[SimulationResult]
    ) -> List[str]:
        """Generate risk recommendations"""
        recommendations = []
        
        # Check total exposure
        if total_exposure > self.max_overnight_exposure:
            excess = total_exposure - self.max_overnight_exposure
            recommendations.append(
                f"⚠️ Total exposure ${total_exposure:,.0f} exceeds limit. "
                f"Reduce by ${excess:,.0f}"
            )
            
        # Check concentration
        for position in positions:
            pct = position.exposure / total_exposure if total_exposure > 0 else 0
            if pct > self.max_single_position_pct:
                recommendations.append(
                    f"⚠️ {position.symbol} is {pct*100:.1f}% of portfolio. "
                    f"Consider reducing to below {self.max_single_position_pct*100:.0f}%"
                )
                
        # Check high beta positions
        high_beta = [p for p in positions if p.beta > 1.5]
        if high_beta:
            total_high_beta = sum(p.exposure for p in high_beta)
            recommendations.append(
                f"💡 ${total_high_beta:,.0f} in high-beta positions. "
                f"Consider hedging before overnight."
            )
            
        # Check worst-case scenarios
        for sim in simulations:
            if sim.scenario in [GapScenario.BLACK_SWAN, GapScenario.FLASH_CRASH]:
                if sim.margin_call_risk:
                    recommendations.append(
                        f"🚨 {sim.scenario.value} scenario could trigger margin call. "
                        f"Potential loss: ${abs(sim.portfolio_pnl):,.0f}"
                    )
                    
        # VaR recommendation
        if var_99 > total_exposure * 0.10:
            recommendations.append(
                f"⚠️ 99% VaR is ${var_99:,.0f} ({var_99/total_exposure*100:.1f}% of exposure). "
                f"Consider reducing risk."
            )
            
        return recommendations
    
    def _calculate_risk_score(
        self,
        total_exposure: float,
        var_99: float,
        expected_shortfall: float,
        simulations: List[SimulationResult]
    ) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0
        
        # Exposure component (0-25)
        exposure_ratio = total_exposure / self.max_overnight_exposure
        score += min(25, exposure_ratio * 25)
        
        # VaR component (0-25)
        var_ratio = var_99 / total_exposure if total_exposure > 0 else 0
        score += min(25, var_ratio * 250)  # 10% VaR = 25 points
        
        # Expected shortfall component (0-25)
        es_ratio = expected_shortfall / total_exposure if total_exposure > 0 else 0
        score += min(25, es_ratio * 200)
        
        # Scenario component (0-25)
        margin_call_scenarios = sum(1 for s in simulations if s.margin_call_risk)
        score += min(25, margin_call_scenarios * 5)
        
        return min(100, score)
    
    def get_trim_recommendations(
        self,
        positions: List[OvernightPosition],
        target_risk_score: float = 50
    ) -> List[Dict[str, Any]]:
        """
        Get position trim recommendations to achieve target risk
        """
        current_report = self.generate_risk_report(positions)
        
        if current_report.risk_score <= target_risk_score:
            return []
            
        recommendations = []
        
        # Sort positions by risk contribution
        position_risks = []
        for position in positions:
            # Simulate without this position
            other_positions = [p for p in positions if p.symbol != position.symbol]
            if other_positions:
                other_report = self.generate_risk_report(other_positions)
                risk_contribution = current_report.risk_score - other_report.risk_score
            else:
                risk_contribution = current_report.risk_score
                
            position_risks.append((position, risk_contribution))
            
        # Sort by risk contribution
        position_risks.sort(key=lambda x: x[1], reverse=True)
        
        # Recommend trimming highest risk contributors
        remaining_reduction = current_report.risk_score - target_risk_score
        
        for position, risk_contrib in position_risks:
            if remaining_reduction <= 0:
                break
                
            # Calculate trim amount
            trim_pct = min(0.5, remaining_reduction / risk_contrib) if risk_contrib > 0 else 0.25
            trim_quantity = position.quantity * trim_pct
            
            recommendations.append({
                'symbol': position.symbol,
                'current_quantity': position.quantity,
                'trim_quantity': trim_quantity,
                'trim_pct': trim_pct,
                'risk_contribution': risk_contrib,
                'reason': f"High risk contribution ({risk_contrib:.1f} points)"
            })
            
            remaining_reduction -= risk_contrib * trim_pct
            
        return recommendations
    
    async def auto_trim_positions(
        self,
        positions: List[OvernightPosition],
        execute_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Automatically trim positions if risk score exceeds threshold
        """
        if not self.auto_trim_enabled:
            return []
            
        report = self.generate_risk_report(positions)
        
        if report.risk_score < self.trim_threshold_risk_score:
            logger.info(f"Risk score {report.risk_score:.1f} below threshold, no trim needed")
            return []
            
        recommendations = self.get_trim_recommendations(
            positions,
            target_risk_score=self.trim_threshold_risk_score - 10
        )
        
        if execute_callback and recommendations:
            for rec in recommendations:
                try:
                    await execute_callback(rec)
                    logger.info(f"Auto-trimmed {rec['symbol']}: {rec['trim_quantity']:.2f} units")
                except Exception as e:
                    logger.error(f"Failed to auto-trim {rec['symbol']}: {e}")
                    
        return recommendations
