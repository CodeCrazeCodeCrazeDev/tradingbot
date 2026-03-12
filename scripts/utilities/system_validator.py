"""
System Validator - Comprehensive validation of all trading bot components
Validates imports, dependencies, configurations, and system readiness
"""

import sys
import os
import importlib
import logging
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    name: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any] = None


class SystemValidator:
    """
    Comprehensive system validation.
    
    Validates:
    - Python version
    - Core dependencies
    - Module imports
    - Configuration files
    - Directory structure
    - Component availability
    """
    
    def __init__(self):
        """Initialize validator."""
        self.results: List[ValidationResult] = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.skipped = 0
    
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            True if all critical checks pass, False otherwise
        """
        logger.info("="*80)
        logger.info("🔍 SYSTEM VALIDATION STARTING")
        logger.info("="*80)
        
        # 1. Python Environment
        self.validate_python_version()
        
        # 2. Core Dependencies
        self.validate_core_dependencies()
        
        # 3. Optional Dependencies
        self.validate_optional_dependencies()
        
        # 4. Directory Structure
        self.validate_directory_structure()
        
        # 5. Configuration Files
        self.validate_configuration_files()
        
        # 6. Module Imports
        self.validate_module_imports()
        
        # 7. Component Availability
        self.validate_components()
        
        # Generate report
        self.generate_report()
        
        return self.failed == 0
    
    def validate_python_version(self):
        """Validate Python version."""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major == 3 and version.minor >= 10:
            self.add_result(ValidationResult(
                name="Python Version",
                status=ValidationStatus.PASS,
                message=f"Python {version_str} (OK)"
            ))
        else:
            self.add_result(ValidationResult(
                name="Python Version",
                status=ValidationStatus.FAIL,
                message=f"Python {version_str} - Requires Python 3.10+"
            ))
    
    def validate_core_dependencies(self):
        """Validate core dependencies."""
        core_deps = [
            'numpy',
            'pandas',
            'asyncio',
            'logging',
            'datetime',
            'typing',
            'dataclasses',
            'enum',
            'json'
        ]
        
        for dep in core_deps:
            try:
                importlib.import_module(dep)
                self.add_result(ValidationResult(
                    name=f"Core Dependency: {dep}",
                    status=ValidationStatus.PASS,
                    message=f"{dep} available"
                ))
            except ImportError:
                self.add_result(ValidationResult(
                    name=f"Core Dependency: {dep}",
                    status=ValidationStatus.FAIL,
                    message=f"{dep} not found"
                ))
    
    def validate_optional_dependencies(self):
        """Validate optional dependencies."""
        optional_deps = {
            'torch': 'PyTorch (ML/RL)',
            'sklearn': 'scikit-learn (ML)',
            'scipy': 'SciPy (Scientific)',
            'yfinance': 'Yahoo Finance (Data)',
            'MetaTrader5': 'MT5 (Broker)',
            'psutil': 'System Monitoring'
        }
        
        for dep, description in optional_deps.items():
            try:
                importlib.import_module(dep)
                self.add_result(ValidationResult(
                    name=f"Optional: {description}",
                    status=ValidationStatus.PASS,
                    message=f"{dep} available"
                ))
            except ImportError:
                self.add_result(ValidationResult(
                    name=f"Optional: {description}",
                    status=ValidationStatus.WARN,
                    message=f"{dep} not found (optional)"
                ))
    
    def validate_directory_structure(self):
        """Validate directory structure."""
        required_dirs = [
            'logs',
            'knowledge',
            'data',
            'trading_bot',
            'learning'
        ]
        
        for directory in required_dirs:
            if os.path.isdir(directory):
                self.add_result(ValidationResult(
                    name=f"Directory: {directory}",
                    status=ValidationStatus.PASS,
                    message=f"{directory}/ exists"
                ))
            else:
                # Try to create it
                try:
                    os.makedirs(directory, exist_ok=True)
                    self.add_result(ValidationResult(
                        name=f"Directory: {directory}",
                        status=ValidationStatus.WARN,
                        message=f"{directory}/ created"
                    ))
                except Exception as e:
                    self.add_result(ValidationResult(
                        name=f"Directory: {directory}",
                        status=ValidationStatus.FAIL,
                        message=f"Cannot create {directory}/: {e}"
                    ))
    
    def validate_configuration_files(self):
        """Validate configuration files."""
        config_files = [
            '.env',
            'requirements.txt'
        ]
        
        for config_file in config_files:
            if os.path.isfile(config_file):
                self.add_result(ValidationResult(
                    name=f"Config: {config_file}",
                    status=ValidationStatus.PASS,
                    message=f"{config_file} exists"
                ))
            else:
                self.add_result(ValidationResult(
                    name=f"Config: {config_file}",
                    status=ValidationStatus.WARN,
                    message=f"{config_file} not found (optional)"
                ))
    
    def validate_module_imports(self):
        """Validate key module imports."""
        modules_to_test = [
            ('learning.distributional_rl', 'DistributionalQLearning'),
            ('learning.multi_objective_rl', 'MultiObjectiveRL'),
            ('learning.strategy_optimizer', 'StrategyOptimizer'),
            ('learning_bot', 'LearningTradingBot'),
            ('alphaalgo_2_0', 'AlphaAlgo2_0'),
        ]
        
        for module_name, class_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, class_name):
                    self.add_result(ValidationResult(
                        name=f"Module: {module_name}.{class_name}",
                        status=ValidationStatus.PASS,
                        message=f"{class_name} importable"
                    ))
                else:
                    self.add_result(ValidationResult(
                        name=f"Module: {module_name}.{class_name}",
                        status=ValidationStatus.FAIL,
                        message=f"{class_name} not found in {module_name}"
                    ))
            except ImportError as e:
                self.add_result(ValidationResult(
                    name=f"Module: {module_name}",
                    status=ValidationStatus.FAIL,
                    message=f"Import failed: {e}"
                ))
    
    def validate_components(self):
        """Validate trading bot components."""
        components = [
            'trading_bot.elite_system',
            'trading_bot.market_intelligence',
            'trading_bot.orchestrator',
            'trading_bot.opportunity_scanner',
            'trading_bot.advanced_features'
        ]
        
        for component in components:
            try:
                importlib.import_module(component)
                self.add_result(ValidationResult(
                    name=f"Component: {component}",
                    status=ValidationStatus.PASS,
                    message=f"{component} available"
                ))
            except ImportError as e:
                self.add_result(ValidationResult(
                    name=f"Component: {component}",
                    status=ValidationStatus.WARN,
                    message=f"{component} not available: {e}"
                ))
    
    def add_result(self, result: ValidationResult):
        """Add validation result."""
        self.results.append(result)
        
        if result.status == ValidationStatus.PASS:
            self.passed += 1
        elif result.status == ValidationStatus.FAIL:
            self.failed += 1
        elif result.status == ValidationStatus.WARN:
            self.warnings += 1
        else:
            self.skipped += 1
    
    def generate_report(self):
        """Generate validation report."""
        logger.info("\n" + "="*80)
        logger.info("📊 VALIDATION REPORT")
        logger.info("="*80)
        
        # Group by status
        for status in ValidationStatus:
            status_results = [r for r in self.results if r.status == status]
            if status_results:
                icon = {
                    ValidationStatus.PASS: "✅",
                    ValidationStatus.FAIL: "❌",
                    ValidationStatus.WARN: "⚠️",
                    ValidationStatus.SKIP: "⏭️"
                }.get(status, "❓")
                
                logger.info(f"\n{icon} {status.value} ({len(status_results)})")
                for result in status_results:
                    logger.info(f"   {result.name}: {result.message}")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("📈 SUMMARY")
        logger.info("="*80)
        logger.info(f"✅ Passed:   {self.passed}")
        logger.info(f"❌ Failed:   {self.failed}")
        logger.info(f"⚠️ Warnings: {self.warnings}")
        logger.info(f"⏭️ Skipped:  {self.skipped}")
        logger.info(f"📊 Total:    {len(self.results)}")
        
        # Overall status
        if self.failed == 0:
            logger.info("\n✅ SYSTEM VALIDATION PASSED")
            logger.info("🚀 System is ready to run")
        else:
            logger.info("\n❌ SYSTEM VALIDATION FAILED")
            logger.info("⚠️ Please fix critical issues before running")
        
        logger.info("="*80)


def main():
    """Main entry point."""
    validator = SystemValidator()
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
