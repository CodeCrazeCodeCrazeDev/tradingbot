"""
JWT authentication for API endpoints
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import secrets

# Set up logger
logger = logging.getLogger(__name__)

security = HTTPBearer()


class JWTAuthenticator:
    """
    JWT-based authentication system.
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        # User database (in production, use real database)
        self.users: Dict[str, Dict] = {}
        
        # Revoked tokens
        self.revoked_tokens = set()
        
        logger.info("✅ JWT Authenticator initialized")
    
    def create_user(
        self,
        username: str,
        password: str,
        roles: list = None
    ) -> Dict:
        """
        Create new user.
        
        Args:
            username: Username
            password: Password
            roles: List of roles
        
        Returns:
            User dictionary
        """
        if username in self.users:
            raise ValueError(f"User {username} already exists")
        
        # Hash password
        password_hash = self._hash_password(password)
        
        user = {
            'username': username,
            'password_hash': password_hash,
            'roles': roles or ['user'],
            'created_at': datetime.now(),
            'active': True
        }
        
        self.users[username] = user
        
        logger.info(f"✅ Created user: {username}")
        
        return {
            'username': username,
            'roles': user['roles'],
            'created_at': user['created_at']
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password."""
        if username not in self.users:
            return False
        
        user = self.users[username]
        password_hash = self._hash_password(password)
        
        return user['password_hash'] == password_hash and user['active']
    
    def create_access_token(
        self,
        username: str,
        additional_claims: Dict = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            username: Username
            additional_claims: Additional claims to include
        
        Returns:
            JWT token string
        """
        if username not in self.users:
            raise ValueError(f"User {username} not found")
        
        user = self.users[username]
        
        # Token expiration
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Claims
        claims = {
            'sub': username,
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'access',
            'roles': user['roles']
        }
        
        if additional_claims:
            claims.update(additional_claims)
        
        # Encode token
        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        
        return token
    
    def create_refresh_token(self, username: str) -> str:
        """
        Create JWT refresh token.
        
        Args:
            username: Username
        
        Returns:
            JWT refresh token string
        """
        if username not in self.users:
            raise ValueError(f"User {username} not found")
        
        # Token expiration
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        # Claims
        claims = {
            'sub': username,
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'refresh',
            'jti': secrets.token_urlsafe(32)  # Unique token ID
        }
        
        # Encode token
        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        
        return token
    
    def verify_token(self, token: str) -> Dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token claims
        
        Raises:
            HTTPException if token is invalid
        """
        try:
            # Check if token is revoked
            if token in self.revoked_tokens:
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check if user exists and is active
            username = payload.get('sub')
            if username not in self.users or not self.users[username]['active']:
                raise HTTPException(status_code=401, detail="User not found or inactive")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Create new access token from refresh token.
        
        Args:
            refresh_token: Refresh token string
        
        Returns:
            New access token
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token)
        
        # Check token type
        if payload.get('type') != 'refresh':
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Create new access token
        username = payload.get('sub')
        access_token = self.create_access_token(username)
        
        return access_token
    
    def revoke_token(self, token: str):
        """Revoke a token."""
        self.revoked_tokens.add(token)
        logger.info(f"🚫 Token revoked")
    
    def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> Dict:
        """
        Get current user from token (for FastAPI dependency).
        
        Args:
            credentials: HTTP authorization credentials
        
        Returns:
            User information
        """
        token = credentials.credentials
        payload = self.verify_token(token)
        
        username = payload.get('sub')
        
        return {
            'username': username,
            'roles': payload.get('roles', []),
            'token_type': payload.get('type')
        }
    
    def require_role(self, required_role: str):
        """
        Decorator to require specific role.
        
        Args:
            required_role: Required role name
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Get current user from kwargs
                current_user = kwargs.get('current_user')
                
                if not current_user:
                    raise HTTPException(status_code=401, detail="Not authenticated")
                
                if required_role not in current_user.get('roles', []):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Role '{required_role}' required"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def login(self, username: str, password: str) -> Dict:
        """
        Login user and return tokens.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            Dictionary with access and refresh tokens
        """
        # Verify credentials
        if not self.verify_password(username, password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create tokens
        access_token = self.create_access_token(username)
        refresh_token = self.create_refresh_token(username)
        
        logger.info(f"✅ User logged in: {username}")
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': self.access_token_expire_minutes * 60
        }
    
    def logout(self, token: str):
        """Logout user by revoking token."""
        self.revoke_token(token)
        logger.info("✅ User logged out")


class APIKeyAuthenticator:
    """
    Simple API key authentication.
    """
    
    def __init__(self):
        self.api_keys: Dict[str, Dict] = {}
        logger.info("✅ API Key Authenticator initialized")
    
    def create_api_key(
        self,
        name: str,
        permissions: list = None
    ) -> str:
        """
        Create new API key.
        
        Args:
            name: Key name/description
            permissions: List of permissions
        
        Returns:
            API key string
        """
        # Generate secure random key
        api_key = secrets.token_urlsafe(32)
        
        self.api_keys[api_key] = {
            'name': name,
            'permissions': permissions or [],
            'created_at': datetime.now(),
            'active': True
        }
        
        logger.info(f"✅ Created API key: {name}")
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify API key."""
        return api_key in self.api_keys and self.api_keys[api_key]['active']
    
    def revoke_api_key(self, api_key: str):
        """Revoke API key."""
        if api_key in self.api_keys:
            self.api_keys[api_key]['active'] = False
            logger.info(f"🚫 API key revoked: {self.api_keys[api_key]['name']}")
    
    def get_api_key_info(self, api_key: str) -> Optional[Dict]:
        """Get API key information."""
        if api_key not in self.api_keys:
            return None
        
        key_info = self.api_keys[api_key].copy()
        return key_info
