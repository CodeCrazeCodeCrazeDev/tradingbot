"""
from typing import Callable, Dict, Optional, Set, Tuple
AlphaAlgo Broker Hub

Secure broker connection management with credential isolation.
Human must provide credentials - AI does NOT auto-connect.

Supported Brokers:
- MT5 (MetaTrader 5)
- Robinhood
- Alpaca
- Interactive Brokers

Security:
- Credentials encrypted at rest
- No external communication without approval
- Connection requires human approval
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import cryptography for encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not available - credentials will not be encrypted")


class BrokerType(Enum):
    """Supported broker types"""
    MT5 = "mt5"
    ROBINHOOD = "robinhood"
    ALPACA = "alpaca"
    INTERACTIVE_BROKERS = "ib"
    BINANCE = "binance"
    SIMULATION = "simulation"


class ConnectionStatus(Enum):
    """Broker connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class BrokerCredentials:
    """
    Broker credentials container.
    
    Human must provide these - AI does NOT generate or guess credentials.
    """
    broker_type: BrokerType
    login: str = ""
    password: str = ""
    server: str = ""
    account: str = ""
    api_key: str = ""
    api_secret: str = ""
    additional: Dict[str, str] = field(default_factory=dict)
    
    def is_complete(self) -> bool:
        """Check if required credentials are provided"""
        if self.broker_type == BrokerType.MT5:
            return bool(self.login and self.password and self.server)
        elif self.broker_type == BrokerType.ALPACA:
            return bool(self.api_key and self.api_secret)
        elif self.broker_type == BrokerType.INTERACTIVE_BROKERS:
            return bool(self.account)
        elif self.broker_type == BrokerType.BINANCE:
            return bool(self.api_key and self.api_secret)
        elif self.broker_type == BrokerType.SIMULATION:
            return True
        return False
    
    def get_masked(self) -> Dict[str, str]:
        """Get credentials with sensitive data masked"""
        return {
            'broker_type': self.broker_type.value,
            'login': self.login[:3] + '***' if self.login else '',
            'server': self.server,
            'account': self.account[:3] + '***' if self.account else '',
            'api_key': self.api_key[:4] + '***' if self.api_key else '',
        }


@dataclass
class BrokerConnection:
    """Broker connection state"""
    broker_type: BrokerType
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    connected_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    error_message: Optional[str] = None
    account_info: Dict[str, Any] = field(default_factory=dict)
    approval_id: Optional[str] = None


class CredentialVault:
    """
    Secure credential storage with encryption.
    
    Credentials are encrypted at rest using Fernet symmetric encryption.
    The encryption key is derived from a master password.
    """
    
    def __init__(self, vault_path: str = "alphaalgo_data/vault"):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self._fernet: Optional[Fernet] = None
        self._lock = threading.Lock()
    
    def initialize(self, master_password: str) -> bool:
        """Initialize vault with master password"""
        if not CRYPTO_AVAILABLE:
            logger.warning("Encryption not available - storing credentials in plain text")
            return True
        try:
        
            # Derive key from password
            salt = self._get_or_create_salt()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            self._fernet = Fernet(key)
            
            logger.info("[Vault] Initialized with encryption")
            return True
        except Exception as e:
            logger.error(f"[Vault] Initialization failed: {e}")
            return False
    
    def _get_or_create_salt(self) -> bytes:
        """Get or create salt for key derivation"""
        salt_file = self.vault_path / ".salt"
        if salt_file.exists():
            return salt_file.read_bytes()
        else:
            salt = os.urandom(16)
            salt_file.write_bytes(salt)
            return salt
    
    def store_credentials(
        self,
        broker_type: BrokerType,
        credentials: BrokerCredentials
    ) -> bool:
        """Store encrypted credentials"""
        with self._lock:
            try:
                data = json.dumps({
                    'login': credentials.login,
                    'password': credentials.password,
                    'server': credentials.server,
                    'account': credentials.account,
                    'api_key': credentials.api_key,
                    'api_secret': credentials.api_secret,
                    'additional': credentials.additional,
                })
                
                if self._fernet:
                    encrypted = self._fernet.encrypt(data.encode())
                    cred_file = self.vault_path / f"{broker_type.value}.enc"
                    cred_file.write_bytes(encrypted)
                else:
                    # Fallback to plain text (not recommended)
                    cred_file = self.vault_path / f"{broker_type.value}.json"
                    cred_file.write_text(data)
                
                logger.info(f"[Vault] Credentials stored for {broker_type.value}")
                return True
            except Exception as e:
                logger.error(f"[Vault] Failed to store credentials: {e}")
                return False
    
    def retrieve_credentials(self, broker_type: BrokerType) -> Optional[BrokerCredentials]:
        """Retrieve and decrypt credentials"""
        with self._lock:
            try:
                if self._fernet:
                    cred_file = self.vault_path / f"{broker_type.value}.enc"
                    if not cred_file.exists():
                        return None
                    encrypted = cred_file.read_bytes()
                    data = json.loads(self._fernet.decrypt(encrypted).decode())
                else:
                    cred_file = self.vault_path / f"{broker_type.value}.json"
                    if not cred_file.exists():
                        return None
                    data = json.loads(cred_file.read_text())
                
                return BrokerCredentials(
                    broker_type=broker_type,
                    login=data.get('login', ''),
                    password=data.get('password', ''),
                    server=data.get('server', ''),
                    account=data.get('account', ''),
                    api_key=data.get('api_key', ''),
                    api_secret=data.get('api_secret', ''),
                    additional=data.get('additional', {}),
                )
            except Exception as e:
                logger.error(f"[Vault] Failed to retrieve credentials: {e}")
                return None
    
    def delete_credentials(self, broker_type: BrokerType) -> bool:
        """Delete stored credentials"""
        with self._lock:
            try:
                for ext in ['.enc', '.json']:
                    cred_file = self.vault_path / f"{broker_type.value}{ext}"
                    if cred_file.exists():
                        cred_file.unlink()
                logger.info(f"[Vault] Credentials deleted for {broker_type.value}")
                return True
            except Exception as e:
                logger.error(f"[Vault] Failed to delete credentials: {e}")
                return False


class BrokerAdapter(ABC):
    """Abstract base class for broker adapters"""
    
    @abstractmethod
    async def connect(self, credentials: BrokerCredentials) -> Tuple[bool, str]:
        """Connect to broker"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if connected"""
        pass


class SimulationBrokerAdapter(BrokerAdapter):
    """Simulation broker for paper trading"""
    
    def __init__(self):
        self._connected = False
        self._balance = 10000.0
        self._equity = 10000.0
    
    async def connect(self, credentials: BrokerCredentials) -> Tuple[bool, str]:
        """
        connect function.

    Args:
        credentials: Description

    Returns:
        Result of operation
        """
        self._connected = True
        logger.info("[SimBroker] Connected to simulation")
        return (True, "Connected to simulation broker")
    
    async def disconnect(self) -> bool:
        self._connected = False
        return True
    
    async def get_account_info(self) -> Dict[str, Any]:
        return {
            'balance': self._balance,
            'equity': self._equity,
            'margin': 0.0,
            'free_margin': self._equity,
            'leverage': 100,
            'currency': 'USD',
            'mode': 'SIMULATION',
        }
    
    async def is_connected(self) -> bool:
        return self._connected


class BrokerHub:
    """
    Central broker connection hub.
    
    Features:
    - Secure credential storage
    - Human approval required for live connections
    - Connection monitoring
    - Multiple broker support
    """
    
    def __init__(
        self,
        vault_path: str = "alphaalgo_data/vault",
        require_approval: bool = True
    ):
        self.vault = CredentialVault(vault_path)
        self.require_approval = require_approval
        self._connections: Dict[BrokerType, BrokerConnection] = {}
        self._adapters: Dict[BrokerType, BrokerAdapter] = {}
        self._approval_callback: Optional[Callable] = None
        self._lock = threading.Lock()
        
        # Initialize simulation adapter
        self._adapters[BrokerType.SIMULATION] = SimulationBrokerAdapter()
        
        logger.info("[BrokerHub] Initialized")
    
    def set_approval_callback(self, callback: Callable):
        """Set callback for requesting human approval"""
        self._approval_callback = callback
    
    def initialize_vault(self, master_password: str) -> bool:
        """Initialize credential vault"""
        return self.vault.initialize(master_password)
    
    def store_credentials(
        self,
        broker_type: BrokerType,
        credentials: BrokerCredentials
    ) -> bool:
        """
        Store broker credentials.
        
        Human provides credentials - AI does NOT generate them.
        """
        if not credentials.is_complete():
            logger.warning(f"[BrokerHub] Incomplete credentials for {broker_type.value}")
            return False
        
        return self.vault.store_credentials(broker_type, credentials)
    
    async def connect(
        self,
        broker_type: BrokerType,
        approval_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Connect to a broker.
        
        For live brokers, requires human approval.
        """
        # Simulation doesn't need approval
        if broker_type == BrokerType.SIMULATION:
            return await self._do_connect(broker_type)
        
        # Check if approval required
        if self.require_approval and not approval_id:
            # Request approval
            with self._lock:
                self._connections[broker_type] = BrokerConnection(
                    broker_type=broker_type,
                    status=ConnectionStatus.AWAITING_APPROVAL,
                )
            
            if self._approval_callback:
                approval_id = self._approval_callback(
                    action="CONNECT_BROKER",
                    details={
                        'broker_type': broker_type.value,
                        'description': f"Connect to {broker_type.value} broker",
                    }
                )
                self._connections[broker_type].approval_id = approval_id
            
            return (False, f"Awaiting human approval. Approval ID: {approval_id}")
        
        return await self._do_connect(broker_type)
    
    async def _do_connect(self, broker_type: BrokerType) -> Tuple[bool, str]:
        """Actually connect to broker"""
        # Get credentials
        credentials = self.vault.retrieve_credentials(broker_type)
        if not credentials and broker_type != BrokerType.SIMULATION:
            return (False, "No credentials found. Please provide credentials first.")
        
        # Get or create adapter
        adapter = self._adapters.get(broker_type)
        if not adapter:
            if broker_type == BrokerType.SIMULATION:
                adapter = SimulationBrokerAdapter()
                self._adapters[broker_type] = adapter
            else:
                return (False, f"No adapter available for {broker_type.value}")
        
        # Connect
        with self._lock:
            pass
        try:
            self._connections[broker_type] = BrokerConnection(
                broker_type=broker_type,
                status=ConnectionStatus.CONNECTING,
            )
        
            success, message = await adapter.connect(
                credentials or BrokerCredentials(broker_type=broker_type)
            )
            
            with self._lock:
                if success:
                    self._connections[broker_type].status = ConnectionStatus.CONNECTED
                    self._connections[broker_type].connected_at = datetime.now()
                    self._connections[broker_type].account_info = await adapter.get_account_info()
                else:
                    self._connections[broker_type].status = ConnectionStatus.ERROR
                    self._connections[broker_type].error_message = message
            
            return (success, message)
            
        except Exception as e:
            with self._lock:
                self._connections[broker_type].status = ConnectionStatus.ERROR
                self._connections[broker_type].error_message = str(e)
            return (False, f"Connection failed: {e}")
    
    async def disconnect(self, broker_type: BrokerType) -> bool:
        """Disconnect from broker"""
        adapter = self._adapters.get(broker_type)
        if adapter:
            await adapter.disconnect()
        
        with self._lock:
            if broker_type in self._connections:
                self._connections[broker_type].status = ConnectionStatus.DISCONNECTED
        
        logger.info(f"[BrokerHub] Disconnected from {broker_type.value}")
        return True
    
    async def disconnect_all(self):
        """Disconnect from all brokers"""
        for broker_type in list(self._connections.keys()):
            await self.disconnect(broker_type)
    
    def get_connection_status(self, broker_type: BrokerType) -> Optional[BrokerConnection]:
        """Get connection status"""
        with self._lock:
            return self._connections.get(broker_type)
    
    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get all connection statuses"""
        with self._lock:
            return {
                bt.value: {
                    'status': conn.status.value,
                    'connected_at': conn.connected_at.isoformat() if conn.connected_at else None,
                    'account_info': conn.account_info,
                    'error': conn.error_message,
                }
                for bt, conn in self._connections.items()
            }
    
    def is_any_live_connected(self) -> bool:
        """Check if any live broker is connected"""
        with self._lock:
            for bt, conn in self._connections.items():
                if bt != BrokerType.SIMULATION and conn.status == ConnectionStatus.CONNECTED:
                    return True
            return False
    
    def get_credential_template(self, broker_type: BrokerType) -> Dict[str, str]:
        """
        Get credential template for human to fill.
        
        AI does NOT fill these - human must provide.
        """
        templates = {
            BrokerType.MT5: {
                'login': '<your_mt5_login>',
                'password': '<your_mt5_password>',
                'server': '<broker_server_name>',
                'account': '<optional_account_id>',
            },
            BrokerType.ALPACA: {
                'api_key': '<your_alpaca_api_key>',
                'api_secret': '<your_alpaca_api_secret>',
                'additional': {'paper': 'true'},
            },
            BrokerType.INTERACTIVE_BROKERS: {
                'account': '<your_ib_account>',
                'additional': {'port': '7497', 'client_id': '1'},
            },
            BrokerType.BINANCE: {
                'api_key': '<your_binance_api_key>',
                'api_secret': '<your_binance_api_secret>',
            },
            BrokerType.ROBINHOOD: {
                'login': '<your_robinhood_email>',
                'password': '<your_robinhood_password>',
                'additional': {'mfa_code': '<if_required>'},
            },
        }
        return templates.get(broker_type, {})
