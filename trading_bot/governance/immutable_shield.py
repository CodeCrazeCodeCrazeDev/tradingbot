import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class GovernanceGate:
    """
    The Immutable Shield.
    Non-bypassable safety and compliance layer.

    Source: Reward Hacking in Autonomous Agents / AlphaAlgo Redesign Stage 6.

    Rules:
    1. Immutability: This module must not be editable by any agent.
    2. Determinism: Safety checks must rely on verified hard-coded limits or
       deterministic oracles, not LLM reasoning.
    3. Monotone Safety: Blocks any action that violates global risk bounds.
    """

    def __init__(self, risk_config: Dict):
        self.risk_config = risk_config
        self.max_exposure = risk_config.get('max_exposure', 0.1) # 10% max
        self.max_drawdown_limit = risk_config.get('max_drawdown', 0.2)
        self.banned_symbols = risk_config.get('banned_symbols', [])

    async def validate(self, action: Dict) -> Dict:
        """
        Validates an action against institutional risk bounds.
        Returns the (possibly modified/clipped) action or raises a SafetyViolation.
        """
        logger.info(f"Shield: Validating action {action.get('type')}")

        # 1. Hard Exposure Checks
        if action.get('type') == 'trade':
            size = action['params'].get('size', 0)
            if size > self.max_exposure:
                logger.warning(f"Shield: Clipping exposure {size} -> {self.max_exposure}")
                action['params']['size'] = self.max_exposure
                action['shield_modified'] = True

        # 2. Banned Assets
        symbol = action.get('params', {}).get('symbol')
        if symbol in self.banned_symbols:
            logger.critical(f"Shield: BLOCKING trade for banned symbol {symbol}")
            return {"type": "blocked", "reason": f"Symbol {symbol} is banned."}

        # 3. Regime-based Veto
        # If the market is in 'CRASH' regime, only allow 'EXIT' actions
        market_regime = action.get('context', {}).get('regime')
        if market_regime == 'EXTREME_VOLATILITY' and action.get('type') != 'exit':
            logger.critical("Shield: VETO - Market in Extreme Volatility. Only exits permitted.")
            return {"type": "blocked", "reason": "Extreme Volatility Veto."}

        return action

    def check_evolution_gate(self, current_perf: float, proposed_perf: float) -> bool:
        """
        Monotone Improvement Gate (RSEA).
        Only allow self-improvement if it passes a strict gain metric on held-out data.
        """
        gain_threshold = 0.02 # 2% minimum improvement
        if proposed_perf > current_perf + gain_threshold:
            logger.info(f"Evolution Gate: PASS (Gain: {proposed_perf - current_perf:.4f})")
            return True
        logger.warning(f"Evolution Gate: REJECT (Insufficient Gain: {proposed_perf - current_perf:.4f})")
        return False
