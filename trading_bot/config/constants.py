"""
Trading Bot Constants
=====================

Centralized constants file to replace hardcoded values throughout the codebase.
All configurable values should be defined here.

Usage:
    from trading_bot.config.constants import *
    # or
    from trading_bot.config.constants import MAX_RISK_PER_TRADE, DEFAULT_TIMEOUT
"""

from typing import Dict, List

# =============================================================================
# IMMUTABLE SAFETY LIMITS (Cannot be changed by AI)
# =============================================================================

# Risk Limits
import logging

logger = logging.getLogger(__name__)

MAX_RISK_PER_TRADE = 0.02          # 2% max risk per trade
MAX_DAILY_LOSS = 0.05              # 5% max daily loss
MAX_DRAWDOWN = 0.20                # 20% max drawdown
MAX_WEEKLY_LOSS = 0.10             # 10% max weekly loss
MAX_MONTHLY_LOSS = 0.15            # 15% max monthly loss

# Position Limits
MAX_POSITION_SIZE = 0.10           # 10% max position size
MAX_LEVERAGE = 5.0                 # 5x max leverage
MAX_CORRELATED_EXPOSURE = 0.30     # 30% max correlated exposure
MAX_SECTOR_EXPOSURE = 0.25         # 25% max sector exposure
MAX_SINGLE_ASSET_EXPOSURE = 0.20   # 20% max single asset exposure

# Order Limits
MAX_ORDERS_PER_SYMBOL = 10         # Max active orders per symbol
MAX_DAILY_ORDERS = 100             # Max orders per day
MAX_ORDERS_PER_MINUTE = 10         # Rate limit
MAX_POSITION_COUNT = 20            # Max open positions

# =============================================================================
# TIMEOUTS (seconds)
# =============================================================================

DEFAULT_TIMEOUT = 30               # Default timeout for operations
ORDER_TIMEOUT = 300                # Order timeout (5 minutes)
BROKER_TIMEOUT = 60                # Broker API timeout
DATA_TIMEOUT = 30                  # Data feed timeout
HEARTBEAT_TIMEOUT = 30             # Heartbeat timeout
KILL_SWITCH_TIMEOUT = 5            # Kill switch max response time
CONNECTION_TIMEOUT = 10            # Connection timeout
READ_TIMEOUT = 30                  # Read timeout
WRITE_TIMEOUT = 30                 # Write timeout

# =============================================================================
# INTERVALS (seconds)
# =============================================================================

HEARTBEAT_INTERVAL = 10            # Heartbeat interval
HEALTH_CHECK_INTERVAL = 60         # Health check interval
DATA_REFRESH_INTERVAL = 1          # Data refresh interval
POSITION_SYNC_INTERVAL = 30        # Position sync interval
RISK_CHECK_INTERVAL = 5            # Risk check interval
SIGNAL_CHECK_INTERVAL = 1          # Signal check interval
CLEANUP_INTERVAL = 3600            # Cleanup interval (1 hour)

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================

MAX_RETRIES = 3                    # Max retry attempts
RETRY_DELAY = 1.0                  # Initial retry delay (seconds)
RETRY_BACKOFF = 2.0                # Retry backoff multiplier
RETRY_MAX_DELAY = 60.0             # Max retry delay

# =============================================================================
# EXECUTION PARAMETERS
# =============================================================================

# Slippage
DEFAULT_SLIPPAGE_BPS = 5           # Default slippage in basis points
MAX_SLIPPAGE_BPS = 50              # Max acceptable slippage
SLIPPAGE_WARNING_BPS = 20          # Slippage warning threshold

# Order Types
DEFAULT_ORDER_TYPE = "MARKET"
DEFAULT_TIME_IN_FORCE = "GTC"

# Execution Algorithms
TWAP_DEFAULT_SLICES = 10           # Default TWAP slices
VWAP_DEFAULT_SLICES = 20           # Default VWAP slices
ICEBERG_DEFAULT_SHOW_SIZE = 0.1    # Default iceberg show size (10%)

# =============================================================================
# NETWORK CONFIGURATION
# =============================================================================

# Ports
DEFAULT_API_PORT = 8000
DEFAULT_DASHBOARD_PORT = 8080
DEFAULT_METRICS_PORT = 9090
DEFAULT_HEALTH_PORT = 8081

# Hosts
DEFAULT_HOST = "127.0.0.1"
LOCALHOST = "127.0.0.1"

# =============================================================================
# DATA CONFIGURATION
# =============================================================================

# Data Freshness
MAX_DATA_AGE_SECONDS = 60          # Max age for market data
STALE_DATA_THRESHOLD = 30          # Stale data warning threshold

# Timeframes
DEFAULT_TIMEFRAME = "1H"
SUPPORTED_TIMEFRAMES = ["1M", "5M", "15M", "30M", "1H", "4H", "1D", "1W"]

# History
DEFAULT_HISTORY_BARS = 500         # Default bars to load
MAX_HISTORY_BARS = 10000           # Max bars to load

# =============================================================================
# TRADING PARAMETERS
# =============================================================================

# Stop Loss / Take Profit
DEFAULT_STOP_LOSS_PCT = 0.02       # 2% default stop loss
DEFAULT_TAKE_PROFIT_PCT = 0.04     # 4% default take profit (2:1 R:R)
MIN_STOP_LOSS_PCT = 0.005          # 0.5% minimum stop loss
MAX_STOP_LOSS_PCT = 0.10           # 10% maximum stop loss

# Position Sizing
DEFAULT_POSITION_SIZE_PCT = 0.02   # 2% default position size
MIN_POSITION_SIZE = 0.01           # Minimum position size (lots)
MAX_POSITION_SIZE_LOTS = 100       # Maximum position size (lots)

# Confidence Thresholds
MIN_SIGNAL_CONFIDENCE = 0.6        # Minimum signal confidence
HIGH_CONFIDENCE_THRESHOLD = 0.8    # High confidence threshold
VERY_HIGH_CONFIDENCE = 0.9         # Very high confidence

# =============================================================================
# VOLATILITY THRESHOLDS
# =============================================================================

NORMAL_VOLATILITY = 1.0            # Normal volatility ratio
HIGH_VOLATILITY = 2.0              # High volatility threshold
EXTREME_VOLATILITY = 3.0           # Extreme volatility threshold
VOLATILITY_REDUCTION_FACTOR = 0.5  # Position reduction in high vol

# =============================================================================
# MARKET HOURS (UTC)
# =============================================================================

FOREX_MARKET_OPEN = "22:00"        # Sunday
FOREX_MARKET_CLOSE = "22:00"       # Friday
NYSE_OPEN = "14:30"                # 9:30 AM ET
NYSE_CLOSE = "21:00"               # 4:00 PM ET
CRYPTO_24_7 = True                 # Crypto markets 24/7

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_SIZE_MB = 100
LOG_BACKUP_COUNT = 5

# =============================================================================
# DATABASE
# =============================================================================

DEFAULT_DB_PATH = "trading_bot.db"
DB_TIMEOUT = 30
DB_MAX_CONNECTIONS = 10
DB_POOL_SIZE = 5

# =============================================================================
# CACHE
# =============================================================================

CACHE_TTL_SECONDS = 300            # Cache TTL (5 minutes)
CACHE_MAX_SIZE = 1000              # Max cache entries
CACHE_CLEANUP_INTERVAL = 600       # Cleanup interval (10 minutes)

# =============================================================================
# NOTIFICATIONS
# =============================================================================

NOTIFICATION_COOLDOWN = 300        # Notification cooldown (5 minutes)
MAX_NOTIFICATIONS_PER_HOUR = 20    # Max notifications per hour
CRITICAL_NOTIFICATION_PRIORITY = 1
HIGH_NOTIFICATION_PRIORITY = 2
NORMAL_NOTIFICATION_PRIORITY = 3

# =============================================================================
# BROKER SPECIFIC
# =============================================================================

# MT5
MT5_MAGIC_NUMBER = 123456
MT5_DEVIATION = 20
MT5_FILLING_MODE = "IOC"

# Alpaca
ALPACA_API_VERSION = "v2"
ALPACA_DATA_FEED = "iex"

# Binance
BINANCE_RECV_WINDOW = 5000

# =============================================================================
# SYMBOLS
# =============================================================================

MAJOR_FOREX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", 
    "AUDUSD", "USDCAD", "NZDUSD"
]

CROSS_FOREX_PAIRS = [
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY",
    "EURCHF", "EURAUD", "GBPCHF"
]

MAJOR_CRYPTO = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "SOLUSDT", "DOTUSDT"
]

# =============================================================================
# FEATURE FLAGS
# =============================================================================

ENABLE_PAPER_TRADING = True
ENABLE_LIVE_TRADING = False
ENABLE_BACKTESTING = True
ENABLE_ML_SIGNALS = True
ENABLE_SENTIMENT_ANALYSIS = True
ENABLE_NOTIFICATIONS = True
ENABLE_DASHBOARD = True
ENABLE_API = True

# =============================================================================
# CIRCUIT BREAKER
# =============================================================================

CIRCUIT_FAILURE_THRESHOLD = 5      # Failures before opening
CIRCUIT_SUCCESS_THRESHOLD = 3      # Successes to close
CIRCUIT_TIMEOUT_SECONDS = 60       # Time before recovery attempt
CIRCUIT_HALF_OPEN_MAX_CALLS = 3    # Max calls in half-open

# =============================================================================
# KILL SWITCH
# =============================================================================

KILL_SWITCH_FILES = [
    "EMERGENCY_STOP.txt",
    "KILL_SWITCH.txt",
    "STOP_TRADING.txt",
    ".kill_switch"
]

KILL_SWITCH_MAX_SHUTDOWN_MS = 5000  # Max time to shutdown

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_timeout(operation: str) -> int:
    """Get timeout for a specific operation"""
    try:
        timeouts = {
            "order": ORDER_TIMEOUT,
            "broker": BROKER_TIMEOUT,
            "data": DATA_TIMEOUT,
            "connection": CONNECTION_TIMEOUT,
            "default": DEFAULT_TIMEOUT
        }
        return timeouts.get(operation, DEFAULT_TIMEOUT)
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in get_timeout: {e}")
        raise


def get_limit(limit_type: str) -> float:
    """Get limit value by type"""
    try:
        limits = {
            "risk_per_trade": MAX_RISK_PER_TRADE,
            "daily_loss": MAX_DAILY_LOSS,
            "drawdown": MAX_DRAWDOWN,
            "position_size": MAX_POSITION_SIZE,
            "leverage": MAX_LEVERAGE,
            "correlated_exposure": MAX_CORRELATED_EXPOSURE
        }
        return limits.get(limit_type, 0.0)
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in get_limit: {e}")
        raise


# =============================================================================
# EXPORT ALL
# =============================================================================

__all__ = [
    # Risk Limits
    "MAX_RISK_PER_TRADE",
    "MAX_DAILY_LOSS",
    "MAX_DRAWDOWN",
    "MAX_WEEKLY_LOSS",
    "MAX_MONTHLY_LOSS",
    "MAX_POSITION_SIZE",
    "MAX_LEVERAGE",
    "MAX_CORRELATED_EXPOSURE",
    "MAX_SECTOR_EXPOSURE",
    "MAX_SINGLE_ASSET_EXPOSURE",
    
    # Order Limits
    "MAX_ORDERS_PER_SYMBOL",
    "MAX_DAILY_ORDERS",
    "MAX_ORDERS_PER_MINUTE",
    "MAX_POSITION_COUNT",
    
    # Timeouts
    "DEFAULT_TIMEOUT",
    "ORDER_TIMEOUT",
    "BROKER_TIMEOUT",
    "DATA_TIMEOUT",
    "HEARTBEAT_TIMEOUT",
    "KILL_SWITCH_TIMEOUT",
    "CONNECTION_TIMEOUT",
    
    # Intervals
    "HEARTBEAT_INTERVAL",
    "HEALTH_CHECK_INTERVAL",
    "DATA_REFRESH_INTERVAL",
    "RISK_CHECK_INTERVAL",
    
    # Retry
    "MAX_RETRIES",
    "RETRY_DELAY",
    "RETRY_BACKOFF",
    "RETRY_MAX_DELAY",
    
    # Execution
    "DEFAULT_SLIPPAGE_BPS",
    "MAX_SLIPPAGE_BPS",
    
    # Trading
    "DEFAULT_STOP_LOSS_PCT",
    "DEFAULT_TAKE_PROFIT_PCT",
    "MIN_SIGNAL_CONFIDENCE",
    
    # Volatility
    "NORMAL_VOLATILITY",
    "HIGH_VOLATILITY",
    "EXTREME_VOLATILITY",
    
    # Circuit Breaker
    "CIRCUIT_FAILURE_THRESHOLD",
    "CIRCUIT_SUCCESS_THRESHOLD",
    "CIRCUIT_TIMEOUT_SECONDS",
    
    # Kill Switch
    "KILL_SWITCH_FILES",
    "KILL_SWITCH_MAX_SHUTDOWN_MS",
    
    # Symbols
    "MAJOR_FOREX_PAIRS",
    "CROSS_FOREX_PAIRS",
    "MAJOR_CRYPTO",
    
    # Feature Flags
    "ENABLE_PAPER_TRADING",
    "ENABLE_LIVE_TRADING",
    
    # Functions
    "get_timeout",
    "get_limit"
]
