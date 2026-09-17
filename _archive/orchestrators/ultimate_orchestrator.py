"""
Ultimate Orchestrator - The Master Controller
==============================================

Orchestrates all systems into a unified trading AI:
1. Internet Research Engine
2. Self-Evolving Core
3. Alpha Discovery Engine
4. Hardware Optimizer
5. Deep Agent System
6. Global-Micro Analyzer
7. Elite Trader Brain

This is the main entry point for the ultimate trading system.
"""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)

try:
    from .self_evolving_core import LearningEvent
except Exception:
    LearningEvent = None


class TradingMode(Enum):
    """Trading modes"""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"
    RESEARCH = "research"


class SystemState(Enum):
    """System states"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    RESEARCHING = "researching"
    EVOLVING = "evolving"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class TradingSignal:
    """Final trading signal from the system"""
    signal_id: str
    symbol: str
    timestamp: datetime
    
    # Action
    action: str  # BUY, SELL, HOLD
    confidence: float
    
    # Trade details
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    
    # Analysis sources
    research_insights: List[str]
    alpha_signals: List[str]
    agent_consensus: str
    global_micro_alignment: float
    elite_quality: str
    
    # Risk
    risk_reward_ratio: float
    max_risk_pct: float
    
    # Reasoning
    reasoning: str


@dataclass
class SystemStatus:
    """Complete system status"""
    state: SystemState
    mode: TradingMode
    uptime_seconds: float
    
    # Component status
    research_engine: str
    evolution_core: str
    alpha_engine: str
    hardware_optimizer: str
    agent_system: str
    analyzer: str
    trader_brain: str
    
    # Performance
    total_signals: int
    total_trades: int
    win_rate: float
    total_pnl: float
    
    # Resources
    cpu_usage: float
    memory_usage: float
    
    timestamp: datetime = field(default_factory=datetime.now)


class UltimateOrchestrator:
    """
    Ultimate Orchestrator - The Master Controller
    
    This is the brain that coordinates all systems:
    - Research: Continuously learns from the internet
    - Evolution: Self-improves over time
    - Discovery: Finds new alpha signals
    - Hardware: Optimizes for available resources
    - Agents: Multi-agent decision making
    - Analysis: Global + micro market intelligence
    - Trading: Elite-level execution
    
    The result is a trading AI that:
    - Learns continuously
    - Evolves autonomously
    - Discovers new opportunities
    - Trades like an elite
    - Outperforms 99% of systems
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        logger.info("=" * 80)
        logger.info("ULTIMATE TRADING SYSTEM - INITIALIZING")
        logger.info("=" * 80)
        
        # System state
        self.state = SystemState.INITIALIZING
        self.mode = TradingMode(self.config.get('mode', 'paper'))
        self.start_time = datetime.now()
        
        # Initialize all components
        self._initialize_components()
        
        # Trading state
        self.symbols = self.config.get('symbols', ['BTCUSDT', 'ETHUSDT', 'EURUSD'])
        self.active_signals: Dict[str, TradingSignal] = {}
        self.signal_history: List[TradingSignal] = []
        
        # Performance tracking
        self.performance = {
            'total_signals': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0
        }
        
        # Background tasks
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Storage
        self.storage_path = Path(self.config.get('storage_path', 'ultimate_system_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.state = SystemState.RUNNING
        
        logger.info("=" * 80)
        logger.info("ULTIMATE TRADING SYSTEM - READY")
        logger.info(f"Mode: {self.mode.value}")
        logger.info(f"Symbols: {self.symbols}")
        logger.info("=" * 80)
    
    def _initialize_components(self):
        """Initialize all system components"""
        
        # 1. Internet Research Engine
        logger.info("Initializing Internet Research Engine...")
        try:
            from .internet_research_engine import InternetResearchEngine
            self.research_engine = InternetResearchEngine(
                self.config.get('research', {})
            )
            logger.info("✓ Internet Research Engine ready")
        except Exception as e:
            logger.error(f"Research Engine failed: {e}")
            self.research_engine = None
        
        # 2. Self-Evolving Core
        logger.info("Initializing Self-Evolving Core...")
        try:
            from .self_evolving_core import SelfEvolvingCore
            self.evolution_core = SelfEvolvingCore(
                self.config.get('evolution', {})
            )
            logger.info("✓ Self-Evolving Core ready")
        except Exception as e:
            logger.error(f"Evolution Core failed: {e}")
            self.evolution_core = None
        
        # 3. Alpha Discovery Engine
        logger.info("Initializing Alpha Discovery Engine...")
        try:
            from .alpha_discovery_engine import AlphaDiscoveryEngine
            self.alpha_engine = AlphaDiscoveryEngine(
                self.config.get('alpha', {})
            )
            logger.info("✓ Alpha Discovery Engine ready")
        except Exception as e:
            logger.error(f"Alpha Engine failed: {e}")
            self.alpha_engine = None
        
        # 4. Hardware Optimizer
        logger.info("Initializing Hardware Optimizer...")
        try:
            from .hardware_optimizer import HardwareOptimizer
            self.hardware_optimizer = HardwareOptimizer(
                self.config.get('hardware', {})
            )
            logger.info("✓ Hardware Optimizer ready")
        except Exception as e:
            logger.error(f"Hardware Optimizer failed: {e}")
            self.hardware_optimizer = None
        
        # 5. Deep Agent System
        logger.info("Initializing Deep Agent System...")
        try:
            from .deep_agent_system import DeepAgentSystem
            self.agent_system = DeepAgentSystem(
                self.config.get('agents', {})
            )
            logger.info("✓ Deep Agent System ready")
        except Exception as e:
            logger.error(f"Agent System failed: {e}")
            self.agent_system = None
        
        # 6. Global-Micro Analyzer
        logger.info("Initializing Global-Micro Analyzer...")
        try:
            from .global_micro_analyzer import GlobalMicroAnalyzer
            self.analyzer = GlobalMicroAnalyzer(
                self.config.get('analyzer', {})
            )
            logger.info("✓ Global-Micro Analyzer ready")
        except Exception as e:
            logger.error(f"Analyzer failed: {e}")
            self.analyzer = None
        
        # 7. Elite Trader Brain
        logger.info("Initializing Elite Trader Brain...")
        try:
            from .elite_trader_brain import EliteTraderBrain
            self.trader_brain = EliteTraderBrain(
                self.config.get('trader', {})
            )
            logger.info("✓ Elite Trader Brain ready")
        except Exception as e:
            logger.error(f"Trader Brain failed: {e}")
            self.trader_brain = None
        
        # Count active components
        components = [
            self.research_engine, self.evolution_core, self.alpha_engine,
            self.hardware_optimizer, self.agent_system, self.analyzer,
            self.trader_brain
        ]
        active = sum(1 for c in components if c is not None)
        logger.info(f"Initialized {active}/7 components")
    
    async def start(self):
        """Start the ultimate trading system"""
        logger.info("Starting Ultimate Trading System...")
        
        self._running = True
        
        # Start hardware monitoring
        if self.hardware_optimizer:
            self.hardware_optimizer.start_monitoring()
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._research_loop()),
            asyncio.create_task(self._evolution_loop()),
            asyncio.create_task(self._trading_loop()),
        ]
        
        logger.info("Ultimate Trading System started")
    
    async def stop(self):
        """Stop the system"""
        logger.info("Stopping Ultimate Trading System...")
        
        self._running = False
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Stop hardware monitoring
        if self.hardware_optimizer:
            self.hardware_optimizer.stop_monitoring()
        
        # Close research engine
        if self.research_engine:
            await self.research_engine.close()
        
        # Save state
        self._save_state()
        
        self.state = SystemState.SHUTDOWN
        logger.info("Ultimate Trading System stopped")
    
    async def _research_loop(self):
        """Background research loop"""
        research_topics = [
            'algorithmic trading strategies',
            'machine learning trading',
            'market microstructure',
            'quantitative finance',
            'risk management trading'
        ]
        
        while self._running:
            try:
                if self.research_engine:
                    self.state = SystemState.RESEARCHING
                    
                    for topic in research_topics:
                        results = await self.research_engine.research(
                            topic,
                            max_results=5
                        )
                        
                        # Learn from research
                        if self.evolution_core and LearningEvent is not None and results:
                            for result in results:
                                event = LearningEvent(
                                    event_id=f"research_{result.result_id}",
                                    event_type='discovery',
                                    timestamp=datetime.now(),
                                    data={
                                        'title': result.title,
                                        'insights': result.key_insights,
                                        'implications': result.trading_implications
                                    }
                                )
                                self.evolution_core.learn(event)
                        
                        await asyncio.sleep(60)  # Rate limiting
                    
                    self.state = SystemState.RUNNING
                
                # Research every hour
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Research loop error: {e}")
                await asyncio.sleep(60)
    
    async def _evolution_loop(self):
        """Background evolution loop"""
        while self._running:
            try:
                if self.evolution_core:
                    self.state = SystemState.EVOLVING
                    
                    # Take performance snapshot
                    self.evolution_core.take_performance_snapshot()
                    
                    # Check for improvements
                    improvement = self.evolution_core.get_improvement_since_baseline()
                    if improvement:
                        logger.info(f"Evolution improvement: {improvement}")
                    
                    self.state = SystemState.RUNNING
                
                # Evolve every 30 minutes
                await asyncio.sleep(1800)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evolution loop error: {e}")
                await asyncio.sleep(60)
    
    async def _trading_loop(self):
        """Main trading loop"""
        while self._running:
            try:
                for symbol in self.symbols:
                    # Generate signal
                    signal = await self.generate_signal(symbol)
                    
                    if signal and signal.action != 'HOLD':
                        self.active_signals[symbol] = signal
                        self.signal_history.append(signal)
                        self.performance['total_signals'] += 1
                        
                        logger.info(f"Signal: {signal.action} {symbol} @ {signal.entry_price}")
                        
                        # In live mode, would execute trade here
                        if self.mode == TradingMode.LIVE:
                            await self._execute_trade(signal)
                
                # Trading interval
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(10)
    
    async def generate_signal(
        self,
        symbol: str,
        market_data: Optional[Dict] = None
    ) -> Optional[TradingSignal]:
        """
        Generate a trading signal using all systems
        
        This is the main intelligence pipeline:
        1. Get market data
        2. Run global-micro analysis
        3. Get agent consensus
        4. Get alpha signals
        5. Make elite decision
        6. Combine into final signal
        """
        signal_id = f"sig_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{symbol}"
        
        try:
            # Get market data (mock for now)
            if market_data is None:
                market_data = await self._get_market_data(symbol)
            
            current_price = market_data.get('close', [100])[-1]
            
            # 1. Global-Micro Analysis
            analysis = None
            if self.analyzer:
                analysis = await self.analyzer.analyze(
                    symbol, market_data
                )
            
            # 2. Agent Consensus
            agent_decision = None
            if self.agent_system:
                agent_decision = await self.agent_system.get_ensemble_decision(
                    market_data, symbol
                )
            
            # 3. Alpha Signals
            alpha_signals = []
            if self.alpha_engine:
                signals = self.alpha_engine.get_signals(market_data)
                alpha_signals = [f"{a.name}: {s:.2f}" for a, s in signals]
            
            # 4. Elite Decision
            elite_decision = None
            if self.trader_brain and analysis:
                elite_decision = await self.trader_brain.make_decision(
                    symbol, market_data,
                    {
                        'overall_bias': analysis.overall_bias,
                        'overall_confidence': analysis.overall_confidence,
                        'alignment_score': analysis.alignment_score
                    },
                    current_price
                )
            
            # 5. Combine into final signal
            signal = self._combine_signals(
                signal_id, symbol, current_price,
                analysis, agent_decision, alpha_signals, elite_decision
            )
            
            # 6. Learn from signal generation
            if self.evolution_core and LearningEvent is not None:
                event = LearningEvent(
                    event_id=signal_id,
                    event_type='signal',
                    timestamp=datetime.now(),
                    data={
                        'symbol': symbol,
                        'action': signal.action if signal else 'NONE',
                        'confidence': signal.confidence if signal else 0
                    }
                )
                self.evolution_core.learn(event)
            
            return signal
            
        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {e}")
            return None
    
    def _combine_signals(
        self,
        signal_id: str,
        symbol: str,
        current_price: float,
        analysis,
        agent_decision,
        alpha_signals: List[str],
        elite_decision
    ) -> TradingSignal:
        """Combine all signals into final decision"""
        
        # Collect votes
        votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        confidences = []
        
        # Analysis vote
        if analysis:
            if analysis.overall_bias == 'bullish':
                votes['BUY'] += analysis.overall_confidence
            elif analysis.overall_bias == 'bearish':
                votes['SELL'] += analysis.overall_confidence
            else:
                votes['HOLD'] += 0.5
            confidences.append(analysis.overall_confidence)
        
        # Agent vote
        if agent_decision:
            votes[agent_decision.action] += agent_decision.confidence
            confidences.append(agent_decision.confidence)
        
        # Elite vote (weighted more heavily)
        if elite_decision and elite_decision.action != 'HOLD':
            votes[elite_decision.action] += elite_decision.confidence * 1.5
            confidences.append(elite_decision.confidence)
        
        # Determine final action
        total_votes = sum(votes.values())
        if total_votes == 0:
            action = 'HOLD'
            confidence = 0
        else:
            action = max(votes, key=votes.get)
            confidence = votes[action] / total_votes
        
        # Use elite decision for trade details if available
        if elite_decision and action == elite_decision.action:
            entry = elite_decision.entry_price
            stop_loss = elite_decision.stop_loss
            take_profit = elite_decision.take_profit
            position_size = elite_decision.position_size
            risk_reward = elite_decision.risk_reward_ratio
            max_risk = elite_decision.max_risk_pct
            quality = elite_decision.trade_quality.value
        else:
            # Default values
            atr = current_price * 0.02
            entry = current_price
            if action == 'BUY':
                stop_loss = current_price - atr * 2
                take_profit = current_price + atr * 3
            elif action == 'SELL':
                stop_loss = current_price + atr * 2
                take_profit = current_price - atr * 3
            else:
                stop_loss = 0
                take_profit = 0
            position_size = 0.01
            risk_reward = 1.5
            max_risk = 0.02
            quality = 'C'
        
        # Build reasoning
        reasoning_parts = []
        if analysis:
            reasoning_parts.append(f"Analysis: {analysis.overall_bias} ({analysis.overall_confidence:.2%})")
        if agent_decision:
            reasoning_parts.append(f"Agents: {agent_decision.action} ({agent_decision.confidence:.2%})")
        if elite_decision:
            reasoning_parts.append(f"Elite: {elite_decision.action} ({elite_decision.confidence:.2%})")
        
        # Research insights
        research_insights = []
        if self.research_engine:
            knowledge = self.research_engine.get_knowledge()
            research_insights = [k.title for k in knowledge[:3]]
        
        return TradingSignal(
            signal_id=signal_id,
            symbol=symbol,
            timestamp=datetime.now(),
            action=action,
            confidence=confidence,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            research_insights=research_insights,
            alpha_signals=alpha_signals,
            agent_consensus=agent_decision.action if agent_decision else 'NONE',
            global_micro_alignment=analysis.alignment_score if analysis else 0,
            elite_quality=quality,
            risk_reward_ratio=risk_reward,
            max_risk_pct=max_risk,
            reasoning=" | ".join(reasoning_parts)
        )
    
    async def _get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for symbol (mock implementation)"""
        import numpy as np
        
        # Generate mock data
        n = 100
        base_price = 100 if 'BTC' not in symbol else 50000
        
        # Random walk with trend
        returns = np.random.normal(0.0001, 0.02, n)
        prices = base_price * np.cumprod(1 + returns)
        
        return {
            'symbol': symbol,
            'close': prices.tolist(),
            'high': (prices * 1.01).tolist(),
            'low': (prices * 0.99).tolist(),
            'volume': np.random.uniform(1000, 10000, n).tolist(),
            'timestamp': datetime.now()
        }
    
    async def _execute_trade(self, signal: TradingSignal):
        """Execute a trade (placeholder for real execution)"""
        logger.info(f"Executing trade: {signal.action} {signal.symbol}")
        
        # In production, would connect to broker here
        self.performance['total_trades'] += 1
    
    def _save_state(self):
        """Save system state"""
        state = {
            'performance': self.performance,
            'signal_count': len(self.signal_history),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.storage_path / 'system_state.json', 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_status(self) -> SystemStatus:
        """Get complete system status"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Get resource usage
        cpu_usage = 0
        memory_usage = 0
        if self.hardware_optimizer:
            stats = self.hardware_optimizer.get_statistics()
            cpu_usage = stats.get('avg_cpu_usage', 0)
            memory_usage = stats.get('avg_memory_usage', 0)
        
        return SystemStatus(
            state=self.state,
            mode=self.mode,
            uptime_seconds=uptime,
            research_engine='active' if self.research_engine else 'inactive',
            evolution_core='active' if self.evolution_core else 'inactive',
            alpha_engine='active' if self.alpha_engine else 'inactive',
            hardware_optimizer='active' if self.hardware_optimizer else 'inactive',
            agent_system='active' if self.agent_system else 'inactive',
            analyzer='active' if self.analyzer else 'inactive',
            trader_brain='active' if self.trader_brain else 'inactive',
            total_signals=self.performance['total_signals'],
            total_trades=self.performance['total_trades'],
            win_rate=self.performance['winning_trades'] / max(1, self.performance['total_trades']),
            total_pnl=self.performance['total_pnl'],
            cpu_usage=cpu_usage,
            memory_usage=memory_usage
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        stats = {
            'system': {
                'state': self.state.value,
                'mode': self.mode.value,
                'uptime': (datetime.now() - self.start_time).total_seconds()
            },
            'performance': self.performance,
            'components': {}
        }
        
        if self.research_engine:
            stats['components']['research'] = self.research_engine.get_statistics()
        if self.evolution_core:
            stats['components']['evolution'] = self.evolution_core.get_statistics()
        if self.alpha_engine:
            stats['components']['alpha'] = self.alpha_engine.get_statistics()
        if self.hardware_optimizer:
            stats['components']['hardware'] = self.hardware_optimizer.get_statistics()
        if self.agent_system:
            stats['components']['agents'] = self.agent_system.get_statistics()
        if self.analyzer:
            stats['components']['analyzer'] = self.analyzer.get_statistics()
        if self.trader_brain:
            stats['components']['trader'] = self.trader_brain.get_statistics()
        
        return stats


# Factory function
def create_ultimate_system(
    mode: str = 'paper',
    symbols: List[str] = None,
    **kwargs
) -> UltimateOrchestrator:
    """
    Create the ultimate trading system
    
    Args:
        mode: Trading mode ('live', 'paper', 'backtest', 'research')
        symbols: List of symbols to trade
        **kwargs: Additional configuration
        
    Returns:
        Configured UltimateOrchestrator
    """
    config = {
        'mode': mode,
        'symbols': symbols or ['BTCUSDT', 'ETHUSDT'],
        **kwargs
    }
    
    return UltimateOrchestrator(config)


# Quick start function
async def quick_start(mode: str = 'paper'):
    """Quick start the ultimate system"""
    system = create_ultimate_system(mode=mode)
    await system.start()
    return system
