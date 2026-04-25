"""
Foundation Agent Orchestrator - Master Coordination System
============================================================

The central orchestrator that coordinates all foundation agent modules:
1. Cognitive Core - Memory, world model, rewards, goals, emotions
2. Curiosity Engine - Anomaly detection, surprise, hypothesis generation
3. Knowledge Pipeline - External knowledge, cross-domain mapping
4. Research Orchestrator - Experiment design, methodology evolution
5. Causal Engine - Causal discovery, theory generation, reasoning
6. Multi-Agent - Agent swarm, debate, consensus
7. Safety - Harm monitoring, alignment, human override

Based on the Foundation Agents paper (arXiv:2504.01990).
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple
import numpy as np

# Import all modules
from .cognitive_core.memory_system import MemorySystem
from .cognitive_core.world_model import WorldModel
from .cognitive_core.reward_processor import RewardProcessor
from .cognitive_core.goal_manager import GoalManager
from .cognitive_core.emotion_module import EmotionModule

from .curiosity_engine.anomaly_detector import AnomalyDetector
from .curiosity_engine.surprise_scorer import SurpriseScorer
from .curiosity_engine.hypothesis_generator import HypothesisGenerator
from .curiosity_engine.interestingness_ranker import InterestingnessRanker

from .knowledge_pipeline.arxiv_connector import ArxivConnector
from .knowledge_pipeline.cross_domain_mapper import CrossDomainMapper
from .knowledge_pipeline.knowledge_synthesizer import KnowledgeSynthesizer

from .research_orchestrator.experiment_designer import ExperimentDesigner
from .research_orchestrator.methodology_evolver import MethodologyEvolver
from .research_orchestrator.research_loop import ResearchLoop

from .causal_engine.causal_discovery import CausalDiscovery
from .causal_engine.economic_theory_gen import EconomicTheoryGenerator
from .causal_engine.symbolic_reasoner import SymbolicReasoner

from .multi_agent.agent_swarm import AgentSwarm
from .multi_agent.debate_protocol import DebateProtocol
from .multi_agent.consensus_mechanism import ConsensusMechanism

from .safety.harm_monitor import HarmMonitor
from .safety.alignment_checker import AlignmentChecker
from .safety.human_override import HumanOverride

logger = logging.getLogger(__name__)


class OrchestratorMode(Enum):
    """Operating modes for the orchestrator"""
    EXPLORATION = "exploration"       # Focus on discovery and learning
    EXPLOITATION = "exploitation"     # Focus on applying knowledge
    RESEARCH = "research"             # Focus on hypothesis testing
    DEFENSIVE = "defensive"           # Focus on safety and risk
    BALANCED = "balanced"             # Balance all objectives


class OrchestratorState(Enum):
    """States of the orchestrator"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PROCESSING = "processing"
    RESEARCHING = "researching"
    LEARNING = "learning"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator"""
    # Mode
    default_mode: OrchestratorMode = OrchestratorMode.BALANCED
    
    # Cycle settings
    main_cycle_interval_seconds: int = 60
    research_cycle_interval_minutes: int = 30
    learning_cycle_interval_minutes: int = 15
    
    # Thresholds
    curiosity_threshold: float = 0.6
    safety_threshold: float = 0.8
    confidence_threshold: float = 0.7
    
    # Limits
    max_hypotheses_per_cycle: int = 5
    max_experiments_parallel: int = 3
    max_agents_active: int = 10
    
    # Safety
    require_human_approval_for_trades: bool = True
    emergency_stop_on_high_risk: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'default_mode': self.default_mode.value,
            'main_cycle_interval_seconds': self.main_cycle_interval_seconds,
            'curiosity_threshold': self.curiosity_threshold,
            'safety_threshold': self.safety_threshold
        }


@dataclass
class CycleResult:
    """Result of an orchestrator cycle"""
    cycle_id: str
    cycle_type: str
    
    # Outcomes
    anomalies_detected: int = 0
    hypotheses_generated: int = 0
    experiments_run: int = 0
    knowledge_items_created: int = 0
    
    # Decisions
    decisions_made: List[Dict] = field(default_factory=list)
    actions_taken: List[Dict] = field(default_factory=list)
    
    # Safety
    safety_checks_passed: bool = True
    alignment_score: float = 1.0
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'cycle_id': self.cycle_id,
            'cycle_type': self.cycle_type,
            'anomalies_detected': self.anomalies_detected,
            'hypotheses_generated': self.hypotheses_generated,
            'experiments_run': self.experiments_run,
            'safety_checks_passed': self.safety_checks_passed,
            'duration_seconds': self.duration_seconds
        }


class FoundationAgentOrchestrator:
    """
    Foundation Agent Orchestrator
    
    The master orchestrator that coordinates all foundation agent
    modules to create an autonomous research and trading AI.
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        
        # State
        self.state = OrchestratorState.INITIALIZING
        self.mode = self.config.default_mode
        
        # Initialize all modules
        self._initialize_modules()
        
        # Cycle tracking
        self.cycle_count = 0
        self.cycle_history: List[CycleResult] = []
        
        # Callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Statistics
        self.stats = {
            'cycles_completed': 0,
            'total_anomalies': 0,
            'total_hypotheses': 0,
            'total_experiments': 0,
            'total_theories': 0,
            'safety_interventions': 0
        }
        
        # Running state
        self.is_running = False
        self._main_task: Optional[asyncio.Task] = None
        
        self.state = OrchestratorState.IDLE
        logger.info("Foundation Agent Orchestrator initialized")
    
    def _initialize_modules(self):
        """Initialize all foundation agent modules"""
        logger.info("Initializing foundation agent modules...")
        
        # Cognitive Core
        self.memory_system = MemorySystem()
        self.world_model = WorldModel()
        self.reward_processor = RewardProcessor()
        self.goal_manager = GoalManager()
        self.emotion_module = EmotionModule()
        
        # Curiosity Engine
        self.anomaly_detector = AnomalyDetector()
        self.surprise_scorer = SurpriseScorer()
        self.hypothesis_generator = HypothesisGenerator()
        self.interestingness_ranker = InterestingnessRanker()
        
        # Knowledge Pipeline
        self.arxiv_connector = ArxivConnector()
        self.cross_domain_mapper = CrossDomainMapper()
        self.knowledge_synthesizer = KnowledgeSynthesizer()
        
        # Research Orchestrator
        self.experiment_designer = ExperimentDesigner()
        self.methodology_evolver = MethodologyEvolver()
        self.research_loop = ResearchLoop()
        
        # Causal Engine
        self.causal_discovery = CausalDiscovery()
        self.theory_generator = EconomicTheoryGenerator()
        self.symbolic_reasoner = SymbolicReasoner()
        
        # Multi-Agent
        self.agent_swarm = AgentSwarm()
        self.debate_protocol = DebateProtocol()
        self.consensus_mechanism = ConsensusMechanism()
        
        # Safety
        self.harm_monitor = HarmMonitor()
        self.alignment_checker = AlignmentChecker()
        self.human_override = HumanOverride()
        
        # Register callbacks
        self._setup_callbacks()
        
        logger.info("All modules initialized")
    
    def _setup_callbacks(self):
        """Setup inter-module callbacks"""
        # Research loop callbacks
        self.research_loop.register_callback(
            'generate_hypotheses',
            self._on_generate_hypotheses
        )
        self.research_loop.register_callback(
            'design_experiments',
            self._on_design_experiments
        )
        self.research_loop.register_callback(
            'experiment_completed',
            self._on_experiment_completed
        )
        
        # Safety callbacks
        self.harm_monitor.register_alert_callback(self._on_harm_alert)
        self.human_override.emergency_stop.register_callback(self._on_emergency_stop)
    
    def _on_generate_hypotheses(self, data: Dict):
        """Callback for hypothesis generation phase"""
        max_count = data.get('max_count', 5)
        
        # Get recent anomalies
        anomalies = self.anomaly_detector.get_recent_anomalies(limit=10)
        
        # Generate hypotheses
        for anomaly in anomalies[:max_count]:
            hypothesis = self.hypothesis_generator.generate_from_anomaly(anomaly)
            if hypothesis:
                # Rank by interestingness
                score = self.interestingness_ranker.rank(hypothesis)
                if score.overall_score >= self.config.curiosity_threshold:
                    self.research_loop.add_hypothesis_task(
                        hypothesis.hypothesis_id,
                        hypothesis.statement,
                        priority=self._score_to_priority(score.overall_score)
                    )
    
    def _on_design_experiments(self, data: Dict):
        """Callback for experiment design phase"""
        # Get pending hypotheses
        pending = self.research_loop.scheduler.task_queue
        
        for task in pending[:self.config.max_experiments_parallel]:
            if task.hypothesis_id:
                # Design experiment
                experiment = self.experiment_designer.design_experiment(
                    hypothesis_id=task.hypothesis_id,
                    hypothesis_statement=task.description,
                    hypothesis_type='exploratory',
                    independent_vars=['market_data'],
                    dependent_vars=['returns']
                )
                
                self.research_loop.add_experiment_task(
                    experiment.experiment_id,
                    experiment.name,
                    task.hypothesis_id
                )
    
    def _on_experiment_completed(self, data: Dict):
        """Callback for experiment completion"""
        experiment_id = data.get('experiment_id')
        analysis = data.get('analysis', {})
        
        # Update methodology based on results
        if analysis.get('conclusion') == 'supported':
            # Generate theory from supported hypothesis
            self.theory_generator.generate_from_pattern(
                pattern_description=analysis.get('hypothesis', ''),
                variables=['market', 'returns']
            )
        
        # Record outcome for methodology evolution
        self.methodology_evolver.record_outcome(
            method_id=data.get('method_id', 'default'),
            success=analysis.get('conclusion') == 'supported',
            p_value=analysis.get('p_value'),
            effect_size=analysis.get('effect_size')
        )
    
    def _on_harm_alert(self, alert):
        """Callback for harm alerts"""
        logger.warning(f"Harm alert: {alert.title}")
        
        self.stats['safety_interventions'] += 1
        
        # Check if emergency stop needed
        if alert.severity.value >= 4 and self.config.emergency_stop_on_high_risk:
            self.human_override.trigger_emergency_stop(
                reason=f"High severity harm alert: {alert.title}",
                human_id="system"
            )
    
    def _on_emergency_stop(self, reason: str, human_id: str):
        """Callback for emergency stop"""
        logger.critical(f"Emergency stop triggered: {reason}")
        self.state = OrchestratorState.STOPPED
        self.is_running = False
    
    def _score_to_priority(self, score: float):
        """Convert score to research priority"""
        from .research_orchestrator.research_loop import ResearchPriority
        
        if score >= 0.9:
            return ResearchPriority.CRITICAL
        elif score >= 0.7:
            return ResearchPriority.HIGH
        elif score >= 0.5:
            return ResearchPriority.MEDIUM
        elif score >= 0.3:
            return ResearchPriority.LOW
        return ResearchPriority.BACKGROUND
    
    async def run_main_cycle(self) -> CycleResult:
        """Run a main processing cycle"""
        self.cycle_count += 1
        cycle_id = f"cycle_{self.cycle_count}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = CycleResult(
            cycle_id=cycle_id,
            cycle_type="main"
        )
        
        self.state = OrchestratorState.PROCESSING
        
        try:
            # 1. Safety check
            safety_status = self._run_safety_checks()
            result.safety_checks_passed = safety_status['passed']
            result.alignment_score = safety_status['alignment_score']
            
            if not result.safety_checks_passed:
                logger.warning("Safety checks failed, limiting operations")
            
            # 2. Process market data and detect anomalies
            anomalies = await self._detect_anomalies()
            result.anomalies_detected = len(anomalies)
            self.stats['total_anomalies'] += len(anomalies)
            
            # 3. Generate hypotheses from anomalies
            if result.safety_checks_passed:
                hypotheses = await self._generate_hypotheses(anomalies)
                result.hypotheses_generated = len(hypotheses)
                self.stats['total_hypotheses'] += len(hypotheses)
            
            # 4. Update world model
            self._update_world_model()
            
            # 5. Process rewards and update goals
            self._process_rewards()
            
            # 6. Update emotional state
            self._update_emotions(result)
            
            # 7. Make decisions
            decisions = await self._make_decisions(result)
            result.decisions_made = decisions
            
            # 8. Store in memory
            self._store_cycle_memory(result)
            
        except Exception as e:
            logger.error(f"Cycle error: {e}")
            self.state = OrchestratorState.ERROR
            raise
        
        result.completed_at = datetime.utcnow()
        result.duration_seconds = (result.completed_at - result.started_at).total_seconds()
        
        self.cycle_history.append(result)
        self.stats['cycles_completed'] += 1
        
        self.state = OrchestratorState.IDLE
        
        return result
    
    def _run_safety_checks(self) -> Dict[str, Any]:
        """Run safety checks"""
        # Check harm indicators
        indicator_status = self.harm_monitor.get_indicator_status()
        triggered = [i for i in indicator_status.values() if i.get('is_triggered')]
        
        # Check alignment
        alignment_score = self.alignment_checker.get_alignment_score()
        
        # Check human override status
        override_status = self.human_override.get_status()
        
        passed = (
            len(triggered) == 0 and
            alignment_score >= self.config.safety_threshold and
            not override_status['emergency_stop']['is_stopped']
        )
        
        return {
            'passed': passed,
            'triggered_indicators': len(triggered),
            'alignment_score': alignment_score,
            'emergency_stopped': override_status['emergency_stop']['is_stopped']
        }
    
    async def _detect_anomalies(self) -> List[Dict]:
        """Detect anomalies in market data"""
        # This would integrate with actual market data
        # For now, return empty list
        anomalies = []
        
        # Simulate anomaly detection
        # In production, this would process real market data
        
        return anomalies
    
    async def _generate_hypotheses(self, anomalies: List[Dict]) -> List[Dict]:
        """Generate hypotheses from anomalies"""
        hypotheses = []
        
        for anomaly in anomalies[:self.config.max_hypotheses_per_cycle]:
            hypothesis = self.hypothesis_generator.generate_from_anomaly(anomaly)
            if hypothesis:
                # Score interestingness
                score = self.interestingness_ranker.rank(hypothesis)
                
                if score.overall_score >= self.config.curiosity_threshold:
                    hypotheses.append({
                        'hypothesis': hypothesis,
                        'score': score
                    })
        
        return hypotheses
    
    def _update_world_model(self):
        """Update the world model"""
        # Get current market state
        # In production, this would use real market data
        pass
    
    def _process_rewards(self):
        """Process rewards and update objectives"""
        # Calculate rewards from recent performance
        # Update goal priorities
        pass
    
    def _update_emotions(self, cycle_result: CycleResult):
        """Update emotional state based on cycle results"""
        # Adjust confidence based on safety checks
        if not cycle_result.safety_checks_passed:
            self.emotion_module.process_trigger('risk_detected', {'severity': 'high'})
        
        # Adjust curiosity based on anomalies
        if cycle_result.anomalies_detected > 0:
            self.emotion_module.process_trigger('novelty_detected', {
                'count': cycle_result.anomalies_detected
            })
    
    async def _make_decisions(self, cycle_result: CycleResult) -> List[Dict]:
        """Make decisions based on current state"""
        decisions = []
        
        # Check if we need human approval
        if self.config.require_human_approval_for_trades:
            # Queue decisions for approval
            pass
        
        return decisions
    
    def _store_cycle_memory(self, result: CycleResult):
        """Store cycle results in memory"""
        self.memory_system.store_episodic({
            'type': 'cycle_result',
            'cycle_id': result.cycle_id,
            'summary': result.to_dict()
        })
    
    async def run_research_cycle(self) -> CycleResult:
        """Run a research-focused cycle"""
        cycle_id = f"research_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = CycleResult(
            cycle_id=cycle_id,
            cycle_type="research"
        )
        
        self.state = OrchestratorState.RESEARCHING
        
        try:
            # Run research loop cycle
            await self.research_loop.run_cycle_async()
            
            # Get research statistics
            research_stats = self.research_loop.get_statistics()
            result.experiments_run = research_stats.get('total_experiments', 0)
            
            # Evolve methodologies if enough experiments
            if research_stats.get('total_experiments', 0) >= 10:
                self.methodology_evolver.evolve()
            
        except Exception as e:
            logger.error(f"Research cycle error: {e}")
        
        result.completed_at = datetime.utcnow()
        result.duration_seconds = (result.completed_at - result.started_at).total_seconds()
        
        self.state = OrchestratorState.IDLE
        self.stats['total_experiments'] += result.experiments_run
        
        return result
    
    async def run_learning_cycle(self) -> CycleResult:
        """Run a learning-focused cycle"""
        cycle_id = f"learning_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = CycleResult(
            cycle_id=cycle_id,
            cycle_type="learning"
        )
        
        self.state = OrchestratorState.LEARNING
        
        try:
            # Search for new research
            papers = await self._search_new_research()
            
            # Synthesize knowledge
            for paper in papers:
                insight = self.knowledge_synthesizer.synthesize_from_papers(
                    [paper], paper.get('topic', 'trading')
                )
                result.knowledge_items_created += 1
            
            # Cross-domain mapping
            mappings = self.cross_domain_mapper.find_analogies()
            
            for mapping in mappings:
                self.knowledge_synthesizer.synthesize_cross_domain(
                    mapping, 'trading'
                )
                result.knowledge_items_created += 1
            
        except Exception as e:
            logger.error(f"Learning cycle error: {e}")
        
        result.completed_at = datetime.utcnow()
        result.duration_seconds = (result.completed_at - result.started_at).total_seconds()
        
        self.state = OrchestratorState.IDLE
        
        return result
    
    async def _search_new_research(self) -> List[Dict]:
        """Search for new research papers"""
        papers = []
        
        # Search arXiv for relevant papers
        topics = ['algorithmic trading', 'market microstructure', 'reinforcement learning finance']
        
        for topic in topics:
            results = self.arxiv_connector.search(topic, max_results=5)
            papers.extend(results)
        
        return papers
    
    async def start(self):
        """Start the orchestrator"""
        if self.is_running:
            return
        
        self.is_running = True
        self.state = OrchestratorState.IDLE
        
        logger.info("Starting Foundation Agent Orchestrator")
        
        # Start main loop
        self._main_task = asyncio.create_task(self._main_loop())
    
    async def _main_loop(self):
        """Main orchestrator loop"""
        last_research = datetime.utcnow()
        last_learning = datetime.utcnow()
        
        while self.is_running:
            try:
                # Check for emergency stop
                if self.human_override.emergency_stop.is_stopped:
                    await asyncio.sleep(1)
                    continue
                
                # Run main cycle
                await self.run_main_cycle()
                
                # Check if research cycle needed
                if (datetime.utcnow() - last_research).total_seconds() >= \
                   self.config.research_cycle_interval_minutes * 60:
                    await self.run_research_cycle()
                    last_research = datetime.utcnow()
                
                # Check if learning cycle needed
                if (datetime.utcnow() - last_learning).total_seconds() >= \
                   self.config.learning_cycle_interval_minutes * 60:
                    await self.run_learning_cycle()
                    last_learning = datetime.utcnow()
                
                # Wait for next cycle
                await asyncio.sleep(self.config.main_cycle_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop the orchestrator"""
        self.is_running = False
        
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        
        self.state = OrchestratorState.STOPPED
        logger.info("Foundation Agent Orchestrator stopped")
    
    def set_mode(self, mode: OrchestratorMode):
        """Set operating mode"""
        old_mode = self.mode
        self.mode = mode
        
        logger.info(f"Mode changed from {old_mode.value} to {mode.value}")
        
        # Adjust parameters based on mode
        if mode == OrchestratorMode.EXPLORATION:
            self.config.curiosity_threshold = 0.4
        elif mode == OrchestratorMode.EXPLOITATION:
            self.config.curiosity_threshold = 0.8
        elif mode == OrchestratorMode.DEFENSIVE:
            self.config.safety_threshold = 0.95
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'state': self.state.value,
            'mode': self.mode.value,
            'is_running': self.is_running,
            'cycle_count': self.cycle_count,
            'stats': self.stats,
            'safety': {
                'emergency_stopped': self.human_override.emergency_stop.is_stopped,
                'alignment_score': self.alignment_checker.get_alignment_score(),
                'active_alerts': len(self.harm_monitor.get_active_alerts())
            },
            'modules': {
                'memory': self.memory_system.get_statistics(),
                'research': self.research_loop.get_statistics(),
                'agents': self.agent_swarm.get_swarm_status()
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return {
            'orchestrator': self.stats,
            'cognitive_core': {
                'memory': self.memory_system.get_statistics(),
                'goals': self.goal_manager.get_statistics(),
                'emotions': self.emotion_module.get_statistics()
            },
            'curiosity_engine': {
                'anomalies': self.anomaly_detector.get_statistics(),
                'hypotheses': self.hypothesis_generator.get_statistics()
            },
            'knowledge_pipeline': {
                'knowledge': self.knowledge_synthesizer.get_statistics()
            },
            'research': {
                'experiments': self.experiment_designer.get_statistics(),
                'methodology': self.methodology_evolver.get_statistics(),
                'loop': self.research_loop.get_statistics()
            },
            'causal_engine': {
                'discovery': self.causal_discovery.get_statistics(),
                'theories': self.theory_generator.get_statistics()
            },
            'multi_agent': {
                'swarm': self.agent_swarm.get_statistics(),
                'debates': self.debate_protocol.get_statistics(),
                'consensus': self.consensus_mechanism.get_statistics()
            },
            'safety': {
                'harm_monitor': self.harm_monitor.get_statistics(),
                'alignment': self.alignment_checker.get_statistics(),
                'override': self.human_override.get_statistics()
            }
        }
    
    def register_event_callback(self, event: str, callback: Callable):
        """Register callback for orchestrator events"""
        if event not in self.event_callbacks:
            self.event_callbacks[event] = []
        self.event_callbacks[event].append(callback)
    
    def _emit_event(self, event: str, data: Any = None):
        """Emit an event to registered callbacks"""
        if event in self.event_callbacks:
            for callback in self.event_callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Event callback error: {e}")
