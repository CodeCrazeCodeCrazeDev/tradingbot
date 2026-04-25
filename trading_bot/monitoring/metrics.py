"""
Metrics Collection for Prometheus
Centralized metrics for monitoring and alerting
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from functools import wraps
from typing import Callable, Any
import time


# =============================================================================
# Registry
# =============================================================================

REGISTRY = CollectorRegistry()


# =============================================================================
# Trading Metrics
# =============================================================================

# Signal Metrics
SIGNALS_GENERATED = Counter(
    'trading_bot_signals_generated_total',
    'Total number of signals generated',
    ['strategy', 'symbol', 'direction'],
    registry=REGISTRY
)

SIGNAL_GENERATION_LATENCY = Histogram(
    'trading_bot_signal_generation_duration_seconds',
    'Time spent generating signals',
    ['strategy'],
    buckets=[.001, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10],
    registry=REGISTRY
)

# Order Metrics
ORDERS_PLACED = Counter(
    'trading_bot_orders_placed_total',
    'Total number of orders placed',
    ['symbol', 'side', 'order_type'],
    registry=REGISTRY
)

ORDERS_FILLED = Counter(
    'trading_bot_orders_filled_total',
    'Total number of orders filled',
    ['symbol', 'side'],
    registry=REGISTRY
)

ORDERS_CANCELLED = Counter(
    'trading_bot_orders_cancelled_total',
    'Total number of orders cancelled',
    ['symbol'],
    registry=REGISTRY
)

ORDER_EXECUTION_LATENCY = Histogram(
    'trading_bot_order_execution_duration_seconds',
    'Time from order placement to fill',
    ['symbol', 'order_type'],
    buckets=[.001, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5],
    registry=REGISTRY
)

# Trade Metrics
TRADES_EXECUTED = Counter(
    'trading_bot_trades_executed_total',
    'Total number of trades executed',
    ['symbol', 'side', 'strategy'],
    registry=REGISTRY
)

TRADE_PNL = Gauge(
    'trading_bot_trade_pnl',
    'Profit/loss from individual trades',
    ['symbol', 'trade_id'],
    registry=REGISTRY
)

# Position Metrics
OPEN_POSITIONS = Gauge(
    'trading_bot_open_positions',
    'Current number of open positions',
    ['symbol', 'direction'],
    registry=REGISTRY
)

POSITION_SIZE = Gauge(
    'trading_bot_position_size',
    'Size of current positions',
    ['symbol'],
    registry=REGISTRY
)

POSITION_UNREALIZED_PNL = Gauge(
    'trading_bot_position_unrealized_pnl',
    'Unrealized PnL of open positions',
    ['symbol'],
    registry=REGISTRY
)

# Portfolio Metrics
PORTFOLIO_VALUE = Gauge(
    'trading_bot_portfolio_value',
    'Total portfolio value',
    registry=REGISTRY
)

PORTFOLIO_EXPOSURE = Gauge(
    'trading_bot_portfolio_exposure',
    'Current portfolio exposure by symbol',
    ['symbol'],
    registry=REGISTRY
)

DAILY_PNL = Gauge(
    'trading_bot_daily_pnl',
    'Daily profit/loss',
    registry=REGISTRY
)

DRAWDOWN_PERCENT = Gauge(
    'trading_bot_drawdown_percent',
    'Current drawdown percentage',
    registry=REGISTRY
)

# =============================================================================
# Risk Metrics
# =============================================================================

RISK_CHECK_PASSED = Counter(
    'trading_bot_risk_checks_passed_total',
    'Number of risk checks passed',
    ['check_type'],
    registry=REGISTRY
)

RISK_CHECK_FAILED = Counter(
    'trading_bot_risk_checks_failed_total',
    'Number of risk checks failed',
    ['check_type'],
    registry=REGISTRY
)

MARGIN_LEVEL = Gauge(
    'trading_bot_margin_level',
    'Current margin level percentage',
    registry=REGISTRY
)

RISK_VIOLATIONS = Counter(
    'trading_bot_risk_violations_total',
    'Total risk limit violations',
    ['violation_type'],
    registry=REGISTRY
)

# =============================================================================
# System Metrics
# =============================================================================

REQUEST_COUNT = Counter(
    'trading_bot_requests_total',
    'Total requests handled',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'trading_bot_request_duration_seconds',
    'Request handling duration',
    ['method', 'endpoint'],
    registry=REGISTRY
)

ERRORS_TOTAL = Counter(
    'trading_bot_errors_total',
    'Total errors',
    ['error_type', 'component'],
    registry=REGISTRY
)

DATABASE_CONNECTION_STATUS = Gauge(
    'trading_bot_database_connection_status',
    'Database connection status (1=connected, 0=disconnected)',
    registry=REGISTRY
)

BROKER_CONNECTION_STATUS = Gauge(
    'trading_bot_broker_connected',
    'Broker connection status (1=connected, 0=disconnected)',
    ['broker_name'],
    registry=REGISTRY
)

# =============================================================================
# ML Metrics
# =============================================================================

ML_PREDICTION_LATENCY = Histogram(
    'trading_bot_ml_prediction_duration_seconds',
    'ML model prediction time',
    ['model_name'],
    registry=REGISTRY
)

ML_MODEL_ACCURACY = Gauge(
    'trading_bot_ml_model_accuracy',
    'Current model accuracy',
    ['model_name'],
    registry=REGISTRY
)

ML_PREDICTIONS_TOTAL = Counter(
    'trading_bot_ml_predictions_total',
    'Total predictions made',
    ['model_name', 'prediction_class'],
    registry=REGISTRY
)

# =============================================================================
# Decorators
# =============================================================================

def measure_latency(histogram: Histogram, labels: dict = None):
    """Decorator to measure function execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)
        return wrapper
    return decorator


def count_calls(counter: Counter, labels: dict = None):
    """Decorator to count function calls."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if labels:
                    counter.labels(**labels).inc()
                else:
                    counter.inc()
                return result
            except Exception as e:
                if labels:
                    counter.labels(**labels).inc()
                else:
                    counter.inc()
                raise e
        return wrapper
    return decorator


# =============================================================================
# Metrics Update Functions
# =============================================================================

def update_position_metrics(symbol: str, direction: str, size: float, unrealized_pnl: float):
    """Update position-related metrics."""
    OPEN_POSITIONS.labels(symbol=symbol, direction=direction).set(1)
    POSITION_SIZE.labels(symbol=symbol).set(size)
    POSITION_UNREALIZED_PNL.labels(symbol=symbol).set(unrealized_pnl)


def update_trade_metrics(symbol: str, side: str, strategy: str, pnl: float, trade_id: str):
    """Update trade execution metrics."""
    TRADES_EXECUTED.labels(symbol=symbol, side=side, strategy=strategy).inc()
    TRADE_PNL.labels(symbol=symbol, trade_id=trade_id).set(pnl)


def update_risk_metrics(check_type: str, passed: bool):
    """Update risk check metrics."""
    if passed:
        RISK_CHECK_PASSED.labels(check_type=check_type).inc()
    else:
        RISK_CHECK_FAILED.labels(check_type=check_type).inc()


def update_portfolio_metrics(portfolio_value: float, daily_pnl: float, drawdown: float):
    """Update portfolio-level metrics."""
    PORTFOLIO_VALUE.set(portfolio_value)
    DAILY_PNL.set(daily_pnl)
    DRAWDOWN_PERCENT.set(drawdown)


def set_connection_status(connected: bool, broker_name: str = 'default'):
    """Set broker connection status."""
    BROKER_CONNECTION_STATUS.labels(broker_name=broker_name).set(1 if connected else 0)


def set_database_status(connected: bool):
    """Set database connection status."""
    DATABASE_CONNECTION_STATUS.set(1 if connected else 0)


def record_error(error_type: str, component: str):
    """Record an error occurrence."""
    ERRORS_TOTAL.labels(error_type=error_type, component=component).inc()


def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record an HTTP request."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def get_metrics():
    """Get current metrics in Prometheus format."""
    return generate_latest(REGISTRY)


def get_metrics_content_type():
    """Get content type for metrics endpoint."""
    return CONTENT_TYPE_LATEST
