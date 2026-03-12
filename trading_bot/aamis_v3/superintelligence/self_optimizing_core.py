"""
Self-Optimizing Intelligence Core (VISTA-Inspired)
Autonomous self-improvement system that learns from everything
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import hashlib
import json
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class LearningSource(Enum):
    """Sources of learning"""
    SELF_EXPERIENCE = "self_experience"
    OTHER_TRADERS = "other_traders"
    BOOKS_KNOWLEDGE = "books_knowledge"
    REAL_TIME_DATA = "real_time_data"
    NATURE_BIO = "nature_bio"
    MARKET_PUNISHMENT = "market_punishment"
    MARKET_REWARD = "market_reward"
    FAILURE_MODE = "failure_mode"
    SIMULATION = "simulation"
    RED_TEAM = "red_team"


class OptimizationObjective(Enum):
    """What to optimize for"""
    PROFIT = "profit"
    STABILITY = "stability"
    SMOOTH_EQUITY = "smooth_equity"
    LOW_DRAWDOWN = "low_drawdown"
    MIN_EXPOSURE = "min_exposure"
    MAX_SHARPE = "max_sharpe"
    MIN_STRESS = "min_stress"
    SURVIVABILITY = "survivability"


@dataclass
class LearningExperience:
    """A single learning experience"""
    experience_id: str
    source: LearningSource
    timestamp: datetime
    
    # What happened
    context: Dict[str, Any]
    action_taken: str
    outcome: float  # PnL or score
    
    # Analysis
    what_worked: List[str]
    what_failed: List[str]
    market_condition: str
    
    # Lessons
    lessons_learned: List[str]
    rules_extracted: List[str]
    patterns_discovered: List[str]
    
    # Metadata
    confidence: float
    importance: float
    replay_count: int = 0
    last_replayed: Optional[datetime] = None


@dataclass
class KnowledgeAtom:
    """Atomic unit of knowledge"""
    atom_id: str
    knowledge_type: str  # rule, pattern, correlation, strategy
    content: str
    
    # Validation
    times_validated: int = 0
    times_invalidated: int = 0
    confidence_score: float = 0.5
    
    # Context
    applicable_regimes: List[str] = field(default_factory=list)
    applicable_assets: List[str] = field(default_factory=list)
    
    # Lifecycle
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0


@dataclass
class Hypothesis:
    """A testable hypothesis"""
    hypothesis_id: str
    statement: str
    
    # Testing
    test_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    # Evidence
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    
    # Status
    status: str = "testing"  # testing, validated, invalidated, uncertain
    confidence: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StrategyGene:
    """DNA of a trading strategy"""
    gene_id: str
    gene_type: str  # entry, exit, filter, sizing, timing
    code: str
    
    # Performance
    fitness_score: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    
    # Evolution
    generation: int = 0
    parent_genes: List[str] = field(default_factory=list)
    mutation_count: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)


class SelfOptimizingCore:
    """
    Self-optimizing intelligence core inspired by VISTA and Q*
    Learns from everything and continuously improves
    """
    
    def __init__(self, max_memory_size: int = 100000):
        # Long-term memory (persistent knowledge)
        try:
            self.long_term_memory: Dict[str, KnowledgeAtom] = {}
        
            # Short-term memory (recent experiences)
            self.short_term_memory: deque = deque(maxlen=1000)
        
            # Experience database
            self.experiences: Dict[str, LearningExperience] = {}
        
            # Hypothesis testing
            self.active_hypotheses: Dict[str, Hypothesis] = {}
            self.validated_hypotheses: Dict[str, Hypothesis] = {}
        
            # Strategy evolution
            self.strategy_genes: Dict[str, StrategyGene] = {}
            self.active_strategies: List[str] = []
        
            # Learning metrics
            self.learning_curve: List[Dict[str, float]] = []
            self.intelligence_score: float = 0.0
        
            # Optimization objectives
            self.objectives: Dict[OptimizationObjective, float] = {
                obj: 1.0 for obj in OptimizationObjective
            }
        
            # Knowledge graph
            self.knowledge_connections: Dict[str, Set[str]] = defaultdict(set)
        
            # Self-improvement tracking
            self.daily_improvements: List[Dict[str, Any]] = []
        
            logger.info("Self-Optimizing Core initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def learn_from_experience(self, experience: LearningExperience) -> Dict[str, Any]:
        """
        Learn from a single experience
        """
        
        # Store experience
        try:
            self.experiences[experience.experience_id] = experience
            self.short_term_memory.append(experience.experience_id)
        
            # Extract knowledge
            knowledge_extracted = []
        
            # Extract rules
            for rule in experience.rules_extracted:
                atom = self._create_knowledge_atom(
                    knowledge_type="rule",
                    content=rule,
                    source=experience.source
                )
                knowledge_extracted.append(atom.atom_id)
        
            # Extract patterns
            for pattern in experience.patterns_discovered:
                atom = self._create_knowledge_atom(
                    knowledge_type="pattern",
                    content=pattern,
                    source=experience.source
                )
                knowledge_extracted.append(atom.atom_id)
        
            # Update intelligence score
            self._update_intelligence_score(experience)
        
            logger.info(f"Learned from experience {experience.experience_id}: "
                       f"{len(knowledge_extracted)} knowledge atoms extracted")
        
            return {
                'experience_id': experience.experience_id,
                'knowledge_extracted': len(knowledge_extracted),
                'lessons_learned': len(experience.lessons_learned),
                'intelligence_score': self.intelligence_score
            }
        except Exception as e:
            logger.error(f"Error in learn_from_experience: {e}")
            raise
    
    def learn_from_other_traders(self, trader_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Imitation + Comparative Learning
        Learn from observing other traders
        """
        
        try:
            insights = []
        
            for action in trader_actions:
                # Analyze trader behavior
                trader_id = action.get('trader_id', 'unknown')
                trader_pnl = action.get('pnl', 0)
            
                if trader_pnl > 0:
                    # Learn from successful traders
                    insight = f"Trader {trader_id} succeeded with: {action.get('strategy', 'unknown')}"
                    insights.append(insight)
                
                    # Create knowledge atom
                    atom = self._create_knowledge_atom(
                        knowledge_type="strategy",
                        content=json.dumps(action),
                        source=LearningSource.OTHER_TRADERS
                    )
                
                    # Create hypothesis to test
                    hypothesis = Hypothesis(
                        hypothesis_id=self._generate_id("hyp"),
                        statement=f"Strategy from trader {trader_id} is profitable in {action.get('regime', 'unknown')} regime"
                    )
                    self.active_hypotheses[hypothesis.hypothesis_id] = hypothesis
        
            logger.info(f"Learned from {len(trader_actions)} other traders: {len(insights)} insights")
        
            return {
                'traders_analyzed': len(trader_actions),
                'insights_gained': len(insights),
                'hypotheses_created': len([h for h in self.active_hypotheses.values() if h.created_at > datetime.now() - timedelta(seconds=1)])
            }
        except Exception as e:
            logger.error(f"Error in learn_from_other_traders: {e}")
            raise
    
    def learn_from_books(self, book_content: str, book_title: str) -> Dict[str, Any]:
        """
        Learn from books and written knowledge
        Extract trading rules and convert to testable strategies
        """
        
        # Simulate knowledge extraction (in production, use NLP)
        try:
            rules_extracted = []
        
            # Example: Extract common trading wisdom
            common_rules = [
                "Cut losses short, let winners run",
                "Trade with the trend",
                "Don't fight the Fed",
                "Buy fear, sell greed",
                "Volume confirms price action"
            ]
        
            for rule in common_rules:
                if rule.lower() in book_content.lower():
                    # Create knowledge atom
                    atom = self._create_knowledge_atom(
                        knowledge_type="rule",
                        content=f"{book_title}: {rule}",
                        source=LearningSource.BOOKS_KNOWLEDGE
                    )
                    rules_extracted.append(atom.atom_id)
                
                    # Create testable hypothesis
                    hypothesis = Hypothesis(
                        hypothesis_id=self._generate_id("hyp"),
                        statement=f"Rule '{rule}' improves trading performance"
                    )
                    self.active_hypotheses[hypothesis.hypothesis_id] = hypothesis
        
            logger.info(f"Learned from book '{book_title}': {len(rules_extracted)} rules extracted")
        
            return {
                'book_title': book_title,
                'rules_extracted': len(rules_extracted),
                'hypotheses_created': len(rules_extracted)
            }
        except Exception as e:
            logger.error(f"Error in learn_from_books: {e}")
            raise
    
    def learn_from_nature(self, bio_system: str) -> Dict[str, Any]:
        """
        Learn from biological systems (ant colonies, neural networks, etc.)
        """
        
        try:
            bio_strategies = {
                'ant_colony': {
                    'principle': 'Pheromone-based pathfinding',
                    'trading_analog': 'Follow strong momentum trails, reinforce winning paths',
                    'implementation': 'Weight recent winners higher, create positive feedback loops'
                },
                'immune_system': {
                    'principle': 'Adaptive defense against threats',
                    'trading_analog': 'Detect and defend against market manipulation',
                    'implementation': 'Pattern recognition for spoofing, layering, wash trading'
                },
                'neural_plasticity': {
                    'principle': 'Strengthen useful connections, prune weak ones',
                    'trading_analog': 'Reinforce profitable strategies, eliminate losers',
                    'implementation': 'Genetic algorithm with fitness-based selection'
                },
                'swarm_intelligence': {
                    'principle': 'Collective decision-making',
                    'trading_analog': 'Multi-agent consensus',
                    'implementation': 'Ensemble of specialized agents voting on decisions'
                }
            }
        
            if bio_system in bio_strategies:
                strategy = bio_strategies[bio_system]
            
                # Create knowledge atom
                atom = self._create_knowledge_atom(
                    knowledge_type="strategy",
                    content=json.dumps(strategy),
                    source=LearningSource.NATURE_BIO
                )
            
                logger.info(f"Learned from {bio_system}: {strategy['principle']}")
            
                return {
                    'bio_system': bio_system,
                    'principle': strategy['principle'],
                    'trading_analog': strategy['trading_analog'],
                    'atom_id': atom.atom_id
                }
        
            return {'error': f'Unknown bio system: {bio_system}'}
        except Exception as e:
            logger.error(f"Error in learn_from_nature: {e}")
            raise
    
    def form_hypothesis(self, statement: str) -> Hypothesis:
        """
        Form a new hypothesis to test
        """
        
        try:
            hypothesis = Hypothesis(
                hypothesis_id=self._generate_id("hyp"),
                statement=statement
            )
        
            self.active_hypotheses[hypothesis.hypothesis_id] = hypothesis
        
            logger.info(f"Formed hypothesis: {statement}")
        
            return hypothesis
        except Exception as e:
            logger.error(f"Error in form_hypothesis: {e}")
            raise
    
    def test_hypothesis(self, hypothesis_id: str, test_result: bool, 
                       evidence: str) -> Dict[str, Any]:
        """
        Test a hypothesis and update its status
        """
        
        try:
            if hypothesis_id not in self.active_hypotheses:
                return {'error': 'Hypothesis not found'}
        
            hypothesis = self.active_hypotheses[hypothesis_id]
            hypothesis.test_count += 1
        
            if test_result:
                hypothesis.success_count += 1
                hypothesis.supporting_evidence.append(evidence)
            else:
                hypothesis.failure_count += 1
                hypothesis.contradicting_evidence.append(evidence)
        
            # Update confidence
            if hypothesis.test_count > 0:
                hypothesis.confidence = hypothesis.success_count / hypothesis.test_count
        
            # Update status
            if hypothesis.test_count >= 10:
                if hypothesis.confidence >= 0.7:
                    hypothesis.status = "validated"
                    self.validated_hypotheses[hypothesis_id] = hypothesis
                
                    # Convert to knowledge
                    atom = self._create_knowledge_atom(
                        knowledge_type="validated_hypothesis",
                        content=hypothesis.statement,
                        source=LearningSource.SELF_EXPERIENCE
                    )
                    atom.confidence_score = hypothesis.confidence
                
                elif hypothesis.confidence <= 0.3:
                    hypothesis.status = "invalidated"
                else:
                    hypothesis.status = "uncertain"
        
            logger.info(f"Tested hypothesis {hypothesis_id}: "
                       f"confidence={hypothesis.confidence:.2f}, status={hypothesis.status}")
        
            return {
                'hypothesis_id': hypothesis_id,
                'test_count': hypothesis.test_count,
                'confidence': hypothesis.confidence,
                'status': hypothesis.status
            }
        except Exception as e:
            logger.error(f"Error in test_hypothesis: {e}")
            raise
    
    def replay_experiences(self, timeframe: str = "3_months") -> Dict[str, Any]:
        """
        Replay past experiences to re-learn
        What markets punished, what markets rewarded
        """
        
        # Define timeframe
        try:
            timeframes = {
                "1_week": timedelta(days=7),
                "1_month": timedelta(days=30),
                "3_months": timedelta(days=90),
                "6_months": timedelta(days=180),
                "1_year": timedelta(days=365),
                "5_years": timedelta(days=1825)
            }
        
            if timeframe not in timeframes:
                timeframe = "3_months"
        
            cutoff_date = datetime.now() - timeframes[timeframe]
        
            # Filter experiences
            relevant_experiences = [
                exp for exp in self.experiences.values()
                if exp.timestamp >= cutoff_date
            ]
        
            # Analyze what worked and what didn't
            punishments = []
            rewards = []
        
            for exp in relevant_experiences:
                if exp.outcome < 0:
                    punishments.extend(exp.what_failed)
                else:
                    rewards.extend(exp.what_worked)
            
                # Update replay count
                exp.replay_count += 1
                exp.last_replayed = datetime.now()
        
            # Extract patterns
            punishment_patterns = self._extract_patterns(punishments)
            reward_patterns = self._extract_patterns(rewards)
        
            # Update knowledge base
            for pattern in punishment_patterns:
                atom = self._create_knowledge_atom(
                    knowledge_type="pattern",
                    content=f"AVOID: {pattern}",
                    source=LearningSource.MARKET_PUNISHMENT
                )
        
            for pattern in reward_patterns:
                atom = self._create_knowledge_atom(
                    knowledge_type="pattern",
                    content=f"SEEK: {pattern}",
                    source=LearningSource.MARKET_REWARD
                )
        
            logger.info(f"Replayed {len(relevant_experiences)} experiences from {timeframe}: "
                       f"{len(punishment_patterns)} punishments, {len(reward_patterns)} rewards")
        
            return {
                'timeframe': timeframe,
                'experiences_replayed': len(relevant_experiences),
                'punishments_identified': len(punishment_patterns),
                'rewards_identified': len(reward_patterns)
            }
        except Exception as e:
            logger.error(f"Error in replay_experiences: {e}")
            raise
    
    def daily_improvement_cycle(self) -> Dict[str, Any]:
        """
        Daily self-improvement cycle
        Learn something new, improve strategies, add rules, remove weak logic
        """
        
        try:
            improvements = {
                'timestamp': datetime.now(),
                'actions': []
            }
        
            # 1. Review recent performance
            recent_experiences = list(self.short_term_memory)[-100:]
        
            # 2. Identify weak knowledge
            weak_atoms = [
                atom for atom in self.long_term_memory.values()
                if atom.times_invalidated > atom.times_validated
            ]
        
            # Remove weak knowledge
            for atom in weak_atoms[:10]:  # Remove up to 10 weak atoms
                del self.long_term_memory[atom.atom_id]
                improvements['actions'].append(f"Removed weak knowledge: {atom.content[:50]}")
        
            # 3. Promote strong hypotheses
            strong_hypotheses = [
                h for h in self.active_hypotheses.values()
                if h.confidence >= 0.7 and h.test_count >= 10
            ]
        
            for hyp in strong_hypotheses:
                atom = self._create_knowledge_atom(
                    knowledge_type="rule",
                    content=hyp.statement,
                    source=LearningSource.SELF_EXPERIENCE
                )
                atom.confidence_score = hyp.confidence
                improvements['actions'].append(f"Promoted hypothesis to rule: {hyp.statement[:50]}")
        
            # 4. Update intelligence score
            old_score = self.intelligence_score
            self.intelligence_score = self._calculate_intelligence_score()
            improvement = self.intelligence_score - old_score
        
            improvements['intelligence_improvement'] = improvement
            improvements['new_intelligence_score'] = self.intelligence_score
        
            # Store daily improvement
            self.daily_improvements.append(improvements)
        
            logger.info(f"Daily improvement cycle complete: "
                       f"{len(improvements['actions'])} actions, "
                       f"intelligence +{improvement:.4f}")
        
            return improvements
        except Exception as e:
            logger.error(f"Error in daily_improvement_cycle: {e}")
            raise
    
    def get_intelligence_metrics(self) -> Dict[str, Any]:
        """
        Get current intelligence metrics
        """
        
        return {
            'intelligence_score': self.intelligence_score,
            'long_term_knowledge': len(self.long_term_memory),
            'short_term_memory': len(self.short_term_memory),
            'total_experiences': len(self.experiences),
            'active_hypotheses': len(self.active_hypotheses),
            'validated_hypotheses': len(self.validated_hypotheses),
            'strategy_genes': len(self.strategy_genes),
            'daily_improvements': len(self.daily_improvements),
            'knowledge_by_type': self._count_knowledge_by_type(),
            'learning_curve': self.learning_curve[-30:] if self.learning_curve else []
        }
    
    def _create_knowledge_atom(self, knowledge_type: str, content: str,
                              source: LearningSource) -> KnowledgeAtom:
        """Create and store a knowledge atom"""
        
        try:
            atom = KnowledgeAtom(
                atom_id=self._generate_id("atom"),
                knowledge_type=knowledge_type,
                content=content
            )
        
            self.long_term_memory[atom.atom_id] = atom
        
            return atom
        except Exception as e:
            logger.error(f"Error in _create_knowledge_atom: {e}")
            raise
    
    def _update_intelligence_score(self, experience: LearningExperience):
        """Update intelligence score based on learning"""
        
        # Intelligence grows with:
        # - Number of validated knowledge atoms
        # - Diversity of learning sources
        # - Quality of lessons learned
        
        try:
            knowledge_factor = len(self.long_term_memory) / 10000
            experience_factor = len(self.experiences) / 1000
            hypothesis_factor = len(self.validated_hypotheses) / 100
        
            self.intelligence_score = (
                knowledge_factor * 0.4 +
                experience_factor * 0.3 +
                hypothesis_factor * 0.3
            )
        
            # Track learning curve
            self.learning_curve.append({
                'timestamp': datetime.now(),
                'intelligence_score': self.intelligence_score,
                'knowledge_count': len(self.long_term_memory)
            })
        except Exception as e:
            logger.error(f"Error in _update_intelligence_score: {e}")
            raise
    
    def _calculate_intelligence_score(self) -> float:
        """Calculate current intelligence score"""
        
        try:
            knowledge_factor = len(self.long_term_memory) / 10000
            experience_factor = len(self.experiences) / 1000
            hypothesis_factor = len(self.validated_hypotheses) / 100
        
            return min(1.0, knowledge_factor * 0.4 + experience_factor * 0.3 + hypothesis_factor * 0.3)
        except Exception as e:
            logger.error(f"Error in _calculate_intelligence_score: {e}")
            raise
    
    def _extract_patterns(self, items: List[str]) -> List[str]:
        """Extract patterns from list of items"""
        
        # Count frequency
        try:
            from collections import Counter
            counter = Counter(items)
        
            # Return most common patterns
            return [item for item, count in counter.most_common(10) if count >= 2]
        except Exception as e:
            logger.error(f"Error in _extract_patterns: {e}")
            raise
    
    def _count_knowledge_by_type(self) -> Dict[str, int]:
        """Count knowledge atoms by type"""
        
        try:
            counts = defaultdict(int)
            for atom in self.long_term_memory.values():
                counts[atom.knowledge_type] += 1
        
            return dict(counts)
        except Exception as e:
            logger.error(f"Error in _count_knowledge_by_type: {e}")
            raise
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        
        try:
            timestamp = datetime.now().isoformat()
            random_data = np.random.rand()
            hash_input = f"{prefix}_{timestamp}_{random_data}"
        
            return hashlib.md5(hash_input.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Error in _generate_id: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize
    core = SelfOptimizingCore()
    
    print("="*80)
    logger.info("SELF-OPTIMIZING INTELLIGENCE CORE")
    print("="*80)
    
    # 1. Learn from experience
    experience = LearningExperience(
        experience_id="exp_001",
        source=LearningSource.SELF_EXPERIENCE,
        timestamp=datetime.now(),
        context={'regime': 'trending', 'volatility': 0.02},
        action_taken="BUY",
        outcome=150.0,
        what_worked=["Trend following", "Volume confirmation"],
        what_failed=[],
        market_condition="bullish",
        lessons_learned=["Buy strength in uptrends"],
        rules_extracted=["Enter on pullbacks in strong trends"],
        patterns_discovered=["Higher highs + volume = continuation"],
        confidence=0.8,
        importance=0.9
    )
    
    result = core.learn_from_experience(experience)
    logger.info(f"\n1. Learned from experience: {result}")
    
    # 2. Learn from other traders
    trader_actions = [
        {'trader_id': 'T001', 'strategy': 'momentum', 'pnl': 200, 'regime': 'trending'},
        {'trader_id': 'T002', 'strategy': 'mean_reversion', 'pnl': -50, 'regime': 'ranging'}
    ]
    
    result = core.learn_from_other_traders(trader_actions)
    logger.info(f"\n2. Learned from other traders: {result}")
    
    # 3. Learn from books
    book_content = "The key to successful trading is to cut losses short and let winners run. Always trade with the trend."
    result = core.learn_from_books(book_content, "Trading Wisdom")
    logger.info(f"\n3. Learned from books: {result}")
    
    # 4. Learn from nature
    result = core.learn_from_nature('ant_colony')
    logger.info(f"\n4. Learned from nature: {result}")
    
    # 5. Form and test hypothesis
    hypothesis = core.form_hypothesis("High volume breakouts are more reliable than low volume breakouts")
    logger.info(f"\n5. Formed hypothesis: {hypothesis.statement}")
    
    # Test it multiple times
    for i in range(15):
        test_result = np.random.rand() > 0.3  # 70% success rate
        core.test_hypothesis(hypothesis.hypothesis_id, test_result, f"Test {i+1}")
    
    logger.info(f"   Hypothesis status: {hypothesis.status}, confidence: {hypothesis.confidence:.2f}")
    
    # 6. Daily improvement
    improvements = core.daily_improvement_cycle()
    logger.info(f"\n6. Daily improvements: {len(improvements['actions'])} actions")
    
    # 7. Get metrics
    metrics = core.get_intelligence_metrics()
    logger.info(f"\n7. Intelligence Metrics:")
    logger.info(f"   Intelligence Score: {metrics['intelligence_score']:.4f}")
    logger.info(f"   Long-term Knowledge: {metrics['long_term_knowledge']}")
    logger.info(f"   Validated Hypotheses: {metrics['validated_hypotheses']}")
    
    print("\n" + "="*80)
    logger.info("SELF-OPTIMIZATION COMPLETE")
    print("="*80)
