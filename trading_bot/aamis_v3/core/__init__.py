"""
Core Module
============================================================

Auto-generated integration file.
"""

# metacognitive_awareness
try:
    from .metacognitive_awareness import (
        SelfReflectionEngine,
    )
except ImportError as e:
    # metacognitive_awareness not available
    pass

# multimodal_fusion
try:
    from .multimodal_fusion import (
        MultiModalFusionEngine,
    )
except ImportError as e:
    # multimodal_fusion not available
    pass

# neuro_symbolic_engine
try:
    from .neuro_symbolic_engine import (
        NeuroSymbolicEngine,
    )
except ImportError as e:
    # neuro_symbolic_engine not available
    pass

# self_evolving_intelligence
try:
    from .self_evolving_intelligence import (
        FeatureEngineer,
    )
except ImportError as e:
    # self_evolving_intelligence not available
    pass

__all__ = [
    'FeatureEngineer',
    'MultiModalFusionEngine',
    'NeuroSymbolicEngine',
    'SelfReflectionEngine',
]
