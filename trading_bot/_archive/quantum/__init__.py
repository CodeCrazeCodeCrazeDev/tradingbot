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