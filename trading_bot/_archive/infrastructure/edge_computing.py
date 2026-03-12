"""
Edge Computing and Infrastructure Evolution
Implements edge deployment, multi-cloud failover, low-latency mesh network
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import time
import numpy

import logging

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


logger = logging.getLogger(__name__)



class CloudProvider(Enum):
    """Cloud provider options"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ALIBABA = "alibaba"
    EDGE = "edge"


class NodeStatus(Enum):
    """Node health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


@dataclass
class ComputeNode:
    """Edge computing node"""
    node_id: str
    provider: CloudProvider
    region: str
    latency_ms: float
    cpu_usage: float
    memory_usage: float
    status: NodeStatus
    last_heartbeat: datetime


@dataclass
class LatencyMetrics:
    """Network latency metrics"""
    avg_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    jitter: float


class EdgeComputingManager:
    """Edge computing deployment and management"""
    
    def __init__(self):
        self.nodes: Dict[str, ComputeNode] = {}
        self.active_node: Optional[str] = None
        self._initialize_nodes()
        
    def _initialize_nodes(self):
        """Initialize edge computing nodes"""
        # Edge nodes (lowest latency)
        self.nodes['edge-ny-1'] = ComputeNode(
            'edge-ny-1', CloudProvider.EDGE, 'us-east-1',
            1.5, 0.3, 0.4, NodeStatus.HEALTHY, datetime.now()
        )
        self.nodes['edge-london-1'] = ComputeNode(
            'edge-london-1', CloudProvider.EDGE, 'eu-west-1',
            2.0, 0.25, 0.35, NodeStatus.HEALTHY, datetime.now()
        )
        
        # Cloud nodes (backup)
        self.nodes['aws-ny-1'] = ComputeNode(
            'aws-ny-1', CloudProvider.AWS, 'us-east-1',
            5.0, 0.2, 0.3, NodeStatus.HEALTHY, datetime.now()
        )
        self.nodes['azure-london-1'] = ComputeNode(
            'azure-london-1', CloudProvider.AZURE, 'uk-south',
            6.0, 0.15, 0.25, NodeStatus.HEALTHY, datetime.now()
        )
        
        # Select initial active node
        self.active_node = 'edge-ny-1'
    
    async def deploy_to_edge(self, strategy_code: str, config: Dict) -> Dict:
        """Deploy trading strategy to edge nodes"""
        
        # Select optimal node
        optimal_node = self._select_optimal_node()
        
        # Deploy to node
        deployment = {
            'node_id': optimal_node,
            'strategy': strategy_code,
            'config': config,
            'timestamp': datetime.now(),
            'latency': self.nodes[optimal_node].latency_ms,
            'status': 'deployed'
        }
        
        # Update active node
        self.active_node = optimal_node
        
        return deployment
    
    def _select_optimal_node(self) -> str:
        """Select node with lowest latency and healthy status"""
        healthy_nodes = [
            (node_id, node) for node_id, node in self.nodes.items()
            if node.status == NodeStatus.HEALTHY
        ]
        
        if not healthy_nodes:
            raise RuntimeError("No healthy nodes available")
        
        # Sort by latency
        optimal = min(healthy_nodes, key=lambda x: x[1].latency_ms)
        return optimal[0]
    
    async def monitor_nodes(self) -> Dict:
        """Monitor all node health"""
        health_report = {}
        
        for node_id, node in self.nodes.items():
            # Simulate health check
            health_report[node_id] = {
                'status': node.status.value,
                'latency_ms': node.latency_ms,
                'cpu_usage': node.cpu_usage,
                'memory_usage': node.memory_usage,
                'uptime': (datetime.now() - node.last_heartbeat).total_seconds()
            }
        
        return health_report
    
    def get_active_node(self) -> ComputeNode:
        """Get currently active node"""
        if self.active_node and self.active_node in self.nodes:
            return self.nodes[self.active_node]
        raise RuntimeError("No active node")


class MultiCloudFailoverSystem:
    """Multi-cloud failover for high availability"""
    
    def __init__(self):
        self.providers: Dict[CloudProvider, Dict] = {}
        self.active_provider: CloudProvider = CloudProvider.AWS
        self.failover_history: List[Dict] = []
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize cloud providers"""
        self.providers = {
            CloudProvider.AWS: {
                'status': 'active',
                'uptime': 0.9999,
                'cost_per_hour': 2.50,
                'regions': ['us-east-1', 'us-west-2', 'eu-west-1']
            },
            CloudProvider.AZURE: {
                'status': 'standby',
                'uptime': 0.9998,
                'cost_per_hour': 2.40,
                'regions': ['eastus', 'westus', 'uksouth']
            },
            CloudProvider.GCP: {
                'status': 'standby',
                'uptime': 0.9997,
                'cost_per_hour': 2.30,
                'regions': ['us-central1', 'europe-west1', 'asia-east1']
            }
        }
    
    async def detect_failure(self, provider: CloudProvider) -> bool:
        """Detect provider failure"""
        if provider not in self.providers:
            return True
        
        provider_info = self.providers[provider]
        
        # Simulate failure detection
        # In production, would check actual health metrics
        if provider_info['status'] == 'failed':
            return True
        
        # Random failure simulation (very low probability)
        failure_prob = 1 - provider_info['uptime']
        return np.random.random() < failure_prob
    
    async def execute_failover(
        self,
        from_provider: CloudProvider,
        to_provider: CloudProvider
    ) -> Dict:
        """Execute failover to backup provider"""
        
        start_time = time.time()
        
        # Mark old provider as failed
        self.providers[from_provider]['status'] = 'failed'
        
        # Activate new provider
        self.providers[to_provider]['status'] = 'active'
        self.active_provider = to_provider
        
        # Record failover
        failover_event = {
            'from': from_provider.value,
            'to': to_provider.value,
            'timestamp': datetime.now(),
            'duration_ms': (time.time() - start_time) * 1000,
            'reason': 'provider_failure'
        }
        
        self.failover_history.append(failover_event)
        
        return failover_event
    
    async def auto_failover(self) -> Optional[Dict]:
        """Automatically failover if active provider fails"""
        
        # Check active provider
        if await self.detect_failure(self.active_provider):
            # Find healthy backup
            for provider, info in self.providers.items():
                if provider != self.active_provider and info['status'] != 'failed':
                    return await self.execute_failover(self.active_provider, provider)
        
        return None
    
    def get_failover_stats(self) -> Dict:
        """Get failover statistics"""
        if not self.failover_history:
            return {
                'total_failovers': 0,
                'avg_duration_ms': 0,
                'uptime': 1.0
            }
        
        total = len(self.failover_history)
        avg_duration = np.mean([f['duration_ms'] for f in self.failover_history])
        
        # Calculate uptime (simplified)
        uptime = 1 - (total * avg_duration / 1000) / (24 * 3600)  # Assume 24h period
        
        return {
            'total_failovers': total,
            'avg_duration_ms': avg_duration,
            'uptime': max(uptime, 0.99),
            'history': self.failover_history[-10:]  # Last 10 events
        }


class LowLatencyMeshNetwork:
    """Low-latency global mesh network"""
    
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.connections: Dict[str, List[str]] = {}
        self.latency_matrix: Dict[tuple, float] = {}
        self._initialize_mesh()
        
    def _initialize_mesh(self):
        """Initialize mesh network topology"""
        # Define nodes
        self.nodes = {
            'ny': {'region': 'us-east', 'lat': 40.7, 'lon': -74.0},
            'london': {'region': 'eu-west', 'lat': 51.5, 'lon': -0.1},
            'tokyo': {'region': 'asia-east', 'lat': 35.7, 'lon': 139.7},
            'singapore': {'region': 'asia-southeast', 'lat': 1.3, 'lon': 103.8},
            'frankfurt': {'region': 'eu-central', 'lat': 50.1, 'lon': 8.7}
        }
        
        # Define connections (full mesh)
        for node1 in self.nodes:
            self.connections[node1] = [n for n in self.nodes if n != node1]
        
        # Calculate latencies based on distance
        self._calculate_latencies()
    
    def _calculate_latencies(self):
        """Calculate latencies between nodes"""
        for node1, info1 in self.nodes.items():
            for node2, info2 in self.nodes.items():
                if node1 != node2:
                    # Simplified: latency based on great circle distance
                    distance = self._haversine_distance(
                        info1['lat'], info1['lon'],
                        info2['lat'], info2['lon']
                    )
                    # Assume ~100ms per 10,000 km
                    latency = distance / 10000 * 100
                    self.latency_matrix[(node1, node2)] = latency
    
    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate great circle distance in km"""
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
    
    async def find_optimal_path(
        self,
        source: str,
        destination: str
    ) -> Dict:
        """Find optimal routing path"""
        
        if source not in self.nodes or destination not in self.nodes:
            raise ValueError("Invalid nodes")
        
        # For mesh network, direct connection is optimal
        direct_latency = self.latency_matrix.get((source, destination), 999)
        
        # Could implement multi-hop routing for redundancy
        return {
            'source': source,
            'destination': destination,
            'path': [source, destination],
            'latency_ms': direct_latency,
            'hops': 1
        }
    
    async def measure_latency(self, source: str, destination: str) -> LatencyMetrics:
        """Measure latency between nodes"""
        
        # Simulate multiple measurements
        base_latency = self.latency_matrix.get((source, destination), 100)
        measurements = np.random.normal(base_latency, base_latency * 0.1, 100)
        
        return LatencyMetrics(
            avg_latency=float(np.mean(measurements)),
            p50_latency=float(np.percentile(measurements, 50)),
            p95_latency=float(np.percentile(measurements, 95)),
            p99_latency=float(np.percentile(measurements, 99)),
            jitter=float(np.std(measurements))
        )
    
    def get_network_topology(self) -> Dict:
        """Get complete network topology"""
        return {
            'nodes': self.nodes,
            'connections': self.connections,
            'total_nodes': len(self.nodes),
            'total_connections': sum(len(c) for c in self.connections.values()) // 2
        }


class ZeroTrustSecurity:
    """Zero-trust security architecture"""
    
    def __init__(self):
        self.authenticated_sessions: Dict[str, Dict] = {}
        self.access_policies: Dict[str, List[str]] = {}
        self.audit_log: List[Dict] = []
        
    async def authenticate(
        self,
        user_id: str,
        credentials: Dict,
        context: Dict
    ) -> Dict:
        """Authenticate user with zero-trust principles"""
        
        # Verify identity
        identity_verified = self._verify_identity(credentials)
        
        # Check device posture
        device_trusted = self._check_device_posture(context.get('device', {}))
        
        # Verify location
        location_valid = self._verify_location(context.get('location', {}))
        
        # Risk assessment
        risk_score = self._assess_risk(user_id, context)
        
        if identity_verified and device_trusted and location_valid and risk_score < 0.5:
            # Grant access
            session_id = f"session_{user_id}_{int(time.time())}"
            self.authenticated_sessions[session_id] = {
                'user_id': user_id,
                'created': datetime.now(),
                'risk_score': risk_score,
                'permissions': self.access_policies.get(user_id, [])
            }
            
            self._log_access('authentication_success', user_id, context)
            
            return {
                'authenticated': True,
                'session_id': session_id,
                'risk_score': risk_score
            }
        else:
            self._log_access('authentication_failed', user_id, context)
            
            return {
                'authenticated': False,
                'reason': 'zero_trust_violation',
                'risk_score': risk_score
            }
    
    def _verify_identity(self, credentials: Dict) -> bool:
        """Verify user identity"""
        # Simplified - would use MFA, biometrics, etc.
        return credentials.get('password') is not None
    
    def _check_device_posture(self, device: Dict) -> bool:
        """Check device security posture"""
        # Check if device is managed, patched, etc.
        return device.get('managed', False) and device.get('encrypted', False)
    
    def _verify_location(self, location: Dict) -> bool:
        """Verify access location"""
        # Check if location is in allowed regions
        allowed_countries = ['US', 'UK', 'DE', 'SG', 'JP']
        return location.get('country') in allowed_countries
    
    def _assess_risk(self, user_id: str, context: Dict) -> float:
        """Assess access risk"""
        risk_factors = []
        
        # Time of day risk
        hour = datetime.now().hour
        if hour < 6 or hour > 22:
            risk_factors.append(0.2)
        
        # New location risk
        if context.get('new_location', False):
            risk_factors.append(0.3)
        
        # Failed attempts
        recent_failures = context.get('recent_failures', 0)
        if recent_failures > 0:
            risk_factors.append(min(recent_failures * 0.1, 0.5))
        
        return min(sum(risk_factors), 1.0)
    
    def _log_access(self, event_type: str, user_id: str, context: Dict):
        """Log access event"""
        self.audit_log.append({
            'event': event_type,
            'user_id': user_id,
            'timestamp': datetime.now(),
            'context': context
        })
    
    async def authorize(self, session_id: str, resource: str, action: str) -> bool:
        """Authorize access to resource"""
        
        if session_id not in self.authenticated_sessions:
            return False
        
        session = self.authenticated_sessions[session_id]
        permissions = session['permissions']
        
        # Check if user has permission
        required_permission = f"{resource}:{action}"
        return required_permission in permissions or 'admin:*' in permissions


class InfrastructureOrchestrator:
    """Unified infrastructure orchestration"""
    
    def __init__(self):
        self.edge_manager = EdgeComputingManager()
        self.failover_system = MultiCloudFailoverSystem()
        self.mesh_network = LowLatencyMeshNetwork()
        self.security = ZeroTrustSecurity()
        
    async def deploy_globally(self, strategy: Dict) -> Dict:
        """Deploy strategy globally with optimal infrastructure"""
        
        # 1. Deploy to edge
        edge_deployment = await self.edge_manager.deploy_to_edge(
            strategy.get('code', ''),
            strategy.get('config', {})
        )
        
        # 2. Setup failover
        failover_config = {
            'primary': self.failover_system.active_provider,
            'backups': [p for p in CloudProvider if p != self.failover_system.active_provider]
        }
        
        # 3. Configure mesh network
        network_topology = self.mesh_network.get_network_topology()
        
        # 4. Apply security
        # Would authenticate and authorize deployment
        
        return {
            'edge_deployment': edge_deployment,
            'failover_config': failover_config,
            'network_topology': network_topology,
            'status': 'deployed',
            'timestamp': datetime.now()
        }
    
    async def get_infrastructure_status(self) -> Dict:
        """Get complete infrastructure status"""
        
        # Edge nodes
        edge_health = await self.edge_manager.monitor_nodes()
        
        # Failover stats
        failover_stats = self.failover_system.get_failover_stats()
        
        # Network topology
        network_info = self.mesh_network.get_network_topology()
        
        # Security audit
        security_events = len(self.security.audit_log)
        
        return {
            'edge_nodes': edge_health,
            'failover': failover_stats,
            'network': network_info,
            'security_events': security_events,
            'overall_health': 'healthy',
            'timestamp': datetime.now()
        }
