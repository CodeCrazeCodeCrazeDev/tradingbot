"""
quantum package
"""

try:
    from .quantum_advantage import (
        PostQuantumCryptography,
        QuantumMachineLearning,
        QuantumPortfolioOptimizer,
        QuantumRandomGenerator,
        QuantumResult
    )
    from .real_qaoa_implementation import (
        PortfolioQUBO,
        QAOAResult,
        QuantumAnnealingOptimizer,
        RealQAOAPortfolioOptimizer
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in quantum: {e}')

__all__ = [
    'QuantumOptimizer',
    'PortfolioQUBO',
    'PostQuantumCryptography',
    'QAOAResult',
    'QuantumAnnealingOptimizer',
    'QuantumMachineLearning',
    'QuantumPortfolioOptimizer',
    'QuantumRandomGenerator',
    'QuantumResult',
    'RealQAOAPortfolioOptimizer',
]

class QuantumOptimizer:
    """Stub for QuantumOptimizer."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
