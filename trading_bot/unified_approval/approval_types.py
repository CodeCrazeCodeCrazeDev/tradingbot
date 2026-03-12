"""
Approval Types and Enums - Unified Approval System

Defines all approval categories, priorities, risk levels, and statuses.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import timedelta


import logging

logger = logging.getLogger(__name__)

class ApprovalCategory(Enum):
    """Categories of approval requests"""
    # Trading Actions
    TRADE_EXECUTION = "trade_execution"
    POSITION_MANAGEMENT = "position_management"
    RISK_OVERRIDE = "risk_override"
    LIVE_TRADING = "live_trading"
    BROKER_CONNECTION = "broker_connection"
    
    # System Changes
    CODE_DEPLOYMENT = "code_deployment"
    RISK_PARAMETERS = "risk_parameters"
    STRATEGY_CHANGE = "strategy_change"
    CONFIG_CHANGE = "config_change"
    GOVERNANCE_CHANGE = "governance_change"
    
    # Evolution & Learning
    STRATEGY_DEPLOYMENT = "strategy_deployment"
    MODEL_DEPLOYMENT = "model_deployment"
    PARAMETER_OPTIMIZATION = "parameter_optimization"
    CODE_IMPROVEMENT = "code_improvement"
    
    # Data & Integration
    DATA_SOURCE = "data_source"
    EXTERNAL_API = "external_api"
    INDICATOR_ADDITION = "indicator_addition"
    
    # Critical Operations
    DATA_DELETION = "data_deletion"
    EMERGENCY_ACTION = "emergency_action"
    SYSTEM_RESTART = "system_restart"
    SECURITY_CHANGE = "security_change"


class ApprovalPriority(Enum):
    """Priority levels for approval requests"""
    CRITICAL = 1  # Requires immediate attention
    HIGH = 2      # Important, respond within 1 hour
    MEDIUM = 3    # Standard priority, respond within 24 hours
    LOW = 4       # Can wait, respond within 7 days


class RiskLevel(Enum):
    """Risk assessment levels"""
    CRITICAL = "critical"  # Extreme risk, requires multiple approvals
    HIGH = "high"          # High risk, requires careful review
    MEDIUM = "medium"      # Moderate risk, standard review
    LOW = "low"            # Low risk, can be auto-approved
    MINIMAL = "minimal"    # Negligible risk


class ApprovalStatus(Enum):
    """Status of approval requests"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    CONDITIONAL = "conditional"  # Approved with conditions


@dataclass
class ApprovalThresholds:
    """Thresholds for auto-approval"""
    category: ApprovalCategory
    auto_approve_below: Optional[float] = None
    auto_reject_above: Optional[float] = None
    require_approval_above: float = 0
    timeout: timedelta = timedelta(hours=24)
    default_on_timeout: ApprovalStatus = ApprovalStatus.REJECTED
    required_approvers: int = 1
    require_2fa: bool = False


# Default thresholds for each category
DEFAULT_THRESHOLDS: Dict[ApprovalCategory, ApprovalThresholds] = {
    # Trading Actions - Conservative thresholds
    ApprovalCategory.TRADE_EXECUTION: ApprovalThresholds(
        category=ApprovalCategory.TRADE_EXECUTION,
        auto_approve_below=10000,  # Auto-approve orders < $10k
        auto_reject_above=1000000,  # Auto-reject orders > $1M
        require_approval_above=50000,  # Require approval > $50k
        timeout=timedelta(minutes=30),
        default_on_timeout=ApprovalStatus.REJECTED
    ),
    
    ApprovalCategory.POSITION_MANAGEMENT: ApprovalThresholds(
        category=ApprovalCategory.POSITION_MANAGEMENT,
        auto_approve_below=5000,
        require_approval_above=25000,
        timeout=timedelta(hours=1)
    ),
    
    ApprovalCategory.RISK_OVERRIDE: ApprovalThresholds(
        category=ApprovalCategory.RISK_OVERRIDE,
        require_approval_above=0,  # Always require approval
        timeout=timedelta(hours=12),
        required_approvers=2,  # Require 2 approvals
        require_2fa=True
    ),
    
    ApprovalCategory.LIVE_TRADING: ApprovalThresholds(
        category=ApprovalCategory.LIVE_TRADING,
        require_approval_above=0,  # Always require approval
        timeout=timedelta(days=7),  # No rush
        required_approvers=1,
        require_2fa=True
    ),
    
    ApprovalCategory.BROKER_CONNECTION: ApprovalThresholds(
        category=ApprovalCategory.BROKER_CONNECTION,
        require_approval_above=0,
        timeout=timedelta(hours=24),
        require_2fa=True
    ),
    
    # System Changes - Require approval
    ApprovalCategory.CODE_DEPLOYMENT: ApprovalThresholds(
        category=ApprovalCategory.CODE_DEPLOYMENT,
        require_approval_above=0,
        timeout=timedelta(days=3),
        required_approvers=1
    ),
    
    ApprovalCategory.RISK_PARAMETERS: ApprovalThresholds(
        category=ApprovalCategory.RISK_PARAMETERS,
        require_approval_above=0,
        timeout=timedelta(days=1),
        required_approvers=2,
        require_2fa=True
    ),
    
    ApprovalCategory.STRATEGY_CHANGE: ApprovalThresholds(
        category=ApprovalCategory.STRATEGY_CHANGE,
        require_approval_above=0,
        timeout=timedelta(days=7)
    ),
    
    ApprovalCategory.CONFIG_CHANGE: ApprovalThresholds(
        category=ApprovalCategory.CONFIG_CHANGE,
        require_approval_above=0,
        timeout=timedelta(hours=24)
    ),
    
    ApprovalCategory.GOVERNANCE_CHANGE: ApprovalThresholds(
        category=ApprovalCategory.GOVERNANCE_CHANGE,
        require_approval_above=0,
        timeout=timedelta(days=30),  # Long timeout for governance
        required_approvers=2,
        require_2fa=True
    ),
    
    # Evolution & Learning - Moderate thresholds
    ApprovalCategory.STRATEGY_DEPLOYMENT: ApprovalThresholds(
        category=ApprovalCategory.STRATEGY_DEPLOYMENT,
        require_approval_above=0,
        timeout=timedelta(days=7)
    ),
    
    ApprovalCategory.MODEL_DEPLOYMENT: ApprovalThresholds(
        category=ApprovalCategory.MODEL_DEPLOYMENT,
        require_approval_above=0,
        timeout=timedelta(days=7)
    ),
    
    ApprovalCategory.PARAMETER_OPTIMIZATION: ApprovalThresholds(
        category=ApprovalCategory.PARAMETER_OPTIMIZATION,
        auto_approve_below=0.05,  # Auto-approve < 5% change
        require_approval_above=0.1,  # Require approval > 10% change
        timeout=timedelta(days=3)
    ),
    
    ApprovalCategory.CODE_IMPROVEMENT: ApprovalThresholds(
        category=ApprovalCategory.CODE_IMPROVEMENT,
        require_approval_above=0,
        timeout=timedelta(days=7)
    ),
    
    # Data & Integration - Lower risk
    ApprovalCategory.DATA_SOURCE: ApprovalThresholds(
        category=ApprovalCategory.DATA_SOURCE,
        auto_approve_below=0,  # Can auto-approve free sources
        require_approval_above=0,  # But still review
        timeout=timedelta(days=3)
    ),
    
    ApprovalCategory.EXTERNAL_API: ApprovalThresholds(
        category=ApprovalCategory.EXTERNAL_API,
        require_approval_above=0,
        timeout=timedelta(days=1),
        require_2fa=True
    ),
    
    ApprovalCategory.INDICATOR_ADDITION: ApprovalThresholds(
        category=ApprovalCategory.INDICATOR_ADDITION,
        auto_approve_below=0,
        require_approval_above=0,
        timeout=timedelta(days=3)
    ),
    
    # Critical Operations - Strictest thresholds
    ApprovalCategory.DATA_DELETION: ApprovalThresholds(
        category=ApprovalCategory.DATA_DELETION,
        require_approval_above=0,
        timeout=timedelta(days=7),
        required_approvers=2,
        require_2fa=True
    ),
    
    ApprovalCategory.EMERGENCY_ACTION: ApprovalThresholds(
        category=ApprovalCategory.EMERGENCY_ACTION,
        require_approval_above=0,
        timeout=timedelta(minutes=5),  # Fast response needed
        default_on_timeout=ApprovalStatus.APPROVED  # Auto-approve on timeout
    ),
    
    ApprovalCategory.SYSTEM_RESTART: ApprovalThresholds(
        category=ApprovalCategory.SYSTEM_RESTART,
        require_approval_above=0,
        timeout=timedelta(hours=1)
    ),
    
    ApprovalCategory.SECURITY_CHANGE: ApprovalThresholds(
        category=ApprovalCategory.SECURITY_CHANGE,
        require_approval_above=0,
        timeout=timedelta(days=7),
        required_approvers=2,
        require_2fa=True
    ),
}


def get_threshold(category: ApprovalCategory) -> ApprovalThresholds:
    """Get threshold configuration for a category"""
    return DEFAULT_THRESHOLDS.get(
        category,
        ApprovalThresholds(category=category)
    )


def get_priority_from_category(category: ApprovalCategory) -> ApprovalPriority:
    """Determine priority based on category"""
    try:
        critical_categories = {
            ApprovalCategory.EMERGENCY_ACTION,
            ApprovalCategory.LIVE_TRADING,
            ApprovalCategory.RISK_OVERRIDE,
        }
    
        high_categories = {
            ApprovalCategory.TRADE_EXECUTION,
            ApprovalCategory.BROKER_CONNECTION,
            ApprovalCategory.RISK_PARAMETERS,
            ApprovalCategory.SECURITY_CHANGE,
        }
    
        low_categories = {
            ApprovalCategory.INDICATOR_ADDITION,
            ApprovalCategory.PARAMETER_OPTIMIZATION,
        }
    
        if category in critical_categories:
            return ApprovalPriority.CRITICAL
        elif category in high_categories:
            return ApprovalPriority.HIGH
        elif category in low_categories:
            return ApprovalPriority.LOW
        else:
            return ApprovalPriority.MEDIUM
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in get_priority_from_category: {e}")
        raise


def get_risk_from_category(category: ApprovalCategory) -> RiskLevel:
    """Determine risk level based on category"""
    try:
        critical_risk = {
            ApprovalCategory.GOVERNANCE_CHANGE,
            ApprovalCategory.DATA_DELETION,
            ApprovalCategory.SECURITY_CHANGE,
        }
    
        high_risk = {
            ApprovalCategory.LIVE_TRADING,
            ApprovalCategory.RISK_OVERRIDE,
            ApprovalCategory.RISK_PARAMETERS,
            ApprovalCategory.CODE_DEPLOYMENT,
        }
    
        low_risk = {
            ApprovalCategory.INDICATOR_ADDITION,
            ApprovalCategory.DATA_SOURCE,
        }
    
        if category in critical_risk:
            return RiskLevel.CRITICAL
        elif category in high_risk:
            return RiskLevel.HIGH
        elif category in low_risk:
            return RiskLevel.LOW
        else:
            return RiskLevel.MEDIUM
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in get_risk_from_category: {e}")
        raise
