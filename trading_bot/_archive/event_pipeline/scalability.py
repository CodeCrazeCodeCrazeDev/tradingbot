"""
AlphaAlgo Scalability
======================
Partitioning, sharding, load balancing, and cluster coordination.
Enables horizontal scaling of the event pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import time
import hashlib
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Callable, Awaitable,
    Set, TypeVar, Generic, Tuple
)
from collections import defaultdict

from .events import Event, EventType

logger = logging.getLogger(__name__)


class PartitionStrategy(Enum):
    """Partitioning strategies"""
    HASH = auto()           # Hash-based partitioning
    RANGE = auto()          # Range-based partitioning
    ROUND_ROBIN = auto()    # Round-robin distribution
    RANDOM = auto()         # Random distribution
    STICKY = auto()         # Sticky sessions


@dataclass
class PartitionConfig:
    """Configuration for partitioner"""
    num_partitions: int = 12
    strategy: PartitionStrategy = PartitionStrategy.HASH
    rebalance_threshold: float = 0.2  # Trigger rebalance if imbalance > 20%


class Partitioner:
    """
    Partitions events across multiple consumers/shards.
    Ensures related events go to the same partition.
    """
    
    def __init__(self, config: PartitionConfig = None):
        self.config = config or PartitionConfig()
        
        # Partition state
        self._partition_counts: Dict[int, int] = defaultdict(int)
        self._round_robin_index = 0
        self._sticky_assignments: Dict[str, int] = {}
        
        # Metrics
        self.metrics = {
            'events_partitioned': 0,
            'rebalances': 0,
        }
    
    def partition(self, event: Event) -> int:
        """
        Determine partition for event.
        
        Returns:
            Partition number (0 to num_partitions-1)
        """
        key = event.metadata.partition_key or event.event_id
        
        if self.config.strategy == PartitionStrategy.HASH:
            partition = self._hash_partition(key)
        elif self.config.strategy == PartitionStrategy.RANGE:
            partition = self._range_partition(key)
        elif self.config.strategy == PartitionStrategy.ROUND_ROBIN:
            partition = self._round_robin_partition()
        elif self.config.strategy == PartitionStrategy.RANDOM:
            partition = self._random_partition()
        elif self.config.strategy == PartitionStrategy.STICKY:
            partition = self._sticky_partition(key)
        else:
            partition = self._hash_partition(key)
        
        self._partition_counts[partition] += 1
        self.metrics['events_partitioned'] += 1
        
        return partition
    
    def _hash_partition(self, key: str) -> int:
        """Hash-based partitioning"""
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return hash_value % self.config.num_partitions
    
    def _range_partition(self, key: str) -> int:
        """Range-based partitioning (alphabetical)"""
        if not key:
            return 0
        first_char = ord(key[0].upper())
        # Map A-Z to partitions
        partition = (first_char - ord('A')) % self.config.num_partitions
        return max(0, min(partition, self.config.num_partitions - 1))
    
    def _round_robin_partition(self) -> int:
        """Round-robin partitioning"""
        partition = self._round_robin_index
        self._round_robin_index = (self._round_robin_index + 1) % self.config.num_partitions
        return partition
    
    def _random_partition(self) -> int:
        """Random partitioning"""
        return random.randint(0, self.config.num_partitions - 1)
    
    def _sticky_partition(self, key: str) -> int:
        """Sticky session partitioning"""
        if key not in self._sticky_assignments:
            self._sticky_assignments[key] = self._hash_partition(key)
        return self._sticky_assignments[key]
    
    def get_partition_stats(self) -> Dict[str, Any]:
        """Get partition statistics"""
        total = sum(self._partition_counts.values())
        if total == 0:
            return {'partitions': {}, 'imbalance': 0}
        
        expected = total / self.config.num_partitions
        max_deviation = max(
            abs(count - expected) / expected if expected > 0 else 0
            for count in self._partition_counts.values()
        ) if self._partition_counts else 0
        
        return {
            'partitions': dict(self._partition_counts),
            'total': total,
            'imbalance': max_deviation,
            'strategy': self.config.strategy.name,
        }
    
    def needs_rebalance(self) -> bool:
        """Check if rebalancing is needed"""
        stats = self.get_partition_stats()
        return stats['imbalance'] > self.config.rebalance_threshold


class ShardState(Enum):
    """Shard states"""
    ACTIVE = auto()
    DRAINING = auto()
    INACTIVE = auto()
    FAILED = auto()


@dataclass
class Shard:
    """Represents a data shard"""
    shard_id: str
    partition_range: Tuple[int, int]  # (start, end) inclusive
    state: ShardState = ShardState.ACTIVE
    node_id: str = ""
    
    # Metrics
    events_processed: int = 0
    last_event_ns: int = 0
    
    def contains_partition(self, partition: int) -> bool:
        """Check if shard handles partition"""
        return self.partition_range[0] <= partition <= self.partition_range[1]


@dataclass
class ShardManagerConfig:
    """Configuration for shard manager"""
    num_shards: int = 4
    partitions_per_shard: int = 3
    replication_factor: int = 2
    rebalance_interval_seconds: float = 60.0


class ShardManager:
    """
    Manages data shards for horizontal scaling.
    Handles shard assignment, rebalancing, and failover.
    """
    
    def __init__(self, config: ShardManagerConfig = None):
        self.config = config or ShardManagerConfig()
        
        self._shards: Dict[str, Shard] = {}
        self._partition_to_shard: Dict[int, str] = {}
        self._lock = asyncio.Lock()
        
        # Initialize shards
        self._initialize_shards()
    
    def _initialize_shards(self):
        """Initialize shard assignments"""
        total_partitions = self.config.num_shards * self.config.partitions_per_shard
        
        for i in range(self.config.num_shards):
            shard_id = f"shard-{i}"
            start = i * self.config.partitions_per_shard
            end = start + self.config.partitions_per_shard - 1
            
            shard = Shard(
                shard_id=shard_id,
                partition_range=(start, end),
                state=ShardState.ACTIVE,
            )
            self._shards[shard_id] = shard
            
            for p in range(start, end + 1):
                self._partition_to_shard[p] = shard_id
    
    async def get_shard_for_partition(self, partition: int) -> Optional[Shard]:
        """Get shard handling a partition"""
        async with self._lock:
            shard_id = self._partition_to_shard.get(partition)
            if shard_id:
                return self._shards.get(shard_id)
        return None
    
    async def get_active_shards(self) -> List[Shard]:
        """Get all active shards"""
        async with self._lock:
            return [s for s in self._shards.values() if s.state == ShardState.ACTIVE]
    
    async def mark_shard_failed(self, shard_id: str):
        """Mark shard as failed and trigger failover"""
        async with self._lock:
            if shard_id in self._shards:
                self._shards[shard_id].state = ShardState.FAILED
                logger.warning(f"Shard {shard_id} marked as failed")
                await self._trigger_failover(shard_id)
    
    async def _trigger_failover(self, failed_shard_id: str):
        """Redistribute partitions from failed shard"""
        failed_shard = self._shards.get(failed_shard_id)
        if not failed_shard:
            return
        
        # Find active shards to take over
        active_shards = [
            s for s in self._shards.values()
            if s.state == ShardState.ACTIVE and s.shard_id != failed_shard_id
        ]
        
        if not active_shards:
            logger.error("No active shards available for failover")
            return
        
        # Redistribute partitions
        partitions = list(range(
            failed_shard.partition_range[0],
            failed_shard.partition_range[1] + 1
        ))
        
        for i, partition in enumerate(partitions):
            target_shard = active_shards[i % len(active_shards)]
            self._partition_to_shard[partition] = target_shard.shard_id
        
        logger.info(f"Failover complete: {len(partitions)} partitions redistributed")
    
    async def add_shard(self, shard_id: str, node_id: str = "") -> Shard:
        """Add a new shard"""
        async with self._lock:
            # Calculate partition range for new shard
            max_partition = max(self._partition_to_shard.keys()) if self._partition_to_shard else -1
            start = max_partition + 1
            end = start + self.config.partitions_per_shard - 1
            
            shard = Shard(
                shard_id=shard_id,
                partition_range=(start, end),
                state=ShardState.ACTIVE,
                node_id=node_id,
            )
            self._shards[shard_id] = shard
            
            for p in range(start, end + 1):
                self._partition_to_shard[p] = shard_id
            
            logger.info(f"Added shard {shard_id} with partitions {start}-{end}")
            return shard
    
    async def remove_shard(self, shard_id: str):
        """Remove a shard (drain first)"""
        async with self._lock:
            if shard_id in self._shards:
                self._shards[shard_id].state = ShardState.DRAINING
                await self._trigger_failover(shard_id)
                del self._shards[shard_id]
                logger.info(f"Removed shard {shard_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get shard manager statistics"""
        return {
            'num_shards': len(self._shards),
            'active_shards': sum(1 for s in self._shards.values() if s.state == ShardState.ACTIVE),
            'total_partitions': len(self._partition_to_shard),
            'shards': {
                sid: {
                    'state': s.state.name,
                    'partitions': f"{s.partition_range[0]}-{s.partition_range[1]}",
                    'events': s.events_processed,
                }
                for sid, s in self._shards.items()
            },
        }


class LoadBalancerStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = auto()
    LEAST_CONNECTIONS = auto()
    WEIGHTED = auto()
    RANDOM = auto()
    CONSISTENT_HASH = auto()


@dataclass
class NodeInfo:
    """Information about a cluster node"""
    node_id: str
    address: str
    port: int
    weight: float = 1.0
    active_connections: int = 0
    is_healthy: bool = True
    last_health_check: float = 0


class LoadBalancer:
    """
    Load balancer for distributing work across nodes.
    Supports multiple balancing strategies.
    """
    
    def __init__(
        self,
        strategy: LoadBalancerStrategy = LoadBalancerStrategy.ROUND_ROBIN
    ):
        self.strategy = strategy
        
        self._nodes: Dict[str, NodeInfo] = {}
        self._round_robin_index = 0
        self._lock = asyncio.Lock()
        
        # Consistent hash ring
        self._hash_ring: List[Tuple[int, str]] = []
        self._virtual_nodes = 100
    
    async def add_node(self, node: NodeInfo):
        """Add a node to the load balancer"""
        async with self._lock:
            self._nodes[node.node_id] = node
            self._rebuild_hash_ring()
            logger.info(f"Added node {node.node_id} to load balancer")
    
    async def remove_node(self, node_id: str):
        """Remove a node from the load balancer"""
        async with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
                self._rebuild_hash_ring()
                logger.info(f"Removed node {node_id} from load balancer")
    
    async def mark_unhealthy(self, node_id: str):
        """Mark a node as unhealthy"""
        async with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].is_healthy = False
    
    async def mark_healthy(self, node_id: str):
        """Mark a node as healthy"""
        async with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].is_healthy = True
    
    def _rebuild_hash_ring(self):
        """Rebuild consistent hash ring"""
        self._hash_ring = []
        for node_id in self._nodes:
            for i in range(self._virtual_nodes):
                key = f"{node_id}:{i}"
                hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
                self._hash_ring.append((hash_value, node_id))
        self._hash_ring.sort(key=lambda x: x[0])
    
    async def get_node(self, key: str = None) -> Optional[NodeInfo]:
        """
        Get a node for handling a request.
        
        Args:
            key: Optional key for consistent hashing
            
        Returns:
            Selected node or None if no healthy nodes
        """
        async with self._lock:
            healthy_nodes = [n for n in self._nodes.values() if n.is_healthy]
            if not healthy_nodes:
                return None
            
            if self.strategy == LoadBalancerStrategy.ROUND_ROBIN:
                return self._round_robin(healthy_nodes)
            elif self.strategy == LoadBalancerStrategy.LEAST_CONNECTIONS:
                return self._least_connections(healthy_nodes)
            elif self.strategy == LoadBalancerStrategy.WEIGHTED:
                return self._weighted(healthy_nodes)
            elif self.strategy == LoadBalancerStrategy.RANDOM:
                return self._random(healthy_nodes)
            elif self.strategy == LoadBalancerStrategy.CONSISTENT_HASH:
                return self._consistent_hash(key, healthy_nodes)
            
            return healthy_nodes[0]
    
    def _round_robin(self, nodes: List[NodeInfo]) -> NodeInfo:
        """Round-robin selection"""
        node = nodes[self._round_robin_index % len(nodes)]
        self._round_robin_index += 1
        return node
    
    def _least_connections(self, nodes: List[NodeInfo]) -> NodeInfo:
        """Select node with least connections"""
        return min(nodes, key=lambda n: n.active_connections)
    
    def _weighted(self, nodes: List[NodeInfo]) -> NodeInfo:
        """Weighted random selection"""
        total_weight = sum(n.weight for n in nodes)
        r = random.uniform(0, total_weight)
        cumulative = 0
        for node in nodes:
            cumulative += node.weight
            if r <= cumulative:
                return node
        return nodes[-1]
    
    def _random(self, nodes: List[NodeInfo]) -> NodeInfo:
        """Random selection"""
        return random.choice(nodes)
    
    def _consistent_hash(self, key: str, nodes: List[NodeInfo]) -> NodeInfo:
        """Consistent hash selection"""
        if not key or not self._hash_ring:
            return self._round_robin(nodes)
        
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        
        # Binary search for position in ring
        left, right = 0, len(self._hash_ring) - 1
        while left < right:
            mid = (left + right) // 2
            if self._hash_ring[mid][0] < hash_value:
                left = mid + 1
            else:
                right = mid
        
        # Find first healthy node from position
        for i in range(len(self._hash_ring)):
            idx = (left + i) % len(self._hash_ring)
            node_id = self._hash_ring[idx][1]
            if node_id in self._nodes and self._nodes[node_id].is_healthy:
                return self._nodes[node_id]
        
        return nodes[0] if nodes else None
    
    async def increment_connections(self, node_id: str):
        """Increment active connections for node"""
        async with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].active_connections += 1
    
    async def decrement_connections(self, node_id: str):
        """Decrement active connections for node"""
        async with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].active_connections = max(
                    0, self._nodes[node_id].active_connections - 1
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        return {
            'strategy': self.strategy.name,
            'num_nodes': len(self._nodes),
            'healthy_nodes': sum(1 for n in self._nodes.values() if n.is_healthy),
            'nodes': {
                nid: {
                    'address': f"{n.address}:{n.port}",
                    'healthy': n.is_healthy,
                    'connections': n.active_connections,
                    'weight': n.weight,
                }
                for nid, n in self._nodes.items()
            },
        }


class ClusterCoordinator:
    """
    Coordinates cluster membership and leader election.
    Manages distributed state across nodes.
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        
        self._members: Dict[str, NodeInfo] = {}
        self._leader_id: Optional[str] = None
        self._is_leader = False
        
        self._lock = asyncio.Lock()
        
        # Heartbeat tracking
        self._last_heartbeat: Dict[str, float] = {}
        self._heartbeat_timeout = 30.0
        
        # Callbacks
        self._on_leader_change: List[Callable[[str], Awaitable[None]]] = []
        self._on_member_join: List[Callable[[str], Awaitable[None]]] = []
        self._on_member_leave: List[Callable[[str], Awaitable[None]]] = []
        
        # Background task
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    def on_leader_change(self, callback: Callable[[str], Awaitable[None]]):
        """Register leader change callback"""
        self._on_leader_change.append(callback)
    
    def on_member_join(self, callback: Callable[[str], Awaitable[None]]):
        """Register member join callback"""
        self._on_member_join.append(callback)
    
    def on_member_leave(self, callback: Callable[[str], Awaitable[None]]):
        """Register member leave callback"""
        self._on_member_leave.append(callback)
    
    async def start(self):
        """Start cluster coordination"""
        self._running = True
        self._task = asyncio.create_task(self._coordination_loop())
        logger.info(f"Cluster coordinator started for node {self.node_id}")
    
    async def stop(self):
        """Stop cluster coordination"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _coordination_loop(self):
        """Background coordination loop"""
        while self._running:
            try:
                await self._check_heartbeats()
                await self._elect_leader()
                await asyncio.sleep(5.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Coordination error: {e}")
                await asyncio.sleep(1)
    
    async def register_member(self, node: NodeInfo):
        """Register a cluster member"""
        async with self._lock:
            is_new = node.node_id not in self._members
            self._members[node.node_id] = node
            self._last_heartbeat[node.node_id] = time.time()
        
        if is_new:
            logger.info(f"Member {node.node_id} joined cluster")
            for callback in self._on_member_join:
                try:
                    await callback(node.node_id)
                except Exception as e:
                    logger.error(f"Member join callback error: {e}")
    
    async def heartbeat(self, node_id: str):
        """Record heartbeat from member"""
        async with self._lock:
            if node_id in self._members:
                self._last_heartbeat[node_id] = time.time()
    
    async def _check_heartbeats(self):
        """Check for timed out members"""
        now = time.time()
        async with self._lock:
            timed_out = [
                nid for nid, last in self._last_heartbeat.items()
                if now - last > self._heartbeat_timeout
            ]
        
        for node_id in timed_out:
            await self._remove_member(node_id)
    
    async def _remove_member(self, node_id: str):
        """Remove a member from cluster"""
        async with self._lock:
            if node_id in self._members:
                del self._members[node_id]
                self._last_heartbeat.pop(node_id, None)
        
        logger.info(f"Member {node_id} left cluster")
        
        for callback in self._on_member_leave:
            try:
                await callback(node_id)
            except Exception as e:
                logger.error(f"Member leave callback error: {e}")
        
        # Re-elect if leader left
        if node_id == self._leader_id:
            await self._elect_leader()
    
    async def _elect_leader(self):
        """Simple leader election (lowest node ID wins)"""
        async with self._lock:
            if not self._members:
                self._leader_id = None
                self._is_leader = False
                return
            
            # Lowest node ID becomes leader
            new_leader = min(self._members.keys())
            
            if new_leader != self._leader_id:
                old_leader = self._leader_id
                self._leader_id = new_leader
                self._is_leader = (new_leader == self.node_id)
                
                logger.info(f"Leader elected: {new_leader}")
                
                for callback in self._on_leader_change:
                    try:
                        await callback(new_leader)
                    except Exception as e:
                        logger.error(f"Leader change callback error: {e}")
    
    def is_leader(self) -> bool:
        """Check if this node is the leader"""
        return self._is_leader
    
    def get_leader(self) -> Optional[str]:
        """Get current leader ID"""
        return self._leader_id
    
    def get_members(self) -> List[str]:
        """Get list of member IDs"""
        return list(self._members.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cluster statistics"""
        return {
            'node_id': self.node_id,
            'is_leader': self._is_leader,
            'leader_id': self._leader_id,
            'num_members': len(self._members),
            'members': list(self._members.keys()),
        }
