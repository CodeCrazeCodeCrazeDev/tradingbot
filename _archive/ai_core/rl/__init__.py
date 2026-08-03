"""
rl package
"""

try:
    from .advanced_rl_agents import (
        BCQAgent,
        BEARAgent,
        CQLAgent,
        PolicyNetwork,
        QNetwork,
        RLConfig,
        VAE
    )
    from .bcq_agent import BcqAgent, create_bcq_agent
    from .bear_agent import BearAgent, create_bear_agent
    from .cql_agent import CqlAgent, create_cql_agent
    from .hierarchical_rl import (
        HierarchicalRLAgent,
        Option,
        OptionCritic,
        OptionPolicy,
        StrategySelector,
        TradingStrategy
    )
    from .magic_agent import MagicAgent, create_magic_agent
    from .mbop_agent import MbopAgent, create_mbop_agent
    from .offline_policy_eval import OfflinePolicyEval, create_offline_policy_eval
    from .offline_policy_evaluation import (
        DoublyRobust,
        FittedQEvaluation,
        OPEResult,
        OfflinePolicyEvaluator,
        WeightedImportanceSampling
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in rl: {e}')

__all__ = [
    'BCQAgent',
    'BEARAgent',
    'BcqAgent',
    'BearAgent',
    'CQLAgent',
    'CqlAgent',
    'DoublyRobust',
    'FittedQEvaluation',
    'HierarchicalRLAgent',
    'MagicAgent',
    'MbopAgent',
    'OPEResult',
    'OfflinePolicyEval',
    'OfflinePolicyEvaluator',
    'Option',
    'OptionCritic',
    'OptionPolicy',
    'PolicyNetwork',
    'QNetwork',
    'RLConfig',
    'StrategySelector',
    'TradingStrategy',
    'VAE',
    'WeightedImportanceSampling',
    'create_bcq_agent',
    'create_bear_agent',
    'create_cql_agent',
    'create_magic_agent',
    'create_mbop_agent',
    'create_offline_policy_eval',
]