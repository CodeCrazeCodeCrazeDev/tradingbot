"""
Hivemind Neural Mesh Network
=============================

A neural mesh network where nodes communicate telepathically through:
- Direct neural links between nodes
- Thought propagation across the mesh
- Synaptic weight adaptation
- Neural plasticity (connection strength changes)
- Distributed processing across all nodes
- Emergent intelligence from mesh topology

The mesh enables instant, parallel communication between all nodes,
creating a true collective intelligence greater than the sum of parts.
"""

import asyncio
import logging
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import hashlib
import json

logger = logging.getLogger(__name__)


class LinkType(Enum):
    """Types of neural links between nodes"""
    EXCITATORY = "excitatory"       # Strengthens signal
    INHIBITORY = "inhibitory"       # Weakens signal
    MODULATORY = "modulatory"       # Modifies other links
    BIDIRECTIONAL = "bidirectional" # Two-way communication
    BROADCAST = "broadcast"         # One-to-many


class SignalType(Enum):
    """Types of signals transmitted through the mesh"""
    THOUGHT = "thought"             # Analysis/opinion
    ALERT = "alert"                 # Urgent notification
    QUERY = "query"                 # Request for information
    RESPONSE = "response"           # Answer to query
    SYNC = "sync"                   # Synchronization pulse
    LEARNING = "learning"           # Learning signal
    INHIBIT = "inhibit"             # Suppress activity
    AMPLIFY = "amplify"             # Boost activity


class PlasticityRule(Enum):
    """Rules for synaptic plasticity"""
    HEBBIAN = "hebbian"             # "Neurons that fire together wire together"
    ANTI_HEBBIAN = "anti_hebbian"   # Opposite of Hebbian
    STDP = "stdp"                   # Spike-timing dependent plasticity
    BCM = "bcm"                     # Bienenstock-Cooper-Munro rule
    HOMEOSTATIC = "homeostatic"     # Maintain stable activity


@dataclass
class NeuralSignal:
    """A signal transmitted through the neural mesh"""
    signal_id: str
    signal_type: SignalType
    source_node: str
    target_nodes: List[str]  # Empty = broadcast to all
    payload: Dict[str, Any]
    strength: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl: int = 10  # Time to live (hops)
    priority: int = 1
    
    def decay(self, factor: float = 0.9) -> None:
        """Decay signal strength"""
        self.strength *= factor
        self.ttl -= 1
    
    def is_alive(self) -> bool:
        """Check if signal is still active"""
        return self.ttl > 0 and self.strength > 0.01


@dataclass
class NeuralLink:
    """A connection between two nodes in the mesh"""
    link_id: str
    source_node: str
    target_node: str
    link_type: LinkType
    weight: float = 1.0
    plasticity_rule: PlasticityRule = PlasticityRule.HEBBIAN
    
    # Activity tracking
    activation_count: int = 0
    last_activation: Optional[datetime] = None
    success_rate: float = 0.5
    
    # Plasticity parameters
    learning_rate: float = 0.01
    decay_rate: float = 0.001
    min_weight: float = 0.01
    max_weight: float = 5.0
    
    def activate(self, signal_strength: float) -> float:
        """Activate the link and return output strength"""
        self.activation_count += 1
        self.last_activation = datetime.utcnow()
        
        if self.link_type == LinkType.EXCITATORY:
            return signal_strength * self.weight
        elif self.link_type == LinkType.INHIBITORY:
            return -signal_strength * self.weight
        elif self.link_type == LinkType.MODULATORY:
            return signal_strength * (1 + self.weight * 0.1)
        else:
            return signal_strength * self.weight
    
    def update_weight(self, pre_activity: float, post_activity: float, reward: float = 0.0) -> None:
        """Update weight based on plasticity rule"""
        if self.plasticity_rule == PlasticityRule.HEBBIAN:
            # Strengthen if both active
            delta = self.learning_rate * pre_activity * post_activity
            self.weight += delta
        
        elif self.plasticity_rule == PlasticityRule.ANTI_HEBBIAN:
            # Weaken if both active
            delta = -self.learning_rate * pre_activity * post_activity
            self.weight += delta
        
        elif self.plasticity_rule == PlasticityRule.STDP:
            # Timing-dependent (simplified)
            if pre_activity > post_activity:
                delta = self.learning_rate * (pre_activity - post_activity)
            else:
                delta = -self.learning_rate * (post_activity - pre_activity) * 0.5
            self.weight += delta
        
        elif self.plasticity_rule == PlasticityRule.BCM:
            # Threshold-based
            threshold = 0.5
            if post_activity > threshold:
                delta = self.learning_rate * pre_activity * (post_activity - threshold)
            else:
                delta = -self.learning_rate * pre_activity * (threshold - post_activity)
            self.weight += delta
        
        elif self.plasticity_rule == PlasticityRule.HOMEOSTATIC:
            # Maintain target activity
            target = 0.5
            delta = self.learning_rate * (target - post_activity)
            self.weight += delta
        
        # Apply reward modulation
        if reward != 0:
            self.weight += self.learning_rate * reward * pre_activity
        
        # Clamp weight
        self.weight = max(self.min_weight, min(self.max_weight, self.weight))
    
    def decay(self) -> None:
        """Apply weight decay"""
        self.weight *= (1 - self.decay_rate)
        self.weight = max(self.min_weight, self.weight)


@dataclass
class MeshNode:
    """A node in the neural mesh network"""
    node_id: str
    node_type: str
    
    # Activity state
    activation: float = 0.0
    threshold: float = 0.5
    refractory_period: float = 0.0
    
    # Connections
    incoming_links: List[str] = field(default_factory=list)
    outgoing_links: List[str] = field(default_factory=list)
    
    # Signal buffer
    signal_buffer: List[NeuralSignal] = field(default_factory=list)
    max_buffer_size: int = 100
    
    # Memory
    short_term_memory: List[Dict[str, Any]] = field(default_factory=list)
    max_memory_size: int = 50
    
    # Performance
    total_signals_processed: int = 0
    successful_predictions: int = 0
    
    def receive_signal(self, signal: NeuralSignal) -> None:
        """Receive a signal into the buffer"""
        self.signal_buffer.append(signal)
        if len(self.signal_buffer) > self.max_buffer_size:
            self.signal_buffer.pop(0)
    
    def process_signals(self) -> float:
        """Process buffered signals and update activation"""
        if not self.signal_buffer:
            return self.activation
        
        # Sum incoming signals
        total_input = sum(s.strength for s in self.signal_buffer)
        self.signal_buffer.clear()
        
        # Apply activation function (sigmoid)
        self.activation = 1 / (1 + math.exp(-total_input + self.threshold))
        
        self.total_signals_processed += 1
        return self.activation
    
    def should_fire(self) -> bool:
        """Check if node should fire (send signal)"""
        if self.refractory_period > 0:
            self.refractory_period -= 0.1
            return False
        return self.activation > self.threshold
    
    def fire(self) -> None:
        """Fire the node (reset after sending signal)"""
        self.refractory_period = 0.5
        self.activation *= 0.5  # Partial reset
    
    def remember(self, memory: Dict[str, Any]) -> None:
        """Store in short-term memory"""
        self.short_term_memory.append({
            'timestamp': datetime.utcnow().isoformat(),
            'content': memory,
        })
        if len(self.short_term_memory) > self.max_memory_size:
            self.short_term_memory.pop(0)
    
    def recall(self, query: str) -> List[Dict[str, Any]]:
        """Recall from short-term memory"""
        # Simple keyword matching
        results = []
        for mem in self.short_term_memory:
            content_str = json.dumps(mem['content']).lower()
            if query.lower() in content_str:
                results.append(mem)
        return results


class NeuralMesh:
    """
    Neural Mesh Network for Hivemind Communication
    
    Creates a fully connected mesh of nodes that can:
    - Transmit signals instantly across the network
    - Learn optimal communication pathways
    - Adapt connection strengths based on outcomes
    - Exhibit emergent collective behavior
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.nodes: Dict[str, MeshNode] = {}
        self.links: Dict[str, NeuralLink] = {}
        
        # Signal queue for processing
        self.signal_queue: List[NeuralSignal] = []
        
        # Global state
        self.global_activation: float = 0.0
        self.synchronization_level: float = 0.0
        
        # Learning
        self.learning_enabled: bool = True
        self.global_reward: float = 0.0
        
        # Statistics
        self.total_signals_transmitted: int = 0
        self.total_learning_updates: int = 0
        
        logger.info("NeuralMesh initialized")
    
    def add_node(self, node_id: str, node_type: str) -> MeshNode:
        """Add a node to the mesh"""
        node = MeshNode(node_id=node_id, node_type=node_type)
        self.nodes[node_id] = node
        logger.debug(f"Added node: {node_id}")
        return node
    
    def add_link(
        self,
        source_id: str,
        target_id: str,
        link_type: LinkType = LinkType.EXCITATORY,
        weight: float = 1.0,
        plasticity: PlasticityRule = PlasticityRule.HEBBIAN,
    ) -> Optional[NeuralLink]:
        """Add a link between nodes"""
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"Cannot create link: nodes not found")
            return None
        
        link_id = f"{source_id}_to_{target_id}"
        
        link = NeuralLink(
            link_id=link_id,
            source_node=source_id,
            target_node=target_id,
            link_type=link_type,
            weight=weight,
            plasticity_rule=plasticity,
        )
        
        self.links[link_id] = link
        self.nodes[source_id].outgoing_links.append(link_id)
        self.nodes[target_id].incoming_links.append(link_id)
        
        return link
    
    def create_fully_connected(self, node_ids: List[str]) -> None:
        """Create fully connected mesh between nodes"""
        for source in node_ids:
            for target in node_ids:
                if source != target:
                    self.add_link(source, target, LinkType.BIDIRECTIONAL)
    
    def transmit_signal(self, signal: NeuralSignal) -> None:
        """Transmit a signal through the mesh"""
        self.signal_queue.append(signal)
        self.total_signals_transmitted += 1
    
    def broadcast(self, source_id: str, signal_type: SignalType, payload: Dict[str, Any]) -> None:
        """Broadcast signal from source to all connected nodes"""
        signal = NeuralSignal(
            signal_id=f"sig_{datetime.utcnow().strftime('%H%M%S%f')}",
            signal_type=signal_type,
            source_node=source_id,
            target_nodes=[],  # Empty = broadcast
            payload=payload,
        )
        self.transmit_signal(signal)
    
    def send_thought(self, source_id: str, thought: str, confidence: float = 0.5) -> None:
        """Send a thought from one node"""
        self.broadcast(source_id, SignalType.THOUGHT, {
            'thought': thought,
            'confidence': confidence,
        })
    
    def send_alert(self, source_id: str, alert: str, severity: int = 1) -> None:
        """Send an alert through the mesh"""
        signal = NeuralSignal(
            signal_id=f"alert_{datetime.utcnow().strftime('%H%M%S%f')}",
            signal_type=SignalType.ALERT,
            source_node=source_id,
            target_nodes=[],
            payload={'alert': alert, 'severity': severity},
            priority=severity + 5,  # High priority
        )
        self.transmit_signal(signal)
    
    def process_signals(self) -> Dict[str, Any]:
        """Process all queued signals"""
        results = {
            'signals_processed': 0,
            'nodes_activated': 0,
            'links_updated': 0,
        }
        
        # Sort by priority
        self.signal_queue.sort(key=lambda s: s.priority, reverse=True)
        
        while self.signal_queue:
            signal = self.signal_queue.pop(0)
            
            if not signal.is_alive():
                continue
            
            # Determine target nodes
            if signal.target_nodes:
                targets = signal.target_nodes
            else:
                # Broadcast to all connected nodes
                source_node = self.nodes.get(signal.source_node)
                if source_node:
                    targets = [
                        self.links[lid].target_node
                        for lid in source_node.outgoing_links
                    ]
                else:
                    targets = list(self.nodes.keys())
            
            # Transmit to each target
            for target_id in targets:
                if target_id == signal.source_node:
                    continue
                
                target_node = self.nodes.get(target_id)
                if not target_node:
                    continue
                
                # Find link and apply weight
                link_id = f"{signal.source_node}_to_{target_id}"
                link = self.links.get(link_id)
                
                if link:
                    modified_signal = NeuralSignal(
                        signal_id=signal.signal_id,
                        signal_type=signal.signal_type,
                        source_node=signal.source_node,
                        target_nodes=[target_id],
                        payload=signal.payload,
                        strength=link.activate(signal.strength),
                        ttl=signal.ttl - 1,
                        priority=signal.priority,
                    )
                    target_node.receive_signal(modified_signal)
                else:
                    # Direct transmission without link
                    signal.decay()
                    target_node.receive_signal(signal)
                
                results['signals_processed'] += 1
            
            signal.decay()
        
        # Process all nodes
        for node in self.nodes.values():
            old_activation = node.activation
            node.process_signals()
            
            if node.should_fire():
                node.fire()
                results['nodes_activated'] += 1
            
            # Update incoming link weights if learning enabled
            if self.learning_enabled:
                for link_id in node.incoming_links:
                    link = self.links.get(link_id)
                    if link:
                        source_node = self.nodes.get(link.source_node)
                        if source_node:
                            link.update_weight(
                                source_node.activation,
                                node.activation,
                                self.global_reward
                            )
                            results['links_updated'] += 1
        
        # Update global state
        self._update_global_state()
        
        return results
    
    def _update_global_state(self) -> None:
        """Update global mesh state"""
        if not self.nodes:
            return
        
        activations = [n.activation for n in self.nodes.values()]
        self.global_activation = sum(activations) / len(activations)
        
        # Calculate synchronization (variance of activations)
        mean = self.global_activation
        variance = sum((a - mean) ** 2 for a in activations) / len(activations)
        self.synchronization_level = 1 - min(1, variance * 4)  # Higher = more synchronized
    
    def apply_reward(self, reward: float) -> None:
        """Apply global reward signal for learning"""
        self.global_reward = reward
        self.total_learning_updates += 1
    
    def decay_all_links(self) -> None:
        """Apply decay to all links"""
        for link in self.links.values():
            link.decay()
    
    def get_strongest_links(self, n: int = 10) -> List[NeuralLink]:
        """Get the n strongest links"""
        sorted_links = sorted(self.links.values(), key=lambda l: l.weight, reverse=True)
        return sorted_links[:n]
    
    def get_most_active_nodes(self, n: int = 5) -> List[MeshNode]:
        """Get the n most active nodes"""
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.activation, reverse=True)
        return sorted_nodes[:n]
    
    def get_collective_thought(self) -> Dict[str, Any]:
        """Aggregate thoughts from all nodes into collective thought"""
        thoughts = []
        total_confidence = 0
        
        for node in self.nodes.values():
            for mem in node.short_term_memory[-5:]:  # Recent memories
                if 'thought' in mem.get('content', {}):
                    thoughts.append(mem['content'])
                    total_confidence += mem['content'].get('confidence', 0.5)
        
        if not thoughts:
            return {'collective_thought': None, 'confidence': 0}
        
        # Aggregate (simplified - just combine)
        return {
            'collective_thought': thoughts,
            'num_thoughts': len(thoughts),
            'avg_confidence': total_confidence / len(thoughts) if thoughts else 0,
            'global_activation': self.global_activation,
            'synchronization': self.synchronization_level,
        }
    
    def get_mesh_topology(self) -> Dict[str, Any]:
        """Get mesh topology information"""
        return {
            'num_nodes': len(self.nodes),
            'num_links': len(self.links),
            'avg_links_per_node': len(self.links) / len(self.nodes) if self.nodes else 0,
            'global_activation': self.global_activation,
            'synchronization_level': self.synchronization_level,
            'total_signals': self.total_signals_transmitted,
            'learning_updates': self.total_learning_updates,
        }
    
    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive mesh report"""
        return {
            'topology': self.get_mesh_topology(),
            'strongest_links': [
                {'link_id': l.link_id, 'weight': l.weight}
                for l in self.get_strongest_links(5)
            ],
            'most_active_nodes': [
                {'node_id': n.node_id, 'activation': n.activation}
                for n in self.get_most_active_nodes(5)
            ],
            'collective_thought': self.get_collective_thought(),
        }


class TelepathicCommunicator:
    """
    Telepathic Communication Layer
    
    Enables instant, thought-based communication between nodes
    without explicit message passing.
    """
    
    def __init__(self, mesh: NeuralMesh):
        self.mesh = mesh
        self.thought_history: List[Dict[str, Any]] = []
        self.consensus_thoughts: Dict[str, float] = {}
    
    async def broadcast_thought(
        self,
        source_id: str,
        thought: str,
        thought_type: str = "analysis",
        confidence: float = 0.5,
    ) -> None:
        """Broadcast a thought telepathically"""
        self.mesh.send_thought(source_id, thought, confidence)
        
        self.thought_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'source': source_id,
            'thought': thought,
            'type': thought_type,
            'confidence': confidence,
        })
        
        # Process immediately
        self.mesh.process_signals()
    
    async def query_collective(self, query: str) -> Dict[str, Any]:
        """Query the collective consciousness"""
        # Broadcast query
        self.mesh.broadcast("system", SignalType.QUERY, {'query': query})
        self.mesh.process_signals()
        
        # Collect responses from node memories
        responses = []
        for node in self.mesh.nodes.values():
            recalled = node.recall(query)
            responses.extend(recalled)
        
        return {
            'query': query,
            'responses': responses,
            'collective_state': self.mesh.get_collective_thought(),
        }
    
    async def reach_consensus(self, topic: str, options: List[str]) -> Dict[str, Any]:
        """Reach consensus on a topic through telepathic voting"""
        votes: Dict[str, float] = {opt: 0 for opt in options}
        
        # Each node votes based on activation
        for node in self.mesh.nodes.values():
            # Node's vote is weighted by activation
            weight = node.activation
            
            # Simple voting - random for demo, would be based on node analysis
            chosen = random.choice(options)
            votes[chosen] += weight
        
        # Normalize
        total = sum(votes.values())
        if total > 0:
            votes = {k: v / total for k, v in votes.items()}
        
        winner = max(votes, key=votes.get)
        
        self.consensus_thoughts[topic] = votes[winner]
        
        return {
            'topic': topic,
            'votes': votes,
            'winner': winner,
            'confidence': votes[winner],
            'synchronization': self.mesh.synchronization_level,
        }
    
    def get_thought_stream(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent thought stream"""
        return self.thought_history[-limit:]


# Factory function
def create_neural_mesh(
    node_types: List[str],
    fully_connected: bool = True,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[NeuralMesh, TelepathicCommunicator]:
    """Create a neural mesh with nodes"""
    mesh = NeuralMesh(config)
    
    # Add nodes
    for i, node_type in enumerate(node_types):
        mesh.add_node(f"node_{node_type}_{i}", node_type)
    
    # Create connections
    if fully_connected:
        mesh.create_fully_connected(list(mesh.nodes.keys()))
    
    communicator = TelepathicCommunicator(mesh)
    
    return mesh, communicator
