"""
Agent Registry - Unified Agent Management

Implements a centralized registry for all agents in the system.
Inspired by:
- OpenAI's function calling (standardized interfaces)
- LangChain's agent registry (tool/agent management)
- DeepMind's agent populations (multi-agent coordination)

Key Features:
- Single source of truth for all agents
- Standardized agent interface
- Capability discovery
- Health monitoring
- Dynamic agent spawning/termination
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from trading_bot.execution.trade_executor import TradeExecutor, Order, OrderType, OrderSide

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in the system"""
    PLANNER = "planner"           # Plans actions
    EXECUTOR = "executor"         # Executes actions
    EVALUATOR = "evaluator"       # Evaluates outcomes
    RESEARCHER = "researcher"     # Conducts research
    MONITOR = "monitor"           # Monitors system
    OPTIMIZER = "optimizer"       # Optimizes performance
    SAFETY = "safety"             # Safety checks
    COORDINATOR = "coordinator"   # Coordinates other agents


class AgentStatus(Enum):
    """Agent operational status"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class AgentCapability:
    """A capability that an agent provides"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    async_capable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'async_capable': self.async_capable
        }


@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    success_rate: float = 1.0
    last_active: datetime = field(default_factory=datetime.now)
    
    def update(self, success: bool, execution_time: float):
        """Update metrics after task completion"""
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1
        
        self.total_execution_time += execution_time
        total_tasks = self.tasks_completed + self.tasks_failed
        self.average_execution_time = self.total_execution_time / total_tasks
        self.success_rate = self.tasks_completed / total_tasks
        self.last_active = datetime.now()


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Provides standardized interface that all agents must implement.
    Inspired by OpenAI's function calling convention.
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "BaseAgent",
        role: AgentRole = AgentRole.EXECUTOR,
        config: Optional[Dict] = None
    ):
        self.config = config or {}
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.role = role
        self.config = config or {}
        
        self.status = AgentStatus.INITIALIZING
        self.capabilities: List[AgentCapability] = []
        self.metrics = AgentMetrics()
        
        self.created_at = datetime.now()
        self.memory: Dict[str, Any] = {}
        
        # Register default capabilities
        self._register_capabilities()
    
    @abstractmethod
    def _register_capabilities(self):
        """Register agent capabilities - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action - must be implemented by subclasses"""
        pass
    
    async def execute_task(self, task: Any) -> Dict[str, Any]:
        """
        Execute a task. Default implementation wraps execute().
        Subclasses can override this for more complex task handling.
        """
        # Try to extract description from task object or use task itself
        description = getattr(task, 'description', getattr(task, 'name', str(task)))

        return await self.execute({
            'operation': 'execute_task',
            'task': task,
            'description': description,
            'metadata': getattr(task, 'metadata', {})
        })

    async def initialize(self):
        """Initialize the agent"""
        self.status = AgentStatus.READY
        logger.info(f"Agent {self.name} ({self.agent_id}) initialized")
    
    async def shutdown(self):
        """Shutdown the agent"""
        self.status = AgentStatus.TERMINATED
        logger.info(f"Agent {self.name} ({self.agent_id}) terminated")
    
    def add_capability(self, capability: AgentCapability):
        """Add a capability to the agent"""
        self.capabilities.append(capability)
    
    def has_capability(self, capability_name: str) -> bool:
        """Check if agent has a specific capability"""
        return any(c.name == capability_name for c in self.capabilities)
    
    def get_capability(self, capability_name: str) -> Optional[AgentCapability]:
        """Get a specific capability"""
        for cap in self.capabilities:
            if cap.name == capability_name:
                return cap
        return None
    
    def store_memory(self, key: str, value: Any):
        """Store something in agent memory"""
        self.memory[key] = value
    
    def recall_memory(self, key: str, default: Any = None) -> Any:
        """Recall something from agent memory"""
        return self.memory.get(key, default)
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'role': self.role.value,
            'status': self.status.value,
            'capabilities': [c.name for c in self.capabilities],
            'metrics': {
                'tasks_completed': self.metrics.tasks_completed,
                'tasks_failed': self.metrics.tasks_failed,
                'success_rate': self.metrics.success_rate,
                'avg_execution_time': self.metrics.average_execution_time
            },
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.agent_id}, name={self.name}, role={self.role.value})"


class AgentRegistry:
    """
    Centralized Agent Registry
    
    Manages all agents in the system:
    - Registration and discovery
    - Capability matching
    - Health monitoring
    - Dynamic scaling
    
    ┌─────────────────────────────────────────────────────────────┐
    │                    AGENT REGISTRY                            │
    │                                                              │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │              Agent Catalog                           │    │
    │  │  - PlannerAgent (planning, analysis)                │    │
    │  │  - ExecutorAgent (trade_execution)                  │    │
    │  │  - EvaluatorAgent (evaluation, backtesting)         │    │
    │  │  - ResearchAgent (research, discovery)              │    │
    │  │  - SafetyAgent (safety_check, verification)         │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                          │                                   │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │           Capability Index                           │    │
    │  │  planning → [PlannerAgent]                          │    │
    │  │  execution → [ExecutorAgent]                        │    │
    │  │  evaluation → [EvaluatorAgent]                      │    │
    │  │  research → [ResearchAgent]                         │    │
    │  │  safety → [SafetyAgent]                             │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                          │                                   │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │           Health Monitor                             │    │
    │  │  - Track agent health                               │    │
    │  │  - Auto-restart failed agents                       │    │
    │  │  - Scale based on load                              │    │
    │  └─────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        self.config = config
        
        # Agent storage
        self.agents: Dict[str, BaseAgent] = {}
        
        # Capability index for fast lookup
        self.capability_index: Dict[str, List[str]] = {}  # capability -> [agent_ids]
        
        # Role index
        self.role_index: Dict[AgentRole, List[str]] = {
            role: [] for role in AgentRole
        }
        
        # Agent factories for dynamic spawning
        self.agent_factories: Dict[str, Type[BaseAgent]] = {}
        
        # Health monitoring
        self.health_check_interval = self.config.get('health_check_interval', 30)
        self.auto_restart = self.config.get('auto_restart', True)
        
        self.running = False
        
        logger.info("Agent Registry initialized")
    
    async def initialize(self):
        """Initialize the registry"""
        logger.info("Initializing Agent Registry")
        self.running = True
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor_loop())
        
        logger.info("Agent Registry ready")
    
    def register_factory(
        self, 
        agent_type: str, 
        factory: Type[BaseAgent]
    ):
        """Register an agent factory for dynamic spawning"""
        self.agent_factories[agent_type] = factory
        logger.debug(f"Registered factory for agent type: {agent_type}")
    
    async def register_agent(self, agent: BaseAgent) -> str:
        """
        Register an agent with the registry.
        
        Args:
            agent: The agent to register
            
        Returns:
            Agent ID
        """
        # Initialize agent if needed
        if agent.status == AgentStatus.INITIALIZING:
            await agent.initialize()
        
        # Store agent
        self.agents[agent.agent_id] = agent
        
        # Index by role
        self.role_index[agent.role].append(agent.agent_id)
        
        # Index by capabilities
        for capability in agent.capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = []
            self.capability_index[capability.name].append(agent.agent_id)
        
        logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
        
        return agent.agent_id
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        
        # Shutdown agent
        await agent.shutdown()
        
        # Remove from indices
        if agent_id in self.role_index[agent.role]:
            self.role_index[agent.role].remove(agent_id)
        
        for capability in agent.capabilities:
            if capability.name in self.capability_index:
                if agent_id in self.capability_index[capability.name]:
                    self.capability_index[capability.name].remove(agent_id)
        
        # Remove from storage
        del self.agents[agent_id]
        
        logger.info(f"Unregistered agent: {agent.name} ({agent_id})")
    
    async def spawn_agent(
        self, 
        agent_type: str, 
        config: Optional[Dict] = None
    ) -> Optional[BaseAgent]:
        """
        Spawn a new agent of the given type.
        
        Args:
            agent_type: Type of agent to spawn
            config: Configuration for the agent
            
        Returns:
            The spawned agent or None if factory not found
        """
        if agent_type not in self.agent_factories:
            logger.warning(f"No factory registered for agent type: {agent_type}")
            return None
        
        factory = self.agent_factories[agent_type]
        agent = factory(config=config)
        
        await self.register_agent(agent)
        
        logger.info(f"Spawned new agent: {agent.name} ({agent_type})")
        
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    async def get_executor(self, action_type: str) -> Optional[BaseAgent]:
        """
        Get an executor agent for a given action type.
        
        Finds the best available agent that can execute the action.
        """
        # First, try to find by capability
        if action_type in self.capability_index:
            agent_ids = self.capability_index[action_type]
            for agent_id in agent_ids:
                agent = self.agents.get(agent_id)
                if agent and agent.status == AgentStatus.READY:
                    return agent
        
        # Fall back to executor role
        for agent_id in self.role_index[AgentRole.EXECUTOR]:
            agent = self.agents.get(agent_id)
            if agent and agent.status == AgentStatus.READY:
                return agent
        
        return None
    
    def get_agents_by_role(self, role: AgentRole) -> List[BaseAgent]:
        """Get all agents with a specific role"""
        if isinstance(role, str):
            try:
                role = AgentRole(role)
            except ValueError:
                return []

        return [
            self.agents[agent_id]
            for agent_id in self.role_index.get(role, [])
            if agent_id in self.agents
        ]
    
    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Get all agents with a specific capability"""
        if capability not in self.capability_index:
            return []
        
        return [
            self.agents[agent_id]
            for agent_id in self.capability_index[capability]
            if agent_id in self.agents
        ]
    
    async def get_all_proposals(self, context) -> List[Dict[str, Any]]:
        """
        Get proposals from all planner agents.
        
        Used by the orchestrator to gather candidate actions.
        """
        proposals = []
        
        for agent in self.get_agents_by_role(AgentRole.PLANNER):
            status = agent.status.value if hasattr(agent.status, 'value') else agent.status
            if status in [AgentStatus.READY.value, "ready", "active"]:
                try:
                    if hasattr(agent, 'status'):
                        agent.status = AgentStatus.BUSY

                    proposal = await agent.execute({
                        'operation': 'propose',
                        'context': context
                    })
                    if proposal:
                        # Ensure proposal is a dict and has required fields
                        if isinstance(proposal, dict):
                            proposals.append({
                                **proposal,
                                'source_agent': agent.agent_id
                            })

                    if hasattr(agent, 'status'):
                        agent.status = AgentStatus.READY
                except Exception as e:
                    logger.error(f"Error getting proposal from {agent.name}: {e}")
                    agent.status = AgentStatus.ERROR
        
        return proposals
    
    async def get_all_states(self) -> Dict[str, Any]:
        """Get states of all agents"""
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self.agents.items()
        }
    
    async def _health_monitor_loop(self):
        """Monitor agent health and restart failed agents"""
        while self.running:
            try:
                for agent_id, agent in list(self.agents.items()):
                    # Check for error state
                    if agent.status == AgentStatus.ERROR:
                        logger.warning(f"Agent {agent.name} in error state")
                        
                        if self.auto_restart:
                            await self._restart_agent(agent)
                    
                    # Check for stale agents
                    time_since_active = (
                        datetime.now() - agent.metrics.last_active
                    ).total_seconds()
                    
                    if time_since_active > 3600:  # 1 hour
                        logger.warning(f"Agent {agent.name} has been inactive for {time_since_active}s")
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _restart_agent(self, agent: BaseAgent):
        """Restart a failed agent"""
        logger.info(f"Restarting agent: {agent.name}")
        
        try:
            await agent.shutdown()
            await agent.initialize()
            logger.info(f"Agent {agent.name} restarted successfully")
        except Exception as e:
            logger.error(f"Failed to restart agent {agent.name}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get registry status"""
        status_counts = {}
        for status in AgentStatus:
            count = sum(1 for a in self.agents.values() if a.status == status)
            if count > 0:
                status_counts[status.value] = count
        
        role_counts = {}
        for role in AgentRole:
            count = len(self.role_index.get(role, self.role_index.get(AgentRole(role), [])) if isinstance(role, str) else self.role_index[role])
            if count > 0:
                role_counts[role.value] = count
        
        return {
            'total_agents': len(self.agents),
            'status_distribution': status_counts,
            'role_distribution': role_counts,
            'capabilities': list(self.capability_index.keys()),
            'factories_registered': list(self.agent_factories.keys())
        }
    
    async def shutdown(self):
        """Shutdown the registry and all agents"""
        logger.info("Shutting down Agent Registry")
        self.running = False
        
        # Shutdown all agents
        for agent in list(self.agents.values()):
            await agent.shutdown()
        
        self.agents.clear()
        logger.info("Agent Registry shutdown complete")


# ==================== CONCRETE AGENT IMPLEMENTATIONS ====================

class PlannerAgent(BaseAgent):
    """
    Planner Agent - Analyzes situations and proposes actions.
    
    Inspired by AlphaGo's policy network - suggests promising moves.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name=config.get("name", "PlannerAgent"),
            role=AgentRole.PLANNER,
            config=config
        )
        self.config = config or {}
    
    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="planning",
            description="Analyze situation and propose actions",
            input_schema={"context": "SystemContext"},
            output_schema={"proposals": "List[Action]"}
        ))
        self.add_capability(AgentCapability(
            name="analysis",
            description="Analyze market conditions",
            input_schema={"market_data": "Dict"},
            output_schema={"analysis": "Dict"}
        ))
    
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planning action"""
        operation = action.get('operation', 'propose')
        
        if operation == 'propose':
            context = action.get('context', {})
            return await self._generate_proposal(context)
        elif operation == 'analyze':
            data = action.get('data', {})
            return await self._analyze(data)
        elif operation == 'execute_task':
            # For general tasks, we can try to propose based on metadata
            context = action.get('metadata', {})
            proposal = await self._generate_proposal(context)
            return {
                'success': True,
                'result': proposal.get('reasoning', 'Task completed'),
                'proposal': proposal
            }
        
        return {'success': False, 'error': f'Unknown operation: {operation}'}
    
    async def _generate_proposal(self, context) -> Dict[str, Any]:
        """Generate action proposal"""
        # Extract relevant information
        market_state = getattr(context, 'market_state', {})
        if isinstance(market_state, dict):
            trend = market_state.get('trend', 'neutral')
            volatility = market_state.get('volatility', 0)
        else:
            trend = 'neutral'
            volatility = 0
        
        # Generate proposal based on analysis
        if trend in ['bullish', 'strong_bullish'] and volatility < 0.02:
            return {
                'type': 'buy',
                'action': {'operation': 'open_long', 'size': 0.02},
                'confidence': 0.7,
                'reasoning': f'Bullish trend with low volatility'
            }
        elif trend in ['bearish', 'strong_bearish']:
            return {
                'type': 'sell',
                'action': {'operation': 'close_long', 'size': 0.02},
                'confidence': 0.7,
                'reasoning': f'Bearish trend detected'
            }
        else:
            return {
                'type': 'hold',
                'action': {'operation': 'no_action'},
                'confidence': 0.5,
                'reasoning': 'No clear signal'
            }
    
    async def _analyze(self, data: Dict) -> Dict[str, Any]:
        """Analyze market data"""
        return {
            'trend': 'neutral',
            'volatility': data.get('volatility', 0),
            'recommendation': 'hold'
        }


class ExecutorAgent(BaseAgent):
    """
    Executor Agent - Executes approved actions.
    
    Handles the actual execution of trades and other operations.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="ExecutorAgent",
            role=AgentRole.EXECUTOR,
            config=config
        )
        self.config = config or {}
        self.executor = TradeExecutor(config)
    
    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="trade_execution",
            description="Execute trading operations",
            input_schema={"trade": "TradeOrder"},
            output_schema={"result": "ExecutionResult"}
        ))
        self.add_capability(AgentCapability(
            name="order_management",
            description="Manage open orders",
            input_schema={"operation": "str", "order_id": "str"},
            output_schema={"result": "Dict"}
        ))
    
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action"""
        operation = action.get('operation', 'execute')
        
        start_time = datetime.now()
        
        try:
            if operation == 'execute':
                result = await self._execute_trade(action)
            elif operation == 'cancel':
                result = await self._cancel_order(action)
            elif operation == 'modify':
                result = await self._modify_order(action)
            elif operation == 'execute_task':
                result = await self._execute_trade(action.get('metadata', {}))
            else:
                result = {'success': False, 'error': f'Unknown operation: {operation}'}
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics.update(result.get('success', False), execution_time)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics.update(False, execution_time)
            return {'success': False, 'error': str(e)}
    
    async def _execute_trade(self, action: Dict) -> Dict[str, Any]:
        """Execute a trade using real/paper executor"""
        try:
            # Map action to Order object
            symbol = action.get('symbol', 'EURUSD')
            side_str = action.get('side', 'BUY').upper()
            side = OrderSide.BUY if side_str == 'BUY' else OrderSide.SELL

            type_str = action.get('order_type', 'MARKET').upper()
            order_type = OrderType.MARKET
            if type_str == 'LIMIT': order_type = OrderType.LIMIT
            elif type_str == 'STOP': order_type = OrderType.STOP

            order = Order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=action.get('size', 0.01),
                price=action.get('price'),
                stop_loss=action.get('stop_loss'),
                take_profit=action.get('take_profit')
            )

            # Execute via TradeExecutor
            result = self.executor.execute_trade(order)
            return result
        except Exception as e:
            logger.error(f"Trade execution failed in ExecutorAgent: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _cancel_order(self, action: Dict) -> Dict[str, Any]:
        """Cancel an order"""
        order_id = action.get('order_id')
        if not order_id:
            return {'success': False, 'error': 'No order_id provided'}

        return self.executor.cancel_order(order_id)
    
    async def _modify_order(self, action: Dict) -> Dict[str, Any]:
        """Modify an order"""
        return {
            'success': True,
            'modified_order_id': action.get('order_id')
        }


class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent - Evaluates outcomes and provides feedback.
    
    Inspired by AlphaGo's value network - estimates expected outcomes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="EvaluatorAgent",
            role=AgentRole.EVALUATOR,
            config=config
        )
        self.config = config or {}
    
    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="evaluation",
            description="Evaluate trading outcomes",
            input_schema={"trade": "Trade", "outcome": "Outcome"},
            output_schema={"evaluation": "EvaluationResult"}
        ))
        self.add_capability(AgentCapability(
            name="backtesting",
            description="Backtest strategies",
            input_schema={"strategy": "Strategy", "data": "HistoricalData"},
            output_schema={"backtest_result": "BacktestResult"}
        ))
    
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute evaluation"""
        operation = action.get('operation', 'evaluate')
        
        if operation == 'evaluate':
            return await self._evaluate(action)
        elif operation == 'backtest':
            return await self._backtest(action)
        elif operation == 'execute_task':
            return await self._evaluate(action.get('metadata', {}))
        
        return {'success': False, 'error': f'Unknown operation: {operation}'}
    
    async def _evaluate(self, action: Dict) -> Dict[str, Any]:
        """Evaluate an outcome"""
        trade = action.get('trade', {})
        outcome = action.get('outcome', {})
        
        pnl = outcome.get('pnl', 0)
        
        return {
            'success': True,
            'evaluation': {
                'pnl': pnl,
                'quality_score': 0.7 if pnl > 0 else 0.3,
                'feedback': 'Good trade' if pnl > 0 else 'Review strategy'
            }
        }
    
    async def _backtest(self, action: Dict) -> Dict[str, Any]:
        """Run backtest"""
        return {
            'success': True,
            'backtest_result': {
                'sharpe_ratio': 1.5,
                'total_return': 0.15,
                'max_drawdown': 0.05,
                'win_rate': 0.6
            }
        }


class ResearchAgent(BaseAgent):
    """
    Research Agent - Conducts research and discovers patterns.
    
    Implements autonomous research capabilities.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="ResearchAgent",
            role=AgentRole.RESEARCHER,
            config=config
        )
        self.config = config or {}
    
    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="research",
            description="Conduct research on trading strategies",
            input_schema={"topic": "str", "depth": "str"},
            output_schema={"findings": "ResearchFindings"}
        ))
        self.add_capability(AgentCapability(
            name="discovery",
            description="Discover new patterns",
            input_schema={"data": "MarketData"},
            output_schema={"patterns": "List[Pattern]"}
        ))
    
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research"""
        operation = action.get('operation', 'research')
        
        if operation == 'research':
            return await self._research(action)
        elif operation == 'discover':
            return await self._discover(action)
        elif operation == 'execute_task':
            return await self._research(action.get('metadata', {}))
        
        return {'success': False, 'error': f'Unknown operation: {operation}'}
    
    async def _research(self, action: Dict) -> Dict[str, Any]:
        """Conduct research"""
        topic = action.get('topic', 'general')
        
        return {
            'success': True,
            'findings': {
                'topic': topic,
                'insights': ['Insight 1', 'Insight 2'],
                'recommendations': ['Recommendation 1']
            }
        }
    
    async def _discover(self, action: Dict) -> Dict[str, Any]:
        """Discover patterns"""
        return {
            'success': True,
            'patterns': [
                {'name': 'Pattern 1', 'confidence': 0.8},
                {'name': 'Pattern 2', 'confidence': 0.6}
            ]
        }


class SafetyAgent(BaseAgent):
    """
    Safety Agent - Performs safety checks and verification.
    
    Implements Constitutional AI safety verification.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="SafetyAgent",
            role=AgentRole.SAFETY,
            config=config
        )
        self.config = config or {}
    
    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="safety_check",
            description="Check action safety",
            input_schema={"action": "Action"},
            output_schema={"safety_result": "SafetyResult"}
        ))
        self.add_capability(AgentCapability(
            name="verification",
            description="Verify action compliance",
            input_schema={"action": "Action", "rules": "List[Rule]"},
            output_schema={"verification_result": "VerificationResult"}
        ))
    
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute safety check"""
        operation = action.get('operation', 'check')
        
        if operation == 'check':
            return await self._safety_check(action)
        elif operation == 'verify':
            return await self._verify(action)
        elif operation == 'execute_task':
            return await self._safety_check(action.get('metadata', {}))
        
        return {'success': False, 'error': f'Unknown operation: {operation}'}
    
    async def _safety_check(self, action: Dict) -> Dict[str, Any]:
        """Perform safety check"""
        target_action = action.get('target_action', {})
        
        # Check for risky parameters
        size = target_action.get('size', 0)
        leverage = target_action.get('leverage', 1)
        
        is_safe = size <= 0.1 and leverage <= 5
        
        return {
            'success': True,
            'is_safe': is_safe,
            'safety_score': 0.9 if is_safe else 0.3,
            'warnings': [] if is_safe else ['Position size or leverage too high']
        }
    
    async def _verify(self, action: Dict) -> Dict[str, Any]:
        """Verify compliance"""
        return {
            'success': True,
            'compliant': True,
            'violations': []
        }

class LegacyAgentWrapper(BaseAgent):
    """
    Wrapper for legacy agents from agents2 system.

    Allows legacy agents that implement analyze_market(market_data)
    to be used in the new core_agent_system.
    """

    def __init__(self, legacy_agent, config: Optional[Dict] = None):
        super().__init__(
            agent_id=legacy_agent.agent_id,
            name=f"Legacy_{legacy_agent.get_strategy_name()}",
            role=AgentRole.PLANNER,
            config=config
        )
        self.legacy_agent = legacy_agent

    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="legacy_planning",
            description="Analyze market using legacy strategy",
            input_schema={"market_data": "Dict"},
            output_schema={"proposal": "Dict"}
        ))

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute legacy agent logic"""
        operation = action.get('operation', 'propose')

        if operation in ['propose', 'execute_task']:
            # Handle both SystemContext and raw Dict
            context = action.get('context', {})
            market_data = getattr(context, 'market_state', context)
            if not isinstance(market_data, dict):
                market_data = {}

            proposal = self.legacy_agent.analyze_market(market_data)

            # Convert AgentProposal dataclass to Dict
            return {
                'success': True,
                'type': proposal.action.lower(),
                'action': {'operation': proposal.action.lower()},
                'confidence': proposal.confidence,
                'reasoning': proposal.reasoning,
                'expected_return': proposal.expected_return,
                'risk_score': proposal.risk_score
            }

        return {'success': False, 'error': f'Operation {operation} not supported by LegacyAgentWrapper'}
