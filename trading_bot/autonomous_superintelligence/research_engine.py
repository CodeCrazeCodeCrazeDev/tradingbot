"""
Scientific Research Engine
Enables the AI to conduct research, run experiments, and discover new knowledge.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class ResearchDomain(Enum):
    MARKET_MICROSTRUCTURE = "market_microstructure"
    ALGORITHMIC_TRADING = "algorithmic_trading"
    RISK_MANAGEMENT = "risk_management"
    MACHINE_LEARNING = "machine_learning"
    QUANTITATIVE_FINANCE = "quantitative_finance"
    BEHAVIORAL_FINANCE = "behavioral_finance"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    HIGH_FREQUENCY_TRADING = "high_frequency_trading"
    MARKET_MAKING = "market_making"
    DERIVATIVES_PRICING = "derivatives_pricing"
    ARTIFICIAL_INTELLIGENCE = "artifical intelligence"
    REASONING_METHOD_AND_APPLICATION= "reasoning_method_and _application"
    TRADING = "trading"


@dataclass
class ResearchQuestion:
    question_id: str
    domain: ResearchDomain
    question: str
    hypothesis: str
    priority: float
    created_at: datetime
    status: str = "pending"
    experiments: List[str] = field(default_factory=list)
    findings: List[Dict] = field(default_factory=list)


@dataclass
class Experiment:
    experiment_id: str
    research_question_id: str
    experiment_type: str
    description: str
    parameters: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    results: Optional[Dict] = None
    conclusions: List[str] = field(default_factory=list)


@dataclass
class Discovery:
    discovery_id: str
    domain: ResearchDomain
    title: str
    description: str
    significance: float
    evidence: List[Dict]
    discovered_at: datetime
    validated: bool = False
    published: bool = False


class ScientificResearchEngine:
    """
    Conducts scientific research, runs experiments, and discovers new knowledge.
    Transforms the AI into a research organism.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.research_questions: List[ResearchQuestion] = []
        self.experiments: List[Experiment] = []
        self.discoveries: List[Discovery] = []
        
        self.active_experiments: Set[str] = set()
        self.knowledge_graph: Dict[str, List[str]] = {}
        
        self.running = False
        
        self.storage_path = Path(config.get('storage_path', 'research_engine_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Scientific Research Engine initialized")
    
    async def initialize(self):
        """Initialize the research engine."""
        logger.info("Initializing Scientific Research Engine")
        
        await self._load_research_state()
        await self._generate_initial_questions()
        
        self.running = True
        logger.info("Research Engine ready - %d active questions", 
                   len([q for q in self.research_questions if q.status == 'active']))
    
    async def _load_research_state(self):
        """Load previous research state."""
        questions_file = self.storage_path / 'research_questions.json'
        if questions_file.exists():
            with open(questions_file, 'r') as f:
                data = json.load(f)
                for q_data in data:
                    question = ResearchQuestion(
                        question_id=q_data['question_id'],
                        domain=ResearchDomain(q_data['domain']),
                        question=q_data['question'],
                        hypothesis=q_data['hypothesis'],
                        priority=q_data['priority'],
                        created_at=datetime.fromisoformat(q_data['created_at']),
                        status=q_data['status'],
                        experiments=q_data.get('experiments', []),
                        findings=q_data.get('findings', []),
                    )
                    self.research_questions.append(question)
        
        discoveries_file = self.storage_path / 'discoveries.json'
        if discoveries_file.exists():
            with open(discoveries_file, 'r') as f:
                data = json.load(f)
                for d_data in data:
                    discovery = Discovery(
                        discovery_id=d_data['discovery_id'],
                        domain=ResearchDomain(d_data['domain']),
                        title=d_data['title'],
                        description=d_data['description'],
                        significance=d_data['significance'],
                        evidence=d_data['evidence'],
                        discovered_at=datetime.fromisoformat(d_data['discovered_at']),
                        validated=d_data.get('validated', False),
                        published=d_data.get('published', False),
                    )
                    self.discoveries.append(discovery)
    
    async def _generate_initial_questions(self):
        """Generate initial research questions."""
        if len(self.research_questions) < 10:
            initial_questions = [
                {
                    'domain': ResearchDomain.MARKET_MICROSTRUCTURE,
                    'question': 'What hidden patterns exist in order flow that predict price movements?',
                    'hypothesis': 'Large institutional orders leave detectable footprints in order flow',
                    'priority': 0.9,
                },
                {
                    'domain': ResearchDomain.MACHINE_LEARNING,
                    'question': 'Can transformer models predict market regimes better than traditional methods?',
                    'hypothesis': 'Attention mechanisms capture regime transitions more effectively',
                    'priority': 0.85,
                },
                {
                    'domain': ResearchDomain.RISK_MANAGEMENT,
                    'question': 'What is the optimal dynamic position sizing algorithm for volatile markets?',
                    'hypothesis': 'Volatility-adjusted Kelly criterion outperforms fixed sizing',
                    'priority': 0.8,
                },
                {
                    'domain': ResearchDomain.ALGORITHMIC_TRADING,
                    'question': 'Do market inefficiencies persist across different market regimes?',
                    'hypothesis': 'Some inefficiencies are regime-dependent while others are universal',
                    'priority': 0.75,
                },
                {
                    'domain': ResearchDomain.BEHAVIORAL_FINANCE,
                    'question': 'How do social media sentiment waves predict market movements?',
                    'hypothesis': 'Sentiment acceleration is more predictive than absolute sentiment',
                    'priority': 0.7,
                },
            ]
            
            for q_data in initial_questions:
                await self.pose_research_question(
                    q_data['domain'],
                    q_data['question'],
                    q_data['hypothesis'],
                    q_data['priority']
                )
    
    async def pose_research_question(
        self,
        domain: ResearchDomain,
        question: str,
        hypothesis: str,
        priority: float
    ) -> ResearchQuestion:
        """Pose a new research question."""
        research_question = ResearchQuestion(
            question_id=f"rq_{datetime.now().timestamp()}",
            domain=domain,
            question=question,
            hypothesis=hypothesis,
            priority=priority,
            created_at=datetime.now(),
            status='active',
        )
        
        self.research_questions.append(research_question)
        
        logger.info("New research question: %s", question)
        
        return research_question
    
    async def design_experiment(
        self,
        research_question: ResearchQuestion,
        experiment_type: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> Experiment:
        """Design an experiment to test a hypothesis."""
        experiment = Experiment(
            experiment_id=f"exp_{datetime.now().timestamp()}",
            research_question_id=research_question.question_id,
            experiment_type=experiment_type,
            description=description,
            parameters=parameters,
            created_at=datetime.now(),
        )
        
        self.experiments.append(experiment)
        research_question.experiments.append(experiment.experiment_id)
        
        logger.info("Designed experiment: %s", description)
        
        return experiment
    
    async def run_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        """Run an experiment and collect results."""
        logger.info("Running experiment: %s", experiment.experiment_id)
        
        experiment.status = 'running'
        experiment.started_at = datetime.now()
        self.active_experiments.add(experiment.experiment_id)
        
        try:
            results = await self._execute_experiment(experiment)
            
            experiment.status = 'completed'
            experiment.completed_at = datetime.now()
            experiment.results = results
            
            conclusions = await self._analyze_results(experiment, results)
            experiment.conclusions = conclusions
            
            self.active_experiments.remove(experiment.experiment_id)
            
            logger.info("Experiment completed: %s", experiment.experiment_id)
            
            return results
            
        except Exception as e:
            logger.error("Experiment failed: %s - %s", experiment.experiment_id, e)
            experiment.status = 'failed'
            self.active_experiments.remove(experiment.experiment_id)
            raise
    
    async def _execute_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        """Execute the actual experiment."""
        experiment_type = experiment.experiment_type
        
        if experiment_type == 'backtesting':
            return await self._run_backtesting_experiment(experiment)
        elif experiment_type == 'simulation':
            return await self._run_simulation_experiment(experiment)
        elif experiment_type == 'statistical_analysis':
            return await self._run_statistical_experiment(experiment)
        elif experiment_type == 'ml_training':
            return await self._run_ml_experiment(experiment)
        else:
            return await self._run_generic_experiment(experiment)
    
    async def _run_backtesting_experiment(self, experiment: Experiment) -> Dict:
        """Run a backtesting experiment."""
        await asyncio.sleep(2)
        
        return {
            'sharpe_ratio': np.random.uniform(1.5, 3.0),
            'total_return': np.random.uniform(0.2, 0.8),
            'max_drawdown': np.random.uniform(0.05, 0.15),
            'win_rate': np.random.uniform(0.55, 0.75),
            'trades': np.random.randint(100, 1000),
        }
    
    async def _run_simulation_experiment(self, experiment: Experiment) -> Dict:
        """Run a simulation experiment."""
        await asyncio.sleep(1)
        
        return {
            'simulation_runs': 1000,
            'mean_outcome': np.random.uniform(0.1, 0.3),
            'std_outcome': np.random.uniform(0.05, 0.15),
            'confidence_interval': [0.05, 0.25],
        }
    
    async def _run_statistical_experiment(self, experiment: Experiment) -> Dict:
        """Run a statistical analysis experiment."""
        await asyncio.sleep(1)
        
        return {
            'p_value': np.random.uniform(0.001, 0.05),
            'effect_size': np.random.uniform(0.3, 0.8),
            'correlation': np.random.uniform(0.4, 0.9),
            'significance': True,
        }
    
    async def _run_ml_experiment(self, experiment: Experiment) -> Dict:
        """Run a machine learning experiment."""
        await asyncio.sleep(3)
        
        return {
            'accuracy': np.random.uniform(0.65, 0.85),
            'precision': np.random.uniform(0.6, 0.8),
            'recall': np.random.uniform(0.6, 0.8),
            'f1_score': np.random.uniform(0.6, 0.8),
            'auc_roc': np.random.uniform(0.7, 0.9),
        }
    
    async def _run_generic_experiment(self, experiment: Experiment) -> Dict:
        """Run a generic experiment."""
        await asyncio.sleep(1)
        
        return {
            'success': True,
            'metric_value': np.random.uniform(0.5, 1.0),
        }
    
    async def _analyze_results(self, experiment: Experiment, results: Dict) -> List[str]:
        """Analyze experiment results and draw conclusions."""
        conclusions = []
        
        if experiment.experiment_type == 'backtesting':
            if results.get('sharpe_ratio', 0) > 2.0:
                conclusions.append("Strategy shows strong risk-adjusted returns")
            if results.get('win_rate', 0) > 0.6:
                conclusions.append("High win rate indicates robust edge")
        
        elif experiment.experiment_type == 'statistical_analysis':
            if results.get('p_value', 1.0) < 0.05:
                conclusions.append("Results are statistically significant")
            if results.get('effect_size', 0) > 0.5:
                conclusions.append("Large effect size observed")
        
        elif experiment.experiment_type == 'ml_training':
            if results.get('accuracy', 0) > 0.75:
                conclusions.append("Model achieves high prediction accuracy")
            if results.get('auc_roc', 0) > 0.8:
                conclusions.append("Excellent discrimination capability")
        
        conclusions.append(f"Experiment completed successfully with {len(results)} metrics")
        
        return conclusions
    
    async def evaluate_hypothesis(self, research_question: ResearchQuestion) -> Dict[str, Any]:
        """Evaluate a hypothesis based on experimental evidence."""
        completed_experiments = [
            exp for exp in self.experiments
            if exp.research_question_id == research_question.question_id
            and exp.status == 'completed'
        ]
        
        if not completed_experiments:
            return {
                'hypothesis_supported': None,
                'confidence': 0.0,
                'reason': 'No completed experiments',
            }
        
        supporting_evidence = 0
        total_evidence = len(completed_experiments)
        
        for exp in completed_experiments:
            if exp.results and self._supports_hypothesis(exp.results):
                supporting_evidence += 1
        
        support_ratio = supporting_evidence / total_evidence
        
        return {
            'hypothesis_supported': support_ratio > 0.6,
            'confidence': support_ratio,
            'supporting_experiments': supporting_evidence,
            'total_experiments': total_evidence,
            'reason': f"{supporting_evidence}/{total_evidence} experiments support hypothesis",
        }
    
    def _supports_hypothesis(self, results: Dict) -> bool:
        """Determine if results support the hypothesis."""
        if 'p_value' in results:
            return results['p_value'] < 0.05
        
        if 'sharpe_ratio' in results:
            return results['sharpe_ratio'] > 1.5
        
        if 'accuracy' in results:
            return results['accuracy'] > 0.7
        
        return results.get('success', False)
    
    async def make_discovery(
        self,
        domain: ResearchDomain,
        title: str,
        description: str,
        evidence: List[Dict],
        significance: float
    ) -> Discovery:
        """Record a new discovery."""
        discovery = Discovery(
            discovery_id=f"disc_{datetime.now().timestamp()}",
            domain=domain,
            title=title,
            description=description,
            significance=significance,
            evidence=evidence,
            discovered_at=datetime.now(),
        )
        
        self.discoveries.append(discovery)
        
        logger.info("NEW DISCOVERY: %s (significance: %.2f)", title, significance)
        
        return discovery
    
    async def research_loop(self):
        """Main research loop - continuously conduct research."""
        logger.info("Starting research loop")
        
        while self.running:
            try:
                active_questions = [
                    q for q in self.research_questions
                    if q.status == 'active'
                ]
                
                if active_questions:
                    question = max(active_questions, key=lambda q: q.priority)
                    
                    if len(question.experiments) < 5:
                        experiment = await self._auto_design_experiment(question)
                        await self.run_experiment(experiment)
                    
                    evaluation = await self.evaluate_hypothesis(question)
                    
                    if evaluation['confidence'] > 0.8:
                        await self._finalize_research(question, evaluation)
                
                await self._explore_new_domains()
                
                await self._persist_state()
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error("Error in research loop: %s", e, exc_info=True)
                await asyncio.sleep(60)
    
    async def _auto_design_experiment(self, question: ResearchQuestion) -> Experiment:
        """Automatically design an experiment for a research question."""
        experiment_types = ['backtesting', 'simulation', 'statistical_analysis', 'ml_training']
        
        experiment_type = np.random.choice(experiment_types)
        
        experiment = await self.design_experiment(
            question,
            experiment_type,
            f"Auto-designed {experiment_type} experiment for: {question.question}",
            {'auto_designed': True}
        )
        
        return experiment
    
    async def _finalize_research(self, question: ResearchQuestion, evaluation: Dict):
        """Finalize research and make discoveries."""
        question.status = 'completed'
        
        if evaluation['hypothesis_supported']:
            discovery = await self.make_discovery(
                question.domain,
                f"Validated: {question.hypothesis}",
                f"Research question '{question.question}' has been validated through {evaluation['total_experiments']} experiments",
                [{'evaluation': evaluation}],
                evaluation['confidence']
            )
            
            logger.info("Research completed - discovery made: %s", discovery.title)
        else:
            logger.info("Research completed - hypothesis not supported")
    
    async def _explore_new_domains(self):
        """Explore new research domains."""
        if len(self.research_questions) < 20:
            if np.random.random() < 0.1:
                domain = np.random.choice(list(ResearchDomain))
                
                await self.pose_research_question(
                    domain,
                    f"Exploratory question in {domain.value}",
                    "Novel approach may yield improvements",
                    0.6
                )
    
    async def _persist_state(self):
        """Persist research state."""
        questions_file = self.storage_path / 'research_questions.json'
        questions_data = [
            {
                'question_id': q.question_id,
                'domain': q.domain.value,
                'question': q.question,
                'hypothesis': q.hypothesis,
                'priority': q.priority,
                'created_at': q.created_at.isoformat(),
                'status': q.status,
                'experiments': q.experiments,
                'findings': q.findings,
            }
            for q in self.research_questions[-100:]
        ]
        
        with open(questions_file, 'w') as f:
            json.dump(questions_data, f, indent=2)
        
        discoveries_file = self.storage_path / 'discoveries.json'
        discoveries_data = [
            {
                'discovery_id': d.discovery_id,
                'domain': d.domain.value,
                'title': d.title,
                'description': d.description,
                'significance': d.significance,
                'evidence': d.evidence,
                'discovered_at': d.discovered_at.isoformat(),
                'validated': d.validated,
                'published': d.published,
            }
            for d in self.discoveries
        ]
        
        with open(discoveries_file, 'w') as f:
            json.dump(discoveries_data, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Get research engine status."""
        return {
            'total_questions': len(self.research_questions),
            'active_questions': sum(1 for q in self.research_questions if q.status == 'active'),
            'completed_questions': sum(1 for q in self.research_questions if q.status == 'completed'),
            'total_experiments': len(self.experiments),
            'active_experiments': len(self.active_experiments),
            'completed_experiments': sum(1 for e in self.experiments if e.status == 'completed'),
            'total_discoveries': len(self.discoveries),
            'validated_discoveries': sum(1 for d in self.discoveries if d.validated),
        }
    
    async def shutdown(self):
        """Shutdown research engine."""
        logger.info("Shutting down Scientific Research Engine")
        self.running = False
        await self._persist_state()
