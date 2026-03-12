"""
Dependency Resolver - Resolves and manages module dependencies.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import networkx as nx

logger = logging.getLogger(__name__)

class DependencyStatus(Enum):
    """Status of dependency resolution."""
    RESOLVED = "resolved"
    PENDING = "pending"
    FAILED = "failed"
    CIRCULAR = "circular"
    MISSING = "missing"

@dataclass
class DependencyNode:
    """A node in the dependency graph."""
    name: str
    dependencies: Set[str]
    dependents: Set[str]
    status: DependencyStatus = DependencyStatus.PENDING
    priority: int = 0
    version: Optional[str] = None
    optional: Set[str] = None  # Optional dependencies
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = set()
        if self.dependents is None:
            self.dependents = set()
        if self.optional is None:
            self.optional = set()

class DependencyResolver:
    """
    Resolves module dependencies and determines initialization order.
    
    Features:
    - Topological sorting for dependency order
    - Circular dependency detection
    - Optional dependency handling
    - Version compatibility checking
    - Priority-based ordering
    """
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.graph: Optional[nx.DiGraph] = None
        self._resolved_order: List[str] = []
        self._circular_deps: List[List[str]] = []
        
    def add_module(self, 
                   name: str, 
                   dependencies: List[str] = None,
                   optional: List[str] = None,
                   priority: int = 0,
                   version: str = None) -> None:
        """
        Add a module to the dependency graph.
        
        Args:
            name: Module name
            dependencies: List of required dependencies
            optional: List of optional dependencies
            priority: Loading priority (higher = loaded first)
            version: Module version
        """
        if name in self.nodes:
            logger.warning(f"Module {name} already exists, updating")
        
        node = DependencyNode(
            name=name,
            dependencies=set(dependencies or []),
            optional=set(optional or []),
            priority=priority,
            version=version
        )
        
        self.nodes[name] = node
        self._invalidate_graph()
        
        logger.debug(f"Added module {name} with {len(node.dependencies)} dependencies")
    
    def remove_module(self, name: str) -> bool:
        """Remove a module from the dependency graph."""
        if name not in self.nodes:
            return False
        
        # Remove from dependents of its dependencies
        node = self.nodes[name]
        for dep in node.dependencies:
            if dep in self.nodes:
                self.nodes[dep].dependents.discard(name)
        
        # Remove the node
        del self.nodes[name]
        self._invalidate_graph()
        
        logger.debug(f"Removed module {name}")
        return True
    
    def add_dependency(self, module: str, dependency: str, optional: bool = False) -> bool:
        """
        Add a dependency to a module.
        
        Args:
            module: Module name
            dependency: Dependency name
            optional: Whether dependency is optional
            
        Returns:
            True if added successfully
        """
        if module not in self.nodes:
            logger.error(f"Module {module} not found")
            return False
        
        node = self.nodes[module]
        
        if optional:
            node.optional.add(dependency)
        else:
            node.dependencies.add(dependency)
        
        # Update dependents
        if dependency in self.nodes:
            self.nodes[dependency].dependents.add(module)
        
        self._invalidate_graph()
        logger.debug(f"Added dependency {dependency} to {module} (optional={optional})")
        return True
    
    def remove_dependency(self, module: str, dependency: str) -> bool:
        """Remove a dependency from a module."""
        if module not in self.nodes:
            return False
        
        node = self.nodes[module]
        node.dependencies.discard(dependency)
        node.optional.discard(dependency)
        
        # Update dependents
        if dependency in self.nodes:
            self.nodes[dependency].dependents.discard(module)
        
        self._invalidate_graph()
        return True
    
    def resolve(self) -> Tuple[bool, List[str], List[str]]:
        """
        Resolve all dependencies and determine load order.
        
        Returns:
            Tuple of (success, resolved_order, error_messages)
        """
        # Build graph
        self._build_graph()
        
        # Check for missing dependencies
        missing = self._check_missing()
        if missing:
            errors = [f"Missing dependencies: {', '.join(missing)}"]
            return False, [], errors
        
        # Check for circular dependencies
        circular = self._check_circular()
        if circular:
            errors = [f"Circular dependencies detected: {circular}"]
            return False, [], errors
        
        # Get topological order
        try:
            order = list(nx.topological_sort(self.graph))
            
            # Sort by priority within each level
            order = self._sort_by_priority(order)
            
            self._resolved_order = order
            logger.info(f"Resolved {len(order)} modules in dependency order")
            
            return True, order, []
            
        except nx.NetworkXError as e:
            return False, [], [f"Failed to resolve dependencies: {e}"]
    
    def _build_graph(self) -> None:
        """Build the NetworkX dependency graph."""
        self.graph = nx.DiGraph()
        
        # Add nodes
        for name, node in self.nodes.items():
            self.graph.add_node(name, priority=node.priority, version=node.version)
        
        # Add edges (dependencies)
        for name, node in self.nodes.items():
            for dep in node.dependencies:
                if dep in self.nodes:
                    self.graph.add_edge(dep, name)  # Edge from dependency to module
        
        logger.debug(f"Built dependency graph with {len(self.graph.nodes)} nodes")
    
    def _invalidate_graph(self) -> None:
        """Invalidate the current graph to force rebuild."""
        self.graph = None
        self._resolved_order = []
        self._circular_deps = []
    
    def _check_missing(self) -> List[str]:
        """Check for missing dependencies."""
        missing = set()
        
        for name, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    missing.add(dep)
                    node.status = DependencyStatus.FAILED
        
        return list(missing)
    
    def _check_circular(self) -> List[List[str]]:
        """Check for circular dependencies."""
        if not self.graph:
            self._build_graph()
        
        try:
            cycles = list(nx.simple_cycles(self.graph))
            self._circular_deps = cycles
            
            # Mark nodes in cycles as failed
            for cycle in cycles:
                for node in cycle:
                    if node in self.nodes:
                        self.nodes[node].status = DependencyStatus.CIRCULAR
            
            return cycles
            
        except Exception as e:
            logger.error(f"Error checking circular dependencies: {e}")
            return []
    
    def _sort_by_priority(self, order: List[str]) -> List[str]:
        """Sort modules by priority while maintaining dependency order."""
        # Group by dependency level
        levels = []
        remaining = set(order)
        
        while remaining:
            # Find modules with no remaining dependencies
            current_level = []
            for module in list(remaining):
                deps = self.nodes[module].dependencies
                if not deps.intersection(remaining):
                    current_level.append(module)
            
            if not current_level:
                # Should not happen if graph is valid
                logger.warning("Could not determine dependency levels")
                break
            
            # Sort by priority within level
            current_level.sort(key=lambda x: self.nodes[x].priority, reverse=True)
            levels.append(current_level)
            
            # Remove processed modules
            for module in current_level:
                remaining.remove(module)
        
        # Flatten levels
        result = []
        for level in levels:
            result.extend(level)
        
        return result
    
    def get_load_order(self) -> List[str]:
        """Get the resolved load order."""
        return self._resolved_order.copy()
    
    def get_dependents(self, module: str) -> List[str]:
        """Get all modules that depend on the given module."""
        if module not in self.nodes:
            return []
        return list(self.nodes[module].dependents)
    
    def get_dependencies(self, module: str, include_optional: bool = False) -> List[str]:
        """Get all dependencies of a module."""
        if module not in self.nodes:
            return []
        
        node = self.nodes[module]
        deps = list(node.dependencies)
        
        if include_optional:
            deps.extend(node.optional)
        
        return deps
    
    def get_initialization_order(self, modules: List[str] = None) -> List[str]:
        """
        Get initialization order for specific modules.
        
        Args:
            modules: List of modules to initialize (all if None)
            
        Returns:
            Ordered list of modules to initialize
        """
        if modules is None:
            modules = list(self.nodes.keys())
        
        # Filter load order to only include requested modules
        ordered = []
        for module in self._resolved_order:
            if module in modules:
                ordered.append(module)
        
        # Add any modules not in resolved order (shouldn't happen)
        for module in modules:
            if module not in ordered and module in self.nodes:
                ordered.append(module)
                logger.warning(f"Module {module} not in resolved order")
        
        return ordered
    
    def validate_resolution(self) -> Dict[str, any]:
        """
        Validate the dependency resolution.
        
        Returns:
            Validation report
        """
        report = {
            'valid': True,
            'total_modules': len(self.nodes),
            'resolved_modules': 0,
            'failed_modules': 0,
            'missing_dependencies': [],
            'circular_dependencies': [],
            'warnings': []
        }
        
        for name, node in self.nodes.items():
            if node.status == DependencyStatus.RESOLVED:
                report['resolved_modules'] += 1
            elif node.status == DependencyStatus.FAILED:
                report['failed_modules'] += 1
                report['valid'] = False
        
        report['missing_dependencies'] = self._check_missing()
        report['circular_dependencies'] = self._circular_deps
        
        if report['missing_dependencies']:
            report['valid'] = False
        
        if report['circular_dependencies']:
            report['valid'] = False
        
        # Check for isolated modules
        isolated = []
        for name, node in self.nodes.items():
            if not node.dependencies and not node.dependents:
                isolated.append(name)
        
        if isolated:
            report['warnings'].append(f"Isolated modules: {', '.join(isolated)}")
        
        return report
    
    def export_graph(self, filepath: str, format: str = 'dot') -> bool:
        """
        Export dependency graph to file.
        
        Args:
            filepath: Output file path
            format: Export format ('dot', 'png', 'svg')
            
        Returns:
            True if export successful
        """
        if not self.graph:
            self._build_graph()
        
        try:
            if format == 'dot':
                nx.drawing.nx_pydot.write_dot(self.graph, filepath)
            else:
                # Use matplotlib for other formats
                import matplotlib.pyplot as plt
                
                pos = nx.spring_layout(self.graph)
                nx.draw(self.graph, pos, with_labels=True, node_size=1000, 
                       node_color='lightblue', font_size=8)
                
                if format == 'png':
                    plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
                elif format == 'svg':
                    plt.savefig(filepath, format='svg', bbox_inches='tight')
                
                plt.close()
            
            logger.info(f"Dependency graph exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export graph: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, any]:
        """Get dependency resolution statistics."""
        if not self.graph:
            self._build_graph()
        
        stats = {
            'total_modules': len(self.nodes),
            'total_dependencies': sum(len(n.dependencies) for n in self.nodes.values()),
            'total_optional': sum(len(n.optional) for n in self.nodes.values()),
            'max_dependencies': 0,
            'max_dependents': 0,
            'average_dependencies': 0,
            'average_dependents': 0,
            'circular_cycles': len(self._circular_deps)
        }
        
        if self.nodes:
            stats['max_dependencies'] = max(len(n.dependencies) for n in self.nodes.values())
            stats['max_dependents'] = max(len(n.dependents) for n in self.nodes.values())
            stats['average_dependencies'] = stats['total_dependencies'] / len(self.nodes)
            stats['average_dependents'] = sum(len(n.dependents) for n in self.nodes.values()) / len(self.nodes)
        
        return stats
