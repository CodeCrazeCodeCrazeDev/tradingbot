"""
Hivemind Orchestrator V2 - Ultimate Collective Intelligence
============================================================

Master orchestrator integrating all advanced hivemind systems:
- Neural Mesh Network (telepathic communication)
- Quantum Entanglement (synchronized decisions)
- Collective Consciousness (unified awareness)
- Swarm Intelligence (collective optimization)
- Consensus Mechanisms (agreement protocols)

Creates a true hivemind - a collective intelligence that thinks,
learns, and decides as one unified entity.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .neural_mesh import NeuralMesh, TelepathicCommunicator, create_neural_mesh, SignalType
from .quantum_entanglement import (
    QuantumEntanglementEngine, 
    QuantumHivemindBridge, 
    create_quantum_entanglement
)
from .collective_consciousness import (
    CollectiveConsciousness, 
    create_collective_consciousness,
    ConsciousnessLevel,
    EmotionalState,
)
from .safety_guards import SafetyOrchestrator, SafetyConfig, create_safety_orchestrator

logger = logging.getLogger(__name__)


class HivemindMode(Enum):
    """Operating modes of the hivemind"""
    DORMANT = "dormant"           # Minimal activity
    OBSERVING = "observing"       # Watching market
    ANALYZING = "analyzing"       # Deep analysis
    DECIDING = "deciding"         # Making decision
    EXECUTING = "executing"       # Taking action
    LEARNING = "learning"         # Learning from outcomes
    SYNCHRONIZED = "synchronized" # All nodes in sync


class HivemindHealth(Enum):
    """Health status of the hivemind"""
    OPTIMAL = "optimal"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    IMPAIRED = "impaired"
    CRITICAL = "critical"


@dataclass
class HivemindState:
    """Current state of the hivemind"""
    mode: HivemindMode = HivemindMode.DORMANT
    health: HivemindHealth = HivemindHealth.HEALTHY
    
    # Component states
    mesh_active: bool = False
    quantum_active: bool = False
    consciousness_active: bool = False
    
    # Metrics
    coherence: float = 1.0
    synchronization: float = 1.0
    collective_confidence: float = 0.5
    
    # Activity
    total_decisions: int = 0
    successful_decisions: int = 0
    total_perceptions: int = 0
    
    # Timestamps
    started_at: Optional[datetime] = None
    last_decision: Optional[datetime] = None
    last_sync: Optional[datetime] = None


@dataclass
class HivemindConfig:
    """Configuration for the hivemind"""
    # Node configuration
    node_types: List[str] = field(default_factory=lambda: [
        'technical', 'fundamental', 'sentiment', 'risk',
        'execution', 'macro', 'pattern', 'momentum'
    ])
    
    # Mesh configuration
    fully_connected_mesh: bool = True
    
    # Quantum configuration
    use_quantum_entanglement: bool = True
    
    # Consciousness configuration
    consciousness_enabled: bool = True
    
    # Sync intervals
    sync_interval_seconds: float = 10.0
    decision_timeout_seconds: float = 30.0
    
    # Thresholds
    min_consensus_threshold: float = 0.6
    min_confidence_threshold: float = 0.5


@dataclass
class HivemindDecision:
    """A decision made by the hivemind"""
    decision_id: str
    action: str  # buy, sell, hold
    confidence: float
    
    # Contributing factors
    mesh_signal: Dict[str, Any]
    quantum_result: Dict[str, Any]
    consciousness_decision: Dict[str, Any]
    
    # Consensus
    consensus_score: float
    node_votes: Dict[str, str]
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reasoning: List[str] = field(default_factory=list)
    
    def get_summary(self) -> str:
        """Get decision summary"""
        return (
            f"Decision: {self.action.upper()} "
            f"(Confidence: {self.confidence:.1%}, "
            f"Consensus: {self.consensus_score:.1%})"
        )


class HivemindOrchestratorV2:
    """
    Hivemind Orchestrator V2
    
    The ultimate collective intelligence system that integrates:
    - Neural mesh for telepathic communication
    - Quantum entanglement for synchronized decisions
    - Collective consciousness for unified awareness
    
    Creates a true hivemind that thinks as one.
    """
    
    def __init__(self, config: Optional[HivemindConfig] = None):
        self.config = config or HivemindConfig()
        
        # State
        self.state = HivemindState()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Components (lazy initialization)
        self._mesh: Optional[NeuralMesh] = None
        self._communicator: Optional[TelepathicCommunicator] = None
        self._quantum_engine: Optional[QuantumEntanglementEngine] = None
        self._quantum_bridge: Optional[QuantumHivemindBridge] = None
        self._consciousness: Optional[CollectiveConsciousness] = None
        
        # Decision history (bounded to prevent memory leak)
        self._max_decision_history = 1000
        self.decision_history: List[HivemindDecision] = []
        
        # Safety orchestrator for risk mitigation
        self._safety = create_safety_orchestrator()
        self._state_lock = asyncio.Lock()
        
        # Callbacks
        self.on_decision: Optional[Callable[[HivemindDecision], None]] = None
        self.on_insight: Optional[Callable[[Dict[str, Any]], None]] = None
        
        logger.info("HivemindOrchestratorV2 initialized")
    
    # ==================== INITIALIZATION ====================
    
    def _init_mesh(self) -> Tuple[NeuralMesh, TelepathicCommunicator]:
        """Initialize neural mesh network"""
        if self._mesh is None:
            self._mesh, self._communicator = create_neural_mesh(
                node_types=self.config.node_types,
                fully_connected=self.config.fully_connected_mesh,
            )
            self.state.mesh_active = True
            logger.info("Neural mesh initialized")
        return self._mesh, self._communicator
    
    def _init_quantum(self) -> Tuple[QuantumEntanglementEngine, QuantumHivemindBridge]:
        """Initialize quantum entanglement system"""
        if self._quantum_engine is None:
            self._quantum_engine, self._quantum_bridge = create_quantum_entanglement(
                node_ids=self.config.node_types,
            )
            self.state.quantum_active = True
            logger.info("Quantum entanglement initialized")
        return self._quantum_engine, self._quantum_bridge
    
    def _init_consciousness(self) -> CollectiveConsciousness:
        """Initialize collective consciousness"""
        if self._consciousness is None:
            self._consciousness = create_collective_consciousness()
            self.state.consciousness_active = True
            logger.info("Collective consciousness initialized")
        return self._consciousness
    
    # ==================== MAIN OPERATIONS ====================
    
    async def start(self) -> None:
        """Start the hivemind"""
        if self._running:
            logger.warning("Hivemind already running")
            return
        
        self._running = True
        self.state.started_at = datetime.utcnow()
        self.state.mode = HivemindMode.OBSERVING
        
        logger.info("Starting Hivemind V2...")
        
        # Initialize all components
        self._init_mesh()
        if self.config.use_quantum_entanglement:
            self._init_quantum()
            # Initialize quantum nodes
            await self._quantum_bridge.initialize_quantum_nodes(self.config.node_types)
        if self.config.consciousness_enabled:
            self._init_consciousness()
        
        # Start background loops
        self._tasks.append(asyncio.create_task(self._sync_loop()))
        self._tasks.append(asyncio.create_task(self._consciousness_loop()))
        self._tasks.append(asyncio.create_task(self._health_monitor_loop()))
        
        logger.info("Hivemind V2 started")
    
    async def stop(self) -> None:
        """Stop the hivemind"""
        self._running = False
        self.state.mode = HivemindMode.DORMANT
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        logger.info("Hivemind V2 stopped")
    
    async def _sync_loop(self) -> None:
        """Background synchronization loop"""
        while self._running:
            try:
                await asyncio.sleep(self.config.sync_interval_seconds)
                await self._synchronize()
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
    
    async def _consciousness_loop(self) -> None:
        """Background consciousness processing loop"""
        while self._running:
            try:
                await asyncio.sleep(5)  # Process every 5 seconds
                
                if self._consciousness:
                    result = self._consciousness.process_perceptions()
                    
                    # Check for insights
                    if result.get('new_insights', 0) > 0 and self.on_insight:
                        for insight in self._consciousness.insights[-result['new_insights']:]:
                            self.on_insight({
                                'type': insight.insight_type,
                                'description': insight.description,
                                'confidence': insight.confidence,
                            })
            except Exception as e:
                logger.error(f"Error in consciousness loop: {e}")
    
    async def _health_monitor_loop(self) -> None:
        """Monitor hivemind health"""
        while self._running:
            try:
                await asyncio.sleep(30)
                self._update_health()
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
    
    async def _synchronize(self) -> None:
        """Synchronize all hivemind components"""
        self.state.mode = HivemindMode.SYNCHRONIZED
        
        # Process mesh signals
        if self._mesh:
            self._mesh.process_signals()
            self.state.synchronization = self._mesh.synchronization_level
        
        # Apply quantum decoherence management
        if self._quantum_engine:
            self._quantum_engine.apply_decoherence_all()
        
        # Synchronize consciousness
        if self._consciousness:
            self._consciousness.synchronize()
            self.state.coherence = self._consciousness.coherence
        
        self.state.last_sync = datetime.utcnow()
        self.state.mode = HivemindMode.OBSERVING
    
    def _update_health(self) -> None:
        """Update health status"""
        # Calculate health score
        score = 0.0
        checks = 0
        
        if self.state.mesh_active:
            score += self.state.synchronization
            checks += 1
        
        if self.state.consciousness_active and self._consciousness:
            score += self._consciousness.coherence
            checks += 1
        
        if self.state.quantum_active and self._quantum_engine:
            summary = self._quantum_engine.get_quantum_state_summary()
            score += summary.get('avg_coherence', 0.5)
            checks += 1
        
        health_score = score / checks if checks > 0 else 0.5
        
        if health_score >= 0.9:
            self.state.health = HivemindHealth.OPTIMAL
        elif health_score >= 0.7:
            self.state.health = HivemindHealth.HEALTHY
        elif health_score >= 0.5:
            self.state.health = HivemindHealth.DEGRADED
        elif health_score >= 0.3:
            self.state.health = HivemindHealth.IMPAIRED
        else:
            self.state.health = HivemindHealth.CRITICAL
    
    # ==================== PERCEPTION & ANALYSIS ====================
    
    async def perceive(
        self,
        perception_type: str,
        content: Dict[str, Any],
        source_node: str,
        confidence: float = 0.5,
    ) -> None:
        """Receive a perception from a node"""
        self.state.total_perceptions += 1
        
        # Send through mesh
        if self._communicator:
            await self._communicator.broadcast_thought(
                source_node,
                f"{perception_type}: {content.get('summary', str(content)[:100])}",
                perception_type,
                confidence,
            )
        
        # Apply to quantum state
        if self._quantum_bridge:
            await self._quantum_bridge.apply_node_analysis(source_node, {
                'signal': content.get('signal', 0),
                'confidence': confidence,
            })
        
        # Add to consciousness
        if self._consciousness:
            salience = confidence * (1 + content.get('importance', 0))
            self._consciousness.receive_perception(
                perception_type,
                content,
                source_node,
                confidence,
                min(1.0, salience),
            )
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data through the hivemind"""
        self.state.mode = HivemindMode.ANALYZING
        
        # Broadcast analysis request through mesh
        if self._mesh:
            self._mesh.broadcast(
                "system",
                SignalType.QUERY,
                {'query': f"analyze_{symbol}", 'data': market_data}
            )
            self._mesh.process_signals()
        
        # Get collective thought
        collective_thought = None
        if self._mesh:
            collective_thought = self._mesh.get_collective_thought()
        
        # Get consciousness perception
        unified_perception = None
        if self._consciousness:
            unified_perception = self._consciousness.get_unified_perception()
        
        self.state.mode = HivemindMode.OBSERVING
        
        return {
            'symbol': symbol,
            'collective_thought': collective_thought,
            'unified_perception': unified_perception,
            'mesh_topology': self._mesh.get_mesh_topology() if self._mesh else None,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    # ==================== DECISION MAKING ====================
    
    async def make_decision(
        self,
        symbol: str,
        options: List[str] = None,
    ) -> HivemindDecision:
        """Make a collective decision"""
        # Pre-decision safety check
        can_proceed, reason = await self._safety.pre_decision_check()
        if not can_proceed:
            logger.warning(f"Decision blocked by safety: {reason}")
            # Return a HOLD decision when blocked
            return HivemindDecision(
                decision_id=f"blocked_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                action='hold',
                confidence=0.0,
                mesh_signal={},
                quantum_result={},
                consciousness_decision={},
                consensus_score=0.0,
                node_votes={},
                reasoning=[f"BLOCKED: {reason}"],
            )
        
        self.state.mode = HivemindMode.DECIDING
        options = options or ['buy', 'sell', 'hold']
        
        # Gather signals from all systems
        mesh_signal = {}
        quantum_result = {}
        consciousness_decision = {}
        node_votes = {}
        
        # 1. Neural Mesh Consensus
        if self._communicator:
            mesh_consensus = await self._communicator.reach_consensus(
                f"decision_{symbol}",
                options
            )
            mesh_signal = mesh_consensus
            node_votes.update({
                f"mesh_{i}": mesh_consensus.get('winner', 'hold')
                for i in range(3)  # Simulate multiple mesh votes
            })
        
        # 2. Quantum Decision
        if self._quantum_bridge:
            quantum_result = await self._quantum_bridge.get_quantum_decision()
            node_votes['quantum'] = quantum_result.get('action', 'hold')
        
        # 3. Consciousness Decision
        if self._consciousness:
            consciousness_decision = self._consciousness.make_collective_decision(options)
            node_votes['consciousness'] = consciousness_decision.get('decision', 'hold')
        
        # Aggregate decisions
        vote_counts = {opt: 0 for opt in options}
        confidence_sum = {opt: 0.0 for opt in options}
        
        for voter, vote in node_votes.items():
            if vote in vote_counts:
                vote_counts[vote] += 1
                # Weight by source
                if 'quantum' in voter:
                    confidence_sum[vote] += quantum_result.get('confidence', 0.5)
                elif 'consciousness' in voter:
                    confidence_sum[vote] += consciousness_decision.get('confidence', 0.5)
                else:
                    confidence_sum[vote] += mesh_signal.get('confidence', 0.5)
        
        # Determine winner
        total_votes = sum(vote_counts.values())
        winner = max(vote_counts, key=vote_counts.get)
        consensus_score = vote_counts[winner] / total_votes if total_votes > 0 else 0
        
        # Calculate confidence
        confidence = confidence_sum[winner] / max(1, vote_counts[winner])
        
        # Build reasoning
        reasoning = []
        if mesh_signal:
            reasoning.append(f"Neural mesh suggests {mesh_signal.get('winner', 'unknown')}")
        if quantum_result:
            reasoning.append(f"Quantum consensus: {quantum_result.get('action', 'unknown')}")
        if consciousness_decision:
            reasoning.append(
                f"Collective consciousness ({consciousness_decision.get('emotional_influence', 'calm')}): "
                f"{consciousness_decision.get('decision', 'unknown')}"
            )
        
        # Create decision
        decision = HivemindDecision(
            decision_id=f"decision_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            action=winner,
            confidence=confidence,
            mesh_signal=mesh_signal,
            quantum_result=quantum_result,
            consciousness_decision=consciousness_decision,
            consensus_score=consensus_score,
            node_votes=node_votes,
            reasoning=reasoning,
        )
        
        # Store and update state (thread-safe with lock)
        async with self._state_lock:
            self.decision_history.append(decision)
            # Bound history to prevent memory leak
            if len(self.decision_history) > self._max_decision_history:
                self.decision_history = self.decision_history[-self._max_decision_history:]
            self.state.total_decisions += 1
            self.state.last_decision = datetime.utcnow()
            self.state.collective_confidence = confidence
            self.state.mode = HivemindMode.OBSERVING
        
        # Callback
        if self.on_decision:
            self.on_decision(decision)
        
        # Store in consciousness memory
        if self._consciousness:
            self._consciousness.store_memory(
                'decision',
                {
                    'action': winner,
                    'confidence': confidence,
                    'consensus': consensus_score,
                },
                importance=confidence,
            )
        
        logger.info(f"Hivemind decision: {decision.get_summary()}")
        return decision
    
    def record_outcome(self, decision_id: str, success: bool, pnl: float = 0) -> None:
        """Record the outcome of a decision for learning"""
        # Find decision
        decision = None
        for d in self.decision_history:
            if d.decision_id == decision_id:
                decision = d
                break
        
        if not decision:
            return
        
        if success:
            self.state.successful_decisions += 1
        
        # Apply learning signal to mesh
        if self._mesh:
            reward = 1.0 if success else -0.5
            self._mesh.apply_reward(reward)
        
        # Store outcome in consciousness
        if self._consciousness:
            self._consciousness.store_memory(
                'outcome',
                {
                    'decision_id': decision_id,
                    'action': decision.action,
                    'success': success,
                    'pnl': pnl,
                },
                importance=0.8 if success else 0.6,
            )
    
    # ==================== REPORTING ====================
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive hivemind report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'state': {
                'mode': self.state.mode.value,
                'health': self.state.health.value,
                'running': self._running,
                'started_at': self.state.started_at.isoformat() if self.state.started_at else None,
            },
            'metrics': {
                'coherence': self.state.coherence,
                'synchronization': self.state.synchronization,
                'collective_confidence': self.state.collective_confidence,
                'total_decisions': self.state.total_decisions,
                'successful_decisions': self.state.successful_decisions,
                'success_rate': (
                    self.state.successful_decisions / self.state.total_decisions
                    if self.state.total_decisions > 0 else 0
                ),
                'total_perceptions': self.state.total_perceptions,
            },
            'components': {
                'mesh_active': self.state.mesh_active,
                'quantum_active': self.state.quantum_active,
                'consciousness_active': self.state.consciousness_active,
            },
        }
        
        # Add component reports
        if self._mesh:
            report['mesh'] = self._mesh.get_report()
        
        if self._quantum_engine:
            report['quantum'] = self._quantum_engine.get_report()
        
        if self._consciousness:
            report['consciousness'] = self._consciousness.get_report()
        
        return report
    
    async def update_equity(self, equity: float) -> Dict[str, Any]:
        """Update equity for loss limit tracking"""
        return await self._safety.update_equity(equity)
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get safety system status"""
        return self._safety.get_status()
    
    def human_override(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Human override - ALWAYS works"""
        params = params or {}
        result = {'action': action, 'success': True, 'message': ''}
        
        if action == "STOP":
            asyncio.create_task(self.stop())
            result['message'] = "Hivemind stopping"
        
        elif action == "FORCE_DECISION":
            direction = params.get('direction', 'hold')
            if self._quantum_bridge:
                asyncio.create_task(
                    self._quantum_bridge.quantum_override(direction, 0.8)
                )
            result['message'] = f"Forced decision towards {direction}"
        
        elif action == "RESET_QUANTUM":
            if self._quantum_engine:
                self._quantum_engine.reset_all()
            result['message'] = "Quantum states reset"
        
        elif action == "SYNC":
            asyncio.create_task(self._synchronize())
            result['message'] = "Synchronization triggered"
        
        elif action == "GET_STATUS":
            result['status'] = self.get_comprehensive_report()
            result['message'] = "Status retrieved"
        
        else:
            result['success'] = False
            result['message'] = f"Unknown action: {action}"
        
        logger.info(f"Human override: {action} - {result['message']}")
        return result


# Factory functions
def create_hivemind_v2(config: Optional[HivemindConfig] = None) -> HivemindOrchestratorV2:
    """Create hivemind orchestrator V2"""
    return HivemindOrchestratorV2(config)


async def run_hivemind_v2(
    config: Optional[HivemindConfig] = None,
    duration_seconds: Optional[float] = None
) -> None:
    """Run hivemind system"""
    hivemind = create_hivemind_v2(config)
    await hivemind.start()
    
    try:
        if duration_seconds:
            await asyncio.sleep(duration_seconds)
        else:
            while True:
                await asyncio.sleep(3600)
    finally:
        await hivemind.stop()
