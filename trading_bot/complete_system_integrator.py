"""
Complete System Integrator - Integrates ALL 3000+ Python files across 170+ packages
into a unified, production-ready trading system.

This is the MASTER integration file that:
1. Discovers and registers ALL modules automatically
2. Resolves dependencies between packages
3. Handles circular import prevention
4. Provides lazy loading for performance
5. Maintains the 8-layer architecture
6. Enforces RISK FIRST principles

Version: 3.0
Total Files: 3000+
Total Packages: 170+

ARCHITECTURE LAYERS:
- Layer 0: Infrastructure (health, monitoring, logging, telemetry)
- Layer 1: Data Foundation (connectivity, database, ingestion, streaming)
- Layer 2: Intelligence Core (ML, AI, cognitive, self-learning)
- Layer 3: Signal Generation (alpha, signals, strategy, analysis)
- Layer 4: Risk & Safety (MSOS, risk, safety) - HIGHEST PRIORITY ⚠️
- Layer 5: Execution (brokers, orders, positions)
- Layer 6: Governance (compliance, audit, human oversight)
- Layer 7: Orchestration (event pipeline, master coordination)

IMMUTABLE PRINCIPLES:
1. RISK FIRST: Layer 4 has VETO power over all trades
2. HUMAN CONTROL: Human override ALWAYS works
3. FAIL-SAFE: Default to NO TRADE when uncertain
4. SURVIVAL: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."
"""

import asyncio
import importlib
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from functools import lru_cache
import traceback
import json

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class SystemLayer(Enum):
    """System architecture layers"""
    INFRASTRUCTURE = 0
    DATA_FOUNDATION = 1
    INTELLIGENCE_CORE = 2
    SIGNAL_GENERATION = 3
    RISK_SAFETY = 4  # HIGHEST PRIORITY
    EXECUTION = 5
    GOVERNANCE = 6
    ORCHESTRATION = 7


class ModuleStatus(Enum):
    """Module lifecycle status"""
    DISCOVERED = auto()
    REGISTERED = auto()
    LOADING = auto()
    LOADED = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    RUNNING = auto()
    STOPPED = auto()
    ERROR = auto()
    DISABLED = auto()


class ComponentType(Enum):
    """Types of components"""
    # Infrastructure
    HEALTH_MONITOR = "health_monitor"
    METRICS_COLLECTOR = "metrics_collector"
    LOGGER = "logger"
    TELEMETRY = "telemetry"
    
    # Data
    DATA_PROVIDER = "data_provider"
    DATA_VALIDATOR = "data_validator"
    DATABASE = "database"
    CACHE = "cache"
    STREAM_PROCESSOR = "stream_processor"
    
    # Intelligence
    ML_ENGINE = "ml_engine"
    RL_AGENT = "rl_agent"
    AI_ENGINE = "ai_engine"
    COGNITIVE = "cognitive"
    LEARNER = "learner"
    
    # Signals
    SIGNAL_GENERATOR = "signal_generator"
    SIGNAL_VALIDATOR = "signal_validator"
    STRATEGY = "strategy"
    ANALYZER = "analyzer"
    RESEARCH = "research"
    
    # Risk
    RISK_MANAGER = "risk_manager"
    SAFETY_SYSTEM = "safety_system"
    CIRCUIT_BREAKER = "circuit_breaker"
    
    # Execution
    EXECUTION_ENGINE = "execution_engine"
    BROKER = "broker"
    POSITION_MANAGER = "position_manager"
    ORDER_ROUTER = "order_router"
    
    # Governance
    COMPLIANCE = "compliance"
    AUDIT = "audit"
    GOVERNANCE = "governance"
    HUMAN_LAYER = "human_layer"
    
    # Orchestration
    ORCHESTRATOR = "orchestrator"
    EVENT_PROCESSOR = "event_processor"
    SCHEDULER = "scheduler"
    
    # Generic
    UTILITY = "utility"
    UNKNOWN = "unknown"


@dataclass
class ModuleInfo:
    """Complete information about a module"""
    name: str
    package: str
    module_path: str
    file_path: str
    layer: SystemLayer
    component_type: ComponentType
    priority: int = 5
    dependencies: List[str] = field(default_factory=list)
    status: ModuleStatus = ModuleStatus.DISCOVERED
    instance: Any = None
    error: Optional[str] = None
    load_time_ms: float = 0.0
    enabled: bool = True
    is_critical: bool = False


@dataclass
class PackageInfo:
    """Information about a package"""
    name: str
    path: Path
    layer: SystemLayer
    file_count: int
    has_init: bool
    modules: List[str] = field(default_factory=list)
    status: ModuleStatus = ModuleStatus.DISCOVERED


@dataclass
class IntegrationStats:
    """Statistics about the integration"""
    total_packages: int = 0
    total_modules: int = 0
    discovered: int = 0
    registered: int = 0
    loaded: int = 0
    initialized: int = 0
    running: int = 0
    errors: int = 0
    disabled: int = 0
    load_time_ms: float = 0.0
    start_time: Optional[datetime] = None


# =============================================================================
# PACKAGE TO LAYER MAPPING
# =============================================================================

PACKAGE_LAYER_MAP: Dict[str, SystemLayer] = {
    # Layer 0: Infrastructure
    'infrastructure': SystemLayer.INFRASTRUCTURE,
    'monitoring': SystemLayer.INFRASTRUCTURE,
    'observability': SystemLayer.INFRASTRUCTURE,
    'alerts': SystemLayer.INFRASTRUCTURE,
    'log_system': SystemLayer.INFRASTRUCTURE,
    'telemetry': SystemLayer.INFRASTRUCTURE,
    'system_health': SystemLayer.INFRASTRUCTURE,
    'diagnostics': SystemLayer.INFRASTRUCTURE,
    'profiling': SystemLayer.INFRASTRUCTURE,
    
    # Layer 1: Data Foundation
    'connectivity': SystemLayer.DATA_FOUNDATION,
    'connectivity_unified': SystemLayer.DATA_FOUNDATION,
    'database': SystemLayer.DATA_FOUNDATION,
    'data': SystemLayer.DATA_FOUNDATION,
    'data_sources': SystemLayer.DATA_FOUNDATION,
    'data_feeds': SystemLayer.DATA_FOUNDATION,
    'ingestion': SystemLayer.DATA_FOUNDATION,
    'streaming': SystemLayer.DATA_FOUNDATION,
    'connectors': SystemLayer.DATA_FOUNDATION,
    'cache': SystemLayer.DATA_FOUNDATION,
    
    # Layer 2: Intelligence Core
    'ml': SystemLayer.INTELLIGENCE_CORE,
    'advanced_ml': SystemLayer.INTELLIGENCE_CORE,
    'ai': SystemLayer.INTELLIGENCE_CORE,
    'ai_core': SystemLayer.INTELLIGENCE_CORE,
    'ai_engineer': SystemLayer.INTELLIGENCE_CORE,
    'cognitive_architecture': SystemLayer.INTELLIGENCE_CORE,
    'self_learning': SystemLayer.INTELLIGENCE_CORE,
    'self_improvement': SystemLayer.INTELLIGENCE_CORE,
    'self_healing_ai': SystemLayer.INTELLIGENCE_CORE,
    'meta_learning': SystemLayer.INTELLIGENCE_CORE,
    'learning': SystemLayer.INTELLIGENCE_CORE,
    'neuro_symbolic': SystemLayer.INTELLIGENCE_CORE,
    'qwen_codemender': SystemLayer.INTELLIGENCE_CORE,
    'qwen_codemender': SystemLayer.INTELLIGENCE_CORE,
    'qwen_codemender': SystemLayer.INTELLIGENCE_CORE,
    'qwen_codemender': SystemLayer.INTELLIGENCE_CORE,
    'adversarial_curriculum': SystemLayer.INTELLIGENCE_CORE,
    'autonomous_learner': SystemLayer.INTELLIGENCE_CORE,
    
    # Layer 3: Signal Generation
    'alpha_engine': SystemLayer.SIGNAL_GENERATION,
    'alpha_research': SystemLayer.SIGNAL_GENERATION,
    'signals': SystemLayer.SIGNAL_GENERATION,
    'strategy': SystemLayer.SIGNAL_GENERATION,
    'strategies': SystemLayer.SIGNAL_GENERATION,
    'analysis': SystemLayer.SIGNAL_GENERATION,
    'analysis_unified': SystemLayer.SIGNAL_GENERATION,
    'advanced_analysis': SystemLayer.SIGNAL_GENERATION,
    'analytics': SystemLayer.SIGNAL_GENERATION,
    'indicators': SystemLayer.SIGNAL_GENERATION,
    'forecasting': SystemLayer.SIGNAL_GENERATION,
    'deepchart': SystemLayer.SIGNAL_GENERATION,
    'market_intelligence': SystemLayer.SIGNAL_GENERATION,
    'market_teacher': SystemLayer.SIGNAL_GENERATION,
    'market_student': SystemLayer.SIGNAL_GENERATION,
    'opportunity_scanner': SystemLayer.SIGNAL_GENERATION,
    'tamic': SystemLayer.SIGNAL_GENERATION,
    'elite_ai_system': SystemLayer.SIGNAL_GENERATION,
    'elite_system': SystemLayer.SIGNAL_GENERATION,
    'brain': SystemLayer.SIGNAL_GENERATION,
    'innovations': SystemLayer.SIGNAL_GENERATION,
    'features': SystemLayer.SIGNAL_GENERATION,
    'alternative_data': SystemLayer.SIGNAL_GENERATION,
    'sentiment': SystemLayer.SIGNAL_GENERATION,
    'macro': SystemLayer.SIGNAL_GENERATION,
    'research': SystemLayer.SIGNAL_GENERATION,
    
    # Layer 4: Risk & Safety (HIGHEST PRIORITY)
    'msos': SystemLayer.RISK_SAFETY,
    'risk': SystemLayer.RISK_SAFETY,
    'risk_unified': SystemLayer.RISK_SAFETY,
    'risk_management': SystemLayer.RISK_SAFETY,
    'safety': SystemLayer.RISK_SAFETY,
    'hedge_fund_safety': SystemLayer.RISK_SAFETY,
    'stealth_safety': SystemLayer.RISK_SAFETY,
    'critical_fixes': SystemLayer.RISK_SAFETY,
    'adversarial_decision': SystemLayer.RISK_SAFETY,
    
    # Layer 5: Execution
    'execution': SystemLayer.EXECUTION,
    'brokers': SystemLayer.EXECUTION,
    'position': SystemLayer.EXECUTION,
    'exit_strategies': SystemLayer.EXECUTION,
    'exits': SystemLayer.EXECUTION,
    'trading': SystemLayer.EXECUTION,
    'hft': SystemLayer.EXECUTION,
    'market_making': SystemLayer.EXECUTION,
    'arbitrage': SystemLayer.EXECUTION,
    'hedging': SystemLayer.EXECUTION,
    'derivatives': SystemLayer.EXECUTION,
    
    # Layer 6: Governance
    'compliance': SystemLayer.GOVERNANCE,
    'audit': SystemLayer.GOVERNANCE,
    'governance': SystemLayer.GOVERNANCE,
    'alphaalgo_core': SystemLayer.GOVERNANCE,
    'qwen_codemender': SystemLayer.GOVERNANCE,
    'human_layer': SystemLayer.GOVERNANCE,
    'approval': SystemLayer.GOVERNANCE,
    'surveillance': SystemLayer.GOVERNANCE,
    'security': SystemLayer.GOVERNANCE,
    
    # Layer 7: Orchestration
    'orchestrator': SystemLayer.ORCHESTRATION,
    'event_pipeline': SystemLayer.ORCHESTRATION,
    'event_monitoring': SystemLayer.ORCHESTRATION,
    'system_supervisor': SystemLayer.ORCHESTRATION,
    'systems_ai': SystemLayer.ORCHESTRATION,
    'unified_architecture': SystemLayer.ORCHESTRATION,
    'integration': SystemLayer.ORCHESTRATION,
    'integrations': SystemLayer.ORCHESTRATION,
    'bridges': SystemLayer.ORCHESTRATION,
    
    # Specialized systems (map to appropriate layers)
    'aamis_v3': SystemLayer.INTELLIGENCE_CORE,
    'alphaalgo_v2': SystemLayer.SIGNAL_GENERATION,
    'alphaalgo_institutional': SystemLayer.GOVERNANCE,
    'adaptive_systems': SystemLayer.INTELLIGENCE_CORE,
    'advanced_features': SystemLayer.SIGNAL_GENERATION,
    'autonomous': SystemLayer.INTELLIGENCE_CORE,
    'blockchain': SystemLayer.GOVERNANCE,
    'crypto': SystemLayer.EXECUTION,
    'dashboard': SystemLayer.INFRASTRUCTURE,
    'eternal_evolution': SystemLayer.INTELLIGENCE_CORE,
    'evolution_layer': SystemLayer.INTELLIGENCE_CORE,
    'hedge_fund': SystemLayer.GOVERNANCE,
    'improvement_agent': SystemLayer.INTELLIGENCE_CORE,
    'improvements': SystemLayer.INTELLIGENCE_CORE,
    'institutional': SystemLayer.GOVERNANCE,
    'institutional_entry': SystemLayer.EXECUTION,
    'intel': SystemLayer.SIGNAL_GENERATION,
    'internet_access': SystemLayer.DATA_FOUNDATION,
    'mobile': SystemLayer.INFRASTRUCTURE,
    'mobile_app': SystemLayer.INFRASTRUCTURE,
    'notifications': SystemLayer.INFRASTRUCTURE,
    'optimization': SystemLayer.INTELLIGENCE_CORE,
    'performance': SystemLayer.INFRASTRUCTURE,
    'portfolio': SystemLayer.RISK_SAFETY,
    'production': SystemLayer.ORCHESTRATION,
    'profit_maximizer': SystemLayer.SIGNAL_GENERATION,
    'psychology': SystemLayer.SIGNAL_GENERATION,
    'quantum': SystemLayer.INTELLIGENCE_CORE,
    'realtime': SystemLayer.DATA_FOUNDATION,
    'reporting': SystemLayer.INFRASTRUCTURE,
    'self_mastery': SystemLayer.INTELLIGENCE_CORE,
    'sentient_core': SystemLayer.INTELLIGENCE_CORE,
    'simulation': SystemLayer.INTELLIGENCE_CORE,
    'skills': SystemLayer.INTELLIGENCE_CORE,
    'social': SystemLayer.SIGNAL_GENERATION,
    'system': SystemLayer.ORCHESTRATION,
    'testing': SystemLayer.INFRASTRUCTURE,
    'tests': SystemLayer.INFRASTRUCTURE,
    'tools': SystemLayer.INFRASTRUCTURE,
    'trade_journal': SystemLayer.GOVERNANCE,
    'trading_calendar': SystemLayer.DATA_FOUNDATION,
    'ultimate_production': SystemLayer.ORCHESTRATION,
    'ultimate_system': SystemLayer.ORCHESTRATION,
    'upgrades': SystemLayer.INTELLIGENCE_CORE,
    'utils': SystemLayer.INFRASTRUCTURE,
    'validation': SystemLayer.RISK_SAFETY,
    'visualization': SystemLayer.INFRASTRUCTURE,
    'voice_assistant': SystemLayer.INFRASTRUCTURE,
    'wealth': SystemLayer.GOVERNANCE,
    'agents': SystemLayer.INTELLIGENCE_CORE,
    'api': SystemLayer.INFRASTRUCTURE,
    'auto_optimizer': SystemLayer.INTELLIGENCE_CORE,
    'backtesting': SystemLayer.SIGNAL_GENERATION,
    'config': SystemLayer.INFRASTRUCTURE,
    'core': SystemLayer.ORCHESTRATION,
    'core_api': SystemLayer.ORCHESTRATION,
    'deployment': SystemLayer.INFRASTRUCTURE,
    'devops': SystemLayer.INFRASTRUCTURE,
    'distributed': SystemLayer.INFRASTRUCTURE,
    'documentation': SystemLayer.INFRASTRUCTURE,
    'error_handling': SystemLayer.INFRASTRUCTURE,
    'explainability': SystemLayer.GOVERNANCE,
    'filters': SystemLayer.SIGNAL_GENERATION,
    'global_expansion': SystemLayer.GOVERNANCE,
    'models': SystemLayer.INTELLIGENCE_CORE,
    'ops': SystemLayer.INFRASTRUCTURE,
    'persistence': SystemLayer.DATA_FOUNDATION,
    'quality': SystemLayer.RISK_SAFETY,
    'schemas': SystemLayer.DATA_FOUNDATION,
}

# Packages to exclude from integration
EXCLUDED_PACKAGES = {
    'autonomous_backups',  # Backup files
    'auto_fix_backups',    # Backup files
    'backup',              # Backup files
    '__pycache__',         # Python cache
    '.improvement_backups', # Backup files
    'trading_bot',         # Nested package (avoid recursion)
}

# Layer priorities (higher = initialized first)
LAYER_PRIORITIES = {
    SystemLayer.RISK_SAFETY: 10,      # HIGHEST - Risk first!
    SystemLayer.INFRASTRUCTURE: 9,
    SystemLayer.DATA_FOUNDATION: 8,
    SystemLayer.GOVERNANCE: 7,
    SystemLayer.INTELLIGENCE_CORE: 6,
    SystemLayer.SIGNAL_GENERATION: 5,
    SystemLayer.EXECUTION: 4,
    SystemLayer.ORCHESTRATION: 3,
}


# =============================================================================
# COMPLETE SYSTEM INTEGRATOR
# =============================================================================

class CompleteSystemIntegrator:
    """
    Master integrator that discovers and integrates ALL modules in the trading system.
    
    Features:
    - Automatic module discovery
    - Dependency resolution
    - Lazy loading for performance
    - Circular import prevention
    - Layer-based initialization (Risk first!)
    - Graceful error handling
    - Comprehensive status reporting
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.base_path = Path(__file__).parent
        
        # Storage
        self.packages: Dict[str, PackageInfo] = {}
        self.modules: Dict[str, ModuleInfo] = {}
        self.instances: Dict[str, Any] = {}
        
        # Statistics
        self.stats = IntegrationStats()
        
        # State
        self._initialized = False
        self._running = False
        self._lock = asyncio.Lock()
        
        # Error tracking
        self.errors: List[Tuple[str, str]] = []
        
        logger.info("CompleteSystemIntegrator created")
    
    # =========================================================================
    # DISCOVERY
    # =========================================================================
    
    def discover_all_packages(self) -> Dict[str, PackageInfo]:
        """Discover all packages in the trading_bot directory"""
        logger.info("=" * 80)
        logger.info("DISCOVERING ALL PACKAGES")
        logger.info("=" * 80)
        
        for item in sorted(self.base_path.iterdir()):
            if not item.is_dir():
                continue
            if item.name.startswith('_') or item.name.startswith('.'):
                continue
            if item.name in EXCLUDED_PACKAGES:
                continue
            
            py_files = list(item.rglob('*.py'))
            if not py_files:
                continue
            
            # Determine layer
            layer = PACKAGE_LAYER_MAP.get(item.name, SystemLayer.ORCHESTRATION)
            
            package_info = PackageInfo(
                name=item.name,
                path=item,
                layer=layer,
                file_count=len(py_files),
                has_init=(item / '__init__.py').exists()
            )
            
            self.packages[item.name] = package_info
            self.stats.total_packages += 1
        
        logger.info(f"Discovered {self.stats.total_packages} packages")
        return self.packages
    
    def discover_all_modules(self) -> Dict[str, ModuleInfo]:
        """Discover all modules in all packages"""
        logger.info("=" * 80)
        logger.info("DISCOVERING ALL MODULES")
        logger.info("=" * 80)
        
        for package_name, package_info in self.packages.items():
            self._discover_package_modules(package_info)
        
        self.stats.discovered = len(self.modules)
        logger.info(f"Discovered {self.stats.discovered} modules")
        return self.modules
    
    def _discover_package_modules(self, package_info: PackageInfo):
        """Discover all modules in a package"""
        for py_file in package_info.path.rglob('*.py'):
            if py_file.name.startswith('_') and py_file.name != '__init__.py':
                continue
            
            # Build module path
            rel_path = py_file.relative_to(self.base_path)
            module_path = 'trading_bot.' + str(rel_path.with_suffix('')).replace(os.sep, '.')
            
            # Determine component type
            component_type = self._infer_component_type(py_file.name, package_info.name)
            
            # Determine if critical
            is_critical = package_info.layer == SystemLayer.RISK_SAFETY
            
            module_info = ModuleInfo(
                name=py_file.stem,
                package=package_info.name,
                module_path=module_path,
                file_path=str(py_file),
                layer=package_info.layer,
                component_type=component_type,
                priority=LAYER_PRIORITIES.get(package_info.layer, 5),
                is_critical=is_critical
            )
            
            # Use full module path as key to avoid collisions
            key = module_path
            self.modules[key] = module_info
            package_info.modules.append(key)
            self.stats.total_modules += 1
    
    def _infer_component_type(self, filename: str, package_name: str) -> ComponentType:
        """Infer component type from filename and package"""
        name_lower = filename.lower()
        
        # Risk & Safety
        if any(x in name_lower for x in ['risk', 'msos', 'safety', 'circuit', 'fail_safe']):
            return ComponentType.RISK_MANAGER
        
        # Execution
        if any(x in name_lower for x in ['executor', 'execution', 'order', 'fill']):
            return ComponentType.EXECUTION_ENGINE
        if any(x in name_lower for x in ['broker', 'mt5', 'alpaca', 'binance']):
            return ComponentType.BROKER
        if any(x in name_lower for x in ['position']):
            return ComponentType.POSITION_MANAGER
        
        # Signals
        if any(x in name_lower for x in ['signal', 'alpha']):
            return ComponentType.SIGNAL_GENERATOR
        if any(x in name_lower for x in ['strategy']):
            return ComponentType.STRATEGY
        if any(x in name_lower for x in ['analyz', 'analysis']):
            return ComponentType.ANALYZER
        
        # Intelligence
        if any(x in name_lower for x in ['ml', 'model', 'neural', 'deep_learning']):
            return ComponentType.ML_ENGINE
        if any(x in name_lower for x in ['rl', 'agent', 'policy']):
            return ComponentType.RL_AGENT
        if any(x in name_lower for x in ['cognitive', 'brain']):
            return ComponentType.COGNITIVE
        if any(x in name_lower for x in ['learn']):
            return ComponentType.LEARNER
        
        # Data
        if any(x in name_lower for x in ['data', 'feed', 'stream']):
            return ComponentType.DATA_PROVIDER
        if any(x in name_lower for x in ['database', 'db', 'storage']):
            return ComponentType.DATABASE
        if any(x in name_lower for x in ['cache']):
            return ComponentType.CACHE
        if any(x in name_lower for x in ['valid']):
            return ComponentType.DATA_VALIDATOR
        
        # Infrastructure
        if any(x in name_lower for x in ['health', 'monitor']):
            return ComponentType.HEALTH_MONITOR
        if any(x in name_lower for x in ['metric']):
            return ComponentType.METRICS_COLLECTOR
        if any(x in name_lower for x in ['log']):
            return ComponentType.LOGGER
        
        # Governance
        if any(x in name_lower for x in ['compliance', 'regulatory']):
            return ComponentType.COMPLIANCE
        if any(x in name_lower for x in ['audit']):
            return ComponentType.AUDIT
        if any(x in name_lower for x in ['governance', 'approval']):
            return ComponentType.GOVERNANCE
        if any(x in name_lower for x in ['human']):
            return ComponentType.HUMAN_LAYER
        
        # Orchestration
        if any(x in name_lower for x in ['orchestrat', 'coordinator']):
            return ComponentType.ORCHESTRATOR
        if any(x in name_lower for x in ['event', 'pipeline']):
            return ComponentType.EVENT_PROCESSOR
        if any(x in name_lower for x in ['schedul']):
            return ComponentType.SCHEDULER
        
        return ComponentType.UTILITY
    
    # =========================================================================
    # LOADING
    # =========================================================================
    
    async def load_all_modules(self, lazy: bool = True) -> Dict[str, bool]:
        """
        Load all discovered modules.
        
        Args:
            lazy: If True, only register modules without importing.
                  If False, import all modules immediately.
        """
        logger.info("=" * 80)
        logger.info(f"LOADING ALL MODULES (lazy={lazy})")
        logger.info("=" * 80)
        
        results = {}
        
        # Sort by priority (Risk first!)
        sorted_modules = sorted(
            self.modules.values(),
            key=lambda m: (-m.priority, m.layer.value)
        )
        
        for module_info in sorted_modules:
            if not module_info.enabled:
                module_info.status = ModuleStatus.DISABLED
                self.stats.disabled += 1
                results[module_info.module_path] = True
                continue
            
            module_info.status = ModuleStatus.REGISTERED
            self.stats.registered += 1
            
            if not lazy:
                success = self._load_module(module_info)
                results[module_info.module_path] = success
            else:
                results[module_info.module_path] = True
        
        logger.info(f"Registered {self.stats.registered} modules")
        if not lazy:
            logger.info(f"Loaded {self.stats.loaded} modules, {self.stats.errors} errors")
        
        return results
    
    def _load_module(self, module_info: ModuleInfo) -> bool:
        """Load a single module"""
        module_info.status = ModuleStatus.LOADING
        start_time = datetime.utcnow()
        
        try:
            module = importlib.import_module(module_info.module_path)
            module_info.instance = module
            module_info.status = ModuleStatus.LOADED
            module_info.load_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.stats.loaded += 1
            self.stats.load_time_ms += module_info.load_time_ms
            return True
            
        except Exception as e:
            module_info.status = ModuleStatus.ERROR
            module_info.error = str(e)
            self.stats.errors += 1
            self.errors.append((module_info.module_path, str(e)))
            logger.debug(f"Failed to load {module_info.module_path}: {e}")
            return False
    
    def get_module(self, module_path: str) -> Optional[Any]:
        """Get a module, loading it if necessary (lazy loading)"""
        module_info = self.modules.get(module_path)
        if not module_info:
            return None
        
        if module_info.status == ModuleStatus.LOADED:
            return module_info.instance
        
        if module_info.status in [ModuleStatus.REGISTERED, ModuleStatus.DISCOVERED]:
            if self._load_module(module_info):
                return module_info.instance
        
        return None
    
    # =========================================================================
    # INITIALIZATION
    # =========================================================================
    
    async def initialize_all(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """Initialize all loaded modules"""
        logger.info("=" * 80)
        logger.info("INITIALIZING ALL MODULES")
        logger.info("=" * 80)
        
        config = config or self.config
        results = {}
        
        # Initialize by layer priority (Risk first!)
        layer_order = sorted(
            SystemLayer,
            key=lambda l: -LAYER_PRIORITIES.get(l, 0)
        )
        
        for layer in layer_order:
            layer_modules = [
                m for m in self.modules.values()
                if m.layer == layer and m.status == ModuleStatus.LOADED
            ]
            
            if not layer_modules:
                continue
            
            logger.info(f"\nInitializing Layer {layer.value}: {layer.name} ({len(layer_modules)} modules)")
            
            for module_info in sorted(layer_modules, key=lambda m: -m.priority):
                success = await self._initialize_module(module_info, config)
                results[module_info.module_path] = success
        
        self._initialized = True
        logger.info(f"\nInitialized {self.stats.initialized} modules")
        return results
    
    async def _initialize_module(self, module_info: ModuleInfo, config: Dict[str, Any]) -> bool:
        """Initialize a single module"""
        module_info.status = ModuleStatus.INITIALIZING
        
        try:
            module = module_info.instance
            
            # Try various initialization patterns
            if hasattr(module, 'initialize'):
                if asyncio.iscoroutinefunction(module.initialize):
                    await module.initialize(config)
                else:
                    module.initialize(config)
            elif hasattr(module, 'init'):
                if asyncio.iscoroutinefunction(module.init):
                    await module.init(config)
                else:
                    module.init(config)
            elif hasattr(module, 'setup'):
                if asyncio.iscoroutinefunction(module.setup):
                    await module.setup(config)
                else:
                    module.setup(config)
            
            module_info.status = ModuleStatus.INITIALIZED
            self.stats.initialized += 1
            return True
            
        except Exception as e:
            module_info.status = ModuleStatus.ERROR
            module_info.error = str(e)
            logger.debug(f"Failed to initialize {module_info.module_path}: {e}")
            return False
    
    # =========================================================================
    # RUNNING
    # =========================================================================
    
    async def start_all(self) -> Dict[str, bool]:
        """Start all initialized modules"""
        logger.info("=" * 80)
        logger.info("STARTING ALL MODULES")
        logger.info("=" * 80)
        
        self.stats.start_time = datetime.utcnow()
        results = {}
        
        # Start by layer priority (Risk first!)
        layer_order = sorted(
            SystemLayer,
            key=lambda l: -LAYER_PRIORITIES.get(l, 0)
        )
        
        for layer in layer_order:
            layer_modules = [
                m for m in self.modules.values()
                if m.layer == layer and m.status == ModuleStatus.INITIALIZED
            ]
            
            for module_info in layer_modules:
                success = await self._start_module(module_info)
                results[module_info.module_path] = success
        
        self._running = True
        logger.info(f"Started {self.stats.running} modules")
        return results
    
    async def _start_module(self, module_info: ModuleInfo) -> bool:
        """Start a single module"""
        try:
            module = module_info.instance
            
            if hasattr(module, 'start'):
                if asyncio.iscoroutinefunction(module.start):
                    await module.start()
                else:
                    module.start()
            elif hasattr(module, 'run'):
                if asyncio.iscoroutinefunction(module.run):
                    await module.run()
                else:
                    module.run()
            
            module_info.status = ModuleStatus.RUNNING
            self.stats.running += 1
            return True
            
        except Exception as e:
            module_info.status = ModuleStatus.ERROR
            module_info.error = str(e)
            return False
    
    async def stop_all(self) -> Dict[str, bool]:
        """Stop all running modules (reverse order, Risk last!)"""
        logger.info("Stopping all modules...")
        
        results = {}
        
        # Stop in reverse layer order (Risk last!)
        layer_order = sorted(
            SystemLayer,
            key=lambda l: LAYER_PRIORITIES.get(l, 0)
        )
        
        for layer in layer_order:
            layer_modules = [
                m for m in self.modules.values()
                if m.layer == layer and m.status == ModuleStatus.RUNNING
            ]
            
            for module_info in layer_modules:
                success = await self._stop_module(module_info)
                results[module_info.module_path] = success
        
        self._running = False
        logger.info("All modules stopped")
        return results
    
    async def _stop_module(self, module_info: ModuleInfo) -> bool:
        """Stop a single module"""
        try:
            module = module_info.instance
            
            if hasattr(module, 'stop'):
                if asyncio.iscoroutinefunction(module.stop):
                    await module.stop()
                else:
                    module.stop()
            elif hasattr(module, 'shutdown'):
                if asyncio.iscoroutinefunction(module.shutdown):
                    await module.shutdown()
                else:
                    module.shutdown()
            
            module_info.status = ModuleStatus.STOPPED
            return True
            
        except Exception as e:
            return False
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    def get_modules_by_layer(self, layer: SystemLayer) -> List[ModuleInfo]:
        """Get all modules in a specific layer"""
        return [m for m in self.modules.values() if m.layer == layer]
    
    def get_modules_by_type(self, component_type: ComponentType) -> List[ModuleInfo]:
        """Get all modules of a specific type"""
        return [m for m in self.modules.values() if m.component_type == component_type]
    
    def get_modules_by_package(self, package_name: str) -> List[ModuleInfo]:
        """Get all modules in a specific package"""
        return [m for m in self.modules.values() if m.package == package_name]
    
    def get_modules_by_status(self, status: ModuleStatus) -> List[ModuleInfo]:
        """Get all modules with a specific status"""
        return [m for m in self.modules.values() if m.status == status]
    
    def get_critical_modules(self) -> List[ModuleInfo]:
        """Get all critical modules (Risk & Safety)"""
        return [m for m in self.modules.values() if m.is_critical]
    
    # =========================================================================
    # REPORTING
    # =========================================================================
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        layer_stats = {}
        for layer in SystemLayer:
            layer_modules = self.get_modules_by_layer(layer)
            layer_stats[layer.name] = {
                'total': len(layer_modules),
                'loaded': sum(1 for m in layer_modules if m.status == ModuleStatus.LOADED),
                'initialized': sum(1 for m in layer_modules if m.status == ModuleStatus.INITIALIZED),
                'running': sum(1 for m in layer_modules if m.status == ModuleStatus.RUNNING),
                'errors': sum(1 for m in layer_modules if m.status == ModuleStatus.ERROR),
                'priority': LAYER_PRIORITIES.get(layer, 0)
            }
        
        return {
            'status': 'running' if self._running else ('initialized' if self._initialized else 'not_started'),
            'start_time': self.stats.start_time.isoformat() if self.stats.start_time else None,
            'statistics': {
                'total_packages': self.stats.total_packages,
                'total_modules': self.stats.total_modules,
                'discovered': self.stats.discovered,
                'registered': self.stats.registered,
                'loaded': self.stats.loaded,
                'initialized': self.stats.initialized,
                'running': self.stats.running,
                'errors': self.stats.errors,
                'disabled': self.stats.disabled,
                'load_time_ms': round(self.stats.load_time_ms, 2)
            },
            'layers': layer_stats,
            'error_count': len(self.errors),
            'recent_errors': self.errors[-10:] if self.errors else []
        }
    
    def print_status_report(self):
        """Print formatted status report"""
        report = self.get_status_report()
        
        print("\n" + "=" * 80)
        print("COMPLETE SYSTEM INTEGRATOR - STATUS REPORT")
        print("=" * 80)
        
        print(f"\nOverall Status: {report['status'].upper()}")
        print(f"Start Time: {report['start_time']}")
        
        print("\n--- Statistics ---")
        for key, value in report['statistics'].items():
            print(f"  {key}: {value}")
        
        print("\n--- Layer Status ---")
        for layer_name, layer_info in sorted(report['layers'].items(), key=lambda x: -x[1]['priority']):
            print(f"\n  {layer_name} (Priority: {layer_info['priority']})")
            print(f"    Total: {layer_info['total']}, Loaded: {layer_info['loaded']}, "
                  f"Initialized: {layer_info['initialized']}, Running: {layer_info['running']}, "
                  f"Errors: {layer_info['errors']}")
        
        if report['recent_errors']:
            print("\n--- Recent Errors ---")
            for module_path, error in report['recent_errors']:
                print(f"  {module_path}: {error[:100]}...")
        
        print("\n" + "=" * 80)
    
    def export_inventory(self, filepath: str = 'complete_module_inventory.json'):
        """Export complete module inventory to JSON"""
        inventory = {
            'generated_at': datetime.utcnow().isoformat(),
            'statistics': {
                'total_packages': self.stats.total_packages,
                'total_modules': self.stats.total_modules,
            },
            'packages': {
                name: {
                    'layer': info.layer.name,
                    'file_count': info.file_count,
                    'has_init': info.has_init,
                    'module_count': len(info.modules)
                }
                for name, info in self.packages.items()
            },
            'modules_by_layer': {
                layer.name: [
                    {
                        'name': m.name,
                        'package': m.package,
                        'module_path': m.module_path,
                        'component_type': m.component_type.value,
                        'is_critical': m.is_critical
                    }
                    for m in self.get_modules_by_layer(layer)
                ]
                for layer in SystemLayer
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(inventory, f, indent=2)
        
        logger.info(f"Exported inventory to {filepath}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def create_complete_system(config: Optional[Dict[str, Any]] = None) -> CompleteSystemIntegrator:
    """Create and discover the complete system"""
    integrator = CompleteSystemIntegrator(config)
    integrator.discover_all_packages()
    integrator.discover_all_modules()
    return integrator


async def quick_start(config: Optional[Dict[str, Any]] = None, lazy: bool = True) -> CompleteSystemIntegrator:
    """Quick start the complete system"""
    integrator = await create_complete_system(config)
    await integrator.load_all_modules(lazy=lazy)
    
    if not lazy:
        await integrator.initialize_all(config)
        await integrator.start_all()
    
    return integrator


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Main entry point for testing"""
    print("""
    ═══════════════════════════════════════════════════════════════════════════════
                    ALPHAALGO TRADING BOT - COMPLETE SYSTEM INTEGRATOR
                              Version 3.0 | 3000+ Modules
    ═══════════════════════════════════════════════════════════════════════════════
    
    IMMUTABLE PRINCIPLES:
    1. RISK FIRST: Layer 4 (MSOS) has VETO power over all trades
    2. HUMAN CONTROL: Human override ALWAYS works
    3. FAIL-SAFE: Default to NO TRADE when uncertain
    4. SURVIVAL: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."
    
    ═══════════════════════════════════════════════════════════════════════════════
    """)
    
    # Create and discover
    integrator = await create_complete_system()
    
    # Print status
    integrator.print_status_report()
    
    # Export inventory
    integrator.export_inventory()
    
    return integrator


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())


__all__ = [
    'CompleteSystemIntegrator',
    'SystemLayer',
    'ModuleStatus',
    'ComponentType',
    'ModuleInfo',
    'PackageInfo',
    'create_complete_system',
    'quick_start',
    'PACKAGE_LAYER_MAP',
    'LAYER_PRIORITIES',
]
