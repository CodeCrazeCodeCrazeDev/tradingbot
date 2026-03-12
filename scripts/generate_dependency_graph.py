"""
Dependency Graph Generator for Quantitative Systems Integration

This script analyzes the module inventory and generates dependency mapping
structures for systematic integration planning.

Usage:
    python scripts/generate_dependency_graph.py
"""

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple


class DependencyAnalyzer:
    """Analyzes module dependencies and generates integration order."""
    
    def __init__(self, inventory_path: str):
        self.inventory_path = inventory_path
        self.modules: List[Dict] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        self.domain_deps: Dict[str, Set[str]] = defaultdict(set)
        
    def load_inventory(self) -> None:
        """Load the module inventory from JSON."""
        with open(self.inventory_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.modules = data.get('modules', [])
        print(f"Loaded {len(self.modules)} modules from inventory")
    
    def build_dependency_graph(self) -> None:
        """Build the dependency graph from module imports."""
        for module in self.modules:
            module_key = module['relative_path']
            
            # Add internal imports as dependencies
            for imp in module.get('imports_internal', []):
                self.dependency_graph[module_key].add(imp)
                self.reverse_deps[imp].add(module_key)
            
            # Track domain-level dependencies
            domain = module.get('domain', 'unknown')
            for imp in module.get('imports_internal', []):
                # Extract domain from import path
                imp_domain = self._get_domain_from_import(imp)
                if imp_domain and imp_domain != domain:
                    self.domain_deps[domain].add(imp_domain)
    
    def _get_domain_from_import(self, import_path: str) -> str:
        """Determine domain from import path."""
        path_lower = import_path.lower()
        
        domain_keywords = {
            'D01_data_infrastructure': ['data', 'database', 'db', 'storage', 'cache', 'stream', 'feed', 'ingestion'],
            'D02_risk_management': ['risk', 'position', 'sizing', 'drawdown', 'limit', 'exposure', 'hedge', 'safety'],
            'D03_execution': ['execution', 'order', 'broker', 'fill', 'routing', 'slippage'],
            'D04_signal_generation': ['signal', 'strategy', 'indicator', 'pattern', 'analysis'],
            'D05_ai_ml': ['ml', 'ai', 'model', 'neural', 'learning', 'prediction', 'cognitive', 'brain'],
            'D06_security_compliance': ['security', 'auth', 'compliance', 'audit', 'encrypt'],
            'D07_infrastructure': ['infrastructure', 'health', 'monitor', 'metric', 'log', 'config', 'util', 'core'],
            'D08_governance': ['governance', 'approval', 'human', 'oversight'],
            'D09_performance': ['performance', 'analytics', 'attribution', 'report'],
            'D10_integration': ['api', 'adapter', 'interface', 'protocol'],
            'D11_testing': ['test', 'mock', 'fixture'],
            'D12_documentation': ['doc', 'example', 'demo'],
        }
        
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in path_lower:
                    return domain
        return 'D07_infrastructure'
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the graph."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return False
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in list(self.dependency_graph.keys())[:1000]:  # Limit for performance
            if node not in visited:
                dfs(node)
        
        return cycles[:50]  # Return first 50 cycles
    
    def calculate_integration_order(self) -> List[Tuple[str, int]]:
        """Calculate optimal integration order using topological sort."""
        # Calculate in-degree for each module
        in_degree = defaultdict(int)
        all_modules = set(self.dependency_graph.keys())
        
        for deps in self.dependency_graph.values():
            for dep in deps:
                in_degree[dep] += 1
        
        # Find modules with no dependencies (start points)
        no_deps = [m for m in all_modules if in_degree[m] == 0]
        
        # Sort by number of dependents (most dependents first)
        no_deps.sort(key=lambda x: len(self.reverse_deps.get(x, set())), reverse=True)
        
        order = []
        level = 0
        
        while no_deps:
            level += 1
            next_level = []
            
            for module in no_deps:
                order.append((module, level))
                
                # Reduce in-degree for dependents
                for dependent in self.reverse_deps.get(module, set()):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_level.append(dependent)
            
            next_level.sort(key=lambda x: len(self.reverse_deps.get(x, set())), reverse=True)
            no_deps = next_level
        
        return order
    
    def get_hub_modules(self, top_n: int = 50) -> List[Tuple[str, int, str]]:
        """Get modules with most dependents (hub modules)."""
        hub_counts = []
        
        for module in self.modules:
            module_key = module['relative_path']
            dependent_count = len(self.reverse_deps.get(module_key, set()))
            
            # Also count imports that reference this module's package
            package = module.get('package', '')
            if package:
                for imp, deps in self.reverse_deps.items():
                    if package in imp:
                        dependent_count += len(deps)
            
            if dependent_count > 0:
                hub_counts.append((
                    module_key,
                    dependent_count,
                    module.get('domain', 'unknown')
                ))
        
        hub_counts.sort(key=lambda x: x[1], reverse=True)
        return hub_counts[:top_n]
    
    def get_leaf_modules(self, top_n: int = 50) -> List[Tuple[str, str]]:
        """Get modules with no dependents (leaf modules)."""
        leaves = []
        
        for module in self.modules:
            module_key = module['relative_path']
            if module_key not in self.reverse_deps or len(self.reverse_deps[module_key]) == 0:
                leaves.append((module_key, module.get('domain', 'unknown')))
        
        return leaves[:top_n]
    
    def get_domain_dependency_matrix(self) -> Dict[str, Dict[str, int]]:
        """Generate domain-to-domain dependency matrix."""
        matrix = defaultdict(lambda: defaultdict(int))
        
        for module in self.modules:
            source_domain = module.get('domain', 'unknown')
            
            for imp in module.get('imports_internal', []):
                target_domain = self._get_domain_from_import(imp)
                if target_domain != source_domain:
                    matrix[source_domain][target_domain] += 1
        
        return dict(matrix)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive dependency report."""
        self.build_dependency_graph()
        
        # Find circular dependencies
        print("Finding circular dependencies...")
        cycles = self.find_circular_dependencies()
        
        # Calculate integration order
        print("Calculating integration order...")
        integration_order = self.calculate_integration_order()
        
        # Get hub and leaf modules
        print("Identifying hub and leaf modules...")
        hub_modules = self.get_hub_modules(50)
        leaf_modules = self.get_leaf_modules(50)
        
        # Get domain dependency matrix
        print("Building domain dependency matrix...")
        domain_matrix = self.get_domain_dependency_matrix()
        
        # Calculate statistics
        total_dependencies = sum(len(deps) for deps in self.dependency_graph.values())
        avg_dependencies = total_dependencies / len(self.modules) if self.modules else 0
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_modules': len(self.modules),
                'total_dependencies': total_dependencies,
                'average_dependencies_per_module': round(avg_dependencies, 2),
                'circular_dependencies_found': len(cycles),
                'hub_modules_count': len(hub_modules),
                'leaf_modules_count': len(leaf_modules),
            },
            'circular_dependencies': cycles[:20],
            'hub_modules': [
                {'module': m, 'dependents': d, 'domain': dom}
                for m, d, dom in hub_modules
            ],
            'leaf_modules': [
                {'module': m, 'domain': dom}
                for m, dom in leaf_modules
            ],
            'domain_dependency_matrix': domain_matrix,
            'integration_order_sample': [
                {'module': m, 'level': l}
                for m, l in integration_order[:100]
            ],
        }
        
        return report
    
    def save_report(self, output_path: str) -> None:
        """Save the dependency report."""
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Dependency report saved to: {output_path}")
        
        # Generate markdown summary
        self._generate_markdown_summary(report, output_path.replace('.json', '.md'))
    
    def _generate_markdown_summary(self, report: Dict, output_path: str) -> None:
        """Generate markdown summary of dependencies."""
        summary = report['summary']
        
        md = f"""# Dependency Analysis Report

**Generated**: {report['generated_at']}

## Summary

| Metric | Value |
|--------|-------|
| Total Modules | {summary['total_modules']:,} |
| Total Dependencies | {summary['total_dependencies']:,} |
| Avg Dependencies/Module | {summary['average_dependencies_per_module']} |
| Circular Dependencies | {summary['circular_dependencies_found']} |
| Hub Modules | {summary['hub_modules_count']} |
| Leaf Modules | {summary['leaf_modules_count']} |

## Domain Dependency Matrix

This shows how many imports flow from one domain to another:

| Source Domain | Target Domains |
|---------------|----------------|
"""
        for source, targets in sorted(report['domain_dependency_matrix'].items()):
            target_str = ', '.join([f"{t}: {c}" for t, c in sorted(targets.items(), key=lambda x: -x[1])[:5]])
            md += f"| {source} | {target_str} |\n"
        
        md += """
## Hub Modules (Most Dependents)

These modules are imported by many others and should be integrated first:

| Module | Dependents | Domain |
|--------|------------|--------|
"""
        for hub in report['hub_modules'][:20]:
            md += f"| `{hub['module']}` | {hub['dependents']} | {hub['domain']} |\n"
        
        if report['circular_dependencies']:
            md += """
## Circular Dependencies (MUST FIX)

These circular dependencies must be resolved before integration:

"""
            for i, cycle in enumerate(report['circular_dependencies'][:10], 1):
                md += f"{i}. `{' → '.join(cycle[:5])}{'...' if len(cycle) > 5 else ''}`\n"
        
        md += """
## Integration Order (First 20)

Start integration with these modules:

| Level | Module |
|-------|--------|
"""
        for item in report['integration_order_sample'][:20]:
            md += f"| {item['level']} | `{item['module']}` |\n"
        
        md += """
## Recommended Integration Strategy

### Phase 1: Foundation (Level 1-2)
- Core utilities and constants
- Logging and configuration
- Base classes and interfaces

### Phase 2: Infrastructure (Level 3-5)
- Database connections
- Message bus
- Health monitoring

### Phase 3: Domain Services (Level 6-10)
- Risk management
- Data pipelines
- Execution engine

### Phase 4: Business Logic (Level 11-15)
- Strategies
- ML models
- Signal generation

### Phase 5: Integration (Level 16-20)
- APIs
- External adapters
- Orchestration

## Next Steps

1. **Fix Circular Dependencies**: Resolve all circular imports before proceeding
2. **Start with Hub Modules**: Integrate high-dependency modules first
3. **Follow Level Order**: Integrate modules level by level
4. **Test Each Level**: Verify integration before moving to next level
5. **Document as You Go**: Update integration status for each module
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"Markdown summary saved to: {output_path}")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent
    
    # Find the latest inventory file
    integration_dir = base_path / 'docs' / 'integration'
    inventory_files = list(integration_dir.glob('module_inventory_*.json'))
    
    if not inventory_files:
        print("ERROR: No module inventory found. Run generate_module_inventory.py first.")
        return
    
    # Use the most recent inventory
    latest_inventory = max(inventory_files, key=lambda p: p.stat().st_mtime)
    print(f"Using inventory: {latest_inventory}")
    
    # Analyze dependencies
    analyzer = DependencyAnalyzer(str(latest_inventory))
    analyzer.load_inventory()
    
    # Generate report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = integration_dir / f'dependency_analysis_{timestamp}.json'
    analyzer.save_report(str(output_path))
    
    # Print summary
    print("\n" + "=" * 60)
    print("DEPENDENCY ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
