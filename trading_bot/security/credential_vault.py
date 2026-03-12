import logging
"""
Encrypted credential storage using Fernet encryption.
Replaces plaintext credential storage with bank-level security.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet
from loguru import logger

logger = logging.getLogger(__name__)



class SecureCredentialVault:
    """Encrypted credential storage with Fernet symmetric encryption."""
    
    def __init__(self, vault_path: str = '.credentials.enc'):
        self.vault_path = Path(vault_path)
        self.key_path = Path.home() / '.trading_bot_key'
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        logger.info("SecureCredentialVault initialized")
    
    def _load_or_generate_key(self) -> bytes:
        """Load encryption key from secure location or generate new one."""
        if self.key_path.exists():
            with open(self.key_path, 'rb') as f:
                key = f.read()
            logger.info(f"Encryption key loaded from {self.key_path}")
            return key
        else:
            # Generate new key
            key = Fernet.generate_key()
            
            # Save key with restricted permissions
            with open(self.key_path, 'wb') as f:
                pass
            try:
                f.write(key)
            
            # Set file permissions (owner read/write only)
                os.chmod(self.key_path, 0o600)
            except Exception as e:
                logger.warning(f"Could not set file permissions: {e}")
            
            logger.info(f"New encryption key generated and saved to {self.key_path}")
            return key
    
    def _load_vault(self) -> Dict:
        """Load and decrypt vault contents."""
        if not self.vault_path.exists():
            return {}
        try:
        
            with open(self.vault_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            vault_data = json.loads(decrypted_data.decode())
            return vault_data
        except Exception as e:
            logger.error(f"Failed to load vault: {e}")
            return {}
    
    def _save_vault(self, vault_data: Dict):
        """Encrypt and save vault contents."""
        try:
            json_data = json.dumps(vault_data, indent=2).encode()
            encrypted_data = self.cipher.encrypt(json_data)
            
            with open(self.vault_path, 'wb') as f:
                pass
            try:
                f.write(encrypted_data)
            
            # Set file permissions
                os.chmod(self.vault_path, 0o600)
            except Exception as e:
                logger.warning(f"Could not set file permissions: {e}")
            
        except Exception as e:
            logger.error(f"Failed to save vault: {e}")
            raise
    
    def store_credential(self, name: str, value: str, metadata: Optional[Dict] = None):
        """
        Store encrypted credential.
        
        Args:
            name: Credential name/key
            value: Credential value (API key, password, etc.)
            metadata: Optional metadata (description, created_at, etc.)
        """
        vault = self._load_vault()
        
        credential_entry = {
            'value': value,
            'metadata': metadata or {}
        }
        
        vault[name] = credential_entry
        self._save_vault(vault)
        
        logger.info(f"Credential '{name}' stored securely")
    
    def get_credential(self, name: str) -> str:
        """
        Retrieve decrypted credential.
        
        Args:
            name: Credential name/key
            
        Returns:
            Decrypted credential value
            
        Raises:
            KeyError: If credential not found
        """
        vault = self._load_vault()
        
        if name not in vault:
            raise KeyError(f"Credential '{name}' not found in vault")
        
        return vault[name]['value']
    
    def get_credential_with_metadata(self, name: str) -> Dict:
        """Get credential with metadata."""
        vault = self._load_vault()
        
        if name not in vault:
            raise KeyError(f"Credential '{name}' not found in vault")
        
        return vault[name]
    
    def delete_credential(self, name: str):
        """Delete credential from vault."""
        vault = self._load_vault()
        
        if name in vault:
            del vault[name]
            self._save_vault(vault)
            logger.info(f"Credential '{name}' deleted")
        else:
            logger.warning(f"Credential '{name}' not found for deletion")
    
    def list_credentials(self) -> list:
        """List all stored credential names."""
        vault = self._load_vault()
        return list(vault.keys())
    
    def credential_exists(self, name: str) -> bool:
        """Check if credential exists."""
        vault = self._load_vault()
        return name in vault
    
    def rotate_key(self):
        """Rotate encryption key (re-encrypt all credentials with new key)."""
        logger.info("Starting key rotation...")
        
        # Load current vault
        old_vault = self._load_vault()
        
        # Generate new key
        new_key = Fernet.generate_key()
        new_cipher = Fernet(new_key)
        
        # Re-encrypt vault with new key
        self.cipher = new_cipher
        self.key = new_key
        
        # Save vault with new encryption
        self._save_vault(old_vault)
        
        # Save new key
        with open(self.key_path, 'wb') as f:
            pass
        try:
            f.write(new_key)
        
            os.chmod(self.key_path, 0o600)
        except Exception as e:
            logger.warning(f"Could not set file permissions: {e}")
        
        logger.success("Key rotation completed successfully")
    
    def export_vault(self, export_path: str, include_values: bool = False):
        """
        Export vault contents (for backup or migration).
        
        Args:
            export_path: Path to export file
            include_values: If True, export decrypted values (DANGEROUS!)
        """
        vault = self._load_vault()
        
        if not include_values:
            # Export only metadata
            export_data = {
                name: entry['metadata'] 
                for name, entry in vault.items()
            }
        else:
            export_data = vault
            logger.warning("Exporting vault with decrypted values - SECURITY RISK!")
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Vault exported to {export_path}")
    
    def import_vault(self, import_path: str, merge: bool = False):
        """
        Import vault contents.
        
        Args:
            import_path: Path to import file
            merge: If True, merge with existing vault; if False, replace
        """
        with open(import_path, 'r') as f:
            import_data = json.load(f)
        
        if merge:
            vault = self._load_vault()
            vault.update(import_data)
        else:
            vault = import_data
        
        self._save_vault(vault)
        logger.info(f"Vault imported from {import_path}")


class EnvironmentCredentialLoader:
    """Load credentials from environment variables with fallback to vault."""
    
    def __init__(self, vault: Optional[SecureCredentialVault] = None):
        self.vault = vault or SecureCredentialVault()
    
    def get_credential(self, name: str, env_var: Optional[str] = None) -> str:
        """
        Get credential from environment variable or vault.
        
        Args:
            name: Credential name
            env_var: Environment variable name (defaults to name.upper())
            
        Returns:
            Credential value
        """
        env_var = env_var or name.upper()
        
        # Try environment variable first
        value = os.getenv(env_var)
        if value:
            logger.debug(f"Loaded '{name}' from environment variable")
            return value
        try:
        
        # Fallback to vault
            value = self.vault.get_credential(name)
            logger.debug(f"Loaded '{name}' from secure vault")
            return value
        except KeyError:
            raise KeyError(
                f"Credential '{name}' not found in environment or vault. "
                f"Set {env_var} environment variable or store in vault."
            )
    
    def get_mt5_credentials(self) -> Dict:
        """Get MT5 credentials."""
        return {
            'login': self.get_credential('mt5_login', 'MT5_LOGIN'),
            'password': self.get_credential('mt5_password', 'MT5_PASSWORD'),
            'server': self.get_credential('mt5_server', 'MT5_SERVER')
        }
    
    def get_api_key(self, service: str) -> str:
        """Get API key for a service."""
        return self.get_credential(f'{service}_api_key', f'{service.upper()}_API_KEY')


# Convenience functions
def store_mt5_credentials(login: str, password: str, server: str):
    """Store MT5 credentials securely."""
    vault = SecureCredentialVault()
    vault.store_credential('mt5_login', login, {'service': 'MT5'})
    vault.store_credential('mt5_password', password, {'service': 'MT5'})
    vault.store_credential('mt5_server', server, {'service': 'MT5'})
    logger.success("MT5 credentials stored securely")


def get_mt5_credentials() -> Dict:
    """Get MT5 credentials from vault or environment."""
    loader = EnvironmentCredentialLoader()
    return loader.get_mt5_credentials()
