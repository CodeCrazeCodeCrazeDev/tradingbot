"""
Module Registry - legacy file-scanner registry API.

``ModuleInfo`` is the per-module record the historical
``trading_bot.registry`` module exposed; ``ModuleRegistry`` and
``ModuleCategory`` live in the package ``__init__`` and are re-exported
here for the ``trading_bot.registry.module_registry`` import path.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Set

from . import ModuleCategory, ModuleRegistry


@dataclass
class ModuleInfo:
    """Metadata record for a discovered module."""

    name: str
    path: str = ""
    category: "ModuleCategory" = None  # ModuleCategory.UNKNOWN at call sites
    dependencies: Set[str] = field(default_factory=set)
    module: Optional[Any] = None
    class_name: Optional[str] = None
    initialized: bool = False
    error: Optional[str] = None

    def __post_init__(self):
        if self.category is None:
            self.category = ModuleCategory.OTHER


__all__ = ["ModuleInfo", "ModuleRegistry", "ModuleCategory"]
