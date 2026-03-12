"""
Elite Trading Bot - Authentication Manager

This module provides secure management of API keys and authentication credentials
for various financial data providers and trading platforms.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Secure manager for API keys and authentication credentials.
    
    Features:
    - Secure storage of API keys and credentials
    - Encryption of sensitive data
    - Dynamic authentication header generation
    - Support for various authentication methods (API key, OAuth, HMAC)
    - Credential rotation and expiration handling
    """
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 master_password: Optional[str] = None,
                 env_prefix: str = "ETB_"):
        """
        Initialize the authentication manager.
        
        Args:
            config_path: Path to the credentials configuration file
            master_password: Master password for encryption (if None, will look for env var)
            env_prefix: Prefix for environment variables
        """
        self.config_path = config_path or os.path.expanduser("~/.elite_trading_bot/credentials.json")
        self.env_prefix = env_prefix
        
        # Get master password from environment if not provided
        if master_password is None:
            master_password = os.environ.get(f"{env_prefix}MASTER_PASSWORD")
        
        # Initialize encryption key
        self.encryption_key = self._derive_key(master_password or "default_password")
        
        # Initialize credentials storage
        self.credentials: Dict[str, Dict[str, Any]] = {}
        
        # Load credentials if config file exists
        config_file = Path(self.config_path)
        if config_file.exists():
            self._load_credentials()
        else:
            # Create directory if it doesn't exist
            config_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_credentials()
        
        logger.info("AuthManager initialized")
    
    def _derive_key(self, password: str) -> bytes:
        """
        Derive encryption key from password.
        
        Args:
            password: Master password
            
        Returns:
            Encryption key
        """
        # Use a static salt (in a real system, this should be stored securely)
        salt = b'elite_trading_bot_salt'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        f = Fernet(self.encryption_key)
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted data
        """
        f = Fernet(self.encryption_key)
        decoded_data = base64.urlsafe_b64decode(encrypted_data)
        return f.decrypt(decoded_data).decode()
    
    def _load_credentials(self):
        """Load credentials from config file."""
        try:
            with open(self.config_path, 'r') as f:
                encrypted_data = f.read()
                if encrypted_data:
                    decrypted_data = self._decrypt(encrypted_data)
                    self.credentials = json.loads(decrypted_data)
                    logger.info(f"Loaded credentials for {len(self.credentials)} services")
                else:
                    self.credentials = {}
        except Exception as e:
            logger.error(f"Failed to load credentials: {str(e)}")
            self.credentials = {}
    
    def _save_credentials(self):
        """Save credentials to config file."""
        try:
            encrypted_data = self._encrypt(json.dumps(self.credentials))
            with open(self.config_path, 'w') as f:
                f.write(encrypted_data)
            logger.info(f"Saved credentials for {len(self.credentials)} services")
        except Exception as e:
            logger.error(f"Failed to save credentials: {str(e)}")
    
    def add_api_key(self, service_name: str, api_key: str, api_secret: Optional[str] = None):
        """
        Add API key credentials for a service.
        
        Args:
            service_name: Name of the service
            api_key: API key
            api_secret: Optional API secret
        """
        self.credentials[service_name] = {
            "type": "api_key",
            "api_key": api_key,
            "api_secret": api_secret,
            "added_at": datetime.now().isoformat()
        }
        self._save_credentials()
        logger.info(f"Added API key for {service_name}")
    
    def add_oauth_credentials(self, 
                             service_name: str, 
                             client_id: str, 
                             client_secret: str,
                             access_token: Optional[str] = None,
                             refresh_token: Optional[str] = None,
                             token_expiry: Optional[str] = None):
        """
        Add OAuth credentials for a service.
        
        Args:
            service_name: Name of the service
            client_id: OAuth client ID
            client_secret: OAuth client secret
            access_token: Optional access token
            refresh_token: Optional refresh token
            token_expiry: Optional token expiry timestamp
        """
        self.credentials[service_name] = {
            "type": "oauth",
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiry": token_expiry,
            "added_at": datetime.now().isoformat()
        }
        self._save_credentials()
        logger.info(f"Added OAuth credentials for {service_name}")
    
    def remove_credentials(self, service_name: str):
        """
        Remove credentials for a service.
        
        Args:
            service_name: Name of the service
        """
        if service_name in self.credentials:
            del self.credentials[service_name]
            self._save_credentials()
            logger.info(f"Removed credentials for {service_name}")
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """
        Get API key for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            API key or None if not found
        """
        # First check environment variables
        env_var_name = f"{self.env_prefix}{service_name.upper()}_API_KEY"
        api_key = os.environ.get(env_var_name)
        
        if api_key:
            return api_key
        
        # Then check stored credentials
        if service_name in self.credentials and self.credentials[service_name]["type"] == "api_key":
            return self.credentials[service_name]["api_key"]
        
        return None
    
    def get_api_secret(self, service_name: str) -> Optional[str]:
        """
        Get API secret for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            API secret or None if not found
        """
        # First check environment variables
        env_var_name = f"{self.env_prefix}{service_name.upper()}_API_SECRET"
        api_secret = os.environ.get(env_var_name)
        
        if api_secret:
            return api_secret
        
        # Then check stored credentials
        if service_name in self.credentials and self.credentials[service_name]["type"] == "api_key":
            return self.credentials[service_name].get("api_secret")
        
        return None
    
    async def get_auth_headers(self, service_name: str) -> Dict[str, str]:
        """
        Get authentication headers for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary of authentication headers
        """
        if service_name not in self.credentials:
            logger.warning(f"No credentials found for {service_name}")
            return {}
        
        creds = self.credentials[service_name]
        
        if creds["type"] == "api_key":
            # Simple API key authentication
            if "header_name" in creds:
                # Custom header name
                return {creds["header_name"]: creds["api_key"]}
            else:
                # Default to X-API-Key
                return {"X-API-Key": creds["api_key"]}
                
        elif creds["type"] == "oauth":
            # OAuth authentication
            # Check if token is expired
            if creds.get("access_token") and creds.get("token_expiry"):
                expiry = datetime.fromisoformat(creds["token_expiry"])
                if datetime.now() < expiry:
                    return {"Authorization": f"Bearer {creds['access_token']}"}
            
            # Token expired or not available, try to refresh
            if creds.get("refresh_token"):
                # This would normally call the OAuth token endpoint
                # For now, just log a warning
                logger.warning(f"OAuth token for {service_name} needs refresh")
            
            return {}
        
        return {}
    
    def generate_signature(self, service_name: str, payload: str) -> Optional[str]:
        """
        Generate HMAC signature for API request.
        
        Args:
            service_name: Name of the service
            payload: Payload to sign
            
        Returns:
            HMAC signature or None if credentials not found
        """
        api_secret = self.get_api_secret(service_name)
        if not api_secret:
            return None
        
        signature = hmac.new(
            api_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def list_services(self) -> List[str]:
        """
        List all services with stored credentials.
        
        Returns:
            List of service names
        """
        return list(self.credentials.keys())
    
    def get_credential_info(self, service_name: str) -> Dict[str, Any]:
        """
        Get non-sensitive information about stored credentials.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary with credential information
        """
        if service_name not in self.credentials:
            return {}
        
        creds = self.credentials[service_name]
        
        # Return only non-sensitive information
        info = {
            "type": creds["type"],
            "added_at": creds["added_at"]
        }
        
        if creds["type"] == "api_key":
            # Mask API key
            api_key = creds["api_key"]
            if api_key and len(api_key) > 8:
                info["api_key_preview"] = f"{api_key[:4]}...{api_key[-4:]}"
            else:
                info["api_key_preview"] = "****"
            
            info["has_secret"] = "api_secret" in creds and creds["api_secret"] is not None
            
        elif creds["type"] == "oauth":
            info["has_access_token"] = "access_token" in creds and creds["access_token"] is not None
            info["has_refresh_token"] = "refresh_token" in creds and creds["refresh_token"] is not None
            
            if "token_expiry" in creds and creds["token_expiry"]:
                expiry = datetime.fromisoformat(creds["token_expiry"])
                info["token_expiry"] = creds["token_expiry"]
                info["token_expired"] = datetime.now() > expiry
        
        return info
