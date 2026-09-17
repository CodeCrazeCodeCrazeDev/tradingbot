"""
Backward-compatibility delegation shim for risk_management.
DEPRECATED: Use trading_bot.risk_management instead.
"""

import warnings

warnings.warn(
    "Importing from 'risk_management' is deprecated and scheduled for removal in v3.0. "
    "Please update your imports to use 'trading_bot.risk_management' instead.",
    DeprecationWarning,
    stacklevel=2
)

from trading_bot.risk_management import (
    PortfolioManager,
    RiskEngine,
    RiskManagementOrchestrator,
)

__all__ = [
    'PortfolioManager',
    'RiskEngine',
    'RiskManagementOrchestrator',
]
