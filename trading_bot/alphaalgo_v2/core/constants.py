"""
AlphaAlgo V2 Core Constants

STABILITY GUARANTEE: These constants are FROZEN and will NEVER change.
These define the immutable safety constraints and system parameters.

CRITICAL: The risk limits defined here are IMMUTABLE and cannot be
modified by the evolution engine or any automated process.
"""

from enum import Enum
from typing import Dict, Final, List
from enum import auto

import logging
logger = logging.getLogger(__name__)



# ============================================================================
# IMMUTABLE RISK LIMITS
# These values are FROZEN and cannot be changed by the AI
# ============================================================================

# Maximum risk per trade (2%)
MAX_RISK_PER_TRADE: Final[float] = 0.02

# Maximum daily loss (5%)
MAX_DAILY_LOSS: Final[float] = 0.05

# Maximum drawdown (20%)
MAX_DRAWDOWN: Final[float] = 0.20

# Maximum leverage (5x)
MAX_LEVERAGE: Final[float] = 5.0

# Maximum position size as % of portfolio (10%)
MAX_POSITION_SIZE: Final[float] = 0.10

# Maximum sector exposure (25%)
MAX_SECTOR_EXPOSURE: Final[float] = 0.25

# Maximum correlated exposure (30%)
MAX_CORRELATED_EXPOSURE: Final[float] = 0.30

# Minimum Sharpe ratio target
MIN_SHARPE_RATIO: Final[float] = 1.5

# Minimum win rate target
MIN_WIN_RATE: Final[float] = 0.45


# ============================================================================
# IMMUTABLE ETHICAL CONSTRAINTS
# These constraints are FROZEN and cannot be changed
# ============================================================================

# No market manipulation
NO_MARKET_MANIPULATION: Final[bool] = True

# No insider trading
NO_INSIDER_TRADING: Final[bool] = True

# No front-running
NO_FRONT_RUNNING: Final[bool] = True

# Human override always available
HUMAN_OVERRIDE_ALWAYS: Final[bool] = True

# Emergency stop always available
EMERGENCY_STOP_ALWAYS: Final[bool] = True

# Complete audit trail
AUDIT_TRAIL_ALWAYS: Final[bool] = True


# ============================================================================
# TRADING MODES
# ============================================================================

class TradingMode(Enum):
    """Trading mode enumeration"""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"
    SIMULATION = "simulation"


class SafetyLevel(Enum):
    """Safety level enumeration"""
    GREEN = "green"       # Normal operation
    YELLOW = "yellow"     # Caution - reduced position sizes
    ORANGE = "orange"     # Warning - minimal trading
    RED = "red"           # Critical - close positions
    BLACK = "black"       # Emergency - full shutdown


class MarketRegime(Enum):
    """Market regime enumeration"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    QUIET = "quiet"
    TRANSITIONING = "transitioning"


class EvolutionApprovalLevel(Enum):
    """Evolution approval level enumeration"""
    AUTO = "auto"           # Can be auto-approved
    REVIEW = "review"       # Requires review but can be auto-approved
    HUMAN = "human"         # Requires human approval


# ============================================================================
# TIMEFRAMES
# ============================================================================

TIMEFRAMES: Dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
    "W1": 10080,
    "MN1": 43200,
}

TIMEFRAME_NAMES: Dict[str, str] = {
    "M1": "1 Minute",
    "M5": "5 Minutes",
    "M15": "15 Minutes",
    "M30": "30 Minutes",
    "H1": "1 Hour",
    "H4": "4 Hours",
    "D1": "1 Day",
    "W1": "1 Week",
    "MN1": "1 Month",
}


# ============================================================================
# SYSTEM DEFAULTS
# ============================================================================

# Default timeframe
DEFAULT_TIMEFRAME: Final[str] = "M15"

# Default bars to fetch
DEFAULT_BARS: Final[int] = 200

# Default confidence threshold
DEFAULT_CONFIDENCE_THRESHOLD: Final[float] = 0.6

# Default position sizing method
DEFAULT_SIZING_METHOD: Final[str] = "kelly"

# Default execution algorithm
DEFAULT_EXECUTION_ALGO: Final[str] = "smart"

# Maximum concurrent positions
MAX_CONCURRENT_POSITIONS: Final[int] = 10

# Maximum orders per minute
MAX_ORDERS_PER_MINUTE: Final[int] = 10

# Data staleness threshold (seconds)
DATA_STALENESS_THRESHOLD: Final[int] = 5

# Signal expiry (seconds)
SIGNAL_EXPIRY_SECONDS: Final[int] = 300


# ============================================================================
# REWARD MODEL WEIGHTS (IMMUTABLE)
# ============================================================================

REWARD_WEIGHTS: Dict[str, float] = {
    "profit_factor": 0.40,
    "sharpe_ratio": 0.30,
    "win_rate": 0.20,
    "drawdown_penalty": 0.10,
}


# ============================================================================
# EVOLUTION CATEGORIES
# ============================================================================

EVOLUTION_CATEGORIES: Dict[str, EvolutionApprovalLevel] = {
    # Auto-approved changes
    "parameter_tuning": EvolutionApprovalLevel.AUTO,
    "model_retraining": EvolutionApprovalLevel.AUTO,
    "cache_optimization": EvolutionApprovalLevel.AUTO,
    
    # Review required
    "strategy_weights": EvolutionApprovalLevel.REVIEW,
    "new_indicators": EvolutionApprovalLevel.REVIEW,
    "execution_params": EvolutionApprovalLevel.REVIEW,
    
    # Human approval required
    "code_refactoring": EvolutionApprovalLevel.HUMAN,
    "new_strategies": EvolutionApprovalLevel.HUMAN,
    "risk_limit_changes": EvolutionApprovalLevel.HUMAN,
    "broker_changes": EvolutionApprovalLevel.HUMAN,
    "security_changes": EvolutionApprovalLevel.HUMAN,
}


# ============================================================================
# SUPPORTED ASSETS
# ============================================================================

FOREX_MAJORS: List[str] = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "USDCAD", "NZDUSD",
]

FOREX_CROSSES: List[str] = [
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY",
    "EURCHF", "EURAUD", "GBPAUD", "CADJPY",
]

CRYPTO_MAJORS: List[str] = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "SOLUSDT", "DOGEUSDT", "DOTUSDT",
]

INDICES: List[str] = [
    "US500", "US30", "US100", "DE40", "UK100",
]


# ============================================================================
# API RATE LIMITS
# ============================================================================

RATE_LIMITS: Dict[str, int] = {
    "mt5": 100,          # Requests per minute
    "yahoo": 2000,       # Requests per hour
    "binance": 1200,     # Requests per minute
    "coingecko": 50,     # Requests per minute
    "newsapi": 100,      # Requests per day (free tier)
    "fred": 120,         # Requests per minute
}


# ============================================================================
# LOGGING LEVELS
# ============================================================================

LOG_LEVELS: Dict[str, int] = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


# ============================================================================
# VERSION INFO
# ============================================================================

VERSION: Final[str] = "2.0.0"
VERSION_NAME: Final[str] = "AlphaAlgo V2 - Unified Architecture"
BUILD_DATE: Final[str] = "2025-12-08"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_constraints() -> Dict[str, float]:
    """Get all immutable constraints as a dictionary"""
    return {
        "max_risk_per_trade": MAX_RISK_PER_TRADE,
        "max_daily_loss": MAX_DAILY_LOSS,
        "max_drawdown": MAX_DRAWDOWN,
        "max_leverage": MAX_LEVERAGE,
        "max_position_size": MAX_POSITION_SIZE,
        "max_sector_exposure": MAX_SECTOR_EXPOSURE,
        "max_correlated_exposure": MAX_CORRELATED_EXPOSURE,
        "min_sharpe_ratio": MIN_SHARPE_RATIO,
        "min_win_rate": MIN_WIN_RATE,
    }


def get_ethical_constraints() -> Dict[str, bool]:
    """Get all ethical constraints as a dictionary"""
    return {
        "no_market_manipulation": NO_MARKET_MANIPULATION,
        "no_insider_trading": NO_INSIDER_TRADING,
        "no_front_running": NO_FRONT_RUNNING,
        "human_override_always": HUMAN_OVERRIDE_ALWAYS,
        "emergency_stop_always": EMERGENCY_STOP_ALWAYS,
        "audit_trail_always": AUDIT_TRAIL_ALWAYS,
    }


def is_valid_timeframe(timeframe: str) -> bool:
    """Check if timeframe is valid"""
    return timeframe in TIMEFRAMES


def get_timeframe_minutes(timeframe: str) -> int:
    """Get timeframe in minutes"""
    return TIMEFRAMES.get(timeframe, 15)
