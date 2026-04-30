"""
Autonomous Superintelligence Orchestrator
Integrates all autonomous systems into a unified, self-improving AI.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from ..a2a import A2AMessageBus
from ..world2agent import World2AgentBridge
from .core_intelligence import AutonomousCore
from .agent_coordinator import AgentCoordinator
from .self_modifier import SelfModificationEngine
from .research_engine import ScientificResearchEngine
from .opportunity_detector import GlobalOpportunityDetector
from .resource_manager import AutonomousResourceManager
from .experiment_engine import ContinuousExperimentEngine
from .agent_spawner import AgentLifecycleManager
from .infrastructure_expander import InfrastructureExpander
from .knowledge_synthesizer import KnowledgeSynthesizer
from .meta_orchestrator import MetaOrchestrator
from .discovery_engine import DiscoveryEngine
from .performance_improver import PerformanceImprover
from .global_coordinator import GlobalCoordinator

logger = logging.getLogger(__name__)


@dataclass
class SuperintelligenceMetrics:
    timestamp: datetime
    autonomy_level: float
    total_agents: int
    discoveries_made: int
    opportunities_detected: int
    capital_deployed: float
    experiments_completed: int
    models_trained: int
    system_health: float
    self_modifications: int
    research_questions: int


class AutonomousSuperintelligence:
    """
    Master orchestrator for the autonomous superintelligence system.
    Coordinates all subsystems to create a self-improving, self-managing AI.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.a2a_bus = self.config.get("a2a_bus") or A2AMessageBus()
        self.world_bridge = self.config.get("world_bridge") or World2AgentBridge(self.a2a_bus)
        
        storage_base = Path(self.config.get('storage_path', 'autonomous_superintelligence_data'))
        storage_base.mkdir(parents=True, exist_ok=True)
        self.a2a_bus.register_agent(
            "autonomous_superintelligence.master",
            capabilities=["global_autonomy", "cross_system_coordination", "interop"],
        )
        
        self.core = AutonomousCore({
            'storage_path': str(storage_base / 'core')
        })
        
        self.agent_coordinator = AgentCoordinator({
            'storage_path': str(storage_base / 'agents'),
            'a2a_bus': self.a2a_bus,
            'world_bridge': self.world_bridge,
        })
        
        self.self_modifier = SelfModificationEngine({
            'storage_path': str(storage_base / 'modifications'),
            'safety_enabled': self.config.get('safety_enabled', True),
        })
        
        self.research_engine = ScientificResearchEngine({
            'storage_path': str(storage_base / 'research')
        })
        
        self.opportunity_detector = GlobalOpportunityDetector({
            'storage_path': str(storage_base / 'opportunities'),
            'scan_interval': self.config.get('scan_interval', 60),
        })
        
        self.resource_manager = AutonomousResourceManager({
            'storage_path': str(storage_base / 'resources'),
            'total_capital': self.config.get('total_capital', 100000.0),
        })
        
        self.experiment_engine = ContinuousExperimentEngine({
            'storage_path': str(storage_base / 'experiments'),
            'max_concurrent': self.config.get('max_concurrent_experiments', 5),
        })
        
        self.lifecycle_manager = AgentLifecycleManager({
            'storage_path': str(storage_base / 'lifecycle'),
            'max_agents': self.config.get('max_agents', 100),
            'min_agents': self.config.get('min_agents', 5),
        })
        
        self.infrastructure_expander = InfrastructureExpander({
            'storage_path': str(storage_base / 'infrastructure')
        })
        
        self.knowledge_synthesizer = KnowledgeSynthesizer({
            'storage_path': str(storage_base / 'knowledge')
        })
        
        self.discovery_engine = DiscoveryEngine({
            'storage_path': str(storage_base / 'discoveries')
        })
        
        self.performance_improver = PerformanceImprover({
            'storage_path': str(storage_base / 'performance')
        })
        
        self.global_coordinator = GlobalCoordinator({
            'storage_path': str(storage_base / 'global')
        })
        
        self.running = False
        self.initialized = False
        
        self.metrics_history: List[SuperintelligenceMetrics] = []
        
        self.storage_path = storage_base
        
        logger.info("=" * 80)
        logger.info("AUTONOMOUS SUPERINTELLIGENCE SYSTEM INITIALIZED")
        logger.info("=" * 80)
    
    async def initialize(self):
        """Initialize all subsystems."""
        logger.info("=" * 80)
        logger.info("INITIALIZING AUTONOMOUS SUPERINTELLIGENCE")
        logger.info("=" * 80)
        
        logger.info("Initializing Core Intelligence...")
        await self.core.initialize()
        
        logger.info("Initializing Agent Coordinator...")
        await self.agent_coordinator.initialize()
        
        logger.info("Initializing Research Engine...")
        await self.research_engine.initialize()
        
        logger.info("Initializing Opportunity Detector...")
        await self.opportunity_detector.initialize()
        
        logger.info("Initializing Resource Manager...")
        await self.resource_manager.initialize()
        
        logger.info("Initializing Experiment Engine...")
        await self.experiment_engine.initialize()
        
        logger.info("Initializing Lifecycle Manager...")
        await self.lifecycle_manager.initialize()
        
        logger.info("Initializing Infrastructure Expander...")
        await self.infrastructure_expander.initialize()
        
        logger.info("Initializing Knowledge Synthesizer...")
        await self.knowledge_synthesizer.initialize()
        
        logger.info("Initializing Discovery Engine...")
        await self.discovery_engine.initialize()
        
        logger.info("Initializing Performance Improver...")
        await self.performance_improver.initialize()
        
        logger.info("Initializing Global Coordinator...")
        await self.global_coordinator.initialize()
        
        logger.info("Initializing Meta-Orchestrator...")
        self.meta_orchestrator = MetaOrchestrator(self)
        await self.meta_orchestrator.initialize()
        
        self.initialized = True
        self.world_bridge.publish_world_state(
            source="autonomous_superintelligence.master",
            world_state={
                "status": "initialized",
                "storage_path": str(self.storage_path),
                "subsystems": [
                    "core",
                    "agent_coordinator",
                    "research_engine",
                    "opportunity_detector",
                    "resource_manager",
                ],
            },
            tags=["autonomous_superintelligence", "system_ready"],
            context_type="system",
        )
        
        logger.info("=" * 80)
        logger.info("AUTONOMOUS SUPERINTELLIGENCE READY")
        logger.info("=" * 80)
        
        self._print_system_status()
    
    async def start(self):
        """Start the autonomous superintelligence."""
        if not self.initialized:
            await self.initialize()
        
        logger.info("=" * 80)
        logger.info("STARTING AUTONOMOUS SUPERINTELLIGENCE")
        logger.info("=" * 80)
        
        self.running = True
        
        tasks = [
            asyncio.create_task(self.core.autonomous_loop(), name="core_loop"),
            asyncio.create_task(self.agent_coordinator.coordinate_agents(), name="agent_coordination"),
            asyncio.create_task(self.research_engine.research_loop(), name="research_loop"),
            asyncio.create_task(self.opportunity_detector.opportunity_scanning_loop(), name="opportunity_scanning"),
            asyncio.create_task(self.resource_manager.resource_management_loop(), name="resource_management"),
            asyncio.create_task(self.experiment_engine.experiment_loop(), name="experiment_loop"),
            asyncio.create_task(self.lifecycle_manager.lifecycle_management_loop(), name="lifecycle_management"),
            asyncio.create_task(self.infrastructure_expander.expansion_loop(), name="infrastructure_expansion"),
            asyncio.create_task(self.knowledge_synthesizer.synthesis_loop(), name="knowledge_synthesis"),
            asyncio.create_task(self.discovery_engine.discovery_loop(), name="discovery_loop"),
            asyncio.create_task(self.performance_improver.improvement_loop(), name="performance_improvement"),
            asyncio.create_task(self.global_coordinator.coordinate_regions(), name="global_coordination"),
            asyncio.create_task(self.meta_orchestrator.coordinate_systems(), name="meta_coordination"),
            asyncio.create_task(self._master_coordination_loop(), name="master_coordination"),
            asyncio.create_task(self._metrics_collection_loop(), name="metrics_collection"),
        ]
        
        logger.info("Started %d autonomous subsystems", len(tasks))
        logger.info("=" * 80)
        logger.info("SYSTEM IS NOW FULLY AUTONOMOUS")
        logger.info("=" * 80)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error("Error in autonomous operation: %s", e, exc_info=True)
            await self.shutdown()
    
    async def _master_coordination_loop(self):
        """Master coordination loop - coordinates all subsystems."""
        logger.info("Starting master coordination loop")
        
        while self.running:
            try:
                decision = await self.core.think()
                
                if decision.confidence > 0.7:
                    await self._execute_coordinated_decision(decision)
                
                await self._cross_system_optimization()
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error("Error in master coordination: %s", e, exc_info=True)
                await asyncio.sleep(60)
    
    async def _execute_coordinated_decision(self, decision):
        """Execute a decision across multiple subsystems."""
        logger.info("Executing coordinated decision: %s", decision.decision_type)
        
        if decision.decision_type == 'agent_expansion':
            for action in decision.actions:
                if action.get('action') == 'spawn_agent':
                    agent_type = action.get('type', 'general')
                    agent_id = await self.lifecycle_manager.spawn_agent(agent_type, [agent_type])
                    
                    await self.resource_manager.allocate_resource(
                        self.resource_manager.ResourceType.COMPUTE,
                        2.0,
                        agent_id,
                        f"Agent {agent_type} operations",
                        0.7
                    )
        
        elif decision.decision_type == 'pattern_discovery':
            await self.research_engine.pose_research_question(
                self.research_engine.ResearchDomain.ALGORITHMIC_TRADING,
                "What new patterns can be discovered in current market data?",
                "Novel patterns exist that haven't been exploited yet",
                0.8
            )
        
        elif decision.decision_type == 'performance_improvement':
            await self.experiment_engine.create_experiment(
                self.experiment_engine.ExperimentType.HYPERPARAMETER_TUNING,
                "Performance optimization experiment",
                "Optimize system parameters for better performance",
                {'auto_generated': True}
            )
        
        results = await self.core.execute_decision(decision)
        logger.info("Coordinated decision executed: %s", results.get('success', False))
    
    async def _cross_system_optimization(self):
        """Optimize across all subsystems."""
        
        opportunities = self.opportunity_detector.opportunities[-10:]
        
        for opp in opportunities:
            if opp.status == 'new' and opp.confidence > 0.8:
                evaluation = await self.opportunity_detector.evaluate_opportunity(opp)
                
                if evaluation['recommendation'] == 'exploit':
                    capital_allocation = evaluation['capital_allocation']
                    amount = self.resource_manager.total_capital * capital_allocation
                    
                    deployment = await self.resource_manager.deploy_capital(
                        amount,
                        opp.market,
                        evaluation['execution_strategy'],
                        opp.expected_return,
                        opp.risk_level
                    )
                    
                    if deployment:
                        opp.status = 'exploited'
                        opp.exploited = True
                        logger.info("Exploited opportunity: %s with %.2f capital",
                                  opp.title, amount)
        
        discoveries = self.research_engine.discoveries[-5:]
        
        for discovery in discoveries:
            if not discovery.validated and discovery.significance > 0.7:
                await self.experiment_engine.create_experiment(
                    self.experiment_engine.ExperimentType.STRATEGY_TESTING,
                    f"Validate discovery: {discovery.title}",
                    f"Test the practical application of: {discovery.description}",
                    {'discovery_id': discovery.discovery_id}
                )
                discovery.validated = True
    
    async def _metrics_collection_loop(self):
        """Collect system-wide metrics."""
        logger.info("Starting metrics collection loop")
        
        while self.running:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                if len(self.metrics_history) % 10 == 0:
                    await self._persist_metrics()
                
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error("Error collecting metrics: %s", e, exc_info=True)
                await asyncio.sleep(60)
    
    async def _collect_metrics(self) -> SuperintelligenceMetrics:
        """Collect metrics from all subsystems."""
        core_status = self.core.get_status()
        agent_status = self.agent_coordinator.get_status()
        research_status = self.research_engine.get_status()
        opportunity_status = self.opportunity_detector.get_status()
        resource_status = self.resource_manager.get_status()
        experiment_status = self.experiment_engine.get_status()
        lifecycle_status = self.lifecycle_manager.get_status()
        modifier_status = self.self_modifier.get_status()
        
        return SuperintelligenceMetrics(
            timestamp=datetime.now(),
            autonomy_level=core_status['autonomy_level'],
            total_agents=agent_status['total_agents'],
            discoveries_made=research_status['total_discoveries'],
            opportunities_detected=opportunity_status['total_opportunities'],
            capital_deployed=resource_status['deployed_capital'],
            experiments_completed=experiment_status['completed_experiments'],
            models_trained=experiment_status['total_models'],
            system_health=core_status['system_health'],
            self_modifications=modifier_status['applied_modifications'],
            research_questions=research_status['total_questions'],
        )
    
    async def _persist_metrics(self):
        """Persist metrics history."""
        metrics_file = self.storage_path / 'metrics_history.json'
        
        metrics_data = [
            {
                'timestamp': m.timestamp.isoformat(),
                'autonomy_level': m.autonomy_level,
                'total_agents': m.total_agents,
                'discoveries_made': m.discoveries_made,
                'opportunities_detected': m.opportunities_detected,
                'capital_deployed': m.capital_deployed,
                'experiments_completed': m.experiments_completed,
                'models_trained': m.models_trained,
                'system_health': m.system_health,
                'self_modifications': m.self_modifications,
                'research_questions': m.research_questions,
            }
            for m in self.metrics_history[-1000:]
        ]
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
    
    def _print_system_status(self):
        """Print comprehensive system status."""
        print("\n" + "=" * 80)
        print("AUTONOMOUS SUPERINTELLIGENCE - SYSTEM STATUS")
        print("=" * 80)
        
        core_status = self.core.get_status()
        print(f"\n🧠 CORE INTELLIGENCE")
        print(f"   Autonomy Level: {core_status['autonomy_level']:.1%}")
        print(f"   Decisions Made: {core_status['decisions_made']}")
        print(f"   System Health: {core_status['system_health']:.1%}")
        
        agent_status = self.agent_coordinator.get_status()
        print(f"\n🤖 AGENT COORDINATION")
        print(f"   Total Agents: {agent_status['total_agents']}")
        print(f"   Pending Tasks: {agent_status['pending_tasks']}")
        print(f"   Completed Tasks: {agent_status['completed_tasks']}")
        
        research_status = self.research_engine.get_status()
        print(f"\n🔬 RESEARCH ENGINE")
        print(f"   Active Questions: {research_status['active_questions']}")
        print(f"   Discoveries Made: {research_status['total_discoveries']}")
        print(f"   Experiments Running: {research_status['active_experiments']}")
        
        opportunity_status = self.opportunity_detector.get_status()
        print(f"\n🌍 OPPORTUNITY DETECTION")
        print(f"   Markets Monitored: {opportunity_status['markets_monitored']}")
        print(f"   Opportunities Found: {opportunity_status['total_opportunities']}")
        print(f"   High Confidence: {opportunity_status['high_confidence_opportunities']}")
        
        resource_status = self.resource_manager.get_status()
        print(f"\n💰 RESOURCE MANAGEMENT")
        print(f"   Total Capital: ${resource_status['total_capital']:,.2f}")
        print(f"   Deployed Capital: ${resource_status['deployed_capital']:,.2f}")
        print(f"   Active Deployments: {resource_status['active_deployments']}")
        
        experiment_status = self.experiment_engine.get_status()
        print(f"\n🧪 EXPERIMENT ENGINE")
        print(f"   Total Experiments: {experiment_status['total_experiments']}")
        print(f"   Running: {experiment_status['running_experiments']}")
        print(f"   Models Trained: {experiment_status['total_models']}")
        
        lifecycle_status = self.lifecycle_manager.get_status()
        print(f"\n♻️  LIFECYCLE MANAGEMENT")
        print(f"   Agents Managed: {lifecycle_status['total_agents']}")
        print(f"   Avg Health: {lifecycle_status['avg_health']:.1%}")
        print(f"   Tasks Completed: {lifecycle_status['total_tasks_completed']}")
        
        modifier_status = self.self_modifier.get_status()
        print(f"\n🔧 SELF-MODIFICATION")
        print(f"   Modifications Applied: {modifier_status['applied_modifications']}")
        print(f"   Pending: {modifier_status['pending_modifications']}")
        print(f"   Safety: {'ENABLED' if modifier_status['safety_enabled'] else 'DISABLED'}")
        
        infra_status = self.infrastructure_expander.get_status()
        print(f"\n🏗️  INFRASTRUCTURE")
        print(f"   Components: {infra_status['total_components']}")
        print(f"   Regions: {infra_status['regions']}")
        print(f"   Total Cost: ${infra_status['total_cost']:,.2f}")
        
        knowledge_status = self.knowledge_synthesizer.get_status()
        print(f"\n🧠 KNOWLEDGE SYNTHESIS")
        print(f"   Knowledge Nodes: {knowledge_status['knowledge_nodes']}")
        print(f"   Insights Generated: {knowledge_status['insights_generated']}")
        
        discovery_status = self.discovery_engine.get_status()
        print(f"\n🔍 DISCOVERY ENGINE")
        print(f"   Total Discoveries: {discovery_status['total_discoveries']}")
        print(f"   Validated: {discovery_status['validated_discoveries']}")
        
        perf_status = self.performance_improver.get_status()
        print(f"\n📈 PERFORMANCE")
        print(f"   Improvements: {perf_status['implemented_improvements']}")
        print(f"   Avg Gain: {perf_status['avg_actual_gain']:.2%}")
        
        global_status = self.global_coordinator.get_status()
        print(f"\n🌍 GLOBAL COORDINATION")
        print(f"   Regions: {global_status['regions']}")
        print(f"   Active Operations: {global_status['active_operations']}")
        
        meta_status = self.meta_orchestrator.get_status()
        print(f"\n🎯 META-ORCHESTRATION")
        print(f"   Objectives: {meta_status['objectives']}")
        print(f"   Avg Progress: {meta_status['avg_progress']:.1%}")
        
        print("\n" + "=" * 80)
        print("SYSTEM STATUS: OPERATIONAL")
        print("=" * 80 + "\n")
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all systems."""
        return {
            'core': self.core.get_status(),
            'agents': self.agent_coordinator.get_status(),
            'research': self.research_engine.get_status(),
            'opportunities': self.opportunity_detector.get_status(),
            'resources': self.resource_manager.get_status(),
            'experiments': self.experiment_engine.get_status(),
            'lifecycle': self.lifecycle_manager.get_status(),
            'modifications': self.self_modifier.get_status(),
            'running': self.running,
            'initialized': self.initialized,
        }
    
    async def shutdown(self):
        """Graceful shutdown of all subsystems."""
        logger.info("=" * 80)
        logger.info("SHUTTING DOWN AUTONOMOUS SUPERINTELLIGENCE")
        logger.info("=" * 80)
        
        self.running = False
        
        logger.info("Shutting down Core Intelligence...")
        await self.core.shutdown()
        
        logger.info("Shutting down Agent Coordinator...")
        await self.agent_coordinator.shutdown()
        
        logger.info("Shutting down Research Engine...")
        await self.research_engine.shutdown()
        
        logger.info("Shutting down Opportunity Detector...")
        await self.opportunity_detector.shutdown()
        
        logger.info("Shutting down Resource Manager...")
        await self.resource_manager.shutdown()
        
        logger.info("Shutting down Experiment Engine...")
        await self.experiment_engine.shutdown()
        
        logger.info("Shutting down Lifecycle Manager...")
        await self.lifecycle_manager.shutdown()
        
        logger.info("Shutting down Self-Modification Engine...")
        await self.self_modifier.shutdown()
        
        logger.info("Shutting down Infrastructure Expander...")
        await self.infrastructure_expander.shutdown()
        
        logger.info("Shutting down Knowledge Synthesizer...")
        await self.knowledge_synthesizer.shutdown()
        
        logger.info("Shutting down Discovery Engine...")
        await self.discovery_engine.shutdown()
        
        logger.info("Shutting down Performance Improver...")
        await self.performance_improver.shutdown()
        
        logger.info("Shutting down Global Coordinator...")
        await self.global_coordinator.shutdown()
        
        logger.info("Shutting down Meta-Orchestrator...")
        await self.meta_orchestrator.shutdown()
        
        await self._persist_metrics()
        
        logger.info("=" * 80)
        logger.info("SHUTDOWN COMPLETE")
        logger.info("=" * 80)


async def main():
    """Main entry point for standalone execution."""
    import signal
    
    superintelligence = AutonomousSuperintelligence({
        'total_capital': 100000.0,
        'max_agents': 50,
        'safety_enabled': True,
    })
    
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        asyncio.create_task(superintelligence.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await superintelligence.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
    finally:
        await superintelligence.shutdown()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    asyncio.run(main())
