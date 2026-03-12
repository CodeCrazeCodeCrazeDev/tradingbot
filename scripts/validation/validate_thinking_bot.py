"""
Thinking Bot Validation Script

Validates all components of the thinking bot before running
"""

import os
import sys
import importlib
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Validation result"""
    def __init__(self, name, passed, message=""):
        self.name = name
        self.passed = passed
        self.message = message
    
    def __str__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        msg = f" - {self.message}" if self.message else ""
        return f"{status}: {self.name}{msg}"


class ThinkingBotValidator:
    """Validates thinking bot components"""
    
    def __init__(self):
        self.results = []
    
    def validate_all(self):
        """Run all validations"""
        logger.info("=" * 80)
        logger.info("THINKING BOT VALIDATION")
        logger.info("=" * 80)
        logger.info("")
        
        # 1. File structure
        logger.info("1. Validating file structure...")
        self.validate_file_structure()
        
        # 2. Dependencies
        logger.info("\n2. Validating dependencies...")
        self.validate_dependencies()
        
        # 3. Configuration
        logger.info("\n3. Validating configuration...")
        self.validate_configuration()
        
        # 4. Module imports
        logger.info("\n4. Validating module imports...")
        self.validate_imports()
        
        # 5. MT5 connection
        logger.info("\n5. Validating MT5 connection...")
        self.validate_mt5()
        
        # 6. Component initialization
        logger.info("\n6. Validating components...")
        self.validate_components()
        
        # Summary
        self.print_summary()
    
    def validate_file_structure(self):
        """Validate required files exist"""
        required_files = [
            'thinking_bot.py',
            'config/config.yaml',
            'RUN_THINKING_BOT.bat',
            'THINKING_BOT_GUIDE.md'
        ]
        
        for file_path in required_files:
            exists = Path(file_path).exists()
            self.results.append(ValidationResult(
                f"File exists: {file_path}",
                exists,
                "" if exists else "File not found"
            ))
            logger.info(str(self.results[-1]))
        
        # Check directories
        required_dirs = [
            'logs',
            'config',
            'trading_bot',
            'tests'
        ]
        
        for dir_path in required_dirs:
            exists = Path(dir_path).exists()
            self.results.append(ValidationResult(
                f"Directory exists: {dir_path}",
                exists,
                "" if exists else "Directory not found"
            ))
            logger.info(str(self.results[-1]))
    
    def validate_dependencies(self):
        """Validate required Python packages"""
        required_packages = [
            'MetaTrader5',
            'pandas',
            'numpy',
            'yaml',
            'asyncio',
            'dotenv'
        ]
        
        for package in required_packages:
            try:
                if package == 'yaml':
                    importlib.import_module('yaml')
                elif package == 'dotenv':
                    importlib.import_module('dotenv')
                else:
                    importlib.import_module(package.lower())
                
                self.results.append(ValidationResult(
                    f"Package installed: {package}",
                    True
                ))
            except ImportError as e:
                self.results.append(ValidationResult(
                    f"Package installed: {package}",
                    False,
                    f"Import error: {str(e)}"
                ))
            
            logger.info(str(self.results[-1]))
        
        # Optional packages
        optional_packages = ['talib']
        
        for package in optional_packages:
            try:
                importlib.import_module(package.lower())
                self.results.append(ValidationResult(
                    f"Optional package: {package}",
                    True,
                    "Available (recommended)"
                ))
            except ImportError:
                self.results.append(ValidationResult(
                    f"Optional package: {package}",
                    True,
                    "Not available (fallback will be used)"
                ))
            
            logger.info(str(self.results[-1]))
    
    def validate_configuration(self):
        """Validate configuration file"""
        try:
            import yaml
            
            config_path = Path('config/config.yaml')
            if not config_path.exists():
                self.results.append(ValidationResult(
                    "Configuration file",
                    False,
                    "config/config.yaml not found"
                ))
                logger.info(str(self.results[-1]))
                return
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check required sections
            required_sections = ['mt5', 'trading', 'risk']
            
            for section in required_sections:
                exists = section in config
                self.results.append(ValidationResult(
                    f"Config section: {section}",
                    exists,
                    "" if exists else f"Section '{section}' missing"
                ))
                logger.info(str(self.results[-1]))
            
            # Check required fields
            if 'trading' in config:
                required_fields = ['mode', 'risk_per_trade', 'max_positions']
                for field in required_fields:
                    exists = field in config['trading']
                    self.results.append(ValidationResult(
                        f"Config field: trading.{field}",
                        exists,
                        "" if exists else f"Field missing"
                    ))
                    logger.info(str(self.results[-1]))
            
            if 'risk' in config:
                required_fields = ['max_position_size', 'min_position_size']
                for field in required_fields:
                    exists = field in config['risk']
                    self.results.append(ValidationResult(
                        f"Config field: risk.{field}",
                        exists,
                        "" if exists else f"Field missing"
                    ))
                    logger.info(str(self.results[-1]))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Configuration validation",
                False,
                str(e)
            ))
            logger.info(str(self.results[-1]))
    
    def validate_imports(self):
        """Validate module imports"""
        try:
            # Import thinking_bot
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            from thinking_bot import (
                ThinkingBot,
                SignalType,
                SignalStrength,
                MarketAnalysis,
                TradingSignal,
                RiskValidation,
                TradeExecution
            )
            
            self.results.append(ValidationResult(
                "Import thinking_bot module",
                True
            ))
            logger.info(str(self.results[-1]))
            
            # Check classes
            classes = [
                ThinkingBot,
                SignalType,
                SignalStrength,
                MarketAnalysis,
                TradingSignal,
                RiskValidation,
                TradeExecution
            ]
            
            for cls in classes:
                self.results.append(ValidationResult(
                    f"Class available: {cls.__name__}",
                    True
                ))
                logger.info(str(self.results[-1]))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Import thinking_bot module",
                False,
                str(e)
            ))
            logger.info(str(self.results[-1]))
    
    def validate_mt5(self):
        """Validate MT5 connection"""
        try:
            import MetaTrader5 as mt5
            
            # Try to initialize
            if not mt5.initialize():
                error = mt5.last_error()
                self.results.append(ValidationResult(
                    "MT5 initialization",
                    False,
                    f"Failed to initialize: {error}"
                ))
                logger.info(str(self.results[-1]))
                return
            
            self.results.append(ValidationResult(
                "MT5 initialization",
                True
            ))
            logger.info(str(self.results[-1]))
            
            # Check account info
            account_info = mt5.account_info()
            if account_info is None:
                self.results.append(ValidationResult(
                    "MT5 account info",
                    False,
                    "Failed to get account info"
                ))
            else:
                self.results.append(ValidationResult(
                    "MT5 account info",
                    True,
                    f"Account: {account_info.login}, Balance: ${account_info.balance:.2f}"
                ))
            logger.info(str(self.results[-1]))
            
            # Check symbol
            symbol = "EURUSD"
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.results.append(ValidationResult(
                    f"MT5 symbol data: {symbol}",
                    False,
                    "Failed to get tick data"
                ))
            else:
                self.results.append(ValidationResult(
                    f"MT5 symbol data: {symbol}",
                    True,
                    f"Bid: {tick.bid:.5f}, Ask: {tick.ask:.5f}"
                ))
            logger.info(str(self.results[-1]))
            
            # Check historical data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
            if rates is None or len(rates) == 0:
                self.results.append(ValidationResult(
                    "MT5 historical data",
                    False,
                    "Failed to get historical data"
                ))
            else:
                self.results.append(ValidationResult(
                    "MT5 historical data",
                    True,
                    f"Retrieved {len(rates)} bars"
                ))
            logger.info(str(self.results[-1]))
            
            mt5.shutdown()
            
        except Exception as e:
            self.results.append(ValidationResult(
                "MT5 validation",
                False,
                str(e)
            ))
            logger.info(str(self.results[-1]))
    
    def validate_components(self):
        """Validate bot components"""
        try:
            from thinking_bot import ThinkingBot
            
            # Create bot instance
            bot = ThinkingBot(config_path="config/config.yaml")
            
            self.results.append(ValidationResult(
                "ThinkingBot instantiation",
                True
            ))
            logger.info(str(self.results[-1]))
            
            # Check attributes
            required_attrs = [
                'config',
                'running',
                'initialized',
                'cycle_count',
                'metrics'
            ]
            
            for attr in required_attrs:
                exists = hasattr(bot, attr)
                self.results.append(ValidationResult(
                    f"Bot attribute: {attr}",
                    exists,
                    "" if exists else f"Attribute missing"
                ))
                logger.info(str(self.results[-1]))
            
            # Check methods
            required_methods = [
                'initialize',
                'analyze_market',
                'generate_signal',
                'validate_signal',
                'execute_trade',
                'monitor_positions',
                'trading_cycle',
                'run'
            ]
            
            for method in required_methods:
                exists = hasattr(bot, method) and callable(getattr(bot, method))
                self.results.append(ValidationResult(
                    f"Bot method: {method}",
                    exists,
                    "" if exists else f"Method missing"
                ))
                logger.info(str(self.results[-1]))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Component validation",
                False,
                str(e)
            ))
            logger.info(str(self.results[-1]))
    
    def print_summary(self):
        """Print validation summary"""
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        logger.info(f"Total checks: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            logger.info("\nFailed checks:")
            for result in self.results:
                if not result.passed:
                    logger.info(f"  - {result.name}: {result.message}")
        
        logger.info("=" * 80)
        
        if failed == 0:
            logger.info("✓ ALL VALIDATIONS PASSED - Ready to run!")
        else:
            logger.info("✗ SOME VALIDATIONS FAILED - Please fix issues before running")
        
        logger.info("=" * 80)
        
        return failed == 0


def main():
    """Main entry point"""
    validator = ThinkingBotValidator()
    success = validator.validate_all()
    
    if success:
        logger.info("\nYou can now run the bot with:")
        logger.info("  python thinking_bot.py")
        logger.info("  or")
        logger.info("  RUN_THINKING_BOT.bat")
        sys.exit(0)
    else:
        logger.info("\nPlease fix the issues above before running the bot.")
        sys.exit(1)


if __name__ == "__main__":
    main()
