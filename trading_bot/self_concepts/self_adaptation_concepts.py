"""
Self-Adaptation Concepts (51-60): Regime switching, dynamic recalibration, environment response.
The bot adapts its behavior to changing market conditions in real-time.
"""

import logging
import numpy as np
from typing import Any, Dict, List
from collections import deque, defaultdict
from .self_concept_engine import SelfConcept, ConceptCategory

logger = logging.getLogger(__name__)


class SelfAdaptationConcepts:
    """10 self-adaptation concepts for dynamic environment response."""

    def __init__(self):
        try:
            self.regime_history = deque(maxlen=200)
            self.strategy_weights: Dict[str, float] = defaultdict(lambda: 1.0)
            self.timeframe_performance: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
            self.indicator_weights: Dict[str, float] = defaultdict(lambda: 1.0)
            self.market_phase = 'neutral'
            self.adaptation_speed = 0.1
            self.stress_level = 0.0
            self.correlation_state: Dict[str, float] = {}
            self.seasonal_patterns: Dict[int, List[float]] = defaultdict(list)
            self.momentum_state = 0.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(51, "RegimeSwitchAdapter", ConceptCategory.ADAPTATION,
                        "Instantly switches strategy set when regime changes"),
            SelfConcept(52, "DynamicStrategyWeighting", ConceptCategory.ADAPTATION,
                        "Adjusts strategy weights based on recent performance per regime"),
            SelfConcept(53, "TimeframeAdaptation", ConceptCategory.ADAPTATION,
                        "Shifts analysis timeframe based on volatility conditions"),
            SelfConcept(54, "IndicatorReweighting", ConceptCategory.ADAPTATION,
                        "Dynamically reweights technical indicators by predictive power"),
            SelfConcept(55, "MarketPhaseDetector", ConceptCategory.ADAPTATION,
                        "Detects accumulation, distribution, markup, markdown phases"),
            SelfConcept(56, "AdaptationSpeedController", ConceptCategory.ADAPTATION,
                        "Controls how fast the bot adapts: fast in crisis, slow in calm"),
            SelfConcept(57, "StressResponseSystem", ConceptCategory.ADAPTATION,
                        "Activates defensive posture under market stress"),
            SelfConcept(58, "CorrelationRegimeAdapter", ConceptCategory.ADAPTATION,
                        "Adapts portfolio when correlation structure breaks down"),
            SelfConcept(59, "SeasonalPatternAdapter", ConceptCategory.ADAPTATION,
                        "Adjusts behavior based on time-of-day, day-of-week patterns"),
            SelfConcept(60, "MomentumRegimeAdapter", ConceptCategory.ADAPTATION,
                        "Switches between mean-reversion and momentum strategies"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            signals = {}
            price = snapshot.get('price', 0.0)
            vol = snapshot.get('volatility', 0.01)
            regime = snapshot.get('self_concepts', {}).get('regime', 'unknown')

            # Concept 51: Regime Switch Adapter
            self.regime_history.append(regime)
            regime_changed = (
                len(self.regime_history) >= 2 and
                self.regime_history[-1] != self.regime_history[-2]
            )
            signals['regime_changed'] = regime_changed
            if regime_changed:
                signals['new_regime'] = regime
                signals['old_regime'] = self.regime_history[-2]
                logger.info(f"Regime switch: {self.regime_history[-2]} -> {regime}")

            # Concept 52: Dynamic Strategy Weighting
            signals['strategy_weights'] = dict(self.strategy_weights)

            # Concept 53: Timeframe Adaptation
            vol_state = snapshot.get('self_concepts', {}).get('volatility_state', 'normal')
            if vol_state == 'extreme':
                signals['preferred_timeframe'] = 'M5'
            elif vol_state == 'high':
                signals['preferred_timeframe'] = 'M15'
            elif vol_state == 'low':
                signals['preferred_timeframe'] = 'H1'
            else:
                signals['preferred_timeframe'] = 'M30'

            # Concept 54: Indicator Reweighting
            signals['indicator_weights'] = dict(self.indicator_weights)

            # Concept 55: Market Phase Detector
            if len(self.regime_history) >= 20:
                recent = list(self.regime_history)[-20:]
                up_count = sum(1 for r in recent if 'up' in r)
                down_count = sum(1 for r in recent if 'down' in r)
                range_count = sum(1 for r in recent if r == 'ranging')
                if up_count > 12:
                    self.market_phase = 'markup'
                elif down_count > 12:
                    self.market_phase = 'markdown'
                elif range_count > 12 and vol < 0.01:
                    self.market_phase = 'accumulation'
                elif range_count > 12 and vol > 0.015:
                    self.market_phase = 'distribution'
                else:
                    self.market_phase = 'neutral'
            signals['market_phase'] = self.market_phase

            # Concept 56: Adaptation Speed Controller
            if vol_state in ('extreme', 'high'):
                self.adaptation_speed = min(0.5, self.adaptation_speed * 1.2)
            else:
                self.adaptation_speed = max(0.05, self.adaptation_speed * 0.95)
            signals['adaptation_speed'] = self.adaptation_speed

            # Concept 57: Stress Response System
            dd = snapshot.get('self_concepts', {}).get('drawdown_pct', 0)
            loss_streak = snapshot.get('self_concepts', {}).get('loss_streak', 0)
            self.stress_level = min(1.0, dd * 5 + loss_streak * 0.1 + (0.3 if vol_state == 'extreme' else 0))
            signals['stress_level'] = self.stress_level
            signals['stress_response'] = (
                'emergency' if self.stress_level > 0.8 else
                'defensive' if self.stress_level > 0.5 else
                'cautious' if self.stress_level > 0.3 else 'normal'
            )

            # Concept 58: Correlation Regime Adapter
            signals['correlation_breakdown'] = False  # Updated by correlation module

            # Concept 59: Seasonal Pattern Adapter
            from datetime import datetime
            hour = datetime.now().hour
            dow = datetime.now().weekday()
            if self.seasonal_patterns.get(hour):
                avg_perf = np.mean(self.seasonal_patterns[hour])
                signals['seasonal_bias'] = float(avg_perf)
            else:
                signals['seasonal_bias'] = 0.0
            signals['day_of_week'] = dow
            signals['hour_of_day'] = hour

            # Concept 60: Momentum Regime Adapter
            sma_20 = snapshot.get('sma_20', price)
            sma_50 = snapshot.get('sma_50', price)
            if sma_20 > 0 and sma_50 > 0:
                self.momentum_state = (sma_20 - sma_50) / sma_50
            signals['momentum_state'] = float(self.momentum_state)
            signals['prefer_momentum'] = abs(self.momentum_state) > 0.005
            signals['prefer_mean_reversion'] = abs(self.momentum_state) < 0.002

            signals['impact'] = 0.7
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            pnl = trade_info.get('pnl', 0)
            strategy = trade_info.get('strategy', 'default')

            # Update strategy weights
            current = self.strategy_weights[strategy]
            if pnl > 0:
                self.strategy_weights[strategy] = current * (1 + self.adaptation_speed)
            else:
                self.strategy_weights[strategy] = current * (1 - self.adaptation_speed * 0.5)
            # Normalize
            total = sum(self.strategy_weights.values())
            if total > 0:
                for k in self.strategy_weights:
                    self.strategy_weights[k] /= total

            # Update seasonal patterns
            from datetime import datetime
            hour = datetime.now().hour
            self.seasonal_patterns[hour].append(pnl)
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise
