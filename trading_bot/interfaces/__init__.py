"""Read-only modular-monolith interface models."""

from .adapters import DashboardRuntimeAdapter, NotificationRuntimeAdapter, ReportingRuntimeAdapter
from .read_models import ModularMonolithReadModel

__all__ = [
    "DashboardRuntimeAdapter",
    "ModularMonolithReadModel",
    "NotificationRuntimeAdapter",
    "ReportingRuntimeAdapter",
]
