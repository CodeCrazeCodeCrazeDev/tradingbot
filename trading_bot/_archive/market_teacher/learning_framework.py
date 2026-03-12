"""
Core Learning Framework
========================
Continuous reinforcement learning architecture where the market teaches through feedback.

Components:
- ContinuousLearner: Never-stopping learning cycle
- MultiArmedBandit: Strategy selection with exploration/exploitation
- ThompsonSampler: Bayesian strategy selection
- MetaLearner: Learning how to learn
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging
import random
import math

logger = logging.getLogger(__name__)


class LearningPhase(Enum):
    """Current phase in the learning lifecycle"""
    OBSERVE = "observe"
    HYPOTHESIZE = "hypothesize"
    ACT = "act"
    RECEIVE_FEEDBACK = "receive_feedback"
    LEARN = "learn"
    ADAPT = "adapt"


@dataclass
class LearningCycle:
    """Represents one complete learning cycle"""
    cycle_id: str
    phase: LearningPhase
    observation: Dict[str, Any] = field(default_factory=dict)
    hypothesis: Dict[str, Any] = field(default_factory=dict)
    action: Dict[str, Any] = field(default_factory=dict)
    feedback: Dict[str, Any] = field(default_factory=dict)
    lesson_learned: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'cycle_id': self.cycle_id,
            'phase': self.phase.value,
            'observation': self.observation,
            'hypothesis': self.hypothesis,
            'action': self.action,
            'feedback': self.feedback,
            'lesson_learned': self.lesson_learned,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ExplorationExploitation:
    """Manages exploration vs exploitation balance"""
    initial_exploration_rate: float = 0.9
    min_exploration_rate: float = 0.1
    decay_rate: float = 0.995
    current_rate: float = 0.9
    total_actions: int = 0
    exploration_actions: int = 0
    exploitation_actions: int = 0
    
    def get_exploration_rate(self) -> float:
        """Get current exploration rate with decay"""
        self.current_rate = max(
            self.min_exploration_rate,
            self.initial_exploration_rate * (self.decay_rate ** self.total_actions)
        )
        return self.current_rate
    
    def should_explore(self) -> bool:
        """Decide whether to explore or exploit"""
        self.total_actions += 1
        explore = random.random() < self.get_exploration_rate()
        
        if explore:
            self.exploration_actions += 1
        else:
            self.exploitation_actions += 1
            
        return explore
    
    def get_stats(self) -> Dict:
        return {
            'current_rate': self.current_rate,
            'total_actions': self.total_actions,
            'exploration_ratio': self.exploration_actions / max(1, self.total_actions),
            'exploitation_ratio': self.exploitation_actions / max(1, self.total_actions)
        }


class ContinuousLearner:
    """
    Perpetual learning system that never stops learning from market feedback.
    
    The market is the teacher:
    - Price movements are lessons
    - Profits and losses are grades
    - Adaptation is the goal
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Learning state
        self.current_cycle: Optional[LearningCycle] = None
        self.cycle_history: deque = deque(maxlen=10000)
        self.total_cycles: int = 0
        
        # Exploration/Exploitation
        self.exploration = ExplorationExploitation(
            initial_exploration_rate=self.config.get('initial_exploration', 0.9),
            min_exploration_rate=self.config.get('min_exploration', 0.1),
            decay_rate=self.config.get('decay_rate', 0.995)
        )
        
        # Learning metrics
        self.lessons_learned: List[Dict] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.belief_updates: int = 0
        
        # Performance tracking
        self.cumulative_reward: float = 0.0
        self.reward_history: deque = deque(maxlen=1000)
        
        logger.info("ContinuousLearner initialized - Ready to learn from market")
    
    def observe(self, market_state: Dict) -> Dict:
        """
        Step 1: OBSERVE the market state
        
        The market presents itself. We observe without judgment.
        """
        self.current_cycle = LearningCycle(
            cycle_id=f"cycle_{self.total_cycles}",
            phase=LearningPhase.OBSERVE,
            observation=market_state
        )
        
        observation = {
            'prices': market_state.get('prices', {}),
            'volumes': market_state.get('volumes', {}),
            'volatility': market_state.get('volatility', {}),
            'order_book': market_state.get('order_book', {}),
            'correlations': market_state.get('correlations', {}),
            'regime': self._detect_regime(market_state),
            'timestamp': datetime.now()
        }
        
        self.current_cycle.observation = observation
        logger.debug(f"Observed market state: regime={observation['regime']}")
        
        return observation
    
    def hypothesize(self, observation: Dict) -> List[Dict]:
        """
        Step 2: HYPOTHESIZE potential actions
        
        Generate multiple trading hypotheses based on observation.
        Each hypothesis is a prediction about what the market will do.
        """
        self.current_cycle.phase = LearningPhase.HYPOTHESIZE
        
        hypotheses = []
        
        # Generate hypotheses from different perspectives
        perspectives = [
            self._momentum_hypothesis,
            self._mean_reversion_hypothesis,
            self._volatility_hypothesis,
            self._trend_hypothesis,
            self._contrarian_hypothesis
        ]
        
        for perspective_fn in perspectives:
            try:
                hypothesis = perspective_fn(observation)
                if hypothesis:
                    hypotheses.append(hypothesis)
            except Exception as e:
                logger.warning(f"Hypothesis generation failed: {e}")
        
        # Calculate confidence for each hypothesis
        for h in hypotheses:
            h['confidence'] = self._calculate_confidence(h, observation)
        
        # Sort by confidence
        hypotheses.sort(key=lambda x: x['confidence'], reverse=True)
        
        self.current_cycle.hypothesis = {
            'count': len(hypotheses),
            'top_hypothesis': hypotheses[0] if hypotheses else None,
            'all_hypotheses': hypotheses
        }
        
        return hypotheses
    
    def act(self, hypotheses: List[Dict]) -> Dict:
        """
        Step 3: ACT based on best hypothesis
        
        Execute trade based on selected hypothesis.
        Use exploration/exploitation to balance learning vs earning.
        """
        self.current_cycle.phase = LearningPhase.ACT
        
        if not hypotheses:
            action = {'type': 'WAIT', 'reason': 'No valid hypotheses'}
            self.current_cycle.action = action
            return action
        
        # Exploration vs Exploitation decision
        if self.exploration.should_explore():
            # EXPLORE: Try random or underused hypothesis
            selected = random.choice(hypotheses)
            action_type = 'EXPLORATION'
            logger.info(f"EXPLORATION MODE: Testing {selected.get('strategy', 'unknown')}")
        else:
            # EXPLOIT: Use highest confidence hypothesis
            selected = hypotheses[0]
            action_type = 'EXPLOITATION'
            logger.info(f"EXPLOITATION MODE: Using proven {selected.get('strategy', 'unknown')}")
        
        action = {
            'type': action_type,
            'hypothesis': selected,
            'direction': selected.get('direction', 'NEUTRAL'),
            'size': self._calculate_position_size(selected),
            'entry_price': selected.get('entry_price'),
            'stop_loss': selected.get('stop_loss'),
            'take_profit': selected.get('take_profit'),
            'confidence': selected.get('confidence', 0.5),
            'timestamp': datetime.now()
        }
        
        self.current_cycle.action = action
        return action
    
    def receive_feedback(self, action: Dict, outcome: Dict) -> Dict:
        """
        Step 4: RECEIVE market feedback (The Teaching Moment)
        
        The market grades our hypothesis:
        - Profit = Correct hypothesis
        - Loss = Incorrect hypothesis
        - The size of P&L indicates confidence in the lesson
        """
        self.current_cycle.phase = LearningPhase.RECEIVE_FEEDBACK
        
        feedback = {
            'pnl': outcome.get('pnl', 0),
            'pnl_percentage': outcome.get('pnl_percentage', 0),
            'execution_quality': self._assess_execution_quality(action, outcome),
            'price_path': outcome.get('price_path', []),
            'volatility_realized': outcome.get('volatility_realized', 0),
            'duration': outcome.get('duration', 0),
            'market_reaction': self._classify_market_reaction(action, outcome),
            'timestamp': datetime.now()
        }
        
        # Update cumulative metrics
        self.cumulative_reward += feedback['pnl']
        self.reward_history.append(feedback['pnl'])
        
        self.current_cycle.feedback = feedback
        
        # Log the teaching moment
        if feedback['pnl'] > 0:
            logger.info(f"✓ Market REWARDED us: +{feedback['pnl']:.2f} ({feedback['pnl_percentage']:.2%})")
        else:
            logger.info(f"✗ Market TAUGHT us: {feedback['pnl']:.2f} ({feedback['pnl_percentage']:.2%})")
        
        return feedback
    
    def learn(self, feedback: Dict) -> Dict:
        """
        Step 5: LEARN from the feedback
        
        Update beliefs, adjust strategies, refine models.
        This is where the market's lesson is internalized.
        """
        self.current_cycle.phase = LearningPhase.LEARN
        
        lesson = {
            'cycle_id': self.current_cycle.cycle_id,
            'hypothesis_tested': self.current_cycle.hypothesis.get('top_hypothesis', {}),
            'action_taken': self.current_cycle.action,
            'market_feedback': feedback,
            'lesson_type': self._classify_lesson_type(feedback),
            'confidence_adjustment': 0.0,
            'knowledge_update': {},
            'timestamp': datetime.now()
        }
        
        # Determine what we learned
        if feedback['pnl'] > 0:
            # Positive reinforcement
            lesson['lesson_type'] = 'REINFORCEMENT'
            lesson['confidence_adjustment'] = min(0.1, feedback['pnl_percentage'])
            lesson['knowledge_update'] = {
                'action': 'STRENGTHEN',
                'strategy': self.current_cycle.action.get('hypothesis', {}).get('strategy'),
                'conditions': self.current_cycle.observation.get('regime')
            }
            self.current_cycle.lesson_learned = "Market validated our hypothesis. Reinforce this pattern."
            
        elif feedback['pnl'] < 0:
            # Negative reinforcement (learning from mistakes)
            lesson['lesson_type'] = 'CORRECTION'
            lesson['confidence_adjustment'] = max(-0.1, feedback['pnl_percentage'])
            lesson['knowledge_update'] = {
                'action': 'WEAKEN',
                'strategy': self.current_cycle.action.get('hypothesis', {}).get('strategy'),
                'conditions': self.current_cycle.observation.get('regime'),
                'what_went_wrong': self._analyze_failure(feedback)
            }
            self.current_cycle.lesson_learned = f"Market corrected us. Lesson: {lesson['knowledge_update']['what_went_wrong']}"
            
        else:
            # Neutral outcome
            lesson['lesson_type'] = 'NEUTRAL'
            lesson['knowledge_update'] = {'action': 'OBSERVE', 'note': 'Market was indifferent'}
            self.current_cycle.lesson_learned = "Market was neutral. Continue observing."
        
        # Update knowledge base
        self._update_knowledge_base(lesson)
        
        # Store lesson
        self.lessons_learned.append(lesson)
        self.belief_updates += 1
        
        logger.info(f"Lesson learned: {self.current_cycle.lesson_learned}")
        
        return lesson
    
    def complete_cycle(self) -> LearningCycle:
        """Complete the learning cycle and prepare for next iteration"""
        self.current_cycle.phase = LearningPhase.ADAPT
        self.cycle_history.append(self.current_cycle)
        self.total_cycles += 1
        
        completed_cycle = self.current_cycle
        self.current_cycle = None
        
        logger.debug(f"Completed learning cycle {completed_cycle.cycle_id}")
        
        return completed_cycle
    
    def _detect_regime(self, market_state: Dict) -> str:
        """Detect current market regime"""
        volatility = market_state.get('volatility', {}).get('current', 0.15)
        trend = market_state.get('trend', {}).get('strength', 0)
        
        if volatility > 0.25:
            return 'HIGH_VOLATILITY'
        elif abs(trend) > 0.7:
            return 'TRENDING'
        elif abs(trend) < 0.3:
            return 'RANGING'
        else:
            return 'TRANSITIONING'
    
    def _momentum_hypothesis(self, observation: Dict) -> Optional[Dict]:
        """Generate momentum-based hypothesis"""
        regime = observation.get('regime', '')
        if regime in ['TRENDING', 'HIGH_VOLATILITY']:
            return {
                'strategy': 'MOMENTUM',
                'direction': 'LONG' if observation.get('trend', {}).get('direction', 0) > 0 else 'SHORT',
                'rationale': 'Trend continuation expected',
                'timeframe': 'SHORT_TERM'
            }
        return None
    
    def _mean_reversion_hypothesis(self, observation: Dict) -> Optional[Dict]:
        """Generate mean reversion hypothesis"""
        regime = observation.get('regime', '')
        if regime == 'RANGING':
            return {
                'strategy': 'MEAN_REVERSION',
                'direction': 'LONG' if observation.get('price_position', 0.5) < 0.3 else 'SHORT',
                'rationale': 'Price expected to revert to mean',
                'timeframe': 'SHORT_TERM'
            }
        return None
    
    def _volatility_hypothesis(self, observation: Dict) -> Optional[Dict]:
        """Generate volatility-based hypothesis"""
        vol = observation.get('volatility', {}).get('current', 0.15)
        vol_percentile = observation.get('volatility', {}).get('percentile', 50)
        
        if vol_percentile > 80:
            return {
                'strategy': 'VOLATILITY_SELL',
                'direction': 'NEUTRAL',
                'rationale': 'High vol expected to mean revert',
                'timeframe': 'MEDIUM_TERM'
            }
        elif vol_percentile < 20:
            return {
                'strategy': 'VOLATILITY_BUY',
                'direction': 'NEUTRAL',
                'rationale': 'Low vol expected to expand',
                'timeframe': 'MEDIUM_TERM'
            }
        return None
    
    def _trend_hypothesis(self, observation: Dict) -> Optional[Dict]:
        """Generate trend-following hypothesis"""
        trend = observation.get('trend', {})
        if trend.get('strength', 0) > 0.5:
            return {
                'strategy': 'TREND_FOLLOW',
                'direction': 'LONG' if trend.get('direction', 0) > 0 else 'SHORT',
                'rationale': 'Strong trend detected',
                'timeframe': 'MEDIUM_TERM'
            }
        return None
    
    def _contrarian_hypothesis(self, observation: Dict) -> Optional[Dict]:
        """Generate contrarian hypothesis"""
        sentiment = observation.get('sentiment', {}).get('extreme', False)
        if sentiment:
            return {
                'strategy': 'CONTRARIAN',
                'direction': 'SHORT' if observation.get('sentiment', {}).get('bullish', False) else 'LONG',
                'rationale': 'Extreme sentiment suggests reversal',
                'timeframe': 'SHORT_TERM'
            }
        return None
    
    def _calculate_confidence(self, hypothesis: Dict, observation: Dict) -> float:
        """Calculate confidence in a hypothesis"""
        base_confidence = 0.5
        
        # Adjust based on regime fit
        strategy = hypothesis.get('strategy', '')
        regime = observation.get('regime', '')
        
        regime_fit = {
            ('MOMENTUM', 'TRENDING'): 0.2,
            ('MOMENTUM', 'HIGH_VOLATILITY'): 0.1,
            ('MEAN_REVERSION', 'RANGING'): 0.2,
            ('TREND_FOLLOW', 'TRENDING'): 0.25,
            ('CONTRARIAN', 'RANGING'): 0.1,
        }
        
        adjustment = regime_fit.get((strategy, regime), 0)
        
        # Adjust based on historical performance
        historical_performance = self.knowledge_base.get(f'{strategy}_{regime}', {})
        if historical_performance:
            win_rate = historical_performance.get('win_rate', 0.5)
            adjustment += (win_rate - 0.5) * 0.3
        
        return min(0.95, max(0.05, base_confidence + adjustment))
    
    def _calculate_position_size(self, hypothesis: Dict) -> float:
        """Calculate position size based on confidence"""
        confidence = hypothesis.get('confidence', 0.5)
        base_size = self.config.get('base_position_size', 0.01)
        
        # Scale by confidence
        size = base_size * (0.5 + confidence)
        
        # Cap at maximum
        max_size = self.config.get('max_position_size', 0.02)
        return min(size, max_size)
    
    def _assess_execution_quality(self, action: Dict, outcome: Dict) -> float:
        """Assess how well the trade was executed"""
        expected_entry = action.get('entry_price', 0)
        actual_entry = outcome.get('actual_entry', expected_entry)
        
        if expected_entry == 0:
            return 1.0
        
        slippage = abs(actual_entry - expected_entry) / expected_entry
        return max(0, 1 - slippage * 10)  # 10% slippage = 0 quality
    
    def _classify_market_reaction(self, action: Dict, outcome: Dict) -> str:
        """Classify how the market reacted to our trade"""
        pnl = outcome.get('pnl', 0)
        duration = outcome.get('duration', 0)
        
        if pnl > 0 and duration < 60:  # Quick profit
            return 'IMMEDIATE_VALIDATION'
        elif pnl > 0:
            return 'DELAYED_VALIDATION'
        elif pnl < 0 and duration < 60:  # Quick loss
            return 'IMMEDIATE_REJECTION'
        elif pnl < 0:
            return 'DELAYED_REJECTION'
        else:
            return 'NEUTRAL'
    
    def _classify_lesson_type(self, feedback: Dict) -> str:
        """Classify the type of lesson from market feedback"""
        pnl = feedback.get('pnl', 0)
        reaction = feedback.get('market_reaction', '')
        
        if 'IMMEDIATE' in reaction:
            return 'STRONG_SIGNAL'
        elif 'DELAYED' in reaction:
            return 'WEAK_SIGNAL'
        else:
            return 'AMBIGUOUS'
    
    def _analyze_failure(self, feedback: Dict) -> str:
        """Analyze why a trade failed"""
        reaction = feedback.get('market_reaction', '')
        execution = feedback.get('execution_quality', 1.0)
        
        if execution < 0.8:
            return "Poor execution - slippage too high"
        elif 'IMMEDIATE' in reaction:
            return "Wrong direction - hypothesis was incorrect"
        else:
            return "Timing issue - entry or exit was suboptimal"
    
    def _update_knowledge_base(self, lesson: Dict) -> None:
        """Update the knowledge base with new lesson"""
        strategy = lesson.get('knowledge_update', {}).get('strategy', 'UNKNOWN')
        conditions = lesson.get('knowledge_update', {}).get('conditions', 'UNKNOWN')
        key = f"{strategy}_{conditions}"
        
        if key not in self.knowledge_base:
            self.knowledge_base[key] = {
                'wins': 0,
                'losses': 0,
                'total_pnl': 0,
                'win_rate': 0.5,
                'avg_pnl': 0,
                'last_updated': datetime.now()
            }
        
        kb = self.knowledge_base[key]
        pnl = lesson.get('market_feedback', {}).get('pnl', 0)
        
        if pnl > 0:
            kb['wins'] += 1
        elif pnl < 0:
            kb['losses'] += 1
        
        kb['total_pnl'] += pnl
        total_trades = kb['wins'] + kb['losses']
        kb['win_rate'] = kb['wins'] / max(1, total_trades)
        kb['avg_pnl'] = kb['total_pnl'] / max(1, total_trades)
        kb['last_updated'] = datetime.now()
    
    def get_learning_stats(self) -> Dict:
        """Get comprehensive learning statistics"""
        return {
            'total_cycles': self.total_cycles,
            'lessons_learned': len(self.lessons_learned),
            'belief_updates': self.belief_updates,
            'cumulative_reward': self.cumulative_reward,
            'avg_reward': np.mean(list(self.reward_history)) if self.reward_history else 0,
            'exploration_stats': self.exploration.get_stats(),
            'knowledge_base_size': len(self.knowledge_base),
            'recent_performance': self._calculate_recent_performance()
        }
    
    def _calculate_recent_performance(self) -> Dict:
        """Calculate recent performance metrics"""
        if not self.reward_history:
            return {'sharpe': 0, 'win_rate': 0, 'avg_pnl': 0}
        
        rewards = list(self.reward_history)
        wins = sum(1 for r in rewards if r > 0)
        
        return {
            'sharpe': np.mean(rewards) / max(0.001, np.std(rewards)) * np.sqrt(252),
            'win_rate': wins / len(rewards),
            'avg_pnl': np.mean(rewards),
            'total_trades': len(rewards)
        }


class MultiArmedBandit:
    """
    Multi-Armed Bandit for strategy selection.
    
    Each "arm" is a strategy. The market teaches us which arms work
    through trial and feedback.
    """
    
    def __init__(self, strategies: List[str], config: Dict = None):
        self.config = config or {}
        self.strategies = strategies
        
        # Initialize arm statistics
        self.arm_stats = {
            strategy: {
                'pulls': 0,
                'total_reward': 0.0,
                'avg_reward': 0.0,
                'ucb_value': float('inf'),  # Upper Confidence Bound
                'last_pulled': None
            }
            for strategy in strategies
        }
        
        self.total_pulls = 0
        self.exploration_constant = self.config.get('exploration_constant', 2.0)
        
        logger.info(f"MultiArmedBandit initialized with {len(strategies)} arms")
    
    def select_arm(self, method: str = 'ucb') -> str:
        """
        Select which strategy (arm) to use.
        
        Methods:
        - 'ucb': Upper Confidence Bound (balances exploration/exploitation)
        - 'epsilon_greedy': Random exploration with probability epsilon
        - 'thompson': Thompson Sampling (Bayesian)
        """
        if method == 'ucb':
            return self._ucb_selection()
        elif method == 'epsilon_greedy':
            return self._epsilon_greedy_selection()
        elif method == 'thompson':
            return self._thompson_selection()
        else:
            return self._ucb_selection()
    
    def _ucb_selection(self) -> str:
        """Upper Confidence Bound selection"""
        # First, try each arm at least once
        for strategy in self.strategies:
            if self.arm_stats[strategy]['pulls'] == 0:
                return strategy
        
        # Calculate UCB values
        for strategy in self.strategies:
            stats = self.arm_stats[strategy]
            exploitation = stats['avg_reward']
            exploration = self.exploration_constant * math.sqrt(
                math.log(self.total_pulls) / stats['pulls']
            )
            stats['ucb_value'] = exploitation + exploration
        
        # Select arm with highest UCB
        best_arm = max(self.strategies, key=lambda s: self.arm_stats[s]['ucb_value'])
        return best_arm
    
    def _epsilon_greedy_selection(self) -> str:
        """Epsilon-greedy selection"""
        epsilon = self.config.get('epsilon', 0.1)
        
        if random.random() < epsilon:
            # Explore: random arm
            return random.choice(self.strategies)
        else:
            # Exploit: best arm
            return max(self.strategies, key=lambda s: self.arm_stats[s]['avg_reward'])
    
    def _thompson_selection(self) -> str:
        """Thompson Sampling selection"""
        samples = {}
        for strategy in self.strategies:
            stats = self.arm_stats[strategy]
            # Use Beta distribution for win/loss
            alpha = stats.get('wins', 1) + 1
            beta = stats.get('losses', 1) + 1
            samples[strategy] = np.random.beta(alpha, beta)
        
        return max(samples, key=samples.get)
    
    def update(self, strategy: str, reward: float) -> None:
        """
        Update arm statistics after receiving market feedback.
        
        This is where the market teaches us about the strategy.
        """
        stats = self.arm_stats[strategy]
        stats['pulls'] += 1
        stats['total_reward'] += reward
        stats['avg_reward'] = stats['total_reward'] / stats['pulls']
        stats['last_pulled'] = datetime.now()
        
        # Track wins/losses for Thompson sampling
        if reward > 0:
            stats['wins'] = stats.get('wins', 0) + 1
        else:
            stats['losses'] = stats.get('losses', 0) + 1
        
        self.total_pulls += 1
        
        logger.debug(f"Updated arm '{strategy}': avg_reward={stats['avg_reward']:.4f}, pulls={stats['pulls']}")
    
    def get_best_arm(self) -> Tuple[str, Dict]:
        """Get the current best performing arm"""
        best = max(self.strategies, key=lambda s: self.arm_stats[s]['avg_reward'])
        return best, self.arm_stats[best]
    
    def get_arm_rankings(self) -> List[Tuple[str, float]]:
        """Get all arms ranked by performance"""
        rankings = [(s, self.arm_stats[s]['avg_reward']) for s in self.strategies]
        return sorted(rankings, key=lambda x: x[1], reverse=True)


class ThompsonSampler:
    """
    Thompson Sampling for Bayesian strategy selection.
    
    Maintains probability distributions over strategy performance.
    The market updates our beliefs through observed outcomes.
    """
    
    def __init__(self, strategies: List[str]):
        self.strategies = strategies
        
        # Beta distribution parameters for each strategy
        # Beta(alpha, beta) where alpha = successes + 1, beta = failures + 1
        self.posteriors = {
            strategy: {'alpha': 1, 'beta': 1}
            for strategy in strategies
        }
        
        self.history = []
        
        logger.info(f"ThompsonSampler initialized with {len(strategies)} strategies")
    
    def sample(self) -> str:
        """
        Sample from posterior distributions and select best.
        
        This naturally balances exploration and exploitation.
        """
        samples = {}
        for strategy in self.strategies:
            params = self.posteriors[strategy]
            samples[strategy] = np.random.beta(params['alpha'], params['beta'])
        
        selected = max(samples, key=samples.get)
        
        logger.debug(f"Thompson sampled: {selected} (sample={samples[selected]:.4f})")
        
        return selected
    
    def update(self, strategy: str, success: bool) -> None:
        """
        Update posterior distribution based on market feedback.
        
        The market teaches us by updating our beliefs.
        """
        if success:
            self.posteriors[strategy]['alpha'] += 1
        else:
            self.posteriors[strategy]['beta'] += 1
        
        self.history.append({
            'strategy': strategy,
            'success': success,
            'timestamp': datetime.now()
        })
        
        # Log updated belief
        params = self.posteriors[strategy]
        expected = params['alpha'] / (params['alpha'] + params['beta'])
        logger.debug(f"Updated belief for '{strategy}': expected_success={expected:.4f}")
    
    def get_expected_values(self) -> Dict[str, float]:
        """Get expected success probability for each strategy"""
        return {
            strategy: params['alpha'] / (params['alpha'] + params['beta'])
            for strategy, params in self.posteriors.items()
        }
    
    def get_confidence_intervals(self, confidence: float = 0.95) -> Dict[str, Tuple[float, float]]:
        """Get confidence intervals for each strategy"""
        from scipy import stats as scipy_stats
        
        intervals = {}
        for strategy, params in self.posteriors.items():
            dist = scipy_stats.beta(params['alpha'], params['beta'])
            lower = dist.ppf((1 - confidence) / 2)
            upper = dist.ppf(1 - (1 - confidence) / 2)
            intervals[strategy] = (lower, upper)
        
        return intervals


class MetaLearner:
    """
    Meta-Learning: Learning how to learn.
    
    Don't just learn strategies, learn the learning process itself.
    Adapt the learning rate, exploration rate, and transfer knowledge.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Learning rate adaptation
        self.base_learning_rate = self.config.get('base_learning_rate', 0.01)
        self.current_learning_rate = self.base_learning_rate
        self.learning_rate_history = []
        
        # Exploration adaptation
        self.base_exploration_rate = self.config.get('base_exploration_rate', 0.2)
        self.current_exploration_rate = self.base_exploration_rate
        
        # Performance tracking for meta-learning
        self.performance_window = deque(maxlen=100)
        self.adaptation_history = []
        
        # Transfer learning
        self.regime_knowledge = {}  # Knowledge about different market regimes
        self.cross_regime_transfers = []
        
        logger.info("MetaLearner initialized - Learning how to learn")
    
    def adapt_learning_rate(self, market_conditions: Dict) -> float:
        """
        Adapt learning rate based on market conditions.
        
        In volatile markets, learn faster. In stable markets, learn slower.
        """
        volatility = market_conditions.get('volatility', 0.15)
        regime_stability = market_conditions.get('regime_stability', 0.5)
        
        # Higher volatility = faster learning
        vol_factor = 1 + (volatility - 0.15) * 2
        
        # Lower stability = faster learning (regime changing)
        stability_factor = 1 + (1 - regime_stability)
        
        self.current_learning_rate = self.base_learning_rate * vol_factor * stability_factor
        self.current_learning_rate = max(0.001, min(0.1, self.current_learning_rate))
        
        self.learning_rate_history.append({
            'rate': self.current_learning_rate,
            'volatility': volatility,
            'stability': regime_stability,
            'timestamp': datetime.now()
        })
        
        logger.debug(f"Adapted learning rate: {self.current_learning_rate:.4f}")
        
        return self.current_learning_rate
    
    def adapt_exploration_rate(self, recent_performance: Dict) -> float:
        """
        Adapt exploration rate based on recent performance.
        
        If performing well, exploit more. If struggling, explore more.
        """
        sharpe = recent_performance.get('sharpe', 0)
        win_rate = recent_performance.get('win_rate', 0.5)
        
        if sharpe > 2.0 and win_rate > 0.6:
            # Performing well - exploit more
            self.current_exploration_rate = max(0.05, self.current_exploration_rate * 0.9)
            logger.info("Good performance - reducing exploration")
        elif sharpe < 0.5 or win_rate < 0.4:
            # Struggling - explore more
            self.current_exploration_rate = min(0.5, self.current_exploration_rate * 1.2)
            logger.info("Poor performance - increasing exploration")
        
        return self.current_exploration_rate
    
    def transfer_knowledge(self, source_regime: str, target_regime: str) -> Dict:
        """
        Transfer learning from one market regime to another.
        
        Apply lessons learned in similar historical periods.
        """
        if source_regime not in self.regime_knowledge:
            return {}
        
        source_knowledge = self.regime_knowledge[source_regime]
        
        # Calculate similarity between regimes
        similarity = self._calculate_regime_similarity(source_regime, target_regime)
        
        if similarity < 0.3:
            logger.debug(f"Regimes too different for transfer: {similarity:.2f}")
            return {}
        
        # Transfer with decay based on similarity
        transferred = {}
        for key, value in source_knowledge.items():
            if isinstance(value, (int, float)):
                transferred[key] = value * similarity
            else:
                transferred[key] = value
        
        self.cross_regime_transfers.append({
            'source': source_regime,
            'target': target_regime,
            'similarity': similarity,
            'transferred_keys': list(transferred.keys()),
            'timestamp': datetime.now()
        })
        
        logger.info(f"Transferred knowledge from {source_regime} to {target_regime} (similarity={similarity:.2f})")
        
        return transferred
    
    def store_regime_knowledge(self, regime: str, knowledge: Dict) -> None:
        """Store learned knowledge about a market regime"""
        if regime not in self.regime_knowledge:
            self.regime_knowledge[regime] = {}
        
        self.regime_knowledge[regime].update(knowledge)
        logger.debug(f"Stored knowledge for regime '{regime}'")
    
    def _calculate_regime_similarity(self, regime1: str, regime2: str) -> float:
        """Calculate similarity between two market regimes"""
        # Simple similarity based on regime names
        regime_groups = {
            'TRENDING': ['TRENDING', 'MOMENTUM', 'BREAKOUT'],
            'RANGING': ['RANGING', 'MEAN_REVERSION', 'CONSOLIDATION'],
            'VOLATILE': ['HIGH_VOLATILITY', 'CRISIS', 'PANIC'],
            'CALM': ['LOW_VOLATILITY', 'STABLE', 'QUIET']
        }
        
        for group, members in regime_groups.items():
            if regime1 in members and regime2 in members:
                return 0.8
            elif regime1 in members or regime2 in members:
                return 0.3
        
        return 0.1
    
    def get_meta_learning_stats(self) -> Dict:
        """Get meta-learning statistics"""
        return {
            'current_learning_rate': self.current_learning_rate,
            'current_exploration_rate': self.current_exploration_rate,
            'regimes_learned': len(self.regime_knowledge),
            'cross_regime_transfers': len(self.cross_regime_transfers),
            'adaptation_count': len(self.adaptation_history)
        }
