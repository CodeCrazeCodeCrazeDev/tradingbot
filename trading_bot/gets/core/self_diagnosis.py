"""
Layer 3: Self-Diagnosis Layer

Introspection engine that inspects every prediction before it becomes a signal.

Per-Forecast Diagnostics:
1. Forecast Stability Testing - Perturbation sensitivity
2. Model Disagreement Topology - Cross-model divergence as signal
3. Evidence Sufficiency Check - Data quality thresholds
4. Contradiction Detection - Cross-model conflict identification
5. Regime Mismatch Assessment - Out-of-regime confidence discounting
6. Calibration Drift Detection - Predicted vs realized quantile tracking
7. Execution Invalidation Check - Edge > cost, liquidity sufficiency

Failure Memory Tracking:
- Recurring failure pattern classification
- Model-specific blind spot catalog
- Temporal failure clustering
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from ..types import (
    ModelType, ForecastHorizon, MarketData, FoundationForecast,
    TradingNativeHeads, RegimeType, GETSConfig, GETSSignal,
    DisagreementGeometry, DisagreementPattern, SelfDiagnosisReport
)

logger = logging.getLogger(__name__)


@dataclass
class FailurePattern:
    """Classification of a failure pattern for learning."""
    pattern_id: str
    failure_class: str
    description: str
    affected_models: List[ModelType]
    typical_regimes: List[RegimeType]
    typical_horizons: List[ForecastHorizon]
    frequency: int = 0
    last_occurrence: Optional[datetime] = None
    
    # Resolution tracking
    resolved_by: Optional[str] = None  # Mutation ID that addressed this
    resolution_confidence: float = 0.0


@dataclass
class BlindSpotCatalog:
    """Known blind spots for each foundation model."""
    model_type: ModelType
    blind_spots: List[str]
    detection_signals: List[str]
    confidence_discount: float  # Factor to reduce confidence when blind spot detected


class DisagreementGeometryEngine:
    """
    Computes disagreement geometry across foundation models.
    
    Edge comes not from prediction alone, but from the structure of:
    - Agreement (consensus, possibly crowded)
    - Disagreement (information, possibly tradable)
    - Stability (reliability of forecasts)
    - Uncertainty (entropy across models)
    """
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        
        # Model authority weights (dynamically adjusted)
        self.model_authority: Dict[ModelType, float] = {
            ModelType.KRONOS: 0.25,
            ModelType.TIMESFM: 0.25,
            ModelType.MOIRAI: 0.25,
            ModelType.TTM: 0.25
        }
        
        # Historical accuracy tracking for authority updates
        self.model_accuracy_history: Dict[ModelType, List[float]] = defaultdict(list)
    
    def compute_geometry(
        self,
        forecasts: Dict[ModelType, FoundationForecast],
        market_data: MarketData
    ) -> DisagreementGeometry:
        """
        Compute full disagreement geometry from foundation forecasts.
        
        Args:
            forecasts: Predictions from each foundation model
            market_data: Current market state
            
        Returns:
            DisagreementGeometry with all metrics
        """
        if len(forecasts) < 2:
            # Not enough models for meaningful disagreement
            return self._create_default_geometry(list(forecasts.keys())[0] if forecasts else None)
        
        # Extract predictions
        current_price = market_data.ohlcv['close']
        predictions = {
            mt: f.point_prediction for mt, f in forecasts.items()
        }
        confidences = {
            mt: f.model_confidence for mt, f in forecasts.items()
        }
        uncertainties = {
            mt: f.forecast_std for mt, f in forecasts.items()
        }
        
        # 1. Directional disagreement
        directional_disagreement = self._compute_directional_disagreement(
            predictions, current_price
        )
        
        # 2. Magnitude disagreement
        magnitude_disagreement = self._compute_magnitude_disagreement(predictions)
        
        # 3. Uncertainty disagreement
        uncertainty_disagreement = self._compute_uncertainty_disagreement(uncertainties)
        
        # 4. Identify disagreement pattern
        pattern, pattern_strength = self._identify_pattern(
            predictions, confidences, uncertainties, forecasts
        )
        
        # 5. Model-specific extremes
        most_bullish, most_bearish = self._find_directional_extremes(predictions)
        most_uncertain, most_confident = self._find_uncertainty_extremes(uncertainties, confidences)
        
        # 6. Stability measures
        stability = self._compute_cross_model_stability(predictions, confidences)
        consensus = self._compute_consensus_score(predictions, current_price)
        
        # 7. Entropy measure
        entropy = self._compute_disagreement_entropy(predictions)
        
        # 8. Dynamic authority weights based on recent performance
        authority_weights = self._compute_authority_weights(forecasts)
        
        return DisagreementGeometry(
            directional_disagreement=directional_disagreement,
            magnitude_disagreement=magnitude_disagreement,
            uncertainty_disagreement=uncertainty_disagreement,
            disagreement_pattern=pattern,
            pattern_strength=pattern_strength,
            most_bullish_model=most_bullish,
            most_bearish_model=most_bearish,
            most_uncertain_model=most_uncertain,
            most_confident_model=most_confident,
            cross_model_stability=stability,
            forecast_consensus_score=consensus,
            disagreement_entropy=entropy,
            model_authority_weights=authority_weights
        )
    
    def _compute_directional_disagreement(
        self,
        predictions: Dict[ModelType, float],
        current_price: float
    ) -> float:
        """
        Compute directional disagreement: how much models disagree on up/down.
        
        Returns value in [0, 1] where 0 = complete agreement, 1 = maximum conflict.
        """
        if not predictions:
            return 0.0
        
        # Get directional signals (-1, 0, 1)
        directions = {}
        for mt, pred in predictions.items():
            ret = (pred / current_price) - 1
            if ret > 0.001:
                directions[mt] = 1  # Bullish
            elif ret < -0.001:
                directions[mt] = -1  # Bearish
            else:
                directions[mt] = 0  # Neutral
        
        # Count direction frequencies
        counts = defaultdict(int)
        for d in directions.values():
            counts[d] += 1
        
        total = len(directions)
        if total == 0:
            return 0.0
        
        # Disagreement is high when both bullish and bearish present
        bullish_pct = counts[1] / total
        bearish_pct = counts[-1] / total
        neutral_pct = counts[0] / total
        
        # Strong disagreement when roughly equal bullish/bearish
        if bullish_pct > 0 and bearish_pct > 0:
            disagreement = 1.0 - abs(bullish_pct - bearish_pct)
        elif neutral_pct > 0.5:
            # Mostly neutral is low disagreement
            disagreement = 0.2
        else:
            # Unanimous direction
            disagreement = 0.0
        
        return disagreement
    
    def _compute_magnitude_disagreement(
        self,
        predictions: Dict[ModelType, float]
    ) -> float:
        """
        Compute variance in prediction magnitudes.
        
        Returns normalized variance coefficient.
        """
        if len(predictions) < 2:
            return 0.0
        
        values = list(predictions.values())
        mean_pred = np.mean(values)
        std_pred = np.std(values)
        
        if mean_pred == 0:
            return 0.0
        
        # Coefficient of variation
        cv = std_pred / abs(mean_pred)
        
        # Normalize to [0, 1] assuming CV > 0.1 is significant
        return min(cv / 0.1, 1.0)
    
    def _compute_uncertainty_disagreement(
        self,
        uncertainties: Dict[ModelType, float]
    ) -> float:
        """Compute disagreement in uncertainty estimates."""
        if len(uncertainties) < 2:
            return 0.0
        
        values = list(uncertainties.values())
        cv = np.std(values) / (np.mean(values) + 1e-8)
        return min(cv, 1.0)
    
    def _identify_pattern(
        self,
        predictions: Dict[ModelType, float],
        confidences: Dict[ModelType, float],
        uncertainties: Dict[ModelType, float],
        forecasts: Dict[ModelType, FoundationForecast]
    ) -> Tuple[Optional[DisagreementPattern], float]:
        """
        Identify which disagreement pattern is present.
        
        Returns pattern type and strength (0-1).
        """
        if len(predictions) < 2:
            return None, 0.0
        
        current_price = np.mean(list(predictions.values()))  # Approximation
        
        # Check each pattern
        
        # 1. KRONOS_UP_TIMESFM_DOWN: Short-term momentum vs long-term mean reversion
        if ModelType.KRONOS in predictions and ModelType.TIMESFM in predictions:
            kronos_ret = (predictions[ModelType.KRONOS] / current_price) - 1
            timesfm_ret = (predictions[ModelType.TIMESFM] / current_price) - 1
            
            if kronos_ret > 0.005 and timesfm_ret < -0.005:
                strength = min(abs(kronos_ret), abs(timesfm_ret)) * 100
                return DisagreementPattern.KRONOS_UP_TIMESFM_DOWN, min(strength, 1.0)
        
        # 2. MOIRAI_HIGH_VARIANCE: Cross-asset uncertainty elevated
        if ModelType.MOIRAI in uncertainties:
            moirai_unc = uncertainties[ModelType.MOIRAI]
            other_unc = [u for mt, u in uncertainties.items() if mt != ModelType.MOIRAI]
            if other_unc and moirai_unc > np.mean(other_unc) * 1.5:
                strength = (moirai_unc / np.mean(other_unc) - 1) / 2
                return DisagreementPattern.MOIRAI_HIGH_VARIANCE, min(strength, 1.0)
        
        # 3. TTM_STABLE_OTHERS_VOLATILE: Local predictability, structural uncertainty
        if ModelType.TTM in uncertainties and len(uncertainties) > 2:
            ttm_unc = uncertainties[ModelType.TTM]
            other_unc = [u for mt, u in uncertainties.items() if mt != ModelType.TTM]
            if ttm_unc < np.mean(other_unc) * 0.5:
                strength = 1.0 - (ttm_unc / (np.mean(other_unc) + 1e-8))
                return DisagreementPattern.TTM_STABLE_OTHERS_VOLATILE, min(strength, 1.0)
        
        # 4. ALL_MODELS_CONVERGING: High-confidence consensus
        if len(predictions) >= 3:
            avg_conf = np.mean(list(confidences.values()))
            directional_agreement = self._compute_directional_disagreement(
                predictions, current_price
            )
            if avg_conf > 0.8 and directional_agreement < 0.2:
                return DisagreementPattern.ALL_MODELS_CONVERGING, avg_conf
        
        # 5. UNCERTAINTY_FAN_EXPANDING: Information entropy increasing
        if len(uncertainties) >= 3:
            unc_values = list(uncertainties.values())
            if np.std(unc_values) > np.mean(unc_values) * 0.5:
                strength = np.std(unc_values) / (np.mean(unc_values) + 1e-8)
                return DisagreementPattern.UNCERTAINTY_FAN_EXPANDING, min(strength, 1.0)
        
        # 6. Model-specific blind spots (based on forecast characteristics)
        for mt, forecast in forecasts.items():
            if mt == ModelType.KRONOS:
                # Kronos struggles in low volatility
                if forecast.volatility_state and forecast.volatility_state < 0.2:
                    if forecast.model_confidence < 0.5:
                        return DisagreementPattern.KRONOS_BLINDSPOT, 0.7
        
        return None, 0.0
    
    def _find_directional_extremes(
        self,
        predictions: Dict[ModelType, float]
    ) -> Tuple[ModelType, ModelType]:
        """Find most bullish and most bearish models."""
        if not predictions:
            return ModelType.KRONOS, ModelType.KRONOS
        
        sorted_models = sorted(predictions.items(), key=lambda x: x[1])
        most_bearish = sorted_models[0][0]
        most_bullish = sorted_models[-1][0]
        return most_bullish, most_bearish
    
    def _find_uncertainty_extremes(
        self,
        uncertainties: Dict[ModelType, float],
        confidences: Dict[ModelType, float]
    ) -> Tuple[ModelType, ModelType]:
        """Find most uncertain and most confident models."""
        if not uncertainties:
            return ModelType.KRONOS, ModelType.KRONOS
        
        most_uncertain = max(uncertainties.items(), key=lambda x: x[1])[0]
        most_confident = max(confidences.items(), key=lambda x: x[1])[0]
        return most_uncertain, most_confident
    
    def _compute_cross_model_stability(
        self,
        predictions: Dict[ModelType, float],
        confidences: Dict[ModelType, float]
    ) -> float:
        """
        Compute stability score based on confidence-weighted variance.
        Higher = more stable.
        """
        if len(predictions) < 2:
            return 1.0
        
        # Weight predictions by confidence
        values = []
        weights = []
        for mt in predictions:
            values.append(predictions[mt])
            weights.append(confidences.get(mt, 0.5))
        
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        weighted_mean = np.average(values, weights=weights)
        weighted_var = np.average((np.array(values) - weighted_mean) ** 2, weights=weights)
        
        # Stability = 1 - normalized variance
        # Assume variance > 0.01 * mean^2 is unstable
        normalized_var = weighted_var / (weighted_mean ** 2 + 1e-8)
        stability = max(0.0, 1.0 - normalized_var / 0.01)
        
        return stability
    
    def _compute_consensus_score(
        self,
        predictions: Dict[ModelType, float],
        current_price: float
    ) -> float:
        """Compute agreement level across models (0-1, higher = more agreement)."""
        if len(predictions) < 2:
            return 1.0
        
        implied_returns = [(p / current_price) - 1 for p in predictions.values()]
        
        # Consensus when all returns have same sign and similar magnitude
        signs = [np.sign(r) for r in implied_returns]
        if len(set(signs)) > 1:
            return 0.3  # Mixed signals
        
        # Same sign: measure magnitude agreement
        mag_cv = np.std(implied_returns) / (abs(np.mean(implied_returns)) + 1e-8)
        consensus = max(0.0, 1.0 - mag_cv)
        
        return consensus
    
    def _compute_disagreement_entropy(
        self,
        predictions: Dict[ModelType, float]
    ) -> float:
        """Compute information-theoretic entropy of predictions."""
        if len(predictions) < 2:
            return 0.0
        
        # Normalize predictions to probabilities
        values = np.array(list(predictions.values()))
        # Softmax normalization
        exp_values = np.exp(values - np.max(values))
        probs = exp_values / exp_values.sum()
        
        # Shannon entropy
        entropy = -np.sum(probs * np.log(probs + 1e-8))
        
        # Normalize by max entropy (uniform distribution)
        max_entropy = np.log(len(predictions))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
        
        return normalized_entropy
    
    def _compute_authority_weights(
        self,
        forecasts: Dict[ModelType, FoundationForecast]
    ) -> Dict[ModelType, float]:
        """Compute dynamic authority weights based on recent accuracy."""
        # Start with base authority
        weights = dict(self.model_authority)
        
        # Adjust based on current confidence
        for mt, forecast in forecasts.items():
            if mt in weights:
                # Weight = base * current confidence
                weights[mt] = weights[mt] * forecast.model_confidence
        
        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def update_model_accuracy(
        self,
        model_type: ModelType,
        realized_return: float,
        predicted_return: float
    ):
        """Update accuracy history for authority weight adjustment."""
        # Compute directional accuracy
        directional_correct = np.sign(realized_return) == np.sign(predicted_return)
        accuracy = 1.0 if directional_correct else 0.0
        
        self.model_accuracy_history[model_type].append(accuracy)
        
        # Keep only recent history
        if len(self.model_accuracy_history[model_type]) > 100:
            self.model_accuracy_history[model_type] = self.model_accuracy_history[model_type][-100:]
        
        # Update authority based on recent accuracy
        if len(self.model_accuracy_history[model_type]) >= 10:
            recent_accuracy = np.mean(self.model_accuracy_history[model_type][-10:])
            # Smooth update
            self.model_authority[model_type] = (
                0.9 * self.model_authority[model_type] + 0.1 * recent_accuracy
            )
            
            # Renormalize
            total = sum(self.model_authority.values())
            self.model_authority = {k: v / total for k, v in self.model_authority.items()}
    
    def _create_default_geometry(self, single_model: Optional[ModelType]) -> DisagreementGeometry:
        """Create default geometry when insufficient models."""
        model = single_model or ModelType.KRONOS
        return DisagreementGeometry(
            directional_disagreement=0.0,
            magnitude_disagreement=0.0,
            uncertainty_disagreement=0.0,
            disagreement_pattern=None,
            pattern_strength=0.0,
            most_bullish_model=model,
            most_bearish_model=model,
            most_uncertain_model=model,
            most_confident_model=model,
            cross_model_stability=1.0,
            forecast_consensus_score=1.0,
            disagreement_entropy=0.0,
            model_authority_weights={model: 1.0}
        )


class ForecastStabilityTester:
    """
    Tests forecast stability under input perturbations.
    
    Philosophy: Slight perturbations should not produce wild output swings.
    """
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        self.perturbation_levels = [0.001, 0.005, 0.01]  # 0.1%, 0.5%, 1%
        self.stability_threshold = config.stability_threshold if config else 0.7
    
    def test_stability(
        self,
        base_forecasts: Dict[ModelType, FoundationForecast],
        market_data: MarketData,
        forecast_fn: Callable[[MarketData, ForecastHorizon], Dict[ModelType, FoundationForecast]],
        horizon: ForecastHorizon
    ) -> Tuple[float, float, bool]:
        """
        Test forecast stability by perturbing inputs.
        
        Returns:
            (stability_score, sensitivity, passed)
        """
        base_predictions = {
            mt: f.point_prediction for mt, f in base_forecasts.items()
        }
        
        max_variance = 0.0
        all_variances = []
        
        for perturbation in self.perturbation_levels:
            # Perturb market data
            perturbed_data = self._perturb_market_data(market_data, perturbation)
            
            # Get forecasts on perturbed data
            try:
                perturbed_forecasts = forecast_fn(perturbed_data, horizon)
                perturbed_predictions = {
                    mt: f.point_prediction for mt, f in perturbed_forecasts.items()
                }
                
                # Compute variance
                variance = self._compute_prediction_variance(
                    base_predictions, perturbed_predictions
                )
                all_variances.append(variance)
                max_variance = max(max_variance, variance)
                
            except Exception as e:
                logger.warning(f"Stability test failed for perturbation {perturbation}: {e}")
                all_variances.append(float('inf'))
        
        # Stability score: higher is more stable
        # Max variance normalized by price level
        price = market_data.ohlcv['close']
        normalized_variance = max_variance / (price ** 2)
        
        # Convert to stability score (0-1)
        stability_score = max(0.0, 1.0 - normalized_variance * 1000)
        
        # Sensitivity: average variance across perturbation levels
        valid_variances = [v for v in all_variances if v != float('inf')]
        sensitivity = np.mean(valid_variances) if valid_variances else float('inf')
        
        passed = stability_score >= self.stability_threshold
        
        return stability_score, sensitivity, passed
    
    def _perturb_market_data(
        self,
        market_data: MarketData,
        perturbation: float
    ) -> MarketData:
        """Create perturbed version of market data."""
        ohlcv = market_data.ohlcv.copy()
        
        # Perturb OHLCV
        for key in ['open', 'high', 'low', 'close']:
            if key in ohlcv:
                noise = np.random.normal(0, perturbation)
                ohlcv[key] = ohlcv[key] * (1 + noise)
        
        # Perturb volume
        if 'volume' in ohlcv:
            ohlcv['volume'] = ohlcv['volume'] * (1 + np.random.normal(0, perturbation))
        
        # Create perturbed market data
        perturbed = MarketData(
            symbol=market_data.symbol,
            timestamp=market_data.timestamp,
            ohlcv=ohlcv,
            bid_ask_spread=market_data.bid_ask_spread,
            depth_imbalance=market_data.depth_imbalance,
            realized_volatility=market_data.realized_volatility,
            volume_profile=market_data.volume_profile
        )
        
        return perturbed
    
    def _compute_prediction_variance(
        self,
        base: Dict[ModelType, float],
        perturbed: Dict[ModelType, float]
    ) -> float:
        """Compute variance between base and perturbed predictions."""
        variances = []
        for mt in base:
            if mt in perturbed:
                diff = base[mt] - perturbed[mt]
                variances.append(diff ** 2)
        
        return np.mean(variances) if variances else 0.0


class EvidenceSufficiencyChecker:
    """Checks if sufficient evidence exists for reliable forecasting."""
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        self.evidence_threshold = config.evidence_threshold if config else 0.6
    
    def check_sufficiency(
        self,
        market_data: MarketData,
        required_models: int = 2
    ) -> Tuple[float, bool, List[str]]:
        """
        Check evidence sufficiency.
        
        Returns:
            (sufficiency_score, passed, missing_evidence)
        """
        issues = []
        score = 1.0
        
        # Check OHLCV completeness
        required_ohlcv = ['open', 'high', 'low', 'close', 'volume']
        missing = [k for k in required_ohlcv if k not in market_data.ohlcv]
        if missing:
            issues.append(f"Missing OHLCV fields: {missing}")
            score -= 0.2 * len(missing)
        
        # Check for stale data (would need timestamp comparison)
        # Placeholder: assume fresh if timestamp present
        if not market_data.timestamp:
            issues.append("Missing timestamp")
            score -= 0.3
        
        # Check for extended features (bonus, not required)
        if market_data.bid_ask_spread is None:
            issues.append("Missing bid-ask spread (bonus)")
            score -= 0.05
        
        if market_data.depth_imbalance is None:
            issues.append("Missing depth imbalance (bonus)")
            score -= 0.05
        
        if market_data.realized_volatility is None:
            issues.append("Missing realized volatility")
            score -= 0.1
        
        # Check volatility sanity
        if market_data.realized_volatility:
            if market_data.realized_volatility > 1.0:  # >100% annualized
                issues.append("Extreme volatility detected")
                score -= 0.2
            elif market_data.realized_volatility < 0.001:  # Near-zero
                issues.append("Near-zero volatility (suspicious)")
                score -= 0.1
        
        score = max(0.0, score)
        passed = score >= self.evidence_threshold
        
        return score, passed, issues


class ContradictionDetector:
    """Detects contradictions between model predictions and market context."""
    
    def detect_contradictions(
        self,
        forecasts: Dict[ModelType, FoundationForecast],
        trading_predictions: TradingNativeHeads,
        market_data: MarketData,
        detected_regime: RegimeType
    ) -> Tuple[bool, List[str]]:
        """
        Detect contradictions in predictions.
        
        Returns:
            (contradiction_detected, details)
        """
        contradictions = []
        
        # 1. Sign conflict: models disagree on direction
        returns = {}
        current_price = market_data.ohlcv['close']
        for mt, forecast in forecasts.items():
            ret = (forecast.point_prediction / current_price) - 1
            returns[mt] = ret
        
        signs = [np.sign(r) for r in returns.values()]
        if len(set(signs)) > 1 and 0 not in signs:
            # Both bullish and bearish predictions
            bullish = [mt for mt, r in returns.items() if r > 0]
            bearish = [mt for mt, r in returns.items() if r < 0]
            contradictions.append(
                f"Directional conflict: {bullish} bullish vs {bearish} bearish"
            )
        
        # 2. Regime-fit mismatch
        regime_friendly = self._is_regime_friendly(detected_regime, trading_predictions)
        if not regime_friendly:
            contradictions.append(
                f"Regime mismatch: {detected_regime.value} vs prediction direction"
            )
        
        # 3. Confidence vs uncertainty mismatch
        for mt, forecast in forecasts.items():
            if forecast.model_confidence > 0.8 and forecast.forecast_std > current_price * 0.05:
                contradictions.append(
                    f"{mt.value}: High confidence with wide forecast interval"
                )
        
        # 4. Edge vs drawdown conflict
        if trading_predictions.edge_after_cost > 0.01 and trading_predictions.drawdown_risk_prob > 0.5:
            contradictions.append(
                f"High edge ({trading_predictions.edge_after_cost:.4f}) with high drawdown risk "
                f"({trading_predictions.drawdown_risk_prob:.2f})"
            )
        
        return len(contradictions) > 0, contradictions
    
    def _is_regime_friendly(
        self,
        regime: RegimeType,
        predictions: TradingNativeHeads
    ) -> bool:
        """Check if prediction aligns with typical regime behavior."""
        # Simple checks
        if regime == RegimeType.TRENDING_BULL and predictions.expected_signed_return < 0:
            return False
        if regime == RegimeType.TRENDING_BEAR and predictions.expected_signed_return > 0:
            return False
        if regime == RegimeType.HIGH_VOLATILITY and predictions.volatility_forecast < 0.2:
            return False
        return True


class SelfDiagnosisLayer:
    """
    Layer 3: Self-Diagnosis Layer
    
    Comprehensive introspection engine that validates every forecast
    before it becomes a trading signal.
    """
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        
        # Sub-components
        self.disagreement_engine = DisagreementGeometryEngine(config)
        self.stability_tester = ForecastStabilityTester(config)
        self.evidence_checker = EvidenceSufficiencyChecker(config)
        self.contradiction_detector = ContradictionDetector()
        
        # Failure memory
        self.failure_patterns: Dict[str, FailurePattern] = {}
        self.blind_spot_catalogs: Dict[ModelType, BlindSpotCatalog] = {}
        self._init_blind_spot_catalogs()
        
        # Calibration tracking
        self.calibration_history: Dict[ModelType, List[Tuple[float, float]]] = defaultdict(list)
        
        self._initialized = True
    
    def _init_blind_spot_catalogs(self):
        """Initialize known blind spots for each model."""
        self.blind_spot_catalogs = {
            ModelType.KRONOS: BlindSpotCatalog(
                model_type=ModelType.KRONOS,
                blind_spots=[
                    "low_volatility_regimes",
                    "flash_crash_events",
                    "overnight_gaps"
                ],
                detection_signals=[
                    "volatility_state < 0.2",
                    "price_gap > 3%",
                    "session_boundary"
                ],
                confidence_discount=0.6
            ),
            ModelType.TIMESFM: BlindSpotCatalog(
                model_type=ModelType.TIMESFM,
                blind_spots=[
                    "regime_transitions",
                    "intraday_microstructure"
                ],
                detection_signals=[
                    "regime_shift_probability > 0.7",
                    "horizon < 1 hour"
                ],
                confidence_discount=0.7
            ),
            ModelType.MOIRAI: BlindSpotCatalog(
                model_type=ModelType.MOIRAI,
                blind_spots=[
                    "low_correlation_regimes",
                    "single_asset_forecast"
                ],
                detection_signals=[
                    "avg_cross_correlation < 0.3",
                    "num_related_assets < 3"
                ],
                confidence_discount=0.8
            ),
            ModelType.TTM: BlindSpotCatalog(
                model_type=ModelType.TTM,
                blind_spots=[
                    "trending_markets",
                    "long_horizon_patterns",
                    "regime_transitions"
                ],
                detection_signals=[
                    "recent_trend_strength > 0.8",
                    "horizon > 1 hour"
                ],
                confidence_discount=0.7
            )
        }
    
    def diagnose(
        self,
        forecasts: Dict[ModelType, FoundationForecast],
        trading_predictions: TradingNativeHeads,
        market_data: MarketData,
        detected_regime: RegimeType,
        stability_test_fn: Optional[Callable] = None,
        horizon: Optional[ForecastHorizon] = None
    ) -> Tuple[DisagreementGeometry, SelfDiagnosisReport]:
        """
        Run full diagnostic suite on forecasts.
        
        Args:
            forecasts: Foundation model predictions
            trading_predictions: Trading-native head outputs
            market_data: Current market state
            detected_regime: Current market regime
            stability_test_fn: Optional function for stability testing
            horizon: Forecast horizon
            
        Returns:
            (disagreement_geometry, diagnosis_report)
        """
        # 1. Compute disagreement geometry
        geometry = self.disagreement_engine.compute_geometry(forecasts, market_data)
        
        # 2. Stability testing (if function provided)
        stability_score = 0.8
        perturbation_sensitivity = 0.0
        stability_passed = True
        
        if stability_test_fn and horizon:
            stability_score, perturbation_sensitivity, stability_passed = \
                self.stability_tester.test_stability(
                    forecasts, market_data, stability_test_fn, horizon
                )
        
        # 3. Evidence sufficiency
        evidence_score, evidence_passed, evidence_issues = \
            self.evidence_checker.check_sufficiency(market_data)
        
        # 4. Contradiction detection
        contradiction_detected, contradiction_details = \
            self.contradiction_detector.detect_contradictions(
                forecasts, trading_predictions, market_data, detected_regime
            )
        
        # 5. Regime mismatch
        regime_mismatch_score, regime_passed = self._check_regime_mismatch(
            forecasts, detected_regime
        )
        
        # 6. Calibration drift
        calibration_drift, calibration_error = self._check_calibration_drift(forecasts)
        
        # 7. Execution feasibility
        execution_feasible, execution_constraints = self._check_execution_feasibility(
            trading_predictions, market_data
        )
        
        # 8. Blind spot detection
        blind_spot_alerts = self._detect_blind_spots(forecasts, market_data)
        
        # 9. Determine overall pass/fail
        blocking_issues = []
        warnings = []
        
        if not stability_passed:
            blocking_issues.append(f"Stability test failed: {stability_score:.2f} < threshold")
        
        if not evidence_passed:
            blocking_issues.append(f"Insufficient evidence: {evidence_score:.2f}")
            blocking_issues.extend(evidence_issues[:2])  # Top issues
        
        if contradiction_detected:
            blocking_issues.append("Contradictions detected between models")
            warnings.extend(contradiction_details)
        
        if not regime_passed:
            blocking_issues.append(f"Regime mismatch: {regime_mismatch_score:.2f}")
        
        if calibration_drift:
            warnings.append(f"Calibration drift detected: {calibration_error:.3f}")
        
        if not execution_feasible:
            blocking_issues.append("Execution not feasible")
            blocking_issues.extend(execution_constraints)
        
        warnings.extend(blind_spot_alerts)
        
        overall_passed = len(blocking_issues) == 0
        
        # 10. Failure classification
        failure_class = None
        similar_failures = 0
        if not overall_passed:
            failure_class = self._classify_failure(
                blocking_issues, warnings, detected_regime, horizon
            )
            similar_failures = self._count_similar_failures(failure_class)
        
        report = SelfDiagnosisReport(
            forecast_stability_score=stability_score,
            perturbation_sensitivity=perturbation_sensitivity,
            stability_passed=stability_passed,
            evidence_sufficiency_score=evidence_score,
            evidence_passed=evidence_passed,
            contradiction_detected=contradiction_detected,
            contradiction_details=contradiction_details,
            regime_mismatch_score=regime_mismatch_score,
            regime_passed=regime_passed,
            calibration_drift_detected=calibration_drift,
            calibration_error=calibration_error,
            execution_feasible=execution_feasible,
            execution_constraints=execution_constraints,
            overall_passed=overall_passed,
            blocking_issues=blocking_issues,
            warnings=warnings,
            failure_class=failure_class,
            similar_failures_count=similar_failures
        )
        
        return geometry, report
    
    def _check_regime_mismatch(
        self,
        forecasts: Dict[ModelType, FoundationForecast],
        detected_regime: RegimeType
    ) -> Tuple[float, bool]:
        """Check if forecasts align with detected regime."""
        # Count models that claim to work well in this regime
        matching_models = 0
        total_models = len(forecasts)
        
        for mt, forecast in forecasts.items():
            catalog = self.blind_spot_catalogs.get(mt)
            if catalog:
                # Check if any blind spot detection signal is present
                blind_spot_present = False
                for signal in catalog.detection_signals:
                    if self._eval_blind_spot_signal(signal, detected_regime):
                        blind_spot_present = True
                        break
                
                if not blind_spot_present:
                    matching_models += 1
        
        if total_models == 0:
            return 1.0, True
        
        match_ratio = matching_models / total_models
        threshold = 0.5  # At least half models should be regime-compatible
        
        return 1.0 - match_ratio, match_ratio >= threshold
    
    def _eval_blind_spot_signal(self, signal: str, regime: RegimeType) -> bool:
        """Evaluate a blind spot detection signal."""
        # Simplified evaluation
        if "volatility" in signal and regime == RegimeType.LOW_VOLATILITY:
            return True
        if "regime_shift" in signal and regime in [
            RegimeType.BREAKOUT, RegimeType.REVERSAL
        ]:
            return True
        return False
    
    def _check_calibration_drift(
        self,
        forecasts: Dict[ModelType, FoundationForecast]
    ) -> Tuple[bool, Optional[float]]:
        """Check if models show calibration drift."""
        # Would need historical calibration data
        # Placeholder: check if in_sample_calibration_error is high
        
        high_error_models = 0
        max_error = 0.0
        
        for forecast in forecasts.values():
            if forecast.in_sample_calibration_error:
                if forecast.in_sample_calibration_error > 0.05:
                    high_error_models += 1
                    max_error = max(max_error, forecast.in_sample_calibration_error)
        
        drift_detected = high_error_models > len(forecasts) * 0.3
        return drift_detected, max_error if drift_detected else None
    
    def _check_execution_feasibility(
        self,
        predictions: TradingNativeHeads,
        market_data: MarketData
    ) -> Tuple[bool, List[str]]:
        """Check if trade can be executed profitably."""
        constraints = []
        
        # Check edge vs cost
        if predictions.edge_after_cost <= 0:
            constraints.append(f"Edge ({predictions.edge_after_cost:.4f}) <= cost")
        
        # Check execution difficulty
        if predictions.execution_difficulty_score > 0.7:
            constraints.append(
                f"High execution difficulty: {predictions.execution_difficulty_score:.2f}"
            )
        
        # Check liquidity (if available)
        spread = market_data.bid_ask_spread
        if spread:
            estimated_cost = spread + 0.0002  # Spread + slippage
            if predictions.edge_after_cost < estimated_cost * 1.5:
                constraints.append(
                    f"Edge ({predictions.edge_after_cost:.4f}) too close to cost ({estimated_cost:.4f})"
                )
        
        feasible = len(constraints) == 0
        return feasible, constraints
    
    def _detect_blind_spots(
        self,
        forecasts: Dict[ModelType, FoundationForecast],
        market_data: MarketData
    ) -> List[str]:
        """Detect if models are operating in known blind spot conditions."""
        alerts = []
        
        for mt, forecast in forecasts.items():
            catalog = self.blind_spot_catalogs.get(mt)
            if not catalog:
                continue
            
            for i, blind_spot in enumerate(catalog.blind_spots):
                signal = catalog.detection_signals[i] if i < len(catalog.detection_signals) else ""
                
                # Check if blind spot condition present
                if self._is_blind_spot_present(blind_spot, forecast, market_data):
                    alerts.append(
                        f"{mt.value}: {blind_spot} (confidence discounted to "
                        f"{catalog.confidence_discount:.0%})"
                    )
        
        return alerts
    
    def _is_blind_spot_present(
        self,
        blind_spot: str,
        forecast: FoundationForecast,
        market_data: MarketData
    ) -> bool:
        """Check if a specific blind spot condition is present."""
        if blind_spot == "low_volatility_regimes":
            return forecast.volatility_state is not None and forecast.volatility_state < 0.2
        elif blind_spot == "flash_crash_events":
            # Would need recent price history
            return False
        elif blind_spot == "overnight_gaps":
            # Would need session information
            return False
        elif blind_spot == "regime_transitions":
            # Simplified: high forecast uncertainty might indicate transition
            return forecast.forecast_std > forecast.point_prediction * 0.05
        return False
    
    def _classify_failure(
        self,
        blocking_issues: List[str],
        warnings: List[str],
        regime: RegimeType,
        horizon: Optional[ForecastHorizon]
    ) -> str:
        """Classify failure pattern for learning."""
        # Simple classification based on primary issue
        if any("Stability" in i for i in blocking_issues):
            return "forecast_instability"
        elif any("evidence" in i.lower() for i in blocking_issues):
            return "insufficient_evidence"
        elif any("Contradiction" in i for i in blocking_issues):
            return "model_disagreement"
        elif any("Regime" in i for i in blocking_issues):
            return f"regime_mismatch_{regime.value}"
        elif any("execution" in i.lower() for i in blocking_issues):
            return "execution_infeasible"
        else:
            return "general_failure"
    
    def _count_similar_failures(self, failure_class: str) -> int:
        """Count how many similar failures have occurred."""
        if failure_class not in self.failure_patterns:
            self.failure_patterns[failure_class] = FailurePattern(
                pattern_id=failure_class,
                failure_class=failure_class,
                description=f"Pattern: {failure_class}",
                affected_models=[],
                typical_regimes=[],
                typical_horizons=[]
            )
        
        pattern = self.failure_patterns[failure_class]
        pattern.frequency += 1
        pattern.last_occurrence = datetime.now()
        
        return pattern.frequency
    
    def record_outcome(
        self,
        model_type: ModelType,
        predicted_return: float,
        realized_return: float
    ):
        """Record outcome for calibration and authority updates."""
        # Update disagreement engine
        self.disagreement_engine.update_model_accuracy(
            model_type, realized_return, predicted_return
        )
        
        # Track calibration
        self.calibration_history[model_type].append((predicted_return, realized_return))
        
        # Keep history bounded
        if len(self.calibration_history[model_type]) > 1000:
            self.calibration_history[model_type] = self.calibration_history[model_type][-1000:]
    
    def get_failure_patterns(self) -> Dict[str, FailurePattern]:
        """Get all tracked failure patterns."""
        return dict(self.failure_patterns)
    
    def get_model_calibrations(self) -> Dict[ModelType, Dict[str, float]]:
        """Get calibration statistics for each model."""
        calibrations = {}
        
        for mt, history in self.calibration_history.items():
            if len(history) < 10:
                continue
            
            predicted = np.array([h[0] for h in history])
            realized = np.array([h[1] for h in history])
            
            # Directional accuracy
            directional_correct = np.mean(
                (predicted * realized) > 0
            )
            
            # MSE
            mse = np.mean((predicted - realized) ** 2)
            
            # Correlation
            if len(predicted) > 1:
                correlation = np.corrcoef(predicted, realized)[0, 1]
            else:
                correlation = 0.0
            
            calibrations[mt] = {
                'directional_accuracy': directional_correct,
                'mse': mse,
                'correlation': correlation,
                'sample_count': len(history)
            }
        
        return calibrations
