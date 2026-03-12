"""
meta_learning package
"""

try:
    from .maml import Maml, create_maml
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in meta_learning: {e}')

__all__ = [
    'Maml',
    'create_maml',
]