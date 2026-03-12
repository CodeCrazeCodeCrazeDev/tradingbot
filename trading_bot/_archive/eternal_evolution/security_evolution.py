"""
Security Evolution Engine - Self-Evolving Security System
==========================================================

Continuously evolves and improves security:
- Attack detection and prevention
- Encryption and key management
- Access control evolution
- Anomaly detection
- Threat intelligence integration
- Vulnerability scanning
- Incident response automation

Learns from attacks and threats to build stronger defenses.
"""

import asyncio
import logging
import json
import hashlib
import hmac
import secrets
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from collections import defaultdict
import threading

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


class ThreatType(Enum):
    """Types of security threats"""
    BRUTE_FORCE = "brute_force"
    INJECTION = "injection"
    XSS = "xss"
    CSRF = "csrf"
    MAN_IN_MIDDLE = "man_in_middle"
    REPLAY_ATTACK = "replay_attack"
    DOS = "dos"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    API_ABUSE = "api_abuse"
    CREDENTIAL_STUFFING = "credential_stuffing"
    BOT_ATTACK = "bot_attack"
    INSIDER_THREAT = "insider_threat"
    MARKET_MANIPULATION = "market_manipulation"


class SecurityLayer(Enum):
    """Security layers that can be evolved"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ENCRYPTION = "encryption"
    INPUT_VALIDATION = "input_validation"
    RATE_LIMITING = "rate_limiting"
    ANOMALY_DETECTION = "anomaly_detection"
    AUDIT_LOGGING = "audit_logging"
    NETWORK_SECURITY = "network_security"
    API_SECURITY = "api_security"
    DATA_PROTECTION = "data_protection"


@dataclass
class SecurityEvent:
    """A security event"""
    event_id: str
    event_type: str
    threat_type: Optional[ThreatType]
    severity: str  # low, medium, high, critical
    source_ip: Optional[str]
    user_id: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    blocked: bool = False
    false_positive: bool = False


@dataclass
class SecurityRule:
    """A security rule"""
    rule_id: str
    layer: SecurityLayer
    condition: str
    action: str  # block, alert, log, challenge
    enabled: bool = True
    hits: int = 0
    false_positives: int = 0
    effectiveness: float = 1.0


@dataclass
class ThreatIntelligence:
    """Threat intelligence data"""
    threat_type: ThreatType
    indicators: List[str]
    severity: str
    confidence: float
    source: str
    last_updated: datetime


class SecurityEvolutionEngine:
    """
    Self-Evolving Security Engine
    
    Continuously learns and improves security by:
    1. Detecting and analyzing attacks
    2. Evolving detection rules
    3. Adapting to new threat patterns
    4. Optimizing security vs usability balance
    5. Automating incident response
    
    The goal: Maximum security with minimum friction.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Security layer configurations (evolvable)
        self.layers = {
            SecurityLayer.AUTHENTICATION: {
                'enabled': True,
                'max_attempts': 5,
                'lockout_duration': 300,  # seconds
                'require_2fa': False,
                'session_timeout': 3600,
                'password_min_length': 12
            },
            SecurityLayer.AUTHORIZATION: {
                'enabled': True,
                'default_deny': True,
                'role_based': True,
                'attribute_based': False,
                'permission_cache_ttl': 300
            },
            SecurityLayer.ENCRYPTION: {
                'enabled': True,
                'algorithm': 'AES-256-GCM',
                'key_rotation_days': 30,
                'tls_min_version': '1.2',
                'encrypt_at_rest': True
            },
            SecurityLayer.INPUT_VALIDATION: {
                'enabled': True,
                'sanitize_html': True,
                'validate_json': True,
                'max_input_length': 10000,
                'block_sql_injection': True,
                'block_xss': True
            },
            SecurityLayer.RATE_LIMITING: {
                'enabled': True,
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'burst_limit': 20,
                'by_ip': True,
                'by_user': True
            },
            SecurityLayer.ANOMALY_DETECTION: {
                'enabled': True,
                'sensitivity': 0.7,
                'learning_period_days': 7,
                'alert_threshold': 0.8,
                'auto_block_threshold': 0.95
            },
            SecurityLayer.AUDIT_LOGGING: {
                'enabled': True,
                'log_all_requests': False,
                'log_auth_events': True,
                'log_data_access': True,
                'retention_days': 90
            },
            SecurityLayer.NETWORK_SECURITY: {
                'enabled': True,
                'allowed_ips': [],
                'blocked_ips': [],
                'geo_blocking': False,
                'blocked_countries': []
            },
            SecurityLayer.API_SECURITY: {
                'enabled': True,
                'require_api_key': True,
                'validate_signatures': True,
                'replay_protection': True,
                'nonce_expiry': 300
            },
            SecurityLayer.DATA_PROTECTION: {
                'enabled': True,
                'mask_sensitive': True,
                'encrypt_pii': True,
                'data_classification': True,
                'access_logging': True
            }
        }
        
        # Security rules (evolvable)
        self.rules: List[SecurityRule] = self._initialize_default_rules()
        
        # Threat intelligence
        self.threat_intel: List[ThreatIntelligence] = []
        
        # Security events history
        self.events: List[SecurityEvent] = []
        
        # Rate limiting state
        self.rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        
        # Blocked entities
        self.blocked_ips: Set[str] = set()
        self.blocked_users: Set[str] = set()
        
        # Behavioral baselines
        self.baselines: Dict[str, Dict] = {}
        
        # Evolution tracking
        self.evolution_history: List[Dict] = []
        
        # Statistics
        self.stats = {
            'events_processed': 0,
            'attacks_blocked': 0,
            'false_positives': 0,
            'rules_evolved': 0,
            'threats_detected': 0,
            'successful_authentications': 0,
            'failed_authentications': 0
        }
        
        # Persistence
        self.state_path = Path(self.config.get('state_path', 'security_evolution_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        # Nonce tracking for replay protection
        self.used_nonces: Dict[str, datetime] = {}
        self._nonce_cleanup_lock = threading.Lock()
        
        self._load_state()
        logger.info("Security Evolution Engine initialized")
    
    def _initialize_default_rules(self) -> List[SecurityRule]:
        """Initialize default security rules"""
        return [
            SecurityRule(
                rule_id="auth_brute_force",
                layer=SecurityLayer.AUTHENTICATION,
                condition="failed_attempts > 5 in 5 minutes",
                action="block"
            ),
            SecurityRule(
                rule_id="sql_injection",
                layer=SecurityLayer.INPUT_VALIDATION,
                condition="input contains SQL keywords",
                action="block"
            ),
            SecurityRule(
                rule_id="xss_attempt",
                layer=SecurityLayer.INPUT_VALIDATION,
                condition="input contains script tags",
                action="block"
            ),
            SecurityRule(
                rule_id="rate_limit_exceeded",
                layer=SecurityLayer.RATE_LIMITING,
                condition="requests > limit",
                action="block"
            ),
            SecurityRule(
                rule_id="anomalous_behavior",
                layer=SecurityLayer.ANOMALY_DETECTION,
                condition="behavior score > threshold",
                action="alert"
            ),
            SecurityRule(
                rule_id="replay_attack",
                layer=SecurityLayer.API_SECURITY,
                condition="nonce already used",
                action="block"
            ),
            SecurityRule(
                rule_id="unusual_trading",
                layer=SecurityLayer.ANOMALY_DETECTION,
                condition="trading pattern anomaly",
                action="alert"
            ),
            SecurityRule(
                rule_id="data_exfiltration",
                layer=SecurityLayer.DATA_PROTECTION,
                condition="large data export",
                action="alert"
            )
        ]
    
    def validate_request(self, request: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate an incoming request"""
        self.stats['events_processed'] += 1
        
        source_ip = request.get('ip', 'unknown')
        user_id = request.get('user_id')
        
        # Check if blocked
        if source_ip in self.blocked_ips:
            return False, "IP is blocked"
        if user_id and user_id in self.blocked_users:
            return False, "User is blocked"
        
        # Rate limiting
        if not self._check_rate_limit(source_ip, user_id):
            self._record_event(SecurityEvent(
                event_id=f"rate_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                event_type="rate_limit_exceeded",
                threat_type=ThreatType.DOS,
                severity="medium",
                source_ip=source_ip,
                user_id=user_id,
                details=request,
                blocked=True
            ))
            return False, "Rate limit exceeded"
        
        # Input validation
        if 'data' in request:
            is_safe, reason = self._validate_input(request['data'])
            if not is_safe:
                self._record_event(SecurityEvent(
                    event_id=f"input_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    event_type="malicious_input",
                    threat_type=ThreatType.INJECTION,
                    severity="high",
                    source_ip=source_ip,
                    user_id=user_id,
                    details={'reason': reason, 'data': str(request['data'])[:100]},
                    blocked=True
                ))
                self.stats['attacks_blocked'] += 1
                return False, reason
        
        # Replay protection
        if 'nonce' in request:
            if not self._check_nonce(request['nonce']):
                self._record_event(SecurityEvent(
                    event_id=f"replay_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    event_type="replay_attack",
                    threat_type=ThreatType.REPLAY_ATTACK,
                    severity="high",
                    source_ip=source_ip,
                    user_id=user_id,
                    details=request,
                    blocked=True
                ))
                self.stats['attacks_blocked'] += 1
                return False, "Replay attack detected"
        
        # Anomaly detection
        anomaly_score = self._calculate_anomaly_score(request)
        if anomaly_score > self.layers[SecurityLayer.ANOMALY_DETECTION]['auto_block_threshold']:
            self._record_event(SecurityEvent(
                event_id=f"anomaly_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                event_type="anomaly_detected",
                threat_type=None,
                severity="high",
                source_ip=source_ip,
                user_id=user_id,
                details={'anomaly_score': anomaly_score},
                blocked=True
            ))
            self.stats['attacks_blocked'] += 1
            return False, "Anomalous behavior detected"
        
        return True, "Request validated"
    
    def _check_rate_limit(self, ip: str, user_id: Optional[str]) -> bool:
        """Check rate limits"""
        if not self.layers[SecurityLayer.RATE_LIMITING]['enabled']:
            return True
        
        now = datetime.now()
        config = self.layers[SecurityLayer.RATE_LIMITING]
        
        # Clean old entries
        cutoff = now - timedelta(hours=1)
        
        # Check IP rate limit
        if config['by_ip']:
            key = f"ip:{ip}"
            self.rate_limits[key] = [t for t in self.rate_limits[key] if t > cutoff]
            
            # Check per-minute limit
            minute_ago = now - timedelta(minutes=1)
            recent = [t for t in self.rate_limits[key] if t > minute_ago]
            if len(recent) >= config['requests_per_minute']:
                return False
            
            # Check per-hour limit
            if len(self.rate_limits[key]) >= config['requests_per_hour']:
                return False
            
            self.rate_limits[key].append(now)
        
        # Check user rate limit
        if config['by_user'] and user_id:
            key = f"user:{user_id}"
            self.rate_limits[key] = [t for t in self.rate_limits[key] if t > cutoff]
            
            minute_ago = now - timedelta(minutes=1)
            recent = [t for t in self.rate_limits[key] if t > minute_ago]
            if len(recent) >= config['requests_per_minute'] * 2:  # Users get higher limit
                return False
            
            self.rate_limits[key].append(now)
        
        return True
    
    def _validate_input(self, data: Any) -> Tuple[bool, str]:
        """Validate input for security threats"""
        if not self.layers[SecurityLayer.INPUT_VALIDATION]['enabled']:
            return True, "Validation disabled"
        
        config = self.layers[SecurityLayer.INPUT_VALIDATION]
        
        # Convert to string for analysis
        data_str = str(data)
        
        # Check length
        if len(data_str) > config['max_input_length']:
            return False, "Input too long"
        
        # SQL injection detection
        if config['block_sql_injection']:
            sql_patterns = [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
                r"(--|;|'|\"|\bOR\b|\bAND\b).*=",
                r"(\bEXEC\b|\bEXECUTE\b)",
                r"(xp_|sp_)"
            ]
            for pattern in sql_patterns:
                if re.search(pattern, data_str, re.IGNORECASE):
                    return False, "SQL injection attempt detected"
        
        # XSS detection
        if config['block_xss']:
            xss_patterns = [
                r"<script[^>]*>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe",
                r"<object",
                r"<embed"
            ]
            for pattern in xss_patterns:
                if re.search(pattern, data_str, re.IGNORECASE):
                    return False, "XSS attempt detected"
        
        return True, "Input valid"
    
    def _check_nonce(self, nonce: str) -> bool:
        """Check nonce for replay protection"""
        if not self.layers[SecurityLayer.API_SECURITY]['replay_protection']:
            return True
        
        with self._nonce_cleanup_lock:
            # Clean expired nonces
            expiry = self.layers[SecurityLayer.API_SECURITY]['nonce_expiry']
            cutoff = datetime.now() - timedelta(seconds=expiry)
            self.used_nonces = {
                n: t for n, t in self.used_nonces.items() if t > cutoff
            }
            
            # Check if nonce was used
            if nonce in self.used_nonces:
                return False
            
            # Record nonce
            self.used_nonces[nonce] = datetime.now()
            return True
    
    def _calculate_anomaly_score(self, request: Dict[str, Any]) -> float:
        """Calculate anomaly score for a request"""
        if not self.layers[SecurityLayer.ANOMALY_DETECTION]['enabled']:
            return 0
        
        score = 0
        factors = []
        
        user_id = request.get('user_id', 'anonymous')
        
        # Get or create baseline
        if user_id not in self.baselines:
            self.baselines[user_id] = {
                'request_times': [],
                'request_types': defaultdict(int),
                'avg_request_size': 0,
                'typical_ips': set()
            }
        
        baseline = self.baselines[user_id]
        
        # Check time anomaly
        now = datetime.now()
        if baseline['request_times']:
            avg_hour = sum(t.hour for t in baseline['request_times'][-100:]) / len(baseline['request_times'][-100:])
            if abs(now.hour - avg_hour) > 6:
                score += 0.2
                factors.append("unusual_time")
        
        # Check IP anomaly
        ip = request.get('ip')
        if ip and baseline['typical_ips'] and ip not in baseline['typical_ips']:
            score += 0.3
            factors.append("new_ip")
        
        # Check request type anomaly
        req_type = request.get('type', 'unknown')
        if baseline['request_types']:
            total_requests = sum(baseline['request_types'].values())
            type_frequency = baseline['request_types'].get(req_type, 0) / max(total_requests, 1)
            if type_frequency < 0.01:  # Rare request type
                score += 0.2
                factors.append("rare_request_type")
        
        # Check request size anomaly
        req_size = len(str(request.get('data', '')))
        if baseline['avg_request_size'] > 0:
            size_ratio = req_size / baseline['avg_request_size']
            if size_ratio > 10:
                score += 0.3
                factors.append("large_request")
        
        # Update baseline
        baseline['request_times'].append(now)
        baseline['request_times'] = baseline['request_times'][-1000:]
        baseline['request_types'][req_type] += 1
        if ip:
            baseline['typical_ips'].add(ip)
        baseline['avg_request_size'] = (baseline['avg_request_size'] * 0.99 + req_size * 0.01)
        
        return min(score, 1.0)
    
    def _record_event(self, event: SecurityEvent):
        """Record a security event"""
        self.events.append(event)
        self.stats['threats_detected'] += 1
        
        # Trim history
        if len(self.events) > 10000:
            self.events = self.events[-5000:]
        
        # Auto-block on repeated attacks
        if event.blocked and event.source_ip:
            recent_attacks = [
                e for e in self.events[-100:]
                if e.source_ip == event.source_ip and e.blocked
            ]
            if len(recent_attacks) >= 10:
                self.blocked_ips.add(event.source_ip)
                logger.warning(f"Auto-blocked IP: {event.source_ip}")
    
    def record_auth_result(self, user_id: str, success: bool, ip: str):
        """Record authentication result"""
        if success:
            self.stats['successful_authentications'] += 1
        else:
            self.stats['failed_authentications'] += 1
            
            # Check for brute force
            recent_failures = [
                e for e in self.events[-100:]
                if e.event_type == 'auth_failure' and 
                (e.source_ip == ip or e.user_id == user_id) and
                e.timestamp > datetime.now() - timedelta(minutes=5)
            ]
            
            if len(recent_failures) >= self.layers[SecurityLayer.AUTHENTICATION]['max_attempts']:
                self._record_event(SecurityEvent(
                    event_id=f"brute_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    event_type="brute_force",
                    threat_type=ThreatType.BRUTE_FORCE,
                    severity="high",
                    source_ip=ip,
                    user_id=user_id,
                    details={'attempts': len(recent_failures)},
                    blocked=True
                ))
                self.blocked_ips.add(ip)
                self.stats['attacks_blocked'] += 1
            else:
                self._record_event(SecurityEvent(
                    event_id=f"auth_fail_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    event_type="auth_failure",
                    threat_type=None,
                    severity="low",
                    source_ip=ip,
                    user_id=user_id,
                    details={},
                    blocked=False
                ))
    
    def mark_false_positive(self, event_id: str):
        """Mark an event as false positive for learning"""
        for event in self.events:
            if event.event_id == event_id:
                event.false_positive = True
                self.stats['false_positives'] += 1
                
                # Update rule effectiveness
                for rule in self.rules:
                    if rule.layer.value in event.event_type:
                        rule.false_positives += 1
                        rule.effectiveness = max(0.1, rule.effectiveness * 0.95)
                break
    
    async def evolve(self) -> List[Dict[str, Any]]:
        """Run security evolution cycle"""
        logger.info("Starting security evolution cycle...")
        evolutions = []
        
        # Analyze recent events
        recent_events = [e for e in self.events if e.timestamp > datetime.now() - timedelta(days=7)]
        
        # Evolve rules based on effectiveness
        for rule in self.rules:
            if rule.hits > 10:
                fp_rate = rule.false_positives / rule.hits
                
                # High false positive rate -> relax rule
                if fp_rate > 0.3:
                    old_effectiveness = rule.effectiveness
                    rule.effectiveness *= 0.9
                    evolutions.append({
                        'type': 'rule_relaxed',
                        'rule_id': rule.rule_id,
                        'reason': f'High false positive rate: {fp_rate:.2%}',
                        'old_effectiveness': old_effectiveness,
                        'new_effectiveness': rule.effectiveness
                    })
                
                # Very low false positive rate -> can tighten
                elif fp_rate < 0.05 and rule.effectiveness < 1.0:
                    old_effectiveness = rule.effectiveness
                    rule.effectiveness = min(1.0, rule.effectiveness * 1.05)
                    evolutions.append({
                        'type': 'rule_tightened',
                        'rule_id': rule.rule_id,
                        'reason': f'Low false positive rate: {fp_rate:.2%}',
                        'old_effectiveness': old_effectiveness,
                        'new_effectiveness': rule.effectiveness
                    })
        
        # Evolve layer configurations
        layer_evolutions = await self._evolve_layers(recent_events)
        evolutions.extend(layer_evolutions)
        
        # Update threat intelligence
        await self._update_threat_intel(recent_events)
        
        self.stats['rules_evolved'] += len(evolutions)
        self._save_state()
        
        logger.info(f"Security evolution complete: {len(evolutions)} changes")
        return evolutions
    
    async def _evolve_layers(self, events: List[SecurityEvent]) -> List[Dict]:
        """Evolve security layer configurations"""
        evolutions = []
        
        # Analyze attack patterns
        attack_types = defaultdict(int)
        for event in events:
            if event.threat_type:
                attack_types[event.threat_type] += 1
        
        # Brute force attacks -> tighten auth
        if attack_types[ThreatType.BRUTE_FORCE] > 10:
            config = self.layers[SecurityLayer.AUTHENTICATION]
            if config['max_attempts'] > 3:
                old_value = config['max_attempts']
                config['max_attempts'] -= 1
                evolutions.append({
                    'type': 'layer_config',
                    'layer': 'authentication',
                    'param': 'max_attempts',
                    'old': old_value,
                    'new': config['max_attempts'],
                    'reason': 'High brute force attacks'
                })
        
        # DOS attacks -> tighten rate limiting
        if attack_types[ThreatType.DOS] > 20:
            config = self.layers[SecurityLayer.RATE_LIMITING]
            if config['requests_per_minute'] > 30:
                old_value = config['requests_per_minute']
                config['requests_per_minute'] = int(config['requests_per_minute'] * 0.9)
                evolutions.append({
                    'type': 'layer_config',
                    'layer': 'rate_limiting',
                    'param': 'requests_per_minute',
                    'old': old_value,
                    'new': config['requests_per_minute'],
                    'reason': 'High DOS attacks'
                })
        
        # Injection attacks -> tighten input validation
        if attack_types[ThreatType.INJECTION] > 5:
            config = self.layers[SecurityLayer.INPUT_VALIDATION]
            if config['max_input_length'] > 5000:
                old_value = config['max_input_length']
                config['max_input_length'] = int(config['max_input_length'] * 0.9)
                evolutions.append({
                    'type': 'layer_config',
                    'layer': 'input_validation',
                    'param': 'max_input_length',
                    'old': old_value,
                    'new': config['max_input_length'],
                    'reason': 'Injection attacks detected'
                })
        
        # Low attack rate -> can relax slightly for usability
        total_attacks = sum(attack_types.values())
        if total_attacks < 5 and len(events) > 100:
            config = self.layers[SecurityLayer.RATE_LIMITING]
            if config['requests_per_minute'] < 100:
                old_value = config['requests_per_minute']
                config['requests_per_minute'] = int(config['requests_per_minute'] * 1.05)
                evolutions.append({
                    'type': 'layer_config',
                    'layer': 'rate_limiting',
                    'param': 'requests_per_minute',
                    'old': old_value,
                    'new': config['requests_per_minute'],
                    'reason': 'Low attack rate, improving usability'
                })
        
        return evolutions
    
    async def _update_threat_intel(self, events: List[SecurityEvent]):
        """Update threat intelligence from events"""
        # Extract indicators from events
        malicious_ips = set()
        attack_patterns = defaultdict(list)
        
        for event in events:
            if event.blocked and not event.false_positive:
                if event.source_ip:
                    malicious_ips.add(event.source_ip)
                if event.threat_type:
                    attack_patterns[event.threat_type].append(event.details)
        
        # Update blocked IPs
        self.blocked_ips.update(malicious_ips)
        
        # Create threat intel entries
        for threat_type, patterns in attack_patterns.items():
            if len(patterns) >= 3:
                self.threat_intel.append(ThreatIntelligence(
                    threat_type=threat_type,
                    indicators=[str(p)[:100] for p in patterns[:10]],
                    severity='high' if len(patterns) > 10 else 'medium',
                    confidence=min(len(patterns) / 20, 1.0),
                    source='internal',
                    last_updated=datetime.now()
                ))
    
    def generate_nonce(self) -> str:
        """Generate a secure nonce"""
        return secrets.token_hex(32)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash a password securely"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA-256
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        )
        return key.hex(), salt
    
    def verify_password(self, password: str, hash: str, salt: str) -> bool:
        """Verify a password"""
        computed_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, hash)
    
    def sign_data(self, data: str, key: str) -> str:
        """Sign data with HMAC"""
        return hmac.new(
            key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, data: str, signature: str, key: str) -> bool:
        """Verify data signature"""
        expected = self.sign_data(data, key)
        return hmac.compare_digest(expected, signature)
    
    def _save_state(self):
        """Save evolution state"""
        state = {
            'layers': {k.value: v for k, v in self.layers.items()},
            'rules': [
                {
                    'rule_id': r.rule_id,
                    'layer': r.layer.value,
                    'condition': r.condition,
                    'action': r.action,
                    'enabled': r.enabled,
                    'hits': r.hits,
                    'false_positives': r.false_positives,
                    'effectiveness': r.effectiveness
                }
                for r in self.rules
            ],
            'blocked_ips': list(self.blocked_ips),
            'blocked_users': list(self.blocked_users),
            'stats': self.stats
        }
        
        state_file = self.state_path / 'security_evolution_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """Load previous state"""
        state_file = self.state_path / 'security_evolution_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                for k, v in state.get('layers', {}).items():
                    layer = SecurityLayer(k)
                    self.layers[layer] = v
                
                self.blocked_ips = set(state.get('blocked_ips', []))
                self.blocked_users = set(state.get('blocked_users', []))
                self.stats = state.get('stats', self.stats)
                
                # Restore rules
                for rule_data in state.get('rules', []):
                    for rule in self.rules:
                        if rule.rule_id == rule_data['rule_id']:
                            rule.hits = rule_data.get('hits', 0)
                            rule.false_positives = rule_data.get('false_positives', 0)
                            rule.effectiveness = rule_data.get('effectiveness', 1.0)
                            break
                
                logger.info("Loaded previous security evolution state")
                
            except Exception as e:
                logger.error(f"Failed to load security evolution state: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evolution statistics"""
        return {
            **self.stats,
            'blocked_ips_count': len(self.blocked_ips),
            'blocked_users_count': len(self.blocked_users),
            'active_rules': sum(1 for r in self.rules if r.enabled),
            'threat_intel_entries': len(self.threat_intel),
            'recent_events': len([e for e in self.events if e.timestamp > datetime.now() - timedelta(hours=24)]),
            'layers_enabled': sum(1 for l in self.layers.values() if l.get('enabled'))
        }
