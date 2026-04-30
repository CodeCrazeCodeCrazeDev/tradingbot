"""
Abstention Budget System

Fix #5: Your "Abstention" Mechanism Creates a Dangerous Default

The attack: The governance arbiter can abstain when uncertainty is too high. 
That sounds prudent. But what happens when uncertainty is always high for a 
given strategy or market condition?

Fix: Add an "abstention budget" per strategy-regime pair. Exceeding it requires 
explicit justification or triggers automatic strategy retirement.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AbstentionAction(Enum):
    """Actions when abstention budget is exceeded"""
    REQUIRE_JUSTIFICATION = "require_justification"
    REDUCE_POSITION_SIZE = "reduce_position_size"
    TRIGGER_REVIEW = "trigger_review"
    AUTO_RETIRE = "auto_retire"
    ESCALATE = "escalate"


@dataclass
class AbstentionBudgetConfig:
    """Configuration for abstention budget"""
    max_abstentions_per_month: int = 5
    max_abstentions_consecutive: int = 3
    lookback_days: int = 30
    action_on_exceeded: AbstentionAction = AbstentionAction.REQUIRE_JUSTIFICATION
    justification_required_after: int = 3
    auto_retire_after: int = 10
    
    # Position size reduction factor when budget exceeded
    position_size_reduction: float = 0.5


@dataclass
class StrategyRegimeAbstentionRecord:
    """Abstention tracking for a strategy-regime pair"""
    strategy_signature: str
    regime_hash: str
    abstention_count: int = 0
    consecutive_count: int = 0
    first_abstention: Optional[datetime] = None
    last_abstention: Optional[datetime] = None
    abstention_history: List[datetime] = field(default_factory=list)
    justification_provided: List[Tuple[datetime, str]] = field(default_factory=list)
    position_size_adjustment: float = 1.0
    retired: bool = False
    retirement_timestamp: Optional[datetime] = None
    retirement_reason: Optional[str] = None


class AbstentionBudgetTracker:
    """
    Tracks and enforces abstention budgets per strategy-regime pair.
    
    Prevents strategies from being stuck in permanent abstention by:
    1. Limiting total abstentions per time period
    2. Limiting consecutive abstentions
    3. Requiring justification when budget exceeded
    4. Triggering automatic retirement for chronic abstainers
    5. Reducing position sizes as abstentions accumulate
    """
    
    def __init__(self, config: Optional[AbstentionBudgetConfig] = None):
        self.config = config or AbstentionBudgetConfig()
        
        # Track abstentions per strategy-regime pair
        self.abstention_records: Dict[str, StrategyRegimeAbstentionRecord] = {}
        
        # Global statistics
        self.total_abstentions: int = 0
        self.strategies_retired: int = 0
        self.justifications_received: int = 0
    
    def _get_key(self, strategy_signature: str, regime_hash: str) -> str:
        """Generate unique key for strategy-regime pair"""
        return f"{strategy_signature}::{regime_hash}"
    
    def record_abstention(
        self,
        strategy_signature: str,
        regime_hash: str,
        decision_id: str,
        uncertainty_metrics: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Record an abstention decision and check budget status.
        
        Returns:
            (allowed, warning_message, adjustments)
            - allowed: Whether the abstention is within budget
            - warning_message: Message if budget concerns
            - adjustments: Position size adjustments, etc.
        """
        key = self._get_key(strategy_signature, regime_hash)
        now = datetime.utcnow()
        
        # Get or create record
        if key not in self.abstention_records:
            record = StrategyRegimeAbstentionRecord(
                strategy_signature=strategy_signature,
                regime_hash=regime_hash,
                first_abstention=now
            )
            self.abstention_records[key] = record
        else:
            record = self.abstention_records[key]
        
        # Check if retired
        if record.retired:
            return False, f"Strategy {strategy_signature} retired in regime {regime_hash}", {
                'action': 'reject',
                'retired': True
            }
        
        # Clean old history
        cutoff = now - timedelta(days=self.config.lookback_days)
        record.abstention_history = [dt for dt in record.abstention_history if dt > cutoff]
        
        # Update record
        record.abstention_count = len(record.abstention_history) + 1
        record.abstention_history.append(now)
        record.last_abstention = now
        record.consecutive_count += 1
        
        self.total_abstentions += 1
        
        # Check thresholds
        warnings = []
        adjustments = {
            'position_size_multiplier': 1.0,
            'requires_justification': False,
            'action': None
        }
        
        # Check consecutive abstentions
        if record.consecutive_count >= self.config.max_abstentions_consecutive:
            warnings.append(
                f"Consecutive abstention limit ({self.config.max_abstentions_consecutive}) exceeded"
            )
            adjustments['position_size_multiplier'] = self.config.position_size_reduction
            record.position_size_adjustment = adjustments['position_size_multiplier']
        
        # Check total abstentions
        if record.abstention_count >= self.config.max_abstentions_per_month:
            warnings.append(
                f"Monthly abstention limit ({self.config.max_abstentions_per_month}) exceeded"
            )
            adjustments['requires_justification'] = True
        
        # Check for auto-retirement
        if record.abstention_count >= self.config.auto_retire_after:
            self._retire_strategy(record, "Auto-retired due to excessive abstentions")
            adjustments['action'] = 'retire'
            return False, f"Strategy auto-retired after {record.abstention_count} abstentions", adjustments
        
        # Check for specific actions
        if record.abstention_count >= self.config.justification_required_after:
            if len(record.justification_provided) == 0 or \
               (now - record.justification_provided[-1][0]) > timedelta(days=7):
                adjustments['requires_justification'] = True
                warnings.append("Justification required for continued abstentions")
        
        # Determine if abstention is allowed
        allowed = record.abstention_count <= self.config.max_abstentions_per_month * 1.5
        
        warning_message = "; ".join(warnings) if warnings else None
        
        if warning_message:
            logger.warning(f"Abstention budget warning for {key}: {warning_message}")
        
        return allowed, warning_message, adjustments
    
    def record_non_abstention(self, strategy_signature: str, regime_hash: str):
        """Record that a decision was made (not abstained) - resets consecutive counter"""
        key = self._get_key(strategy_signature, regime_hash)
        if key in self.abstention_records:
            self.abstention_records[key].consecutive_count = 0
    
    def provide_justification(
        self,
        strategy_signature: str,
        regime_hash: str,
        justification: str,
        approved_by: str
    ) -> bool:
        """Record a justification for continued abstentions"""
        key = self._get_key(strategy_signature, regime_hash)
        if key not in self.abstention_records:
            return False
        
        record = self.abstention_records[key]
        record.justification_provided.append((datetime.utcnow(), justification))
        record.consecutive_count = 0  # Reset consecutive
        
        self.justifications_received += 1
        
        logger.info(f"Justification received for {key} from {approved_by}")
        return True
    
    def _retire_strategy(self, record: StrategyRegimeAbstentionRecord, reason: str):
        """Retire a strategy-regime pair"""
        record.retired = True
        record.retirement_timestamp = datetime.utcnow()
        record.retirement_reason = reason
        self.strategies_retired += 1
        
        logger.warning(
            f"Strategy retired: {record.strategy_signature} in {record.regime_hash}. "
            f"Reason: {reason}"
        )
    
    def get_budget_status(
        self,
        strategy_signature: str,
        regime_hash: str
    ) -> Dict[str, Any]:
        """Get current budget status for a strategy-regime pair"""
        key = self._get_key(strategy_signature, regime_hash)
        
        if key not in self.abstention_records:
            return {
                'abstention_count': 0,
                'consecutive_count': 0,
                'remaining_budget': self.config.max_abstentions_per_month,
                'retired': False,
                'requires_justification': False
            }
        
        record = self.abstention_records[key]
        remaining = max(0, self.config.max_abstentions_per_month - record.abstention_count)
        
        return {
            'abstention_count': record.abstention_count,
            'consecutive_count': record.consecutive_count,
            'remaining_budget': remaining,
            'position_size_adjustment': record.position_size_adjustment,
            'retired': record.retired,
            'retirement_reason': record.retirement_reason,
            'requires_justification': record.abstention_count >= self.config.justification_required_after,
            'justifications_provided': len(record.justification_provided),
            'first_abstention': record.first_abstention.isoformat() if record.first_abstention else None,
            'last_abstention': record.last_abstention.isoformat() if record.last_abstention else None
        }
    
    def get_all_budget_status(self) -> Dict[str, List[Dict]]:
        """Get budget status for all strategy-regime pairs"""
        at_risk = []
        retired = []
        healthy = []
        
        for key, record in self.abstention_records.items():
            status = self.get_budget_status(record.strategy_signature, record.regime_hash)
            
            if record.retired:
                retired.append(status)
            elif record.abstention_count >= self.config.max_abstentions_per_month * 0.8:
                at_risk.append(status)
            else:
                healthy.append(status)
        
        return {
            'at_risk': at_risk,
            'retired': retired,
            'healthy': healthy,
            'summary': {
                'total_tracked': len(self.abstention_records),
                'retired_count': len(retired),
                'at_risk_count': len(at_risk),
                'total_abstentions': self.total_abstentions
            }
        }


# Factory function
def create_abstention_budget_tracker(
    max_abstentions_per_month: int = 5,
    auto_retire_after: int = 10
) -> AbstentionBudgetTracker:
    """Factory function to create abstention budget tracker"""
    
    config = AbstentionBudgetConfig(
        max_abstentions_per_month=max_abstentions_per_month,
        auto_retire_after=auto_retire_after
    )
    
    return AbstentionBudgetTracker(config)
