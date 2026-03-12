"""
Deep Agent System - Multi-Agent AI Trading Intelligence
========================================================

Combines DeepAgent, VISTA, AutoML, and RL into a unified system:
1. Multiple specialized AI agents
2. Reinforcement learning for decision making
3. AutoML for model optimization
4. VISTA-style visual analysis
5. Ensemble decision making
"""

import asyncio
import logging
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import json
from pathlib import Path
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of AI agents"""
    TREND_FOLLOWER = "trend_follower"
    MEAN_REVERTER = "mean_reverter"
    MOMENTUM_TRADER = "momentum_trader"
    VOLATILITY_TRADER = "volatility_trader"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    PATTERN_RECOGNIZER = "pattern_recognizer"
    RISK_MANAGER = "risk_manager"
    PORTFOLIO_OPTIMIZER = "portfolio_optimizer"
    NEWS_ANALYZER = "news_analyzer"
    MACRO_ANALYST = "macro_analyst"
    MICROSTRUCTURE_EXPERT = "microstructure_expert"
    RL_AGENT = "rl_agent"
    AUTOML_AGENT = "automl_agent"
    VISTA_AGENT = "vista_agent"


class AgentState(Enum):
    """Agent states"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    DECIDING = "deciding"
    EXECUTING = "executing"
    LEARNING = "learning"
    ERROR = "error"


@dataclass
class AgentDecision:
    """Decision from an agent"""
    agent_id: str
    agent_type: AgentType
    action: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    
    # Trade details
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    
    # Analysis
    signals: Dict[str, float]
    features: Dict[str, Any]
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0


@dataclass
class AgentPerformance:
    """Agent performance metrics"""
    agent_id: str
    total_decisions: int
    correct_decisions: int
    accuracy: float
    avg_confidence: float
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    last_updated: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, agent_id: str, agent_type: AgentType, config: Dict = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        self.state = AgentState.IDLE
        
        # Performance tracking
        self.decisions_made = 0
        self.correct_decisions = 0
        self.total_return = 0.0
        
        # Learning
        self.learning_rate = self.config.get('learning_rate', 0.01)
        self.experience_buffer: List[Dict] = []
        self.max_experience = 10000
    
    @abstractmethod
    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data"""
        pass
    
    @abstractmethod
    async def decide(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Make a trading decision"""
        pass
    
    def learn(self, decision: AgentDecision, outcome: Dict[str, Any]):
        """Learn from decision outcome"""
        experience = {
            'decision': decision,
            'outcome': outcome,
            'timestamp': datetime.now()
        }
        self.experience_buffer.append(experience)
        
        if len(self.experience_buffer) > self.max_experience:
            self.experience_buffer = self.experience_buffer[-self.max_experience:]
        
        # Update performance
        self.decisions_made += 1
        if outcome.get('correct', False):
            self.correct_decisions += 1
        self.total_return += outcome.get('return', 0)
    
    def get_performance(self) -> AgentPerformance:
        """Get agent performance"""
        accuracy = self.correct_decisions / max(1, self.decisions_made)
        avg_return = self.total_return / max(1, self.decisions_made)
        
        return AgentPerformance(
            agent_id=self.agent_id,
            total_decisions=self.decisions_made,
            correct_decisions=self.correct_decisions,
            accuracy=accuracy,
            avg_confidence=0.7,  # Would calculate from decisions
            avg_return=avg_return,
            sharpe_ratio=avg_return / 0.1 if avg_return > 0 else 0,  # Simplified
            max_drawdown=0.1  # Would track actual drawdown
        )


class TrendFollowerAgent(BaseAgent):
    """Trend following agent"""
    
    def __init__(self, agent_id: str, config: Dict = None):
        super().__init__(agent_id, AgentType.TREND_FOLLOWER, config)
        self.fast_period = config.get('fast_period', 10) if config else 10
        self.slow_period = config.get('slow_period', 50) if config else 50
    
    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze for trends"""
        self.state = AgentState.ANALYZING
        
        prices = market_data.get('close', [])
        if len(prices) < self.slow_period:
            return {'trend': 'neutral', 'strength': 0}
        
        # Calculate moving averages
        fast_ma = np.mean(prices[-self.fast_period:])
        slow_ma = np.mean(prices[-self.slow_period:])
        
        # Determine trend
        if fast_ma > slow_ma * 1.01:
            trend = 'bullish'
            strength = min(1.0, (fast_ma - slow_ma) / slow_ma * 10)
        elif fast_ma < slow_ma * 0.99:
            trend = 'bearish'
            strength = min(1.0, (slow_ma - fast_ma) / slow_ma * 10)
        else:
            trend = 'neutral'
            strength = 0
        
        self.state = AgentState.IDLE
        
        return {
            'trend': trend,
            'strength': strength,
            'fast_ma': fast_ma,
            'slow_ma': slow_ma
        }
    
    async def decide(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Make trend-based decision"""
        self.state = AgentState.DECIDING
        
        trend = analysis.get('trend', 'neutral')
        strength = analysis.get('strength', 0)
        
        if trend == 'bullish' and strength > 0.3:
            action = 'BUY'
            confidence = min(0.9, 0.5 + strength * 0.4)
        elif trend == 'bearish' and strength > 0.3:
            action = 'SELL'
            confidence = min(0.9, 0.5 + strength * 0.4)
        else:
            action = 'HOLD'
            confidence = 0.5
        
        self.state = AgentState.IDLE
        
        return AgentDecision(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=f"Trend: {trend}, Strength: {strength:.2f}",
            symbol="",
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            position_size=0,
            signals={'trend': 1 if trend == 'bullish' else -1 if trend == 'bearish' else 0},
            features=analysis
        )


class MomentumAgent(BaseAgent):
    """Momentum trading agent"""
    
    def __init__(self, agent_id: str, config: Dict = None):
        super().__init__(agent_id, AgentType.MOMENTUM_TRADER, config)
        self.lookback = config.get('lookback', 14) if config else 14
    
    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze momentum"""
        self.state = AgentState.ANALYZING
        
        prices = market_data.get('close', [])
        if len(prices) < self.lookback + 1:
            return {'momentum': 0, 'rsi': 50}
        
        # Calculate momentum
        returns = np.diff(prices[-self.lookback-1:]) / prices[-self.lookback-1:-1]
        momentum = np.sum(returns)
        
        # Calculate RSI
        gains = np.maximum(returns, 0)
        losses = np.abs(np.minimum(returns, 0))
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.0001
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        self.state = AgentState.IDLE
        
        return {
            'momentum': momentum,
            'rsi': rsi,
            'returns': returns.tolist()
        }
    
    async def decide(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Make momentum-based decision"""
        self.state = AgentState.DECIDING
        
        momentum = analysis.get('momentum', 0)
        rsi = analysis.get('rsi', 50)
        
        # Strong momentum + not overbought
        if momentum > 0.05 and rsi < 70:
            action = 'BUY'
            confidence = min(0.85, 0.5 + momentum * 2)
        # Negative momentum + not oversold
        elif momentum < -0.05 and rsi > 30:
            action = 'SELL'
            confidence = min(0.85, 0.5 + abs(momentum) * 2)
        else:
            action = 'HOLD'
            confidence = 0.5
        
        self.state = AgentState.IDLE
        
        return AgentDecision(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=f"Momentum: {momentum:.4f}, RSI: {rsi:.1f}",
            symbol="",
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            position_size=0,
            signals={'momentum': momentum, 'rsi': rsi},
            features=analysis
        )


class RLAgent(BaseAgent):
    """Reinforcement Learning agent"""
    
    def __init__(self, agent_id: str, config: Dict = None):
        super().__init__(agent_id, AgentType.RL_AGENT, config)
        
        # Q-learning parameters
        self.gamma = config.get('gamma', 0.99) if config else 0.99
        self.epsilon = config.get('epsilon', 0.1) if config else 0.1
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.01
        
        # State-action values (simplified)
        self.q_table: Dict[str, Dict[str, float]] = {}
        
        # Actions
        self.actions = ['BUY', 'SELL', 'HOLD']
    
    def _get_state_key(self, features: Dict) -> str:
        """Convert features to state key"""
        # Discretize features
        trend = 'up' if features.get('trend', 0) > 0 else 'down' if features.get('trend', 0) < 0 else 'flat'
        vol = 'high' if features.get('volatility', 0) > 0.02 else 'low'
        return f"{trend}_{vol}"
    
    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market for RL state"""
        self.state = AgentState.ANALYZING
        
        prices = market_data.get('close', [])
        if len(prices) < 20:
            return {'trend': 0, 'volatility': 0}
        
        # Calculate features
        returns = np.diff(prices[-20:]) / prices[-20:-1]
        trend = np.mean(returns)
        volatility = np.std(returns)
        
        self.state = AgentState.IDLE
        
        return {
            'trend': trend,
            'volatility': volatility,
            'last_price': prices[-1]
        }
    
    async def decide(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Make RL-based decision"""
        self.state = AgentState.DECIDING
        
        state_key = self._get_state_key(analysis)
        
        # Epsilon-greedy action selection
        if np.random.random() < self.epsilon:
            action = np.random.choice(self.actions)
            confidence = 0.5
        else:
            # Get Q-values for state
            if state_key not in self.q_table:
                self.q_table[state_key] = {a: 0.0 for a in self.actions}
            
            q_values = self.q_table[state_key]
            action = max(q_values, key=q_values.get)
            confidence = min(0.9, 0.5 + abs(q_values[action]) / 10)
        
        # Decay epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        self.state = AgentState.IDLE
        
        return AgentDecision(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=f"RL decision from state: {state_key}",
            symbol="",
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            position_size=0,
            signals={'state': state_key},
            features=analysis
        )
    
    def update_q_value(self, state: str, action: str, reward: float, next_state: str):
        """Update Q-value"""
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.actions}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in self.actions}
        
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action] = new_q


class AutoMLAgent(BaseAgent):
    """AutoML agent for automatic model selection"""
    
    def __init__(self, agent_id: str, config: Dict = None):
        super().__init__(agent_id, AgentType.AUTOML_AGENT, config)
        
        # Model registry
        self.models: Dict[str, Any] = {}
        self.model_scores: Dict[str, float] = {}
        self.best_model: Optional[str] = None
    
    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with AutoML"""
        self.state = AgentState.ANALYZING
        
        prices = market_data.get('close', [])
        if len(prices) < 50:
            return {'prediction': 0, 'model': 'none'}
        
        # Feature engineering
        features = self._extract_features(prices)
        
        # Get prediction from best model (simplified)
        prediction = np.mean(features.get('returns', [0]))
        
        self.state = AgentState.IDLE
        
        return {
            'prediction': prediction,
            'features': features,
            'model': self.best_model or 'ensemble'
        }
    
    def _extract_features(self, prices: List[float]) -> Dict[str, Any]:
        """Extract features for ML"""
        prices_arr = np.array(prices)
        returns = np.diff(prices_arr) / prices_arr[:-1]
        
        return {
            'returns': returns[-10:].tolist(),
            'mean_return': float(np.mean(returns)),
            'std_return': float(np.std(returns)),
            'skew': float(np.mean((returns - np.mean(returns))**3) / (np.std(returns)**3 + 1e-10)),
            'last_5_returns': returns[-5:].tolist()
        }
    
    async def decide(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Make AutoML-based decision"""
        self.state = AgentState.DECIDING
        
        prediction = analysis.get('prediction', 0)
        
        if prediction > 0.001:
            action = 'BUY'
            confidence = min(0.85, 0.5 + prediction * 100)
        elif prediction < -0.001:
            action = 'SELL'
            confidence = min(0.85, 0.5 + abs(prediction) * 100)
        else:
            action = 'HOLD'
            confidence = 0.5
        
        self.state = AgentState.IDLE
        
        return AgentDecision(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=f"AutoML prediction: {prediction:.6f}",
            symbol="",
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            position_size=0,
            signals={'prediction': prediction},
            features=analysis
        )


class DeepAgentSystem:
    """
    Deep Agent System - Multi-Agent AI Trading Intelligence
    
    Combines multiple specialized agents:
    - Trend followers
    - Momentum traders
    - RL agents
    - AutoML agents
    - And more...
    
    Uses ensemble decision making for robust trading.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize agents
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()
        
        # Ensemble weights
        self.agent_weights: Dict[str, float] = {}
        self._initialize_weights()
        
        # Decision history
        self.decision_history: List[Dict] = []
        self.max_history = 1000
        
        # Performance tracking
        self.ensemble_performance = {
            'total_decisions': 0,
            'correct_decisions': 0,
            'total_return': 0.0
        }
        
        # Storage
        self.storage_path = Path(self.config.get('storage_path', 'agent_storage'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Deep Agent System initialized with {len(self.agents)} agents")
    
    def _initialize_agents(self):
        """Initialize all agents"""
        # Trend follower
        self.agents['trend_fast'] = TrendFollowerAgent(
            'trend_fast', {'fast_period': 5, 'slow_period': 20}
        )
        self.agents['trend_slow'] = TrendFollowerAgent(
            'trend_slow', {'fast_period': 20, 'slow_period': 100}
        )
        
        # Momentum
        self.agents['momentum_short'] = MomentumAgent(
            'momentum_short', {'lookback': 7}
        )
        self.agents['momentum_long'] = MomentumAgent(
            'momentum_long', {'lookback': 21}
        )
        
        # RL
        self.agents['rl_main'] = RLAgent(
            'rl_main', {'gamma': 0.99, 'epsilon': 0.1}
        )
        
        # AutoML
        self.agents['automl'] = AutoMLAgent('automl', {})
    
    def _initialize_weights(self):
        """Initialize agent weights"""
        # Equal weights initially
        n_agents = len(self.agents)
        for agent_id in self.agents:
            self.agent_weights[agent_id] = 1.0 / n_agents
    
    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Get analysis from all agents"""
        analyses = {}
        
        # Run all agents in parallel
        tasks = []
        for agent_id, agent in self.agents.items():
            tasks.append(self._analyze_with_agent(agent_id, agent, market_data))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for agent_id, result in zip(self.agents.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_id} analysis failed: {result}")
                analyses[agent_id] = {'error': str(result)}
            else:
                analyses[agent_id] = result
        
        return analyses
    
    async def _analyze_with_agent(
        self,
        agent_id: str,
        agent: BaseAgent,
        market_data: Dict
    ) -> Dict:
        """Run analysis with single agent"""
        try:
            return await agent.analyze(market_data)
        except Exception as e:
            logger.error(f"Agent {agent_id} error: {e}")
            return {'error': str(e)}
    
    async def get_ensemble_decision(
        self,
        market_data: Dict[str, Any],
        symbol: str = "UNKNOWN"
    ) -> AgentDecision:
        """Get ensemble decision from all agents"""
        # Get analyses
        analyses = await self.analyze_market(market_data)
        
        # Get decisions from each agent
        decisions: List[AgentDecision] = []
        
        for agent_id, agent in self.agents.items():
            analysis = analyses.get(agent_id, {})
            if 'error' not in analysis:
                try:
                    decision = await agent.decide(analysis)
                    decision.symbol = symbol
                    decisions.append(decision)
                except Exception as e:
                    logger.error(f"Agent {agent_id} decision failed: {e}")
        
        # Ensemble voting
        ensemble_decision = self._ensemble_vote(decisions, symbol)
        
        # Store decision
        self.decision_history.append({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'individual_decisions': [
                {'agent': d.agent_id, 'action': d.action, 'confidence': d.confidence}
                for d in decisions
            ],
            'ensemble_decision': ensemble_decision.action,
            'ensemble_confidence': ensemble_decision.confidence
        })
        
        if len(self.decision_history) > self.max_history:
            self.decision_history = self.decision_history[-self.max_history:]
        
        self.ensemble_performance['total_decisions'] += 1
        
        return ensemble_decision
    
    def _ensemble_vote(
        self,
        decisions: List[AgentDecision],
        symbol: str
    ) -> AgentDecision:
        """Combine agent decisions through weighted voting"""
        if not decisions:
            return AgentDecision(
                agent_id='ensemble',
                agent_type=AgentType.RL_AGENT,
                action='HOLD',
                confidence=0.0,
                reasoning="No agent decisions available",
                symbol=symbol,
                entry_price=0,
                stop_loss=0,
                take_profit=0,
                position_size=0,
                signals={},
                features={}
            )
        
        # Weighted voting
        action_scores = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        
        for decision in decisions:
            weight = self.agent_weights.get(decision.agent_id, 1.0 / len(decisions))
            action_scores[decision.action] += weight * decision.confidence
        
        # Get winning action
        best_action = max(action_scores, key=action_scores.get)
        total_score = sum(action_scores.values())
        confidence = action_scores[best_action] / total_score if total_score > 0 else 0
        
        # Combine reasoning
        reasoning_parts = [
            f"{d.agent_id}: {d.action} ({d.confidence:.2f})"
            for d in decisions
        ]
        reasoning = f"Ensemble: {' | '.join(reasoning_parts)}"
        
        # Combine signals
        combined_signals = {}
        for decision in decisions:
            for key, value in decision.signals.items():
                if key not in combined_signals:
                    combined_signals[key] = []
                combined_signals[key].append(value)
        
        # Average signals
        avg_signals = {
            k: np.mean([v for v in vals if isinstance(v, (int, float))])
            for k, vals in combined_signals.items()
            if any(isinstance(v, (int, float)) for v in vals)
        }
        
        return AgentDecision(
            agent_id='ensemble',
            agent_type=AgentType.RL_AGENT,
            action=best_action,
            confidence=confidence,
            reasoning=reasoning,
            symbol=symbol,
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            position_size=0,
            signals=avg_signals,
            features={'action_scores': action_scores}
        )
    
    def update_weights(self, agent_id: str, performance_delta: float):
        """Update agent weight based on performance"""
        if agent_id in self.agent_weights:
            # Increase weight for good performance
            self.agent_weights[agent_id] *= (1 + performance_delta * 0.1)
            
            # Normalize weights
            total = sum(self.agent_weights.values())
            for aid in self.agent_weights:
                self.agent_weights[aid] /= total
    
    def learn_from_outcome(
        self,
        decision: AgentDecision,
        outcome: Dict[str, Any]
    ):
        """Learn from decision outcome"""
        # Update ensemble performance
        if outcome.get('correct', False):
            self.ensemble_performance['correct_decisions'] += 1
        self.ensemble_performance['total_return'] += outcome.get('return', 0)
        
        # Update individual agents
        for agent_id, agent in self.agents.items():
            agent.learn(decision, outcome)
            
            # Update weights based on agent performance
            perf = agent.get_performance()
            if perf.total_decisions > 10:
                delta = perf.accuracy - 0.5  # Relative to random
                self.update_weights(agent_id, delta)
    
    def get_agent_performances(self) -> Dict[str, AgentPerformance]:
        """Get all agent performances"""
        return {
            agent_id: agent.get_performance()
            for agent_id, agent in self.agents.items()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        performances = self.get_agent_performances()
        
        return {
            'num_agents': len(self.agents),
            'agent_types': [a.agent_type.value for a in self.agents.values()],
            'agent_weights': self.agent_weights,
            'ensemble_performance': self.ensemble_performance,
            'agent_performances': {
                aid: {
                    'accuracy': p.accuracy,
                    'total_decisions': p.total_decisions,
                    'avg_return': p.avg_return
                }
                for aid, p in performances.items()
            },
            'decision_history_size': len(self.decision_history)
        }
