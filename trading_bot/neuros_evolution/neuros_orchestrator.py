"""
NEUROS Evolution Orchestrator

Master coordinator for the autonomous financial intelligence infrastructure.
Integrates research agents, adaptive networks, autonomous organization,
and continuous evolution.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np

from .research_agents import (
    QuantResearchAgent,
    MLResearchAgent,
    MicrostructureExpert,
    CrossDomainDiscoveryAgent,
    ResearchCoordinator,
)

from .adaptive_network import (
    AdaptiveRoutingNetwork,
    ResourceAllocationEngine,
    TopologyEvolutionEngine,
    LoadBalancingIntelligence,
    NetworkNode,
    NetworkNodeType,
    DataFlow,
)

from .autonomous_org import (
    AIProjectManager,
    PerformanceMonitor,
    ResourceEconomist,
    StrategyPortfolioManager,
)

from .evolution_engine import (
    ArchitectureEvolution,
    KnowledgeSynthesis,
    MetaLearningEngine,
    SelfImprovementEngine,
)

# ASI-Evolve Core Components
from .cognition_store import CognitionStore
from .experiment_database import ExperimentDatabase
from .analyzer import ExperimentAnalyzer
from .researcher import LLMResearcher
from .engineer import ExperimentEngineer

logger = logging.getLogger(__name__)


@dataclass
class NeurosConfig:
    """NEUROS Evolution configuration"""
    initial_capital: float = 1000000.0
    num_quant_agents: int = 3
    num_ml_agents: int = 2
    num_microstructure_agents: int = 1
    num_discovery_agents: int = 2
    evolution_interval_minutes: int = 60
    rebalance_interval_minutes: int = 30
    improvement_cycle_interval_minutes: int = 120
    enable_auto_evolution: bool = True
    enable_auto_rebalancing: bool = True
    enable_self_improvement: bool = True


class NeurosEvolutionOrchestrator:
    """
    Master orchestrator for NEUROS autonomous evolution infrastructure.
    
    Coordinates:
    - Autonomous research agents
    - Self-rewiring network infrastructure
    - Autonomous organization management
    - Continuous evolution engine
    """
    
    def __init__(self, config: Optional[NeurosConfig] = None):
        self.config = config or NeurosConfig()
        
        # Research Division
        self.research_coordinator = ResearchCoordinator()
        self.quant_agents: List[QuantResearchAgent] = []
        self.ml_agents: List[MLResearchAgent] = []
        self.microstructure_agents: List[MicrostructureExpert] = []
        self.discovery_agents: List[CrossDomainDiscoveryAgent] = []
        
        # Network Infrastructure
        self.routing_network = AdaptiveRoutingNetwork()
        self.resource_allocator = ResourceAllocationEngine()
        self.topology_evolver = TopologyEvolutionEngine(self.routing_network)
        self.load_balancer = LoadBalancingIntelligence(self.routing_network)
        
        # Organization Management
        self.project_manager = AIProjectManager('neuros_pm')
        self.performance_monitor = PerformanceMonitor()
        self.resource_economist = ResourceEconomist(self.config.initial_capital)
        self.portfolio_manager = StrategyPortfolioManager()
        
        # ASI-Evolve Evolution Engine
        self.architecture_evolution = ArchitectureEvolution()
        self.knowledge_synthesis = KnowledgeSynthesis()
        self.meta_learning = MetaLearningEngine()
        self.self_improvement = SelfImprovementEngine()
        
        # ASI-Evolve Core Components
        self.cognition_store = CognitionStore()  # Embedding-indexed knowledge base
        self.experiment_database = ExperimentDatabase()  # Persistent experiment storage
        self.experiment_analyzer = ExperimentAnalyzer()  # Complex outcome distillation
        self.llm_researcher = LLMResearcher()  # LLM-based candidate generation
        self.experiment_engineer = ExperimentEngineer()  # Multi-stage execution with early rejection
        
        # State
        self.initialized = False
        self.running = False
        self.background_tasks: List[asyncio.Task] = []
        
        logger.info("NEUROS Evolution Orchestrator created")
    
    async def initialize(self):
        """Initialize all components"""
        if self.initialized:
            logger.warning("Already initialized")
            return
        
        logger.info("Initializing NEUROS Evolution infrastructure...")
        
        # Create research agents with ASI-Evolve architecture
        for i in range(self.config.num_quant_agents):
            agent = QuantResearchAgent(f"quant_{i}")
            # Inject ASI-Evolve components
            agent.cognition_retriever = self.cognition_store
            agent.experiment_database = self.experiment_database
            agent.analyzer = self.experiment_analyzer
            
            self.quant_agents.append(agent)
            self.research_coordinator.register_agent(f"quant_{i}", agent)
        
        for i in range(self.config.num_ml_agents):
            agent = MLResearchAgent(f"ml_{i}")
            # Inject ASI-Evolve components
            agent.cognition_retriever = self.cognition_store
            agent.experiment_database = self.experiment_database
            agent.analyzer = self.experiment_analyzer
            
            self.ml_agents.append(agent)
            self.research_coordinator.register_agent(f"ml_{i}", agent)
        
        for i in range(self.config.num_microstructure_agents):
            agent = MicrostructureExpert(f"micro_{i}")
            # Inject ASI-Evolve components
            agent.cognition_retriever = self.cognition_store
            agent.experiment_database = self.experiment_database
            agent.analyzer = self.experiment_analyzer
            
            self.microstructure_agents.append(agent)
            self.research_coordinator.register_agent(f"micro_{i}", agent)
        
        for i in range(self.config.num_discovery_agents):
            agent = CrossDomainDiscoveryAgent(f"discovery_{i}")
            # Inject ASI-Evolve components
            agent.cognition_retriever = self.cognition_store
            agent.experiment_database = self.experiment_database
            agent.analyzer = self.experiment_analyzer
            
            self.discovery_agents.append(agent)
            self.research_coordinator.register_agent(f"discovery_{i}", agent)
        
        # Initialize ASI-Evolve components
        self.cognition_store.initialize()
        self.experiment_database.initialize()
        self.experiment_analyzer.initialize()
        self.llm_researcher.initialize()
        self.experiment_engineer.initialize()
        
        # Initialize network topology
        self._initialize_network()
        
        self.initialized = True
        logger.info("NEUROS Evolution infrastructure initialized")
    
    def _initialize_network(self):
        """Initialize network topology"""
        # Create network nodes
        nodes = [
            NetworkNode('data_ingestion', NetworkNodeType.DATA_SOURCE, capacity=100.0),
            NetworkNode('preprocessing', NetworkNodeType.PROCESSOR, capacity=80.0),
            NetworkNode('feature_engineering', NetworkNodeType.PROCESSOR, capacity=60.0),
            NetworkNode('signal_generation', NetworkNodeType.ANALYZER, capacity=50.0),
            NetworkNode('risk_analysis', NetworkNodeType.ANALYZER, capacity=40.0),
            NetworkNode('portfolio_optimization', NetworkNodeType.DECISION_MAKER, capacity=30.0),
            NetworkNode('execution', NetworkNodeType.EXECUTOR, capacity=70.0),
            NetworkNode('storage', NetworkNodeType.STORAGE, capacity=200.0),
        ]
        
        for node in nodes:
            self.routing_network.add_node(node)
        
        # Create connections
        connections = [
            ('data_ingestion', 'preprocessing', 1.0),
            ('preprocessing', 'feature_engineering', 1.0),
            ('feature_engineering', 'signal_generation', 1.0),
            ('signal_generation', 'risk_analysis', 1.0),
            ('risk_analysis', 'portfolio_optimization', 1.0),
            ('portfolio_optimization', 'execution', 1.0),
            ('execution', 'storage', 1.0),
            ('data_ingestion', 'storage', 2.0),  # Direct storage path
        ]
        
        for source, dest, weight in connections:
            self.routing_network.add_edge(source, dest, weight)
        
        logger.info(f"Initialized network with {len(nodes)} nodes and {len(connections)} edges")
    
    async def start(self):
        """Start the autonomous system"""
        if not self.initialized:
            await self.initialize()
        
        if self.running:
            logger.warning("Already running")
            return
        
        self.running = True
        logger.info("Starting NEUROS Evolution system...")
        
        # Start background tasks
        if self.config.enable_auto_evolution:
            task = asyncio.create_task(self._evolution_loop())
            self.background_tasks.append(task)
        
        if self.config.enable_auto_rebalancing:
            task = asyncio.create_task(self._rebalancing_loop())
            self.background_tasks.append(task)
        
        if self.config.enable_self_improvement:
            task = asyncio.create_task(self._improvement_loop())
            self.background_tasks.append(task)
        
        logger.info(f"Started {len(self.background_tasks)} background tasks")
    
    async def stop(self):
        """Stop the autonomous system"""
        if not self.running:
            return
        
        logger.info("Stopping NEUROS Evolution system...")
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks.clear()
        
        logger.info("NEUROS Evolution system stopped")
    
    async def _evolution_loop(self):
        """Background evolution loop"""
        while self.running:
            try:
                await asyncio.sleep(self.config.evolution_interval_minutes * 60)
                
                logger.info("Running evolution cycle...")
                
                # ASI-Evolve Researcher: generate and analyze evolution proposals
                context_nodes = self.experiment_database.sample_nodes(sample_n=5)
                cognition_items = self.cognition_store.search("topology optimization", top_k=3)
                
                proposal = await self.llm_researcher.generate_candidate(
                    "architecture_evolution", 
                    context_nodes, cognition_items
                )
                
                # ASI-Evolve Engineer: multi-stage evaluation
                evaluation_result = await self.experiment_engineer.execute_experiment(
                    proposal, 
                    early_rejection=True
                )
                
                # ASI-Evolve Analyzer: distill outcomes into insights
                analysis = await self.experiment_analyzer.analyze_outcome(
                    proposal, evaluation_result
                )
                
                if analysis.get('validation_passed', False):
                    proposal.status = 'rejected'
                else:
                    proposal.status = 'validated'
                
                if proposal.status == 'validated':
                    await self.architecture_evolution.deploy_evolution(proposal)
                
                logger.info(f"Evolution cycle complete: {len(changes)} changes applied")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in evolution loop: {e}")
    
    async def _rebalancing_loop(self):
        """Background rebalancing loop"""
        while self.running:
            try:
                await asyncio.sleep(self.config.rebalance_interval_minutes * 60)
                
                logger.info("Running rebalancing cycle...")
                
                # Rebalance network load
                rebalance_result = await self.load_balancer.rebalance_load()
                
                # ASI-Evolve Knowledge Synthesis: integrate insights across domains
                insights = await self.knowledge_synthesis.synthesize_cross_domain_insights(
                    self.research_coordinator.get_research_summary()
                )
                
                # Update cognition with new insights
                for insight in insights:
                    self.cognition_store.add_cognition_item(insight)
                
                # ASI-Evolve Meta-Learning: adapt parameters based on performance
                performance_feedback = {
                    'discovery_rate': np.random.uniform(0.1, 0.4),
                    'convergence_speed': np.random.uniform(0.3, 0.7),
                    'model_complexity': np.random.uniform(0.4, 0.8),
                }
                
                adaptations = await self.meta_learning.adapt_parameters(performance_feedback)
                
                # ASI-Evolve Self-Improvement: run improvement cycles
                improvement_result = await self.self_improvement.run_improvement_cycle()
                
                logger.info(f"Improvement cycle complete: {improvement_result['improvements_made']} improvements, "
                          f"{len(adaptations)} parameter adaptations")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rebalancing loop: {e}")
    
    async def _improvement_loop(self):
        """Background self-improvement loop"""
        while self.running:
            try:
                await asyncio.sleep(self.config.improvement_cycle_interval_minutes * 60)
                
                logger.info("Running improvement cycle...")
                
                # Run improvement cycle
                result = await self.self_improvement.run_improvement_cycle()
                
                # Adapt meta-learning parameters
                performance_feedback = {
                    'discovery_rate': np.random.uniform(0.1, 0.4),
                    'convergence_speed': np.random.uniform(0.3, 0.7),
                    'model_complexity': np.random.uniform(0.4, 0.8),
                }
                
                adaptations = await self.meta_learning.adapt_parameters(performance_feedback)
                
                logger.info(f"Improvement cycle complete: {result['improvements_made']} improvements, "
                          f"{len(adaptations)} parameter adaptations")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in improvement loop: {e}")
    
    async def run_research_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a complete research cycle"""
        logger.info("Running research cycle...")
        
        # Coordinate research across all agents
        research_results = await self.research_coordinator.coordinate_research(market_data)
        
        # Synthesize insights
        if research_results.get('insights'):
            synthesis = await self.knowledge_synthesis.synthesize_insights(
                research_results['insights']
            )
            research_results['synthesis'] = synthesis
        
        # Record performance metrics
        self.performance_monitor.record_metric(
            'research_coordinator',
            'hypotheses_generated',
            len(research_results.get('hypotheses', [])),
        )
        
        self.performance_monitor.record_metric(
            'research_coordinator',
            'insights_discovered',
            len(research_results.get('insights', [])),
        )
        
        return research_results
    
    async def process_data_flow(self, source: str, destination: str, 
                               data_size_mb: float, priority: int = 5) -> bool:
        """Process a data flow through the network"""
        flow = DataFlow(
            flow_id=f"flow_{datetime.utcnow().timestamp()}",
            source_node=source,
            destination_node=destination,
            data_size_mb=data_size_mb,
            priority=priority,
            created_at=datetime.utcnow(),
        )
        
        success = await self.routing_network.route_data_flow(flow)
        
        if success:
            # Record latency metric
            self.performance_monitor.record_metric(
                'routing_network',
                'flow_latency_ms',
                flow.latency_ms,
                threshold_max=100.0,
            )
        
        return success
    
    def create_research_project(self, name: str, description: str,
                               priority: int, duration_days: int) -> str:
        """Create a new research project"""
        project = self.project_manager.create_project(
            name=name,
            description=description,
            priority=priority,
            estimated_duration_days=duration_days,
            required_resources={'compute': 10.0, 'data': 5.0},
        )
        
        return project.project_id
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'initialized': self.initialized,
            'running': self.running,
            'research': {
                'total_agents': len(self.quant_agents) + len(self.ml_agents) + 
                               len(self.microstructure_agents) + len(self.discovery_agents),
                'quant_agents': len(self.quant_agents),
                'ml_agents': len(self.ml_agents),
                'microstructure_agents': len(self.microstructure_agents),
                'discovery_agents': len(self.discovery_agents),
                'coordinator_summary': self.research_coordinator.get_research_summary(),
            },
            'network': {
                'status': self.routing_network.get_network_status(),
                'resources': self.resource_allocator.get_resource_status(),
            },
            'organization': {
                'active_projects': len(self.project_manager.get_active_projects()),
                'system_health': self.performance_monitor.get_system_health(),
                'capital_allocation': self.resource_economist.get_allocation_summary(),
                'portfolio': self.portfolio_manager.get_portfolio_summary(),
            },
            'evolution': {
                'architecture': self.architecture_evolution.get_evolution_summary(),
                'knowledge': self.knowledge_synthesis.get_knowledge_summary(),
                'meta_learning': self.meta_learning.get_meta_learning_summary(),
                'self_improvement': self.self_improvement.get_improvement_summary(),
            },
            'background_tasks': len(self.background_tasks),
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'research_productivity': {
                'hypotheses_generated': sum(
                    agent.performance_metrics['hypotheses_generated']
                    for agent in self.quant_agents
                ),
                'hypotheses_validated': sum(
                    agent.performance_metrics['hypotheses_validated']
                    for agent in self.quant_agents
                ),
                'models_tested': sum(
                    agent.performance_metrics['models_tested']
                    for agent in self.ml_agents
                ),
            },
            'system_performance': {
                'network_efficiency': self.routing_network.get_network_status(),
                'resource_utilization': self.resource_allocator.get_resource_status(),
            },
            'organizational_intelligence': {
                'projects_completed': len(self.project_manager.completed_projects),
                'capital_efficiency': self.resource_economist.get_allocation_summary()['utilization'],
                'portfolio_risk': self.portfolio_manager.calculate_portfolio_risk(),
            },
            'evolution_velocity': {
                'architecture_changes': len(self.architecture_evolution.evolution_history),
                'knowledge_nodes': len(self.knowledge_synthesis.knowledge_graph),
                'improvement_cycles': len(self.self_improvement.improvement_history),
            },
        }


def quick_start(config: Optional[Dict[str, Any]] = None) -> NeurosEvolutionOrchestrator:
    """Quick start NEUROS Evolution system"""
    neuros_config = NeurosConfig()
    
    if config:
        for key, value in config.items():
            if hasattr(neuros_config, key):
                setattr(neuros_config, key, value)
    
    orchestrator = NeurosEvolutionOrchestrator(neuros_config)
    
    return orchestrator
