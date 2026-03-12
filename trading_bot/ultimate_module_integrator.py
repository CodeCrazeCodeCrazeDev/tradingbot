"""
ULTIMATE MODULE INTEGRATOR - Auto-discovers and integrates ALL 1500+ modules
============================================================================

This is the MASTER integration that automatically discovers and loads
ALL Python modules in the trading_bot package.

Features:
- Auto-discovery of all Python modules
- Safe loading with error handling
- Circular import prevention
- Lazy loading for performance
- Module health tracking
- Category-based organization

Author: AlphaAlgo Trading System
Version: 3.0.0 ULTIMATE
"""

import asyncio
import importlib
import inspect
import logging
import os
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type
import json

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONFIGURATION
# ============================================================================

class ModuleCategory(Enum):
    """Module categories for organization"""
    # Core Systems
    CORE = "core"
    DATA = "data"
    INTELLIGENCE = "intelligence"
    STRATEGY = "strategy"
    EXECUTION = "execution"
    RISK = "risk"
    SAFETY = "safety"
    ORCHESTRATION = "orchestration"
    
    # Specialized
    AI_ML = "ai_ml"
    QUANTUM = "quantum"
    BLOCKCHAIN = "blockchain"
    ANALYSIS = "analysis"
    MONITORING = "monitoring"
    INFRASTRUCTURE = "infrastructure"
    
    # Advanced
    HEDGE_FUND = "hedge_fund"
    ELITE = "elite"
    AUTONOMOUS = "autonomous"
    EVOLUTION = "evolution"
    
    # Support
    UTILS = "utils"
    TESTING = "testing"
    CONFIG = "config"
    UNKNOWN = "unknown"


class LoadStatus(Enum):
    """Module load status"""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ModuleInfo:
    """Information about a discovered module"""
    name: str
    path: str
    import_path: str
    category: ModuleCategory
    status: LoadStatus = LoadStatus.NOT_LOADED
    module: Any = None
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    error: Optional[str] = None
    load_time: float = 0.0


@dataclass
class IntegrationStats:
    """Statistics about the integration"""
    total_discovered: int = 0
    total_loaded: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    total_classes: int = 0
    total_functions: int = 0
    load_time_seconds: float = 0.0
    categories: Dict[str, int] = field(default_factory=dict)


# ============================================================================
# CATEGORY DETECTION
# ============================================================================

CATEGORY_PATTERNS = {
    ModuleCategory.CORE: ['core', 'main', 'base', 'engine', 'system'],
    ModuleCategory.DATA: ['data', 'database', 'stream', 'feed', 'source', 'pipeline', 'ingestion'],
    ModuleCategory.INTELLIGENCE: ['intelligence', 'cognitive', 'brain', 'ai_core', 'ml', 'learning'],
    ModuleCategory.STRATEGY: ['strategy', 'signal', 'alpha', 'opportunity', 'scanner'],
    ModuleCategory.EXECUTION: ['execution', 'executor', 'order', 'fill', 'broker', 'trade'],
    ModuleCategory.RISK: ['risk', 'position', 'portfolio', 'sizing', 'hedge'],
    ModuleCategory.SAFETY: ['safety', 'security', 'guard', 'kill', 'circuit', 'emergency'],
    ModuleCategory.ORCHESTRATION: ['orchestrat', 'master', 'coordinator', 'supervisor'],
    ModuleCategory.AI_ML: ['ml', 'ai', 'neural', 'deep', 'model', 'predict', 'forecast'],
    ModuleCategory.QUANTUM: ['quantum'],
    ModuleCategory.BLOCKCHAIN: ['blockchain', 'defi', 'crypto', 'chain'],
    ModuleCategory.ANALYSIS: ['analysis', 'analyz', 'indicator', 'pattern', 'technical'],
    ModuleCategory.MONITORING: ['monitor', 'metric', 'dashboard', 'alert', 'log'],
    ModuleCategory.INFRASTRUCTURE: ['infrastructure', 'health', 'deploy', 'config'],
    ModuleCategory.HEDGE_FUND: ['hedge_fund', 'fund', 'institutional'],
    ModuleCategory.ELITE: ['elite', 'advanced', 'premium'],
    ModuleCategory.AUTONOMOUS: ['autonomous', 'auto', 'self_'],
    ModuleCategory.EVOLUTION: ['evolution', 'evolv', 'adapt', 'learn'],
    ModuleCategory.UTILS: ['util', 'helper', 'tool', 'common'],
    ModuleCategory.TESTING: ['test', 'mock', 'fixture', 'validation'],
    ModuleCategory.CONFIG: ['config', 'setting', 'constant'],
}

# Directories to skip
SKIP_DIRECTORIES = {
    '__pycache__', 'backup', 'auto_fix_backups', 'auto_fix_logs',
    'autonomous_backups', 'autonomous_logs', 'code_backups',
    'templates', 'static', 'examples', '.git', 'node_modules'
}

# Files to skip
SKIP_FILES = {
    '__init__.py', 'setup.py', 'conftest.py', '__main__.py'
}

# Modules known to cause issues (circular imports, heavy dependencies)
PROBLEMATIC_MODULES = {
    'trading_bot.tests',
    'trading_bot.autonomous_backups',
}


def detect_category(path: str, name: str) -> ModuleCategory:
    """Detect module category based on path and name"""
    full_path = f"{path}/{name}".lower()
    
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern in full_path:
                return category
    
    return ModuleCategory.UNKNOWN


# ============================================================================
# ULTIMATE MODULE INTEGRATOR
# ============================================================================

class UltimateModuleIntegrator:
    """
    The ULTIMATE Module Integrator - Auto-discovers and loads ALL modules
    
    This class automatically:
    1. Discovers all Python modules in trading_bot
    2. Categorizes them by function
    3. Loads them safely with error handling
    4. Tracks health and provides access
    """
    
    def __init__(self, base_path: Optional[str] = None, lazy_load: bool = True):
        """
        Initialize the integrator
        
        Args:
            base_path: Path to trading_bot directory
            lazy_load: If True, only discover modules, load on demand
        """
        if base_path is None:
            base_path = str(Path(__file__).parent)
        
        self.base_path = Path(base_path)
        self.lazy_load = lazy_load
        self.modules: Dict[str, ModuleInfo] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.failed_modules: Set[str] = set()
        self.stats = IntegrationStats()
        self.start_time = datetime.now()
        
        # Track loading to prevent circular imports
        self._loading_stack: Set[str] = set()
        
        logger.info("=" * 70)
        logger.info("ULTIMATE MODULE INTEGRATOR - Initializing")
        logger.info("=" * 70)
        logger.info(f"Base path: {self.base_path}")
        logger.info(f"Lazy load: {self.lazy_load}")
        
    def discover_all_modules(self) -> int:
        """
        Discover all Python modules in the trading_bot package
        
        Returns:
            Number of modules discovered
        """
        logger.info("\n[DISCOVERY] Scanning for modules...")
        
        discovered = 0
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]
            
            # Get relative path
            rel_path = Path(root).relative_to(self.base_path.parent)
            
            for file in files:
                if not file.endswith('.py'):
                    continue
                if file in SKIP_FILES:
                    continue
                
                # Build import path
                file_path = Path(root) / file
                module_name = file[:-3]  # Remove .py
                
                # Convert path to import format
                import_parts = list(rel_path.parts) + [module_name]
                import_path = '.'.join(import_parts)
                
                # Skip problematic modules
                skip = False
                for prob in PROBLEMATIC_MODULES:
                    if import_path.startswith(prob):
                        skip = True
                        break
                
                if skip:
                    continue
                
                # Detect category
                category = detect_category(str(rel_path), module_name)
                
                # Create module info
                info = ModuleInfo(
                    name=module_name,
                    path=str(file_path),
                    import_path=import_path,
                    category=category
                )
                
                self.modules[import_path] = info
                discovered += 1
        
        self.stats.total_discovered = discovered
        
        # Count by category
        for info in self.modules.values():
            cat_name = info.category.value
            self.stats.categories[cat_name] = self.stats.categories.get(cat_name, 0) + 1
        
        logger.info(f"Discovered {discovered} modules")
        logger.info("\nModules by category:")
        for cat, count in sorted(self.stats.categories.items(), key=lambda x: -x[1]):
            logger.info(f"  {cat}: {count}")
        
        return discovered
    
    def load_module(self, import_path: str) -> Optional[Any]:
        """
        Load a single module safely
        
        Args:
            import_path: Full import path (e.g., 'trading_bot.core.engine')
            
        Returns:
            Loaded module or None if failed
        """
        # Check if already loaded
        if import_path in self.loaded_modules:
            return self.loaded_modules[import_path]
        
        # Check if failed before
        if import_path in self.failed_modules:
            return None
        
        # Check for circular import
        if import_path in self._loading_stack:
            logger.debug(f"Circular import detected: {import_path}")
            return None
        
        # Get module info
        if import_path not in self.modules:
            logger.warning(f"Module not discovered: {import_path}")
            return None
        
        info = self.modules[import_path]
        
        # Mark as loading
        self._loading_stack.add(import_path)
        info.status = LoadStatus.LOADING
        
        start_time = datetime.now()
        
        try:
            # Import the module
            module = importlib.import_module(import_path)
            
            # Extract classes and functions
            for name, obj in inspect.getmembers(module):
                if name.startswith('_'):
                    continue
                if inspect.isclass(obj) and obj.__module__ == import_path:
                    info.classes.append(name)
                elif inspect.isfunction(obj) and obj.__module__ == import_path:
                    info.functions.append(name)
            
            # Update info
            info.status = LoadStatus.LOADED
            info.module = module
            info.load_time = (datetime.now() - start_time).total_seconds()
            
            # Store
            self.loaded_modules[import_path] = module
            self.stats.total_loaded += 1
            self.stats.total_classes += len(info.classes)
            self.stats.total_functions += len(info.functions)
            
            logger.debug(f"Loaded: {import_path} ({len(info.classes)} classes, {len(info.functions)} functions)")
            
            return module
            
        except Exception as e:
            error_msg = str(e)
            info.status = LoadStatus.FAILED
            info.error = error_msg
            self.failed_modules.add(import_path)
            self.stats.total_failed += 1
            
            logger.debug(f"Failed to load {import_path}: {error_msg[:100]}")
            
            return None
            
        finally:
            self._loading_stack.discard(import_path)
    
    def load_all_modules(self, categories: Optional[List[ModuleCategory]] = None) -> int:
        """
        Load all discovered modules (or specific categories)
        
        Args:
            categories: Optional list of categories to load
            
        Returns:
            Number of modules successfully loaded
        """
        logger.info("\n[LOADING] Loading all modules...")
        
        start_time = datetime.now()
        loaded = 0
        
        for import_path, info in self.modules.items():
            # Filter by category if specified
            if categories and info.category not in categories:
                info.status = LoadStatus.SKIPPED
                self.stats.total_skipped += 1
                continue
            
            if self.load_module(import_path):
                loaded += 1
        
        self.stats.load_time_seconds = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"\nLoading complete:")
        logger.info(f"  Loaded: {self.stats.total_loaded}")
        logger.info(f"  Failed: {self.stats.total_failed}")
        logger.info(f"  Skipped: {self.stats.total_skipped}")
        logger.info(f"  Classes: {self.stats.total_classes}")
        logger.info(f"  Functions: {self.stats.total_functions}")
        logger.info(f"  Time: {self.stats.load_time_seconds:.2f}s")
        
        return loaded
    
    def load_category(self, category: ModuleCategory) -> int:
        """Load all modules in a specific category"""
        return self.load_all_modules(categories=[category])
    
    def get_module(self, import_path: str) -> Optional[Any]:
        """Get a loaded module (loads if not already loaded)"""
        if import_path not in self.loaded_modules:
            self.load_module(import_path)
        return self.loaded_modules.get(import_path)
    
    def get_class(self, import_path: str, class_name: str) -> Optional[Type]:
        """Get a specific class from a module"""
        module = self.get_module(import_path)
        if module and hasattr(module, class_name):
            return getattr(module, class_name)
        return None
    
    def get_all_classes(self, category: Optional[ModuleCategory] = None) -> Dict[str, Type]:
        """Get all classes (optionally filtered by category)"""
        classes = {}
        
        for import_path, info in self.modules.items():
            if category and info.category != category:
                continue
            
            if info.status != LoadStatus.LOADED:
                continue
            
            for class_name in info.classes:
                full_name = f"{import_path}.{class_name}"
                cls = self.get_class(import_path, class_name)
                if cls:
                    classes[full_name] = cls
        
        return classes
    
    def search_modules(self, query: str) -> List[ModuleInfo]:
        """Search modules by name or path"""
        query = query.lower()
        results = []
        
        for import_path, info in self.modules.items():
            if query in import_path.lower() or query in info.name.lower():
                results.append(info)
        
        return results
    
    def get_stats(self) -> IntegrationStats:
        """Get integration statistics"""
        return self.stats
    
    def get_health_report(self) -> Dict:
        """Get a health report of all modules"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_modules': len(self.modules),
            'loaded': self.stats.total_loaded,
            'failed': self.stats.total_failed,
            'skipped': self.stats.total_skipped,
            'success_rate': self.stats.total_loaded / max(len(self.modules), 1) * 100,
            'categories': {},
            'failed_modules': []
        }
        
        # Category breakdown
        for category in ModuleCategory:
            cat_modules = [m for m in self.modules.values() if m.category == category]
            loaded = sum(1 for m in cat_modules if m.status == LoadStatus.LOADED)
            failed = sum(1 for m in cat_modules if m.status == LoadStatus.FAILED)
            
            if cat_modules:
                report['categories'][category.value] = {
                    'total': len(cat_modules),
                    'loaded': loaded,
                    'failed': failed,
                    'success_rate': loaded / len(cat_modules) * 100
                }
        
        # Failed modules list
        for import_path in self.failed_modules:
            if import_path in self.modules:
                info = self.modules[import_path]
                report['failed_modules'].append({
                    'path': import_path,
                    'error': info.error[:200] if info.error else 'Unknown'
                })
        
        return report
    
    def export_module_map(self, output_path: str):
        """Export module map to JSON file"""
        module_map = {
            'generated': datetime.now().isoformat(),
            'stats': {
                'total': self.stats.total_discovered,
                'loaded': self.stats.total_loaded,
                'failed': self.stats.total_failed,
                'classes': self.stats.total_classes,
                'functions': self.stats.total_functions
            },
            'modules': {}
        }
        
        for import_path, info in self.modules.items():
            module_map['modules'][import_path] = {
                'name': info.name,
                'category': info.category.value,
                'status': info.status.value,
                'classes': info.classes,
                'functions': info.functions,
                'error': info.error
            }
        
        with open(output_path, 'w') as f:
            json.dump(module_map, f, indent=2)
        
        logger.info(f"Module map exported to {output_path}")


# ============================================================================
# INTEGRATED TRADING SYSTEM
# ============================================================================

class IntegratedTradingSystem:
    """
    The Integrated Trading System - Uses UltimateModuleIntegrator to create
    a fully functional trading system with ALL modules.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.integrator = UltimateModuleIntegrator()
        self.running = False
        self.start_time = datetime.now()
        
        # Core system references
        self.orchestrators: Dict[str, Any] = {}
        self.strategies: Dict[str, Any] = {}
        self.risk_managers: Dict[str, Any] = {}
        self.executors: Dict[str, Any] = {}
        
        logger.info("=" * 70)
        logger.info("INTEGRATED TRADING SYSTEM - Initializing")
        logger.info("=" * 70)
    
    def initialize(self) -> bool:
        """Initialize the integrated trading system"""
        logger.info("\n[INIT] Initializing Integrated Trading System...")
        
        # Step 1: Discover all modules
        discovered = self.integrator.discover_all_modules()
        logger.info(f"Discovered {discovered} modules")
        
        # Step 2: Load core modules first (in order of dependency)
        priority_categories = [
            ModuleCategory.UTILS,
            ModuleCategory.CONFIG,
            ModuleCategory.DATA,
            ModuleCategory.CORE,
            ModuleCategory.ANALYSIS,
            ModuleCategory.INTELLIGENCE,
            ModuleCategory.STRATEGY,
            ModuleCategory.RISK,
            ModuleCategory.EXECUTION,
            ModuleCategory.SAFETY,
            ModuleCategory.ORCHESTRATION,
        ]
        
        for category in priority_categories:
            logger.info(f"\nLoading {category.value} modules...")
            self.integrator.load_category(category)
        
        # Step 3: Load remaining modules
        logger.info("\nLoading remaining modules...")
        self.integrator.load_all_modules()
        
        # Step 4: Initialize key orchestrators
        self._initialize_orchestrators()
        
        # Step 5: Report status
        self._report_status()
        
        return self.integrator.stats.total_loaded > 0
    
    def _initialize_orchestrators(self):
        """Initialize key orchestrator instances"""
        logger.info("\n[ORCHESTRATORS] Initializing key orchestrators...")
        
        orchestrator_classes = [
            ('trading_bot.mega_integration', 'MegaIntegration'),
            ('trading_bot.master_orchestrator', 'MasterOrchestrator'),
            ('trading_bot.master_integration', 'MasterTradingSystem'),
            ('trading_bot.unified_architecture.unified_trading_system', 'UnifiedTradingSystem'),
            ('trading_bot.alpha_engine.orchestrator', 'AlphaEngineOrchestrator'),
            ('trading_bot.alpha_research.alpha_research_orchestrator', 'AlphaResearchOrchestrator'),
            ('trading_bot.elite_ai_system.elite_trading_orchestrator', 'EliteTradingOrchestrator'),
            ('trading_bot.ultimate_system.ultimate_orchestrator', 'UltimateOrchestrator'),
            ('trading_bot.hedge_fund.hedge_fund_orchestrator', 'HedgeFundOrchestrator'),
            ('trading_bot.sentient_core.sentient_orchestrator', 'SentientOrchestrator'),
            ('trading_bot.eternal_evolution.eternal_orchestrator', 'EternalEvolutionOrchestrator'),
            ('trading_bot.qwen_codemender.governance_orchestrator', 'GovernanceOrchestrator'),
            ('trading_bot.alphaalgo_core.alphaalgo_orchestrator', 'AlphaAlgoOrchestrator'),
        ]
        
        for import_path, class_name in orchestrator_classes:
            try:
                cls = self.integrator.get_class(import_path, class_name)
                if cls:
                    try:
                        instance = cls({})
                    except TypeError:
                        try:
                            instance = cls()
                        except Exception:
                            instance = None
                    
                    if instance:
                        self.orchestrators[class_name] = instance
                        logger.info(f"  ✓ {class_name}")
            except Exception as e:
                logger.debug(f"  ✗ {class_name}: {e}")
    
    def _report_status(self):
        """Report initialization status"""
        stats = self.integrator.get_stats()
        
        logger.info("\n" + "=" * 70)
        logger.info("INTEGRATED TRADING SYSTEM - READY")
        logger.info("=" * 70)
        logger.info(f"Total Modules Discovered: {stats.total_discovered}")
        logger.info(f"Successfully Loaded: {stats.total_loaded}")
        logger.info(f"Failed to Load: {stats.total_failed}")
        logger.info(f"Total Classes: {stats.total_classes}")
        logger.info(f"Total Functions: {stats.total_functions}")
        logger.info(f"Active Orchestrators: {len(self.orchestrators)}")
        logger.info(f"Load Time: {stats.load_time_seconds:.2f}s")
        
        success_rate = stats.total_loaded / max(stats.total_discovered, 1) * 100
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("=" * 70)
    
    def get_orchestrator(self, name: str) -> Optional[Any]:
        """Get a specific orchestrator by name"""
        return self.orchestrators.get(name)
    
    def list_orchestrators(self) -> List[str]:
        """List all available orchestrators"""
        return list(self.orchestrators.keys())
    
    def get_module(self, import_path: str) -> Optional[Any]:
        """Get any module by import path"""
        return self.integrator.get_module(import_path)
    
    def get_class(self, import_path: str, class_name: str) -> Optional[Type]:
        """Get any class from any module"""
        return self.integrator.get_class(import_path, class_name)
    
    def search(self, query: str) -> List[ModuleInfo]:
        """Search for modules"""
        return self.integrator.search_modules(query)
    
    def get_health_report(self) -> Dict:
        """Get system health report"""
        return self.integrator.get_health_report()
    
    async def start(self):
        """Start the integrated trading system"""
        logger.info("\n[START] Starting Integrated Trading System...")
        self.running = True
        
        # Start orchestrators that have start methods
        for name, orchestrator in self.orchestrators.items():
            if hasattr(orchestrator, 'start'):
                try:
                    result = orchestrator.start()
                    if asyncio.iscoroutine(result):
                        asyncio.create_task(result)
                    logger.info(f"Started: {name}")
                except Exception as e:
                    logger.warning(f"Failed to start {name}: {e}")
        
        logger.info("System started")
    
    async def stop(self):
        """Stop the integrated trading system"""
        logger.info("\n[STOP] Stopping Integrated Trading System...")
        self.running = False
        
        # Stop orchestrators
        for name, orchestrator in self.orchestrators.items():
            if hasattr(orchestrator, 'stop'):
                try:
                    result = orchestrator.stop()
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    pass
        
        logger.info("System stopped")


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_integrator(base_path: Optional[str] = None) -> UltimateModuleIntegrator:
    """Create a new UltimateModuleIntegrator"""
    return UltimateModuleIntegrator(base_path)


def create_integrated_system(config: Optional[Dict] = None) -> IntegratedTradingSystem:
    """Create a new IntegratedTradingSystem"""
    return IntegratedTradingSystem(config)


def quick_integrate() -> IntegratedTradingSystem:
    """Quick integration - discover and load all modules"""
    system = IntegratedTradingSystem()
    system.initialize()
    return system


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ultimate Module Integrator")
    parser.add_argument('--discover-only', action='store_true', 
                        help='Only discover modules, do not load')
    parser.add_argument('--export', type=str, 
                        help='Export module map to JSON file')
    parser.add_argument('--category', type=str,
                        help='Load only specific category')
    parser.add_argument('--search', type=str,
                        help='Search for modules')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create integrator
    integrator = UltimateModuleIntegrator()
    
    # Discover modules
    integrator.discover_all_modules()
    
    if args.search:
        # Search mode
        results = integrator.search_modules(args.search)
        print(f"\nFound {len(results)} modules matching '{args.search}':")
        for info in results[:50]:
            print(f"  {info.import_path} ({info.category.value})")
    
    elif not args.discover_only:
        # Load modules
        if args.category:
            try:
                category = ModuleCategory(args.category)
                integrator.load_category(category)
            except ValueError:
                print(f"Invalid category: {args.category}")
                print(f"Valid categories: {[c.value for c in ModuleCategory]}")
        else:
            integrator.load_all_modules()
    
    # Export if requested
    if args.export:
        integrator.export_module_map(args.export)
    
    # Print health report
    report = integrator.get_health_report()
    print(f"\n{'=' * 60}")
    print("INTEGRATION REPORT")
    print(f"{'=' * 60}")
    print(f"Total Modules: {report['total_modules']}")
    print(f"Loaded: {report['loaded']}")
    print(f"Failed: {report['failed']}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print(f"{'=' * 60}")
