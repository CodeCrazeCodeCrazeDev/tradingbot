"""
Optional compatibility shim forwarding legacy imports to trading_bot.risk_management.
"""

from trading_bot.risk_management.risk_engine import RiskEngine
from trading_bot.risk_management.portfolio_manager import PortfolioManager

__all__ = [
    'RiskEngine',
    'PortfolioManager'
]
