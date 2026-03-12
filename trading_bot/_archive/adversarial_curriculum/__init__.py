"""
adversarial_curriculum package
"""

try:
    from .anti_cheat import (
        AntiCheatSystem,
        BehaviorAnalyzer,
        ExploitDetector,
        OverfitDetector
    )
    from .core_types import (
        AgentAction,
        AgentState,
        AntiCheatViolation,
        AntiCheatViolationType,
        CurriculumLevel,
        EpisodeResult,
        FailureDiagnostic,
        FailureMode,
        HardeningMechanism,
        LevelConfig,
        MarketRegime,
        MarketState,
        PromotionGate,
        PromotionResult,
        get_level_config,
        get_promotion_gate
    )
    from .curriculum_orchestrator import (
        AgentInterface,
        CurriculumOrchestrator,
        RandomAgent,
        SimpleRuleAgent,
        TrainingSession,
        quick_start
    )
    from .failure_handler import FailureAnalyzer, RegressionManager, RetrainingScheduler
    from .market_environment import (
        AdversarialMarketEnvironment,
        AdversarialMechanisms,
        CrisisSimulator,
        ExecutionSimulator,
        NoiseInjector,
        RegimeSwitcher
    )
    from .promotion_system import (
        OODTester,
        PromotionEvaluator,
        RobustnessChecker,
        StatisticalValidator
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in adversarial_curriculum: {e}')

__all__ = [
    'AdversarialMarketEnvironment',
    'AdversarialMechanisms',
    'AgentAction',
    'AgentInterface',
    'AgentState',
    'AntiCheatSystem',
    'AntiCheatViolation',
    'AntiCheatViolationType',
    'BehaviorAnalyzer',
    'CrisisSimulator',
    'CurriculumLevel',
    'CurriculumOrchestrator',
    'EpisodeResult',
    'ExecutionSimulator',
    'ExploitDetector',
    'FailureAnalyzer',
    'FailureDiagnostic',
    'FailureMode',
    'HardeningMechanism',
    'LevelConfig',
    'MarketRegime',
    'MarketState',
    'NoiseInjector',
    'OODTester',
    'OverfitDetector',
    'PromotionEvaluator',
    'PromotionGate',
    'PromotionResult',
    'RandomAgent',
    'RegimeSwitcher',
    'RegressionManager',
    'RetrainingScheduler',
    'RobustnessChecker',
    'SimpleRuleAgent',
    'StatisticalValidator',
    'TrainingSession',
    'get_level_config',
    'get_promotion_gate',
    'quick_start',
]