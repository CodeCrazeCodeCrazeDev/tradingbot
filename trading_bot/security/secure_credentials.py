"""
Secure Credentials Manager
Handles API keys and secrets securely using environment variables and encryption.

This module replaces plain-text API key storage with secure alternatives.
"""

import os
import json
import base64
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


@dataclass
class CredentialConfig:
    """Configuration for credential storage"""
    use_env_vars: bool = True
    use_encrypted_file: bool = False
    encrypted_file_path: str = "config/credentials.enc"
    key_derivation_salt: bytes = b"alphaalgo_salt_v1"


class SecureCredentialsManager:
    """
    Secure credentials manager that:
    1. Prioritizes environment variables
    2. Falls back to encrypted file storage
    3. Never stores credentials in plain text
    4. Provides audit logging for credential access
    """
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        'fred_api_key': 'FRED_API_KEY',
        'newsapi_api_key': 'NEWSAPI_API_KEY',
        'alpha_vantage_api_key': 'ALPHA_VANTAGE_API_KEY',
        'mt5_login': 'MT5_LOGIN',
        'mt5_password': 'MT5_PASSWORD',
        'mt5_server': 'MT5_SERVER',
        'telegram_token': 'TELEGRAM_BOT_TOKEN',
        'telegram_chat_id': 'TELEGRAM_CHAT_ID',
        'binance_api_key': 'BINANCE_API_KEY',
        'binance_api_secret': 'BINANCE_API_SECRET',
        'alpaca_api_key': 'ALPACA_API_KEY',
        'alpaca_api_secret': 'ALPACA_API_SECRET',
        'openai_api_key': 'OPENAI_API_KEY',
    }
    
    def __init__(self, config: Optional[CredentialConfig] = None):
        self.config = config or CredentialConfig()
        self._cache: Dict[str, str] = {}
        self._fernet: Optional[Fernet] = None
        self._access_log: list = []
        
        logger.info("SecureCredentialsManager initialized")
    
    def get_credential(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a credential securely.
        
        Priority:
        1. Environment variable
        2. Encrypted file
        3. Default value
        
        Args:
            key: Credential key (e.g., 'fred_api_key')
            default: Default value if not found
            
        Returns:
            Credential value or default
        """
        # Log access attempt
        self._log_access(key)
        
        # Check cache first
        if key in self._cache:
            return self._cache[key]
        
        value = None
        
        # Try environment variable
        if self.config.use_env_vars:
            env_var = self.ENV_MAPPINGS.get(key, key.upper())
            value = os.environ.get(env_var)
            if value:
                logger.debug(f"Credential '{key}' loaded from environment")
        
        # Try encrypted file
        if value is None and self.config.use_encrypted_file:
            value = self._get_from_encrypted_file(key)
            if value:
                logger.debug(f"Credential '{key}' loaded from encrypted file")
        
        # Use default
        if value is None:
            value = default
            if default:
                logger.warning(f"Using default value for credential '{key}'")
        
        # Cache the value
        if value:
            self._cache[key] = value
        
        return value
    
    def set_credential(self, key: str, value: str, persist: bool = False):
        """
        Set a credential.
        
        Args:
            key: Credential key
            value: Credential value
            persist: Whether to persist to encrypted file
        """
        self._cache[key] = value
        
        if persist and self.config.use_encrypted_file:
            self._save_to_encrypted_file(key, value)
            logger.info(f"Credential '{key}' persisted to encrypted storage")
    
    def get_api_keys(self) -> Dict[str, str]:
        """
        Get all API keys as a dictionary.
        Compatible with existing code expecting api_keys dict.
        """
        return {
            'fred': {'api_key': self.get_credential('fred_api_key', '')},
            'newsapi': {'api_key': self.get_credential('newsapi_api_key', '')},
            'alpha_vantage': {'api_key': self.get_credential('alpha_vantage_api_key', '')},
        }
    
    def get_mt5_credentials(self) -> Dict[str, str]:
        """Get MT5 trading credentials"""
        return {
            'login': self.get_credential('mt5_login', ''),
            'password': self.get_credential('mt5_password', ''),
            'server': self.get_credential('mt5_server', ''),
        }
    
    def get_broker_credentials(self, broker: str) -> Dict[str, str]:
        """Get credentials for a specific broker"""
        broker = broker.lower()
        
        if broker == 'binance':
            return {
                'api_key': self.get_credential('binance_api_key', ''),
                'api_secret': self.get_credential('binance_api_secret', ''),
            }
        elif broker == 'alpaca':
            return {
                'api_key': self.get_credential('alpaca_api_key', ''),
                'api_secret': self.get_credential('alpaca_api_secret', ''),
            }
        else:
            logger.warning(f"Unknown broker: {broker}")
            return {}
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet encryption instance"""
        if self._fernet is None:
            # Derive key from master password (from env) or generate
            master_key = os.environ.get('CREDENTIALS_MASTER_KEY', 'default_dev_key')
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.config.key_derivation_salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            self._fernet = Fernet(key)
        
        return self._fernet
    
    def _get_from_encrypted_file(self, key: str) -> Optional[str]:
        """Get credential from encrypted file"""
        try:
            file_path = Path(self.config.encrypted_file_path)
            if not file_path.exists():
                return None
            
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            fernet = self._get_fernet()
            decrypted_data = fernet.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            return credentials.get(key)
        except Exception as e:
            logger.error(f"Error reading encrypted credentials: {e}")
            return None
    
    def _save_to_encrypted_file(self, key: str, value: str):
        """Save credential to encrypted file"""
        try:
            file_path = Path(self.config.encrypted_file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing credentials
            credentials = {}
            if file_path.exists():
                try:
                    with open(file_path, 'rb') as f:
                        encrypted_data = f.read()
                    fernet = self._get_fernet()
                    decrypted_data = fernet.decrypt(encrypted_data)
                    credentials = json.loads(decrypted_data.decode())
                except Exception:
                    pass
            
            # Update and save
            credentials[key] = value
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            logger.error(f"Error saving encrypted credentials: {e}")
    
    def _log_access(self, key: str):
        """Log credential access for audit"""
        import datetime
        self._access_log.append({
            'key': key,
            'timestamp': datetime.datetime.now().isoformat(),
        })
        
        # Keep only last 1000 entries
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-1000:]
    
    def get_access_log(self) -> list:
        """Get credential access log for auditing"""
        return self._access_log.copy()
    
    def validate_credentials(self) -> Dict[str, bool]:
        """
        Validate that required credentials are available.
        
        Returns:
            Dict mapping credential names to availability status
        """
        results = {}
        
        for key in self.ENV_MAPPINGS.keys():
            value = self.get_credential(key)
            results[key] = bool(value and len(value) > 0)
        
        return results
    
    def mask_credential(self, value: str, visible_chars: int = 4) -> str:
        """Mask a credential for safe logging"""
        if not value or len(value) <= visible_chars:
            return '*' * len(value) if value else ''
        return value[:visible_chars] + '*' * (len(value) - visible_chars)


# Global instance
_credentials_manager: Optional[SecureCredentialsManager] = None


def get_credentials_manager() -> SecureCredentialsManager:
    """Get the global credentials manager instance"""
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = SecureCredentialsManager()
    return _credentials_manager


def get_api_key(service: str) -> str:
    """
    Convenience function to get an API key.
    
    Args:
        service: Service name (e.g., 'fred', 'newsapi', 'alpha_vantage')
        
    Returns:
        API key or empty string
    """
    manager = get_credentials_manager()
    key_name = f"{service.lower()}_api_key"
    return manager.get_credential(key_name, '') or ''


def load_api_keys_secure() -> Dict[str, Any]:
    """
    Load API keys securely - replacement for loading from JSON file.
    
    Returns:
        Dictionary compatible with existing api_keys.json format
    """
    manager = get_credentials_manager()
    return manager.get_api_keys()


# Migration helper
def migrate_from_json_file(json_path: str = "config/api_keys.json"):
    """
    Migrate API keys from JSON file to environment variables.
    Prints instructions for setting up environment variables.
    """
    try:
        with open(json_path, 'r') as f:
            old_keys = json.load(f)
        
        print("\n" + "=" * 60)
        print("API KEY MIGRATION INSTRUCTIONS")
        print("=" * 60)
        print("\nAdd these to your .env file or system environment:\n")
        
        for service, data in old_keys.items():
            if isinstance(data, dict) and 'api_key' in data:
                env_var = f"{service.upper()}_API_KEY"
                value = data['api_key']
                print(f"export {env_var}=\"{value}\"")
        
        print("\n" + "=" * 60)
        print("After setting environment variables, delete config/api_keys.json")
        print("=" * 60 + "\n")
        
    except FileNotFoundError:
        print("No api_keys.json file found - already migrated or not needed")
    except Exception as e:
        print(f"Error during migration: {e}")
