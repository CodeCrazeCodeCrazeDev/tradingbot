"""
Module Registry - Backward-compatibility shim.

The authoritative component registry lives in
``trading_bot.core.unified_registry.UnifiedComponentRegistry`` and the
canonical file-scanner registry in
``trading_bot.integration.module_registry.ModuleRegistry``.

This module preserves the historical ``trading_bot.registry`` import path
used by ``trading_bot/__init__.py`` and legacy callers.
"""

import ast
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Set, Any

from trading_bot.core.unified_registry import (
    UnifiedComponentRegistry,
    get_registry,
    get_service_registry,
    create_service_registry,
    registry,
)
from trading_bot.integration.module_registry import (
    ModuleRegistry as _ScannerModuleRegistry,
)

logger = logging.getLogger(__name__)


class ModuleCategory(Enum):
    """Legacy module categories for organization."""
    # Legacy registry names
    DATA_CONNECTIVITY = "data"
    ANALYSIS_INTELLIGENCE = "analysis"
    TRADING_EXECUTION = "trading"
    RISK_SAFETY = "risk"
    # Integrator/orchestration names
    CORE = "core"
    DATA = "data"
    INTELLIGENCE = "intelligence"
    STRATEGY = "strategy"
    EXECUTION = "execution"
    RISK = "risk"
    SAFETY = "safety"
    OPTIMIZATION_EVOLUTION = "optimization_evolution"
    ORCHESTRATION_MANAGEMENT = "orchestration_management"
    SPECIALIZED_SYSTEMS = "specialized_systems"
    ORCHESTRATION = "orchestration"
    AI_ML = "ai_ml"
    QUANTUM = "quantum"
    BLOCKCHAIN = "blockchain"
    ANALYSIS = "analysis"
    MONITORING = "monitoring"
    INFRASTRUCTURE = "infrastructure"
    HEDGE_FUND = "hedge_fund"
    ELITE = "elite"
    AUTONOMOUS = "autonomous"
    EVOLUTION = "evolution"
    UTILS = "utils"
    TESTING = "testing"
    CONFIG = "config"
    OTHER = "other"
    UNKNOWN = "unknown"


class ModuleRegistry(_ScannerModuleRegistry):
    """
    Legacy ``trading_bot.registry.ModuleRegistry`` facade.

    Subclasses the canonical file-scanner registry and restores the
    historical attribute names (``modules``, ``discover_modules``,
    ``category_map``, ``_extract_dependencies``) used by older callers.
    """

    category_map: Dict[str, ModuleCategory] = {
        "data": ModuleCategory.DATA_CONNECTIVITY,
        "data_feeds": ModuleCategory.DATA_CONNECTIVITY,
        "connectivity": ModuleCategory.DATA_CONNECTIVITY,
        "analysis": ModuleCategory.ANALYSIS_INTELLIGENCE,
        "intelligence": ModuleCategory.ANALYSIS_INTELLIGENCE,
        "ml": ModuleCategory.ANALYSIS_INTELLIGENCE,
        "trading": ModuleCategory.TRADING_EXECUTION,
        "execution": ModuleCategory.TRADING_EXECUTION,
        "risk": ModuleCategory.RISK_SAFETY,
        "safety": ModuleCategory.RISK_SAFETY,
        "orchestration": ModuleCategory.ORCHESTRATION,
        "monitoring": ModuleCategory.MONITORING,
        "infrastructure": ModuleCategory.INFRASTRUCTURE,
        "utils": ModuleCategory.UTILS,
        "config": ModuleCategory.CONFIG,
        "tests": ModuleCategory.TESTING,
    }

    @property
    def modules(self) -> Dict[str, Any]:
        """Legacy alias for ``records``."""
        return self.records

    def discover_modules(self) -> int:
        """Legacy alias for ``scan()``."""
        return self.scan()

    def _extract_dependencies(self, module: Any) -> Set[str]:
        """Extract ``trading_bot.*`` imports from a module's source file."""
        file_path = getattr(module, "__file__", None)
        deps: Set[str] = set()
        if not file_path:
            return deps
        try:
            tree = ast.parse(Path(file_path).read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            return deps
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                deps.update(a.name for a in node.names if a.name.startswith("trading_bot"))
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("trading_bot"):
                deps.add(node.module)
        return deps

    @property
    def load_order(self) -> list:
        """Topologically resolved module load order (names)."""
        return getattr(self, "_load_order", [])

    @load_order.setter
    def load_order(self, value: list) -> None:
        self._load_order = value

    def resolve_dependencies(self):
        """
        Topologically sort ``self.modules`` by their ``dependencies`` sets
        and store the result in ``self.load_order``.

        Entries may be ``ModuleInfo``-like objects or plain values exposing a
        ``dependencies`` set. Cycles are tolerated: remaining modules are
        appended in insertion order.
        """
        modules = self.modules
        deps = {
            name: set(getattr(info, "dependencies", set()) or set()) & set(modules)
            for name, info in modules.items()
        }
        order = []
        resolved = set()
        pending = list(deps)
        while pending:
            progressed = False
            for name in list(pending):
                if deps[name] <= resolved:
                    order.append(name)
                    resolved.add(name)
                    pending.remove(name)
                    progressed = True
            if not progressed:
                # Cyclic dependencies: append the rest deterministically
                order.extend(pending)
                break
        self._load_order = order
        return order


def initialize_registry(config=None):
    """Initialize and return the singleton component registry."""
    return get_registry()


__all__ = [
    "ModuleRegistry",
    "ModuleCategory",
    "UnifiedComponentRegistry",
    "get_registry",
    "initialize_registry",
    "get_service_registry",
    "create_service_registry",
    "registry",
]
