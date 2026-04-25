"""
Knowledge Sharing - Inter-Agent Knowledge Exchange
======================================================

Enables agents to share insights and knowledge:
1. Knowledge message passing
2. Belief updating from peers
3. Shared knowledge bases
4. Collaborative learning

Based on the Foundation Agents paper multi-agent systems.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Types of knowledge to share"""
    HYPOTHESIS = "hypothesis"
    FINDING = "finding"
    INSIGHT = "insight"
    EXPERIENCE = "experience"
    PREDICTION = "prediction"
    WARNING = "warning"
    STRATEGY = "strategy"
    THEORY = "theory"


class ConfidenceLevel(Enum):
    """Confidence in shared knowledge"""
    VERY_HIGH = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    VERY_LOW = 1


@dataclass
class KnowledgeItem:
    """A piece of knowledge to be shared"""
    item_id: str
    knowledge_type: KnowledgeType
    
    # Content
    content: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Source
    origin_agent: str
    source_evidence: List[str] = field(default_factory=list)
    
    # Confidence
    confidence: float = 0.5
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    
    # Sharing
    share_count: int = 0
    recipients: List[str] = field(default_factory=list)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Validation
    validated_by: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'item_id': self.item_id,
            'type': self.knowledge_type.value,
            'content': self.content[:100] + "..." if len(self.content) > 100 else self.content,
            'origin': self.origin_agent,
            'confidence': self.confidence,
            'shares': self.share_count
        }


@dataclass
class KnowledgeShareEvent:
    """An event of knowledge sharing"""
    event_id: str
    knowledge_item: KnowledgeItem
    
    # Participants
    from_agent: str
    to_agent: str
    
    # Reception
    accepted: bool = True
    reception_confidence: float = 0.5
    notes: str = ""
    
    # Timing
    shared_at: datetime = field(default_factory=datetime.utcnow)


class KnowledgeProtocol:
    """Protocol for knowledge sharing between agents"""
    
    def __init__(
        self,
        min_confidence: float = 0.3,
        max_shares: int = 10
    ):
        self.min_confidence = min_confidence
        self.max_shares = max_shares
        
        # Trust network
        self.trust_scores: Dict[Tuple[str, str], float] = defaultdict(lambda: 0.5)
        
        # Reputation
        self.agent_reputation: Dict[str, float] = defaultdict(lambda: 0.5)
        self.agent_accuracy: Dict[str, List[bool]] = defaultdict(list)
    
    def evaluate_knowledge(
        self,
        item: KnowledgeItem,
        recipient: str,
        recipient_context: Optional[Dict] = None
    ) -> Tuple[bool, float]:
        """Evaluate whether recipient should accept knowledge"""
        # Check confidence threshold
        if item.confidence < self.min_confidence:
            return False, 0.0
        
        # Check sender reputation
        sender_reputation = self.agent_reputation[item.origin_agent]
        
        # Check trust between agents
        trust = self.trust_scores[(item.origin_agent, recipient)]
        
        # Calculate reception probability
        reception_score = (
            item.confidence * 0.4 +
            sender_reputation * 0.3 +
            trust * 0.3
        )
        
        should_accept = reception_score >= self.min_confidence
        
        return should_accept, reception_score
    
    def update_trust(
        self,
        sender: str,
        recipient: str,
        knowledge_valid: bool
    ):
        """Update trust score based on knowledge validity"""
        current_trust = self.trust_scores[(sender, recipient)]
        
        # Update with learning rate
        alpha = 0.1
        new_trust = current_trust + alpha * (1.0 if knowledge_valid else -1.0)
        self.trust_scores[(sender, recipient)] = max(0.0, min(1.0, new_trust))
        
        # Update sender reputation
        self.agent_accuracy[sender].append(knowledge_valid)
        if len(self.agent_accuracy[sender]) > 100:
            self.agent_accuracy[sender] = self.agent_accuracy[sender][-50:]
        
        self.agent_reputation[sender] = np.mean(self.agent_accuracy[sender])


class KnowledgeSharingSystem:
    """
    Knowledge Sharing System
    
    Manages knowledge exchange between agents in the swarm,
    enabling collaborative learning and distributed intelligence.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Knowledge storage
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.agent_knowledge: Dict[str, Set[str]] = defaultdict(set)  # agent -> item_ids
        
        # Sharing events
        self.share_history: List[KnowledgeShareEvent] = []
        
        # Protocol
        self.protocol = KnowledgeProtocol(
            min_confidence=self.config.get('min_confidence', 0.3),
            max_shares=self.config.get('max_shares', 10)
        )
        
        # Subscribers
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Statistics
        self.stats = {
            'items_created': 0,
            'items_shared': 0,
            'shares_accepted': 0,
            'shares_rejected': 0
        }
        
        logger.info("Knowledge Sharing System initialized")
    
    def create_knowledge(
        self,
        knowledge_type: KnowledgeType,
        content: str,
        origin_agent: str,
        data: Optional[Dict] = None,
        confidence: float = 0.5,
        evidence: Optional[List[str]] = None
    ) -> KnowledgeItem:
        """Create new knowledge item"""
        item = KnowledgeItem(
            item_id=str(uuid.uuid4())[:8],
            knowledge_type=knowledge_type,
            content=content,
            data=data or {},
            origin_agent=origin_agent,
            source_evidence=evidence or [],
            confidence=confidence,
            confidence_level=self._confidence_to_level(confidence)
        )
        
        self.knowledge_base[item.item_id] = item
        self.agent_knowledge[origin_agent].add(item.item_id)
        
        self.stats['items_created'] += 1
        
        # Notify subscribers
        self._notify_subscribers('new_knowledge', item)
        
        return item
    
    def share_knowledge(
        self,
        item_id: str,
        from_agent: str,
        to_agent: str,
        context: Optional[Dict] = None
    ) -> KnowledgeShareEvent:
        """Share knowledge from one agent to another"""
        if item_id not in self.knowledge_base:
            raise ValueError(f"Knowledge item {item_id} not found")
        
        item = self.knowledge_base[item_id]
        
        # Evaluate if recipient should accept
        should_accept, reception_score = self.protocol.evaluate_knowledge(
            item, to_agent, context
        )
        
        # Create share event
        event = KnowledgeShareEvent(
            event_id=str(uuid.uuid4())[:8],
            knowledge_item=item,
            from_agent=from_agent,
            to_agent=to_agent,
            accepted=should_accept,
            reception_confidence=reception_score,
            notes="Shared directly" if should_accept else "Low confidence/reputation"
        )
        
        self.share_history.append(event)
        
        if should_accept:
            item.share_count += 1
            item.recipients.append(to_agent)
            self.agent_knowledge[to_agent].add(item_id)
            self.stats['shares_accepted'] += 1
        else:
            self.stats['shares_rejected'] += 1
        
        self.stats['items_shared'] += 1
        
        # Notify
        self._notify_subscribers('knowledge_shared', event)
        
        return event
    
    def broadcast_knowledge(
        self,
        item_id: str,
        from_agent: str,
        target_agents: List[str],
        require_acceptance: bool = True
    ) -> List[KnowledgeShareEvent]:
        """Broadcast knowledge to multiple agents"""
        events = []
        
        for target in target_agents:
            if target != from_agent:
                event = self.share_knowledge(item_id, from_agent, target)
                events.append(event)
        
        return events
    
    def validate_knowledge(
        self,
        item_id: str,
        validator_agent: str,
        is_valid: bool,
        validation_notes: str = ""
    ):
        """Validate knowledge by an agent"""
        if item_id not in self.knowledge_base:
            return
        
        item = self.knowledge_base[item_id]
        
        if is_valid:
            item.validated_by.append(validator_agent)
        
        # Update trust in origin agent
        self.protocol.update_trust(
            item.origin_agent,
            validator_agent,
            is_valid
        )
        
        # Notify
        self._notify_subscribers('knowledge_validated', {
            'item_id': item_id,
            'validator': validator_agent,
            'valid': is_valid,
            'notes': validation_notes
        })
    
    def contradict_knowledge(
        self,
        item_id: str,
        contradicting_agent: str,
        contradiction_evidence: str
    ):
        """Register a contradiction to knowledge"""
        if item_id not in self.knowledge_base:
            return
        
        item = self.knowledge_base[item_id]
        item.contradictions.append(contradiction_evidence)
        
        # Reduce confidence
        item.confidence *= 0.8
        
        # Notify
        self._notify_subscribers('knowledge_contradicted', {
            'item_id': item_id,
            'agent': contradicting_agent,
            'evidence': contradiction_evidence
        })
    
    def query_knowledge(
        self,
        agent_id: str,
        knowledge_type: Optional[KnowledgeType] = None,
        min_confidence: float = 0.0,
        limit: int = 10
    ) -> List[KnowledgeItem]:
        """Query knowledge available to an agent"""
        item_ids = self.agent_knowledge.get(agent_id, set())
        
        items = [self.knowledge_base[iid] for iid in item_ids if iid in self.knowledge_base]
        
        # Filter by type
        if knowledge_type:
            items = [i for i in items if i.knowledge_type == knowledge_type]
        
        # Filter by confidence
        items = [i for i in items if i.confidence >= min_confidence]
        
        # Sort by confidence and recency
        items.sort(key=lambda i: (i.confidence, i.created_at), reverse=True)
        
        return items[:limit]
    
    def get_shared_insights(
        self,
        topic: str,
        min_agents: int = 2
    ) -> List[Dict]:
        """Get insights shared by multiple agents on a topic"""
        topic_items = []
        
        for item in self.knowledge_base.values():
            if topic.lower() in item.content.lower():
                topic_items.append(item)
        
        # Group by similarity (simplified)
        insights = []
        for item in topic_items:
            if item.share_count >= min_agents - 1:  # Shared with at least min_agents
                insights.append({
                    'content': item.content,
                    'origin': item.origin_agent,
                    'confidence': item.confidence,
                    'shared_by': len(item.recipients) + 1,
                    'type': item.knowledge_type.value
                })
        
        return insights
    
    def get_collaborative_learning_summary(
        self,
        agent_ids: List[str]
    ) -> Dict:
        """Get summary of collaborative learning among agents"""
        # Calculate shared knowledge
        all_knowledge = set()
        for agent in agent_ids:
            all_knowledge.update(self.agent_knowledge.get(agent, set()))
        
        # Find knowledge shared by multiple agents
        shared_counts = defaultdict(int)
        for item_id in all_knowledge:
            item = self.knowledge_base.get(item_id)
            if item:
                for agent in agent_ids:
                    if item_id in self.agent_knowledge.get(agent, set()):
                        shared_counts[item_id] += 1
        
        multi_shared = {k: v for k, v in shared_counts.items() if v >= 2}
        
        return {
            'total_knowledge_items': len(all_knowledge),
            'shared_knowledge_items': len(multi_shared),
            'collaboration_rate': len(multi_shared) / max(1, len(all_knowledge)),
            'avg_confidence': np.mean([
                self.knowledge_base[k].confidence for k in all_knowledge
                if k in self.knowledge_base
            ]) if all_knowledge else 0.0
        }
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to knowledge events"""
        self.subscribers[event_type].append(callback)
    
    def _notify_subscribers(self, event_type: str, data: Any):
        """Notify event subscribers"""
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Subscriber error: {e}")
    
    def _confidence_to_level(self, confidence: float) -> ConfidenceLevel:
        """Convert numeric confidence to level"""
        if confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def get_statistics(self) -> Dict:
        """Get sharing system statistics"""
        return {
            **self.stats,
            'total_knowledge_items': len(self.knowledge_base),
            'total_sharing_events': len(self.share_history),
            'acceptance_rate': (
                self.stats['shares_accepted'] / max(1, self.stats['items_shared'])
            ),
            'avg_shares_per_item': (
                np.mean([i.share_count for i in self.knowledge_base.values()])
                if self.knowledge_base else 0.0
            )
        }
