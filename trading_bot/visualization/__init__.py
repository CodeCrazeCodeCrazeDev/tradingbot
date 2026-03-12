"""
visualization package
"""

try:
    from .anomaly_viz import (
        AnnotatedEvent,
        Anomaly,
        AnomalyDetector,
        AnomalyType,
        AnomalyVisualizer,
        Severity
    )
    from .chart_visualizer import ChartVisualizer
    from .ml_visualizer import MLVisualizer
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in visualization: {e}')

__all__ = [
    'AnnotatedEvent',
    'Anomaly',
    'AnomalyDetector',
    'AnomalyType',
    'AnomalyVisualizer',
    'ChartVisualizer',
    'MLVisualizer',
    'Severity',
]

class VisualizationOrchestrator:
    """Auto-generated stub orchestrator for visualization."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}
