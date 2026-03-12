"""
simulation package
"""

try:
    from .adversarial_agent import AdversarialAgent, create_adversarial_agent
    from .digital_twin import (
        CommissionModel,
        DigitalTwin,
        ExecutionResult,
        ExecutionSimulator,
        MarketTick,
        SimulatedOrder,
        SimulatedPosition,
        SimulatedTrade,
        SimulationMode,
        SlippageModel,
        ValidationResult,
        create_digital_twin
    )
    from .market_simulator import MarketSimulator, create_market_simulator
    from .self_play_trainer import SelfPlayTrainer, create_self_play_trainer
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in simulation: {e}')

__all__ = [
    'AdversarialAgent',
    'CommissionModel',
    'DigitalTwin',
    'ExecutionResult',
    'ExecutionSimulator',
    'MarketSimulator',
    'MarketTick',
    'SelfPlayTrainer',
    'SimulatedOrder',
    'SimulatedPosition',
    'SimulatedTrade',
    'SimulationMode',
    'SlippageModel',
    'ValidationResult',
    'create_adversarial_agent',
    'create_digital_twin',
    'create_market_simulator',
    'create_self_play_trainer',
]

class SimulationOrchestrator:
    """Auto-generated stub orchestrator for simulation."""
    
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
