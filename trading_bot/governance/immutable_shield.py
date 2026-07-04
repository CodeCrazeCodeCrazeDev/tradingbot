"""
Immutable Shield - UCA-2026 Governance Gate

Provides a non-bypassable safety layer that enforces hard risk limits
and compliance rules, independent of the agentic reasoning brain (CSC).
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RiskLimit:
    max_exposure: float
    max_drawdown: float
    max_concentration: float
    forbidden_assets: List[str]

class ImmutableShield:
    """
    The 'Immutable Shield' (Governance Gate).
    This layer is deterministic and cannot be modified by autonomous agents.
    """

    def __init__(self, limits: Optional[RiskLimit] = None):
        self.limits = limits or RiskLimit(
            max_exposure=1.0, # 100% of equity
            max_drawdown=0.2, # 20% max
            max_concentration=0.25, # 25% in one asset
            forbidden_assets=['USDT', 'LUNA'] # Example restrictions
        )
        logger.info("UCA-2026 Immutable Shield initialized.")

    def validate_trade(self, trade_request: Dict[str, Any], current_portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates a trade request against immutable institutional bounds.
        Returns a result dictionary with 'approved' status and 'violations'.
        """
        violations = []
        symbol = trade_request.get('symbol')
        size = trade_request.get('size', 0)

        # 1. Asset Restriction check
        if symbol in self.limits.forbidden_assets:
            violations.append(f"FORBIDDEN_ASSET: {symbol} is restricted by institutional policy.")

        # 2. Exposure check
        current_exposure = current_portfolio.get('exposure', 0)
        new_exposure = current_exposure + size
        if new_exposure > self.limits.max_exposure:
            violations.append(f"EXPOSURE_LIMIT: New exposure {new_exposure:.2f} exceeds limit {self.limits.max_exposure}.")

        # 3. Concentration check
        asset_exposure = current_portfolio.get('assets', {}).get(symbol, 0) + size
        if asset_exposure > self.limits.max_concentration:
            violations.append(f"CONCENTRATION_LIMIT: Concentration in {symbol} ({asset_exposure:.2f}) exceeds limit.")

        is_approved = len(violations) == 0

        if not is_approved:
            logger.critical(f"SHIELD_BLOCK: Trade {symbol} REJECTED. Violations: {violations}")
        else:
            logger.info(f"SHIELD_PASS: Trade {symbol} validated.")

        return {
            'approved': is_approved,
            'violations': violations,
            'shield_version': 'UCA-2026-v1'
        }
