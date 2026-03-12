"""
Auto Dependency Installer
=========================

Automatically detects and installs missing Python dependencies.
Scans the codebase for imports and ensures all required packages are installed.

Author: AlphaAlgo Trading System
Version: 1.0.0
"""

import subprocess
import sys
import importlib
import importlib.util
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# KNOWN PACKAGE MAPPINGS
# ============================================================================

# Maps import names to pip package names (when they differ)
IMPORT_TO_PACKAGE = {
    # Core ML/AI
    'sklearn': 'scikit-learn',
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'yaml': 'PyYAML',
    'bs4': 'beautifulsoup4',
    'dateutil': 'python-dateutil',
    
    # Trading specific
    'MetaTrader5': 'MetaTrader5',
    'mt5': 'MetaTrader5',
    'ta': 'ta',
    'talib': 'TA-Lib',
    
    # Web/API
    'flask': 'Flask',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'aiohttp': 'aiohttp',
    'httpx': 'httpx',
    'websockets': 'websockets',
    'websocket': 'websocket-client',
    
    # Data
    'pandas': 'pandas',
    'numpy': 'numpy',
    'scipy': 'scipy',
    'statsmodels': 'statsmodels',
    
    # ML/DL
    'tensorflow': 'tensorflow',
    'tf': 'tensorflow',
    'torch': 'torch',
    'transformers': 'transformers',
    'xgboost': 'xgboost',
    'lightgbm': 'lightgbm',
    'catboost': 'catboost',
    
    # Visualization
    'plotly': 'plotly',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'dash': 'dash',
    
    # Database
    'sqlalchemy': 'SQLAlchemy',
    'redis': 'redis',
    'pymongo': 'pymongo',
    'psycopg2': 'psycopg2-binary',
    
    # Async
    'asyncio': None,  # Built-in
    'aiofiles': 'aiofiles',
    
    # Crypto/Security
    'cryptography': 'cryptography',
    'jwt': 'PyJWT',
    'bcrypt': 'bcrypt',
    
    # Messaging
    'pika': 'pika',
    'zmq': 'pyzmq',
    'kafka': 'kafka-python',
    
    # NLP
    'nltk': 'nltk',
    'spacy': 'spacy',
    'textblob': 'textblob',
    
    # Quantum
    'qiskit': 'qiskit',
    'qiskit_aer': 'qiskit-aer',
    'qiskit_algorithms': 'qiskit-algorithms',
    
    # Blockchain
    'web3': 'web3',
    'eth_account': 'eth-account',
    
    # Utilities
    'tqdm': 'tqdm',
    'loguru': 'loguru',
    'pydantic': 'pydantic',
    'dotenv': 'python-dotenv',
    'requests': 'requests',
    'urllib3': 'urllib3',
    'colorama': 'colorama',
    'rich': 'rich',
    
    # Testing
    'pytest': 'pytest',
    'hypothesis': 'hypothesis',
    
    # Profiling
    'memory_profiler': 'memory-profiler',
    'line_profiler': 'line-profiler',
    'psutil': 'psutil',
    
    # FAISS
    'faiss': 'faiss-cpu',
    
    # Other
    'schedule': 'schedule',
    'apscheduler': 'APScheduler',
    'arrow': 'arrow',
    'pendulum': 'pendulum',
    'pytz': 'pytz',
    'ntplib': 'ntplib',
}

# Packages that are optional (don't fail if can't install)
OPTIONAL_PACKAGES = {
    'MetaTrader5', 'TA-Lib', 'ibapi', 'qiskit', 'qiskit-aer', 
    'qiskit-algorithms', 'web3', 'd3rlpy', 'lime', 'shap',
    'onnxruntime', 'tensorflow-gpu', 'torch-cuda'
}

# Built-in modules (don't try to install)
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
}


class AutoDependencyInstaller:
    """
    Automatically detects and installs missing Python dependencies.
    """
    
    def __init__(self, base_path: str = None, verbose: bool = True):
        if base_path is None:
            base_path = str(Path(__file__).parent)
        
        self.base_path = Path(base_path)
        self.verbose = verbose
        self.missing_packages: Set[str] = set()
        self.installed_packages: Set[str] = set()
        self.failed_packages: Set[str] = set()
        self.optional_skipped: Set[str] = set()
        
    def log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.verbose:
            if level == "error":
                print(f"[ERROR] {message}")
            elif level == "warning":
                print(f"[WARN] {message}")
            elif level == "success":
                print(f"[OK] {message}")
            else:
                print(f"[INFO] {message}")
    
    def is_package_installed(self, package_name: str) -> bool:
        """Check if a package is installed"""
        try:
            # Handle package names with extras like 'package[extra]'
            base_package = package_name.split('[')[0]
            importlib.import_module(base_package)
            return True
        except ImportError:
            # Try the pip package name mapping
            import_name = None
            for imp, pkg in IMPORT_TO_PACKAGE.items():
                if pkg == package_name:
                    import_name = imp
                    break
            
            if import_name:
                try:
                    importlib.import_module(import_name)
                    return True
                except ImportError:
                    pass
            
            return False
    
    def scan_imports(self) -> Set[str]:
        """Scan all Python files for import statements"""
        imports = set()
        
        # Common words that are NOT packages (false positives)
        FALSE_POSITIVES = {
            'good', 'the', 'various', 'all', 'any', 'some', 'this', 'that',
            'from', 'import', 'as', 'with', 'for', 'in', 'is', 'not', 'and',
            'or', 'if', 'else', 'elif', 'try', 'except', 'finally', 'raise',
            'return', 'yield', 'class', 'def', 'lambda', 'pass', 'break',
            'continue', 'global', 'nonlocal', 'assert', 'del', 'while',
            'true', 'false', 'none', 'self', 'cls', 'super', 'object',
            'type', 'list', 'dict', 'set', 'tuple', 'str', 'int', 'float',
            'bool', 'bytes', 'range', 'print', 'input', 'open', 'file',
            'name', 'main', 'init', 'new', 'call', 'get', 'set', 'add',
            'remove', 'update', 'clear', 'copy', 'keys', 'values', 'items',
            'example', 'test', 'demo', 'sample', 'data', 'result', 'output',
            'error', 'exception', 'warning', 'info', 'debug', 'critical',
        }
        
        for py_file in self.base_path.rglob("*.py"):
            # Skip certain directories
            if any(skip in str(py_file) for skip in ['__pycache__', 'backup', '.git']):
                continue
            try:
            
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Find import statements - more precise patterns
                # Pattern 1: import xxx (at start of line, not in string/comment)
                pattern1 = r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)'
                # Pattern 2: from xxx import (at start of line)
                pattern2 = r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
                
                for match in re.finditer(pattern1, content, re.MULTILINE):
                    imp = match.group(1)
                    if imp.lower() not in FALSE_POSITIVES and len(imp) > 1:
                        imports.add(imp)
                
                for match in re.finditer(pattern2, content, re.MULTILINE):
                    module = match.group(1)
                    if not module.startswith('trading_bot') and module.lower() not in FALSE_POSITIVES and len(module) > 1:
                        imports.add(module)
                        
            except Exception as e:
                self.log(f"Error scanning {py_file}: {e}", "warning")
        
        return imports
    
    def get_missing_packages(self) -> List[str]:
        """Get list of missing packages"""
        self.log("Scanning codebase for imports...")
        imports = self.scan_imports()
        
        self.log(f"Found {len(imports)} unique imports")
        
        missing = []
        
        for imp in imports:
            # Skip built-in modules
            if imp in BUILTIN_MODULES:
                continue
            
            # Skip trading_bot internal imports
            if imp.startswith('trading_bot'):
                continue
            
            # Get the pip package name
            package_name = IMPORT_TO_PACKAGE.get(imp, imp)
            
            # Skip if None (built-in)
            if package_name is None:
                continue
            
            # Check if installed
            if not self.is_package_installed(imp):
                missing.append(package_name)
        
        self.missing_packages = set(missing)
        return list(set(missing))
    
    def install_package(self, package_name: str) -> bool:
        """Install a single package using pip"""
        try:
            self.log(f"Installing {package_name}...")
            
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name, '-q'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.installed_packages.add(package_name)
                self.log(f"Successfully installed {package_name}", "success")
                return True
            else:
                if package_name in OPTIONAL_PACKAGES:
                    self.optional_skipped.add(package_name)
                    self.log(f"Optional package {package_name} skipped", "warning")
                else:
                    self.failed_packages.add(package_name)
                    self.log(f"Failed to install {package_name}: {result.stderr[:200]}", "error")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"Timeout installing {package_name}", "error")
            self.failed_packages.add(package_name)
            return False
        except Exception as e:
            self.log(f"Error installing {package_name}: {e}", "error")
            self.failed_packages.add(package_name)
            return False
    
    def install_all_missing(self) -> Tuple[int, int, int]:
        """
        Install all missing packages
        
        Returns:
            Tuple of (installed_count, failed_count, skipped_count)
        """
        missing = self.get_missing_packages()
        
        if not missing:
            self.log("All dependencies are already installed!", "success")
            return (0, 0, 0)
        
        self.log(f"\nFound {len(missing)} missing packages:")
        for pkg in sorted(missing):
            optional = " (optional)" if pkg in OPTIONAL_PACKAGES else ""
            self.log(f"  - {pkg}{optional}")
        
        self.log("\nInstalling missing packages...")
        
        for package in missing:
            self.install_package(package)
        
        installed = len(self.installed_packages)
        failed = len(self.failed_packages)
        skipped = len(self.optional_skipped)
        
        self.log(f"\n{'='*50}")
        self.log(f"Installation complete:")
        self.log(f"  Installed: {installed}")
        self.log(f"  Failed: {failed}")
        self.log(f"  Optional skipped: {skipped}")
        self.log(f"{'='*50}")
        
        return (installed, failed, skipped)
    
    def install_core_requirements(self) -> bool:
        """Install core requirements from requirements.txt if exists"""
        req_file = self.base_path.parent / 'requirements.txt'
        
        if not req_file.exists():
            self.log("No requirements.txt found", "warning")
            return False
        
        self.log(f"Installing from {req_file}...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(req_file), '-q'],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                self.log("Core requirements installed successfully", "success")
                return True
            else:
                self.log(f"Some requirements failed: {result.stderr[:500]}", "warning")
                return False
                
        except Exception as e:
            self.log(f"Error installing requirements: {e}", "error")
            return False
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip to latest version"""
        self.log("Upgrading pip...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', '-q'],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def full_install(self) -> bool:
        """
        Perform full dependency installation:
        1. Upgrade pip
        2. Install from requirements.txt
        3. Scan and install any missing packages
        """
        self.log("="*60)
        self.log("AUTO DEPENDENCY INSTALLER")
        self.log("="*60)
        
        # Step 1: Upgrade pip
        self.upgrade_pip()
        
        # Step 2: Install core requirements
        self.install_core_requirements()
        
        # Step 3: Scan and install missing
        installed, failed, skipped = self.install_all_missing()
        
        # Return True if no critical failures
        return failed == 0


def install_dependencies(base_path: str = None, verbose: bool = True) -> bool:
    """
    Convenience function to install all dependencies
    
    Args:
        base_path: Path to trading_bot directory
        verbose: Print progress messages
        
    Returns:
        True if all critical dependencies installed successfully
    """
    installer = AutoDependencyInstaller(base_path, verbose)
    return installer.full_install()


def check_dependencies(base_path: str = None) -> List[str]:
    """
    Check for missing dependencies without installing
    
    Returns:
        List of missing package names
    """
    installer = AutoDependencyInstaller(base_path, verbose=False)
    return installer.get_missing_packages()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto Dependency Installer")
    parser.add_argument('--check', action='store_true', 
                        help='Only check for missing dependencies')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet mode')
    parser.add_argument('--path', type=str, default=None,
                        help='Path to trading_bot directory')
    
    args = parser.parse_args()
    
    if args.check:
        missing = check_dependencies(args.path)
        if missing:
            print(f"Missing packages ({len(missing)}):")
            for pkg in sorted(missing):
                print(f"  - {pkg}")
            sys.exit(1)
        else:
            print("All dependencies installed!")
            sys.exit(0)
    else:
        success = install_dependencies(args.path, not args.quiet)
        sys.exit(0 if success else 1)
