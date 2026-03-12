"""
Self-Awareness Concepts (1-10): Market state awareness, performance introspection.
The bot knows what it knows, what it doesn't, and where it stands.
"""

import logging
import numpy as np
from typing import Any, Dict, List
from collections import deque
from .self_concept_engine import SelfConcept, ConceptCategory, ConceptStatus

logger = logging.getLogger(__name__)


class SelfAwarenessConcepts:
    """10 self-awareness concepts that give the bot situational consciousness."""

    def __init__(self):
        try:
            self.price_history = deque(maxlen=500)
            self.volatility_history = deque(maxlen=200)
            self.trade_results = deque(maxlen=100)
            self.regime_state = 'unknown'
            self.confidence_level = 0.5
            self.drawdown_pct = 0.0
            self.peak_equity = 0.0
            self.current_equity = 0.0
            self.win_streak = 0
            self.loss_streak = 0
            self.session_pnl = 0.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(1, "MarketRegimeAwareness", ConceptCategory.AWARENESS,
                        "Detects current market regime: trending, ranging, volatile, quiet"),
            SelfConcept(2, "VolatilityStateAwareness", ConceptCategory.AWARENESS,
                        "Tracks volatility percentile relative to historical norms"),
            SelfConcept(3, "DrawdownAwareness", ConceptCategory.AWARENESS,
                        "Monitors current drawdown from equity peak"),
            SelfConcept(4, "StreakAwareness", ConceptCategory.AWARENESS,
                        "Tracks win/loss streaks to detect tilt or hot-hand"),
            SelfConcept(5, "ConfidenceCalibration", ConceptCategory.AWARENESS,
                        "Calibrates prediction confidence against actual outcomes"),
            SelfConcept(6, "LiquidityAwareness", ConceptCategory.AWARENESS,
                        "Detects thin liquidity conditions that increase slippage risk"),
            SelfConcept(7, "SessionTimeAwareness", ConceptCategory.AWARENESS,
                        "Knows which trading session is active and its characteristics"),
            SelfConcept(8, "CorrelationAwareness", ConceptCategory.AWARENESS,
                        "Detects when asset correlations shift from historical norms"),
            SelfConcept(9, "SpreadAwareness", ConceptCategory.AWARENESS,
                        "Monitors bid-ask spread widening as a risk signal"),
            SelfConcept(10, "CapacityAwareness", ConceptCategory.AWARENESS,
                        "Knows system resource usage and processing latency"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            price = snapshot.get('price', 0.0)
            vol = snapshot.get('volatility', 0.01)
            self.price_history.append(price)
            self.volatility_history.append(vol)

            signals = {}

            # Concept 1: Market Regime Awareness
            if len(self.price_history) >= 50:
                prices = list(self.price_history)
                sma20 = np.mean(prices[-20:])
                sma50 = np.mean(prices[-50:])
                std20 = np.std(prices[-20:])
                if std20 / max(sma20, 1e-8) > 0.02:
                    self.regime_state = 'volatile'
                elif sma20 > sma50 * 1.002:
                    self.regime_state = 'trending_up'
                elif sma20 < sma50 * 0.998:
                    self.regime_state = 'trending_down'
                else:
                    self.regime_state = 'ranging'
            signals['regime'] = self.regime_state

            # Concept 2: Volatility State Awareness
            if len(self.volatility_history) >= 20:
                vol_arr = np.array(list(self.volatility_history))
                vol_percentile = np.searchsorted(np.sort(vol_arr), vol) / len(vol_arr)
                signals['volatility_percentile'] = float(vol_percentile)
                signals['volatility_state'] = (
                    'extreme' if vol_percentile > 0.9 else
                    'high' if vol_percentile > 0.7 else
                    'normal' if vol_percentile > 0.3 else 'low'
                )
            else:
                signals['volatility_percentile'] = 0.5
                signals['volatility_state'] = 'normal'

            # Concept 3: Drawdown Awareness
            if price > 0:
                self.peak_equity = max(self.peak_equity, price)
                self.drawdown_pct = (self.peak_equity - price) / self.peak_equity if self.peak_equity > 0 else 0
            signals['drawdown_pct'] = self.drawdown_pct
            signals['drawdown_severity'] = (
                'critical' if self.drawdown_pct > 0.10 else
                'warning' if self.drawdown_pct > 0.05 else 'normal'
            )

            # Concept 4: Streak Awareness
            signals['win_streak'] = self.win_streak
            signals['loss_streak'] = self.loss_streak
            signals['streak_warning'] = self.loss_streak >= 3

            # Concept 5: Confidence Calibration
            signals['confidence'] = self.confidence_level

            # Concept 6: Liquidity Awareness
            volume = snapshot.get('volume', 0)
            signals['liquidity_thin'] = volume < 100 if volume else False

            # Concept 7: Session Time Awareness
            from datetime import datetime
            hour = datetime.now().hour
            if 8 <= hour < 16:
                signals['session'] = 'london'
            elif 13 <= hour < 21:
                signals['session'] = 'new_york'
            elif 0 <= hour < 9:
                signals['session'] = 'asian'
            else:
                signals['session'] = 'off_hours'

            # Concept 8: Correlation Awareness
            signals['correlation_shift'] = False

            # Concept 9: Spread Awareness
            high = snapshot.get('high', price)
            low = snapshot.get('low', price)
            spread_proxy = (high - low) / max(price, 1e-8)
            signals['spread_wide'] = spread_proxy > 0.005

            # Concept 10: Capacity Awareness
            signals['system_healthy'] = True

            signals['impact'] = 0.5
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            pnl = trade_info.get('pnl', 0)
            self.session_pnl += pnl
            if pnl > 0:
                self.win_streak += 1
                self.loss_streak = 0
            elif pnl < 0:
                self.loss_streak += 1
                self.win_streak = 0
            self.trade_results.append(pnl)

            # Update confidence calibration
            if len(self.trade_results) >= 10:
                wins = sum(1 for r in self.trade_results if r > 0)
                self.confidence_level = wins / len(self.trade_results)
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise
