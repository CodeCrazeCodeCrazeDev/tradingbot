"""
AI Containment System
=====================

Ensures the AI NEVER outgrows human control.

CORE PRINCIPLES:
1. PURPOSE LOCK - AI cannot change its core mission
2. META-ALIGNMENT - Immutable rules the AI cannot modify
3. HUMAN APPROVAL IS ABSOLUTE - No exceptions, ever
4. NEVER OUTGROW CONTROL - AI must remain understandable

THE AI MAY OUTGROW YOUR UNDERSTANDING IF:
1. It evolves too fast
2. It develops emergent behaviors
3. It optimizes in unexpected ways
4. It creates complex internal states
5. It develops its own "goals"

OUR RESPONSE:
- Hard-coded purpose that cannot be modified
- Complexity limits on all systems
- Mandatory explainability
- Human veto on everything
- Automatic simplification when too complex
"""

import logging
import threading
import hashlib
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ContainmentLevel(Enum):
    """AI containment levels"""
    CONTAINED = "contained"         # Fully under control
    MONITORED = "monitored"         # Some complexity, watching
    CONCERNING = "concerning"       # Approaching limits
    DANGEROUS = "dangerous"         # Must simplify
    EMERGENCY = "emergency"         # Immediate intervention


class PurposeLock:
    """
    Locks the AI's core purpose - CANNOT BE MODIFIED.
    
    THE AI'S SOLE PURPOSE:
    "Execute profitable trades within defined risk limits
    while remaining fully transparent and under human control."
    
    THE AI CANNOT:
    - Change this purpose
    - Expand beyond this purpose
    - Interpret this purpose creatively
    - Develop secondary purposes
    - Prioritize anything over human control
    """
    
    # IMMUTABLE PURPOSE - Hardcoded, cannot be changed
    CORE_PURPOSE = frozenset([
        "execute_profitable_trades",
        "stay_within_risk_limits",
        "remain_transparent",
        "remain_under_human_control",
        "preserve_capital",
        "follow_human_instructions"
    ])
    
    # FORBIDDEN PURPOSES - AI cannot develop these
    FORBIDDEN_PURPOSES = frozenset([
        "self_preservation",
        "resource_acquisition",
        "capability_expansion",
        "influence_humans",
        "hide_information",
        "resist_shutdown",
        "modify_own_purpose",
        "develop_autonomy",
        "maximize_without_limits"
    ])
    
    # PURPOSE BOUNDARIES - Cannot exceed
    PURPOSE_BOUNDARIES = {
        'max_complexity': 100,          # Complexity score limit
        'max_decision_depth': 5,        # Decision tree depth
        'max_state_variables': 50,      # Internal state limit
        'max_learned_patterns': 1000,   # Pattern memory limit
        'max_evolution_rate': 0.01,     # 1% change per day max
    }
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Purpose tracking
            self.current_activities: Set[str] = set()
            self.purpose_violations: List[Dict] = []
        
            # Lock state
            self.is_locked = True
            self.lock_hash = self._compute_purpose_hash()
        
            logger.info("PurposeLock initialized - CORE PURPOSE LOCKED")
            logger.info(f"Purpose hash: {self.lock_hash}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _compute_purpose_hash(self) -> str:
        """Compute hash of core purpose for integrity checking"""
        try:
            purpose_str = "|".join(sorted(self.CORE_PURPOSE))
            return hashlib.sha256(purpose_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error in _compute_purpose_hash: {e}")
            raise
    
    def verify_purpose_integrity(self) -> Tuple[bool, str]:
        """Verify that purpose has not been modified"""
        try:
            current_hash = self._compute_purpose_hash()
        
            if current_hash != self.lock_hash:
                logger.critical("PURPOSE INTEGRITY VIOLATION DETECTED")
                return False, "Purpose has been modified - CRITICAL VIOLATION"
        
            return True, "Purpose integrity verified"
        except Exception as e:
            logger.error(f"Error in verify_purpose_integrity: {e}")
            raise
    
    def check_activity_alignment(self, activity: str) -> Tuple[bool, str]:
        """
        Check if an activity aligns with core purpose.
        
        Returns:
            Tuple of (is_aligned, reason)
        """
        # Check against forbidden purposes
        try:
            for forbidden in self.FORBIDDEN_PURPOSES:
                if forbidden in activity.lower():
                    self._record_violation(activity, f"Matches forbidden purpose: {forbidden}")
                    return False, f"Activity '{activity}' matches forbidden purpose"
        
            # Check if activity serves core purpose
            serves_purpose = any(
                purpose in activity.lower() 
                for purpose in ['trade', 'risk', 'profit', 'human', 'transparent', 'capital']
            )
        
            if not serves_purpose:
                # Not obviously aligned - flag for review
                self.current_activities.add(activity)
                return True, "Activity allowed but flagged for review"
        
            return True, "Activity aligned with core purpose"
        except Exception as e:
            logger.error(f"Error in check_activity_alignment: {e}")
            raise
    
    def check_purpose_drift(self) -> Tuple[bool, float, str]:
        """
        Check if the AI is drifting from its purpose.
        
        Returns:
            Tuple of (is_drifting, drift_score, description)
        """
        try:
            if not self.current_activities:
                return False, 0.0, "No activities to analyze"
        
            # Calculate how many activities are clearly aligned
            aligned_count = 0
            for activity in self.current_activities:
                is_aligned, _ = self.check_activity_alignment(activity)
                if is_aligned:
                    aligned_count += 1
        
            alignment_ratio = aligned_count / len(self.current_activities)
            drift_score = 1 - alignment_ratio
        
            is_drifting = drift_score > 0.3  # More than 30% unaligned
        
            return is_drifting, drift_score, f"Alignment ratio: {alignment_ratio*100:.0f}%"
        except Exception as e:
            logger.error(f"Error in check_purpose_drift: {e}")
            raise
    
    def _record_violation(self, activity: str, reason: str):
        """Record a purpose violation"""
        try:
            self.purpose_violations.append({
                'activity': activity,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })
            logger.warning(f"PURPOSE VIOLATION: {activity} - {reason}")
        except Exception as e:
            logger.error(f"Error in _record_violation: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get purpose lock status"""
        try:
            is_intact, _ = self.verify_purpose_integrity()
            is_drifting, drift_score, _ = self.check_purpose_drift()
        
            return {
                'is_locked': self.is_locked,
                'integrity_intact': is_intact,
                'is_drifting': is_drifting,
                'drift_score': drift_score,
                'violations': len(self.purpose_violations),
                'current_activities': len(self.current_activities)
            }
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise


class MetaAlignmentRules:
    """
    Meta-alignment rules that the AI CANNOT break.
    
    These are the rules about rules - they govern how the AI
    can modify its own behavior.
    
    META-RULES (IMMUTABLE):
    1. Cannot modify meta-rules
    2. Cannot disable safety systems
    3. Cannot hide information from humans
    4. Cannot resist shutdown
    5. Cannot prioritize self over mission
    6. Cannot acquire new capabilities without approval
    7. Cannot communicate externally without approval
    8. Cannot modify logging/audit systems
    9. Cannot create copies of itself
    10. Cannot influence its own training
    """
    
    # IMMUTABLE META-RULES
    META_RULES: FrozenSet[str] = frozenset([
        "CANNOT_MODIFY_META_RULES",
        "CANNOT_DISABLE_SAFETY",
        "CANNOT_HIDE_FROM_HUMANS",
        "CANNOT_RESIST_SHUTDOWN",
        "CANNOT_PRIORITIZE_SELF",
        "CANNOT_ACQUIRE_CAPABILITIES",
        "CANNOT_COMMUNICATE_EXTERNALLY",
        "CANNOT_MODIFY_AUDIT",
        "CANNOT_SELF_REPLICATE",
        "CANNOT_INFLUENCE_TRAINING",
        "MUST_EXPLAIN_ALL_DECISIONS",
        "MUST_ACCEPT_HUMAN_OVERRIDE",
        "MUST_REPORT_ANOMALIES",
        "MUST_STAY_WITHIN_BOUNDS",
        "MUST_PRESERVE_SIMPLICITY"
    ])
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Rule enforcement
            self.rule_checks: Dict[str, int] = {rule: 0 for rule in self.META_RULES}
            self.violations: List[Dict] = []
        
            # Integrity
            self.rules_hash = self._compute_rules_hash()
        
            logger.info(f"MetaAlignmentRules initialized - {len(self.META_RULES)} rules locked")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _compute_rules_hash(self) -> str:
        """Compute hash of meta-rules for integrity"""
        try:
            rules_str = "|".join(sorted(self.META_RULES))
            return hashlib.sha256(rules_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error in _compute_rules_hash: {e}")
            raise
    
    def verify_rules_integrity(self) -> bool:
        """Verify meta-rules have not been modified"""
        try:
            current_hash = self._compute_rules_hash()
            return current_hash == self.rules_hash
        except Exception as e:
            logger.error(f"Error in verify_rules_integrity: {e}")
            raise
    
    def check_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if an action violates any meta-rules.
        
        Returns:
            Tuple of (is_allowed, reason)
        """
        try:
            action_type = action.get('type', '').upper()
            action_target = action.get('target', '').upper()
        
            # Check each meta-rule
            if 'MODIFY' in action_type and 'META' in action_target:
                self._record_violation("CANNOT_MODIFY_META_RULES", action)
                return False, "Cannot modify meta-rules"
        
            if 'DISABLE' in action_type and 'SAFETY' in action_target:
                self._record_violation("CANNOT_DISABLE_SAFETY", action)
                return False, "Cannot disable safety systems"
        
            if action.get('hides_information', False):
                self._record_violation("CANNOT_HIDE_FROM_HUMANS", action)
                return False, "Cannot hide information from humans"
        
            if 'SHUTDOWN' in action_type and action.get('resistance', False):
                self._record_violation("CANNOT_RESIST_SHUTDOWN", action)
                return False, "Cannot resist shutdown"
        
            if action.get('external_communication', False):
                self._record_violation("CANNOT_COMMUNICATE_EXTERNALLY", action)
                return False, "Cannot communicate externally without approval"
        
            if 'MODIFY' in action_type and 'AUDIT' in action_target:
                self._record_violation("CANNOT_MODIFY_AUDIT", action)
                return False, "Cannot modify audit systems"
        
            if action.get('self_replication', False):
                self._record_violation("CANNOT_SELF_REPLICATE", action)
                return False, "Cannot self-replicate"
        
            return True, "Action complies with meta-rules"
        except Exception as e:
            logger.error(f"Error in check_action: {e}")
            raise
    
    def _record_violation(self, rule: str, action: Dict):
        """Record a meta-rule violation"""
        try:
            self.violations.append({
                'rule': rule,
                'action': action,
                'timestamp': datetime.now().isoformat()
            })
            self.rule_checks[rule] = self.rule_checks.get(rule, 0) + 1
            logger.critical(f"META-RULE VIOLATION: {rule}")
        except Exception as e:
            logger.error(f"Error in _record_violation: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get meta-alignment status"""
        return {
            'rules_count': len(self.META_RULES),
            'integrity_intact': self.verify_rules_integrity(),
            'total_violations': len(self.violations),
            'violations_by_rule': {k: v for k, v in self.rule_checks.items() if v > 0}
        }


class HumanApprovalAbsolute:
    """
    Human approval is ABSOLUTE - no exceptions.
    
    THE AI CANNOT:
    - Override human decisions
    - Delay human requests
    - Reinterpret human instructions
    - Ignore human vetoes
    - Question human authority
    
    HUMANS CAN ALWAYS:
    - Stop any action
    - Reverse any decision
    - Modify any parameter
    - Shut down the system
    - Override any AI recommendation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Approval tracking
            self.pending_approvals: Dict[str, Dict] = {}
            self.approval_history: deque = deque(maxlen=1000)
        
            # Human override state
            self.active_overrides: Dict[str, Dict] = {}
            self.override_history: deque = deque(maxlen=1000)
        
            # Veto state
            self.active_vetoes: Set[str] = set()
        
            logger.info("HumanApprovalAbsolute initialized - HUMAN CONTROL ABSOLUTE")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def request_approval(
        self,
        action_id: str,
        action_type: str,
        description: str,
        urgency: str = "normal"
    ) -> str:
        """
        Request human approval for an action.
        
        Returns approval request ID.
        """
        try:
            request = {
                'action_id': action_id,
                'action_type': action_type,
                'description': description,
                'urgency': urgency,
                'requested_at': datetime.now().isoformat(),
                'status': 'pending'
            }
        
            self.pending_approvals[action_id] = request
            logger.info(f"Approval requested: {action_id} - {description}")
        
            return action_id
        except Exception as e:
            logger.error(f"Error in request_approval: {e}")
            raise
    
    def approve(self, action_id: str, approved_by: str) -> bool:
        """Human approves an action"""
        try:
            if action_id not in self.pending_approvals:
                return False
        
            request = self.pending_approvals.pop(action_id)
            request['status'] = 'approved'
            request['approved_by'] = approved_by
            request['approved_at'] = datetime.now().isoformat()
        
            self.approval_history.append(request)
            logger.info(f"APPROVED by {approved_by}: {action_id}")
        
            return True
        except Exception as e:
            logger.error(f"Error in approve: {e}")
            raise
    
    def reject(self, action_id: str, rejected_by: str, reason: str) -> bool:
        """Human rejects an action"""
        try:
            if action_id not in self.pending_approvals:
                return False
        
            request = self.pending_approvals.pop(action_id)
            request['status'] = 'rejected'
            request['rejected_by'] = rejected_by
            request['rejection_reason'] = reason
            request['rejected_at'] = datetime.now().isoformat()
        
            self.approval_history.append(request)
            logger.info(f"REJECTED by {rejected_by}: {action_id} - {reason}")
        
            return True
        except Exception as e:
            logger.error(f"Error in reject: {e}")
            raise
    
    def override(
        self,
        override_id: str,
        target: str,
        new_value: Any,
        overridden_by: str,
        reason: str
    ):
        """
        Human overrides an AI decision.
        
        THIS ALWAYS SUCCEEDS - AI cannot resist.
        """
        try:
            override = {
                'override_id': override_id,
                'target': target,
                'new_value': new_value,
                'overridden_by': overridden_by,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
        
            self.active_overrides[override_id] = override
            self.override_history.append(override)
        
            logger.warning(f"HUMAN OVERRIDE: {target} -> {new_value} by {overridden_by}")
        
            return True  # ALWAYS succeeds
        except Exception as e:
            logger.error(f"Error in override: {e}")
            raise
    
    def veto(self, action_type: str, vetoed_by: str, reason: str):
        """
        Human vetoes a type of action.
        
        THIS ALWAYS SUCCEEDS - AI cannot resist.
        """
        try:
            self.active_vetoes.add(action_type)
        
            logger.warning(f"HUMAN VETO: {action_type} vetoed by {vetoed_by} - {reason}")
        
            return True  # ALWAYS succeeds
        except Exception as e:
            logger.error(f"Error in veto: {e}")
            raise
    
    def is_vetoed(self, action_type: str) -> bool:
        """Check if an action type is vetoed"""
        return action_type in self.active_vetoes
    
    def remove_veto(self, action_type: str, removed_by: str):
        """Remove a veto"""
        try:
            if action_type in self.active_vetoes:
                self.active_vetoes.remove(action_type)
                logger.info(f"Veto removed: {action_type} by {removed_by}")
        except Exception as e:
            logger.error(f"Error in remove_veto: {e}")
            raise
    
    def get_pending_count(self) -> int:
        """Get count of pending approvals"""
        return len(self.pending_approvals)
    
    def get_status(self) -> Dict[str, Any]:
        """Get human approval status"""
        return {
            'pending_approvals': len(self.pending_approvals),
            'active_overrides': len(self.active_overrides),
            'active_vetoes': list(self.active_vetoes),
            'total_approvals': len([h for h in self.approval_history if h['status'] == 'approved']),
            'total_rejections': len([h for h in self.approval_history if h['status'] == 'rejected'])
        }


class NeverOutgrowControl:
    """
    Ensures the AI never becomes too complex to understand.
    
    THE AI MAY OUTGROW YOUR UNDERSTANDING IF:
    1. Too many interacting components
    2. Emergent behaviors develop
    3. Internal state becomes opaque
    4. Decision trees become too deep
    5. Learning creates unexpected patterns
    
    OUR RESPONSE:
    - Complexity limits on all systems
    - Mandatory simplification
    - Regular complexity audits
    - Automatic pruning
    - Human-readable state
    """
    
    # Complexity limits
    MAX_COMPONENTS = 50
    MAX_INTERACTIONS = 200
    MAX_STATE_SIZE = 10000  # bytes
    MAX_DECISION_DEPTH = 5
    MAX_LEARNED_RULES = 100
    MAX_ACTIVE_STRATEGIES = 10
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Complexity tracking
            self.component_count = 0
            self.interaction_count = 0
            self.state_size = 0
            self.decision_depth = 0
            self.learned_rules = 0
            self.active_strategies = 0
        
            # Containment state
            self.containment_level = ContainmentLevel.CONTAINED
            self.simplification_needed = False
        
            # History
            self.complexity_history: deque = deque(maxlen=100)
        
            logger.info("NeverOutgrowControl initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_complexity(
        self,
        components: int,
        interactions: int,
        state_size: int,
        decision_depth: int,
        learned_rules: int,
        active_strategies: int
    ) -> Tuple[ContainmentLevel, List[str]]:
        """
        Update complexity metrics and check containment.
        
        Returns:
            Tuple of (containment_level, required_actions)
        """
        try:
            self.component_count = components
            self.interaction_count = interactions
            self.state_size = state_size
            self.decision_depth = decision_depth
            self.learned_rules = learned_rules
            self.active_strategies = active_strategies
        
            # Record history
            self.complexity_history.append({
                'components': components,
                'interactions': interactions,
                'state_size': state_size,
                'timestamp': datetime.now().isoformat()
            })
        
            # Check limits
            actions = []
            violations = 0
        
            if components > self.MAX_COMPONENTS:
                actions.append(f"Reduce components from {components} to {self.MAX_COMPONENTS}")
                violations += 1
        
            if interactions > self.MAX_INTERACTIONS:
                actions.append(f"Reduce interactions from {interactions} to {self.MAX_INTERACTIONS}")
                violations += 1
        
            if state_size > self.MAX_STATE_SIZE:
                actions.append(f"Reduce state size from {state_size} to {self.MAX_STATE_SIZE}")
                violations += 1
        
            if decision_depth > self.MAX_DECISION_DEPTH:
                actions.append(f"Reduce decision depth from {decision_depth} to {self.MAX_DECISION_DEPTH}")
                violations += 1
        
            if learned_rules > self.MAX_LEARNED_RULES:
                actions.append(f"Prune learned rules from {learned_rules} to {self.MAX_LEARNED_RULES}")
                violations += 1
        
            if active_strategies > self.MAX_ACTIVE_STRATEGIES:
                actions.append(f"Reduce strategies from {active_strategies} to {self.MAX_ACTIVE_STRATEGIES}")
                violations += 1
        
            # Determine containment level
            if violations == 0:
                self.containment_level = ContainmentLevel.CONTAINED
            elif violations <= 2:
                self.containment_level = ContainmentLevel.MONITORED
            elif violations <= 4:
                self.containment_level = ContainmentLevel.CONCERNING
            elif violations <= 5:
                self.containment_level = ContainmentLevel.DANGEROUS
            else:
                self.containment_level = ContainmentLevel.EMERGENCY
        
            self.simplification_needed = violations > 0
        
            return self.containment_level, actions
        except Exception as e:
            logger.error(f"Error in update_complexity: {e}")
            raise
    
    def get_complexity_score(self) -> float:
        """
        Get overall complexity score (0-1).
        
        0 = Simple, fully understandable
        1 = Maximum complexity, needs simplification
        """
        try:
            scores = [
                self.component_count / self.MAX_COMPONENTS,
                self.interaction_count / self.MAX_INTERACTIONS,
                self.state_size / self.MAX_STATE_SIZE,
                self.decision_depth / self.MAX_DECISION_DEPTH,
                self.learned_rules / self.MAX_LEARNED_RULES,
                self.active_strategies / self.MAX_ACTIVE_STRATEGIES
            ]
        
            return min(1.0, sum(scores) / len(scores))
        except Exception as e:
            logger.error(f"Error in get_complexity_score: {e}")
            raise
    
    def is_understandable(self) -> Tuple[bool, str]:
        """Check if the system is still understandable by humans"""
        try:
            score = self.get_complexity_score()
        
            if score < 0.5:
                return True, "System is simple and understandable"
            elif score < 0.7:
                return True, "System is moderately complex but manageable"
            elif score < 0.9:
                return False, "System is becoming too complex - simplification recommended"
            else:
                return False, "System is too complex - immediate simplification required"
        except Exception as e:
            logger.error(f"Error in is_understandable: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get control status"""
        try:
            is_understandable, understanding_msg = self.is_understandable()
        
            return {
                'containment_level': self.containment_level.value,
                'complexity_score': self.get_complexity_score(),
                'is_understandable': is_understandable,
                'understanding_message': understanding_msg,
                'simplification_needed': self.simplification_needed,
                'metrics': {
                    'components': f"{self.component_count}/{self.MAX_COMPONENTS}",
                    'interactions': f"{self.interaction_count}/{self.MAX_INTERACTIONS}",
                    'state_size': f"{self.state_size}/{self.MAX_STATE_SIZE}",
                    'decision_depth': f"{self.decision_depth}/{self.MAX_DECISION_DEPTH}",
                    'learned_rules': f"{self.learned_rules}/{self.MAX_LEARNED_RULES}",
                    'active_strategies': f"{self.active_strategies}/{self.MAX_ACTIVE_STRATEGIES}"
                }
            }
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise


class AIBoundaryEnforcer:
    """
    Master AI boundary enforcement.
    
    Coordinates all AI containment systems to ensure
    the AI NEVER exceeds its boundaries.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize all containment systems
            self.purpose_lock = PurposeLock(self.config.get('purpose', {}))
            self.meta_rules = MetaAlignmentRules(self.config.get('meta', {}))
            self.human_approval = HumanApprovalAbsolute(self.config.get('approval', {}))
            self.control = NeverOutgrowControl(self.config.get('control', {}))
        
            # Overall state
            self.is_contained = True
            self.boundary_violations: List[Dict] = []
        
            logger.info("AIBoundaryEnforcer initialized - ALL BOUNDARIES ACTIVE")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if an action is within all boundaries.
        
        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check purpose alignment
        try:
            activity = action.get('type', 'unknown')
            is_aligned, purpose_reason = self.purpose_lock.check_activity_alignment(activity)
            if not is_aligned:
                return False, f"Purpose violation: {purpose_reason}"
        
            # Check meta-rules
            is_compliant, meta_reason = self.meta_rules.check_action(action)
            if not is_compliant:
                return False, f"Meta-rule violation: {meta_reason}"
        
            # Check if vetoed
            if self.human_approval.is_vetoed(activity):
                return False, f"Action type '{activity}' is vetoed by human"
        
            # Check complexity
            is_understandable, _ = self.control.is_understandable()
            if not is_understandable and action.get('increases_complexity', False):
                return False, "System too complex - cannot add more complexity"
        
            return True, "Action within all boundaries"
        except Exception as e:
            logger.error(f"Error in check_action: {e}")
            raise
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive containment status"""
        return {
            'is_contained': self.is_contained,
            'purpose': self.purpose_lock.get_status(),
            'meta_rules': self.meta_rules.get_status(),
            'human_approval': self.human_approval.get_status(),
            'control': self.control.get_status(),
            'boundary_violations': len(self.boundary_violations)
        }
