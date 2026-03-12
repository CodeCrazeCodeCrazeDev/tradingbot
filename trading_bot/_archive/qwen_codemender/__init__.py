"""
Qwen 3 8B CodeMender - AI-Powered Code Analysis, Repair & Evolution Engine

Replaces the legacy DeepSeek modules with Qwen 3 8B running locally via Ollama.
Provides autonomous code mending, optimization, safety guardrails, and self-evolution.
"""

try:
    from .codemender_core import (
        QwenCodeMender,
        CodeMenderConfig,
        InferenceBackend,
        TaskType,
        CodeChange,
        MendingTask,
        MendingResult,
        create_codemender,
        quick_fix,
        quick_validate,
    )
    from .inference_client import (
        QwenInferenceClient,
        InferenceResponse,
    )
    from .code_analyzer import (
        CodeAnalyzer,
        AnalysisReport,
        CodeSmell,
        SeverityLevel,
    )
    from .safety_guardrails import (
        SafetyGuardrails,
        SafetyLevel,
        SafetyViolation,
        ChangeRiskLevel,
        ApprovalStatus,
        ProtectedFileRegistry,
    )
    from .autonomous_mender import (
        AutonomousMender,
        MenderState,
        MenderCycle,
        MaintenanceReport,
    )
    from .self_evolution import (
        SelfEvolutionEngine,
        EvolutionProposal,
        EvolutionResult,
        EvolutionStage,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in qwen_codemender: {e}')

__all__ = [
    'AnalysisReport',
    'ApprovalStatus',
    'AutonomousMender',
    'ChangeRiskLevel',
    'CodeAnalyzer',
    'CodeChange',
    'CodeMenderConfig',
    'CodeSmell',
    'EvolutionProposal',
    'EvolutionResult',
    'EvolutionStage',
    'InferenceBackend',
    'InferenceResponse',
    'MaintenanceReport',
    'MenderCycle',
    'MenderState',
    'MendingResult',
    'MendingTask',
    'ProtectedFileRegistry',
    'QwenCodeMender',
    'QwenInferenceClient',
    'SafetyGuardrails',
    'SafetyLevel',
    'SafetyViolation',
    'SelfEvolutionEngine',
    'SeverityLevel',
    'TaskType',
    'create_codemender',
    'quick_fix',
    'quick_validate',
]
