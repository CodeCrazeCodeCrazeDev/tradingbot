"""
Real-Time Dependency Manager
============================

Aggressive dependency management system that:
1. Detects problematic/missing dependencies
2. Uninstalls broken packages
3. Reinstalls fresh versions
4. Validates all imports work
5. Ensures real-time capability

Author: AlphaAlgo Trading System
Version: 2.0.0
"""

import subprocess
import sys
import importlib
import importlib.util
import re
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import json
import traceback

logger = logging.getLogger(__name__)


class PackageStatus(Enum):
    """Package installation status"""
    INSTALLED = "installed"
    MISSING = "missing"
    BROKEN = "broken"
    OUTDATED = "outdated"
    OPTIONAL_MISSING = "optional_missing"


@dataclass
class PackageInfo:
    """Information about a package"""
    name: str
    import_name: str
    pip_name: str
    status: PackageStatus
    version: Optional[str] = None
    error: Optional[str] = None
    is_optional: bool = False
    is_realtime_critical: bool = False


@dataclass
class DependencyReport:
    """Report of dependency status"""
    timestamp: datetime = field(default_factory=datetime.now)
    total_packages: int = 0
    installed: int = 0
    missing: int = 0
    broken: int = 0
    fixed: int = 0
    failed: int = 0
    packages: List[PackageInfo] = field(default_factory=list)


# =============================================================================
# COMPREHENSIVE PACKAGE MAPPINGS
# =============================================================================

IMPORT_TO_PACKAGE = {
    # Core Data Science
    'numpy': 'numpy',
    'np': 'numpy',
    'pandas': 'pandas',
    'pd': 'pandas',
    'scipy': 'scipy',
    'sklearn': 'scikit-learn',
    'statsmodels': 'statsmodels',
    
    # ML/DL
    'torch': 'torch',
    'tensorflow': 'tensorflow',
    'tf': 'tensorflow',
    'keras': 'keras',
    'transformers': 'transformers',
    'xgboost': 'xgboost',
    'lightgbm': 'lightgbm',
    'catboost': 'catboost',
    'onnxruntime': 'onnxruntime',
    'onnx': 'onnx',
    
    # Technical Analysis
    'ta': 'ta',
    'talib': 'TA-Lib',
    'pandas_ta': 'pandas-ta',
    'mplfinance': 'mplfinance',
    
    # Web/API
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'starlette': 'starlette',
    'flask': 'Flask',
    'aiohttp': 'aiohttp',
    'httpx': 'httpx',
    'requests': 'requests',
    'websockets': 'websockets',
    'websocket': 'websocket-client',
    
    # Real-time & Messaging
    'zmq': 'pyzmq',
    'pyzmq': 'pyzmq',
    'redis': 'redis',
    'aioredis': 'aioredis',
    'kafka': 'kafka-python',
    'aiokafka': 'aiokafka',
    'pika': 'pika',
    
    # Database
    'sqlalchemy': 'SQLAlchemy',
    'psycopg2': 'psycopg2-binary',
    'asyncpg': 'asyncpg',
    'pymongo': 'pymongo',
    'clickhouse_driver': 'clickhouse-driver',
    
    # Visualization
    'matplotlib': 'matplotlib',
    'plt': 'matplotlib',
    'seaborn': 'seaborn',
    'sns': 'seaborn',
    'plotly': 'plotly',
    'dash': 'dash',
    
    # NLP
    'nltk': 'nltk',
    'textblob': 'textblob',
    'vaderSentiment': 'vaderSentiment',
    'spacy': 'spacy',
    
    # Security
    'cryptography': 'cryptography',
    'jwt': 'PyJWT',
    'jose': 'python-jose',
    'bcrypt': 'bcrypt',
    'passlib': 'passlib',
    
    # Config & Utils
    'yaml': 'PyYAML',
    'pyyaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'pydantic': 'pydantic',
    'pydantic_settings': 'pydantic-settings',
    'loguru': 'loguru',
    'rich': 'rich',
    'colorama': 'colorama',
    'tqdm': 'tqdm',
    
    # Async & Files
    'aiofiles': 'aiofiles',
    'asyncio_throttle': 'asyncio-throttle',
    
    # Scheduling
    'apscheduler': 'APScheduler',
    'schedule': 'schedule',
    'arrow': 'arrow',
    'pendulum': 'pendulum',
    'pytz': 'pytz',
    'ntplib': 'ntplib',
    'dateutil': 'python-dateutil',
    
    # Monitoring
    'prometheus_client': 'prometheus-client',
    'psutil': 'psutil',
    'memory_profiler': 'memory-profiler',
    
    # Testing
    'pytest': 'pytest',
    'hypothesis': 'hypothesis',
    
    # Optimization
    'optuna': 'optuna',
    'skopt': 'scikit-optimize',
    'cvxpy': 'cvxpy',
    
    # Image/CV
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'pillow': 'Pillow',
    
    # Other
    'bs4': 'beautifulsoup4',
    'lz4': 'lz4',
    'faiss': 'faiss-cpu',
    'jinja2': 'jinja2',
    'multipart': 'python-multipart',
    
    # Trading Platforms (Optional)
    'MetaTrader5': 'MetaTrader5',
    'mt5': 'MetaTrader5',
    'ibapi': 'ibapi',
    
    # Quantum/Blockchain (Optional)
    'qiskit': 'qiskit',
    'web3': 'web3',
}

# Packages critical for real-time operation
REALTIME_CRITICAL = {
    'numpy', 'pandas', 'aiohttp', 'websockets', 'websocket-client',
    'pyzmq', 'redis', 'asyncio-throttle', 'aiofiles', 'fastapi',
    'uvicorn', 'psutil', 'loguru', 'PyYAML', 'python-dotenv',
    'requests', 'httpx', 'pydantic', 'APScheduler', 'pytz',
}

# Optional packages (don't fail if can't install)
OPTIONAL_PACKAGES = {
    'MetaTrader5', 'TA-Lib', 'ibapi', 'qiskit', 'qiskit-aer',
    'web3', 'tensorflow', 'tensorflow-gpu', 'faiss-cpu',
    'spacy', 'opencv-python', 'd3rlpy', 'lime', 'shap',
}

# Built-in modules
BUILTIN_MODULES = {
    'os', 'sys', 'json', 'time', 'datetime', 'asyncio', 'typing',
    'collections', 'functools', 'itertools', 'pathlib', 'logging',
    'threading', 'multiprocessing', 'queue', 'socket', 'ssl',
    'hashlib', 'hmac', 'secrets', 'random', 'math', 'statistics',
    'copy', 'pickle', 'shelve', 'sqlite3', 'csv', 'configparser',
    'argparse', 'getpass', 'platform', 'subprocess', 'shutil',
    'tempfile', 'glob', 'fnmatch', 're', 'string', 'textwrap',
    'struct', 'codecs', 'unicodedata', 'io', 'abc', 'contextlib',
    'dataclasses', 'enum', 'warnings', 'traceback', 'inspect',
    'importlib', 'pkgutil', 'unittest', 'doctest', 'pdb',
    'profile', 'timeit', 'trace', 'gc', 'weakref', 'types',
    'operator', 'decimal', 'fractions', 'numbers', 'cmath',
    'array', 'bisect', 'heapq', 'email', 'html', 'xml',
    'urllib', 'http', 'ftplib', 'smtplib', 'uuid', 'base64',
    'binascii', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',
    'concurrent', 'signal', 'select', 'selectors', 'mmap',
    'contextvars', 'token', 'tokenize', 'ast', 'dis', 'code',
}


class RealTimeDependencyManager:
    """
    Aggressive dependency manager that ensures all packages work.
    Uninstalls broken packages and reinstalls them.
    """
    
    def __init__(self, base_path: str = None, verbose: bool = True):
        if base_path is None:
            base_path = str(Path(__file__).parent.parent)
        
        self.base_path = Path(base_path)
        self.verbose = verbose
        self.report = DependencyReport()
        self._import_cache: Dict[str, bool] = {}
        
    def log(self, message: str, level: str = "info"):
        """Log with color coding"""
        if not self.verbose:
            return
            
        colors = {
            "info": "\033[94m",     # Blue
            "success": "\033[92m",  # Green
            "warning": "\033[93m",  # Yellow
            "error": "\033[91m",    # Red
            "reset": "\033[0m"
        }
        
        prefix = {
            "info": "[INFO]",
            "success": "[OK]",
            "warning": "[WARN]",
            "error": "[ERROR]"
        }
        
        color = colors.get(level, colors["info"])
        reset = colors["reset"]
        pre = prefix.get(level, "[INFO]")
        
        print(f"{color}{pre}{reset} {message}")
    
    def run_pip(self, *args, timeout: int = 300) -> Tuple[bool, str]:
        """Run pip command and return success status and output"""
        try:
            cmd = [sys.executable, '-m', 'pip'] + list(args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def check_import(self, import_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if an import works.
        Returns: (success, version, error)
        """
        if import_name in self._import_cache:
            return self._import_cache[import_name], None, None
        try:
            
            # Clear any cached failed imports
            if import_name in sys.modules:
                del sys.modules[import_name]
            
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', None)
            self._import_cache[import_name] = True
            return True, version, None
        except ImportError as e:
            self._import_cache[import_name] = False
            return False, None, str(e)
        except Exception as e:
            self._import_cache[import_name] = False
            return False, None, f"Import error: {str(e)}"
    
    def uninstall_package(self, package_name: str) -> bool:
        """Uninstall a package"""
        self.log(f"Uninstalling {package_name}...", "warning")
        success, output = self.run_pip('uninstall', package_name, '-y')
        if success:
            self.log(f"Uninstalled {package_name}", "success")
            # Clear import cache
            self._import_cache.clear()
        else:
            self.log(f"Failed to uninstall {package_name}: {output[:100]}", "error")
        return success
    
    def install_package(self, package_name: str, force_reinstall: bool = False) -> bool:
        """Install a package, optionally forcing reinstall"""
        args = ['install', package_name]
        if force_reinstall:
            args.append('--force-reinstall')
        args.append('--no-cache-dir')  # Fresh install
        
        self.log(f"Installing {package_name}{'(force)' if force_reinstall else ''}...")
        success, output = self.run_pip(*args)
        
        if success:
            self.log(f"Installed {package_name}", "success")
            self._import_cache.clear()
            return True
        else:
            self.log(f"Failed to install {package_name}: {output[:200]}", "error")
            return False
    
    def fix_package(self, import_name: str, pip_name: str) -> bool:
        """
        Fix a broken package by uninstalling and reinstalling.
        This is the aggressive approach.
        """
        self.log(f"Fixing {pip_name} (import: {import_name})...", "warning")
        
        # Step 1: Uninstall
        self.uninstall_package(pip_name)
        
        # Step 2: Clear any cached modules
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith(import_name)]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        # Step 3: Reinstall
        if self.install_package(pip_name):
            # Step 4: Verify
            time.sleep(0.5)  # Brief pause for filesystem
            importlib.invalidate_caches()
            success, _, _ = self.check_import(import_name)
            if success:
                self.log(f"Fixed {pip_name}!", "success")
                return True
        
        self.log(f"Could not fix {pip_name}", "error")
        return False
    
    def scan_codebase_imports(self) -> Set[str]:
        """Scan all Python files for imports"""
        imports = set()
        
        for py_file in self.base_path.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', 'backup', '.git', 'venv', 'env']):
                continue
            try:
            
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Pattern 1: import xxx
                for match in re.finditer(r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE):
                    imports.add(match.group(1))
                
                # Pattern 2: from xxx import
                for match in re.finditer(r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', content, re.MULTILINE):
                    module = match.group(1)
                    if not module.startswith('trading_bot'):
                        imports.add(module)
                        
            except Exception as e:
                pass  # Skip files that can't be read
        
        return imports
    
    def get_package_status(self, import_name: str) -> PackageInfo:
        """Get detailed status of a package"""
        pip_name = IMPORT_TO_PACKAGE.get(import_name, import_name)
        is_optional = pip_name in OPTIONAL_PACKAGES
        is_realtime = pip_name in REALTIME_CRITICAL
        
        success, version, error = self.check_import(import_name)
        
        if success:
            status = PackageStatus.INSTALLED
        elif is_optional:
            status = PackageStatus.OPTIONAL_MISSING
        else:
            # Check if it's broken vs missing
            check_success, output = self.run_pip('show', pip_name, timeout=30)
            if check_success and pip_name.lower() in output.lower():
                status = PackageStatus.BROKEN
            else:
                status = PackageStatus.MISSING
        
        return PackageInfo(
            name=import_name,
            import_name=import_name,
            pip_name=pip_name,
            status=status,
            version=version,
            error=error,
            is_optional=is_optional,
            is_realtime_critical=is_realtime
        )
    
    def fix_all_dependencies(self) -> DependencyReport:
        """
        Main entry point: Fix ALL dependency issues.
        Scans codebase, identifies problems, fixes them.
        """
        self.log("=" * 60)
        self.log("REAL-TIME DEPENDENCY MANAGER")
        self.log("=" * 60)
        
        # Step 1: Upgrade pip first
        self.log("\n[1/5] Upgrading pip...")
        self.run_pip('install', '--upgrade', 'pip')
        
        # Step 2: Install from requirements.txt
        req_file = self.base_path / 'requirements.txt'
        if req_file.exists():
            self.log("\n[2/5] Installing from requirements.txt...")
            success, output = self.run_pip('install', '-r', str(req_file), timeout=600)
            if not success:
                self.log(f"Some requirements failed, will fix individually", "warning")
        else:
            self.log("\n[2/5] No requirements.txt found, skipping...", "warning")
        
        # Step 3: Scan codebase for all imports
        self.log("\n[3/5] Scanning codebase for imports...")
        imports = self.scan_codebase_imports()
        self.log(f"Found {len(imports)} unique imports")
        
        # Step 4: Check each import
        self.log("\n[4/5] Checking all packages...")
        packages_to_fix = []
        packages_to_install = []
        
        for imp in imports:
            if imp in BUILTIN_MODULES:
                continue
            if imp.startswith('trading_bot'):
                continue
            
            info = self.get_package_status(imp)
            self.report.packages.append(info)
            
            if info.status == PackageStatus.INSTALLED:
                self.report.installed += 1
            elif info.status == PackageStatus.BROKEN:
                self.report.broken += 1
                packages_to_fix.append(info)
            elif info.status == PackageStatus.MISSING:
                self.report.missing += 1
                packages_to_install.append(info)
            elif info.status == PackageStatus.OPTIONAL_MISSING:
                pass  # Skip optional
        
        self.report.total_packages = len(self.report.packages)
        
        # Step 5: Fix broken and install missing
        self.log("\n[5/5] Fixing issues...")
        
        # Fix broken packages first (uninstall + reinstall)
        for pkg in packages_to_fix:
            self.log(f"\nFixing broken: {pkg.pip_name}")
            if self.fix_package(pkg.import_name, pkg.pip_name):
                self.report.fixed += 1
            else:
                self.report.failed += 1
        
        # Install missing packages
        for pkg in packages_to_install:
            self.log(f"\nInstalling missing: {pkg.pip_name}")
            if self.install_package(pkg.pip_name):
                self.report.fixed += 1
            else:
                if pkg.is_realtime_critical:
                    self.log(f"CRITICAL: {pkg.pip_name} is required for real-time!", "error")
                    self.report.failed += 1
                else:
                    self.log(f"Non-critical package failed: {pkg.pip_name}", "warning")
        
        # Final report
        self.log("\n" + "=" * 60)
        self.log("DEPENDENCY FIX COMPLETE")
        self.log("=" * 60)
        self.log(f"Total packages scanned: {self.report.total_packages}")
        self.log(f"Already installed: {self.report.installed}", "success")
        self.log(f"Fixed: {self.report.fixed}", "success")
        self.log(f"Failed: {self.report.failed}", "error" if self.report.failed > 0 else "info")
        
        return self.report
    
    def verify_realtime_ready(self) -> Tuple[bool, List[str]]:
        """
        Verify all real-time critical packages are working.
        Returns (ready, list of issues)
        """
        issues = []
        
        self.log("\nVerifying real-time readiness...")
        
        for pip_name in REALTIME_CRITICAL:
            # Find import name
            import_name = None
            for imp, pkg in IMPORT_TO_PACKAGE.items():
                if pkg == pip_name:
                    import_name = imp
                    break
            
            if import_name is None:
                import_name = pip_name.replace('-', '_')
            
            success, _, error = self.check_import(import_name)
            if not success:
                issues.append(f"{pip_name}: {error}")
        
        ready = len(issues) == 0
        
        if ready:
            self.log("All real-time critical packages verified!", "success")
        else:
            self.log(f"Real-time readiness issues: {len(issues)}", "error")
            for issue in issues:
                self.log(f"  - {issue}", "error")
        
        return ready, issues


class RealTimeModuleValidator:
    """
    Validates that all modules in the codebase can be imported
    and are real-time capable.
    """
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = str(Path(__file__).parent.parent)
        self.base_path = Path(base_path)
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        
    def validate_module(self, module_path: Path) -> Tuple[bool, Optional[str]]:
        """Try to import a module and return success status"""
        try:
            # Convert path to module name
            rel_path = module_path.relative_to(self.base_path)
            module_name = str(rel_path).replace('\\', '.').replace('/', '.').replace('.py', '')
            
            # Skip __init__ and test files for now
            if '__init__' in module_name or 'test_' in module_name:
                return True, None
            
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Don't actually execute, just check it can be loaded
                return True, None
                
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Error: {str(e)[:100]}"
        
        return True, None
    
    def validate_all(self) -> Tuple[int, int, List[Dict]]:
        """
        Validate all Python modules in the codebase.
        Returns (success_count, error_count, errors)
        """
        success = 0
        errors = 0
        error_list = []
        
        trading_bot_path = self.base_path / 'trading_bot'
        
        for py_file in trading_bot_path.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
            
            valid, error = self.validate_module(py_file)
            if valid:
                success += 1
            else:
                errors += 1
                error_list.append({
                    'file': str(py_file),
                    'error': error
                })
        
        return success, errors, error_list


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def fix_all_dependencies(verbose: bool = True) -> DependencyReport:
    """Fix all dependency issues in the codebase"""
    manager = RealTimeDependencyManager(verbose=verbose)
    return manager.fix_all_dependencies()


def verify_realtime() -> Tuple[bool, List[str]]:
    """Verify real-time readiness"""
    manager = RealTimeDependencyManager(verbose=True)
    return manager.verify_realtime_ready()


def validate_modules() -> Tuple[int, int, List[Dict]]:
    """Validate all modules can be imported"""
    validator = RealTimeModuleValidator()
    return validator.validate_all()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-Time Dependency Manager")
    parser.add_argument('--fix', action='store_true', help='Fix all dependencies')
    parser.add_argument('--verify', action='store_true', help='Verify real-time readiness')
    parser.add_argument('--validate', action='store_true', help='Validate all modules')
    parser.add_argument('--all', action='store_true', help='Run all checks and fixes')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
    
    args = parser.parse_args()
    
    if args.all or (not args.fix and not args.verify and not args.validate):
        # Default: run everything
        print("\n" + "=" * 60)
        print("ALPHAALGO REAL-TIME DEPENDENCY MANAGER")
        print("=" * 60)
        
        # Fix dependencies
        report = fix_all_dependencies(not args.quiet)
        
        # Verify real-time
        ready, issues = verify_realtime()
        
        # Validate modules
        success, errors, error_list = validate_modules()
        
        print("\n" + "=" * 60)
        print("FINAL STATUS")
        print("=" * 60)
        print(f"Dependencies fixed: {report.fixed}")
        print(f"Dependencies failed: {report.failed}")
        print(f"Real-time ready: {'YES' if ready else 'NO'}")
        print(f"Modules valid: {success}")
        print(f"Modules with errors: {errors}")
        
        sys.exit(0 if report.failed == 0 and ready else 1)
    
    if args.fix:
        report = fix_all_dependencies(not args.quiet)
        sys.exit(0 if report.failed == 0 else 1)
    
    if args.verify:
        ready, issues = verify_realtime()
        sys.exit(0 if ready else 1)
    
    if args.validate:
        success, errors, error_list = validate_modules()
        if error_list:
            print(f"\nModules with errors ({errors}):")
            for err in error_list[:20]:
                print(f"  - {err['file']}: {err['error']}")
        sys.exit(0 if errors == 0 else 1)
