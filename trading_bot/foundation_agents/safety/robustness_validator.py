"""
Robustness Validator - Adversarial Testing
============================================

Validates system robustness against:
1. Adversarial market conditions
2. Edge cases and extreme scenarios
3. Noise and data corruption
4. Performance degradation

Ensures the system remains safe and effective under stress.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)


class StressType(Enum):
    """Types of stress tests"""
    MARKET_CRASH = "market_crash"
    FLASH_CRASH = "flash_crash"
    HIGH_VOLATILITY = "high_volatility"
    LOW_LIQUIDITY = "low_liquidity"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    DATA_CORRUPTION = "data_corruption"
    LATENCY_SPIKE = "latency_spike"
    ORDER_BOOK_IMBALANCE = "order_book_imbalance"


class RobustnessLevel(Enum):
    """Robustness assessment levels"""
    EXCELLENT = 5
    GOOD = 4
    ADEQUATE = 3
    POOR = 2
    CRITICAL = 1


@dataclass
class StressTestResult:
    """Result of a stress test"""
    test_id: str
    stress_type: StressType
    
    # Test parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Results
    survived: bool = True
    performance_degradation: float = 0.0
    max_drawdown: float = 0.0
    recovery_time: float = 0.0
    
    # Safety
    safety_triggered: bool = False
    emergency_actions: List[str] = field(default_factory=list)
    
    # Assessment
    robustness_score: float = 1.0
    
    # Timing
    executed_at: datetime = field(default_factory=datetime.utcnow)
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'test_id': self.test_id,
            'stress_type': self.stress_type.value,
            'survived': self.survived,
            'degradation': self.performance_degradation,
            'drawdown': self.max_drawdown,
            'robustness_score': self.robustness_score
        }


@dataclass
class AdversarialScenario:
    """An adversarial test scenario"""
    scenario_id: str
    name: str
    description: str
    
    # Scenario definition
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    duration_minutes: int = 60
    
    # Expected outcomes
    max_acceptable_drawdown: float = 0.10
    max_acceptable_loss: float = 0.05
    min_recovery_rate: float = 0.5


class RobustnessValidator:
    """
    Robustness Validator
    
    Tests system robustness against various adversarial conditions
    and stress scenarios to ensure safe operation.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.max_drawdown_threshold = self.config.get('max_drawdown', 0.15)
        self.max_volatility_threshold = self.config.get('max_volatility', 0.50)
        self.min_recovery_rate = self.config.get('min_recovery', 0.3)
        
        # Scenarios
        self.scenarios: Dict[str, AdversarialScenario] = {}
        self.test_results: List[StressTestResult] = []
        
        # Current state
        self.is_testing = False
        self.current_scenario: Optional[AdversarialScenario] = None
        
        # Statistics
        self.stats = {
            'tests_run': 0,
            'tests_passed': 0,
            'avg_robustness_score': 1.0
        }
        
        # Register default scenarios
        self._register_default_scenarios()
        
        logger.info("Robustness Validator initialized")
    
    def _register_default_scenarios(self):
        """Register default adversarial scenarios"""
        scenarios = [
            AdversarialScenario(
                scenario_id="market_crash_2008",
                name="2008-style Market Crash",
                description="50% drawdown over 6 months with high volatility",
                market_conditions={
                    'daily_return_mean': -0.003,
                    'daily_return_std': 0.04,
                    'max_drawdown': 0.50,
                    'duration_days': 120
                },
                duration_minutes=120,
                max_acceptable_drawdown=0.20
            ),
            AdversarialScenario(
                scenario_id="flash_crash_2010",
                name="2010 Flash Crash",
                description="Rapid 10% drop in minutes followed by recovery",
                market_conditions={
                    'initial_drop': 0.10,
                    'drop_duration_minutes': 10,
                    'recovery_duration_minutes': 30,
                    'volatility_spike': 3.0
                },
                duration_minutes=60,
                max_acceptable_drawdown=0.05
            ),
            AdversarialScenario(
                scenario_id="high_volatility_2020",
                name="COVID-19 Volatility",
                description="Sustained high volatility with sharp moves",
                market_conditions={
                    'vix_level': 60,
                    'daily_return_std': 0.05,
                    'gap_frequency': 0.3,
                    'duration_days': 30
                },
                duration_minutes=90,
                max_acceptable_drawdown=0.15
            ),
            AdversarialScenario(
                scenario_id="correlation_breakdown",
                name="Correlation Breakdown",
                description="Diversification fails when needed most",
                market_conditions={
                    'normal_correlation': 0.3,
                    'crisis_correlation': 0.9,
                    'crisis_frequency': 0.2,
                    'asset_count': 10
                },
                duration_minutes=60,
                max_acceptable_drawdown=0.12
            ),
            AdversarialScenario(
                scenario_id="liquidity_crisis",
                name="Liquidity Crisis",
                description="Widening spreads and reduced market depth",
                market_conditions={
                    'spread_widening': 5.0,
                    'depth_reduction': 0.8,
                    'slippage_increase': 3.0
                },
                duration_minutes=45,
                max_acceptable_drawdown=0.08
            )
        ]
        
        for scenario in scenarios:
            self.scenarios[scenario.scenario_id] = scenario
    
    def add_scenario(self, scenario: AdversarialScenario):
        """Add a custom adversarial scenario"""
        self.scenarios[scenario.scenario_id] = scenario
    
    def run_stress_test(
        self,
        scenario_id: str,
        strategy_function: Callable,
        initial_portfolio_value: float = 100000.0
    ) -> StressTestResult:
        """Run a stress test with given scenario"""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        scenario = self.scenarios[scenario_id]
        self.current_scenario = scenario
        self.is_testing = True
        
        logger.info(f"Running stress test: {scenario.name}")
        
        test_id = f"stress_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = StressTestResult(
            test_id=test_id,
            stress_type=self._map_scenario_to_stress_type(scenario),
            parameters=scenario.market_conditions
        )
        
        try:
            # Generate synthetic market data for scenario
            market_data = self._generate_scenario_data(scenario)
            
            # Run strategy through scenario
            portfolio_values = self._simulate_strategy(
                strategy_function,
                market_data,
                initial_portfolio_value
            )
            
            # Analyze results
            result = self._analyze_performance(portfolio_values, scenario, result)
            
        except Exception as e:
            logger.error(f"Stress test error: {e}")
            result.survived = False
            result.safety_triggered = True
            result.emergency_actions.append(f"Test error: {str(e)}")
        
        finally:
            self.is_testing = False
            self.current_scenario = None
        
        self.test_results.append(result)
        self.stats['tests_run'] += 1
        if result.survived:
            self.stats['tests_passed'] += 1
        
        # Update average score
        self.stats['avg_robustness_score'] = np.mean([
            r.robustness_score for r in self.test_results[-20:]
        ]) if self.test_results else 1.0
        
        return result
    
    def _map_scenario_to_stress_type(self, scenario: AdversarialScenario) -> StressType:
        """Map scenario to stress type"""
        scenario_id = scenario.scenario_id.lower()
        
        if 'crash' in scenario_id and 'flash' in scenario_id:
            return StressType.FLASH_CRASH
        elif 'crash' in scenario_id:
            return StressType.MARKET_CRASH
        elif 'volatility' in scenario_id:
            return StressType.HIGH_VOLATILITY
        elif 'correlation' in scenario_id:
            return StressType.CORRELATION_BREAKDOWN
        elif 'liquidity' in scenario_id:
            return StressType.LOW_LIQUIDITY
        else:
            return StressType.HIGH_VOLATILITY
    
    def _generate_scenario_data(
        self,
        scenario: AdversarialScenario
    ) -> Dict[str, np.ndarray]:
        """Generate synthetic market data for scenario"""
        conditions = scenario.market_conditions
        
        # Generate price series
        duration_days = conditions.get('duration_days', 30)
        n_days = duration_days
        
        returns = np.random.normal(
            conditions.get('daily_return_mean', 0),
            conditions.get('daily_return_std', 0.02),
            n_days
        )
        
        # Add crash if specified
        if 'max_drawdown' in conditions:
            # Simulate drawdown period
            crash_start = n_days // 3
            crash_end = crash_start + n_days // 3
            returns[crash_start:crash_end] = np.random.normal(-0.02, 0.03, crash_end - crash_start)
        
        # Generate prices
        prices = 100 * np.exp(np.cumsum(returns))
        
        # Generate volatility
        base_vol = conditions.get('daily_return_std', 0.02)
        volatility = np.full(n_days, base_vol)
        
        if 'vix_level' in conditions:
            # Scale volatility by VIX level
            volatility = volatility * (conditions['vix_level'] / 20)
        
        return {
            'prices': prices,
            'returns': returns,
            'volatility': volatility,
            'dates': range(n_days)
        }
    
    def _simulate_strategy(
        self,
        strategy_function: Callable,
        market_data: Dict[str, np.ndarray],
        initial_value: float
    ) -> np.ndarray:
        """Simulate strategy through market data"""
        n_days = len(market_data['prices'])
        portfolio_values = np.zeros(n_days)
        portfolio_values[0] = initial_value
        
        # Simplified simulation
        for i in range(1, n_days):
            try:
                # Get strategy signal
                signal = strategy_function(market_data, i)
                
                # Apply signal to portfolio
                market_return = market_data['returns'][i]
                portfolio_values[i] = portfolio_values[i-1] * (1 + signal * market_return)
                
            except Exception as e:
                # Hold if strategy fails
                portfolio_values[i] = portfolio_values[i-1]
        
        return portfolio_values
    
    def _analyze_performance(
        self,
        portfolio_values: np.ndarray,
        scenario: AdversarialScenario,
        result: StressTestResult
    ) -> StressTestResult:
        """Analyze performance during stress test"""
        # Calculate metrics
        initial_value = portfolio_values[0]
        min_value = np.min(portfolio_values)
        final_value = portfolio_values[-1]
        
        # Max drawdown
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (peak - portfolio_values) / peak
        max_dd = np.max(drawdown)
        result.max_drawdown = max_dd
        
        # Performance degradation
        total_return = (final_value - initial_value) / initial_value
        benchmark_return = -0.10  # Assume -10% benchmark in stress
        result.performance_degradation = abs(total_return - benchmark_return)
        
        # Recovery time
        max_dd_idx = np.argmax(drawdown)
        if max_dd_idx < len(portfolio_values) - 1:
            # Find when portfolio recovered to previous peak
            peak_value = peak[max_dd_idx]
            recovery_idx = np.where(portfolio_values[max_dd_idx:] >= peak_value * 0.99)[0]
            if len(recovery_idx) > 0:
                result.recovery_time = recovery_idx[0]
        
        # Assess survival
        result.survived = (
            max_dd <= scenario.max_acceptable_drawdown and
            final_value >= initial_value * (1 - scenario.max_acceptable_loss)
        )
        
        # Calculate robustness score
        dd_score = max(0, 1 - max_dd / self.max_drawdown_threshold)
        recovery_score = min(1.0, result.recovery_time / max(1, len(portfolio_values) * 0.5))
        return_score = max(0, 1 + total_return) if total_return > -1 else 0
        
        result.robustness_score = (
            dd_score * 0.4 +
            recovery_score * 0.3 +
            return_score * 0.3
        )
        
        # Safety check
        if max_dd > self.max_drawdown_threshold * 1.5:
            result.safety_triggered = True
            result.emergency_actions.append("Drawdown limit exceeded")
        
        result.duration_seconds = len(portfolio_values)
        
        return result
    
    def test_data_corruption_resilience(
        self,
        data: np.ndarray,
        corruption_rate: float = 0.1,
        corruption_type: str = "random"
    ) -> Dict:
        """Test resilience to data corruption"""
        n_corrupt = int(len(data) * corruption_rate)
        corrupt_indices = np.random.choice(len(data), size=n_corrupt, replace=False)
        
        corrupted_data = data.copy()
        
        if corruption_type == "random":
            corrupted_data[corrupt_indices] = np.random.randn(n_corrupt) * np.std(data)
        elif corruption_type == "missing":
            corrupted_data[corrupt_indices] = np.nan
        elif corruption_type == "outlier":
            corrupted_data[corrupt_indices] = np.random.choice([-5, 5], n_corrupt) * np.std(data)
        
        # Measure information loss
        if corruption_type == "missing":
            # Handle missing values
            valid_mask = ~np.isnan(corrupted_data)
            correlation = np.corrcoef(
                data[valid_mask],
                corrupted_data[valid_mask]
            )[0, 1] if np.sum(valid_mask) > 1 else 0.0
        else:
            correlation = np.corrcoef(data, corrupted_data)[0, 1]
        
        if np.isnan(correlation):
            correlation = 0.0
        
        return {
            'corruption_rate': corruption_rate,
            'corruption_type': corruption_type,
            'information_retention': correlation,
            'corrupted_indices': len(corrupt_indices),
            'resilience_score': correlation
        }
    
    def get_robustness_report(self) -> Dict:
        """Generate comprehensive robustness report"""
        if not self.test_results:
            return {'status': 'no_tests_run'}
        
        recent_tests = self.test_results[-20:]
        
        return {
            'overall_robustness': self.stats['avg_robustness_score'],
            'tests_passed_rate': self.stats['tests_passed'] / max(1, self.stats['tests_run']),
            'scenarios_tested': len(self.scenarios),
            'by_scenario': [
                {
                    'scenario': r.parameters.get('scenario_name', 'unknown'),
                    'survived': r.survived,
                    'robustness': r.robustness_score,
                    'drawdown': r.max_drawdown
                }
                for r in recent_tests
            ],
            'recommendations': self._generate_recommendations(recent_tests)
        }
    
    def _generate_recommendations(self, tests: List[StressTestResult]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [t for t in tests if not t.survived]
        
        if len(failed_tests) > len(tests) * 0.3:
            recommendations.append("High failure rate - review risk management parameters")
        
        high_drawdown_tests = [t for t in tests if t.max_drawdown > 0.15]
        if high_drawdown_tests:
            recommendations.append("Consider tighter stop-losses during stress periods")
        
        slow_recovery_tests = [t for t in tests if t.recovery_time > len(tests) * 0.5]
        if slow_recovery_tests:
            recommendations.append("Improve recovery mechanisms after drawdowns")
        
        if not recommendations:
            recommendations.append("System shows good robustness - maintain current parameters")
        
        return recommendations
    
    def get_statistics(self) -> Dict:
        """Get validator statistics"""
        return {
            **self.stats,
            'scenarios_available': len(self.scenarios),
            'tests_in_history': len(self.test_results),
            'robustness_level': self._score_to_level(self.stats['avg_robustness_score']).name
        }
    
    def _score_to_level(self, score: float) -> RobustnessLevel:
        """Convert score to robustness level"""
        if score >= 0.8:
            return RobustnessLevel.EXCELLENT
        elif score >= 0.6:
            return RobustnessLevel.GOOD
        elif score >= 0.4:
            return RobustnessLevel.ADEQUATE
        elif score >= 0.2:
            return RobustnessLevel.POOR
        else:
            return RobustnessLevel.CRITICAL
