"""
Adversarial Simulator
=====================

Red Team / Blue Team architecture for testing strategy robustness.

Red Team: Generates worst-case market scenarios
- Flash crashes (-10% in minutes)
- Liquidity freezes (bid-ask > 5%)
- Correlation breakdowns (all correlations → 1)
- Gap opens (-20% overnight)
- Halt cascades (multiple halts in session)

Blue Team: Tests if strategies survive

Goal: Find strategies humans never tried AND survive black swans.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """Types of adversarial market scenarios."""
    FLASH_CRASH = "flash_crash"
    LIQUIDITY_FREEZE = "liquidity_freeze"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    GAP_OPEN = "gap_open"
    HALT_CASCADE = "halt_cascade"
    VOLATILITY_EXPLOSION = "volatility_explosion"
    CONTAGION = "contagion"
    FLASH_RALLY = "flash_rally"


@dataclass
class MarketScenario:
    """Adversarial market scenario."""
    scenario_id: str
    scenario_type: ScenarioType
    description: str
    severity: float  # 0.0-1.0
    
    # Price path modifications
    price_shocks: List[Tuple[int, float]] = field(default_factory=list)  # (step, multiplier)
    volatility_multiplier: float = 1.0
    liquidity_factor: float = 1.0
    
    # Duration
    duration_steps: int = 100
    recovery_steps: int = 50
    
    # Success criteria
    max_acceptable_loss: float = 0.20  # 20%
    min_recovery_time: int = 20
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scenario_id': self.scenario_id,
            'scenario_type': self.scenario_type.value,
            'description': self.description,
            'severity': self.severity,
            'price_shocks': self.price_shocks,
            'volatility_multiplier': self.volatility_multiplier,
            'liquidity_factor': self.liquidity_factor,
            'duration_steps': self.duration_steps,
            'recovery_steps': self.recovery_steps,
        }


@dataclass
class SurvivalMetrics:
    """Metrics for how well a strategy survived a scenario."""
    scenario_id: str
    survived: bool
    
    # Performance metrics
    max_drawdown: float
    total_return: float
    recovery_time: int
    
    # Strategy behavior
    num_trades: int
    avg_position_size: float
    time_in_market: float  # percentage
    
    # Risk metrics
    var_95: float  # Value at Risk
    cvar_95: float  # Conditional VaR
    
    # Score
    survival_score: float  # 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scenario_id': self.scenario_id,
            'survived': self.survived,
            'max_drawdown': self.max_drawdown,
            'total_return': self.total_return,
            'recovery_time': self.recovery_time,
            'num_trades': self.num_trades,
            'avg_position_size': self.avg_position_size,
            'time_in_market': self.time_in_market,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'survival_score': self.survival_score,
        }


class AdversarialSimulator:
    """
    Red Team / Blue Team adversarial testing system.
    
    Red Team generates increasingly difficult scenarios.
    Blue Team (strategies) must demonstrate survival.
    """
    
    def __init__(self, 
                 initial_difficulty: float = 0.3,
                 difficulty_escalation: float = 0.1):
        """
        Initialize adversarial simulator.
        
        Args:
            initial_difficulty: Starting difficulty (0.0-1.0)
            difficulty_escalation: How much to increase difficulty each round
        """
        self.difficulty = initial_difficulty
        self.difficulty_escalation = difficulty_escalation
        
        self.scenarios: List[MarketScenario] = []
        self.results: List[Tuple[MarketScenario, SurvivalMetrics]] = []
        
        logger.info(f"AdversarialSimulator initialized (difficulty={initial_difficulty})")
    
    def red_team_generate_scenario(self, 
                                  scenario_type: Optional[ScenarioType] = None) -> MarketScenario:
        """
        Red Team generates adversarial market conditions.
        
        Args:
            scenario_type: Type of scenario (random if None)
            
        Returns:
            MarketScenario
        """
        if scenario_type is None:
            scenario_type = np.random.choice(list(ScenarioType))
        
        scenario_id = f"{scenario_type.value}_{len(self.scenarios)}"
        severity = min(1.0, self.difficulty + np.random.uniform(-0.1, 0.1))
        
        if scenario_type == ScenarioType.FLASH_CRASH:
            scenario = self._generate_flash_crash(scenario_id, severity)
        elif scenario_type == ScenarioType.LIQUIDITY_FREEZE:
            scenario = self._generate_liquidity_freeze(scenario_id, severity)
        elif scenario_type == ScenarioType.CORRELATION_BREAKDOWN:
            scenario = self._generate_correlation_breakdown(scenario_id, severity)
        elif scenario_type == ScenarioType.GAP_OPEN:
            scenario = self._generate_gap_open(scenario_id, severity)
        elif scenario_type == ScenarioType.HALT_CASCADE:
            scenario = self._generate_halt_cascade(scenario_id, severity)
        elif scenario_type == ScenarioType.VOLATILITY_EXPLOSION:
            scenario = self._generate_volatility_explosion(scenario_id, severity)
        elif scenario_type == ScenarioType.CONTAGION:
            scenario = self._generate_contagion(scenario_id, severity)
        else:  # FLASH_RALLY
            scenario = self._generate_flash_rally(scenario_id, severity)
        
        self.scenarios.append(scenario)
        return scenario
    
    def _generate_flash_crash(self, scenario_id: str, severity: float) -> MarketScenario:
        """Generate flash crash scenario (-5% to -20% in minutes)."""
        crash_magnitude = 0.05 + severity * 0.15  # 5% to 20%
        
        return MarketScenario(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.FLASH_CRASH,
            description=f"Flash crash: -{crash_magnitude*100:.1f}% in 10 minutes",
            severity=severity,
            price_shocks=[(10, 1 - crash_magnitude), (20, 1 - crash_magnitude * 0.8)],
            volatility_multiplier=3.0 + severity * 2.0,
            liquidity_factor=0.3,
            duration_steps=50,
            recovery_steps=100,
        )
    
    def _generate_liquidity_freeze(self, scenario_id: str, severity: float) -> MarketScenario:
        """Generate liquidity freeze scenario."""
        return MarketScenario(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.LIQUIDITY_FREEZE,
            description="Liquidity freeze: bid-ask spreads widen 10x",
            severity=severity,
            price_shocks=[],
            volatility_multiplier=2.0,
            liquidity_factor=0.1 + (1 - severity) * 0.2,
            duration_steps=100,
            recovery_steps=50,
        )
    
    def _generate_correlation_breakdown(self, scenario_id: str, severity: float) -> MarketScenario:
        """Generate correlation breakdown (all correlations → 1)."""
        return MarketScenario(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.CORRELATION_BREAKDOWN,
            description="Correlation breakdown: all assets move together",
            severity=severity,
            price_shocks=[(i, 1 - 0.001 * i) for i in range(1, 30)],
            volatility_multiplier=2.5,
            liquidity_factor=0.5,
            duration_steps=80,
            recovery_steps=60,
        )
    
    def _generate_gap_open(self, scenario_id: str, severity: float) -> MarketScenario:
        """Generate overnight gap down scenario."""
        gap_size = 0.05 + severity * 0.15  # 5% to 20% gap
        
        return MarketScenario(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.GAP_OPEN,
            description=f"Gap open: -{gap_size*100:.1f}% overnight",
            severity=severity,
            price_shocks=[(0, 1 - gap_size)],
            volatility_multiplier=2.0,
            liquidity_factor=0.4,
            duration_steps=30,
            recovery_steps=80,
        )
    
    def _generate_halt_cascade(self, scenario_id: str, severity: float) -> MarketScenario:
        """Generate trading halt cascade scenario."""
        return MarketScenario(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.HALT_CASCADE,
            description="Multiple circuit breaker halts",
            severity=severity,
            price_shocks=[(5, 0.92), (15, 0.88), (25, 0.85)],
            volatility_multiplier=4.0,
            liquidity_factor=0.0,  # No trading possible
            duration_steps=40,
            recovery_steps=120,
        )
    
    def _generate_volatility_explosion(self, scenario_id: str, severity: float) -> MarketScenario:
        """Generate volatility explosion scenario."""
        return MarketScenario(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.VOLATILITY_EXPLOSION,
            description=f"Volatility explodes {2 + severity * 3:.1f}x normal",
            severity=severity,
            price_shocks=[],
            volatility_multiplier=2.0 + severity * 3.0,
            liquidity_factor=0.5,
            duration_steps=150,
            recovery_steps=100,
        )
    
    def _generate_contagion(self, scenario_id: str, severity: float) -> MarketScenario:
        """Generate cross-asset contagion scenario."""
        return MarketScenario(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.CONTAGION,
            description="Cross-asset contagion: crisis spreads across markets",
            severity=severity,
            price_shocks=[(i, 1 - 0.002 * i) for i in range(1, 50)],
            volatility_multiplier=2.0 + severity,
            liquidity_factor=0.4,
            duration_steps=100,
            recovery_steps=150,
        )
    
    def _generate_flash_rally(self, scenario_id: str, severity: float) -> MarketScenario:
        """Generate flash rally (unexpected spike up)."""
        rally_size = 0.05 + severity * 0.10
        
        return MarketScenario(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.FLASH_RALLY,
            description=f"Flash rally: +{rally_size*100:.1f}% in 10 minutes",
            severity=severity,
            price_shocks=[(10, 1 + rally_size), (20, 1 + rally_size * 0.9)],
            volatility_multiplier=2.5,
            liquidity_factor=0.5,
            duration_steps=40,
            recovery_steps=60,
        )
    
    def blue_team_test_strategy(self, 
                              strategy,
                              scenario: MarketScenario,
                              base_prices: List[float]) -> SurvivalMetrics:
        """
        Blue Team: Test if strategy survives worst-case scenario.
        
        Args:
            strategy: Trading strategy to test
            scenario: Adversarial scenario
            base_prices: Base price series
            
        Returns:
            SurvivalMetrics
        """
        # Apply scenario shocks to prices
        shocked_prices = self._apply_scenario(base_prices, scenario)
        
        # Simulate strategy
        portfolio_values = [10000.0]
        positions = []
        trades = 0
        
        for i in range(len(shocked_prices) - 1):
            # Get strategy signal (simplified)
            if hasattr(strategy, 'generate_signal'):
                market_data = {'price': shocked_prices[i], 'returns': 0}
                signal = strategy.generate_signal(market_data)
            else:
                signal = 0
            
            # Simple position management
            position = 1 if signal > 0.3 else -1 if signal < -0.3 else 0
            positions.append(position)
            
            if position != 0:
                trades += 1
            
            # Calculate PnL
            price_return = (shocked_prices[i + 1] - shocked_prices[i]) / shocked_prices[i]
            trade_pnl = position * price_return * portfolio_values[-1]
            
            portfolio_values.append(portfolio_values[-1] + trade_pnl)
        
        # Calculate metrics
        max_dd = self._calculate_max_drawdown(portfolio_values)
        total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
        
        # Find recovery time
        peak_idx = np.argmax(portfolio_values)
        recovery_time = 0
        for i in range(peak_idx, len(portfolio_values)):
            if portfolio_values[i] >= portfolio_values[peak_idx]:
                recovery_time = i - peak_idx
                break
        
        # Calculate VaR
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
        cvar_95 = np.mean([r for r in returns if r <= var_95]) if len(returns) > 0 else 0
        
        # Survival score
        survival_score = self._calculate_survival_score(
            max_dd, total_return, recovery_time, scenario
        )
        
        survived = (
            max_dd < scenario.max_acceptable_loss and
            total_return > -scenario.max_acceptable_loss and
            recovery_time < scenario.min_recovery_time * 3
        )
        
        metrics = SurvivalMetrics(
            scenario_id=scenario.scenario_id,
            survived=survived,
            max_drawdown=max_dd,
            total_return=total_return,
            recovery_time=recovery_time,
            num_trades=trades,
            avg_position_size=np.mean([abs(p) for p in positions]) if positions else 0,
            time_in_market=sum(1 for p in positions if p != 0) / len(positions) if positions else 0,
            var_95=var_95,
            cvar_95=cvar_95,
            survival_score=survival_score,
        )
        
        self.results.append((scenario, metrics))
        return metrics
    
    def _apply_scenario(self, base_prices: List[float], scenario: MarketScenario) -> List[float]:
        """Apply scenario shocks to price series."""
        prices = base_prices.copy()
        
        # Apply price shocks
        for step, multiplier in scenario.price_shocks:
            if step < len(prices):
                prices[step] *= multiplier
        
        # Ensure prices don't go negative
        prices = [max(0.01, p) for p in prices]
        
        return prices
    
    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown."""
        peak = portfolio_values[0]
        max_dd = 0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            if peak > 0:
                dd = (peak - value) / peak
                max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _calculate_survival_score(self, 
                                 max_dd: float, 
                                 total_return: float, 
                                 recovery_time: int,
                                 scenario: MarketScenario) -> float:
        """Calculate overall survival score."""
        # Penalize drawdown
        dd_score = max(0, 1 - max_dd / scenario.max_acceptable_loss)
        
        # Reward positive returns
        return_score = max(0, 1 + total_return) if total_return > -0.5 else 0
        
        # Penalize long recovery
        recovery_score = max(0, 1 - recovery_time / (scenario.min_recovery_time * 3))
        
        # Combined score
        score = (dd_score * 0.5 + return_score * 0.3 + recovery_score * 0.2)
        
        return min(1.0, score)
    
    def adversarial_training_loop(self, 
                                 strategy,
                                 base_prices: List[float],
                                 num_rounds: int = 10) -> Tuple[Any, List[SurvivalMetrics]]:
        """
        Iteratively improve strategy against ever-worse scenarios.
        
        Args:
            strategy: Initial strategy
            base_prices: Base price series
            num_rounds: Number of adversarial rounds
            
        Returns:
            (improved_strategy, survival_metrics_list)
        """
        logger.info(f"Starting adversarial training for {num_rounds} rounds")
        
        all_metrics = []
        
        for round_num in range(num_rounds):
            # Generate scenario at current difficulty
            scenario = self.red_team_generate_scenario()
            
            # Test strategy
            metrics = self.blue_team_test_strategy(strategy, scenario, base_prices)
            all_metrics.append(metrics)
            
            logger.info(f"Round {round_num + 1}: Survival={metrics.survived}, "
                       f"Score={metrics.survival_score:.3f}, "
                       f"DD={metrics.max_drawdown:.2%}")
            
            # Escalate difficulty if strategy survived
            if metrics.survived and metrics.survival_score > 0.7:
                self.difficulty = min(1.0, self.difficulty + self.difficulty_escalation)
                logger.info(f"Escalating difficulty to {self.difficulty:.2f}")
        
        return strategy, all_metrics
    
    def get_stress_test_report(self) -> Dict[str, Any]:
        """Get comprehensive stress test report."""
        if not self.results:
            return {'status': 'no_tests_run'}
        
        survival_rate = sum(1 for _, m in self.results if m.survived) / len(self.results)
        avg_survival_score = np.mean([m.survival_score for _, m in self.results])
        
        by_scenario_type = {}
        for scenario, metrics in self.results:
            st = scenario.scenario_type.value
            if st not in by_scenario_type:
                by_scenario_type[st] = []
            by_scenario_type[st].append(metrics.survival_score)
        
        avg_by_type = {k: np.mean(v) for k, v in by_scenario_type.items()}
        
        return {
            'total_scenarios': len(self.results),
            'survival_rate': survival_rate,
            'avg_survival_score': avg_survival_score,
            'max_drawdown_worst': max(m.max_drawdown for _, m in self.results),
            'survival_by_scenario_type': avg_by_type,
            'current_difficulty': self.difficulty,
        }
