"""
Multi-Agent Learning Collective
================================
Ensemble of specialist AI agents learning together from the market.

Features:
- Specialist agents (Momentum, Mean Reversion, Volatility, etc.)
- Meta-agent coordination
- Competitive learning (capital allocation)
- Cooperative learning (knowledge sharing)
"""

import logging
import random
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
from abc import ABC, abstractmethod
import numpy

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of specialist agents"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    MICROSTRUCTURE = "microstructure"
    MACRO = "macro"
    SENTIMENT = "sentiment"
    META = "meta"


@dataclass
class AgentSignal:
    """Signal from a specialist agent"""
    agent_id: str
    agent_type: AgentType
    action: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    features_used: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'action': self.action,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'features_used': self.features_used,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SharedKnowledge:
    """Knowledge shared between agents"""
    knowledge_id: str
    source_agent: str
    knowledge_type: str
    content: Dict
    confidence: float
    validated_by: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'knowledge_id': self.knowledge_id,
            'source_agent': self.source_agent,
            'knowledge_type': self.knowledge_type,
            'content': self.content,
            'confidence': self.confidence,
            'validated_by': self.validated_by,
            'timestamp': self.timestamp.isoformat()
        }


class SpecialistAgent(ABC):
    """
    Base class for specialist trading agents.
    
    Each specialist focuses on a specific aspect of the market.
    """
    
    def __init__(self, agent_id: str, agent_type: AgentType, config: Dict = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        
        # Performance tracking
        self.trades: int = 0
        self.wins: int = 0
        self.total_pnl: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.recent_performance: deque = deque(maxlen=100)
        
        # Learning state
        self.knowledge_base: List[Dict] = []
        self.lessons_learned: List[Dict] = []
        self.is_learning: bool = True
        
        # Capital allocation
        self.capital_allocation: float = 0.0
        self.allocation_history: List[float] = []
        
    @abstractmethod
    def analyze(self, market_data: Dict) -> AgentSignal:
        """Analyze market data and generate signal"""
        pass
    
    @abstractmethod
    def learn_from_feedback(self, feedback: Dict):
        """Learn from market feedback"""
        pass
    
    def update_performance(self, trade_result: Dict):
        """Update performance metrics"""
        pnl = trade_result.get('pnl', 0)
        
        self.trades += 1
        if pnl > 0:
            self.wins += 1
        self.total_pnl += pnl
        self.recent_performance.append(pnl)
        
        # Update Sharpe ratio
        if len(self.recent_performance) > 10:
            returns = list(self.recent_performance)
            self.sharpe_ratio = np.mean(returns) / max(np.std(returns), 0.0001) * np.sqrt(252)
    
    @property
    def win_rate(self) -> float:
        if self.trades == 0:
            return 0.5
        return self.wins / self.trades
    
    @property
    def performance_score(self) -> float:
        """Combined performance score"""
        return 0.4 * self.sharpe_ratio + 0.3 * self.win_rate + 0.3 * min(1.0, self.total_pnl)
    
    def get_status(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'trades': self.trades,
            'win_rate': self.win_rate,
            'sharpe_ratio': self.sharpe_ratio,
            'total_pnl': self.total_pnl,
            'performance_score': self.performance_score,
            'capital_allocation': self.capital_allocation,
            'is_learning': self.is_learning
        }


class MomentumSpecialist(SpecialistAgent):
    """
    Specialist in momentum/trend-following strategies.
    
    Focuses on:
    - Trend detection
    - Breakout identification
    - Momentum indicators
    """
    
    def __init__(self, agent_id: str = "momentum_agent", config: Dict = None):
        super().__init__(agent_id, AgentType.MOMENTUM, config)
        
        self.trend_threshold = config.get('trend_threshold', 0.6) if config else 0.6
        self.momentum_period = config.get('momentum_period', 20) if config else 20
        
    def analyze(self, market_data: Dict) -> AgentSignal:
        """Analyze for momentum signals"""
        prices = market_data.get('prices', [])
        
        if len(prices) < self.momentum_period:
            return AgentSignal(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                action='HOLD',
                confidence=0.0,
                reasoning="Insufficient data for momentum analysis"
            )
        
        # Calculate momentum
        recent_prices = prices[-self.momentum_period:]
        momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # Calculate trend strength
        trend_strength = abs(momentum) / 0.05  # Normalize to ~1 for 5% move
        trend_strength = min(1.0, trend_strength)
        
        if momentum > 0.01 and trend_strength > self.trend_threshold:
            action = 'BUY'
            confidence = trend_strength
            reasoning = f"Strong upward momentum: {momentum*100:.2f}%"
        elif momentum < -0.01 and trend_strength > self.trend_threshold:
            action = 'SELL'
            confidence = trend_strength
            reasoning = f"Strong downward momentum: {momentum*100:.2f}%"
        else:
            action = 'HOLD'
            confidence = 0.3
            reasoning = f"No clear momentum signal: {momentum*100:.2f}%"
        
        return AgentSignal(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            features_used=['momentum', 'trend_strength']
        )
    
    def learn_from_feedback(self, feedback: Dict):
        """Learn from trade outcome"""
        if feedback.get('action') in ['BUY', 'SELL']:
            pnl = feedback.get('pnl', 0)
            
            if pnl < 0:
                # Lesson: Maybe trend wasn't strong enough
                self.trend_threshold = min(0.9, self.trend_threshold * 1.05)
                self.lessons_learned.append({
                    'type': 'THRESHOLD_INCREASE',
                    'reason': 'False momentum signal',
                    'new_threshold': self.trend_threshold
                })
            elif pnl > 0:
                # Lesson: Threshold was appropriate
                self.lessons_learned.append({
                    'type': 'VALIDATION',
                    'reason': 'Momentum signal was correct'
                })


class MeanReversionSpecialist(SpecialistAgent):
    """
    Specialist in mean reversion strategies.
    
    Focuses on:
    - Overbought/oversold conditions
    - Support/resistance levels
    - Range-bound markets
    """
    
    def __init__(self, agent_id: str = "mean_reversion_agent", config: Dict = None):
        super().__init__(agent_id, AgentType.MEAN_REVERSION, config)
        
        self.rsi_oversold = config.get('rsi_oversold', 30) if config else 30
        self.rsi_overbought = config.get('rsi_overbought', 70) if config else 70
        self.lookback_period = config.get('lookback_period', 14) if config else 14
        
    def analyze(self, market_data: Dict) -> AgentSignal:
        """Analyze for mean reversion signals"""
        prices = market_data.get('prices', [])
        
        if len(prices) < self.lookback_period + 1:
            return AgentSignal(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                action='HOLD',
                confidence=0.0,
                reasoning="Insufficient data for mean reversion analysis"
            )
        
        # Calculate simple RSI-like indicator
        changes = np.diff(prices[-self.lookback_period-1:])
        gains = np.sum(changes[changes > 0])
        losses = abs(np.sum(changes[changes < 0]))
        
        if losses == 0:
            rsi = 100
        else:
            rs = gains / losses
            rsi = 100 - (100 / (1 + rs))
        
        # Calculate distance from mean
        mean_price = np.mean(prices[-self.lookback_period:])
        current_price = prices[-1]
        deviation = (current_price - mean_price) / mean_price
        
        if rsi < self.rsi_oversold:
            action = 'BUY'
            confidence = (self.rsi_oversold - rsi) / self.rsi_oversold
            reasoning = f"Oversold condition: RSI={rsi:.1f}, deviation={deviation*100:.2f}%"
        elif rsi > self.rsi_overbought:
            action = 'SELL'
            confidence = (rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
            reasoning = f"Overbought condition: RSI={rsi:.1f}, deviation={deviation*100:.2f}%"
        else:
            action = 'HOLD'
            confidence = 0.3
            reasoning = f"Neutral RSI: {rsi:.1f}"
        
        return AgentSignal(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=min(1.0, confidence),
            reasoning=reasoning,
            features_used=['rsi', 'mean_deviation']
        )
    
    def learn_from_feedback(self, feedback: Dict):
        """Learn from trade outcome"""
        pnl = feedback.get('pnl', 0)
        
        if pnl < 0:
            # Adjust thresholds to be more conservative
            self.rsi_oversold = max(20, self.rsi_oversold - 2)
            self.rsi_overbought = min(80, self.rsi_overbought + 2)
        elif pnl > 0:
            # Thresholds were appropriate
            pass


class VolatilitySpecialist(SpecialistAgent):
    """
    Specialist in volatility-based strategies.
    
    Focuses on:
    - Volatility regime detection
    - Volatility breakouts
    - Options-like strategies
    """
    
    def __init__(self, agent_id: str = "volatility_agent", config: Dict = None):
        super().__init__(agent_id, AgentType.VOLATILITY, config)
        
        self.vol_window = config.get('vol_window', 20) if config else 20
        self.vol_threshold = config.get('vol_threshold', 1.5) if config else 1.5
        
    def analyze(self, market_data: Dict) -> AgentSignal:
        """Analyze volatility conditions"""
        prices = market_data.get('prices', [])
        
        if len(prices) < self.vol_window * 2:
            return AgentSignal(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                action='HOLD',
                confidence=0.0,
                reasoning="Insufficient data for volatility analysis"
            )
        
        # Calculate recent vs historical volatility
        returns = np.diff(np.log(prices[-self.vol_window*2:]))
        recent_vol = np.std(returns[-self.vol_window:])
        historical_vol = np.std(returns[:-self.vol_window])
        
        vol_ratio = recent_vol / max(historical_vol, 0.0001)
        
        if vol_ratio > self.vol_threshold:
            # High volatility - be cautious
            action = 'HOLD'
            confidence = 0.8
            reasoning = f"High volatility regime: {vol_ratio:.2f}x normal. Reduce exposure."
        elif vol_ratio < 1 / self.vol_threshold:
            # Low volatility - potential breakout coming
            action = 'HOLD'
            confidence = 0.6
            reasoning = f"Low volatility regime: {vol_ratio:.2f}x normal. Breakout may be imminent."
        else:
            action = 'HOLD'
            confidence = 0.4
            reasoning = f"Normal volatility: {vol_ratio:.2f}x"
        
        return AgentSignal(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            features_used=['volatility_ratio', 'recent_vol', 'historical_vol']
        )
    
    def learn_from_feedback(self, feedback: Dict):
        """Learn from volatility predictions"""
        pass


class MicrostructureSpecialist(SpecialistAgent):
    """
    Specialist in market microstructure.
    
    Focuses on:
    - Order book analysis
    - Trade flow
    - Liquidity patterns
    """
    
    def __init__(self, agent_id: str = "microstructure_agent", config: Dict = None):
        super().__init__(agent_id, AgentType.MICROSTRUCTURE, config)
        
    def analyze(self, market_data: Dict) -> AgentSignal:
        """Analyze market microstructure"""
        order_book = market_data.get('order_book', {})
        
        bid_volume = order_book.get('bid_volume', 0)
        ask_volume = order_book.get('ask_volume', 0)
        
        if bid_volume == 0 and ask_volume == 0:
            return AgentSignal(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                action='HOLD',
                confidence=0.0,
                reasoning="No order book data available"
            )
        
        # Calculate order imbalance
        total_volume = bid_volume + ask_volume
        imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
        
        if imbalance > 0.3:
            action = 'BUY'
            confidence = min(1.0, abs(imbalance))
            reasoning = f"Strong bid imbalance: {imbalance:.2f}"
        elif imbalance < -0.3:
            action = 'SELL'
            confidence = min(1.0, abs(imbalance))
            reasoning = f"Strong ask imbalance: {imbalance:.2f}"
        else:
            action = 'HOLD'
            confidence = 0.3
            reasoning = f"Balanced order book: {imbalance:.2f}"
        
        return AgentSignal(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            features_used=['order_imbalance', 'bid_volume', 'ask_volume']
        )
    
    def learn_from_feedback(self, feedback: Dict):
        """Learn from microstructure predictions"""
        pass


class MacroSpecialist(SpecialistAgent):
    """
    Specialist in macroeconomic analysis.
    
    Focuses on:
    - Economic indicators
    - Central bank policy
    - Geopolitical events
    """
    
    def __init__(self, agent_id: str = "macro_agent", config: Dict = None):
        super().__init__(agent_id, AgentType.MACRO, config)
        
    def analyze(self, market_data: Dict) -> AgentSignal:
        """Analyze macroeconomic conditions"""
        macro_data = market_data.get('macro', {})
        
        interest_rate_trend = macro_data.get('interest_rate_trend', 0)
        inflation_trend = macro_data.get('inflation_trend', 0)
        gdp_growth = macro_data.get('gdp_growth', 0)
        
        # Simple macro score
        macro_score = gdp_growth - inflation_trend + interest_rate_trend * 0.5
        
        if macro_score > 0.5:
            action = 'BUY'
            confidence = min(1.0, macro_score)
            reasoning = f"Positive macro environment: score={macro_score:.2f}"
        elif macro_score < -0.5:
            action = 'SELL'
            confidence = min(1.0, abs(macro_score))
            reasoning = f"Negative macro environment: score={macro_score:.2f}"
        else:
            action = 'HOLD'
            confidence = 0.4
            reasoning = f"Neutral macro environment: score={macro_score:.2f}"
        
        return AgentSignal(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            features_used=['interest_rate', 'inflation', 'gdp']
        )
    
    def learn_from_feedback(self, feedback: Dict):
        """Learn from macro predictions"""
        pass


class SentimentSpecialist(SpecialistAgent):
    """
    Specialist in market sentiment analysis.
    
    Focuses on:
    - News sentiment
    - Social media sentiment
    - Fear/Greed indicators
    """
    
    def __init__(self, agent_id: str = "sentiment_agent", config: Dict = None):
        super().__init__(agent_id, AgentType.SENTIMENT, config)
        
    def analyze(self, market_data: Dict) -> AgentSignal:
        """Analyze market sentiment"""
        sentiment_data = market_data.get('sentiment', {})
        
        news_sentiment = sentiment_data.get('news', 0)
        social_sentiment = sentiment_data.get('social', 0)
        fear_greed = sentiment_data.get('fear_greed', 50)
        
        # Combine sentiments
        combined_sentiment = 0.4 * news_sentiment + 0.3 * social_sentiment + 0.3 * (fear_greed - 50) / 50
        
        if combined_sentiment > 0.3:
            action = 'BUY'
            confidence = min(1.0, combined_sentiment)
            reasoning = f"Positive sentiment: {combined_sentiment:.2f}"
        elif combined_sentiment < -0.3:
            action = 'SELL'
            confidence = min(1.0, abs(combined_sentiment))
            reasoning = f"Negative sentiment: {combined_sentiment:.2f}"
        else:
            action = 'HOLD'
            confidence = 0.3
            reasoning = f"Neutral sentiment: {combined_sentiment:.2f}"
        
        return AgentSignal(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            features_used=['news_sentiment', 'social_sentiment', 'fear_greed']
        )
    
    def learn_from_feedback(self, feedback: Dict):
        """Learn from sentiment predictions"""
        pass


class MetaAgent:
    """
    Meta-agent that coordinates all specialist agents.
    
    Responsibilities:
    - Aggregate signals from specialists
    - Resolve conflicts
    - Make final trading decisions
    - Learn which specialists to trust
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        self.agent_id = "meta_agent"
        self.specialists: Dict[str, SpecialistAgent] = {}
        self.agent_weights: Dict[str, float] = {}
        self.decision_history: deque = deque(maxlen=10000)
        
        # Learning parameters
        self.weight_learning_rate = config.get('weight_learning_rate', 0.1)
        self.min_weight = config.get('min_weight', 0.05)
        
    def register_specialist(self, agent: SpecialistAgent):
        """Register a specialist agent"""
        self.specialists[agent.agent_id] = agent
        self.agent_weights[agent.agent_id] = 1.0 / max(1, len(self.specialists))
        
        # Normalize weights
        total = sum(self.agent_weights.values())
        for agent_id in self.agent_weights:
            self.agent_weights[agent_id] /= total
        
        logger.info(f"Registered specialist: {agent.agent_id}")
    
    def aggregate_signals(self, market_data: Dict) -> Dict:
        """
        Aggregate signals from all specialists.
        
        Returns final decision with confidence.
        """
        signals = {}
        
        # Collect signals from all specialists
        for agent_id, agent in self.specialists.items():
            try:
                signal = agent.analyze(market_data)
                signals[agent_id] = signal
            except Exception as e:
                logger.error(f"Agent {agent_id} failed to analyze: {e}")
        
        if not signals:
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': 'No signals from specialists',
                'signals': {}
            }
        
        # Weighted voting
        action_scores = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        
        for agent_id, signal in signals.items():
            weight = self.agent_weights.get(agent_id, 0.1)
            action_scores[signal.action] += weight * signal.confidence
        
        # Normalize
        total_score = sum(action_scores.values())
        if total_score > 0:
            for action in action_scores:
                action_scores[action] /= total_score
        
        # Get best action
        best_action = max(action_scores, key=action_scores.get)
        confidence = action_scores[best_action]
        
        # Build reasoning
        supporting_agents = [
            agent_id for agent_id, signal in signals.items()
            if signal.action == best_action
        ]
        
        decision = {
            'action': best_action,
            'confidence': confidence,
            'action_scores': action_scores,
            'supporting_agents': supporting_agents,
            'signals': {agent_id: signal.to_dict() for agent_id, signal in signals.items()},
            'reasoning': f"Consensus: {best_action} ({len(supporting_agents)}/{len(signals)} agents agree)"
        }
        
        self.decision_history.append({
            'decision': decision,
            'timestamp': datetime.now().isoformat()
        })
        
        return decision
    
    def update_weights(self, feedback: Dict):
        """
        Update agent weights based on feedback.
        
        Agents that contributed to correct decisions get higher weights.
        """
        action_taken = feedback.get('action')
        pnl = feedback.get('pnl', 0)
        signals = feedback.get('signals', {})
        
        for agent_id, signal in signals.items():
            if agent_id not in self.agent_weights:
                continue
            
            # Reward agents that agreed with the action
            if signal.get('action') == action_taken:
                if pnl > 0:
                    # Correct prediction - increase weight
                    self.agent_weights[agent_id] *= (1 + self.weight_learning_rate)
                else:
                    # Wrong prediction - decrease weight
                    self.agent_weights[agent_id] *= (1 - self.weight_learning_rate)
            else:
                if pnl > 0:
                    # Disagreed but we were right - slight decrease
                    self.agent_weights[agent_id] *= (1 - self.weight_learning_rate * 0.5)
                else:
                    # Disagreed and we were wrong - slight increase
                    self.agent_weights[agent_id] *= (1 + self.weight_learning_rate * 0.5)
            
            # Enforce minimum weight
            self.agent_weights[agent_id] = max(self.min_weight, self.agent_weights[agent_id])
        
        # Normalize weights
        total = sum(self.agent_weights.values())
        for agent_id in self.agent_weights:
            self.agent_weights[agent_id] /= total
    
    def get_agent_rankings(self) -> List[Tuple[str, float]]:
        """Get agents ranked by weight"""
        return sorted(self.agent_weights.items(), key=lambda x: x[1], reverse=True)


class AgentCompetition:
    """
    Manages competition between agents for capital allocation.
    
    Better performing agents get more capital.
    """
    
    def __init__(self, total_capital: float = 1000000):
        self.total_capital = total_capital
        self.agents: Dict[str, SpecialistAgent] = {}
        self.allocation_history: List[Dict] = []
        
    def register_agent(self, agent: SpecialistAgent):
        """Register an agent for competition"""
        self.agents[agent.agent_id] = agent
    
    def allocate_capital(self) -> Dict[str, float]:
        """
        Allocate capital based on performance.
        
        Uses softmax for smooth allocation.
        """
        if not self.agents:
            return {}
        
        # Get performance scores
        scores = {}
        for agent_id, agent in self.agents.items():
            scores[agent_id] = agent.performance_score
        
        # Softmax allocation
        max_score = max(scores.values()) if scores else 0
        exp_scores = {k: np.exp(v - max_score) for k, v in scores.items()}
        total_exp = sum(exp_scores.values())
        
        allocations = {}
        for agent_id, exp_score in exp_scores.items():
            allocation = (exp_score / total_exp) * self.total_capital
            allocations[agent_id] = allocation
            self.agents[agent_id].capital_allocation = allocation
        
        self.allocation_history.append({
            'allocations': allocations,
            'timestamp': datetime.now().isoformat()
        })
        
        return allocations
    
    def get_allocation_summary(self) -> Dict:
        """Get allocation summary"""
        allocations = self.allocate_capital()
        
        return {
            'total_capital': self.total_capital,
            'allocations': allocations,
            'agent_count': len(self.agents),
            'top_agent': max(allocations, key=allocations.get) if allocations else None
        }


class KnowledgeTransfer:
    """
    Manages knowledge sharing between agents.
    
    When one agent discovers something, others can learn from it.
    """
    
    def __init__(self):
        self.shared_knowledge: List[SharedKnowledge] = []
        self.transfer_history: List[Dict] = []
        
    def share_knowledge(
        self,
        source_agent: str,
        knowledge_type: str,
        content: Dict,
        confidence: float
    ) -> SharedKnowledge:
        """Share knowledge from one agent"""
        knowledge = SharedKnowledge(
            knowledge_id=f"know_{datetime.now().timestamp()}",
            source_agent=source_agent,
            knowledge_type=knowledge_type,
            content=content,
            confidence=confidence
        )
        
        self.shared_knowledge.append(knowledge)
        logger.info(f"Knowledge shared by {source_agent}: {knowledge_type}")
        
        return knowledge
    
    def validate_knowledge(self, knowledge_id: str, validator_agent: str, is_valid: bool):
        """Validate shared knowledge"""
        for knowledge in self.shared_knowledge:
            if knowledge.knowledge_id == knowledge_id:
                if is_valid:
                    knowledge.validated_by.append(validator_agent)
                    knowledge.confidence = min(1.0, knowledge.confidence * 1.1)
                else:
                    knowledge.confidence *= 0.9
                break
    
    def get_knowledge_for_agent(self, agent_id: str) -> List[SharedKnowledge]:
        """Get knowledge relevant for an agent (not from themselves)"""
        return [k for k in self.shared_knowledge if k.source_agent != agent_id]
    
    def get_validated_knowledge(self, min_validators: int = 2) -> List[SharedKnowledge]:
        """Get knowledge validated by multiple agents"""
        return [k for k in self.shared_knowledge if len(k.validated_by) >= min_validators]


class AgentCollective:
    """
    Master system for the multi-agent learning collective.
    
    Coordinates:
    - Specialist agents
    - Meta-agent
    - Competition
    - Knowledge sharing
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        self.meta_agent = MetaAgent(config)
        self.competition = AgentCompetition(config.get('total_capital', 1000000))
        self.knowledge_transfer = KnowledgeTransfer()
        
        # Initialize default specialists
        self._initialize_specialists(config)
        
        logger.info("AgentCollective initialized")
    
    def _initialize_specialists(self, config: Dict):
        """Initialize default specialist agents"""
        specialists = [
            MomentumSpecialist(config=config),
            MeanReversionSpecialist(config=config),
            VolatilitySpecialist(config=config),
            MicrostructureSpecialist(config=config),
            MacroSpecialist(config=config),
            SentimentSpecialist(config=config)
        ]
        
        for specialist in specialists:
            self.meta_agent.register_specialist(specialist)
            self.competition.register_agent(specialist)
    
    def analyze_market(self, market_data: Dict) -> Dict:
        """Get collective analysis of market"""
        return self.meta_agent.aggregate_signals(market_data)
    
    def process_feedback(self, feedback: Dict):
        """Process feedback and update all agents"""
        # Update meta-agent weights
        self.meta_agent.update_weights(feedback)
        
        # Update individual specialists
        for agent_id, agent in self.meta_agent.specialists.items():
            agent.update_performance(feedback)
            agent.learn_from_feedback(feedback)
        
        # Reallocate capital
        self.competition.allocate_capital()
    
    def share_discovery(self, agent_id: str, knowledge_type: str, content: Dict, confidence: float):
        """Share a discovery from one agent"""
        return self.knowledge_transfer.share_knowledge(agent_id, knowledge_type, content, confidence)
    
    def get_collective_status(self) -> Dict:
        """Get status of the entire collective"""
        return {
            'agents': {
                agent_id: agent.get_status()
                for agent_id, agent in self.meta_agent.specialists.items()
            },
            'agent_weights': self.meta_agent.agent_weights,
            'capital_allocation': self.competition.get_allocation_summary(),
            'shared_knowledge': len(self.knowledge_transfer.shared_knowledge),
            'validated_knowledge': len(self.knowledge_transfer.get_validated_knowledge())
        }


# Export all classes
__all__ = [
    'AgentType',
    'AgentSignal',
    'SharedKnowledge',
    'SpecialistAgent',
    'MomentumSpecialist',
    'MeanReversionSpecialist',
    'VolatilitySpecialist',
    'MicrostructureSpecialist',
    'MacroSpecialist',
    'SentimentSpecialist',
    'MetaAgent',
    'AgentCompetition',
    'KnowledgeTransfer',
    'AgentCollective'
]
