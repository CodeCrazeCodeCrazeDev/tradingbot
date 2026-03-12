"""
Cloud Infrastructure Components
================================

Comprehensive infrastructure:
- Kubernetes deployment configs
- Auto-scaling
- Load balancing
- Redis caching
- Message queue
- Service mesh
- Secrets management
- Log aggregation
- Distributed tracing

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
import json
import time
import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from enum import Enum, auto
from collections import defaultdict, deque
import threading
import uuid

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not available")


class ServiceStatus(Enum):
    """Service status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"


class ScalingPolicy(Enum):
    """Auto-scaling policies"""
    CPU_BASED = "cpu_based"
    MEMORY_BASED = "memory_based"
    REQUEST_BASED = "request_based"
    CUSTOM = "custom"


class MessagePriority(Enum):
    """Message priorities"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class ServiceInstance:
    """Service instance"""
    instance_id: str
    service_name: str
    host: str
    port: int
    status: ServiceStatus
    
    # Metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    request_count: int = 0
    error_count: int = 0
    
    # Health
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    
    # Metadata
    started_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict:
        return {
            'instance_id': self.instance_id,
            'service_name': self.service_name,
            'host': self.host,
            'port': self.port,
            'status': self.status.value,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'version': self.version
        }


@dataclass
class ScalingConfig:
    """Auto-scaling configuration"""
    service_name: str
    min_instances: int = 1
    max_instances: int = 10
    policy: ScalingPolicy = ScalingPolicy.CPU_BASED
    
    # Thresholds
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 20.0
    
    # Cooldown
    scale_up_cooldown_seconds: int = 60
    scale_down_cooldown_seconds: int = 300
    
    def to_dict(self) -> Dict:
        return {
            'service_name': self.service_name,
            'min_instances': self.min_instances,
            'max_instances': self.max_instances,
            'policy': self.policy.value,
            'scale_up_threshold': self.scale_up_threshold,
            'scale_down_threshold': self.scale_down_threshold
        }


@dataclass
class Message:
    """Queue message"""
    message_id: str
    topic: str
    payload: Dict[str, Any]
    priority: MessagePriority
    created_at: datetime
    
    # Delivery
    delivered: bool = False
    delivered_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        return {
            'message_id': self.message_id,
            'topic': self.topic,
            'payload': self.payload,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'delivered': self.delivered,
            'retries': self.retries
        }


@dataclass
class TraceSpan:
    """Distributed trace span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Tags and logs
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict] = field(default_factory=list)
    
    # Status
    status: str = "ok"
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0
    
    def to_dict(self) -> Dict:
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'operation_name': self.operation_name,
            'service_name': self.service_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'tags': self.tags,
            'status': self.status
        }


class KubernetesDeploymentGenerator:
    """
    Generates Kubernetes deployment configurations
    """
    
    def __init__(self):
        logger.info("KubernetesDeploymentGenerator initialized")
    
    def generate_deployment(
        self,
        name: str,
        image: str,
        replicas: int = 1,
        port: int = 8080,
        cpu_request: str = "100m",
        cpu_limit: str = "500m",
        memory_request: str = "128Mi",
        memory_limit: str = "512Mi",
        env_vars: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Generate deployment YAML as dict"""
        env = []
        if env_vars:
            for k, v in env_vars.items():
                env.append({'name': k, 'value': v})
        
        return {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': name,
                'labels': {'app': name}
            },
            'spec': {
                'replicas': replicas,
                'selector': {
                    'matchLabels': {'app': name}
                },
                'template': {
                    'metadata': {
                        'labels': {'app': name}
                    },
                    'spec': {
                        'containers': [{
                            'name': name,
                            'image': image,
                            'ports': [{'containerPort': port}],
                            'resources': {
                                'requests': {
                                    'cpu': cpu_request,
                                    'memory': memory_request
                                },
                                'limits': {
                                    'cpu': cpu_limit,
                                    'memory': memory_limit
                                }
                            },
                            'env': env,
                            'livenessProbe': {
                                'httpGet': {
                                    'path': '/health/live',
                                    'port': port
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': '/health/ready',
                                    'port': port
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            }
                        }]
                    }
                }
            }
        }
    
    def generate_service(
        self,
        name: str,
        port: int = 8080,
        target_port: int = 8080,
        service_type: str = "ClusterIP"
    ) -> Dict:
        """Generate service YAML as dict"""
        return {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': name
            },
            'spec': {
                'selector': {'app': name},
                'ports': [{
                    'port': port,
                    'targetPort': target_port
                }],
                'type': service_type
            }
        }
    
    def generate_hpa(
        self,
        name: str,
        min_replicas: int = 1,
        max_replicas: int = 10,
        cpu_target: int = 80
    ) -> Dict:
        """Generate HorizontalPodAutoscaler YAML as dict"""
        return {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': f"{name}-hpa"
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': name
                },
                'minReplicas': min_replicas,
                'maxReplicas': max_replicas,
                'metrics': [{
                    'type': 'Resource',
                    'resource': {
                        'name': 'cpu',
                        'target': {
                            'type': 'Utilization',
                            'averageUtilization': cpu_target
                        }
                    }
                }]
            }
        }
    
    def generate_configmap(
        self,
        name: str,
        data: Dict[str, str]
    ) -> Dict:
        """Generate ConfigMap YAML as dict"""
        return {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': name
            },
            'data': data
        }
    
    def generate_secret(
        self,
        name: str,
        data: Dict[str, str]
    ) -> Dict:
        """Generate Secret YAML as dict"""
        import base64
        encoded_data = {
            k: base64.b64encode(v.encode()).decode()
            for k, v in data.items()
        }
        
        return {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': name
            },
            'type': 'Opaque',
            'data': encoded_data
        }


class AutoScaler:
    """
    Auto-scaling manager
    """
    
    def __init__(self):
        # Service instances
        self.instances: Dict[str, List[ServiceInstance]] = defaultdict(list)
        
        # Scaling configs
        self.configs: Dict[str, ScalingConfig] = {}
        
        # Last scaling actions
        self.last_scale_up: Dict[str, datetime] = {}
        self.last_scale_down: Dict[str, datetime] = {}
        
        # Callbacks
        self.on_scale_up: List[Callable] = []
        self.on_scale_down: List[Callable] = []
        
        self._lock = threading.RLock()
        
        logger.info("AutoScaler initialized")
    
    def configure(self, config: ScalingConfig):
        """Configure scaling for a service"""
        with self._lock:
            self.configs[config.service_name] = config
    
    def register_instance(self, instance: ServiceInstance):
        """Register a service instance"""
        with self._lock:
            self.instances[instance.service_name].append(instance)
    
    def unregister_instance(self, service_name: str, instance_id: str):
        """Unregister a service instance"""
        with self._lock:
            self.instances[service_name] = [
                i for i in self.instances[service_name]
                if i.instance_id != instance_id
            ]
    
    def update_metrics(
        self,
        service_name: str,
        instance_id: str,
        cpu_usage: float,
        memory_usage: float,
        request_count: int
    ):
        """Update instance metrics"""
        with self._lock:
            for instance in self.instances.get(service_name, []):
                if instance.instance_id == instance_id:
                    instance.cpu_usage = cpu_usage
                    instance.memory_usage = memory_usage
                    instance.request_count = request_count
                    break
    
    def evaluate_scaling(self, service_name: str) -> Optional[str]:
        """
        Evaluate if scaling is needed
        Returns: "up", "down", or None
        """
        with self._lock:
            config = self.configs.get(service_name)
            instances = self.instances.get(service_name, [])
            
            if not config or not instances:
                return None
            
            # Calculate average metric based on policy
            if config.policy == ScalingPolicy.CPU_BASED:
                avg_metric = sum(i.cpu_usage for i in instances) / len(instances)
            elif config.policy == ScalingPolicy.MEMORY_BASED:
                avg_metric = sum(i.memory_usage for i in instances) / len(instances)
            elif config.policy == ScalingPolicy.REQUEST_BASED:
                avg_metric = sum(i.request_count for i in instances) / len(instances)
            else:
                return None
            
            now = datetime.now()
            
            # Check scale up
            if avg_metric > config.scale_up_threshold:
                if len(instances) < config.max_instances:
                    last_up = self.last_scale_up.get(service_name)
                    if not last_up or (now - last_up).total_seconds() > config.scale_up_cooldown_seconds:
                        return "up"
            
            # Check scale down
            if avg_metric < config.scale_down_threshold:
                if len(instances) > config.min_instances:
                    last_down = self.last_scale_down.get(service_name)
                    if not last_down or (now - last_down).total_seconds() > config.scale_down_cooldown_seconds:
                        return "down"
            
            return None
    
    def scale_up(self, service_name: str) -> bool:
        """Scale up a service"""
        with self._lock:
            config = self.configs.get(service_name)
            instances = self.instances.get(service_name, [])
            
            if not config or len(instances) >= config.max_instances:
                return False
            
            self.last_scale_up[service_name] = datetime.now()
            
            # Fire callbacks
            for callback in self.on_scale_up:
                try:
                    callback(service_name, len(instances) + 1)
                except Exception as e:
                    logger.error(f"Scale up callback error: {e}")
            
            logger.info(f"Scaling up {service_name} to {len(instances) + 1} instances")
            return True
    
    def scale_down(self, service_name: str) -> bool:
        """Scale down a service"""
        with self._lock:
            config = self.configs.get(service_name)
            instances = self.instances.get(service_name, [])
            
            if not config or len(instances) <= config.min_instances:
                return False
            
            self.last_scale_down[service_name] = datetime.now()
            
            # Fire callbacks
            for callback in self.on_scale_down:
                try:
                    callback(service_name, len(instances) - 1)
                except Exception as e:
                    logger.error(f"Scale down callback error: {e}")
            
            logger.info(f"Scaling down {service_name} to {len(instances) - 1} instances")
            return True
    
    def get_status(self, service_name: str) -> Dict[str, Any]:
        """Get scaling status for a service"""
        with self._lock:
            config = self.configs.get(service_name)
            instances = self.instances.get(service_name, [])
            
            return {
                'service_name': service_name,
                'current_instances': len(instances),
                'min_instances': config.min_instances if config else 0,
                'max_instances': config.max_instances if config else 0,
                'instances': [i.to_dict() for i in instances]
            }


class LoadBalancer:
    """
    Load balancer
    """
    
    def __init__(self, algorithm: str = "round_robin"):
        self.algorithm = algorithm
        
        # Service instances
        self.instances: Dict[str, List[ServiceInstance]] = defaultdict(list)
        
        # Round robin counters
        self.counters: Dict[str, int] = defaultdict(int)
        
        # Weighted instances
        self.weights: Dict[str, Dict[str, int]] = defaultdict(dict)
        
        self._lock = threading.RLock()
        
        logger.info(f"LoadBalancer initialized with {algorithm}")
    
    def register_instance(self, instance: ServiceInstance, weight: int = 1):
        """Register an instance"""
        with self._lock:
            self.instances[instance.service_name].append(instance)
            self.weights[instance.service_name][instance.instance_id] = weight
    
    def unregister_instance(self, service_name: str, instance_id: str):
        """Unregister an instance"""
        with self._lock:
            self.instances[service_name] = [
                i for i in self.instances[service_name]
                if i.instance_id != instance_id
            ]
            if instance_id in self.weights.get(service_name, {}):
                del self.weights[service_name][instance_id]
    
    def get_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """Get an instance using the configured algorithm"""
        with self._lock:
            instances = [
                i for i in self.instances.get(service_name, [])
                if i.status == ServiceStatus.HEALTHY
            ]
            
            if not instances:
                return None
            
            if self.algorithm == "round_robin":
                return self._round_robin(service_name, instances)
            elif self.algorithm == "least_connections":
                return self._least_connections(instances)
            elif self.algorithm == "weighted":
                return self._weighted(service_name, instances)
            elif self.algorithm == "random":
                return random.choice(instances)
            else:
                return instances[0]
    
    def _round_robin(
        self,
        service_name: str,
        instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """Round robin selection"""
        idx = self.counters[service_name] % len(instances)
        self.counters[service_name] += 1
        return instances[idx]
    
    def _least_connections(
        self,
        instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """Least connections selection"""
        return min(instances, key=lambda i: i.request_count)
    
    def _weighted(
        self,
        service_name: str,
        instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """Weighted selection"""
        
        weights = self.weights.get(service_name, {})
        weighted_instances = []
        
        for instance in instances:
            weight = weights.get(instance.instance_id, 1)
            weighted_instances.extend([instance] * weight)
        
        return random.choice(weighted_instances) if weighted_instances else instances[0]


class RedisCache:
    """
    Redis caching layer
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.db = db
        
        if REDIS_AVAILABLE:
            try:
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=True
                )
                self.client.ping()
                self.connected = True
                logger.info("Redis connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.client = None
                self.connected = False
        else:
            self.client = None
            self.connected = False
        
        # Fallback in-memory cache
        self.memory_cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.connected and self.client:
            try:
                value = self.client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to memory
        with self._lock:
            if key in self.memory_cache:
                value, expiry = self.memory_cache[key]
                if expiry == 0 or time.time() < expiry:
                    return value
                else:
                    del self.memory_cache[key]
        
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if self.connected and self.client:
            try:
                serialized = json.dumps(value)
                if ttl_seconds:
                    self.client.setex(key, ttl_seconds, serialized)
                else:
                    self.client.set(key, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Fallback to memory
        with self._lock:
            expiry = time.time() + ttl_seconds if ttl_seconds else 0
            self.memory_cache[key] = (value, expiry)
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete from cache"""
        if self.connected and self.client:
            try:
                self.client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        with self._lock:
            if key in self.memory_cache:
                del self.memory_cache[key]
        
        return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if self.connected and self.client:
            try:
                return self.client.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis exists error: {e}")
        
        with self._lock:
            if key in self.memory_cache:
                _, expiry = self.memory_cache[key]
                return expiry == 0 or time.time() < expiry
        
        return False
    
    def clear(self):
        """Clear all cache"""
        if self.connected and self.client:
            try:
                self.client.flushdb()
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        with self._lock:
            self.memory_cache.clear()


class MessageQueue:
    """
    In-memory message queue (production would use RabbitMQ/Kafka)
    """
    
    def __init__(self):
        # Queues by topic
        self.queues: Dict[str, List[Message]] = defaultdict(list)
        
        # Subscribers
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Dead letter queue
        self.dlq: List[Message] = []
        
        self._lock = threading.RLock()
        self._next_id = 1
        
        logger.info("MessageQueue initialized")
    
    def _generate_id(self) -> str:
        with self._lock:
            msg_id = f"MSG_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_id}"
            self._next_id += 1
            return msg_id
    
    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Message:
        """Publish a message"""
        message = Message(
            message_id=self._generate_id(),
            topic=topic,
            payload=payload,
            priority=priority,
            created_at=datetime.now()
        )
        
        with self._lock:
            # Insert based on priority
            queue = self.queues[topic]
            inserted = False
            
            for i, msg in enumerate(queue):
                if msg.priority.value < priority.value:
                    queue.insert(i, message)
                    inserted = True
                    break
            
            if not inserted:
                queue.append(message)
        
        # Notify subscribers
        self._notify_subscribers(topic, message)
        
        return message
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic"""
        with self._lock:
            self.subscribers[topic].append(callback)
    
    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        with self._lock:
            if callback in self.subscribers[topic]:
                self.subscribers[topic].remove(callback)
    
    def _notify_subscribers(self, topic: str, message: Message):
        """Notify subscribers of new message"""
        for callback in self.subscribers.get(topic, []):
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")
    
    def consume(self, topic: str) -> Optional[Message]:
        """Consume a message from a topic"""
        with self._lock:
            queue = self.queues.get(topic, [])
            
            if not queue:
                return None
            
            message = queue.pop(0)
            message.delivered = True
            message.delivered_at = datetime.now()
            
            return message
    
    def ack(self, message_id: str):
        """Acknowledge a message"""
        # In a real implementation, this would mark the message as processed
        pass
    
    def nack(self, message: Message):
        """Negative acknowledge - retry or send to DLQ"""
        with self._lock:
            message.retries += 1
            
            if message.retries >= message.max_retries:
                self.dlq.append(message)
                logger.warning(f"Message {message.message_id} sent to DLQ")
            else:
                # Re-queue
                self.queues[message.topic].append(message)
    
    def get_queue_size(self, topic: str) -> int:
        """Get queue size"""
        with self._lock:
            return len(self.queues.get(topic, []))
    
    def get_dlq_size(self) -> int:
        """Get dead letter queue size"""
        with self._lock:
            return len(self.dlq)


class SecretsManager:
    """
    Secrets management
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        # Secrets storage
        self.secrets: Dict[str, str] = {}
        
        # Encryption
        if encryption_key:
            try:
                from cryptography.fernet import Fernet
                self.fernet = Fernet(encryption_key.encode())
            except Exception:
                self.fernet = None
        else:
            self.fernet = None
        
        # Access log
        self.access_log: deque = deque(maxlen=1000)
        
        self._lock = threading.RLock()
        
        logger.info("SecretsManager initialized")
    
    def set_secret(self, name: str, value: str):
        """Set a secret"""
        with self._lock:
            if self.fernet:
                encrypted = self.fernet.encrypt(value.encode()).decode()
                self.secrets[name] = encrypted
            else:
                self.secrets[name] = value
            
            self.access_log.append({
                'action': 'set',
                'name': name,
                'timestamp': datetime.now()
            })
    
    def get_secret(self, name: str) -> Optional[str]:
        """Get a secret"""
        with self._lock:
            value = self.secrets.get(name)
            
            if value is None:
                return None
            
            self.access_log.append({
                'action': 'get',
                'name': name,
                'timestamp': datetime.now()
            })
            
            if self.fernet:
                try:
                    return self.fernet.decrypt(value.encode()).decode()
                except Exception:
                    return value
            
            return value
    
    def delete_secret(self, name: str):
        """Delete a secret"""
        with self._lock:
            if name in self.secrets:
                del self.secrets[name]
                
                self.access_log.append({
                    'action': 'delete',
                    'name': name,
                    'timestamp': datetime.now()
                })
    
    def list_secrets(self) -> List[str]:
        """List secret names"""
        with self._lock:
            return list(self.secrets.keys())


class LogAggregator:
    """
    Log aggregation
    """
    
    def __init__(self, max_logs: int = 100000):
        self.max_logs = max_logs
        
        # Logs by service
        self.logs: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_logs // 10)
        )
        
        # All logs
        self.all_logs: deque = deque(maxlen=max_logs)
        
        self._lock = threading.RLock()
        
        logger.info("LogAggregator initialized")
    
    def log(
        self,
        service: str,
        level: str,
        message: str,
        metadata: Optional[Dict] = None
    ):
        """Add a log entry"""
        entry = {
            'service': service,
            'level': level,
            'message': message,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        with self._lock:
            self.logs[service].append(entry)
            self.all_logs.append(entry)
    
    def search(
        self,
        service: Optional[str] = None,
        level: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Search logs"""
        with self._lock:
            if service:
                logs = list(self.logs.get(service, []))
            else:
                logs = list(self.all_logs)
            
            if level:
                logs = [l for l in logs if l['level'] == level]
            
            if query:
                logs = [l for l in logs if query.lower() in l['message'].lower()]
            
            return logs[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get log statistics"""
        with self._lock:
            stats = {
                'total_logs': len(self.all_logs),
                'by_service': {},
                'by_level': defaultdict(int)
            }
            
            for service, logs in self.logs.items():
                stats['by_service'][service] = len(logs)
            
            for log in self.all_logs:
                stats['by_level'][log['level']] += 1
            
            return stats


class DistributedTracer:
    """
    Distributed tracing
    """
    
    def __init__(self):
        # Traces
        self.traces: Dict[str, List[TraceSpan]] = defaultdict(list)
        
        # Active spans
        self.active_spans: Dict[str, TraceSpan] = {}
        
        self._lock = threading.RLock()
        
        logger.info("DistributedTracer initialized")
    
    def start_trace(self, operation_name: str, service_name: str) -> TraceSpan:
        """Start a new trace"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())[:8]
        
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            operation_name=operation_name,
            service_name=service_name,
            start_time=datetime.now()
        )
        
        with self._lock:
            self.traces[trace_id].append(span)
            self.active_spans[span_id] = span
        
        return span
    
    def start_span(
        self,
        trace_id: str,
        parent_span_id: str,
        operation_name: str,
        service_name: str
    ) -> TraceSpan:
        """Start a child span"""
        span_id = str(uuid.uuid4())[:8]
        
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            service_name=service_name,
            start_time=datetime.now()
        )
        
        with self._lock:
            self.traces[trace_id].append(span)
            self.active_spans[span_id] = span
        
        return span
    
    def end_span(self, span_id: str, status: str = "ok", error: Optional[str] = None):
        """End a span"""
        with self._lock:
            span = self.active_spans.get(span_id)
            
            if span:
                span.end_time = datetime.now()
                span.status = status
                span.error = error
                del self.active_spans[span_id]
    
    def add_tag(self, span_id: str, key: str, value: str):
        """Add a tag to a span"""
        with self._lock:
            span = self.active_spans.get(span_id)
            if span:
                span.tags[key] = value
    
    def add_log(self, span_id: str, message: str, fields: Optional[Dict] = None):
        """Add a log to a span"""
        with self._lock:
            span = self.active_spans.get(span_id)
            if span:
                span.logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': message,
                    'fields': fields or {}
                })
    
    def get_trace(self, trace_id: str) -> List[Dict]:
        """Get all spans for a trace"""
        with self._lock:
            return [s.to_dict() for s in self.traces.get(trace_id, [])]


class CloudInfrastructure:
    """
    Complete cloud infrastructure system
    """
    
    def __init__(self):
        self.k8s_generator = KubernetesDeploymentGenerator()
        self.auto_scaler = AutoScaler()
        self.load_balancer = LoadBalancer()
        self.cache = RedisCache()
        self.message_queue = MessageQueue()
        self.secrets_manager = SecretsManager()
        self.log_aggregator = LogAggregator()
        self.tracer = DistributedTracer()
        
        logger.info("CloudInfrastructure initialized")
    
    def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get overall infrastructure status"""
        return {
            'cache': {
                'connected': self.cache.connected,
                'memory_cache_size': len(self.cache.memory_cache)
            },
            'message_queue': {
                'queues': {
                    topic: self.message_queue.get_queue_size(topic)
                    for topic in self.message_queue.queues
                },
                'dlq_size': self.message_queue.get_dlq_size()
            },
            'logs': self.log_aggregator.get_stats(),
            'secrets': len(self.secrets_manager.list_secrets())
        }


# Singleton instance
_infrastructure: Optional[CloudInfrastructure] = None


def get_infrastructure() -> CloudInfrastructure:
    global _infrastructure
    if _infrastructure is None:
        _infrastructure = CloudInfrastructure()
    return _infrastructure


# Export
__all__ = [
    'CloudInfrastructure',
    'KubernetesDeploymentGenerator',
    'AutoScaler',
    'LoadBalancer',
    'RedisCache',
    'MessageQueue',
    'SecretsManager',
    'LogAggregator',
    'DistributedTracer',
    'ServiceInstance',
    'ServiceStatus',
    'ScalingConfig',
    'ScalingPolicy',
    'Message',
    'MessagePriority',
    'TraceSpan',
    'get_infrastructure'
]
