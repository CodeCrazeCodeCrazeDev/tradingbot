"""
Elite Trading Bot - System Validation Runner
Standalone script to run comprehensive system validation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
import yaml
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/system_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main validation runner"""
    try:
        # Import validator
        from trading_bot.diagnostics.system_validator import SystemValidator
        
        # Load configuration
        config = {}
        config_files = ['config/config.yaml', 'config/complete_config.yaml']
        
        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                    logger.info(f"Loaded configuration from {config_file}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load {config_file}: {e}")
        
        # Create validator
        validator = SystemValidator(config)
        
        # Run full validation
        report = await validator.run_full_validation()
        
        # Print summary
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print(f"Overall Status: {report.overall_status.value}")
        print(f"Safe to Trade: {'[YES]' if report.safe_to_trade else '[NO]'}")
        print(f"Total Checks: {len(report.validation_results)}")
        print(f"Critical Failures: {len(report.critical_failures)}")
        print(f"Warnings: {len(report.warnings)}")
        print("="*80)
        
        if report.safe_to_trade:
            print("\n[OK] THINKINGBOT READY - ALL SYSTEMS GREEN. SAFE TO TRADE.\n")
            return 0
        else:
            print("\n[FAIL] THINKINGBOT NOT READY - CRITICAL ISSUES DETECTED. DO NOT TRADE.\n")
            
            if report.critical_failures:
                print("CRITICAL FAILURES:")
                for failure in report.critical_failures:
                    print(f"  [X] {failure}")
            
            if report.warnings:
                print("\nWARNINGS:")
                for warning in report.warnings:
                    print(f"  [!] {warning}")
            
            print()
            return 1
    
    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        print(f"\n[FAIL] VALIDATION FAILED: {e}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
