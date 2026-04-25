"""
GETS System Orchestrator

Main entry point for the Governed Evolving Time-Series Foundation System.
Orchestrates all five layers:
1. Temporal Perception Layer - Foundation model inference
2. Forecast & Representation Layer - Trading-native heads
3. Self-Diagnosis Layer - Introspection and disagreement geometry
4. Controlled Evolution Layer - Sandbox-only improvement
5. Governance & Promotion Layer - Audited capability promotion

Usage:
    from trading_bot.gets import create_gets
    
    gets = create_gets(config)
    gets.initialize()
    
    # Generate trading signal
    signal = gets.generate_signal(market_data, horizon)
    
    # Record outcome for learning
    gets.record_outcome(signal, realized_return)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

from .types import (
    ModelType, ForecastHorizon, MarketData, FoundationForecast,
    TradingNativeHeads, RegimeType, GETSConfig, GETSSignal,
    DisagreementGeometry, SelfDiagnosisReport, GovernanceDecision
)

from .core.temporal_perception import TemporalPerceptionLayer
from .core.forecast_representation import ForecastRepresentationLayer
from .core.self_diagnosis import SelfDiagnosisLayer
from .core.controlled_evolution import ControlledEvolutionLayer
from .core.governance_promotion import GovernancePromotionLayer
from .multimodal_awareness import MultiModalAwareness

logger = logging.getLogger(__name__)


class GETS:
    """
    Governed Evolving Time-Series Foundation System
    
    Hierarchical temporal intelligence stack with strict governance boundaries.
    """
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        
        # Five layers
        self.layer1_perception: Optional[TemporalPerceptionLayer] = None
        self.layer2_representation: Optional[ForecastRepresentationLayer] = None
        self.layer3_diagnosis: Optional[SelfDiagnosisLayer] = None
        self.layer4_evolution: Optional[ControlledEvolutionLayer] = None
        self.layer5_governance: Optional[GovernancePromotionLayer] = None
        
        # State
        self._initialized = False
        self._current_regime: RegimeType = RegimeType.UNKNOWN
        self.signal_history: List[GETSSignal] = []
        
        # Multi-modal awareness
        self.awareness: Optional[MultiModalAwareness] = None
        
        # Integration with existing systems
        self.dgs_integration = self.config.decision_governance_integration
    
    def initialize(self) -> bool:
        """
        Initialize all five layers of GETS.
        
        Returns:
            Success status
        """
        logger.info("Initializing GETS - Governed Evolving Time-Series Foundation System")
        logger.info("=" * 80)
        
        # Layer 1: Temporal Perception
        logger.info("[Layer 1] Initializing Temporal Perception...")
        self.layer1_perception = TemporalPerceptionLayer(self.config)
        if not self.layer1_perception.initialize():
            logger.error("Failed to initialize Layer 1")
            return False
        logger.info("[Layer 1] ✓ Foundation models ready")
        
        # Layer 2: Forecast & Representation
        logger.info("[Layer 2] Initializing Forecast & Representation...")
        self.layer2_representation = ForecastRepresentationLayer(self.config)
        if not self.layer2_representation.initialize(embedding_dim=256):
            logger.error("Failed to initialize Layer 2")
            return False
        logger.info("[Layer 2] ✓ Trading-native heads ready")
        
        # Layer 3: Self-Diagnosis
        logger.info("[Layer 3] Initializing Self-Diagnosis...")
        self.layer3_diagnosis = SelfDiagnosisLayer(self.config)
        logger.info("[Layer 3] ✓ Introspection engine ready")
        
        # Layer 4: Controlled Evolution (sandbox only)
        logger.info("[Layer 4] Initializing Controlled Evolution...")
        self.layer4_evolution = ControlledEvolutionLayer(self.config)
        logger.info("[Layer 4] ✓ Sandbox evolution system ready")
        
        # Layer 5: Governance & Promotion
        logger.info("[Layer 5] Initializing Governance & Promotion...")
        self.layer5_governance = GovernancePromotionLayer(self.config)
        logger.info("[Layer 5] ✓ Governance layer ready")
        
        # Multi-Modal Awareness
        logger.info("[Awareness] Initializing Multi-Modal Awareness...")
        self.awareness = MultiModalAwareness()
        logger.info("[Awareness] ✓ Causality, Market Structure, Decision, Risk, Regime ready")
        
        self._initialized = True
        
        logger.info("=" * 80)
        logger.info("GETS initialization complete")
        logger.info(f"  Models enabled: Kronos={self.config.kronos_enabled}, "
                   f"TimesFM={self.config.timesfm_enabled}, "
                   f"Moirai={self.config.moirai_enabled}, "
                   f"TTM={self.config.ttm_enabled}")
        logger.info(f"  Integration with decision_governance: {self.dgs_integration}")
        
        return True
    
    def generate_signal(
        self,
        market_data: MarketData,
        horizon: ForecastHorizon = ForecastHorizon.SHORT,
        required_models: Optional[List[ModelType]] = None
    ) -> GETSSignal:
        """
        Generate a trading signal through all five layers.
        
        Pipeline:
        1. Get foundation forecasts from Layer 1
        2. Generate trading-native predictions with Layer 2
        3. Run introspection diagnostics with Layer 3
        4. Apply governance decision with Layer 5 (if integrated)
        
        Args:
            market_data: Current market state
            horizon: Forecast horizon
            required_models: Specific models to use (default: all available)
            
        Returns:
            GETSSignal with full diagnostic context
        """
        if not self._initialized:
            raise RuntimeError("GETS not initialized. Call initialize() first.")
        
        timestamp = datetime.now()
        
        # === LAYER 1: Temporal Perception ===
        logger.debug(f"[Layer 1] Getting foundation forecasts for {market_data.symbol}")
        
        foundation_forecasts = self.layer1_perception.get_foundation_forecasts(
            market_data, horizon, required_models
        )
        
        if not foundation_forecasts:
            logger.warning(f"No foundation forecasts available for {market_data.symbol}")
            return self._create_null_signal(market_data, timestamp, "No forecasts available")
        
        # Update current regime based on forecasts
        self._update_regime_estimate(foundation_forecasts)
        
        # === LAYER 2: Forecast & Representation ===
        logger.debug(f"[Layer 2] Generating trading-native predictions")
        
        trading_predictions = self.layer2_representation.generate_trading_predictions(
            foundation_forecasts,
            market_data,
            self._current_regime
        )
        
        # === LAYER 3: Self-Diagnosis ===
        logger.debug(f"[Layer 3] Running introspection diagnostics")
        
        def stability_test_fn(data: MarketData, h: ForecastHorizon):
            return self.layer1_perception.get_foundation_forecasts(data, h)
        
        disagreement_geometry, diagnosis_report = self.layer3_diagnosis.diagnose(
            foundation_forecasts,
            trading_predictions,
            market_data,
            self._current_regime,
            stability_test_fn if len(foundation_forecasts) > 1 else None,
            horizon
        )
        
        # === LAYER 5: Governance Decision (Layer 4 is sandbox-only) ===
        logger.debug(f"[Layer 5] Applying governance decision")
        
        governance_decision, reasoning = self._apply_governance(
            trading_predictions,
            diagnosis_report,
            disagreement_geometry,
            market_data
        )
        
        # === Construct Final Signal ===
        direction = np.sign(trading_predictions.expected_signed_return)
        if not diagnosis_report.overall_passed or governance_decision == GovernanceDecision.ABSTAIN:
            direction = 0
        
        # Compute prediction interval
        point_preds = [f.point_prediction for f in foundation_forecasts.values()]
        if point_preds:
            price = market_data.ohlcv['close']
            implied_returns = [(p / price) - 1 for p in point_preds]
            mean_ret = np.mean(implied_returns)
            std_ret = np.std(implied_returns) if len(implied_returns) > 1 else 0.01
            
            q05 = price * (1 + mean_ret - 1.645 * std_ret)
            q95 = price * (1 + mean_ret + 1.645 * std_ret)
        else:
            q05 = q95 = market_data.ohlcv['close']
        
        # Determine abstention
        abstain = (
            governance_decision == GovernanceDecision.ABSTAIN or
            not trading_predictions.tradable or
            not diagnosis_report.overall_passed
        )
        
        abstain_reason = None
        if abstain:
            if not trading_predictions.tradable:
                abstain_reason = "Edge after cost insufficient"
            elif diagnosis_report.blocking_issues:
                abstain_reason = f"Diagnosis failed: {diagnosis_report.blocking_issues[0]}"
            else:
                abstain_reason = "Governance abstention"
        
        # Compute recommended position size
        if abstain:
            size_scale = 0.0
        elif governance_decision == GovernanceDecision.RESIZE:
            size_scale = 0.5  # Reduce position
        else:
            # Scale by confidence, disagreement, and execution difficulty
            base_scale = trading_predictions.edge_after_cost * 100  # Scale to reasonable range
            confidence_factor = disagreement_geometry.forecast_consensus_score
            difficulty_factor = 1.0 - trading_predictions.execution_difficulty_score
            size_scale = min(base_scale * confidence_factor * difficulty_factor, 1.0)
            size_scale = max(0.0, size_scale)
        
        signal = GETSSignal(
            symbol=market_data.symbol,
            timestamp=timestamp,
            direction=int(direction),
            confidence=trading_predictions.prob_exceed_cost_threshold,
            expected_edge=trading_predictions.edge_after_cost,
            uncertainty_quantile_05=q05,
            uncertainty_quantile_95=q95,
            prediction_interval=(q05, q95),
            governance_decision=governance_decision,
            decision_reasoning=reasoning,
            source_models=list(foundation_forecasts.keys()),
            disagreement_geometry=disagreement_geometry,
            diagnosis_report=diagnosis_report,
            recommended_size_scale=size_scale,
            abstain_recommended=abstain,
            abstain_reason=abstain_reason
        )
        
        # Store in history
        self.signal_history.append(signal)
        
        # Trim history
        if len(self.signal_history) > 10000:
            self.signal_history = self.signal_history[-10000:]
        
        logger.info(f"Signal generated for {market_data.symbol}: "
                   f"direction={direction}, confidence={signal.confidence:.2f}, "
                   f"decision={governance_decision.name}")
        
        return signal
    
    def _create_null_signal(
        self,
        market_data: MarketData,
        timestamp: datetime,
        reason: str
    ) -> GETSSignal:
        """Create a null signal when generation fails."""
        price = market_data.ohlcv['close']
        
        from .types import DisagreementGeometry, SelfDiagnosisReport
        
        return GETSSignal(
            symbol=market_data.symbol,
            timestamp=timestamp,
            direction=0,
            confidence=0.0,
            expected_edge=0.0,
            uncertainty_quantile_05=price * 0.95,
            uncertainty_quantile_95=price * 1.05,
            prediction_interval=(price * 0.95, price * 1.05),
            governance_decision=GovernanceDecision.ABSTAIN,
            decision_reasoning=reason,
            source_models=[],
            disagreement_geometry=DisagreementGeometry(
                directional_disagreement=0.0,
                magnitude_disagreement=0.0,
                uncertainty_disagreement=0.0,
                disagreement_pattern=None,
                pattern_strength=0.0,
                most_bullish_model=ModelType.KRONOS,
                most_bearish_model=ModelType.KRONOS,
                most_uncertain_model=ModelType.KRONOS,
                most_confident_model=ModelType.KRONOS,
                cross_model_stability=0.0,
                forecast_consensus_score=0.0,
                disagreement_entropy=0.0,
                model_authority_weights={}
            ),
            diagnosis_report=SelfDiagnosisReport(
                forecast_stability_score=0.0,
                perturbation_sensitivity=0.0,
                stability_passed=False,
                evidence_sufficiency_score=0.0,
                evidence_passed=False,
                contradiction_detected=False,
                contradiction_details=[reason],
                regime_mismatch_score=1.0,
                regime_passed=False,
                calibration_drift_detected=False,
                calibration_error=None,
                execution_feasible=False,
                execution_constraints=[reason],
                overall_passed=False,
                blocking_issues=[reason],
                warnings=[],
                failure_class="null_signal",
                similar_failures_count=0
            ),
            recommended_size_scale=0.0,
            abstain_recommended=True,
            abstain_reason=reason
        )
    
    def _update_regime_estimate(self, forecasts: Dict[ModelType, FoundationForecast]):
        """Update current regime estimate from foundation forecasts."""
        # Simple regime detection from volatility states
        vol_states = [
            f.volatility_state for f in forecasts.values()
            if f.volatility_state is not None
        ]
        
        if vol_states:
            avg_vol = np.mean(vol_states)
            
            if avg_vol > 0.4:
                self._current_regime = RegimeType.HIGH_VOLATILITY
            elif avg_vol < 0.15:
                self._current_regime = RegimeType.LOW_VOLATILITY
            else:
                # Could use more sophisticated detection
                self._current_regime = RegimeType.RANGING
    
    def _apply_governance(
        self,
        trading_predictions: TradingNativeHeads,
        diagnosis_report: SelfDiagnosisReport,
        disagreement_geometry: DisagreementGeometry,
        market_data: MarketData
    ) -> Tuple[GovernanceDecision, str]:
        """
        Apply governance decision logic.
        
        Can integrate with existing decision_governance system if configured.
        """
        # If integration enabled, would call out to decision_governance
        # For now, implement internal governance logic
        
        reasons = []
        
        # Check Layer 3 diagnostics
        if not diagnosis_report.overall_passed:
            if diagnosis_report.blocking_issues:
                reasons.append(f"Layer 3 blocking: {diagnosis_report.blocking_issues[0]}")
            return GovernanceDecision.ABSTAIN, "; ".join(reasons)
        
        # Check edge viability
        if trading_predictions.edge_after_cost <= 0:
            reasons.append(f"Edge after cost negative: {trading_predictions.edge_after_cost:.4f}")
            return GovernanceDecision.ABSTAIN, "; ".join(reasons)
        
        # Check execution difficulty
        if trading_predictions.execution_difficulty_score > 0.7:
            reasons.append(f"High execution difficulty: {trading_predictions.execution_difficulty_score:.2f}")
            return GovernanceDecision.RESIZE, "; ".join(reasons)
        
        # Check drawdown risk
        if trading_predictions.drawdown_risk_prob > 0.5:
            reasons.append(f"High drawdown risk: {trading_predictions.drawdown_risk_prob:.2f}")
            return GovernanceDecision.RESIZE, "; ".join(reasons)
        
        # Check for concerning disagreement patterns
        if disagreement_geometry.disagreement_pattern:
            if disagreement_geometry.disagreement_pattern in [
                DisagreementPattern.MOIRAI_HIGH_VARIANCE,
                DisagreementPattern.UNCERTAINTY_FAN_EXPANDING
            ]:
                reasons.append(f"High uncertainty pattern: {disagreement_geometry.disagreement_pattern.name}")
                return GovernanceDecision.DEFER, "; ".join(reasons)
        
        # All checks passed
        return GovernanceDecision.APPROVE, "All governance checks passed"
    
    def record_outcome(
        self,
        signal: GETSSignal,
        realized_return: float,
        market_data: Optional[MarketData] = None
    ):
        """
        Record outcome for learning and evolution.
        
        Updates:
        - Layer 3 calibration tracking
        - Layer 4 failure analysis (if prediction was poor)
        - Model authority weights
        """
        if not self._initialized:
            return
        
        # Update Layer 3 calibration for each model
        predicted_return = signal.expected_edge
        
        for model_type in signal.source_models:
            self.layer3_diagnosis.record_outcome(
                model_type, predicted_return, realized_return
            )
        
        # Check if this was a significant failure
        error = abs(predicted_return - realized_return)
        if error > 0.02 or np.sign(predicted_return) != np.sign(realized_return):
            # Record for Layer 4 failure analysis
            if market_data:
                self.layer4_evolution.record_failure(
                    model_type=signal.source_models[0] if signal.source_models else ModelType.KRONOS,
                    market_data=market_data,
                    predicted_return=predicted_return,
                    realized_return=realized_return,
                    detected_regime=self._current_regime,
                    horizon=ForecastHorizon.SHORT,  # Would need to track this
                    diagnosis_issues=signal.diagnosis_report.blocking_issues
                )
        
        logger.debug(f"Recorded outcome for {signal.symbol}: "
                    f"predicted={predicted_return:.4f}, realized={realized_return:.4f}, "
                    f"error={error:.4f}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        if not self._initialized:
            return {"status": "NOT_INITIALIZED"}
        
        return {
            "status": "OPERATIONAL",
            "current_regime": self._current_regime.value,
            "layers": {
                "layer1_perception": "ACTIVE" if self.layer1_perception._initialized else "INACTIVE",
                "layer2_representation": "ACTIVE" if self.layer2_representation._initialized else "INACTIVE",
                "layer3_diagnosis": "ACTIVE" if self.layer3_diagnosis._initialized else "INACTIVE",
                "layer4_evolution": "ACTIVE" if self.layer4_evolution._initialized else "INACTIVE",
                "layer5_governance": "ACTIVE" if self.layer5_governance._initialized else "INACTIVE",
            },
            "foundation_models": {
                mt.value: "AVAILABLE" if self.layer1_perception.is_model_available(mt) else "UNAVAILABLE"
                for mt in ModelType
            },
            "signal_history_count": len(self.signal_history),
            "governance_integration": self.dgs_integration
        }
    
    def get_disagreement_metrics(self) -> Dict[str, Any]:
        """Get current disagreement geometry metrics."""
        if not self.signal_history:
            return {}
        
        recent_signals = self.signal_history[-100:]
        
        avg_consensus = np.mean([
            s.disagreement_geometry.forecast_consensus_score
            for s in recent_signals
        ]) if recent_signals else 0.0
        
        pattern_counts = {}
        for s in recent_signals:
            if s.disagreement_geometry.disagreement_pattern:
                p = s.disagreement_geometry.disagreement_pattern.name
                pattern_counts[p] = pattern_counts.get(p, 0) + 1
        
        return {
            "avg_consensus_score": avg_consensus,
            "recent_patterns": pattern_counts,
            "model_authority_weights": (
                recent_signals[-1].disagreement_geometry.model_authority_weights
                if recent_signals else {}
            ) if recent_signals else {}
        }
    
    def get_evolution_status(self) -> Dict[str, Any]:
        """Get Layer 4 evolution system status."""
        if not self._initialized or not self.layer4_evolution:
            return {}
        
        failure_clusters = self.layer4_evolution.analyze_failures()
        pending_champions = self.layer4_evolution.get_pending_champions()
        
        return {
            "failure_clusters": len(failure_clusters),
            "cluster_details": [
                {
                    "id": c.cluster_id,
                    "count": c.count,
                    "models": [m.value for m in c.affected_models],
                    "regimes": [r.value for r in c.regimes]
                }
                for c in failure_clusters
            ],
            "pending_champions": len(pending_champions),
            "champion_details": [
                {
                    "id": c.champion_id,
                    "ic_improvement": c.ic_improvement,
                    "regime_coverage": c.regime_coverage_score
                }
                for c in pending_champions
            ]
        }
    
    def submit_champion_for_promotion(self, champion_id: str) -> Tuple[GovernanceDecision, str]:
        """
        Submit a pending champion for Layer 5 governance approval.
        
        Args:
            champion_id: ID of champion to submit
            
        Returns:
            (decision, reasoning)
        """
        if not self._initialized:
            return GovernanceDecision.ABSTAIN, "System not initialized"
        
        pending = self.layer4_evolution.get_pending_champions()
        champion = next((c for c in pending if c.champion_id == champion_id), None)
        
        if not champion:
            return GovernanceDecision.REJECT, f"Champion {champion_id} not found in pending queue"
        
        decision, record = self.layer5_governance.evaluate_champion(champion)
        
        return decision, record.promotion_reasoning
    
    def shutdown(self):
        """Gracefully shutdown GETS system."""
        logger.info("Shutting down GETS...")
        
        # Save sandbox state
        if self.layer4_evolution:
            self.layer4_evolution.save_sandbox_state()
        
        self._initialized = False
        logger.info("GETS shutdown complete")
