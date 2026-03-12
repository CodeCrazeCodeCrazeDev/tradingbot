"""
federated package
"""

try:
    from .global_model import GlobalModel, create_global_model
    from .local_trainer import LocalTrainer, create_local_trainer
    from .secure_aggregator import SecureAggregator, create_secure_aggregator
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in federated: {e}')

__all__ = [
    'GlobalModel',
    'LocalTrainer',
    'SecureAggregator',
    'create_global_model',
    'create_local_trainer',
    'create_secure_aggregator',
]