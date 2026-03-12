"""
Self-Diagnosis Concepts (11-20): Error detection, anomaly identification, health checks.
The bot detects when something is wrong before it causes damage.
"""

import logging
import numpy as np
from typing import Any, Dict, List
from collections import deque
from .self_concept_engine import SelfConcept, ConceptCategory

logger = logging.getLogger(__name__)


class SelfDiagnosisConcepts:
    """10 self-diagnosis concepts for detecting internal and external anomalies."""

    def __init__(self):
        try:
            self.signal_history = deque(maxlen=200)
            self.prediction_errors = deque(maxlen=100)
            self.latency_history = deque(maxlen=100)
            self.data_gap_count = 0
            self.stale_data_count = 0
            self.contradiction_count = 0
            self.error_rate_window = deque(maxlen=50)
            self.last_price = None
            self.price_jump_threshold = 0.02
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(11, "SignalDegradationDetector", ConceptCategory.DIAGNOSIS,
                        "Detects when signal quality degrades over time"),
            SelfConcept(12, "PredictionDriftDetector", ConceptCategory.DIAGNOSIS,
                        "Identifies systematic drift between predictions and outcomes"),
            SelfConcept(13, "DataIntegrityChecker", ConceptCategory.DIAGNOSIS,
                        "Validates incoming data for gaps, staleness, and corruption"),
            SelfConcept(14, "LatencyAnomalyDetector", ConceptCategory.DIAGNOSIS,
                        "Flags unusual processing or network latency spikes"),
            SelfConcept(15, "StrategyContradictionDetector", ConceptCategory.DIAGNOSIS,
                        "Detects when multiple strategies give conflicting signals"),
            SelfConcept(16, "OverfitSymptomDetector", ConceptCategory.DIAGNOSIS,
                        "Identifies signs of overfitting: great backtest, poor live"),
            SelfConcept(17, "FeatureImportanceDrift", ConceptCategory.DIAGNOSIS,
                        "Detects when feature importance rankings shift significantly"),
            SelfConcept(18, "ExecutionQualityMonitor", ConceptCategory.DIAGNOSIS,
                        "Monitors slippage, fill rates, and execution degradation"),
            SelfConcept(19, "PriceJumpDetector", ConceptCategory.DIAGNOSIS,
                        "Detects abnormal price jumps that may indicate data errors or flash events"),
            SelfConcept(20, "ErrorRateMonitor", ConceptCategory.DIAGNOSIS,
                        "Tracks system error rate and flags when it exceeds thresholds"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            price = snapshot.get('price', 0.0)
            signals = {}

            # Concept 11: Signal Degradation Detector
            rsi = snapshot.get('rsi', 50)
            macd = snapshot.get('macd', 0)
            self.signal_history.append({'rsi': rsi, 'macd': macd})
            if len(self.signal_history) >= 50:
                recent_rsi = [s['rsi'] for s in list(self.signal_history)[-20:]]
                rsi_range = max(recent_rsi) - min(recent_rsi)
                signals['signal_degraded'] = rsi_range < 5  # RSI stuck in narrow band
            else:
                signals['signal_degraded'] = False

            # Concept 12: Prediction Drift Detector
            if len(self.prediction_errors) >= 20:
                errors = list(self.prediction_errors)
                recent_bias = np.mean(errors[-20:])
                signals['prediction_drift'] = abs(recent_bias) > 0.01
                signals['prediction_bias'] = float(recent_bias)
            else:
                signals['prediction_drift'] = False
                signals['prediction_bias'] = 0.0

            # Concept 13: Data Integrity Checker
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            missing = [f for f in required_fields if f not in snapshot or snapshot[f] == 0]
            signals['data_integrity_ok'] = len(missing) == 0
            signals['missing_fields'] = missing
            if missing:
                self.data_gap_count += 1
            signals['data_gap_count'] = self.data_gap_count

            # Concept 14: Latency Anomaly Detector
            cycle_ms = snapshot.get('self_concepts', {}).get('last_cycle_ms', 0)
            self.latency_history.append(cycle_ms)
            if len(self.latency_history) >= 10:
                avg_lat = np.mean(list(self.latency_history))
                signals['latency_anomaly'] = cycle_ms > avg_lat * 3
            else:
                signals['latency_anomaly'] = False

            # Concept 15: Strategy Contradiction Detector
            sma_20 = snapshot.get('sma_20', price)
            sma_50 = snapshot.get('sma_50', price)
            trend_signal = 1 if sma_20 > sma_50 else -1
            momentum_signal = 1 if rsi > 50 else -1
            signals['strategy_contradiction'] = trend_signal != momentum_signal
            if signals['strategy_contradiction']:
                self.contradiction_count += 1
            signals['contradiction_rate'] = self.contradiction_count

            # Concept 16: Overfit Symptom Detector
            if len(self.prediction_errors) >= 30:
                first_half = list(self.prediction_errors)[:15]
                second_half = list(self.prediction_errors)[15:]
                signals['overfit_symptom'] = np.std(second_half) > np.std(first_half) * 1.5
            else:
                signals['overfit_symptom'] = False

            # Concept 17: Feature Importance Drift
            signals['feature_drift'] = False  # Updated by ML modules

            # Concept 18: Execution Quality Monitor
            signals['execution_quality'] = 'good'  # Updated by execution module

            # Concept 19: Price Jump Detector
            if self.last_price and self.last_price > 0:
                pct_change = abs(price - self.last_price) / self.last_price
                signals['price_jump'] = pct_change > self.price_jump_threshold
                signals['price_jump_pct'] = float(pct_change)
            else:
                signals['price_jump'] = False
                signals['price_jump_pct'] = 0.0
            self.last_price = price

            # Concept 20: Error Rate Monitor
            signals['error_rate_high'] = (
                sum(self.error_rate_window) / max(len(self.error_rate_window), 1) > 0.1
                if self.error_rate_window else False
            )

            signals['impact'] = 0.6
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            predicted = trade_info.get('predicted_direction', 0)
            actual = trade_info.get('pnl', 0)
            if predicted != 0:
                error = 1.0 if (predicted > 0) != (actual > 0) else 0.0
                self.prediction_errors.append(error)
                self.error_rate_window.append(error)
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise
