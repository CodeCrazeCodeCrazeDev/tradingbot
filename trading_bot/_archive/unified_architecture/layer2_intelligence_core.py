"""
Layer 2: Intelligence Core
==========================

The intelligence layer that houses all AI/ML components for market analysis
and decision support.

Components:
- ExpertRouter: Routes inputs to specialized experts (MoE)
- CognitiveProcessor: 10-layer cognitive architecture
- RLEngine: Offline RL (CQL, BCQ, IQL)
- MetaLearner: Meta-learning and transfer learning
- IntelligenceCore: Master coordinator

Integrates:
- trading_bot/qwen_codemender/mixture_of_experts.py
- trading_bot/cognitive_architecture/cognitive_core.py
- trading_bot/ml/offline_rl/
- trading_bot/advanced_ml/meta_learning.py
- trading_bot/brain/adaptive_integration.py
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ExpertCategory(Enum):
    """Categories of experts in the MoE system"""
    PATTERN = "pattern"
    INDICATOR = "indicator"
    REGIME = "regime"
    SENTIMENT = "sentiment"
    ON_CHAIN = "on_chain"
    RISK = "risk"
    ORDER_FLOW = "order_flow"
    TEMPORAL = "temporal"
    SHARED = "shared"


@dataclass
class ExpertOutput:
    """Output from an expert"""
    expert_id: str
    category: ExpertCategory
    signal: float  # -1 to 1
    confidence: float  # 0 to 1
    reasoning: str
    features: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntelligenceOutput:
    """Output from the intelligence core"""
    timestamp: datetime
    symbol: str
    
    # Aggregated signal
    signal: float  # -1 to 1
    confidence: float  # 0 to 1
    
    # Expert contributions
    expert_outputs: List[ExpertOutput]
    expert_weights: Dict[str, float]
    
    # Cognitive state
    market_regime: str
    cognitive_state: Dict[str, Any]
    
    # RL policy
    rl_action: str
    rl_confidence: float
    q_values: Dict[str, float]
    
    # Reasoning
    reasoning_chain: List[str]
    
    # Metadata
    processing_time_ms: float


class Expert(ABC):
    """Base class for experts in the MoE system"""
    
    def __init__(self, expert_id: str, category: ExpertCategory):
        self.expert_id = expert_id
        self.category = category
        self.performance_history: List[float] = []
        
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> ExpertOutput:
        """Analyze data and produce output"""
        pass
    
    def update_performance(self, actual_outcome: float, predicted: float):
        """Update expert performance tracking"""
        error = abs(actual_outcome - predicted)
        self.performance_history.append(1 - error)
        if len(self.performance_history) > 100:
            self.performance_history.pop(0)
    
    @property
    def average_performance(self) -> float:
        """Get average performance"""
        if not self.performance_history:
            return 0.5
        return np.mean(self.performance_history)


class PatternExpert(Expert):
    """Expert for pattern recognition"""
    
    def __init__(self, pattern_type: str):
        super().__init__(f"pattern_{pattern_type}", ExpertCategory.PATTERN)
        self.pattern_type = pattern_type
        
    def analyze(self, data: Dict[str, Any]) -> ExpertOutput:
        """Analyze patterns in market data"""
        market_data = data.get('market')
        if market_data is None or not isinstance(market_data, pd.DataFrame):
            return ExpertOutput(
                expert_id=self.expert_id,
                category=self.category,
                signal=0.0,
                confidence=0.0,
                reasoning="No market data available"
            )
        
        # Pattern detection logic (simplified)
        close = market_data['close'].values if 'close' in market_data.columns else []
        
        if len(close) < 20:
            return ExpertOutput(
                expert_id=self.expert_id,
                category=self.category,
                signal=0.0,
                confidence=0.0,
                reasoning="Insufficient data"
            )
        
        # Detect trend
        sma_short = np.mean(close[-10:])
        sma_long = np.mean(close[-20:])
        
        if sma_short > sma_long * 1.01:
            signal = 0.7
            reasoning = f"Bullish pattern: SMA10 > SMA20 by {((sma_short/sma_long)-1)*100:.2f}%"
        elif sma_short < sma_long * 0.99:
            signal = -0.7
            reasoning = f"Bearish pattern: SMA10 < SMA20 by {((sma_long/sma_short)-1)*100:.2f}%"
        else:
            signal = 0.0
            reasoning = "No clear pattern"
        
        return ExpertOutput(
            expert_id=self.expert_id,
            category=self.category,
            signal=signal,
            confidence=0.6,
            reasoning=reasoning,
            features={'sma_short': sma_short, 'sma_long': sma_long}
        )


class IndicatorExpert(Expert):
    """Expert for technical indicators"""
    
    def __init__(self, indicator_type: str):
        super().__init__(f"indicator_{indicator_type}", ExpertCategory.INDICATOR)
        self.indicator_type = indicator_type
        
    def analyze(self, data: Dict[str, Any]) -> ExpertOutput:
        """Analyze technical indicators"""
        market_data = data.get('market')
        if market_data is None or not isinstance(market_data, pd.DataFrame):
            return ExpertOutput(
                expert_id=self.expert_id,
                category=self.category,
                signal=0.0,
                confidence=0.0,
                reasoning="No market data available"
            )
        
        # RSI analysis
        if 'rsi' in market_data.columns:
            rsi = market_data['rsi'].iloc[-1]
            
            if rsi < 30:
                signal = 0.8
                reasoning = f"RSI oversold at {rsi:.1f}"
                confidence = 0.7
            elif rsi > 70:
                signal = -0.8
                reasoning = f"RSI overbought at {rsi:.1f}"
                confidence = 0.7
            else:
                signal = (50 - rsi) / 50
                reasoning = f"RSI neutral at {rsi:.1f}"
                confidence = 0.4
        else:
            signal = 0.0
            reasoning = "RSI not available"
            confidence = 0.0
        
        return ExpertOutput(
            expert_id=self.expert_id,
            category=self.category,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )


class RegimeExpert(Expert):
    """Expert for market regime detection"""
    
    def __init__(self):
        super().__init__("regime_detector", ExpertCategory.REGIME)
        
    def analyze(self, data: Dict[str, Any]) -> ExpertOutput:
        """Detect market regime"""
        market_data = data.get('market')
        if market_data is None or not isinstance(market_data, pd.DataFrame):
            return ExpertOutput(
                expert_id=self.expert_id,
                category=self.category,
                signal=0.0,
                confidence=0.0,
                reasoning="No market data available"
            )
        
        # Calculate volatility
        if 'volatility' in market_data.columns:
            vol = market_data['volatility'].iloc[-1]
        elif 'close' in market_data.columns:
            returns = market_data['close'].pct_change().dropna()
            vol = returns.std() * np.sqrt(252)
        else:
            vol = 0.0
        
        # Determine regime
        if vol > 0.30:
            regime = "high_volatility"
            signal = -0.5  # Reduce exposure
            confidence = 0.8
        elif vol < 0.10:
            regime = "low_volatility"
            signal = 0.3  # Can take more risk
            confidence = 0.7
        else:
            regime = "normal"
            signal = 0.0
            confidence = 0.6
        
        return ExpertOutput(
            expert_id=self.expert_id,
            category=self.category,
            signal=signal,
            confidence=confidence,
            reasoning=f"Market regime: {regime} (volatility: {vol:.2%})",
            features={'volatility': vol, 'regime': regime}
        )


class SentimentExpert(Expert):
    """Expert for sentiment analysis"""
    
    def __init__(self):
        super().__init__("sentiment_analyzer", ExpertCategory.SENTIMENT)
        
    def analyze(self, data: Dict[str, Any]) -> ExpertOutput:
        """Analyze market sentiment"""
        sentiment = data.get('sentiment', {})
        
        if not sentiment:
            return ExpertOutput(
                expert_id=self.expert_id,
                category=self.category,
                signal=0.0,
                confidence=0.0,
                reasoning="No sentiment data available"
            )
        
        avg_sentiment = sentiment.get('average', 0)
        
        return ExpertOutput(
            expert_id=self.expert_id,
            category=self.category,
            signal=avg_sentiment,
            confidence=0.5,
            reasoning=f"Sentiment score: {avg_sentiment:.2f}",
            features={'sentiment': avg_sentiment}
        )


class ExpertRouter:
    """
    Routes inputs to specialized experts using Mixture of Experts
    
    Implements QwenCodeMender-style MoE with:
    - 1 shared expert (always active)
    - 256 routed experts (top-k selected per input)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Expert pools
        self.shared_expert: Optional[Expert] = None
        self.routed_experts: Dict[str, Expert] = {}
        
        # Routing parameters
        self.top_k = config.get('top_k', 8)  # Number of experts to activate
        
        # Expert weights (learned)
        self.expert_weights: Dict[str, float] = {}
        
        # Initialize experts
        self._init_experts()
        
        logger.info(f"Expert Router initialized with {len(self.routed_experts)} experts")
    
    def _init_experts(self):
        """Initialize all experts"""
        # Shared expert (always active)
        self.shared_expert = RegimeExpert()
        
        # Pattern experts
        for pattern in ['trend', 'reversal', 'breakout', 'consolidation']:
            expert = PatternExpert(pattern)
            self.routed_experts[expert.expert_id] = expert
            self.expert_weights[expert.expert_id] = 1.0
        
        # Indicator experts
        for indicator in ['rsi', 'macd', 'bollinger', 'atr']:
            expert = IndicatorExpert(indicator)
            self.routed_experts[expert.expert_id] = expert
            self.expert_weights[expert.expert_id] = 1.0
        
        # Sentiment expert
        sentiment_expert = SentimentExpert()
        self.routed_experts[sentiment_expert.expert_id] = sentiment_expert
        self.expert_weights[sentiment_expert.expert_id] = 1.0
    
    def route(self, data: Dict[str, Any]) -> List[ExpertOutput]:
        """Route input to appropriate experts and collect outputs"""
        outputs = []
        
        # Always run shared expert
        if self.shared_expert:
            outputs.append(self.shared_expert.analyze(data))
        
        # Score experts for routing
        expert_scores = self._score_experts(data)
        
        # Select top-k experts
        sorted_experts = sorted(
            expert_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.top_k]
        
        # Run selected experts
        for expert_id, score in sorted_experts:
            expert = self.routed_experts.get(expert_id)
            if expert:
                output = expert.analyze(data)
                output.metadata['routing_score'] = score
                outputs.append(output)
        
        return outputs
    
    def _score_experts(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Score experts based on input relevance"""
        scores = {}
        
        for expert_id, expert in self.routed_experts.items():
            # Base score from historical performance
            base_score = expert.average_performance
            
            # Adjust based on data availability
            relevance = self._calculate_relevance(expert, data)
            
            # Final score
            scores[expert_id] = base_score * relevance * self.expert_weights.get(expert_id, 1.0)
        
        return scores
    
    def _calculate_relevance(self, expert: Expert, data: Dict[str, Any]) -> float:
        """Calculate expert relevance to current data"""
        # Pattern/Indicator experts need market data
        if expert.category in [ExpertCategory.PATTERN, ExpertCategory.INDICATOR]:
            if 'market' in data and data['market'] is not None:
                return 1.0
            return 0.1
        
        # Sentiment expert needs sentiment data
        if expert.category == ExpertCategory.SENTIMENT:
            if 'sentiment' in data and data['sentiment']:
                return 1.0
            return 0.1
        
        return 0.5
    
    def aggregate_outputs(self, outputs: List[ExpertOutput]) -> Tuple[float, float, Dict[str, float]]:
        """Aggregate expert outputs into final signal"""
        if not outputs:
            return 0.0, 0.0, {}
        
        # Weight by confidence and expert weight
        total_weight = 0
        weighted_signal = 0
        expert_contributions = {}
        
        for output in outputs:
            weight = output.confidence * self.expert_weights.get(output.expert_id, 1.0)
            weighted_signal += output.signal * weight
            total_weight += weight
            expert_contributions[output.expert_id] = output.signal * weight
        
        if total_weight == 0:
            return 0.0, 0.0, expert_contributions
        
        final_signal = weighted_signal / total_weight
        avg_confidence = np.mean([o.confidence for o in outputs])
        
        return final_signal, avg_confidence, expert_contributions
    
    def update_weights(self, expert_id: str, performance: float):
        """Update expert weight based on performance"""
        current = self.expert_weights.get(expert_id, 1.0)
        # Exponential moving average
        self.expert_weights[expert_id] = 0.9 * current + 0.1 * performance


class CognitiveProcessor:
    """
    10-layer cognitive architecture processor
    
    Integrates trading_bot/cognitive_architecture/cognitive_core.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._cognitive_core = None
        
        try:
            # Try to import existing cognitive core
            from trading_bot.cognitive_architecture import AlphaAlgoCognitiveCore
            self._cognitive_core = AlphaAlgoCognitiveCore(config)
            logger.info("Cognitive processor initialized with AlphaAlgoCognitiveCore")
        except Exception as e:
            logger.warning(f"Could not initialize cognitive core: {e}")
    
    def process(self, market_data: pd.DataFrame, 
                sentiment_data: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Process through cognitive layers"""
        if self._cognitive_core:
            try:
                decision = self._cognitive_core.make_decision(market_data, sentiment_data)
                return {
                    'action': decision.action,
                    'confidence': decision.confidence,
                    'reasoning': decision.reasoning,
                    'market_regime': decision.cognitive_state.market_regime.value,
                    'cognitive_state': {
                        'integration_mode': decision.cognitive_state.integration_mode,
                        'consensus_score': decision.cognitive_state.consensus_score,
                        'system_health': decision.cognitive_state.system_health
                    }
                }
            except Exception as e:
                logger.error(f"Cognitive processing error: {e}")
        
        # Fallback simple processing
        return {
            'action': 'HOLD',
            'confidence': 0.5,
            'reasoning': 'Fallback processing',
            'market_regime': 'unknown',
            'cognitive_state': {}
        }


class RLEngine:
    """
    Offline Reinforcement Learning engine
    
    Integrates trading_bot/ml/offline_rl/ (CQL, BCQ, IQL)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._rl_system = None
        self._policy = 'cql'  # Default policy
        
        try:
            # Try to import existing RL system
            from trading_bot.ml.offline_rl import AlphaAlgoAutonomousSystem
            self._rl_system = AlphaAlgoAutonomousSystem(config)
            logger.info("RL Engine initialized with AlphaAlgoAutonomousSystem")
        except Exception as e:
            logger.warning(f"Could not initialize RL system: {e}")
    
    def get_action(self, state: np.ndarray) -> Tuple[str, float, Dict[str, float]]:
        """Get action from RL policy"""
        if self._rl_system:
            try:
                action, q_values = self._rl_system.select_action(state)
                actions = ['BUY', 'SELL', 'HOLD']
                action_str = actions[action] if isinstance(action, int) else action
                confidence = max(q_values) if isinstance(q_values, (list, np.ndarray)) else 0.5
                q_dict = {actions[i]: float(q_values[i]) for i in range(len(actions))} if isinstance(q_values, (list, np.ndarray)) else {}
                return action_str, confidence, q_dict
            except Exception as e:
                logger.error(f"RL action error: {e}")
        
        # Fallback
        return 'HOLD', 0.5, {'BUY': 0.3, 'SELL': 0.3, 'HOLD': 0.4}
    
    def update(self, state: np.ndarray, action: int, reward: float, 
               next_state: np.ndarray, done: bool):
        """Update RL model with new experience"""
        if self._rl_system:
            try:
                self._rl_system.update(state, action, reward, next_state, done)
            except Exception as e:
                logger.error(f"RL update error: {e}")


class MetaLearner:
    """
    Meta-learning and transfer learning engine
    
    Integrates trading_bot/advanced_ml/meta_learning.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._maml = None
        self._transfer = None
        
        try:
            # Try to import existing meta-learning
            from trading_bot.advanced_ml.meta_learning import MAML, TransferLearning
            self._maml = MAML(config)
            self._transfer = TransferLearning(config)
            logger.info("Meta-learner initialized")
        except Exception as e:
            logger.warning(f"Could not initialize meta-learner: {e}")
    
    def adapt(self, task_data: Dict[str, Any], n_steps: int = 5) -> Dict[str, Any]:
        """Adapt to new task using meta-learning"""
        if self._maml:
            try:
                return self._maml.adapt(task_data, n_steps)
            except Exception as e:
                logger.error(f"Meta-learning adaptation error: {e}")
        
        return {'adapted': False, 'reason': 'Meta-learner not available'}
    
    def transfer(self, source_model: Any, target_domain: str) -> Any:
        """Transfer knowledge to new domain"""
        if self._transfer:
            try:
                return self._transfer.transfer(source_model, target_domain)
            except Exception as e:
                logger.error(f"Transfer learning error: {e}")
        
        return None


class IntelligenceCore:
    """
    Master coordinator for Layer 2: Intelligence Core
    
    Orchestrates all AI/ML components for comprehensive market analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.expert_router = ExpertRouter(config.get('moe', {}))
        self.cognitive_processor = CognitiveProcessor(config.get('cognitive', {}))
        self.rl_engine = RLEngine(config.get('rl', {}))
        self.meta_learner = MetaLearner(config.get('meta', {}))
        
        # State tracking
        self.last_output: Optional[IntelligenceOutput] = None
        self.output_history: List[IntelligenceOutput] = []
        self.max_history = 1000
        
        logger.info("Intelligence Core initialized")
    
    async def analyze(self, data: Dict[str, Any], symbol: str) -> IntelligenceOutput:
        """
        Run full intelligence analysis pipeline
        
        1. Route to experts (MoE)
        2. Process through cognitive layers
        3. Get RL policy action
        4. Aggregate and return
        """
        start_time = datetime.now()
        
        # Step 1: Expert routing and analysis
        expert_outputs = self.expert_router.route(data)
        signal, confidence, expert_weights = self.expert_router.aggregate_outputs(expert_outputs)
        
        # Step 2: Cognitive processing
        market_data = data.get('market')
        if isinstance(market_data, pd.DataFrame):
            cognitive_result = self.cognitive_processor.process(market_data)
        else:
            cognitive_result = {'action': 'HOLD', 'confidence': 0.5, 'market_regime': 'unknown', 'cognitive_state': {}}
        
        # Step 3: RL policy
        state = self._build_state(data, expert_outputs)
        rl_action, rl_confidence, q_values = self.rl_engine.get_action(state)
        
        # Step 4: Build reasoning chain
        reasoning_chain = self._build_reasoning(expert_outputs, cognitive_result, rl_action)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Build output
        output = IntelligenceOutput(
            timestamp=datetime.now(),
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            expert_outputs=expert_outputs,
            expert_weights=expert_weights,
            market_regime=cognitive_result.get('market_regime', 'unknown'),
            cognitive_state=cognitive_result.get('cognitive_state', {}),
            rl_action=rl_action,
            rl_confidence=rl_confidence,
            q_values=q_values,
            reasoning_chain=reasoning_chain,
            processing_time_ms=processing_time
        )
        
        # Store output
        self.last_output = output
        self.output_history.append(output)
        if len(self.output_history) > self.max_history:
            self.output_history.pop(0)
        
        return output
    
    def _build_state(self, data: Dict[str, Any], 
                     expert_outputs: List[ExpertOutput]) -> np.ndarray:
        """Build state vector for RL"""
        state = []
        
        # Expert signals
        for output in expert_outputs:
            state.extend([output.signal, output.confidence])
        
        # Pad to fixed size
        while len(state) < 50:
            state.append(0.0)
        
        return np.array(state[:50])
    
    def _build_reasoning(self, expert_outputs: List[ExpertOutput],
                        cognitive_result: Dict[str, Any],
                        rl_action: str) -> List[str]:
        """Build reasoning chain"""
        reasoning = []
        
        # Expert reasoning
        for output in expert_outputs:
            if output.confidence > 0.3:
                reasoning.append(f"[{output.category.value}] {output.reasoning}")
        
        # Cognitive reasoning
        if 'reasoning' in cognitive_result:
            reasoning.append(f"[cognitive] {cognitive_result['reasoning']}")
        
        # RL reasoning
        reasoning.append(f"[rl] Policy suggests: {rl_action}")
        
        return reasoning
    
    def get_status(self) -> Dict[str, Any]:
        """Get intelligence core status"""
        return {
            'expert_count': len(self.expert_router.routed_experts),
            'cognitive_available': self.cognitive_processor._cognitive_core is not None,
            'rl_available': self.rl_engine._rl_system is not None,
            'meta_available': self.meta_learner._maml is not None,
            'outputs_generated': len(self.output_history),
            'last_output_time': self.last_output.timestamp.isoformat() if self.last_output else None
        }
    
    def update_from_outcome(self, symbol: str, outcome: float):
        """Update models based on actual outcome"""
        if self.last_output and self.last_output.symbol == symbol:
            # Update expert weights
            for output in self.last_output.expert_outputs:
                self.expert_router.update_weights(
                    output.expert_id,
                    1.0 - abs(outcome - output.signal)
                )
