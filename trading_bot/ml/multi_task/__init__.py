"""
multi_task package
"""

try:
    from .mtl_model import MtlModel, create_mtl_model
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in multi_task: {e}')

__all__ = [
    'MtlModel',
    'create_mtl_model',
]