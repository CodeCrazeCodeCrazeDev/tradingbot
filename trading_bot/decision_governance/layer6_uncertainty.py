"""
Layer 6: Uncertainty and Calibration Layer

Non-negotiable calibration system.
Outputs:
- confidence
- calibration quality
- abstention probability
- uncertainty decomposition
- confidence under distribution shift
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque
import logging
import math

from .core_types import (
    UncertaintyProfile, UncertaintyType, DecisionRecord, OutcomeRecord
)

logger = logging.getLogger(__name__)


class UncertaintyCalibrationLayer:
    """
    Calibrates uncertainty and determines when to abstain.
    Tracks prediction accuracy for calibration quality assessment.
    """
    
    def __init__(
        self,
        calibration_window: int = 100,
        abstention_threshold: float = 0.3,
        calibration_bins: int = 10
    ):
        self.calibration_window = calibration_window
        self.abstention_threshold = abstention_threshold
        self.calibration_bins = calibration_bins
        
        # History for calibration tracking
        self.prediction_history: deque = deque(maxlen=calibration_window)
        self.outcome_history: deque = deque(maxlen=calibration_window)
        
        # Brier score tracking
        self.brier_scores: deque = deque(maxlen=calibration_window)
        
    def compute_uncertainty_profile(
        self,
        base_confidence: float,
        evidence_coverage: float,
        adversarial_challenges: List[Any],
        regime_fit_score: float,
        robustness_score: float,
        distribution_shift_detected: bool = False
    ) -> UncertaintyProfile:
        """
        Compute comprehensive uncertainty profile.
        
        Args:
            base_confidence: Raw confidence from signal generator
            evidence_coverage: Evidence sufficiency score
            adversarial_challenges: List of challenges raised
            regime_fit_score: How well thesis fits current regime
            robustness_score: Counterfactual robustness
            distribution_shift_detected: Whether regime shift is detected
            
        Returns:
            UncertaintyProfile with full decomposition
        """
        # Decompose uncertainty by type
        decomposition = {}
        
        # Aleatoric uncertainty (inherent market randomness)
        decomposition[UncertaintyType.ALEATORIC] = self._estimate_aleatoric_uncertainty(
            regime_fit_score
        )
        
        # Epistemic uncertainty (lack of knowledge)
        decomposition[UncertaintyType.EPISTEMIC] = self._estimate_epistemic_uncertainty(
            evidence_coverage, adversarial_challenges
        )
        
        # Model uncertainty
        decomposition[UncertaintyType.MODEL] = self._estimate_model_uncertainty(
            base_confidence, robustness_score
        )
        
        # Regime uncertainty
        decomposition[UncertaintyType.REGIME] = self._estimate_regime_uncertainty(
            regime_fit_score
        )
        
        # Execution uncertainty
        decomposition[UncertaintyType.EXECUTION] = 0.15  # Base execution uncertainty
        
        # Calculate overall confidence with uncertainty penalty
        uncertainty_penalty = sum(decomposition.values()) / len(decomposition)
        adjusted_confidence = base_confidence * (1 - uncertainty_penalty)
        
        # Calculate calibration quality
        calibration_quality = self._calculate_calibration_quality()
        
        # Calculate abstention probability
        abstention_prob = self._calculate_abstention_probability(
            adjusted_confidence, decomposition, distribution_shift_detected
        )
        
        # Confidence under distribution shift
        confidence_under_shift = self._estimate_shift_confidence(
            adjusted_confidence, distribution_shift_detected
        )
        
        return UncertaintyProfile(
            overall_confidence=max(0.0, min(1.0, adjusted_confidence)),
            calibration_quality=calibration_quality,
            abstention_probability=abstention_prob,
            decomposition=decomposition,
            confidence_under_distribution_shift=confidence_under_shift
        )
    
    def _estimate_aleatoric_uncertainty(self, regime_fit_score: float) -> float:
        """
        Estimate inherent market uncertainty.
        Higher in volatile or unfamiliar regimes.
        """
        base_aleatoric = 0.2  # Markets are inherently noisy
        
        # Increase if regime fit is poor (unfamiliar territory)
        if regime_fit_score < 0.5:
            base_aleatoric += 0.15
        elif regime_fit_score < 0.7:
            base_aleatoric += 0.05
            
        return min(0.5, base_aleatoric)
    
    def _estimate_epistemic_uncertainty(
        self,
        evidence_coverage: float,
        adversarial_challenges: List[Any]
    ) -> float:
        """
        Estimate knowledge uncertainty.
        Higher when evidence is poor or challenges are strong.
        """
        base_epistemic = 0.3
        
        # Reduce with good evidence
        base_epistemic *= (1 - evidence_coverage)
        
        # Increase with strong adversarial challenges
        if adversarial_challenges:
            avg_challenge_severity = sum(
                getattr(c, 'severity', 0.5) for c in adversarial_challenges
            ) / len(adversarial_challenges)
            base_epistemic += avg_challenge_severity * 0.2
            
        return min(0.6, base_epistemic)
    
    def _estimate_model_uncertainty(
        self,
        base_confidence: float,
        robustness_score: float
    ) -> float:
        """
        Estimate model uncertainty.
        Higher when confidence is extreme or robustness is low.
        """
        # Overconfidence detection
        if base_confidence > 0.9 and robustness_score < 0.6:
            return 0.4  # High model uncertainty
        
        # Underconfidence detection  
        if base_confidence < 0.3:
            return 0.25
            
        # General model uncertainty
        return 0.15
    
    def _estimate_regime_uncertainty(self, regime_fit_score: float) -> float:
        """Estimate uncertainty due to regime mismatch"""
        return max(0.0, 1 - regime_fit_score) * 0.5
    
    def _calculate_calibration_quality(self) -> float:
        """
        Calculate calibration quality using reliability diagram approach.
        Returns score from 0 (poorly calibrated) to 1 (well calibrated).
        """
        if len(self.prediction_history) < 20:
            return 0.5  # Neutral if insufficient data
            
        # Bin predictions by confidence level
        bins = [[] for _ in range(self.calibration_bins)]
        
        for pred, outcome in zip(self.prediction_history, self.outcome_history):
            confidence = pred['confidence']
            bin_idx = min(int(confidence * self.calibration_bins), self.calibration_bins - 1)
            bins[bin_idx].append((confidence, outcome))
            
        # Calculate calibration error per bin
        total_calibration_error = 0.0
        total_weight = 0
        
        for bin_data in bins:
            if not bin_data:
                continue
                
            avg_confidence = sum(c for c, _ in bin_data) / len(bin_data)
            avg_outcome = sum(1 if o['success'] else 0 for _, o in bin_data) / len(bin_data)
            
            # Expected calibration error for this bin
            calibration_error = abs(avg_confidence - avg_outcome)
            total_calibration_error += calibration_error * len(bin_data)
            total_weight += len(bin_data)
            
        if total_weight == 0:
            return 0.5
            
        ece = total_calibration_error / total_weight
        
        # Convert to quality score (1 - normalized ECE)
        quality = max(0.0, 1 - (ece * 2))  # Scale so 0.5 ECE -> 0 quality
        
        return quality
    
    def _calculate_abstention_probability(
        self,
        adjusted_confidence: float,
        uncertainty_decomposition: Dict[UncertaintyType, float],
        distribution_shift: bool
    ) -> float:
        """
        Calculate probability that we should abstain from this decision.
        """
        # Base abstention from low confidence
        if adjusted_confidence < self.abstention_threshold:
            base_abstention = 0.8
        elif adjusted_confidence < 0.5:
            base_abstention = 0.4
        else:
            base_abstention = 0.1
            
        # Increase for high epistemic uncertainty
        epistemic = uncertainty_decomposition.get(UncertaintyType.EPISTEMIC, 0)
        if epistemic > 0.4:
            base_abstention += 0.2
            
        # Increase for distribution shift
        if distribution_shift:
            base_abstention += 0.3
            
        # Increase for poor calibration
        calibration = self._calculate_calibration_quality()
        if calibration < 0.3:
            base_abstention += 0.15
            
        return min(1.0, base_abstention)
    
    def _estimate_shift_confidence(
        self,
        base_confidence: float,
        distribution_shift: bool
    ) -> float:
        """Estimate confidence under distribution shift"""
        if distribution_shift:
            return base_confidence * 0.6  # Significant penalty for shift
        return base_confidence
    
    def record_prediction(
        self,
        confidence: float,
        prediction: Dict[str, Any]
    ) -> None:
        """Record a prediction for future calibration"""
        self.prediction_history.append({
            'timestamp': datetime.utcnow(),
            'confidence': confidence,
            'prediction': prediction
        })
    
    def record_outcome(
        self,
        outcome: OutcomeRecord
    ) -> None:
        """Record an outcome for calibration"""
        success = outcome.realized_pnl > 0 and outcome.calibration_error < 0.2
        
        self.outcome_history.append({
            'timestamp': outcome.timestamp,
            'success': success,
            'pnl': outcome.realized_pnl,
            'calibration_error': outcome.calibration_error
        })
        
        # Calculate Brier score if we have matching prediction
        if self.prediction_history:
            last_pred = self.prediction_history[-1]
            confidence = last_pred['confidence']
            outcome_prob = 1.0 if success else 0.0
            brier = (confidence - outcome_prob) ** 2
            self.brier_scores.append(brier)
    
    def get_calibration_metrics(self) -> Dict[str, float]:
        """Get current calibration metrics"""
        
        metrics = {
            'calibration_quality': self._calculate_calibration_quality(),
            'predictions_count': len(self.prediction_history),
            'outcomes_count': len(self.outcome_history)
        }
        
        if self.brier_scores:
            metrics['average_brier_score'] = sum(self.brier_scores) / len(self.brier_scores)
            metrics['brier_skill'] = 1 - (metrics['average_brier_score'] / 0.25)  # vs random
        else:
            metrics['average_brier_score'] = 0.25
            metrics['brier_skill'] = 0.0
            
        return metrics
    
    def should_abstain(self, uncertainty_profile: UncertaintyProfile) -> Tuple[bool, str]:
        """
        Determine if we should abstain from trading.
        
        Returns:
            Tuple of (should_abstain, reason)
        """
        if uncertainty_profile.abstention_probability > 0.7:
            return True, "High abstention probability due to excessive uncertainty"
            
        if uncertainty_profile.overall_confidence < self.abstention_threshold:
            return True, f"Confidence {uncertainty_profile.overall_confidence:.2f} below threshold {self.abstention_threshold}"
            
        if uncertainty_profile.calibration_quality < 0.2:
            return True, "Poor calibration quality - predictions unreliable"
            
        if uncertainty_profile.confidence_under_distribution_shift < 0.3:
            return True, "Distribution shift detected - confidence unreliable"
            
        # Check for excessive epistemic uncertainty
        epistemic = uncertainty_profile.decomposition.get(UncertaintyType.EPISTEMIC, 0)
        if epistemic > 0.5:
            return True, f"Excessive epistemic uncertainty ({epistemic:.2f})"
            
        return False, "Uncertainty within acceptable bounds"
    
    def generate_uncertainty_report(
        self,
        uncertainty_profile: UncertaintyProfile
    ) -> Dict[str, Any]:
        """Generate detailed uncertainty report"""
        
        should_abstain, abstain_reason = self.should_abstain(uncertainty_profile)
        
        # Identify dominant uncertainty type
        dominant_type = max(
            uncertainty_profile.decomposition,
            key=lambda k: uncertainty_profile.decomposition[k]
        )
        
        return {
            'overall_confidence': uncertainty_profile.overall_confidence,
            'calibration_quality': uncertainty_profile.calibration_quality,
            'abstention_probability': uncertainty_profile.abstention_probability,
            'should_abstain': should_abstain,
            'abstain_reason': abstain_reason,
            'dominant_uncertainty': dominant_type.value,
            'uncertainty_breakdown': {
                k.value: round(v, 3) for k, v in uncertainty_profile.decomposition.items()
            },
            'confidence_under_shift': uncertainty_profile.confidence_under_distribution_shift,
            'recommendation': 'ABSTAIN' if should_abstain else 'PROCEED_WITH_CAUTION'
        }


class ConfidenceCalibrationEngine:
    """
    Confidence Calibration Engine
    
    Your confidence is probably fake.
    
    Track:
    - Predicted confidence vs actual outcome
    
    Fix:
    - Recalibrate confidence dynamically
    - Reduce overconfidence bias
    """
    
    def __init__(self, calibration_window: int = 100):
        self.calibration_window = calibration_window
        self.predictions: List[Dict] = []  # {confidence, outcome, timestamp}
        self.calibration_map: Dict[float, float] = {}  # predicted -> actual
        
    def record_prediction(self, confidence: float, outcome: bool, metadata: Dict = None):
        """Record a prediction and its outcome."""
        self.predictions.append({
            'confidence': confidence,
            'outcome': 1.0 if outcome else 0.0,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        })
        
        # Keep only recent predictions
        if len(self.predictions) > self.calibration_window * 2:
            self.predictions = self.predictions[-self.calibration_window:]
        
        # Update calibration
        self._update_calibration()
    
    def _update_calibration(self):
        """Update calibration mapping based on recent predictions."""
        if len(self.predictions) < 20:
            return
        
        # Bin predictions by confidence level
        bins = defaultdict(list)
        for pred in self.predictions[-self.calibration_window:]:
            # Round to nearest 0.1
            bin_key = round(pred['confidence'] * 10) / 10
            bins[bin_key].append(pred['outcome'])
        
        # Calculate actual accuracy for each bin
        for bin_key, outcomes in bins.items():
            if len(outcomes) >= 5:  # Need minimum sample size
                actual_accuracy = sum(outcomes) / len(outcomes)
                self.calibration_map[bin_key] = actual_accuracy
    
    def calibrate_confidence(self, predicted_confidence: float) -> float:
        """
        Calibrate predicted confidence to actual accuracy.
        
        Args:
            predicted_confidence: Raw confidence prediction (0-1)
            
        Returns:
            Calibrated confidence
        """
        if not self.calibration_map:
            return predicted_confidence
        
        # Find nearest bin
        bin_key = round(predicted_confidence * 10) / 10
        
        if bin_key in self.calibration_map:
            # Use calibration map
            calibrated = self.calibration_map[bin_key]
            
            # Blend with original to avoid overcorrection
            return 0.7 * calibrated + 0.3 * predicted_confidence
        
        return predicted_confidence
    
    def detect_overconfidence(self) -> Dict[str, Any]:
        """Detect systematic overconfidence."""
        if len(self.predictions) < 50:
            return {'status': 'insufficient_data'}
        
        recent = self.predictions[-100:]
        
        # Group by confidence level
        high_conf = [p for p in recent if p['confidence'] > 0.8]
        med_conf = [p for p in recent if 0.5 < p['confidence'] <= 0.8]
        
        results = {}
        
        if high_conf:
            avg_pred_conf = np.mean([p['confidence'] for p in high_conf])
            actual_acc = np.mean([p['outcome'] for p in high_conf])
            overconf = avg_pred_conf - actual_acc
            
            results['high_confidence'] = {
                'predicted_accuracy': avg_pred_conf,
                'actual_accuracy': actual_acc,
                'overconfidence_gap': overconf,
                'is_overconfident': overconf > 0.1
            }
        
        return results
    
    def get_calibration_report(self) -> Dict[str, Any]:
        """Generate calibration report."""
        if len(self.predictions) < 20:
            return {'status': 'insufficient_data'}
        
        recent = self.predictions[-100:]
        
        predicted_accuracies = [p['confidence'] for p in recent]
        actual_outcomes = [p['outcome'] for p in recent]
        
        # Calculate reliability diagram data
        reliability = {}
        for pred_bin in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            bin_preds = [p for p in recent if abs(p['confidence'] - pred_bin) < 0.05]
            if bin_preds:
                reliability[pred_bin] = {
                    'predicted': pred_bin,
                    'actual': np.mean([p['outcome'] for p in bin_preds]),
                    'count': len(bin_preds)
                }
        
        # ECE (Expected Calibration Error)
        ece = sum(
            abs(r['predicted'] - r['actual']) * (r['count'] / len(recent))
            for r in reliability.values()
        )
        
        return {
            'total_predictions': len(self.predictions),
            'calibration_map': self.calibration_map,
            'reliability_diagram': reliability,
            'expected_calibration_error': ece,
            'mean_predicted_confidence': np.mean(predicted_accuracies),
            'mean_actual_accuracy': np.mean(actual_outcomes),
            'overconfidence_detected': self.detect_overconfidence(),
            'recommendation': 'Recalibration needed' if ece > 0.1 else 'Well calibrated'
        }


class MetaUncertaintyController:
    """
    Meta-Uncertainty Controller
    
    If uncertainty too high:
    System must: abstain > trade
    
    Most systems fail here.
    """
    
    def __init__(
        self,
        max_uncertainty_threshold: float = 0.6,
        abstention_threshold: float = 0.7,
        minimum_trades_for_override: int = 100
    ):
        self.max_uncertainty = max_uncertainty_threshold
        self.abstention_threshold = abstention_threshold
        self.min_trades_override = minimum_trades_for_override
        
        self.abstention_history: List[Dict] = []
        self.override_count = 0
        
    def evaluate_trade_decision(
        self,
        signal_confidence: float,
        uncertainty_profile: UncertaintyProfile,
        regime_stability: float,
        recent_performance: List[float]
    ) -> Tuple[str, str, float]:
        """
        Evaluate whether to trade or abstain.
        
        Returns:
            Tuple of (decision, reason, adjusted_confidence)
        """
        # Calculate meta-uncertainty
        meta_uncertainty = self._calculate_meta_uncertainty(
            uncertainty_profile, regime_stability, recent_performance
        )
        
        # Check if uncertainty is too high
        if meta_uncertainty > self.abstention_threshold:
            self.abstention_history.append({
                'timestamp': datetime.now(),
                'reason': 'meta_uncertainty_high',
                'uncertainty': meta_uncertainty,
                'signal_confidence': signal_confidence
            })
            return 'ABSTAIN', f'Meta-uncertainty {meta_uncertainty:.2f} exceeds threshold', 0.0
        
        # Check individual uncertainty components
        if uncertainty_profile.overall_confidence < 0.3:
            return 'ABSTAIN', 'Overall confidence too low', 0.0
        
        if uncertainty_profile.calibration_quality < 0.3:
            return 'ABSTAIN', 'Poor calibration quality', 0.0
        
        # Adjust confidence based on meta-uncertainty
        adjusted_confidence = signal_confidence * (1 - meta_uncertainty)
        
        if adjusted_confidence < 0.5:
            return 'ABSTAIN', f'Adjusted confidence {adjusted_confidence:.2f} too low', adjusted_confidence
        
        return 'TRADE', 'Uncertainty within acceptable bounds', adjusted_confidence
    
    def _calculate_meta_uncertainty(
        self,
        uncertainty_profile: UncertaintyProfile,
        regime_stability: float,
        recent_performance: List[float]
    ) -> float:
        """Calculate meta-uncertainty score."""
        scores = []
        
        # Uncertainty profile contribution
        scores.append(1 - uncertainty_profile.overall_confidence)
        scores.append(1 - uncertainty_profile.calibration_quality)
        
        # Regime stability contribution
        scores.append(1 - regime_stability)
        
        # Recent performance contribution
        if len(recent_performance) >= 10:
            perf_volatility = np.std(recent_performance[-10:])
            scores.append(min(1.0, perf_volatility * 5))
        
        # Average the components
        return np.mean(scores) if scores else 0.5
    
    def get_abstention_stats(self) -> Dict[str, Any]:
        """Get abstention statistics."""
        if not self.abstention_history:
            return {'status': 'no_abstentions'}
        
        recent_abstentions = [
            a for a in self.abstention_history
            if (datetime.now() - a['timestamp']).days < 30
        ]
        
        return {
            'total_abstentions': len(self.abstention_history),
            'recent_30d': len(recent_abstentions),
            'abstention_rate_30d': len(recent_abstentions) / max(1, len(self.abstention_history)),
            'avg_uncertainty_at_abstention': np.mean([a['uncertainty'] for a in recent_abstentions]) if recent_abstentions else 0,
            'overrides_performed': self.override_count
        }
