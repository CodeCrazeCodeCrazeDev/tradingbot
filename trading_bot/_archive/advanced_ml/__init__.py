"""
advanced_ml package
"""

try:
    from .meta_learning import (
        ContinualLearning,
        FewShotLearning,
        MAML,
        MetaModel,
        Task,
        TransferLearning
    )
    from .neural_architecture_search import (
        ActivationType,
        Architecture,
        ArchitectureBuilder,
        LayerConfig,
        LayerType,
        NeuralArchitectureSearch,
        SearchSpace
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in advanced_ml: {e}')

__all__ = [
    'ActivationType',
    'Architecture',
    'ArchitectureBuilder',
    'ContinualLearning',
    'FewShotLearning',
    'LayerConfig',
    'LayerType',
    'MAML',
    'MetaModel',
    'NeuralArchitectureSearch',
    'SearchSpace',
    'Task',
    'TransferLearning',
]