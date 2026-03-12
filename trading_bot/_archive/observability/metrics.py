"""
Metrics Exporter - Prometheus-compatible metrics for the trading system
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    name: str
    type: MetricType
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    help_text: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class MetricsExporter:
    """Exports metrics in Prometheus format"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.metrics: Dict[str, Metric] = {}
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        if config:
            self.config.update(config)
        logger.info("MetricsExporter initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        logger.info("MetricsExporter started")
        return True
    
    async def stop(self) -> bool:
        self._running = False
        logger.info("MetricsExporter stopped")
        return True
    
    def register_metric(self, name: str, metric_type: MetricType, help_text: str = "") -> Metric:
        metric = Metric(name=name, type=metric_type, help_text=help_text)
        self.metrics[name] = metric
        return metric
    
    def inc(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        if name in self.metrics:
            self.metrics[name].value += value
            if labels:
                self.metrics[name].labels.update(labels)
    
    def set(self, name: str, value: float, labels: Dict[str, str] = None):
        if name in self.metrics:
            self.metrics[name].value = value
            if labels:
                self.metrics[name].labels.update(labels)
    
    def export_prometheus(self) -> str:
        lines = []
        for name, metric in self.metrics.items():
            if metric.help_text:
                lines.append(f"# HELP {name} {metric.help_text}")
            lines.append(f"# TYPE {name} {metric.type.value}")
            label_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
            if label_str:
                lines.append(f"{name}{{{label_str}}} {metric.value}")
            else:
                lines.append(f"{name} {metric.value}")
        return "\n".join(lines)


_exporter: Optional[MetricsExporter] = None

def get_exporter() -> MetricsExporter:
    global _exporter
    if _exporter is None:
        _exporter = MetricsExporter()
    return _exporter

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_exporter().initialize(config)

async def start() -> bool:
    return await get_exporter().start()

async def stop() -> bool:
    return await get_exporter().stop()
