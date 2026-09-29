"""
Unified Evolution System
========================

Integrates recursive self-evolution with all advanced trading systems:
- AAMIS v3 (Advanced Autonomous Market Intelligence System)
- TAMIC (Time-Aware Market Intelligence Core)
- Adaptive Systems (Adaptive learning and optimization)
- Advanced Analysis (Pattern recognition and analysis)
- Advanced Features (Cutting-edge trading features)
- Advanced ML (Machine learning models)
- Adversarial Decision (Adversarial training and robustness)

This system recursively evolves and improves models across all systems,
enabling cross-system learning and knowledge transfer.
"""

from .unified_model_evolver import (
    UnifiedModelEvolver,
    ModelType,
    EvolutionStrategy,
    ModelPerformance
)

from .system_integrator import (
    SystemIntegrator,
    SystemType,
    IntegrationPoint,
    CrossSystemLearning
)

from .advanced_model_optimizer import (
    AdvancedModelOptimizer,
    OptimizationMethod,
    HyperparameterSpace
)

from .unified_orchestrator import (
    UnifiedEvolutionOrchestrator,
    quick_start_unified,
    EvolutionConfig
)

__all__ = [
    # Model Evolution
    'UnifiedModelEvolver',
    'ModelType',
    'EvolutionStrategy',
    'ModelPerformance',
    
    # System Integration
    'SystemIntegrator',
    'SystemType',
    'IntegrationPoint',
    'CrossSystemLearning',
    
    # Model Optimization
    'AdvancedModelOptimizer',
    'OptimizationMethod',
    'HyperparameterSpace',
    
    # Orchestration
    'UnifiedEvolutionOrchestrator',
    'quick_start_unified',
    'EvolutionConfig'
]
