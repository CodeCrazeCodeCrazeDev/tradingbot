"""
Automatic Dependency Manager for AlphaAlgo Trading Bot

Handles installation, updates, and management of both required and optional dependencies.
Ensures the bot runs perfectly by automatically resolving dependency issues.
"""

import subprocess
import sys
import logging
import importlib
import pkg_resources
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DependencyStatus(Enum):
    """Dependency installation status"""
    INSTALLED = "installed"
    MISSING = "missing"
    OUTDATED = "outdated"
    FAILED = "failed"
    OPTIONAL_MISSING = "optional_missing"


@dataclass
class DependencyInfo:
    """Information about a dependency"""
    name: str
    required_version: Optional[str] = None
    installed_version: Optional[str] = None
    status: DependencyStatus = DependencyStatus.MISSING
    is_optional: bool = False
    import_name: Optional[str] = None  # Name used for import (if different from package name)
    description: str = ""
    install_command: Optional[str] = None


class AutoDependencyManager:
    """
    Automatic dependency manager that can install, update, and verify dependencies.
    
    Features:
    - Auto-install missing required dependencies
    - Auto-install optional dependencies on demand
    - Update outdated packages
    - Verify dependency health
    - Handle import name vs package name differences
    - Retry failed installations
    - Generate dependency reports
    """
    
    def __init__(self, auto_install: bool = True, auto_update: bool = False):
        """
        Initialize the dependency manager.
        
        Args:
            auto_install: Automatically install missing required dependencies
            auto_update: Automatically update outdated dependencies
        """
        self.auto_install = auto_install
        self.auto_update = auto_update
        self.project_root = Path(__file__).parent.parent.parent
        self.dependencies: Dict[str, DependencyInfo] = {}
        self.installation_log: List[Dict] = []
        
        # Define all dependencies
        self._define_dependencies()
    
    def _define_dependencies(self):
        """Define all required and optional dependencies"""
        
        # Core required dependencies
        required_deps = {
            "numpy": DependencyInfo(
                name="numpy",
                required_version=">=1.20.0",
                is_optional=False,
                description="Numerical computing library"
            ),
            "pandas": DependencyInfo(
                name="pandas",
                required_version=">=1.3.0",
                is_optional=False,
                description="Data manipulation and analysis"
            ),
            "pyyaml": DependencyInfo(
                name="pyyaml",
                import_name="yaml",
                required_version=">=5.4.0",
                is_optional=False,
                description="YAML configuration parser"
            ),
            "requests": DependencyInfo(
                name="requests",
                required_version=">=2.26.0",
                is_optional=False,
                description="HTTP library"
            ),
            "aiohttp": DependencyInfo(
                name="aiohttp",
                required_version=">=3.8.0",
                is_optional=False,
                description="Async HTTP client/server"
            ),
            "websockets": DependencyInfo(
                name="websockets",
                required_version=">=10.0",
                is_optional=False,
                description="WebSocket client and server"
            ),
            "scikit-learn": DependencyInfo(
                name="scikit-learn",
                import_name="sklearn",
                required_version=">=1.0.0",
                is_optional=False,
                description="Machine learning library"
            ),
            "scipy": DependencyInfo(
                name="scipy",
                required_version=">=1.7.0",
                is_optional=False,
                description="Scientific computing"
            ),
            "loguru": DependencyInfo(
                name="loguru",
                required_version=">=0.6.0",
                is_optional=False,
                description="Advanced logging"
            ),
            "redis": DependencyInfo(
                name="redis",
                required_version=">=4.0.0",
                is_optional=False,
                description="Redis client for caching"
            ),
            "sqlalchemy": DependencyInfo(
                name="sqlalchemy",
                required_version=">=1.4.0",
                is_optional=False,
                description="SQL toolkit and ORM"
            ),
            "nltk": DependencyInfo(
                name="nltk",
                required_version=">=3.6.0",
                is_optional=False,
                description="Natural language processing"
            ),
            "spacy": DependencyInfo(
                name="spacy",
                required_version=">=3.0.0",
                is_optional=False,
                description="Advanced NLP"
            ),
            "ccxt": DependencyInfo(
                name="ccxt",
                required_version=">=2.0.0",
                is_optional=False,
                description="Cryptocurrency exchange trading"
            ),
        }
        
        # Optional dependencies
        optional_deps = {
            "torch": DependencyInfo(
                name="torch",
                required_version=">=1.10.0",
                is_optional=True,
                description="PyTorch deep learning framework"
            ),
            "torchvision": DependencyInfo(
                name="torchvision",
                required_version=">=0.11.0",
                is_optional=True,
                description="PyTorch vision library"
            ),
            "tensorflow": DependencyInfo(
                name="tensorflow",
                required_version=">=2.8.0",
                is_optional=True,
                description="TensorFlow deep learning"
            ),
            "xgboost": DependencyInfo(
                name="xgboost",
                required_version=">=1.5.0",
                is_optional=True,
                description="Gradient boosting library"
            ),
            "lightgbm": DependencyInfo(
                name="lightgbm",
                required_version=">=3.3.0",
                is_optional=True,
                description="Light gradient boosting"
            ),
            "catboost": DependencyInfo(
                name="catboost",
                required_version=">=1.0.0",
                is_optional=True,
                description="CatBoost gradient boosting"
            ),
            "ta-lib": DependencyInfo(
                name="ta-lib",
                import_name="talib",
                is_optional=True,
                description="Technical analysis library",
                install_command="pip install TA-Lib"
            ),
            "qiskit": DependencyInfo(
                name="qiskit",
                required_version=">=0.30.0",
                is_optional=True,
                description="Quantum computing framework"
            ),
            "web3": DependencyInfo(
                name="web3",
                required_version=">=5.0.0",
                is_optional=True,
                description="Ethereum blockchain interaction"
            ),
            "ibapi": DependencyInfo(
                name="ibapi",
                is_optional=True,
                description="Interactive Brokers API"
            ),
            "d3rlpy": DependencyInfo(
                name="d3rlpy",
                required_version=">=1.0.0",
                is_optional=True,
                description="Offline reinforcement learning"
            ),
            "stable-baselines3": DependencyInfo(
                name="stable-baselines3",
                import_name="stable_baselines3",
                required_version=">=1.5.0",
                is_optional=True,
                description="Reinforcement learning algorithms"
            ),
            "gym": DependencyInfo(
                name="gym",
                required_version=">=0.21.0",
                is_optional=True,
                description="RL environment toolkit"
            ),
            "plotly": DependencyInfo(
                name="plotly",
                required_version=">=5.0.0",
                is_optional=True,
                description="Interactive plotting"
            ),
            "dash": DependencyInfo(
                name="dash",
                required_version=">=2.0.0",
                is_optional=True,
                description="Web dashboard framework"
            ),
            "streamlit": DependencyInfo(
                name="streamlit",
                required_version=">=1.10.0",
                is_optional=True,
                description="Data app framework"
            ),
            "transformers": DependencyInfo(
                name="transformers",
                required_version=">=4.20.0",
                is_optional=True,
                description="Hugging Face transformers"
            ),
            "optuna": DependencyInfo(
                name="optuna",
                required_version=">=2.10.0",
                is_optional=True,
                description="Hyperparameter optimization"
            ),
            "mlflow": DependencyInfo(
                name="mlflow",
                required_version=">=1.20.0",
                is_optional=True,
                description="ML experiment tracking"
            ),
            "prophet": DependencyInfo(
                name="prophet",
                required_version=">=1.0.0",
                is_optional=True,
                description="Time series forecasting"
            ),
        }
        
        self.dependencies.update(required_deps)
        self.dependencies.update(optional_deps)
    
    def check_dependency(self, dep_info: DependencyInfo) -> DependencyStatus:
        """
        Check if a dependency is installed and up to date.
        
        Args:
            dep_info: Dependency information
            
        Returns:
            Current status of the dependency
        """
        import_name = dep_info.import_name or dep_info.name
        
        try:
            # Try to import the module
            module = importlib.import_module(import_name)
            
            try:
                # Get installed version
                installed_version = pkg_resources.get_distribution(dep_info.name).version
                dep_info.installed_version = installed_version
                
                # Check if version meets requirements
                if dep_info.required_version:
                    req = pkg_resources.Requirement.parse(f"{dep_info.name}{dep_info.required_version}")
                    if installed_version not in req:
                        return DependencyStatus.OUTDATED
                
                return DependencyStatus.INSTALLED
                
            except pkg_resources.DistributionNotFound:
                # Module exists but not installed via pip (e.g., built-in)
                return DependencyStatus.INSTALLED
                
        except ImportError:
            if dep_info.is_optional:
                return DependencyStatus.OPTIONAL_MISSING
            return DependencyStatus.MISSING
    
    def install_dependency(self, dep_info: DependencyInfo, upgrade: bool = False) -> bool:
        """
        Install or upgrade a dependency.
        
        Args:
            dep_info: Dependency to install
            upgrade: Whether to upgrade if already installed
            
        Returns:
            True if installation succeeded, False otherwise
        """
        try:
            # Determine install command
            if dep_info.install_command:
                cmd = dep_info.install_command.split()
            else:
                package_spec = dep_info.name
                if dep_info.required_version and not upgrade:
                    package_spec += dep_info.required_version
                
                cmd = [sys.executable, "-m", "pip", "install"]
                if upgrade:
                    cmd.append("--upgrade")
                cmd.append(package_spec)
            
            logger.info(f"Installing {dep_info.name}... Command: {' '.join(cmd)}")
            
            # Run installation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Log result
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "package": dep_info.name,
                "command": " ".join(cmd),
                "success": result.returncode == 0,
                "stdout": result.stdout[-500:] if result.stdout else "",
                "stderr": result.stderr[-500:] if result.stderr else ""
            }
            self.installation_log.append(log_entry)
            
            if result.returncode == 0:
                logger.info(f"[OK] Successfully installed {dep_info.name}")
                dep_info.status = DependencyStatus.INSTALLED
                return True
            else:
                logger.error(f"[ERROR] Failed to install {dep_info.name}: {result.stderr}")
                dep_info.status = DependencyStatus.FAILED
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"[ERROR] Installation of {dep_info.name} timed out")
            dep_info.status = DependencyStatus.FAILED
            return False
        except Exception as e:
            logger.error(f"[ERROR] Error installing {dep_info.name}: {e}")
            dep_info.status = DependencyStatus.FAILED
            return False
    
    def check_all_dependencies(self) -> Dict[str, DependencyStatus]:
        """
        Check status of all dependencies.
        
        Returns:
            Dictionary mapping dependency names to their status
        """
        status_map = {}
        
        for name, dep_info in self.dependencies.items():
            status = self.check_dependency(dep_info)
            dep_info.status = status
            status_map[name] = status
        
        return status_map
    
    def install_missing_required(self) -> Tuple[int, int]:
        """
        Install all missing required dependencies.
        
        Returns:
            Tuple of (successful_installs, failed_installs)
        """
        successful = 0
        failed = 0
        
        for name, dep_info in self.dependencies.items():
            if dep_info.is_optional:
                continue
            
            if dep_info.status == DependencyStatus.MISSING:
                logger.info(f"Installing required dependency: {name}")
                if self.install_dependency(dep_info):
                    successful += 1
                else:
                    failed += 1
        
        return successful, failed
    
    def update_outdated(self) -> Tuple[int, int]:
        """
        Update all outdated dependencies.
        
        Returns:
            Tuple of (successful_updates, failed_updates)
        """
        successful = 0
        failed = 0
        
        for name, dep_info in self.dependencies.items():
            if dep_info.status == DependencyStatus.OUTDATED:
                logger.info(f"Updating outdated dependency: {name}")
                if self.install_dependency(dep_info, upgrade=True):
                    successful += 1
                else:
                    failed += 1
        
        return successful, failed
    
    def install_optional(self, package_names: Optional[List[str]] = None) -> Tuple[int, int]:
        """
        Install optional dependencies.
        
        Args:
            package_names: List of specific packages to install, or None for all
            
        Returns:
            Tuple of (successful_installs, failed_installs)
        """
        successful = 0
        failed = 0
        
        for name, dep_info in self.dependencies.items():
            if not dep_info.is_optional:
                continue
            
            if package_names and name not in package_names:
                continue
            
            if dep_info.status in [DependencyStatus.OPTIONAL_MISSING, DependencyStatus.MISSING]:
                logger.info(f"Installing optional dependency: {name}")
                if self.install_dependency(dep_info):
                    successful += 1
                else:
                    failed += 1
        
        return successful, failed
    
    def ensure_dependencies(self, install_optional: bool = True) -> bool:
        """
        Ensure all required dependencies are installed and working.
        
        Args:
            install_optional: Also install optional dependencies (default: True)
        
        Returns:
            True if all required dependencies are available, False otherwise
        """
        logger.info("[CHECK] Checking dependencies...")
        
        # Check all dependencies
        status_map = self.check_all_dependencies()
        
        # Count by status
        installed = sum(1 for s in status_map.values() if s == DependencyStatus.INSTALLED)
        missing = sum(1 for s in status_map.values() if s == DependencyStatus.MISSING)
        outdated = sum(1 for s in status_map.values() if s == DependencyStatus.OUTDATED)
        optional_missing = sum(1 for s in status_map.values() if s == DependencyStatus.OPTIONAL_MISSING)
        
        logger.info(f"📊 Dependency Status: {installed} installed, {missing} missing, "
                   f"{outdated} outdated, {optional_missing} optional missing")
        
        # Install missing required dependencies
        if missing > 0 and self.auto_install:
            logger.info(f"[INSTALL] Installing {missing} missing required dependencies...")
            success, failed = self.install_missing_required()
            logger.info(f"[OK] Installed {success} dependencies, {failed} failed")
            
            if failed > 0:
                logger.error(f"[ERROR] Failed to install {failed} required dependencies")
                return False
        
        # Install missing optional dependencies
        if optional_missing > 0 and self.auto_install and install_optional:
            logger.info(f"[INSTALL] Installing {optional_missing} missing optional dependencies...")
            success, failed = self.install_optional()
            logger.info(f"[OK] Installed {success} optional dependencies, {failed} failed")
            
            if failed > 0:
                logger.warning(f"[WARN] Failed to install {failed} optional dependencies (non-critical)")
        
        # Update outdated dependencies
        if outdated > 0 and self.auto_update:
            logger.info(f"[UPDATE] Updating {outdated} outdated dependencies...")
            success, failed = self.update_outdated()
            logger.info(f"[OK] Updated {success} dependencies, {failed} failed")
        
        # Check if all required dependencies are now available
        required_missing = [
            name for name, dep in self.dependencies.items()
            if not dep.is_optional and dep.status != DependencyStatus.INSTALLED
        ]
        
        if required_missing:
            logger.error(f"[ERROR] Missing required dependencies: {', '.join(required_missing)}")
            return False
        
        logger.info("[OK] All required dependencies are installed")
        
        # Report on optional dependencies
        if install_optional:
            optional_installed = sum(
                1 for name, dep in self.dependencies.items()
                if dep.is_optional and dep.status == DependencyStatus.INSTALLED
            )
            optional_total = sum(1 for dep in self.dependencies.values() if dep.is_optional)
            logger.info(f"[OK] Optional dependencies: {optional_installed}/{optional_total} installed")
        
        return True
    
    def generate_report(self) -> Dict:
        """
        Generate a comprehensive dependency report.
        
        Returns:
            Dictionary containing dependency status and information
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_dependencies": len(self.dependencies),
            "required": {},
            "optional": {},
            "summary": {
                "installed": 0,
                "missing": 0,
                "outdated": 0,
                "optional_missing": 0,
                "failed": 0
            },
            "installation_log": self.installation_log[-20:]  # Last 20 entries
        }
        
        for name, dep_info in self.dependencies.items():
            dep_dict = {
                "name": dep_info.name,
                "status": dep_info.status.value,
                "installed_version": dep_info.installed_version,
                "required_version": dep_info.required_version,
                "description": dep_info.description
            }
            
            if dep_info.is_optional:
                report["optional"][name] = dep_dict
            else:
                report["required"][name] = dep_dict
            
            # Update summary
            report["summary"][dep_info.status.value] = \
                report["summary"].get(dep_info.status.value, 0) + 1
        
        return report
    
    def save_report(self, filepath: Optional[Path] = None):
        """
        Save dependency report to JSON file.
        
        Args:
            filepath: Path to save report, or None for default location
        """
        if filepath is None:
            filepath = self.project_root / "dependency_report.json"
        
        report = self.generate_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Dependency report saved to: {filepath}")
    
    def print_report(self):
        """Print a human-readable dependency report"""
        report = self.generate_report()
        
        print("\n" + "="*70)
        print("ALPHAALGO DEPENDENCY REPORT")
        print("="*70)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Dependencies: {report['total_dependencies']}")
        print("\nSummary:")
        for status, count in report['summary'].items():
            print(f"  {status}: {count}")
        
        print("\nRequired Dependencies:")
        for name, info in sorted(report['required'].items()):
            status_icon = "[OK]" if info['status'] == 'installed' else "[MISSING]"
            version = info['installed_version'] or 'N/A'
            print(f"  {status_icon} {name:25s} {version:15s} - {info['description']}")
        
        print("\nOptional Dependencies:")
        for name, info in sorted(report['optional'].items()):
            if info['status'] == 'installed':
                status_icon = "[OK]"
            elif info['status'] == 'optional_missing':
                status_icon = "[SKIP]"
            else:
                status_icon = "[FAIL]"
            version = info['installed_version'] or 'N/A'
            print(f"  {status_icon} {name:25s} {version:15s} - {info['description']}")
        
        print("="*70 + "\n")


def ensure_bot_dependencies(auto_install: bool = True, auto_update: bool = False, install_optional: bool = True) -> bool:
    """
    Convenience function to ensure all bot dependencies are installed.
    
    Args:
        auto_install: Automatically install missing dependencies
        auto_update: Automatically update outdated dependencies
        install_optional: Also install optional dependencies (default: True)
        
    Returns:
        True if all required dependencies are available
    """
    manager = AutoDependencyManager(auto_install=auto_install, auto_update=auto_update)
    return manager.ensure_dependencies(install_optional=install_optional)


if __name__ == "__main__":
    # Test the dependency manager
    logging.basicConfig(level=logging.INFO)
    
    manager = AutoDependencyManager(auto_install=True, auto_update=False)
    manager.ensure_dependencies(install_optional=True)  # Install ALL dependencies including optional
    manager.print_report()
    manager.save_report()
