"""
AlphaAlgo Perplexity Trading Architecture
============================================================

A Perplexity Computer-style multi-model orchestration system
specifically designed for trading decisions.

ARCHITECTURE OVERVIEW:
======================

┌─────────────────────────────────────────────────────────────────────────┐
│                    PERPLEXITY TRADING ORCHESTRATOR                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     TASK DECOMPOSITION LAYER                        │ │
│  │  "Analyze EURUSD for entry" → [Research, Technical, Risk, Execute] │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     MULTI-MODEL ROUTER                              │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │ │
│  │  │ RESEARCH │ │TECHNICAL │ │   RISK   │ │EXECUTION │ │ REASONING│ │ │
│  │  │  AGENT   │ │  AGENT   │ │  AGENT   │ │  AGENT   │ │  AGENT   │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     RETRIEVAL PIPELINE                              │ │
│  │  Market Data → News → Sentiment → Fundamentals → Alternative Data  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     PERSISTENT MEMORY                               │ │
│  │  Short-term (session) │ Medium-term (7d) │ Long-term (forever)     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     ASSEMBLY & QA LAYER                             │ │
│  │  Cross-reference │ Verification │ Citation │ Confidence Scoring    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     HUMAN-IN-THE-LOOP                               │ │
│  │  High-stakes actions require explicit approval                      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

KEY PRINCIPLES (from Perplexity Computer):
==========================================
1. MULTI-MODEL ROUTING: Different models for different subtasks
2. TASK DECOMPOSITION: Break complex queries into discrete subtasks
3. RETRIEVAL-AUGMENTED: Real-time data retrieval with citation
4. PERSISTENT MEMORY: Context across sessions (short/medium/long-term)
5. ORCHESTRATION GRAPH: Dependency management between subtasks
6. QA VERIFICATION: Cross-reference outputs against sources
7. HUMAN-IN-THE-LOOP: High-stakes actions require approval

TRADING-SPECIFIC ADAPTATIONS:
=============================
- Research Agent: Market research, news, fundamentals
- Technical Agent: Chart patterns, indicators, price action
- Risk Agent: Position sizing, drawdown, exposure
- Execution Agent: Order routing, timing, slippage
- Reasoning Agent: Multi-step analysis, chain-of-thought
- Sentiment Agent: Social media, news sentiment
- Macro Agent: Economic indicators, central bank policy
- Microstructure Agent: Order flow, liquidity, market depth

USAGE:
======
```python
from trading_bot.perplexity_trading import PerplexityTradingOrchestrator

orchestrator = PerplexityTradingOrchestrator()
await orchestrator.initialize()

# Simple query
decision = await orchestrator.analyze("Should I buy EURUSD?")

# Complex multi-step query
decision = await orchestrator.analyze(
    "Research EURUSD fundamentals, analyze the 4H chart for entry, "
    "calculate position size for 1% risk, and prepare a limit order "
    "at the next support level."
)

# Access decision details
print(decision.action)           # BUY, SELL, HOLD
print(decision.confidence)       # 0.0 - 1.0
print(decision.reasoning_chain)  # Step-by-step reasoning
print(decision.citations)        # Data sources used
print(decision.subtask_results)  # Results from each agent
```
"""

# Core types
try:
    from .core_types import (
        TradingQuery,
        TradingDecision,
        SubTask,
        SubTaskResult,
        AgentType,
        TaskType,
        MemoryLevel,
        RetrievalSource,
        Citation,
        QACheckResult,
    )
except ImportError as e:
    pass

# Task decomposition
try:
    from .task_decomposer import (
        TaskDecomposer,
        TaskGraph,
        TaskDependency,
    )
except ImportError as e:
    pass

# Multi-model router
try:
    from .model_router import (
        ModelRouter,
        AgentConfig,
        RoutingDecision,
    )
except ImportError as e:
    pass

# Specialized agents
try:
    from .trading_agents import (
        BaseTradingAgent,
        ResearchAgent,
        TechnicalAgent,
        RiskAgent,
        ExecutionAgent,
        ReasoningAgent,
        SentimentAgent,
        MacroAgent,
        MicrostructureAgent,
    )
except ImportError as e:
    pass

# Retrieval pipeline
try:
    from .retrieval_pipeline import (
        RetrievalPipeline,
        MarketDataRetriever,
        NewsRetriever,
        SentimentRetriever,
        FundamentalsRetriever,
        AlternativeDataRetriever,
    )
except ImportError as e:
    pass

# Persistent memory
try:
    from .persistent_memory import (
        PersistentMemory,
        MemoryEntry,
        MemoryQuery,
        KnowledgeGraph,
    )
except ImportError as e:
    pass

# Assembly and QA
try:
    from .assembly_qa import (
        AssemblyEngine,
        QAVerifier,
        CitationTracker,
        ConfidenceScorer,
    )
except ImportError as e:
    pass

# Human-in-the-loop
try:
    from .human_approval import (
        HumanApprovalGate,
        ApprovalRequest,
        ApprovalDecision,
    )
except ImportError as e:
    pass

# Research guardrails
try:
    from .research_guardrails import (
        PerplexityTradingGuard,
        ResearchGuardConfig,
        ResearchGuardReport,
    )
except ImportError as e:
    pass

# Main orchestrator
try:
    from .orchestrator import (
        PerplexityTradingOrchestrator,
        OrchestratorConfig,
        quick_start,
    )
except ImportError as e:
    pass

# Quant Agent
try:
    from .quant_agent import (
        QuantAgent,
        QuantStrategy,
        RegimeType,
        QuantSignal,
    )
except ImportError as e:
    pass

# Military-grade protocols
try:
    from .military_protocols import (
        MilitaryPerplexityOrchestrator,
        StrategicCommand,
        MilitaryROE,
        TacticalOrder,
        TacticalObjective,
        IntelligenceReport,
        IntelligenceCell,
        CombatReadiness,
        AlertStatus,
    )
except ImportError as e:
    pass

# V2 Components - Deep Research Engine
try:
    from .deep_research_engine import (
        DeepResearchEngine,
        SourceRegistry,
        InformationSynthesizer,
        ResearchFinding,
        ResearchQuery,
        Citation as ResearchCitation,
        SourceType,
        SourceReliability,
        ResearchDepth,
        create_deep_research_engine,
    )
except ImportError:
    pass

# V2 Components - Reasoning Chains
try:
    from .reasoning_chains import (
        ReasoningChainEngine,
        ReasoningChain,
        ReasoningStep,
        Thought,
        TreeOfThoughts,
        ThoughtVerifier,
        SelfConsistencyChecker,
        ReasoningType,
        ThoughtStatus,
        ConfidenceLevel,
        create_reasoning_chain_engine,
    )
except ImportError:
    pass

# V2 Components - Knowledge Graph
try:
    from .knowledge_graph import (
        KnowledgeGraph as TradingKnowledgeGraph,
        KnowledgeGraphReasoner,
        Entity,
        Relation,
        GraphQuery,
        EntityType,
        RelationType,
        create_knowledge_graph,
    )
except ImportError:
    pass

# V2 Master Orchestrator
try:
    from .perplexity_orchestrator_v2 import (
        PerplexityOrchestratorV2,
        PerplexityMode,
        PerplexityState,
        PerplexityConfig,
        PerplexityDecision,
        QueryComplexity,
        create_perplexity_v2,
        quick_start_perplexity_v2,
    )
except ImportError:
    pass

__all__ = [
    # Core types V1
    'TradingQuery',
    'TradingDecision',
    'SubTask',
    'SubTaskResult',
    'AgentType',
    'TaskType',
    'MemoryLevel',
    'RetrievalSource',
    'Citation',
    'QACheckResult',
    # Task decomposition
    'TaskDecomposer',
    'TaskGraph',
    'TaskDependency',
    # Model router
    'ModelRouter',
    'AgentConfig',
    'RoutingDecision',
    # Agents
    'BaseTradingAgent',
    'ResearchAgent',
    'TechnicalAgent',
    'RiskAgent',
    'ExecutionAgent',
    'ReasoningAgent',
    'SentimentAgent',
    'MacroAgent',
    'MicrostructureAgent',
    # Retrieval
    'RetrievalPipeline',
    'MarketDataRetriever',
    'NewsRetriever',
    'SentimentRetriever',
    'FundamentalsRetriever',
    'AlternativeDataRetriever',
    # Memory
    'PersistentMemory',
    'MemoryEntry',
    'MemoryQuery',
    'KnowledgeGraph',
    # Assembly & QA
    'AssemblyEngine',
    'QAVerifier',
    'CitationTracker',
    'ConfidenceScorer',
    # Human approval
    'HumanApprovalGate',
    'ApprovalRequest',
    'ApprovalDecision',
    # Research guardrails
    'PerplexityTradingGuard',
    'ResearchGuardConfig',
    'ResearchGuardReport',
    # Orchestrator V1
    'PerplexityTradingOrchestrator',
    'OrchestratorConfig',
    'quick_start',
    # Quant Agent
    'QuantAgent',
    'QuantStrategy',
    'RegimeType',
    'QuantSignal',
    # Military Protocols
    'MilitaryPerplexityOrchestrator',
    'StrategicCommand',
    'MilitaryROE',
    'TacticalOrder',
    'TacticalObjective',
    'IntelligenceReport',
    'IntelligenceCell',
    'CombatReadiness',
    'AlertStatus',
    
    # V2 - Deep Research Engine
    'DeepResearchEngine',
    'SourceRegistry',
    'InformationSynthesizer',
    'ResearchFinding',
    'ResearchQuery',
    'ResearchCitation',
    'SourceType',
    'SourceReliability',
    'ResearchDepth',
    'create_deep_research_engine',
    
    # V2 - Reasoning Chains
    'ReasoningChainEngine',
    'ReasoningChain',
    'ReasoningStep',
    'Thought',
    'TreeOfThoughts',
    'ThoughtVerifier',
    'SelfConsistencyChecker',
    'ReasoningType',
    'ThoughtStatus',
    'ConfidenceLevel',
    'create_reasoning_chain_engine',
    
    # V2 - Knowledge Graph
    'TradingKnowledgeGraph',
    'KnowledgeGraphReasoner',
    'Entity',
    'Relation',
    'GraphQuery',
    'EntityType',
    'RelationType',
    'create_knowledge_graph',
    
    # V2 - Master Orchestrator
    'PerplexityOrchestratorV2',
    'PerplexityMode',
    'PerplexityState',
    'PerplexityConfig',
    'PerplexityDecision',
    'QueryComplexity',
    'create_perplexity_v2',
    'quick_start_perplexity_v2',
]
