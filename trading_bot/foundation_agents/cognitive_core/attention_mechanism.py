"""
Attention Mechanism - Cognitive Focus Allocation
=================================================

Implements brain-inspired attention mechanisms:
1. Information source prioritization
2. Dynamic focus allocation
3. Salience detection
4. Attention switching

Based on the Foundation Agents paper (arXiv:2504.01990) cognitive core.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque, defaultdict
import heapq

logger = logging.getLogger(__name__)


class AttentionType(Enum):
    """Types of attention mechanisms"""
    FOCUSED = "focused"           # Narrow, deep attention
    DIFFUSE = "diffuse"           # Broad, scanning attention
    SUSTAINED = "sustained"       # Long-term focused attention
    ALTERNATING = "alternating"   # Switching between targets
    DIVIDED = "divided"           # Multiple simultaneous targets


class SalienceSource(Enum):
    """Sources of salience"""
    NOVELTY = "novelty"           # New, unexpected information
    THREAT = "threat"             # Danger signals
    REWARD = "reward"             # Opportunity signals
    RELEVANCE = "relevance"       # Task-relevant information
    URGENCY = "urgency"           # Time-sensitive information
    PATTERN = "pattern"           # Recognizable patterns


@dataclass
class AttentionTarget:
    """Something that can attract attention"""
    target_id: str
    name: str
    target_type: str  # "market_data", "research", "alert", "goal", etc.
    
    # Salience components
    salience: float = 0.0
    salience_sources: Dict[SalienceSource, float] = field(default_factory=dict)
    
    # Attention state
    current_attention: float = 0.0
    attention_history: List[float] = field(default_factory=list)
    
    # Timing
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_salience(self, source: SalienceSource, value: float):
        """Update salience from a specific source"""
        self.salience_sources[source] = max(0.0, min(1.0, value))
        self._recalculate_salience()
    
    def _recalculate_salience(self):
        """Recalculate overall salience"""
        if not self.salience_sources:
            self.salience = 0.0
        else:
            # Weighted combination
            weights = {
                SalienceSource.THREAT: 2.0,
                SalienceSource.URGENCY: 1.5,
                SalienceSource.REWARD: 1.2,
                SalienceSource.NOVELTY: 1.0,
                SalienceSource.RELEVANCE: 0.8,
                SalienceSource.PATTERN: 0.5
            }
            
            total_weight = sum(weights.get(s, 1.0) for s in self.salience_sources.keys())
            weighted_sum = sum(
                self.salience_sources[s] * weights.get(s, 1.0)
                for s in self.salience_sources.keys()
            )
            
            self.salience = min(1.0, weighted_sum / max(1.0, total_weight * 0.5))
    
    def allocate_attention(self, amount: float):
        """Allocate attention to this target"""
        self.current_attention = max(0.0, min(1.0, amount))
        self.attention_history.append(self.current_attention)
        if len(self.attention_history) > 100:
            self.attention_history = self.attention_history[-50:]
        self.last_accessed = datetime.utcnow()


class SalienceCalculator:
    """Calculate salience for different information types"""
    
    def calculate_novelty(self, data: Any, history: List[Any]) -> float:
        """Calculate novelty score"""
        if not history:
            return 0.5
        
        # Simple novelty: distance from historical mean
        try:
            if isinstance(data, (int, float)):
                hist_values = [float(h) for h in history if isinstance(h, (int, float))]
                if hist_values:
                    mean = np.mean(hist_values)
                    std = np.std(hist_values) + 1e-10
                    z_score = abs(data - mean) / std
                    return min(1.0, z_score / 3.0)  # Normalize to 0-1
        except:
            pass
        
        return 0.3  # Default moderate novelty
    
    def calculate_urgency(self, deadline: Optional[datetime]) -> float:
        """Calculate urgency based on deadline"""
        if not deadline:
            return 0.0
        
        time_remaining = (deadline - datetime.utcnow()).total_seconds()
        
        if time_remaining < 0:
            return 1.0  # Overdue
        elif time_remaining < 300:  # 5 minutes
            return 0.9
        elif time_remaining < 3600:  # 1 hour
            return 0.7
        elif time_remaining < 86400:  # 1 day
            return 0.5
        else:
            return 0.2
    
    def calculate_relevance(self, data_tags: List[str], current_goals: List[str]) -> float:
        """Calculate relevance to current goals"""
        if not data_tags or not current_goals:
            return 0.5
        
        matches = sum(1 for tag in data_tags if any(goal in tag for goal in current_goals))
        return min(1.0, matches / len(current_goals)) if current_goals else 0.5
    
    def calculate_threat(self, risk_indicators: Dict[str, float]) -> float:
        """Calculate threat level"""
        if not risk_indicators:
            return 0.0
        
        # Weight high-severity indicators more
        max_threat = max(risk_indicators.values()) if risk_indicators else 0.0
        avg_threat = np.mean(list(risk_indicators.values())) if risk_indicators else 0.0
        
        return 0.7 * max_threat + 0.3 * avg_threat
    
    def calculate_reward_potential(self, opportunity_indicators: Dict[str, float]) -> float:
        """Calculate potential reward"""
        if not opportunity_indicators:
            return 0.0
        
        # Weight high-reward opportunities
        max_reward = max(opportunity_indicators.values()) if opportunity_indicators else 0.0
        return min(1.0, max_reward)


class AttentionMechanism:
    """
    Attention Mechanism
    
    Manages cognitive focus allocation across multiple information
    sources, prioritizing based on salience and strategic importance.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Attention capacity
        self.total_attention_capacity = self.config.get('attention_capacity', 1.0)
        self.current_attention_usage = 0.0
        
        # Attention targets
        self.targets: Dict[str, AttentionTarget] = {}
        self.active_targets: List[str] = []
        
        # Attention type
        self.current_mode = AttentionType.FOCUSED
        self.focus_target: Optional[str] = None
        
        # Salience calculator
        self.salience_calc = SalienceCalculator()
        
        # History
        self.attention_history: deque = deque(maxlen=1000)
        self.switch_history: deque = deque(maxlen=100)
        
        # Statistics
        self.stats = {
            'attention_switches': 0,
            'targets_created': 0,
            'total_attention_allocated': 0.0
        }
        
        logger.info("Attention Mechanism initialized")
    
    def register_target(
        self,
        target_id: str,
        name: str,
        target_type: str,
        initial_salience: float = 0.5
    ) -> AttentionTarget:
        """Register a new attention target"""
        target = AttentionTarget(
            target_id=target_id,
            name=name,
            target_type=target_type,
            salience=initial_salience
        )
        
        self.targets[target_id] = target
        self.stats['targets_created'] += 1
        
        logger.debug(f"Registered attention target: {name} ({target_id})")
        
        return target
    
    def update_salience(
        self,
        target_id: str,
        source: SalienceSource,
        value: float
    ):
        """Update salience for a target"""
        if target_id not in self.targets:
            return
        
        self.targets[target_id].update_salience(source, value)
    
    def calculate_salience_for_data(
        self,
        target_id: str,
        data: Dict[str, Any]
    ):
        """Automatically calculate salience for data"""
        if target_id not in self.targets:
            return
        
        target = self.targets[target_id]
        
        # Calculate various salience components
        if 'novelty_score' in data:
            target.update_salience(SalienceSource.NOVELTY, data['novelty_score'])
        
        if 'risk_level' in data:
            threat = self.salience_calc.calculate_threat({'risk': data['risk_level']})
            target.update_salience(SalienceSource.THREAT, threat)
        
        if 'deadline' in data:
            urgency = self.salience_calc.calculate_urgency(data['deadline'])
            target.update_salience(SalienceSource.URGENCY, urgency)
        
        if 'reward_potential' in data:
            target.update_salience(SalienceSource.REWARD, data['reward_potential'])
        
        if 'tags' in data and 'current_goals' in data:
            relevance = self.salience_calc.calculate_relevance(
                data['tags'],
                data['current_goals']
            )
            target.update_salience(SalienceSource.RELEVANCE, relevance)
    
    def allocate_attention(self, target_id: str, amount: float) -> bool:
        """Allocate attention to a specific target"""
        if target_id not in self.targets:
            return False
        
        target = self.targets[target_id]
        
        # Check capacity
        new_usage = self.current_attention_usage + amount - target.current_attention
        if new_usage > self.total_attention_capacity:
            # Not enough capacity, need to reallocate
            self._reallocate_attention(amount - target.current_attention)
        
        old_attention = target.current_attention
        target.allocate_attention(amount)
        
        self.current_attention_usage += (amount - old_attention)
        
        if target_id not in self.active_targets and amount > 0.1:
            self.active_targets.append(target_id)
        
        self.attention_history.append({
            'timestamp': datetime.utcnow(),
            'target_id': target_id,
            'attention': amount,
            'salience': target.salience
        })
        
        self.stats['total_attention_allocated'] += amount
        
        return True
    
    def _reallocate_attention(self, needed: float):
        """Reallocate attention from lower-salience targets"""
        if needed <= 0:
            return
        
        # Sort active targets by salience (lowest first)
        sorted_targets = sorted(
            [(tid, self.targets[tid].salience) for tid in self.active_targets],
            key=lambda x: x[1]
        )
        
        reallocated = 0.0
        for tid, _ in sorted_targets:
            if reallocated >= needed:
                break
            
            target = self.targets[tid]
            available = target.current_attention * 0.5  # Can reduce by half
            
            if available > 0:
                reduction = min(available, needed - reallocated)
                target.allocate_attention(target.current_attention - reduction)
                self.current_attention_usage -= reduction
                reallocated += reduction
                
                if target.current_attention < 0.1:
                    self.active_targets.remove(tid)
    
    def get_attention_focus(self) -> Optional[str]:
        """Get the current primary focus of attention"""
        if self.focus_target and self.focus_target in self.targets:
            return self.focus_target
        
        # Find target with highest attention allocation
        if self.active_targets:
            return max(
                self.active_targets,
                key=lambda tid: self.targets[tid].current_attention
            )
        
        return None
    
    def switch_attention(self, new_target_id: str, reason: str = ""):
        """Switch primary attention to a new target"""
        if new_target_id not in self.targets:
            return False
        
        old_focus = self.focus_target
        self.focus_target = new_target_id
        
        # Allocate high attention to new focus
        self.allocate_attention(new_target_id, 0.8)
        
        # Record switch
        self.switch_history.append({
            'timestamp': datetime.utcnow(),
            'from': old_focus,
            'to': new_target_id,
            'reason': reason
        })
        
        self.stats['attention_switches'] += 1
        
        logger.info(f"Attention switched to {new_target_id}: {reason}")
        
        return True
    
    def auto_allocate(self):
        """Automatically allocate attention based on salience"""
        # Sort targets by salience
        sorted_targets = sorted(
            self.targets.values(),
            key=lambda t: t.salience,
            reverse=True
        )
        
        # Allocate attention proportionally to salience
        total_salience = sum(t.salience for t in sorted_targets)
        
        if total_salience == 0:
            return
        
        for target in sorted_targets[:5]:  # Top 5 targets
            proportion = target.salience / total_salience
            attention_amount = proportion * self.total_attention_capacity
            self.allocate_attention(target.target_id, attention_amount)
    
    def get_top_targets(self, n: int = 5) -> List[Tuple[str, float, float]]:
        """Get top N targets by attention allocation"""
        sorted_targets = sorted(
            [(tid, t.salience, t.current_attention) for tid, t in self.targets.items()],
            key=lambda x: x[2],
            reverse=True
        )
        return sorted_targets[:n]
    
    def set_attention_mode(self, mode: AttentionType):
        """Set the attention mode"""
        self.current_mode = mode
        
        if mode == AttentionType.FOCUSED:
            # Concentrate on highest salience target
            if self.targets:
                top = max(self.targets.values(), key=lambda t: t.salience)
                self.switch_attention(top.target_id, "focused mode")
        
        elif mode == AttentionType.DIFFUSE:
            # Spread attention broadly
            self.auto_allocate()
        
        logger.info(f"Attention mode set to: {mode.value}")
    
    def get_focus_summary(self) -> Dict[str, Any]:
        """Get summary of current attention focus"""
        focus_id = self.get_attention_focus()
        focus_target = self.targets.get(focus_id) if focus_id else None
        
        return {
            'mode': self.current_mode.value,
            'primary_focus': focus_target.name if focus_target else None,
            'focus_type': focus_target.target_type if focus_target else None,
            'focus_salience': focus_target.salience if focus_target else 0.0,
            'focus_attention': focus_target.current_attention if focus_target else 0.0,
            'active_targets': len(self.active_targets),
            'attention_usage': self.current_attention_usage,
            'attention_capacity': self.total_attention_capacity
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get attention mechanism statistics"""
        return {
            **self.stats,
            'total_targets': len(self.targets),
            'active_targets': len(self.active_targets),
            'attention_utilization': self.current_attention_usage / max(1e-10, self.total_attention_capacity),
            'recent_switches': len(self.switch_history),
            'mode': self.current_mode.value
        }
