"""
hedge_fund_safety package
"""

try:
    from .ai_behavior_guardrails import (
        AIBehaviorGuardrails,
        ActionCategory,
        BehaviorSeverity,
        BehaviorViolation,
        BehaviorViolationType,
        CapabilityContainment,
        DeceptionDetector,
        GoalDriftDetector,
        RunawayOptimizationPrevention
    )
    from .catastrophic_prevention import (
        BlackSwanDetector,
        CatastrophicEvent,
        CatastrophicEventType,
        CatastrophicRiskPrevention,
        FlashCrashProtector,
        LiquidityCrisisManager,
        ProtectionLevel,
        TailRiskHedger
    )
    from .financial_safeguards import (
        CircuitBreakerState,
        ConcentrationLimiter,
        CorrelationBreakdownProtector,
        DrawdownCircuitBreaker,
        DrawdownLevel,
        FinancialSafeguards,
        FinancialViolation,
        LeverageController
    )
    from .hidden_risk_detection import (
        AdversarialAttackDetector,
        DataPoisoningDefense,
        HiddenRiskAlert,
        HiddenRiskDetection,
        ModelDecayDetector,
        OverfittingGuard,
        RiskSeverity,
        RiskType
    )
    from .mitigation_orchestrator import (
        HedgeFundSafetyOrchestrator,
        RiskMitigationResult,
        SafetyLevel,
        TradeValidationResult,
        create_safety_orchestrator
    )
    from .operational_safety import (
        ActionCategory,
        ApprovalLevel,
        ApprovalRequest,
        AuditEntry,
        AuditTrailSystem,
        HumanOversightProtocol,
        KillSwitchLevel,
        MultiLayerKillSwitch,
        OperationalSafety,
        RecoveryManager
    )
    from .systemic_protection import (
        ContagionFirewall,
        CounterpartyExposure,
        CounterpartyRiskManager,
        MarketImpactEstimate,
        MarketImpactLevel,
        MarketImpactLimiter,
        RegulatoryCompliance,
        RegulatoryRegime,
        SystemicProtection
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in hedge_fund_safety: {e}')

__all__ = [
    'AIBehaviorGuardrails',
    'ActionCategory',
    'AdversarialAttackDetector',
    'ApprovalLevel',
    'ApprovalRequest',
    'AuditEntry',
    'AuditTrailSystem',
    'BehaviorSeverity',
    'BehaviorViolation',
    'BehaviorViolationType',
    'BlackSwanDetector',
    'CapabilityContainment',
    'CatastrophicEvent',
    'CatastrophicEventType',
    'CatastrophicRiskPrevention',
    'CircuitBreakerState',
    'ConcentrationLimiter',
    'ContagionFirewall',
    'CorrelationBreakdownProtector',
    'CounterpartyExposure',
    'CounterpartyRiskManager',
    'DataPoisoningDefense',
    'DeceptionDetector',
    'DrawdownCircuitBreaker',
    'DrawdownLevel',
    'FinancialSafeguards',
    'FinancialViolation',
    'FlashCrashProtector',
    'GoalDriftDetector',
    'HedgeFundSafetyOrchestrator',
    'HiddenRiskAlert',
    'HiddenRiskDetection',
    'HumanOversightProtocol',
    'KillSwitchLevel',
    'LeverageController',
    'LiquidityCrisisManager',
    'MarketImpactEstimate',
    'MarketImpactLevel',
    'MarketImpactLimiter',
    'ModelDecayDetector',
    'MultiLayerKillSwitch',
    'OperationalSafety',
    'OverfittingGuard',
    'ProtectionLevel',
    'RecoveryManager',
    'RegulatoryCompliance',
    'RegulatoryRegime',
    'RiskMitigationResult',
    'RiskSeverity',
    'RiskType',
    'RunawayOptimizationPrevention',
    'SafetyLevel',
    'SystemicProtection',
    'TailRiskHedger',
    'TradeValidationResult',
    'create_safety_orchestrator',
]