"""
Decision Governance System (DGS) Integration

Main integration point that ties together all layers, planes, and memory systems.
Provides a unified interface for the complete governance stack.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import asyncio

# Core types
from .core_types import (
    GovernanceDecision, DecisionRecord, OutcomeRecord, MarketRegime,
    ExecutionFeasibility, UncertaintyProfile, FailurePattern, CapabilityHypothesis
)

# Layers
from .layer1_claim_graph import ClaimGraphConstructor
from .layer2_evidence_auditor import EvidenceSufficiencyAuditor
from .layer3_adversarial_analyst import AdversarialCounterAnalyst
from .layer4_regime_engine import RegimeApplicabilityEngine
from .layer5_counterfactual import CounterfactualSimulator
from .layer6_uncertainty import UncertaintyCalibrationLayer
from .layer7_arbiter import GovernanceArbiter, GovernanceCriteria

# Planes
from .plane_realtime import RealtimeDecisionGovernancePlane
from .plane_offline import OfflineResearchPlane
from .plane_evolution import ControlledEvolutionPlane, PromotionGate

# Memory
from .memory_system import DecisionMemory, OutcomeMemory, FailureMemory

# Capability Discovery
from .capability_discovery import CapabilityDiscoveryEngine

logger = logging.getLogger(__name__)


class DecisionGovernanceSystem:
    """
    Complete Decision Governance System integrating all 7 layers,
    3 planes, 3 memory systems, and capability discovery.
    
    Provides:
    - Real-time decision governance for trading
    - Offline analysis and failure detection
    - Controlled capability evolution
    - Continuous gap discovery
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        criteria: Optional[GovernanceCriteria] = None,
        promotion_gates: Optional[PromotionGate] = None,
        realtime_latency_ms: float = 100.0
    ):
        self.storage_path = storage_path or "dgs_data"
        
        # Initialize memory systems
        self.decision_memory = DecisionMemory(f"{self.storage_path}/decisions.db")
        self.outcome_memory = OutcomeMemory(f"{self.storage_path}/outcomes.db")
        self.failure_memory = FailureMemory(f"{self.storage_path}/failures.db")
        
        # Initialize planes
        self.realtime_plane = RealtimeDecisionGovernancePlane(
            criteria=criteria,
            decision_memory=self.decision_memory,
            max_latency_ms=realtime_latency_ms
        )
        
        self.offline_plane = OfflineResearchPlane(
            decision_memory=self.decision_memory,
            outcome_memory=self.outcome_memory,
            failure_memory=self.failure_memory
        )
        
        self.evolution_plane = ControlledEvolutionPlane(
            decision_memory=self.decision_memory,
            outcome_memory=self.outcome_memory,
            failure_memory=self.failure_memory,
            promotion_gates=promotion_gates
        )
        
        # Initialize capability discovery
        self.capability_discovery = CapabilityDiscoveryEngine(
            failure_memory=self.failure_memory,
            outcome_memory=self.outcome_memory,
            decision_memory=self.decision_memory,
            evolution_plane=self.evolution_plane
        )
        
        # System state
        self.running = False
        self.last_offline_analysis: Optional[datetime] = None
        self.last_evolution_cycle: Optional[datetime] = None
        
    async def evaluate_trade_signal(
        self,
        signal: Dict[str, Any],
        symbol: str,
        current_regime: Optional[MarketRegime] = None,
        execution_feasibility: Optional[ExecutionFeasibility] = None,
        hard_constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[GovernanceDecision, DecisionRecord]:
        """
        Evaluate a trade signal through the complete governance stack.
        
        This is the main entry point for real-time trading decisions.
        
        Args:
            signal: Trading signal with confidence, rationale, etc.
            symbol: Trading symbol
            current_regime: Current market regime characterization
            execution_feasibility: Execution feasibility assessment
            hard_constraints: Hard risk constraints
            
        Returns:
            Tuple of (decision, decision_record)
        """
        if not self.running:
            logger.warning("DGS not started - starting now")
            await self.start()
            
        # Use real-time plane for fast decision
        decision, record, latency = await self.realtime_plane.evaluate_signal(
            signal=signal,
            symbol=symbol,
            current_regime=current_regime,
            execution_feasibility=execution_feasibility,
            hard_constraints=hard_constraints
        )
        
        return decision, record
    
    async def record_trade_outcome(
        self,
        decision_id: str,
        pnl: float,
        slippage: float = 0.0,
        fill_behavior: str = "full",
        invalidation_hit: bool = False,
        realized_regime: Optional[MarketRegime] = None,
        expected_pnl: Optional[float] = None
    ) -> None:
        """
        Record the outcome of a trade for learning.
        
        Args:
            decision_id: ID of the decision that led to this trade
            pnl: Realized PnL
            slippage: Realized slippage
            fill_behavior: How the order filled (full, partial, none)
            invalidation_hit: Whether the trade hit an invalidation condition
            realized_regime: Market regime that actually occurred
            expected_pnl: PnL that was expected at decision time
        """
        decision = self.decision_memory.get_decision(decision_id)
        if not decision:
            logger.error(f"Decision {decision_id} not found")
            return
            
        # Calculate errors
        confidence_error = 0.0
        if expected_pnl is not None and expected_pnl != 0:
            confidence_error = abs(pnl - expected_pnl) / abs(expected_pnl)
        
        # Brier-like calibration error
        predicted_success_prob = decision.uncertainty_profile.overall_confidence if decision.uncertainty_profile else 0.5
        actual_success = 1.0 if pnl > 0 else 0.0
        calibration_error = abs(predicted_success_prob - actual_success)
        
        outcome = OutcomeRecord(
            decision_id=decision_id,
            realized_pnl=pnl,
            realized_slippage=slippage,
            fill_behavior=fill_behavior,
            invalidation_hit=invalidation_hit,
            regime_realized_post_entry=realized_regime,
            confidence_error=confidence_error,
            calibration_error=calibration_error
        )
        
        # Store outcome
        self.outcome_memory.record_outcome(decision_id, outcome, decision.symbol)
        self.decision_memory.mark_outcome_recorded(decision_id)
        
        # Update calibration layer
        self.realtime_plane.uncertainty_layer.record_outcome(outcome)
        
        # Record failure if appropriate
        if pnl < 0 or invalidation_hit:
            self.failure_memory.record_failure(decision, outcome)
            
        logger.info(
            f"Recorded outcome for {decision_id}: PnL={pnl:.4f}, "
            f"calibration_error={calibration_error:.4f}"
        )
    
    async def run_offline_analysis(self) -> Dict[str, Any]:
        """
        Run comprehensive offline analysis.
        
        This should be run periodically (e.g., daily or weekly)
        to analyze performance and identify improvements.
        
        Returns:
            Analysis results
        """
        results = await self.offline_plane.run_comprehensive_analysis()
        self.last_offline_analysis = datetime.utcnow()
        
        # Submit any generated hypotheses to evolution
        for proposal in results.get('sections', {}).get('upgrade_proposals', []):
            if isinstance(proposal, CapabilityHypothesis):
                self.evolution_plane.submit_capability_hypothesis(proposal)
                
        return results
    
    async def run_capability_discovery(self) -> Dict[str, Any]:
        """
        Run capability discovery cycle.
        
        Detects limitations and generates improvement hypotheses.
        
        Returns:
            Discovery results
        """
        results = await self.capability_discovery.run_discovery_cycle()
        return results
    
    async def run_evolution_cycle(self) -> Dict[str, Any]:
        """
        Run controlled evolution cycle.
        
        Validates pending hypotheses and promotes those that pass gates.
        
        Returns:
            Evolution results
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'validations': [],
            'promotions': [],
            'rollbacks': []
        }
        
        # Validate pending hypotheses
        pending = [
            h for h in self.evolution_plane.capability_registry.values()
            if not h.tested
        ]
        
        for hypothesis in pending:
            validation = await self.evolution_plane.validate_in_sandbox(hypothesis.id)
            results['validations'].append({
                'hypothesis_id': hypothesis.id,
                'status': validation.status.value,
                'improvement': validation.vs_baseline_improvement
            })
            
        # Promote validated capabilities
        validated = [
            h for h in self.evolution_plane.capability_registry.values()
            if h.tested and not h.promoted
        ]
        
        for hypothesis in validated:
            can_promote, violations = self.evolution_plane.check_promotion_gates(hypothesis.id)
            
            if can_promote:
                promotion = self.evolution_plane.promote_capability(hypothesis.id)
                results['promotions'].append(promotion)
            else:
                results['promotions'].append({
                    'capability_id': hypothesis.id,
                    'success': False,
                    'violations': violations
                })
                
        self.last_evolution_cycle = datetime.utcnow()
        
        return results
    
    async def start(self) -> None:
        """Start the governance system"""
        self.running = True
        logger.info("Decision Governance System started")
        
    async def stop(self) -> None:
        """Stop the governance system"""
        self.running = False
        logger.info("Decision Governance System stopped")
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        
        return {
            'running': self.running,
            'last_offline_analysis': self.last_offline_analysis.isoformat() if self.last_offline_analysis else None,
            'last_evolution_cycle': self.last_evolution_cycle.isoformat() if self.last_evolution_cycle else None,
            
            'realtime_plane': self.realtime_plane.get_performance_metrics(),
            'offline_plane': self.offline_plane.get_analysis_summary(),
            'evolution_plane': self.evolution_plane.get_evolution_status(),
            'capability_discovery': self.capability_discovery.get_discovery_metrics(),
            
            'memory_systems': {
                'decisions': self.decision_memory.get_decision_statistics(),
                'outcomes': len(self.outcome_memory.outcomes),
                'failure_patterns': self.failure_memory.get_statistics()
            }
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        
        return {
            'system_status': self.get_system_status(),
            'decision_statistics': self.realtime_plane.arbiter.get_decision_statistics(),
            'calibration_metrics': self.realtime_plane.uncertainty_layer.get_calibration_metrics(),
            'capability_gaps': self.failure_memory.generate_capability_gaps(),
            'discovery_report': self.capability_discovery.generate_discovery_report(),
            'evolution_report': self.evolution_plane.generate_evolution_report()
        }
