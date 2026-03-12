"""
human_layer package
"""

try:
    from .alerts import (
        Alert,
        AlertChannel,
        AlertManager,
        AlertPriority,
        get_alert_manager,
        send_alert,
        send_critical_alert,
        send_emergency_alert
    )
    from .approval import (
        ApprovalLevel,
        ApprovalRequest,
        ApprovalStatus,
        HumanApprovalGate,
        get_approval_gate,
        is_action_forbidden,
        is_approval_required,
        request_approval,
        retry
    )
    from .dashboard import (
        AlertLevel,
        DashboardData,
        DashboardPanel,
        HumanDashboard,
        get_dashboard,
        retry
    )
    from .override import (
        EmergencyStop,
        ManualOverride,
        OverrideAction,
        OverrideResult,
        emergency_stop,
        get_manual_override,
        is_trading_allowed,
        pause_trading,
        resume_trading,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in human_layer: {e}')

__all__ = [
    'Alert',
    'AlertChannel',
    'AlertLevel',
    'AlertManager',
    'AlertPriority',
    'ApprovalLevel',
    'ApprovalRequest',
    'ApprovalStatus',
    'DashboardData',
    'DashboardPanel',
    'EmergencyStop',
    'HumanApprovalGate',
    'HumanDashboard',
    'ManualOverride',
    'OverrideAction',
    'OverrideResult',
    'emergency_stop',
    'get_alert_manager',
    'get_approval_gate',
    'get_dashboard',
    'get_manual_override',
    'is_action_forbidden',
    'is_approval_required',
    'is_trading_allowed',
    'pause_trading',
    'request_approval',
    'resume_trading',
    'retry',
    'send_alert',
    'send_critical_alert',
    'send_emergency_alert',
]