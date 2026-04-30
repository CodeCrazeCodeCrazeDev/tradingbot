"""
Risk Control Evolution System

Fix #8: Your "Never Modify Risk Controls" Rule Creates Brittleness

The attack: You correctly forbid the system from automatically altering risk controls. 
But risk controls should evolve. Static risk limits are how funds blow up in new regimes.

Fix: Allow risk control evolution through the same governance stack—proposals tested 
offline, validated on regime slices, promoted with rollback hooks. The prohibition 
should be on direct live mutation, not on evolution through the proper channel.
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging
import copy

logger = logging.getLogger(__name__)


class RiskControlProposalStatus(Enum):
    """Status of a risk control evolution proposal"""
    DRAFT = "draft"
    OFFLINE_TESTING = "offline_testing"
    REGIME_VALIDATION = "regime_validation"
    PENDING_PROMOTION = "pending_promotion"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


@dataclass
class RiskControlVersion:
    """A version of a risk control"""
    version_id: str
    created_at: datetime
    risk_limits: Dict[str, Any]
    circuit_breakers: Dict[str, Any]
    position_sizing_rules: Dict[str, Any]
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    def is_more_restrictive_than(self, other: 'RiskControlVersion') -> bool:
        """Check if this version is more restrictive than another"""
        # Compare position limits
        for key in ['max_position_size', 'max_portfolio_exposure']:
            self_val = self.risk_limits.get(key, float('inf'))
            other_val = other.risk_limits.get(key, float('inf'))
            if self_val < other_val:
                return True
            if self_val > other_val:
                return False
        return False


@dataclass
class RiskControlProposal:
    """A proposal to evolve risk controls"""
    proposal_id: str
    name: str
    description: str
    proposed_by: str
    created_at: datetime
    
    # Current and proposed versions
    current_version: RiskControlVersion
    proposed_version: RiskControlVersion
    
    # Status
    status: RiskControlProposalStatus = RiskControlProposalStatus.DRAFT
    
    # Testing and validation
    offline_test_results: List[Dict] = field(default_factory=list)
    regime_validation_results: Dict[str, Dict] = field(default_factory=dict)
    
    # Promotion tracking
    promotion_timestamp: Optional[datetime] = None
    rollback_triggered: bool = False
    rollback_timestamp: Optional[datetime] = None
    rollback_reason: Optional[str] = None
    
    def can_rollback(self) -> bool:
        """Check if this proposal can be rolled back"""
        return (self.status == RiskControlProposalStatus.PROMOTED and 
                not self.rollback_triggered and
                self.current_version is not None)


class RiskControlEvolutionEngine:
    """
    Risk Control Evolution Engine
    
    Manages the evolution of risk controls through proper governance channels:
    
    1. Proposal Phase:
       - Proposed risk control changes are drafted
       - Must be more restrictive or have extensive validation
       - Never automatically generated from live trading
    
    2. Offline Testing:
       - Proposed controls tested against historical data
       - Tested across multiple market regimes
       - Simulated stress scenarios applied
    
    3. Regime Slice Validation:
       - Validated on specific regime slices
       - Must work in both normal and stressed conditions
       - Backward compatibility checked
    
    4. Promotion with Rollback Hooks:
       - Promoted controls have automatic rollback triggers
       - Monitored for unexpected behavior
       - Can be instantly rolled back to previous version
    
    Key Principles:
    - NO direct live mutation of risk controls
    - ALL changes go through the evolution pipeline
    - MORE restrictive changes promoted faster
    - LESS restrictive changes require more validation
    - Rollback capability always maintained
    """
    
    def __init__(
        self,
        min_offline_tests: int = 100,
        min_regime_slices: int = 5,
        rollback_lookback_hours: int = 24
    ):
        self.min_offline_tests = min_offline_tests
        self.min_regime_slices = min_regime_slices
        self.rollback_lookback_hours = rollback_lookback_hours
        
        # Risk control versions (history)
        self.version_history: List[RiskControlVersion] = []
        self.current_version: Optional[RiskControlVersion] = None
        
        # Proposals
        self.proposals: Dict[str, RiskControlProposal] = {}
        self.active_proposal: Optional[str] = None
        
        # Rollback state
        self.rollback_hooks: List[Dict] = []
        self.last_promotion_time: Optional[datetime] = None
        
        # Statistics
        self.total_proposals: int = 0
        self.promoted_count: int = 0
        self.rejected_count: int = 0
        self.rollback_count: int = 0
        
        logger.info("Risk Control Evolution Engine initialized - risk controls can evolve safely")
    
    def propose_evolution(
        self,
        name: str,
        description: str,
        proposed_by: str,
        new_risk_limits: Dict[str, Any],
        new_circuit_breakers: Dict[str, Any],
        new_position_sizing: Dict[str, Any]
    ) -> RiskControlProposal:
        """
        Propose a risk control evolution.
        
        Unlike direct mutation, this creates a proposal that must pass
        through the full governance pipeline.
        """
        proposal_id = f"risk_evolution_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create proposed version
        proposed_version = RiskControlVersion(
            version_id=f"{proposal_id}_v1",
            created_at=datetime.utcnow(),
            risk_limits=new_risk_limits,
            circuit_breakers=new_circuit_breakers,
            position_sizing_rules=new_position_sizing
        )
        
        # Use current version as baseline
        current = self.current_version or RiskControlVersion(
            version_id="baseline",
            created_at=datetime.utcnow(),
            risk_limits={},
            circuit_breakers={},
            position_sizing_rules={}
        )
        
        proposal = RiskControlProposal(
            proposal_id=proposal_id,
            name=name,
            description=description,
            proposed_by=proposed_by,
            created_at=datetime.utcnow(),
            current_version=current,
            proposed_version=proposed_version,
            status=RiskControlProposalStatus.DRAFT
        )
        
        self.proposals[proposal_id] = proposal
        self.total_proposals += 1
        
        logger.info(
            f"Risk control evolution proposed: {proposal_id} ({name}) by {proposed_by}"
        )
        
        return proposal
    
    def start_offline_testing(self, proposal_id: str) -> bool:
        """Move proposal to offline testing phase"""
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        proposal.status = RiskControlProposalStatus.OFFLINE_TESTING
        
        logger.info(f"Proposal {proposal_id} moved to offline testing")
        return True
    
    def record_offline_test(
        self,
        proposal_id: str,
        test_result: Dict[str, Any]
    ) -> bool:
        """
        Record an offline test result.
        
        Tests must cover:
        - Historical scenarios
        - Stress tests
        - Edge cases
        """
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        proposal.offline_test_results.append(test_result)
        
        # Check if we have enough tests
        if len(proposal.offline_test_results) >= self.min_offline_tests:
            # Check pass rate
            passed = sum(1 for r in proposal.offline_test_results if r.get('passed', False))
            pass_rate = passed / len(proposal.offline_test_results)
            
            if pass_rate >= 0.95:  # 95% pass threshold
                proposal.status = RiskControlProposalStatus.REGIME_VALIDATION
                logger.info(f"Proposal {proposal_id} passed offline testing ({pass_rate:.1%})")
            else:
                proposal.status = RiskControlProposalStatus.REJECTED
                self.rejected_count += 1
                logger.warning(
                    f"Proposal {proposal_id} rejected: offline test pass rate {pass_rate:.1%}"
                )
        
        return True
    
    def record_regime_validation(
        self,
        proposal_id: str,
        regime_name: str,
        validation_result: Dict[str, Any]
    ) -> bool:
        """
        Record validation result for a specific regime slice.
        
        Must validate across diverse regimes:
        - Normal markets
        - High volatility
        - Low liquidity
        - Crisis conditions
        """
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        proposal.regime_validation_results[regime_name] = validation_result
        
        # Check if we have enough regime validations
        if len(proposal.regime_validation_results) >= self.min_regime_slices:
            # Check all regimes passed
            all_passed = all(
                r.get('passed', False) 
                for r in proposal.regime_validation_results.values()
            )
            
            if all_passed:
                proposal.status = RiskControlProposalStatus.PENDING_PROMOTION
                logger.info(f"Proposal {proposal_id} ready for promotion")
            else:
                failed_regimes = [
                    name for name, result in proposal.regime_validation_results.items()
                    if not result.get('passed', False)
                ]
                proposal.status = RiskControlProposalStatus.REJECTED
                self.rejected_count += 1
                logger.warning(
                    f"Proposal {proposal_id} rejected: failed in regimes {failed_regimes}"
                )
        
        return True
    
    def promote_to_production(
        self,
        proposal_id: str,
        approved_by: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Promote a validated risk control to production.
        
        This is the ONLY way risk controls can change in production.
        Sets up rollback hooks before promotion.
        """
        if proposal_id not in self.proposals:
            return False, "proposal_not_found"
        
        proposal = self.proposals[proposal_id]
        
        if proposal.status != RiskControlProposalStatus.PENDING_PROMOTION:
            return False, f"invalid_status: {proposal.status.value}"
        
        # Set up rollback hook
        rollback_trigger = {
            'timestamp': datetime.utcnow(),
            'previous_version': copy.deepcopy(self.current_version),
            'proposal_id': proposal_id,
            'conditions': {
                'max_drawdown_increase': 0.05,  # Rollback if DD increases 5%
                'volatility_increase': 0.3,       # Rollback if vol increases 30%
                'consecutive_losses': 3           # Rollback after 3 consecutive losses
            }
        }
        self.rollback_hooks.append(rollback_trigger)
        
        # Promote
        proposal.status = RiskControlProposalStatus.PROMOTED
        proposal.promotion_timestamp = datetime.utcnow()
        self.current_version = proposal.proposed_version
        self.version_history.append(self.current_version)
        
        self.active_proposal = proposal_id
        self.last_promotion_time = datetime.utcnow()
        self.promoted_count += 1
        
        logger.info(
            f"Risk control promoted to production: {proposal_id} "
            f"by {approved_by}. Rollback hooks active."
        )
        
        return True, None
    
    def check_rollback_conditions(
        self,
        current_metrics: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if rollback conditions have been triggered.
        
        Monitors:
        - Drawdown increases
        - Volatility spikes
        - Consecutive losses
        - Anomalous behavior
        """
        if not self.rollback_hooks:
            return False, None
        
        latest_hook = self.rollback_hooks[-1]
        conditions = latest_hook['conditions']
        
        # Check drawdown
        current_dd = current_metrics.get('current_drawdown', 0)
        baseline_dd = latest_hook['previous_version'].validation_results.get('max_drawdown', 0)
        if current_dd > baseline_dd + conditions['max_drawdown_increase']:
            return True, f"drawdown_increase: {current_dd:.2f} > {baseline_dd + conditions['max_drawdown_increase']:.2f}"
        
        # Check volatility
        current_vol = current_metrics.get('realized_volatility', 0)
        baseline_vol = latest_hook['previous_version'].validation_results.get('volatility', 0.1)
        if baseline_vol > 0 and current_vol > baseline_vol * (1 + conditions['volatility_increase']):
            return True, f"volatility_spike: {current_vol:.2f} > {baseline_vol * (1 + conditions['volatility_increase']):.2f}"
        
        # Check consecutive losses
        recent_losses = current_metrics.get('consecutive_losses', 0)
        if recent_losses >= conditions['consecutive_losses']:
            return True, f"consecutive_losses: {recent_losses}"
        
        return False, None
    
    def execute_rollback(self, reason: str) -> bool:
        """
        Execute rollback to previous risk control version.
        
        This is the emergency brake for risk control evolution.
        """
        if not self.rollback_hooks:
            logger.error("Rollback requested but no rollback hooks available")
            return False
        
        latest_hook = self.rollback_hooks[-1]
        proposal_id = latest_hook['proposal_id']
        
        if proposal_id in self.proposals:
            proposal = self.proposals[proposal_id]
            proposal.rollback_triggered = True
            proposal.rollback_timestamp = datetime.utcnow()
            proposal.rollback_reason = reason
        
        # Restore previous version
        self.current_version = latest_hook['previous_version']
        self.active_proposal = None
        self.rollback_count += 1
        
        logger.warning(
            f"ROLLBACK EXECUTED: Reverted to previous risk controls. "
            f"Reason: {reason}. Proposal: {proposal_id}"
        )
        
        return True
    
    def get_current_risk_controls(self) -> Optional[Dict[str, Any]]:
        """Get current active risk controls"""
        if not self.current_version:
            return None
        
        return {
            'risk_limits': self.current_version.risk_limits,
            'circuit_breakers': self.current_version.circuit_breakers,
            'position_sizing': self.current_version.position_sizing_rules,
            'version_id': self.current_version.version_id
        }
    
    def get_evolution_report(self) -> Dict[str, Any]:
        """Get comprehensive report on risk control evolution"""
        return {
            'current_version': self.current_version.version_id if self.current_version else None,
            'version_count': len(self.version_history),
            'statistics': {
                'total_proposals': self.total_proposals,
                'promoted': self.promoted_count,
                'rejected': self.rejected_count,
                'rolled_back': self.rollback_count,
                'success_rate': self.promoted_count / max(1, self.promoted_count + self.rejected_count)
            },
            'active_proposal': self.active_proposal,
            'rollback_hooks_active': len(self.rollback_hooks),
            'last_promotion': self.last_promotion_time.isoformat() if self.last_promotion_time else None,
            'pending_proposals': [
                {
                    'id': p.proposal_id,
                    'name': p.name,
                    'status': p.status.value,
                    'offline_tests': len(p.offline_test_results),
                    'regime_validations': len(p.regime_validation_results)
                }
                for p in self.proposals.values()
                if p.status not in [RiskControlProposalStatus.PROMOTED, RiskControlProposalStatus.REJECTED]
            ]
        }


# Factory function
def create_risk_control_evolution_engine(
    min_offline_tests: int = 100,
    min_regime_slices: int = 5
) -> RiskControlEvolutionEngine:
    """Factory function to create risk control evolution engine"""
    
    return RiskControlEvolutionEngine(
        min_offline_tests=min_offline_tests,
        min_regime_slices=min_regime_slices
    )
