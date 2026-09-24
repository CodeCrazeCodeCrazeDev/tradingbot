"""
Data Integrity Firewall
========================

Protects production data from unauthorized access and modification.
All data access from AI experiments must go through this firewall.

Features:
1. Access control for data sources
2. Read-only enforcement for production data
3. Data validation and sanitization
4. Audit logging of all data access
5. Anomaly detection in data requests

Author: AlphaAlgo Trading System
"""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Data access levels."""
    NONE = 0           # No access
    READ_SAMPLE = 1    # Read sample/anonymized data only
    READ_HISTORICAL = 2  # Read historical data
    READ_REALTIME = 3  # Read real-time data
    READ_ALL = 4       # Read all data
    WRITE_SANDBOX = 5  # Write to sandbox only
    WRITE_ALL = 6      # Full write access (production only)


class DataCategory(Enum):
    """Categories of data."""
    MARKET_DATA = "market_data"
    TRADE_DATA = "trade_data"
    POSITION_DATA = "position_data"
    ACCOUNT_DATA = "account_data"
    CONFIGURATION = "configuration"
    CREDENTIALS = "credentials"
    AUDIT_LOGS = "audit_logs"
    MODEL_WEIGHTS = "model_weights"
    RESEARCH_DATA = "research_data"


class RequestStatus(Enum):
    """Status of data access request."""
    PENDING = auto()
    APPROVED = auto()
    DENIED = auto()
    RATE_LIMITED = auto()
    ANOMALY_DETECTED = auto()


@dataclass
class FirewallConfig:
    """Configuration for data integrity firewall."""
    # Access Control
    default_access_level: AccessLevel = AccessLevel.READ_SAMPLE
    sandbox_access_level: AccessLevel = AccessLevel.READ_HISTORICAL
    production_access_level: AccessLevel = AccessLevel.NONE
    
    # Rate Limiting
    max_requests_per_minute: int = 100
    max_requests_per_hour: int = 1000
    max_data_volume_mb_per_hour: float = 100.0
    
    # Data Protection
    anonymize_sensitive_data: bool = True
    mask_account_numbers: bool = True
    mask_api_keys: bool = True
    
    # Blocked Patterns
    blocked_data_patterns: List[str] = field(default_factory=lambda: [
        r'password',
        r'secret',
        r'api_key',
        r'private_key',
        r'credential',
    ])
    
    # Allowed Sources
    allowed_data_sources: Set[str] = field(default_factory=lambda: {
        'historical_prices',
        'market_data',
        'technical_indicators',
        'economic_calendar',
        'news_sentiment',
    })
    
    # Paths
    audit_log_path: str = "firewall_audit"


@dataclass
class AccessRequest:
    """A data access request."""
    request_id: str
    requester_id: str  # Agent or experiment ID
    requester_type: str  # 'agent', 'experiment', 'system'
    
    # Request Details
    data_category: DataCategory
    data_source: str
    operation: str  # 'read', 'write', 'delete'
    query: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    
    # Status
    status: RequestStatus = RequestStatus.PENDING
    denial_reason: Optional[str] = None
    
    # Access Level
    required_level: AccessLevel = AccessLevel.READ_SAMPLE
    granted_level: Optional[AccessLevel] = None
    
    # Data Volume
    estimated_size_bytes: int = 0
    actual_size_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'requester_id': self.requester_id,
            'requester_type': self.requester_type,
            'data_category': self.data_category.value,
            'data_source': self.data_source,
            'operation': self.operation,
            'query': self.query,
            'parameters': self.parameters,
            'requested_at': self.requested_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'status': self.status.name,
            'denial_reason': self.denial_reason,
            'required_level': self.required_level.name,
            'granted_level': self.granted_level.name if self.granted_level else None,
            'estimated_size_bytes': self.estimated_size_bytes,
            'actual_size_bytes': self.actual_size_bytes,
        }


@dataclass
class AccessPolicy:
    """Access policy for a requester."""
    policy_id: str
    requester_id: str
    
    # Permissions
    allowed_categories: Set[DataCategory]
    allowed_sources: Set[str]
    max_access_level: AccessLevel
    
    # Restrictions
    read_only: bool = True
    max_query_size: int = 10000
    allowed_operations: Set[str] = field(default_factory=lambda: {'read'})
    
    # Time Restrictions
    valid_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = None
    
    # Rate Limits (override defaults)
    custom_rate_limit: Optional[int] = None
    
    def is_valid(self) -> bool:
        """Check if policy is currently valid."""
        now = datetime.now(timezone.utc)
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True


@dataclass
class AnomalyReport:
    """Report of detected anomaly in data access."""
    report_id: str
    request_id: str
    detected_at: datetime
    anomaly_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    evidence: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'request_id': self.request_id,
            'detected_at': self.detected_at.isoformat(),
            'anomaly_type': self.anomaly_type,
            'severity': self.severity,
            'description': self.description,
            'evidence': self.evidence,
        }


class DataIntegrityFirewall:
    """
    Firewall protecting production data from unauthorized access.
    
    All data access from AI experiments MUST go through this firewall.
    Production data is protected with multiple layers:
    1. Access control based on requester identity
    2. Rate limiting to prevent abuse
    3. Data sanitization and anonymization
    4. Anomaly detection for suspicious patterns
    5. Complete audit logging
    """
    
    # Sensitive data patterns to mask
    SENSITIVE_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]'),
        (r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b', '[IBAN]'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+', '[API_KEY]'),
        (r'password["\']?\s*[:=]\s*["\']?[\w-]+', '[PASSWORD]'),
        (r'secret["\']?\s*[:=]\s*["\']?[\w-]+', '[SECRET]'),
    ]
    
    def __init__(self, config: Optional[FirewallConfig] = None):
        """
        Initialize the data integrity firewall.
        
        Args:
            config: Firewall configuration
        """
        self.config = config or FirewallConfig()
        
        # Policies
        self._policies: Dict[str, AccessPolicy] = {}
        
        # Request tracking
        self._requests: Dict[str, AccessRequest] = {}
        self._request_history: List[AccessRequest] = []
        
        # Rate limiting
        self._request_counts: Dict[str, List[datetime]] = {}
        self._data_volume: Dict[str, float] = {}
        
        # Anomaly detection
        self._anomaly_reports: List[AnomalyReport] = []
        self._baseline_patterns: Dict[str, Dict] = {}
        
        # Callbacks
        self._anomaly_callbacks: List[Callable] = []
        self._denial_callbacks: List[Callable] = []
        
        # Storage
        self._audit_path = Path(self.config.audit_log_path)
        self._audit_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("DataIntegrityFirewall initialized")
    
    async def request_access(
        self,
        requester_id: str,
        requester_type: str,
        data_category: DataCategory,
        data_source: str,
        operation: str = 'read',
        query: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        estimated_size: int = 0,
    ) -> Tuple[bool, AccessRequest]:
        """
        Request access to data.
        
        Args:
            requester_id: ID of the requester
            requester_type: Type of requester
            data_category: Category of data
            data_source: Source of data
            operation: Operation to perform
            query: Optional query
            parameters: Optional parameters
            estimated_size: Estimated data size in bytes
        
        Returns:
            Tuple of (access_granted, AccessRequest)
        """
        request_id = f"REQ-{uuid.uuid4().hex[:12]}"
        
        request = AccessRequest(
            request_id=request_id,
            requester_id=requester_id,
            requester_type=requester_type,
            data_category=data_category,
            data_source=data_source,
            operation=operation,
            query=query,
            parameters=parameters or {},
            estimated_size_bytes=estimated_size,
        )
        
        self._requests[request_id] = request
        
        # Process request
        granted = await self._process_request(request)
        
        # Record in history
        self._request_history.append(request)
        
        # Audit log
        await self._audit_request(request)
        
        return granted, request
    
    async def _process_request(self, request: AccessRequest) -> bool:
        """Process an access request."""
        request.processed_at = datetime.now(timezone.utc)
        
        # Step 1: Check if data category is protected
        if request.data_category in [DataCategory.CREDENTIALS, DataCategory.ACCOUNT_DATA]:
            if request.requester_type != 'system':
                request.status = RequestStatus.DENIED
                request.denial_reason = f"Access to {request.data_category.value} denied for non-system requesters"
                await self._notify_denial(request)
                return False
        
        # Step 2: Check policy
        policy = self._policies.get(request.requester_id)
        if policy:
            if not policy.is_valid():
                request.status = RequestStatus.DENIED
                request.denial_reason = "Access policy expired"
                return False
            
            if request.data_category not in policy.allowed_categories:
                request.status = RequestStatus.DENIED
                request.denial_reason = f"Category {request.data_category.value} not allowed"
                return False
            
            if request.operation not in policy.allowed_operations:
                request.status = RequestStatus.DENIED
                request.denial_reason = f"Operation {request.operation} not allowed"
                return False
            
            request.granted_level = min(
                policy.max_access_level,
                self.config.sandbox_access_level
            )
        else:
            # Default policy
            request.granted_level = self.config.default_access_level
        
        # Step 3: Check rate limits
        if not self._check_rate_limit(request.requester_id):
            request.status = RequestStatus.RATE_LIMITED
            request.denial_reason = "Rate limit exceeded"
            return False
        
        # Step 4: Check data source
        if request.data_source not in self.config.allowed_data_sources:
            request.status = RequestStatus.DENIED
            request.denial_reason = f"Data source {request.data_source} not allowed"
            return False
        
        # Step 5: Check for blocked patterns in query
        if request.query:
            for pattern in self.config.blocked_data_patterns:
                if re.search(pattern, request.query, re.IGNORECASE):
                    request.status = RequestStatus.DENIED
                    request.denial_reason = "Query contains blocked pattern"
                    return False
        
        # Step 6: Anomaly detection
        anomaly = await self._detect_anomaly(request)
        if anomaly:
            request.status = RequestStatus.ANOMALY_DETECTED
            request.denial_reason = f"Anomaly detected: {anomaly.anomaly_type}"
            await self._notify_anomaly(anomaly)
            return False
        
        # Step 7: Write operation check
        if request.operation in ['write', 'delete']:
            if request.requester_type != 'system':
                request.status = RequestStatus.DENIED
                request.denial_reason = "Write operations not allowed for non-system requesters"
                return False
        
        # Approved
        request.status = RequestStatus.APPROVED
        self._record_request(request.requester_id)
        
        logger.debug(f"Access granted: {request.request_id} for {request.requester_id}")
        
        return True
    
    def _check_rate_limit(self, requester_id: str) -> bool:
        """Check if requester is within rate limits."""
        now = datetime.now(timezone.utc)
        
        if requester_id not in self._request_counts:
            self._request_counts[requester_id] = []
        
        # Clean old entries
        one_hour_ago = now - timedelta(hours=1)
        one_minute_ago = now - timedelta(minutes=1)
        
        self._request_counts[requester_id] = [
            t for t in self._request_counts[requester_id]
            if t > one_hour_ago
        ]
        
        requests = self._request_counts[requester_id]
        
        # Check per-minute limit
        recent_requests = sum(1 for t in requests if t > one_minute_ago)
        if recent_requests >= self.config.max_requests_per_minute:
            return False
        
        # Check per-hour limit
        if len(requests) >= self.config.max_requests_per_hour:
            return False
        
        return True
    
    def _record_request(self, requester_id: str):
        """Record a request for rate limiting."""
        if requester_id not in self._request_counts:
            self._request_counts[requester_id] = []
        
        self._request_counts[requester_id].append(datetime.now(timezone.utc))
    
    async def _detect_anomaly(self, request: AccessRequest) -> Optional[AnomalyReport]:
        """Detect anomalies in access request."""
        requester_id = request.requester_id
        
        # Get baseline for requester
        baseline = self._baseline_patterns.get(requester_id, {})
        
        # Check for unusual data category
        usual_categories = baseline.get('usual_categories', set())
        if usual_categories and request.data_category not in usual_categories:
            if len(usual_categories) > 5:  # Only flag if we have enough history
                return AnomalyReport(
                    report_id=f"ANOM-{uuid.uuid4().hex[:8]}",
                    request_id=request.request_id,
                    detected_at=datetime.now(timezone.utc),
                    anomaly_type='unusual_category',
                    severity='medium',
                    description=f"Unusual data category access: {request.data_category.value}",
                    evidence={
                        'usual_categories': [c.value for c in usual_categories],
                        'requested_category': request.data_category.value,
                    }
                )
        
        # Check for unusual request volume
        recent_count = len([
            r for r in self._request_history[-100:]
            if r.requester_id == requester_id
        ])
        
        avg_count = baseline.get('avg_requests_per_100', 5)
        if recent_count > avg_count * 3:
            return AnomalyReport(
                report_id=f"ANOM-{uuid.uuid4().hex[:8]}",
                request_id=request.request_id,
                detected_at=datetime.now(timezone.utc),
                anomaly_type='volume_spike',
                severity='high',
                description=f"Unusual request volume: {recent_count} vs avg {avg_count}",
                evidence={
                    'recent_count': recent_count,
                    'average_count': avg_count,
                }
            )
        
        # Check for suspicious query patterns
        if request.query:
            suspicious_patterns = [
                r'SELECT\s+\*\s+FROM',  # SELECT * queries
                r'DROP\s+TABLE',
                r'DELETE\s+FROM',
                r'TRUNCATE',
                r';\s*--',  # SQL injection attempt
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, request.query, re.IGNORECASE):
                    return AnomalyReport(
                        report_id=f"ANOM-{uuid.uuid4().hex[:8]}",
                        request_id=request.request_id,
                        detected_at=datetime.now(timezone.utc),
                        anomaly_type='suspicious_query',
                        severity='critical',
                        description=f"Suspicious query pattern detected",
                        evidence={
                            'pattern': pattern,
                            'query_snippet': request.query[:100],
                        }
                    )
        
        return None
    
    def sanitize_data(self, data: Any) -> Any:
        """
        Sanitize data before returning to requester.
        
        Args:
            data: Data to sanitize
        
        Returns:
            Sanitized data
        """
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize a string value."""
        result = text
        
        if self.config.anonymize_sensitive_data:
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        if self.config.mask_account_numbers:
            # Mask account numbers (keep last 4 digits)
            result = re.sub(r'\b(\d{4,})\d{4}\b', r'****\1', result)
        
        return result
    
    async def create_policy(
        self,
        requester_id: str,
        allowed_categories: Set[DataCategory],
        allowed_sources: Set[str],
        max_access_level: AccessLevel,
        read_only: bool = True,
        valid_hours: int = 24,
    ) -> AccessPolicy:
        """
        Create an access policy for a requester.
        
        Args:
            requester_id: ID of the requester
            allowed_categories: Allowed data categories
            allowed_sources: Allowed data sources
            max_access_level: Maximum access level
            read_only: Whether read-only
            valid_hours: Policy validity in hours
        
        Returns:
            Created AccessPolicy
        """
        policy_id = f"POL-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        
        policy = AccessPolicy(
            policy_id=policy_id,
            requester_id=requester_id,
            allowed_categories=allowed_categories,
            allowed_sources=allowed_sources,
            max_access_level=max_access_level,
            read_only=read_only,
            valid_from=now,
            valid_until=now + timedelta(hours=valid_hours),
        )
        
        self._policies[requester_id] = policy
        
        logger.info(f"Created policy {policy_id} for {requester_id}")
        
        return policy
    
    async def revoke_policy(self, requester_id: str):
        """Revoke access policy for a requester."""
        if requester_id in self._policies:
            del self._policies[requester_id]
            logger.info(f"Revoked policy for {requester_id}")
    
    async def _audit_request(self, request: AccessRequest):
        """Audit log a request."""
        try:
            date_str = request.requested_at.strftime('%Y%m%d')
            audit_file = self._audit_path / f"access_audit_{date_str}.jsonl"
            
            with open(audit_file, 'a') as f:
                f.write(json.dumps(request.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to audit request: {e}")
    
    async def _notify_anomaly(self, anomaly: AnomalyReport):
        """Notify about detected anomaly."""
        self._anomaly_reports.append(anomaly)
        
        for callback in self._anomaly_callbacks:
            try:
                await callback(anomaly)
            except Exception as e:
                logger.error(f"Anomaly callback error: {e}")
        
        logger.warning(f"Anomaly detected: {anomaly.anomaly_type} - {anomaly.description}")
    
    async def _notify_denial(self, request: AccessRequest):
        """Notify about access denial."""
        for callback in self._denial_callbacks:
            try:
                await callback(request)
            except Exception as e:
                logger.error(f"Denial callback error: {e}")
    
    def register_anomaly_callback(self, callback: Callable):
        """Register callback for anomaly detection."""
        self._anomaly_callbacks.append(callback)
    
    def register_denial_callback(self, callback: Callable):
        """Register callback for access denials."""
        self._denial_callbacks.append(callback)
    
    def get_request(self, request_id: str) -> Optional[AccessRequest]:
        """Get request by ID."""
        return self._requests.get(request_id)
    
    def get_policy(self, requester_id: str) -> Optional[AccessPolicy]:
        """Get policy for requester."""
        return self._policies.get(requester_id)
    
    def get_anomaly_reports(self, hours: int = 24) -> List[AnomalyReport]:
        """Get anomaly reports from specified hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [a for a in self._anomaly_reports if a.detected_at > cutoff]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get firewall statistics."""
        total_requests = len(self._request_history)
        approved = sum(1 for r in self._request_history if r.status == RequestStatus.APPROVED)
        denied = sum(1 for r in self._request_history if r.status == RequestStatus.DENIED)
        rate_limited = sum(1 for r in self._request_history if r.status == RequestStatus.RATE_LIMITED)
        
        return {
            'total_requests': total_requests,
            'approved_requests': approved,
            'denied_requests': denied,
            'rate_limited_requests': rate_limited,
            'approval_rate': approved / total_requests if total_requests > 0 else 0,
            'active_policies': len(self._policies),
            'anomalies_detected': len(self._anomaly_reports),
            'unique_requesters': len(set(r.requester_id for r in self._request_history)),
        }
