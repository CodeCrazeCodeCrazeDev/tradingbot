"""Deployment module for multi-symbol and scaling."""

from trading_bot.deployment.multi_symbol_manager import (
    MultiSymbolManager,
    LoadBalancer,
    HorizontalScaler
)

__all__ = [
    'MultiSymbolManager',
    'LoadBalancer',
    'HorizontalScaler'
]
