"""
Self-Learning Trading System

A comprehensive self-learning, self-evolving, and self-optimizing system
for AI-driven market analysis, prediction, and profit generation.

This module integrates:
- Core Learning Engine: Online learning, adaptive models, pattern discovery
- Strategy Evolution: Genetic algorithms, meta-learning, strategy optimization
- Execution Optimizer: RL-based execution, adaptive routing, cost minimization
- Self-Healing System: Autonomous monitoring, error detection, auto-repair
- Distributed Learning: Knowledge sharing, collective intelligence, coordination
- Master Orchestrator: Unified control and optimization

Key Features:
- Continuous learning from every trade
- Evolutionary strategy improvement
- Reinforcement learning for execution
- Autonomous system health management
- Distributed knowledge sharing
- Collective intelligence
- Self-adaptation to market conditions
- Profit maximization focus
"""

from .core_learning_engine import (
    CoreLearningEngine,
    LearningMode,
    ModelType,
    LearningMetrics,
    MarketPattern,
    OnlinePredictor,
    EnsembleLearner,
    PatternDiscovery,
    create_learning_engine
)

from .strategy_evolution import (
    StrategyEvolutionEngine,
    StrategyDNA,
    StrategyGene,
    StrategyPerformance,
    GeneticOperators,
    StrategyPopulation,
    MetaLearner,
    EvolutionOperator,
    create_evolution_engine
)

from .execution_optimizer import (
    ExecutionOptimizer,
    ExecutionAction,
    ExecutionState,
    ExecutionExperience,
    ExecutionMetrics,
    ExecutionRL,
    AdaptiveRouter,
    create_execution_optimizer
)

from .self_healing_system import (
    SelfHealingSystem,
    HealthStatus,
    IssueType,
    RepairAction,
    HealthMetrics,
    SystemIssue,
    RepairRecord,
    ComponentMonitor,
    AutoRepair,
    create_self_healing_system
)

from .distributed_learning import (
    DistributedLearningSystem,
    KnowledgeType,
    ComponentRole,
    Knowledge,
    LearningMessage,
    KnowledgeBase,
    MessageBus,
    LearningComponent,
    CollectiveIntelligence,
    create_distributed_learning_system
)

from .master_orchestrator import (
    MasterSelfLearningOrchestrator,
    SystemMode,
    TradingDecision,
    PerformanceSnapshot,
    create_master_orchestrator
)

__all__ = [
    # Core Learning Engine
    'CoreLearningEngine',
    'LearningMode',
    'ModelType',
    'LearningMetrics',
    'MarketPattern',
    'OnlinePredictor',
    'EnsembleLearner',
    'PatternDiscovery',
    'create_learning_engine',
    
    # Strategy Evolution
    'StrategyEvolutionEngine',
    'StrategyDNA',
    'StrategyGene',
    'StrategyPerformance',
    'GeneticOperators',
    'StrategyPopulation',
    'MetaLearner',
    'EvolutionOperator',
    'create_evolution_engine',
    
    # Execution Optimizer
    'ExecutionOptimizer',
    'ExecutionAction',
    'ExecutionState',
    'ExecutionExperience',
    'ExecutionMetrics',
    'ExecutionRL',
    'AdaptiveRouter',
    'create_execution_optimizer',
    
    # Self-Healing System
    'SelfHealingSystem',
    'HealthStatus',
    'IssueType',
    'RepairAction',
    'HealthMetrics',
    'SystemIssue',
    'RepairRecord',
    'ComponentMonitor',
    'AutoRepair',
    'create_self_healing_system',
    
    # Distributed Learning
    'DistributedLearningSystem',
    'KnowledgeType',
    'ComponentRole',
    'Knowledge',
    'LearningMessage',
    'KnowledgeBase',
    'MessageBus',
    'LearningComponent',
    'CollectiveIntelligence',
    'create_distributed_learning_system',
    
    # Master Orchestrator
    'MasterSelfLearningOrchestrator',
    'SystemMode',
    'TradingDecision',
    'PerformanceSnapshot',
    'create_master_orchestrator',
]

__version__ = '1.0.0'
__author__ = 'AlphaAlgo Trading Bot'
__description__ = 'Comprehensive self-learning system for AI-driven trading'


# Quick start helper
async def quick_start(config: dict = None):
    """
    Quick start the complete self-learning system.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Initialized MasterSelfLearningOrchestrator
        
    Example:
        >>> import asyncio
        >>> from trading_bot.self_learning import quick_start
        >>> 
        >>> async def main():
        ...     orchestrator = await quick_start({
        ...         'learning': {'epsilon': 0.1},
        ...         'evolution': {'population_size': 50},
        ...         'execution': {'learning_rate': 0.001}
        ...     })
        ...     
        ...     # Analyze market and get trading decision
        ...     decision = await orchestrator.analyze_market('BTCUSDT', market_data)
        ...     
        ...     # Execute trade and learn from result
        ...     trade_result = execute_trade(decision)
        ...     await orchestrator.learn_from_trade(decision, trade_result)
        ...     
        ...     # Evolve strategies periodically
        ...     await orchestrator.evolve_strategies()
        >>> 
        >>> asyncio.run(main())
    """
    return await create_master_orchestrator(config)
