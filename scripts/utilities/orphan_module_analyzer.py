"""
Orphan Module Analyzer for AlphaAlgo Trading Bot
Identifies unused, unimported, and orphaned modules in the codebase.
"""

import os
import ast
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import re

class OrphanModuleAnalyzer:
    """Analyzes the codebase to find orphaned modules."""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.modules = {}  # module_path -> {classes, functions, imports}
        self.import_graph = defaultdict(set)  # module -> set of modules it imports
        self.reverse_import_graph = defaultdict(set)  # module -> set of modules that import it
        self.entry_points = set()  # main.py, run_*.py, etc.
        self.orphaned_modules = []
        self.partially_used_modules = []
        self.unused_functions = defaultdict(list)
        self.unused_classes = defaultdict(list)
        
    def scan_codebase(self):
        """Scan all Python files in the codebase."""
        print(f"[SCAN] Scanning codebase at: {self.root_dir}")
        
        # Find all Python files
        py_files = list(self.root_dir.rglob("*.py"))
        
        # Exclude certain directories
        exclude_patterns = [
            ".venv", "__pycache__", "backup", ".pytest_cache",
            "site-packages", "tests", "test_"
        ]
        
        py_files = [
            f for f in py_files 
            if not any(pattern in str(f) for pattern in exclude_patterns)
        ]
        
        print(f"[FILES] Found {len(py_files)} Python files to analyze")
        
        # Identify entry points
        for py_file in py_files:
            if py_file.name in ["main.py", "__main__.py"] or py_file.name.startswith("run_"):
                self.entry_points.add(str(py_file.relative_to(self.root_dir)))
        
        print(f"[ENTRY] Identified {len(self.entry_points)} entry points")
        
        # Parse each file
        for py_file in py_files:
            try:
                self._parse_file(py_file)
            except Exception as e:
                print(f"[WARN] Error parsing {py_file}: {e}")
        
        print(f"[OK] Parsed {len(self.modules)} modules")
        
    def _parse_file(self, file_path: Path):
        """Parse a Python file and extract information."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            rel_path = str(file_path.relative_to(self.root_dir))
            
            # Extract classes, functions, and imports
            classes = []
            functions = []
            imports = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    # Only top-level functions
                    if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                        functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
            
            self.modules[rel_path] = {
                'classes': classes,
                'functions': functions,
                'imports': imports,
                'path': str(file_path)
            }
            
            # Build import graph
            for imp in imports:
                # Try to resolve to actual module
                if imp == 'trading_bot':
                    # Track trading_bot imports
                    self.import_graph[rel_path].add('trading_bot')
                    self.reverse_import_graph['trading_bot'].add(rel_path)
                    
        except SyntaxError:
            # Some files may have syntax errors
            pass
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def build_dependency_graph(self):
        """Build a complete dependency graph."""
        print("\n[GRAPH] Building dependency graph...")
        
        # Search for actual import statements in files
        for module_path, module_info in self.modules.items():
            try:
                with open(module_info['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all imports
                import_pattern = r'from\s+([\w.]+)\s+import|import\s+([\w.]+)'
                matches = re.findall(import_pattern, content)
                
                for match in matches:
                    imported = match[0] or match[1]
                    # Resolve relative imports
                    if imported.startswith('trading_bot'):
                        self.import_graph[module_path].add(imported)
                        self.reverse_import_graph[imported].add(module_path)
                    elif imported.startswith('.'):
                        # Relative import
                        parent = str(Path(module_path).parent)
                        resolved = os.path.join(parent, imported.lstrip('.'))
                        self.import_graph[module_path].add(resolved)
                        self.reverse_import_graph[resolved].add(module_path)
            except Exception as e:
                pass
        
        print(f"[OK] Built dependency graph with {len(self.import_graph)} nodes")
    
    def find_orphaned_modules(self):
        """Identify modules that are never imported."""
        print("\n[ORPHAN] Identifying orphaned modules...")
        
        # Start from entry points and do BFS
        reachable = set()
        queue = list(self.entry_points)
        
        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue
            reachable.add(current)
            
            # Add all modules imported by current
            for imported in self.import_graph.get(current, set()):
                if imported not in reachable:
                    queue.append(imported)
        
        # Find unreachable modules
        all_modules = set(self.modules.keys())
        unreachable = all_modules - reachable
        
        # Categorize orphaned modules
        for module_path in unreachable:
            module_info = self.modules[module_path]
            
            # Check if it's imported anywhere
            if module_path not in self.reverse_import_graph or len(self.reverse_import_graph[module_path]) == 0:
                self.orphaned_modules.append({
                    'path': module_path,
                    'classes': module_info['classes'],
                    'functions': module_info['functions'],
                    'reason': 'Never imported anywhere'
                })
            else:
                self.partially_used_modules.append({
                    'path': module_path,
                    'classes': module_info['classes'],
                    'functions': module_info['functions'],
                    'imported_by': list(self.reverse_import_graph[module_path]),
                    'reason': 'Imported but not reachable from entry points'
                })
        
        print(f"[ALERT] Found {len(self.orphaned_modules)} completely orphaned modules")
        print(f"[WARN] Found {len(self.partially_used_modules)} partially used modules")
    
    def analyze_module_purpose(self, module_path: str) -> Dict:
        """Analyze module purpose based on name and content."""
        module_info = self.modules.get(module_path, {})
        path_parts = Path(module_path).parts
        
        # Categorize by directory
        category = "Unknown"
        integration_point = "Unknown"
        
        if "adaptive_systems" in path_parts:
            category = "Adaptive Trading System"
            integration_point = "trading_bot.adaptive_systems.master_controller"
        elif "advanced_features" in path_parts:
            category = "Advanced Trading Features"
            integration_point = "main.py or orchestrator"
        elif "ml" in path_parts or "ai" in path_parts:
            category = "Machine Learning / AI"
            integration_point = "trading_bot.ml or strategy engine"
        elif "risk" in path_parts:
            category = "Risk Management"
            integration_point = "trading_bot.risk.RiskManager"
        elif "execution" in path_parts:
            category = "Trade Execution"
            integration_point = "trading_bot.execution or main.py"
        elif "analysis" in path_parts or "analytics" in path_parts:
            category = "Market Analysis"
            integration_point = "strategy engine or main.py"
        elif "orchestrator" in path_parts:
            category = "System Orchestration"
            integration_point = "main.py"
        elif "opportunity_scanner" in path_parts:
            category = "Opportunity Detection"
            integration_point = "orchestrator or main.py"
        elif "data" in path_parts or "database" in path_parts:
            category = "Data Management"
            integration_point = "data pipeline or main.py"
        elif "monitoring" in path_parts or "system_health" in path_parts:
            category = "System Monitoring"
            integration_point = "main.py or system supervisor"
        elif "connectivity" in path_parts or "internet_access" in path_parts:
            category = "External Connectivity"
            integration_point = "main.py or data feeds"
        elif "dashboard" in path_parts or "visualization" in path_parts:
            category = "Visualization / Dashboard"
            integration_point = "dashboard server or main.py"
        elif "backtesting" in path_parts:
            category = "Backtesting"
            integration_point = "backtesting runner"
        elif "exit_strategies" in path_parts:
            category = "Exit Strategy Management"
            integration_point = "strategy engine or execution"
        elif "market_intelligence" in path_parts:
            category = "Market Intelligence"
            integration_point = "strategy engine or main.py"
        elif "self_improvement" in path_parts:
            category = "Self-Improvement System"
            integration_point = "adaptive systems or main.py"
        
        return {
            'category': category,
            'integration_point': integration_point,
            'classes': module_info.get('classes', []),
            'functions': module_info.get('functions', [])
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive report."""
        report = []
        report.append("=" * 80)
        report.append("ALPHAALGO ORPHANED MODULE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Modules Scanned: {len(self.modules)}")
        report.append(f"Entry Points: {len(self.entry_points)}")
        report.append(f"Completely Orphaned: {len(self.orphaned_modules)}")
        report.append(f"Partially Used: {len(self.partially_used_modules)}")
        report.append("")
        
        # Orphaned modules
        if self.orphaned_modules:
            report.append("COMPLETELY ORPHANED MODULES")
            report.append("-" * 80)
            
            # Group by category
            by_category = defaultdict(list)
            for module in self.orphaned_modules:
                analysis = self.analyze_module_purpose(module['path'])
                by_category[analysis['category']].append({
                    **module,
                    **analysis
                })
            
            for category, modules in sorted(by_category.items()):
                report.append(f"\n[{category}] ({len(modules)} modules)")
                report.append("")
                
                for module in modules:
                    report.append(f"  FILE: {module['path']}")
                    report.append(f"     Classes: {', '.join(module['classes']) if module['classes'] else 'None'}")
                    report.append(f"     Functions: {', '.join(module['functions'][:5]) if module['functions'] else 'None'}")
                    if len(module['functions']) > 5:
                        report.append(f"                ... and {len(module['functions']) - 5} more")
                    report.append(f"     Reason: {module['reason']}")
                    report.append(f"     Integration Point: {module['integration_point']}")
                    report.append(f"     Recommendation: {'INTEGRATE' if module['classes'] or module['functions'] else 'ARCHIVE'}")
                    report.append("")
        
        # Partially used modules
        if self.partially_used_modules:
            report.append("\nPARTIALLY USED MODULES")
            report.append("-" * 80)
            
            for module in self.partially_used_modules[:20]:  # Limit to top 20
                analysis = self.analyze_module_purpose(module['path'])
                report.append(f"\n  FILE: {module['path']}")
                report.append(f"     Category: {analysis['category']}")
                report.append(f"     Classes: {', '.join(module['classes']) if module['classes'] else 'None'}")
                report.append(f"     Imported By: {', '.join(module['imported_by'][:3])}")
                if len(module['imported_by']) > 3:
                    report.append(f"                  ... and {len(module['imported_by']) - 3} more")
                report.append(f"     Reason: {module['reason']}")
                report.append("")
        
        # Entry points
        report.append("\nENTRY POINTS")
        report.append("-" * 80)
        for entry in sorted(self.entry_points):
            report.append(f"  • {entry}")
        report.append("")
        
        return "\n".join(report)
    
    def save_json_report(self, output_file: str):
        """Save detailed JSON report."""
        data = {
            'summary': {
                'total_modules': len(self.modules),
                'entry_points': len(self.entry_points),
                'orphaned_modules': len(self.orphaned_modules),
                'partially_used_modules': len(self.partially_used_modules)
            },
            'orphaned_modules': [
                {
                    **module,
                    **self.analyze_module_purpose(module['path'])
                }
                for module in self.orphaned_modules
            ],
            'partially_used_modules': [
                {
                    **module,
                    **self.analyze_module_purpose(module['path'])
                }
                for module in self.partially_used_modules
            ],
            'entry_points': list(self.entry_points)
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[SAVE] Saved JSON report to: {output_file}")


def main():
    """Main execution."""
    root_dir = r"c:\Users\peterson\trading bot"
    
    analyzer = OrphanModuleAnalyzer(root_dir)
    
    # Run analysis
    analyzer.scan_codebase()
    analyzer.build_dependency_graph()
    analyzer.find_orphaned_modules()
    
    # Generate reports
    report = analyzer.generate_report()
    print("\n" + report)
    
    # Save reports
    with open(os.path.join(root_dir, "ORPHAN_MODULE_REPORT.md"), 'w') as f:
        f.write(report)
    
    analyzer.save_json_report(os.path.join(root_dir, "orphan_module_report.json"))
    
    print("\n[OK] Analysis complete!")
    print(f"[REPORT] Report saved to: ORPHAN_MODULE_REPORT.md")
    print(f"[REPORT] JSON report saved to: orphan_module_report.json")


if __name__ == "__main__":
    main()
