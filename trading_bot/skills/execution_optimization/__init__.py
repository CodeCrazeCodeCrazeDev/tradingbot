"""
Execution Optimization Module
============================================================

Auto-generated integration file.
"""

# maker_taker
try:
    from .maker_taker import (
        MakerTakerDecisionEngine,
    )
except ImportError as e:
    # maker_taker not available
    pass

# participation_rate
try:
    from .participation_rate import (
        ParticipationRateController,
    )
except ImportError as e:
    # participation_rate not available
    pass

__all__ = [
    'MakerTakerDecisionEngine',
    'ParticipationRateController',
]
