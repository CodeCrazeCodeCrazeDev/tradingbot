"""
approval package
"""

try:
    from .human_in_loop import (
        ApprovalDecision,
        ApprovalRequest,
        ApprovalStatus,
        ApprovalThreshold,
        ApprovalType,
        HumanApprovalSystem,
        request_order_approval,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in approval: {e}')

__all__ = [
    'ApprovalDecision',
    'ApprovalRequest',
    'ApprovalStatus',
    'ApprovalThreshold',
    'ApprovalType',
    'HumanApprovalSystem',
    'request_order_approval',
    'retry',
]