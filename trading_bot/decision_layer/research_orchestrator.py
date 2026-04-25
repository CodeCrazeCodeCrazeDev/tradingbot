"""
Research Orchestrator for Decision Layer
=========================================

ASI-Evolve inspired four-agent system for autonomous trading research.
Adapts the arXiv:2603.29640 framework for financial decision making.

Four-Agent System:
- Researcher: Generates candidate decision strategies using LLM-based reasoning
- Engineer: Executes experiments, handles early rejection
- Analyzer: Distills complex outputs into actionable insights  
- Cognition: Semantic knowledge base with embedding-based retrieval

Author: AlphaAlgo Research Lab
"""

import asyncio
import hashlib
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Status of an experiment in the research pipeline"""
    PENDING = "pending"
    RUNNING = "running"
    EXPLORATION = "exploration"
    VERIFICATION = "verification"
    VALIDATION = "validation"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class SamplingPolicy(Enum):
    """Policies for sampling from experiment database"""
    UCB1 = "ucb1"
    GREEDY = "greedy"
    RANDOM = "random"
    MAP_ELITES = "map_elites"


@dataclass
class ResearchMotivation:
    """Motivation for a research direction"""
    id: str
    description: str
    rationale: str
    expected_improvement: float
    source: str  # 'gap_analysis', 'failure_pattern', 'novel_idea', 'cross_domain'
    novelty_score: float  # 0-1, how novel is this direction
    related_motivations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def compute_similarity(self, other: 'ResearchMotivation') -> float:
        """Compute semantic similarity to another motivation"""
        # Simple keyword overlap - could use embeddings in production
        words1 = set(self.description.lower().split())
        words2 = set(other.description.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        return len(intersection) / max(len(words1), len(words2))


@dataclass
class ExperimentNode:
    """Node in the experiment graph"""
    id: str
    motivation: ResearchMotivation
    code: str  # Decision strategy implementation
    results: Dict[str, Any] = field(default_factory=dict)
    analysis: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: ExperimentStatus = ExperimentStatus.PENDING
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    score: float = 0.0
    visits: int = 0
    creation_time: datetime = field(default_factory=datetime.utcnow)
    completion_time: Optional[datetime] = None
    
    def compute_hash(self) -> str:
        """Compute unique hash for deduplication"""
        content = f"{self.motivation.description}:{self.code}:{self.creation_time.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class CognitionEntry:
    """Entry in the cognition store (semantic knowledge base)"""
    id: str
    content: str
    embedding: List[float]  # Vector embedding
    entry_type: str  # 'strategy', 'pattern', 'insight', 'failure', 'success'
    source_experiment: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class AnalysisResult:
    """Result from the analyzer agent"""
    insights: List[str]
    actionable_recommendations: List[str]
    confidence: float
    key_metrics: Dict[str, float]
    improvement_potential: float


class ResearcherAgent:
    """
    Researcher Agent: Generates candidate programs/strategies
    
    Responsibilities:
    - Generate novel decision strategies based on motivations
    - Condition on context and existing cognition
    - Ensure diversity of approaches
    """
    
    def __init__(self, cognition_store: 'CognitionStore'):
        self.cognition = cognition_store
        self.generation_count = 0
        
    async def generate_strategy(
        self,
        motivation: ResearchMotivation,
        context: Dict[str, Any],
        num_candidates: int = 3
    ) -> List[str]:
        """
        Generate candidate decision strategies based on motivation.
        
        In production, this would use LLM-based generation.
        For now, we use template-based generation.
        """
        candidates = []
        
        # Retrieve relevant prior knowledge
        relevant_entries = self.cognition.retrieve_similar(
            motivation.description,
            k=5,
            entry_type='strategy'
        )
        
        # Generate diverse candidates
        for i in range(num_candidates):
            strategy = self._generate_strategy_template(
                motivation, context, relevant_entries, variation=i
            )
            candidates.append(strategy)
        
        self.generation_count += num_candidates
        logger.info(f"Generated {num_candidates} strategy candidates for motivation {motivation.id}")
        
        return candidates
    
    def _generate_strategy_template(
        self,
        motivation: ResearchMotivation,
        context: Dict[str, Any],
        prior_knowledge: List[CognitionEntry],
        variation: int
    ) -> str:
        """Generate a strategy implementation (template-based for now)"""
        # Template strategies based on motivation type
        templates = {
            'gap_analysis': [
                "class GapFillingStrategy:\n    def decide(self, ctx):\n        # Addresses identified gap\n        return self.adaptive_decision(ctx)",
                "class EnhancedRiskStrategy:\n    def decide(self, ctx):\n        # Enhanced risk management\n        return self.risk_aware_decision(ctx)",
            ],
            'failure_pattern': [
                "class FailureResistantStrategy:\n    def decide(self, ctx):\n        # Avoids known failure patterns\n        return self.robust_decision(ctx)",
                "class PatternAwareStrategy:\n    def decide(self, ctx):\n        # Detects and avoids failure patterns\n        return self.pattern_safe_decision(ctx)",
            ],
            'novel_idea': [
                "class NovelStrategy:\n    def decide(self, ctx):\n        # Novel approach\n        return self.innovative_decision(ctx)",
                "class ExperimentalStrategy:\n    def decide(self, ctx):\n        # Experimental technique\n        return self.experimental_decision(ctx)",
            ],
            'cross_domain': [
                "class CrossDomainStrategy:\n    def decide(self, ctx):\n        # Adapted from other domain\n        return self.transferred_decision(ctx)",
                "class HybridStrategy:\n    def decide(self, ctx):\n        # Hybrid approach\n        return self.hybrid_decision(ctx)",
            ]
        }
        
        source_templates = templates.get(motivation.source, templates['novel_idea'])
        return source_templates[variation % len(source_templates)]


class EngineerAgent:
    """
    Engineer Agent: Executes experiments
    
    Responsibilities:
    - Run experiments with proper resource management
    - Handle early rejection of unpromising approaches
    - Support LLM-as-judge evaluation
    - Manage multi-stage evaluation pipeline
    """
    
    def __init__(self, max_runtime_seconds: float = 300.0):
        self.max_runtime = max_runtime_seconds
        self.experiments_run = 0
        self.early_rejections = 0
        
    async def execute_experiment(
        self,
        node: ExperimentNode,
        evaluation_config: Dict[str, Any]
    ) -> ExperimentNode:
        """
        Execute experiment with multi-stage evaluation.
        
        Stages:
        1. Exploration - Quick validation
        2. Verification - More thorough testing
        3. Validation - Final confirmation
        """
        node.status = ExperimentStatus.RUNNING
        
        try:
            # Stage 1: Exploration (quick)
            node.status = ExperimentStatus.EXPLORATION
            exploration_results = await self._run_exploration(node, evaluation_config)
            
            # Early rejection check
            if not self._passes_early_rejection(exploration_results):
                node.status = ExperimentStatus.REJECTED
                node.results = exploration_results
                self.early_rejections += 1
                logger.info(f"Early rejection for node {node.id}")
                return node
            
            # Stage 2: Verification
            node.status = ExperimentStatus.VERIFICATION
            verification_results = await self._run_verification(node, evaluation_config, exploration_results)
            
            # Stage 3: Validation
            node.status = ExperimentStatus.VALIDATION
            validation_results = await self._run_validation(node, evaluation_config, verification_results)
            
            # Combine all results
            node.results = {
                'exploration': exploration_results,
                'verification': verification_results,
                'validation': validation_results,
                'final_score': validation_results.get('score', 0.0),
                'passed_all_stages': True
            }
            
            node.status = ExperimentStatus.COMPLETED
            node.completion_time = datetime.utcnow()
            self.experiments_run += 1
            
        except Exception as e:
            logger.error(f"Experiment failed for node {node.id}: {e}")
            node.status = ExperimentStatus.FAILED
            node.results = {'error': str(e)}
        
        return node
    
    async def _run_exploration(
        self,
        node: ExperimentNode,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Quick exploration stage"""
        # Simulate quick backtest
        await asyncio.sleep(0.1)  # Simulated work
        
        return {
            'stage': 'exploration',
            'sharpe_ratio': 0.5 + (hash(node.id) % 100) / 200,  # Simulated metric
            'max_drawdown': 0.05 + (hash(node.id) % 50) / 1000,
            'win_rate': 0.45 + (hash(node.id) % 20) / 100,
            'sample_size': 100,
            'runtime_ms': 100
        }
    
    def _passes_early_rejection(self, results: Dict[str, Any]) -> bool:
        """Check if results pass early rejection criteria"""
        # Reject if Sharpe is too low or drawdown too high
        if results.get('sharpe_ratio', 0) < 0.3:
            return False
        if results.get('max_drawdown', 1.0) > 0.15:
            return False
        if results.get('win_rate', 0) < 0.4:
            return False
        return True
    
    async def _run_verification(
        self,
        node: ExperimentNode,
        config: Dict[str, Any],
        exploration_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verification stage with more data"""
        await asyncio.sleep(0.2)  # Simulated work
        
        # Build on exploration results
        return {
            'stage': 'verification',
            'sharpe_ratio': exploration_results['sharpe_ratio'] * (0.9 + (hash(node.id) % 20) / 100),
            'max_drawdown': exploration_results['max_drawdown'] * (1.0 + (hash(node.id) % 20) / 100),
            'win_rate': exploration_results['win_rate'],
            'profit_factor': 1.2 + (hash(node.id) % 100) / 200,
            'sample_size': 500,
            'runtime_ms': 500
        }
    
    async def _run_validation(
        self,
        node: ExperimentNode,
        config: Dict[str, Any],
        verification_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Final validation stage"""
        await asyncio.sleep(0.3)  # Simulated work
        
        score = (
            verification_results['sharpe_ratio'] * 0.4 +
            (1 - verification_results['max_drawdown']) * 0.3 +
            verification_results['win_rate'] * 0.2 +
            (verification_results.get('profit_factor', 1.0) - 1) * 0.1
        )
        
        return {
            'stage': 'validation',
            'score': score,
            'sharpe_ratio': verification_results['sharpe_ratio'],
            'max_drawdown': verification_results['max_drawdown'],
            'win_rate': verification_results['win_rate'],
            'profit_factor': verification_results['profit_factor'],
            'sample_size': 1000,
            'runtime_ms': 1000,
            'passed': score > 0.5
        }


class AnalyzerAgent:
    """
    Analyzer Agent: Distills outputs into insights
    
    Responsibilities:
    - Analyze experiment results
    - Extract actionable insights
    - Identify success/failure patterns
    - Generate improvement recommendations
    """
    
    def __init__(self):
        self.analyses_performed = 0
        
    async def analyze_experiment(
        self,
        node: ExperimentNode,
        baseline_results: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Analyze experiment results and extract insights.
        
        Returns structured analysis with actionable recommendations.
        """
        results = node.results
        
        # Generate insights based on results
        insights = []
        recommendations = []
        key_metrics = {}
        
        if 'validation' in results:
            validation = results['validation']
            
            # Extract key metrics
            key_metrics = {
                'final_score': validation.get('score', 0.0),
                'sharpe_ratio': validation.get('sharpe_ratio', 0.0),
                'max_drawdown': validation.get('max_drawdown', 0.0),
                'win_rate': validation.get('win_rate', 0.0),
                'profit_factor': validation.get('profit_factor', 1.0)
            }
            
            # Generate insights
            if key_metrics['sharpe_ratio'] > 1.0:
                insights.append(f"Strong risk-adjusted returns (Sharpe: {key_metrics['sharpe_ratio']:.2f})")
            
            if key_metrics['max_drawdown'] < 0.05:
                insights.append("Excellent drawdown control")
            elif key_metrics['max_drawdown'] > 0.10:
                insights.append("High drawdown risk detected")
            
            if key_metrics['win_rate'] > 0.55:
                insights.append("Above-average win rate")
            
            # Compare to baseline if available
            if baseline_results:
                improvement = key_metrics['final_score'] - baseline_results.get('score', 0.5)
                key_metrics['improvement_over_baseline'] = improvement
                
                if improvement > 0.1:
                    insights.append(f"Significant improvement over baseline (+{improvement:.2f})")
                    recommendations.append("Promote to production after further validation")
                elif improvement > 0:
                    insights.append(f"Marginal improvement over baseline (+{improvement:.2f})")
                    recommendations.append("Consider for A/B testing")
                else:
                    insights.append(f"Underperforms baseline ({improvement:.2f})")
                    recommendations.append("Reject or iterate on approach")
            
            # Generate specific recommendations
            if key_metrics['max_drawdown'] > 0.08:
                recommendations.append("Add tighter stop-loss rules")
            
            if key_metrics['win_rate'] < 0.48:
                recommendations.append("Improve entry signal quality")
        
        # Calculate confidence based on sample size and consistency
        confidence = 0.5
        if 'validation' in results:
            sample_size = results['validation'].get('sample_size', 100)
            confidence = min(0.95, 0.5 + (sample_size / 2000))
        
        improvement_potential = self._estimate_improvement_potential(key_metrics)
        
        self.analyses_performed += 1
        
        return AnalysisResult(
            insights=insights,
            actionable_recommendations=recommendations,
            confidence=confidence,
            key_metrics=key_metrics,
            improvement_potential=improvement_potential
        )
    
    def _estimate_improvement_potential(self, metrics: Dict[str, float]) -> float:
        """Estimate potential for further improvement"""
        potential = 0.5  # Base potential
        
        # Higher potential if win rate is low (room for improvement)
        if metrics.get('win_rate', 0.5) < 0.5:
            potential += 0.2
        
        # Higher potential if drawdown is high (risk management can improve)
        if metrics.get('max_drawdown', 0.05) > 0.08:
            potential += 0.15
        
        # Lower potential if already excellent
        if metrics.get('sharpe_ratio', 0) > 1.5:
            potential -= 0.3
        
        return max(0.0, min(1.0, potential))


class CognitionStore:
    """
    Cognition Store: Semantic knowledge base
    
    Embedding-indexed storage for domain priors and learned knowledge.
    Supports semantic search and dynamic updates.
    """
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.entries: Dict[str, CognitionEntry] = {}
        self.index_by_type: Dict[str, Set[str]] = defaultdict(set)
        
        # Initialize with some domain knowledge
        self._initialize_domain_knowledge()
    
    def _initialize_domain_knowledge(self):
        """Seed with initial domain knowledge"""
        initial_knowledge = [
            {
                'content': 'Trend following strategies work best in high volatility regimes with clear directional movement',
                'type': 'strategy',
                'embedding': self._simple_embedding('trend volatility directional')
            },
            {
                'content': 'Mean reversion strategies perform well in low volatility, range-bound markets',
                'type': 'strategy',
                'embedding': self._simple_embedding('mean reversion low volatility range')
            },
            {
                'content': 'Risk management is more important than entry timing for long-term survival',
                'type': 'insight',
                'embedding': self._simple_embedding('risk management survival priority')
            },
            {
                'content': 'High frequency strategies require careful consideration of transaction costs',
                'type': 'insight',
                'embedding': self._simple_embedding('high frequency costs transaction')
            },
            {
                'content': 'Pattern: Breakout failures often occur when volume is below average',
                'type': 'pattern',
                'embedding': self._simple_embedding('breakout failure volume low')
            },
        ]
        
        for knowledge in initial_knowledge:
            entry = CognitionEntry(
                id=str(uuid.uuid4()),
                content=knowledge['content'],
                embedding=knowledge['embedding'],
                entry_type=knowledge['type']
            )
            self.add_entry(entry)
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Create simple hash-based embedding (replace with real embeddings in production)"""
        # Simple character-based hash embedding
        embedding = [0.0] * self.embedding_dim
        for i, char in enumerate(text):
            embedding[i % self.embedding_dim] += ord(char) / 255.0
        # Normalize
        magnitude = sum(x**2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        return embedding
    
    def add_entry(self, entry: CognitionEntry):
        """Add entry to cognition store"""
        self.entries[entry.id] = entry
        self.index_by_type[entry.entry_type].add(entry.id)
    
    def retrieve_similar(
        self,
        query: str,
        k: int = 5,
        entry_type: Optional[str] = None
    ) -> List[CognitionEntry]:
        """
        Retrieve k most similar entries to query.
        
        Uses cosine similarity on embeddings.
        """
        query_embedding = self._simple_embedding(query)
        
        # Get candidate set
        if entry_type:
            candidates = [self.entries[eid] for eid in self.index_by_type[entry_type]]
        else:
            candidates = list(self.entries.values())
        
        # Compute similarities
        def cosine_similarity(e1: List[float], e2: List[float]) -> float:
            dot = sum(a * b for a, b in zip(e1, e2))
            return dot  # Already normalized
        
        scored = [(entry, cosine_similarity(query_embedding, entry.embedding)) 
                  for entry in candidates]
        
        # Sort by similarity and return top k
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Update access counts
        for entry, _ in scored[:k]:
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
        
        return [entry for entry, _ in scored[:k]]
    
    def update_from_experiment(self, node: ExperimentNode, analysis: AnalysisResult):
        """Update cognition store with learnings from experiment"""
        # Add successful strategies
        if node.results.get('final_score', 0) > 0.7:
            entry = CognitionEntry(
                id=str(uuid.uuid4()),
                content=f"Successful strategy: {node.motivation.description}. "
                        f"Key insight: {analysis.insights[0] if analysis.insights else 'N/A'}",
                embedding=self._simple_embedding(node.motivation.description),
                entry_type='strategy',
                source_experiment=node.id
            )
            self.add_entry(entry)
        
        # Add failure patterns
        if node.results.get('final_score', 0) < 0.3:
            entry = CognitionEntry(
                id=str(uuid.uuid4()),
                content=f"Failure pattern: {node.motivation.description} underperformed. "
                        f"Recommendations: {analysis.actionable_recommendations[0] if analysis.actionable_recommendations else 'N/A'}",
                embedding=self._simple_embedding(node.motivation.description),
                entry_type='failure',
                source_experiment=node.id
            )
            self.add_entry(entry)
        
        # Add general insights
        for insight in analysis.insights:
            entry = CognitionEntry(
                id=str(uuid.uuid4()),
                content=insight,
                embedding=self._simple_embedding(insight),
                entry_type='insight',
                source_experiment=node.id
            )
            self.add_entry(entry)


class ResearchOrchestrator:
    """
    Master orchestrator for the four-agent research system.
    
    Coordinates Researcher, Engineer, Analyzer, and Cognition agents
    to conduct autonomous research on trading strategies.
    """
    
    def __init__(
        self,
        sampling_policy: SamplingPolicy = SamplingPolicy.UCB1,
        max_parallel_experiments: int = 4,
        exploration_constant: float = 1.414
    ):
        self.cognition = CognitionStore()
        self.researcher = ResearcherAgent(self.cognition)
        self.engineer = EngineerAgent()
        self.analyzer = AnalyzerAgent()
        
        self.sampling_policy = sampling_policy
        self.max_parallel = max_parallel_experiments
        self.exploration_constant = exploration_constant
        
        # Experiment database
        self.experiments: Dict[str, ExperimentNode] = {}
        self.motivations: Dict[str, ResearchMotivation] = {}
        
        # Statistics
        self.stats = {
            'experiments_created': 0,
            'experiments_completed': 0,
            'experiments_failed': 0,
            'best_score': 0.0,
            'knowledge_entries_added': 0
        }
    
    async def run_research_cycle(
        self,
        motivations: List[ResearchMotivation],
        evaluation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a complete research cycle.
        
        1. Generate strategies for each motivation
        2. Execute experiments in parallel
        3. Analyze results
        4. Update cognition store
        """
        evaluation_config = evaluation_config or {}
        
        results = {
            'cycle_start': datetime.utcnow().isoformat(),
            'motivations_processed': len(motivations),
            'experiments_created': [],
            'experiments_completed': [],
            'analyses': [],
            'knowledge_added': 0
        }
        
        # Store motivations
        for motivation in motivations:
            self.motivations[motivation.id] = motivation
        
        # Generate and queue experiments
        experiment_queue = []
        for motivation in motivations:
            strategies = await self.researcher.generate_strategy(
                motivation, {}, num_candidates=2
            )
            
            for strategy in strategies:
                node = ExperimentNode(
                    id=str(uuid.uuid4()),
                    motivation=motivation,
                    code=strategy
                )
                self.experiments[node.id] = node
                experiment_queue.append(node)
                results['experiments_created'].append(node.id)
                self.stats['experiments_created'] += 1
        
        # Execute experiments in parallel batches
        completed_nodes = await self._execute_parallel(experiment_queue, evaluation_config)
        
        # Analyze results
        for node in completed_nodes:
            if node.status == ExperimentStatus.COMPLETED:
                analysis = await self.analyzer.analyze_experiment(node)
                results['analyses'].append({
                    'experiment_id': node.id,
                    'insights': analysis.insights,
                    'recommendations': analysis.actionable_recommendations,
                    'confidence': analysis.confidence,
                    'key_metrics': analysis.key_metrics
                })
                
                # Update cognition
                self.cognition.update_from_experiment(node, analysis)
                results['knowledge_added'] += 1
                self.stats['knowledge_entries_added'] += 1
                
                self.stats['experiments_completed'] += 1
                self.stats['best_score'] = max(
                    self.stats['best_score'],
                    node.results.get('final_score', 0)
                )
            elif node.status == ExperimentStatus.FAILED:
                self.stats['experiments_failed'] += 1
            
            results['experiments_completed'].append({
                'id': node.id,
                'status': node.status.value,
                'score': node.results.get('final_score', 0)
            })
        
        results['cycle_end'] = datetime.utcnow().isoformat()
        results['best_score_this_cycle'] = max(
            (r['score'] for r in results['experiments_completed']),
            default=0
        )
        
        return results
    
    async def _execute_parallel(
        self,
        nodes: List[ExperimentNode],
        config: Dict[str, Any]
    ) -> List[ExperimentNode]:
        """Execute experiments in parallel with semaphore control"""
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def run_with_semaphore(node: ExperimentNode) -> ExperimentNode:
            async with semaphore:
                return await self.engineer.execute_experiment(node, config)
        
        tasks = [run_with_semaphore(node) for node in nodes]
        return await asyncio.gather(*tasks)
    
    def sample_next_experiment(self) -> Optional[ExperimentNode]:
        """Sample next experiment to run based on policy"""
        pending = [n for n in self.experiments.values() 
                   if n.status == ExperimentStatus.PENDING]
        
        if not pending:
            return None
        
        if self.sampling_policy == SamplingPolicy.RANDOM:
            import random
            return random.choice(pending)
        
        elif self.sampling_policy == SamplingPolicy.GREEDY:
            return max(pending, key=lambda n: n.score)
        
        elif self.sampling_policy == SamplingPolicy.UCB1:
            total_visits = sum(n.visits for n in self.experiments.values()) or 1
            
            def ucb_score(node: ExperimentNode) -> float:
                if node.visits == 0:
                    return float('inf')
                exploitation = node.score / node.visits
                exploration = self.exploration_constant * (
                    (2 * (total_visits ** 0.5)) / node.visits
                ) ** 0.5
                return exploitation + exploration
            
            return max(pending, key=ucb_score)
        
        else:  # MAP_ELITES or default
            return pending[0]
    
    def get_best_strategies(self, k: int = 5) -> List[Tuple[ExperimentNode, float]]:
        """Get top k strategies by score"""
        completed = [
            (n, n.results.get('final_score', 0))
            for n in self.experiments.values()
            if n.status == ExperimentStatus.COMPLETED
        ]
        completed.sort(key=lambda x: x[1], reverse=True)
        return completed[:k]
    
    def generate_research_report(self) -> Dict[str, Any]:
        """Generate comprehensive research report"""
        best = self.get_best_strategies(k=3)
        
        return {
            'stats': self.stats,
            'total_experiments': len(self.experiments),
            'total_motivations': len(self.motivations),
            'cognition_entries': len(self.cognition.entries),
            'best_strategies': [
                {
                    'id': node.id,
                    'score': score,
                    'motivation': node.motivation.description,
                    'sharpe': node.results.get('sharpe_ratio', 0)
                }
                for node, score in best
            ],
            'knowledge_summary': {
                'strategies': len(self.cognition.index_by_type['strategy']),
                'insights': len(self.cognition.index_by_type['insight']),
                'patterns': len(self.cognition.index_by_type['pattern']),
                'failures': len(self.cognition.index_by_type['failure'])
            }
        }


def create_research_orchestrator(
    sampling_policy: str = "ucb1",
    max_parallel: int = 4
) -> ResearchOrchestrator:
    """Factory function to create research orchestrator"""
    policy = SamplingPolicy(sampling_policy)
    return ResearchOrchestrator(
        sampling_policy=policy,
        max_parallel_experiments=max_parallel
    )
