"""
Comprehensive Trading Bot Validation and Operational Deployment System
======================================================================
This script performs complete validation of all trading bot components and
deploys the system in operational mode with continuous monitoring.

Author: AI Trading Systems Engineer
Date: 2025-10-08
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import traceback
import psutil
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/comprehensive_validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Stores validation result for a component."""
    
    def __init__(self, component: str, status: str, message: str, 
                 details: Optional[Dict] = None, error: Optional[Exception] = None):
        self.component = component
        self.status = status  # PASS, FAIL, WARNING, SKIP
        self.message = message
        self.details = details or {}
        self.error = error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'component': self.component,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'error': str(self.error) if self.error else None,
            'timestamp': self.timestamp.isoformat()
        }


class ComprehensiveValidator:
    """Comprehensive validation system for trading bot."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = datetime.now()
        self.config = {}
        self.api_keys = {}
        
    def add_result(self, result: ValidationResult):
        """Add validation result."""
        self.results.append(result)
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌',
            'WARNING': '⚠️',
            'SKIP': '⏭️'
        }
        emoji = status_emoji.get(result.status, '❓')
        logger.info(f"{emoji} {result.component}: {result.message}")
    
    # ========================================================================
    # PHASE 1: Configuration and File Validation
    # ========================================================================
    
    def validate_directory_structure(self) -> ValidationResult:
        """Validate that all required directories exist."""
        try:
            required_dirs = [
                'trading_bot',
                'config',
                'logs',
                'tests',
                'data',
                'models',
                'diagnostics'
            ]
            
            missing_dirs = []
            for dir_name in required_dirs:
                if not os.path.exists(dir_name):
                    missing_dirs.append(dir_name)
            
            if missing_dirs:
                return ValidationResult(
                    'Directory Structure',
                    'WARNING',
                    f'Missing directories: {", ".join(missing_dirs)}',
                    {'missing': missing_dirs}
                )
            
            return ValidationResult(
                'Directory Structure',
                'PASS',
                'All required directories present',
                {'directories': required_dirs}
            )
        except Exception as e:
            return ValidationResult(
                'Directory Structure',
                'FAIL',
                f'Error checking directories: {str(e)}',
                error=e
            )
    
    def validate_config_files(self) -> ValidationResult:
        """Validate configuration files."""
        try:
            import yaml
            
            # Check config.yaml
            config_path = 'config/config.yaml'
            if not os.path.exists(config_path):
                return ValidationResult(
                    'Configuration Files',
                    'FAIL',
                    'config.yaml not found'
                )
            
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Validate required sections
            required_sections = ['mt5', 'trading', 'risk', 'logging']
            missing_sections = [s for s in required_sections if s not in self.config]
            
            if missing_sections:
                return ValidationResult(
                    'Configuration Files',
                    'WARNING',
                    f'Missing config sections: {", ".join(missing_sections)}',
                    {'missing': missing_sections}
                )
            
            return ValidationResult(
                'Configuration Files',
                'PASS',
                'Configuration files valid',
                {
                    'trading_mode': self.config.get('trading', {}).get('mode', 'unknown'),
                    'symbols': self.config.get('mt5', {}).get('symbols', []),
                    'risk_per_trade': self.config.get('trading', {}).get('risk_per_trade', 0)
                }
            )
        except Exception as e:
            return ValidationResult(
                'Configuration Files',
                'FAIL',
                f'Error validating config: {str(e)}',
                error=e
            )
    
    def validate_api_keys(self) -> ValidationResult:
        """Validate API keys configuration."""
        try:
            api_keys_path = 'config/api_keys.json'
            if not os.path.exists(api_keys_path):
                return ValidationResult(
                    'API Keys',
                    'WARNING',
                    'api_keys.json not found - external APIs will not work'
                )
            
            with open(api_keys_path, 'r') as f:
                self.api_keys = json.load(f)
            
            # Check for key APIs
            api_services = ['alpha_vantage', 'fred', 'newsapi']
            configured_apis = []
            missing_apis = []
            
            for service in api_services:
                if service in self.api_keys and self.api_keys[service].get('api_key'):
                    configured_apis.append(service)
                else:
                    missing_apis.append(service)
            
            if not configured_apis:
                return ValidationResult(
                    'API Keys',
                    'WARNING',
                    'No API keys configured',
                    {'missing': missing_apis}
                )
            
            return ValidationResult(
                'API Keys',
                'PASS',
                f'API keys configured for: {", ".join(configured_apis)}',
                {
                    'configured': configured_apis,
                    'missing': missing_apis
                }
            )
        except Exception as e:
            return ValidationResult(
                'API Keys',
                'FAIL',
                f'Error validating API keys: {str(e)}',
                error=e
            )
    
    # ========================================================================
    # PHASE 2: Dependency and Import Validation
    # ========================================================================
    
    def validate_dependencies(self) -> ValidationResult:
        """Validate that all required dependencies are installed."""
        try:
            required_packages = [
                'pandas', 'numpy', 'MetaTrader5', 'loguru', 'pyyaml',
                'scikit-learn', 'scipy', 'matplotlib', 'requests'
            ]
            
            missing_packages = []
            installed_packages = []
            
            for package in required_packages:
                try:
                    __import__(package)
                    installed_packages.append(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                return ValidationResult(
                    'Dependencies',
                    'FAIL',
                    f'Missing packages: {", ".join(missing_packages)}',
                    {
                        'installed': installed_packages,
                        'missing': missing_packages
                    }
                )
            
            return ValidationResult(
                'Dependencies',
                'PASS',
                f'All {len(installed_packages)} required packages installed',
                {'packages': installed_packages}
            )
        except Exception as e:
            return ValidationResult(
                'Dependencies',
                'FAIL',
                f'Error checking dependencies: {str(e)}',
                error=e
            )
    
    def validate_trading_bot_imports(self) -> ValidationResult:
        """Validate that trading bot modules can be imported."""
        try:
            critical_imports = [
                ('trading_bot.data', 'MT5Interface'),
                ('trading_bot.strategy', 'StrategyEngine'),
                ('trading_bot.risk', 'RiskManager'),
                ('trading_bot.execution', 'PaperExecutor'),
                ('trading_bot.analytics', 'PerformanceAnalytics'),
            ]
            
            import_errors = []
            successful_imports = []
            
            for module_name, class_name in critical_imports:
                try:
                    module = __import__(module_name, fromlist=[class_name])
                    getattr(module, class_name)
                    successful_imports.append(f'{module_name}.{class_name}')
                except (ImportError, AttributeError) as e:
                    import_errors.append(f'{module_name}.{class_name}: {str(e)}')
            
            if import_errors:
                return ValidationResult(
                    'Trading Bot Imports',
                    'FAIL',
                    f'Import errors: {len(import_errors)}',
                    {
                        'successful': successful_imports,
                        'errors': import_errors
                    }
                )
            
            return ValidationResult(
                'Trading Bot Imports',
                'PASS',
                f'All {len(successful_imports)} critical imports successful',
                {'imports': successful_imports}
            )
        except Exception as e:
            return ValidationResult(
                'Trading Bot Imports',
                'FAIL',
                f'Error testing imports: {str(e)}',
                error=e
            )
    
    # ========================================================================
    # PHASE 3: Market Data and Connectivity Validation
    # ========================================================================
    
    async def validate_mt5_connection(self) -> ValidationResult:
        """Validate MT5 connection."""
        try:
            from trading_bot.data import MT5Interface
            
            mt5 = MT5Interface()
            
            # Test connection
            if not mt5.initialize():
                return ValidationResult(
                    'MT5 Connection',
                    'FAIL',
                    'Failed to initialize MT5 connection'
                )
            
            # Get account info
            account_info = mt5.account_info()
            if not account_info:
                mt5.shutdown()
                return ValidationResult(
                    'MT5 Connection',
                    'FAIL',
                    'Failed to get account info'
                )
            
            details = {
                'login': account_info.login,
                'server': account_info.server,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'leverage': account_info.leverage
            }
            
            mt5.shutdown()
            
            return ValidationResult(
                'MT5 Connection',
                'PASS',
                f'Connected to MT5 (Account: {account_info.login})',
                details
            )
        except Exception as e:
            return ValidationResult(
                'MT5 Connection',
                'FAIL',
                f'MT5 connection error: {str(e)}',
                error=e
            )
    
    async def validate_market_data(self) -> ValidationResult:
        """Validate market data retrieval."""
        try:
            from trading_bot.data import MT5Interface
            
            mt5 = MT5Interface()
            if not mt5.initialize():
                return ValidationResult(
                    'Market Data',
                    'FAIL',
                    'Cannot initialize MT5'
                )
            
            # Test data retrieval for configured symbols
            symbols = self.config.get('mt5', {}).get('symbols', ['EURUSD'])
            timeframe = 'H1'
            bars = 100
            
            data_results = {}
            for symbol in symbols[:3]:  # Test first 3 symbols
                try:
                    rates = mt5.get_rates(symbol, timeframe, bars)
                    if rates and len(rates) > 0:
                        data_results[symbol] = {
                            'bars': len(rates),
                            'latest_price': rates[-1]['close'],
                            'timestamp': rates[-1]['time']
                        }
                    else:
                        data_results[symbol] = {'error': 'No data returned'}
                except Exception as e:
                    data_results[symbol] = {'error': str(e)}
            
            mt5.shutdown()
            
            successful = sum(1 for r in data_results.values() if 'error' not in r)
            
            if successful == 0:
                return ValidationResult(
                    'Market Data',
                    'FAIL',
                    'Failed to retrieve data for any symbol',
                    {'results': data_results}
                )
            elif successful < len(data_results):
                return ValidationResult(
                    'Market Data',
                    'WARNING',
                    f'Data retrieved for {successful}/{len(data_results)} symbols',
                    {'results': data_results}
                )
            
            return ValidationResult(
                'Market Data',
                'PASS',
                f'Successfully retrieved data for {successful} symbols',
                {'results': data_results}
            )
        except Exception as e:
            return ValidationResult(
                'Market Data',
                'FAIL',
                f'Market data validation error: {str(e)}',
                error=e
            )
    
    async def validate_api_connectivity(self) -> ValidationResult:
        """Validate external API connectivity."""
        try:
            import requests
            
            api_tests = []
            
            # Test Alpha Vantage
            if 'alpha_vantage' in self.api_keys:
                api_key = self.api_keys['alpha_vantage'].get('api_key')
                if api_key:
                    try:
                        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey={api_key}'
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            api_tests.append(('Alpha Vantage', 'PASS'))
                        else:
                            api_tests.append(('Alpha Vantage', f'HTTP {response.status_code}'))
                    except Exception as e:
                        api_tests.append(('Alpha Vantage', f'ERROR: {str(e)}'))
            
            # Test FRED
            if 'fred' in self.api_keys:
                api_key = self.api_keys['fred'].get('api_key')
                if api_key:
                    try:
                        url = f'https://api.stlouisfed.org/fred/series?series_id=GNPCA&api_key={api_key}&file_type=json'
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            api_tests.append(('FRED', 'PASS'))
                        else:
                            api_tests.append(('FRED', f'HTTP {response.status_code}'))
                    except Exception as e:
                        api_tests.append(('FRED', f'ERROR: {str(e)}'))
            
            # Test NewsAPI
            if 'newsapi' in self.api_keys:
                api_key = self.api_keys['newsapi'].get('api_key')
                if api_key:
                    try:
                        url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}'
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            api_tests.append(('NewsAPI', 'PASS'))
                        else:
                            api_tests.append(('NewsAPI', f'HTTP {response.status_code}'))
                    except Exception as e:
                        api_tests.append(('NewsAPI', f'ERROR: {str(e)}'))
            
            if not api_tests:
                return ValidationResult(
                    'API Connectivity',
                    'SKIP',
                    'No API keys configured to test'
                )
            
            passed = sum(1 for _, status in api_tests if status == 'PASS')
            
            if passed == 0:
                return ValidationResult(
                    'API Connectivity',
                    'FAIL',
                    'All API connectivity tests failed',
                    {'tests': api_tests}
                )
            elif passed < len(api_tests):
                return ValidationResult(
                    'API Connectivity',
                    'WARNING',
                    f'{passed}/{len(api_tests)} APIs responding',
                    {'tests': api_tests}
                )
            
            return ValidationResult(
                'API Connectivity',
                'PASS',
                f'All {passed} APIs responding correctly',
                {'tests': api_tests}
            )
        except Exception as e:
            return ValidationResult(
                'API Connectivity',
                'FAIL',
                f'API connectivity test error: {str(e)}',
                error=e
            )
    
    # ========================================================================
    # PHASE 4: Technical Indicators Validation
    # ========================================================================
    
    async def validate_technical_indicators(self) -> ValidationResult:
        """Validate technical indicator calculations."""
        try:
            from trading_bot.data import MT5Interface
            from trading_bot.analysis import TechnicalAnalysis
            
            mt5 = MT5Interface()
            if not mt5.initialize():
                return ValidationResult(
                    'Technical Indicators',
                    'FAIL',
                    'Cannot initialize MT5'
                )
            
            # Get sample data
            symbol = self.config.get('mt5', {}).get('symbols', ['EURUSD'])[0]
            rates = mt5.get_rates(symbol, 'H1', 200)
            mt5.shutdown()
            
            if not rates or len(rates) < 50:
                return ValidationResult(
                    'Technical Indicators',
                    'FAIL',
                    'Insufficient data for indicator calculation'
                )
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            
            # Test indicator calculations
            indicator_tests = {}
            
            try:
                # EMA
                df['ema_20'] = df['close'].ewm(span=20).mean()
                indicator_tests['EMA'] = 'PASS' if not df['ema_20'].isna().all() else 'FAIL'
            except Exception as e:
                indicator_tests['EMA'] = f'ERROR: {str(e)}'
            
            try:
                # RSI
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))
                indicator_tests['RSI'] = 'PASS' if not df['rsi'].isna().all() else 'FAIL'
            except Exception as e:
                indicator_tests['RSI'] = f'ERROR: {str(e)}'
            
            try:
                # Bollinger Bands
                df['bb_middle'] = df['close'].rolling(window=20).mean()
                df['bb_std'] = df['close'].rolling(window=20).std()
                df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
                df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
                indicator_tests['Bollinger Bands'] = 'PASS' if not df['bb_upper'].isna().all() else 'FAIL'
            except Exception as e:
                indicator_tests['Bollinger Bands'] = f'ERROR: {str(e)}'
            
            try:
                # ATR
                df['high_low'] = df['high'] - df['low']
                df['high_close'] = abs(df['high'] - df['close'].shift())
                df['low_close'] = abs(df['low'] - df['close'].shift())
                df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
                df['atr'] = df['tr'].rolling(window=14).mean()
                indicator_tests['ATR'] = 'PASS' if not df['atr'].isna().all() else 'FAIL'
            except Exception as e:
                indicator_tests['ATR'] = f'ERROR: {str(e)}'
            
            passed = sum(1 for status in indicator_tests.values() if status == 'PASS')
            
            if passed == 0:
                return ValidationResult(
                    'Technical Indicators',
                    'FAIL',
                    'All indicator calculations failed',
                    {'tests': indicator_tests}
                )
            elif passed < len(indicator_tests):
                return ValidationResult(
                    'Technical Indicators',
                    'WARNING',
                    f'{passed}/{len(indicator_tests)} indicators working',
                    {'tests': indicator_tests}
                )
            
            return ValidationResult(
                'Technical Indicators',
                'PASS',
                f'All {passed} indicators calculating correctly',
                {'tests': indicator_tests}
            )
        except Exception as e:
            return ValidationResult(
                'Technical Indicators',
                'FAIL',
                f'Indicator validation error: {str(e)}',
                error=e
            )
    
    # ========================================================================
    # PHASE 5: Strategy and Signal Logic Validation
    # ========================================================================
    
    async def validate_signal_generation(self) -> ValidationResult:
        """Validate trading signal generation."""
        try:
            from trading_bot.data import MT5Interface
            from trading_bot.strategy import StrategyEngine
            
            mt5 = MT5Interface()
            if not mt5.initialize():
                return ValidationResult(
                    'Signal Generation',
                    'FAIL',
                    'Cannot initialize MT5'
                )
            
            symbol = self.config.get('mt5', {}).get('symbols', ['EURUSD'])[0]
            strategy = StrategyEngine(mt5, symbol=symbol)
            
            # Get market data
            rates = mt5.get_rates(symbol, 'H1', 200)
            if not rates or len(rates) < 50:
                mt5.shutdown()
                return ValidationResult(
                    'Signal Generation',
                    'FAIL',
                    'Insufficient data for signal generation'
                )
            
            df = pd.DataFrame(rates)
            df.set_index('time', inplace=True)
            
            # Generate signals
            signals = strategy.analyse(df)
            
            mt5.shutdown()
            
            if signals is None:
                return ValidationResult(
                    'Signal Generation',
                    'WARNING',
                    'No signals generated (may be normal)',
                    {'signals': None}
                )
            
            # Validate signal structure
            if isinstance(signals, dict):
                signal_count = 1
                has_direction = 'direction' in signals or 'action' in signals
            elif isinstance(signals, list):
                signal_count = len(signals)
                has_direction = any('direction' in s or 'action' in s for s in signals)
            else:
                return ValidationResult(
                    'Signal Generation',
                    'FAIL',
                    f'Invalid signal format: {type(signals)}'
                )
            
            return ValidationResult(
                'Signal Generation',
                'PASS',
                f'Generated {signal_count} signal(s)',
                {
                    'signal_count': signal_count,
                    'has_direction': has_direction,
                    'signal_type': type(signals).__name__
                }
            )
        except Exception as e:
            return ValidationResult(
                'Signal Generation',
                'FAIL',
                f'Signal generation error: {str(e)}',
                error=e
            )
    
    # ========================================================================
    # PHASE 6: Risk Management Validation
    # ========================================================================
    
    async def validate_risk_management(self) -> ValidationResult:
        """Validate risk management system."""
        try:
            from trading_bot.data import MT5Interface
            from trading_bot.risk import RiskManager
            
            mt5 = MT5Interface()
            if not mt5.initialize():
                return ValidationResult(
                    'Risk Management',
                    'FAIL',
                    'Cannot initialize MT5'
                )
            
            risk_manager = RiskManager(mt5)
            
            # Test position size calculation
            symbol = self.config.get('mt5', {}).get('symbols', ['EURUSD'])[0]
            stop_loss_pips = 20
            
            try:
                position_size = risk_manager.calculate_position_size(
                    symbol=symbol,
                    stop_loss_pips=stop_loss_pips
                )
                
                # Validate position size
                if hasattr(position_size, 'lot'):
                    lot_size = position_size.lot
                else:
                    lot_size = position_size
                
                max_allowed = self.config.get('risk', {}).get('max_position_size', 0.01)
                
                if lot_size > max_allowed:
                    mt5.shutdown()
                    return ValidationResult(
                        'Risk Management',
                        'FAIL',
                        f'Position size {lot_size} exceeds maximum {max_allowed}',
                        {
                            'calculated_size': lot_size,
                            'max_allowed': max_allowed
                        }
                    )
                
                mt5.shutdown()
                
                return ValidationResult(
                    'Risk Management',
                    'PASS',
                    f'Position sizing working correctly (size: {lot_size})',
                    {
                        'position_size': lot_size,
                        'stop_loss_pips': stop_loss_pips,
                        'max_allowed': max_allowed
                    }
                )
            except Exception as e:
                mt5.shutdown()
                return ValidationResult(
                    'Risk Management',
                    'FAIL',
                    f'Position size calculation error: {str(e)}',
                    error=e
                )
        except Exception as e:
            return ValidationResult(
                'Risk Management',
                'FAIL',
                f'Risk management validation error: {str(e)}',
                error=e
            )
    
    # ========================================================================
    # PHASE 7: Execution Engine Validation
    # ========================================================================
    
    async def validate_execution_engine(self) -> ValidationResult:
        """Validate trade execution engine."""
        try:
            from trading_bot.data import MT5Interface
            from trading_bot.risk import RiskManager
            from trading_bot.execution import PaperExecutor
            
            mt5 = MT5Interface()
            if not mt5.initialize():
                return ValidationResult(
                    'Execution Engine',
                    'FAIL',
                    'Cannot initialize MT5'
                )
            
            risk_manager = RiskManager(mt5)
            executor = PaperExecutor(mt5, risk_manager)
            
            # Test paper trade execution (won't send real orders)
            symbol = self.config.get('mt5', {}).get('symbols', ['EURUSD'])[0]
            
            try:
                # This should not fail in paper mode
                result = await executor.execute_trade(
                    symbol=symbol,
                    direction=1,  # Buy
                    size=0.01
                )
                
                mt5.shutdown()
                
                return ValidationResult(
                    'Execution Engine',
                    'PASS',
                    'Paper execution engine working correctly',
                    {
                        'mode': 'paper',
                        'test_symbol': symbol,
                        'test_size': 0.01
                    }
                )
            except Exception as e:
                mt5.shutdown()
                return ValidationResult(
                    'Execution Engine',
                    'FAIL',
                    f'Execution test failed: {str(e)}',
                    error=e
                )
        except Exception as e:
            return ValidationResult(
                'Execution Engine',
                'FAIL',
                f'Execution engine validation error: {str(e)}',
                error=e
            )
    
    # ========================================================================
    # PHASE 8: System Performance and Health
    # ========================================================================
    
    def validate_system_resources(self) -> ValidationResult:
        """Validate system resources."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk
            disk = psutil.disk_usage('.')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Check thresholds
            warnings = []
            if cpu_percent > 80:
                warnings.append(f'High CPU usage: {cpu_percent}%')
            if memory_percent > 90:
                warnings.append(f'High memory usage: {memory_percent}%')
            if disk_percent > 90:
                warnings.append(f'Low disk space: {disk_free_gb:.1f}GB free')
            
            details = {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'memory_percent': memory_percent,
                'memory_available_gb': round(memory_available_gb, 2),
                'disk_percent': disk_percent,
                'disk_free_gb': round(disk_free_gb, 2)
            }
            
            if warnings:
                return ValidationResult(
                    'System Resources',
                    'WARNING',
                    f'Resource warnings: {"; ".join(warnings)}',
                    details
                )
            
            return ValidationResult(
                'System Resources',
                'PASS',
                'System resources adequate',
                details
            )
        except Exception as e:
            return ValidationResult(
                'System Resources',
                'FAIL',
                f'Resource check error: {str(e)}',
                error=e
            )
    
    def validate_log_system(self) -> ValidationResult:
        """Validate logging system."""
        try:
            log_dir = Path('logs')
            if not log_dir.exists():
                log_dir.mkdir(parents=True, exist_ok=True)
            
            # Test log writing
            test_log_file = log_dir / 'validation_test.log'
            with open(test_log_file, 'w') as f:
                f.write(f'Validation test at {datetime.now()}\n')
            
            # Check existing log files
            log_files = list(log_dir.glob('*.log'))
            total_log_size_mb = sum(f.stat().st_size for f in log_files) / (1024**2)
            
            return ValidationResult(
                'Logging System',
                'PASS',
                f'Logging system operational ({len(log_files)} log files)',
                {
                    'log_directory': str(log_dir),
                    'log_file_count': len(log_files),
                    'total_size_mb': round(total_log_size_mb, 2)
                }
            )
        except Exception as e:
            return ValidationResult(
                'Logging System',
                'FAIL',
                f'Logging system error: {str(e)}',
                error=e
            )
    
    # ========================================================================
    # Main Validation Runner
    # ========================================================================
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation phases."""
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE TRADING BOT VALIDATION")
        logger.info("=" * 80)
        logger.info(f"Started at: {self.start_time}")
        logger.info("")
        
        # Phase 1: Configuration
        logger.info("PHASE 1: Configuration and File Validation")
        logger.info("-" * 80)
        self.add_result(self.validate_directory_structure())
        self.add_result(self.validate_config_files())
        self.add_result(self.validate_api_keys())
        logger.info("")
        
        # Phase 2: Dependencies
        logger.info("PHASE 2: Dependency and Import Validation")
        logger.info("-" * 80)
        self.add_result(self.validate_dependencies())
        self.add_result(self.validate_trading_bot_imports())
        logger.info("")
        
        # Phase 3: Connectivity
        logger.info("PHASE 3: Market Data and Connectivity Validation")
        logger.info("-" * 80)
        self.add_result(await self.validate_mt5_connection())
        self.add_result(await self.validate_market_data())
        self.add_result(await self.validate_api_connectivity())
        logger.info("")
        
        # Phase 4: Technical Analysis
        logger.info("PHASE 4: Technical Indicators Validation")
        logger.info("-" * 80)
        self.add_result(await self.validate_technical_indicators())
        logger.info("")
        
        # Phase 5: Strategy
        logger.info("PHASE 5: Strategy and Signal Logic Validation")
        logger.info("-" * 80)
        self.add_result(await self.validate_signal_generation())
        logger.info("")
        
        # Phase 6: Risk Management
        logger.info("PHASE 6: Risk Management Validation")
        logger.info("-" * 80)
        self.add_result(await self.validate_risk_management())
        logger.info("")
        
        # Phase 7: Execution
        logger.info("PHASE 7: Execution Engine Validation")
        logger.info("-" * 80)
        self.add_result(await self.validate_execution_engine())
        logger.info("")
        
        # Phase 8: System Health
        logger.info("PHASE 8: System Performance and Health")
        logger.info("-" * 80)
        self.add_result(self.validate_system_resources())
        self.add_result(self.validate_log_system())
        logger.info("")
        
        # Generate summary
        return self.generate_summary()
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Count results by status
        status_counts = {
            'PASS': sum(1 for r in self.results if r.status == 'PASS'),
            'FAIL': sum(1 for r in self.results if r.status == 'FAIL'),
            'WARNING': sum(1 for r in self.results if r.status == 'WARNING'),
            'SKIP': sum(1 for r in self.results if r.status == 'SKIP')
        }
        
        total_tests = len(self.results)
        pass_rate = (status_counts['PASS'] / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall status
        if status_counts['FAIL'] > 0:
            overall_status = 'FAILED'
            operational_ready = False
        elif status_counts['WARNING'] > 3:
            overall_status = 'WARNING'
            operational_ready = False
        else:
            overall_status = 'PASSED'
            operational_ready = True
        
        summary = {
            'validation_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'total_tests': total_tests,
                'status_counts': status_counts,
                'pass_rate': round(pass_rate, 2),
                'overall_status': overall_status,
                'operational_ready': operational_ready
            },
            'results': [r.to_dict() for r in self.results]
        }
        
        # Print summary
        logger.info("=" * 80)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {status_counts['PASS']}")
        logger.info(f"❌ Failed: {status_counts['FAIL']}")
        logger.info(f"⚠️  Warnings: {status_counts['WARNING']}")
        logger.info(f"⏭️  Skipped: {status_counts['SKIP']}")
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Overall Status: {overall_status}")
        logger.info(f"Operational Ready: {'YES' if operational_ready else 'NO'}")
        logger.info("=" * 80)
        
        return summary


class OperationalMonitor:
    """Continuous operational monitoring system."""
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.running = False
        self.health_checks = []
        
    async def start_monitoring(self):
        """Start continuous monitoring."""
        self.running = True
        logger.info("Starting continuous operational monitoring...")
        logger.info(f"Health check interval: {self.check_interval} seconds")
        
        while self.running:
            try:
                health_check = await self.perform_health_check()
                self.health_checks.append(health_check)
                
                # Keep only last 100 checks
                if len(self.health_checks) > 100:
                    self.health_checks = self.health_checks[-100:]
                
                await asyncio.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform a health check."""
        timestamp = datetime.now()
        
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Check for trading bot process
        bot_process = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if any('main.py' in str(arg) for arg in cmdline):
                        bot_process = proc
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        health_check = {
            'timestamp': timestamp.isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'bot_running': bot_process is not None,
            'bot_pid': bot_process.pid if bot_process else None
        }
        
        # Log health status
        status_emoji = '✅' if health_check['bot_running'] else '❌'
        logger.info(
            f"{status_emoji} Health Check | CPU: {cpu_percent:.1f}% | "
            f"Memory: {memory.percent:.1f}% | Bot: {'Running' if bot_process else 'Stopped'}"
        )
        
        return health_check
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.running = False
        logger.info("Stopping monitoring...")


async def main():
    """Main entry point."""
    try:
        # Run comprehensive validation
        validator = ComprehensiveValidator()
        summary = await validator.run_all_validations()
        
        # Save validation report
        report_path = f'diagnostics/validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        os.makedirs('diagnostics', exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Validation report saved to: {report_path}")
        
        # Check if operational ready
        if summary['validation_summary']['operational_ready']:
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ SYSTEM OPERATIONAL READY")
            logger.info("=" * 80)
            logger.info("The trading bot has passed all critical validations.")
            logger.info("You can now start the bot in operational mode.")
            logger.info("")
            logger.info("To start the bot:")
            logger.info("  python main.py --symbol EURUSD --timeframe H1 --mode paper")
            logger.info("")
            logger.info("To enable continuous monitoring:")
            logger.info("  Run this script with --monitor flag")
            logger.info("=" * 80)
            
            return 0
        else:
            logger.error("")
            logger.error("=" * 80)
            logger.error("❌ SYSTEM NOT OPERATIONAL READY")
            logger.error("=" * 80)
            logger.error("Critical issues detected. Please fix the following:")
            logger.error("")
            
            for result in validator.results:
                if result.status == 'FAIL':
                    logger.error(f"  ❌ {result.component}: {result.message}")
            
            logger.error("")
            logger.error("=" * 80)
            
            return 1
    
    except Exception as e:
        logger.error(f"Fatal error in validation: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    import sys
    
    # Check for monitor flag
    if '--monitor' in sys.argv:
        # Start monitoring mode
        monitor = OperationalMonitor(check_interval=60)
        try:
            asyncio.run(monitor.start_monitoring())
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
    else:
        # Run validation
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
