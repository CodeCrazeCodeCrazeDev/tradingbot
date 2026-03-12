"""
Cognitive Systems
=================

Advanced cognitive capabilities including:
- Working Memory System
- Attention Mechanisms for Market Focus
- Reasoning Chain Visualization
- Emotion Simulation for Market Psychology
"""

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# WORKING MEMORY SYSTEM
# =============================================================================

class MemoryType(Enum):
    """Types of memory"""
    SENSORY = "sensory"  # Very short-term (seconds)
    SHORT_TERM = "short_term"  # Working memory (minutes)
    LONG_TERM = "long_term"  # Persistent (days/weeks)
    EPISODIC = "episodic"  # Specific events
    SEMANTIC = "semantic"  # General knowledge
    PROCEDURAL = "procedural"  # Skills/procedures


@dataclass
class MemoryItem:
    """A single memory item"""
    memory_id: str
    content: Any
    memory_type: MemoryType
    importance: float = 0.5
    access_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    decay_rate: float = 0.1
    associations: List[str] = field(default_factory=list)
    
    def get_strength(self) -> float:
        """Calculate current memory strength with decay"""
        age = (datetime.utcnow() - self.last_accessed).total_seconds()
        decay = math.exp(-self.decay_rate * age / 3600)  # Hourly decay
        recency_boost = min(1.0, self.access_count * 0.1)
        return self.importance * decay * (1 + recency_boost)


class WorkingMemorySystem:
    """
    Working Memory System
    
    Implements a multi-store memory model with:
    - Sensory buffer (very short-term)
    - Short-term/working memory
    - Long-term memory with consolidation
    - Episodic memory for specific events
    """
    
    def __init__(
        self,
        sensory_capacity: int = 100,
        short_term_capacity: int = 7,  # Miller's magic number
        long_term_capacity: int = 10000,
        consolidation_threshold: float = 0.7
    ):
        self.sensory_capacity = sensory_capacity
        self.short_term_capacity = short_term_capacity
        self.long_term_capacity = long_term_capacity
        self.consolidation_threshold = consolidation_threshold
        
        # Memory stores
        self.sensory_buffer: deque = deque(maxlen=sensory_capacity)
        self.short_term: Dict[str, MemoryItem] = {}
        self.long_term: Dict[str, MemoryItem] = {}
        self.episodic: List[MemoryItem] = []
        
        # Attention focus
        self.attention_focus: List[str] = []
        
        logger.info("WorkingMemorySystem initialized")
    
    def encode(
        self,
        content: Any,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 0.5,
        associations: List[str] = None
    ) -> str:
        """Encode new information into memory"""
        
        memory_id = f"mem_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        item = MemoryItem(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            associations=associations or []
        )
        
        if memory_type == MemoryType.SENSORY:
            self.sensory_buffer.append(item)
        
        elif memory_type == MemoryType.SHORT_TERM:
            # Check capacity
            if len(self.short_term) >= self.short_term_capacity:
                self._consolidate_or_forget()
            self.short_term[memory_id] = item
        
        elif memory_type in [MemoryType.LONG_TERM, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            if len(self.long_term) >= self.long_term_capacity:
                self._prune_long_term()
            self.long_term[memory_id] = item
        
        elif memory_type == MemoryType.EPISODIC:
            self.episodic.append(item)
        
        return memory_id
    
    def retrieve(
        self,
        query: Any = None,
        memory_type: Optional[MemoryType] = None,
        top_k: int = 5
    ) -> List[MemoryItem]:
        """Retrieve memories matching query"""
        
        candidates = []
        
        # Gather candidates from appropriate stores
        if memory_type is None or memory_type == MemoryType.SHORT_TERM:
            candidates.extend(self.short_term.values())
        
        if memory_type is None or memory_type in [MemoryType.LONG_TERM, MemoryType.SEMANTIC]:
            candidates.extend(self.long_term.values())
        
        if memory_type is None or memory_type == MemoryType.EPISODIC:
            candidates.extend(self.episodic)
        
        # Score by relevance and strength
        scored = []
        for item in candidates:
            strength = item.get_strength()
            relevance = self._compute_relevance(item, query) if query else 1.0
            score = strength * relevance
            scored.append((item, score))
        
        # Sort and return top-k
        scored.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for item, _ in scored[:top_k]:
            item.access_count += 1
            item.last_accessed = datetime.utcnow()
            results.append(item)
        
        return results
    
    def _compute_relevance(self, item: MemoryItem, query: Any) -> float:
        """Compute relevance of memory to query"""
        
        # Simple string matching for now
        if isinstance(query, str) and isinstance(item.content, str):
            query_words = set(query.lower().split())
            content_words = set(item.content.lower().split())
            
            if not query_words:
                return 0.0
            
            overlap = len(query_words & content_words)
            return overlap / len(query_words)
        
        # Check associations
        if isinstance(query, str) and query in item.associations:
            return 1.0
        
        return 0.5  # Default moderate relevance
    
    def _consolidate_or_forget(self):
        """Consolidate important memories to long-term or forget"""
        
        # Find weakest short-term memory
        if not self.short_term:
            return
        
        weakest_id = min(
            self.short_term.keys(),
            key=lambda k: self.short_term[k].get_strength()
        )
        
        item = self.short_term[weakest_id]
        
        # Consolidate if important enough
        if item.importance >= self.consolidation_threshold:
            item.memory_type = MemoryType.LONG_TERM
            item.decay_rate *= 0.1  # Slower decay in long-term
            self.long_term[weakest_id] = item
            logger.debug(f"Consolidated memory {weakest_id} to long-term")
        
        del self.short_term[weakest_id]
    
    def _prune_long_term(self):
        """Remove weakest long-term memories"""
        
        if len(self.long_term) < self.long_term_capacity:
            return
        
        # Remove bottom 10%
        items = list(self.long_term.items())
        items.sort(key=lambda x: x[1].get_strength())
        
        to_remove = len(items) // 10
        for memory_id, _ in items[:to_remove]:
            del self.long_term[memory_id]
    
    def focus_attention(self, memory_ids: List[str]):
        """Focus attention on specific memories"""
        self.attention_focus = memory_ids
        
        # Boost importance of focused memories
        for memory_id in memory_ids:
            if memory_id in self.short_term:
                self.short_term[memory_id].importance *= 1.2
            if memory_id in self.long_term:
                self.long_term[memory_id].importance *= 1.1
    
    def get_context(self, max_items: int = 10) -> List[MemoryItem]:
        """Get current working memory context"""
        
        # Prioritize focused items
        context = []
        
        for memory_id in self.attention_focus:
            if memory_id in self.short_term:
                context.append(self.short_term[memory_id])
            elif memory_id in self.long_term:
                context.append(self.long_term[memory_id])
        
        # Fill with strongest short-term memories
        remaining = max_items - len(context)
        if remaining > 0:
            stm_items = sorted(
                self.short_term.values(),
                key=lambda x: x.get_strength(),
                reverse=True
            )
            for item in stm_items[:remaining]:
                if item not in context:
                    context.append(item)
        
        return context
    
    def store_episode(
        self,
        event_type: str,
        details: Dict[str, Any],
        outcome: Optional[str] = None
    ) -> str:
        """Store an episodic memory (specific event)"""
        
        content = {
            'event_type': event_type,
            'details': details,
            'outcome': outcome,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return self.encode(
            content,
            memory_type=MemoryType.EPISODIC,
            importance=0.7
        )
    
    def recall_similar_episodes(
        self,
        event_type: str,
        top_k: int = 5
    ) -> List[MemoryItem]:
        """Recall similar past episodes"""
        
        similar = []
        
        for episode in self.episodic:
            if isinstance(episode.content, dict):
                if episode.content.get('event_type') == event_type:
                    similar.append(episode)
        
        # Sort by recency and strength
        similar.sort(key=lambda x: x.get_strength(), reverse=True)
        
        return similar[:top_k]


# =============================================================================
# ATTENTION MECHANISMS
# =============================================================================

@dataclass
class AttentionWeight:
    """Attention weight for a feature/asset"""
    target: str
    weight: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MarketAttentionSystem:
    """
    Attention Mechanisms for Market Focus
    
    Dynamically allocates attention to different:
    - Assets/symbols
    - Timeframes
    - Market features
    - News/events
    """
    
    def __init__(
        self,
        num_heads: int = 4,
        attention_decay: float = 0.95
    ):
        self.num_heads = num_heads
        self.attention_decay = attention_decay
        
        # Attention weights by category
        self.symbol_attention: Dict[str, float] = {}
        self.timeframe_attention: Dict[str, float] = {}
        self.feature_attention: Dict[str, float] = {}
        self.event_attention: Dict[str, float] = {}
        
        # Attention history
        self.attention_history: List[AttentionWeight] = []
        
        logger.info("MarketAttentionSystem initialized")
    
    def compute_attention(
        self,
        queries: np.ndarray,
        keys: np.ndarray,
        values: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute scaled dot-product attention
        
        Args:
            queries: Query vectors (batch, seq, dim)
            keys: Key vectors (batch, seq, dim)
            values: Value vectors (batch, seq, dim)
            mask: Optional attention mask
        
        Returns:
            Attended values and attention weights
        """
        
        d_k = queries.shape[-1]
        
        # Compute attention scores
        scores = np.matmul(queries, keys.transpose(-2, -1)) / math.sqrt(d_k)
        
        # Apply mask if provided
        if mask is not None:
            scores = np.where(mask, scores, -1e9)
        
        # Softmax
        attention_weights = self._softmax(scores)
        
        # Apply attention to values
        attended = np.matmul(attention_weights, values)
        
        return attended, attention_weights
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax"""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    def update_symbol_attention(
        self,
        symbol: str,
        importance: float,
        reason: str
    ):
        """Update attention weight for a symbol"""
        
        # Decay existing weights
        for s in self.symbol_attention:
            self.symbol_attention[s] *= self.attention_decay
        
        # Update target symbol
        current = self.symbol_attention.get(symbol, 0.0)
        self.symbol_attention[symbol] = min(1.0, current + importance)
        
        # Record
        self.attention_history.append(AttentionWeight(
            target=symbol,
            weight=self.symbol_attention[symbol],
            reason=reason
        ))
    
    def update_feature_attention(
        self,
        feature: str,
        importance: float,
        reason: str
    ):
        """Update attention weight for a feature"""
        
        for f in self.feature_attention:
            self.feature_attention[f] *= self.attention_decay
        
        current = self.feature_attention.get(feature, 0.0)
        self.feature_attention[feature] = min(1.0, current + importance)
    
    def get_top_attention(
        self,
        category: str = "symbol",
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Get top attention targets"""
        
        if category == "symbol":
            weights = self.symbol_attention
        elif category == "timeframe":
            weights = self.timeframe_attention
        elif category == "feature":
            weights = self.feature_attention
        elif category == "event":
            weights = self.event_attention
        else:
            weights = {}
        
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        return sorted_weights[:top_k]
    
    def should_focus(self, target: str, category: str = "symbol") -> bool:
        """Check if target deserves focus"""
        
        if category == "symbol":
            weights = self.symbol_attention
        elif category == "feature":
            weights = self.feature_attention
        else:
            return False
        
        weight = weights.get(target, 0.0)
        threshold = np.mean(list(weights.values())) if weights else 0.5
        
        return weight > threshold
    
    def multi_head_attention(
        self,
        market_data: Dict[str, np.ndarray],
        query_features: List[str]
    ) -> Dict[str, float]:
        """
        Apply multi-head attention across market features
        
        Returns attention-weighted importance scores
        """
        
        importance_scores = {}
        
        for feature in query_features:
            if feature not in market_data:
                continue
            
            data = market_data[feature]
            
            # Compute feature importance using self-attention
            if len(data) > 1:
                # Recent values get more attention
                recency_weights = np.exp(np.linspace(-1, 0, len(data)))
                recency_weights /= recency_weights.sum()
                
                # Volatility-based attention
                volatility = np.std(data[-20:]) if len(data) >= 20 else np.std(data)
                vol_weight = min(1.0, volatility / (np.mean(np.abs(data)) + 1e-10))
                
                # Trend-based attention
                if len(data) >= 5:
                    trend = (data[-1] - data[-5]) / (np.abs(data[-5]) + 1e-10)
                    trend_weight = min(1.0, abs(trend))
                else:
                    trend_weight = 0.0
                
                importance_scores[feature] = (vol_weight + trend_weight) / 2
            else:
                importance_scores[feature] = 0.5
        
        # Normalize
        total = sum(importance_scores.values())
        if total > 0:
            importance_scores = {k: v / total for k, v in importance_scores.items()}
        
        return importance_scores


# =============================================================================
# REASONING CHAIN VISUALIZATION
# =============================================================================

@dataclass
class ReasoningStep:
    """A single step in the reasoning chain"""
    step_id: int
    description: str
    inputs: List[str]
    output: Any
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ReasoningChain:
    """
    Reasoning Chain Visualization
    
    Tracks and visualizes the decision-making process
    for explainability and debugging.
    """
    
    def __init__(self):
        self.steps: List[ReasoningStep] = []
        self.current_step = 0
        self.final_decision: Optional[str] = None
        self.final_confidence: float = 0.0
        
        logger.info("ReasoningChain initialized")
    
    def add_step(
        self,
        description: str,
        inputs: List[str],
        output: Any,
        confidence: float
    ) -> int:
        """Add a reasoning step"""
        
        step = ReasoningStep(
            step_id=self.current_step,
            description=description,
            inputs=inputs,
            output=output,
            confidence=confidence
        )
        
        self.steps.append(step)
        self.current_step += 1
        
        return step.step_id
    
    def set_conclusion(self, decision: str, confidence: float):
        """Set the final conclusion"""
        self.final_decision = decision
        self.final_confidence = confidence
    
    def get_explanation(self) -> str:
        """Generate natural language explanation"""
        
        if not self.steps:
            return "No reasoning steps recorded."
        
        lines = ["## Reasoning Chain\n"]
        
        for step in self.steps:
            lines.append(f"**Step {step.step_id + 1}**: {step.description}")
            lines.append(f"  - Inputs: {', '.join(step.inputs)}")
            lines.append(f"  - Output: {step.output}")
            lines.append(f"  - Confidence: {step.confidence:.1%}")
            lines.append("")
        
        if self.final_decision:
            lines.append(f"**Conclusion**: {self.final_decision}")
            lines.append(f"**Overall Confidence**: {self.final_confidence:.1%}")
        
        return '\n'.join(lines)
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for visualization"""
        
        nodes = []
        edges = []
        
        for i, step in enumerate(self.steps):
            nodes.append({
                'id': f"step_{step.step_id}",
                'label': step.description[:30] + "..." if len(step.description) > 30 else step.description,
                'confidence': step.confidence,
                'type': 'step'
            })
            
            # Connect to previous step
            if i > 0:
                edges.append({
                    'from': f"step_{self.steps[i-1].step_id}",
                    'to': f"step_{step.step_id}"
                })
        
        # Add conclusion node
        if self.final_decision:
            nodes.append({
                'id': 'conclusion',
                'label': self.final_decision,
                'confidence': self.final_confidence,
                'type': 'conclusion'
            })
            
            if self.steps:
                edges.append({
                    'from': f"step_{self.steps[-1].step_id}",
                    'to': 'conclusion'
                })
        
        return {'nodes': nodes, 'edges': edges}
    
    def reset(self):
        """Reset the reasoning chain"""
        self.steps = []
        self.current_step = 0
        self.final_decision = None
        self.final_confidence = 0.0


# =============================================================================
# EMOTION SIMULATION FOR MARKET PSYCHOLOGY
# =============================================================================

class MarketEmotion(Enum):
    """Market emotion states"""
    EUPHORIA = "euphoria"
    GREED = "greed"
    OPTIMISM = "optimism"
    NEUTRAL = "neutral"
    ANXIETY = "anxiety"
    FEAR = "fear"
    PANIC = "panic"
    CAPITULATION = "capitulation"
    DEPRESSION = "depression"


@dataclass
class EmotionState:
    """Current emotional state of the market"""
    primary_emotion: MarketEmotion
    intensity: float  # 0-1
    fear_greed_index: float  # 0-100
    sentiment_score: float  # -1 to 1
    volatility_stress: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MarketPsychologySimulator:
    """
    Emotion Simulation for Market Psychology
    
    Models market psychology and crowd behavior
    to anticipate emotional extremes and reversals.
    """
    
    def __init__(self):
        self.emotion_history: List[EmotionState] = []
        self.current_state: Optional[EmotionState] = None
        
        # Emotion thresholds
        self.fear_greed_thresholds = {
            MarketEmotion.EUPHORIA: (90, 100),
            MarketEmotion.GREED: (70, 90),
            MarketEmotion.OPTIMISM: (55, 70),
            MarketEmotion.NEUTRAL: (45, 55),
            MarketEmotion.ANXIETY: (30, 45),
            MarketEmotion.FEAR: (15, 30),
            MarketEmotion.PANIC: (5, 15),
            MarketEmotion.CAPITULATION: (0, 5)
        }
        
        logger.info("MarketPsychologySimulator initialized")
    
    def analyze_market_psychology(
        self,
        price_data: np.ndarray,
        volume_data: Optional[np.ndarray] = None,
        sentiment_data: Optional[float] = None,
        vix_data: Optional[float] = None
    ) -> EmotionState:
        """
        Analyze current market psychology
        
        Args:
            price_data: Recent price data
            volume_data: Recent volume data
            sentiment_data: External sentiment score (-1 to 1)
            vix_data: VIX or volatility index value
        
        Returns:
            Current emotional state
        """
        
        # Calculate fear/greed components
        components = {}
        
        # 1. Price momentum
        if len(price_data) >= 20:
            returns = np.diff(price_data) / price_data[:-1]
            momentum = np.mean(returns[-20:]) * 100
            components['momentum'] = self._normalize_score(momentum, -5, 5)
        else:
            components['momentum'] = 50
        
        # 2. Volatility
        if len(price_data) >= 20:
            volatility = np.std(price_data[-20:]) / np.mean(price_data[-20:])
            # High volatility = fear
            components['volatility'] = 100 - self._normalize_score(volatility, 0, 0.1) * 100
        else:
            components['volatility'] = 50
        
        # 3. Volume analysis
        if volume_data is not None and len(volume_data) >= 20:
            vol_ratio = volume_data[-1] / np.mean(volume_data[-20:])
            # High volume with price drop = fear, with price rise = greed
            price_direction = 1 if price_data[-1] > price_data[-2] else -1
            components['volume'] = 50 + (vol_ratio - 1) * 20 * price_direction
            components['volume'] = np.clip(components['volume'], 0, 100)
        else:
            components['volume'] = 50
        
        # 4. External sentiment
        if sentiment_data is not None:
            components['sentiment'] = (sentiment_data + 1) * 50  # Convert -1,1 to 0,100
        else:
            components['sentiment'] = 50
        
        # 5. VIX/Volatility index
        if vix_data is not None:
            # VIX > 30 = fear, VIX < 15 = greed
            components['vix'] = 100 - self._normalize_score(vix_data, 10, 40) * 100
        else:
            components['vix'] = 50
        
        # Calculate weighted fear/greed index
        weights = {
            'momentum': 0.25,
            'volatility': 0.20,
            'volume': 0.15,
            'sentiment': 0.25,
            'vix': 0.15
        }
        
        fear_greed_index = sum(
            components[k] * weights[k]
            for k in components
        )
        
        # Determine primary emotion
        primary_emotion = self._index_to_emotion(fear_greed_index)
        
        # Calculate intensity
        intensity = abs(fear_greed_index - 50) / 50
        
        # Calculate sentiment score
        sentiment_score = (fear_greed_index - 50) / 50
        
        # Calculate volatility stress
        volatility_stress = 1 - components.get('volatility', 50) / 100
        
        state = EmotionState(
            primary_emotion=primary_emotion,
            intensity=intensity,
            fear_greed_index=fear_greed_index,
            sentiment_score=sentiment_score,
            volatility_stress=volatility_stress
        )
        
        self.current_state = state
        self.emotion_history.append(state)
        
        return state
    
    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range"""
        return np.clip((value - min_val) / (max_val - min_val), 0, 1)
    
    def _index_to_emotion(self, index: float) -> MarketEmotion:
        """Convert fear/greed index to emotion"""
        
        for emotion, (low, high) in self.fear_greed_thresholds.items():
            if low <= index < high:
                return emotion
        
        return MarketEmotion.NEUTRAL
    
    def detect_emotional_extreme(self) -> Optional[str]:
        """Detect if market is at emotional extreme"""
        
        if not self.current_state:
            return None
        
        if self.current_state.fear_greed_index >= 85:
            return "EXTREME_GREED"
        elif self.current_state.fear_greed_index <= 15:
            return "EXTREME_FEAR"
        elif self.current_state.intensity >= 0.8:
            return f"HIGH_INTENSITY_{self.current_state.primary_emotion.value.upper()}"
        
        return None
    
    def predict_reversal_probability(self) -> float:
        """Predict probability of sentiment reversal"""
        
        if len(self.emotion_history) < 5:
            return 0.5
        
        recent = self.emotion_history[-5:]
        
        # Check for sustained extreme
        extreme_count = sum(
            1 for s in recent
            if s.fear_greed_index >= 80 or s.fear_greed_index <= 20
        )
        
        # Check for increasing intensity
        intensities = [s.intensity for s in recent]
        intensity_trend = np.polyfit(range(len(intensities)), intensities, 1)[0]
        
        # Higher probability of reversal at extremes with increasing intensity
        base_prob = 0.3
        extreme_factor = extreme_count / 5 * 0.3
        intensity_factor = max(0, intensity_trend) * 0.2
        
        return min(0.9, base_prob + extreme_factor + intensity_factor)
    
    def get_contrarian_signal(self) -> Optional[Dict[str, Any]]:
        """Generate contrarian signal based on psychology"""
        
        if not self.current_state:
            return None
        
        extreme = self.detect_emotional_extreme()
        reversal_prob = self.predict_reversal_probability()
        
        if extreme and reversal_prob > 0.6:
            if "GREED" in extreme or "EUPHORIA" in extreme:
                return {
                    'signal': 'SELL',
                    'reason': f"Extreme greed detected (FGI: {self.current_state.fear_greed_index:.0f})",
                    'confidence': reversal_prob,
                    'emotion': self.current_state.primary_emotion.value
                }
            elif "FEAR" in extreme or "PANIC" in extreme:
                return {
                    'signal': 'BUY',
                    'reason': f"Extreme fear detected (FGI: {self.current_state.fear_greed_index:.0f})",
                    'confidence': reversal_prob,
                    'emotion': self.current_state.primary_emotion.value
                }
        
        return None
    
    def get_psychology_report(self) -> Dict[str, Any]:
        """Get comprehensive psychology report"""
        
        if not self.current_state:
            return {'status': 'No data available'}
        
        return {
            'current_emotion': self.current_state.primary_emotion.value,
            'intensity': self.current_state.intensity,
            'fear_greed_index': self.current_state.fear_greed_index,
            'sentiment_score': self.current_state.sentiment_score,
            'volatility_stress': self.current_state.volatility_stress,
            'extreme_detected': self.detect_emotional_extreme(),
            'reversal_probability': self.predict_reversal_probability(),
            'contrarian_signal': self.get_contrarian_signal(),
            'history_length': len(self.emotion_history)
        }


# =============================================================================
# INTEGRATED COGNITIVE SYSTEM
# =============================================================================

class IntegratedCognitiveSystem:
    """
    Integrated Cognitive System
    
    Combines all cognitive components for unified
    market analysis and decision making.
    """
    
    def __init__(self):
        self.memory = WorkingMemorySystem()
        self.attention = MarketAttentionSystem()
        self.reasoning = ReasoningChain()
        self.psychology = MarketPsychologySimulator()
        
        logger.info("IntegratedCognitiveSystem initialized")
    
    def process_market_data(
        self,
        market_data: Dict[str, np.ndarray],
        symbol: str
    ) -> Dict[str, Any]:
        """
        Process market data through cognitive pipeline
        
        Returns comprehensive analysis with reasoning chain
        """
        
        self.reasoning.reset()
        
        # Step 1: Attention allocation
        attention_scores = self.attention.multi_head_attention(
            market_data,
            list(market_data.keys())
        )
        
        self.reasoning.add_step(
            "Allocate attention to market features",
            list(market_data.keys()),
            f"Top features: {sorted(attention_scores.items(), key=lambda x: x[1], reverse=True)[:3]}",
            0.9
        )
        
        # Step 2: Memory retrieval
        similar_episodes = self.memory.recall_similar_episodes(
            f"market_analysis_{symbol}",
            top_k=3
        )
        
        self.reasoning.add_step(
            "Retrieve similar past episodes",
            [symbol],
            f"Found {len(similar_episodes)} similar episodes",
            0.8
        )
        
        # Step 3: Psychology analysis
        price_data = market_data.get('close', market_data.get('price', np.array([100])))
        volume_data = market_data.get('volume')
        
        emotion_state = self.psychology.analyze_market_psychology(
            price_data,
            volume_data
        )
        
        self.reasoning.add_step(
            "Analyze market psychology",
            ['price', 'volume'],
            f"Emotion: {emotion_state.primary_emotion.value}, FGI: {emotion_state.fear_greed_index:.0f}",
            0.85
        )
        
        # Step 4: Generate conclusion
        contrarian_signal = self.psychology.get_contrarian_signal()
        
        if contrarian_signal:
            decision = contrarian_signal['signal']
            confidence = contrarian_signal['confidence']
            reason = contrarian_signal['reason']
        else:
            decision = "HOLD"
            confidence = 0.5
            reason = "No strong signal detected"
        
        self.reasoning.set_conclusion(decision, confidence)
        
        # Store episode
        self.memory.store_episode(
            f"market_analysis_{symbol}",
            {
                'symbol': symbol,
                'emotion': emotion_state.primary_emotion.value,
                'decision': decision
            },
            outcome=None  # Will be updated later
        )
        
        return {
            'symbol': symbol,
            'decision': decision,
            'confidence': confidence,
            'reason': reason,
            'emotion_state': self.psychology.get_psychology_report(),
            'attention_scores': attention_scores,
            'reasoning_chain': self.reasoning.get_explanation(),
            'visualization': self.reasoning.get_visualization_data()
        }


# Convenience functions
def create_cognitive_system() -> IntegratedCognitiveSystem:
    """Create integrated cognitive system"""
    return IntegratedCognitiveSystem()
