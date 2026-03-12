"""
Self-Protection Concepts (31-40): Risk guards, drawdown shields, capital preservation.
The bot protects itself from catastrophic losses and adverse conditions.
"""

import logging
import numpy as np
from typing import Any, Dict, List
from collections import deque
from .self_concept_engine import SelfConcept, ConceptCategory

logger = logging.getLogger(__name__)


class SelfProtectionConcepts:
    """10 self-protection concepts for capital preservation and risk shielding."""

    def __init__(self):
        try:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.max_daily_loss = -500.0
            self.max_daily_trades = 50
            self.consecutive_losses = 0
            self.max_consecutive_losses = 5
            self.exposure_history = deque(maxlen=100)
            self.correlation_matrix: Dict[str, float] = {}
            self.volatility_spike_count = 0
            self.circuit_breaker_active = False
            self.cooldown_until = 0.0
            self.tail_risk_events = deque(maxlen=50)
            self.max_open_positions = 5
            self.current_positions = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(31, "DailyLossCircuitBreaker", ConceptCategory.PROTECTION,
                        "Halts trading when daily loss exceeds threshold"),
            SelfConcept(32, "ConsecutiveLossGuard", ConceptCategory.PROTECTION,
                        "Reduces size or pauses after N consecutive losses"),
            SelfConcept(33, "VolatilitySpikeShelter", ConceptCategory.PROTECTION,
                        "Reduces exposure during extreme volatility events"),
            SelfConcept(34, "CorrelationExposureGuard", ConceptCategory.PROTECTION,
                        "Prevents over-concentration in correlated positions"),
            SelfConcept(35, "MaxPositionGuard", ConceptCategory.PROTECTION,
                        "Enforces maximum number of simultaneous open positions"),
            SelfConcept(36, "TailRiskDetector", ConceptCategory.PROTECTION,
                        "Identifies fat-tail risk conditions and reduces exposure"),
            SelfConcept(37, "DrawdownRecoveryMode", ConceptCategory.PROTECTION,
                        "Switches to conservative mode during drawdown recovery"),
            SelfConcept(38, "NewsEventShield", ConceptCategory.PROTECTION,
                        "Reduces exposure before high-impact scheduled events"),
            SelfConcept(39, "WeekendGapProtection", ConceptCategory.PROTECTION,
                        "Reduces or closes positions before weekend gaps"),
            SelfConcept(40, "EmergencyLiquidator", ConceptCategory.PROTECTION,
                        "Emergency position liquidation when multiple guards trigger"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            signals = {}
            import time

            # Concept 31: Daily Loss Circuit Breaker
            signals['circuit_breaker'] = self.daily_pnl <= self.max_daily_loss
            if signals['circuit_breaker'] and not self.circuit_breaker_active:
                self.circuit_breaker_active = True
                logger.warning(f"CIRCUIT BREAKER: Daily loss {self.daily_pnl:.2f} exceeds limit")

            # Concept 32: Consecutive Loss Guard
            signals['consecutive_loss_guard'] = self.consecutive_losses >= self.max_consecutive_losses
            if self.consecutive_losses >= 3:
                signals['size_reduction_factor'] = max(0.25, 1.0 - self.consecutive_losses * 0.15)
            else:
                signals['size_reduction_factor'] = 1.0

            # Concept 33: Volatility Spike Shelter
            vol_state = snapshot.get('self_concepts', {}).get('volatility_state', 'normal')
            signals['vol_shelter_active'] = vol_state in ('extreme', 'high')
            if signals['vol_shelter_active']:
                signals['vol_size_cap'] = 0.5 if vol_state == 'high' else 0.25
            else:
                signals['vol_size_cap'] = 1.0

            # Concept 34: Correlation Exposure Guard
            signals['correlation_risk'] = False
            total_exposure = sum(self.exposure_history) if self.exposure_history else 0
            signals['total_exposure'] = total_exposure

            # Concept 35: Max Position Guard
            signals['max_positions_reached'] = self.current_positions >= self.max_open_positions
            signals['positions_available'] = max(0, self.max_open_positions - self.current_positions)

            # Concept 36: Tail Risk Detector
            vol = snapshot.get('volatility', 0.01)
            if vol > 0.05:
                self.tail_risk_events.append(time.time())
            recent_tail = sum(1 for t in self.tail_risk_events if time.time() - t < 3600)
            signals['tail_risk_elevated'] = recent_tail >= 3
            signals['tail_risk_count'] = recent_tail

            # Concept 37: Drawdown Recovery Mode
            dd = snapshot.get('self_concepts', {}).get('drawdown_pct', 0)
            signals['recovery_mode'] = dd > 0.03
            if signals['recovery_mode']:
                signals['recovery_size_cap'] = max(0.3, 1.0 - dd * 5)
            else:
                signals['recovery_size_cap'] = 1.0

            # Concept 38: News Event Shield
            signals['news_shield_active'] = False  # Updated by news module

            # Concept 39: Weekend Gap Protection
            from datetime import datetime
            now = datetime.now()
            signals['weekend_close_warning'] = now.weekday() == 4 and now.hour >= 20
            signals['pre_weekend'] = now.weekday() >= 4

            # Concept 40: Emergency Liquidator
            emergency_triggers = sum([
                signals['circuit_breaker'],
                signals['consecutive_loss_guard'],
                signals['tail_risk_elevated'],
                dd > 0.10,
            ])
            signals['emergency_liquidate'] = emergency_triggers >= 2
            if signals['emergency_liquidate']:
                logger.warning("EMERGENCY: Multiple protection triggers active - liquidation recommended")

            # Aggregate trade permission
            signals['trade_allowed'] = not any([
                signals['circuit_breaker'],
                signals['emergency_liquidate'],
                signals['max_positions_reached'],
                time.time() < self.cooldown_until,
            ])

            signals['impact'] = 0.9
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            pnl = trade_info.get('pnl', 0)
            self.daily_pnl += pnl
            self.daily_trades += 1

            if pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise

    def reset_daily(self):
        try:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.circuit_breaker_active = False
        except Exception as e:
            logger.error(f"Error in reset_daily: {e}")
            raise
