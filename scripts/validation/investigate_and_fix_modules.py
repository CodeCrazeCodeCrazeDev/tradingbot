"""
Module Structure Investigation and Auto-Fix Script
Discovers actual module locations and creates compatibility wrappers
"""

import os
import sys
from pathlib import Path
import importlib
import json
from typing import Any, Dict, List, Tuple

class ModuleInvestigator:
    """Investigates and fixes module structure issues"""
    
    def __init__(self):
        self.root = Path(__file__).parent
        self.trading_bot_path = self.root / 'trading_bot'
        self.findings = {}
        self.fixes_applied = []
        
    def investigate_all(self):
        """Run all investigations"""
        print("="*80)
        print("MODULE STRUCTURE INVESTIGATION")
        print("="*80)
        
        self.investigate_data_modules()
        self.investigate_strategy_modules()
        self.investigate_execution_modules()
        self.investigate_config_modules()
        self.investigate_utils_modules()
        
        self.save_findings()
        self.print_summary()
        
    def investigate_data_modules(self):
        """Investigate data module structure"""
        print("\n[1] Investigating DATA modules...")
        
        data_path = self.trading_bot_path / 'data'
        findings = {
            'expected': 'trading_bot.data.market_data',
            'exists': False,
            'alternatives': []
        }
        
        if data_path.exists():
            for file in data_path.glob('*.py'):
                if file.name != '__init__.py':
                    findings['alternatives'].append(str(file.relative_to(self.trading_bot_path)))
        
        # Check schemas
        schemas_path = self.trading_bot_path / 'schemas'
        if schemas_path.exists():
            for file in schemas_path.glob('*market*.py'):
                findings['alternatives'].append(f"schemas/{file.name}")
        
        # Check if expected exists
        expected_file = data_path / 'market_data.py'
        findings['exists'] = expected_file.exists()
        
        self.findings['data_modules'] = findings
        print(f"   Expected: {findings['expected']}")
        print(f"   Exists: {findings['exists']}")
        print(f"   Alternatives found: {len(findings['alternatives'])}")
        for alt in findings['alternatives']:
            print(f"      - {alt}")
    
    def investigate_strategy_modules(self):
        """Investigate strategy module structure"""
        print("\n[2] Investigating STRATEGY modules...")
        
        strategy_path = self.trading_bot_path / 'strategy'
        findings = {
            'expected': 'trading_bot.strategy.base_strategy',
            'exists': False,
            'alternatives': []
        }
        
        if strategy_path.exists():
            for file in strategy_path.glob('*.py'):
                if file.name != '__init__.py':
                    findings['alternatives'].append(str(file.relative_to(self.trading_bot_path)))
        
        # Check adaptive_systems
        adaptive_path = self.trading_bot_path / 'adaptive_systems'
        if adaptive_path.exists():
            for file in adaptive_path.glob('*strategy*.py'):
                findings['alternatives'].append(f"adaptive_systems/{file.name}")
        
        expected_file = strategy_path / 'base_strategy.py'
        findings['exists'] = expected_file.exists()
        
        self.findings['strategy_modules'] = findings
        print(f"   Expected: {findings['expected']}")
        print(f"   Exists: {findings['exists']}")
        print(f"   Alternatives found: {len(findings['alternatives'])}")
        for alt in findings['alternatives']:
            print(f"      - {alt}")
    
    def investigate_execution_modules(self):
        """Investigate execution module structure"""
        print("\n[3] Investigating EXECUTION modules...")
        
        execution_path = self.trading_bot_path / 'execution'
        findings = {
            'expected': 'trading_bot.execution.trade_executor',
            'exists': False,
            'alternatives': []
        }
        
        if execution_path.exists():
            for file in execution_path.glob('*.py'):
                if file.name != '__init__.py':
                    findings['alternatives'].append(str(file.relative_to(self.trading_bot_path)))
        
        expected_file = execution_path / 'trade_executor.py'
        findings['exists'] = expected_file.exists()
        
        self.findings['execution_modules'] = findings
        print(f"   Expected: {findings['expected']}")
        print(f"   Exists: {findings['exists']}")
        print(f"   Alternatives found: {len(findings['alternatives'])}")
        for alt in findings['alternatives']:
            print(f"      - {alt}")
    
    def investigate_config_modules(self):
        """Investigate config module structure"""
        print("\n[4] Investigating CONFIG modules...")
        
        config_path = self.trading_bot_path / 'config'
        findings = {
            'expected': 'trading_bot.config.config_manager',
            'exists': False,
            'alternatives': []
        }
        
        if config_path.exists():
            for file in config_path.glob('*.py'):
                if file.name != '__init__.py':
                    findings['alternatives'].append(str(file.relative_to(self.trading_bot_path)))
        
        expected_file = config_path / 'config_manager.py'
        findings['exists'] = expected_file.exists()
        
        self.findings['config_modules'] = findings
        print(f"   Expected: {findings['expected']}")
        print(f"   Exists: {findings['exists']}")
        print(f"   Alternatives found: {len(findings['alternatives'])}")
        for alt in findings['alternatives']:
            print(f"      - {alt}")
    
    def investigate_utils_modules(self):
        """Investigate utils module structure"""
        print("\n[5] Investigating UTILS modules...")
        
        utils_path = self.trading_bot_path / 'utils'
        findings = {
            'expected': 'trading_bot.utils.logger',
            'exists': False,
            'alternatives': []
        }
        
        if utils_path.exists():
            for file in utils_path.glob('*.py'):
                if file.name != '__init__.py':
                    findings['alternatives'].append(str(file.relative_to(self.trading_bot_path)))
        
        expected_file = utils_path / 'logger.py'
        findings['exists'] = expected_file.exists()
        
        self.findings['utils_modules'] = findings
        print(f"   Expected: {findings['expected']}")
        print(f"   Exists: {findings['exists']}")
        print(f"   Alternatives found: {len(findings['alternatives'])}")
        for alt in findings['alternatives']:
            print(f"      - {alt}")
    
    def save_findings(self):
        """Save findings to JSON"""
        findings_file = self.root / 'logs' / 'module_investigation_report.json'
        findings_file.parent.mkdir(exist_ok=True)
        
        with open(findings_file, 'w', encoding='utf-8') as f:
            json.dump(self.findings, f, indent=2)
        
        print(f"\n✅ Findings saved to: {findings_file}")
    
    def print_summary(self):
        """Print investigation summary"""
        print("\n" + "="*80)
        print("INVESTIGATION SUMMARY")
        print("="*80)
        
        total_expected = len(self.findings)
        total_exists = sum(1 for f in self.findings.values() if f.get('exists'))
        total_missing = total_expected - total_exists
        
        print(f"\nTotal Expected Modules: {total_expected}")
        print(f"✅ Existing: {total_exists}")
        print(f"❌ Missing: {total_missing}")
        
        if total_missing > 0:
            print(f"\n❌ MISSING MODULES:")
            for category, data in self.findings.items():
                if not data.get('exists'):
                    print(f"   - {data['expected']}")
                    if data['alternatives']:
                        print(f"     Alternatives available: {len(data['alternatives'])}")
    
    def create_compatibility_wrappers(self):
        """Create compatibility wrapper modules"""
        print("\n" + "="*80)
        print("CREATING COMPATIBILITY WRAPPERS")
        print("="*80)
        
        # Create market_data wrapper
        self._create_market_data_wrapper()
        
        # Create base_strategy wrapper
        self._create_base_strategy_wrapper()
        
        # Create trade_executor wrapper
        self._create_trade_executor_wrapper()
        
        # Create logger wrapper
        self._create_logger_wrapper()
        
        # Create config_manager wrapper
        self._create_config_manager_wrapper()
        
        print(f"\n✅ Created {len(self.fixes_applied)} compatibility wrappers")
    
    def _create_market_data_wrapper(self):
        """Create market_data.py wrapper"""
        target = self.trading_bot_path / 'data' / 'market_data.py'
        
        if target.exists():
            print(f"⚠️  {target.name} already exists, skipping")
            return
        
        content = '''"""
Market Data Module - Compatibility Wrapper
Provides unified interface to market data functionality
"""

from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime

# Import from actual implementation
try:
    from trading_bot.data.market_data_stream import MarketDataStream
except ImportError:
    MarketDataStream = None

try:
    from trading_bot.schemas.market_data import MarketData
except ImportError:
    MarketData = None

class MarketDataFetcher:
    """
    Unified market data fetcher
    Wrapper for compatibility with legacy code
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.stream = None
        
        if MarketDataStream:
            try:
                self.stream = MarketDataStream(self.config)
            except Exception as e:
                print(f"Warning: Could not initialize MarketDataStream: {e}")
    
    def fetch_data(self, symbol: str, timeframe: str = '1H', 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch market data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe (e.g., '1H', '1D')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        # Try to use MT5 if available
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                raise Exception("MT5 initialization failed")
            
            # Convert timeframe
            tf_map = {
                '1M': mt5.TIMEFRAME_M1,
                '5M': mt5.TIMEFRAME_M5,
                '15M': mt5.TIMEFRAME_M15,
                '30M': mt5.TIMEFRAME_M30,
                '1H': mt5.TIMEFRAME_H1,
                '4H': mt5.TIMEFRAME_H4,
                '1D': mt5.TIMEFRAME_D1,
                '1W': mt5.TIMEFRAME_W1,
            }
            
            mt5_tf = tf_map.get(timeframe.upper(), mt5.TIMEFRAME_H1)
            
            # Fetch data
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, 1000)
            
            if rates is None or len(rates) == 0:
                raise Exception(f"No data returned for {symbol}")
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.rename(columns={
                'time': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            })
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            # Return empty DataFrame with correct structure
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for symbol"""
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                return None
            
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return tick.bid
            
        except Exception:
            pass
        
        return None

# Export for compatibility
__all__ = ['MarketDataFetcher', 'MarketData', 'MarketDataStream']
'''
        
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Created: {target.relative_to(self.root)}")
        self.fixes_applied.append(str(target))
    
    def _create_base_strategy_wrapper(self):
        """Create base_strategy.py wrapper"""
        target = self.trading_bot_path / 'strategy' / 'base_strategy.py'
        
        if target.exists():
            print(f"⚠️  {target.name} already exists, skipping")
            return
        
        content = '''"""
Base Strategy Module - Compatibility Wrapper
Provides base classes for trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd

class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"

@dataclass
class TradingSignal:
    """Trading signal data structure"""
    signal_type: SignalType
    symbol: str
    confidence: float
    timestamp: pd.Timestamp
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseStrategy(ABC):
    """
    Base class for all trading strategies
    
    All strategies should inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy
        
        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.is_initialized = False
        self.parameters = {}
        
    @abstractmethod
    def analyze_market(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze market data
        
        Args:
            data: Market data DataFrame with OHLCV columns
            
        Returns:
            Dictionary with analysis results
        """
        pass
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame, 
                       analysis: Optional[Dict[str, Any]] = None) -> TradingSignal:
        """
        Generate trading signal
        
        Args:
            data: Market data DataFrame
            analysis: Optional pre-computed analysis results
            
        Returns:
            TradingSignal object
        """
        pass
    
    def filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Filter and validate signals
        
        Args:
            signals: List of trading signals
            
        Returns:
            Filtered list of signals
        """
        # Default implementation: return all signals
        return signals
    
    def update_parameters(self, parameters: Dict[str, Any]):
        """
        Update strategy parameters
        
        Args:
            parameters: Dictionary of parameters to update
        """
        self.parameters.update(parameters)
    
    def initialize(self):
        """Initialize strategy (called before first use)"""
        self.is_initialized = True
    
    def shutdown(self):
        """Cleanup strategy resources"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'parameters': self.parameters,
            'is_initialized': self.is_initialized
        }

# Try to import from actual implementations
try:
    from trading_bot.strategy.strategy_engine import StrategyEngine
except ImportError:
    StrategyEngine = None

try:
    from trading_bot.strategy.ml_strategy import MLStrategy
except ImportError:
    MLStrategy = None

# Export for compatibility
__all__ = ['BaseStrategy', 'TradingSignal', 'SignalType', 'StrategyEngine', 'MLStrategy']
'''
        
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Created: {target.relative_to(self.root)}")
        self.fixes_applied.append(str(target))
    
    def _create_trade_executor_wrapper(self):
        """Create trade_executor.py wrapper"""
        target = self.trading_bot_path / 'execution' / 'trade_executor.py'
        
        if target.exists():
            print(f"⚠️  {target.name} already exists, skipping")
            return
        
        content = '''"""
Trade Executor Module - Compatibility Wrapper
Provides unified interface for trade execution
"""

from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderSide(Enum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class Order:
    """Order data structure"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class TradeExecutor:
    """
    Trade execution engine
    Handles order placement and management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize trade executor
        
        Args:
            config: Executor configuration
        """
        self.config = config or {}
        self.is_paper_trading = self.config.get('paper_trading', True)
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0
        
    def execute_trade(self, order: Order) -> Dict[str, Any]:
        """
        Execute a trade order
        
        Args:
            order: Order object to execute
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Generate order ID if not provided
            if not order.order_id:
                self.order_counter += 1
                order.order_id = f"ORD_{self.order_counter:06d}"
            
            order.timestamp = datetime.now()
            
            if self.is_paper_trading:
                # Paper trading simulation
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                self.orders[order.order_id] = order
                
                return {
                    'success': True,
                    'order_id': order.order_id,
                    'status': order.status.value,
                    'message': 'Order executed (paper trading)'
                }
            else:
                # Real trading (requires MT5 or broker integration)
                return self._execute_real_trade(order)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Order execution failed: {str(e)}'
            }
    
    def _execute_real_trade(self, order: Order) -> Dict[str, Any]:
        """Execute real trade via MT5"""
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                raise Exception("MT5 not initialized")
            
            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": order.symbol,
                "volume": order.quantity,
                "type": mt5.ORDER_TYPE_BUY if order.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL,
                "deviation": 20,
                "magic": 234000,
                "comment": "python script",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            if order.price:
                request["price"] = order.price
            if order.stop_loss:
                request["sl"] = order.stop_loss
            if order.take_profit:
                request["tp"] = order.take_profit
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.order_id = str(result.order)
                self.orders[order.order_id] = order
                
                return {
                    'success': True,
                    'order_id': order.order_id,
                    'status': order.status.value,
                    'message': 'Order executed successfully'
                }
            else:
                raise Exception(f"Order failed: {result.comment}")
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Real trade execution failed: {str(e)}'
            }
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        if order_id in self.orders:
            order = self.orders[order_id]
            order.status = OrderStatus.CANCELLED
            return {'success': True, 'message': 'Order cancelled'}
        return {'success': False, 'message': 'Order not found'}
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        return self.orders.get(order_id)
    
    def get_open_orders(self) -> List[Order]:
        """Get all open orders"""
        return [o for o in self.orders.values() 
                if o.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]]

# Export for compatibility
__all__ = ['TradeExecutor', 'Order', 'OrderType', 'OrderSide', 'OrderStatus']
'''
        
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Created: {target.relative_to(self.root)}")
        self.fixes_applied.append(str(target))
    
    def _create_logger_wrapper(self):
        """Create logger.py wrapper"""
        target = self.trading_bot_path / 'utils' / 'logger.py'
        
        if target.exists():
            print(f"⚠️  {target.name} already exists, skipping")
            return
        
        content = '''"""
Logger Module - Compatibility Wrapper
Provides unified logging interface using loguru
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional

def setup_logger(log_file: Optional[str] = None, 
                level: str = "INFO",
                rotation: str = "100 MB",
                retention: str = "30 days"):
    """
    Setup logger with file and console output
    
    Args:
        log_file: Path to log file (default: logs/trading_bot.log)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: When to rotate log file
        retention: How long to keep old logs
        
    Returns:
        Configured logger instance
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    else:
        # Default log file
        default_log = Path("logs/trading_bot.log")
        default_log.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            str(default_log),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    return logger

# Create default logger instance
default_logger = setup_logger()

# Export for compatibility
__all__ = ['setup_logger', 'logger', 'default_logger']
'''
        
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Created: {target.relative_to(self.root)}")
        self.fixes_applied.append(str(target))
    
    def _create_config_manager_wrapper(self):
        """Create config_manager.py wrapper"""
        target = self.trading_bot_path / 'config' / 'config_manager.py'
        
        if target.exists():
            print(f"⚠️  {target.name} already exists, skipping")
            return
        
        content = '''"""
Config Manager Module - Compatibility Wrapper
Provides unified configuration management
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """
    Configuration manager
    Handles loading and managing bot configuration
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config manager
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        self.config_path = config_path or "config/config.yaml"
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            print(f"Warning: Config file not found: {config_file}")
            self.config = self._get_default_config()
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    self.config = yaml.safe_load(f) or {}
                elif config_file.suffix == '.json':
                    self.config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_file.suffix}")
            
            print(f"✅ Loaded config from: {config_file}")
            
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self._get_default_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'risk.max_drawdown')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self, output_path: Optional[str] = None):
        """
        Save configuration to file
        
        Args:
            output_path: Output file path (default: use original path)
        """
        output_file = Path(output_path or self.config_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_file.suffix in ['.yaml', '.yml']:
                    yaml.dump(self.config, f, default_flow_style=False)
                elif output_file.suffix == '.json':
                    json.dump(self.config, f, indent=2)
            
            print(f"✅ Saved config to: {output_file}")
            
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'trading': {
                'symbol': 'EURUSD',
                'timeframe': '1H',
                'paper_trading': True
            },
            'risk': {
                'max_lot_size': 1.0,
                'max_drawdown': 0.2,
                'risk_per_trade': 0.02,
                'stop_loss_pips': 50,
                'take_profit_pips': 100
            },
            'strategy': {
                'name': 'default',
                'parameters': {}
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/trading_bot.log'
            }
        }
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self.config.copy()

# Export for compatibility
__all__ = ['ConfigManager']
'''
        
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Created: {target.relative_to(self.root)}")
        self.fixes_applied.append(str(target))

def main():
    """Main function"""
    # Set UTF-8 encoding for Windows console
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("Starting module investigation and auto-fix...\n")
    
    investigator = ModuleInvestigator()
    
    # Run investigation
    investigator.investigate_all()
    
    # Ask user if they want to create wrappers
    print("\n" + "="*80)
    response = input("Create compatibility wrappers for missing modules? (y/n): ")
    
    if response.lower() == 'y':
        investigator.create_compatibility_wrappers()
        print("\n✅ Auto-fix complete!")
        print("\nNext steps:")
        print("1. Review created wrapper modules")
        print("2. Run comprehensive_qa_validation.py again")
        print("3. Update main.py and other entry points if needed")
    else:
        print("\n⚠️  Skipped wrapper creation")
        print("Review the investigation report in logs/module_investigation_report.json")

if __name__ == '__main__':
    main()
