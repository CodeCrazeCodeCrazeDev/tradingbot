"""
Architecture Core - Meta-architecture coordination and system topology management.

Provides architecture-level orchestration, module discovery, dependency resolution,
and system topology management for the unified trading platform.
"""

import logging
import os
import importlib
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """Architecture layers in the unified system."""
    INFRASTRUCTURE = "layer_0_infrastructure"
    OBSERVABILITY = "layer_1_observability"
    CONNECTIVITY = "layer_2_connectivity"
    DATA_FOUNDATION = "layer_3_data_foundation"
    INTELLIGENCE = "layer_4_intelligence"
    SIGNAL = "layer_5_signal"
    RISK_SAFETY = "layer_6_risk_safety"
    DECISION = "layer_7_decision"
    EXECUTION = "layer_8_execution"
    ORCHESTRATION = "layer_9_orchestration"
    GOVERNANCE = "layer_10_governance"
    CROSS_CUTTING = "cross_cutting"


class ModuleStatus(Enum):
    """Status of a discovered module."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    STUB = "stub"
    DEPRECATED = "deprecated"


@dataclass
class ModuleDescriptor:
    """Describes a discovered module in the architecture."""
    name: str
    path: str
    layer: LayerType
    status: ModuleStatus = ModuleStatus.INACTIVE
    has_init: bool = False
    file_count: int = 0
    classes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    description: str = ""
    last_scanned: Optional[datetime] = None


# Module-to-layer mapping
MODULE_LAYER_MAP = {
    # Layer 0: Infrastructure
    "infrastructure": LayerType.INFRASTRUCTURE,
    "performance": LayerType.INFRASTRUCTURE,
    "profiling": LayerType.INFRASTRUCTURE,
    "deployment": LayerType.INFRASTRUCTURE,
    "devops": LayerType.INFRASTRUCTURE,
    "distributed": LayerType.INFRASTRUCTURE,
    "ops": LayerType.INFRASTRUCTURE,
    "production": LayerType.INFRASTRUCTURE,
    "upgrades": LayerType.INFRASTRUCTURE,
    # Layer 1: Observability
    "monitoring": LayerType.OBSERVABILITY,
    "observability": LayerType.OBSERVABILITY,
    "log_system": LayerType.OBSERVABILITY,
    "telemetry": LayerType.OBSERVABILITY,
    "alerts": LayerType.OBSERVABILITY,
    "dashboard": LayerType.OBSERVABILITY,
    "diagnostics": LayerType.OBSERVABILITY,
    "error_handling": LayerType.OBSERVABILITY,
    "event_monitoring": LayerType.OBSERVABILITY,
    "notifications": LayerType.OBSERVABILITY,
    "quality": LayerType.OBSERVABILITY,
    "reporting": LayerType.OBSERVABILITY,
    "surveillance": LayerType.OBSERVABILITY,
    "system_health": LayerType.OBSERVABILITY,
    "trade_journal": LayerType.OBSERVABILITY,
    "visualization": LayerType.OBSERVABILITY,
    "voice_assistant": LayerType.OBSERVABILITY,
    "mobile": LayerType.OBSERVABILITY,
    "mobile_app": LayerType.OBSERVABILITY,
    # Layer 2: Connectivity
    "connectivity": LayerType.CONNECTIVITY,
    "connectivity_unified": LayerType.CONNECTIVITY,
    "connectors": LayerType.CONNECTIVITY,
    "brokers": LayerType.CONNECTIVITY,
    "broker": LayerType.CONNECTIVITY,
    "ingestion": LayerType.CONNECTIVITY,
    "internet_access": LayerType.CONNECTIVITY,
    "streaming": LayerType.CONNECTIVITY,
    "api": LayerType.CONNECTIVITY,
    "bridges": LayerType.CONNECTIVITY,
    "core_api": LayerType.CONNECTIVITY,
    # Layer 3: Data Foundation
    "data": LayerType.DATA_FOUNDATION,
    "data_feeds": LayerType.DATA_FOUNDATION,
    "data_sources": LayerType.DATA_FOUNDATION,
    "database": LayerType.DATA_FOUNDATION,
    "event_pipeline": LayerType.DATA_FOUNDATION,
    "features": LayerType.DATA_FOUNDATION,
    "persistence": LayerType.DATA_FOUNDATION,
    "realtime": LayerType.DATA_FOUNDATION,
    "sentiment": LayerType.DATA_FOUNDATION,
    "social": LayerType.DATA_FOUNDATION,
    "trading_calendar": LayerType.DATA_FOUNDATION,
    "calendar": LayerType.DATA_FOUNDATION,
    "alternative_data": LayerType.DATA_FOUNDATION,
    "blockchain": LayerType.DATA_FOUNDATION,
    "crypto": LayerType.DATA_FOUNDATION,
    "macro": LayerType.DATA_FOUNDATION,
    # Layer 4: Intelligence
    "ml": LayerType.INTELLIGENCE,
    "ai_core": LayerType.INTELLIGENCE,
    "ai": LayerType.INTELLIGENCE,
    "ai_engineer": LayerType.INTELLIGENCE,
    "alpha_engine": LayerType.INTELLIGENCE,
    "alpha_research": LayerType.INTELLIGENCE,
    "analysis": LayerType.INTELLIGENCE,
    "analysis_unified": LayerType.INTELLIGENCE,
    "analytics": LayerType.INTELLIGENCE,
    "cognitive_architecture": LayerType.INTELLIGENCE,
    "deepchart": LayerType.INTELLIGENCE,
    "elite_ai_system": LayerType.INTELLIGENCE,
    "eternal_evolution": LayerType.INTELLIGENCE,
    "evolution_layer": LayerType.INTELLIGENCE,
    "explainability": LayerType.INTELLIGENCE,
    "improvement_agent": LayerType.INTELLIGENCE,
    "improvements": LayerType.INTELLIGENCE,
    "indicators": LayerType.INTELLIGENCE,
    "innovations": LayerType.INTELLIGENCE,
    "intel": LayerType.INTELLIGENCE,
    "learning": LayerType.INTELLIGENCE,
    "market_intelligence": LayerType.INTELLIGENCE,
    "market_student": LayerType.INTELLIGENCE,
    "market_teacher": LayerType.INTELLIGENCE,
    "meta_learning": LayerType.INTELLIGENCE,
    "multimodal": LayerType.INTELLIGENCE,
    "optimization": LayerType.INTELLIGENCE,
    "psychology": LayerType.INTELLIGENCE,
    "quantum": LayerType.INTELLIGENCE,
    "qwen_codemender": LayerType.INTELLIGENCE,
    "reasoning": LayerType.INTELLIGENCE,
    "recursive_improvement": LayerType.INTELLIGENCE,
    "research": LayerType.INTELLIGENCE,
    "research_ingestion": LayerType.INTELLIGENCE,
    "self_healing_ai": LayerType.INTELLIGENCE,
    "self_improvement": LayerType.INTELLIGENCE,
    "self_learning": LayerType.INTELLIGENCE,
    "self_mastery": LayerType.INTELLIGENCE,
    "sentient_core": LayerType.INTELLIGENCE,
    "skills": LayerType.INTELLIGENCE,
    "superintelligence": LayerType.INTELLIGENCE,
    "systems_ai": LayerType.INTELLIGENCE,
    "tamic": LayerType.INTELLIGENCE,
    "advanced_analysis": LayerType.INTELLIGENCE,
    "advanced_features": LayerType.INTELLIGENCE,
    "advanced_ml": LayerType.INTELLIGENCE,
    "autonomous_learner": LayerType.INTELLIGENCE,
    "aamis_v3": LayerType.INTELLIGENCE,
    "adaptive_systems": LayerType.INTELLIGENCE,
    "self_concepts": LayerType.INTELLIGENCE,
    # Layer 5: Signal
    "signals": LayerType.SIGNAL,
    "strategies": LayerType.SIGNAL,
    "strategy": LayerType.SIGNAL,
    "opportunity_scanner": LayerType.SIGNAL,
    "institutional_entry": LayerType.SIGNAL,
    "arbitrage": LayerType.SIGNAL,
    "backtesting": LayerType.SIGNAL,
    "derivatives": LayerType.SIGNAL,
    "filters": LayerType.SIGNAL,
    "market_making": LayerType.SIGNAL,
    "profit_maximizer": LayerType.SIGNAL,
    "simulation": LayerType.SIGNAL,
    # Layer 6: Risk & Safety
    "risk": LayerType.RISK_SAFETY,
    "risk_management": LayerType.RISK_SAFETY,
    "risk_unified": LayerType.RISK_SAFETY,
    "safety": LayerType.RISK_SAFETY,
    "reality_gates": LayerType.RISK_SAFETY,
    "hedge_fund_safety": LayerType.RISK_SAFETY,
    "hedge_fund": LayerType.RISK_SAFETY,
    "hedging": LayerType.RISK_SAFETY,
    "msos": LayerType.RISK_SAFETY,
    "critical_fixes": LayerType.RISK_SAFETY,
    "portfolio": LayerType.RISK_SAFETY,
    "security": LayerType.RISK_SAFETY,
    "stealth_safety": LayerType.RISK_SAFETY,
    "validation": LayerType.RISK_SAFETY,
    "wealth": LayerType.RISK_SAFETY,
    # Layer 7: Decision
    "adversarial_curriculum": LayerType.DECISION,
    "adversarial_decision": LayerType.DECISION,
    "agents": LayerType.DECISION,
    "decision_layer": LayerType.DECISION,
    "verification": LayerType.DECISION,
    # Layer 8: Execution
    "execution": LayerType.EXECUTION,
    "exit_strategies": LayerType.EXECUTION,
    "exits": LayerType.EXECUTION,
    "hft": LayerType.EXECUTION,
    "position": LayerType.EXECUTION,
    "trading": LayerType.EXECUTION,
    # Layer 9: Orchestration
    "orchestrator": LayerType.ORCHESTRATION,
    "brain": LayerType.ORCHESTRATION,
    "core": LayerType.ORCHESTRATION,
    "elite_system": LayerType.ORCHESTRATION,
    "system": LayerType.ORCHESTRATION,
    "system_supervisor": LayerType.ORCHESTRATION,
    "unified_architecture": LayerType.ORCHESTRATION,
    "unified_system": LayerType.ORCHESTRATION,
    "ultimate_system": LayerType.ORCHESTRATION,
    "ultimate_production": LayerType.ORCHESTRATION,
    "ultimate_architecture": LayerType.ORCHESTRATION,
    "ultimate_bot": LayerType.ORCHESTRATION,
    "autonomous": LayerType.ORCHESTRATION,
    "autonomous_pipeline": LayerType.ORCHESTRATION,
    "auto_optimizer": LayerType.ORCHESTRATION,
    "global_expansion": LayerType.ORCHESTRATION,
    "alphaalgo_v2": LayerType.ORCHESTRATION,
    # Layer 10: Governance
    "alphaalgo_core": LayerType.GOVERNANCE,
    "alphaalgo_institutional": LayerType.GOVERNANCE,
    "approval": LayerType.GOVERNANCE,
    "ultimate_approval": LayerType.GOVERNANCE,
    "audit": LayerType.GOVERNANCE,
    "compliance": LayerType.GOVERNANCE,
    "governance": LayerType.GOVERNANCE,
    "human_layer": LayerType.GOVERNANCE,
    "institutional": LayerType.GOVERNANCE,
    "unified_approval": LayerType.GOVERNANCE,
    # Cross-cutting
    "config": LayerType.CROSS_CUTTING,
    "utils": LayerType.CROSS_CUTTING,
    "models": LayerType.CROSS_CUTTING,
    "schemas": LayerType.CROSS_CUTTING,
    "tools": LayerType.CROSS_CUTTING,
    "integration": LayerType.CROSS_CUTTING,
    "integrations": LayerType.CROSS_CUTTING,
    "testing": LayerType.CROSS_CUTTING,
    "documentation": LayerType.CROSS_CUTTING,
    "automation": LayerType.CROSS_CUTTING,
}


class ArchitectureManager:
    """
    Meta-architecture coordination and system topology management.

    Discovers modules, resolves dependencies, and provides a complete
    view of the system architecture.
    """

    def __init__(self, base_path: Optional[str] = None):
        self._base_path = base_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._modules: Dict[str, ModuleDescriptor] = {}
        self._scan_timestamp: Optional[datetime] = None
        logger.info("ArchitectureManager initialized, base: %s", self._base_path)

    def scan_modules(self) -> Dict[str, ModuleDescriptor]:
        """Scan the trading_bot directory and discover all modules."""
        self._modules.clear()
        trading_bot_path = self._base_path

        if not os.path.isdir(trading_bot_path):
            logger.error("Base path not found: %s", trading_bot_path)
            return self._modules

        for entry in os.listdir(trading_bot_path):
            full_path = os.path.join(trading_bot_path, entry)
            if not os.path.isdir(full_path):
                continue
            if entry.startswith((".", "_", "__")):
                continue

            has_init = os.path.exists(os.path.join(full_path, "__init__.py"))
            file_count = sum(1 for f in os.listdir(full_path)
                             if f.endswith(".py") and not f.startswith("__"))

            layer = MODULE_LAYER_MAP.get(entry, LayerType.CROSS_CUTTING)
            status = ModuleStatus.ACTIVE if has_init and file_count > 0 else ModuleStatus.STUB

            self._modules[entry] = ModuleDescriptor(
                name=entry,
                path=full_path,
                layer=layer,
                status=status,
                has_init=has_init,
                file_count=file_count,
                last_scanned=datetime.utcnow(),
            )

        self._scan_timestamp = datetime.utcnow()
        logger.info("Scanned %d modules", len(self._modules))
        return self._modules

    def get_module(self, name: str) -> Optional[ModuleDescriptor]:
        """Get a specific module descriptor."""
        return self._modules.get(name)

    def get_modules_by_layer(self, layer: LayerType) -> List[ModuleDescriptor]:
        """Get all modules in a specific layer."""
        return [m for m in self._modules.values() if m.layer == layer]

    def get_layer_summary(self) -> Dict[str, Dict]:
        """Get a summary of modules per layer."""
        summary = {}
        for layer in LayerType:
            modules = self.get_modules_by_layer(layer)
            summary[layer.value] = {
                "module_count": len(modules),
                "active": sum(1 for m in modules if m.status == ModuleStatus.ACTIVE),
                "stubs": sum(1 for m in modules if m.status == ModuleStatus.STUB),
                "total_files": sum(m.file_count for m in modules),
                "modules": [m.name for m in modules],
            }
        return summary

    def find_missing_inits(self) -> List[str]:
        """Find module directories missing __init__.py."""
        return [m.name for m in self._modules.values() if not m.has_init]

    def find_empty_modules(self) -> List[str]:
        """Find modules with no Python files (besides __init__.py)."""
        return [m.name for m in self._modules.values() if m.file_count == 0]

    def get_architecture_health(self) -> Dict:
        """Get overall architecture health metrics."""
        if not self._modules:
            self.scan_modules()

        total = len(self._modules)
        active = sum(1 for m in self._modules.values() if m.status == ModuleStatus.ACTIVE)
        stubs = sum(1 for m in self._modules.values() if m.status == ModuleStatus.STUB)
        missing_inits = len(self.find_missing_inits())
        empty = len(self.find_empty_modules())

        return {
            "total_modules": total,
            "active_modules": active,
            "stub_modules": stubs,
            "missing_inits": missing_inits,
            "empty_modules": empty,
            "health_score": active / total if total > 0 else 0,
            "layers_populated": sum(
                1 for layer in LayerType
                if any(m.layer == layer for m in self._modules.values())
            ),
            "total_layers": len(LayerType),
            "scan_timestamp": self._scan_timestamp.isoformat() if self._scan_timestamp else None,
        }

    def get_status(self) -> Dict:
        """Get architecture manager status."""
        health = self.get_architecture_health()
        return {
            **health,
            "layer_summary": self.get_layer_summary(),
        }
