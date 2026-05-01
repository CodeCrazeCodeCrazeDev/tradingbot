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
        UniversalHivemindController,
        HivemindAgentController,
        AgentController,
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

# Governed advanced hivemind patterns
try:
    from .governed_hivemind import (
        AgentEvolutionGateReport,
        AgentSignalProfile,
        GovernedHivemindEngine,
        HivemindCapabilityFamily,
        HivemindCapabilitySpec,
        HivemindCapabilityStatus,
        HivemindGateDecision,
        HivemindGovernanceConfig,
        HivemindValidationReport,
        HivemindVoteGuardReport,
        SignalDiversityAudit,
        create_governed_hivemind,
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

    # Governed advanced hivemind patterns
    'AgentEvolutionGateReport',
    'AgentSignalProfile',
    'GovernedHivemindEngine',
    'HivemindCapabilityFamily',
    'HivemindCapabilitySpec',
    'HivemindCapabilityStatus',
    'HivemindGateDecision',
    'HivemindGovernanceConfig',
    'HivemindValidationReport',
    'HivemindVoteGuardReport',
    'SignalDiversityAudit',
    'create_governed_hivemind',
]

__version__ = '2.0.0'

# Import all agent systems under hivemind control
# These imports make all agents accessible through the hivemind module

# RadarAI Agents
try:
    from ..radar_ai.agents import (
        MetaOrchestrator as RadarMetaOrchestrator,
        DataFusionAgent,
        OntologyAgent,
        IntelligenceAgent,
        StrategyAgent,
        BullAgent,
        BearAgent,
        SimulationAgent,
        RiskEvaluationAgent,
        ExecutionAgent,
        ExperimentInfrastructure,
    )
except ImportError:
    pass

# RadarAI Hivemind Controller
try:
    from ..radar_ai.hivemind_controller import (
        HivemindController as RadarHivemindController,
        AgentSwarm,
        OntologyDrivenAgent,
        AgentRole,
        AgentTier,
        AgentDecision,
        SwarmConsensus,
        ConsensusMethod as AgentConsensusMethod,
    )
except ImportError:
    pass

# Agents2 System
try:
    from ..agents2 import (
        MultiAgentCoordinator,
        RiskManagerAgent as Agents2RiskManager,
    )
    from ..agents2.base_agent import BaseAgent, AgentProposal
    from ..agents2.specialized_agents import (
        RiskManagerAgent,
        PortfolioManagerAgent,
        StrategyOptimizerAgent,
    )
except ImportError:
    pass

# Multi-Agent Debate System
try:
    from ..agents.multi_agent_debate import (
        MultiAgentDebateSystem,
        DebateTopic,
        DebateResult,
        DebateAgent,
    )
except ImportError:
    pass

# Self-Coordinating AI
try:
    from ..self_coordinating_ai import (
        SelfCoordinatingAIOrchestrator,
        CoreProductionSystem,
        SandboxExecutor,
        ComputeBudgetController,
        ExperimentRegistry,
        DataIntegrityFirewall,
        CodeSafetyScanner,
        PromotionSystem,
        MarketOpportunityDiscovery,
        SelfProgrammingProposer,
    )
except ImportError:
    pass

# Foundation Agents
try:
    from ..foundation_agents.foundation_agent_orchestrator import (
        FoundationAgentOrchestrator,
    )
except ImportError:
    pass

# Core Agent System
try:
    from ..core_agent_system import (
        HivemindCoreAgentAdapter,
        MasterOrchestrator,
        AgentRegistry,
        ReActLoop,
        IntegratedAgentSystem,
    )
except ImportError:
    pass

# AI Core Agents
try:
    from ..ai_core.agents import (
        HivemindAICoreAdapter,
        AICoreOrchestrator,
        ExecutorAgent,
        PlannerAgent,
        VerifierAgent,
        SafetyValidator,
    )
except ImportError:
    pass

# Improvement Agent
try:
    from ..improvement_agent import (
        HivemindImprovementAdapter,
        ImprovementAgent,
        DeepAnalyzer,
        WeaknessDetector,
        ImprovementProposer,
    )
except ImportError:
    pass

# Aletheia Autonomous
try:
    from ..aletheia_autonomous import (
        HivemindAletheiaAdapter,
        AletheiaOrchestrator,
        StrategyGenerator,
        StrategyVerifier,
        StrategyReviser,
    )
except ImportError:
    pass


# Aliases for backward compatibility - use UniversalHivemindController
class HivemindAgentController(UniversalHivemindController):
    """Backward compatible alias for UniversalHivemindController."""
    pass

class AgentController(UniversalHivemindController):
    """Backward compatible alias for UniversalHivemindController."""
    pass

class HivemindOrchestrator(UniversalHivemindController):
    """Backward compatible alias for UniversalHivemindController."""
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
    
    # Master Controllers
    'UniversalHivemindController',
    'HivemindAgentController',
    'HivemindOrchestrator',
    'AgentController',
    
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
    
    # RadarAI Agents
    'RadarMetaOrchestrator',
    'DataFusionAgent',
    'OntologyAgent',
    'IntelligenceAgent',
    'StrategyAgent',
    'BullAgent',
    'BearAgent',
    'SimulationAgent',
    'RiskEvaluationAgent',
    'ExecutionAgent',
    'ExperimentInfrastructure',
    
    # RadarAI Hivemind
    'RadarHivemindController',
    'AgentSwarm',
    'OntologyDrivenAgent',
    'AgentRole',
    'AgentTier',
    'AgentDecision',
    'SwarmConsensus',
    'AgentConsensusMethod',
    
    # Agents2
    'BaseAgent',
    'AgentProposal',
    'MultiAgentCoordinator',
    'RiskManagerAgent',
    'PortfolioManagerAgent',
    'StrategyOptimizerAgent',
    'Agents2RiskManager',
    
    # Multi-Agent Debate
    'MultiAgentDebateSystem',
    'DebateTopic',
    'DebateResult',
    'DebateAgent',
    
    # Self-Coordinating AI
    'SelfCoordinatingAIOrchestrator',
    'CoreProductionSystem',
    'SandboxExecutor',
    'ComputeBudgetController',
    'ExperimentRegistry',
    'DataIntegrityFirewall',
    'CodeSafetyScanner',
    'PromotionSystem',
    'MarketOpportunityDiscovery',
    'SelfProgrammingProposer',
    
    # Foundation Agents
    'FoundationAgentOrchestrator',
    
    # Core Agent System
    'HivemindCoreAgentAdapter',
    'MasterOrchestrator',
    'AgentRegistry',
    'ReActLoop',
    'IntegratedAgentSystem',
    
    # AI Core Agents
    'HivemindAICoreAdapter',
    'AICoreOrchestrator',
    'ExecutorAgent',
    'PlannerAgent',
    'VerifierAgent',
    'SafetyValidator',
    
    # Improvement Agent
    'HivemindImprovementAdapter',
    'ImprovementAgent',
    'DeepAnalyzer',
    'WeaknessDetector',
    'ImprovementProposer',
    
    # Aletheia Autonomous
    'HivemindAletheiaAdapter',
    'AletheiaOrchestrator',
    'StrategyGenerator',
    'StrategyVerifier',
    'StrategyReviser',
]

__version__ = '2.0.0'
