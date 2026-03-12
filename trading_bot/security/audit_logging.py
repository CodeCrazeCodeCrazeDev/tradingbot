"""
Audit Logging and Security System

Production-ready security infrastructure:
- Comprehensive audit logging
- Role-Based Access Control (RBAC)
- Multi-user support
- Session management
- API key management
- Security event monitoring
"""

import asyncio
import logging
import json
import hashlib
import secrets
import uuid
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import os

logger = logging.getLogger(__name__)

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("PyJWT not installed. Install with: pip install PyJWT")

try:
    from passlib.hash import bcrypt
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    logger.warning("passlib not installed. Install with: pip install passlib")


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    
    # Authorization
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGE = "permission_change"
    
    # Trading
    ORDER_PLACED = "order_placed"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_MODIFIED = "order_modified"
    POSITION_CLOSED = "position_closed"
    
    # Configuration
    CONFIG_CHANGE = "config_change"
    FEATURE_FLAG_CHANGE = "feature_flag_change"
    
    # System
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    ERROR = "error"
    SECURITY_ALERT = "security_alert"
    
    # Data
    DATA_EXPORT = "data_export"
    DATA_ACCESS = "data_access"


class Permission(Enum):
    """System permissions"""
    # Trading
    TRADE_VIEW = "trade:view"
    TRADE_EXECUTE = "trade:execute"
    TRADE_CANCEL = "trade:cancel"
    
    # Positions
    POSITION_VIEW = "position:view"
    POSITION_CLOSE = "position:close"
    
    # Account
    ACCOUNT_VIEW = "account:view"
    ACCOUNT_MANAGE = "account:manage"
    
    # Configuration
    CONFIG_VIEW = "config:view"
    CONFIG_MODIFY = "config:modify"
    
    # Users
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_MODIFY = "user:modify"
    USER_DELETE = "user:delete"
    
    # System
    SYSTEM_ADMIN = "system:admin"
    AUDIT_VIEW = "audit:view"
    METRICS_VIEW = "metrics:view"


class Role(Enum):
    """User roles"""
    VIEWER = "viewer"
    TRADER = "trader"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.TRADE_VIEW,
        Permission.POSITION_VIEW,
        Permission.ACCOUNT_VIEW,
        Permission.METRICS_VIEW
    },
    Role.TRADER: {
        Permission.TRADE_VIEW,
        Permission.TRADE_EXECUTE,
        Permission.TRADE_CANCEL,
        Permission.POSITION_VIEW,
        Permission.POSITION_CLOSE,
        Permission.ACCOUNT_VIEW,
        Permission.METRICS_VIEW
    },
    Role.MANAGER: {
        Permission.TRADE_VIEW,
        Permission.TRADE_EXECUTE,
        Permission.TRADE_CANCEL,
        Permission.POSITION_VIEW,
        Permission.POSITION_CLOSE,
        Permission.ACCOUNT_VIEW,
        Permission.ACCOUNT_MANAGE,
        Permission.CONFIG_VIEW,
        Permission.USER_VIEW,
        Permission.AUDIT_VIEW,
        Permission.METRICS_VIEW
    },
    Role.ADMIN: {
        Permission.TRADE_VIEW,
        Permission.TRADE_EXECUTE,
        Permission.TRADE_CANCEL,
        Permission.POSITION_VIEW,
        Permission.POSITION_CLOSE,
        Permission.ACCOUNT_VIEW,
        Permission.ACCOUNT_MANAGE,
        Permission.CONFIG_VIEW,
        Permission.CONFIG_MODIFY,
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.USER_MODIFY,
        Permission.AUDIT_VIEW,
        Permission.METRICS_VIEW
    },
    Role.SUPER_ADMIN: set(Permission)  # All permissions
}


@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    ip_address: Optional[str]
    resource: Optional[str]
    action: str
    status: str  # success, failure
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'resource': self.resource,
            'action': self.action,
            'status': self.status,
            'details': self.details
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class User:
    """User account"""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: Role
    permissions: Set[Permission] = field(default_factory=set)
    api_keys: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'permissions': [p.value for p in self.permissions],
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'mfa_enabled': self.mfa_enabled
        }


@dataclass
class Session:
    """User session"""
    session_id: str
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True


class AuditLogger:
    """
    Comprehensive audit logging system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Storage
        self.events: List[AuditEvent] = []
        self.max_events = self.config.get('max_events', 100000)
        
        # File logging
        self.log_file = self.config.get('log_file', 'audit.log')
        self.enable_file_logging = self.config.get('enable_file_logging', True)
        
        # Callbacks
        self.on_security_event: Optional[callable] = None
        
        logger.info("AuditLogger initialized")
    
    def log(
        self,
        event_type: AuditEventType,
        action: str,
        status: str = "success",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource: Optional[str] = None,
        **details
    ) -> AuditEvent:
        """Log an audit event"""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            status=status,
            details=details
        )
        
        # Store in memory
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        # Write to file
        if self.enable_file_logging:
            self._write_to_file(event)
        
        # Security event callback
        if event_type in [AuditEventType.LOGIN_FAILURE, AuditEventType.ACCESS_DENIED,
                          AuditEventType.SECURITY_ALERT] and self.on_security_event:
            try:
                self.on_security_event(event)
            except Exception as e:
                logger.error(f"Security event callback error: {e}")
        
        return event
    
    def _write_to_file(self, event: AuditEvent):
        """Write event to log file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(event.to_json() + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def get_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Query audit events"""
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        return events[-limit:]
    
    def get_security_events(self, hours: int = 24) -> List[AuditEvent]:
        """Get recent security-related events"""
        cutoff = datetime.now() - timedelta(hours=hours)
        security_types = [
            AuditEventType.LOGIN_FAILURE,
            AuditEventType.ACCESS_DENIED,
            AuditEventType.SECURITY_ALERT,
            AuditEventType.PERMISSION_CHANGE
        ]
        
        return [
            e for e in self.events
            if e.event_type in security_types and e.timestamp >= cutoff
        ]


class UserManager:
    """
    User management with RBAC.
    """
    
    def __init__(self, audit_logger: AuditLogger, config: Optional[Dict[str, Any]] = None):
        self.audit = audit_logger
        self.config = config or {}
        
        # User storage
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, str] = {}  # api_key -> user_id
        
        # Session storage
        self.sessions: Dict[str, Session] = {}
        
        # JWT settings
        self.jwt_secret = self.config.get('jwt_secret', os.getenv('JWT_SECRET', secrets.token_hex(32)))
        self.token_expiry_hours = self.config.get('token_expiry_hours', 24)
        
        # Security settings
        self.max_login_attempts = self.config.get('max_login_attempts', 5)
        self.lockout_duration_minutes = self.config.get('lockout_duration_minutes', 30)
        self.login_attempts: Dict[str, List[datetime]] = {}
        
        logger.info("UserManager initialized")
    
    def _hash_password(self, password: str) -> str:
        """Hash password"""
        if PASSLIB_AVAILABLE:
            return bcrypt.hash(password)
        else:
            # Fallback to SHA256 (less secure)
            return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password"""
        if PASSLIB_AVAILABLE:
            return bcrypt.verify(password, password_hash)
        else:
            return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: Role = Role.VIEWER,
        created_by: Optional[str] = None
    ) -> User:
        """Create a new user"""
        # Check if username exists
        for user in self.users.values():
            if user.username == username:
                raise ValueError(f"Username {username} already exists")
        
        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=self._hash_password(password),
            role=role,
            permissions=ROLE_PERMISSIONS.get(role, set()).copy()
        )
        
        self.users[user.user_id] = user
        
        self.audit.log(
            AuditEventType.PERMISSION_CHANGE,
            action="user_created",
            user_id=created_by,
            resource=f"user:{user.user_id}",
            new_user=username,
            role=role.value
        )
        
        logger.info(f"User created: {username} ({role.value})")
        return user
    
    def authenticate(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> Optional[str]:
        """Authenticate user and return JWT token"""
        # Check lockout
        if self._is_locked_out(username):
            self.audit.log(
                AuditEventType.LOGIN_FAILURE,
                action="login_locked_out",
                ip_address=ip_address,
                username=username
            )
            return None
        
        # Find user
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user or not user.is_active:
            self._record_login_attempt(username)
            self.audit.log(
                AuditEventType.LOGIN_FAILURE,
                action="login_user_not_found",
                ip_address=ip_address,
                username=username
            )
            return None
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            self._record_login_attempt(username)
            self.audit.log(
                AuditEventType.LOGIN_FAILURE,
                action="login_invalid_password",
                user_id=user.user_id,
                ip_address=ip_address
            )
            return None
        
        # Clear login attempts
        self.login_attempts.pop(username, None)
        
        # Create session
        token = self._create_token(user)
        session = Session(
            session_id=str(uuid.uuid4()),
            user_id=user.user_id,
            token=token,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self.token_expiry_hours),
            ip_address=ip_address
        )
        self.sessions[session.session_id] = session
        
        # Update last login
        user.last_login = datetime.now()
        
        self.audit.log(
            AuditEventType.LOGIN_SUCCESS,
            action="login",
            user_id=user.user_id,
            ip_address=ip_address
        )
        
        return token
    
    def _create_token(self, user: User) -> str:
        """Create JWT token"""
        if not JWT_AVAILABLE:
            return secrets.token_hex(32)
        
        payload = {
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role.value,
            'permissions': [p.value for p in user.permissions],
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        if not JWT_AVAILABLE:
            try:
                # Check if token exists in sessions
                for session in self.sessions.values():
                    if session.token == token and session.is_active:
                        if session.expires_at > datetime.now():
                            user = self.users.get(session.user_id)
                            if user:
                                return {
                                    'user_id': user.user_id,
                                    'username': user.username,
                                    'role': user.role.value,
                                    'permissions': [p.value for p in user.permissions]
                                }
                return None

                payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
                return payload
            except jwt.ExpiredSignatureError:
                return None
            except jwt.InvalidTokenError:
                return None

    def _is_locked_out(self, username: str) -> bool:
        """Check if user is locked out"""
        attempts = self.login_attempts.get(username, [])
        cutoff = datetime.now() - timedelta(minutes=self.lockout_duration_minutes)
        recent_attempts = [a for a in attempts if a > cutoff]
        return len(recent_attempts) >= self.max_login_attempts
    
    def _record_login_attempt(self, username: str):
        """Record failed login attempt"""
        if username not in self.login_attempts:
            self.login_attempts[username] = []
        self.login_attempts[username].append(datetime.now())
    
    def create_api_key(self, user_id: str, created_by: Optional[str] = None) -> str:
        """Create API key for user"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        api_key = f"ak_{secrets.token_hex(32)}"
        self.api_keys[api_key] = user_id
        user.api_keys.append(api_key)
        
        self.audit.log(
            AuditEventType.PERMISSION_CHANGE,
            action="api_key_created",
            user_id=created_by,
            resource=f"user:{user_id}"
        )
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[User]:
        """Verify API key and return user"""
        user_id = self.api_keys.get(api_key)
        if user_id:
            user = self.users.get(user_id)
            if user and user.is_active:
                return user
        return None
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has permission"""
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False
        
        return permission in user.permissions
    
    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Check permission and log access"""
        has_perm = self.has_permission(user_id, permission)
        
        event_type = AuditEventType.ACCESS_GRANTED if has_perm else AuditEventType.ACCESS_DENIED
        
        self.audit.log(
            event_type,
            action=f"check_permission:{permission.value}",
            user_id=user_id,
            resource=resource,
            ip_address=ip_address
        )
        
        return has_perm
    
    def update_user_role(
        self,
        user_id: str,
        new_role: Role,
        updated_by: str
    ):
        """Update user role"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        old_role = user.role
        user.role = new_role
        user.permissions = ROLE_PERMISSIONS.get(new_role, set()).copy()
        
        self.audit.log(
            AuditEventType.PERMISSION_CHANGE,
            action="role_changed",
            user_id=updated_by,
            resource=f"user:{user_id}",
            old_role=old_role.value,
            new_role=new_role.value
        )
    
    def logout(self, token: str, ip_address: Optional[str] = None):
        """Logout user"""
        # Find and invalidate session
        for session_id, session in list(self.sessions.items()):
            if session.token == token:
                session.is_active = False
                
                self.audit.log(
                    AuditEventType.LOGOUT,
                    action="logout",
                    user_id=session.user_id,
                    ip_address=ip_address
                )
                break
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_users(self) -> List[User]:
        """Get all users"""
        return list(self.users.values())


class SecurityMonitor:
    """
    Security event monitoring and alerting.
    """
    
    def __init__(self, audit_logger: AuditLogger, config: Optional[Dict[str, Any]] = None):
        self.audit = audit_logger
        self.config = config or {}
        
        # Thresholds
        self.failed_login_threshold = self.config.get('failed_login_threshold', 5)
        self.access_denied_threshold = self.config.get('access_denied_threshold', 10)
        self.alert_window_minutes = self.config.get('alert_window_minutes', 15)
        
        # Callbacks
        self.on_security_alert: Optional[callable] = None
        
        # Set up audit callback
        self.audit.on_security_event = self._handle_security_event
        
        logger.info("SecurityMonitor initialized")
    
    def _handle_security_event(self, event: AuditEvent):
        """Handle security event"""
        # Check for patterns
        if event.event_type == AuditEventType.LOGIN_FAILURE:
            self._check_brute_force(event)
        elif event.event_type == AuditEventType.ACCESS_DENIED:
            self._check_privilege_escalation(event)
    
    def _check_brute_force(self, event: AuditEvent):
        """Check for brute force attacks"""
        cutoff = datetime.now() - timedelta(minutes=self.alert_window_minutes)
        
        # Count recent failed logins from same IP
        if event.ip_address:
            failed_logins = [
                e for e in self.audit.events
                if e.event_type == AuditEventType.LOGIN_FAILURE
                and e.ip_address == event.ip_address
                and e.timestamp >= cutoff
            ]
            
            if len(failed_logins) >= self.failed_login_threshold:
                self._raise_alert(
                    "Possible brute force attack",
                    f"Multiple failed login attempts from IP {event.ip_address}",
                    event
                )
    
    def _check_privilege_escalation(self, event: AuditEvent):
        """Check for privilege escalation attempts"""
        cutoff = datetime.now() - timedelta(minutes=self.alert_window_minutes)
        
        if event.user_id:
            denied_access = [
                e for e in self.audit.events
                if e.event_type == AuditEventType.ACCESS_DENIED
                and e.user_id == event.user_id
                and e.timestamp >= cutoff
            ]
            
            if len(denied_access) >= self.access_denied_threshold:
                self._raise_alert(
                    "Possible privilege escalation attempt",
                    f"Multiple access denied events for user {event.user_id}",
                    event
                )
    
    def _raise_alert(self, title: str, message: str, trigger_event: AuditEvent):
        """Raise security alert"""
        alert_event = self.audit.log(
            AuditEventType.SECURITY_ALERT,
            action="security_alert",
            user_id=trigger_event.user_id,
            ip_address=trigger_event.ip_address,
            title=title,
            message=message,
            trigger_event_id=trigger_event.event_id
        )
        
        logger.warning(f"SECURITY ALERT: {title} - {message}")
        
        if self.on_security_alert:
            try:
                self.on_security_alert(alert_event)
            except Exception as e:
                logger.error(f"Security alert callback error: {e}")


def require_permission(permission: Permission):
    """Decorator to require permission for function"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user_id from kwargs or first arg
            user_id = kwargs.get('user_id')
            if not user_id and args:
                user_id = getattr(args[0], 'current_user_id', None)
            
            if not user_id:
                raise PermissionError("User not authenticated")
            
            # Get user manager from kwargs or first arg
            user_manager = kwargs.get('user_manager')
            if not user_manager and args:
                user_manager = getattr(args[0], 'user_manager', None)
            
            if not user_manager:
                raise RuntimeError("UserManager not available")
            
            if not user_manager.has_permission(user_id, permission):
                raise PermissionError(f"Permission denied: {permission.value}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Export
__all__ = [
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'UserManager',
    'User',
    'Session',
    'Permission',
    'Role',
    'ROLE_PERMISSIONS',
    'SecurityMonitor',
    'require_permission'
]
