"""
AlphaAlgo Systems Architecture
==============================
Complete system architecture where intelligence emerges from:
- Data ingestion pipelines
- Event store & replay engine
- Feature pipelines
- Model ensemble
- Decision attribution layer
- Memory hierarchy
- Research agents
- Text-to-system command layer
- Governance & approval gates

TEXT ARCHITECTURE DIAGRAM:
==========================

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ALPHAALGO SYSTEMS AI                                   │
│                    "Intelligence from Architecture, Not Parameters"              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌───────────────┐              ┌───────────────┐              ┌───────────────┐
│  DATA LAYER   │              │ COMPUTE LAYER │              │ CONTROL LAYER │
│  (Ingestion)  │              │  (Processing) │              │ (Governance)  │
└───────────────┘              └───────────────┘              └───────────────┘
        │                               │                               │
        ▼                               ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA INGESTION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ L1 Quotes   │  │ L2 Order    │  │ Trade Tape  │  │ News/       │            │
│  │ (BBO)       │  │ Book        │  │ (Prints)    │  │ Sentiment   │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                │                    │
│         └────────────────┴────────────────┴────────────────┘                    │
│                                   │                                              │
│                                   ▼                                              │
│                        ┌─────────────────────┐                                   │
│                        │   NORMALIZER        │                                   │
│                        │   - Timestamp align │                                   │
│                        │   - Sequence valid  │                                   │
│                        │   - Quality flags   │                                   │
│                        └──────────┬──────────┘                                   │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EVENT STORE & REPLAY                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         IMMUTABLE EVENT LOG                              │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│  │  │ Event 1  │→ │ Event 2  │→ │ Event 3  │→ │ Event N  │→ │ HEAD     │  │    │
│  │  │ t=0.001  │  │ t=0.002  │  │ t=0.003  │  │ t=N.xxx  │  │ (live)   │  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                   │                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         REPLAY ENGINE                                    │    │
│  │  - Deterministic replay from any point                                   │    │
│  │  - Speed: REALTIME | FAST | STEPPED                                      │    │
│  │  - Bookmarks for key events                                              │    │
│  │  - Reproducible training                                                 │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FEATURE PIPELINES                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Microstruc- │  │ Technical   │  │ Regime      │  │ Sentiment   │            │
│  │ ture        │  │ Indicators  │  │ Features    │  │ Features    │            │
│  │ ─────────── │  │ ─────────── │  │ ─────────── │  │ ─────────── │            │
│  │ - Imbalance │  │ - Momentum  │  │ - Volatility│  │ - News NLP  │            │
│  │ - Spread    │  │ - Mean Rev  │  │ - Liquidity │  │ - Social    │            │
│  │ - Toxicity  │  │ - Trend     │  │ - Regime ID │  │ - Macro     │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                │                    │
│         └────────────────┴────────────────┴────────────────┘                    │
│                                   │                                              │
│                                   ▼                                              │
│                        ┌─────────────────────┐                                   │
│                        │   FEATURE STORE     │                                   │
│                        │   - Versioned       │                                   │
│                        │   - Point-in-time   │                                   │
│                        │   - Decay tracking  │                                   │
│                        └──────────┬──────────┘                                   │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MODEL ENSEMBLE                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    REGIME-AWARE MODEL ROUTER                             │    │
│  │                                                                          │    │
│  │    Regime: TRENDING    Regime: RANGING    Regime: VOLATILE               │    │
│  │    ┌─────────────┐     ┌─────────────┐    ┌─────────────┐               │    │
│  │    │ Trend Model │     │ MeanRev Mdl │    │ Vol Model   │               │    │
│  │    │ w=0.7       │     │ w=0.8       │    │ w=0.6       │               │    │
│  │    └─────────────┘     └─────────────┘    └─────────────┘               │    │
│  │                                                                          │    │
│  │    ┌─────────────┐     ┌─────────────┐    ┌─────────────┐               │    │
│  │    │ Momentum    │     │ Stat Arb    │    │ Tail Risk   │               │    │
│  │    │ w=0.5       │     │ w=0.6       │    │ w=0.9       │               │    │
│  │    └─────────────┘     └─────────────┘    └─────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                   │                                              │
│                                   ▼                                              │
│                        ┌─────────────────────┐                                   │
│                        │   CONFIDENCE-       │                                   │
│                        │   WEIGHTED          │                                   │
│                        │   AGGREGATOR        │                                   │
│                        └──────────┬──────────┘                                   │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DECISION ATTRIBUTION LAYER                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Every signal MUST output:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  {                                                                       │    │
│  │    "signal_id": "uuid",                                                  │    │
│  │    "timestamp": "2024-01-01T00:00:00.000Z",                              │    │
│  │    "feature_snapshot_hash": "sha256:abc123...",                          │    │
│  │    "contributing_models": [                                              │    │
│  │      {"model_id": "trend_v3", "weight": 0.4, "confidence": 0.85},        │    │
│  │      {"model_id": "momentum_v2", "weight": 0.3, "confidence": 0.72}      │    │
│  │    ],                                                                    │    │
│  │    "latent_regime_id": "regime_cluster_7",                               │    │
│  │    "historical_analogs": ["2023-03-15", "2022-11-08"],                   │    │
│  │    "expected_outcome": {"direction": "LONG", "magnitude": 0.02},         │    │
│  │    "confidence_score": 0.78,                                             │    │
│  │    "reasoning_chain": ["high_imbalance", "trend_confirmed", "vol_low"]   │    │
│  │  }                                                                       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MEMORY HIERARCHY                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐     │
│  │   SHORT-TERM        │  │   MID-TERM          │  │   LONG-TERM         │     │
│  │   (Seconds-Minutes) │  │   (Hours-Days)      │  │   (Weeks-Forever)   │     │
│  │   ───────────────── │  │   ───────────────── │  │   ───────────────── │     │
│  │   - Microstructure  │  │   - Session regime  │  │   - Archived events │     │
│  │   - Execution ctx   │  │   - Volatility      │  │   - Training data   │     │
│  │   - Order book      │  │   - Liquidity       │  │   - Model versions  │     │
│  │   - Recent trades   │  │   - Correlations    │  │   - Outcomes        │     │
│  │                     │  │                     │  │   - Shock signatures│     │
│  │   TTL: 5 minutes    │  │   TTL: 7 days       │  │   TTL: Forever      │     │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘     │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RESEARCH AGENTS                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    SCIENTIFIC LOOP (NON-TRADING)                         │    │
│  │                                                                          │    │
│  │    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │    │
│  │    │ OBSERVE  │ →  │ HYPOTHE- │ →  │ TEST     │ →  │ VALIDATE │        │    │
│  │    │ Data     │    │ SIZE     │    │ Replay   │    │ Robustness│        │    │
│  │    └──────────┘    └──────────┘    └──────────┘    └──────────┘        │    │
│  │         │                                               │               │    │
│  │         └───────────────────────────────────────────────┘               │    │
│  │                              │                                          │    │
│  │                              ▼                                          │    │
│  │                    ┌──────────────────┐                                 │    │
│  │                    │ PROMOTE (if pass)│                                 │    │
│  │                    │ to Governance    │                                 │    │
│  │                    └──────────────────┘                                 │    │
│  │                                                                          │    │
│  │    CONSTRAINTS:                                                          │    │
│  │    ✗ CANNOT deploy live                                                  │    │
│  │    ✗ CANNOT modify risk rules                                            │    │
│  │    ✗ CANNOT bypass governance                                            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         TEXT-TO-SYSTEM COMMAND LAYER                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ALLOWED COMMANDS:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  "Analyze why slippage exceeded forecast last week"                      │    │
│  │  "Find features that fail in low-volatility regimes"                     │    │
│  │  "Retrain execution model excluding high-spread periods"                 │    │
│  │  "Simulate alternative sizing under current regime"                      │    │
│  │  "Show attribution for signal XYZ"                                       │    │
│  │  "Compare model performance across regimes"                              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  FORBIDDEN COMMANDS:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  ✗ "Execute trade..."                                                    │    │
│  │  ✗ "Override risk limit..."                                              │    │
│  │  ✗ "Deploy model to production..."                                       │    │
│  │  ✗ "Disable safety check..."                                             │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         GOVERNANCE & APPROVAL GATES                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         APPROVAL HIERARCHY                               │    │
│  │                                                                          │    │
│  │    G0: HUMAN AUTHORITY (Ultimate control)                                │    │
│  │    ├── Approves: Model deployment, Risk changes, System config           │    │
│  │    │                                                                     │    │
│  │    G1: SYSTEM CONTROLLER (Automated gates)                               │    │
│  │    ├── Validates: Signal quality, Risk limits, Data integrity            │    │
│  │    │                                                                     │    │
│  │    G2: AGENT LAYER (Research & discovery)                                │    │
│  │    └── Proposes: Features, Hypotheses, Improvements                      │    │
│  │                                                                          │    │
│  │    FLOW: G2 proposes → G1 validates → G0 approves → Deploy               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         AUDIT LOG (IMMUTABLE)                            │    │
│  │                                                                          │    │
│  │    Every action logged:                                                  │    │
│  │    - Who (agent/human)                                                   │    │
│  │    - What (action type)                                                  │    │
│  │    - When (timestamp)                                                    │    │
│  │    - Why (reasoning)                                                     │    │
│  │    - Outcome (result)                                                    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SELF-IMPROVEMENT LOOP                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                          │    │
│  │    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │    │
│  │    │ OUTCOME  │ →  │ DRIFT    │ →  │ DECAY    │ →  │ RETRAIN  │        │    │
│  │    │ LABELING │    │ DETECT   │    │ DETECT   │    │ TRIGGER  │        │    │
│  │    └──────────┘    └──────────┘    └──────────┘    └──────────┘        │    │
│  │         │                                               │               │    │
│  │         │         ┌──────────┐    ┌──────────┐         │               │    │
│  │         └────────→│ VALIDATE │ →  │ DEPLOY   │←────────┘               │    │
│  │                   │ GATE     │    │ GATE     │                         │    │
│  │                   └──────────┘    └──────────┘                         │    │
│  │                                                                          │    │
│  │    ALL IMPROVEMENTS MUST BE:                                             │    │
│  │    ✓ Measured (quantified impact)                                        │    │
│  │    ✓ Reversible (rollback available)                                     │    │
│  │    ✓ Auditable (full trace)                                              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘

"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SystemLayer(Enum):
    """System architecture layers."""
    DATA_INGESTION = auto()
    EVENT_STORE = auto()
    FEATURE_PIPELINE = auto()
    MODEL_ENSEMBLE = auto()
    ATTRIBUTION = auto()
    MEMORY = auto()
    RESEARCH = auto()
    TEXT_TO_SYSTEM = auto()
    GOVERNANCE = auto()
    SELF_IMPROVEMENT = auto()


class ComponentStatus(Enum):
    """Component health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    INITIALIZING = "initializing"
    STOPPED = "stopped"


@dataclass
class LayerConfig:
    """Configuration for a system layer."""
    layer: SystemLayer
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[SystemLayer] = field(default_factory=list)


@dataclass
class SystemHealth:
    """System health snapshot."""
    timestamp: datetime
    overall_status: ComponentStatus
    layer_status: Dict[SystemLayer, ComponentStatus]
    metrics: Dict[str, float]
    alerts: List[str]


class SystemComponent(ABC):
    """Base class for all system components."""
    
    def __init__(self, name: str, layer: SystemLayer):
        self.name = name
        self.layer = layer
        self.status = ComponentStatus.INITIALIZING
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the component."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the component."""
        pass
    
    @abstractmethod
    def health_check(self) -> ComponentStatus:
        """Check component health."""
        pass


class SystemArchitecture:
    """
    AlphaAlgo Systems Architecture.
    
    Coordinates all system layers and ensures:
    - Data flows correctly through pipelines
    - Attribution is maintained for every decision
    - Governance gates are enforced
    - Self-improvement is controlled and auditable
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.components: Dict[str, SystemComponent] = {}
        self.layer_configs: Dict[SystemLayer, LayerConfig] = {}
        self._initialized = False
        
        # Initialize layer configurations
        self._init_layer_configs()
    
    def _init_layer_configs(self):
        """Initialize default layer configurations."""
        self.layer_configs = {
            SystemLayer.DATA_INGESTION: LayerConfig(
                layer=SystemLayer.DATA_INGESTION,
                dependencies=[],
                config={
                    "sources": ["L1_QUOTES", "L2_ORDERBOOK", "TRADES", "NEWS"],
                    "normalization": True,
                    "quality_flags": True,
                }
            ),
            SystemLayer.EVENT_STORE: LayerConfig(
                layer=SystemLayer.EVENT_STORE,
                dependencies=[SystemLayer.DATA_INGESTION],
                config={
                    "storage": "immutable_log",
                    "replay_modes": ["REALTIME", "FAST", "STEPPED"],
                    "retention_days": 365,
                }
            ),
            SystemLayer.FEATURE_PIPELINE: LayerConfig(
                layer=SystemLayer.FEATURE_PIPELINE,
                dependencies=[SystemLayer.EVENT_STORE],
                config={
                    "feature_groups": [
                        "microstructure",
                        "technical",
                        "regime",
                        "sentiment",
                    ],
                    "versioning": True,
                    "decay_tracking": True,
                }
            ),
            SystemLayer.MODEL_ENSEMBLE: LayerConfig(
                layer=SystemLayer.MODEL_ENSEMBLE,
                dependencies=[SystemLayer.FEATURE_PIPELINE],
                config={
                    "regime_aware_routing": True,
                    "confidence_weighting": True,
                    "hot_swap": True,
                }
            ),
            SystemLayer.ATTRIBUTION: LayerConfig(
                layer=SystemLayer.ATTRIBUTION,
                dependencies=[SystemLayer.MODEL_ENSEMBLE],
                config={
                    "required_fields": [
                        "feature_snapshot_hash",
                        "contributing_models",
                        "latent_regime_id",
                        "historical_analogs",
                        "expected_outcome",
                        "confidence_score",
                    ],
                    "storage": "attribution_store",
                }
            ),
            SystemLayer.MEMORY: LayerConfig(
                layer=SystemLayer.MEMORY,
                dependencies=[SystemLayer.ATTRIBUTION],
                config={
                    "tiers": ["short_term", "mid_term", "long_term"],
                    "short_term_ttl_seconds": 300,
                    "mid_term_ttl_days": 7,
                    "long_term_ttl": "forever",
                }
            ),
            SystemLayer.RESEARCH: LayerConfig(
                layer=SystemLayer.RESEARCH,
                dependencies=[SystemLayer.MEMORY, SystemLayer.EVENT_STORE],
                config={
                    "can_deploy_live": False,
                    "can_modify_risk": False,
                    "can_bypass_governance": False,
                    "sandbox_only": True,
                }
            ),
            SystemLayer.TEXT_TO_SYSTEM: LayerConfig(
                layer=SystemLayer.TEXT_TO_SYSTEM,
                dependencies=[SystemLayer.RESEARCH],
                config={
                    "forbidden_commands": [
                        "execute_trade",
                        "override_risk",
                        "deploy_model",
                        "disable_safety",
                    ],
                    "allowed_categories": [
                        "analyze",
                        "find",
                        "retrain",
                        "simulate",
                        "show",
                        "compare",
                    ],
                }
            ),
            SystemLayer.GOVERNANCE: LayerConfig(
                layer=SystemLayer.GOVERNANCE,
                dependencies=[],  # Independent layer
                config={
                    "approval_levels": ["G0_HUMAN", "G1_SYSTEM", "G2_AGENT"],
                    "audit_log": True,
                    "immutable_log": True,
                }
            ),
            SystemLayer.SELF_IMPROVEMENT: LayerConfig(
                layer=SystemLayer.SELF_IMPROVEMENT,
                dependencies=[
                    SystemLayer.GOVERNANCE,
                    SystemLayer.ATTRIBUTION,
                    SystemLayer.MEMORY,
                ],
                config={
                    "drift_detection": True,
                    "decay_detection": True,
                    "auto_retrain": False,  # Requires approval
                    "rollback_enabled": True,
                }
            ),
        }
    
    def register_component(self, component: SystemComponent):
        """Register a system component."""
        self.components[component.name] = component
        logger.info(f"Registered component: {component.name} in layer {component.layer.name}")
    
    async def initialize(self) -> bool:
        """Initialize the system architecture."""
        logger.info("Initializing AlphaAlgo Systems Architecture...")
        
        # Initialize layers in dependency order
        initialized_layers = set()
        
        for layer in SystemLayer:
            config = self.layer_configs.get(layer)
            if not config or not config.enabled:
                continue
            
            # Check dependencies
            for dep in config.dependencies:
                if dep not in initialized_layers:
                    logger.error(f"Layer {layer.name} depends on {dep.name} which is not initialized")
                    return False
            
            # Initialize components in this layer
            for name, component in self.components.items():
                if component.layer == layer:
                    try:
                        success = await component.initialize()
                        if not success:
                            logger.error(f"Failed to initialize component: {name}")
                            return False
                        logger.info(f"Initialized component: {name}")
                    except Exception as e:
                        logger.error(f"Error initializing component {name}: {e}")
                        return False
            
            initialized_layers.add(layer)
        
        self._initialized = True
        logger.info("AlphaAlgo Systems Architecture initialized successfully")
        return True
    
    async def shutdown(self) -> bool:
        """Shutdown the system architecture."""
        logger.info("Shutting down AlphaAlgo Systems Architecture...")
        
        # Shutdown in reverse order
        for layer in reversed(list(SystemLayer)):
            for name, component in self.components.items():
                if component.layer == layer:
                    try:
                        await component.shutdown()
                        logger.info(f"Shutdown component: {name}")
                    except Exception as e:
                        logger.error(f"Error shutting down component {name}: {e}")
        
        self._initialized = False
        logger.info("AlphaAlgo Systems Architecture shutdown complete")
        return True
    
    def get_health(self) -> SystemHealth:
        """Get system health status."""
        layer_status = {}
        alerts = []
        
        for layer in SystemLayer:
            layer_components = [
                c for c in self.components.values()
                if c.layer == layer
            ]
            
            if not layer_components:
                layer_status[layer] = ComponentStatus.STOPPED
                continue
            
            statuses = [c.health_check() for c in layer_components]
            
            if all(s == ComponentStatus.HEALTHY for s in statuses):
                layer_status[layer] = ComponentStatus.HEALTHY
            elif any(s == ComponentStatus.FAILED for s in statuses):
                layer_status[layer] = ComponentStatus.FAILED
                alerts.append(f"Layer {layer.name} has failed components")
            else:
                layer_status[layer] = ComponentStatus.DEGRADED
                alerts.append(f"Layer {layer.name} is degraded")
        
        # Determine overall status
        if all(s == ComponentStatus.HEALTHY for s in layer_status.values()):
            overall = ComponentStatus.HEALTHY
        elif any(s == ComponentStatus.FAILED for s in layer_status.values()):
            overall = ComponentStatus.FAILED
        else:
            overall = ComponentStatus.DEGRADED
        
        return SystemHealth(
            timestamp=datetime.utcnow(),
            overall_status=overall,
            layer_status=layer_status,
            metrics={
                "components_total": len(self.components),
                "components_healthy": sum(
                    1 for c in self.components.values()
                    if c.health_check() == ComponentStatus.HEALTHY
                ),
            },
            alerts=alerts,
        )
    
    def get_architecture_diagram(self) -> str:
        """Return the text architecture diagram."""
        return __doc__
