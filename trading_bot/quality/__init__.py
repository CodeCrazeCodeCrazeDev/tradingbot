"""
Data quality validation and monitoring
"""

try:
    from .data_validator import (
        DataQualityValidator,
        DataQualityMonitor,
        ValidationResult,
        ValidationLevel,
        DataQualityIssue
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed for data_validator: {e}')

__all__ = [
    'DataQualityValidator',
    'DataQualityMonitor',
    'ValidationResult',
    'ValidationLevel',
    'DataQualityIssue'
]



class QualityOrchestrator:
    """Auto-generated stub orchestrator for quality."""
    
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "QualityOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}
