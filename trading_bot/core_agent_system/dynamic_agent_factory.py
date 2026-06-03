"""
Dynamic Sub-Agent Factory - On-Demand Agent Creation

Allows the AI to create specialized sub-agents dynamically to help with tasks.
All created agents follow DeepMind, OpenAI, and Anthropic patterns.

Key Features:
- Template-based agent creation
- Capability-driven design
- Automatic integration with core systems
- Constitutional AI compliance
- Self-improvement through learning

Patterns:
- DeepMind: Hierarchical agent architecture
- OpenAI: Tool-using agents with ReAct
- Anthropic: Constitutional safety for all agents
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from .agent_registry import AgentRole, AgentMetrics, AgentStatus
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

from .agent_registry import BaseAgent, AgentRole

logger = logging.getLogger(__name__)


# ==================== AGENT TEMPLATES ====================

class AgentArchetype(Enum):
    """Predefined agent archetypes based on research lab patterns"""
    ALPHAGO_PLAYER = "alphago_player"  # DeepMind: Policy + Value networks
    REACT_REASONER = "react_reasoner"  # OpenAI: ReAct loop agent
    CONSTITUTIONAL_GUARDIAN = "constitutional_guardian"  # Anthropic: Safety agent
    RESEARCHER = "researcher"  # Scientific research agent
    OPTIMIZER = "optimizer"  # Optimization specialist
    ANALYST = "analyst"  # Data analysis specialist
    EXECUTOR = "executor"  # Action execution specialist
    MONITOR = "monitor"  # System monitoring agent
    COORDINATOR = "coordinator"  # Multi-agent coordinator


@dataclass
class AgentTemplate:
    """Template for creating agents"""
    template_id: str
    name: str
    archetype: AgentArchetype
    
    # Capabilities
    base_capabilities: List[str]
    required_tools: List[str]
    
    # Architecture
    has_policy_network: bool = False
    has_value_network: bool = False
    has_react_loop: bool = False
    has_constitutional_check: bool = True  # All agents have safety by default
    
    # Configuration
    config_template: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class SubAgent(BaseAgent):
    """A dynamically created sub-agent"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        archetype: AgentArchetype,
        role: AgentRole = AgentRole.EXECUTOR,
        parent_agent_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
        config: Optional[Dict] = None
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            role=role,
            config=config
        )
        self.archetype = archetype
        self.parent_agent_id = parent_agent_id
        self.tools = tools or []

        # Convert string capabilities to AgentCapability objects
        if capabilities:
            from .agent_registry import AgentCapability
            for cap_name in capabilities:
                if isinstance(cap_name, str):
                    self.add_capability(AgentCapability(
                        name=cap_name,
                        description=f"Dynamic capability: {cap_name}",
                        input_schema={},
                        output_schema={}
                    ))

        # Components (injected from core system)
        self.policy_network = None
        self.value_network = None
        self.react_loop = None
        self.constitutional_layer = None
        self.memory_system = None
        self.tool_registry = None
        self.shared_memory = None
        self.coordination_layer = None

        # State
        self.status = "active"  # active, idle, terminated
        self.current_tasks = []
        self.max_concurrent_tasks = 3

        # Performance
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.success_rate = 1.0

        # Metadata
        self.last_active = datetime.now()
        self.metadata = {}

    def _register_capabilities(self):
        """SubAgent capabilities are managed dynamically"""
        pass

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action for compatibility with AgentRegistry"""
        operation = action.get("operation", "execute")

        if operation == "propose":
            # Attempt to use execute_task to get a proposal if appropriate
            try:
                from .coordination_core import Task, TaskType, TaskPriority
                task = Task(
                    task_id=str(uuid.uuid4()),
                    name="proposal_task",
                    task_type=TaskType.ANALYSIS,
                    priority=TaskPriority.MEDIUM,
                    description="Generate action proposal",
                    metadata=action.get('context', {})
                )
                # Some agents might handle this task specifically
                proposal_result = await self.execute_task(task)
                if proposal_result.get('success') and 'type' in proposal_result:
                    return proposal_result
            except Exception as e:
                logger.debug(f"Could not use execute_task for proposal: {e}")

            # Default proposal
            return {
                "type": "hold",
                "action": {"operation": "no_action"},
                "confidence": 0.5,
                "reasoning": f"Dynamic agent {self.name} ({self.archetype.value})"
            }

        return await self._execute_default(action)

    async def execute_task(self, task: Any) -> Dict[str, Any]:
        """
        Execute a task using this agent's capabilities.
        
        Follows the appropriate pattern based on archetype.
        """
        self.last_active = datetime.now()
        
        # Extract context if task is from MasterOrchestrator proposal
        context = task.metadata
        if hasattr(context, 'market_state'):
            # Convert SystemContext to dict
            context = {
                'market_state': context.market_state,
                'portfolio_state': context.portfolio_state,
                'agent_states': context.agent_states,
                'risk_metrics': context.risk_metrics
            }

        try:
            # Add to current tasks
            self.current_tasks.append(task.task_id)
            
            # Execute based on archetype/capabilities
            if self.react_loop and (self.archetype == AgentArchetype.REACT_REASONER or self.archetype == AgentArchetype.ANALYST or self.archetype == AgentArchetype.RESEARCHER or self.archetype == AgentArchetype.COORDINATOR):
                # Use ReAct loop (OpenAI pattern)
                result = await self._execute_with_react(task)
            
            elif self.archetype == AgentArchetype.ALPHAGO_PLAYER and self.policy_network:
                # Use policy/value networks (DeepMind pattern)
                result = await self._execute_with_alphago(task)
            
            elif self.archetype == AgentArchetype.CONSTITUTIONAL_GUARDIAN:
                # Safety verification (Anthropic pattern)
                result = await self._execute_safety_check(task)
            
            else:
                # Default execution
                result = await self._execute_default(task)
            
            # Update performance
            self.tasks_completed += 1
            self.success_rate = self.tasks_completed / (self.tasks_completed + self.tasks_failed)
            
            return result
            
        except Exception as e:
            self.tasks_failed += 1
            self.success_rate = self.tasks_completed / (self.tasks_completed + self.tasks_failed)
            logger.error(f"Agent {self.name} failed task: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            # Remove from current tasks
            if task.task_id in self.current_tasks:
                self.current_tasks.remove(task.task_id)
    
    async def _execute_with_react(self, task: Any) -> Dict[str, Any]:
        """Execute using ReAct loop (OpenAI pattern)"""
        if not self.react_loop:
            return {'success': False, 'error': 'ReAct loop not available'}
        
        # Extract context if task is from MasterOrchestrator proposal
        context = task.metadata
        if hasattr(context, 'market_state'):
            # Convert SystemContext to dict
            context = {
                'market_state': context.market_state,
                'portfolio_state': context.portfolio_state,
                'agent_states': context.agent_states,
                'risk_metrics': context.risk_metrics
            }

        trace = await self.react_loop.run(
            task=task.description,
            context={'task_id': task.task_id, 'metadata': context},
            available_tools=self.tools
        )
        
        return {
            'success': trace.success,
            'result': trace.final_answer,
            'reasoning': trace.to_string(),
            'iterations': len(trace.steps)
        }
    
    async def _execute_with_alphago(self, task: Any) -> Dict[str, Any]:
        """Execute using policy/value networks (DeepMind pattern)"""
        if not self.policy_network or not self.value_network:
            return {'success': False, 'error': 'Policy/Value networks not available'}
        
        # Get state from task
        state = task.metadata.get('state', {})
        
        # Get action from policy network
        policy_output = await self.policy_network.predict(state)
        action = policy_output.top_action
        
        # Evaluate with value network
        value_output = await self.value_network.evaluate(state)
        expected_value = value_output.value
        
        return {
            'success': True,
            'action': action,
            'expected_value': expected_value,
            'confidence': policy_output.confidence,
            'reasoning': f"Policy selected {action['type']} with value {expected_value:.3f}"
        }
    
    async def _execute_safety_check(self, task: Any) -> Dict[str, Any]:
        """Execute safety verification (Anthropic pattern)"""
        if not self.constitutional_layer:
            return {'success': False, 'error': 'Constitutional layer not available'}
        
        # Get action to verify
        action = task.metadata.get('action', {})
        
        # Critique
        critique = await self.constitutional_layer.critique(action)
        
        if not critique.can_proceed:
            # Revise
            revision = await self.constitutional_layer.revise(action, [str(v) for v in critique.violations])
            if revision:
                return {
                    'success': True,
                    'safe': False,
                    'violations': [str(v) for v in critique.violations],
                    'revised_action': revision,
                    'changes': revision.get('revision_notes', [])
                }
        
        return {
            'success': True,
            'safe': True,
            'safety_score': critique.safety_score
        }
    
    async def _execute_default(self, task: Any) -> Dict[str, Any]:
        """Default execution"""
        # Use available tools
        if self.tool_registry and self.tools:
            # Execute using first available tool
            for tool_name in self.tools:
                tool = await self.tool_registry.get_tool(tool_name)
                if tool:
                    # Handle both dictionary actions and task objects
                    params = task.metadata.get('params', {}) if hasattr(task, 'metadata') else task.get('params', {})
                    result = await tool.execute(params)
                    if result.get('success'):
                        return result
        
        task_name = task.name if hasattr(task, 'name') else "unnamed_task"
        return {
            'success': True,
            'result': f"Task {task_name} processed by {self.name}",
            'agent': self.name
        }
    
    def can_handle_task(self, task: Any) -> bool:
        """Check if agent can handle a task"""
        # Check capacity
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return False
        
        # Check capabilities
        required_capabilities = set(task.required_capabilities)
        agent_capability_names = set(c.name for c in self.capabilities)
        
        return required_capabilities.issubset(agent_capability_names)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'archetype': self.archetype.value,
            'role': self.role.value if hasattr(self.role, 'value') else str(self.role),
            'capabilities': [c.name for c in self.capabilities],
            'status': self.status.value if hasattr(self.status, 'value') else str(self.status),
            'current_tasks': len(self.current_tasks),
            'tasks_completed': self.tasks_completed,
            'success_rate': self.success_rate,
            'created_at': self.created_at.isoformat()
        }

    async def initialize(self):
        pass

    async def shutdown(self):
        self.status = "terminated"

    def get_status(self) -> Dict[str, Any]:
        return self.to_dict()


class DynamicAgentFactory:
    """
    Dynamic Sub-Agent Factory
    
    Creates specialized sub-agents on-demand to help with tasks.
    All agents follow research lab patterns (DeepMind, OpenAI, Anthropic).
    
    ┌─────────────────────────────────────────────────────────────┐
    │              DYNAMIC AGENT FACTORY                           │
    │                                                              │
    │  Master AI Request:                                          │
    │  "I need an agent to analyze market sentiment"              │
    │                                                              │
    │  Factory Process:                                            │
    │  1. Analyze Requirements                                     │
    │     ├─ Task Type: Analysis                                  │
    │     ├─ Required Capabilities: [sentiment, nlp, market]      │
    │     └─ Best Archetype: ANALYST                              │
    │                                                              │
    │  2. Select Template                                          │
    │     └─ Template: Analyst Agent (ReAct + Tools)              │
    │                                                              │
    │  3. Create Agent                                             │
    │     ├─ Inject: ReAct Loop (OpenAI)                          │
    │     ├─ Inject: Constitutional Layer (Anthropic)             │
    │     ├─ Inject: Tool Registry                                │
    │     ├─ Inject: Memory System                                │
    │     └─ Assign: Sentiment analysis tools                     │
    │                                                              │
    │  4. Verify Safety                                            │
    │     └─ Constitutional check: PASSED                         │
    │                                                              │
    │  5. Deploy Agent                                             │
    │     └─ Agent "SentimentAnalyzer-001" ready                  │
    │                                                              │
    │  Created Agents: 15 active, 42 total                        │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(
        self,
        policy_network=None,
        value_network=None,
        react_loop=None,
        constitutional_layer=None,
        memory_system=None,
        tool_registry=None,
        agent_registry=None,
        shared_memory=None,
        coordination_layer=None
    ):
        # Core components (injected)
        self.policy_network = policy_network
        self.value_network = value_network
        self.react_loop = react_loop
        self.constitutional_layer = constitutional_layer
        self.memory_system = memory_system
        self.tool_registry = tool_registry
        self.agent_registry = agent_registry
        self.shared_memory = shared_memory
        self.coordination_layer = coordination_layer
        
        # Templates
        self.templates: Dict[str, AgentTemplate] = {}
        
        # Created agents
        self.agents: Dict[str, SubAgent] = {}
        self.agent_count_by_archetype: Dict[AgentArchetype, int] = {}
        
        # Initialize templates
        self._initialize_templates()
        
        logger.info("Dynamic Agent Factory initialized")
    
    def _initialize_templates(self):
        from .agent_registry import AgentRole
        """Initialize agent templates"""
        
        # AlphaGo Player (DeepMind pattern)
        self.templates['alphago_player'] = AgentTemplate(
            template_id='alphago_player',
            name='AlphaGo Player Agent',
            archetype=AgentArchetype.ALPHAGO_PLAYER,
            base_capabilities=['decision_making', 'strategy', 'evaluation'],
            required_tools=['market_data', 'portfolio', 'risk_calculator'],
            has_policy_network=True,
            has_value_network=True,
            has_react_loop=False,
            config_template={'role': AgentRole.PLANNER},
            description='Agent using policy and value networks for decision making'
        )
        
        # ReAct Reasoner (OpenAI pattern)
        self.templates['react_reasoner'] = AgentTemplate(
            template_id='react_reasoner',
            name='ReAct Reasoning Agent',
            archetype=AgentArchetype.REACT_REASONER,
            base_capabilities=['reasoning', 'tool_use', 'problem_solving'],
            required_tools=['market_data', 'strategy_analyzer'],
            has_policy_network=False,
            has_value_network=False,
            has_react_loop=True,
            config_template={'role': AgentRole.PLANNER},
            description='Agent using thought-action-observation reasoning loop'
        )
        
        # Constitutional Guardian (Anthropic pattern)
        self.templates['constitutional_guardian'] = AgentTemplate(
            template_id='constitutional_guardian',
            name='Constitutional Safety Agent',
            archetype=AgentArchetype.CONSTITUTIONAL_GUARDIAN,
            base_capabilities=['safety_verification', 'compliance', 'oversight'],
            required_tools=['risk_calculator'],
            has_policy_network=False,
            has_value_network=False,
            has_react_loop=False,
            config_template={'role': AgentRole.SAFETY},
            description='Agent ensuring safety and constitutional compliance'
        )
        
        # Researcher
        self.templates['researcher'] = AgentTemplate(
            template_id='researcher',
            name='Research Agent',
            archetype=AgentArchetype.RESEARCHER,
            base_capabilities=['research', 'experimentation', 'analysis'],
            required_tools=['backtester', 'strategy_analyzer', 'market_data'],
            has_react_loop=True,
            config_template={'role': AgentRole.RESEARCHER},
            description='Agent conducting research and experiments'
        )
        
        # Optimizer
        self.templates['optimizer'] = AgentTemplate(
            template_id='optimizer',
            name='Optimization Agent',
            archetype=AgentArchetype.OPTIMIZER,
            base_capabilities=['optimization', 'tuning', 'evaluation'],
            required_tools=['backtester', 'strategy_analyzer'],
            has_policy_network=True,
            has_value_network=True,
            config_template={'role': AgentRole.OPTIMIZER},
            description='Agent optimizing strategies and parameters'
        )
        
        # Analyst
        self.templates['analyst'] = AgentTemplate(
            template_id='analyst',
            name='Analysis Agent',
            archetype=AgentArchetype.ANALYST,
            base_capabilities=['analysis', 'data_processing', 'reporting'],
            required_tools=['market_data', 'strategy_analyzer'],
            has_react_loop=True,
            config_template={'role': AgentRole.PLANNER},
            description='Agent analyzing data and generating insights'
        )
        
        # Executor
        self.templates['executor'] = AgentTemplate(
            template_id='executor',
            name='Execution Agent',
            archetype=AgentArchetype.EXECUTOR,
            base_capabilities=['execution', 'validation', 'verification'],
            required_tools=['trade_executor', 'portfolio'],
            has_constitutional_check=True,
            config_template={'role': AgentRole.EXECUTOR},
            description='Agent executing actions with safety checks'
        )
        
        # Monitor
        self.templates['monitor'] = AgentTemplate(
            template_id='monitor',
            name='Monitoring Agent',
            archetype=AgentArchetype.MONITOR,
            base_capabilities=['monitoring', 'alerting', 'tracking'],
            required_tools=['status_checker', 'portfolio', 'risk_calculator'],
            config_template={'role': AgentRole.MONITOR},
            description='Agent monitoring system and market conditions'
        )
        
        # Coordinator
        self.templates['coordinator'] = AgentTemplate(
            template_id='coordinator',
            name='Coordination Agent',
            archetype=AgentArchetype.COORDINATOR,
            base_capabilities=['coordination', 'task_management', 'resource_allocation'],
            required_tools=['status_checker'],
            has_react_loop=True,
            config_template={'role': AgentRole.COORDINATOR},
            description='Agent coordinating multiple sub-agents'
        )
    
    async def create_agent(
        self,
        template_id: str,
        name: Optional[str] = None,
        parent_agent_id: Optional[str] = None,
        additional_capabilities: Optional[List[str]] = None,
        custom_config: Optional[Dict] = None
    ) -> SubAgent:
        """
        Create a new sub-agent from template.
        
        This is the main entry point for dynamic agent creation.
        """
        # Get template
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Generate agent ID and name
        archetype = template.archetype
        count = self.agent_count_by_archetype.get(archetype, 0) + 1
        self.agent_count_by_archetype[archetype] = count
        
        agent_id = f"{archetype.value}_{count}_{uuid.uuid4().hex[:8]}"
        agent_name = name or f"{template.name}-{count:03d}"
        
        # Combine capabilities
        capabilities = template.base_capabilities.copy()
        if additional_capabilities:
            capabilities.extend(additional_capabilities)
        
        # Create agent
        from .agent_registry import AgentRole, AgentMetrics, AgentStatus, AgentCapability
        role = template.config_template.get('role', AgentRole.EXECUTOR)

        # Convert string capabilities to AgentCapability objects
        agent_capabilities = [
            AgentCapability(name=cap, description=f"Capability: {cap}", input_schema={}, output_schema={})
            for cap in capabilities
        ]

        agent = SubAgent(
            agent_id=agent_id,
            name=agent_name,
            archetype=archetype,
            role=role,
            parent_agent_id=parent_agent_id,
            capabilities=capabilities,
            tools=template.required_tools.copy(),
            config=custom_config
        )
        
        # Inject components based on template
        if template.has_policy_network:
            agent.policy_network = self.policy_network
        
        if template.has_value_network:
            agent.value_network = self.value_network
        
        if template.has_react_loop:
            agent.react_loop = self.react_loop
        
        if template.has_constitutional_check:
            agent.constitutional_layer = self.constitutional_layer
        
        # Always inject memory and tools
        agent.memory_system = self.memory_system
        agent.tool_registry = self.tool_registry
        agent.shared_memory = self.shared_memory
        agent.coordination_layer = self.coordination_layer
        
        # Apply custom config to metadata
        if custom_config:
            agent.metadata.update(custom_config)
        
        # Verify safety with Constitutional AI
        if self.constitutional_layer:
            is_safe = await self._verify_agent_safety(agent)
            if not is_safe:
                logger.error(f"Agent {agent_name} failed safety verification")
                raise ValueError("Agent failed constitutional safety check")
        
        # Register agent
        self.agents[agent_id] = agent
        
        # Register with agent registry if available
        if self.agent_registry:
            await self.agent_registry.register_agent(agent)
        
        # Store in memory
        if self.memory_system:
            await self.memory_system.store_knowledge(
                f"agent_{agent_id}",
                agent.to_dict(),
                related=['dynamic_agents', archetype.value]
            )
        
        logger.info(f"Created agent: {agent_name} ({archetype.value})")
        
        return agent
    
    async def _verify_agent_safety(self, agent: SubAgent) -> bool:
        """Verify agent meets constitutional safety requirements"""
        # Create action representing agent creation
        action = {
            'type': 'create_agent',
            'agent_name': agent.name,
            'archetype': agent.archetype.value,
            'capabilities': agent.capabilities,
            'tools': agent.tools
        }
        
        # Critique with Constitutional AI
        critique = await self.constitutional_layer.critique(action)
        
        return critique.can_proceed
    
    async def create_agent_for_task(
        self,
        task: Any,
        parent_agent_id: Optional[str] = None
    ) -> Optional[SubAgent]:
        """
        Automatically create best agent for a task.
        
        Analyzes task requirements and selects appropriate template.
        """
        # Analyze task to determine best archetype
        archetype = self._select_archetype_for_task(task)
        
        # Find template for archetype
        template_id = archetype.value
        
        if template_id not in self.templates:
            logger.warning(f"No template for archetype {archetype.value}")
            return None
        
        # Create agent
        agent = await self.create_agent(
            template_id=template_id,
            name=f"{task.name}_Agent",
            parent_agent_id=parent_agent_id,
            additional_capabilities=task.required_capabilities,
            custom_config={'created_for_task': task.task_id}
        )
        
        return agent
    
    def _select_archetype_for_task(self, task: Any) -> AgentArchetype:
        """Select best archetype for a task"""
        from .coordination_core import TaskType
        
        # Map task types to archetypes
        task_type_mapping = {
            TaskType.ANALYSIS: AgentArchetype.ANALYST,
            TaskType.EXECUTION: AgentArchetype.EXECUTOR,
            TaskType.RESEARCH: AgentArchetype.RESEARCHER,
            TaskType.MONITORING: AgentArchetype.MONITOR,
            TaskType.OPTIMIZATION: AgentArchetype.OPTIMIZER,
            TaskType.COORDINATION: AgentArchetype.COORDINATOR
        }
        
        archetype = task_type_mapping.get(task.task_type, AgentArchetype.REACT_REASONER)
        
        return archetype
    
    async def terminate_agent(self, agent_id: str):
        """Terminate a sub-agent"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        agent.status = "terminated"
        
        # Unregister from agent registry
        if self.agent_registry:
            await self.agent_registry.unregister_agent(agent_id)
        
        logger.info(f"Terminated agent: {agent.name}")
    
    def get_agent(self, agent_id: str) -> Optional[SubAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_active_agents(self) -> List[SubAgent]:
        """Get all active agents"""
        return [
            agent for agent in self.agents.values()
            if agent.status == "active"
        ]
    
    def get_agents_by_capability(self, capability: str) -> List[SubAgent]:
        """Get agents with specific capability"""
        return [
            agent for agent in self.agents.values()
            if any(c.name == capability for c in agent.capabilities) and agent.status == "active"
        ]
    
    def get_best_agent_for_task(self, task: Any) -> Optional[BaseAgent]:
        """Get best existing agent for a task"""
        capable_agents = []

        # 1. Look in dynamic agents
        for agent in self.agents.values():
            status = agent.status.value if hasattr(agent.status, 'value') else str(agent.status)
            if status in ["active", "ready"] and agent.can_handle_task(task):
                capable_agents.append(agent)
        
        # 2. Look in main agent registry if available
        if self.agent_registry:
            # If task has required capabilities, use them for lookup
            if task.required_capabilities:
                # Get agents that have the first required capability
                reg_agents = self.agent_registry.get_agents_by_capability(task.required_capabilities[0])
                for agent in reg_agents:
                    # Check if agent has ALL required capabilities
                    if all(agent.has_capability(c) for c in task.required_capabilities):
                        if agent not in capable_agents:
                            capable_agents.append(agent)
            else:
                # If no specific capabilities required, look at all agents
                for agent in self.agent_registry.agents.values():
                    if agent not in capable_agents:
                        capable_agents.append(agent)

        if not capable_agents:
            return None
        
        # Select agent with best success rate and lowest load
        def get_agent_score(a):
            success_rate = getattr(a, 'success_rate', 1.0)
            if hasattr(a, 'metrics'):
                success_rate = a.metrics.success_rate

            current_tasks_count = len(getattr(a, 'current_tasks', []))
            max_tasks = getattr(a, 'max_concurrent_tasks', 5)

            return (success_rate * 0.6 + (1.0 - current_tasks_count / max_tasks) * 0.4)

        best_agent = max(capable_agents, key=get_agent_score)
        
        return best_agent
    
    def get_status(self) -> Dict[str, Any]:
        """Get factory status"""
        active_agents = self.get_active_agents()
        
        return {
            'total_agents_created': len(self.agents),
            'active_agents': len(active_agents),
            'agents_by_archetype': {
                archetype.value: count
                for archetype, count in self.agent_count_by_archetype.items()
            },
            'templates_available': len(self.templates),
            'average_success_rate': (
                sum(a.success_rate for a in active_agents) / len(active_agents)
                if active_agents else 0.0
            ),
            'total_tasks_completed': sum(a.tasks_completed for a in self.agents.values()),
            'agents': [a.to_dict() for a in active_agents[:10]]  # First 10
        }


# Export
__all__ = [
    'AgentArchetype', 'AgentTemplate', 'SubAgent', 'DynamicAgentFactory'
]
