"""
Ingestion Module
============================================================

Auto-generated integration file.
"""

# collector
try:
    from .collector import (
        CollectorManager,
    )
except ImportError as e:
    # collector not available
    pass

# orchestrator
try:
    from .orchestrator import (
        IngestionOrchestrator,
        OrchestratorConfig,
    )
except ImportError as e:
    # orchestrator not available
    pass

# orderbook_builder
try:
    from .orderbook_builder import (
        OrderBookManager,
    )
except ImportError as e:
    # orderbook_builder not available
    pass

# replay_engine
try:
    from .replay_engine import (
        ReplayEngine,
    )
except ImportError as e:
    # replay_engine not available
    pass

# storage
try:
    from .storage import (
        StorageManager,
    )
except ImportError as e:
    # storage not available
    pass

__all__ = [
    'CollectorManager',
    'IngestionOrchestrator',
    'OrchestratorConfig',
    'OrderBookManager',
    'ReplayEngine',
    'StorageManager',
]
