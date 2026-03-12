"""
Helper utility functions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio."""
    if len(returns) == 0:
        return 0.0
    
    excess_returns = returns - risk_free_rate / 252
    if excess_returns.std() == 0:
        return 0.0
    
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()


def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """Calculate Sortino ratio."""
    if len(returns) == 0:
        return 0.0
    
    excess_returns = returns - risk_free_rate / 252
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0.0
    
    return np.sqrt(252) * excess_returns.mean() / downside_returns.std()


def calculate_max_drawdown(equity_curve: np.ndarray) -> float:
    """Calculate maximum drawdown."""
    if len(equity_curve) == 0:
        return 0.0
    
    cummax = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - cummax) / cummax
    
    return abs(drawdown.min())


def calculate_var(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Calculate Value at Risk."""
    if len(returns) == 0:
        return 0.0
    
    return np.percentile(returns, (1 - confidence) * 100)


def calculate_cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Calculate Conditional Value at Risk."""
    if len(returns) == 0:
        return 0.0
    
    var = calculate_var(returns, confidence)
    return returns[returns <= var].mean()


def normalize_data(data: np.ndarray, method: str = 'zscore') -> np.ndarray:
    """Normalize data."""
    if method == 'zscore':
        return (data - data.mean()) / (data.std() + 1e-8)
    elif method == 'minmax':
        return (data - data.min()) / (data.max() - data.min() + 1e-8)
    else:
        return data


def exponential_moving_average(data: np.ndarray, window: int) -> np.ndarray:
    """Calculate exponential moving average."""
    alpha = 2 / (window + 1)
    ema = np.zeros_like(data)
    ema[0] = data[0]
    
    for i in range(1, len(data)):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
    
    return ema


def calculate_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Calculate correlation coefficient."""
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    
    return np.corrcoef(x, y)[0, 1]


def calculate_beta(returns: np.ndarray, market_returns: np.ndarray) -> float:
    """Calculate beta."""
    if len(returns) != len(market_returns) or len(returns) == 0:
        return 1.0
    
    covariance = np.cov(returns, market_returns)[0, 1]
    market_variance = np.var(market_returns)
    
    if market_variance == 0:
        return 1.0
    
    return covariance / market_variance


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency amount."""
    return f"{currency} {amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format percentage."""
    return f"{value * 100:.2f}%"


def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp."""
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')


def parse_timeframe(timeframe: str) -> int:
    """Parse timeframe string to seconds."""
    mapping = {
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '4h': 14400,
        '1d': 86400,
        '1w': 604800
    }
    return mapping.get(timeframe, 3600)


def generate_order_id() -> str:
    """Generate unique order ID."""
    return f"order_{int(datetime.now().timestamp() * 1000)}"


def calculate_position_size(
    capital: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss_price: float
) -> float:
    """Calculate position size based on risk."""
    risk_amount = capital * risk_per_trade
    price_risk = abs(entry_price - stop_loss_price)
    
    if price_risk == 0:
        return 0.0
    
    return risk_amount / price_risk


def calculate_kelly_criterion(
    win_rate: float,
    avg_win: float,
    avg_loss: float
) -> float:
    """Calculate Kelly criterion for position sizing."""
    if avg_loss == 0:
        return 0.0
    
    win_loss_ratio = avg_win / abs(avg_loss)
    kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
    
    return max(0.0, min(kelly, 1.0))  # Clamp between 0 and 1


def resample_ohlcv(
    df: pd.DataFrame,
    timeframe: str
) -> pd.DataFrame:
    """Resample OHLCV data to different timeframe."""
    resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    return resampled.dropna()


def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Average True Range."""
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    atr = exponential_moving_average(tr, period)
    
    return atr


def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Relative Strength Index."""
    deltas = np.diff(prices)
    
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gains = exponential_moving_average(np.concatenate([[0], gains]), period)
    avg_losses = exponential_moving_average(np.concatenate([[0], losses]), period)
    
    rs = avg_gains / (avg_losses + 1e-8)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(
    prices: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> tuple:
    """Calculate MACD."""
    fast_ema = exponential_moving_average(prices, fast_period)
    slow_ema = exponential_moving_average(prices, slow_period)
    
    macd_line = fast_ema - slow_ema
    signal_line = exponential_moving_average(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: np.ndarray,
    period: int = 20,
    std_dev: float = 2.0
) -> tuple:
    """Calculate Bollinger Bands."""
    sma = np.convolve(prices, np.ones(period) / period, mode='same')
    std = np.array([prices[max(0, i-period):i+1].std() for i in range(len(prices))])
    
    upper_band = sma + std_dev * std
    lower_band = sma - std_dev * std
    
    return upper_band, sma, lower_band
