"""
Secure Vault - Encrypted Credential Storage
============================================

Provides encrypted storage for sensitive credentials:
- API keys
- Passwords
- Tokens
- Secrets

Uses Fernet symmetric encryption (AES-128-CBC with HMAC).
"""

import logging
import os
import json
import base64
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import cryptography, fall back to basic encoding if not available
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not installed. Using basic encoding (NOT SECURE FOR PRODUCTION)")


class SecureVault:
    """
    Encrypted credential vault using Fernet encryption.
    
    Features:
    - AES-128-CBC encryption with HMAC
    - Password-derived key using PBKDF2
    - Secure storage of API keys, passwords, tokens
    - Salt-based key derivation for additional security
    """
    
    def __init__(
        self,
        vault_path: str = "vault.enc",
        salt_path: str = ".salt"
    ):
        """
        Initialize secure vault.
        
        Args:
            vault_path: Path to encrypted vault file
            salt_path: Path to salt file
        """
        self.vault_path = Path(vault_path)
        self.salt_path = Path(salt_path)
        self._fernet: Optional[Any] = None
        self._credentials: Dict[str, str] = {}
        self._initialized = False
        
        logger.info("SecureVault initialized")
    
    def initialize(self, master_password: str) -> bool:
        """
        Initialize vault with master password.
        
        Args:
            master_password: Master password for encryption
            
        Returns:
            True if initialized successfully
        """
        try:
            if not CRYPTO_AVAILABLE:
                logger.warning("Using basic encoding - install cryptography for real encryption")
                self._fernet = None
                self._initialized = True
                self._load_vault_basic()
                return True
            
            # Get or create salt
            salt = self._get_or_create_salt()
            
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            self._fernet = Fernet(key)
            
            # Load existing vault if present
            if self.vault_path.exists():
                self._load_vault()
            
            self._initialized = True
            logger.info("Vault initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize vault: {e}")
            return False
    
    def _get_or_create_salt(self) -> bytes:
        """Get existing salt or create new one"""
        if self.salt_path.exists():
            with open(self.salt_path, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(16)
            self.salt_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.salt_path, 'wb') as f:
                f.write(salt)
            return salt
    
    def store(self, key: str, value: str) -> bool:
        """
        Store a credential securely.
        
        Args:
            key: Credential key (e.g., "BINANCE_API_KEY")
            value: Credential value
            
        Returns:
            True if stored successfully
        """
        if not self._initialized:
            logger.error("Vault not initialized")
            return False
        try:
        
            self._credentials[key] = value
            self._save_vault()
            logger.info(f"Stored credential: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to store credential: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[str]:
        """
        Retrieve a credential.
        
        Args:
            key: Credential key
            
        Returns:
            Credential value or None
        """
        if not self._initialized:
            logger.error("Vault not initialized")
            return None
        
        return self._credentials.get(key)
    
    def delete(self, key: str) -> bool:
        """
        Delete a credential.
        
        Args:
            key: Credential key
            
        Returns:
            True if deleted
        """
        if not self._initialized:
            return False
        
        if key in self._credentials:
            del self._credentials[key]
            self._save_vault()
            logger.info(f"Deleted credential: {key}")
            return True
        return False
    
    def list_keys(self) -> list:
        """List all stored credential keys"""
        return list(self._credentials.keys())
    
    def _save_vault(self):
        """Save encrypted vault to file"""
        try:
            data = json.dumps(self._credentials)
            
            if CRYPTO_AVAILABLE and self._fernet:
                encrypted = self._fernet.encrypt(data.encode())
                self.vault_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.vault_path, 'wb') as f:
                    f.write(encrypted)
            else:
                # Basic encoding (NOT SECURE)
                encoded = base64.b64encode(data.encode())
                self.vault_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.vault_path, 'wb') as f:
                    f.write(encoded)
                    
        except Exception as e:
            logger.error(f"Failed to save vault: {e}")
    
    def _load_vault(self):
        """Load encrypted vault from file"""
        try:
            with open(self.vault_path, 'rb') as f:
                encrypted = f.read()
            
            if CRYPTO_AVAILABLE and self._fernet:
                decrypted = self._fernet.decrypt(encrypted)
                self._credentials = json.loads(decrypted.decode())
            else:
                decoded = base64.b64decode(encrypted)
                self._credentials = json.loads(decoded.decode())
                
            logger.info(f"Loaded {len(self._credentials)} credentials from vault")
            
        except Exception as e:
            logger.error(f"Failed to load vault: {e}")
            self._credentials = {}
    
    def _load_vault_basic(self):
        """Load vault with basic encoding"""
        if self.vault_path.exists():
            try:
                with open(self.vault_path, 'rb') as f:
                    encoded = f.read()
                decoded = base64.b64decode(encoded)
                self._credentials = json.loads(decoded.decode())
            except:
                self._credentials = {}
    
    def get_status(self) -> Dict:
        """Get vault status"""
        return {
            'initialized': self._initialized,
            'encryption': 'Fernet (AES-128-CBC)' if CRYPTO_AVAILABLE else 'Basic (NOT SECURE)',
            'credentials_count': len(self._credentials),
            'vault_path': str(self.vault_path),
            'timestamp': datetime.now().isoformat()
        }


# Alias for backward compatibility
Vault = SecureVault


def create_vault(config: Optional[Dict] = None) -> SecureVault:
    """Factory function to create SecureVault instance"""
    vault_path = config.get('vault_path', 'vault.enc') if config else 'vault.enc'
    salt_path = config.get('salt_path', '.salt') if config else '.salt'
    return SecureVault(vault_path=vault_path, salt_path=salt_path)


# Global instance
_global_vault: Optional[SecureVault] = None


def get_vault() -> SecureVault:
    """Get global vault instance"""
    global _global_vault
    if _global_vault is None:
        _global_vault = SecureVault()
    return _global_vault


if __name__ == "__main__":
    # Test the module
    vault = create_vault()
    vault.initialize("test_password")
    vault.store("TEST_KEY", "test_value")
    print(f"Retrieved: {vault.retrieve('TEST_KEY')}")
    print(f"Status: {vault.get_status()}")
