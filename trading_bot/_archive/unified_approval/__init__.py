"""
Unified Approval System - Centralized Human-Bot Communication

This module consolidates all approval systems into one unified interface.
Provides web dashboard, CLI tool, and API for managing bot approval requests.

Author: AlphaAlgo Trading System
Version: 1.0.0
"""

from .approval_hub import (
    UnifiedApprovalHub,
    ApprovalRequest,
    ApprovalDecision,
    get_approval_hub,
)

from .approval_types import (
    ApprovalCategory,
    ApprovalPriority,
    RiskLevel,
    ApprovalStatus,
)

from .notification_system import (
    NotificationSystem,
    NotificationChannel,
)

from .pipeline_approval import (
    PipelineApprovalManager,
    ApprovalRulesEngine,
    ApprovalRule,
    CLIApprovalInterface,
)

__all__ = [
    'UnifiedApprovalHub',
    'ApprovalRequest',
    'ApprovalDecision',
    'ApprovalCategory',
    'ApprovalPriority',
    'RiskLevel',
    'ApprovalStatus',
    'NotificationSystem',
    'NotificationChannel',
    'get_approval_hub',
    'PipelineApprovalManager',
    'ApprovalRulesEngine',
    'ApprovalRule',
    'CLIApprovalInterface',
]

__version__ = '1.0.0'
