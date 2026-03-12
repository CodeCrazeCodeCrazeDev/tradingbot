"""
Secure Credential Management

This module provides secure storage and retrieval of API keys and secrets.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import cryptography, make it optional
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not available - install with: pip install cryptography")

# Try to import dotenv, make it optional
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.warning("python-dotenv not available - install with: pip install python-dotenv")


class SecureCredentialManager:
    """
    Secure credential management system
    
    Features:
    - Loads credentials from environment variables
    - Encrypts credentials in memory
    - Ensures sensitive files are gitignored
    - Provides secure access methods
    """
    
    def __init__(self, env_file: str = '.env'):
        self.env_file = Path(env_file)
        self.encrypted_cache: Dict[str, bytes] = {}
        
        # Load environment variables
        if DOTENV_AVAILABLE and self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info(f"Loaded environment from {self.env_file}")
        else:
            logger.info("Using system environment variables")
        
        # Setup encryption
        if CRYPTO_AVAILABLE:
            self.cipher = self._setup_encryption()
        else:
            self.cipher = None
            logger.warning("Encryption not available - credentials stored in plain text")
        
        # Ensure .gitignore is configured
        self._ensure_gitignore()
    
    def _setup_encryption(self) -> Optional[Fernet]:
        """Setup encryption key"""
        key_file = Path('.secret_key')
        
        if key_file.exists():
            # Load existing key
            with open(key_file, 'rb') as f:
                key = f.read()
            logger.info("Loaded encryption key")
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            logger.info("Generated new encryption key")
        
        return Fernet(key)
    
    def get_credential(self, name: str, required: bool = True) -> Optional[str]:
        """
        Get credential from environment
        
        Args:
            name: Credential name (e.g., 'API_KEY')
            required: If True, raises error if not found
        
        Returns:
            Credential value or None
        """
        value = os.getenv(name)
        
        if value is None and required:
            raise ValueError(
                f"Credential '{name}' not found in environment. "
                f"Please set it in {self.env_file} or system environment."
            )
        
        return value
    
    def get_encrypted(self, name: str) -> Optional[bytes]:
        """
        Get credential and encrypt it
        
        Args:
            name: Credential name
        
        Returns:
            Encrypted credential
        """
        # Check cache first
        if name in self.encrypted_cache:
            return self.encrypted_cache[name]
        
        # Get from environment
        value = self.get_credential(name, required=False)
        if value is None:
            return None
        
        # Encrypt if available
        if self.cipher:
            encrypted = self.cipher.encrypt(value.encode())
            self.encrypted_cache[name] = encrypted
            return encrypted
        else:
            # Store as bytes without encryption
            encrypted = value.encode()
            self.encrypted_cache[name] = encrypted
            return encrypted
    
    def decrypt(self, encrypted_value: bytes) -> str:
        """
        Decrypt credential
        
        Args:
            encrypted_value: Encrypted bytes
        
        Returns:
            Decrypted string
        """
        if self.cipher:
            return self.cipher.decrypt(encrypted_value).decode()
        else:
            return encrypted_value.decode()
    
    def set_credential(self, name: str, value: str):
        """
        Set credential in environment (runtime only)
        
        Args:
            name: Credential name
            value: Credential value
        """
        os.environ[name] = value
        
        # Clear cache
        if name in self.encrypted_cache:
            del self.encrypted_cache[name]
    
    def _ensure_gitignore(self):
        """Ensure sensitive files are in .gitignore"""
        gitignore = Path('.gitignore')
        
        sensitive_patterns = [
            '.env',
            '.env.*',
            '.secret_key',
            '*.key',
            '*.pem',
            'credentials.json',
            'secrets.json',
            '*.credentials',
        ]
        
        # Read existing .gitignore
        if gitignore.exists():
            with open(gitignore, 'r') as f:
                existing = f.read()
        else:
            existing = ''
        
        # Add missing patterns
        added = []
        with open(gitignore, 'a') as f:
            for pattern in sensitive_patterns:
                if pattern not in existing:
                    f.write(f'\n{pattern}')
                    added.append(pattern)
        
        if added:
            logger.info(f"Added {len(added)} patterns to .gitignore")
    
    def create_env_template(self):
        """Create .env.template file with required credentials"""
        template = """# Elite Trading Bot - Environment Variables Template
# Copy this file to .env and fill in your credentials

# Broker Credentials
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# API Keys
API_KEY=your_api_key
API_SECRET=your_api_secret

# Telegram Bot
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_ADMIN_ID=your_telegram_user_id

# Database
DATABASE_URL=sqlite:///data/trading_bot.db

# Optional Services
REDIS_URL=redis://localhost:6379
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_email_password

# Risk Limits
MAX_DAILY_LOSS=1000
MAX_POSITION_SIZE=10000
MAX_POSITIONS=10
"""
        
        template_file = Path('.env.template')
        with open(template_file, 'w') as f:
            f.write(template)
        
        logger.info(f"Created {template_file}")
    
    def validate_required_credentials(self, required: list):
        """
        Validate that all required credentials are present
        
        Args:
            required: List of required credential names
        
        Raises:
            ValueError: If any required credential is missing
        """
        missing = []
        for name in required:
            if not os.getenv(name):
                missing.append(name)
        
        if missing:
            raise ValueError(
                f"Missing required credentials: {', '.join(missing)}\n"
                f"Please set them in {self.env_file} or system environment."
            )
    
    def get_all_credentials(self) -> Dict[str, str]:
        """
        Get all credentials (for debugging only - use carefully!)
        
        Returns:
            Dict of all environment variables
        """
        logger.warning("Getting all credentials - use only for debugging!")
        return dict(os.environ)


# Singleton instance
_credential_manager = None


def get_credential_manager(env_file: str = '.env') -> SecureCredentialManager:
    """Get singleton credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = SecureCredentialManager(env_file)
    return _credential_manager


# Export
__all__ = [
    'SecureCredentialManager',
    'get_credential_manager',
    'CRYPTO_AVAILABLE',
    'DOTENV_AVAILABLE'
]
