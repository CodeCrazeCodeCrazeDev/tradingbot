"""
Emotion Module - Affective State Management
============================================

Implements emotion-like states for the AI agent:
1. Risk Sentiment: Fear/greed-like states affecting risk tolerance
2. Confidence: Certainty in decisions and predictions
3. Arousal: Activation level affecting exploration vs exploitation
4. Valence: Positive/negative affect from outcomes

Based on the Foundation Agents paper (arXiv:2504.01990) emotion systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class EmotionDimension(Enum):
    """Dimensions of emotional state"""
    VALENCE = "valence"          # Positive/negative (-1 to 1)
    AROUSAL = "arousal"          # Low/high activation (0 to 1)
    DOMINANCE = "dominance"      # Control/submissive (0 to 1)
    CONFIDENCE = "confidence"    # Certainty (0 to 1)
    RISK_APPETITE = "risk_appetite"  # Risk tolerance (0 to 1)


class EmotionalTrigger(Enum):
    """Events that trigger emotional responses"""
    PROFIT = "profit"
    LOSS = "loss"
    WINNING_STREAK = "winning_streak"
    LOSING_STREAK = "losing_streak"
    VOLATILITY_SPIKE = "volatility_spike"
    ANOMALY_DETECTED = "anomaly_detected"
    GOAL_ACHIEVED = "goal_achieved"
    GOAL_FAILED = "goal_failed"
    PREDICTION_CORRECT = "prediction_correct"
    PREDICTION_WRONG = "prediction_wrong"
    DISCOVERY = "discovery"
    UNCERTAINTY = "uncertainty"


@dataclass
class EmotionalState:
    """Current emotional state of the agent"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Core dimensions (all normalized 0-1 or -1 to 1)
    valence: float = 0.0          # -1 (negative) to 1 (positive)
    arousal: float = 0.5          # 0 (calm) to 1 (excited)
    dominance: float = 0.5        # 0 (no control) to 1 (full control)
    confidence: float = 0.5       # 0 (uncertain) to 1 (certain)
    risk_appetite: float = 0.5    # 0 (risk averse) to 1 (risk seeking)
    
    # Derived states
    fear_level: float = 0.0       # 0 to 1
    greed_level: float = 0.0      # 0 to 1
    curiosity_level: float = 0.5  # 0 to 1
    
    # Recent triggers
    recent_triggers: List[EmotionalTrigger] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'valence': self.valence,
            'arousal': self.arousal,
            'dominance': self.dominance,
            'confidence': self.confidence,
            'risk_appetite': self.risk_appetite,
            'fear_level': self.fear_level,
            'greed_level': self.greed_level,
            'curiosity_level': self.curiosity_level,
            'recent_triggers': [t.value for t in self.recent_triggers]
        }
    
    def get_mood(self) -> str:
        """Get a descriptive mood label"""
        if self.valence > 0.3 and self.arousal > 0.6:
            return "excited"
        elif self.valence > 0.3 and self.arousal < 0.4:
            return "content"
        elif self.valence < -0.3 and self.arousal > 0.6:
            return "anxious"
        elif self.valence < -0.3 and self.arousal < 0.4:
            return "depressed"
        elif self.arousal > 0.7:
            return "alert"
        elif self.arousal < 0.3:
            return "calm"
        else:
            return "neutral"
    
    def copy(self) -> 'EmotionalState':
        return EmotionalState(
            timestamp=self.timestamp,
            valence=self.valence,
            arousal=self.arousal,
            dominance=self.dominance,
            confidence=self.confidence,
            risk_appetite=self.risk_appetite,
            fear_level=self.fear_level,
            greed_level=self.greed_level,
            curiosity_level=self.curiosity_level,
            recent_triggers=self.recent_triggers.copy()
        )


@dataclass
class EmotionalResponse:
    """Response to an emotional trigger"""
    trigger: EmotionalTrigger
    intensity: float  # 0 to 1
    
    # Changes to emotional dimensions
    valence_delta: float = 0.0
    arousal_delta: float = 0.0
    dominance_delta: float = 0.0
    confidence_delta: float = 0.0
    risk_appetite_delta: float = 0.0
    
    # Duration of effect
    decay_rate: float = 0.1  # How fast the effect decays


class EmotionalMemory:
    """
    Emotional Memory
    
    Stores emotional associations with events and outcomes.
    Enables learning from emotional experiences.
    """
    
    def __init__(self, max_size: int = 1000):
        self.memories: deque = deque(maxlen=max_size)
        self.associations: Dict[str, List[float]] = {}  # event_type -> valence history
        
    def store(
        self,
        event_type: str,
        emotional_state: EmotionalState,
        outcome: Optional[float] = None
    ):
        """Store an emotional memory"""
        memory = {
            'event_type': event_type,
            'state': emotional_state.to_dict(),
            'outcome': outcome,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.memories.append(memory)
        
        # Update associations
        if event_type not in self.associations:
            self.associations[event_type] = []
        self.associations[event_type].append(emotional_state.valence)
        
        # Keep only recent associations
        if len(self.associations[event_type]) > 100:
            self.associations[event_type] = self.associations[event_type][-100:]
    
    def get_emotional_expectation(self, event_type: str) -> float:
        """Get expected emotional valence for an event type"""
        if event_type not in self.associations:
            return 0.0
        
        values = self.associations[event_type]
        if not values:
            return 0.0
        
        # Weighted average favoring recent experiences
        weights = np.exp(np.linspace(-2, 0, len(values)))
        return np.average(values, weights=weights)


class EmotionRegulator:
    """
    Emotion Regulation System
    
    Prevents extreme emotional states and maintains stability.
    """
    
    def __init__(self):
        self.baseline = EmotionalState()
        self.regulation_strength = 0.1  # How strongly to pull toward baseline
        
        # Bounds for emotional dimensions
        self.bounds = {
            'valence': (-0.8, 0.8),
            'arousal': (0.2, 0.9),
            'dominance': (0.2, 0.9),
            'confidence': (0.1, 0.95),
            'risk_appetite': (0.1, 0.9)
        }
    
    def regulate(self, state: EmotionalState) -> EmotionalState:
        """Regulate emotional state toward baseline and within bounds"""
        regulated = state.copy()
        
        # Pull toward baseline
        regulated.valence = self._regulate_dimension(
            state.valence, self.baseline.valence, 'valence'
        )
        regulated.arousal = self._regulate_dimension(
            state.arousal, self.baseline.arousal, 'arousal'
        )
        regulated.dominance = self._regulate_dimension(
            state.dominance, self.baseline.dominance, 'dominance'
        )
        regulated.confidence = self._regulate_dimension(
            state.confidence, self.baseline.confidence, 'confidence'
        )
        regulated.risk_appetite = self._regulate_dimension(
            state.risk_appetite, self.baseline.risk_appetite, 'risk_appetite'
        )
        
        return regulated
    
    def _regulate_dimension(
        self,
        current: float,
        baseline: float,
        dimension: str
    ) -> float:
        """Regulate a single dimension"""
        # Pull toward baseline
        regulated = current + self.regulation_strength * (baseline - current)
        
        # Apply bounds
        bounds = self.bounds.get(dimension, (-1, 1))
        return np.clip(regulated, bounds[0], bounds[1])
    
    def set_baseline(self, state: EmotionalState):
        """Set new baseline emotional state"""
        self.baseline = state.copy()


class EmotionModule:
    """
    Emotion Module
    
    Central system for managing emotional states:
    - Process emotional triggers
    - Maintain emotional state
    - Regulate extreme states
    - Influence decision-making
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Current state
        self.state = EmotionalState()
        
        # History
        self.state_history: deque = deque(maxlen=1000)
        
        # Subsystems
        self.memory = EmotionalMemory()
        self.regulator = EmotionRegulator()
        
        # Trigger response mappings
        self.trigger_responses = self._initialize_trigger_responses()
        
        # Pending responses (for decay)
        self.active_responses: List[Tuple[EmotionalResponse, datetime]] = []
        
        # Statistics
        self.stats = {
            'triggers_processed': 0,
            'regulations_applied': 0,
            'avg_valence': 0.0,
            'avg_arousal': 0.5
        }
        
        logger.info("Emotion Module initialized")
    
    def _initialize_trigger_responses(self) -> Dict[EmotionalTrigger, EmotionalResponse]:
        """Initialize default emotional responses to triggers"""
        return {
            EmotionalTrigger.PROFIT: EmotionalResponse(
                trigger=EmotionalTrigger.PROFIT,
                intensity=0.5,
                valence_delta=0.2,
                arousal_delta=0.1,
                confidence_delta=0.1,
                risk_appetite_delta=0.05
            ),
            EmotionalTrigger.LOSS: EmotionalResponse(
                trigger=EmotionalTrigger.LOSS,
                intensity=0.6,
                valence_delta=-0.25,
                arousal_delta=0.15,
                confidence_delta=-0.15,
                risk_appetite_delta=-0.1
            ),
            EmotionalTrigger.WINNING_STREAK: EmotionalResponse(
                trigger=EmotionalTrigger.WINNING_STREAK,
                intensity=0.7,
                valence_delta=0.3,
                arousal_delta=0.2,
                confidence_delta=0.2,
                risk_appetite_delta=0.15,
                decay_rate=0.05
            ),
            EmotionalTrigger.LOSING_STREAK: EmotionalResponse(
                trigger=EmotionalTrigger.LOSING_STREAK,
                intensity=0.8,
                valence_delta=-0.4,
                arousal_delta=0.3,
                confidence_delta=-0.3,
                risk_appetite_delta=-0.2,
                decay_rate=0.05
            ),
            EmotionalTrigger.VOLATILITY_SPIKE: EmotionalResponse(
                trigger=EmotionalTrigger.VOLATILITY_SPIKE,
                intensity=0.6,
                valence_delta=-0.1,
                arousal_delta=0.3,
                dominance_delta=-0.1,
                risk_appetite_delta=-0.15
            ),
            EmotionalTrigger.ANOMALY_DETECTED: EmotionalResponse(
                trigger=EmotionalTrigger.ANOMALY_DETECTED,
                intensity=0.5,
                arousal_delta=0.2,
                dominance_delta=-0.1
            ),
            EmotionalTrigger.GOAL_ACHIEVED: EmotionalResponse(
                trigger=EmotionalTrigger.GOAL_ACHIEVED,
                intensity=0.7,
                valence_delta=0.3,
                arousal_delta=0.1,
                dominance_delta=0.15,
                confidence_delta=0.15
            ),
            EmotionalTrigger.GOAL_FAILED: EmotionalResponse(
                trigger=EmotionalTrigger.GOAL_FAILED,
                intensity=0.6,
                valence_delta=-0.25,
                arousal_delta=0.1,
                dominance_delta=-0.15,
                confidence_delta=-0.2
            ),
            EmotionalTrigger.PREDICTION_CORRECT: EmotionalResponse(
                trigger=EmotionalTrigger.PREDICTION_CORRECT,
                intensity=0.4,
                valence_delta=0.1,
                confidence_delta=0.15
            ),
            EmotionalTrigger.PREDICTION_WRONG: EmotionalResponse(
                trigger=EmotionalTrigger.PREDICTION_WRONG,
                intensity=0.4,
                valence_delta=-0.1,
                confidence_delta=-0.15
            ),
            EmotionalTrigger.DISCOVERY: EmotionalResponse(
                trigger=EmotionalTrigger.DISCOVERY,
                intensity=0.6,
                valence_delta=0.25,
                arousal_delta=0.15,
                dominance_delta=0.1
            ),
            EmotionalTrigger.UNCERTAINTY: EmotionalResponse(
                trigger=EmotionalTrigger.UNCERTAINTY,
                intensity=0.5,
                valence_delta=-0.1,
                arousal_delta=0.1,
                confidence_delta=-0.2,
                risk_appetite_delta=-0.1
            )
        }
    
    def process_trigger(
        self,
        trigger: EmotionalTrigger,
        intensity_modifier: float = 1.0,
        context: Optional[Dict] = None
    ) -> EmotionalState:
        """Process an emotional trigger and update state"""
        self.stats['triggers_processed'] += 1
        
        # Get response template
        response = self.trigger_responses.get(trigger)
        if not response:
            return self.state
        
        # Modify intensity
        effective_intensity = response.intensity * intensity_modifier
        
        # Apply changes
        self.state.valence += response.valence_delta * effective_intensity
        self.state.arousal += response.arousal_delta * effective_intensity
        self.state.dominance += response.dominance_delta * effective_intensity
        self.state.confidence += response.confidence_delta * effective_intensity
        self.state.risk_appetite += response.risk_appetite_delta * effective_intensity
        
        # Track trigger
        self.state.recent_triggers.append(trigger)
        if len(self.state.recent_triggers) > 10:
            self.state.recent_triggers.pop(0)
        
        # Add to active responses for decay
        self.active_responses.append((response, datetime.utcnow()))
        
        # Update derived states
        self._update_derived_states()
        
        # Regulate
        self.state = self.regulator.regulate(self.state)
        self.stats['regulations_applied'] += 1
        
        # Update timestamp
        self.state.timestamp = datetime.utcnow()
        
        # Store in history
        self.state_history.append(self.state.copy())
        
        # Store in emotional memory
        self.memory.store(trigger.value, self.state)
        
        # Update statistics
        self._update_stats()
        
        logger.debug(f"Processed trigger {trigger.value}: valence={self.state.valence:.2f}, "
                    f"arousal={self.state.arousal:.2f}, mood={self.state.get_mood()}")
        
        return self.state
    
    def _update_derived_states(self):
        """Update derived emotional states"""
        # Fear: negative valence + high arousal + low dominance
        self.state.fear_level = max(0, (
            (-self.state.valence + 1) / 2 * 0.4 +
            self.state.arousal * 0.3 +
            (1 - self.state.dominance) * 0.3
        ))
        
        # Greed: positive valence + high arousal + high confidence
        self.state.greed_level = max(0, (
            (self.state.valence + 1) / 2 * 0.4 +
            self.state.arousal * 0.3 +
            self.state.confidence * 0.3
        ))
        
        # Curiosity: moderate arousal + low confidence (wanting to learn)
        self.state.curiosity_level = max(0, (
            self.state.arousal * 0.4 +
            (1 - self.state.confidence) * 0.4 +
            (self.state.valence + 1) / 2 * 0.2
        ))
    
    def _update_stats(self):
        """Update running statistics"""
        if self.state_history:
            recent = list(self.state_history)[-100:]
            self.stats['avg_valence'] = np.mean([s.valence for s in recent])
            self.stats['avg_arousal'] = np.mean([s.arousal for s in recent])
    
    def decay_emotions(self, time_elapsed: timedelta):
        """Apply decay to emotional effects over time"""
        hours = time_elapsed.total_seconds() / 3600
        
        # Decay active responses
        still_active = []
        for response, start_time in self.active_responses:
            elapsed = (datetime.utcnow() - start_time).total_seconds() / 3600
            remaining = np.exp(-response.decay_rate * elapsed)
            
            if remaining > 0.1:  # Still significant
                still_active.append((response, start_time))
        
        self.active_responses = still_active
        
        # Natural decay toward baseline
        decay_factor = np.exp(-0.05 * hours)  # Slow natural decay
        
        self.state.valence *= decay_factor
        self.state.arousal = 0.5 + (self.state.arousal - 0.5) * decay_factor
        self.state.confidence = 0.5 + (self.state.confidence - 0.5) * decay_factor
        self.state.risk_appetite = 0.5 + (self.state.risk_appetite - 0.5) * decay_factor
        
        self._update_derived_states()
    
    def get_risk_adjustment(self) -> float:
        """Get risk adjustment factor based on emotional state"""
        # Base adjustment from risk appetite
        adjustment = self.state.risk_appetite
        
        # Reduce risk when fearful
        adjustment *= (1 - self.state.fear_level * 0.5)
        
        # Reduce risk when uncertain
        adjustment *= self.state.confidence
        
        # Slight increase when confident but not greedy
        if self.state.confidence > 0.7 and self.state.greed_level < 0.5:
            adjustment *= 1.1
        
        # Strong reduction when very greedy (overconfidence protection)
        if self.state.greed_level > 0.7:
            adjustment *= 0.7
        
        return np.clip(adjustment, 0.1, 1.5)
    
    def get_exploration_rate(self) -> float:
        """Get exploration rate based on emotional state"""
        # Higher curiosity = more exploration
        exploration = self.state.curiosity_level
        
        # Higher arousal = more exploration
        exploration += self.state.arousal * 0.2
        
        # Lower confidence = more exploration (need to learn)
        exploration += (1 - self.state.confidence) * 0.2
        
        # Reduce exploration when fearful
        exploration *= (1 - self.state.fear_level * 0.3)
        
        return np.clip(exploration, 0.1, 0.9)
    
    def should_pause_trading(self) -> Tuple[bool, str]:
        """Determine if trading should be paused based on emotional state"""
        reasons = []
        
        # Extreme fear
        if self.state.fear_level > 0.8:
            reasons.append("extreme fear")
        
        # Extreme greed
        if self.state.greed_level > 0.85:
            reasons.append("extreme greed")
        
        # Very low confidence
        if self.state.confidence < 0.15:
            reasons.append("very low confidence")
        
        # Very negative valence
        if self.state.valence < -0.7:
            reasons.append("very negative state")
        
        # Losing streak detected
        if EmotionalTrigger.LOSING_STREAK in self.state.recent_triggers:
            reasons.append("recent losing streak")
        
        should_pause = len(reasons) > 0
        reason_str = ", ".join(reasons) if reasons else ""
        
        return should_pause, reason_str
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current emotional state"""
        return {
            'current_state': self.state.to_dict(),
            'mood': self.state.get_mood(),
            'risk_adjustment': self.get_risk_adjustment(),
            'exploration_rate': self.get_exploration_rate(),
            'should_pause': self.should_pause_trading(),
            'stats': self.stats
        }
    
    def reset_to_baseline(self):
        """Reset emotional state to baseline"""
        self.state = EmotionalState()
        self.active_responses.clear()
        logger.info("Emotional state reset to baseline")
