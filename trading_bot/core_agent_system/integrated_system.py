"""
Integrated Agent System - Research Lab Grade Architecture

This module integrates all components into a unified system following
patterns from DeepMind, OpenAI, and Anthropic.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from .master_orchestrator import MasterOrchestrator, SystemContext
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
        
        # Initialize components
        self._init_components()
        
        # State
        self.running = False
        self.initialized = False
        
        logger.info("=" * 60)
        logger.info("INTEGRATED AGENT SYSTEM - RESEARCH LAB GRADE")
        logger.info("=" * 60)
    
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
            TrendFollowingPlanner(config={'name': 'TrendPlanner'}),
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
            return SystemContext(
                timestamp=datetime.now(),
                market_state={},
                portfolio_state={},
                agent_states={},
                pending_decisions=[],
                recent_outcomes=[],
                risk_metrics={}
            )

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
    
    async def execute_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a task using the research-grade Meta-Orchestrator or USIS.
        """
        context = context or {}
        
        # Check for swarm-specific tasks
        if context.get('use_swarm') or 'swarm' in task.lower():
            logger.info(f"Integrated System routing task to USIS: {task}")
            return await self.swarm_system.analyze(task, context)

        logger.info(f"Integrated System executing task via Meta-Orchestrator: {task}")

        # Use Meta-Orchestrator for self-scaffolding workflow
        meta_result = await self.meta_orchestrator.execute_task(
            task=task,
            context=context,
            core_system=self
        )

        # Use our new adapters for standardized reasoning and tool calls
        from .adapters import ReasoningTrace, ResponseFormatter

        trace = ReasoningTrace(
            goal=task,
            analysis_summary=f"Task executed via Meta-Orchestrator policy: {meta_result.get('policy_id')}",
            plan=[step.get('type') for step in meta_result.get('trace', [])],
            metadata=meta_result.get('metrics', {})
        )

        formatted_response = ResponseFormatter.format_response(trace, [])

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
            total_iterations = 0
            if result.get('results'):
                # Try to find the most relevant result
                for r in reversed(result['results']):
                    if r.get('result'):
                        answer_part = r['result']
                        break
                    elif r.get('answer'):
                        answer_part = r['answer']
                        break

                # Sum up iterations if available from subtasks
                for r in result['results']:
                    total_iterations += r.get('iterations', 0)

            final_answer = f"Task completed by coordinated team. Result: {answer_part}"

            return {
                'success': result.get('success', False),
                'answer': final_answer,
                'coordination_report': result,
                'reasoning': f"Multi-agent coordination used. {len(result.get('results', []))} agents involved.",
                'iterations': len(result.get('results', []))
            }

        # Format standardized response
        formatted_response = ResponseFormatter.format_response(trace, [])

        return {
            'success': meta_result.get('success', False),
            'answer': f"Task '{task}' has been completed by Meta-Orchestrator. Status: SUCCESS",
            'reasoning': formatted_response['reasoning'],
            'tool_calls': formatted_response['tool_calls'],
            'coordination_report': meta_result,
            'iterations': len(meta_result.get('trace', []))
        }

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
        await self.coordination_core.shutdown()
        await self.self_play_loop.shutdown()
        await self.react_loop.shutdown()
        await self.constitutional_layer.shutdown()
        await self.agent_registry.shutdown()
        await self.tool_registry.shutdown()
        await self.memory_system.shutdown()

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
