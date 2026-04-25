"""
Hivemind Coordinator - Main Orchestrator
============================================================

The central coordinator that manages all swarms, facilitates
consensus, and produces collective trading decisions.
"""

import logging
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from .core import (
    HiveNode,
    NodeType,
    NodeVote,
    SwarmSignal,
    CollectiveDecision,
    SignalDirection,
    ConsensusMethod,
    MarketContext,
)
from .swarm import Swarm, SwarmType, SwarmConfig, SwarmManager
from .consensus import ConsensusEngine
from .collective_memory import CollectiveMemory, SharedKnowledge, EmergentPattern

logger = logging.getLogger(__name__)


@dataclass
class HiveMindConfig:
    """Configuration for the Hivemind"""
    # Swarm configuration
    enable_technical_swarm: bool = True
    enable_fundamental_swarm: bool = True
    enable_sentiment_swarm: bool = True
    enable_risk_swarm: bool = True
    enable_execution_swarm: bool = True
    enable_macro_swarm: bool = True
    enable_quant_swarm: bool = True
    
    # Consensus settings
    consensus_method: ConsensusMethod = ConsensusMethod.WEIGHTED_VOTE
    min_consensus: float = 0.5
    min_confidence: float = 0.4
    
    # Memory settings
    memory_db_path: str = "hivemind_memory.db"
    enable_learning: bool = True
    
    # Execution settings
    parallel_analysis: bool = True
    analysis_timeout_seconds: float = 30.0
    
    # Risk settings
    require_risk_approval: bool = True
    max_position_without_consensus: float = 0.0


class TradingHiveMind:
    """
    Main Hivemind coordinator for collective trading intelligence.
    
    The Hivemind:
    - Manages multiple specialized swarms
    - Facilitates inter-swarm communication
    - Reaches consensus through voting
    - Learns from collective outcomes
    - Produces emergent trading signals
    
    Usage:
    ```python
    hivemind = TradingHiveMind()
    await hivemind.initialize()
    
    decision = await hivemind.analyze("EURUSD", market_data)
    print(decision.get_summary())
    ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = HiveMindConfig(**(config or {}))
        
        # Core components
        self.swarm_manager = SwarmManager(config)
        self.consensus_engine = ConsensusEngine(config)
        self.collective_memory = CollectiveMemory(self.config.memory_db_path, config)
        
        # State
        self.initialized = False
        self.current_symbol: Optional[str] = None
        self.last_decision: Optional[CollectiveDecision] = None
        
        # Metrics
        self.total_analyses = 0
        self.successful_analyses = 0
        self.total_processing_time_ms = 0.0
        
        # Callbacks
        self.on_decision: Optional[Callable[[CollectiveDecision], None]] = None
        self.on_emergent_signal: Optional[Callable[[SwarmSignal], None]] = None
    
    async def initialize(self) -> None:
        """Initialize the hivemind"""
        logger.info("Initializing Trading Hivemind...")
        
        # Initialize swarms based on config
        self._configure_swarms()
        
        # Load collective memory
        stats = self.collective_memory.get_stats()
        logger.info(f"Loaded collective memory: {stats['knowledge_count']} knowledge items, {stats['pattern_count']} patterns")
        
        self.initialized = True
        logger.info(f"Hivemind initialized with {self._count_nodes()} nodes across {len(self.swarm_manager.swarms)} swarms")
    
    def _configure_swarms(self) -> None:
        """Configure swarms based on settings"""
        # Swarms are already initialized by SwarmManager
        # Here we can customize based on config
        pass
    
    def _count_nodes(self) -> int:
        """Count total nodes across all swarms"""
        return sum(len(s.nodes) for s in self.swarm_manager.swarms.values())
    
    async def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        timeframe: str = "H1",
    ) -> CollectiveDecision:
        """
        Analyze a symbol using collective intelligence.
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            market_data: Market data dictionary containing:
                - ohlcv: List of OHLCV bars
                - fundamentals: Fundamental data
                - sentiment: Sentiment data
                - etc.
            timeframe: Analysis timeframe
            
        Returns:
            CollectiveDecision with action, consensus, and reasoning
        """
        if not self.initialized:
            await self.initialize()
        
        start_time = time.time()
        self.total_analyses += 1
        self.current_symbol = symbol
        
        logger.info(f"Hivemind analyzing {symbol} on {timeframe}")
        
        try:
            # Step 1: Prepare market context
            context = self._prepare_context(symbol, market_data, timeframe)
            
            # Step 2: Get relevant patterns from collective memory
            relevant_patterns = self.collective_memory.get_relevant_patterns(
                symbol,
                {'trend': context.trend, 'volatility': context.volatility, 'regime': context.regime},
            )
            
            # Inject patterns into market data
            market_data['collective_patterns'] = [p.to_dict() for p in relevant_patterns]
            
            # Step 3: Have all swarms analyze in parallel
            logger.debug("Running swarm analysis...")
            swarm_signals = await self.swarm_manager.analyze_all(symbol, market_data)
            
            # Step 4: Collect all node votes
            all_votes = self.swarm_manager.get_all_votes()
            
            # Step 5: Detect emergent signals
            emergent_signals = self._detect_emergent_signals(all_votes, list(swarm_signals.values()))
            
            # Step 6: Reach consensus
            logger.debug("Reaching consensus...")
            decision = self.consensus_engine.reach_consensus(
                all_votes,
                list(swarm_signals.values()) + emergent_signals,
                self.config.consensus_method,
            )
            
            # Step 7: Enrich decision
            decision.symbol = symbol
            decision.emergent_signals = emergent_signals
            
            # Calculate trade parameters if action is BUY/SELL
            if decision.action in ['BUY', 'SELL']:
                self._calculate_trade_params(decision, context, market_data)
            
            # Step 8: Apply risk checks
            if self.config.require_risk_approval:
                decision = self._apply_risk_checks(decision, market_data)
            
            # Step 9: Record in collective memory
            if self.config.enable_learning:
                self.collective_memory.record_decision(
                    symbol=symbol,
                    action=decision.action,
                    direction=decision.direction.value,
                    consensus_score=decision.consensus_score,
                    confidence=decision.confidence,
                )
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            decision.processing_time_ms = processing_time
            self.total_processing_time_ms += processing_time
            self.successful_analyses += 1
            
            self.last_decision = decision
            
            # Callbacks
            if self.on_decision:
                self.on_decision(decision)
            
            for signal in emergent_signals:
                if self.on_emergent_signal:
                    self.on_emergent_signal(signal)
            
            logger.info(f"Hivemind decision: {decision.action} ({decision.consensus_score:.0%} consensus, {decision.confidence:.0%} confidence)")
            
            return decision
            
        except Exception as e:
            logger.error(f"Hivemind analysis error: {e}", exc_info=True)
            
            return CollectiveDecision(
                symbol=symbol,
                action="HOLD",
                direction=SignalDirection.NEUTRAL,
                consensus_score=0.0,
                confidence=0.0,
                processing_time_ms=(time.time() - start_time) * 1000,
            )
    
    def _prepare_context(self, symbol: str, market_data: Dict[str, Any], timeframe: str) -> MarketContext:
        """Prepare market context from data"""
        ohlcv = market_data.get('ohlcv', [])
        
        # Determine trend
        if ohlcv and len(ohlcv) >= 20:
            closes = [bar.get('close', 0) for bar in ohlcv[-20:]]
            ma_short = sum(closes[-5:]) / 5
            ma_long = sum(closes) / len(closes)
            
            if ma_short > ma_long * 1.01:
                trend = "bullish"
            elif ma_short < ma_long * 0.99:
                trend = "bearish"
            else:
                trend = "neutral"
            
            current_price = closes[-1]
        else:
            trend = "neutral"
            current_price = market_data.get('current_price', 0)
        
        # Determine volatility
        volatility = market_data.get('volatility', 'normal')
        
        # Determine regime
        regime = market_data.get('regime', 'unknown')
        
        return MarketContext(
            symbol=symbol,
            timeframe=timeframe,
            current_price=current_price,
            trend=trend,
            volatility=volatility,
            regime=regime,
            ohlcv=ohlcv,
        )
    
    def _detect_emergent_signals(
        self,
        votes: List[NodeVote],
        swarm_signals: List[SwarmSignal],
    ) -> List[SwarmSignal]:
        """Detect emergent signals from collective behavior"""
        emergent = []
        
        if not votes:
            return emergent
        
        # Signal 1: Strong agreement across different node types
        node_types_bullish = set()
        node_types_bearish = set()
        
        for vote in votes:
            if vote.direction.to_numeric() > 0.3:
                node_types_bullish.add(vote.node_type)
            elif vote.direction.to_numeric() < -0.3:
                node_types_bearish.add(vote.node_type)
        
        if len(node_types_bullish) >= 4:
            emergent.append(SwarmSignal(
                signal_type="cross_domain_bullish",
                direction=SignalDirection.BUY,
                strength=len(node_types_bullish) / len(NodeType),
                source_nodes=[v.node_id for v in votes if v.direction.to_numeric() > 0.3],
                description=f"Bullish consensus across {len(node_types_bullish)} different analysis domains",
            ))
        
        if len(node_types_bearish) >= 4:
            emergent.append(SwarmSignal(
                signal_type="cross_domain_bearish",
                direction=SignalDirection.SELL,
                strength=len(node_types_bearish) / len(NodeType),
                source_nodes=[v.node_id for v in votes if v.direction.to_numeric() < -0.3],
                description=f"Bearish consensus across {len(node_types_bearish)} different analysis domains",
            ))
        
        # Signal 2: High confidence cluster
        high_conf_votes = [v for v in votes if v.confidence > 0.8]
        if len(high_conf_votes) >= 3:
            avg_direction = sum(v.direction.to_numeric() for v in high_conf_votes) / len(high_conf_votes)
            if abs(avg_direction) > 0.3:
                emergent.append(SwarmSignal(
                    signal_type="high_confidence_cluster",
                    direction=SignalDirection.from_numeric(avg_direction),
                    strength=len(high_conf_votes) / len(votes),
                    source_nodes=[v.node_id for v in high_conf_votes],
                    description=f"{len(high_conf_votes)} nodes with >80% confidence agree",
                ))
        
        # Signal 3: Swarm alignment
        bullish_swarms = sum(1 for s in swarm_signals if s.direction.to_numeric() > 0.2)
        bearish_swarms = sum(1 for s in swarm_signals if s.direction.to_numeric() < -0.2)
        
        if bullish_swarms >= 5:
            emergent.append(SwarmSignal(
                signal_type="swarm_alignment_bullish",
                direction=SignalDirection.BUY,
                strength=bullish_swarms / len(swarm_signals) if swarm_signals else 0,
                source_nodes=[],
                description=f"{bullish_swarms}/{len(swarm_signals)} swarms are bullish",
            ))
        
        if bearish_swarms >= 5:
            emergent.append(SwarmSignal(
                signal_type="swarm_alignment_bearish",
                direction=SignalDirection.SELL,
                strength=bearish_swarms / len(swarm_signals) if swarm_signals else 0,
                source_nodes=[],
                description=f"{bearish_swarms}/{len(swarm_signals)} swarms are bearish",
            ))
        
        return emergent
    
    def _calculate_trade_params(
        self,
        decision: CollectiveDecision,
        context: MarketContext,
        market_data: Dict[str, Any],
    ) -> None:
        """Calculate trade parameters for the decision"""
        current_price = context.current_price
        
        if current_price <= 0:
            return
        
        # Get risk parameters from risk swarm votes
        risk_votes = [v for v in decision.node_votes if v.node_type == NodeType.RISK]
        
        # Default risk parameters
        risk_percent = 0.01  # 1% risk
        
        # Calculate stop loss based on ATR or fixed percentage
        atr = market_data.get('atr', current_price * 0.01)
        
        if decision.action == "BUY":
            decision.entry_price = current_price
            decision.stop_loss = current_price - (atr * 1.5)
            decision.take_profit = current_price + (atr * 3.0)
        else:  # SELL
            decision.entry_price = current_price
            decision.stop_loss = current_price + (atr * 1.5)
            decision.take_profit = current_price - (atr * 3.0)
        
        # Calculate position size based on risk
        account_equity = market_data.get('account_equity', 10000)
        risk_amount = account_equity * risk_percent
        
        stop_distance = abs(current_price - decision.stop_loss)
        if stop_distance > 0:
            decision.position_size = risk_amount / stop_distance
        else:
            decision.position_size = 0
    
    def _apply_risk_checks(
        self,
        decision: CollectiveDecision,
        market_data: Dict[str, Any],
    ) -> CollectiveDecision:
        """Apply risk management checks"""
        # Check minimum consensus
        if decision.consensus_score < self.config.min_consensus:
            logger.warning(f"Low consensus ({decision.consensus_score:.0%}), downgrading to HOLD")
            decision.action = "HOLD"
            decision.direction = SignalDirection.NEUTRAL
        
        # Check minimum confidence
        if decision.confidence < self.config.min_confidence:
            logger.warning(f"Low confidence ({decision.confidence:.0%}), downgrading to HOLD")
            decision.action = "HOLD"
            decision.direction = SignalDirection.NEUTRAL
        
        # Check risk swarm approval
        risk_votes = [v for v in decision.node_votes if v.node_type == NodeType.RISK]
        if risk_votes:
            avg_risk_signal = sum(v.direction.to_numeric() for v in risk_votes) / len(risk_votes)
            if avg_risk_signal < -0.5:
                logger.warning("Risk swarm disapproves, downgrading to HOLD")
                decision.action = "HOLD"
                decision.direction = SignalDirection.NEUTRAL
        
        return decision
    
    def record_outcome(self, was_correct: bool, profit: float) -> None:
        """Record the outcome of the last decision for learning"""
        if not self.last_decision:
            return
        
        # Update swarm performance
        self.swarm_manager.record_outcome(was_correct, profit)
        
        # Update collective memory
        if self.config.enable_learning:
            self.collective_memory.record_outcome(
                self.last_decision.symbol,
                was_correct,
                profit,
            )
            
            # Trigger learning
            new_patterns = self.collective_memory.learn_from_history()
            if new_patterns:
                logger.info(f"Discovered {len(new_patterns)} new patterns from collective learning")
    
    def get_status(self) -> Dict[str, Any]:
        """Get hivemind status"""
        return {
            'initialized': self.initialized,
            'total_nodes': self._count_nodes(),
            'total_swarms': len(self.swarm_manager.swarms),
            'total_analyses': self.total_analyses,
            'successful_analyses': self.successful_analyses,
            'success_rate': self.successful_analyses / self.total_analyses if self.total_analyses > 0 else 0,
            'avg_processing_time_ms': self.total_processing_time_ms / self.total_analyses if self.total_analyses > 0 else 0,
            'swarms': self.swarm_manager.get_status(),
            'memory': self.collective_memory.get_stats(),
            'last_decision': self.last_decision.to_dict() if self.last_decision else None,
        }
    
    def get_node_rankings(self) -> List[Dict[str, Any]]:
        """Get nodes ranked by performance"""
        all_nodes = []
        
        for swarm in self.swarm_manager.swarms.values():
            for node in swarm.nodes:
                all_nodes.append({
                    'node_id': node.node_id,
                    'node_type': node.node_type.value,
                    'weight': node.current_weight,
                    'accuracy': node.performance.accuracy,
                    'total_votes': node.performance.total_votes,
                    'profit_factor': node.performance.profit_factor,
                })
        
        # Sort by weight (performance)
        all_nodes.sort(key=lambda n: n['weight'], reverse=True)
        
        return all_nodes


async def quick_start(config: Optional[Dict[str, Any]] = None) -> TradingHiveMind:
    """Quick start helper to create and initialize hivemind"""
    hivemind = TradingHiveMind(config)
    await hivemind.initialize()
    return hivemind


class UniversalHivemindController:
    """
    Universal controller that manages ALL agent systems in the trading bot.
    
    This is the master controller that ensures all agents across all modules
    are controlled by the central hivemind intelligence.
    
    Controlled Systems:
    - Hivemind swarms (Technical, Fundamental, Sentiment, Risk, Execution, Macro, Quant)
    - RadarAI agents (MetaOrchestrator, DataFusion, Ontology, Intelligence, Strategy, etc.)
    - Agents (MultiAgentDebate, Executor, Planner, Verifier)
    - Agents2 (MultiAgentCoordinator with specialized agents)
    - Self-Coordinating AI (Discovery, Self-Programming, Experimentation)
    - Foundation Agents (Cognitive Core, Curiosity Engine, etc.)
    - Core Agent System (MasterOrchestrator, AgentRegistry, ReActLoop, etc.)
    - AI Core Agents (Orchestrator, Executor, Planner, Verifier, SafetyValidator)
    - Improvement Agent (DeepAnalyzer, WeaknessDetector, ImprovementProposer)
    - Aletheia Autonomous (StrategyGenerator, StrategyVerifier, StrategyReviser)
    
    Usage:
        controller = UniversalHivemindController()
        await controller.initialize()
        
        # All agents are now under unified hivemind control
        result = await controller.analyze_with_all_agents(symbol, market_data)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Main hivemind
        self.trading_hivemind: Optional[TradingHiveMind] = None
        
        # Agent system controllers
        self.radar_ai = None
        self.agents_manager = None
        self.agents2_manager = None
        self.self_coordinating = None
        self.foundation_agents = None
        self.core_agent_system = None
        self.ai_core_agents = None
        self.improvement_agent = None
        self.aletheia_autonomous = None
        
        # State
        self._initialized = False
        self._running = False
        
        logger.info("UniversalHivemindController created")
    
    async def initialize(self) -> None:
        """Initialize all agent systems under hivemind control."""
        logger.info("Initializing Universal Hivemind Controller...")
        
        # Initialize main TradingHiveMind
        try:
            self.trading_hivemind = TradingHiveMind(self.config)
            await self.trading_hivemind.initialize()
            logger.info("✓ TradingHiveMind initialized")
        except Exception as e:
            logger.warning(f"TradingHiveMind initialization: {e}")
        
        # Initialize RadarAI under hivemind control
        try:
            from ..radar_ai import RadarAIHivemindAdapter
            self.radar_ai = RadarAIHivemindAdapter(hivemind_controller=self)
            await self.radar_ai.initialize(self.config.get('radar_ai', {}))
            logger.info("✓ RadarAI under hivemind control")
        except Exception as e:
            logger.warning(f"RadarAI initialization: {e}")
        
        # Initialize Agents module under hivemind control
        try:
            from ..agents import HivemindAgentManager
            self.agents_manager = HivemindAgentManager(hivemind_controller=self, config=self.config)
            await self.agents_manager.initialize()
            logger.info("✓ Agents module under hivemind control")
        except Exception as e:
            logger.warning(f"Agents initialization: {e}")
        
        # Initialize Agents2 module under hivemind control
        try:
            from ..agents2 import HivemindAgents2Manager
            self.agents2_manager = HivemindAgents2Manager(hivemind_controller=self, config=self.config)
            await self.agents2_manager.initialize()
            logger.info("✓ Agents2 module under hivemind control")
        except Exception as e:
            logger.warning(f"Agents2 initialization: {e}")
        
        # Initialize Self-Coordinating AI under hivemind control
        try:
            from ..self_coordinating_ai import HivemindSelfCoordinatingAdapter
            self.self_coordinating = HivemindSelfCoordinatingAdapter(hivemind_controller=self, config=self.config)
            await self.self_coordinating.initialize()
            logger.info("✓ Self-Coordinating AI under hivemind control")
        except Exception as e:
            logger.warning(f"Self-Coordinating AI initialization: {e}")
        
        # Initialize Foundation Agents under hivemind control
        try:
            from ..foundation_agents import HivemindFoundationAdapter
            self.foundation_agents = HivemindFoundationAdapter(hivemind_controller=self, config=self.config)
            await self.foundation_agents.initialize()
            logger.info("✓ Foundation Agents under hivemind control")
        except Exception as e:
            logger.warning(f"Foundation Agents initialization: {e}")
        
        # Initialize Core Agent System under hivemind control
        try:
            from ..core_agent_system import HivemindCoreAgentAdapter
            self.core_agent_system = HivemindCoreAgentAdapter(hivemind_controller=self, config=self.config)
            await self.core_agent_system.initialize()
            logger.info("✓ Core Agent System under hivemind control")
        except Exception as e:
            logger.warning(f"Core Agent System initialization: {e}")
        
        # Initialize AI Core Agents under hivemind control
        try:
            from ..ai_core.agents import HivemindAICoreAdapter
            self.ai_core_agents = HivemindAICoreAdapter(hivemind_controller=self, config=self.config)
            await self.ai_core_agents.initialize()
            logger.info("✓ AI Core Agents under hivemind control")
        except Exception as e:
            logger.warning(f"AI Core Agents initialization: {e}")
        
        # Initialize Improvement Agent under hivemind control
        try:
            from ..improvement_agent import HivemindImprovementAdapter
            self.improvement_agent = HivemindImprovementAdapter(hivemind_controller=self, config=self.config)
            await self.improvement_agent.initialize()
            logger.info("✓ Improvement Agent under hivemind control")
        except Exception as e:
            logger.warning(f"Improvement Agent initialization: {e}")
        
        # Initialize Aletheia Autonomous under hivemind control
        try:
            from ..aletheia_autonomous import HivemindAletheiaAdapter
            self.aletheia_autonomous = HivemindAletheiaAdapter(hivemind_controller=self, config=self.config)
            await self.aletheia_autonomous.initialize()
            logger.info("✓ Aletheia Autonomous under hivemind control")
        except Exception as e:
            logger.warning(f"Aletheia Autonomous initialization: {e}")
        
        self._initialized = True
        logger.info("=" * 60)
        logger.info("UNIVERSAL HIVEMIND CONTROLLER READY")
        logger.info("All agent systems are under unified control")
        logger.info("=" * 60)
    
    async def analyze_with_all_agents(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run analysis through ALL controlled agent systems.
        
        This aggregates intelligence from every agent system under hivemind control.
        """
        if not self._initialized:
            await self.initialize()
        
        results = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'systems': {}
        }
        
        # Trading Hivemind analysis
        if self.trading_hivemind:
            try:
                results['systems']['trading_hivemind'] = await self.trading_hivemind.analyze(symbol, market_data)
            except Exception as e:
                logger.error(f"TradingHiveMind analysis error: {e}")
        
        # RadarAI analysis
        if self.radar_ai:
            try:
                results['systems']['radar_ai'] = self.radar_ai.get_status()
            except Exception as e:
                logger.error(f"RadarAI analysis error: {e}")
        
        # Agents2 analysis
        if self.agents2_manager:
            try:
                results['systems']['agents2'] = self.agents2_manager.analyze_market(market_data)
            except Exception as e:
                logger.error(f"Agents2 analysis error: {e}")
        
        return results
    
    def get_unified_status(self) -> Dict[str, Any]:
        """Get status of ALL controlled agent systems."""
        return {
            'initialized': self._initialized,
            'running': self._running,
            'trading_hivemind': self.trading_hivemind.get_status() if self.trading_hivemind else None,
            'radar_ai': self.radar_ai.get_status() if self.radar_ai else None,
            'agents': self.agents_manager.get_status() if self.agents_manager else None,
            'agents2': self.agents2_manager.get_status() if self.agents2_manager else None,
            'self_coordinating': self.self_coordinating.get_status() if self.self_coordinating else None,
            'foundation_agents': self.foundation_agents.get_status() if self.foundation_agents else None,
            'core_agent_system': self.core_agent_system.get_status() if self.core_agent_system else None,
            'ai_core_agents': self.ai_core_agents.get_status() if self.ai_core_agents else None,
            'improvement_agent': self.improvement_agent.get_status() if self.improvement_agent else None,
            'aletheia_autonomous': self.aletheia_autonomous.get_status() if self.aletheia_autonomous else None,
        }
    
    async def start_all(self) -> None:
        """Start all agent systems."""
        self._running = True
        
        if self.self_coordinating:
            await self.self_coordinating.start()
        if self.foundation_agents:
            await self.foundation_agents.start()
        if self.agents_manager:
            await self.agents_manager.start()
        if self.agents2_manager:
            await self.agents2_manager.start()
        if self.core_agent_system:
            await self.core_agent_system.start()
        if self.ai_core_agents:
            await self.ai_core_agents.start()
        if self.improvement_agent:
            await self.improvement_agent.start()
        if self.aletheia_autonomous:
            await self.aletheia_autonomous.start()
        
        logger.info("All agent systems started")
    
    async def stop_all(self) -> None:
        """Stop all agent systems."""
        self._running = False
        
        if self.self_coordinating:
            await self.self_coordinating.stop()
        if self.foundation_agents:
            await self.foundation_agents.stop()
        if self.agents_manager:
            await self.agents_manager.stop()
        if self.agents2_manager:
            await self.agents2_manager.stop()
        if self.core_agent_system:
            await self.core_agent_system.stop()
        if self.ai_core_agents:
            await self.ai_core_agents.stop()
        if self.improvement_agent:
            await self.improvement_agent.stop()
        if self.aletheia_autonomous:
            await self.aletheia_autonomous.stop()
        
        logger.info("All agent systems stopped")


# Aliases for easy access
HivemindAgentController = UniversalHivemindController
AgentController = UniversalHivemindController
