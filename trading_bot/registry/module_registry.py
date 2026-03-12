"""
Module Registry - Dynamic module discovery and management system.
"""

import os
import sys
import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Type
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ModuleCategory(Enum):
    """Categories of trading bot modules."""
    DATA_CONNECTIVITY = "data_connectivity"
    ANALYSIS_INTELLIGENCE = "analysis_intelligence"
    TRADING_EXECUTION = "trading_execution"
    RISK_SAFETY = "risk_safety"
    OPTIMIZATION_EVOLUTION = "optimization_evolution"
    ORCHESTRATION_MANAGEMENT = "orchestration_management"
    SPECIALIZED_SYSTEMS = "specialized_systems"
    INFRASTRUCTURE = "infrastructure"
    UNKNOWN = "unknown"

@dataclass
class ModuleInfo:
    """Information about a registered module."""
    name: str
    path: str
    category: ModuleCategory
    module: Optional[Any] = None
    class_name: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    initialized: bool = False
    enabled: bool = True
    priority: int = 0  # Higher = loaded first
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_modified: Optional[datetime] = None
    import_error: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.dependencies, list):
            self.dependencies = set(self.dependencies)
        if isinstance(self.dependents, list):
            self.dependents = set(self.dependents)

class ModuleRegistry:
    """Central registry for all trading bot modules."""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.modules: Dict[str, ModuleInfo] = {}
        self.category_map = self._build_category_map()
        self._discovery_complete = False
        
    def _build_category_map(self) -> Dict[str, ModuleCategory]:
        """Map directory names to categories."""
        return {
            # Data & Connectivity
            'data': ModuleCategory.DATA_CONNECTIVITY,
            'data_feeds': ModuleCategory.DATA_CONNECTIVITY,
            'data_sources': ModuleCategory.DATA_CONNECTIVITY,
            'ingestion': ModuleCategory.DATA_CONNECTIVITY,
            'connectivity': ModuleCategory.DATA_CONNECTIVITY,
            'connectivity_unified': ModuleCategory.DATA_CONNECTIVITY,
            'connectors': ModuleCategory.DATA_CONNECTIVITY,
            'database': ModuleCategory.DATA_CONNECTIVITY,
            'persistence': ModuleCategory.DATA_CONNECTIVITY,
            'streaming': ModuleCategory.DATA_CONNECTIVITY,
            'blockchain': ModuleCategory.DATA_CONNECTIVITY,
            
            # Analysis & Intelligence
            'analysis': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'advanced_analysis': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'market_intelligence': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'intelligence': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'intelligence_core': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'ai': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'ai_core': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'ml': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'advanced_ml': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'meta_learning': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'sentiment': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'alternative_data': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'deepchart': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'alpha_research': ModuleCategory.ANALYSIS_INTELLIGENCE,
            'quantum': ModuleCategory.ANALYSIS_INTELLIGENCE,
            
            # Trading & Execution
            'execution': ModuleCategory.TRADING_EXECUTION,
            'exits': ModuleCategory.TRADING_EXECUTION,
            'exit_strategies': ModuleCategory.TRADING_EXECUTION,
            'strategies': ModuleCategory.TRADING_EXECUTION,
            'trading': ModuleCategory.TRADING_EXECUTION,
            'realtime_trading_core': ModuleCategory.TRADING_EXECUTION,
            'position': ModuleCategory.TRADING_EXECUTION,
            'arbitrage': ModuleCategory.TRADING_EXECUTION,
            'market_making': ModuleCategory.TRADING_EXECUTION,
            'hft': ModuleCategory.TRADING_EXECUTION,
            'brokers': ModuleCategory.TRADING_EXECUTION,
            'broker': ModuleCategory.TRADING_EXECUTION,
            
            # Risk & Safety
            'risk': ModuleCategory.RISK_SAFETY,
            'risk_management': ModuleCategory.RISK_SAFETY,
            'risk_unified': ModuleCategory.RISK_SAFETY,
            'safety': ModuleCategory.RISK_SAFETY,
            'security': ModuleCategory.RISK_SAFETY,
            'validation': ModuleCategory.RISK_SAFETY,
            'verification': ModuleCategory.RISK_SAFETY,
            'stealth_safety': ModuleCategory.RISK_SAFETY,
            'anti_rogue_ai': ModuleCategory.RISK_SAFETY,
            'reality_gates': ModuleCategory.RISK_SAFETY,
            
            # Optimization & Evolution
            'optimization': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'auto_optimizer': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'self_improvement': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'evolution_layer': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'recursive_evolution': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'eternal_evolution': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'autonomous': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'self_assembly_ai': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'sentient_core': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'self_mastery': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'self_learning': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'self_diagnostic': ModuleCategory.OPTIMIZATION_EVOLUTION,
            'self_healing_ai': ModuleCategory.OPTIMIZATION_EVOLUTION,
            
            # Orchestration & Management
            'orchestrator': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'master_system': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'unified_system': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'governance': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'systems_ai': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'intelligent_delegation': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'infrastructure': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'monitoring': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'reporting': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'alerts': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            'notifications': ModuleCategory.ORCHESTRATION_MANAGEMENT,
            
            # Specialized Systems
            'alpha_engine': ModuleCategory.SPECIALIZED_SYSTEMS,
            'alphaalgo_core': ModuleCategory.SPECIALIZED_SYSTEMS,
            'alphaalgo_institutional': ModuleCategory.SPECIALIZED_SYSTEMS,
            'elite_ai_system': ModuleCategory.SPECIALIZED_SYSTEMS,
            'apex_fi': ModuleCategory.SPECIALIZED_SYSTEMS,
            'mosefs': ModuleCategory.SPECIALIZED_SYSTEMS,
            'hedge_fund': ModuleCategory.SPECIALIZED_SYSTEMS,
            'msos': ModuleCategory.SPECIALIZED_SYSTEMS,
            'neuros_evolution': ModuleCategory.SPECIALIZED_SYSTEMS,
            'neuros_fi': ModuleCategory.SPECIALIZED_SYSTEMS,
            'perplexity_trading': ModuleCategory.SPECIALIZED_SYSTEMS,
            'hivemind': ModuleCategory.SPECIALIZED_SYSTEMS,
            
            # Infrastructure
            'config': ModuleCategory.INFRASTRUCTURE,
            'logs': ModuleCategory.INFRASTRUCTURE,
            'log_system': ModuleCategory.INFRASTRUCTURE,
            'utils': ModuleCategory.INFRASTRUCTURE,
            'utils2': ModuleCategory.INFRASTRUCTURE,
            'tools': ModuleCategory.INFRASTRUCTURE,
            'schemas': ModuleCategory.INFRASTRUCTURE,
            'api': ModuleCategory.INFRASTRUCTURE,
            'web': ModuleCategory.INFRASTRUCTURE,
            'mobile': ModuleCategory.INFRASTRUCTURE,
            'deployment': ModuleCategory.INFRASTRUCTURE,
            'devops': ModuleCategory.INFRASTRUCTURE,
            'testing': ModuleCategory.INFRASTRUCTURE,
            'documentation': ModuleCategory.INFRASTRUCTURE,
        }
    
    def discover_modules(self, force_rediscover: bool = False) -> None:
        """Discover all modules in the trading bot directory."""
        if self._discovery_complete and not force_rediscover:
            return
            
        logger.info("Discovering modules...")
        discovered_count = 0
        
        for item in self.base_path.iterdir():
            if item.is_dir() and not item.name.startswith('_') and not item.name.startswith('.'):
                # Skip archive directory
                if item.name == '_archive':
                    continue
                    
                # Check if it's a Python package
                init_file = item / '__init__.py'
                if init_file.exists():
                    category = self.category_map.get(item.name, ModuleCategory.UNKNOWN)
                    
                    # Create module info
                    module_info = ModuleInfo(
                        name=item.name,
                        path=str(item),
                        category=category,
                        last_modified=datetime.fromtimestamp(item.stat().st_mtime)
                    )
                    
                    # Try to import and analyze the module
                    try:
                        module_info = self._analyze_module(module_info)
                        discovered_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to analyze module {item.name}: {e}")
                        module_info.import_error = str(e)
                    
                    self.modules[item.name] = module_info
        
        self._discovery_complete = True
        logger.info(f"Discovered {discovered_count} modules total")
        
        # Log summary by category
        category_counts = {}
        for module in self.modules.values():
            category_counts[module.category] = category_counts.get(module.category, 0) + 1
        
        for category, count in category_counts.items():
            logger.info(f"  {category.value}: {count} modules")
    
    def _analyze_module(self, module_info: ModuleInfo) -> ModuleInfo:
        """Analyze a module to extract metadata and dependencies."""
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(
                module_info.name,
                os.path.join(module_info.path, '__init__.py')
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module_info.module = module
            
            # Extract metadata from __init__.py
            if hasattr(module, '__doc__') and module.__doc__:
                module_info.metadata['description'] = module.__doc__.strip()
            
            # Look for version info
            if hasattr(module, '__version__'):
                module_info.metadata['version'] = module.__version__
            
            # Look for main classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if not name.startswith('_') and obj.__module__ == module.__name__:
                    if module_info.class_name is None:
                        module_info.class_name = name
                    if 'main' in name.lower() or 'orchestrator' in name.lower() or 'manager' in name.lower():
                        module_info.class_name = name
                        break
            
            # Extract dependencies from imports
            module_info.dependencies = self._extract_dependencies(module)
            
            # Set priority based on category
            module_info.priority = self._get_module_priority(module_info.category)
            
        except Exception as e:
            logger.debug(f"Module analysis failed for {module_info.name}: {e}")
            raise
        
        return module_info
    
    def _extract_dependencies(self, module) -> Set[str]:
        """Extract module dependencies from import statements."""
        dependencies = set()
        
        try:
            # Read the __init__.py file
            init_file = Path(module.__file__) if hasattr(module, '__file__') else None
            if init_file and init_file.exists():
                with open(init_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple regex to find import statements
                import re
                
                # From trading_bot.xxx import yyy
                from_imports = re.findall(r'from\s+trading_bot\.([a-zA-Z_][a-zA-Z0-9_]*)\s+import', content)
                dependencies.update(from_imports)
                
                # Import trading_bot.xxx
                direct_imports = re.findall(r'import\s+trading_bot\.([a-zA-Z_][a-zA-Z0-9_]*)', content)
                dependencies.update(direct_imports)
                
                # Filter out non-module imports
                dependencies = {d for d in dependencies if d in self.category_map}
        
        except Exception as e:
            logger.debug(f"Failed to extract dependencies: {e}")
        
        return dependencies
    
    def _get_module_priority(self, category: ModuleCategory) -> int:
        """Get loading priority for a module category."""
        priorities = {
            ModuleCategory.INFRASTRUCTURE: 100,
            ModuleCategory.DATA_CONNECTIVITY: 90,
            ModuleCategory.RISK_SAFETY: 80,
            ModuleCategory.ORCHESTRATION_MANAGEMENT: 70,
            ModuleCategory.ANALYSIS_INTELLIGENCE: 60,
            ModuleCategory.TRADING_EXECUTION: 50,
            ModuleCategory.OPTIMIZATION_EVOLUTION: 40,
            ModuleCategory.SPECIALIZED_SYSTEMS: 30,
            ModuleCategory.UNKNOWN: 10,
        }
        return priorities.get(category, 10)
    
    def resolve_dependencies(self) -> None:
        """Resolve and validate module dependencies."""
        logger.info("Resolving module dependencies...")
        
        # Build dependency graph
        for name, module_info in self.modules.items():
            for dep in module_info.dependencies:
                if dep in self.modules:
                    self.modules[dep].dependents.add(name)
                else:
                    logger.warning(f"Module {name} depends on {dep} which was not found")
        
        # Check for circular dependencies
        self._check_circular_dependencies()
        
        # Calculate load order
        self.load_order = self._calculate_load_order()
        
        logger.info(f"Dependency resolution complete. Load order: {len(self.load_order)} modules")
    
    def _check_circular_dependencies(self) -> None:
        """Check for circular dependencies in modules."""
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.modules[node].dependencies:
                if neighbor not in visited:
                    if dfs(neighbor, path + [neighbor]):
                        return True
                elif neighbor in rec_stack:
                    # Circular dependency found
                    cycle = path[path.index(neighbor):] + [neighbor]
                    logger.error(f"Circular dependency detected: {' -> '.join(cycle)}")
                    return True
            
            rec_stack.remove(node)
            return False
        
        for module_name in self.modules:
            if module_name not in visited:
                dfs(module_name, [module_name])
    
    def _calculate_load_order(self) -> List[str]:
        """Calculate module load order based on dependencies."""
        # Topological sort
        in_degree = {name: len(info.dependencies) for name, info in self.modules.items()}
        queue = [name for name, degree in in_degree.items() if degree == 0]
        load_order = []
        
        # Sort by priority within same level
        queue.sort(key=lambda x: self.modules[x].priority, reverse=True)
        
        while queue:
            node = queue.pop(0)
            load_order.append(node)
            
            # Update dependents
            for dependent in self.modules[node].dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
            
            # Maintain priority order
            queue.sort(key=lambda x: self.modules[x].priority, reverse=True)
        
        if len(load_order) != len(self.modules):
            logger.error("Circular dependency exists, could not determine complete load order")
        
        return load_order
    
    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """Get module info by name."""
        return self.modules.get(name)
    
    def get_modules_by_category(self, category: ModuleCategory) -> List[ModuleInfo]:
        """Get all modules in a category."""
        return [m for m in self.modules.values() if m.category == category]
    
    def get_enabled_modules(self) -> List[ModuleInfo]:
        """Get all enabled modules."""
        return [m for m in self.modules.values() if m.enabled]
    
    def enable_module(self, name: str) -> bool:
        """Enable a module."""
        if name in self.modules:
            self.modules[name].enabled = True
            return True
        return False
    
    def disable_module(self, name: str) -> bool:
        """Disable a module."""
        if name in self.modules:
            self.modules[name].enabled = False
            logger.info(f"Module {name} disabled")
            return True
        return False
    
    def initialize_module(self, name: str) -> bool:
        """Initialize a module."""
        if name not in self.modules:
            logger.error(f"Module {name} not found")
            return False
        
        module_info = self.modules[name]
        
        if not module_info.enabled:
            logger.warning(f"Module {name} is disabled")
            return False
        
        if module_info.initialized:
            logger.debug(f"Module {name} already initialized")
            return True
        
        try:
            # Initialize dependencies first
            for dep in module_info.dependencies:
                if not self.initialize_module(dep):
                    logger.error(f"Failed to initialize dependency {dep} for {name}")
                    return False
            
            # Initialize the module
            if module_info.module:
                # Look for initialize function
                if hasattr(module_info.module, 'initialize'):
                    result = module_info.module.initialize()
                    if asyncio.iscoroutine(result):
                        # Need to handle async initialization
                        logger.warning(f"Module {name} has async initialize, may need special handling")
                elif hasattr(module_info.module, 'init'):
                    module_info.module.init()
                
                module_info.initialized = True
                logger.info(f"Module {name} initialized successfully")
                return True
            else:
                logger.error(f"Module {name} has no loaded module object")
                return False
        
        except Exception as e:
            logger.error(f"Failed to initialize module {name}: {e}")
            module_info.import_error = str(e)
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        stats = {
            'total_modules': len(self.modules),
            'enabled_modules': len(self.get_enabled_modules()),
            'initialized_modules': len([m for m in self.modules.values() if m.initialized]),
            'categories': {},
            'load_order_length': len(getattr(self, 'load_order', [])),
        }
        
        for category in ModuleCategory:
            modules = self.get_modules_by_category(category)
            stats['categories'][category.value] = {
                'total': len(modules),
                'enabled': len([m for m in modules if m.enabled]),
                'initialized': len([m for m in modules if m.initialized]),
            }
        
        return stats
    
    def export_registry(self, filepath: str) -> None:
        """Export registry state to JSON file."""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'modules': {}
        }
        
        for name, info in self.modules.items():
            export_data['modules'][name] = {
                'path': info.path,
                'category': info.category.value,
                'class_name': info.class_name,
                'dependencies': list(info.dependencies),
                'dependents': list(info.dependents),
                'initialized': info.initialized,
                'enabled': info.enabled,
                'priority': info.priority,
                'metadata': info.metadata,
                'import_error': info.import_error,
            }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Registry exported to {filepath}")
