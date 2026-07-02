"""
Integrated Agent System - Research Lab Grade Architecture

This module integrates all components into a unified system following
patterns from DeepMind, OpenAI, and Anthropic.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import redis

from .master_orchestrator import MasterOrchestrator, SystemContext
from .meta_orchestrator import MetaOrchestrator
from trading_bot.neuros_evolution.controlled_objects import ControlledObjectRegistry
from .react_loop import ReActLoop
from .constitutional_layer import ConstitutionalAI
from trading_bot.execution.trade_executor import TradeExecutor
from .policy_value_network import PolicyNetwork, ValueNetwork, DualNetwork
from .agent_registry import (
    AgentRegistry, 
    AgentRole,
    PlannerAgent, 
    ExecutorAgent, 
    EvaluatorAgent,
    ResearchAgent,
    SafetyAgent,
    OptimizerAgent,
    LegacyAgentWrapper
)
from .migrated_agents.planner import MigratedPlannerAgent
from .multidimensional_intelligence.agent import MultidimensionalResearchAgent
from trading_bot.agents2.specialized_agents import (
    TrendFollowingAgent,
    MeanReversionAgent,
    VolatilityAgent,
    RiskManagerAgent,
    MarketMakerAgent
)
from .specialized_planners import (
    TrendFollowingPlanner,
    MeanReversionPlanner,
    VolatilityPlanner
)
from .tool_registry import ToolRegistry
from .memory_system import MemorySystem
from .self_play_loop import SelfPlayLoop
from .self_coordinating_core import SelfCoordinatingCore
from .meta_orchestrator import MetaOrchestrator
from .swarm.usis import UnifiedSwarmIntelligenceSystem
from .swarm.experts import MarketScientist, QuantAnalyst, SwarmRiskManager

logger = logging.getLogger(__name__)


class IntegratedAgentSystem:
    """
    Integrated Agent System - Research Lab Grade
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Storage path
        storage_base = Path(self.config.get('storage_path', 'core_agent_data'))
        storage_base.mkdir(parents=True, exist_ok=True)
        self.storage_path = storage_base
        
        # 0. Unified Registry (Section 4)
        self.object_registry = ControlledObjectRegistry(
            str(self.storage_path / 'controlled_objects.json')
        )

        # Initialize components
        self._init_components()
        
        # State
        self.running = False
        self.initialized = False
        
        logger.info("=" * 60)
        logger.info("INTEGRATED AGENT SYSTEM - RESEARCH LAB GRADE")
        logger.info("=" * 60)

    def _init_redis(self):
        """Initialize Redis connection for IPC."""
        try:
            self.redis_client = redis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✓ Redis connection established")
        except Exception as e:
            logger.warning(f"✗ Redis connection failed: {e}. Background services may be restricted.")
            self.redis_client = None
    
    def _init_components(self):
        """Initialize all system components"""
        # 1. Memory System
        self.memory_system = MemorySystem({
            'storage_path': str(self.storage_path / 'memory'),
            'working_memory_capacity': self.config.get('working_memory_capacity', 20),
            'max_episodes': self.config.get('max_episodes', 50000)
        })
        
        # 2. Tool Registry
        self.tool_registry = ToolRegistry({
            'storage_path': str(self.storage_path / 'tools')
        })
        
        # 3. Agent Registry
        self.agent_registry = AgentRegistry({
            'storage_path': str(self.storage_path / 'agents'),
            'health_check_interval': 30,
            'auto_restart': True
        })
        
        # 4. Policy Network
        self.policy_network = PolicyNetwork({
            'learning_rate': self.config.get('policy_lr', 0.001),
            'temperature': self.config.get('temperature', 1.0)
        })
        
        # 5. Value Network
        self.value_network = ValueNetwork({
            'learning_rate': self.config.get('value_lr', 0.001)
        })
        
        # 5b. World Model
        from trading_bot.world_model.latent_dynamics import WorldModel
        self.world_model = WorldModel({
            'input_dim': self.config.get('market_input_dim', 20),
            'latent_dim': self.config.get('latent_dim', 64),
            'hidden_dim': self.config.get('hidden_dim', 128)
        })

        # 6. Constitutional Layer
        self.constitutional_layer = ConstitutionalAI({
            'safety_threshold': self.config.get('safety_threshold', 0.7),
            'red_team_enabled': self.config.get('red_team_enabled', True),
            'red_team_iterations': 3
        })
        
        # 7. ReAct Loop
        self.react_loop = ReActLoop(
            tool_registry=self.tool_registry,
            memory_system=self.memory_system,
            max_iterations=self.config.get('max_react_iterations', 10)
        )
        
        # 8. Master Orchestrator
        self.orchestrator = MasterOrchestrator({
            'search_depth': self.config.get('search_depth', 5),
            'num_simulations': self.config.get('num_simulations', 100),
            'safety_threshold': self.config.get('safety_threshold', 0.7),
            'max_history': 10000
        })
        
        # 9. Self-Play Loop
        self.self_play_loop = SelfPlayLoop(
            policy_network=self.policy_network,
            value_network=self.value_network,
            memory_system=self.memory_system,
            config={
                'games_per_iteration': self.config.get('games_per_iteration', 50),
                'training_batch_size': self.config.get('training_batch_size', 32),
                'evaluation_games': self.config.get('evaluation_games', 20),
                'improvement_threshold': 0.55
            }
        )

        # 10. Self-Coordinating Core
        self.coordination_core = SelfCoordinatingCore(
            policy_network=self.policy_network,
            value_network=self.value_network,
            react_loop=self.react_loop,
            constitutional_layer=self.constitutional_layer,
            memory_system=self.memory_system,
            tool_registry=self.tool_registry,
            agent_registry=self.agent_registry,
            config=self.config
        )

        # 11. Meta-Orchestrator
        self.meta_orchestrator = MetaOrchestrator(self.config)

        # 12. Unified Swarm Intelligence System (USIS)
        self.swarm_system = UnifiedSwarmIntelligenceSystem(
            self.agent_registry,
            self.config.get('swarm', {})
        )
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("INITIALIZING INTEGRATED AGENT SYSTEM")
        
        await self.memory_system.initialize()
        await self.tool_registry.initialize()
        await self.agent_registry.initialize()
        
        # Register default agents
        await self._register_default_agents()
        
        await self.policy_network.initialize()
        await self.value_network.initialize()
        await self.constitutional_layer.initialize()
        await self.react_loop.initialize()
        
        from trading_bot.world_model.latent_dynamics import WorldModel
        self.world_model = WorldModel({
            'input_dim': self.config.get('market_input_dim', 20),
            'latent_dim': self.config.get('latent_dim', 64),
            'hidden_dim': self.config.get('hidden_dim', 128)
        })

        self.orchestrator.inject_dependencies(
            policy_network=self.policy_network,
            value_network=self.value_network,
            constitutional_layer=self.constitutional_layer,
            react_loop=self.react_loop,
            agent_registry=self.agent_registry,
            tool_registry=self.tool_registry,
            memory_system=self.memory_system,
            world_model=self.world_model
        )
        await self.orchestrator.initialize()
        
        self.self_play_loop.audit_system = self.coordination_core.governance
        await self.self_play_loop.initialize()
        
        await self.coordination_core.initialize()
        await self._assign_agents_to_teams()

        self.initialized = True

    async def _register_default_agents(self):
        """Register default agents"""
        trade_executor = TradeExecutor(self.config.get('executor', {}))

        default_agents = [
            MigratedPlannerAgent(config={'name': 'ComprehensivePlanner'}),
            PlannerAgent(config={'name': 'MainPlanner'}),
            TrendFollowingPlanner(config={'name': 'TrendFollowingPlanner'}),
            MeanReversionPlanner(config={'name': 'MeanReversionPlanner'}),
            VolatilityPlanner(config={'name': 'VolatilityPlanner'}),
            ExecutorAgent(executor=trade_executor, config={'name': 'MainExecutor'}),
            EvaluatorAgent(config={'name': 'MainEvaluator'}),
            ResearchAgent(config={'name': 'MainResearcher'}),
            MultidimensionalResearchAgent(config={'name': 'MultidimensionalResearcher'}),
            SafetyAgent(config={'name': 'MainSafety'}),

            # Swarm Experts
            MarketScientist(config={'name': 'SwarmMarketScientist'}),
            QuantAnalyst(config={'name': 'SwarmQuantAnalyst'}),
            SwarmRiskManager(config={'name': 'SwarmRiskManager'}),
        ]
        
        for agent in default_agents:
            await self.agent_registry.register_agent(agent)

        legacy_agents = [
            LegacyAgentWrapper(TrendFollowingAgent()),
            LegacyAgentWrapper(MeanReversionAgent()),
            LegacyAgentWrapper(VolatilityAgent()),
            LegacyAgentWrapper(RiskManagerAgent()),
            LegacyAgentWrapper(MarketMakerAgent()),
        ]

        for agent in legacy_agents:
            await self.agent_registry.register_agent(agent)
        
        logger.info(f"Registered {len(default_agents)} standard and {len(legacy_agents)} legacy agents")

    async def _assign_agents_to_teams(self):
        """Assign registered agents to functional teams in coordination core"""
        logger.info("Assigning agents to functional teams...")

        role_to_team = {
            AgentRole.PLANNER: 'trading_team',
            AgentRole.EXECUTOR: 'trading_team',
            AgentRole.COORDINATOR: 'trading_team',
            AgentRole.RESEARCHER: 'research_team',
            AgentRole.EVALUATOR: 'research_team',
            AgentRole.SAFETY: 'safety_team'
        }

        for agent_id, agent in self.agent_registry.agents.items():
            team = role_to_team.get(agent.role)
            if team:
                self.coordination_core.shared_memory.add_to_team(team, agent_id)
                logger.debug(f"Assigned agent {agent.name} to team {team}")

    async def start(self):
        """Start the integrated system"""
        if not self.initialized:
            await self.initialize()
        
        logger.info("STARTING INTEGRATED AGENT SYSTEM")
        self.running = True

        # Start Layer 2: Background Services
        self.start_background_services()
        
        tasks = [
            asyncio.create_task(self._main_loop(), name="main_loop"),
            asyncio.create_task(self._self_improvement_loop(), name="self_improvement"),
            asyncio.create_task(self._multidimensional_intelligence_loop(), name="multidimensional_intelligence"),
            asyncio.create_task(self._monitoring_loop(), name="monitoring"),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in system operation: {e}")
            await self.shutdown()

    def start_background_services(self):
        """Start Layer 2 background intelligence services."""
        logger.info("Starting background services...")

        services = [
            ('market_student', run_market_student_service),
            ('eternal_evolution', run_eternal_evolution_service),
            ('sentiment_analysis', run_sentiment_analysis_service),
            ('market_monitor', run_market_monitor_service),
        ]

        for name, func in services:
            try:
                # Use standalone functions to avoid pickling 'self'
                process = multiprocessing.Process(
                    target=func,
                    args=(self.config,),
                    name=name
                )
                process.daemon = True
                process.start()
                self.background_processes[name] = process
                logger.info(f"✓ Started: {name} (PID: {process.pid})")
            except Exception as e:
                logger.error(f"✗ Failed to start {name}: {e}")

    def stop_background_services(self):
        """Stop all background services."""
        logger.info("Stopping background services...")

        for name, process in self.background_processes.items():
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
                logger.info(f"✓ Stopped: {name}")

        self.background_processes.clear()
    
    async def _main_loop(self):
        """Main orchestration loop"""
        while self.running:
            try:
                context = await self._gather_context()
                decision = await self.orchestrator.think(context)
                
                if decision.is_safe() and decision.expected_value > 0.5:
                    result = await self.execute_task(
                        task=f"Execute {decision.decision_type}",
                        context={
                            'decision': decision,
                            'market_state': context.market_state,
                            'portfolio_state': context.portfolio_state,
                            'use_coordination': True
                        }
                    )
                    
                    await self.orchestrator.learn({
                        'decision': decision,
                        'result': result,
                        'success': result.get('success', False),
                        'actual_value': decision.expected_value if result.get('success') else 0.0
                    })
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
    
    async def _self_improvement_loop(self):
        """Self-improvement through self-play"""
        while self.running:
            try:
                results = await self.self_play_loop.run_iteration()
                if results['improved']:
                    await self.memory_system.store_knowledge(f"improvement_{results['iteration']}", results)
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in self-improvement loop: {e}")
                await asyncio.sleep(60)

    async def _multidimensional_intelligence_loop(self):
        """Scientific self-improvement through Multidimensional Intelligence"""
        while self.running:
            try:
                agents = self.agent_registry.get_agents_by_role(AgentRole.RESEARCHER)
                multi_agent = next((a for a in agents if isinstance(a, MultidimensionalResearchAgent)), None)

                if multi_agent:
                    context = await self._gather_context()
                    result = await multi_agent.execute({
                        'operation': 'scientific_improvement',
                        'context': context.__dict__ if hasattr(context, '__dict__') else context
                    })
                    if result.get('success'):
                        logger.info("Successfully completed multidimensional intelligence cycle")

                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"Error in multidimensional intelligence loop: {e}")
                await asyncio.sleep(300)
    
    async def _monitoring_loop(self):
        """System monitoring and health checks"""
        while self.running:
            try:
                status = self.get_comprehensive_status()
                logger.info(f"System Status: agents={status['agents']['total_agents']}, tools={status['tools']['total_tools']}")
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _gather_context(self) -> SystemContext:
        """Gather current system context"""
        if not hasattr(self, 'tool_registry'):
            # Empty context
            return SystemContext(datetime.now(), {}, {}, {}, [], [], {})

        # Get market state from tools
        market_tool = await self.tool_registry.get_tool('market_data')
        if market_tool:
            market_result = await market_tool.execute({'symbol': 'EURUSD'})
            market_state = market_result if (market_result and market_result.get('success')) else {}
        else:
            market_state = {}
        
        # Get portfolio state
        portfolio_tool = await self.tool_registry.get_tool('portfolio')
        if portfolio_tool:
            portfolio_result = await portfolio_tool.execute({'operation': 'get_state'})
            portfolio_state = portfolio_result if (portfolio_result and portfolio_result.get('success')) else {}
        else:
            portfolio_state = {}
        
        # Get risk metrics
        risk_tool = await self.tool_registry.get_tool('risk_calculator')
        if risk_tool:
            risk_result = await risk_tool.execute({'operation': 'get_metrics'})
            risk_metrics = risk_result if (risk_result and risk_result.get('success')) else {}
        else:
            risk_metrics = {}
        
        # Get agent states
        agent_states = await self.agent_registry.get_all_states()
        
        return SystemContext(
            timestamp=datetime.now(),
            market_state=market_state,
            portfolio_state=portfolio_state,
            agent_states=agent_states,
            pending_decisions=[],
            recent_outcomes=[],
            risk_metrics=risk_metrics
        )
    
    # ========================================================================
    # EXECUTION INTERFACE (Standardized)
    # ========================================================================

    async def execute_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a high-level task using the unified brain.
        Primary entry point for external callers.
        """
        context = context or {}
        start_time = datetime.now()
        answer_part = "No specific result returned."
        final_answer = "Task execution failed or returned no result."
        
        # Check for swarm-specific tasks
        if context.get('use_swarm') or 'swarm' in task.lower():
            logger.info(f"IAS routing task to USIS: {task}")
            return await self.swarm_system.analyze(task, context)

        logger.info(f"IAS executing task: {task}")

        # 1. Use Meta-Orchestrator for self-scaffolding workflow
        meta_result = await self.meta_orchestrator.execute_task(
            task=task,
            context=context,
            core_system=self
        )

        # 2. Record deep observability data
        duration = (datetime.now() - start_time).total_seconds()
        obs_trace = {}

        obs_trace["selected_workflow"] = meta_result.get('policy_id')
        obs_trace["workflow_trace"] = meta_result.get('trace', [])

        # Extract activated agents and tools from the trace
        activated_agents = []
        tools_used = []
        for step in obs_trace["workflow_trace"]:
            res = step.get('result', {})
            if 'agents' in res:
                activated_agents.extend(res['agents'])
            if step.get('type') == 'call_tool':
                tools_used.append(step.get('node'))

        obs_trace["activated_agents"] = list(set(activated_agents))
        obs_trace["tools_used"] = list(set(tools_used))
        obs_trace["duration"] = duration
        obs_trace["success"] = meta_result.get('success', False)

        # 3. Store in Semantic Memory
        await self.memory_system.store_knowledge(
            f"obs_trace_{uuid.uuid4().hex[:8]}",
            obs_trace,
            tags=["observability", "execution_trace", meta_result.get('policy_id')]
        )

        # Standardized Response Formatting
        from .adapters import ReasoningTrace, ResponseFormatter

        # Extract results from trace
        if meta_result.get('result'):
            if isinstance(meta_result['result'], dict):
                answer_part = meta_result['result'].get('result', meta_result['result'].get('answer', str(meta_result['result'])))
            else:
                answer_part = str(meta_result['result'])

        trace_data = meta_result.get('trace', [])
        # We need a ReasoningTrace object for format_response
        trace_obj = ReasoningTrace(
            goal=task,
            analysis_summary=f"Executed workflow {meta_result.get('policy_id')}",
            plan=[step.get('node', 'step') for step in trace_data],
            reflection=meta_result.get('reflection')
        )
        formatted_response = ResponseFormatter.format_response(trace_obj, [])

        if context.get('use_coordination'):
            # If using multi-agent coordination explicitly
            from .coordination_core import TaskType, TaskPriority

            # Determine task type from context or task string
            task_type = context.get('task_type', TaskType.ANALYSIS)
            if isinstance(task_type, str):
                try:
                    task_type = TaskType(task_type.lower())
                except ValueError:
                    task_type = TaskType.ANALYSIS

            result = await self.coordination_core.execute_task(
                task_name=f"Task: {task[:30]}",
                task_type=task_type,
                description=task,
                priority=context.get('priority', TaskPriority.MEDIUM),
                metadata=context
            )

            # Extract final answer from results
            answer_part = "No specific result returned."
            if result.get('results'):
                for r in reversed(result['results']):
                    if r.get('result'):
                        answer_part = r['result']
                        break
                    elif r.get('answer'):
                        answer_part = r['answer']
                        break

            return {
                'success': result.get('success', False),
                'answer': f"Task completed by coordinated team. Result: {answer_part}",
                'coordination_report': result,
                'reasoning': f"Multi-agent coordination used. {len(result.get('results', []))} agents involved.",
                'iterations': len(result.get('results', []))
            }

        # Format standardized response
        final_answer = f"Task completed by Meta-Orchestrator. Result: {answer_part}"

        return {
            'success': meta_result.get('success', False),
            'answer': final_answer,
            'reasoning': f"Workflow policy '{meta_result.get('policy_id')}' executed with {len(meta_result.get('trace', []))} steps.",
            'coordination_report': meta_result,
            'iterations': len(meta_result.get('trace', []))
        }

    async def think(self, context: Optional[SystemContext] = None) -> Decision:
        """
        Perform a reasoning cycle based on the current context.
        Returns a strategic Decision object.
        """
        if not context:
            context = await self._gather_context()

        return await self.orchestrator.think(context)

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a structured request (JSON/Dict).
        Maps requests to either execute_task or think based on content.
        """
        task = request.get('task') or request.get('instruction')
        context = request.get('context', {})

        if task:
            return await self.execute_task(task, context)

        # If no explicit task, perform a general reasoning cycle
        decision = await self.think()
        return {
            'success': True,
            'decision': decision.to_dict() if hasattr(decision, 'to_dict') else str(decision)
        }

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'running': self.running,
            'initialized': self.initialized,
            'orchestrator': self.orchestrator.get_status(),
            'agents': self.agent_registry.get_status(),
            'tools': self.tool_registry.get_status(),
            'memory': self.memory_system.get_status(),
            'policy_network': self.policy_network.get_status(),
            'value_network': self.value_network.get_status(),
            'self_play': self.self_play_loop.get_status(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _print_system_status(self):
        """Print system status"""
        status = self.get_comprehensive_status()
        
        print("\n" + "=" * 60)
        print("INTEGRATED AGENT SYSTEM - STATUS")
        print("=" * 60)
        
        print(f"\n🧠 ORCHESTRATOR")
        print(f"   State: {status['orchestrator']['state']}")
        print(f"   Safety Threshold: {status['orchestrator']['safety_threshold']}")
        
        print(f"\n🤖 AGENTS")
        print(f"   Total: {status['agents']['total_agents']}")
        print(f"   Roles: {status['agents']['role_distribution']}")
        
        print(f"\n🔧 TOOLS")
        print(f"   Total: {status['tools']['total_tools']}")
        print(f"   Categories: {status['tools']['category_distribution']}")
        
        print(f"\n💾 MEMORY")
        print(f"   Working: {status['memory']['working']['used']}/{status['memory']['working']['capacity']}")
        print(f"   Episodic: {status['memory']['episodic']['total_episodes']}")
        print(f"   Semantic: {status['memory']['semantic']['total_knowledge']}")
        
        print(f"\n📊 NETWORKS")
        print(f"   Policy: {len(status['policy_network']['action_weights'])} actions")
        print(f"   Value: {status['value_network']['update_count']} updates")
        
        print(f"\n🔄 SELF-PLAY")
        print(f"   Iteration: {status['self_play']['iteration']}")
        print(f"   Games: {status['self_play']['total_games']}")
        print(f"   Best Policy: v{status['self_play']['best_policy_version']}")
        
        print("\n" + "=" * 60)

    async def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        self.stop_background_services()
        await self.coordination_core.shutdown()
        await self.self_play_loop.shutdown()
        await self.react_loop.shutdown()
        await self.constitutional_layer.shutdown()
        await self.agent_registry.shutdown()
        await self.tool_registry.shutdown()
        await self.memory_system.shutdown()

# ============================================================================
# STANDALONE BACKGROUND SERVICES (Async Robust)
# ============================================================================

def _init_redis_for_service(config):
    """Initialize Redis in child process."""
    try:
        import redis
        client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=0,
            decode_responses=True
        )
        client.ping()
        return client
    except Exception:
        return None

def run_market_student_service(config):
    """Background service: Market Student."""
    logging.basicConfig(level=logging.INFO)
    srv_logger = logging.getLogger("Background.MarketStudent")

    async def run_loop():
        redis_client = _init_redis_for_service(config)
        try:
            from trading_bot.market_student import MarketStudentOrchestrator
            orchestrator = MarketStudentOrchestrator({})

            while True:
                try:
                    if redis_client:
                        trade_data = redis_client.lpop('trade_results')
                        if trade_data:
                            import json
                            trade = json.loads(trade_data)
                            lesson = await orchestrator.learn_from_trade(trade)
                            if lesson:
                                srv_logger.info(f"Insight: {lesson.get('insight', 'Learned')}")

                    await asyncio.sleep(10)
                except Exception as e:
                    srv_logger.error(f"Loop error: {e}")
                    await asyncio.sleep(30)
        except ImportError:
            srv_logger.error("Market Student not available")

    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        pass

def run_eternal_evolution_service(config):
    """Background service: Eternal Evolution."""
    logging.basicConfig(level=logging.INFO)
    srv_logger = logging.getLogger("Background.EternalEvolution")

    async def run_loop():
        redis_client = _init_redis_for_service(config)
        try:
            from trading_bot.eternal_evolution import EternalEvolutionOrchestrator
            orchestrator = EternalEvolutionOrchestrator({})
            await orchestrator.start()

            while True:
                try:
                    await asyncio.sleep(3600)
                except Exception as e:
                    srv_logger.error(f"Loop error: {e}")
                    await asyncio.sleep(300)
        except ImportError:
            srv_logger.error("Eternal Evolution not available")
        except Exception as e:
            srv_logger.error(f"Initialization error: {e}")

    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        pass

def run_sentiment_analysis_service(config):
    """Background service: Sentiment Analysis."""
    logging.basicConfig(level=logging.INFO)
    srv_logger = logging.getLogger("Background.Sentiment")

    async def run_loop():
        redis_client = _init_redis_for_service(config)
        try:
            from trading_bot.sentiment import SentimentAnalyzer
            analyzer = SentimentAnalyzer()

            while True:
                try:
                    symbols = config.get('trading', {}).get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY'])
                    for symbol in symbols:
                        sentiment = analyzer.analyze_symbol(symbol)
                        if sentiment and redis_client:
                            import json
                            redis_client.setex(f'sentiment:{symbol}', 300, json.dumps(sentiment))

                    await asyncio.sleep(300)
                except Exception as e:
                    srv_logger.error(f"Loop error: {e}")
                    await asyncio.sleep(60)
        except ImportError:
            srv_logger.error("Sentiment Analyzer not available")

    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        pass

def run_market_monitor_service(config):
    """Background service: Market Intelligence Monitor."""
    logging.basicConfig(level=logging.INFO)
    srv_logger = logging.getLogger("Background.MarketMonitor")

    async def run_loop():
        redis_client = _init_redis_for_service(config)
        try:
            from trading_bot.market_intelligence import MarketDataMonitor
            monitor = MarketDataMonitor()

            symbols = config.get('trading', {}).get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY'])
            for symbol in symbols:
                monitor.start_monitoring(symbol=symbol, timeframe='M15')

            while True:
                try:
                    for symbol in symbols:
                        state = monitor.get_current_state(symbol)
                        if state and redis_client:
                            import json
                            redis_client.setex(f'market_state:{symbol}', 60, json.dumps(state))

                    await asyncio.sleep(60)
                except Exception as e:
                    srv_logger.error(f"Loop error: {e}")
                    await asyncio.sleep(30)
        except ImportError:
            srv_logger.error("Market Intelligence not available")

    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        pass

async def main():
    import signal
    system = IntegratedAgentSystem()
    def signal_handler(sig, frame):
        asyncio.create_task(system.shutdown())
    signal.signal(signal.SIGINT, signal_handler)
    try:
        await system.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await system.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
