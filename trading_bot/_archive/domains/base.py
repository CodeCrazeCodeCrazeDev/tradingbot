"""
Base Domain Class
==================

Abstract base class for all 12 domains in the hedge fund architecture.
Each domain inherits from this base and implements domain-specific logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)


class DomainStatus(Enum):
    """Domain operational status."""
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    ONLINE = "online"
    DEGRADED = "degraded"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class DomainPriority(Enum):
    """Domain priority levels for resource allocation."""
    CRITICAL = 1      # Must always be running (Risk, Execution)
    HIGH = 2          # Important for trading (Alpha, Data)
    MEDIUM = 3        # Supporting functions (Analytics, ML)
    LOW = 4           # Background tasks (R&D, Compliance)


@dataclass
class DomainHealth:
    """Health metrics for a domain."""
    status: DomainStatus = DomainStatus.OFFLINE
    last_heartbeat: Optional[datetime] = None
    error_count: int = 0
    warning_count: int = 0
    uptime_seconds: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    active_tasks: int = 0
    pending_tasks: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    
    def is_healthy(self) -> bool:
        """Check if domain is healthy."""
        return self.status in (DomainStatus.ONLINE, DomainStatus.DEGRADED)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'status': self.status.value,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'uptime_seconds': self.uptime_seconds,
            'cpu_usage_percent': self.cpu_usage_percent,
            'memory_usage_mb': self.memory_usage_mb,
            'active_tasks': self.active_tasks,
            'pending_tasks': self.pending_tasks,
            'messages_processed': self.messages_processed,
            'messages_failed': self.messages_failed,
        }


@dataclass
class DomainMessage:
    """Message passed between domains."""
    source_domain: str
    target_domain: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    priority: int = 5  # 1-10, lower is higher priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source_domain': self.source_domain,
            'target_domain': self.target_domain,
            'message_type': self.message_type,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'priority': self.priority,
        }


class BaseDomain(ABC):
    """
    Abstract base class for all hedge fund domains.
    
    Each domain represents a major functional area of the trading system,
    encapsulating related modules and providing a unified interface.
    """
    
    def __init__(self, domain_id: str, domain_name: str, priority: DomainPriority = DomainPriority.MEDIUM):
        self.domain_id = domain_id
        self.domain_name = domain_name
        self.priority = priority
        self.health = DomainHealth()
        self._initialized = False
        self._start_time: Optional[datetime] = None
        self._modules: Dict[str, Any] = {}
        self._dependencies: Set[str] = set()
        self._message_handlers: Dict[str, callable] = {}
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(f"domain.{domain_id}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if domain is initialized."""
        return self._initialized
    
    @property
    def uptime(self) -> float:
        """Get domain uptime in seconds."""
        if self._start_time:
            return (datetime.now() - self._start_time).total_seconds()
        return 0.0
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the domain and all its modules.
        
        Returns:
            bool: True if initialization successful
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """
        Gracefully shutdown the domain.
        
        Returns:
            bool: True if shutdown successful
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities this domain provides.
        
        Returns:
            List[str]: List of capability identifiers
        """
        pass
    
    @abstractmethod
    def get_module_mapping(self) -> Dict[str, str]:
        """
        Get mapping of module names to their paths.
        
        Returns:
            Dict[str, str]: Module name -> module path mapping
        """
        pass
    
    async def handle_message(self, message: DomainMessage) -> Optional[Dict[str, Any]]:
        """
        Handle an incoming message from another domain.
        
        Args:
            message: The incoming message
            
        Returns:
            Optional response payload
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                return await handler(message)
            except Exception as e:
                self.logger.error(f"Error handling message {message.message_type}: {e}")
                self.health.messages_failed += 1
                return {'error': str(e)}
        else:
            self.logger.warning(f"No handler for message type: {message.message_type}")
            return None
    
    def register_handler(self, message_type: str, handler: callable):
        """Register a message handler."""
        self._message_handlers[message_type] = handler
    
    def add_dependency(self, domain_id: str):
        """Add a domain dependency."""
        self._dependencies.add(domain_id)
    
    def get_dependencies(self) -> Set[str]:
        """Get domain dependencies."""
        return self._dependencies.copy()
    
    def register_module(self, name: str, module: Any):
        """Register a module with this domain."""
        self._modules[name] = module
        self.logger.debug(f"Registered module: {name}")
    
    def get_module(self, name: str) -> Optional[Any]:
        """Get a registered module."""
        return self._modules.get(name)
    
    def get_health(self) -> DomainHealth:
        """Get current health metrics."""
        self.health.uptime_seconds = self.uptime
        self.health.last_heartbeat = datetime.now()
        return self.health
    
    def get_status(self) -> Dict[str, Any]:
        """Get domain status summary."""
        return {
            'domain_id': self.domain_id,
            'domain_name': self.domain_name,
            'priority': self.priority.name,
            'initialized': self._initialized,
            'health': self.get_health().to_dict(),
            'modules': list(self._modules.keys()),
            'dependencies': list(self._dependencies),
            'capabilities': self.get_capabilities(),
        }
    
    async def _safe_initialize(self) -> bool:
        """Thread-safe initialization wrapper."""
        async with self._lock:
            if self._initialized:
                return True
            
            self.health.status = DomainStatus.INITIALIZING
            self._start_time = datetime.now()
            
            try:
                result = await self.initialize()
                if result:
                    self._initialized = True
                    self.health.status = DomainStatus.ONLINE
                    self.logger.info(f"Domain {self.domain_name} initialized successfully")
                else:
                    self.health.status = DomainStatus.ERROR
                    self.logger.error(f"Domain {self.domain_name} initialization failed")
                return result
            except Exception as e:
                self.health.status = DomainStatus.ERROR
                self.health.error_count += 1
                self.logger.error(f"Domain {self.domain_name} initialization error: {e}")
                return False
    
    async def _safe_shutdown(self) -> bool:
        """Thread-safe shutdown wrapper."""
        async with self._lock:
            if not self._initialized:
                return True
            
            self.health.status = DomainStatus.MAINTENANCE
            
            try:
                result = await self.shutdown()
                self._initialized = False
                self.health.status = DomainStatus.OFFLINE
                self.logger.info(f"Domain {self.domain_name} shutdown successfully")
                return result
            except Exception as e:
                self.health.status = DomainStatus.ERROR
                self.health.error_count += 1
                self.logger.error(f"Domain {self.domain_name} shutdown error: {e}")
                return False
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.domain_id}, status={self.health.status.value})>"
