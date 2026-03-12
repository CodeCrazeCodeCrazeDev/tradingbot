"""
import os
Phase 4: Security & Privacy Manager
Protects API keys, verifies SSL/TLS, scans content, and validates downloads.
"""

import logging
import hashlib
import ssl
import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import certifi

logger = logging.getLogger(__name__)


@dataclass
class SecurityEvent:
    """Security event for audit logging"""
    timestamp: datetime
    event_type: str
    severity: str  # 'INFO', 'WARNING', 'CRITICAL'
    description: str
    metadata: Dict = None
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'metadata': self.metadata or {}
        }


class SecurityManager:
    """
    Manages all security aspects of internet access:
    - API key protection
    - SSL/TLS verification
    - Content scanning
    - Hash verification
    - Audit logging
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.security_log: List[SecurityEvent] = []
        
        # Paths
        self.secure_dir = Path(config.get('secure_dir', 'secure'))
        self.secure_dir.mkdir(exist_ok=True)
        
        self.audit_log_path = self.secure_dir / 'security_audit.log'
        
        # Known model hashes (for verification)
        self.known_hashes: Dict[str, str] = config.get('known_hashes', {})
        
        # Malicious patterns to scan for
        self.malicious_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
            r'compile\s*\(',
            r'os\.system',
            r'subprocess\.',
            r'rm\s+-rf',
            r'del\s+/[fqs]',
        ]
        
        logger.info("Security Manager initialized")
    
    def load_api_keys(self, key_file: str = 'config/api_keys.json') -> Dict[str, str]:
        """
        Securely load API keys from encrypted/protected file.
        Never expose keys in logs or errors.
        """
        try:
            key_path = Path(key_file)
            
            if not key_path.exists():
                logger.warning(f"API key file not found: {key_file}")
                self._log_security_event(
                    'API_KEY_LOAD',
                    'WARNING',
                    f"API key file not found: {key_file}"
                )
                return {}
            
            with open(key_path, 'r') as f:
                keys = json.load(f)
            
            # Validate key format (basic check)
            validated_keys = {}
            for service, key in keys.items():
                if self._validate_api_key_format(service, key):
                    validated_keys[service] = key
                    logger.info(f"✓ Loaded API key for: {service}")
                else:
                    logger.warning(f"✗ Invalid API key format for: {service}")
                    self._log_security_event(
                        'API_KEY_VALIDATION',
                        'WARNING',
                        f"Invalid API key format for {service}"
                    )
            
            self._log_security_event(
                'API_KEY_LOAD',
                'INFO',
                f"Loaded {len(validated_keys)} API keys"
            )
            
            return validated_keys
        
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            self._log_security_event(
                'API_KEY_LOAD',
                'CRITICAL',
                f"Failed to load API keys: {str(e)}"
            )
            return {}
    
    def _validate_api_key_format(self, service: str, key: str) -> bool:
        """Validate API key format (basic checks)"""
        if not key or len(key) < 10:
            return False
        
        # Service-specific validation
        if service == 'news' and not (key.startswith('news_') or len(key) == 32):
            return False
        
        return True
    
    def mask_api_key(self, key: str) -> str:
        """Mask API key for logging (show only first/last 4 chars)"""
        if len(key) <= 8:
            return '***'
        return f"{key[:4]}...{key[-4:]}"
    
    def verify_ssl_certificate(self, url: str) -> Tuple[bool, str]:
        """
        Verify SSL/TLS certificate for a URL.
        Returns (is_valid, message)
        """
        try:
            import urllib.parse
            from urllib.request import urlopen
            
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname
            port = parsed.port or 443
            
            # Create SSL context with certificate verification
            context = ssl.create_default_context(cafile=certifi.where())
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            # Connect and verify
            with ssl.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate validity
                    not_after = datetime.strptime(
                        cert['notAfter'],
                        '%b %d %H:%M:%S %Y %Z'
                    )
                    
                    if datetime.now() > not_after:
                        msg = f"Certificate expired: {not_after}"
                        self._log_security_event(
                            'SSL_VERIFICATION',
                            'CRITICAL',
                            msg,
                            {'url': url}
                        )
                        return False, msg
                    
                    logger.info(f"✓ SSL certificate valid for {hostname}")
                    self._log_security_event(
                        'SSL_VERIFICATION',
                        'INFO',
                        f"SSL verified for {hostname}"
                    )
                    return True, "Certificate valid"
        
        except ssl.SSLError as e:
            msg = f"SSL verification failed: {e}"
            logger.error(msg)
            self._log_security_event(
                'SSL_VERIFICATION',
                'CRITICAL',
                msg,
                {'url': url, 'error': str(e)}
            )
            return False, msg
        
        except Exception as e:
            msg = f"Error verifying SSL: {e}"
            logger.error(msg)
            self._log_security_event(
                'SSL_VERIFICATION',
                'WARNING',
                msg,
                {'url': url, 'error': str(e)}
            )
            return False, msg
    
    def scan_content_for_malicious_code(self, content: str) -> Tuple[bool, List[str]]:
        """
        Scan content for potentially malicious code patterns.
        Returns (is_safe, list_of_issues)
        """
        issues = []
        
        for pattern in self.malicious_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                issues.append(f"Suspicious pattern found: {pattern}")
                logger.warning(f"⚠️ Malicious pattern detected: {pattern}")
        
        is_safe = len(issues) == 0
        
        if not is_safe:
            self._log_security_event(
                'CONTENT_SCAN',
                'CRITICAL',
                f"Malicious content detected: {len(issues)} issues",
                {'issues': issues}
            )
        else:
            self._log_security_event(
                'CONTENT_SCAN',
                'INFO',
                "Content scan passed"
            )
        
        return is_safe, issues
    
    def calculate_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """Calculate cryptographic hash of a file"""
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def verify_file_hash(
        self,
        file_path: Path,
        expected_hash: str,
        algorithm: str = 'sha256'
    ) -> Tuple[bool, str]:
        """
        Verify file hash against expected value.
        Returns (is_valid, message)
        """
        try:
            actual_hash = self.calculate_file_hash(file_path, algorithm)
            
            if actual_hash == expected_hash:
                msg = f"Hash verification passed for {file_path.name}"
                logger.info(f"✓ {msg}")
                self._log_security_event(
                    'HASH_VERIFICATION',
                    'INFO',
                    msg,
                    {'file': str(file_path), 'hash': actual_hash}
                )
                return True, msg
            else:
                msg = f"Hash mismatch for {file_path.name}"
                logger.error(f"✗ {msg}")
                logger.error(f"  Expected: {expected_hash}")
                logger.error(f"  Actual:   {actual_hash}")
                self._log_security_event(
                    'HASH_VERIFICATION',
                    'CRITICAL',
                    msg,
                    {
                        'file': str(file_path),
                        'expected': expected_hash,
                        'actual': actual_hash
                    }
                )
                return False, msg
        
        except Exception as e:
            msg = f"Error verifying hash: {e}"
            logger.error(msg)
            self._log_security_event(
                'HASH_VERIFICATION',
                'WARNING',
                msg,
                {'file': str(file_path), 'error': str(e)}
            )
            return False, msg
    
    def validate_downloaded_model(
        self,
        model_path: Path,
        model_name: str
    ) -> Tuple[bool, str]:
        """
        Validate a downloaded model file.
        Checks hash and scans for malicious content.
        """
        logger.info(f"🔒 Validating downloaded model: {model_name}")
        
        # Check if file exists
        if not model_path.exists():
            msg = f"Model file not found: {model_path}"
            logger.error(msg)
            return False, msg
        
        # Check hash if known
        if model_name in self.known_hashes:
            expected_hash = self.known_hashes[model_name]
            is_valid, msg = self.verify_file_hash(model_path, expected_hash)
            
            if not is_valid:
                return False, msg
        else:
            logger.warning(f"No known hash for {model_name}, calculating...")
            actual_hash = self.calculate_file_hash(model_path)
            logger.info(f"Model hash: {actual_hash}")
            logger.info("⚠️ Add this hash to known_hashes for future verification")
        
        # Scan content if it's a text file
        if model_path.suffix in ['.py', '.txt', '.json', '.yaml']:
            try:
                with open(model_path, 'r') as f:
                    content = f.read()
                
                is_safe, issues = self.scan_content_for_malicious_code(content)
                
                if not is_safe:
                    msg = f"Malicious content detected in {model_name}: {issues}"
                    logger.error(msg)
                    return False, msg
            
            except Exception as e:
                logger.warning(f"Could not scan model content: {e}")
        
        logger.info(f"✅ Model validation passed: {model_name}")
        return True, "Validation successful"
    
    def _log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        metadata: Dict = None
    ):
        """Log a security event"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            description=description,
            metadata=metadata
        )
        
        self.security_log.append(event)
        
        # Write to audit log
        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to audit log: {e}")
        
        # Keep only last 10000 events in memory
        if len(self.security_log) > 10000:
            self.security_log = self.security_log[-10000:]
    
    def get_security_report(self) -> Dict:
        """Generate security report"""
        if not self.security_log:
            return {'status': 'No security events logged'}
        
        # Count by severity
        severity_counts = {}
        event_type_counts = {}
        
        for event in self.security_log:
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
            event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
        
        # Recent critical events
        critical_events = [
            e for e in self.security_log[-100:]
            if e.severity == 'CRITICAL'
        ]
        
        return {
            'total_events': len(self.security_log),
            'severity_breakdown': severity_counts,
            'event_types': event_type_counts,
            'recent_critical_events': len(critical_events),
            'critical_details': [e.to_dict() for e in critical_events[-5:]],
            'audit_log_path': str(self.audit_log_path)
        }
    
    def sanitize_log_message(self, message: str, api_keys: Dict[str, str]) -> str:
        """Remove API keys from log messages"""
        sanitized = message
        
        for service, key in api_keys.items():
            if key in sanitized:
                sanitized = sanitized.replace(key, self.mask_api_key(key))
        
        return sanitized
    
    def check_url_safety(self, url: str) -> Tuple[bool, str]:
        """
        Check if a URL is safe to access.
        Basic checks for known malicious patterns.
        """
        # Must use HTTPS
        if not url.startswith('https://'):
            msg = f"URL must use HTTPS: {url}"
            logger.warning(msg)
            self._log_security_event(
                'URL_SAFETY',
                'WARNING',
                msg
            )
            return False, msg
        
        # Check for suspicious patterns
        suspicious_patterns = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            'file://',
            'javascript:',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in url.lower():
                msg = f"Suspicious URL pattern detected: {pattern}"
                logger.warning(msg)
                self._log_security_event(
                    'URL_SAFETY',
                    'WARNING',
                    msg,
                    {'url': url}
                )
                return False, msg
        
        return True, "URL appears safe"
    
    def create_secure_session_config(self) -> Dict:
        """
        Create secure configuration for HTTP sessions.
        Enforces SSL, timeouts, and security headers.
        """
        return {
            'verify_ssl': True,
            'ssl_context': ssl.create_default_context(cafile=certifi.where()),
            'timeout': 30,
            'max_redirects': 3,
            'headers': {
                'User-Agent': 'AlphaAlgo-TradingBot/1.0',
                'Accept': 'application/json',
            }
        }
