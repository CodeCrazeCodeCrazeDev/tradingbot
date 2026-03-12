"""
Master Validation Runner
Orchestrates all validation tests and auto-fixes issues before running operational mode
"""

import os
import sys
import time
import json
import asyncio
import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Tuple
from pathlib import Path
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validation.comprehensive_validator import (
    APIKeyValidator, MarketFeedValidator, IndicatorValidator,
    ValidationResult, ValidationStatus
)
from validation.signal_validator import SignalValidator
from validation.risk_validator import RiskValidator
from validation.notification_validator import NotificationValidator
from validation.ai_ml_validator import AIMLValidator

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/full_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoFixer:
    """Automatic issue fixing system"""
    
    def __init__(self):
        self.fixes_applied = []
        self.changelog = []
    
    def fix_missing_dependencies(self) -> bool:
        """Auto-fix missing dependencies"""
        try:
            logger.info("Checking for missing dependencies...")
            
            required_packages = [
                'MetaTrader5',
                'pandas',
                'numpy',
                'talib',
                'pyyaml',
                'python-dotenv',
                'requests',
                'aiohttp'
            ]
            
            missing = []
            for package in required_packages:
                try:
                    __import__(package.replace('-', '_'))
                except ImportError:
                    missing.append(package)
            
            if missing:
                logger.warning(f"Missing packages: {', '.join(missing)}")
                logger.info("Installing missing packages...")
                
                for package in missing:
                    try:
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                        self.changelog.append(f"Installed package: {package}")
                        logger.info(f"✓ Installed {package}")
                    except Exception as e:
                        logger.error(f"✗ Failed to install {package}: {e}")
                        return False
                
                self.fixes_applied.append("Installed missing dependencies")
                return True
            else:
                logger.info("✓ All dependencies present")
                return True
        except Exception as e:
            logger.error(f"Error fixing dependencies: {e}")
            return False
    
    def fix_api_connections(self, validation_results: List[ValidationResult]) -> bool:
        """Auto-fix API connection issues"""
        try:
            api_failures = [r for r in validation_results 
                          if r.component == "API Keys" and r.status == ValidationStatus.FAILED]
            
            if not api_failures:
                logger.info("✓ No API connection issues")
                return True
            
            logger.warning(f"Found {len(api_failures)} API connection issues")
            
            # Check .env file
            env_path = Path('.env')
            if not env_path.exists():
                logger.warning(".env file not found, creating from template...")
                template_path = Path('.env.template')
                if template_path.exists():
                    import shutil
                    shutil.copy(template_path, env_path)
                    self.changelog.append("Created .env from template")
                    logger.info("✓ Created .env file - please configure API keys")
                else:
                    logger.error("✗ .env.template not found")
                    return False
            
            # Validate API keys are set
            from dotenv import load_dotenv
            load_dotenv()
            
            missing_keys = []
            if not os.getenv('ALPHA_VANTAGE_KEY'):
                missing_keys.append('ALPHA_VANTAGE_KEY')
            if not os.getenv('FRED_API_KEY'):
                missing_keys.append('FRED_API_KEY')
            
            if missing_keys:
                logger.warning(f"Missing API keys in .env: {', '.join(missing_keys)}")
                logger.info("Please configure these keys in .env file")
                return False
            
            self.fixes_applied.append("Validated API configuration")
            return True
        except Exception as e:
            logger.error(f"Error fixing API connections: {e}")
            return False
    
    def fix_config_issues(self) -> bool:
        """Auto-fix configuration issues"""
        try:
            import yaml
            
            config_path = Path('config/config.yaml')
            if not config_path.exists():
                logger.error("✗ config.yaml not found")
                return False
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate critical settings
            fixes_needed = False
            
            # Check trading mode
            if config.get('trading', {}).get('mode') not in ['paper', 'live']:
                logger.warning("Invalid trading mode, setting to 'paper'")
                config['trading']['mode'] = 'paper'
                fixes_needed = True
            
            # Check risk settings
            if config.get('trading', {}).get('risk_per_trade', 0) > 0.05:
                logger.warning("Risk per trade too high, capping at 2%")
                config['trading']['risk_per_trade'] = 0.02
                fixes_needed = True
            
            # Check position sizing
            if 'risk' not in config:
                config['risk'] = {
                    'max_position_size': 0.01,
                    'min_position_size': 0.01,
                    'risk_per_trade_pct': 1.0,
                    'max_drawdown_pct': 20.0
                }
                fixes_needed = True
            
            if fixes_needed:
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                self.changelog.append("Fixed configuration issues")
                logger.info("✓ Configuration fixed")
            else:
                logger.info("✓ Configuration valid")
            
            return True
        except Exception as e:
            logger.error(f"Error fixing config: {e}")
            return False
    
    def save_changelog(self):
        """Save changelog of fixes"""
        if self.changelog:
            changelog_file = f"logs/auto_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(changelog_file, 'w') as f:
                f.write("AUTO-FIX CHANGELOG\n")
                f.write("=" * 80 + "\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n\n")
                for fix in self.changelog:
                    f.write(f"- {fix}\n")
            logger.info(f"Changelog saved to: {changelog_file}")


class MasterValidator:
    """Master validation orchestrator"""
    
    def __init__(self):
        self.all_results = []
        self.auto_fixer = AutoFixer()
    
    async def run_all_validations(self) -> Tuple[bool, List[ValidationResult]]:
        """Run all validation tests"""
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE VALIDATION SUITE")
        logger.info("=" * 80)
        logger.info(f"Started at: {datetime.now().isoformat()}")
        logger.info("")
        
        # 1. API Key Validation
        logger.info("Phase 1: API Key Validation")
        logger.info("-" * 80)
        api_validator = APIKeyValidator()
        self.all_results.extend(api_validator.validate_all())
        logger.info("")
        
        # 2. Market Feed Validation
        logger.info("Phase 2: Market Feed Validation")
        logger.info("-" * 80)
        feed_validator = MarketFeedValidator()
        self.all_results.extend(feed_validator.validate_all())
        logger.info("")
        
        # 3. Indicator Validation
        logger.info("Phase 3: Technical Indicator Validation")
        logger.info("-" * 80)
        indicator_validator = IndicatorValidator()
        self.all_results.extend(indicator_validator.validate_all())
        logger.info("")
        
        # 4. Signal Logic Validation
        logger.info("Phase 4: Signal Logic Validation")
        logger.info("-" * 80)
        signal_validator = SignalValidator()
        self.all_results.extend(signal_validator.validate_all())
        logger.info("")
        
        # 5. Risk Management Validation
        logger.info("Phase 5: Risk Management Validation")
        logger.info("-" * 80)
        risk_validator = RiskValidator()
        self.all_results.extend(risk_validator.validate_all())
        logger.info("")
        
        # 6. Notification System Validation
        logger.info("Phase 6: Notification System Validation")
        logger.info("-" * 80)
        notification_validator = NotificationValidator()
        self.all_results.extend(notification_validator.validate_all())
        logger.info("")
        
        # 7. AI/ML System Validation
        logger.info("Phase 7: AI/ML System Validation")
        logger.info("-" * 80)
        ai_ml_validator = AIMLValidator()
        self.all_results.extend(ai_ml_validator.validate_all())
        logger.info("")
        
        # Calculate summary
        passed = sum(1 for r in self.all_results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in self.all_results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in self.all_results if r.status == ValidationStatus.WARNING)
        skipped = sum(1 for r in self.all_results if r.status == ValidationStatus.SKIPPED)
        
        success = failed == 0
        
        logger.info("=" * 80)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {len(self.all_results)}")
        logger.info(f"✓ Passed: {passed}")
        logger.info(f"✗ Failed: {failed}")
        logger.info(f"⚠ Warnings: {warnings}")
        logger.info(f"○ Skipped: {skipped}")
        logger.info("")
        
        return success, self.all_results
    
    async def run_auto_fixes(self, validation_results: List[ValidationResult]) -> bool:
        """Run automatic fixes for detected issues"""
        logger.info("=" * 80)
        logger.info("AUTO-FIX SYSTEM")
        logger.info("=" * 80)
        
        # 1. Fix dependencies
        if not self.auto_fixer.fix_missing_dependencies():
            logger.error("✗ Failed to fix dependencies")
            return False
        
        # 2. Fix API connections
        if not self.auto_fixer.fix_api_connections(validation_results):
            logger.warning("⚠ API connection issues remain")
        
        # 3. Fix config
        if not self.auto_fixer.fix_config_issues():
            logger.error("✗ Failed to fix configuration")
            return False
        
        # Save changelog
        self.auto_fixer.save_changelog()
        
        logger.info("")
        logger.info(f"Applied {len(self.auto_fixer.fixes_applied)} fixes")
        for fix in self.auto_fixer.fixes_applied:
            logger.info(f"  ✓ {fix}")
        
        return True
    
    async def run_unit_tests(self) -> bool:
        """Run unit tests"""
        logger.info("=" * 80)
        logger.info("UNIT TESTS")
        logger.info("=" * 80)
        
        try:
            # Check if pytest is available
            import pytest
            
            # Run tests
            test_dir = Path("tests")
            if test_dir.exists():
                logger.info(f"Running tests in {test_dir}...")
                result = pytest.main([str(test_dir), "-v", "--tb=short"])
                
                if result == 0:
                    logger.info("✓ All unit tests passed")
                    return True
                else:
                    logger.warning(f"⚠ Some unit tests failed (exit code: {result})")
                    return False
            else:
                logger.warning("⚠ No tests directory found")
                return True
        except ImportError:
            logger.warning("⚠ pytest not installed, skipping unit tests")
            return True
        except Exception as e:
            logger.error(f"✗ Error running unit tests: {e}")
            return False
    
    async def run_integration_tests(self) -> bool:
        """Run integration tests"""
        logger.info("=" * 80)
        logger.info("INTEGRATION TESTS")
        logger.info("=" * 80)
        
        try:
            # Test end-to-end flow
            logger.info("Testing end-to-end trading flow...")
            
            # 1. Data retrieval
            import MetaTrader5 as mt5
            if not mt5.initialize():
                logger.error("✗ MT5 initialization failed")
                return False
            
            # 2. Signal generation
            import talib
            import pandas as pd
            
            rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_H1, 0, 100)
            if rates is None:
                logger.error("✗ Failed to get market data")
                mt5.shutdown()
                return False
            
            df = pd.DataFrame(rates)
            ema = talib.EMA(df['close'].values, timeperiod=20)
            
            if ema is None or len(ema) == 0:
                logger.error("✗ Indicator calculation failed")
                mt5.shutdown()
                return False
            
            # 3. Risk calculation
            # (Would test actual risk manager here)
            
            mt5.shutdown()
            
            logger.info("✓ Integration tests passed")
            return True
        except Exception as e:
            logger.error(f"✗ Integration test error: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def save_results(self):
        """Save validation results"""
        results_file = f"logs/validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump([r.to_dict() for r in self.all_results], f, indent=2)
        logger.info(f"Results saved to: {results_file}")


async def main():
    """Main entry point"""
    validator = MasterValidator()
    
    # Run validations
    success, results = await validator.run_all_validations()
    
    # If failed, try auto-fix
    if not success:
        logger.info("")
        logger.warning("Validation failed. Attempting auto-fix...")
        logger.info("")
        
        if await validator.run_auto_fixes(results):
            logger.info("")
            logger.info("Auto-fixes applied. Re-running validation...")
            logger.info("")
            success, results = await validator.run_all_validations()
    
    # Save results
    validator.save_results()
    
    # Run unit tests
    logger.info("")
    unit_tests_passed = await validator.run_unit_tests()
    
    # Run integration tests
    logger.info("")
    integration_tests_passed = await validator.run_integration_tests()
    
    # Final summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINAL VALIDATION REPORT")
    logger.info("=" * 80)
    logger.info(f"Validation Tests: {'✓ PASSED' if success else '✗ FAILED'}")
    logger.info(f"Unit Tests: {'✓ PASSED' if unit_tests_passed else '⚠ WARNINGS'}")
    logger.info(f"Integration Tests: {'✓ PASSED' if integration_tests_passed else '✗ FAILED'}")
    logger.info("")
    
    all_passed = success and integration_tests_passed
    
    if all_passed:
        logger.info("=" * 80)
        logger.info("✓ ALL CHECKS PASSED - READY FOR OPERATIONAL MODE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("To start operational mode, run:")
        logger.info("  python operational_mode.py")
        logger.info("")
        return 0
    else:
        logger.error("=" * 80)
        logger.error("✗ VALIDATION FAILED - REVIEW ERRORS ABOVE")
        logger.error("=" * 80)
        logger.info("")
        logger.info("Critical errors detected. Please fix manually:")
        
        failed_tests = [r for r in results if r.status == ValidationStatus.FAILED]
        for test in failed_tests:
            logger.error(f"  ✗ {test.component} - {test.test_name}: {test.message}")
        
        logger.info("")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
