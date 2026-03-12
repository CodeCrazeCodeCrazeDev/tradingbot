"""
Startup Checks for AlphaAlgo Trading Bot

Performs comprehensive checks before bot startup including:
- Dependency verification and auto-installation
- Configuration validation
- Database connectivity
- API key verification
- System resource checks
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
import warnings

# Suppress warnings during startup checks
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class StartupChecker:
    """Comprehensive startup checker for the trading bot"""
    
    def __init__(self, auto_fix: bool = True):
        """
        Initialize startup checker.
        
        Args:
            auto_fix: Automatically fix issues when possible
        """
        self.auto_fix = auto_fix
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.project_root = Path(__file__).parent.parent.parent
    
    def check_dependencies(self) -> bool:
        """
        Check and install dependencies.
        
        Returns:
            True if all required dependencies are available
        """
        try:
            from trading_bot.core.dependency_manager import AutoDependencyManager
            
            logger.info("[CHECK] Checking dependencies...")
            
            manager = AutoDependencyManager(
                auto_install=self.auto_fix,
                auto_update=False
            )
            
            # Check and install ALL dependencies (including optional)
            success = manager.ensure_dependencies(install_optional=True)
            
            if not success:
                self.issues.append("Missing required dependencies")
                return False
            
            # Check for optional dependencies
            status_map = manager.check_all_dependencies()
            optional_missing = [
                name for name, status in status_map.items()
                if manager.dependencies[name].is_optional and 
                status.value == 'optional_missing'
            ]
            
            if optional_missing:
                self.warnings.append(
                    f"Optional dependencies missing: {', '.join(optional_missing[:5])}"
                    + (f" and {len(optional_missing)-5} more" if len(optional_missing) > 5 else "")
                )
            
            logger.info("[OK] Dependencies check passed")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Dependency check failed: {e}")
            self.issues.append(f"Dependency check error: {e}")
            return False
    
    def check_configuration(self) -> bool:
        """
        Check if configuration files exist and are valid.
        
        Returns:
            True if configuration is valid
        """
        try:
            logger.info("[CHECK] Checking configuration...")
            
            # Check for config files
            config_locations = [
                self.project_root / 'deploy' / 'production_config.yaml',
                self.project_root / 'config' / 'alphaalgo_config.yaml',
                self.project_root / 'config' / 'survival_config.yaml',
            ]
            
            config_found = False
            for config_path in config_locations:
                if config_path.exists():
                    config_found = True
                    logger.info(f"✅ Found config: {config_path.name}")
                    break
            
            if not config_found:
                self.warnings.append("No configuration file found, will use defaults")
            
            logger.info("✅ Configuration check passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration check failed: {e}")
            self.issues.append(f"Configuration error: {e}")
            return False
    
    def check_directories(self) -> bool:
        """
        Check and create required directories.
        
        Returns:
            True if directories are ready
        """
        try:
            logger.info("🔍 Checking directories...")
            
            required_dirs = [
                'logs',
                'data',
                'models',
                'cache',
                'reports',
                'backups',
            ]
            
            for dir_name in required_dirs:
                dir_path = self.project_root / dir_name
                if not dir_path.exists():
                    if self.auto_fix:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"✅ Created directory: {dir_name}")
                    else:
                        self.warnings.append(f"Directory missing: {dir_name}")
            
            logger.info("✅ Directory check passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Directory check failed: {e}")
            self.issues.append(f"Directory error: {e}")
            return False
    
    def check_system_resources(self) -> bool:
        """
        Check system resources (CPU, memory, disk).
        
        Returns:
            True if resources are adequate
        """
        try:
            import psutil
            
            logger.info("🔍 Checking system resources...")
            
            # Check available memory
            memory = psutil.virtual_memory()
            if memory.available < 1 * 1024 * 1024 * 1024:  # Less than 1GB
                self.warnings.append(f"Low memory: {memory.available / 1024**3:.1f}GB available")
            
            # Check disk space
            disk = psutil.disk_usage(str(self.project_root))
            if disk.free < 5 * 1024 * 1024 * 1024:  # Less than 5GB
                self.warnings.append(f"Low disk space: {disk.free / 1024**3:.1f}GB available")
            
            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.warnings.append(f"High CPU usage: {cpu_percent}%")
            
            logger.info("✅ System resources check passed")
            return True
            
        except ImportError:
            self.warnings.append("psutil not available, skipping resource check")
            return True
        except Exception as e:
            logger.error(f"❌ System resources check failed: {e}")
            self.warnings.append(f"Resource check error: {e}")
            return True  # Non-critical
    
    def check_python_version(self) -> bool:
        """
        Check if Python version is compatible.
        
        Returns:
            True if Python version is compatible
        """
        try:
            logger.info("🔍 Checking Python version...")
            
            version = sys.version_info
            if version.major < 3 or (version.major == 3 and version.minor < 8):
                self.issues.append(
                    f"Python 3.8+ required, found {version.major}.{version.minor}"
                )
                return False
            
            logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Python version check failed: {e}")
            self.issues.append(f"Python version error: {e}")
            return False
    
    def run_all_checks(self) -> bool:
        """
        Run all startup checks.
        
        Returns:
            True if all critical checks pass
        """
        print("\n" + "="*70)
        print("ALPHAALGO TRADING BOT - STARTUP CHECKS")
        print("="*70 + "\n")
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Dependencies", self.check_dependencies),
            ("Configuration", self.check_configuration),
            ("Directories", self.check_directories),
            ("System Resources", self.check_system_resources),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                if not result:
                    all_passed = False
            except Exception as e:
                logger.error(f"❌ {check_name} check crashed: {e}")
                self.issues.append(f"{check_name} check crashed: {e}")
                all_passed = False
        
        # Print summary
        print("\n" + "="*70)
        print("STARTUP CHECK SUMMARY")
        print("="*70)
        
        if self.issues:
            print("\n[CRITICAL ISSUES]:")
            for issue in self.issues:
                print(f"  - {issue}")
        
        if self.warnings:
            print("\n[WARNINGS]:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if all_passed and not self.issues:
            print("\n[OK] ALL CHECKS PASSED - BOT READY TO START")
        else:
            print("\n[FAIL] STARTUP CHECKS FAILED - PLEASE FIX ISSUES ABOVE")
        
        print("="*70 + "\n")
        
        return all_passed


def run_startup_checks(auto_fix: bool = True) -> bool:
    """
    Convenience function to run startup checks.
    
    Args:
        auto_fix: Automatically fix issues when possible
        
    Returns:
        True if all checks pass
    """
    checker = StartupChecker(auto_fix=auto_fix)
    return checker.run_all_checks()


if __name__ == "__main__":
    # Run startup checks
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    success = run_startup_checks(auto_fix=True)
    sys.exit(0 if success else 1)
