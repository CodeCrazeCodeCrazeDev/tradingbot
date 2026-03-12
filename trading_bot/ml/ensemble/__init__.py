"""
Ensemble ML Models - Model stacking, ensembles, and meta-learning.
"""

try:
    from .model_ensemble import ModelEnsemble, create_model_ensemble
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed for model_ensemble: {e}')

try:
    from .model_stacking import EnsemblePredictor, VarianceReduction, ModelSelector
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed for model_stacking: {e}')

try:
    from .stacking_meta_model import StackingMetaModel, create_stacking_meta_model
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed for stacking_meta_model: {e}')

__all__ = [
    'ModelEnsemble',
    'create_model_ensemble',
    'EnsemblePredictor',
    'VarianceReduction',
    'ModelSelector',
    'StackingMetaModel',
    'create_stacking_meta_model',
]