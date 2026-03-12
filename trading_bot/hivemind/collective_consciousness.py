"""
Hivemind Collective Consciousness
==================================

A unified consciousness that emerges from the collective:
- Shared awareness across all nodes
- Unified perception of market state
- Collective memory and learning
- Emergent insights from node interactions
- Synchronized attention mechanisms
- Global coherence and harmony

This creates a single "mind" from many nodes - the whole
becomes greater than the sum of its parts.
"""

import asyncio
import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import hashlib
import json

logger = logging.getLogger(__name__)


class ConsciousnessLevel(Enum):
    """Levels of collective consciousness"""
    DORMANT = "dormant"           # Minimal activity
    AWARE = "aware"               # Basic awareness
    FOCUSED = "focused"           # Concentrated attention
    ENLIGHTENED = "enlightened"   # Peak performance
    TRANSCENDENT = "transcendent" # Extraordinary insight


class AttentionFocus(Enum):
    """What the collective is focusing on"""
    MARKET_TREND = "market_trend"
    RISK_ASSESSMENT = "risk_assessment"
    OPPORTUNITY_SCAN = "opportunity_scan"
    PATTERN_RECOGNITION = "pattern_recognition"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    EXECUTION_TIMING = "execution_timing"
    SELF_REFLECTION = "self_reflection"


class EmotionalState(Enum):
    """Collective emotional state"""
    CALM = "calm"
    EXCITED = "excited"
    CAUTIOUS = "cautious"
    FEARFUL = "fearful"
    GREEDY = "greedy"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"


@dataclass
class Perception:
    """A perception from the collective consciousness"""
    perception_id: str
    perception_type: str
    content: Dict[str, Any]
    confidence: float
    source_nodes: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    salience: float = 0.5  # How important/attention-grabbing
    
    def decay(self, factor: float = 0.95) -> None:
        """Decay perception salience over time"""
        self.salience *= factor


@dataclass
class CollectiveInsight:
    """An insight that emerges from collective processing"""
    insight_id: str
    insight_type: str
    description: str
    evidence: List[str]
    confidence: float
    novelty: float  # How new/unexpected
    actionability: float  # How actionable
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def get_importance_score(self) -> float:
        """Calculate overall importance"""
        return (self.confidence * 0.4 + 
                self.novelty * 0.3 + 
                self.actionability * 0.3)


@dataclass
class SharedMemory:
    """Memory shared across the collective"""
    memory_id: str
    memory_type: str  # "experience", "lesson", "pattern", "rule"
    content: Dict[str, Any]
    importance: float
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def access(self) -> None:
        """Record memory access"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
    
    def get_relevance(self, query: str) -> float:
        """Calculate relevance to query"""
        content_str = json.dumps(self.content).lower()
        query_lower = query.lower()
        
        # Simple keyword matching
        words = query_lower.split()
        matches = sum(1 for w in words if w in content_str)
        
        relevance = matches / len(words) if words else 0
        
        # Boost by importance and recency
        recency_boost = 1.0
        if self.last_accessed:
            hours_ago = (datetime.utcnow() - self.last_accessed).total_seconds() / 3600
            recency_boost = math.exp(-hours_ago / 24)  # Decay over 24 hours
        
        return relevance * self.importance * recency_boost


class AttentionMechanism:
    """
    Attention mechanism for the collective consciousness
    
    Determines what the collective focuses on and how
    attention is distributed across different concerns.
    """
    
    def __init__(self):
        self.current_focus: AttentionFocus = AttentionFocus.MARKET_TREND
        self.attention_weights: Dict[AttentionFocus, float] = {
            focus: 1.0 / len(AttentionFocus) for focus in AttentionFocus
        }
        self.focus_history: List[Tuple[AttentionFocus, datetime]] = []
        self.attention_span: float = 1.0  # How well attention is maintained
    
    def update_attention(self, perceptions: List[Perception]) -> None:
        """Update attention based on perceptions"""
        if not perceptions:
            return
        
        # Calculate salience for each focus area
        focus_salience: Dict[AttentionFocus, float] = {
            focus: 0.0 for focus in AttentionFocus
        }
        
        for perception in perceptions:
            # Map perception type to focus area
            ptype = perception.perception_type.lower()
            
            if 'trend' in ptype or 'price' in ptype:
                focus_salience[AttentionFocus.MARKET_TREND] += perception.salience
            if 'risk' in ptype or 'danger' in ptype:
                focus_salience[AttentionFocus.RISK_ASSESSMENT] += perception.salience
            if 'opportunity' in ptype or 'signal' in ptype:
                focus_salience[AttentionFocus.OPPORTUNITY_SCAN] += perception.salience
            if 'pattern' in ptype:
                focus_salience[AttentionFocus.PATTERN_RECOGNITION] += perception.salience
            if 'sentiment' in ptype or 'emotion' in ptype:
                focus_salience[AttentionFocus.SENTIMENT_ANALYSIS] += perception.salience
            if 'execution' in ptype or 'timing' in ptype:
                focus_salience[AttentionFocus.EXECUTION_TIMING] += perception.salience
        
        # Update weights using softmax
        total = sum(math.exp(s) for s in focus_salience.values())
        if total > 0:
            for focus in AttentionFocus:
                self.attention_weights[focus] = math.exp(focus_salience[focus]) / total
        
        # Update current focus
        self.current_focus = max(self.attention_weights, key=self.attention_weights.get)
        self.focus_history.append((self.current_focus, datetime.utcnow()))
        
        # Trim history
        if len(self.focus_history) > 100:
            self.focus_history = self.focus_history[-100:]
    
    def get_attention_distribution(self) -> Dict[str, float]:
        """Get current attention distribution"""
        return {focus.value: weight for focus, weight in self.attention_weights.items()}
    
    def is_focused(self) -> bool:
        """Check if attention is well-focused"""
        max_weight = max(self.attention_weights.values())
        return max_weight > 0.3  # Focused if one area has >30% attention
    
    def get_focus_stability(self) -> float:
        """Calculate how stable the focus has been"""
        if len(self.focus_history) < 5:
            return 1.0
        
        recent = [f for f, _ in self.focus_history[-10:]]
        most_common = max(set(recent), key=recent.count)
        stability = recent.count(most_common) / len(recent)
        
        return stability


class GlobalWorkspace:
    """
    Global Workspace for Collective Consciousness
    
    Based on Global Workspace Theory - a "blackboard" where
    information becomes globally available to all processes.
    """
    
    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self.workspace: List[Dict[str, Any]] = []
        self.broadcast_history: List[Dict[str, Any]] = []
    
    def broadcast(self, content: Dict[str, Any], source: str, priority: float = 0.5) -> None:
        """Broadcast content to global workspace"""
        entry = {
            'content': content,
            'source': source,
            'priority': priority,
            'timestamp': datetime.utcnow().isoformat(),
            'access_count': 0,
        }
        
        self.workspace.append(entry)
        self.broadcast_history.append(entry)
        
        # Maintain capacity
        if len(self.workspace) > self.capacity:
            # Remove lowest priority
            self.workspace.sort(key=lambda x: x['priority'], reverse=True)
            self.workspace = self.workspace[:self.capacity]
        
        if len(self.broadcast_history) > 500:
            self.broadcast_history = self.broadcast_history[-500:]
    
    def access(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Access workspace contents"""
        if query:
            # Filter by relevance
            results = []
            for entry in self.workspace:
                content_str = json.dumps(entry['content']).lower()
                if query.lower() in content_str:
                    entry['access_count'] += 1
                    results.append(entry)
            return results
        
        # Return all, sorted by priority
        for entry in self.workspace:
            entry['access_count'] += 1
        return sorted(self.workspace, key=lambda x: x['priority'], reverse=True)
    
    def get_most_salient(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get most salient items"""
        return sorted(self.workspace, key=lambda x: x['priority'], reverse=True)[:n]
    
    def clear_old(self, max_age_hours: float = 1.0) -> int:
        """Clear old entries"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        original_count = len(self.workspace)
        
        self.workspace = [
            e for e in self.workspace
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        
        return original_count - len(self.workspace)


class CollectiveConsciousness:
    """
    Collective Consciousness System
    
    Creates a unified consciousness from multiple nodes:
    - Integrates perceptions from all nodes
    - Maintains shared memory
    - Generates emergent insights
    - Coordinates collective attention
    - Produces unified decisions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core components
        self.attention = AttentionMechanism()
        self.workspace = GlobalWorkspace()
        
        # State
        self.level: ConsciousnessLevel = ConsciousnessLevel.AWARE
        self.emotional_state: EmotionalState = EmotionalState.CALM
        
        # Perceptions
        self.perceptions: List[Perception] = []
        self.max_perceptions = 200
        
        # Insights
        self.insights: List[CollectiveInsight] = []
        self.max_insights = 100
        
        # Shared memory
        self.memories: Dict[str, SharedMemory] = {}
        
        # Metrics
        self.coherence: float = 1.0  # How unified the consciousness is
        self.clarity: float = 1.0   # How clear the perceptions are
        self.energy: float = 1.0    # Available processing capacity
        
        # Node contributions
        self.node_contributions: Dict[str, int] = {}
        
        logger.info("CollectiveConsciousness initialized")
    
    def receive_perception(
        self,
        perception_type: str,
        content: Dict[str, Any],
        source_node: str,
        confidence: float = 0.5,
        salience: float = 0.5,
    ) -> Perception:
        """Receive a perception from a node"""
        perception = Perception(
            perception_id=f"perc_{datetime.utcnow().strftime('%H%M%S%f')}",
            perception_type=perception_type,
            content=content,
            confidence=confidence,
            source_nodes=[source_node],
            salience=salience,
        )
        
        self.perceptions.append(perception)
        
        # Track node contribution
        self.node_contributions[source_node] = self.node_contributions.get(source_node, 0) + 1
        
        # Broadcast to workspace if salient
        if salience > 0.5:
            self.workspace.broadcast(content, source_node, salience)
        
        # Maintain capacity
        if len(self.perceptions) > self.max_perceptions:
            self.perceptions = self.perceptions[-self.max_perceptions:]
        
        return perception
    
    def process_perceptions(self) -> Dict[str, Any]:
        """Process all perceptions and update state"""
        if not self.perceptions:
            return {'processed': 0}
        
        # Decay old perceptions
        for p in self.perceptions:
            p.decay()
        
        # Remove very old perceptions
        self.perceptions = [p for p in self.perceptions if p.salience > 0.01]
        
        # Update attention
        self.attention.update_attention(self.perceptions)
        
        # Update emotional state based on perceptions
        self._update_emotional_state()
        
        # Update consciousness level
        self._update_consciousness_level()
        
        # Try to generate insights
        new_insights = self._generate_insights()
        
        return {
            'processed': len(self.perceptions),
            'focus': self.attention.current_focus.value,
            'emotional_state': self.emotional_state.value,
            'consciousness_level': self.level.value,
            'new_insights': len(new_insights),
        }
    
    def _update_emotional_state(self) -> None:
        """Update collective emotional state"""
        if not self.perceptions:
            return
        
        # Analyze recent perceptions
        recent = self.perceptions[-20:]
        
        risk_signals = sum(1 for p in recent if 'risk' in p.perception_type.lower())
        opportunity_signals = sum(1 for p in recent if 'opportunity' in p.perception_type.lower())
        avg_confidence = sum(p.confidence for p in recent) / len(recent)
        
        if risk_signals > len(recent) * 0.4:
            self.emotional_state = EmotionalState.FEARFUL if avg_confidence < 0.5 else EmotionalState.CAUTIOUS
        elif opportunity_signals > len(recent) * 0.4:
            self.emotional_state = EmotionalState.EXCITED if avg_confidence > 0.7 else EmotionalState.CONFIDENT
        elif avg_confidence < 0.3:
            self.emotional_state = EmotionalState.UNCERTAIN
        elif avg_confidence > 0.8:
            self.emotional_state = EmotionalState.CONFIDENT
        else:
            self.emotional_state = EmotionalState.CALM
    
    def _update_consciousness_level(self) -> None:
        """Update consciousness level based on metrics"""
        # Calculate composite score
        score = (
            self.coherence * 0.3 +
            self.clarity * 0.3 +
            self.energy * 0.2 +
            self.attention.attention_span * 0.2
        )
        
        if score >= 0.9:
            self.level = ConsciousnessLevel.TRANSCENDENT
        elif score >= 0.75:
            self.level = ConsciousnessLevel.ENLIGHTENED
        elif score >= 0.5:
            self.level = ConsciousnessLevel.FOCUSED
        elif score >= 0.25:
            self.level = ConsciousnessLevel.AWARE
        else:
            self.level = ConsciousnessLevel.DORMANT
    
    def _generate_insights(self) -> List[CollectiveInsight]:
        """Generate insights from perceptions"""
        new_insights = []
        
        if len(self.perceptions) < 5:
            return new_insights
        
        recent = self.perceptions[-30:]
        
        # Look for patterns
        perception_types = [p.perception_type for p in recent]
        type_counts = {}
        for pt in perception_types:
            type_counts[pt] = type_counts.get(pt, 0) + 1
        
        # Insight: Dominant perception type
        if type_counts:
            dominant_type = max(type_counts, key=type_counts.get)
            if type_counts[dominant_type] >= len(recent) * 0.3:
                insight = CollectiveInsight(
                    insight_id=f"insight_{datetime.utcnow().strftime('%H%M%S%f')}",
                    insight_type="pattern_dominance",
                    description=f"Strong focus on {dominant_type}",
                    evidence=[p.perception_id for p in recent if p.perception_type == dominant_type],
                    confidence=type_counts[dominant_type] / len(recent),
                    novelty=0.3,
                    actionability=0.5,
                )
                new_insights.append(insight)
        
        # Insight: Confidence trend
        confidences = [p.confidence for p in recent]
        if len(confidences) >= 10:
            early_avg = sum(confidences[:5]) / 5
            late_avg = sum(confidences[-5:]) / 5
            
            if late_avg > early_avg + 0.2:
                insight = CollectiveInsight(
                    insight_id=f"insight_{datetime.utcnow().strftime('%H%M%S%f')}_conf",
                    insight_type="confidence_rising",
                    description="Collective confidence is increasing",
                    evidence=[],
                    confidence=late_avg,
                    novelty=0.5,
                    actionability=0.7,
                )
                new_insights.append(insight)
            elif late_avg < early_avg - 0.2:
                insight = CollectiveInsight(
                    insight_id=f"insight_{datetime.utcnow().strftime('%H%M%S%f')}_conf",
                    insight_type="confidence_falling",
                    description="Collective confidence is decreasing",
                    evidence=[],
                    confidence=1 - late_avg,
                    novelty=0.5,
                    actionability=0.7,
                )
                new_insights.append(insight)
        
        # Store insights
        self.insights.extend(new_insights)
        if len(self.insights) > self.max_insights:
            self.insights = self.insights[-self.max_insights:]
        
        return new_insights
    
    def store_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        importance: float = 0.5,
    ) -> SharedMemory:
        """Store a memory in collective memory"""
        memory_id = f"mem_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        memory = SharedMemory(
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
        )
        
        self.memories[memory_id] = memory
        
        return memory
    
    def recall_memories(self, query: str, limit: int = 10) -> List[SharedMemory]:
        """Recall relevant memories"""
        scored_memories = []
        
        for memory in self.memories.values():
            relevance = memory.get_relevance(query)
            if relevance > 0:
                scored_memories.append((memory, relevance))
        
        # Sort by relevance
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # Access and return
        results = []
        for memory, _ in scored_memories[:limit]:
            memory.access()
            results.append(memory)
        
        return results
    
    def get_unified_perception(self) -> Dict[str, Any]:
        """Get unified perception of current state"""
        if not self.perceptions:
            return {'state': 'no_perceptions'}
        
        recent = self.perceptions[-20:]
        
        # Aggregate perceptions
        aggregated = {
            'timestamp': datetime.utcnow().isoformat(),
            'consciousness_level': self.level.value,
            'emotional_state': self.emotional_state.value,
            'attention_focus': self.attention.current_focus.value,
            'attention_distribution': self.attention.get_attention_distribution(),
            'coherence': self.coherence,
            'clarity': self.clarity,
            'perception_count': len(recent),
            'avg_confidence': sum(p.confidence for p in recent) / len(recent),
            'avg_salience': sum(p.salience for p in recent) / len(recent),
            'recent_insights': [
                {
                    'type': i.insight_type,
                    'description': i.description,
                    'importance': i.get_importance_score(),
                }
                for i in self.insights[-5:]
            ],
            'workspace_highlights': [
                e['content'] for e in self.workspace.get_most_salient(3)
            ],
        }
        
        return aggregated
    
    def make_collective_decision(self, options: List[str]) -> Dict[str, Any]:
        """Make a decision using collective consciousness"""
        # Get unified perception
        perception = self.get_unified_perception()
        
        # Score each option based on current state
        scores = {opt: 0.5 for opt in options}
        
        # Adjust based on emotional state
        if self.emotional_state == EmotionalState.FEARFUL:
            if 'hold' in options:
                scores['hold'] += 0.3
            if 'sell' in options:
                scores['sell'] += 0.2
        elif self.emotional_state == EmotionalState.CONFIDENT:
            if 'buy' in options:
                scores['buy'] += 0.2
        elif self.emotional_state == EmotionalState.CAUTIOUS:
            if 'hold' in options:
                scores['hold'] += 0.2
        
        # Adjust based on recent insights
        for insight in self.insights[-5:]:
            if insight.insight_type == "confidence_rising" and 'buy' in options:
                scores['buy'] += insight.confidence * 0.2
            elif insight.insight_type == "confidence_falling" and 'sell' in options:
                scores['sell'] += insight.confidence * 0.2
        
        # Normalize
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        
        # Choose
        winner = max(scores, key=scores.get)
        
        return {
            'decision': winner,
            'confidence': scores[winner],
            'scores': scores,
            'emotional_influence': self.emotional_state.value,
            'consciousness_level': self.level.value,
            'coherence': self.coherence,
        }
    
    def synchronize(self) -> None:
        """Synchronize the collective consciousness"""
        # Increase coherence
        self.coherence = min(1.0, self.coherence + 0.1)
        
        # Clear workspace of old items
        self.workspace.clear_old(max_age_hours=0.5)
        
        # Consolidate memories
        self._consolidate_memories()
    
    def _consolidate_memories(self) -> None:
        """Consolidate and prune memories"""
        if len(self.memories) < 100:
            return
        
        # Remove low-importance, rarely accessed memories
        to_remove = []
        for mem_id, memory in self.memories.items():
            if memory.importance < 0.3 and memory.access_count < 2:
                to_remove.append(mem_id)
        
        for mem_id in to_remove[:len(to_remove) // 2]:  # Remove half
            del self.memories[mem_id]
    
    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive consciousness report"""
        return {
            'level': self.level.value,
            'emotional_state': self.emotional_state.value,
            'metrics': {
                'coherence': self.coherence,
                'clarity': self.clarity,
                'energy': self.energy,
            },
            'attention': {
                'focus': self.attention.current_focus.value,
                'distribution': self.attention.get_attention_distribution(),
                'stability': self.attention.get_focus_stability(),
            },
            'perceptions': {
                'count': len(self.perceptions),
                'recent_types': list(set(p.perception_type for p in self.perceptions[-10:])),
            },
            'insights': {
                'count': len(self.insights),
                'recent': [i.insight_type for i in self.insights[-5:]],
            },
            'memories': {
                'count': len(self.memories),
                'types': list(set(m.memory_type for m in self.memories.values())),
            },
            'workspace': {
                'items': len(self.workspace.workspace),
                'capacity': self.workspace.capacity,
            },
            'node_contributions': self.node_contributions,
        }


# Factory function
def create_collective_consciousness(
    config: Optional[Dict[str, Any]] = None
) -> CollectiveConsciousness:
    """Create collective consciousness system"""
    return CollectiveConsciousness(config)
