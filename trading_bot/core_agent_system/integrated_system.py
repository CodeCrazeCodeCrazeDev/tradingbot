"""
Integrated Agent System - Research Lab Grade Architecture

This module integrates all components into a unified system following
patterns from DeepMind, OpenAI, and Anthropic.

Architecture Overview:
┌─────────────────────────────────────────────────────────────────────┐
│                    INTEGRATED AGENT SYSTEM                           │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   MASTER ORCHESTRATOR                          │ │
│  │  - Hierarchical control (DeepMind)                             │ │
│  │  - Decision fusion with MCTS                                   │ │
│  │  - Safety verification (Anthropic)                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│         ┌────────────────────┼────────────────────┐                 │
│         ▼                    ▼                    ▼                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │   Policy    │     │   Value     │     │Constitutional│           │
│  │   Network   │     │   Network   │     │    Layer    │           │
│  │ (AlphaGo)   │     │ (AlphaGo)   │     │ (Anthropic) │           │
│  └─────────────┘     └─────────────┘     └─────────────┘           │
│         │                    │                    │                 │
│         └────────────────────┼────────────────────┘                 │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      ReAct LOOP                                │ │
│  │  Thought → Action → Observation (OpenAI GPT-4)                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│         ┌────────────────────┼────────────────────┐                 │
│         ▼                    ▼                    ▼                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │   Agent     │     │    Tool     │     │   Memory    │           │
│  │  Registry   │     │  Registry   │     │   System    │           │
│  └─────────────┘     └─────────────┘     └─────────────┘           │
│         │                    │                    │                 │
│         └────────────────────┼────────────────────┘                 │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   SELF-PLAY LOOP                               │ │
│  │  Continuous improvement through self-play (DeepMind)           │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

Usage:
    from trading_bot.core_agent_system import IntegratedAgentSystem
    
    system = IntegratedAgentSystem(config)
    await system.initialize()
    await system.start()
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from .master_orchestrator import MasterOrchestrator, SystemContext
from .react_loop import ReActLoop
from .constitutional_layer import ConstitutionalAI
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
from trading_bot.world_model.latent_dynamics import WorldModel
from .tool_registry import ToolRegistry
from .memory_system import MemorySystem
from .self_play_loop import SelfPlayLoop
from .self_coordinating_core import SelfCoordinatingCore

logger = logging.getLogger(__name__)


class IntegratedAgentSystem:
    """
    Integrated Agent System - Research Lab Grade
    
    Combines all components into a unified, production-ready system
    following patterns from leading AI research labs.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Storage path
        storage_base = Path(config.get('storage_path', 'core_agent_data'))
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
        logger.info("Patterns: DeepMind AlphaGo + OpenAI GPT-4 + Anthropic Constitutional AI")
        logger.info("=" * 60)
    
    def _init_components(self):
        """Initialize all system components"""
        
        # 1. Memory System (foundation for all learning)
        self.memory_system = MemorySystem({
            'storage_path': str(self.storage_path / 'memory'),
            'working_memory_capacity': self.config.get('working_memory_capacity', 20),
            'max_episodes': self.config.get('max_episodes', 50000)
        })
        
        # 2. Tool Registry (standardized tool interface)
        self.tool_registry = ToolRegistry({
            'storage_path': str(self.storage_path / 'tools')
        })
        
        # 3. Agent Registry (unified agent management)
        self.agent_registry = AgentRegistry({
            'storage_path': str(self.storage_path / 'agents'),
            'health_check_interval': 30,
            'auto_restart': True
        })
        
        # 4. Policy Network (DeepMind - what to do)
        self.policy_network = PolicyNetwork({
            'learning_rate': self.config.get('policy_lr', 0.001),
            'temperature': self.config.get('temperature', 1.0)
        })
        
        # 5. Value Network (DeepMind - how good)
        self.value_network = ValueNetwork({
            'learning_rate': self.config.get('value_lr', 0.001)
        })
        
        # 5b. World Model (DreamerV3/JEPA - imagination)
        self.world_model = WorldModel({
            'input_dim': self.config.get('market_input_dim', 20),
            'latent_dim': self.config.get('latent_dim', 64),
            'hidden_dim': self.config.get('hidden_dim', 128)
        })

        # 6. Constitutional Layer (Anthropic - safety)
        self.constitutional_layer = ConstitutionalAI({
            'safety_threshold': self.config.get('safety_threshold', 0.7),
            'red_team_enabled': self.config.get('red_team_enabled', True),
            'red_team_iterations': 3
        })
        
        # 7. ReAct Loop (OpenAI - reasoning)
        self.react_loop = ReActLoop(
            tool_registry=self.tool_registry,
            memory_system=self.memory_system,
            max_iterations=self.config.get('max_react_iterations', 10)
        )
        
        # 8. Master Orchestrator (central coordination)
        self.orchestrator = MasterOrchestrator({
            'search_depth': self.config.get('search_depth', 5),
            'num_simulations': self.config.get('num_simulations', 100),
            'safety_threshold': self.config.get('safety_threshold', 0.7),
            'max_history': 10000
        })
        
        # 9. Self-Play Loop (DeepMind - continuous improvement)
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

        # 10. Self-Coordinating Core (Advanced Multi-Agent Coordination)
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
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("=" * 60)
        logger.info("INITIALIZING INTEGRATED AGENT SYSTEM")
        logger.info("=" * 60)
        
        # Initialize in dependency order
        logger.info("1. Initializing Memory System...")
        await self.memory_system.initialize()
        
        logger.info("2. Initializing Tool Registry...")
        await self.tool_registry.initialize()
        
        logger.info("3. Initializing Agent Registry...")
        await self.agent_registry.initialize()
        
        # Register default agents
        await self._register_default_agents()
        
        logger.info("4. Initializing Policy Network...")
        await self.policy_network.initialize()
        
        logger.info("5. Initializing Value Network...")
        await self.value_network.initialize()
        
        logger.info("6. Initializing Constitutional Layer...")
        await self.constitutional_layer.initialize()
        
        logger.info("7. Initializing ReAct Loop...")
        await self.react_loop.initialize()
        
        logger.info("7b. Initializing World Model...")
        # Note: WorldModel doesn't have an async initialize, but it's good practice

        logger.info("8. Initializing Master Orchestrator...")
        # Inject dependencies into orchestrator
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
        
        logger.info("9. Initializing Self-Play Loop...")
        await self.self_play_loop.initialize()
        
        logger.info("10. Initializing Self-Coordinating Core...")
        await self.coordination_core.initialize()

        # 11. Assign default agents to teams for teamwork
        await self._assign_agents_to_teams()

        self.initialized = True
        
        logger.info("=" * 60)
        logger.info("INTEGRATED AGENT SYSTEM READY")
        logger.info("=" * 60)
        
        self._print_system_status()

    async def _assign_agents_to_teams(self):
        """Assign registered agents to functional teams in coordination core"""
        logger.info("Assigning agents to functional teams...")

        for agent_id, agent in self.agent_registry.agents.items():
            team = None

            # Map roles to teams
            if agent.role in [AgentRole.PLANNER, AgentRole.EXECUTOR, AgentRole.MONITOR]:
                team = 'trading_team'
            elif agent.role in [AgentRole.RESEARCHER, AgentRole.OPTIMIZER]:
                team = 'research_team'
            elif agent.role in [AgentRole.SAFETY, AgentRole.EVALUATOR]:
                team = 'safety_team'

            if team:
                self.coordination_core.shared_memory.add_to_team(team, agent_id)
                logger.debug(f"Assigned agent {agent.name} ({agent_id}) to {team}")
    
    async def _register_default_agents(self):
        """Register default agents including legacy ones"""
        default_agents = [
            PlannerAgent(config={'name': 'MainPlanner'}),
            TrendFollowingPlanner(config={'name': 'TrendPlanner'}),
            MeanReversionPlanner(config={'name': 'MeanReversionPlanner'}),
            VolatilityPlanner(config={'name': 'VolatilityPlanner'}),
            ExecutorAgent(config={'name': 'MainExecutor'}),
            EvaluatorAgent(config={'name': 'MainEvaluator'}),
            ResearchAgent(config={'name': 'MainResearcher'}),
            SafetyAgent(config={'name': 'MainSafety'}),
        ]
        
        # Register standard agents
        for agent in default_agents:
            await self.agent_registry.register_agent(agent)

        # Register legacy specialized agents via wrapper
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
    
    async def start(self):
        """Start the integrated system"""
        if not self.initialized:
            await self.initialize()
        
        logger.info("=" * 60)
        logger.info("STARTING INTEGRATED AGENT SYSTEM")
        logger.info("=" * 60)
        
        self.running = True
        
        # Start all async loops
        tasks = [
            asyncio.create_task(self._main_loop(), name="main_loop"),
            asyncio.create_task(self._self_improvement_loop(), name="self_improvement"),
            asyncio.create_task(self._monitoring_loop(), name="monitoring"),
        ]
        
        logger.info(f"Started {len(tasks)} system loops")
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in system operation: {e}")
            await self.shutdown()
    
    async def _main_loop(self):
        """Main orchestration loop"""
        logger.info("Starting main orchestration loop")
        
        while self.running:
            try:
                # Gather current context
                context = await self._gather_context()
                
                # Think and decide (AlphaGo + Constitutional AI)
                decision = await self.orchestrator.think(context)
                
                # Execute if safe and valuable
                if decision.is_safe() and decision.expected_value > 0.5:
                    # Use coordinated teamwork for execution
                    result = await self.execute_task(
                        task=f"Execute {decision.decision_type}",
                        context={
                            'decision': decision,
                            'market_state': context.market_state,
                            'portfolio_state': context.portfolio_state,
                            'use_coordination': True
                        }
                    )
                    
                    # Learn from outcome
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
        logger.info("Starting self-improvement loop")
        
        while self.running:
            try:
                # Run one iteration of self-play
                results = await self.self_play_loop.run_iteration()
                
                if results['improved']:
                    logger.info(f"System improved at iteration {results['iteration']}")
                    
                    # Store improvement in memory
                    await self.memory_system.store_knowledge(
                        f"improvement_{results['iteration']}",
                        results
                    )
                
                # Longer interval for self-play
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in self-improvement loop: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_loop(self):
        """System monitoring and health checks"""
        logger.info("Starting monitoring loop")
        
        while self.running:
            try:
                status = self.get_comprehensive_status()
                
                # Log periodic status
                logger.info(f"System Status: agents={status['agents']['total_agents']}, "
                           f"tools={status['tools']['total_tools']}, "
                           f"memory={status['memory']['episodic']['total_episodes']}")
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _gather_context(self) -> SystemContext:
        """Gather current system context"""
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
        Execute a task using the full system with multi-agent coordination.
        
        This is the main entry point for external requests.
        It uses the Self-Coordinating Core to leverage teamwork.
        """
        context = context or {}
        
        logger.info(f"Integrated System executing task: {task}")
        
        # For complex tasks, use the Self-Coordinating Core to enable teamwork
        from .coordination_core import TaskType, TaskPriority

        # Determine if we should use coordination core or simple ReAct
        # Heuristic: if task contains multiple keywords, or explicitly requested
        use_coordination = context.get('use_coordination', True)

        if use_coordination:
            result = await self.coordination_core.execute_task(
                task_name=f"Request: {task[:30]}...",
                task_type=TaskType.ANALYSIS,
                description=task,
                priority=TaskPriority.MEDIUM,
                metadata=context
            )

            # Extract final answer from results
            final_answer = "Task completed by coordinated team."
            if result.get('results'):
                # Try to find the most relevant result
                for r in reversed(result['results']):
                    if r.get('result'):
                        final_answer = r['result']
                        break
                    elif r.get('answer'):
                        final_answer = r['answer']
                        break

            return {
                'success': result.get('success', False),
                'answer': final_answer,
                'coordination_report': result,
                'reasoning': f"Multi-agent coordination used. {len(result.get('results', []))} agents involved.",
                'iterations': len(result.get('results', []))
            }
        else:
            # Fallback to simple ReAct loop for simpler tasks
            trace = await self.react_loop.run(
                task=task,
                context=context,
                available_tools=list(self.tool_registry.tools.keys())
            )

            return {
                'success': trace.success,
                'answer': trace.final_answer,
                'reasoning': trace.to_string(),
                'iterations': len(trace.steps)
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
        logger.info("=" * 60)
        logger.info("SHUTTING DOWN INTEGRATED AGENT SYSTEM")
        logger.info("=" * 60)
        
        self.running = False
        
        # Shutdown in reverse order
        logger.info("Shutting down Self-Coordinating Core...")
        await self.coordination_core.shutdown()

        logger.info("Shutting down Self-Play Loop...")
        await self.self_play_loop.shutdown()
        
        logger.info("Shutting down ReAct Loop...")
        await self.react_loop.shutdown()
        
        logger.info("Shutting down Constitutional Layer...")
        await self.constitutional_layer.shutdown()
        
        logger.info("Shutting down Agent Registry...")
        await self.agent_registry.shutdown()
        
        logger.info("Shutting down Tool Registry...")
        await self.tool_registry.shutdown()
        
        logger.info("Shutting down Memory System...")
        await self.memory_system.shutdown()
        
        logger.info("=" * 60)
        logger.info("SHUTDOWN COMPLETE")
        logger.info("=" * 60)


async def main():
    """Main entry point"""
    import signal
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    
    # Create system
    system = IntegratedAgentSystem({
        'storage_path': 'core_agent_data',
        'safety_threshold': 0.7,
        'games_per_iteration': 20,
        'training_batch_size': 16
    })
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        asyncio.create_task(system.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
