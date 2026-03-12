"""
Adversarial Hardening System
=============================

Become HARDER TO FOOL than the market itself.

PHILOSOPHY:
- The market is adversarial - it actively tries to fool you
- Generate adversarial scenarios to stress test
- Test against worst-case conditions
- Build robustness through stress testing
- If you can fool yourself, the market will fool you

HARDENING TYPES:
1. SCENARIO GENERATION - Generate adversarial scenarios
2. STRESS TESTING - Test under extreme conditions
3. REGIME SIMULATION - Simulate regime changes
4. MANIPULATION DETECTION - Detect market manipulation
5. ROBUSTNESS VERIFICATION - Verify strategy robustness
6. ANTI-FRAGILITY - Become stronger from stress
"""

import logging
import hashlib
import threading
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """Types of adversarial scenarios"""
    FLASH_CRASH = "flash_crash"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    REGIME_CHANGE = "regime_change"
    VOLATILITY_SPIKE = "volatility_spike"
    GAP_OPEN = "gap_open"
    STOP_HUNTING = "stop_hunting"
    FAKE_BREAKOUT = "fake_breakout"
    NEWS_SHOCK = "news_shock"
    MANIPULATION = "manipulation"


class StressLevel(Enum):
    """Stress test intensity"""
    MILD = "mild"           # 1-sigma event
    MODERATE = "moderate"   # 2-sigma event
    SEVERE = "severe"       # 3-sigma event
    EXTREME = "extreme"     # 4+ sigma event
    BLACK_SWAN = "black_swan"  # Unprecedented


class RobustnessLevel(Enum):
    """Robustness assessment"""
    FRAGILE = "fragile"         # Breaks easily
    WEAK = "weak"               # Breaks under stress
    MODERATE = "moderate"       # Survives mild stress
    ROBUST = "robust"           # Survives severe stress
    ANTIFRAGILE = "antifragile" # Gets stronger from stress


@dataclass
class AdversarialScenario:
    """An adversarial scenario for testing"""
    scenario_id: str
    scenario_type: ScenarioType
    stress_level: StressLevel
    description: str
    
    # Scenario parameters
    parameters: Dict[str, Any]
    
    # Expected impact
    expected_drawdown: float
    expected_duration: str
    
    # Historical precedent
    historical_examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'scenario_id': self.scenario_id,
            'scenario_type': self.scenario_type.value,
            'stress_level': self.stress_level.value,
            'description': self.description,
            'parameters': self.parameters,
            'expected_drawdown': self.expected_drawdown,
            'expected_duration': self.expected_duration,
            'historical_examples': self.historical_examples
        }


@dataclass
class StressTestResult:
    """Result of a stress test"""
    test_id: str
    scenario: AdversarialScenario
    
    # Results
    survived: bool
    max_drawdown: float
    recovery_time: Optional[str]
    pnl_impact: float
    
    # Analysis
    failure_points: List[str]
    vulnerabilities: List[str]
    recommendations: List[str]
    
    # Robustness
    robustness_score: float  # 0 to 1
    robustness_level: RobustnessLevel
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'test_id': self.test_id,
            'scenario': self.scenario.to_dict(),
            'survived': self.survived,
            'max_drawdown': self.max_drawdown,
            'recovery_time': self.recovery_time,
            'pnl_impact': self.pnl_impact,
            'failure_points': self.failure_points,
            'vulnerabilities': self.vulnerabilities,
            'recommendations': self.recommendations,
            'robustness_score': self.robustness_score,
            'robustness_level': self.robustness_level.value,
            'timestamp': self.timestamp.isoformat()
        }


class ScenarioGenerator:
    """Generates adversarial scenarios"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.scenarios_generated = 0
    
    def generate_flash_crash(self, stress_level: StressLevel) -> AdversarialScenario:
        """Generate flash crash scenario"""
        severity_map = {
            StressLevel.MILD: {'drop_pct': 0.02, 'duration_seconds': 60},
            StressLevel.MODERATE: {'drop_pct': 0.05, 'duration_seconds': 120},
            StressLevel.SEVERE: {'drop_pct': 0.10, 'duration_seconds': 300},
            StressLevel.EXTREME: {'drop_pct': 0.20, 'duration_seconds': 600},
            StressLevel.BLACK_SWAN: {'drop_pct': 0.35, 'duration_seconds': 1800}
        }
        
        params = severity_map.get(stress_level, severity_map[StressLevel.MODERATE])
        
        return AdversarialScenario(
            scenario_id=self._generate_id("flash_crash"),
            scenario_type=ScenarioType.FLASH_CRASH,
            stress_level=stress_level,
            description=f"Flash crash: {params['drop_pct']:.0%} drop in {params['duration_seconds']}s",
            parameters={
                'price_drop_pct': params['drop_pct'],
                'duration_seconds': params['duration_seconds'],
                'recovery_pct': params['drop_pct'] * 0.7,
                'liquidity_drop': 0.9,
                'spread_multiplier': 10
            },
            expected_drawdown=params['drop_pct'] * 1.5,
            expected_duration=f"{params['duration_seconds'] * 2} seconds",
            historical_examples=[
                "2010-05-06 Flash Crash",
                "2015-08-24 ETF Flash Crash",
                "2020-03-12 COVID Crash"
            ]
        )
    
    def generate_liquidity_crisis(self, stress_level: StressLevel) -> AdversarialScenario:
        """Generate liquidity crisis scenario"""
        severity_map = {
            StressLevel.MILD: {'liquidity_drop': 0.3, 'spread_mult': 2},
            StressLevel.MODERATE: {'liquidity_drop': 0.5, 'spread_mult': 5},
            StressLevel.SEVERE: {'liquidity_drop': 0.7, 'spread_mult': 10},
            StressLevel.EXTREME: {'liquidity_drop': 0.9, 'spread_mult': 20},
            StressLevel.BLACK_SWAN: {'liquidity_drop': 0.99, 'spread_mult': 50}
        }
        
        params = severity_map.get(stress_level, severity_map[StressLevel.MODERATE])
        
        return AdversarialScenario(
            scenario_id=self._generate_id("liquidity_crisis"),
            scenario_type=ScenarioType.LIQUIDITY_CRISIS,
            stress_level=stress_level,
            description=f"Liquidity crisis: {params['liquidity_drop']:.0%} liquidity drop",
            parameters={
                'liquidity_drop_pct': params['liquidity_drop'],
                'spread_multiplier': params['spread_mult'],
                'fill_rate': 1 - params['liquidity_drop'],
                'slippage_multiplier': params['spread_mult'] * 2
            },
            expected_drawdown=params['liquidity_drop'] * 0.3,
            expected_duration="1-5 hours",
            historical_examples=[
                "2008 Financial Crisis",
                "2020 March Liquidity Crisis",
                "2022 Crypto Liquidity Crisis"
            ]
        )
    
    def generate_regime_change(self, stress_level: StressLevel) -> AdversarialScenario:
        """Generate regime change scenario"""
        return AdversarialScenario(
            scenario_id=self._generate_id("regime_change"),
            scenario_type=ScenarioType.REGIME_CHANGE,
            stress_level=stress_level,
            description="Sudden regime change invalidating model assumptions",
            parameters={
                'volatility_change': 2.0 if stress_level == StressLevel.MILD else 5.0,
                'correlation_change': 0.5,
                'trend_reversal': True,
                'model_invalidation': True
            },
            expected_drawdown=0.15,
            expected_duration="Days to weeks",
            historical_examples=[
                "2007-2008 Credit Crisis",
                "2020 COVID Regime Shift",
                "2022 Rate Hike Regime"
            ]
        )
    
    def generate_stop_hunting(self, stress_level: StressLevel) -> AdversarialScenario:
        """Generate stop hunting scenario"""
        return AdversarialScenario(
            scenario_id=self._generate_id("stop_hunting"),
            scenario_type=ScenarioType.STOP_HUNTING,
            stress_level=stress_level,
            description="Stop hunting: price spikes to trigger stops then reverses",
            parameters={
                'spike_pct': 0.01 if stress_level == StressLevel.MILD else 0.03,
                'reversal_pct': 0.02 if stress_level == StressLevel.MILD else 0.05,
                'duration_seconds': 30,
                'volume_spike': 5.0
            },
            expected_drawdown=0.02,
            expected_duration="Minutes",
            historical_examples=[
                "Common in FX markets",
                "Crypto weekend manipulation",
                "Low liquidity hours"
            ]
        )
    
    def generate_fake_breakout(self, stress_level: StressLevel) -> AdversarialScenario:
        """Generate fake breakout scenario"""
        return AdversarialScenario(
            scenario_id=self._generate_id("fake_breakout"),
            scenario_type=ScenarioType.FAKE_BREAKOUT,
            stress_level=stress_level,
            description="Fake breakout: price breaks level then reverses sharply",
            parameters={
                'breakout_pct': 0.005 if stress_level == StressLevel.MILD else 0.015,
                'reversal_pct': 0.02 if stress_level == StressLevel.MILD else 0.04,
                'time_above_level': 5,  # minutes
                'volume_confirmation': False
            },
            expected_drawdown=0.03,
            expected_duration="Hours",
            historical_examples=[
                "Common pattern in ranging markets",
                "News-driven fake breakouts",
                "Weekend gap reversals"
            ]
        )
    
    def generate_all_scenarios(
        self,
        stress_level: StressLevel = StressLevel.MODERATE
    ) -> List[AdversarialScenario]:
        """Generate all scenario types"""
        scenarios = [
            self.generate_flash_crash(stress_level),
            self.generate_liquidity_crisis(stress_level),
            self.generate_regime_change(stress_level),
            self.generate_stop_hunting(stress_level),
            self.generate_fake_breakout(stress_level)
        ]
        
        self.scenarios_generated += len(scenarios)
        return scenarios
    
    def _generate_id(self, prefix: str) -> str:
        return hashlib.md5(
            f"{prefix}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]


class StressTester:
    """Runs stress tests against strategies"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tests_run = 0
        self.tests_passed = 0
    
    def run_stress_test(
        self,
        strategy: Dict[str, Any],
        scenario: AdversarialScenario
    ) -> StressTestResult:
        """
        Run stress test on strategy.
        
        Args:
            strategy: Strategy to test
            scenario: Adversarial scenario
            
        Returns:
            StressTestResult
        """
        test_id = hashlib.md5(
            f"stress_test_{scenario.scenario_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Simulate stress test (in production, would run actual simulation)
        result = self._simulate_stress_test(strategy, scenario)
        
        # Analyze results
        failure_points = self._identify_failure_points(strategy, scenario, result)
        vulnerabilities = self._identify_vulnerabilities(strategy, scenario, result)
        recommendations = self._generate_recommendations(failure_points, vulnerabilities)
        
        # Calculate robustness
        robustness_score = self._calculate_robustness(result, scenario)
        robustness_level = self._determine_robustness_level(robustness_score)
        
        # Determine if survived
        survived = result['max_drawdown'] < strategy.get('max_acceptable_drawdown', 0.2)
        
        self.tests_run += 1
        if survived:
            self.tests_passed += 1
        
        return StressTestResult(
            test_id=test_id,
            scenario=scenario,
            survived=survived,
            max_drawdown=result['max_drawdown'],
            recovery_time=result.get('recovery_time'),
            pnl_impact=result['pnl_impact'],
            failure_points=failure_points,
            vulnerabilities=vulnerabilities,
            recommendations=recommendations,
            robustness_score=robustness_score,
            robustness_level=robustness_level
        )
    
    def _simulate_stress_test(
        self,
        strategy: Dict[str, Any],
        scenario: AdversarialScenario
    ) -> Dict[str, Any]:
        """Simulate stress test"""
        # Get strategy parameters
        position_size = strategy.get('position_size', 0.1)
        stop_loss = strategy.get('stop_loss', 0.02)
        leverage = strategy.get('leverage', 1.0)
        
        # Get scenario parameters
        params = scenario.parameters
        
        # Simulate impact
        if scenario.scenario_type == ScenarioType.FLASH_CRASH:
            price_drop = params.get('price_drop_pct', 0.1)
            max_drawdown = min(price_drop * leverage * position_size, 1.0)
            pnl_impact = -max_drawdown
            
        elif scenario.scenario_type == ScenarioType.LIQUIDITY_CRISIS:
            liquidity_drop = params.get('liquidity_drop_pct', 0.5)
            slippage = params.get('slippage_multiplier', 5) * 0.001
            max_drawdown = slippage * position_size * leverage
            pnl_impact = -max_drawdown
            
        elif scenario.scenario_type == ScenarioType.STOP_HUNTING:
            spike_pct = params.get('spike_pct', 0.02)
            if spike_pct > stop_loss:
                max_drawdown = stop_loss * position_size * leverage
                pnl_impact = -max_drawdown
            else:
                max_drawdown = 0.0
                pnl_impact = 0.0
                
        else:
            # Generic stress
            max_drawdown = 0.1 * position_size * leverage
            pnl_impact = -max_drawdown
        
        # Add noise
        max_drawdown *= (1 + np.random.uniform(-0.2, 0.2))
        
        return {
            'max_drawdown': max_drawdown,
            'pnl_impact': pnl_impact,
            'recovery_time': f"{int(max_drawdown * 100)} hours" if max_drawdown > 0 else None
        }
    
    def _identify_failure_points(
        self,
        strategy: Dict[str, Any],
        scenario: AdversarialScenario,
        result: Dict[str, Any]
    ) -> List[str]:
        """Identify failure points"""
        failure_points = []
        
        if result['max_drawdown'] > strategy.get('max_acceptable_drawdown', 0.2):
            failure_points.append("Exceeded maximum acceptable drawdown")
        
        if scenario.scenario_type == ScenarioType.STOP_HUNTING:
            if strategy.get('stop_loss', 0.02) < scenario.parameters.get('spike_pct', 0.02):
                failure_points.append("Stop loss too tight - vulnerable to stop hunting")
        
        if scenario.scenario_type == ScenarioType.LIQUIDITY_CRISIS:
            if strategy.get('position_size', 0.1) > 0.05:
                failure_points.append("Position size too large for liquidity crisis")
        
        if strategy.get('leverage', 1.0) > 2.0:
            failure_points.append("High leverage amplifies losses")
        
        return failure_points
    
    def _identify_vulnerabilities(
        self,
        strategy: Dict[str, Any],
        scenario: AdversarialScenario,
        result: Dict[str, Any]
    ) -> List[str]:
        """Identify vulnerabilities"""
        vulnerabilities = []
        
        if not strategy.get('has_circuit_breaker', False):
            vulnerabilities.append("No circuit breaker for extreme moves")
        
        if not strategy.get('dynamic_position_sizing', False):
            vulnerabilities.append("Static position sizing - no volatility adjustment")
        
        if not strategy.get('regime_detection', False):
            vulnerabilities.append("No regime detection - blind to regime changes")
        
        if not strategy.get('liquidity_check', False):
            vulnerabilities.append("No liquidity check before trading")
        
        if strategy.get('uses_stops', True) and not strategy.get('uses_time_stops', False):
            vulnerabilities.append("Only price stops - vulnerable to manipulation")
        
        return vulnerabilities
    
    def _generate_recommendations(
        self,
        failure_points: List[str],
        vulnerabilities: List[str]
    ) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        for fp in failure_points:
            if "drawdown" in fp.lower():
                recommendations.append("Reduce position size or leverage")
            if "stop hunting" in fp.lower():
                recommendations.append("Widen stops or use time-based exits")
            if "liquidity" in fp.lower():
                recommendations.append("Reduce position size in low liquidity")
        
        for vuln in vulnerabilities:
            if "circuit breaker" in vuln.lower():
                recommendations.append("Add circuit breaker for extreme moves")
            if "regime" in vuln.lower():
                recommendations.append("Implement regime detection")
            if "liquidity check" in vuln.lower():
                recommendations.append("Add pre-trade liquidity check")
        
        return list(set(recommendations))
    
    def _calculate_robustness(
        self,
        result: Dict[str, Any],
        scenario: AdversarialScenario
    ) -> float:
        """Calculate robustness score"""
        # Base score
        score = 1.0
        
        # Penalize for drawdown
        max_dd = result['max_drawdown']
        if max_dd > 0.3:
            score -= 0.5
        elif max_dd > 0.2:
            score -= 0.3
        elif max_dd > 0.1:
            score -= 0.15
        elif max_dd > 0.05:
            score -= 0.05
        
        # Bonus for surviving extreme scenarios
        if scenario.stress_level == StressLevel.EXTREME and max_dd < 0.2:
            score += 0.1
        if scenario.stress_level == StressLevel.BLACK_SWAN and max_dd < 0.3:
            score += 0.2
        
        return max(0, min(1, score))
    
    def _determine_robustness_level(self, score: float) -> RobustnessLevel:
        """Determine robustness level from score"""
        if score >= 0.9:
            return RobustnessLevel.ANTIFRAGILE
        elif score >= 0.7:
            return RobustnessLevel.ROBUST
        elif score >= 0.5:
            return RobustnessLevel.MODERATE
        elif score >= 0.3:
            return RobustnessLevel.WEAK
        else:
            return RobustnessLevel.FRAGILE


class AdversarialHardening:
    """
    Main adversarial hardening system.
    
    CORE PRINCIPLE:
    Become HARDER TO FOOL than the market itself.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Components
        self.scenario_generator = ScenarioGenerator(config)
        self.stress_tester = StressTester(config)
        
        # History
        self.test_history: List[StressTestResult] = []
        
        # Statistics
        self.total_tests = 0
        self.survival_rate = 0.0
        self.avg_robustness = 0.0
        
        logger.info("AdversarialHardening initialized")
    
    def harden_strategy(
        self,
        strategy: Dict[str, Any],
        stress_levels: Optional[List[StressLevel]] = None
    ) -> Dict[str, Any]:
        """
        Harden a strategy through adversarial testing.
        
        Args:
            strategy: Strategy to harden
            stress_levels: Stress levels to test
            
        Returns:
            Hardening report
        """
        with self.lock:
            if stress_levels is None:
                stress_levels = [
                    StressLevel.MILD,
                    StressLevel.MODERATE,
                    StressLevel.SEVERE
                ]
            
            all_results = []
            
            for stress_level in stress_levels:
                # Generate scenarios
                scenarios = self.scenario_generator.generate_all_scenarios(stress_level)
                
                # Run stress tests
                for scenario in scenarios:
                    result = self.stress_tester.run_stress_test(strategy, scenario)
                    all_results.append(result)
                    self.test_history.append(result)
                    self.total_tests += 1
            
            # Calculate statistics
            survived_count = sum(1 for r in all_results if r.survived)
            self.survival_rate = survived_count / max(len(all_results), 1)
            self.avg_robustness = np.mean([r.robustness_score for r in all_results])
            
            # Aggregate findings
            all_failure_points = []
            all_vulnerabilities = []
            all_recommendations = []
            
            for result in all_results:
                all_failure_points.extend(result.failure_points)
                all_vulnerabilities.extend(result.vulnerabilities)
                all_recommendations.extend(result.recommendations)
            
            # Deduplicate
            unique_failure_points = list(set(all_failure_points))
            unique_vulnerabilities = list(set(all_vulnerabilities))
            unique_recommendations = list(set(all_recommendations))
            
            # Determine overall robustness
            overall_robustness = self._determine_overall_robustness(all_results)
            
            return {
                'strategy_id': strategy.get('strategy_id', 'unknown'),
                'tests_run': len(all_results),
                'tests_survived': survived_count,
                'survival_rate': self.survival_rate,
                'average_robustness': self.avg_robustness,
                'overall_robustness': overall_robustness.value,
                'failure_points': unique_failure_points,
                'vulnerabilities': unique_vulnerabilities,
                'recommendations': unique_recommendations,
                'worst_case_drawdown': max(r.max_drawdown for r in all_results),
                'test_results': [r.to_dict() for r in all_results]
            }
    
    def _determine_overall_robustness(
        self,
        results: List[StressTestResult]
    ) -> RobustnessLevel:
        """Determine overall robustness from all results"""
        if not results:
            return RobustnessLevel.FRAGILE
        
        # Count by level
        level_counts = {level: 0 for level in RobustnessLevel}
        for result in results:
            level_counts[result.robustness_level] += 1
        
        # If any fragile, overall is weak at best
        if level_counts[RobustnessLevel.FRAGILE] > 0:
            return RobustnessLevel.WEAK
        
        # If mostly robust or antifragile
        robust_count = level_counts[RobustnessLevel.ROBUST] + level_counts[RobustnessLevel.ANTIFRAGILE]
        if robust_count >= len(results) * 0.8:
            return RobustnessLevel.ROBUST
        
        # If mostly moderate
        if level_counts[RobustnessLevel.MODERATE] >= len(results) * 0.5:
            return RobustnessLevel.MODERATE
        
        return RobustnessLevel.WEAK
    
    def quick_stress_test(
        self,
        strategy: Dict[str, Any],
        scenario_type: ScenarioType,
        stress_level: StressLevel = StressLevel.MODERATE
    ) -> StressTestResult:
        """Run a quick single stress test"""
        with self.lock:
            # Generate specific scenario
            if scenario_type == ScenarioType.FLASH_CRASH:
                scenario = self.scenario_generator.generate_flash_crash(stress_level)
            elif scenario_type == ScenarioType.LIQUIDITY_CRISIS:
                scenario = self.scenario_generator.generate_liquidity_crisis(stress_level)
            elif scenario_type == ScenarioType.REGIME_CHANGE:
                scenario = self.scenario_generator.generate_regime_change(stress_level)
            elif scenario_type == ScenarioType.STOP_HUNTING:
                scenario = self.scenario_generator.generate_stop_hunting(stress_level)
            elif scenario_type == ScenarioType.FAKE_BREAKOUT:
                scenario = self.scenario_generator.generate_fake_breakout(stress_level)
            else:
                scenario = self.scenario_generator.generate_flash_crash(stress_level)
            
            # Run test
            result = self.stress_tester.run_stress_test(strategy, scenario)
            self.test_history.append(result)
            self.total_tests += 1
            
            return result
    
    def get_hardening_score(self) -> float:
        """Get overall hardening score based on test history"""
        with self.lock:
            if not self.test_history:
                return 0.0
            
            return np.mean([r.robustness_score for r in self.test_history])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get hardening statistics"""
        with self.lock:
            return {
                'total_tests': self.total_tests,
                'scenarios_generated': self.scenario_generator.scenarios_generated,
                'survival_rate': self.survival_rate,
                'average_robustness': self.avg_robustness,
                'hardening_score': self.get_hardening_score(),
                'recent_tests': [
                    r.to_dict() for r in self.test_history[-10:]
                ]
            }
