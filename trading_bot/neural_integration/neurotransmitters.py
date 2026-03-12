"""
Neurotransmitter Messaging System - Brain-like chemical signaling
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)


class NeurotransmitterType(Enum):
    """
    Chemical messengers like in a biological brain
    """
    GLUTAMATE = auto()      # Excitatory - "go" signal
    GABA = auto()           # Inhibitory - "stop" signal
    DOPAMINE = auto()       # Reward - "good outcome"
    SEROTONIN = auto()      # Mood - "stable state"
    ACETYLCHOLINE = auto()  # Attention - "focus here"
    NOREPINEPHRINE = auto() # Alert - "danger/stress"
    OXYTOCIN = auto()       # Trust - "safe to proceed"
    ENDORPHIN = auto()      # Pain relief - "recovering"


@dataclass
class NeurotransmitterSignal:
    """Chemical signal between neurons"""
    transmitter_type: NeurotransmitterType
    concentration: float  # 0.0 to 1.0
    source_module: str
    target_module: str
    timestamp: datetime
    decay_rate: float = 0.1
    receptor_affinity: float = 1.0
    
    def decay(self, time_elapsed: float) -> float:
        """Chemical decay over time"""
        return self.concentration * np.exp(-self.decay_rate * time_elapsed)


class SynapticCleft:
    """
    Space between neurons where neurotransmitters flow
    """
    
    def __init__(self):
        self.signals: List[NeurotransmitterSignal] = []
        self.receptors: Dict[str, Dict[NeurotransmitterType, List[Callable]]] = {}
        self.chemical_balance = {nt: 0.5 for nt in NeurotransmitterType}
        
    async def release_neurotransmitter(self, signal: NeurotransmitterSignal):
        """Release chemical into synaptic cleft"""
        self.signals.append(signal)
        
        # Update chemical balance
        self.chemical_balance[signal.transmitter_type] = min(
            1.0, self.chemical_balance[signal.transmitter_type] + signal.concentration * 0.1
        )
        
        # Trigger receptors
        await self._trigger_receptors(signal)
        
        # Start decay process
        asyncio.create_task(self._decay_signal(signal))
    
    async def _trigger_receptors(self, signal: NeurotransmitterSignal):
        """Trigger receptor callbacks"""
        target = signal.target_module
        nt_type = signal.transmitter_type
        
        if target in self.receptors and nt_type in self.receptors[target]:
            for callback in self.receptors[target][nt_type]:
                try:
                    await callback(signal)
                except Exception as e:
                    logger.error(f"Receptor callback failed: {e}")
    
    async def _decay_signal(self, signal: NeurotransmitterSignal):
        """Decay neurotransmitter over time"""
        await asyncio.sleep(1.0)
        
        if signal in self.signals:
            self.signals.remove(signal)
            
        # Decay chemical balance
        self.chemical_balance[signal.transmitter_type] = max(
            0.0, self.chemical_balance[signal.transmitter_type] - signal.decay_rate
        )
    
    def register_receptor(self, module: str, nt_type: NeurotransmitterType, 
                         callback: Callable):
        """Register a receptor for neurotransmitter"""
        if module not in self.receptors:
            self.receptors[module] = {}
        if nt_type not in self.receptors[module]:
            self.receptors[module][nt_type] = []
        
        self.receptors[module][nt_type].append(callback)
        logger.debug(f"Receptor registered: {module} -> {nt_type.name}")
    
    def get_chemical_state(self) -> Dict[str, float]:
        """Get current chemical balance"""
        return {nt.name: level for nt, level in self.chemical_balance.items()}


class NeuralPlasticityEngine:
    """
    Hebbian learning: "Neurons that fire together, wire together"
    
    Strengthens connections that are used frequently
    Weakens connections that are unused
    """
    
    def __init__(self):
        self.connection_weights: Dict[str, Dict[str, float]] = {}
        self.firing_history: Dict[str, List[datetime]] = {}
        self.learning_rate = 0.1
        self.decay_rate = 0.01
        
    def record_firing(self, source: str, target: str):
        """Record that two neurons fired together"""
        key = f"{source}->{target}"
        
        if key not in self.firing_history:
            self.firing_history[key] = []
        
        self.firing_history[key].append(datetime.now())
        
        # Strengthen connection (Hebbian learning)
        self._strengthen_connection(source, target)
    
    def _strengthen_connection(self, source: str, target: str):
        """Strengthen synaptic connection"""
        if source not in self.connection_weights:
            self.connection_weights[source] = {}
        
        current_weight = self.connection_weights[source].get(target, 0.5)
        new_weight = min(2.0, current_weight + self.learning_rate)
        self.connection_weights[source][target] = new_weight
        
        logger.debug(f"Connection strengthened: {source} -> {target} = {new_weight:.3f}")
    
    def weaken_unused_connections(self):
        """Weaken connections not used recently"""
        now = datetime.now()
        
        for source, targets in self.connection_weights.items():
            for target, weight in list(targets.items()):
                key = f"{source}->{target}"
                
                # Check last firing
                if key in self.firing_history:
                    last_firing = self.firing_history[key][-1]
                    time_since = (now - last_firing).total_seconds()
                    
                    # Weaken if not used in 60 seconds
                    if time_since > 60:
                        new_weight = max(0.1, weight - self.decay_rate)
                        self.connection_weights[source][target] = new_weight
                        
                        if new_weight < 0.2:
                            logger.info(f"Connection weakened: {source} -> {target} = {new_weight:.3f}")
    
    def get_connection_strength(self, source: str, target: str) -> float:
        """Get current connection strength"""
        return self.connection_weights.get(source, {}).get(target, 0.5)
    
    def find_strongest_connections(self, source: str, n: int = 5) -> List[str]:
        """Find strongest connected modules"""
        if source not in self.connection_weights:
            return []
        
        connections = self.connection_weights[source]
        sorted_targets = sorted(connections.items(), key=lambda x: x[1], reverse=True)
        return [target for target, _ in sorted_targets[:n]]


class CollectiveConsciousness:
    """
    Global workspace theory implementation
    
    All modules contribute to and access a shared conscious state
    """
    
    def __init__(self):
        self.global_workspace: Dict[str, Any] = {}
        self.attention_focus: Optional[str] = None
        self.consciousness_level = 0.0
        self.perceptions: List[Dict] = []
        self.insights: List[Dict] = []
        self.emotional_state = {
            'arousal': 0.5,      # Alertness
            'valence': 0.5,      # Pleasantness
            'dominance': 0.5,    # Control
        }
        
    def broadcast_to_workspace(self, module: str, content: Any, priority: int = 5):
        """Broadcast information to global workspace"""
        self.global_workspace[module] = {
            'content': content,
            'timestamp': datetime.now(),
            'priority': priority,
            'attention_score': self._calculate_attention_score(content, priority)
        }
        
        # Update consciousness level
        self._update_consciousness()
    
    def _calculate_attention_score(self, content: Any, priority: int) -> float:
        """Calculate how much attention this content deserves"""
        # Higher priority = more attention
        # More novel/surprising = more attention
        base_score = priority / 10.0
        
        # Check if content is novel
        is_novel = not any(p['content'] == content for p in self.perceptions[-10:])
        novelty_bonus = 0.3 if is_novel else 0.0
        
        return min(1.0, base_score + novelty_bonus)
    
    def _update_consciousness(self):
        """Update overall consciousness level"""
        # Based on workspace activity
        active_items = len([w for w in self.global_workspace.values() 
                          if (datetime.now() - w['timestamp']).seconds < 60])
        
        self.consciousness_level = min(1.0, active_items / 20.0)
        
    def focus_attention(self, module: str):
        """Focus conscious attention on specific module"""
        self.attention_focus = module
        
        if module in self.global_workspace:
            self.global_workspace[module]['attention_score'] = 1.0
            logger.info(f"🎯 Attention focused on: {module}")
    
    def add_perception(self, source: str, perception: Dict):
        """Add sensory perception to consciousness"""
        self.perceptions.append({
            'source': source,
            'data': perception,
            'timestamp': datetime.now(),
            'integrated': False
        })
        
        # Keep only recent perceptions
        self.perceptions = self.perceptions[-100:]
    
    def generate_insight(self, source: str, insight: str, confidence: float):
        """Generate conscious insight"""
        self.insights.append({
            'source': source,
            'insight': insight,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        
        # Keep only recent insights
        self.insights = self.insights[-50:]
        
        logger.info(f"💡 Insight from {source}: {insight} (confidence: {confidence:.2f})")
    
    def get_workspace_summary(self) -> Dict:
        """Get summary of conscious state"""
        return {
            'consciousness_level': self.consciousness_level,
            'attention_focus': self.attention_focus,
            'workspace_items': len(self.global_workspace),
            'recent_perceptions': len(self.perceptions),
            'insights_generated': len(self.insights),
            'emotional_state': self.emotional_state,
            'top_attention': sorted(
                self.global_workspace.items(),
                key=lambda x: x[1].get('attention_score', 0),
                reverse=True
            )[:5]
        }
    
    def update_emotional_state(self, neurotransmitter: NeurotransmitterType, 
                              concentration: float):
        """Update emotional state based on neurotransmitters"""
        # Map neurotransmitters to emotional dimensions
        effects = {
            NeurotransmitterType.DOPAMINE: {'valence': concentration * 0.3, 'arousal': concentration * 0.1},
            NeurotransmitterType.NOREPINEPHRINE: {'arousal': concentration * 0.4},
            NeurotransmitterType.SEROTONIN: {'valence': concentration * 0.2, 'dominance': concentration * 0.1},
            NeurotransmitterType.GABA: {'arousal': -concentration * 0.3, 'dominance': concentration * 0.1},
            NeurotransmitterType.OXYTOCIN: {'valence': concentration * 0.3, 'dominance': concentration * 0.2},
        }
        
        if neurotransmitter in effects:
            for dimension, delta in effects[neurotransmitter].items():
                self.emotional_state[dimension] = np.clip(
                    self.emotional_state[dimension] + delta, 0.0, 1.0
                )


class BrainStem:
    """
    Core infrastructure - like the brain stem
    Controls vital functions: breathing, heartbeat, basic reflexes
    
    In trading bot: core execution, logging, error handling, basic monitoring
    """
    
    def __init__(self):
        self.vital_signs = {
            'heart_rate': 60,        # Operations per minute
            'breathing_rate': 12,    # Log writes per minute
            'blood_pressure': (120, 80),  # Memory/CPU usage
            'temperature': 37.0,     # System temperature
        }
        self.reflexes: Dict[str, Callable] = {}
        self.is_alive = True
        
    def register_reflex(self, trigger: str, response: Callable):
        """Register automatic reflex response"""
        self.reflexes[trigger] = response
        logger.info(f"Reflex registered: {trigger}")
    
    async def trigger_reflex(self, trigger: str, data: Any):
        """Trigger automatic response"""
        if trigger in self.reflexes:
            try:
                await self.reflexes[trigger](data)
                logger.debug(f"Reflex triggered: {trigger}")
            except Exception as e:
                logger.error(f"Reflex failed: {trigger} - {e}")
    
    def update_vital_signs(self, **kwargs):
        """Update vital system signs"""
        for key, value in kwargs.items():
            if key in self.vital_signs:
                self.vital_signs[key] = value
    
    def check_health(self) -> Dict[str, Any]:
        """Check brain stem health"""
        issues = []
        
        if self.vital_signs['heart_rate'] < 30:
            issues.append("Bradycardia: System too slow")
        elif self.vital_signs['heart_rate'] > 150:
            issues.append("Tachycardia: System overloaded")
        
        if self.vital_signs['temperature'] > 40:
            issues.append("Hyperthermia: CPU overheating")
        
        return {
            'is_alive': self.is_alive,
            'vital_signs': self.vital_signs,
            'issues': issues,
            'status': 'CRITICAL' if issues else 'HEALTHY'
        }


# Global instances
SYNAPTIC_CLEFT = SynapticCleft()
PLASTICITY_ENGINE = NeuralPlasticityEngine()
CONSCIOUSNESS = CollectiveConsciousness()
BRAIN_STEM = BrainStem()


async def global_neural_tick():
    """Global tick for all neural processes"""
    # Weaken unused connections
    PLASTICITY_ENGINE.weaken_unused_connections()
    
    # Update consciousness
    CONSCIOUSNESS._update_consciousness()
    
    # Check brain stem health
    health = BRAIN_STEM.check_health()
    if health['status'] == 'CRITICAL':
        logger.warning(f"🚨 Brain stem critical: {health['issues']}")


if __name__ == "__main__":
    # Test neurotransmitter system
    async def test():
        # Release dopamine (reward)
        signal = NeurotransmitterSignal(
            transmitter_type=NeurotransmitterType.DOPAMINE,
            concentration=0.8,
            source_module="ai_core",
            target_module="risk",
            timestamp=datetime.now()
        )
        
        await SYNAPTIC_CLEFT.release_neurotransmitter(signal)
        print(f"Chemical state: {SYNAPTIC_CLEFT.get_chemical_state()}")
        
        # Test plasticity
        PLASTICITY_ENGINE.record_firing("ai_core", "execution")
        print(f"Connection strength: {PLASTICITY_ENGINE.get_connection_strength('ai_core', 'execution')}")
        
        # Test consciousness
        CONSCIOUSNESS.broadcast_to_workspace("market_data", {"price": 1.0850})
        print(f"Consciousness level: {CONSCIOUSNESS.consciousness_level}")
    
    asyncio.run(test())
