"""
Core Agent System - Research Lab Grade Architecture

This module implements a unified agent architecture inspired by:
- DeepMind AlphaGo: Policy/Value networks, MCTS, Self-play
- OpenAI GPT-4 Agents: ReAct loop, Tool use, Function calling
- Anthropic Constitutional AI: Multi-stage verification, Safety constraints

Architecture Overview:
├── MasterOrchestrator (Hierarchical Control)
│   ├── PolicyNetwork (What to do - DeepMind)
│   ├── ValueNetwork (How good is it - DeepMind)
│   └── SafetyLayer (Constitutional AI - Anthropic)
│
├── ReActLoop (OpenAI Pattern)
│   ├── Thought → Action → Observation cycle
│   └── Tool calling with reflection
│
├── AgentRegistry (Unified agent management)
│   ├── PlannerAgents
│   ├── ExecutorAgents
│   └── EvaluatorAgents
"""

from .master_orchestrator import MasterOrchestrator, SystemContext, Decision
from .react_loop import ReActLoop, Thought, Action, Observation, ReActTrace
from .constitutional_layer import (
    ConstitutionalAI,
    SafetyPrinciple,
    PrincipleCategory,
    CritiqueResult,
    RevisionResult
)
from .policy_value_network import (
    PolicyNetwork,
    ValueNetwork,
    DualNetwork,
    PolicyOutput,
    ValueOutput
)
from .agent_registry import (
    AgentRegistry,
    AgentRole,
    AgentStatus,
    BaseAgent,
    PlannerAgent,
    ExecutorAgent,
    EvaluatorAgent,
    ResearchAgent,
    SafetyAgent
)
from .tool_registry import (
    ToolRegistry,
    BaseTool,
    ToolSchema,
    ToolCategory,
    ToolPermission
)
from .memory_system import (
    MemorySystem,
    WorkingMemory,
    EpisodicMemory,
    SemanticMemory,
    ProceduralMemory,
    MemoryType
)
from .self_play_loop import (
    SelfPlayLoop,
    Hypothesis,
    Experiment,
    SelfPlayGame
)
from .coordination_core import (
    Task,
    TaskType,
    TaskPriority,
    TaskStatus,
    TaskDecomposer,
    AgentNegotiator,
    ResourceAllocator,
    FailureRecoverySystem
)
from .coordination_core_part2 import (
    CoordinationLayer,
    SharedMemory,
    SharedMemoryScope,
    GovernanceSystem,
    CoordinationLearningLoop
)
from .dynamic_agent_factory import (
    DynamicAgentFactory,
    AgentArchetype,
    AgentTemplate,
    SubAgent
)
from .self_coordinating_core import (
    SelfCoordinatingCore,
    CoordinationMetrics
)
from .integrated_system import IntegratedAgentSystem


class HivemindCoreAgentAdapter:
    """
    Adapter that connects Core Agent System to the Hivemind.
    
    This ensures all core agents (MasterOrchestrator, AgentRegistry,
    ReActLoop, etc.) are controlled by the central hivemind intelligence.
    """
    
    def __init__(self, hivemind_controller=None, config=None):
        self.hivemind = hivemind_controller
        self.config = config or {}
        self.master_orchestrator = None
        self.agent_registry = None
        self.integrated_system = None
        self._initialized = False
        self._running = False
    
    async def initialize(self):
        """Initialize Core Agent System under hivemind control."""
        try:
            self.master_orchestrator = MasterOrchestrator(config=self.config)
            self.agent_registry = AgentRegistry()
            self.integrated_system = IntegratedAgentSystem(config=self.config)
            self._initialized = True
        except Exception as e:
            pass
    
    async def start(self):
        """Start the core agent system."""
        if self.master_orchestrator:
            await self.master_orchestrator.start()
        self._running = True
    
    async def stop(self):
        """Stop the core agent system."""
        if self.master_orchestrator:
            await self.master_orchestrator.stop()
        self._running = False
    
    def get_status(self):
        """Get status of the core agent system."""
        return {
            'initialized': self._initialized,
            'running': self._running,
            'master_orchestrator_active': self.master_orchestrator is not None,
            'agent_registry_active': self.agent_registry is not None,
            'integrated_system_active': self.integrated_system is not None,
            'under_hivemind_control': self.hivemind is not None,
        }


__all__ = [
    # Orchestration
    'MasterOrchestrator',
    'SystemContext',
    'Decision',
    
    # ReAct Loop
    'ReActLoop',
    'Thought',
    'Action',
    'Observation',
    'ReActTrace',
    
    # Constitutional AI
    'ConstitutionalAI',
    'SafetyPrinciple',
    'PrincipleCategory',
    'CritiqueResult',
    'RevisionResult',
    
    # Networks
    'PolicyNetwork',
    'ValueNetwork',
    'DualNetwork',
    'PolicyOutput',
    'ValueOutput',
    
    # Agents
    'AgentRegistry',
    'AgentRole',
    'AgentStatus',
    'BaseAgent',
    'PlannerAgent',
    'ExecutorAgent',
    'EvaluatorAgent',
    'ResearchAgent',
    'SafetyAgent',
    
    # Tools
    'ToolRegistry',
    'BaseTool',
    'ToolSchema',
    'ToolCategory',
    'ToolPermission',
    
    # Memory
    'MemorySystem',
    'WorkingMemory',
    'EpisodicMemory',
    'SemanticMemory',
    'ProceduralMemory',
    'MemoryType',
    
    # Self-Play
    'SelfPlayLoop',
    'Hypothesis',
    'Experiment',
    'SelfPlayGame',
    
    # Coordination
    'Task',
    'TaskType',
    'TaskPriority',
    'TaskStatus',
    'TaskDecomposer',
    'AgentNegotiator',
    'ResourceAllocator',
    'FailureRecoverySystem',
    'CoordinationLayer',
    'SharedMemory',
    'SharedMemoryScope',
    'GovernanceSystem',
    'CoordinationLearningLoop',
    
    # Dynamic Agents
    'DynamicAgentFactory',
    'AgentArchetype',
    'AgentTemplate',
    'SubAgent',
    
    # Self-Coordinating Core
    'SelfCoordinatingCore',
    'CoordinationMetrics',
    
    # Integrated System
    'IntegratedAgentSystem',
    
    # Hivemind Adapter
    'HivemindCoreAgentAdapter',
]
