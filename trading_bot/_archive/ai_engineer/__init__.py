"""
ai_engineer package - Powered by Qwen 3 8B CodeMender
"""

try:
    from .autonomous_orchestrator import (
        AuditResult,
        AutonomousOrchestrator,
        CyclePhase,
        Priority,
        WindsurfContext,
        main,
        retry
    )
    from .safeguards import (
        ApprovalStatus,
        BranchIsolation,
        ChangeMonitor,
        ChangeRiskLevel,
        CodeChange,
        ComplianceAuditor,
        ContainerizedEnvironment,
        IntegratedSafeguardSystem,
        RoleBasedAccessControl,
        SafeguardSystem,
        SandboxMode,
        VersionCheckpoint
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in ai_engineer: {e}')

# Backward-compatible aliases
try:
    from trading_bot.qwen_codemender import (
        QwenCodeMender,
        CodeMenderConfig,
        QwenInferenceClient,
        InferenceBackend,
        TaskType,
        MendingTask,
    )
    # Aliases for backward compatibility
    DeepSeekEngineer = QwenCodeMender
    DeepSeekConfig = CodeMenderConfig
    DeepSeekInferenceClient = QwenInferenceClient
    EngineeringTask = MendingTask
except ImportError:
    pass

__all__ = [
    'ApprovalStatus',
    'AuditResult',
    'AutonomousOrchestrator',
    'BranchIsolation',
    'ChangeMonitor',
    'ChangeRiskLevel',
    'CodeChange',
    'CodeMenderConfig',
    'ComplianceAuditor',
    'ContainerizedEnvironment',
    'CyclePhase',
    'DeepSeekConfig',
    'DeepSeekEngineer',
    'DeepSeekInferenceClient',
    'EngineeringTask',
    'InferenceBackend',
    'IntegratedSafeguardSystem',
    'Priority',
    'QwenCodeMender',
    'QwenInferenceClient',
    'RoleBasedAccessControl',
    'SafeguardSystem',
    'SandboxMode',
    'TaskType',
    'VersionCheckpoint',
    'WindsurfContext',
    'main',
    'retry',
]