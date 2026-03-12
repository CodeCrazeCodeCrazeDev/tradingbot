"""
adversarial package
"""

try:
    from .adversarial_trainer import AdversarialTrainer, create_adversarial_trainer
    from .robustness_tester import RobustnessTester, create_robustness_tester
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in adversarial: {e}')

__all__ = [
    'AdversarialTrainer',
    'RobustnessTester',
    'create_adversarial_trainer',
    'create_robustness_tester',
]