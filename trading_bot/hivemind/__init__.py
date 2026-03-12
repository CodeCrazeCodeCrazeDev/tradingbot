"""
Trading Bot Hivemind - Collective Intelligence System
============================================================

A swarm intelligence architecture where multiple specialized AI nodes
work together to make trading decisions through consensus.

Architecture:
```
                    ┌─────────────────────────────────────┐
                    │         HIVEMIND COORDINATOR        │
                    │   (Consensus, Aggregation, Memory)  │
                    └─────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
    ┌───────▼───────┐         ┌───────▼───────┐         ┌───────▼───────┐
    │  TECHNICAL    │         │ FUNDAMENTAL   │         │  SENTIMENT    │
    │    SWARM      │         │    SWARM      │         │    SWARM      │
    │  (5 nodes)    │         │  (3 nodes)    │         │  (4 nodes)    │
    └───────────────┘         └───────────────┘         └───────────────┘
            │                         │                         │
    ┌───────▼───────┐         ┌───────▼───────┐         ┌───────▼───────┐
    │    RISK       │         │  EXECUTION    │         │   MACRO       │
    │    SWARM      │         │    SWARM      │         │    SWARM      │
    │  (3 nodes)    │         │  (2 nodes)    │         │  (3 nodes)    │
    └───────────────┘         └───────────────┘         └───────────────┘
```

Key Concepts:
- **HiveNode**: Individual AI agent with specific expertise
- **Swarm**: Group of related nodes that collaborate
- **Consensus**: Voting mechanism for collective decisions
- **Emergence**: Complex behavior from simple node interactions
- **Collective Memory**: Shared knowledge across all nodes

Features:
- Multi-node parallel analysis
- Weighted voting based on node performance
- Adaptive node weights (successful nodes gain influence)
- Conflict resolution through consensus
- Emergent trading signals from node interactions
- Collective learning from outcomes

Usage:
```python
from trading_bot.hivemind import TradingHiveMind, quick_start

# Quick start
hivemind = await quick_start()

# Get collective decision
decision = await hivemind.analyze("EURUSD", market_data)

print(decision.action)           # BUY, SELL, HOLD
print(decision.consensus_score)  # 0.0 - 1.0 (agreement level)
print(decision.node_votes)       # Individual node opinions
print(decision.emergent_signals) # Signals from node interactions
```
"""

# Core components
try:
    from .core import (
        HiveNode,
        NodeType,
        NodeState,
        NodeVote,
        SwarmSignal,
        CollectiveDecision,
        ConsensusMethod,
    )
except ImportError:
    pass

# Specialized nodes
try:
    from .nodes import (
        TechnicalNode,
        FundamentalNode,
        SentimentNode,
        RiskNode,
        ExecutionNode,
        MacroNode,
        MicrostructureNode,
        QuantNode,
    )
except ImportError:
    pass

# Swarm management
try:
    from .swarm import (
        Swarm,
        SwarmType,
        SwarmConfig,
    )
except ImportError:
    pass

# Consensus mechanisms
try:
    from .consensus import (
        ConsensusEngine,
        VotingStrategy,
        ConflictResolver,
    )
except ImportError:
    pass

# Collective memory
try:
    from .collective_memory import (
        CollectiveMemory,
        SharedKnowledge,
        EmergentPattern,
    )
except ImportError:
    pass

# Main coordinator
try:
    from .coordinator import (
        TradingHiveMind,
        HiveMindConfig,
        quick_start,
    )
except ImportError:
    pass

# Military-grade protocols
try:
    from .military_protocols import (
        MilitaryCommandCenter,
        MilitaryHiveMind,
        SecurityClearance,
        ThreatLevel,
        DefenseCondition,
        OperationalMode,
        Rank,
        MissionType,
        MissionPlan,
        RulesOfEngagement,
        ThreatAssessment,
        BattleDamageAssessment,
    )
except ImportError:
    pass

# V2 Components - Neural Mesh
try:
    from .neural_mesh import (
        NeuralMesh,
        TelepathicCommunicator,
        MeshNode,
        NeuralLink,
        NeuralSignal,
        LinkType,
        SignalType,
        create_neural_mesh,
    )
except ImportError:
    pass

# V2 Components - Quantum Entanglement
try:
    from .quantum_entanglement import (
        QuantumEntanglementEngine,
        QuantumHivemindBridge,
        TradingQubit,
        EntangledPair,
        QuantumState,
        EntanglementType,
        create_quantum_entanglement,
    )
except ImportError:
    pass

# V2 Components - Collective Consciousness
try:
    from .collective_consciousness import (
        CollectiveConsciousness,
        AttentionMechanism,
        GlobalWorkspace,
        Perception,
        CollectiveInsight,
        SharedMemory,
        ConsciousnessLevel,
        AttentionFocus,
        EmotionalState,
        create_collective_consciousness,
    )
except ImportError:
    pass

# V2 Master Orchestrator
try:
    from .hivemind_orchestrator_v2 import (
        HivemindOrchestratorV2,
        HivemindMode,
        HivemindHealth,
        HivemindState,
        HivemindConfig,
        HivemindDecision,
        create_hivemind_v2,
        run_hivemind_v2,
    )
except ImportError:
    pass

# Safety Guards (Risk Mitigation)
try:
    from .safety_guards import (
        SafetyOrchestrator,
        SafetyConfig,
        CircuitBreaker,
        CircuitState,
        LossLimitGuard,
        RateLimiter,
        InputValidator,
        ThreadSafeState,
        create_safety_orchestrator,
    )
except ImportError:
    pass

__all__ = [
    # Core V1
    'HiveNode',
    'NodeType',
    'NodeState',
    'NodeVote',
    'SwarmSignal',
    'CollectiveDecision',
    'ConsensusMethod',
    
    # Nodes
    'TechnicalNode',
    'FundamentalNode',
    'SentimentNode',
    'RiskNode',
    'ExecutionNode',
    'MacroNode',
    'MicrostructureNode',
    'QuantNode',
    
    # Swarm
    'Swarm',
    'SwarmType',
    'SwarmConfig',
    
    # Consensus
    'ConsensusEngine',
    'VotingStrategy',
    'ConflictResolver',
    
    # Memory
    'CollectiveMemory',
    'SharedKnowledge',
    'EmergentPattern',
    
    # Coordinator V1
    'TradingHiveMind',
    'HiveMindConfig',
    'quick_start',
    
    # Military Protocols
    'MilitaryCommandCenter',
    'MilitaryHiveMind',
    'SecurityClearance',
    'ThreatLevel',
    'DefenseCondition',
    'OperationalMode',
    'Rank',
    'MissionType',
    'MissionPlan',
    'RulesOfEngagement',
    'ThreatAssessment',
    'BattleDamageAssessment',
    
    # V2 - Neural Mesh
    'NeuralMesh',
    'TelepathicCommunicator',
    'MeshNode',
    'NeuralLink',
    'NeuralSignal',
    'LinkType',
    'SignalType',
    'create_neural_mesh',
    
    # V2 - Quantum Entanglement
    'QuantumEntanglementEngine',
    'QuantumHivemindBridge',
    'TradingQubit',
    'EntangledPair',
    'QuantumState',
    'EntanglementType',
    'create_quantum_entanglement',
    
    # V2 - Collective Consciousness
    'CollectiveConsciousness',
    'AttentionMechanism',
    'GlobalWorkspace',
    'Perception',
    'CollectiveInsight',
    'SharedMemory',
    'ConsciousnessLevel',
    'AttentionFocus',
    'EmotionalState',
    'create_collective_consciousness',
    
    # V2 - Master Orchestrator
    'HivemindOrchestratorV2',
    'HivemindMode',
    'HivemindHealth',
    'HivemindState',
    'HivemindConfig',
    'HivemindDecision',
    'create_hivemind_v2',
    'run_hivemind_v2',
    
    # Safety Guards
    'SafetyOrchestrator',
    'SafetyConfig',
    'CircuitBreaker',
    'CircuitState',
    'LossLimitGuard',
    'RateLimiter',
    'InputValidator',
    'ThreadSafeState',
    'create_safety_orchestrator',
]

__version__ = '2.0.0'

class HivemindOrchestrator:
    """Auto-generated stub orchestrator for module integration."""
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self._initialized = True
    
    async def start(self):
        """Start the orchestrator."""
        self.running = True
    
    async def stop(self):
        """Stop the orchestrator."""
        self.running = False
    
    def get_status(self):
        """Get orchestrator status."""
        return {"running": self.running, "initialized": self._initialized}

