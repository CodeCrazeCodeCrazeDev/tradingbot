"""
Complete Audit Logging System
==============================
Production-grade audit trail for all trading operations.
Supports compliance, debugging, and forensic analysis.
"""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import sqlite3
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from collections import deque
import queue
from typing import Set

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class AuditEventType(Enum):
    """Types of audit events."""
    # Trading events
    ORDER_SUBMITTED = "order_submitted"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    ORDER_MODIFIED = "order_modified"
    
    # Position events
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_MODIFIED = "position_modified"
    
    # Risk events
    RISK_LIMIT_BREACH = "risk_limit_breach"
    RISK_WARNING = "risk_warning"
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker_triggered"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"
    
    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGE = "config_change"
    ERROR_OCCURRED = "error_occurred"
    RECOVERY_ATTEMPT = "recovery_attempt"
    
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    API_KEY_USED = "api_key_used"
    
    # Data events
    DATA_RECEIVED = "data_received"
    DATA_VALIDATION_FAILED = "data_validation_failed"
    DATA_QUARANTINED = "data_quarantined"
    
    # Signal events
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_VALIDATED = "signal_validated"
    SIGNAL_REJECTED = "signal_rejected"
    SIGNAL_EXPIRED = "signal_expired"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    component: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    action: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    checksum: str = ""
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for integrity verification."""
        data = f"{self.event_id}:{self.event_type.value}:{self.timestamp.isoformat()}:{self.component}:{json.dumps(self.details, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def verify_integrity(self) -> bool:
        """Verify event integrity."""
        return self.checksum == self._calculate_checksum()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'component': self.component,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'correlation_id': self.correlation_id,
            'action': self.action,
            'details': self.details,
            'metadata': self.metadata,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'checksum': self.checksum,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            event_type=AuditEventType(data['event_type']),
            severity=AuditSeverity(data['severity']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            component=data['component'],
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            correlation_id=data.get('correlation_id'),
            action=data.get('action', ''),
            details=data.get('details', {}),
            metadata=data.get('metadata', {}),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            checksum=data.get('checksum', ''),
        )


# ============================================================================
# AUDIT STORAGE BACKENDS
# ============================================================================

class AuditStorageBackend(ABC):
    """Abstract base class for audit storage."""
    
    @abstractmethod
    async def store(self, event: AuditEvent) -> bool:
        """Store an audit event."""
        pass
    
    @abstractmethod
    async def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query audit events."""
        pass
    
    @abstractmethod
    async def get_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Get event by ID."""
        pass


class SQLiteAuditStorage(AuditStorageBackend):
    """SQLite-based audit storage."""
    
    def __init__(self, db_path: str = "audit_trail.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    component TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    correlation_id TEXT,
                    action TEXT,
                    details TEXT,
                    metadata TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    checksum TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_component ON audit_events(component)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_correlation_id ON audit_events(correlation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON audit_events(user_id)")
            
            conn.commit()
    
    async def store(self, event: AuditEvent) -> bool:
        """Store audit event."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO audit_events (
                            event_id, event_type, severity, timestamp, component,
                            user_id, session_id, correlation_id, action, details,
                            metadata, ip_address, user_agent, checksum
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.event_id,
                        event.event_type.value,
                        event.severity.value,
                        event.timestamp.isoformat(),
                        event.component,
                        event.user_id,
                        event.session_id,
                        event.correlation_id,
                        event.action,
                        json.dumps(event.details),
                        json.dumps(event.metadata),
                        event.ip_address,
                        event.user_agent,
                        event.checksum,
                    ))
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store audit event: {e}")
            return False
    
    async def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query audit events."""
        conditions = []
        params = []
        
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        if event_types:
            placeholders = ','.join(['?' for _ in event_types])
            conditions.append(f"event_type IN ({placeholders})")
            params.extend([et.value for et in event_types])
        
        if component:
            conditions.append("component = ?")
            params.append(component)
        
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        
        if correlation_id:
            conditions.append("correlation_id = ?")
            params.append(correlation_id)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM audit_events
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                events = []
                for row in rows:
                    events.append(AuditEvent(
                        event_id=row['event_id'],
                        event_type=AuditEventType(row['event_type']),
                        severity=AuditSeverity(row['severity']),
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        component=row['component'],
                        user_id=row['user_id'],
                        session_id=row['session_id'],
                        correlation_id=row['correlation_id'],
                        action=row['action'],
                        details=json.loads(row['details']) if row['details'] else {},
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        ip_address=row['ip_address'],
                        user_agent=row['user_agent'],
                        checksum=row['checksum'],
                    ))
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to query audit events: {e}")
            return []
    
    async def get_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Get event by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM audit_events WHERE event_id = ?",
                    (event_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return AuditEvent(
                        event_id=row['event_id'],
                        event_type=AuditEventType(row['event_type']),
                        severity=AuditSeverity(row['severity']),
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        component=row['component'],
                        user_id=row['user_id'],
                        session_id=row['session_id'],
                        correlation_id=row['correlation_id'],
                        action=row['action'],
                        details=json.loads(row['details']) if row['details'] else {},
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        ip_address=row['ip_address'],
                        user_agent=row['user_agent'],
                        checksum=row['checksum'],
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get audit event: {e}")
            return None


class FileAuditStorage(AuditStorageBackend):
    """File-based audit storage with rotation."""
    
    def __init__(
        self,
        log_dir: str = "audit_logs",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        max_files: int = 100,
        compress_old: bool = True,
    ):
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.compress_old = compress_old
        self._current_file: Optional[Path] = None
        self._lock = threading.Lock()
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_current_file(self) -> Path:
        """Get current log file, rotating if needed."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        base_name = f"audit_{today}.jsonl"
        file_path = self.log_dir / base_name
        
        # Check if rotation needed
        if file_path.exists() and file_path.stat().st_size >= self.max_file_size:
            # Rotate
            counter = 1
            while True:
                rotated_name = f"audit_{today}_{counter}.jsonl"
                rotated_path = self.log_dir / rotated_name
                if not rotated_path.exists():
                    file_path.rename(rotated_path)
                    if self.compress_old:
                        self._compress_file(rotated_path)
                    break
                counter += 1
        
        self._cleanup_old_files()
        return file_path
    
    def _compress_file(self, file_path: Path):
        """Compress old log file."""
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                    f_out.writelines(f_in)
            file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to compress file: {e}")
    
    def _cleanup_old_files(self):
        """Remove old log files."""
        files = sorted(self.log_dir.glob("audit_*.jsonl*"), key=lambda x: x.stat().st_mtime)
        while len(files) > self.max_files:
            oldest = files.pop(0)
            oldest.unlink()
    
    async def store(self, event: AuditEvent) -> bool:
        """Store audit event."""
        try:
            with self._lock:
                file_path = self._get_current_file()
                with open(file_path, 'a') as f:
                    f.write(json.dumps(event.to_dict()) + '\n')
            return True
        except Exception as e:
            logger.error(f"Failed to store audit event: {e}")
            return False
    
    async def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query audit events."""
        events = []
        
        for file_path in sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True):
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        if len(events) >= limit:
                            break
                        
                        data = json.loads(line.strip())
                        event = AuditEvent.from_dict(data)
                        
                        # Apply filters
                        if start_time and event.timestamp < start_time:
                            continue
                        if end_time and event.timestamp > end_time:
                            continue
                        if event_types and event.event_type not in event_types:
                            continue
                        if component and event.component != component:
                            continue
                        if user_id and event.user_id != user_id:
                            continue
                        if correlation_id and event.correlation_id != correlation_id:
                            continue
                        
                        events.append(event)
                
                if len(events) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"Failed to read audit file {file_path}: {e}")
        
        return events[:limit]
    
    async def get_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Get event by ID."""
        for file_path in self.log_dir.glob("audit_*.jsonl"):
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        data = json.loads(line.strip())
                        if data.get('event_id') == event_id:
                            return AuditEvent.from_dict(data)
            except Exception:
                continue
        return None


# ============================================================================
# AUDIT LOGGER
# ============================================================================

class AuditLogger:
    """
    Main audit logging interface.
    Provides high-level methods for logging various events.
    """
    
    def __init__(
        self,
        storage: Optional[AuditStorageBackend] = None,
        component: str = "trading_bot",
        async_write: bool = True,
        buffer_size: int = 100,
    ):
        self.storage = storage or SQLiteAuditStorage()
        self.component = component
        self.async_write = async_write
        self._buffer: deque = deque(maxlen=buffer_size)
        self._write_queue: queue.Queue = queue.Queue()
        self._session_id = str(uuid.uuid4())
        self._correlation_id: Optional[str] = None
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()
        
        if async_write:
            self._start_writer_thread()
    
    def _start_writer_thread(self):
        """Start background writer thread."""
        def writer():
            while True:
                try:
                    event = self._write_queue.get()
                    if event is None:
                        break
                    asyncio.run(self.storage.store(event))
                except Exception as e:
                    logger.error(f"Audit writer error: {e}")
        
        thread = threading.Thread(target=writer, daemon=True)
        thread.start()
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for subsequent events."""
        self._correlation_id = correlation_id
    
    def clear_correlation_id(self):
        """Clear correlation ID."""
        self._correlation_id = None
    
    def on_event(self, callback: Callable):
        """Register event callback."""
        self._callbacks.append(callback)
    
    async def log(
        self,
        event_type: AuditEventType,
        action: str,
        details: Optional[Dict] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            component=self.component,
            user_id=user_id,
            session_id=self._session_id,
            correlation_id=correlation_id or self._correlation_id,
            action=action,
            details=details or {},
            metadata=metadata or {},
        )
        
        # Buffer
        with self._lock:
            self._buffer.append(event)
        
        # Store
        if self.async_write:
            self._write_queue.put(event)
        else:
            await self.storage.store(event)
        
        # Callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Audit callback error: {e}")
        
        return event
    
    # Convenience methods
    
    async def log_order_submitted(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "market",
        **kwargs
    ) -> AuditEvent:
        """Log order submission."""
        return await self.log(
            event_type=AuditEventType.ORDER_SUBMITTED,
            action=f"Submit {side} order for {symbol}",
            details={
                'order_id': order_id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_type': order_type,
                **kwargs
            },
        )
    
    async def log_order_filled(
        self,
        order_id: str,
        symbol: str,
        filled_quantity: float,
        fill_price: float,
        **kwargs
    ) -> AuditEvent:
        """Log order fill."""
        return await self.log(
            event_type=AuditEventType.ORDER_FILLED,
            action=f"Order {order_id} filled",
            details={
                'order_id': order_id,
                'symbol': symbol,
                'filled_quantity': filled_quantity,
                'fill_price': fill_price,
                **kwargs
            },
        )
    
    async def log_risk_breach(
        self,
        breach_type: str,
        current_value: float,
        limit_value: float,
        action_taken: str,
        **kwargs
    ) -> AuditEvent:
        """Log risk limit breach."""
        return await self.log(
            event_type=AuditEventType.RISK_LIMIT_BREACH,
            action=f"Risk breach: {breach_type}",
            severity=AuditSeverity.WARNING,
            details={
                'breach_type': breach_type,
                'current_value': current_value,
                'limit_value': limit_value,
                'action_taken': action_taken,
                **kwargs
            },
        )
    
    async def log_error(
        self,
        error: Exception,
        context: str,
        **kwargs
    ) -> AuditEvent:
        """Log error."""
        return await self.log(
            event_type=AuditEventType.ERROR_OCCURRED,
            action=f"Error in {context}",
            severity=AuditSeverity.ERROR,
            details={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context,
                **kwargs
            },
        )
    
    async def log_signal(
        self,
        signal_id: str,
        symbol: str,
        direction: str,
        confidence: float,
        source: str,
        **kwargs
    ) -> AuditEvent:
        """Log signal generation."""
        return await self.log(
            event_type=AuditEventType.SIGNAL_GENERATED,
            action=f"Signal generated for {symbol}",
            details={
                'signal_id': signal_id,
                'symbol': symbol,
                'direction': direction,
                'confidence': confidence,
                'source': source,
                **kwargs
            },
        )
    
    async def log_config_change(
        self,
        config_key: str,
        old_value: Any,
        new_value: Any,
        changed_by: str,
        **kwargs
    ) -> AuditEvent:
        """Log configuration change."""
        return await self.log(
            event_type=AuditEventType.CONFIG_CHANGE,
            action=f"Config changed: {config_key}",
            details={
                'config_key': config_key,
                'old_value': str(old_value),
                'new_value': str(new_value),
                'changed_by': changed_by,
                **kwargs
            },
        )
    
    async def query(self, **kwargs) -> List[AuditEvent]:
        """Query audit events."""
        return await self.storage.query(**kwargs)
    
    def get_recent(self, limit: int = 50) -> List[AuditEvent]:
        """Get recent events from buffer."""
        with self._lock:
            return list(self._buffer)[-limit:]


# ============================================================================
# AUDIT REPORT GENERATOR
# ============================================================================

class AuditReportGenerator:
    """Generates audit reports for compliance and analysis."""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
    
    async def generate_daily_report(self, date: datetime) -> Dict:
        """Generate daily audit report."""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        events = await self.audit_logger.query(
            start_time=start,
            end_time=end,
            limit=10000,
        )
        
        # Aggregate statistics
        stats = {
            'date': date.strftime('%Y-%m-%d'),
            'total_events': len(events),
            'by_type': {},
            'by_severity': {},
            'by_component': {},
            'orders': {
                'submitted': 0,
                'filled': 0,
                'cancelled': 0,
                'rejected': 0,
            },
            'errors': [],
            'risk_breaches': [],
        }
        
        for event in events:
            # By type
            type_key = event.event_type.value
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1
            
            # By severity
            sev_key = event.severity.value
            stats['by_severity'][sev_key] = stats['by_severity'].get(sev_key, 0) + 1
            
            # By component
            stats['by_component'][event.component] = stats['by_component'].get(event.component, 0) + 1
            
            # Orders
            if event.event_type == AuditEventType.ORDER_SUBMITTED:
                stats['orders']['submitted'] += 1
            elif event.event_type == AuditEventType.ORDER_FILLED:
                stats['orders']['filled'] += 1
            elif event.event_type == AuditEventType.ORDER_CANCELLED:
                stats['orders']['cancelled'] += 1
            elif event.event_type == AuditEventType.ORDER_REJECTED:
                stats['orders']['rejected'] += 1
            
            # Errors
            if event.event_type == AuditEventType.ERROR_OCCURRED:
                stats['errors'].append({
                    'timestamp': event.timestamp.isoformat(),
                    'details': event.details,
                })
            
            # Risk breaches
            if event.event_type == AuditEventType.RISK_LIMIT_BREACH:
                stats['risk_breaches'].append({
                    'timestamp': event.timestamp.isoformat(),
                    'details': event.details,
                })
        
        return stats
    
    async def generate_trade_report(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict:
        """Generate trade-focused report."""
        events = await self.audit_logger.query(
            start_time=start_time,
            end_time=end_time,
            event_types=[
                AuditEventType.ORDER_SUBMITTED,
                AuditEventType.ORDER_FILLED,
                AuditEventType.ORDER_CANCELLED,
                AuditEventType.ORDER_REJECTED,
            ],
            limit=10000,
        )
        
        trades = {}
        
        for event in events:
            order_id = event.details.get('order_id')
            if not order_id:
                continue
            
            if order_id not in trades:
                trades[order_id] = {
                    'order_id': order_id,
                    'events': [],
                }
            
            trades[order_id]['events'].append({
                'type': event.event_type.value,
                'timestamp': event.timestamp.isoformat(),
                'details': event.details,
            })
        
        return {
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
            },
            'total_orders': len(trades),
            'trades': list(trades.values()),
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'AuditEventType', 'AuditSeverity', 'AuditEvent',
    'AuditStorageBackend', 'SQLiteAuditStorage', 'FileAuditStorage',
    'AuditLogger', 'AuditReportGenerator', 'get_audit_logger',
]
