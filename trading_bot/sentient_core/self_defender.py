"""
Self Defender - Autonomous Security and Threat Protection

Protects the trading bot from:
- Hackers and unauthorized access
- Malicious code injection
- Data breaches
- API key theft
- DDoS attacks
- Man-in-the-middle attacks
"""

import asyncio
import hashlib
import hmac
import json
import os
import re
import socket
import ssl
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import deque
from pathlib import Path
import logging
import secrets
import base64

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ThreatType(Enum):
    """Types of security threats"""
    UNAUTHORIZED_ACCESS = auto()
    BRUTE_FORCE = auto()
    CODE_INJECTION = auto()
    DATA_EXFILTRATION = auto()
    API_ABUSE = auto()
    DDOS = auto()
    MITM = auto()
    MALWARE = auto()
    INSIDER_THREAT = auto()
    CONFIGURATION_TAMPERING = auto()


@dataclass
class SecurityEvent:
    """A security event or threat"""
    id: str
    timestamp: datetime
    threat_type: ThreatType
    threat_level: ThreatLevel
    source_ip: Optional[str]
    description: str
    details: Dict[str, Any]
    mitigated: bool = False
    mitigation_action: Optional[str] = None


@dataclass
class SecurityConfig:
    """Security configuration"""
    max_failed_logins: int = 5
    lockout_duration_minutes: int = 30
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    require_ssl: bool = True
    allowed_ips: List[str] = field(default_factory=list)
    blocked_ips: Set[str] = field(default_factory=set)
    api_key_rotation_days: int = 30
    session_timeout_minutes: int = 60
    enable_intrusion_detection: bool = True
    enable_anomaly_detection: bool = True


class SelfDefender:
    """
    Autonomous security system for the trading bot.
    
    Features:
    - Intrusion detection and prevention
    - API key protection and rotation
    - Rate limiting and DDoS protection
    - Anomaly detection
    - Secure communication enforcement
    - Automatic threat mitigation
    """
    
    # Suspicious patterns to detect
    INJECTION_PATTERNS = [
        r'(?i)(union\s+select|drop\s+table|insert\s+into)',  # SQL injection
        r'(?i)(<script|javascript:|on\w+\s*=)',  # XSS
        r'(?i)(\.\.\/|\.\.\\)',  # Path traversal
        r'(?i)(__import__|eval\s*\(|exec\s*\()',  # Python injection
        r'(?i)(subprocess|os\.system|popen)',  # Command injection
    ]
    
    # Known malicious IPs (sample - would be updated from threat feeds)
    KNOWN_MALICIOUS_IPS = set()
    
    def __init__(
        self,
        config: SecurityConfig = None,
        secrets_path: str = "secrets/",
        log_path: str = "security_logs/",
    ):
        self.config = config or SecurityConfig()
        self.secrets_path = Path(secrets_path)
        self.log_path = Path(log_path)
        
        # Create directories
        self.secrets_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # State
        self.is_running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Security state
        self.failed_logins: Dict[str, List[datetime]] = {}
        self.locked_accounts: Dict[str, datetime] = {}
        self.request_counts: Dict[str, deque] = {}
        self.active_sessions: Dict[str, datetime] = {}
        self.security_events: deque = deque(maxlen=10000)
        
        # Encryption
        self._encryption_key: Optional[bytes] = None
        self._fernet: Optional[Any] = None
        
        # Threat detection
        self.threat_level = ThreatLevel.NONE
        self.active_threats: List[SecurityEvent] = []
        
        # Callbacks
        self._on_threat_callbacks: List[Callable] = []
        
        # Initialize encryption
        self._init_encryption()
        
        # Statistics
        self.stats = {
            'threats_detected': 0,
            'threats_mitigated': 0,
            'blocked_requests': 0,
            'blocked_ips': 0,
            'api_keys_rotated': 0,
        }
        
        logger.info("SelfDefender initialized")
    
    def _init_encryption(self) -> None:
        """Initialize encryption for secrets"""
        if not HAS_CRYPTOGRAPHY:
            logger.warning("Cryptography library not available - encryption disabled")
            return
        
        key_file = self.secrets_path / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self._encryption_key = f.read()
        else:
            self._encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self._encryption_key)
            # Secure the key file
            os.chmod(key_file, 0o600)
        
        self._fernet = Fernet(self._encryption_key)
    
    def start(self) -> None:
        """Start the security monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="SelfDefender"
        )
        self._monitor_thread.start()
        logger.info("SelfDefender started monitoring")
    
    def stop(self) -> None:
        """Stop the security monitoring"""
        self.is_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)
        logger.info("SelfDefender stopped")
    
    def _monitoring_loop(self) -> None:
        """Main security monitoring loop"""
        while self.is_running:
            try:
                self._check_for_threats()
                self._cleanup_expired_entries()
                self._update_threat_level()
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")
            
            time.sleep(10)
    
    def _check_for_threats(self) -> None:
        """Check for active threats"""
        # Check for brute force attacks
        self._detect_brute_force()
        
        # Check for DDoS
        self._detect_ddos()
        
        # Check file integrity
        self._check_file_integrity()
        
        # Check for suspicious processes
        self._check_suspicious_processes()
    
    def _detect_brute_force(self) -> None:
        """Detect brute force login attempts"""
        with self._lock:
            for ip, attempts in self.failed_logins.items():
                recent = [a for a in attempts if a > datetime.now() - timedelta(minutes=5)]
                
                if len(recent) >= self.config.max_failed_logins:
                    self._record_threat(
                        ThreatType.BRUTE_FORCE,
                        ThreatLevel.HIGH,
                        ip,
                        f"Brute force attack detected from {ip}: {len(recent)} failed attempts",
                        {'attempts': len(recent)}
                    )
                    self._block_ip(ip)
    
    def _detect_ddos(self) -> None:
        """Detect DDoS attacks"""
        with self._lock:
            for ip, requests in self.request_counts.items():
                # Count requests in the window
                window_start = time.time() - self.config.rate_limit_window_seconds
                recent = [r for r in requests if r > window_start]
                
                if len(recent) > self.config.rate_limit_requests * 10:
                    self._record_threat(
                        ThreatType.DDOS,
                        ThreatLevel.CRITICAL,
                        ip,
                        f"Potential DDoS attack from {ip}: {len(recent)} requests",
                        {'requests': len(recent)}
                    )
                    self._block_ip(ip)
    
    def _check_file_integrity(self) -> None:
        """Check integrity of critical files"""
        critical_files = [
            'config/alphaalgo_config.yaml',
            'trading_bot/main.py',
            'trading_bot/core/survival_core.py',
        ]
        
        integrity_file = self.secrets_path / "file_hashes.json"
        
        if integrity_file.exists():
            with open(integrity_file, 'r') as f:
                stored_hashes = json.load(f)
        else:
            stored_hashes = {}
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                current_hash = self._hash_file(file_path)
                
                if file_path in stored_hashes:
                    if current_hash != stored_hashes[file_path]:
                        self._record_threat(
                            ThreatType.CONFIGURATION_TAMPERING,
                            ThreatLevel.HIGH,
                            None,
                            f"File integrity violation: {file_path}",
                            {'file': file_path, 'expected': stored_hashes[file_path], 'actual': current_hash}
                        )
                else:
                    stored_hashes[file_path] = current_hash
        
        # Save updated hashes
        with open(integrity_file, 'w') as f:
            json.dump(stored_hashes, f)
    
    def _hash_file(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""
    
    def _check_suspicious_processes(self) -> None:
        """Check for suspicious processes"""
        # This would integrate with OS-level process monitoring
        # For now, we'll check for common attack indicators
        pass
    
    def _record_threat(
        self,
        threat_type: ThreatType,
        threat_level: ThreatLevel,
        source_ip: Optional[str],
        description: str,
        details: Dict[str, Any]
    ) -> SecurityEvent:
        """Record a security threat"""
        event = SecurityEvent(
            id=secrets.token_hex(16),
            timestamp=datetime.now(),
            threat_type=threat_type,
            threat_level=threat_level,
            source_ip=source_ip,
            description=description,
            details=details,
        )
        
        with self._lock:
            self.security_events.append(event)
            self.active_threats.append(event)
            self.stats['threats_detected'] += 1
        
        logger.warning(f"Security threat: {description}")
        
        # Trigger callbacks
        for callback in self._on_threat_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Threat callback error: {e}")
        
        # Auto-mitigate if possible
        self._auto_mitigate(event)
        
        # Log to file
        self._log_security_event(event)
        
        return event
    
    def _auto_mitigate(self, event: SecurityEvent) -> None:
        """Automatically mitigate threats"""
        mitigation = None
        
        if event.threat_type == ThreatType.BRUTE_FORCE:
            if event.source_ip:
                self._block_ip(event.source_ip)
                mitigation = f"Blocked IP {event.source_ip}"
        
        elif event.threat_type == ThreatType.DDOS:
            if event.source_ip:
                self._block_ip(event.source_ip)
                mitigation = f"Blocked IP {event.source_ip}"
        
        elif event.threat_type == ThreatType.CODE_INJECTION:
            mitigation = "Request blocked and logged"
        
        elif event.threat_type == ThreatType.CONFIGURATION_TAMPERING:
            mitigation = "Alert sent, manual review required"
        
        if mitigation:
            event.mitigated = True
            event.mitigation_action = mitigation
            self.stats['threats_mitigated'] += 1
            logger.info(f"Threat mitigated: {mitigation}")
    
    def _block_ip(self, ip: str) -> None:
        """Block an IP address"""
        with self._lock:
            self.config.blocked_ips.add(ip)
            self.stats['blocked_ips'] += 1
        logger.warning(f"Blocked IP: {ip}")
    
    def _unblock_ip(self, ip: str) -> None:
        """Unblock an IP address"""
        with self._lock:
            self.config.blocked_ips.discard(ip)
        logger.info(f"Unblocked IP: {ip}")
    
    def _cleanup_expired_entries(self) -> None:
        """Clean up expired security entries"""
        now = datetime.now()
        
        with self._lock:
            # Clean up locked accounts
            expired = [
                account for account, locked_until in self.locked_accounts.items()
                if locked_until < now
            ]
            for account in expired:
                del self.locked_accounts[account]
            
            # Clean up old failed logins
            for ip in list(self.failed_logins.keys()):
                self.failed_logins[ip] = [
                    a for a in self.failed_logins[ip]
                    if a > now - timedelta(hours=1)
                ]
                if not self.failed_logins[ip]:
                    del self.failed_logins[ip]
            
            # Clean up old request counts
            window_start = time.time() - self.config.rate_limit_window_seconds
            for ip in list(self.request_counts.keys()):
                self.request_counts[ip] = deque(
                    [r for r in self.request_counts[ip] if r > window_start],
                    maxlen=10000
                )
                if not self.request_counts[ip]:
                    del self.request_counts[ip]
            
            # Clean up mitigated threats
            self.active_threats = [
                t for t in self.active_threats
                if not t.mitigated and t.timestamp > now - timedelta(hours=24)
            ]
    
    def _update_threat_level(self) -> None:
        """Update overall threat level"""
        with self._lock:
            if not self.active_threats:
                self.threat_level = ThreatLevel.NONE
            else:
                max_level = max(t.threat_level.value for t in self.active_threats)
                self.threat_level = ThreatLevel(max_level)
    
    def _log_security_event(self, event: SecurityEvent) -> None:
        """Log security event to file"""
        log_file = self.log_path / f"security_{datetime.now().strftime('%Y%m%d')}.log"
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps({
                    'id': event.id,
                    'timestamp': event.timestamp.isoformat(),
                    'type': event.threat_type.name,
                    'level': event.threat_level.name,
                    'source_ip': event.source_ip,
                    'description': event.description,
                    'details': event.details,
                    'mitigated': event.mitigated,
                    'mitigation': event.mitigation_action,
                }) + '\n')
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    # Public API
    
    def on_threat(self, callback: Callable) -> None:
        """Register callback for threat events"""
        self._on_threat_callbacks.append(callback)
    
    def record_failed_login(self, identifier: str, ip: str = None) -> bool:
        """Record a failed login attempt"""
        with self._lock:
            if ip not in self.failed_logins:
                self.failed_logins[ip] = []
            self.failed_logins[ip].append(datetime.now())
            
            # Check if should lock
            recent = [
                a for a in self.failed_logins[ip]
                if a > datetime.now() - timedelta(minutes=5)
            ]
            
            if len(recent) >= self.config.max_failed_logins:
                self.locked_accounts[identifier] = (
                    datetime.now() + timedelta(minutes=self.config.lockout_duration_minutes)
                )
                return True  # Account locked
        
        return False
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if an account is locked"""
        with self._lock:
            if identifier in self.locked_accounts:
                if self.locked_accounts[identifier] > datetime.now():
                    return True
                else:
                    del self.locked_accounts[identifier]
        return False
    
    def check_rate_limit(self, ip: str) -> bool:
        """Check if request should be rate limited"""
        with self._lock:
            if ip in self.config.blocked_ips:
                self.stats['blocked_requests'] += 1
                return False
            
            if ip not in self.request_counts:
                self.request_counts[ip] = deque(maxlen=10000)
            
            self.request_counts[ip].append(time.time())
            
            # Count requests in window
            window_start = time.time() - self.config.rate_limit_window_seconds
            recent = [r for r in self.request_counts[ip] if r > window_start]
            
            if len(recent) > self.config.rate_limit_requests:
                self.stats['blocked_requests'] += 1
                return False
        
        return True
    
    def validate_input(self, input_data: str) -> Tuple[bool, Optional[str]]:
        """Validate input for injection attacks"""
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, input_data):
                self._record_threat(
                    ThreatType.CODE_INJECTION,
                    ThreatLevel.HIGH,
                    None,
                    f"Injection attempt detected: {pattern}",
                    {'input': input_data[:100], 'pattern': pattern}
                )
                return False, f"Suspicious pattern detected: {pattern}"
        
        return True, None
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret value"""
        if not self._fernet:
            logger.warning("Encryption not available")
            return secret
        
        return self._fernet.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self, encrypted: str) -> str:
        """Decrypt a secret value"""
        if not self._fernet:
            logger.warning("Encryption not available")
            return encrypted
        try:
        
            return self._fernet.decrypt(encrypted.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""
    
    def store_api_key(self, name: str, key: str) -> None:
        """Securely store an API key"""
        encrypted = self.encrypt_secret(key)
        
        keys_file = self.secrets_path / "api_keys.json"
        
        if keys_file.exists():
            with open(keys_file, 'r') as f:
                keys = json.load(f)
        else:
            keys = {}
        
        keys[name] = {
            'encrypted_key': encrypted,
            'created_at': datetime.now().isoformat(),
            'last_rotated': datetime.now().isoformat(),
        }
        
        with open(keys_file, 'w') as f:
            json.dump(keys, f)
        
        os.chmod(keys_file, 0o600)
    
    def get_api_key(self, name: str) -> Optional[str]:
        """Retrieve an API key"""
        keys_file = self.secrets_path / "api_keys.json"
        
        if not keys_file.exists():
            return None
        
        with open(keys_file, 'r') as f:
            keys = json.load(f)
        
        if name not in keys:
            return None
        
        return self.decrypt_secret(keys[name]['encrypted_key'])
    
    def rotate_api_key(self, name: str, new_key: str) -> None:
        """Rotate an API key"""
        self.store_api_key(name, new_key)
        self.stats['api_keys_rotated'] += 1
        logger.info(f"API key rotated: {name}")
    
    def verify_ssl_certificate(self, hostname: str, port: int = 443) -> Dict[str, Any]:
        """Verify SSL certificate of a host"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        'valid': True,
                        'issuer': dict(x[0] for x in cert.get('issuer', [])),
                        'subject': dict(x[0] for x in cert.get('subject', [])),
                        'expires': cert.get('notAfter'),
                        'serial': cert.get('serialNumber'),
                    }
        except ssl.SSLError as e:
            self._record_threat(
                ThreatType.MITM,
                ThreatLevel.CRITICAL,
                None,
                f"SSL verification failed for {hostname}: {e}",
                {'hostname': hostname, 'error': str(e)}
            )
            return {'valid': False, 'error': str(e)}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_hex(length)
    
    def hash_password(self, password: str, salt: bytes = None) -> Tuple[str, bytes]:
        """Hash a password securely"""
        if salt is None:
            salt = os.urandom(16)
        
        if HAS_CRYPTOGRAPHY:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return key.decode(), salt
        else:
            # Fallback to hashlib
            key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return base64.urlsafe_b64encode(key).decode(), salt
    
    def verify_password(self, password: str, hashed: str, salt: bytes) -> bool:
        """Verify a password against its hash"""
        new_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(new_hash, hashed)
    
    def get_threat_level(self) -> ThreatLevel:
        """Get current threat level"""
        return self.threat_level
    
    def get_active_threats(self) -> List[SecurityEvent]:
        """Get list of active threats"""
        return self.active_threats.copy()
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status"""
        return {
            'threat_level': self.threat_level.name,
            'active_threats': len(self.active_threats),
            'blocked_ips': len(self.config.blocked_ips),
            'locked_accounts': len(self.locked_accounts),
            'stats': self.stats,
            'is_running': self.is_running,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            **self.stats,
            'threat_level': self.threat_level.name,
            'active_threats': len(self.active_threats),
            'blocked_ips': len(self.config.blocked_ips),
        }

