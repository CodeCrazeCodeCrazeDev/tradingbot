"""
from typing import Optional, Set
Survival Core - Critical elements for long-term trading success

This module implements the core components necessary for long-term survival
and profitability in live markets:
1. Market Data & Analysis (Brain)
2. Execution (Hands)
3. Risk & Money Management (Shield)
4. Monitoring & Control (Eyes)
5. Security & Reliability (Foundation)
"""

import asyncio
import logging
import json
import hmac
import hashlib
import base64
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import pandas as pd
import numpy as np
from pathlib import Path
try:
    import telegram
except ImportError:
    telegram = None
from cryptography.fernet import Fernet

# Optional dependencies with safe fallbacks
try:
    import redis
except ImportError:
    redis = None
    logging.warning("Redis not available - caching features disabled")

try:
    import ntplib
except ImportError:
    ntplib = None
    logging.warning("ntplib not available - clock drift check disabled")

try:
    import zmq
    import zmq.asyncio
except ImportError:
    zmq = None
    logging.warning("ZMQ not available - some streaming features disabled")

# Import core components (non-circular imports only)
from trading_bot.core.analysis_orchestrator import AnalysisOrchestrator
from trading_bot.core.monitoring_system import MonitoringSystem
from trading_bot.data.market_data_stream import MarketDataStream

try:
    # Lazy imports to avoid circular dependencies
# ExecutionManager, TimeSeriesDB, EmergencyControls imported in methods

# Import OrderType for signal processing
    from trading_bot.core.execution_manager import OrderType
except ImportError:
    pass

try:
    from enum import Enum
    class OrderType(Enum):
        MARKET = 'market'
        LIMIT = 'limit'
        STOP = 'stop'

except Exception:
    pass
logger = logging.getLogger(__name__)


class SurvivalCore:
    """Core system ensuring long-term survival and profitability"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the survival core"""
        self.config = config or {}
        logger.info("Initializing Survival Core")
        
        # Initialize security components
        self._init_security()
        
        # Initialize core components
        self._init_components()
        
        # Initialize risk limits
        self._init_risk_limits()
        
        # Initialize notification system
        self._init_notifications()
        
        # System state
        self.running = False
        self.paused = False
        self.emergency_shutdown = False
        self.last_health_check = datetime.now()
        self.errors = []  # List of error records: {'component': str, 'timestamp': datetime, 'error': str}
        
        # Notification throttling
        self.notification_history = defaultdict(lambda: deque(maxlen=10))  # Track last 10 notifications per type
        self.notification_cooldown = self.config.get('notification_cooldown', 300)  # 5 minutes default
        
        # Data quality tracking
        self.last_tick_time = {}
        self.max_data_staleness = self.config.get('max_data_staleness_seconds', 5)
        
        # Clock drift tracking
        self.last_ntp_check = None
        self.ntp_check_interval = self.config.get('ntp_check_interval', 300)  # 5 minutes
        
        logger.info("Survival Core initialized")
    
    def _init_security(self):
        """Initialize security components"""
        # Load encryption key with additional security measures
        key_file = Path(self.config.get('key_file', 'config/encryption.key'))
        key_rotation_days = self.config.get('security', {}).get('key_rotation_days', 30)
        
        try:
            if key_file.exists():
                # Check key file age for rotation
                key_age = datetime.now() - datetime.fromtimestamp(key_file.stat().st_mtime)
                if key_age.days >= key_rotation_days:
                    logger.info(f"Encryption key is {key_age.days} days old, rotating")
                    self._rotate_encryption_key(key_file)
                else:
                    # Load existing key with integrity check
                    with open(key_file, 'rb') as f:
                        key_data = f.read()
                        # Verify key format is valid
                        if len(key_data) != 44 or not key_data.endswith(b'='):
                            logger.warning("Encryption key appears to be tampered with, regenerating")
                            self._rotate_encryption_key(key_file)
                        else:
                            self.encryption_key = key_data
            else:
                # Generate new key
                logger.info("No encryption key found, generating new key")
                self._rotate_encryption_key(key_file)
            
            # Initialize cipher
            self.cipher = Fernet(self.encryption_key)
            
            # Load API keys
            self.api_keys = self._load_api_keys()
            
        except Exception as e:
            logger.error(f"Error initializing security components: {e}")
            # Generate emergency key if there's an issue
            self.encryption_key = Fernet.generate_key()
            self.cipher = Fernet(self.encryption_key)
            self.api_keys = {}
            
    def _rotate_encryption_key(self, key_file: Path):
        """Generate a new encryption key and re-encrypt any existing secrets"""
        # Generate new key
        new_key = Fernet.generate_key()
        
        # If we had an old key, re-encrypt secrets
        if hasattr(self, 'encryption_key') and hasattr(self, 'cipher'):
            old_cipher = self.cipher
            new_cipher = Fernet(new_key)
            
            # Re-encrypt API keys if they exist
            api_keys_file = Path(self.config.get('api_keys_file', 'config/api_keys.json'))
            if api_keys_file.exists():
                try:
                    # Load and decrypt with old key
                    with open(api_keys_file, 'r') as f:
                        encrypted_keys = json.load(f)
                    
                    # Re-encrypt with new key
                    for exchange, keys in encrypted_keys.items():
                        for key_name, encrypted_value in keys.items():
                            if encrypted_value:
                                # Decrypt with old key
                                decrypted = old_cipher.decrypt(encrypted_value.encode()).decode()
                                # Re-encrypt with new key
                                encrypted_keys[exchange][key_name] = new_cipher.encrypt(decrypted.encode()).decode()
                    
                    # Save re-encrypted keys
                    with open(api_keys_file, 'w') as f:
                        json.dump(encrypted_keys, f, indent=2)
                        
                    logger.info("Successfully re-encrypted API keys with new key")
                except Exception as e:
                    logger.error(f"Error re-encrypting API keys: {e}")
        
        # Save new key with secure permissions
        key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file, 'wb') as f:
            pass
        try:
            f.write(new_key)
        
        # Set permissions (on non-Windows systems)
            if os.name != 'nt':  # Not Windows
                os.chmod(key_file, 0o600)  # Read/write for owner only
        except Exception as e:
            logger.warning(f"Could not set secure permissions on key file: {e}")
        
        self.encryption_key = new_key
    
    def _init_database(self):
        """Initialize database with fallback"""
        try:
            from trading_bot.persistence.database_initializer import initialize_database_with_fallback
            self.time_series_db = initialize_database_with_fallback(self.config)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

        try:
            from trading_bot.persistence.database_initializer import InMemoryTimeSeriesDB
            self.time_series_db = InMemoryTimeSeriesDB(self.config)
    
        except Exception:
            pass
    def _init_broker_adapter(self):
        """Initialize broker adapter"""
        try:
            from trading_bot.brokers import MT5BrokerAdapter, MockBrokerAdapter
            
            broker_type = self.config.get('broker', {}).get('type', 'mock')
            
            if broker_type == 'mt5':
                self.broker_adapter = MT5BrokerAdapter(self.config.get('broker', {}))
                logger.info("MT5 broker adapter initialized")
            else:
                self.broker_adapter = MockBrokerAdapter(self.config.get('broker', {}))
                logger.info("Mock broker adapter initialized (paper trading)")
                
        except Exception as e:
            logger.error(f"Broker adapter initialization failed: {e}")

        try:
            from trading_bot.brokers import MockBrokerAdapter
            self.broker_adapter = MockBrokerAdapter(self.config)
    
        except Exception:
            pass
    def _init_execution_manager(self):
        """Initialize execution manager with lazy import"""
        try:
            from trading_bot.core.execution_manager import ExecutionManager
            self.execution = ExecutionManager(self.config.get('execution', {}))
            
            # Initialize fill tracker
            from trading_bot.execution.fill_tracker import FillTracker
            self.fill_tracker = FillTracker(self.broker_adapter, self.config.get('fill_tracker', {}))
            
            # Initialize position sizer
            from trading_bot.risk.position_sizer import PositionSizer
            self.position_sizer = PositionSizer(self.config.get('position_sizer', {}))
            
            logger.info("Execution manager and components initialized")
        except Exception as e:
            logger.error(f"Execution manager initialization failed: {e}")
            self.execution = None
            self.fill_tracker = None
            self.position_sizer = None
    
    def _init_components(self):
        """Initialize core components"""
        # Initialize database with fallback
        self._init_database()
        
        # Initialize broker adapter
        self._init_broker_adapter()
        
        # Initialize execution manager (lazy import)
        self._init_execution_manager()
        
        # Initialize other components
        # Market Data & Analysis (Brain)
        self.data_stream = MarketDataStream(self.config.get('data_stream', {}))
        self.analysis = AnalysisOrchestrator(self.config.get('analysis', {}))
        
        # Monitoring & Control (Eyes)
        self.monitoring = MonitoringSystem(self.config.get('monitoring', {}))
        
        try:
            # Initialize correlation manager with persistence
            from trading_bot.risk.correlation_persistence import EnhancedCorrelationManager
            self.correlation_manager = EnhancedCorrelationManager(self.config.get('correlation', {}))
            logger.info("Correlation manager with persistence initialized")
        except Exception as e:
            logger.warning(f"Correlation manager initialization failed: {e}")
            self.correlation_manager = None
    
    def _init_risk_limits(self):
        """Initialize risk management limits"""
        # Support both nested and top-level risk limit configuration
        risk_config = self.config.get('risk_limits', {})
        
        self.risk_limits = {
            'max_position_size': risk_config.get('max_position_size') or self.config.get('max_position_size', 0.02),  # 2% of account
            'max_leverage': risk_config.get('max_leverage') or self.config.get('max_leverage', 5.0),
            'max_daily_loss': risk_config.get('max_daily_loss') or self.config.get('max_daily_loss', 0.05),  # 5% of account
            'max_drawdown': risk_config.get('max_drawdown') or self.config.get('max_drawdown', 0.15),  # 15% drawdown
            'max_correlation': risk_config.get('max_correlation') or self.config.get('max_correlation', 0.7),
            'max_open_positions': risk_config.get('max_open_positions') or self.config.get('max_open_positions', 5),
            'min_free_margin': risk_config.get('min_free_margin') or self.config.get('min_free_margin', 0.3)  # 30% free margin
        }
    
    def _init_notifications(self):
        """Initialize notification system"""
        # Telegram bot
        telegram_token = self._decrypt_secret(
            self.config.get('telegram', {}).get('token', '')
        )
        if telegram_token:
            self.telegram_bot = telegram.Bot(token=telegram_token)
            self.telegram_chat_id = self.config.get('telegram', {}).get('chat_id')
        else:
            self.telegram_bot = None
            self.telegram_chat_id = None
        
        # Email settings
        self.email_settings = self.config.get('email', {})
        if self.email_settings.get('password'):
            self.email_settings['password'] = self._decrypt_secret(
                self.email_settings['password']
            )
    
    def _load_api_keys(self) -> Dict[str, Dict[str, str]]:
        """Load and decrypt API keys with validation"""
        api_keys_file = Path(self.config.get('api_keys_file', 'config/api_keys.json'))
        if not api_keys_file.exists():
            logger.info("No API keys file found")
            return {}
        try:
        
            with open(api_keys_file, 'r') as f:
                encrypted_keys = json.load(f)
            
            # Validate structure
            if not isinstance(encrypted_keys, dict):
                logger.error("API keys file has invalid structure (not a dict)")
                return {}
            
            decrypted_keys = {}
            for exchange, keys in encrypted_keys.items():
                # Validate exchange keys structure
                if not isinstance(keys, dict):
                    logger.warning(f"Invalid keys structure for exchange {exchange}, skipping")
                    continue
                
                # Ensure required keys exist
                if 'api_key' not in keys or 'api_secret' not in keys:
                    logger.warning(f"Missing api_key or api_secret for exchange {exchange}, skipping")
                    continue
                
                decrypted_keys[exchange] = {
                    'api_key': self._decrypt_secret(keys['api_key']),
                    'api_secret': self._decrypt_secret(keys['api_secret'])
                }
            
            logger.info(f"Loaded API keys for {len(decrypted_keys)} exchanges")
            return decrypted_keys
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API keys file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            return {}
    
    def _encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret value with error handling"""
        if not secret:
            return ''
        try:
            
            # Encrypt the secret
            encrypted_bytes = self.cipher.encrypt(secret.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Error encrypting secret: {e}")
            # Return a special marker to indicate encryption failure
            return ''
    
    def _decrypt_secret(self, encrypted: str) -> str:
        """Decrypt a secret value with error handling"""
        if not encrypted:
            return ''
        try:
            
            # Decrypt the secret
            decrypted_bytes = self.cipher.decrypt(encrypted.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting secret: {e}")
            # Return empty string on decryption failure
            # In a production system, you might want to raise an exception
            # or implement a more sophisticated error handling strategy
            return ''
    
    async def start(self):
        """Start the trading system"""
        if self.running:
            logger.warning("System already running")
            return
        
        logger.info("Starting trading system")
        self.running = True
        self.paused = False
        self.emergency_shutdown = False
        
        try:
            # Connect to market data
            await self.data_stream.connect()
            
            # Start monitoring
            self.monitoring.update_component_status('system', 'ok', {
                'state': 'running',
                'startup_time': datetime.now().isoformat()
            })
            
            # Start background tasks
            self.tasks = {
                'market_data': asyncio.create_task(self._market_data_loop()),
                'analysis': asyncio.create_task(self._analysis_loop()),
                'risk_check': asyncio.create_task(self._risk_check_loop()),
                'health_check': asyncio.create_task(self._health_check_loop())
            }
            
            # Send startup notification
            await self._send_notification(
                "System Started",
                "Trading system has started successfully",
                level="info"
            )
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop the trading system"""
        if not self.running:
            return
        
        logger.info("Stopping trading system")
        self.running = False
        
        try:
            # Cancel background tasks with timeout
            for name, task in self.tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        # Wait up to 5 seconds for graceful shutdown
                        await asyncio.wait_for(task, timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Task {name} did not complete within timeout")
                    except asyncio.CancelledError:
                        logger.info(f"Task {name} cancelled successfully")
                    except Exception as e:
                        logger.error(f"Error cancelling task {name}: {e}")
            
            # Close all positions if emergency shutdown
            if self.emergency_shutdown:
                await self.close_all_positions()
            
            # Disconnect from market data
            await self.data_stream.disconnect()
            
            # Update status
            self.monitoring.update_component_status('system', 'ok', {
                'state': 'stopped',
                'shutdown_time': datetime.now().isoformat()
            })
            
            # Send shutdown notification
            await self._send_notification(
                "System Stopped",
                "Trading system has been stopped",
                level="info"
            )
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
            raise
    
    async def emergency_stop(self):
        """Emergency stop with position closure"""
        logger.warning("Emergency stop initiated")
        self.emergency_shutdown = True
        
        await self._send_notification(
            "Emergency Shutdown",
            "Emergency shutdown initiated - closing all positions",
            level="critical"
        )
        
        await self.stop()
    
    async def pause(self):
        """Pause trading"""
        if not self.running:
            return
        
        logger.info("Pausing trading")
        self.paused = True
        
        self.monitoring.update_component_status('system', 'ok', {
            'state': 'paused',
            'pause_time': datetime.now().isoformat()
        })
        
        await self._send_notification(
            "Trading Paused",
            "Trading has been paused",
            level="warning"
        )
    
    async def resume(self):
        """Resume trading"""
        if not self.running:
            return
        
        logger.info("Resuming trading")
        self.paused = False
        
        self.monitoring.update_component_status('system', 'ok', {
            'state': 'running',
            'resume_time': datetime.now().isoformat()
        })
        
        await self._send_notification(
            "Trading Resumed",
            "Trading has been resumed",
            level="info"
        )
    
    async def _market_data_loop(self):
        """Background task for market data processing"""
        logger.info("Market data loop started")
        
        while self.running:
            try:
                # Skip if paused
                if self.paused:
                    await asyncio.sleep(1)
                    continue
                
                # Process market data
                for symbol in self.config.get('symbols', []):
                    # Get latest data
                    tick_data = await self.data_stream.get_latest_tick(symbol)
                    if tick_data:
                        # Check data staleness (kill-switch)
                        tick_timestamp = tick_data.get('timestamp', datetime.now())
                        if isinstance(tick_timestamp, str):
                            tick_timestamp = datetime.fromisoformat(tick_timestamp)
                        
                        tick_age = (datetime.now() - tick_timestamp).total_seconds()
                        
                        if tick_age > self.max_data_staleness:
                            logger.critical(
                                f"Stale data detected for {symbol}: {tick_age:.1f}s old "
                                f"(threshold: {self.max_data_staleness}s)"
                            )
                            
                            self.monitoring.update_component_status('market_data', 'critical', {
                                'staleness_seconds': tick_age,
                                'threshold': self.max_data_staleness,
                                'symbol': symbol
                            })
                            
                            await self._send_notification(
                                "Stale Data Kill-Switch Activated",
                                f"Trading paused: {symbol} data is {tick_age:.1f}s stale "
                                f"(threshold: {self.max_data_staleness}s)",
                                level="critical"
                            )
                            
                            await self.pause()
                            continue
                        
                        # Track last tick time
                        self.last_tick_time[symbol] = tick_timestamp
                        
                        # Store in time series database
                        await self.time_series_db.store(
                            symbol=symbol,
                            timeframe='tick',
                            data=pd.DataFrame([tick_data])
                        )
                        
                        # Update execution engine
                        await self.execution.update_market_price(
                            symbol=symbol,
                            price=tick_data['bid']
                        )
                
                # Update status
                self.monitoring.update_component_status('market_data', 'ok', {
                    'last_update': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in market data loop: {e}")
                
                # Record error
                self._record_error('market_data', str(e))
                
                self.monitoring.update_component_status('market_data', 'error', {
                    'error': str(e),
                    'last_update': datetime.now().isoformat()
                })
                
                await self._send_notification(
                    "Market Data Error",
                    f"Error in market data processing: {e}",
                    level="error"
                )
            
            await asyncio.sleep(1)
    
    async def _analysis_loop(self):
        """Background task for market analysis"""
        logger.info("Analysis loop started")
        
        while self.running:
            try:
                # Skip if paused
                if self.paused:
                    await asyncio.sleep(1)
                    continue
                
                # Process each symbol
                for symbol in self.config.get('symbols', []):
                    # Get OHLCV data
                    for timeframe in self.config.get('timeframes', ['M5']):
                        data = await self.data_stream.get_ohlcv(
                            symbol=symbol,
                            timeframe=timeframe,
                            limit=100
                        )
                        
                        if data is not None:
                            # Generate signals
                            signals = await self.analysis.generate_signals(
                                symbol=symbol,
                                timeframe=timeframe,
                                data=data
                            )
                            
                            # Process signals
                            for signal in signals:
                                if signal.confidence >= self.config.get('min_confidence', 70):
                                    await self._process_signal(signal)
                
                # Update status
                self.monitoring.update_component_status('analysis', 'ok', {
                    'last_update': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                
                # Record error
                self._record_error('analysis', str(e))
                
                self.monitoring.update_component_status('analysis', 'error', {
                    'error': str(e),
                    'last_update': datetime.now().isoformat()
                })
                
                await self._send_notification(
                    "Analysis Error",
                    f"Error in market analysis: {e}",
                    level="error"
                )
            
            await asyncio.sleep(self.config.get('analysis_interval', 5))
    
    async def _risk_check_loop(self):
        """Background task for risk monitoring"""
        logger.info("Risk check loop started")
        
        while self.running:
            try:
                # Get account status
                status = self.execution.get_portfolio_status()
                
                # Check daily loss limit (only trigger on losses, not profits)
                daily_pnl = status.get('daily_pnl', 0)
                max_daily_loss_amount = self.risk_limits['max_daily_loss'] * status['account_balance']
                
                if daily_pnl < -max_daily_loss_amount:
                    logger.warning(f"Daily loss limit exceeded: {daily_pnl:.2f} < -{max_daily_loss_amount:.2f}")
                    await self._send_notification(
                        "Daily Loss Limit Exceeded",
                        f"Daily P&L ({daily_pnl:.2f}) exceeds loss limit (-{max_daily_loss_amount:.2f})",
                        level="critical"
                    )
                    await self.pause()
                
                # Check drawdown
                if status['current_drawdown'] > self.risk_limits['max_drawdown']:
                    logger.warning("Maximum drawdown exceeded")
                    await self._send_notification(
                        "Max Drawdown Exceeded",
                        f"Current drawdown ({status['current_drawdown']:.2%}) exceeds limit",
                        level="critical"
                    )
                    await self.pause()
                
                # Check margin level
                if status.get('free_margin_ratio', 1) < self.risk_limits['min_free_margin']:
                    logger.warning("Low free margin")
                    await self._send_notification(
                        "Low Free Margin",
                        f"Free margin ratio ({status.get('free_margin_ratio', 0):.2%}) below minimum",
                        level="warning"
                    )
                
                # Update status
                self.monitoring.update_component_status('risk', 'ok', {
                    'last_update': datetime.now().isoformat(),
                    'daily_pnl': daily_pnl,
                    'drawdown': status['current_drawdown']
                })
                
            except Exception as e:
                logger.error(f"Error in risk check loop: {e}")
                
                # Record error
                self._record_error('risk', str(e))
                
                self.monitoring.update_component_status('risk', 'error', {
                    'error': str(e),
                    'last_update': datetime.now().isoformat()
                })
                
                await self._send_notification(
                    "Risk Check Error",
                    f"Error in risk monitoring: {e}",
                    level="error"
                )
            
            await asyncio.sleep(self.config.get('risk_check_interval', 60))
    
    async def _health_check_loop(self):
        """Background task for system health monitoring"""
        logger.info("Health check loop started")
        
        # Track consecutive failures
        consecutive_failures = 0
        max_consecutive_failures = self.config.get('monitoring', {}).get('max_consecutive_failures', 3)
        health_check_interval = self.config.get('monitoring', {}).get('health_check_interval', 30)
        
        while self.running:
            try:
                # Reset failure counter on successful execution
                if consecutive_failures > 0:
                    logger.info(f"Health check recovered after {consecutive_failures} consecutive failures")
                    consecutive_failures = 0
                
                # Check component status
                status = self.monitoring.get_system_status()
                critical_errors = []
                warning_errors = []
                
                # Check for component errors
                for component, info in status['components'].items():
                    if info['status'] == 'error':
                        error_msg = f"Error in {component}: {info.get('error', 'Unknown error')}"
                        logger.error(f"Component error: {component}")
                        critical_errors.append(error_msg)
                
                # Check API connectivity
                for exchange, keys in self.api_keys.items():
                    pass
                try:
                    try:
                        # Implement exchange-specific health check
                        # For now we're just checking if we have valid API keys
                        if not keys.get('api_key') or not keys.get('api_secret'):
                            warning_errors.append(f"Missing API credentials for {exchange}")
                    except Exception as e:
                        error_msg = f"Error connecting to {exchange}: {e}"
                        logger.error(f"API error for {exchange}: {e}")
                        warning_errors.append(error_msg)
                
                # Check clock drift (NTP)
                    if (self.last_ntp_check is None or 
                        (datetime.now() - self.last_ntp_check).total_seconds() >= self.ntp_check_interval):
                        
                        ntp_client = ntplib.NTPClient()
                        
                        try:
                            response = ntp_client.request('pool.ntp.org', timeout=5)
                            clock_offset_ms = response.offset * 1000
                            max_drift_ms = self.config.get('max_clock_drift_ms', 100)
                            
                            self.last_ntp_check = datetime.now()
                            
                            if abs(clock_offset_ms) > max_drift_ms:
                                critical_errors.append(
                                    f"Clock drift detected: {clock_offset_ms:.1f}ms "
                                    f"(threshold: {max_drift_ms}ms)"
                                )
                                logger.critical(f"Clock drift: {clock_offset_ms:.1f}ms")
                                
                                # Pause trading on significant clock drift
                                if not self.paused:
                                    await self.pause()
                                    await self._send_notification(
                                        "Clock Drift Detected",
                                        f"Trading paused: system clock drift {clock_offset_ms:.1f}ms "
                                        f"exceeds threshold ({max_drift_ms}ms)",
                                        level="critical"
                                    )
                        except Exception as ntp_error:
                            logger.warning(f"NTP check failed: {ntp_error}")
                except ImportError:
                    logger.debug("ntplib not available, skipping clock drift check")
                except Exception as e:
                    logger.warning(f"Clock drift check error: {e}")
                # Check system resources
                    import psutil
                    
                    # Check CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    cpu_threshold = self.config.get('monitoring', {}).get('thresholds', {}).get('cpu_usage', 80.0)
                    if cpu_percent > cpu_threshold:
                        warning_errors.append(f"High CPU usage: {cpu_percent:.1f}% (threshold: {cpu_threshold}%)") 
                    
                    # Check memory usage
                    memory = psutil.virtual_memory()
                    memory_percent = memory.percent
                    memory_threshold = self.config.get('monitoring', {}).get('thresholds', {}).get('memory_usage', 80.0)
                    if memory_percent > memory_threshold:
                        warning_errors.append(f"High memory usage: {memory_percent:.1f}% (threshold: {memory_threshold}%)") 
                    
                    # Check disk space (Windows-compatible)
                    if os.name == 'nt':  # Windows
                        disk_path = Path.home().anchor  # e.g., 'C:\\'
                    else:
                        disk_path = '/'
                    
                    disk = psutil.disk_usage(disk_path)
                    disk_percent = disk.percent
                    disk_threshold = self.config.get('monitoring', {}).get('thresholds', {}).get('disk_usage', 90.0)
                    if disk_percent > disk_threshold:
                        warning_errors.append(f"Low disk space on {disk_path}: {disk_percent:.1f}% used (threshold: {disk_threshold}%)")
                    
                except ImportError:
                    logger.warning("psutil not available, skipping system resource checks")
                except Exception as e:
                    logger.error(f"Error checking system resources: {e}")
                
                # Send notifications for critical errors
                if critical_errors:
                    await self._send_notification(
                        "Critical System Errors",
                        "\n- " + "\n- ".join(critical_errors),
                        level="critical"
                    )
                    
                    # Consider pausing trading if there are critical errors
                    if not self.paused and self.config.get('emergency', {}).get('pause_on_critical_error', True):
                        logger.warning("Pausing trading due to critical errors")
                        await self.pause()
                
                # Send notifications for warnings
                if warning_errors:
                    await self._send_notification(
                        "System Warnings",
                        "\n- " + "\n- ".join(warning_errors),
                        level="warning"
                    )
                
                # Update last health check
                self.last_health_check = datetime.now()
                
                # Update status
                self.monitoring.update_component_status('health', 'ok', {
                    'last_update': self.last_health_check.isoformat(),
                    'critical_errors': len(critical_errors),
                    'warnings': len(warning_errors)
                })
                
            except Exception as e:
                # Track consecutive failures
                consecutive_failures += 1
                
                logger.error(f"Error in health check loop: {e}")
                
                # Record error
                self._record_error('health', str(e))
                
                self.monitoring.update_component_status('health', 'error', {
                    'error': str(e),
                    'last_update': datetime.now().isoformat(),
                    'consecutive_failures': consecutive_failures
                })
                
                await self._send_notification(
                    "Health Check Error",
                    f"Error in system health monitoring: {e}\n\nConsecutive failures: {consecutive_failures}",
                    level="error"
                )
                
                # Emergency shutdown if too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.critical(f"Health check failed {consecutive_failures} times in a row, initiating emergency shutdown")
                    await self._send_notification(
                        "Emergency Shutdown",
                        f"Health check failed {consecutive_failures} times in a row, initiating emergency shutdown",
                        level="critical"
                    )
                    await self.emergency_stop()
                    break
            
            # Adjust sleep interval based on system health
            if consecutive_failures > 0:
                # Shorter interval when there are failures
                adjusted_interval = max(5, health_check_interval // 2)
                await asyncio.sleep(adjusted_interval)
            else:
                await asyncio.sleep(health_check_interval)
    
    async def _process_signal(self, signal):
        """Process a trading signal"""
        try:
            # Skip if paused
            if self.paused:
                return
            
            # Check risk limits
            status = self.execution.get_portfolio_status()
            
            # Check position count
            if len(status['positions']) >= self.risk_limits['max_open_positions']:
                logger.info("Maximum open positions reached")
                return
            
            # Calculate position size using execution manager's method
            # Extract stop loss from signal metadata or use default
            entry_price = signal.metadata.get('entry_price', signal.price)
            stop_loss = signal.metadata.get('stop_loss')
            
            if not stop_loss:
                # Default stop loss based on ATR or percentage
                atr = signal.metadata.get('atr', entry_price * 0.01)  # 1% default
                stop_loss = entry_price - atr if signal.direction > 0 else entry_price + atr
            
            # Use execution manager's position sizing
            position_calc = self.execution.calculate_position_size(
                symbol=signal.symbol,
                entry_price=entry_price,
                stop_loss=stop_loss,
                win_rate=signal.metadata.get('win_rate', 0.5),
                reward_risk_ratio=signal.metadata.get('reward_risk_ratio', 1.5)
            )
            
            # Place order with calculated size
            order = await self.execution.place_order(
                symbol=signal.symbol,
                order_type=OrderType.MARKET,
                side='buy' if signal.direction > 0 else 'sell',
                quantity=position_calc['recommended_size'],
                metadata={
                    'signal': {
                        'source': signal.source,
                        'confidence': signal.confidence,
                        'metadata': signal.metadata
                    },
                    'position_calc': position_calc
                }
            )
            
            if order:
                logger.info(f"Order placed: {order.id}")
                await self._send_notification(
                    "Order Placed",
                    f"New {order.side} order for {order.symbol}",
                    level="info"
                )
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            
            # Record error
            self._record_error('signal_processing', str(e))
            
            await self._send_notification(
                "Signal Processing Error",
                f"Error processing trading signal: {e}",
                level="error"
            )
    
    def _should_send_notification(self, title: str, level: str) -> bool:
        """Check if notification should be sent based on throttling rules"""
        notification_key = f"{level}:{title}"
        now = datetime.now()
        
        # Check recent notifications
        recent = self.notification_history[notification_key]
        
        if recent:
            last_sent = recent[-1]
            time_since_last = (now - last_sent).total_seconds()
            
            # Always send critical notifications
            if level == 'critical':
                self.notification_history[notification_key].append(now)
                return True
            
            # Throttle other notifications
            if time_since_last < self.notification_cooldown:
                logger.debug(f"Throttling notification '{title}' (sent {time_since_last:.0f}s ago)")
                return False
        
        # Record this notification
        self.notification_history[notification_key].append(now)
        return True
    
    async def _send_notification(self, title: str, message: str, level: str = "info"):
        """Send notification through configured channels with throttling"""
        try:
            # Check throttling
            if not self._should_send_notification(title, level):
                return
            
            # Telegram notification
            if self.telegram_bot and self.telegram_chat_id:
                emoji = {
                    "info": "ℹ️",
                    "warning": "⚠️",
                    "error": "❌",
                    "critical": "🚨"
                }.get(level, "ℹ️")
                
                try:
                    await self.telegram_bot.send_message(
                        chat_id=self.telegram_chat_id,
                        text=f"{emoji} {title}\n\n{message}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send Telegram notification: {e}")
            
            # Email notification for errors and critical alerts
            if self.email_settings and level in ['error', 'critical']:
                await self._send_email_notification(title, message, level)
            
            # Log notification
            log_func = {
                "info": logger.info,
                "warning": logger.warning,
                "error": logger.error,
                "critical": logger.critical
            }.get(level, logger.info)
            
            log_func(f"Notification - {title}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def _send_email_notification(self, title: str, message: str, level: str, max_retries: int = 3):
        """Send email notification with retry logic"""
        if not self.email_settings:
            return
        
        smtp_server = self.email_settings.get('smtp_server')
        smtp_port = self.email_settings.get('smtp_port', 587)
        sender_email = self.email_settings.get('sender_email')
        sender_password = self.email_settings.get('password')
        recipient_email = self.email_settings.get('recipient_email')
        
        if not all([smtp_server, sender_email, sender_password, recipient_email]):
            logger.warning("Email settings incomplete, skipping email notification")
            return
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"[{level.upper()}] Trading Bot Alert: {title}"
        
        body = f"""
        Trading Bot Alert
        
        Level: {level.upper()}
        Title: {title}
        Time: {datetime.now().isoformat()}
        
        Message:
        {message}
        
        ---
        This is an automated notification from your Elite Trading Bot.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send with retries and exponential backoff
        for attempt in range(max_retries):
            try:
                with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                
                logger.info(f"Email notification sent successfully to {recipient_email}")
                return
                
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.error(f"Failed to send email (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to send email notification after {max_retries} attempts")
    
    async def close_all_positions(self):
        """Close all open positions"""
        try:
            # Get open positions
            positions = self.execution.get_active_positions()
            
            for position in positions:
                # Close position
                result = await self.execution.close_position(position.symbol)
                
                if result:
                    logger.info(f"Closed position: {position.symbol}")
                    await self._send_notification(
                        "Position Closed",
                        f"Closed position for {position.symbol}",
                        level="info"
                    )
                else:
                    logger.error(f"Failed to close position: {position.symbol}")
                    await self._send_notification(
                        "Position Close Error",
                        f"Failed to close position for {position.symbol}",
                        level="error"
                    )
            
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
            
            # Record error
            self._record_error('position_close', str(e))
            
            await self._send_notification(
                "Position Close Error",
                f"Error closing all positions: {e}",
                level="error"
            )
    
    def _record_error(self, component: str, error_message: str):
        """Record an error for tracking"""
        error_record = {
            'component': component,
            'timestamp': datetime.now(),
            'error': error_message
        }
        self.errors.append(error_record)
        
        # Keep only last 100 errors to prevent memory issues
        if len(self.errors) > 100:
            self.errors = self.errors[-100:]
        
        logger.debug(f"Recorded error for {component}: {error_message}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'system': {
                'running': self.running,
                'paused': self.paused,
                'emergency_shutdown': self.emergency_shutdown,
                'last_health_check': self.last_health_check.isoformat(),
                'error_count': len(self.errors),
                'recent_errors': self.errors[-10:] if self.errors else []  # Last 10 errors
            },
            'data_quality': {
                'last_tick_times': {sym: ts.isoformat() for sym, ts in self.last_tick_time.items()},
                'max_staleness_seconds': self.max_data_staleness,
                'last_ntp_check': self.last_ntp_check.isoformat() if self.last_ntp_check else None
            },
            'monitoring': self.monitoring.get_system_status(),
            'portfolio': self.execution.get_portfolio_status(),
            'risk_limits': self.risk_limits
        }
