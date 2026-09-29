"""
GovernanceGate — compatibility adapter over the canonical Immutable Shield.

CANONICAL SHIELD: ``trading_bot.core.immutable_shield.ImmutableShield`` is the
single non-bypassable safety gate (registered voter on ``decision_bus``,
deterministic checks only). This module preserves the legacy
``GovernanceGate`` API (``validate`` / ``check_evolution_gate``) by delegating
to that shield — there is exactly one shield in the system.

Rules (unchanged semantics):
1. Immutability: safety decisions are made by the canonical shield, which no
   agent-editable module may replace.
2. Determinism: hard-coded limits / deterministic oracles only.
3. Monotone Safety: actions violating global risk bounds are blocked.
"""

import logging
from typing import Dict, Any

from trading_bot.core.immutable_shield import (
    ImmutableShield,
    GovernanceDecision,
    ShieldReport,
)

logger = logging.getLogger(__name__)


class GovernanceGate:
    """
    Legacy governance-gate interface delegating to the canonical
    ``ImmutableShield`` singleton.

    Keeps the original contract: ``validate()`` returns the (possibly
    clipped) action dict on approval, or ``{"type": "blocked", "reason": ...}``
    on veto.
    """

    def __init__(self, risk_config: Dict = None):
        self.risk_config = risk_config or {}
        self.max_exposure = self.risk_config.get('max_exposure', 0.1)
        self.max_drawdown_limit = self.risk_config.get('max_drawdown', 0.2)
        self.banned_symbols = self.risk_config.get('banned_symbols', [])
        # Feed legacy config keys into the canonical shield's config so its
        # deterministic checks see the same limits (banned_symbols → denylist).
        self._shield = ImmutableShield()
        merged = dict(self._shield.config)
        merged.setdefault('blocked_symbols', list(self.banned_symbols))
        if 'max_exposure' in self.risk_config:
            merged['max_exposure'] = self.max_exposure
        # Legacy action vocabulary must include exits — otherwise the
        # EXTREME_VOLATILITY "only exits permitted" rule can never pass.
        merged['allowed_actions'] = list(set(merged.get('allowed_actions', [])) | {
            'trade', 'TRADE_PROPOSAL', 'TRADE_EXECUTION',
            'exit', 'close', 'reduce', 'hedge', 'rebalance', 'hold', 'wait',
        })
        self._shield.config = merged

    async def validate(self, action: Dict) -> Dict:
        """
        Validates an action through the canonical shield.
        Returns the (possibly modified/clipped) action, or a blocked dict.
        """
        action_type = action.get('type', 'trade')
        params = dict(action.get('params', {}) or {})
        context = dict(action.get('context', {}) or {})

        logger.info(f"Shield: Validating action {action_type}")

        # Legacy semantics: oversized trades are CLIPPED, not rejected
        size = params.get('size')
        if action_type == 'trade' and isinstance(size, (int, float)) and size > self.max_exposure:
            logger.warning(f"Shield: Clipping exposure {size} -> {self.max_exposure}")
            params['size'] = self.max_exposure
            action['params'] = params
            action['shield_modified'] = True

        # Banned symbols: legacy contract blocks outright
        symbol = params.get('symbol')
        if symbol in self.banned_symbols:
            logger.critical(f"Shield: BLOCKING trade for banned symbol {symbol}")
            return {"type": "blocked", "reason": f"Symbol {symbol} is banned."}

        # Delegate remaining checks to the canonical shield
        report: ShieldReport = await self._shield.validate_action(
            action_type, params, context
        )
        if report.decision != GovernanceDecision.APPROVED:
            logger.critical(f"Shield: {report.decision.value} - {report.reason}")
            return {"type": "blocked", "reason": report.reason}

        return action

    def check_evolution_gate(self, current_perf: float, proposed_perf: float) -> bool:
        """Monotone Improvement Gate (RSEA) — delegated to the canonical shield."""
        return self._shield.check_evolution_gate(current_perf, proposed_perf)


__all__ = ["GovernanceGate", "ImmutableShield", "GovernanceDecision", "ShieldReport"]
