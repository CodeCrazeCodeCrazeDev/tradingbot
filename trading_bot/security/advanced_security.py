"""
Advanced Security System
=========================

Comprehensive security infrastructure:
- API key rotation
- IP whitelisting
- 2FA for trading
- Audit logging
- Encryption at rest
- Rate limiting
- DDoS protection
- Security scanning

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
import hashlib
import hmac
import secrets
import json
import base64
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum, auto
from collections import defaultdict, deque
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import cryptography
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not available")
# Try to import pyotp for 2FA
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    logger.warning("pyotp not available for 2FA")


class SecurityLevel(Enum):
    """Security levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditAction(Enum):
    """Audit action types"""
    LOGIN = "login"
    LOGOUT = "logout"
    API_CALL = "api_call"
    TRADE_PLACED = "trade_placed"
    TRADE_CANCELLED = "trade_cancelled"
    CONFIG_CHANGED = "config_changed"
    KEY_ROTATED = "key_rotated"
    ACCESS_DENIED = "access_denied"
    SECURITY_ALERT = "security_alert"


@dataclass
class APIKey:
    """API key data"""
    key_id: str
    key_hash: str
    name: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime] = None
    is_active: bool = True
    ip_whitelist: List[str] = field(default_factory=list)
    rate_limit: int = 100  # requests per minute
    
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def to_dict(self) -> Dict:
        return {
            'key_id': self.key_id,
            'name': self.name,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_active': self.is_active,
            'ip_whitelist': self.ip_whitelist,
            'rate_limit': self.rate_limit
        }


@dataclass
class AuditEntry:
    """Audit log entry"""
    entry_id: str
    timestamp: datetime
    action: AuditAction
    user_id: str
    ip_address: str
    details: Dict[str, Any]
    success: bool
    security_level: SecurityLevel
    
    def to_dict(self) -> Dict:
        return {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action.value,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'details': self.details,
            'success': self.success,
            'security_level': self.security_level.value
        }


@dataclass
class SecurityAlert:
    """Security alert"""
    alert_id: str
    timestamp: datetime
    alert_type: str
    severity: SecurityLevel
    message: str
    source_ip: str
    details: Dict[str, Any]
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat(),
            'alert_type': self.alert_type,
            'severity': self.severity.value,
            'message': self.message,
            'source_ip': self.source_ip,
            'details': self.details,
            'resolved': self.resolved
        }


class APIKeyManager:
    """
    Manages API keys with rotation
    """
    
    def __init__(self, rotation_days: int = 90):
        self.rotation_days = rotation_days
        
        # Keys storage
        self.keys: Dict[str, APIKey] = {}
        
        # Key usage tracking
        self.usage: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        self._lock = threading.RLock()
        self._next_id = 1
        
        logger.info("APIKeyManager initialized")
    
    def _generate_key(self) -> Tuple[str, str]:
        """Generate a new API key"""
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key, key_hash
    
    def _generate_id(self) -> str:
        with self._lock:
            key_id = f"KEY_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_id}"
            self._next_id += 1
            return key_id
    
    def create_key(
        self,
        name: str,
        permissions: List[str],
        expires_days: Optional[int] = None,
        ip_whitelist: Optional[List[str]] = None,
        rate_limit: int = 100
    ) -> Tuple[str, APIKey]:
        """Create a new API key"""
        key, key_hash = self._generate_key()
        key_id = self._generate_id()
        
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        elif self.rotation_days:
            expires_at = datetime.now() + timedelta(days=self.rotation_days)
        
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            permissions=permissions,
            created_at=datetime.now(),
            expires_at=expires_at,
            ip_whitelist=ip_whitelist or [],
            rate_limit=rate_limit
        )
        
        with self._lock:
            self.keys[key_id] = api_key
        
        logger.info(f"API key created: {key_id}")
        
        # Return the actual key only once
        return key, api_key
    
    def validate_key(
        self,
        key: str,
        ip_address: str,
        required_permission: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[APIKey]]:
        """
        Validate an API key
        Returns: (is_valid, error_message, api_key)
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        with self._lock:
            # Find key by hash
            api_key = None
            for k in self.keys.values():
                if k.key_hash == key_hash:
                    api_key = k
                    break
            
            if not api_key:
                return (False, "Invalid API key", None)
            
            if not api_key.is_active:
                return (False, "API key is disabled", None)
            
            if api_key.is_expired():
                return (False, "API key has expired", None)
            
            # Check IP whitelist
            if api_key.ip_whitelist and ip_address not in api_key.ip_whitelist:
                return (False, "IP address not whitelisted", None)
            
            # Check permission
            if required_permission and required_permission not in api_key.permissions:
                return (False, f"Missing permission: {required_permission}", None)
            
            # Check rate limit
            if not self._check_rate_limit(api_key.key_id, api_key.rate_limit):
                return (False, "Rate limit exceeded", None)
            
            # Update last used
            api_key.last_used = datetime.now()
            
            return (True, None, api_key)
    
    def _check_rate_limit(self, key_id: str, limit: int) -> bool:
        """Check if rate limit is exceeded"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Count requests in last minute
        recent = [t for t in self.usage[key_id] if t > minute_ago]
        
        if len(recent) >= limit:
            return False
        
        self.usage[key_id].append(now)
        return True
    
    def rotate_key(self, key_id: str) -> Optional[Tuple[str, APIKey]]:
        """Rotate an API key"""
        with self._lock:
            old_key = self.keys.get(key_id)
            
            if not old_key:
                return None
            
            # Create new key with same settings
            new_key, new_api_key = self.create_key(
                name=old_key.name,
                permissions=old_key.permissions,
                ip_whitelist=old_key.ip_whitelist,
                rate_limit=old_key.rate_limit
            )
            
            # Disable old key
            old_key.is_active = False
            
            logger.info(f"API key rotated: {key_id} -> {new_api_key.key_id}")
            
            return new_key, new_api_key
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        with self._lock:
            if key_id in self.keys:
                self.keys[key_id].is_active = False
                logger.info(f"API key revoked: {key_id}")
                return True
            return False
    
    def get_keys_needing_rotation(self) -> List[APIKey]:
        """Get keys that need rotation"""
        with self._lock:
            threshold = datetime.now() + timedelta(days=7)
            return [
                k for k in self.keys.values()
                if k.is_active and k.expires_at and k.expires_at < threshold
            ]
    
    def list_keys(self) -> List[Dict]:
        """List all keys"""
        with self._lock:
            return [k.to_dict() for k in self.keys.values()]


class IPWhitelist:
    """
    IP whitelisting system
    """
    
    def __init__(self):
        # Whitelisted IPs
        self.whitelist: Set[str] = set()
        
        # Blacklisted IPs
        self.blacklist: Set[str] = set()
        
        # Temporary blocks
        self.temp_blocks: Dict[str, datetime] = {}
        
        # Failed attempts tracking
        self.failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        
        # Configuration
        self.max_failed_attempts = 5
        self.block_duration_minutes = 30
        
        self._lock = threading.RLock()
        
        logger.info("IPWhitelist initialized")
    
    def add_to_whitelist(self, ip: str):
        """Add IP to whitelist"""
        with self._lock:
            self.whitelist.add(ip)
            # Remove from blacklist if present
            self.blacklist.discard(ip)
            logger.info(f"IP whitelisted: {ip}")
    
    def remove_from_whitelist(self, ip: str):
        """Remove IP from whitelist"""
        with self._lock:
            self.whitelist.discard(ip)
    
    def add_to_blacklist(self, ip: str):
        """Add IP to blacklist"""
        with self._lock:
            self.blacklist.add(ip)
            self.whitelist.discard(ip)
            logger.warning(f"IP blacklisted: {ip}")
    
    def is_allowed(self, ip: str) -> Tuple[bool, str]:
        """Check if IP is allowed"""
        with self._lock:
            # Check blacklist
            if ip in self.blacklist:
                return (False, "IP is blacklisted")
            
            # Check temporary blocks
            if ip in self.temp_blocks:
                if datetime.now() < self.temp_blocks[ip]:
                    return (False, "IP is temporarily blocked")
                else:
                    del self.temp_blocks[ip]
            
            # If whitelist is empty, allow all (except blacklisted)
            if not self.whitelist:
                return (True, "")
            
            # Check whitelist
            if ip in self.whitelist:
                return (True, "")
            
            return (False, "IP not in whitelist")
    
    def record_failed_attempt(self, ip: str):
        """Record a failed authentication attempt"""
        with self._lock:
            now = datetime.now()
            
            # Clean old attempts
            cutoff = now - timedelta(minutes=self.block_duration_minutes)
            self.failed_attempts[ip] = [
                t for t in self.failed_attempts[ip]
                if t > cutoff
            ]
            
            # Add new attempt
            self.failed_attempts[ip].append(now)
            
            # Check if should block
            if len(self.failed_attempts[ip]) >= self.max_failed_attempts:
                self.temp_blocks[ip] = now + timedelta(minutes=self.block_duration_minutes)
                logger.warning(f"IP temporarily blocked: {ip}")
    
    def clear_failed_attempts(self, ip: str):
        """Clear failed attempts for an IP"""
        with self._lock:
            if ip in self.failed_attempts:
                del self.failed_attempts[ip]


class TwoFactorAuth:
    """
    Two-factor authentication
    """
    
    def __init__(self):
        # User secrets
        self.secrets: Dict[str, str] = {}
        
        # Backup codes
        self.backup_codes: Dict[str, List[str]] = {}
        
        # Used codes (to prevent replay)
        self.used_codes: Dict[str, Set[str]] = defaultdict(set)
        
        self._lock = threading.RLock()
        
        logger.info("TwoFactorAuth initialized")
    
    def setup_2fa(self, user_id: str) -> Tuple[str, str, List[str]]:
        """
        Setup 2FA for a user
        Returns: (secret, provisioning_uri, backup_codes)
        """
        if not PYOTP_AVAILABLE:
            raise RuntimeError("pyotp not available")
        
        # Generate secret
        secret = pyotp.random_base32()
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        with self._lock:
            self.secrets[user_id] = secret
            self.backup_codes[user_id] = backup_codes
        
        # Generate provisioning URI
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user_id,
            issuer_name="Elite Trading Bot"
        )
        
        logger.info(f"2FA setup for user: {user_id}")
        
        return secret, uri, backup_codes
    
    def verify_code(self, user_id: str, code: str) -> bool:
        """Verify a 2FA code"""
        if not PYOTP_AVAILABLE:
            return False
        
        with self._lock:
            secret = self.secrets.get(user_id)
            
            if not secret:
                return False
            
            # Check if code was already used
            if code in self.used_codes[user_id]:
                return False
            
            # Verify TOTP
            totp = pyotp.TOTP(secret)
            if totp.verify(code, valid_window=1):
                self.used_codes[user_id].add(code)
                return True
            
            # Check backup codes
            if code in self.backup_codes.get(user_id, []):
                self.backup_codes[user_id].remove(code)
                return True
            
            return False
    
    def disable_2fa(self, user_id: str):
        """Disable 2FA for a user"""
        with self._lock:
            if user_id in self.secrets:
                del self.secrets[user_id]
            if user_id in self.backup_codes:
                del self.backup_codes[user_id]
            if user_id in self.used_codes:
                del self.used_codes[user_id]
            
            logger.info(f"2FA disabled for user: {user_id}")
    
    def is_enabled(self, user_id: str) -> bool:
        """Check if 2FA is enabled for a user"""
        return user_id in self.secrets


class AuditLogger:
    """
    Security audit logging
    """
    
    def __init__(self, storage_path: str = "./audit_logs"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory buffer
        self.buffer: deque = deque(maxlen=10000)
        
        # Callbacks
        self.on_critical: List[Callable] = []
        
        self._lock = threading.RLock()
        self._next_id = 1
        
        logger.info("AuditLogger initialized")
    
    def _generate_id(self) -> str:
        with self._lock:
            entry_id = f"AUD_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_id}"
            self._next_id += 1
            return entry_id
    
    def log(
        self,
        action: AuditAction,
        user_id: str,
        ip_address: str,
        details: Dict[str, Any],
        success: bool = True,
        security_level: SecurityLevel = SecurityLevel.LOW
    ) -> AuditEntry:
        """Log an audit entry"""
        entry = AuditEntry(
            entry_id=self._generate_id(),
            timestamp=datetime.now(),
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=success,
            security_level=security_level
        )
        
        with self._lock:
            self.buffer.append(entry)
        
        # Write to file
        self._write_to_file(entry)
        
        # Fire callbacks for critical events
        if security_level == SecurityLevel.CRITICAL:
            for callback in self.on_critical:
                try:
                    callback(entry)
                except Exception as e:
                    logger.error(f"Audit callback error: {e}")
        
        return entry
    
    def _write_to_file(self, entry: AuditEntry):
        """Write entry to file"""
        try:
            date_str = entry.timestamp.strftime('%Y%m%d')
            file_path = self.storage_path / f"audit_{date_str}.jsonl"
            
            with open(file_path, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def search(
        self,
        action: Optional[AuditAction] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        success: Optional[bool] = None
    ) -> List[AuditEntry]:
        """Search audit logs"""
        with self._lock:
            results = list(self.buffer)
            
            if action:
                results = [e for e in results if e.action == action]
            if user_id:
                results = [e for e in results if e.user_id == user_id]
            if ip_address:
                results = [e for e in results if e.ip_address == ip_address]
            if start_time:
                results = [e for e in results if e.timestamp >= start_time]
            if end_time:
                results = [e for e in results if e.timestamp <= end_time]
            if success is not None:
                results = [e for e in results if e.success == success]
            
            return results
    
    def get_recent(self, count: int = 100) -> List[Dict]:
        """Get recent audit entries"""
        with self._lock:
            return [e.to_dict() for e in list(self.buffer)[-count:]]


class EncryptionManager:
    """
    Encryption at rest
    """
    
    def __init__(self, master_key: Optional[str] = None):
        if not CRYPTO_AVAILABLE:
            logger.warning("cryptography not available")
            self.fernet = None
        else:
            if master_key:
                # Derive key from master key
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'elite_trading_bot_salt',
                    iterations=100000
                )
                key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            else:
                # Generate new key
                key = Fernet.generate_key()
            
            self.fernet = Fernet(key)
        
        logger.info("EncryptionManager initialized")
    
    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        if not self.fernet:
            return data
        
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        if not self.fernet:
            return encrypted_data
        
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_dict(self, data: Dict) -> str:
        """Encrypt a dictionary"""
        return self.encrypt(json.dumps(data))
    
    def decrypt_dict(self, encrypted_data: str) -> Dict:
        """Decrypt to a dictionary"""
        return json.loads(self.decrypt(encrypted_data))


class RateLimiter:
    """
    Advanced rate limiting
    """
    
    def __init__(self):
        # Rate limits: {key: (requests, window_seconds)}
        self.limits: Dict[str, Tuple[int, int]] = {}
        
        # Request tracking
        self.requests: Dict[str, deque] = defaultdict(deque)
        
        self._lock = threading.RLock()
        
        logger.info("RateLimiter initialized")
    
    def set_limit(self, key: str, requests: int, window_seconds: int):
        """Set rate limit for a key"""
        self.limits[key] = (requests, window_seconds)
    
    def check_limit(self, key: str, identifier: str) -> Tuple[bool, int]:
        """
        Check if rate limit is exceeded
        Returns: (is_allowed, remaining_requests)
        """
        limit = self.limits.get(key)
        
        if not limit:
            return (True, -1)
        
        max_requests, window = limit
        full_key = f"{key}:{identifier}"
        
        with self._lock:
            now = time.time()
            cutoff = now - window
            
            # Clean old requests
            while self.requests[full_key] and self.requests[full_key][0] < cutoff:
                self.requests[full_key].popleft()
            
            current_count = len(self.requests[full_key])
            remaining = max_requests - current_count
            
            if current_count >= max_requests:
                return (False, 0)
            
            # Record request
            self.requests[full_key].append(now)
            
            return (True, remaining - 1)
    
    def get_reset_time(self, key: str, identifier: str) -> Optional[float]:
        """Get time until rate limit resets"""
        limit = self.limits.get(key)
        
        if not limit:
            return None
        
        _, window = limit
        full_key = f"{key}:{identifier}"
        
        with self._lock:
            if not self.requests[full_key]:
                return None
            
            oldest = self.requests[full_key][0]
            reset_time = oldest + window - time.time()
            
            return max(0, reset_time)


class DDoSProtection:
    """
    DDoS protection
    """
    
    def __init__(
        self,
        requests_per_second: int = 100,
        burst_limit: int = 200,
        block_duration_seconds: int = 300
    ):
        self.rps_limit = requests_per_second
        self.burst_limit = burst_limit
        self.block_duration = block_duration_seconds
        
        # Request tracking
        self.requests: Dict[str, deque] = defaultdict(deque)
        
        # Blocked IPs
        self.blocked: Dict[str, datetime] = {}
        
        # Suspicious IPs
        self.suspicious: Dict[str, int] = defaultdict(int)
        
        self._lock = threading.RLock()
        
        logger.info("DDoSProtection initialized")
    
    def check_request(self, ip: str) -> Tuple[bool, str]:
        """Check if request should be allowed"""
        with self._lock:
            now = datetime.now()
            
            # Check if blocked
            if ip in self.blocked:
                if now < self.blocked[ip]:
                    return (False, "IP is blocked due to suspicious activity")
                else:
                    del self.blocked[ip]
            
            # Clean old requests
            second_ago = now - timedelta(seconds=1)
            while self.requests[ip] and self.requests[ip][0] < second_ago:
                self.requests[ip].popleft()
            
            current_rps = len(self.requests[ip])
            
            # Check burst limit
            if current_rps >= self.burst_limit:
                self._block_ip(ip)
                return (False, "Burst limit exceeded")
            
            # Check RPS limit
            if current_rps >= self.rps_limit:
                self.suspicious[ip] += 1
                
                if self.suspicious[ip] >= 3:
                    self._block_ip(ip)
                    return (False, "Rate limit exceeded repeatedly")
                
                return (False, "Rate limit exceeded")
            
            # Record request
            self.requests[ip].append(now)
            
            # Reset suspicious counter on successful request
            if ip in self.suspicious:
                self.suspicious[ip] = max(0, self.suspicious[ip] - 1)
            
            return (True, "")
    
    def _block_ip(self, ip: str):
        """Block an IP"""
        self.blocked[ip] = datetime.now() + timedelta(seconds=self.block_duration)
        logger.warning(f"IP blocked for DDoS protection: {ip}")
    
    def unblock_ip(self, ip: str):
        """Manually unblock an IP"""
        with self._lock:
            if ip in self.blocked:
                del self.blocked[ip]
            if ip in self.suspicious:
                del self.suspicious[ip]
    
    def get_blocked_ips(self) -> List[str]:
        """Get list of blocked IPs"""
        with self._lock:
            now = datetime.now()
            return [ip for ip, until in self.blocked.items() if until > now]


class SecurityScanner:
    """
    Security vulnerability scanner
    """
    
    def __init__(self):
        # Scan results
        self.results: List[Dict] = []
        
        # Known vulnerabilities
        self.vulnerabilities: List[Dict] = []
        
        self._lock = threading.RLock()
        
        logger.info("SecurityScanner initialized")
    
    def scan_config(self, config: Dict) -> List[Dict]:
        """Scan configuration for security issues"""
        issues = []
        
        # Check for hardcoded secrets
        secret_patterns = ['password', 'secret', 'key', 'token', 'api_key']
        
        def check_dict(d: Dict, path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    check_dict(value, current_path)
                elif isinstance(value, str):
                    # Check for potential secrets
                    if any(p in key.lower() for p in secret_patterns):
                        if len(value) > 0 and not value.startswith('${'):
                            issues.append({
                                'type': 'hardcoded_secret',
                                'severity': 'high',
                                'path': current_path,
                                'message': f"Potential hardcoded secret at {current_path}"
                            })
        
        check_dict(config)
        
        with self._lock:
            self.results.extend(issues)
        
        return issues
    
    def scan_permissions(self, permissions: List[str]) -> List[Dict]:
        """Scan permissions for security issues"""
        issues = []
        
        dangerous_permissions = ['admin', 'root', 'superuser', '*']
        
        for perm in permissions:
            if any(d in perm.lower() for d in dangerous_permissions):
                issues.append({
                    'type': 'dangerous_permission',
                    'severity': 'high',
                    'permission': perm,
                    'message': f"Dangerous permission detected: {perm}"
                })
        
        with self._lock:
            self.results.extend(issues)
        
        return issues
    
    def get_scan_report(self) -> Dict[str, Any]:
        """Get scan report"""
        with self._lock:
            high = [r for r in self.results if r.get('severity') == 'high']
            medium = [r for r in self.results if r.get('severity') == 'medium']
            low = [r for r in self.results if r.get('severity') == 'low']
            
            return {
                'total_issues': len(self.results),
                'high_severity': len(high),
                'medium_severity': len(medium),
                'low_severity': len(low),
                'issues': self.results
            }


class AdvancedSecuritySystem:
    """
    Complete advanced security system
    """
    
    def __init__(self, master_key: Optional[str] = None):
        self.api_key_manager = APIKeyManager()
        self.ip_whitelist = IPWhitelist()
        self.two_factor = TwoFactorAuth()
        self.audit_logger = AuditLogger()
        self.encryption = EncryptionManager(master_key)
        self.rate_limiter = RateLimiter()
        self.ddos_protection = DDoSProtection()
        self.security_scanner = SecurityScanner()
        
        # Security alerts
        self.alerts: deque = deque(maxlen=1000)
        
        self._lock = threading.RLock()
        self._next_alert_id = 1
        
        logger.info("AdvancedSecuritySystem initialized")
    
    def _generate_alert_id(self) -> str:
        with self._lock:
            alert_id = f"SEC_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_alert_id}"
            self._next_alert_id += 1
            return alert_id
    
    def create_alert(
        self,
        alert_type: str,
        severity: SecurityLevel,
        message: str,
        source_ip: str,
        details: Optional[Dict] = None
    ) -> SecurityAlert:
        """Create a security alert"""
        alert = SecurityAlert(
            alert_id=self._generate_alert_id(),
            timestamp=datetime.now(),
            alert_type=alert_type,
            severity=severity,
            message=message,
            source_ip=source_ip,
            details=details or {}
        )
        
        with self._lock:
            self.alerts.append(alert)
        
        # Log to audit
        self.audit_logger.log(
            action=AuditAction.SECURITY_ALERT,
            user_id="system",
            ip_address=source_ip,
            details={'alert': alert.to_dict()},
            security_level=severity
        )
        
        return alert
    
    def authenticate(
        self,
        api_key: str,
        ip_address: str,
        required_permission: Optional[str] = None,
        totp_code: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[APIKey]]:
        """Full authentication flow"""
        # Check DDoS protection
        ddos_ok, ddos_msg = self.ddos_protection.check_request(ip_address)
        if not ddos_ok:
            self.create_alert(
                "ddos_blocked",
                SecurityLevel.HIGH,
                ddos_msg,
                ip_address
            )
            return (False, ddos_msg, None)
        
        # Check IP whitelist
        ip_ok, ip_msg = self.ip_whitelist.is_allowed(ip_address)
        if not ip_ok:
            self.ip_whitelist.record_failed_attempt(ip_address)
            return (False, ip_msg, None)
        
        # Validate API key
        key_ok, key_msg, api_key_obj = self.api_key_manager.validate_key(
            api_key, ip_address, required_permission
        )
        
        if not key_ok:
            self.ip_whitelist.record_failed_attempt(ip_address)
            self.audit_logger.log(
                action=AuditAction.ACCESS_DENIED,
                user_id=user_id or "unknown",
                ip_address=ip_address,
                details={'reason': key_msg},
                success=False,
                security_level=SecurityLevel.MEDIUM
            )
            return (False, key_msg, None)
        
        # Check 2FA if enabled
        if user_id and self.two_factor.is_enabled(user_id):
            if not totp_code:
                return (False, "2FA code required", None)
            
            if not self.two_factor.verify_code(user_id, totp_code):
                self.audit_logger.log(
                    action=AuditAction.ACCESS_DENIED,
                    user_id=user_id,
                    ip_address=ip_address,
                    details={'reason': "Invalid 2FA code"},
                    success=False,
                    security_level=SecurityLevel.HIGH
                )
                return (False, "Invalid 2FA code", None)
        
        # Clear failed attempts on success
        self.ip_whitelist.clear_failed_attempts(ip_address)
        
        # Log successful authentication
        self.audit_logger.log(
            action=AuditAction.LOGIN,
            user_id=user_id or api_key_obj.name,
            ip_address=ip_address,
            details={'key_id': api_key_obj.key_id},
            success=True
        )
        
        return (True, "", api_key_obj)
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary"""
        return {
            'api_keys': {
                'total': len(self.api_key_manager.keys),
                'active': sum(1 for k in self.api_key_manager.keys.values() if k.is_active),
                'needing_rotation': len(self.api_key_manager.get_keys_needing_rotation())
            },
            'blocked_ips': len(self.ddos_protection.get_blocked_ips()),
            'recent_alerts': [a.to_dict() for a in list(self.alerts)[-10:]],
            'scan_report': self.security_scanner.get_scan_report()
        }


# Singleton instance
_security_system: Optional[AdvancedSecuritySystem] = None


def get_security_system(master_key: Optional[str] = None) -> AdvancedSecuritySystem:
    global _security_system
    if _security_system is None:
        _security_system = AdvancedSecuritySystem(master_key)
    return _security_system


# Export
__all__ = [
    'AdvancedSecuritySystem',
    'APIKeyManager',
    'IPWhitelist',
    'TwoFactorAuth',
    'AuditLogger',
    'EncryptionManager',
    'RateLimiter',
    'DDoSProtection',
    'SecurityScanner',
    'APIKey',
    'AuditEntry',
    'AuditAction',
    'SecurityAlert',
    'SecurityLevel',
    'get_security_system'
]
