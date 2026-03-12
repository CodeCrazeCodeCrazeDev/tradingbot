"""
Adversarial Failure Analysis - Stage 2 Fix

Addresses violations:
- No adversarial failure analysis
- No execution stress testing
- Shared assumptions across modules
- Limited microstructure analysis

This module actively tries to BREAK signals by finding failure modes.

Author: AlphaAlgo Core
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class FailureMode(Enum):
    """Types of failure modes"""
    REGIME_SHIFT = "regime_shift"
    LIQUIDITY_VACUUM = "liquidity_vacuum"
    CORRELATION_SPIKE = "correlation_spike"
    VOLATILITY_EXPLOSION = "volatility_explosion"
    EXECUTION_FAILURE = "execution_failure"
    SLIPPAGE_BLOWOUT = "slippage_blowout"
    PARTIAL_FILL = "partial_fill"
    STOP_HUNT = "stop_hunt"
    FLASH_CRASH = "flash_crash"
    NEWS_SHOCK = "news_shock"


@dataclass
class FailureScenario:
    """A specific failure scenario"""
    failure_mode: FailureMode
    description: str
    probability: float
    impact_multiplier: float
    expected_loss: float
    can_survive: bool
    mitigation: Optional[str] = None


@dataclass
class ExecutionStressTest:
    """Results of execution stress testing"""
    scenario: str
    assumed_fill_price: float
    worst_case_fill_price: float
    slippage_bps: float
    partial_fill_probability: float
    expected_execution_cost: float
    passes_stress_test: bool


@dataclass
class AdversarialAnalysis:
    """Complete adversarial analysis results"""
    signal_id: str
    symbol: str
    
    # Failure scenarios
    failure_scenarios: List[FailureScenario]
    catastrophic_scenarios: List[FailureScenario]
    
    # Execution stress tests
    execution_tests: List[ExecutionStressTest]
    worst_case_execution_cost: float
    
    # Overall assessment
    survives_adversarial_analysis: bool
    dominant_failure_risk: Optional[FailureMode]
    expected_worst_case_loss: float
    
    timestamp: datetime


class RegimeShiftAnalyzer:
    """Analyzes regime shift failure risk"""
    
    def analyze(
        self,
        signal: Dict,
        market_context: Dict
    ) -> FailureScenario:
        """Analyze regime shift risk"""
        try:
            current_regime = market_context.get('regime', 'unknown')
            regime_confidence = market_context.get('regime_confidence', 0.5)
            regime_stability = market_context.get('regime_stability', 0.5)
        
            # Probability of regime shift
            # Low confidence or low stability = high shift probability
            shift_probability = 1.0 - (regime_confidence * regime_stability)
        
            # Impact if regime shifts
            # Strategies optimized for one regime fail in another
            impact_multiplier = 2.0  # 2x loss
        
            # Expected loss
            position_size = signal.get('quantity', 1.0)
            entry_price = signal['price']
            stop_loss = signal.get('stop_loss', entry_price * 0.95)
            max_loss = abs(stop_loss - entry_price) / entry_price
        
            expected_loss = shift_probability * impact_multiplier * max_loss * position_size * entry_price
        
            # Can survive?
            can_survive = shift_probability < 0.3 and expected_loss < (entry_price * 0.02)
        
            return FailureScenario(
                failure_mode=FailureMode.REGIME_SHIFT,
                description=f"Regime shifts from {current_regime} during trade",
                probability=shift_probability,
                impact_multiplier=impact_multiplier,
                expected_loss=expected_loss,
                can_survive=can_survive,
                mitigation="Tighten stop loss, reduce position size" if not can_survive else None
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class LiquidityVacuumAnalyzer:
    """Analyzes liquidity vacuum risk"""
    
    def analyze(
        self,
        signal: Dict,
        market_context: Dict
    ) -> FailureScenario:
        """Analyze liquidity vacuum risk"""
        try:
            liquidity_score = market_context.get('liquidity_score', 0.5)
            volume_24h = market_context.get('volume_24h', 0)
        
            # Probability of liquidity vacuum
            # Low liquidity = high vacuum probability
            vacuum_probability = 1.0 - liquidity_score
        
            # Impact if liquidity disappears
            # Cannot exit at stop loss, slippage explodes
            impact_multiplier = 3.0  # 3x loss
        
            position_size = signal.get('quantity', 1.0)
            entry_price = signal['price']
            stop_loss = signal.get('stop_loss', entry_price * 0.95)
            max_loss = abs(stop_loss - entry_price) / entry_price
        
            expected_loss = vacuum_probability * impact_multiplier * max_loss * position_size * entry_price
        
            can_survive = vacuum_probability < 0.2 and expected_loss < (entry_price * 0.03)
        
            return FailureScenario(
                failure_mode=FailureMode.LIQUIDITY_VACUUM,
                description="Liquidity disappears, cannot exit at stop",
                probability=vacuum_probability,
                impact_multiplier=impact_multiplier,
                expected_loss=expected_loss,
                can_survive=can_survive,
                mitigation="Trade only high liquidity symbols" if not can_survive else None
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class CorrelationSpikeAnalyzer:
    """Analyzes correlation spike risk"""
    
    def analyze(
        self,
        signal: Dict,
        market_context: Dict
    ) -> FailureScenario:
        """Analyze correlation spike risk"""
        try:
            current_correlation = market_context.get('correlation_exposure', 0.0)
        
            # Probability of correlation spike
            # High current correlation = high spike probability
            spike_probability = current_correlation
        
            # Impact if correlations spike to 1.0
            # All positions move together, diversification fails
            impact_multiplier = 2.5
        
            position_size = signal.get('quantity', 1.0)
            entry_price = signal['price']
            stop_loss = signal.get('stop_loss', entry_price * 0.95)
            max_loss = abs(stop_loss - entry_price) / entry_price
        
            expected_loss = spike_probability * impact_multiplier * max_loss * position_size * entry_price
        
            can_survive = spike_probability < 0.4 and expected_loss < (entry_price * 0.025)
        
            return FailureScenario(
                failure_mode=FailureMode.CORRELATION_SPIKE,
                description="Correlations spike, diversification fails",
                probability=spike_probability,
                impact_multiplier=impact_multiplier,
                expected_loss=expected_loss,
                can_survive=can_survive,
                mitigation="Reduce correlated positions" if not can_survive else None
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class VolatilityExplosionAnalyzer:
    """Analyzes volatility explosion risk"""
    
    def analyze(
        self,
        signal: Dict,
        market_context: Dict
    ) -> FailureScenario:
        """Analyze volatility explosion risk"""
        try:
            current_volatility = market_context.get('volatility', 0.0)
        
            # Probability of volatility explosion
            # Already high volatility = higher explosion probability
            explosion_probability = min(current_volatility / 0.5, 0.8)
        
            # Impact if volatility doubles
            # Stop loss hit much faster
            impact_multiplier = 2.0
        
            position_size = signal.get('quantity', 1.0)
            entry_price = signal['price']
            stop_loss = signal.get('stop_loss', entry_price * 0.95)
            max_loss = abs(stop_loss - entry_price) / entry_price
        
            expected_loss = explosion_probability * impact_multiplier * max_loss * position_size * entry_price
        
            can_survive = explosion_probability < 0.5 and expected_loss < (entry_price * 0.03)
        
            return FailureScenario(
                failure_mode=FailureMode.VOLATILITY_EXPLOSION,
                description="Volatility explodes, stop loss hit immediately",
                probability=explosion_probability,
                impact_multiplier=impact_multiplier,
                expected_loss=expected_loss,
                can_survive=can_survive,
                mitigation="Widen stop loss or reduce size" if not can_survive else None
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class ExecutionStressTester:
    """
    Stress tests execution under worst-case conditions.
    
    Assumes:
    - Worst possible fill price
    - Maximum slippage
    - Partial fills
    - Stop hunts
    """
    
    def stress_test_entry(
        self,
        signal: Dict,
        market_context: Dict
    ) -> ExecutionStressTest:
        """Stress test entry execution"""
        try:
            entry_price = signal['price']
            direction = signal['direction']
        
            # Estimate spread
            spread_bps = market_context.get('spread_bps', 10.0)
        
            # Worst case: pay full spread + additional slippage
            additional_slippage_bps = 20.0  # Assume 20 bps additional slippage
            total_slippage_bps = spread_bps + additional_slippage_bps
        
            if direction == 'long':
                worst_case_fill = entry_price * (1 + total_slippage_bps / 10000)
            else:
                worst_case_fill = entry_price * (1 - total_slippage_bps / 10000)
        
            # Partial fill probability
            liquidity_score = market_context.get('liquidity_score', 0.5)
            partial_fill_prob = 1.0 - liquidity_score
        
            # Expected execution cost
            expected_cost = (total_slippage_bps / 10000) * entry_price * signal.get('quantity', 1.0)
        
            # Passes stress test if cost is acceptable
            passes = total_slippage_bps < 50.0 and partial_fill_prob < 0.3
        
            return ExecutionStressTest(
                scenario="Entry Execution",
                assumed_fill_price=entry_price,
                worst_case_fill_price=worst_case_fill,
                slippage_bps=total_slippage_bps,
                partial_fill_probability=partial_fill_prob,
                expected_execution_cost=expected_cost,
                passes_stress_test=passes
            )
        except Exception as e:
            logger.error(f"Error in stress_test_entry: {e}")
            raise
    
    def stress_test_stop_loss(
        self,
        signal: Dict,
        market_context: Dict
    ) -> ExecutionStressTest:
        """Stress test stop loss execution"""
        try:
            stop_loss = signal.get('stop_loss')
            if not stop_loss:
                return ExecutionStressTest(
                    scenario="Stop Loss Execution",
                    assumed_fill_price=0,
                    worst_case_fill_price=0,
                    slippage_bps=0,
                    partial_fill_probability=0,
                    expected_execution_cost=0,
                    passes_stress_test=False
                )
        
            direction = signal['direction']
        
            # Stop loss slippage is MUCH worse
            # Market orders in panic = terrible fills
            stop_slippage_bps = 100.0  # Assume 100 bps slippage on stop
        
            if direction == 'long':
                # Stop is below entry, slippage makes it worse
                worst_case_fill = stop_loss * (1 - stop_slippage_bps / 10000)
            else:
                # Stop is above entry, slippage makes it worse
                worst_case_fill = stop_loss * (1 + stop_slippage_bps / 10000)
        
            # Partial fills on stops are dangerous
            partial_fill_prob = 0.5  # Assume 50% chance of partial fill
        
            expected_cost = (stop_slippage_bps / 10000) * stop_loss * signal.get('quantity', 1.0)
        
            # Passes if slippage is acceptable
            passes = stop_slippage_bps < 150.0
        
            return ExecutionStressTest(
                scenario="Stop Loss Execution",
                assumed_fill_price=stop_loss,
                worst_case_fill_price=worst_case_fill,
                slippage_bps=stop_slippage_bps,
                partial_fill_probability=partial_fill_prob,
                expected_execution_cost=expected_cost,
                passes_stress_test=passes
            )
        except Exception as e:
            logger.error(f"Error in stress_test_stop_loss: {e}")
            raise
    
    def stress_test_take_profit(
        self,
        signal: Dict,
        market_context: Dict
    ) -> ExecutionStressTest:
        """Stress test take profit execution"""
        try:
            take_profit = signal.get('take_profit')
            if not take_profit:
                return ExecutionStressTest(
                    scenario="Take Profit Execution",
                    assumed_fill_price=0,
                    worst_case_fill_price=0,
                    slippage_bps=0,
                    partial_fill_probability=0,
                    expected_execution_cost=0,
                    passes_stress_test=True  # No TP = no risk
                )
        
            direction = signal['direction']
        
            # Take profit slippage
            tp_slippage_bps = 30.0
        
            if direction == 'long':
                # TP is above entry, slippage reduces profit
                worst_case_fill = take_profit * (1 - tp_slippage_bps / 10000)
            else:
                # TP is below entry, slippage reduces profit
                worst_case_fill = take_profit * (1 + tp_slippage_bps / 10000)
        
            partial_fill_prob = 0.3
        
            expected_cost = (tp_slippage_bps / 10000) * take_profit * signal.get('quantity', 1.0)
        
            passes = tp_slippage_bps < 50.0
        
            return ExecutionStressTest(
                scenario="Take Profit Execution",
                assumed_fill_price=take_profit,
                worst_case_fill_price=worst_case_fill,
                slippage_bps=tp_slippage_bps,
                partial_fill_probability=partial_fill_prob,
                expected_execution_cost=expected_cost,
                passes_stress_test=passes
            )
        except Exception as e:
            logger.error(f"Error in stress_test_take_profit: {e}")
            raise


class AdversarialFailureAnalyzer:
    """
    Main adversarial analyzer that tries to BREAK signals.
    
    This module is HOSTILE and assumes the worst.
    """
    
    def __init__(self):
        try:
            self.regime_analyzer = RegimeShiftAnalyzer()
            self.liquidity_analyzer = LiquidityVacuumAnalyzer()
            self.correlation_analyzer = CorrelationSpikeAnalyzer()
            self.volatility_analyzer = VolatilityExplosionAnalyzer()
            self.execution_tester = ExecutionStressTester()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(
        self,
        signal: Dict,
        market_context: Dict
    ) -> AdversarialAnalysis:
        """
        Perform complete adversarial analysis.
        
        Tries to find ways the signal will FAIL.
        """
        # Analyze failure scenarios
        try:
            failure_scenarios = [
                self.regime_analyzer.analyze(signal, market_context),
                self.liquidity_analyzer.analyze(signal, market_context),
                self.correlation_analyzer.analyze(signal, market_context),
                self.volatility_analyzer.analyze(signal, market_context)
            ]
        
            # Identify catastrophic scenarios
            catastrophic = [
                scenario for scenario in failure_scenarios
                if not scenario.can_survive
            ]
        
            # Stress test execution
            execution_tests = [
                self.execution_tester.stress_test_entry(signal, market_context),
                self.execution_tester.stress_test_stop_loss(signal, market_context),
                self.execution_tester.stress_test_take_profit(signal, market_context)
            ]
        
            # Calculate worst case execution cost
            worst_case_cost = sum(test.expected_execution_cost for test in execution_tests)
        
            # Overall assessment
            survives = (
                len(catastrophic) == 0 and
                all(test.passes_stress_test for test in execution_tests)
            )
        
            # Dominant failure risk
            if failure_scenarios:
                dominant = max(failure_scenarios, key=lambda s: s.expected_loss)
                dominant_mode = dominant.failure_mode
            else:
                dominant_mode = None
        
            # Expected worst case loss
            total_expected_loss = sum(s.expected_loss for s in failure_scenarios)
        
            analysis = AdversarialAnalysis(
                signal_id=signal.get('signal_id', 'unknown'),
                symbol=signal['symbol'],
                failure_scenarios=failure_scenarios,
                catastrophic_scenarios=catastrophic,
                execution_tests=execution_tests,
                worst_case_execution_cost=worst_case_cost,
                survives_adversarial_analysis=survives,
                dominant_failure_risk=dominant_mode,
                expected_worst_case_loss=total_expected_loss,
                timestamp=datetime.utcnow()
            )
        
            # Log if doesn't survive
            if not survives:
                logger.warning(
                    f"Signal {signal.get('signal_id')} FAILS adversarial analysis:\n"
                    f"  Catastrophic scenarios: {len(catastrophic)}\n"
                    f"  Failed execution tests: {sum(1 for t in execution_tests if not t.passes_stress_test)}\n"
                    f"  Expected worst case loss: ${total_expected_loss:.2f}\n"
                    f"  Dominant risk: {dominant_mode.value if dominant_mode else 'None'}"
                )
        
            return analysis
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


# Global singleton
_global_analyzer: Optional[AdversarialFailureAnalyzer] = None


def get_global_analyzer() -> AdversarialFailureAnalyzer:
    """Get global analyzer singleton"""
    try:
        global _global_analyzer
        if _global_analyzer is None:
            _global_analyzer = AdversarialFailureAnalyzer()
        return _global_analyzer
    except Exception as e:
        logger.error(f"Error in get_global_analyzer: {e}")
        raise


def analyze_signal(
    signal: Dict,
    market_context: Dict
) -> AdversarialAnalysis:
    """Analyze signal using global analyzer"""
    return get_global_analyzer().analyze(signal, market_context)
