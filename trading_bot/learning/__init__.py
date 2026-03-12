"""
Learning Module - Self-improvement capabilities for trading bots
"""

from .performance_analyzer import PerformanceAnalyzer
from .strategy_optimizer import StrategyOptimizer, LearningParameters

__all__ = ['PerformanceAnalyzer', 'StrategyOptimizer', 'LearningParameters']

# === Auto-added missing module imports for learning ===

try:
    from .distributional_rl import *  # Auto-added: was missing from __init__.py
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed for distributional_rl: {e}')


try:
    from .multi_objective_rl import *  # Auto-added: was missing from __init__.py
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed for multi_objective_rl: {e}')



class LearningOrchestrator:
    """Auto-generated stub orchestrator for learning."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}
