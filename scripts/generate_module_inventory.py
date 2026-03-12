"""
Module Inventory Generator for Quantitative Systems Integration

This script scans all Python modules from advanced_systems 2/ through trading_bot/wealth.py
and generates a comprehensive inventory for systematic integration.

Usage:
    python scripts/generate_module_inventory.py
"""

import ast
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict
import hashlib


@dataclass
class ModuleInfo:
    """Information about a single Python module."""
    file_path: str
    module_name: str
    package: str
    relative_path: str
    file_size: int
    line_count: int
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports_internal: List[str] = field(default_factory=list)
    imports_external: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    has_main: bool = False
    has_async: bool = False
    domain: str = "unclassified"
    integration_status: str = "pending"
    complexity_score: int = 0
    notes: str = ""
    parse_error: Optional[str] = None


class ModuleAnalyzer:
    """Analyzes Python modules and extracts metadata."""
    
    # Known external packages
    EXTERNAL_PACKAGES = {
        'numpy', 'pandas', 'scipy', 'sklearn', 'torch', 'tensorflow',
        'asyncio', 'aiohttp', 'requests', 'httpx', 'websockets',
        'redis', 'kafka', 'zmq', 'celery', 'rabbitmq',
        'sqlalchemy', 'sqlite3', 'psycopg2', 'pymongo', 'influxdb',
        'fastapi', 'flask', 'django', 'starlette', 'uvicorn',
        'pydantic', 'dataclasses', 'typing', 'typing_extensions',
        'logging', 'json', 'yaml', 'toml', 'configparser',
        'os', 'sys', 'pathlib', 'shutil', 'glob', 'fnmatch',
        'datetime', 'time', 'calendar', 'dateutil',
        're', 'string', 'textwrap', 'difflib',
        'collections', 'itertools', 'functools', 'operator',
        'math', 'random', 'statistics', 'decimal', 'fractions',
        'hashlib', 'hmac', 'secrets', 'cryptography',
        'threading', 'multiprocessing', 'concurrent', 'queue',
        'subprocess', 'signal', 'select', 'selectors',
        'socket', 'ssl', 'email', 'smtplib',
        'unittest', 'pytest', 'mock', 'hypothesis',
        'argparse', 'click', 'typer', 'fire',
        'structlog', 'loguru', 'colorama', 'rich', 'tqdm',
        'matplotlib', 'seaborn', 'plotly', 'bokeh',
        'PIL', 'cv2', 'imageio', 'skimage',
        'nltk', 'spacy', 'transformers', 'huggingface',
        'gym', 'stable_baselines3', 'ray', 'optuna',
        'ta', 'talib', 'backtrader', 'zipline', 'bt',
        'ccxt', 'binance', 'alpaca', 'ib_insync',
        'prometheus_client', 'opentelemetry', 'jaeger',
        'boto3', 'google', 'azure', 'docker', 'kubernetes',
        'abc', 'enum', 'copy', 'pickle', 'shelve', 'dbm',
        'io', 'tempfile', 'contextlib', 'atexit', 'traceback',
        'warnings', 'inspect', 'dis', 'gc', 'weakref',
        'uuid', 'base64', 'binascii', 'struct', 'codecs',
        'html', 'xml', 'csv', 'configparser',
        'http', 'urllib', 'ftplib', 'telnetlib',
        'ipaddress', 'netrc', 'nntplib', 'poplib', 'imaplib',
        'cProfile', 'profile', 'timeit', 'trace', 'tracemalloc',
        'MetaTrader5', 'mt5', 'mplfinance', 'yfinance',
        'networkx', 'igraph', 'graphviz',
        'sympy', 'numba', 'cython', 'cffi', 'ctypes',
        'qiskit', 'cirq', 'pennylane',
        'web3', 'eth_account', 'brownie',
    }
    
    # Domain classification keywords
    DOMAIN_KEYWORDS = {
        'D01_data_infrastructure': ['data', 'database', 'db', 'storage', 'cache', 'stream', 'feed', 'ingestion', 'pipeline'],
        'D02_risk_management': ['risk', 'position', 'sizing', 'drawdown', 'limit', 'exposure', 'hedge', 'safety'],
        'D03_execution': ['execution', 'order', 'broker', 'fill', 'routing', 'slippage', 'trade'],
        'D04_signal_generation': ['signal', 'strategy', 'indicator', 'pattern', 'analysis', 'technical'],
        'D05_ai_ml': ['ml', 'ai', 'model', 'neural', 'learning', 'prediction', 'cognitive', 'rl', 'reinforcement'],
        'D06_security_compliance': ['security', 'auth', 'compliance', 'audit', 'encrypt', 'credential', 'permission'],
        'D07_infrastructure': ['infrastructure', 'health', 'monitor', 'metric', 'log', 'config', 'util'],
        'D08_governance': ['governance', 'approval', 'human', 'oversight', 'constraint', 'rule'],
        'D09_performance': ['performance', 'analytics', 'attribution', 'report', 'metric', 'benchmark'],
        'D10_integration': ['api', 'adapter', 'interface', 'protocol', 'webhook', 'rest', 'grpc'],
        'D11_testing': ['test', 'mock', 'fixture', 'assert', 'validate', 'verify'],
        'D12_documentation': ['doc', 'example', 'demo', 'tutorial', 'guide', 'readme'],
    }
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.modules: List[ModuleInfo] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        
    def analyze_file(self, file_path: Path) -> Optional[ModuleInfo]:
        """Analyze a single Python file."""
        try:
            relative_path = str(file_path.relative_to(self.base_path))
            module_name = file_path.stem
            package = str(file_path.parent.relative_to(self.base_path)).replace(os.sep, '.')
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            line_count = len(content.splitlines())
            file_size = file_path.stat().st_size
            
            info = ModuleInfo(
                file_path=str(file_path),
                module_name=module_name,
                package=package if package != '.' else '',
                relative_path=relative_path,
                file_size=file_size,
                line_count=line_count,
            )
            
            try:
                tree = ast.parse(content)
                self._extract_from_ast(tree, info, content)
            except SyntaxError as e:
                info.parse_error = f"SyntaxError: {e}"
            
            # Classify domain
            info.domain = self._classify_domain(relative_path, info)
            
            # Calculate complexity
            info.complexity_score = self._calculate_complexity(info)
            
            return info
            
        except Exception as e:
            return ModuleInfo(
                file_path=str(file_path),
                module_name=file_path.stem,
                package="",
                relative_path=str(file_path.relative_to(self.base_path)),
                file_size=0,
                line_count=0,
                parse_error=str(e)
            )
    
    def _extract_from_ast(self, tree: ast.AST, info: ModuleInfo, content: str) -> None:
        """Extract information from AST."""
        for node in ast.walk(tree):
            # Classes
            if isinstance(node, ast.ClassDef):
                info.classes.append(node.name)
            
            # Functions
            elif isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_') or node.name in ('__init__', '__call__'):
                    info.functions.append(node.name)
            
            # Async functions
            elif isinstance(node, ast.AsyncFunctionDef):
                info.has_async = True
                if not node.name.startswith('_'):
                    info.functions.append(node.name)
            
            # Imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self._classify_import(alias.name, info)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._classify_import(node.module, info)
        
        # Check for __all__
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    info.exports.append(elt.value)
        
        # Check for if __name__ == "__main__"
        if 'if __name__' in content and '__main__' in content:
            info.has_main = True
    
    def _classify_import(self, module_name: str, info: ModuleInfo) -> None:
        """Classify an import as internal or external."""
        root_module = module_name.split('.')[0]
        
        if root_module in self.EXTERNAL_PACKAGES:
            if module_name not in info.imports_external:
                info.imports_external.append(module_name)
        elif root_module in ('trading_bot', 'trading', 'broker', 'api', 'utils', 
                            'validation', 'config', 'tests', 'examples', 'scripts'):
            if module_name not in info.imports_internal:
                info.imports_internal.append(module_name)
        else:
            # Could be either - check if it looks like a standard library
            if root_module.islower() and len(root_module) <= 12:
                if module_name not in info.imports_external:
                    info.imports_external.append(module_name)
            else:
                if module_name not in info.imports_internal:
                    info.imports_internal.append(module_name)
    
    def _classify_domain(self, path: str, info: ModuleInfo) -> str:
        """Classify module into a domain based on path and content."""
        path_lower = path.lower()
        
        # Check path against domain keywords
        scores = defaultdict(int)
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in path_lower:
                    scores[domain] += 2
                # Check class/function names
                for cls in info.classes:
                    if keyword in cls.lower():
                        scores[domain] += 1
                for func in info.functions:
                    if keyword in func.lower():
                        scores[domain] += 1
        
        if scores:
            return max(scores, key=scores.get)
        return "D07_infrastructure"  # Default
    
    def _calculate_complexity(self, info: ModuleInfo) -> int:
        """Calculate a complexity score for the module."""
        score = 0
        score += len(info.classes) * 10
        score += len(info.functions) * 2
        score += len(info.imports_internal) * 3
        score += len(info.imports_external) * 1
        score += info.line_count // 50
        if info.has_async:
            score += 5
        return score
    
    def scan_directory(self, start_dir: str = None, end_file: str = None) -> None:
        """Scan all Python files in the directory."""
        scan_path = self.base_path / start_dir if start_dir else self.base_path
        
        # Get all Python files
        all_files = []
        for root, dirs, files in os.walk(self.base_path):
            # Skip hidden directories and common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                      ('__pycache__', 'node_modules', '.git', '.venv', 'venv', 
                       'htmlcov', '.pytest_cache', '.hypothesis', 'mlruns')]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    all_files.append(file_path)
        
        # Sort files for consistent ordering
        all_files.sort()
        
        print(f"Found {len(all_files)} Python files to analyze...")
        
        # Analyze each file
        for i, file_path in enumerate(all_files):
            if (i + 1) % 500 == 0:
                print(f"  Analyzed {i + 1}/{len(all_files)} files...")
            
            info = self.analyze_file(file_path)
            if info:
                self.modules.append(info)
                
                # Build dependency graph
                module_key = info.relative_path
                for imp in info.imports_internal:
                    self.dependency_graph[module_key].add(imp)
                    self.reverse_deps[imp].add(module_key)
        
        print(f"Completed analysis of {len(self.modules)} modules.")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report."""
        # Domain statistics
        domain_stats = defaultdict(lambda: {'count': 0, 'total_lines': 0, 'modules': []})
        for mod in self.modules:
            domain_stats[mod.domain]['count'] += 1
            domain_stats[mod.domain]['total_lines'] += mod.line_count
            domain_stats[mod.domain]['modules'].append(mod.relative_path)
        
        # Find hub modules (many dependents)
        hub_modules = sorted(
            [(k, len(v)) for k, v in self.reverse_deps.items()],
            key=lambda x: x[1],
            reverse=True
        )[:50]
        
        # Find modules with parse errors
        error_modules = [m for m in self.modules if m.parse_error]
        
        # Calculate totals
        total_lines = sum(m.line_count for m in self.modules)
        total_classes = sum(len(m.classes) for m in self.modules)
        total_functions = sum(len(m.functions) for m in self.modules)
        async_modules = sum(1 for m in self.modules if m.has_async)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_modules': len(self.modules),
                'total_lines': total_lines,
                'total_classes': total_classes,
                'total_functions': total_functions,
                'async_modules': async_modules,
                'modules_with_errors': len(error_modules),
            },
            'domain_statistics': {
                k: {'count': v['count'], 'total_lines': v['total_lines']}
                for k, v in sorted(domain_stats.items())
            },
            'hub_modules': hub_modules[:20],
            'error_modules': [
                {'path': m.relative_path, 'error': m.parse_error}
                for m in error_modules[:50]
            ],
            'modules': [asdict(m) for m in self.modules],
        }
        
        return report
    
    def save_report(self, output_path: str) -> None:
        """Save the report to a JSON file."""
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Report saved to: {output_path}")
        
        # Also generate a summary markdown
        summary_path = output_path.replace('.json', '_SUMMARY.md')
        self._generate_summary_markdown(report, summary_path)
    
    def _generate_summary_markdown(self, report: Dict, output_path: str) -> None:
        """Generate a markdown summary of the report."""
        summary = report['summary']
        domains = report['domain_statistics']
        
        md = f"""# Module Inventory Summary

**Generated**: {report['generated_at']}

## Overview

| Metric | Value |
|--------|-------|
| Total Modules | {summary['total_modules']:,} |
| Total Lines of Code | {summary['total_lines']:,} |
| Total Classes | {summary['total_classes']:,} |
| Total Functions | {summary['total_functions']:,} |
| Async Modules | {summary['async_modules']:,} |
| Modules with Parse Errors | {summary['modules_with_errors']:,} |

## Domain Distribution

| Domain | Module Count | Lines of Code |
|--------|-------------|---------------|
"""
        for domain, stats in sorted(domains.items()):
            md += f"| {domain} | {stats['count']:,} | {stats['total_lines']:,} |\n"
        
        md += f"""
## Hub Modules (Most Dependencies)

These modules are imported by many other modules and should be integrated first:

| Module | Dependent Count |
|--------|-----------------|
"""
        for module, count in report['hub_modules']:
            md += f"| `{module}` | {count} |\n"
        
        if report['error_modules']:
            md += f"""
## Modules with Parse Errors

These modules have syntax errors and need fixing:

| Module | Error |
|--------|-------|
"""
            for err in report['error_modules'][:20]:
                error_short = err['error'][:80] + '...' if len(err['error']) > 80 else err['error']
                md += f"| `{err['path']}` | {error_short} |\n"
        
        md += """
## Integration Priority

Based on dependency analysis, integrate modules in this order:

1. **Foundation** (no dependencies): Core utilities, constants, types
2. **Infrastructure**: Logging, configuration, health checks
3. **Data Layer**: Database, caching, data pipelines
4. **Domain Services**: Risk, execution, signals
5. **Business Logic**: Strategies, ML models, analysis
6. **Integration**: APIs, brokers, external adapters
7. **Orchestration**: Coordinators, schedulers
8. **Interface**: CLI, dashboard, notifications

## Next Steps

1. Review modules with parse errors and fix syntax issues
2. Start integration with hub modules (most dependencies)
3. Follow domain-by-domain integration approach
4. Verify all imports resolve correctly
5. Add missing tests and documentation
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"Summary saved to: {output_path}")


def main():
    """Main entry point."""
    # Determine base path
    script_dir = Path(__file__).parent
    base_path = script_dir.parent  # trading bot directory
    
    print(f"Scanning modules in: {base_path}")
    print("=" * 60)
    
    analyzer = ModuleAnalyzer(str(base_path))
    analyzer.scan_directory()
    
    # Save report
    output_dir = base_path / 'docs' / 'integration'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = output_dir / f'module_inventory_{timestamp}.json'
    
    analyzer.save_report(str(output_path))
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    report = analyzer.generate_report()
    summary = report['summary']
    print(f"Total Modules: {summary['total_modules']:,}")
    print(f"Total Lines: {summary['total_lines']:,}")
    print(f"Total Classes: {summary['total_classes']:,}")
    print(f"Total Functions: {summary['total_functions']:,}")
    print(f"Modules with Errors: {summary['modules_with_errors']}")
    print("\nDomain Distribution:")
    for domain, stats in sorted(report['domain_statistics'].items()):
        print(f"  {domain}: {stats['count']} modules, {stats['total_lines']:,} lines")


if __name__ == '__main__':
    main()
