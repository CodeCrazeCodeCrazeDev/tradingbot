"""
Secrets Management System
Secure handling of API keys, passwords, and sensitive configuration
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import getpass

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages secure storage and retrieval of secrets."""
    
    def __init__(self, secrets_dir: str = "secrets"):
        self.secrets_dir = Path(secrets_dir)
        self.secrets_dir.mkdir(exist_ok=True)
        self.key_file = self.secrets_dir / ".master_key"
        self.secrets_file = self.secrets_dir / "secrets.enc"
        self._cipher = None
        self._secrets_cache: Dict[str, str] = {}
        
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return base64.urlsafe_b64decode(f.read())
        else:
            # Generate new key
            password = getpass.getpass("Set master password for secrets: ").encode()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Save salt and key
            with open(self.key_file, 'wb') as f:
                f.write(salt + b'\n' + key)
            
            return base64.urlsafe_b64decode(key)
    
    def _get_cipher(self) -> Fernet:
        """Get or create Fernet cipher."""
        if self._cipher is None:
            key = self._get_or_create_key()
            self._cipher = Fernet(base64.urlsafe_b64encode(key))
        return self._cipher
    
    def store_secret(self, name: str, value: str) -> bool:
        """Store a secret securely."""
        try:
            cipher = self._get_cipher()
            encrypted = cipher.encrypt(value.encode())
            
            # Load existing secrets
            secrets = self._load_all_secrets()
            secrets[name] = encrypted.decode()
            
            # Save back
            with open(self.secrets_file, 'w') as f:
                json.dump(secrets, f)
            
            # Update cache
            self._secrets_cache[name] = value
            
            logger.info(f"Secret '{name}' stored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret '{name}': {e}")
            return False
    
    def get_secret(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a secret."""
        # Check cache first
        if name in self._secrets_cache:
            return self._secrets_cache[name]
        
        try:
            secrets = self._load_all_secrets()
            if name not in secrets:
                return default
            
            cipher = self._get_cipher()
            decrypted = cipher.decrypt(secrets[name].encode()).decode()
            
            # Cache for future use
            self._secrets_cache[name] = decrypted
            
            return decrypted
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{name}': {e}")
            return default
    
    def rotate_secret(self, name: str, new_value: str) -> bool:
        """Rotate a secret to a new value."""
        if self.store_secret(name, new_value):
            logger.info(f"Secret '{name}' rotated successfully")
            return True
        return False
    
    def delete_secret(self, name: str) -> bool:
        """Delete a secret."""
        try:
            secrets = self._load_all_secrets()
            if name in secrets:
                del secrets[name]
                
                with open(self.secrets_file, 'w') as f:
                    json.dump(secrets, f)
                
                # Remove from cache
                self._secrets_cache.pop(name, None)
                
                logger.info(f"Secret '{name}' deleted")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete secret '{name}': {e}")
            return False
    
    def list_secrets(self) -> list:
        """List all secret names (without values)."""
        try:
            secrets = self._load_all_secrets()
            return list(secrets.keys())
        except Exception:
            return []
    
    def _load_all_secrets(self) -> Dict[str, str]:
        """Load all secrets from file."""
        if not self.secrets_file.exists():
            return {}
        
        with open(self.secrets_file) as f:
            return json.load(f)
    
    def backup_secrets(self, backup_path: str) -> bool:
        """Create encrypted backup of all secrets."""
        try:
            import shutil
            shutil.copy2(self.secrets_file, backup_path)
            logger.info(f"Secrets backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False


class EnvironmentSecrets:
    """Fallback secrets manager using environment variables."""
    
    @staticmethod
    def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from environment variable."""
        env_name = f"TRADING_BOT_{name.upper()}"
        return os.environ.get(env_name, default)
    
    @staticmethod
    def store_secret(name: str, value: str) -> bool:
        """Note: Cannot store to environment variables permanently."""
        logger.warning("EnvironmentSecrets cannot persist secrets. Use SecretsManager instead.")
        os.environ[f"TRADING_BOT_{name.upper()}"] = value
        return True


class ConfigWithSecrets:
    """Configuration manager that integrates secrets."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.secrets_manager = SecretsManager()
        self.env_secrets = EnvironmentSecrets()
        self.config_path = config_path or "config/config.yaml"
        self._config: Dict[str, Any] = {}
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value, resolving secrets if needed."""
        # Check if it's a secret reference
        if key.startswith("secret:"):
            secret_name = key[7:]  # Remove 'secret:' prefix
            return self._resolve_secret(secret_name)
        
        # Check environment first
        env_value = self.env_secrets.get_secret(key)
        if env_value is not None:
            return env_value
        
        # Check secrets manager
        secret_value = self.secrets_manager.get_secret(key)
        if secret_value is not None:
            return secret_value
        
        return default
    
    def _resolve_secret(self, name: str) -> Optional[str]:
        """Resolve a secret from available sources."""
        # Try secrets manager first
        value = self.secrets_manager.get_secret(name)
        if value:
            return value
        
        # Fall back to environment
        return self.env_secrets.get_secret(name)
    
    def get_mt5_credentials(self) -> Dict[str, Optional[str]]:
        """Get MT5 credentials securely."""
        return {
            'login': self.get('mt5_login'),
            'password': self.get('mt5_password'),
            'server': self.get('mt5_server')
        }
    
    def get_database_url(self) -> Optional[str]:
        """Get database URL with password from secrets."""
        db_password = self.get('db_password')
        if db_password:
            return f"postgresql://trading_bot:{db_password}@localhost:5432/trading_bot"
        return os.environ.get('DATABASE_URL')
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service."""
        return self.get(f'{service}_api_key')


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def initialize_secrets():
    """Initialize secrets storage interactively."""
    manager = get_secrets_manager()
    
    print("\n=== Trading Bot Secrets Setup ===\n")
    
    # MT5 Credentials
    print("MT5 Credentials:")
    mt5_login = input("MT5 Login (or press Enter to skip): ").strip()
    if mt5_login:
        manager.store_secret('mt5_login', mt5_login)
        
        mt5_pass = getpass.getpass("MT5 Password: ")
        if mt5_pass:
            manager.store_secret('mt5_password', mt5_pass)
        
        mt5_server = input("MT5 Server: ").strip()
        if mt5_server:
            manager.store_secret('mt5_server', mt5_server)
    
    # Database
    print("\nDatabase:")
    db_pass = getpass.getpass("Database Password (or press Enter to skip): ")
    if db_pass:
        manager.store_secret('db_password', db_pass)
    
    # API Keys
    print("\nAPI Keys (press Enter to skip):")
    for service in ['news_api', 'sentiment_api', 'alternative_data']:
        key = getpass.getpass(f"{service.replace('_', ' ').title()} API Key: ").strip()
        if key:
            manager.store_secret(f'{service}_api_key', key)
    
    print("\n✓ Secrets setup complete!")


if __name__ == "__main__":
    # Allow running as script for setup
    initialize_secrets()
