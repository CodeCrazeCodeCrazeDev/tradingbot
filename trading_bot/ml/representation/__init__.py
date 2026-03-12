"""
representation package
"""

try:
    from .augmentations import Augmentations, create_augmentations
    from .contrastive_pretrain import (
        ContrastiveLoss,
        ContrastivePretrainer,
        FineTuner,
        TimeSeriesAugmentation,
        TimeSeriesEncoder
    )
    from .finetune import Finetune, create_finetune
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in representation: {e}')

__all__ = [
    'Augmentations',
    'ContrastiveLoss',
    'ContrastivePretrainer',
    'FineTuner',
    'Finetune',
    'TimeSeriesAugmentation',
    'TimeSeriesEncoder',
    'create_augmentations',
    'create_finetune',
]