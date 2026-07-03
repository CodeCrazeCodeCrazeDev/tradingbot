"""
Legacy Orchestrator Adapter - Phase 1 Migration
==============================================

Provides a shim layer to maintain compatibility with legacy components
that expect the old TradingOrchestrator interface, while routing all
actual decisions through the new IntegratedAgentSystem (IAS).
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from trading_bot.core_agent_system import IntegratedAgentSystem
from trading_bot.core.orchestrator import TradingSignal, SignalType, Position

logger = logging.getLogger(__name__)


class LegacyOrchestratorAdapter:
    """
    Adapter that mimics TradingOrchestrator but uses IntegratedAgentSystem.
    """

    def __init__(self, ias: IntegratedAgentSystem, config: Dict[str, Any]):
        self.ias = ias
        self.config = config

        # Mimic legacy state
        self.positions: Dict[str, Position] = {}
        self.pending_signals: List[TradingSignal] = []
        self.trade_history: List[Dict[str, Any]] = []

        logger.info("LegacyOrchestratorAdapter initialized - routing to IAS")

    async def initialize(self):
        """No-op as IAS is already initialized by the main system"""
        pass

    async def generate_signal(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Route to IAS for signal generation"""
        task_desc = f"Analyze market for {symbol} and determine if a trade signal exists"
        context = {'symbol': symbol, 'market_data': market_data, 'legacy_mode': True}

        result = await self.ias.execute_task(task_desc, context)

        if result.get('success') and result.get('signal'):
            # Map IAS result back to legacy TradingSignal
            sig_data = result['signal']
            signal = TradingSignal(
                symbol=symbol,
                signal_type=SignalType(sig_data.get('type', 'hold').lower()),
                confidence=sig_data.get('confidence', 0.5),
                price=sig_data.get('price', market_data.get('price', 0)),
                timestamp=datetime.now(),
                reasons=[result.get('reasoning', 'Brain decision')]
            )
            return signal

        return None

    async def execute_signal(self, signal: TradingSignal) -> bool:
        """Route to IAS for trade execution"""
        task_desc = f"Execute trade signal: {signal.signal_type.value} {signal.symbol}"
        context = {
            'signal': {
                'symbol': signal.symbol,
                'type': signal.signal_type.value,
                'price': signal.price,
                'confidence': signal.confidence
            },
            'use_coordination': True
        }

        result = await self.ias.execute_task(task_desc, context)
        success = result.get('success', False)

        if success:
            # Update legacy position tracking (mimicry)
            if signal.signal_type == SignalType.BUY:
                self.positions[signal.symbol] = Position(
                    symbol=signal.symbol,
                    side='long',
                    entry_price=signal.price,
                    quantity=1.0, # Simplified
                    entry_time=datetime.now()
                )
            elif signal.signal_type == SignalType.SELL:
                if signal.symbol in self.positions:
                    del self.positions[signal.symbol]

        return success

    def get_portfolio_status(self) -> Dict[str, Any]:
        """Get status from IAS and map to legacy format"""
        status = self.ias.get_comprehensive_status()

        return {
            'mode': 'unified',
            'positions': len(self.positions),
            'ias_iteration': status.get('self_play', {}).get('iteration', 0),
            'brain_status': status.get('running'),
            'active_agents': status.get('agents', {}).get('total_agents', 0)
        }

    async def update_positions(self, market_data: Dict[str, Dict[str, Any]]):
        """Update mimic positions"""
        for symbol, position in self.positions.items():
            if symbol in market_data:
                position.current_price = market_data[symbol].get('price')

    async def shutdown(self):
        """No-op as IAS lifecycle is managed elsewhere"""
        pass
