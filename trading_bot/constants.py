"""
import json

import logging
logger = logging.getLogger(__name__)

Trading Bot Constants

Centralized constants to replace magic numbers throughout the codebase.
"""

# Risk Management Constants
DEFAULT_RISK_PERCENTAGE = 0.02  # 2% risk per trade
MAX_RISK_PERCENTAGE = 0.10  # 10% maximum risk
MIN_RISK_PERCENTAGE = 0.001  # 0.1% minimum risk
MAX_POSITION_SIZE = 1000000  # Maximum position size in units
MIN_POSITION_SIZE = 1000  # Minimum position size in units
MAX_LEVERAGE = 100  # Maximum leverage allowed
DEFAULT_LEVERAGE = 1  # Default leverage (no leverage)

# Correlation Thresholds
HIGH_CORRELATION_THRESHOLD = 0.7  # High correlation threshold
MODERATE_CORRELATION_THRESHOLD = 0.5  # Moderate correlation
LOW_CORRELATION_THRESHOLD = 0.3  # Low correlation
NEGATIVE_CORRELATION_THRESHOLD = -0.3  # Negative correlation

# Position Sizing
KELLY_FRACTION = 0.25  # Kelly criterion fraction (conservative)
VOLATILITY_SCALING_FACTOR = 2.0  # Volatility scaling factor
RISK_PARITY_TARGET = 0.15  # Target volatility for risk parity

# Order Execution
DEFAULT_SLIPPAGE_BPS = 5  # Default slippage in basis points
MAX_SLIPPAGE_BPS = 50  # Maximum acceptable slippage
ORDER_TIMEOUT_SECONDS = 30  # Order execution timeout
MAX_RETRIES = 3  # Maximum retry attempts
RETRY_DELAY_SECONDS = 1  # Delay between retries
CONFIRMATION_TIMEOUT_SECONDS = 30  # Fill confirmation timeout

# Time Constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
MILLISECONDS_PER_SECOND = 1000
MICROSECONDS_PER_SECOND = 1000000

# Data Management
MAX_HISTORY_LENGTH = 1000  # Maximum price history length
MIN_DATA_POINTS = 30  # Minimum data points for calculations
MAX_DATA_AGE_HOURS = 24  # Maximum age of cached data
AUTO_SAVE_INTERVAL_SECONDS = 300  # Auto-save interval (5 minutes)

# Health Check Constants
STARTUP_GRACE_PERIOD_SECONDS = 60  # Startup grace period
HEALTH_CHECK_INTERVAL_SECONDS = 30  # Health check interval
MAX_COMPONENT_AGE_SECONDS = 300  # Maximum component check age
HEALTH_CHECK_TIMEOUT_SECONDS = 10  # Health check timeout

# Network Constants
DEFAULT_TIMEOUT_SECONDS = 30  # Default network timeout
MAX_TIMEOUT_SECONDS = 120  # Maximum timeout
CONNECTION_RETRY_DELAY = 5  # Connection retry delay
MAX_CONNECTION_RETRIES = 5  # Maximum connection retries
HIGH_LATENCY_THRESHOLD_MS = 200  # High latency threshold

# Memory Management
LOW_MEMORY_THRESHOLD_MB = 500  # Low memory warning threshold
CRITICAL_MEMORY_THRESHOLD_MB = 200  # Critical memory threshold
MAX_MEMORY_USAGE_MB = 2000  # Maximum memory usage

# Performance Thresholds
MIN_WIN_RATE = 0.40  # Minimum acceptable win rate (40%)
TARGET_WIN_RATE = 0.55  # Target win rate (55%)
EXCELLENT_WIN_RATE = 0.65  # Excellent win rate (65%)
MIN_PROFIT_FACTOR = 1.2  # Minimum profit factor
TARGET_PROFIT_FACTOR = 2.0  # Target profit factor
MAX_DRAWDOWN_PERCENTAGE = 0.20  # Maximum drawdown (20%)

# Technical Indicators
RSI_PERIOD = 14  # RSI period
RSI_OVERBOUGHT = 70  # RSI overbought level
RSI_OVERSOLD = 30  # RSI oversold level
MACD_FAST_PERIOD = 12  # MACD fast period
MACD_SLOW_PERIOD = 26  # MACD slow period
MACD_SIGNAL_PERIOD = 9  # MACD signal period
ATR_PERIOD = 14  # ATR period
BOLLINGER_PERIOD = 20  # Bollinger Bands period
BOLLINGER_STD_DEV = 2.0  # Bollinger Bands standard deviation

# Position Management
MAX_OPEN_POSITIONS = 10  # Maximum open positions
MAX_POSITIONS_PER_SYMBOL = 3  # Maximum positions per symbol
MIN_FREE_MARGIN_PERCENTAGE = 0.30  # Minimum free margin (30%)
POSITION_SIZE_INCREMENT = 1000  # Position size increment

# Price Precision
FOREX_PRICE_PRECISION = 5  # Forex price decimal places
CRYPTO_PRICE_PRECISION = 8  # Crypto price decimal places
STOCK_PRICE_PRECISION = 2  # Stock price decimal places

# Pip Values (for forex)
STANDARD_LOT_SIZE = 100000  # Standard lot size
MINI_LOT_SIZE = 10000  # Mini lot size
MICRO_LOT_SIZE = 1000  # Micro lot size
NANO_LOT_SIZE = 100  # Nano lot size
JPY_PIP_MULTIPLIER = 0.01  # JPY pip multiplier
STANDARD_PIP_MULTIPLIER = 0.0001  # Standard pip multiplier

# Confidence Levels
MIN_CONFIDENCE = 0.50  # Minimum confidence for trade
MODERATE_CONFIDENCE = 0.65  # Moderate confidence
HIGH_CONFIDENCE = 0.80  # High confidence
VERY_HIGH_CONFIDENCE = 0.90  # Very high confidence

# Volatility Levels
LOW_VOLATILITY = 0.01  # Low volatility (1%)
MODERATE_VOLATILITY = 0.02  # Moderate volatility (2%)
HIGH_VOLATILITY = 0.04  # High volatility (4%)
EXTREME_VOLATILITY = 0.08  # Extreme volatility (8%)

# Stop Loss / Take Profit
DEFAULT_STOP_LOSS_PIPS = 50  # Default stop loss in pips
DEFAULT_TAKE_PROFIT_PIPS = 100  # Default take profit in pips
MIN_STOP_LOSS_PIPS = 10  # Minimum stop loss
MAX_STOP_LOSS_PIPS = 500  # Maximum stop loss
TRAILING_STOP_DISTANCE_PIPS = 30  # Trailing stop distance
BREAKEVEN_TRIGGER_PIPS = 20  # Breakeven trigger distance

# Risk-Reward Ratios
MIN_RISK_REWARD_RATIO = 1.5  # Minimum risk-reward ratio
TARGET_RISK_REWARD_RATIO = 2.0  # Target risk-reward ratio
EXCELLENT_RISK_REWARD_RATIO = 3.0  # Excellent risk-reward ratio

# Slippage Tracking
POSITIVE_SLIPPAGE_THRESHOLD_BPS = 0  # Positive slippage threshold
NEGATIVE_SLIPPAGE_THRESHOLD_BPS = -10  # Negative slippage threshold
EXCESSIVE_SLIPPAGE_BPS = 20  # Excessive slippage threshold

# Database Constants
MAX_QUERY_RESULTS = 10000  # Maximum query results
BATCH_SIZE = 1000  # Batch processing size
CACHE_TTL_SECONDS = 3600  # Cache time-to-live (1 hour)

# Logging Constants
LOG_ROTATION_SIZE_MB = 100  # Log file rotation size
LOG_RETENTION_DAYS = 30  # Log retention period
MAX_LOG_FILES = 10  # Maximum log files to keep

# API Rate Limits
API_RATE_LIMIT_PER_MINUTE = 60  # API calls per minute
API_RATE_LIMIT_PER_HOUR = 1000  # API calls per hour
API_BURST_LIMIT = 10  # Burst limit

# Backtesting Constants
MIN_BACKTEST_DAYS = 30  # Minimum backtest period
RECOMMENDED_BACKTEST_DAYS = 365  # Recommended backtest period
MIN_TRADES_FOR_STATISTICS = 30  # Minimum trades for valid statistics

# Machine Learning Constants
MIN_TRAINING_SAMPLES = 1000  # Minimum training samples
VALIDATION_SPLIT = 0.2  # Validation split ratio
TEST_SPLIT = 0.1  # Test split ratio
EARLY_STOPPING_PATIENCE = 10  # Early stopping patience
MAX_EPOCHS = 100  # Maximum training epochs
LEARNING_RATE = 0.001  # Default learning rate

# Feature Engineering
MAX_FEATURES = 100  # Maximum number of features
FEATURE_IMPORTANCE_THRESHOLD = 0.01  # Feature importance threshold
CORRELATION_FEATURE_THRESHOLD = 0.95  # Feature correlation threshold

# Model Performance
MIN_MODEL_ACCURACY = 0.55  # Minimum model accuracy
TARGET_MODEL_ACCURACY = 0.65  # Target model accuracy
MIN_MODEL_PRECISION = 0.60  # Minimum precision
MIN_MODEL_RECALL = 0.60  # Minimum recall
MIN_F1_SCORE = 0.60  # Minimum F1 score

# Alert Thresholds
CRITICAL_ALERT_THRESHOLD = 0.90  # Critical alert threshold
WARNING_ALERT_THRESHOLD = 0.70  # Warning alert threshold
INFO_ALERT_THRESHOLD = 0.50  # Info alert threshold

# System Resources
MAX_CPU_USAGE_PERCENTAGE = 80  # Maximum CPU usage
MAX_DISK_USAGE_PERCENTAGE = 90  # Maximum disk usage
MIN_FREE_DISK_SPACE_GB = 10  # Minimum free disk space

# Concurrency
MAX_CONCURRENT_ORDERS = 5  # Maximum concurrent orders
MAX_WORKER_THREADS = 10  # Maximum worker threads
THREAD_POOL_SIZE = 4  # Thread pool size

# Validation Constants
MAX_STRING_LENGTH = 1000  # Maximum string length
MAX_ARRAY_SIZE = 10000  # Maximum array size
MIN_PRICE = 0.00001  # Minimum valid price
MAX_PRICE = 1000000  # Maximum valid price

# Symbol Types
FOREX_SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
CRYPTO_SYMBOLS = ['BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD']
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']

# Status Codes
STATUS_SUCCESS = 'success'
STATUS_FAILURE = 'failure'
STATUS_PENDING = 'pending'
STATUS_TIMEOUT = 'timeout'
STATUS_CANCELLED = 'cancelled'
STATUS_REJECTED = 'rejected'

# Error Codes
ERROR_INVALID_INPUT = 'INVALID_INPUT'
ERROR_INSUFFICIENT_FUNDS = 'INSUFFICIENT_FUNDS'
ERROR_CONNECTION_FAILED = 'CONNECTION_FAILED'
ERROR_TIMEOUT = 'TIMEOUT'
ERROR_RATE_LIMIT = 'RATE_LIMIT_EXCEEDED'
ERROR_INVALID_SYMBOL = 'INVALID_SYMBOL'
ERROR_INVALID_ORDER = 'INVALID_ORDER'
ERROR_BROKER_ERROR = 'BROKER_ERROR'
ERROR_DATA_ERROR = 'DATA_ERROR'
ERROR_SYSTEM_ERROR = 'SYSTEM_ERROR'

# File Extensions
JSON_EXTENSION = '.json'
CSV_EXTENSION = '.csv'
PICKLE_EXTENSION = '.pkl'
PARQUET_EXTENSION = '.parquet'
LOG_EXTENSION = '.log'

# Date Formats
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
ISO_FORMAT = '%Y-%m-%dT%H:%M:%S'

# Environment
ENV_DEVELOPMENT = 'development'
ENV_STAGING = 'staging'
ENV_PRODUCTION = 'production'
ENV_TESTING = 'testing'

# Trading Sessions
ASIAN_SESSION_START = 0  # 00:00 UTC
ASIAN_SESSION_END = 9  # 09:00 UTC
EUROPEAN_SESSION_START = 7  # 07:00 UTC
EUROPEAN_SESSION_END = 16  # 16:00 UTC
AMERICAN_SESSION_START = 13  # 13:00 UTC
AMERICAN_SESSION_END = 22  # 22:00 UTC

# Version
VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_STRING = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
