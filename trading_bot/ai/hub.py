"""
MetaTrader Alpha Superintelligence Hub (MTASH)
==============================================
The primary intelligence hub for the AlphaAlgo Trading Bot.

MTASH unifies tactical real-time tuning, strategic autonomous research,
and high-level multi-agent orchestration into a single coherent AI system.

Architectural Patterns:
- DeepMind AlphaGo (Policy/Value Networks)
- OpenAI GPT-4 (ReAct Reasoning Loops)
- Anthropic Constitutional AI (Safety Gates)
- Systems AI (Decision Attribution & Memory Hierarchy)
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .autonomous_tuner import AutonomousTuner
from .self_optimizer import AIOptimizer
from ..systems_ai.orchestrator import SystemsAIOrchestrator, SystemConfig, SystemMode
from ..autonomous_superintelligence.superintelligence_orchestrator import AutonomousSuperintelligence
from ..core_agent_system.integrated_system import IntegratedAgentSystem

logger = logging.getLogger(__name__)

class MTASH:
    """
    MetaTrader Alpha Superintelligence Hub.
    The 'Master Brain' of the AlphaAlgo system.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Tactical AI (Real-time tuning)
        self.tuner = AutonomousTuner()
        self.optimizer = AIOptimizer()

        # Systems AI (Advanced Attribution & Memory)
        mode_str = self.config.get('mode', 'paper')
        try:
            mode = SystemMode(mode_str)
        except ValueError:
            mode = SystemMode.PAPER

        self.systems_ai = SystemsAIOrchestrator(
            SystemConfig(mode=mode)
        )

        # Strategic AI (Autonomous Research & Discovery)
        self.superintelligence = AutonomousSuperintelligence({
            'total_capital': self.config.get('total_capital', 100000.0),
            'max_agents': self.config.get('max_agents', 50),
            'safety_enabled': self.config.get('safety_enabled', True),
        })

        # Agent AI (Hierarchical Coordination)
        self.agent_system = IntegratedAgentSystem({
            'storage_path': 'core_agent_data',
            'safety_threshold': self.config.get('safety_threshold', 0.7)
        })

        self.initialized = False
        self.running = False
        logger.info("MTASH: MetaTrader Alpha Superintelligence Hub initialized")

    async def initialize(self):
        """Initialize all intelligence layers."""
        logger.info("MTASH: Awakening all intelligence layers...")

        # Initialize in order of dependency
        await self.systems_ai.initialize()
        await self.superintelligence.initialize()
        await self.agent_system.initialize()

        self.initialized = True
        logger.info("MTASH: All systems initialized and ready")

    async def start(self):
        """Start the hub's autonomous loops."""
        if not self.initialized:
            await self.initialize()

        self.running = True
        logger.info("MTASH: Starting autonomous operations")

        # Start background loops
        asyncio.create_task(self.superintelligence.start())
        asyncio.create_task(self.agent_system.start())

        logger.info("MTASH: Hub is now active")

    async def think(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Primary decision-making entry point.
        Combines tactical tuning with strategic analysis.
        """
        # 1. System AI Signal Generation (with Attribution)
        from ..systems_ai.orchestrator import SignalRequest
        request = SignalRequest(
            request_id=f"mtash_{datetime.now().timestamp()}",
            symbol=symbol,
            timestamp=datetime.now(),
            features=market_data
        )

        signal = self.systems_ai.generate_signal(request)

        # 2. Agent System Verification (Constitutional Safety)
        task_description = f"Verify {signal.direction} signal for {symbol} with confidence {signal.confidence}"
        verification = await self.agent_system.execute_task(
            task_description,
            context={'signal': signal.__dict__, 'market_data': market_data}
        )

        # 3. Tactical Parameter Injection
        tuned_params = self.tuner.tune_all_parameters(signal.confidence)

        return {
            'signal': signal,
            'verification': verification,
            'params': tuned_params,
            'timestamp': datetime.now().isoformat()
        }

    async def record_outcome(self, outcome_data: Dict[str, Any]):
        """Record trade outcome for learning across all systems."""
        # Update Tactical Tuner
        self.tuner.tune_all_parameters(outcome_data.get('pnl', 0))

        # Update Systems AI (Attribution & Improvements)
        self.systems_ai.record_outcome(
            signal_id=outcome_data.get('signal_id'),
            direction_correct=outcome_data.get('success', False),
            pnl=outcome_data.get('pnl', 0),
            pnl_percent=outcome_data.get('pnl_pct', 0),
            slippage=outcome_data.get('slippage', 0),
            execution_quality=outcome_data.get('execution_quality', 1.0)
        )

        # Feed back to Optimizer
        from .self_optimizer import PerformanceMetrics
        metrics = PerformanceMetrics(
            sharpe_ratio=outcome_data.get('sharpe', 0),
            win_rate=outcome_data.get('win_rate', 0),
            profit_factor=outcome_data.get('profit_factor', 0),
            max_drawdown=outcome_data.get('drawdown', 0),
            total_trades=outcome_data.get('total_trades', 1),
            avg_profit=outcome_data.get('avg_profit', 0),
            avg_loss=outcome_data.get('avg_loss', 0),
            timestamp=datetime.now()
        )
        self.optimizer.add_performance_data(metrics)

        if self.optimizer.should_optimize():
            self.optimizer.run_optimization_cycle()

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the entire Superintelligence Hub."""
        return {
            'hub_running': self.running,
            'systems_ai': self.systems_ai.get_system_status(),
            'superintelligence': await self.superintelligence.get_comprehensive_status() if self.running else {},
            'tuner': self.tuner.get_tuning_summary(),
            'optimizer': self.optimizer.get_optimization_summary()
        }

    async def shutdown(self):
        """Shutdown the hub gracefully."""
        logger.info("MTASH: Shutting down...")
        self.running = False

        # Shutdown in parallel
        shutdown_tasks = [
            self.systems_ai.shutdown(),
            self.superintelligence.shutdown()
        ]

        # Add agent system shutdown if method exists
        if hasattr(self.agent_system, 'shutdown'):
            shutdown_tasks.append(self.agent_system.shutdown())

        await asyncio.gather(*shutdown_tasks)
        logger.info("MTASH: Shutdown complete")

def create_hub(config: Optional[Dict] = None) -> MTASH:
    """Factory function to create the MTASH Hub."""
    return MTASH(config)
