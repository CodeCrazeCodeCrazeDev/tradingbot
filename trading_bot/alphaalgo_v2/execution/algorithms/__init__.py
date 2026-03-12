"""
algorithms package
"""

try:
    from .smart import ExecutionAlgorithm, ExecutionPlan, SmartOrderRouter
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in algorithms: {e}')

__all__ = [
    'ExecutionAlgorithm',
    'ExecutionPlan',
    'SmartOrderRouter',
]