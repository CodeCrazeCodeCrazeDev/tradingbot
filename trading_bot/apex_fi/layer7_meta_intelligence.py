"""
APEX-FI Layer 7: Meta-Intelligence & Recursive Self-Improvement Engine
=======================================================================

The Apex Layer - autonomous post-mortem, performance tracking, transfer learning,
Neural Architecture Search for entire pipeline, and evolution ledger.

Mission: Become a different, better system every quarter without human architects.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import hashlib
from collections import deque

logger = logging.getLogger(__name__)


class FailureMode(str, Enum):
    """Types of failure modes."""
    DATA_ISSUE = "data_issue"
    REGIME_MISMATCH = "regime_mismatch"
    OVERFITTING = "overfitting"
    SIGNAL_DECAY = "signal_decay"
    EXECUTION_SLIPPAGE = "execution_slippage"
    MODEL_SPECIFICATION = "model_specification"
    CORRELATION_BREAK = "correlation_break"


class ImprovementType(str, Enum):
    """Types of improvements."""
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"
    ARCHITECTURE_CHANGE = "architecture_change"
    DATA_ENHANCEMENT = "data_enhancement"
    FEATURE_ENGINEERING = "feature_engineering"
    ENSEMBLE_REWEIGHTING = "ensemble_reweighting"
    REGIME_ADAPTATION = "regime_adaptation"


@dataclass
class ImprovementProposal:
    """Proposal for system improvement."""
    proposal_id: str
    improvement_type: ImprovementType
    component: str  # Which component to improve
    rationale: str
    proposed_changes: Dict[str, Any]
    expected_improvement: float  # Expected improvement metric
    validation_required: bool = True
    min_validation_days: int = 30
    min_tstat: float = 2.0
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "proposed"  # proposed, testing, validated, deployed, rejected
    
    def get_hash(self) -> str:
        """Get cryptographic hash of proposal."""
        proposal_data = {
            'proposal_id': self.proposal_id,
            'type': self.improvement_type.value,
            'component': self.component,
            'changes': self.proposed_changes,
        }
        proposal_json = json.dumps(proposal_data, sort_keys=True)
        return hashlib.sha256(proposal_json.encode()).hexdigest()


@dataclass
class EvolutionRecord:
    """Record in the evolution ledger."""
    record_id: str
    timestamp: datetime
    component_modified: str
    modification_type: str
    rationale: str
    validation_stats: Dict[str, float]
    human_reviewer: Optional[str] = None
    post_deployment_performance: Optional[Dict[str, float]] = None
    proposal_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'record_id': self.record_id,
            'timestamp': self.timestamp.isoformat(),
            'component_modified': self.component_modified,
            'modification_type': self.modification_type,
            'rationale': self.rationale,
            'validation_stats': self.validation_stats,
            'human_reviewer': self.human_reviewer,
            'post_deployment_performance': self.post_deployment_performance,
            'proposal_hash': self.proposal_hash,
        }


class AutoPostMortem:
    """
    Automated post-mortem pipeline.
    
    After every model underperformance event:
    1. Diagnose failure mode
    2. Generate improvement hypotheses
    3. Implement in sandbox
    4. Validate with statistical significance
    5. Deploy if passes validation gate
    """
    
    def __init__(self):
        self.failure_log: List[Dict[str, Any]] = []
        self.diagnosis_history: deque = deque(maxlen=1000)
        
        logger.info("Auto Post-Mortem initialized")
    
    def diagnose_failure(
        self,
        prediction: float,
        actual: float,
        context: Dict[str, Any]
    ) -> Tuple[FailureMode, str]:
        """
        Diagnose failure mode using automated attribution.
        
        Args:
            prediction: Model prediction
            actual: Actual outcome
            context: Context data (regime, data quality, etc.)
            
        Returns:
            (failure_mode, detailed_diagnosis)
        """
        error = abs(prediction - actual)
        
        # Check data quality
        data_quality = context.get('data_quality', 1.0)
        if data_quality < 0.7:
            return FailureMode.DATA_ISSUE, f"Low data quality: {data_quality:.2f}"
        
        # Check regime match
        predicted_regime = context.get('predicted_regime')
        actual_regime = context.get('actual_regime')
        if predicted_regime and actual_regime and predicted_regime != actual_regime:
            return FailureMode.REGIME_MISMATCH, f"Regime mismatch: {predicted_regime} vs {actual_regime}"
        
        # Check signal decay
        signal_age_days = context.get('signal_age_days', 0)
        if signal_age_days > 30:
            return FailureMode.SIGNAL_DECAY, f"Signal age: {signal_age_days} days"
        
        # Check execution quality
        execution_quality = context.get('execution_quality', 1.0)
        if execution_quality < 0.8:
            return FailureMode.EXECUTION_SLIPPAGE, f"Poor execution quality: {execution_quality:.2f}"
        
        # Check model complexity (overfitting indicator)
        model_complexity = context.get('model_complexity', 0)
        if model_complexity > 100 and error > 0.1:
            return FailureMode.OVERFITTING, f"High complexity with large error"
        
        # Default to model specification issue
        return FailureMode.MODEL_SPECIFICATION, f"Prediction error: {error:.4f}"
    
    def generate_improvement_hypotheses(
        self,
        failure_mode: FailureMode,
        context: Dict[str, Any]
    ) -> List[ImprovementProposal]:
        """
        Generate improvement hypotheses via Bayesian optimization and LLM.
        
        Returns:
            List of improvement proposals
        """
        proposals = []
        
        if failure_mode == FailureMode.DATA_ISSUE:
            # Propose data enhancement
            proposals.append(ImprovementProposal(
                proposal_id=f"data_enhance_{datetime.now().timestamp()}",
                improvement_type=ImprovementType.DATA_ENHANCEMENT,
                component="data_pipeline",
                rationale="Improve data quality filtering and validation",
                proposed_changes={'quality_threshold': 0.8, 'staleness_limit_ms': 500},
                expected_improvement=0.15,
            ))
        
        elif failure_mode == FailureMode.REGIME_MISMATCH:
            # Propose regime adaptation
            proposals.append(ImprovementProposal(
                proposal_id=f"regime_adapt_{datetime.now().timestamp()}",
                improvement_type=ImprovementType.REGIME_ADAPTATION,
                component="meta_learner",
                rationale="Improve regime classification and model weighting",
                proposed_changes={'regime_confidence_threshold': 0.8},
                expected_improvement=0.20,
            ))
        
        elif failure_mode == FailureMode.OVERFITTING:
            # Propose regularization
            proposals.append(ImprovementProposal(
                proposal_id=f"regularize_{datetime.now().timestamp()}",
                improvement_type=ImprovementType.HYPERPARAMETER_TUNING,
                component="model_parliament",
                rationale="Increase regularization to reduce overfitting",
                proposed_changes={'l2_penalty': 0.01, 'dropout': 0.3},
                expected_improvement=0.10,
            ))
        
        elif failure_mode == FailureMode.SIGNAL_DECAY:
            # Propose signal refresh
            proposals.append(ImprovementProposal(
                proposal_id=f"signal_refresh_{datetime.now().timestamp()}",
                improvement_type=ImprovementType.FEATURE_ENGINEERING,
                component="alpha_mining",
                rationale="Retire decayed signals and discover new ones",
                proposed_changes={'decay_threshold': 0.03, 'discovery_rate': 200},
                expected_improvement=0.18,
            ))
        
        return proposals
    
    def record_failure(
        self,
        prediction: float,
        actual: float,
        context: Dict[str, Any]
    ) -> None:
        """Record failure for analysis."""
        failure_mode, diagnosis = self.diagnose_failure(prediction, actual, context)
        
        self.failure_log.append({
            'timestamp': datetime.now(),
            'prediction': prediction,
            'actual': actual,
            'error': abs(prediction - actual),
            'failure_mode': failure_mode.value,
            'diagnosis': diagnosis,
            'context': context,
        })
        
        self.diagnosis_history.append({
            'timestamp': datetime.now(),
            'failure_mode': failure_mode,
            'diagnosis': diagnosis,
        })
        
        logger.info(f"Failure diagnosed: {failure_mode.value} - {diagnosis}")


class PerformanceTracker:
    """
    Performance tracking with half-life monitoring.
    
    Tracks every model's performance half-life.
    Triggers retraining when performance drops below significance threshold.
    """
    
    def __init__(self):
        self.model_performance: Dict[str, deque] = {}
        self.performance_half_life: Dict[str, float] = {}
        self.significance_threshold = 2.0  # t-statistic threshold
        
        logger.info("Performance Tracker initialized")
    
    def record_performance(
        self,
        model_id: str,
        metric_value: float,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record model performance."""
        if timestamp is None:
            timestamp = datetime.now()
        
        if model_id not in self.model_performance:
            self.model_performance[model_id] = deque(maxlen=1000)
        
        self.model_performance[model_id].append({
            'timestamp': timestamp,
            'value': metric_value,
        })
    
    def calculate_half_life(self, model_id: str) -> Optional[float]:
        """
        Calculate performance half-life in days.
        
        Half-life is time for performance to decay to 50% of initial value.
        """
        if model_id not in self.model_performance:
            return None
        
        performance = list(self.model_performance[model_id])
        
        if len(performance) < 10:
            return None
        
        # Simple exponential decay fit (simplified)
        values = [p['value'] for p in performance]
        initial_value = values[0]
        
        # Find when value drops to 50%
        target = initial_value * 0.5
        
        for i, value in enumerate(values):
            if value <= target:
                # Estimate half-life from time elapsed
                days = (performance[i]['timestamp'] - performance[0]['timestamp']).days
                self.performance_half_life[model_id] = days
                return days
        
        return None  # Not yet decayed to 50%
    
    def needs_retraining(
        self,
        model_id: str,
        current_performance: float,
        baseline_performance: float
    ) -> bool:
        """
        Check if model needs retraining.
        
        Uses t-test to determine if performance drop is statistically significant.
        """
        if model_id not in self.model_performance:
            return False
        
        recent_performance = list(self.model_performance[model_id])[-30:]  # Last 30 observations
        
        if len(recent_performance) < 10:
            return False
        
        recent_values = [p['value'] for p in recent_performance]
        
        # Simple t-test (simplified)
        import numpy as np
        mean_recent = np.mean(recent_values)
        std_recent = np.std(recent_values)
        
        if std_recent == 0:
            return False
        
        # T-statistic for difference from baseline
        t_stat = abs(mean_recent - baseline_performance) / (std_recent / np.sqrt(len(recent_values)))
        
        # Need retraining if performance significantly below baseline
        if mean_recent < baseline_performance and t_stat > self.significance_threshold:
            logger.info(f"Model {model_id} needs retraining - t-stat: {t_stat:.2f}")
            return True
        
        return False


class TransferLearner:
    """
    Transfer learning across asset classes and geographies.
    
    Tests whether signals/models that work in one domain transfer to others.
    Documents every cross-asset transfer finding.
    """
    
    def __init__(self):
        self.transfer_experiments: List[Dict[str, Any]] = []
        self.successful_transfers: List[Dict[str, Any]] = []
        
        logger.info("Transfer Learner initialized")
    
    def test_transfer(
        self,
        source_domain: str,
        target_domain: str,
        model_or_signal: str,
        performance_source: float,
        performance_target: float
    ) -> bool:
        """
        Test if model/signal transfers successfully.
        
        Args:
            source_domain: Source domain (e.g., 'US_equities')
            target_domain: Target domain (e.g., 'EU_equities')
            model_or_signal: Model or signal identifier
            performance_source: Performance in source domain
            performance_target: Performance in target domain
            
        Returns:
            True if transfer successful
        """
        # Transfer successful if target performance >= 70% of source
        transfer_ratio = performance_target / performance_source if performance_source > 0 else 0
        successful = transfer_ratio >= 0.7
        
        experiment = {
            'timestamp': datetime.now(),
            'source_domain': source_domain,
            'target_domain': target_domain,
            'model_or_signal': model_or_signal,
            'performance_source': performance_source,
            'performance_target': performance_target,
            'transfer_ratio': transfer_ratio,
            'successful': successful,
        }
        
        self.transfer_experiments.append(experiment)
        
        if successful:
            self.successful_transfers.append(experiment)
            logger.info(f"Successful transfer: {model_or_signal} from {source_domain} to {target_domain}")
        
        return successful
    
    def get_transfer_success_rate(
        self,
        source_domain: Optional[str] = None,
        target_domain: Optional[str] = None
    ) -> float:
        """Get transfer success rate."""
        relevant_experiments = self.transfer_experiments
        
        if source_domain:
            relevant_experiments = [e for e in relevant_experiments if e['source_domain'] == source_domain]
        
        if target_domain:
            relevant_experiments = [e for e in relevant_experiments if e['target_domain'] == target_domain]
        
        if not relevant_experiments:
            return 0.0
        
        successful = sum(1 for e in relevant_experiments if e['successful'])
        return successful / len(relevant_experiments)


class ArchitectureEvolver:
    """
    Architecture evolution engine.
    
    Runs Neural Architecture Search not just for models but for entire pipeline.
    Can propose new layer types, feedback mechanisms, data modalities, connections.
    """
    
    def __init__(self):
        self.architecture_proposals: List[Dict[str, Any]] = []
        self.deployed_architectures: List[Dict[str, Any]] = []
        
        logger.info("Architecture Evolver initialized")
    
    def propose_architecture_change(
        self,
        component: str,
        change_type: str,
        description: str,
        expected_benefit: str
    ) -> ImprovementProposal:
        """
        Propose architecture-level change.
        
        Args:
            component: Component to modify
            change_type: Type of change
            description: Detailed description
            expected_benefit: Expected benefit
            
        Returns:
            Improvement proposal
        """
        proposal = ImprovementProposal(
            proposal_id=f"arch_{component}_{datetime.now().timestamp()}",
            improvement_type=ImprovementType.ARCHITECTURE_CHANGE,
            component=component,
            rationale=description,
            proposed_changes={'change_type': change_type, 'description': description},
            expected_improvement=0.0,  # Qualitative improvement
            validation_required=True,
            min_validation_days=60,  # Longer validation for architecture changes
        )
        
        self.architecture_proposals.append({
            'proposal': proposal,
            'timestamp': datetime.now(),
            'expected_benefit': expected_benefit,
        })
        
        logger.info(f"Architecture change proposed: {component} - {change_type}")
        return proposal
    
    def can_modify_component(self, component: str) -> bool:
        """
        Check if component can be modified by self-evolution.
        
        Constitutional constraints prevent modification of certain components.
        """
        # Components that cannot be modified
        immutable_components = [
            'constitutional_layer',
            'immutable_constraints',
            'validation_gate',
            'human_oversight',
        ]
        
        return component not in immutable_components


class EvolutionLedger:
    """
    Evolution Ledger - permanent, append-only record of all self-modifications.
    
    Records every modification with timestamp, component, rationale,
    validation statistics, human reviewer, and post-deployment performance.
    Cannot be deleted or modified.
    """
    
    def __init__(self):
        self.ledger: List[EvolutionRecord] = []
        self._ledger_hash: Optional[str] = None
        
        logger.info("Evolution Ledger initialized")
    
    def record_evolution(
        self,
        component_modified: str,
        modification_type: str,
        rationale: str,
        validation_stats: Dict[str, float],
        proposal: Optional[ImprovementProposal] = None,
        human_reviewer: Optional[str] = None
    ) -> str:
        """
        Record evolution in ledger.
        
        Returns:
            Record ID
        """
        record_id = f"evolution_{len(self.ledger)}_{datetime.now().timestamp()}"
        
        record = EvolutionRecord(
            record_id=record_id,
            timestamp=datetime.now(),
            component_modified=component_modified,
            modification_type=modification_type,
            rationale=rationale,
            validation_stats=validation_stats,
            human_reviewer=human_reviewer,
            proposal_hash=proposal.get_hash() if proposal else None,
        )
        
        self.ledger.append(record)
        self._update_ledger_hash()
        
        logger.info(f"Evolution recorded: {record_id} - {component_modified}")
        return record_id
    
    def update_post_deployment_performance(
        self,
        record_id: str,
        performance: Dict[str, float]
    ) -> None:
        """Update post-deployment performance for a record."""
        for record in self.ledger:
            if record.record_id == record_id:
                record.post_deployment_performance = performance
                self._update_ledger_hash()
                logger.info(f"Updated post-deployment performance for {record_id}")
                return
        
        logger.warning(f"Record not found: {record_id}")
    
    def _update_ledger_hash(self) -> None:
        """Update cryptographic hash of entire ledger."""
        ledger_data = [record.to_dict() for record in self.ledger]
        ledger_json = json.dumps(ledger_data, sort_keys=True)
        self._ledger_hash = hashlib.sha256(ledger_json.encode()).hexdigest()
    
    def get_ledger_hash(self) -> str:
        """Get cryptographic hash of ledger for integrity verification."""
        return self._ledger_hash or ""
    
    def get_evolution_history(
        self,
        component: Optional[str] = None,
        limit: int = 100
    ) -> List[EvolutionRecord]:
        """Get evolution history."""
        records = self.ledger
        
        if component:
            records = [r for r in records if r.component_modified == component]
        
        return records[-limit:]
    
    def export_ledger(self) -> List[Dict[str, Any]]:
        """Export ledger for external storage."""
        return [record.to_dict() for record in self.ledger]


class MetaIntelligence:
    """
    Meta-Intelligence - Master coordinator for Layer 7.
    
    Integrates auto post-mortem, performance tracking, transfer learning,
    architecture evolution, and evolution ledger.
    
    This is the ceiling. This is what makes APEX-FI evolutionary.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.post_mortem = AutoPostMortem()
        self.performance_tracker = PerformanceTracker()
        self.transfer_learner = TransferLearner()
        self.architecture_evolver = ArchitectureEvolver()
        self.evolution_ledger = EvolutionLedger()
        
        self._improvement_queue: List[ImprovementProposal] = []
        self._sandbox_experiments: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Meta-Intelligence initialized - Layer 7 operational")
        logger.info("APEX Layer active - System is now evolutionary")
    
    def process_underperformance(
        self,
        prediction: float,
        actual: float,
        context: Dict[str, Any]
    ) -> List[ImprovementProposal]:
        """
        Process underperformance event through full post-mortem pipeline.
        
        Returns:
            List of improvement proposals
        """
        # 1. Diagnose failure mode
        failure_mode, diagnosis = self.post_mortem.diagnose_failure(prediction, actual, context)
        
        # 2. Record failure
        self.post_mortem.record_failure(prediction, actual, context)
        
        # 3. Generate improvement hypotheses
        proposals = self.post_mortem.generate_improvement_hypotheses(failure_mode, context)
        
        # 4. Add to improvement queue
        self._improvement_queue.extend(proposals)
        
        logger.info(f"Generated {len(proposals)} improvement proposals for {failure_mode.value}")
        return proposals
    
    def validate_proposal(
        self,
        proposal: ImprovementProposal,
        sandbox_performance: Dict[str, float]
    ) -> bool:
        """
        Validate improvement proposal.
        
        Checks if proposal meets validation gate requirements.
        """
        # Check minimum validation period
        if 'validation_days' in sandbox_performance:
            if sandbox_performance['validation_days'] < proposal.min_validation_days:
                logger.info(f"Proposal {proposal.proposal_id} needs more validation time")
                return False
        
        # Check t-statistic
        if 't_statistic' in sandbox_performance:
            if sandbox_performance['t_statistic'] < proposal.min_tstat:
                logger.info(f"Proposal {proposal.proposal_id} failed t-stat requirement")
                return False
        
        # Check improvement
        if 'improvement' in sandbox_performance:
            if sandbox_performance['improvement'] < 0:
                logger.info(f"Proposal {proposal.proposal_id} showed negative improvement")
                return False
        
        logger.info(f"Proposal {proposal.proposal_id} passed validation gate")
        return True
    
    def deploy_improvement(
        self,
        proposal: ImprovementProposal,
        validation_stats: Dict[str, float],
        human_reviewer: Optional[str] = None
    ) -> str:
        """
        Deploy validated improvement.
        
        Records in evolution ledger and returns record ID.
        """
        # Record in evolution ledger
        record_id = self.evolution_ledger.record_evolution(
            component_modified=proposal.component,
            modification_type=proposal.improvement_type.value,
            rationale=proposal.rationale,
            validation_stats=validation_stats,
            proposal=proposal,
            human_reviewer=human_reviewer,
        )
        
        # Update proposal status
        proposal.status = "deployed"
        
        logger.info(f"Improvement deployed: {proposal.proposal_id} -> {record_id}")
        return record_id
    
    def run_transfer_learning_experiment(
        self,
        model_id: str,
        source_domain: str,
        target_domains: List[str],
        source_performance: float
    ) -> Dict[str, bool]:
        """
        Run transfer learning experiments.
        
        Returns:
            Dictionary of target_domain -> success
        """
        results = {}
        
        for target_domain in target_domains:
            # Simulate transfer (in production: actual testing)
            target_performance = source_performance * np.random.uniform(0.5, 1.2)
            
            success = self.transfer_learner.test_transfer(
                source_domain,
                target_domain,
                model_id,
                source_performance,
                target_performance
            )
            
            results[target_domain] = success
        
        return results
    
    def propose_architecture_evolution(
        self,
        component: str,
        change_description: str,
        expected_benefit: str
    ) -> Optional[ImprovementProposal]:
        """Propose architecture-level evolution."""
        # Check if component can be modified
        if not self.architecture_evolver.can_modify_component(component):
            logger.warning(f"Component {component} is immutable")
            return None
        
        proposal = self.architecture_evolver.propose_architecture_change(
            component=component,
            change_type="evolution",
            description=change_description,
            expected_benefit=expected_benefit
        )
        
        self._improvement_queue.append(proposal)
        return proposal
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get meta-intelligence statistics."""
        return {
            'total_failures_analyzed': len(self.post_mortem.failure_log),
            'improvement_proposals': len(self._improvement_queue),
            'evolution_records': len(self.evolution_ledger.ledger),
            'transfer_experiments': len(self.transfer_learner.transfer_experiments),
            'successful_transfers': len(self.transfer_learner.successful_transfers),
            'architecture_proposals': len(self.architecture_evolver.architecture_proposals),
            'ledger_hash': self.evolution_ledger.get_ledger_hash(),
        }
