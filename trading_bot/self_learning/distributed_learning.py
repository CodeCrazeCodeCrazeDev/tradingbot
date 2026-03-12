"""
Distributed Learning System

This module implements distributed learning across all bot components,
enabling knowledge sharing, collective intelligence, and coordinated improvement.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import deque
import logging
import json

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Types of knowledge that can be shared"""
    MARKET_PATTERN = "market_pattern"
    STRATEGY_INSIGHT = "strategy_insight"
    RISK_SIGNAL = "risk_signal"
    EXECUTION_TECHNIQUE = "execution_technique"
    MODEL_WEIGHTS = "model_weights"
    PERFORMANCE_METRIC = "performance_metric"
    ERROR_PATTERN = "error_pattern"
    OPTIMIZATION_RESULT = "optimization_result"


class ComponentRole(Enum):
    """Roles of different components in distributed learning"""
    SIGNAL_GENERATOR = "signal_generator"
    RISK_MANAGER = "risk_manager"
    EXECUTION_ENGINE = "execution_engine"
    MARKET_ANALYZER = "market_analyzer"
    STRATEGY_OPTIMIZER = "strategy_optimizer"
    PERFORMANCE_TRACKER = "performance_tracker"


@dataclass
class Knowledge:
    """Shared knowledge unit"""
    knowledge_id: str
    knowledge_type: KnowledgeType
    source_component: str
    content: Dict[str, Any]
    confidence: float
    timestamp: datetime
    validation_count: int = 0
    success_rate: float = 0.0
    usage_count: int = 0
    
    def validate(self, outcome: bool):
        """Validate knowledge with outcome"""
        self.validation_count += 1
        self.success_rate = (
            (self.success_rate * (self.validation_count - 1) + (1.0 if outcome else 0.0)) 
            / self.validation_count
        )


@dataclass
class LearningMessage:
    """Message for inter-component communication"""
    message_id: str
    sender: str
    receiver: Optional[str]  # None for broadcast
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: int = 5  # 1-10, higher is more important


class KnowledgeBase:
    """Centralized knowledge repository"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.knowledge: Dict[str, Knowledge] = {}
        self.knowledge_by_type: Dict[KnowledgeType, List[str]] = {kt: [] for kt in KnowledgeType}
        self.access_log: deque = deque(maxlen=1000)
        
    def store(self, knowledge: Knowledge):
        """Store knowledge in the base"""
        # Remove oldest if at capacity
        if len(self.knowledge) >= self.max_size:
            oldest_id = min(self.knowledge.keys(), 
                          key=lambda k: self.knowledge[k].timestamp)
            self.remove(oldest_id)
        
        self.knowledge[knowledge.knowledge_id] = knowledge
        self.knowledge_by_type[knowledge.knowledge_type].append(knowledge.knowledge_id)
        
        logger.debug(f"Stored knowledge: {knowledge.knowledge_id} from {knowledge.source_component}")
    
    def retrieve(self, knowledge_id: str) -> Optional[Knowledge]:
        """Retrieve specific knowledge"""
        knowledge = self.knowledge.get(knowledge_id)
        if knowledge:
            knowledge.usage_count += 1
            self.access_log.append({
                'knowledge_id': knowledge_id,
                'timestamp': datetime.utcnow()
            })
        return knowledge
    
    def query(self, knowledge_type: Optional[KnowledgeType] = None,
             min_confidence: float = 0.0,
             min_success_rate: float = 0.0,
             limit: int = 100) -> List[Knowledge]:
        """Query knowledge base"""
        candidates = []
        
        if knowledge_type:
            knowledge_ids = self.knowledge_by_type.get(knowledge_type, [])
            candidates = [self.knowledge[kid] for kid in knowledge_ids if kid in self.knowledge]
        else:
            candidates = list(self.knowledge.values())
        
        # Filter by criteria
        filtered = [
            k for k in candidates
            if k.confidence >= min_confidence and k.success_rate >= min_success_rate
        ]
        
        # Sort by relevance (confidence * success_rate * recency)
        now = datetime.utcnow()
        scored = []
        for k in filtered:
            age_hours = (now - k.timestamp).total_seconds() / 3600
            recency_score = 1.0 / (1.0 + age_hours / 24)  # Decay over days
            score = k.confidence * max(k.success_rate, 0.5) * recency_score
            scored.append((score, k))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [k for _, k in scored[:limit]]
    
    def remove(self, knowledge_id: str):
        """Remove knowledge from base"""
        if knowledge_id in self.knowledge:
            knowledge = self.knowledge[knowledge_id]
            del self.knowledge[knowledge_id]
            
            if knowledge_id in self.knowledge_by_type[knowledge.knowledge_type]:
                self.knowledge_by_type[knowledge.knowledge_type].remove(knowledge_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            'total_knowledge': len(self.knowledge),
            'by_type': {kt.value: len(ids) for kt, ids in self.knowledge_by_type.items()},
            'avg_confidence': np.mean([k.confidence for k in self.knowledge.values()]) if self.knowledge else 0,
            'avg_success_rate': np.mean([k.success_rate for k in self.knowledge.values() if k.validation_count > 0]) if self.knowledge else 0,
            'total_validations': sum(k.validation_count for k in self.knowledge.values()),
            'recent_accesses': len(self.access_log)
        }


class MessageBus:
    """Message bus for inter-component communication"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.message_history: deque = deque(maxlen=1000)
        
    def subscribe(self, component_name: str) -> asyncio.Queue:
        """Subscribe component to message bus"""
        queue = asyncio.Queue(maxsize=100)
        if component_name not in self.subscribers:
            self.subscribers[component_name] = []
        self.subscribers[component_name].append(queue)
        logger.info(f"Component subscribed: {component_name}")
        return queue
    
    async def publish(self, message: LearningMessage):
        """Publish message to bus"""
        self.message_history.append(message)
        
        # Deliver to specific receiver or broadcast
        if message.receiver:
            if message.receiver in self.subscribers:
                for queue in self.subscribers[message.receiver]:
                    try:
                        await asyncio.wait_for(queue.put(message), timeout=1.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Message queue full for {message.receiver}")
        else:
            # Broadcast to all except sender
            for component_name, queues in self.subscribers.items():
                if component_name != message.sender:
                    for queue in queues:
                        try:
                            await asyncio.wait_for(queue.put(message), timeout=1.0)
                        except asyncio.TimeoutError:
                            pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        return {
            'total_subscribers': len(self.subscribers),
            'total_messages': len(self.message_history),
            'messages_by_type': {}
        }


class LearningComponent:
    """Base class for learning components"""
    
    def __init__(self, component_name: str, role: ComponentRole, 
                 knowledge_base: KnowledgeBase, message_bus: MessageBus):
        self.component_name = component_name
        self.role = role
        self.knowledge_base = knowledge_base
        self.message_bus = message_bus
        self.message_queue = message_bus.subscribe(component_name)
        self.is_active = False
        self.learned_knowledge: List[str] = []
        
    async def share_knowledge(self, knowledge_type: KnowledgeType, 
                             content: Dict[str, Any], confidence: float):
        """Share knowledge with other components"""
        knowledge = Knowledge(
            knowledge_id=f"{self.component_name}_{knowledge_type.value}_{datetime.utcnow().timestamp()}",
            knowledge_type=knowledge_type,
            source_component=self.component_name,
            content=content,
            confidence=confidence,
            timestamp=datetime.utcnow()
        )
        
        self.knowledge_base.store(knowledge)
        
        # Notify other components
        message = LearningMessage(
            message_id=f"msg_{datetime.utcnow().timestamp()}",
            sender=self.component_name,
            receiver=None,  # Broadcast
            message_type="knowledge_shared",
            payload={
                'knowledge_id': knowledge.knowledge_id,
                'knowledge_type': knowledge_type.value,
                'confidence': confidence
            }
        )
        
        await self.message_bus.publish(message)
        logger.info(f"{self.component_name} shared knowledge: {knowledge.knowledge_id}")
    
    async def learn_from_others(self, knowledge_type: Optional[KnowledgeType] = None,
                                min_confidence: float = 0.7) -> List[Knowledge]:
        """Learn from knowledge shared by other components"""
        knowledge_list = self.knowledge_base.query(
            knowledge_type=knowledge_type,
            min_confidence=min_confidence,
            min_success_rate=0.6,
            limit=10
        )
        
        # Filter out own knowledge
        other_knowledge = [k for k in knowledge_list if k.source_component != self.component_name]
        
        for knowledge in other_knowledge:
            if knowledge.knowledge_id not in self.learned_knowledge:
                self.learned_knowledge.append(knowledge.knowledge_id)
                await self._apply_knowledge(knowledge)
        
        return other_knowledge
    
    async def _apply_knowledge(self, knowledge: Knowledge):
        """Apply learned knowledge (to be implemented by subclasses)"""
        pass
    
    async def send_message(self, receiver: str, message_type: str, 
                          payload: Dict[str, Any], priority: int = 5):
        """Send message to specific component"""
        message = LearningMessage(
            message_id=f"msg_{datetime.utcnow().timestamp()}",
            sender=self.component_name,
            receiver=receiver,
            message_type=message_type,
            payload=payload,
            priority=priority
        )
        
        await self.message_bus.publish(message)
    
    async def process_messages(self):
        """Process incoming messages"""
        while self.is_active:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message in {self.component_name}: {e}")
    
    async def _handle_message(self, message: LearningMessage):
        """Handle incoming message (to be implemented by subclasses)"""
        pass


class CollectiveIntelligence:
    """Manages collective intelligence across components"""
    
    def __init__(self):
        self.component_contributions: Dict[str, Dict[str, float]] = {}
        self.consensus_history: List[Dict] = []
        
    def record_contribution(self, component_name: str, contribution_type: str, value: float):
        """Record component contribution"""
        if component_name not in self.component_contributions:
            self.component_contributions[component_name] = {}
        
        if contribution_type not in self.component_contributions[component_name]:
            self.component_contributions[component_name][contribution_type] = []
        
        self.component_contributions[component_name][contribution_type] = value
    
    def calculate_consensus(self, predictions: Dict[str, float], 
                          weights: Optional[Dict[str, float]] = None) -> Tuple[float, float]:
        """Calculate consensus prediction from multiple components"""
        if not predictions:
            return 0.0, 0.0
        
        if weights is None:
            weights = {k: 1.0 for k in predictions.keys()}
        
        # Weighted average
        total_weight = sum(weights.values())
        consensus = sum(pred * weights.get(comp, 1.0) 
                       for comp, pred in predictions.items()) / total_weight
        
        # Confidence based on agreement
        values = list(predictions.values())
        agreement = 1.0 - (np.std(values) / (np.mean(np.abs(values)) + 1e-6))
        confidence = min(agreement, 1.0)
        
        self.consensus_history.append({
            'timestamp': datetime.utcnow(),
            'predictions': predictions,
            'consensus': consensus,
            'confidence': confidence
        })
        
        return consensus, confidence
    
    def get_component_weights(self) -> Dict[str, float]:
        """Calculate component weights based on historical performance"""
        weights = {}
        
        for component_name, contributions in self.component_contributions.items():
            # Simple average of all contribution types
            if contributions:
                weights[component_name] = np.mean(list(contributions.values()))
            else:
                weights[component_name] = 0.5
        
        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights


class DistributedLearningSystem:
    """Main distributed learning system coordinator"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.knowledge_base = KnowledgeBase(max_size=self.config.get('knowledge_base_size', 10000))
        self.message_bus = MessageBus()
        self.collective_intelligence = CollectiveIntelligence()
        self.components: Dict[str, LearningComponent] = {}
        self.is_active = False
        
    def register_component(self, component: LearningComponent):
        """Register a learning component"""
        self.components[component.component_name] = component
        logger.info(f"Registered component: {component.component_name} ({component.role.value})")
    
    async def start(self):
        """Start distributed learning"""
        self.is_active = True
        
        # Start all components
        for component in self.components.values():
            component.is_active = True
            asyncio.create_task(component.process_messages())
        
        logger.info("Distributed learning system started")
    
    def stop(self):
        """Stop distributed learning"""
        self.is_active = False
        
        for component in self.components.values():
            component.is_active = False
        
        logger.info("Distributed learning system stopped")
    
    async def synchronize_learning(self):
        """Synchronize learning across all components"""
        # Trigger learning from shared knowledge
        for component in self.components.values():
            await component.learn_from_others()
        
        logger.info("Learning synchronized across components")
    
    async def get_collective_prediction(self, context: Dict[str, Any]) -> Tuple[float, float]:
        """Get collective prediction from all components"""
        predictions = {}
        
        # Collect predictions from components that can predict
        for component_name, component in self.components.items():
            if hasattr(component, 'predict'):
                try:
                    pred = await component.predict(context)
                    predictions[component_name] = pred
                except Exception as e:
                    logger.error(f"Error getting prediction from {component_name}: {e}")
        
        # Calculate consensus
        weights = self.collective_intelligence.get_component_weights()
        consensus, confidence = self.collective_intelligence.calculate_consensus(predictions, weights)
        
        return consensus, confidence
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'active': self.is_active,
            'components': {
                name: {
                    'role': comp.role.value,
                    'active': comp.is_active,
                    'learned_knowledge': len(comp.learned_knowledge)
                }
                for name, comp in self.components.items()
            },
            'knowledge_base': self.knowledge_base.get_statistics(),
            'message_bus': self.message_bus.get_statistics(),
            'collective_intelligence': {
                'consensus_history': len(self.collective_intelligence.consensus_history),
                'component_weights': self.collective_intelligence.get_component_weights()
            }
        }
    
    async def save_state(self, filepath: str):
        """Save distributed learning state"""
        state = {
            'timestamp': datetime.utcnow().isoformat(),
            'knowledge_base': {
                'total_knowledge': len(self.knowledge_base.knowledge),
                'knowledge_ids': list(self.knowledge_base.knowledge.keys())
            },
            'components': list(self.components.keys()),
            'system_status': self.get_system_status()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"Distributed learning state saved to {filepath}")


async def create_distributed_learning_system(config: Optional[Dict] = None) -> DistributedLearningSystem:
    """Factory function to create distributed learning system"""
    system = DistributedLearningSystem(config)
    logger.info("Distributed learning system initialized")
    return system
