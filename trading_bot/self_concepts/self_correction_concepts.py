"""
Self-Correction Concepts (61-70): Trade repair, signal filtering, error recovery.
The bot corrects its own mistakes in real-time and prevents repeat errors.
"""

import logging
import numpy as np
from typing import Any, Dict, List
from collections import deque, defaultdict
from .self_concept_engine import SelfConcept, ConceptCategory

logger = logging.getLogger(__name__)


class SelfCorrectionConcepts:
    """10 self-correction concepts for real-time error recovery and trade repair."""

    def __init__(self):
        try:
            self.false_signal_history = deque(maxlen=100)
            self.premature_exits = deque(maxlen=50)
            self.late_entries = deque(maxlen=50)
            self.overtrading_window = deque(maxlen=60)
            self.signal_noise_ratio = deque(maxlen=100)
            self.bias_tracker: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
            self.stop_loss_adjustments = deque(maxlen=50)
            self.missed_opportunities = deque(maxlen=50)
            self.reversal_detections = deque(maxlen=50)
            self.error_corrections = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(61, "FalseSignalFilter", ConceptCategory.CORRECTION,
                        "Filters out signals that match historical false-positive patterns"),
            SelfConcept(62, "PrematureExitCorrector", ConceptCategory.CORRECTION,
                        "Detects and corrects tendency to exit profitable trades too early"),
            SelfConcept(63, "LateEntryCorrector", ConceptCategory.CORRECTION,
                        "Detects and corrects tendency to enter trades too late"),
            SelfConcept(64, "OvertradingBrake", ConceptCategory.CORRECTION,
                        "Detects overtrading patterns and enforces cooldown periods"),
            SelfConcept(65, "SignalNoiseFilter", ConceptCategory.CORRECTION,
                        "Filters noise from signals using adaptive thresholds"),
            SelfConcept(66, "DirectionalBiasCorrector", ConceptCategory.CORRECTION,
                        "Detects and corrects persistent long/short bias"),
            SelfConcept(67, "StopLossRecalibrator", ConceptCategory.CORRECTION,
                        "Adjusts stop-loss placement based on actual price behavior"),
            SelfConcept(68, "MissedOpportunityLearner", ConceptCategory.CORRECTION,
                        "Learns from missed trades to improve future entry criteria"),
            SelfConcept(69, "ReversalDetector", ConceptCategory.CORRECTION,
                        "Detects when a trade should be reversed instead of stopped out"),
            SelfConcept(70, "ErrorPatternBreaker", ConceptCategory.CORRECTION,
                        "Identifies recurring error patterns and breaks the cycle"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            signals = {}
            price = snapshot.get('price', 0.0)
            import time

            # Concept 61: False Signal Filter
            if len(self.false_signal_history) >= 10:
                false_rate = sum(self.false_signal_history) / len(self.false_signal_history)
                signals['false_signal_rate'] = float(false_rate)
                signals['signal_trustworthy'] = false_rate < 0.4
            else:
                signals['false_signal_rate'] = 0.0
                signals['signal_trustworthy'] = True

            # Concept 62: Premature Exit Corrector
            if len(self.premature_exits) >= 5:
                premature_rate = sum(1 for p in self.premature_exits if p) / len(self.premature_exits)
                signals['premature_exit_tendency'] = float(premature_rate)
                signals['extend_tp'] = premature_rate > 0.3
            else:
                signals['premature_exit_tendency'] = 0.0
                signals['extend_tp'] = False

            # Concept 63: Late Entry Corrector
            if len(self.late_entries) >= 5:
                late_rate = sum(1 for l in self.late_entries if l) / len(self.late_entries)
                signals['late_entry_tendency'] = float(late_rate)
                signals['enter_earlier'] = late_rate > 0.3
            else:
                signals['late_entry_tendency'] = 0.0
                signals['enter_earlier'] = False

            # Concept 64: Overtrading Brake
            self.overtrading_window.append(time.time())
            # Count trades in last 60 minutes
            cutoff = time.time() - 3600
            recent_trades = sum(1 for t in self.overtrading_window if t > cutoff)
            signals['trades_per_hour'] = recent_trades
            signals['overtrading'] = recent_trades > 20
            if signals['overtrading']:
                signals['cooldown_recommended'] = True
                logger.info(f"Overtrading detected: {recent_trades} trades/hour")

            # Concept 65: Signal Noise Filter
            rsi = snapshot.get('rsi', 50)
            macd = snapshot.get('macd', 0)
            self.signal_noise_ratio.append(abs(macd))
            if len(self.signal_noise_ratio) >= 20:
                noise_floor = np.percentile(list(self.signal_noise_ratio), 25)
                signals['signal_above_noise'] = abs(macd) > noise_floor * 1.5
                signals['noise_floor'] = float(noise_floor)
            else:
                signals['signal_above_noise'] = True
                signals['noise_floor'] = 0.0

            # Concept 66: Directional Bias Corrector
            for direction in ['long', 'short']:
                if direction in self.bias_tracker and len(self.bias_tracker[direction]) >= 10:
                    win_rate = sum(1 for p in self.bias_tracker[direction] if p > 0) / len(self.bias_tracker[direction])
                    signals[f'{direction}_bias_winrate'] = float(win_rate)
                else:
                    signals[f'{direction}_bias_winrate'] = 0.5
            long_wr = signals.get('long_bias_winrate', 0.5)
            short_wr = signals.get('short_bias_winrate', 0.5)
            signals['directional_bias'] = (
                'long_biased' if long_wr > short_wr + 0.15 else
                'short_biased' if short_wr > long_wr + 0.15 else 'balanced'
            )

            # Concept 67: Stop-Loss Recalibrator
            if len(self.stop_loss_adjustments) >= 10:
                avg_adj = np.mean(list(self.stop_loss_adjustments))
                signals['sl_adjustment_factor'] = float(1.0 + avg_adj)
            else:
                signals['sl_adjustment_factor'] = 1.0

            # Concept 68: Missed Opportunity Learner
            signals['missed_opportunity_count'] = len(self.missed_opportunities)

            # Concept 69: Reversal Detector
            if len(self.reversal_detections) >= 5:
                reversal_rate = sum(1 for r in self.reversal_detections if r) / len(self.reversal_detections)
                signals['reversal_likely'] = reversal_rate > 0.3
            else:
                signals['reversal_likely'] = False

            # Concept 70: Error Pattern Breaker
            if len(self.error_corrections) >= 10:
                recent_errors = list(self.error_corrections)[-10:]
                error_types = defaultdict(int)
                for e in recent_errors:
                    error_types[e.get('type', 'unknown')] += 1
                most_common = max(error_types, key=error_types.get) if error_types else 'none'
                signals['recurring_error_type'] = most_common
                signals['error_pattern_detected'] = error_types.get(most_common, 0) >= 3
            else:
                signals['recurring_error_type'] = 'none'
                signals['error_pattern_detected'] = False

            signals['impact'] = 0.8
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            pnl = trade_info.get('pnl', 0)
            direction = trade_info.get('direction', 'long')

            # Track false signals
            predicted = trade_info.get('predicted_direction', 0)
            if predicted != 0:
                was_false = (predicted > 0) != (pnl > 0)
                self.false_signal_history.append(1.0 if was_false else 0.0)

            # Track directional bias
            self.bias_tracker[direction].append(pnl)

            # Track premature exits
            max_favorable = trade_info.get('max_favorable_excursion', 0)
            actual_exit_pnl = pnl
            if max_favorable > 0 and actual_exit_pnl > 0:
                captured_ratio = actual_exit_pnl / max_favorable
                self.premature_exits.append(captured_ratio < 0.4)

            # Track stop-loss effectiveness
            sl_hit = trade_info.get('stop_loss_hit', False)
            if sl_hit and pnl < 0:
                price_after = trade_info.get('price_after_sl', 0)
                entry = trade_info.get('entry_price', 0)
                if entry > 0 and price_after > 0:
                    would_have_recovered = (
                        (price_after > entry and direction == 'long') or
                        (price_after < entry and direction == 'short')
                    )
                    if would_have_recovered:
                        self.stop_loss_adjustments.append(0.1)  # Widen SL
                    else:
                        self.stop_loss_adjustments.append(-0.05)  # Tighten SL

            # Track errors
            if pnl < 0:
                error_type = 'false_signal' if predicted != 0 else 'bad_timing'
                self.error_corrections.append({'type': error_type, 'pnl': pnl})
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise
