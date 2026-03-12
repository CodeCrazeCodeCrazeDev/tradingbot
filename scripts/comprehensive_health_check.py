#!/usr/bin/env python3
"""
Comprehensive System Health Check for AlphaAlgo Trading Bot
Performs 25+ validation and analysis tasks
"""

import sys
import os
import ast
import importlib
import importlib.util
import traceback
import time
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Set

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class HealthCheckReport:
    """Aggregates all health check results"""
    
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.results = {}
        self.critical_issues = []
        self.warnings = []
        self.passed = []
        self.metrics = {}
        
    def add_result(self, category: str, status: str, details: Any):
        self.results[category] = {"status": status, "details": details}
        if status == "CRITICAL":
            self.critical_issues.append(f"{category}: {details}")
        elif status == "WARNING":
            self.warnings.append(f"{category}: {details}")
        else:
            self.passed.append(category)
            
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "summary": {
                "critical": len(self.critical_issues),
                "warnings": len(self.warnings),
                "passed": len(self.passed)
            },
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "passed": self.passed,
            "results": self.results,
            "metrics": self.metrics
        }


class ImportAnalyzer:
    """Analyzes imports for broken dependencies and circular imports"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.import_graph = defaultdict(set)
        self.broken_imports = []
        self.circular_deps = []
        self.files_analyzed = 0
        
    def analyze_file(self, filepath: Path) -> List[str]:
        """Extract imports from a Python file"""
        imports = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except SyntaxError as e:
            self.broken_imports.append((str(filepath), f"SyntaxError: {e}"))
        except Exception as e:
            self.broken_imports.append((str(filepath), f"Error: {e}"))
        return imports
    
    def build_import_graph(self):
        """Build import graph for all Python files"""
        trading_bot_dir = self.project_root / "trading_bot"
        if not trading_bot_dir.exists():
            return
            
        for py_file in trading_bot_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            self.files_analyzed += 1
            relative_path = py_file.relative_to(self.project_root)
            module_name = str(relative_path).replace(os.sep, ".").replace(".py", "")
            imports = self.analyze_file(py_file)
            for imp in imports:
                if imp.startswith("trading_bot"):
                    self.import_graph[module_name].add(imp)
                    
    def find_circular_deps(self):
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.import_graph.get(node, []):
                if neighbor not in visited:
                    result = dfs(neighbor)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
                    
            path.pop()
            rec_stack.remove(node)
            return None
            
        for node in self.import_graph:
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    self.circular_deps.append(cycle)
                    
    def test_imports(self) -> List[Tuple[str, str]]:
        """Test if critical modules can be imported"""
        critical_modules = [
            "trading_bot",
            "trading_bot.core",
            "trading_bot.risk",
            "trading_bot.execution",
            "trading_bot.signals",
            "trading_bot.ml",
            "trading_bot.brokers",
        ]
        
        failed_imports = []
        for module in critical_modules:
            try:
                importlib.import_module(module)
            except Exception as e:
                failed_imports.append((module, str(e)[:200]))
        return failed_imports


class MockImplementationFinder:
    """Finds mock/placeholder implementations"""
    
    MOCK_PATTERNS = [
        r'pass\s*$',
        r'raise\s+NotImplementedError',
        r'TODO',
        r'FIXME',
        r'PLACEHOLDER',
        r'return\s+None\s*$',
        r'return\s+\[\]\s*$',
        r'return\s+\{\}\s*$',
        r'\.\.\.', 
        r'#\s*stub',
        r'#\s*mock',
        r'MockBroker',
        r'FakeBroker',
        r'SimulatedBroker',
    ]
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.mock_implementations = []
        
    def scan(self) -> List[Dict]:
        """Scan for mock implementations"""
        trading_bot_dir = self.project_root / "trading_bot"
        if not trading_bot_dir.exists():
            return []
            
        for py_file in trading_bot_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            self._scan_file(py_file)
        return self.mock_implementations
        
    def _scan_file(self, filepath: Path):
        """Scan a single file for mock patterns"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                for pattern in self.MOCK_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.mock_implementations.append({
                            "file": str(filepath.relative_to(self.project_root)),
                            "line": i,
                            "pattern": pattern,
                            "content": line.strip()[:100]
                        })
                        break
        except Exception:
            pass


class TODOScanner:
    """Scans for TODO markers in codebase"""
    
    TODO_PATTERNS = [
        r'#\s*TODO',
        r'#\s*FIXME',
        r'#\s*XXX',
        r'#\s*HACK',
        r'#\s*BUG',
        r'#\s*INCOMPLETE',
    ]
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.todos = []
        
    def scan(self) -> List[Dict]:
        """Scan for TODO markers"""
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            self._scan_file(py_file)
        return self.todos
        
    def _scan_file(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                for pattern in self.TODO_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.todos.append({
                            "file": str(filepath.relative_to(self.project_root)),
                            "line": i,
                            "content": line.strip()[:150]
                        })
                        break
        except Exception:
            pass


class HardcodedValueScanner:
    """Finds hardcoded values that should be configurable"""
    
    HARDCODED_PATTERNS = [
        (r'api_key\s*=\s*["\'][^"\']+["\']', "API Key"),
        (r'password\s*=\s*["\'][^"\']+["\']', "Password"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Secret"),
        (r'localhost:\d+', "Hardcoded localhost port"),
        (r'127\.0\.0\.1:\d+', "Hardcoded IP:port"),
        (r'max_position\s*=\s*\d+', "Hardcoded max position"),
        (r'stop_loss\s*=\s*0\.\d+', "Hardcoded stop loss"),
        (r'take_profit\s*=\s*0\.\d+', "Hardcoded take profit"),
        (r'leverage\s*=\s*\d+', "Hardcoded leverage"),
        (r'risk_percent\s*=\s*0\.\d+', "Hardcoded risk percent"),
    ]
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.hardcoded = []
        
    def scan(self) -> List[Dict]:
        """Scan for hardcoded values"""
        trading_bot_dir = self.project_root / "trading_bot"
        if not trading_bot_dir.exists():
            return []
            
        for py_file in trading_bot_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            self._scan_file(py_file)
        return self.hardcoded
        
    def _scan_file(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            for pattern, desc in self.HARDCODED_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    self.hardcoded.append({
                        "file": str(filepath.relative_to(self.project_root)),
                        "type": desc,
                        "match": match.group()[:50]
                    })
        except Exception:
            pass


class SecretScanner:
    """Scans for exposed secrets and sensitive data"""
    
    SECRET_PATTERNS = [
        (r'["\']sk-[a-zA-Z0-9]{20,}["\']', "OpenAI API Key"),
        (r'["\']ghp_[a-zA-Z0-9]{36}["\']', "GitHub Token"),
        (r'["\']xox[baprs]-[a-zA-Z0-9-]+["\']', "Slack Token"),
        (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
        (r'["\'][a-zA-Z0-9]{32,}["\']', "Potential API Key"),
        (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded Password"),
        (r'private_key\s*=\s*["\']', "Private Key"),
        (r'-----BEGIN.*PRIVATE KEY-----', "Private Key Block"),
    ]
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.secrets = []
        
    def scan_code(self) -> List[Dict]:
        """Scan code for secrets"""
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            self._scan_file(py_file)
        return self.secrets
        
    def scan_logs(self) -> List[Dict]:
        """Scan log files for secrets"""
        log_patterns = ["*.log", "*.txt"]
        log_secrets = []
        for pattern in log_patterns:
            for log_file in self.project_root.rglob(pattern):
                if ".venv" in str(log_file):
                    continue
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    for secret_pattern, desc in self.SECRET_PATTERNS:
                        if re.search(secret_pattern, content):
                            log_secrets.append({
                                "file": str(log_file.relative_to(self.project_root)),
                                "type": desc
                            })
                            break
                except Exception:
                    pass
        return log_secrets
        
    def _scan_file(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            for pattern, desc in self.SECRET_PATTERNS:
                if re.search(pattern, content):
                    self.secrets.append({
                        "file": str(filepath.relative_to(self.project_root)),
                        "type": desc
                    })
        except Exception:
            pass


class BrokerConnectionValidator:
    """Validates broker connections and execution pipeline"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def check_broker_adapters(self) -> Dict:
        """Check which broker adapters exist and their status"""
        broker_dir = self.project_root / "trading_bot" / "brokers"
        adapters = {}
        
        if broker_dir.exists():
            for py_file in broker_dir.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                adapters[py_file.stem] = self._analyze_adapter(py_file)
        
        # Also check broker/ directory
        broker_dir2 = self.project_root / "broker"
        if broker_dir2.exists():
            for py_file in broker_dir2.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                adapters[py_file.stem] = self._analyze_adapter(py_file)
                
        return adapters
        
    def _analyze_adapter(self, filepath: Path) -> Dict:
        """Analyze a broker adapter file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            has_connect = "def connect" in content or "async def connect" in content
            has_execute = "def execute" in content or "def place_order" in content
            has_positions = "def get_positions" in content or "def positions" in content
            is_mock = "Mock" in content or "Fake" in content or "Simulated" in content
            
            return {
                "has_connect": has_connect,
                "has_execute": has_execute,
                "has_positions": has_positions,
                "is_mock": is_mock,
                "status": "MOCK" if is_mock else ("COMPLETE" if all([has_connect, has_execute, has_positions]) else "INCOMPLETE")
            }
        except Exception as e:
            return {"error": str(e)}


class SafetyGuardrailValidator:
    """Validates safety guardrails and kill switches"""
    
    REQUIRED_GUARDRAILS = [
        "max_risk_per_trade",
        "max_daily_loss",
        "max_drawdown",
        "max_position_size",
        "max_leverage",
        "emergency_stop",
        "kill_switch",
        "circuit_breaker",
    ]
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def validate(self) -> Dict:
        """Validate all safety guardrails"""
        results = {guardrail: False for guardrail in self.REQUIRED_GUARDRAILS}
        
        # Search for guardrail implementations
        trading_bot_dir = self.project_root / "trading_bot"
        if not trading_bot_dir.exists():
            return results
            
        for py_file in trading_bot_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                for guardrail in self.REQUIRED_GUARDRAILS:
                    if guardrail.replace("_", "") in content.replace("_", ""):
                        results[guardrail] = True
            except Exception:
                pass
                
        return results


class TestCoverageAnalyzer:
    """Analyzes test coverage"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def analyze(self) -> Dict:
        """Analyze test coverage"""
        tests_dir = self.project_root / "tests"
        trading_bot_dir = self.project_root / "trading_bot"
        
        test_files = list(tests_dir.rglob("test_*.py")) if tests_dir.exists() else []
        source_files = list(trading_bot_dir.rglob("*.py")) if trading_bot_dir.exists() else []
        
        # Filter out __pycache__
        test_files = [f for f in test_files if "__pycache__" not in str(f)]
        source_files = [f for f in source_files if "__pycache__" not in str(f)]
        
        # Find modules without tests
        tested_modules = set()
        for test_file in test_files:
            # Extract module name from test file name
            module_name = test_file.stem.replace("test_", "")
            tested_modules.add(module_name)
            
        untested_modules = []
        for source_file in source_files:
            module_name = source_file.stem
            if module_name not in tested_modules and not module_name.startswith("__"):
                untested_modules.append(str(source_file.relative_to(self.project_root)))
                
        return {
            "total_test_files": len(test_files),
            "total_source_files": len(source_files),
            "coverage_estimate": f"{len(tested_modules) / max(len(source_files), 1) * 100:.1f}%",
            "untested_modules_sample": untested_modules[:20]
        }


class InactiveFeatureFinder:
    """Finds implemented but inactive features"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def find(self) -> List[Dict]:
        """Find inactive features"""
        inactive = []
        
        # Check config files for disabled features
        config_dir = self.project_root / "config"
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                inactive.extend(self._check_config(config_file))
                
        # Check for feature flags
        trading_bot_dir = self.project_root / "trading_bot"
        if trading_bot_dir.exists():
            for py_file in trading_bot_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                inactive.extend(self._check_feature_flags(py_file))
                
        return inactive[:50]  # Limit results
        
    def _check_config(self, filepath: Path) -> List[Dict]:
        """Check config file for disabled features"""
        inactive = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # Look for enabled: false patterns
            matches = re.finditer(r'(\w+):\s*\n\s*enabled:\s*false', content, re.IGNORECASE)
            for match in matches:
                inactive.append({
                    "feature": match.group(1),
                    "file": str(filepath.relative_to(self.project_root)),
                    "how_to_enable": f"Set 'enabled: true' in {filepath.name}"
                })
        except Exception:
            pass
        return inactive
        
    def _check_feature_flags(self, filepath: Path) -> List[Dict]:
        """Check for feature flags in code"""
        inactive = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # Look for ENABLE_* = False patterns
            matches = re.finditer(r'(ENABLE_\w+)\s*=\s*False', content)
            for match in matches:
                inactive.append({
                    "feature": match.group(1),
                    "file": str(filepath.relative_to(self.project_root)),
                    "how_to_enable": f"Set {match.group(1)} = True"
                })
        except Exception:
            pass
        return inactive


def run_health_check():
    """Run comprehensive health check"""
    print("=" * 80)
    print("COMPREHENSIVE SYSTEM HEALTH CHECK")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)
    
    report = HealthCheckReport()
    project_root = PROJECT_ROOT
    
    # 1. Import Analysis
    print("\n[1/12] Analyzing imports and circular dependencies...")
    import_analyzer = ImportAnalyzer(project_root)
    import_analyzer.build_import_graph()
    import_analyzer.find_circular_deps()
    failed_imports = import_analyzer.test_imports()
    
    report.add_result(
        "Import Analysis",
        "CRITICAL" if failed_imports or import_analyzer.circular_deps else "PASS",
        {
            "files_analyzed": import_analyzer.files_analyzed,
            "broken_imports": import_analyzer.broken_imports[:20],
            "circular_dependencies": import_analyzer.circular_deps[:10],
            "failed_critical_imports": failed_imports
        }
    )
    print(f"   Files analyzed: {import_analyzer.files_analyzed}")
    print(f"   Broken imports: {len(import_analyzer.broken_imports)}")
    print(f"   Circular deps: {len(import_analyzer.circular_deps)}")
    
    # 2. Mock Implementation Scan
    print("\n[2/12] Scanning for mock/placeholder implementations...")
    mock_finder = MockImplementationFinder(project_root)
    mocks = mock_finder.scan()
    
    critical_mocks = [m for m in mocks if any(x in m['file'] for x in ['broker', 'execution', 'risk'])]
    report.add_result(
        "Mock Implementations",
        "WARNING" if critical_mocks else "PASS",
        {
            "total_mocks": len(mocks),
            "critical_mocks": critical_mocks[:20],
            "sample": mocks[:10]
        }
    )
    print(f"   Total mock patterns: {len(mocks)}")
    print(f"   Critical mocks: {len(critical_mocks)}")
    
    # 3. Broker Connection Validation
    print("\n[3/12] Validating broker connections...")
    broker_validator = BrokerConnectionValidator(project_root)
    broker_status = broker_validator.check_broker_adapters()
    
    mock_brokers = [k for k, v in broker_status.items() if v.get('is_mock')]
    report.add_result(
        "Broker Connections",
        "WARNING" if mock_brokers else "PASS",
        broker_status
    )
    print(f"   Broker adapters found: {len(broker_status)}")
    print(f"   Mock brokers: {mock_brokers}")
    
    # 4. Safety Guardrails
    print("\n[4/12] Validating safety guardrails...")
    safety_validator = SafetyGuardrailValidator(project_root)
    guardrails = safety_validator.validate()
    
    missing_guardrails = [k for k, v in guardrails.items() if not v]
    report.add_result(
        "Safety Guardrails",
        "CRITICAL" if missing_guardrails else "PASS",
        {
            "guardrails": guardrails,
            "missing": missing_guardrails
        }
    )
    print(f"   Guardrails found: {sum(guardrails.values())}/{len(guardrails)}")
    print(f"   Missing: {missing_guardrails}")
    
    # 5. TODO Markers
    print("\n[5/12] Scanning for TODO markers...")
    todo_scanner = TODOScanner(project_root)
    todos = todo_scanner.scan()
    
    report.add_result(
        "TODO Markers",
        "WARNING" if len(todos) > 50 else "PASS",
        {
            "total": len(todos),
            "sample": todos[:30]
        }
    )
    print(f"   TODO markers found: {len(todos)}")
    
    # 6. Hardcoded Values
    print("\n[6/12] Scanning for hardcoded values...")
    hardcoded_scanner = HardcodedValueScanner(project_root)
    hardcoded = hardcoded_scanner.scan()
    
    report.add_result(
        "Hardcoded Values",
        "WARNING" if hardcoded else "PASS",
        {
            "total": len(hardcoded),
            "sample": hardcoded[:20]
        }
    )
    print(f"   Hardcoded values found: {len(hardcoded)}")
    
    # 7. Secret Scan
    print("\n[7/12] Scanning for exposed secrets...")
    secret_scanner = SecretScanner(project_root)
    code_secrets = secret_scanner.scan_code()
    log_secrets = secret_scanner.scan_logs()
    
    report.add_result(
        "Secret Exposure",
        "CRITICAL" if code_secrets or log_secrets else "PASS",
        {
            "code_secrets": code_secrets[:10],
            "log_secrets": log_secrets[:10]
        }
    )
    print(f"   Secrets in code: {len(code_secrets)}")
    print(f"   Secrets in logs: {len(log_secrets)}")
    
    # 8. Test Coverage
    print("\n[8/12] Analyzing test coverage...")
    coverage_analyzer = TestCoverageAnalyzer(project_root)
    coverage = coverage_analyzer.analyze()
    
    report.add_result(
        "Test Coverage",
        "WARNING" if float(coverage['coverage_estimate'].replace('%', '')) < 50 else "PASS",
        coverage
    )
    print(f"   Test files: {coverage['total_test_files']}")
    print(f"   Source files: {coverage['total_source_files']}")
    print(f"   Coverage estimate: {coverage['coverage_estimate']}")
    
    # 9. Inactive Features
    print("\n[9/12] Finding inactive features...")
    inactive_finder = InactiveFeatureFinder(project_root)
    inactive = inactive_finder.find()
    
    report.add_result(
        "Inactive Features",
        "INFO",
        inactive
    )
    print(f"   Inactive features found: {len(inactive)}")
    
    # 10. Check .env file
    print("\n[10/12] Checking environment configuration...")
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    env_status = {
        "env_exists": env_file.exists(),
        "env_example_exists": env_example.exists(),
    }
    
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
            env_status["has_api_keys"] = "API_KEY" in env_content or "api_key" in env_content.lower()
            env_status["has_broker_config"] = "BROKER" in env_content or "MT5" in env_content
        except Exception:
            pass
            
    report.add_result(
        "Environment Config",
        "PASS" if env_status.get("env_exists") else "WARNING",
        env_status
    )
    print(f"   .env exists: {env_status['env_exists']}")
    
    # 11. Check unified architecture
    print("\n[11/12] Checking unified architecture layers...")
    unified_dir = project_root / "trading_bot" / "unified_architecture"
    layers_status = {}
    
    if unified_dir.exists():
        for i in range(1, 7):
            layer_file = unified_dir / f"layer{i}_*.py"
            layer_files = list(unified_dir.glob(f"layer{i}_*.py"))
            layers_status[f"layer_{i}"] = len(layer_files) > 0
    else:
        layers_status["unified_architecture"] = "NOT_FOUND"
        
    report.add_result(
        "Unified Architecture",
        "PASS" if all(layers_status.values()) else "WARNING",
        layers_status
    )
    print(f"   Layers found: {layers_status}")
    
    # 12. Check critical directories
    print("\n[12/12] Checking critical directories...")
    critical_dirs = [
        "trading_bot/core",
        "trading_bot/risk",
        "trading_bot/execution",
        "trading_bot/signals",
        "trading_bot/ml",
        "trading_bot/brokers",
        "trading_bot/database",
    ]
    
    dir_status = {}
    for dir_path in critical_dirs:
        full_path = project_root / dir_path
        dir_status[dir_path] = {
            "exists": full_path.exists(),
            "files": len(list(full_path.glob("*.py"))) if full_path.exists() else 0
        }
        
    report.add_result(
        "Critical Directories",
        "PASS" if all(d["exists"] for d in dir_status.values()) else "WARNING",
        dir_status
    )
    
    # Generate summary
    print("\n" + "=" * 80)
    print("HEALTH CHECK SUMMARY")
    print("=" * 80)
    
    summary = report.to_dict()
    print(f"\n✅ PASSED: {summary['summary']['passed']}")
    print(f"⚠️  WARNINGS: {summary['summary']['warnings']}")
    print(f"❌ CRITICAL: {summary['summary']['critical']}")
    
    if summary['critical_issues']:
        print("\n🚨 CRITICAL ISSUES:")
        for issue in summary['critical_issues'][:10]:
            print(f"   - {issue[:100]}")
            
    if summary['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in summary['warnings'][:10]:
            print(f"   - {warning[:100]}")
    
    # Save report
    report_path = project_root / "diagnostics" / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n📄 Full report saved to: {report_path}")
    
    return summary


if __name__ == "__main__":
    run_health_check()
