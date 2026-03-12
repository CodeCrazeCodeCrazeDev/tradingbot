"""
Automatic Strategy Optimizer
Continuously optimizes trading parameters using genetic algorithms and Bayesian optimization
"""

from .strategy_optimizer import (
    StrategyOptimizer,
    OptimizationMethod,
    OptimizationResult,
    GeneticOptimizer,
    BayesianOptimizer,
    GridSearchOptimizer
)

__all__ = [
    'AutoOptimizerOrchestrator',
    'StrategyOptimizer',
    'OptimizationMethod',
    'OptimizationResult',
    'GeneticOptimizer',
    'BayesianOptimizer',
    'GridSearchOptimizer'
]

class AutoOptimizer:
    """Auto-generated stub orchestrator for module integration."""
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self._initialized = True
    
    async def start(self):
        """Start the orchestrator."""
        self.running = True
    
    async def stop(self):
        """Stop the orchestrator."""
        self.running = False
    
    def get_status(self):
        """Get orchestrator status."""
        return {"running": self.running, "initialized": self._initialized}



class AutoOptimizerOrchestrator:
    """Stub for AutoOptimizerOrchestrator."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
