"""
Specialized Planner Agents - Integrated Trading Strategies

Ported from legacy agents 2/ layer to the unified Core Agent System.
Includes:
- TrendFollowingPlanner
- MeanReversionPlanner
- VolatilityPlanner
"""

import logging
from typing import Any, Dict, List, Optional
from .agent_registry import BaseAgent, AgentRole, AgentCapability

logger = logging.getLogger(__name__)

class TrendFollowingPlanner(BaseAgent):
    """Planner specialized in trend-following strategies."""

    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(
            agent_id=agent_id,
            name="TrendFollowingPlanner",
            role=AgentRole.PLANNER,
            config=config or {}
        )
        self.trend_threshold = self.config.get('trend_threshold', 0.01)

    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="trend_following",
            description="Analyze and propose trend-following trades",
            input_schema={"context": "SystemContext"},
            output_schema={"proposal": "Dict"}
        ))

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        operation = action.get('operation', 'propose')
        if operation == 'propose':
            return await self._generate_proposal(action.get('context'))
        return {'success': False, 'error': f"Unknown operation: {operation}"}

    async def _generate_proposal(self, context: Any) -> Dict[str, Any]:
        market_state = getattr(context, 'market_state', {})
        if not isinstance(market_state, dict):
            market_state = {}

        sma_20 = market_state.get('sma_20', 0)
        sma_50 = market_state.get('sma_50', 0)
        price = market_state.get('price', 0)
        macd = market_state.get('macd', 0)

        if sma_20 > sma_50 * (1 + self.trend_threshold) and price > sma_20 and macd > 0:
            return {
                'type': 'buy',
                'action': {'operation': 'open_long', 'size': 0.02},
                'confidence': 0.75,
                'reasoning': "Strong uptrend: SMA20 > SMA50, price above SMA20, MACD positive"
            }
        elif sma_20 < sma_50 * (1 - self.trend_threshold) and price < sma_20 and macd < 0:
            return {
                'type': 'sell',
                'action': {'operation': 'open_short', 'size': 0.02},
                'confidence': 0.75,
                'reasoning': "Strong downtrend: SMA20 < SMA50, price below SMA20, MACD negative"
            }

        return {
            'type': 'hold',
            'action': {'operation': 'no_action'},
            'confidence': 0.5,
            'reasoning': "No clear trend detected"
        }

class MeanReversionPlanner(BaseAgent):
    """Planner specialized in mean-reversion strategies."""

    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(
            agent_id=agent_id,
            name="MeanReversionPlanner",
            role=AgentRole.PLANNER,
            config=config or {}
        )
        self.oversold_threshold = self.config.get('oversold_threshold', 30)
        self.overbought_threshold = self.config.get('overbought_threshold', 70)

    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="mean_reversion",
            description="Analyze and propose mean-reversion trades",
            input_schema={"context": "SystemContext"},
            output_schema={"proposal": "Dict"}
        ))

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        operation = action.get('operation', 'propose')
        if operation == 'propose':
            return await self._generate_proposal(action.get('context'))
        return {'success': False, 'error': f"Unknown operation: {operation}"}

    async def _generate_proposal(self, context: Any) -> Dict[str, Any]:
        market_state = getattr(context, 'market_state', {})
        if not isinstance(market_state, dict):
            market_state = {}

        rsi = market_state.get('rsi', 50)
        price = market_state.get('price', 0)
        sma_20 = market_state.get('sma_20', price)

        deviation = abs(price - sma_20) / sma_20 if sma_20 > 0 else 0

        if rsi < self.oversold_threshold and deviation > 0.02:
            return {
                'type': 'buy',
                'action': {'operation': 'open_long', 'size': 0.015},
                'confidence': 0.7,
                'reasoning': f"Oversold (RSI={rsi:.1f}), {deviation:.1%} below mean"
            }
        elif rsi > self.overbought_threshold and deviation > 0.02:
            return {
                'type': 'sell',
                'action': {'operation': 'open_short', 'size': 0.015},
                'confidence': 0.7,
                'reasoning': f"Overbought (RSI={rsi:.1f}), {deviation:.1%} above mean"
            }

        return {
            'type': 'hold',
            'action': {'operation': 'no_action'},
            'confidence': 0.5,
            'reasoning': "No mean reversion opportunity"
        }

class VolatilityPlanner(BaseAgent):
    """Planner specialized in volatility breakout strategies."""

    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(
            agent_id=agent_id,
            name="VolatilityPlanner",
            role=AgentRole.PLANNER,
            config=config or {}
        )
        self.high_vol_threshold = self.config.get('high_vol_threshold', 2.0)

    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="volatility_trading",
            description="Analyze and propose volatility-based trades",
            input_schema={"context": "SystemContext"},
            output_schema={"proposal": "Dict"}
        ))

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        operation = action.get('operation', 'propose')
        if operation == 'propose':
            return await self._generate_proposal(action.get('context'))
        return {'success': False, 'error': f"Unknown operation: {operation}"}

    async def _generate_proposal(self, context: Any) -> Dict[str, Any]:
        market_state = getattr(context, 'market_state', {})
        if not isinstance(market_state, dict):
            market_state = {}

        volatility = market_state.get('volatility', 1.0)
        rsi = market_state.get('rsi', 50)
        macd = market_state.get('macd', 0)

        if volatility > self.high_vol_threshold:
            if rsi > 60 and macd > 0:
                return {
                    'type': 'buy',
                    'action': {'operation': 'open_long', 'size': 0.025},
                    'confidence': 0.8,
                    'reasoning': f"High volatility ({volatility:.2f}), bullish breakout"
                }
            elif rsi < 40 and macd < 0:
                return {
                    'type': 'sell',
                    'action': {'operation': 'open_short', 'size': 0.025},
                    'confidence': 0.8,
                    'reasoning': f"High volatility ({volatility:.2f}), bearish breakout"
                }

        return {
            'type': 'hold',
            'action': {'operation': 'no_action'},
            'confidence': 0.5,
            'reasoning': "Normal volatility or no clear breakout"
        }
