"""
Self-Rewiring Network Infrastructure

Adaptive routing, resource allocation, topology evolution, and load balancing
for optimal information flow and system performance.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class NetworkNodeType(Enum):
    """Types of network nodes"""
    DATA_SOURCE = "data_source"
    PROCESSOR = "processor"
    ANALYZER = "analyzer"
    DECISION_MAKER = "decision_maker"
    EXECUTOR = "executor"
    STORAGE = "storage"


class RoutingStrategy(Enum):
    """Routing strategies"""
    SHORTEST_PATH = "shortest_path"
    LEAST_LOADED = "least_loaded"
    HIGHEST_PRIORITY = "highest_priority"
    ADAPTIVE = "adaptive"
    PREDICTIVE = "predictive"


@dataclass
class NetworkNode:
    """Network node representation"""
    node_id: str
    node_type: NetworkNodeType
    capacity: float
    current_load: float = 0.0
    connections: Set[str] = field(default_factory=set)
    processing_time_ms: float = 10.0
    reliability: float = 0.99
    
    def utilization(self) -> float:
        """Get current utilization percentage"""
        return self.current_load / self.capacity if self.capacity > 0 else 0.0
    
    def available_capacity(self) -> float:
        """Get available capacity"""
        return max(0.0, self.capacity - self.current_load)


@dataclass
class DataFlow:
    """Data flow through network"""
    flow_id: str
    source_node: str
    destination_node: str
    data_size_mb: float
    priority: int
    created_at: datetime
    route: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    completed: bool = False


@dataclass
class TopologyChange:
    """Network topology change"""
    change_id: str
    change_type: str  # add_node, remove_node, add_edge, remove_edge, modify_capacity
    timestamp: datetime
    details: Dict[str, Any]
    reason: str
    expected_improvement: float


class AdaptiveRoutingNetwork:
    """
    Adaptive routing network that dynamically optimizes data flow paths.
    
    Features:
    - Real-time route optimization
    - Congestion avoidance
    - Predictive routing
    - Multi-path routing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.nodes: Dict[str, NetworkNode] = {}
        self.edges: Dict[Tuple[str, str], float] = {}  # (source, dest) -> weight
        self.active_flows: Dict[str, DataFlow] = {}
        self.routing_history: deque = deque(maxlen=1000)
        self.performance_metrics = {
            'avg_latency_ms': 0.0,
            'throughput_mbps': 0.0,
            'packet_loss_rate': 0.0,
            'route_optimizations': 0,
        }
        
    def add_node(self, node: NetworkNode):
        """Add a node to the network"""
        self.nodes[node.node_id] = node
        logger.info(f"Added node {node.node_id} of type {node.node_type.value}")
    
    def add_edge(self, source: str, dest: str, weight: float = 1.0):
        """Add an edge between nodes"""
        if source in self.nodes and dest in self.nodes:
            self.edges[(source, dest)] = weight
            self.nodes[source].connections.add(dest)
            logger.debug(f"Added edge {source} -> {dest} with weight {weight}")
    
    def find_optimal_route(self, source: str, dest: str, 
                          strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE) -> List[str]:
        """Find optimal route between nodes"""
        if source not in self.nodes or dest not in self.nodes:
            return []
        
        if strategy == RoutingStrategy.SHORTEST_PATH:
            return self._dijkstra(source, dest)
        elif strategy == RoutingStrategy.LEAST_LOADED:
            return self._least_loaded_path(source, dest)
        elif strategy == RoutingStrategy.ADAPTIVE:
            return self._adaptive_routing(source, dest)
        else:
            return self._dijkstra(source, dest)
    
    def _dijkstra(self, source: str, dest: str) -> List[str]:
        """Dijkstra's shortest path algorithm"""
        distances = {node: float('inf') for node in self.nodes}
        distances[source] = 0
        previous = {}
        unvisited = set(self.nodes.keys())
        
        while unvisited:
            current = min(unvisited, key=lambda n: distances[n])
            if distances[current] == float('inf'):
                break
            
            unvisited.remove(current)
            
            if current == dest:
                break
            
            for neighbor in self.nodes[current].connections:
                if neighbor in unvisited:
                    edge_weight = self.edges.get((current, neighbor), 1.0)
                    distance = distances[current] + edge_weight
                    
                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous[neighbor] = current
        
        # Reconstruct path
        if dest not in previous and dest != source:
            return []
        
        path = []
        current = dest
        while current != source:
            path.append(current)
            if current not in previous:
                return []
            current = previous[current]
        path.append(source)
        path.reverse()
        
        return path
    
    def _least_loaded_path(self, source: str, dest: str) -> List[str]:
        """Find path through least loaded nodes"""
        # Modified Dijkstra using node load as weight
        distances = {node: float('inf') for node in self.nodes}
        distances[source] = 0
        previous = {}
        unvisited = set(self.nodes.keys())
        
        while unvisited:
            current = min(unvisited, key=lambda n: distances[n])
            if distances[current] == float('inf'):
                break
            
            unvisited.remove(current)
            
            if current == dest:
                break
            
            for neighbor in self.nodes[current].connections:
                if neighbor in unvisited:
                    # Weight by node utilization
                    node_load = self.nodes[neighbor].utilization()
                    edge_weight = self.edges.get((current, neighbor), 1.0)
                    distance = distances[current] + edge_weight * (1 + node_load)
                    
                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous[neighbor] = current
        
        # Reconstruct path
        if dest not in previous and dest != source:
            return []
        
        path = []
        current = dest
        while current != source:
            path.append(current)
            if current not in previous:
                return []
            current = previous[current]
        path.append(source)
        path.reverse()
        
        return path
    
    def _adaptive_routing(self, source: str, dest: str) -> List[str]:
        """Adaptive routing based on current network state"""
        # Combine shortest path and load balancing
        shortest = self._dijkstra(source, dest)
        least_loaded = self._least_loaded_path(source, dest)
        
        # Calculate scores for both paths
        def path_score(path: List[str]) -> float:
            if not path:
                return float('inf')
            
            length_penalty = len(path)
            load_penalty = sum(self.nodes[n].utilization() for n in path)
            
            return length_penalty + load_penalty * 2
        
        shortest_score = path_score(shortest)
        loaded_score = path_score(least_loaded)
        
        return shortest if shortest_score < loaded_score else least_loaded
    
    async def route_data_flow(self, flow: DataFlow) -> bool:
        """Route a data flow through the network"""
        route = self.find_optimal_route(flow.source_node, flow.destination_node)
        
        if not route:
            logger.warning(f"No route found for flow {flow.flow_id}")
            return False
        
        flow.route = route
        
        # Calculate latency
        latency = 0.0
        for node_id in route:
            node = self.nodes[node_id]
            latency += node.processing_time_ms
            node.current_load += flow.data_size_mb
        
        flow.latency_ms = latency
        self.active_flows[flow.flow_id] = flow
        self.routing_history.append({
            'flow_id': flow.flow_id,
            'route': route,
            'latency_ms': latency,
            'timestamp': datetime.utcnow(),
        })
        
        # Update metrics
        self.performance_metrics['avg_latency_ms'] = np.mean([
            h['latency_ms'] for h in list(self.routing_history)[-100:]
        ])
        
        logger.debug(f"Routed flow {flow.flow_id} through {len(route)} nodes")
        return True
    
    def complete_flow(self, flow_id: str):
        """Mark flow as completed and free resources"""
        if flow_id in self.active_flows:
            flow = self.active_flows[flow_id]
            
            # Free node capacity
            for node_id in flow.route:
                if node_id in self.nodes:
                    self.nodes[node_id].current_load -= flow.data_size_mb
                    self.nodes[node_id].current_load = max(0.0, self.nodes[node_id].current_load)
            
            flow.completed = True
            del self.active_flows[flow_id]
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status"""
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'active_flows': len(self.active_flows),
            'avg_node_utilization': np.mean([n.utilization() for n in self.nodes.values()]),
            'performance_metrics': self.performance_metrics.copy(),
        }


class ResourceAllocationEngine:
    """
    Resource allocation engine that optimizes compute resource distribution.
    
    Allocates:
    - CPU cores
    - Memory
    - GPU resources
    - Network bandwidth
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.total_resources = {
            'cpu_cores': self.config.get('cpu_cores', 16),
            'memory_gb': self.config.get('memory_gb', 64),
            'gpu_count': self.config.get('gpu_count', 2),
            'network_gbps': self.config.get('network_gbps', 10),
        }
        self.allocations: Dict[str, Dict[str, float]] = {}
        self.allocation_history: deque = deque(maxlen=1000)
        
    def allocate_resources(self, task_id: str, requirements: Dict[str, float],
                          priority: int = 5) -> bool:
        """Allocate resources to a task"""
        # Check if resources are available
        current_usage = self._get_current_usage()
        
        can_allocate = all(
            current_usage[resource] + requirements.get(resource, 0) <= total
            for resource, total in self.total_resources.items()
        )
        
        if not can_allocate:
            logger.warning(f"Insufficient resources for task {task_id}")
            return False
        
        self.allocations[task_id] = {
            **requirements,
            'priority': priority,
            'allocated_at': datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Allocated resources to task {task_id}")
        return True
    
    def release_resources(self, task_id: str):
        """Release resources from a task"""
        if task_id in self.allocations:
            del self.allocations[task_id]
            logger.info(f"Released resources from task {task_id}")
    
    def _get_current_usage(self) -> Dict[str, float]:
        """Get current resource usage"""
        usage = {resource: 0.0 for resource in self.total_resources}
        
        for allocation in self.allocations.values():
            for resource in self.total_resources:
                usage[resource] += allocation.get(resource, 0.0)
        
        return usage
    
    def optimize_allocation(self) -> List[str]:
        """Optimize resource allocation based on priorities"""
        # Sort tasks by priority
        sorted_tasks = sorted(
            self.allocations.items(),
            key=lambda x: x[1].get('priority', 5),
            reverse=True
        )
        
        # Reallocate if needed
        optimizations = []
        current_usage = self._get_current_usage()
        
        for resource, usage in current_usage.items():
            if usage > self.total_resources[resource] * 0.9:
                optimizations.append(f"High {resource} usage: {usage}/{self.total_resources[resource]}")
        
        return optimizations
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get resource allocation status"""
        usage = self._get_current_usage()
        
        return {
            'total_resources': self.total_resources.copy(),
            'current_usage': usage,
            'utilization': {
                resource: usage[resource] / total if total > 0 else 0.0
                for resource, total in self.total_resources.items()
            },
            'active_allocations': len(self.allocations),
        }


class TopologyEvolutionEngine:
    """
    Topology evolution engine that modifies network structure for efficiency.
    
    Evolves:
    - Node additions/removals
    - Edge weight adjustments
    - Capacity modifications
    - Structure optimization
    """
    
    def __init__(self, network: AdaptiveRoutingNetwork, config: Optional[Dict[str, Any]] = None):
        self.network = network
        self.config = config or {}
        self.evolution_history: List[TopologyChange] = []
        self.performance_baseline = {}
        
    async def evolve_topology(self) -> List[TopologyChange]:
        """Evolve network topology based on performance"""
        changes = []
        
        # Analyze current performance
        status = self.network.get_network_status()
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks()
        
        for bottleneck in bottlenecks:
            change = await self._resolve_bottleneck(bottleneck)
            if change:
                changes.append(change)
                self.evolution_history.append(change)
        
        # Optimize underutilized nodes
        optimizations = self._optimize_underutilized()
        changes.extend(optimizations)
        
        logger.info(f"Applied {len(changes)} topology changes")
        return changes
    
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify network bottlenecks"""
        bottlenecks = []
        
        for node_id, node in self.network.nodes.items():
            if node.utilization() > 0.85:
                bottlenecks.append({
                    'type': 'overloaded_node',
                    'node_id': node_id,
                    'utilization': node.utilization(),
                })
        
        return bottlenecks
    
    async def _resolve_bottleneck(self, bottleneck: Dict[str, Any]) -> Optional[TopologyChange]:
        """Resolve a network bottleneck"""
        if bottleneck['type'] == 'overloaded_node':
            node_id = bottleneck['node_id']
            node = self.network.nodes[node_id]
            
            # Increase capacity
            old_capacity = node.capacity
            node.capacity *= 1.5
            
            change = TopologyChange(
                change_id=f"change_{len(self.evolution_history)}",
                change_type='modify_capacity',
                timestamp=datetime.utcnow(),
                details={
                    'node_id': node_id,
                    'old_capacity': old_capacity,
                    'new_capacity': node.capacity,
                },
                reason=f"Resolve overload on {node_id}",
                expected_improvement=0.3,
            )
            
            return change
        
        return None
    
    def _optimize_underutilized(self) -> List[TopologyChange]:
        """Optimize underutilized resources"""
        changes = []
        
        for node_id, node in self.network.nodes.items():
            if node.utilization() < 0.1 and node.capacity > 10:
                # Reduce capacity to save resources
                old_capacity = node.capacity
                node.capacity *= 0.7
                
                change = TopologyChange(
                    change_id=f"change_{len(self.evolution_history)}",
                    change_type='modify_capacity',
                    timestamp=datetime.utcnow(),
                    details={
                        'node_id': node_id,
                        'old_capacity': old_capacity,
                        'new_capacity': node.capacity,
                    },
                    reason=f"Optimize underutilized {node_id}",
                    expected_improvement=0.1,
                )
                
                changes.append(change)
                self.evolution_history.append(change)
        
        return changes


class LoadBalancingIntelligence:
    """
    Load balancing intelligence that predicts and prevents bottlenecks.
    
    Features:
    - Predictive load forecasting
    - Proactive rebalancing
    - Anomaly detection
    - Capacity planning
    """
    
    def __init__(self, network: AdaptiveRoutingNetwork, config: Optional[Dict[str, Any]] = None):
        self.network = network
        self.config = config or {}
        self.load_history: deque = deque(maxlen=1000)
        self.predictions: Dict[str, List[float]] = {}
        
    async def predict_load(self, node_id: str, horizon_minutes: int = 30) -> List[float]:
        """Predict future load for a node"""
        if node_id not in self.network.nodes:
            return []
        
        # Simple moving average prediction
        recent_loads = [h['load'] for h in list(self.load_history)[-100:] 
                       if h.get('node_id') == node_id]
        
        if not recent_loads:
            return [0.0] * horizon_minutes
        
        avg_load = np.mean(recent_loads)
        trend = np.mean(np.diff(recent_loads)) if len(recent_loads) > 1 else 0.0
        
        predictions = []
        for i in range(horizon_minutes):
            predicted_load = avg_load + trend * i
            predictions.append(max(0.0, predicted_load))
        
        self.predictions[node_id] = predictions
        return predictions
    
    async def rebalance_load(self) -> Dict[str, Any]:
        """Rebalance load across network"""
        rebalancing_actions = []
        
        # Identify overloaded and underloaded nodes
        overloaded = []
        underloaded = []
        
        for node_id, node in self.network.nodes.items():
            utilization = node.utilization()
            if utilization > 0.8:
                overloaded.append((node_id, utilization))
            elif utilization < 0.3:
                underloaded.append((node_id, utilization))
        
        # Migrate flows from overloaded to underloaded
        for overloaded_node, _ in overloaded[:3]:
            # Find flows through this node
            flows_to_migrate = [
                flow for flow in self.network.active_flows.values()
                if overloaded_node in flow.route and not flow.completed
            ]
            
            for flow in flows_to_migrate[:2]:
                # Try to reroute
                self.network.complete_flow(flow.flow_id)
                await self.network.route_data_flow(flow)
                
                rebalancing_actions.append({
                    'action': 'reroute_flow',
                    'flow_id': flow.flow_id,
                    'from_node': overloaded_node,
                })
        
        return {
            'actions_taken': len(rebalancing_actions),
            'actions': rebalancing_actions,
            'overloaded_nodes': len(overloaded),
            'underloaded_nodes': len(underloaded),
        }
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect load anomalies"""
        anomalies = []
        
        for node_id, node in self.network.nodes.items():
            utilization = node.utilization()
            
            # Check for sudden spikes
            if utilization > 0.95:
                anomalies.append({
                    'type': 'critical_overload',
                    'node_id': node_id,
                    'utilization': utilization,
                    'severity': 'critical',
                })
            
            # Check for predictions
            if node_id in self.predictions:
                future_loads = self.predictions[node_id]
                if any(load > node.capacity * 0.9 for load in future_loads[:10]):
                    anomalies.append({
                        'type': 'predicted_overload',
                        'node_id': node_id,
                        'predicted_in_minutes': next(i for i, load in enumerate(future_loads) 
                                                    if load > node.capacity * 0.9),
                        'severity': 'warning',
                    })
        
        return anomalies
    
    def record_load(self, node_id: str, load: float):
        """Record load measurement"""
        self.load_history.append({
            'node_id': node_id,
            'load': load,
            'timestamp': datetime.utcnow(),
        })
