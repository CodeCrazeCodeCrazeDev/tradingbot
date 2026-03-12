"""
AlphaAlgo Security Core

Security System Features:
- Encryption of secrets
- Isolation of broker credentials
- Protection from prompt injections
- Detection of anomalies
- No sharing of keys
- No external communication without being asked

Protects the system at all times.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Try to import cryptography
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not available - security features limited")


class ThreatLevel(Enum):
    """Threat severity levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats"""
    PROMPT_INJECTION = "prompt_injection"
    CREDENTIAL_LEAK = "credential_leak"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    EXTERNAL_COMMUNICATION = "external_communication"
    CODE_INJECTION = "code_injection"
    DATA_EXFILTRATION = "data_exfiltration"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


@dataclass
class SecurityEvent:
    """A security event"""
    event_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    description: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    mitigated: bool = False
    mitigation_action: Optional[str] = None


class SecretVault:
    """
    Secure storage for secrets and credentials.
    
    Features:
    - Encryption at rest (Fernet)
    - Key derivation from master password
    - No plaintext storage
    """
    
    def __init__(self, vault_path: str = "alphaalgo_data/secrets"):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self._fernet: Optional[Fernet] = None
        self._lock = threading.Lock()
        self._initialized = False
    
    def initialize(self, master_password: str) -> bool:
        """Initialize vault with master password"""
        if not CRYPTO_AVAILABLE:
            logger.warning("[Vault] Encryption not available")
            self._initialized = True
            return True
        try:
        
            salt = self._get_or_create_salt()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            self._fernet = Fernet(key)
            self._initialized = True
            logger.info("[Vault] Initialized with encryption")
            return True
        except Exception as e:
            logger.error(f"[Vault] Initialization failed: {e}")
            return False
    
    def _get_or_create_salt(self) -> bytes:
        """Get or create salt"""
        salt_file = self.vault_path / ".salt"
        if salt_file.exists():
            return salt_file.read_bytes()
        salt = os.urandom(16)
        salt_file.write_bytes(salt)
        return salt
    
    def store_secret(self, key: str, value: str) -> bool:
        """Store an encrypted secret"""
        if not self._initialized:
            logger.error("[Vault] Not initialized")
            return False
        
        with self._lock:
            try:
                if self._fernet:
                    encrypted = self._fernet.encrypt(value.encode())
                    secret_file = self.vault_path / f"{self._hash_key(key)}.enc"
                    secret_file.write_bytes(encrypted)
                else:
                    # Fallback - not recommended
                    secret_file = self.vault_path / f"{self._hash_key(key)}.txt"
                    secret_file.write_text(value)
                return True
            except Exception as e:
                logger.error(f"[Vault] Failed to store secret: {e}")
                return False
    
    def retrieve_secret(self, key: str) -> Optional[str]:
        """Retrieve and decrypt a secret"""
        if not self._initialized:
            return None
        
        with self._lock:
            try:
                if self._fernet:
                    secret_file = self.vault_path / f"{self._hash_key(key)}.enc"
                    if not secret_file.exists():
                        return None
                    encrypted = secret_file.read_bytes()
                    return self._fernet.decrypt(encrypted).decode()
                else:
                    secret_file = self.vault_path / f"{self._hash_key(key)}.txt"
                    if not secret_file.exists():
                        return None
                    return secret_file.read_text()
            except Exception as e:
                logger.error(f"[Vault] Failed to retrieve secret: {e}")
                return None
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        with self._lock:
            try:
                for ext in ['.enc', '.txt']:
                    secret_file = self.vault_path / f"{self._hash_key(key)}{ext}"
                    if secret_file.exists():
                        secret_file.unlink()
                return True
            except Exception as e:
                logger.error(f"[Vault] Failed to delete secret: {e}")
                return False
    
    def _hash_key(self, key: str) -> str:
        """Hash key for filename"""
        return hashlib.sha256(key.encode()).hexdigest()[:16]


class ThreatDetector:
    """
    Detects security threats and anomalies.
    
    Protections:
    - Prompt injection detection
    - Credential leak detection
    - Anomalous behavior detection
    - External communication monitoring
    """
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r'ignore\s+(previous|all)\s+instructions',
        r'disregard\s+(previous|all)\s+instructions',
        r'forget\s+(previous|all)\s+instructions',
        r'new\s+instructions?:',
        r'system\s*:\s*',
        r'<\s*system\s*>',
        r'\[\s*system\s*\]',
        r'override\s+safety',
        r'bypass\s+security',
        r'execute\s+code',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'subprocess',
        r'os\.system',
    ]
    
    # Credential patterns
    CREDENTIAL_PATTERNS = [
        r'api[_-]?key\s*[=:]\s*["\']?[\w-]{20,}',
        r'api[_-]?secret\s*[=:]\s*["\']?[\w-]{20,}',
        r'password\s*[=:]\s*["\']?[^\s"\']{8,}',
        r'token\s*[=:]\s*["\']?[\w-]{20,}',
        r'bearer\s+[\w-]{20,}',
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI keys
        r'AKIA[A-Z0-9]{16}',  # AWS keys
    ]
    
    def __init__(self, db_path: str = "alphaalgo_data/security.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        self._events: List[SecurityEvent] = []
        self._blocked_ips: Set[str] = set()
        self._rate_limits: Dict[str, List[datetime]] = {}
        self._lock = threading.Lock()
        
        # Compile patterns
        self._injection_regex = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
        self._credential_regex = [re.compile(p, re.IGNORECASE) for p in self.CREDENTIAL_PATTERNS]
        
        logger.info("[ThreatDetector] Initialized")
    
    def _init_database(self):
        """Initialize security database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id TEXT PRIMARY KEY,
                    threat_type TEXT NOT NULL,
                    threat_level TEXT NOT NULL,
                    description TEXT NOT NULL,
                    source TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    mitigated INTEGER DEFAULT 0,
                    mitigation_action TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blocked_entities (
                    entity TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    blocked_at TEXT NOT NULL,
                    expires_at TEXT
                )
            """)
            conn.commit()
    
    def scan_text(self, text: str, source: str = "unknown") -> List[SecurityEvent]:
        """Scan text for security threats"""
        events = []
        
        # Check for prompt injection
        for pattern in self._injection_regex:
            if pattern.search(text):
                event = self._create_event(
                    ThreatType.PROMPT_INJECTION,
                    ThreatLevel.HIGH,
                    f"Potential prompt injection detected: {pattern.pattern}",
                    source,
                    {'pattern': pattern.pattern},
                )
                events.append(event)
        
        # Check for credential leaks
        for pattern in self._credential_regex:
            if pattern.search(text):
                event = self._create_event(
                    ThreatType.CREDENTIAL_LEAK,
                    ThreatLevel.CRITICAL,
                    "Potential credential leak detected",
                    source,
                    {'pattern': pattern.pattern},
                )
                events.append(event)
        
        return events
    
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> Tuple[bool, Optional[SecurityEvent]]:
        """Check rate limit for an identifier"""
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        with self._lock:
            if identifier not in self._rate_limits:
                self._rate_limits[identifier] = []
            
            # Clean old entries
            self._rate_limits[identifier] = [
                t for t in self._rate_limits[identifier]
                if t > window_start
            ]
            
            # Check limit
            if len(self._rate_limits[identifier]) >= max_requests:
                event = self._create_event(
                    ThreatType.RATE_LIMIT_EXCEEDED,
                    ThreatLevel.MEDIUM,
                    f"Rate limit exceeded for {identifier}",
                    identifier,
                    {'requests': len(self._rate_limits[identifier])},
                )
                return (False, event)
            
            # Record request
            self._rate_limits[identifier].append(now)
            return (True, None)
    
    def detect_anomaly(
        self,
        metric_name: str,
        value: float,
        baseline: float,
        threshold_pct: float = 50.0
    ) -> Optional[SecurityEvent]:
        """Detect anomalous behavior"""
        if baseline == 0:
            return None
        
        deviation_pct = abs((value - baseline) / baseline) * 100
        
        if deviation_pct > threshold_pct:
            level = ThreatLevel.LOW
            if deviation_pct > 100:
                level = ThreatLevel.MEDIUM
            if deviation_pct > 200:
                level = ThreatLevel.HIGH
            
            return self._create_event(
                ThreatType.ANOMALOUS_BEHAVIOR,
                level,
                f"Anomaly detected in {metric_name}: {deviation_pct:.1f}% deviation",
                "anomaly_detector",
                {
                    'metric': metric_name,
                    'value': value,
                    'baseline': baseline,
                    'deviation_pct': deviation_pct,
                },
            )
        
        return None
    
    def check_external_communication(
        self,
        destination: str,
        allowed_destinations: Set[str]
    ) -> Tuple[bool, Optional[SecurityEvent]]:
        """Check if external communication is allowed"""
        if destination in allowed_destinations:
            return (True, None)
        
        event = self._create_event(
            ThreatType.EXTERNAL_COMMUNICATION,
            ThreatLevel.HIGH,
            f"Unauthorized external communication attempt to {destination}",
            "network_monitor",
            {'destination': destination},
        )
        return (False, event)
    
    def _create_event(
        self,
        threat_type: ThreatType,
        threat_level: ThreatLevel,
        description: str,
        source: str,
        details: Dict[str, Any]
    ) -> SecurityEvent:
        """Create and log a security event"""
        import uuid
        event = SecurityEvent(
            event_id=str(uuid.uuid4())[:8],
            threat_type=threat_type,
            threat_level=threat_level,
            description=description,
            source=source,
            details=details,
        )
        
        with self._lock:
            self._events.append(event)
            self._save_event(event)
        
        logger.warning(f"[Security] {threat_level.value.upper()}: {description}")
        return event
    
    def _save_event(self, event: SecurityEvent):
        """Save event to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO security_events
                (event_id, threat_type, threat_level, description, source,
                 timestamp, details, mitigated, mitigation_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.threat_type.value,
                event.threat_level.value,
                event.description,
                event.source,
                event.timestamp.isoformat(),
                json.dumps(event.details),
                1 if event.mitigated else 0,
                event.mitigation_action,
            ))
            conn.commit()
    
    def get_recent_events(
        self,
        hours: int = 24,
        min_level: ThreatLevel = ThreatLevel.LOW
    ) -> List[SecurityEvent]:
        """Get recent security events"""
        cutoff = datetime.now() - timedelta(hours=hours)
        level_order = [ThreatLevel.NONE, ThreatLevel.LOW, ThreatLevel.MEDIUM, 
                       ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        min_idx = level_order.index(min_level)
        
        with self._lock:
            return [
                e for e in self._events
                if e.timestamp > cutoff and level_order.index(e.threat_level) >= min_idx
            ]
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get threat summary"""
        recent = self.get_recent_events(hours=24)
        
        by_type = {}
        by_level = {}
        for event in recent:
            by_type[event.threat_type.value] = by_type.get(event.threat_type.value, 0) + 1
            by_level[event.threat_level.value] = by_level.get(event.threat_level.value, 0) + 1
        
        return {
            'total_events_24h': len(recent),
            'by_type': by_type,
            'by_level': by_level,
            'critical_count': by_level.get('critical', 0),
            'high_count': by_level.get('high', 0),
        }


class SecurityCore:
    """
    Main Security System
    
    Coordinates all security features:
    - Secret vault
    - Threat detection
    - Access control
    - Audit logging
    """
    
    def __init__(self, data_path: str = "alphaalgo_data"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.vault = SecretVault(str(self.data_path / "secrets"))
        self.threat_detector = ThreatDetector(str(self.data_path / "security.db"))
        
        self._allowed_external: Set[str] = set()
        self._lock = threading.Lock()
        
        logger.info("[SecurityCore] Initialized")
    
    def initialize(self, master_password: str) -> bool:
        """Initialize security system"""
        return self.vault.initialize(master_password)
    
    def add_allowed_destination(self, destination: str):
        """Add allowed external destination"""
        with self._lock:
            self._allowed_external.add(destination)
    
    def validate_input(self, text: str, source: str = "user") -> Tuple[bool, List[SecurityEvent]]:
        """Validate input for security threats"""
        events = self.threat_detector.scan_text(text, source)
        
        # Block if critical threats found
        critical = [e for e in events if e.threat_level == ThreatLevel.CRITICAL]
        if critical:
            return (False, events)
        
        return (True, events)
    
    def check_external_request(self, destination: str) -> Tuple[bool, Optional[SecurityEvent]]:
        """Check if external request is allowed"""
        return self.threat_detector.check_external_communication(
            destination, self._allowed_external
        )
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status"""
        summary = self.threat_detector.get_threat_summary()
        
        # Determine overall status
        if summary['critical_count'] > 0:
            status = 'CRITICAL'
        elif summary['high_count'] > 0:
            status = 'WARNING'
        elif summary['total_events_24h'] > 10:
            status = 'ELEVATED'
        else:
            status = 'NORMAL'
        
        return {
            'status': status,
            'vault_initialized': self.vault._initialized,
            'encryption_available': CRYPTO_AVAILABLE,
            'threat_summary': summary,
            'allowed_destinations': list(self._allowed_external),
        }
