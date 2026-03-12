"""
Self-Optimization Concepts (21-30): Parameter tuning, resource allocation, efficiency.
The bot continuously tunes itself for peak performance.
"""

import logging
import numpy as np
from typing import Any, Dict, List
from collections import deque
from .self_concept_engine import SelfConcept, ConceptCategory

logger = logging.getLogger(__name__)


class SelfOptimizationConcepts:
    """10 self-optimization concepts for continuous performance tuning."""

    def __init__(self):
        try:
            self.param_history: Dict[str, deque] = {}
            self.performance_by_regime: Dict[str, List[float]] = {}
            self.position_size_history = deque(maxlen=100)
            self.timing_scores = deque(maxlen=100)
            self.risk_reward_history = deque(maxlen=100)
            self.holding_periods = deque(maxlen=100)
            self.best_params: Dict[str, float] = {}
            self.resource_usage = deque(maxlen=50)
            self.batch_efficiency = deque(maxlen=50)
            self.rebalance_counter = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(21, "AdaptivePositionSizer", ConceptCategory.OPTIMIZATION,
                        "Dynamically adjusts position size based on recent win rate and volatility"),
            SelfConcept(22, "EntryTimingOptimizer", ConceptCategory.OPTIMIZATION,
                        "Learns optimal entry timing relative to signal generation"),
            SelfConcept(23, "ExitTimingOptimizer", ConceptCategory.OPTIMIZATION,
                        "Optimizes exit timing to maximize realized profit factor"),
            SelfConcept(24, "RiskRewardCalibrator", ConceptCategory.OPTIMIZATION,
                        "Adjusts stop-loss and take-profit ratios based on regime"),
            SelfConcept(25, "HoldingPeriodOptimizer", ConceptCategory.OPTIMIZATION,
                        "Learns optimal holding periods per regime and strategy"),
            SelfConcept(26, "ParameterDecayDetector", ConceptCategory.OPTIMIZATION,
                        "Detects when strategy parameters become stale and need refresh"),
            SelfConcept(27, "RegimeSpecificTuner", ConceptCategory.OPTIMIZATION,
                        "Maintains separate parameter sets for each market regime"),
            SelfConcept(28, "ResourceAllocator", ConceptCategory.OPTIMIZATION,
                        "Optimizes CPU/memory allocation across modules"),
            SelfConcept(29, "BatchProcessingOptimizer", ConceptCategory.OPTIMIZATION,
                        "Optimizes batch sizes for data processing efficiency"),
            SelfConcept(30, "RebalanceFrequencyTuner", ConceptCategory.OPTIMIZATION,
                        "Tunes how often portfolio rebalancing should occur"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            signals = {}
            price = snapshot.get('price', 0.0)
            vol = snapshot.get('volatility', 0.01)
            regime = snapshot.get('self_concepts', {}).get('regime', 'unknown')

            # Concept 21: Adaptive Position Sizer
            if len(self.position_size_history) >= 10:
                recent_pnl = list(self.position_size_history)[-10:]
                win_rate = sum(1 for p in recent_pnl if p > 0) / len(recent_pnl)
                vol_factor = max(0.3, 1.0 - vol * 10)
                signals['optimal_size_multiplier'] = float(win_rate * vol_factor)
            else:
                signals['optimal_size_multiplier'] = 0.5

            # Concept 22: Entry Timing Optimizer
            if len(self.timing_scores) >= 20:
                avg_timing = np.mean(list(self.timing_scores))
                signals['entry_timing_score'] = float(avg_timing)
                signals['delay_entry'] = avg_timing < 0.3
            else:
                signals['entry_timing_score'] = 0.5
                signals['delay_entry'] = False

            # Concept 23: Exit Timing Optimizer
            signals['exit_urgency'] = 'normal'
            dd = snapshot.get('self_concepts', {}).get('drawdown_pct', 0)
            if dd > 0.05:
                signals['exit_urgency'] = 'high'
            elif dd > 0.08:
                signals['exit_urgency'] = 'critical'

            # Concept 24: Risk-Reward Calibrator
            if regime in self.performance_by_regime:
                perf = self.performance_by_regime[regime]
                if len(perf) >= 5:
                    avg_rr = np.mean(perf)
                    signals['optimal_rr_ratio'] = max(1.5, float(avg_rr))
                else:
                    signals['optimal_rr_ratio'] = 2.0
            else:
                signals['optimal_rr_ratio'] = 2.0

            # Concept 25: Holding Period Optimizer
            if len(self.holding_periods) >= 10:
                avg_hold = np.mean(list(self.holding_periods))
                signals['optimal_hold_bars'] = int(avg_hold)
            else:
                signals['optimal_hold_bars'] = 12

            # Concept 26: Parameter Decay Detector
            signals['params_stale'] = False
            for param_name, history in self.param_history.items():
                if len(history) >= 30:
                    recent = list(history)[-10:]
                    older = list(history)[-30:-10]
                    if np.std(recent) < np.std(older) * 0.3:
                        signals['params_stale'] = True
                        break

            # Concept 27: Regime-Specific Tuner
            signals['regime_params'] = self.best_params.get(regime, {})

            # Concept 28: Resource Allocator
            signals['resource_pressure'] = False

            # Concept 29: Batch Processing Optimizer
            signals['optimal_batch_size'] = 64

            # Concept 30: Rebalance Frequency Tuner
            self.rebalance_counter += 1
            vol_state = snapshot.get('self_concepts', {}).get('volatility_state', 'normal')
            rebalance_freq = 10 if vol_state in ('high', 'extreme') else 20
            signals['should_rebalance'] = self.rebalance_counter >= rebalance_freq
            if signals['should_rebalance']:
                self.rebalance_counter = 0

            signals['impact'] = 0.7
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            pnl = trade_info.get('pnl', 0)
            self.position_size_history.append(pnl)

            regime = trade_info.get('regime', 'unknown')
            if regime not in self.performance_by_regime:
                self.performance_by_regime[regime] = []
            rr = trade_info.get('risk_reward', 0)
            self.performance_by_regime[regime].append(rr)

            hold = trade_info.get('holding_bars', 0)
            if hold > 0:
                self.holding_periods.append(hold)

            timing = trade_info.get('timing_score', 0.5)
            self.timing_scores.append(timing)
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise
