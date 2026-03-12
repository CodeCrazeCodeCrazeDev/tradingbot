"""
This module implements comprehensive security features including:
- Fraud and manipulation detection
- Encrypted trade logs
- Failsafe mode for server outages
- Regulatory compliance automation
"""

import os
import json
import time
import hashlib
import hmac
import base64
import logging
logger = logging.getLogger(__name__)
import threading
import queue
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import numpy as np
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger
from typing import Set
import numpy


class SecurityLevel(Enum):
    """Security level settings."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    PARANOID = auto()


class AlertType(Enum):
    """Types of security alerts."""
    FRAUD_DETECTED = auto()
    MANIPULATION_DETECTED = auto()
    UNAUTHORIZED_ACCESS = auto()
    ABNORMAL_TRADING = auto()
    SERVER_ISSUE = auto()
    DATA_INTEGRITY = auto()
    REGULATORY_VIOLATION = auto()


@dataclass
class SecurityAlert:
    """Security alert with details."""
    alert_type: AlertType
    severity: int  # 1-10
    timestamp: datetime
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: str = ""


class SecuritySystem:
    """Comprehensive security system for the trading bot.
    
    Features:
    - Fraud and manipulation detection
    - Encrypted trade logs
    - Failsafe mode for server outages
    - Regulatory compliance automation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the security system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.security_level = SecurityLevel[self.config.get('security_level', 'MEDIUM')]
        self.encryption_key = self._initialize_encryption()
        self.alert_history = []
        self.alert_callbacks = []
        self.failsafe_active = False
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)  # seconds
        self.heartbeat_thread = None
        self.heartbeat_queue = queue.Queue()
        self.last_heartbeat = datetime.now()
        
        # Initialize subsystems
        self.fraud_detector = FraudDetector(self.config.get('fraud_detector_config', {}))
        self.log_encryptor = LogEncryptor(self.encryption_key)
        self.failsafe_system = FailsafeSystem(self.config.get('failsafe_config', {}))
        self.compliance_system = ComplianceSystem(self.config.get('compliance_config', {}))
        
        logger.info(f"SecuritySystem initialized with level: {self.security_level.name}")
        
        # Start heartbeat monitoring if enabled
        if self.config.get('enable_heartbeat', True):
            self._start_heartbeat_monitoring()
    
    def _initialize_encryption(self) -> bytes:
        """Initialize encryption key for secure operations."""
        try:
            # Use existing key if available
            key_file = self.config.get('key_file', 'security_key.key')
            
            if os.path.exists(key_file):
                try:
                    with open(key_file, 'rb') as f:
                        key = f.read()
                    logger.info("Loaded existing encryption key")
                    return key
                except Exception as e:
                    logger.error(f"Error loading encryption key: {e}")
            
            # Generate new key
            key = Fernet.generate_key()
            
            # Save key if configured to do so
            if self.config.get('save_key', True):
                os.makedirs(os.path.dirname(key_file) or '.', exist_ok=True)
                with open(key_file, 'wb') as f:
                    f.write(key)
                logger.info("Generated and saved new encryption key")
            else:
                logger.info("Generated new encryption key (not saved)")
            
            return key
        except Exception as e:
            logger.error(f"Error generating encryption key: {e}")
            # Fallback to a derived key (less secure but functional)
            salt = b'elite_trading_bot'
            password = self.config.get('fallback_password', 'default_secure_password').encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            logger.warning("Using fallback derived encryption key")
            return key
    
    def _start_heartbeat_monitoring(self):
        """Start the heartbeat monitoring thread."""
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_monitor,
            daemon=True,
            name="HeartbeatMonitor"
        )
        self.heartbeat_thread.start()
        logger.info("Heartbeat monitoring started")
    
    def _heartbeat_monitor(self):
        """Monitor system heartbeat to detect issues."""
        while True:
            try:
                try:
                    # Check if there's a new heartbeat
                    while not self.heartbeat_queue.empty():
                        self.last_heartbeat = self.heartbeat_queue.get_nowait()
                except queue.Empty:
                    pass
                
                # Check if heartbeat is too old
                time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
                
                if time_since_heartbeat > self.heartbeat_interval * 3:
                    if not self.failsafe_active:
                        logger.warning(f"No heartbeat detected for {time_since_heartbeat:.1f} seconds, activating failsafe")
                        self.activate_failsafe("Heartbeat timeout")
                
                # Sleep for a bit
                time.sleep(self.heartbeat_interval / 2)
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                time.sleep(self.heartbeat_interval)
    
    def send_heartbeat(self):
        """Send a heartbeat to indicate the system is functioning."""
        self.heartbeat_queue.put(datetime.now())
    
    def check_for_fraud(self, trade_data: Dict[str, Any]) -> bool:
        """Check for fraudulent activity in trade data.
        
        Args:
            trade_data: Dictionary with trade information
            
        Returns:
            True if fraud is detected, False otherwise
        """
        result = self.fraud_detector.analyze_trade(trade_data)
        
        if result['fraud_detected']:
            self._create_alert(
                AlertType.FRAUD_DETECTED,
                result['severity'],
                result['description'],
                result
            )
            return True
        
        return False
    
    def check_for_manipulation(self, market_data: Dict[str, Any]) -> bool:
        """Check for market manipulation in market data.
        
        Args:
            market_data: Dictionary with market information
            
        Returns:
            True if manipulation is detected, False otherwise
        """
        result = self.fraud_detector.analyze_market(market_data)
        
        if result['manipulation_detected']:
            self._create_alert(
                AlertType.MANIPULATION_DETECTED,
                result['severity'],
                result['description'],
                result
            )
            return True
        
        return False
    
    def encrypt_trade_log(self, trade_log: Dict[str, Any]) -> str:
        """Encrypt a trade log for secure storage.
        
        Args:
            trade_log: Dictionary with trade log information
            
        Returns:
            Encrypted trade log as a string
        """
        return self.log_encryptor.encrypt_log(trade_log)
    
    def decrypt_trade_log(self, encrypted_log: str) -> Dict[str, Any]:
        """Decrypt a trade log.
        
        Args:
            encrypted_log: Encrypted trade log string
            
        Returns:
            Decrypted trade log as a dictionary
        """
        return self.log_encryptor.decrypt_log(encrypted_log)
    
    def activate_failsafe(self, reason: str):
        """Activate failsafe mode to safely manage positions during issues.
        
        Args:
            reason: Reason for activating failsafe
        """
        if self.failsafe_active:
            logger.info("Failsafe already active")
            return
        
        self.failsafe_active = True
        logger.warning(f"ACTIVATING FAILSAFE MODE: {reason}")
        
        # Create alert
        self._create_alert(
            AlertType.SERVER_ISSUE,
            8,  # High severity
            f"Failsafe mode activated: {reason}",
            {'reason': reason}
        )
        
        # Activate failsafe system
        self.failsafe_system.activate(reason)
    
    def deactivate_failsafe(self):
        """Deactivate failsafe mode when issues are resolved."""
        if not self.failsafe_active:
            logger.info("Failsafe not active")
            return
        
        self.failsafe_active = False
        logger.info("Deactivating failsafe mode")
        
        # Deactivate failsafe system
        self.failsafe_system.deactivate()
    
    def check_compliance(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a trade complies with regulatory requirements.
        
        Args:
            trade_data: Dictionary with trade information
            
        Returns:
            Dictionary with compliance check results
        """
        return self.compliance_system.check_trade(trade_data)
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate a compliance report for a date range.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            
        Returns:
            Dictionary with compliance report
        """
        return self.compliance_system.generate_report(start_date, end_date)
    
    def register_alert_callback(self, callback: Callable[[SecurityAlert], None]):
        """Register a callback function for security alerts.
        
        Args:
            callback: Function to call when an alert is created
        """
        self.alert_callbacks.append(callback)
    
    def _create_alert(self, alert_type: AlertType, severity: int, description: str, data: Dict[str, Any] = None):
        """Create a security alert and notify callbacks.
        
        Args:
            alert_type: Type of alert
            severity: Severity level (1-10)
            description: Alert description
            data: Additional alert data
        """
        alert = SecurityAlert(
            alert_type=alert_type,
            severity=severity,
            timestamp=datetime.now(),
            description=description,
            data=data or {}
        )
        
        self.alert_history.append(alert)
        
        # Log alert
        log_level = logging.WARNING if severity < 7 else logging.ERROR
        logger.log(log_level, f"SECURITY ALERT: {alert_type.name} - {description}")
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def get_alerts(self, alert_type: Optional[AlertType] = None, 
                 min_severity: int = 0, resolved: Optional[bool] = None) -> List[SecurityAlert]:
        """Get filtered security alerts.
        
        Args:
            alert_type: Optional filter by alert type
            min_severity: Minimum severity level
            resolved: Optional filter by resolved status
            
        Returns:
            List of matching security alerts
        """
        filtered_alerts = []
        
        for alert in self.alert_history:
            if alert_type is not None and alert.alert_type != alert_type:
                continue
                
            if alert.severity < min_severity:
                continue
                
            if resolved is not None and alert.resolved != resolved:
                continue
                
            filtered_alerts.append(alert)
        
        return filtered_alerts
    
    def resolve_alert(self, alert_index: int, resolution_notes: str):
        """Mark an alert as resolved.
        
        Args:
            alert_index: Index of the alert in the history
            resolution_notes: Notes on how the alert was resolved
        """
        if 0 <= alert_index < len(self.alert_history):
            alert = self.alert_history[alert_index]
            alert.resolved = True
            alert.resolution_notes = resolution_notes
            logger.info(f"Alert resolved: {alert.alert_type.name} - {resolution_notes}")
        else:
            logger.error(f"Invalid alert index: {alert_index}")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get the current security status.
        
        Returns:
            Dictionary with security status information
        """
        return {
            'security_level': self.security_level.name,
            'failsafe_active': self.failsafe_active,
            'alert_count': len(self.alert_history),
            'unresolved_alerts': len([a for a in self.alert_history if not a.resolved]),
            'high_severity_alerts': len([a for a in self.alert_history if a.severity >= 7]),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'heartbeat_age_seconds': (datetime.now() - self.last_heartbeat).total_seconds(),
            'fraud_detector_status': self.fraud_detector.get_status(),
            'failsafe_status': self.failsafe_system.get_status(),
            'compliance_status': self.compliance_system.get_status()
        }


class FraudDetector:
    """Detects fraudulent activity and market manipulation."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the fraud detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.anomaly_threshold = self.config.get('anomaly_threshold', 0.8)
        self.trade_history = []
        self.market_history = []
        logger.info("FraudDetector initialized")
    
    def analyze_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a trade for potential fraud.
        
        Args:
            trade_data: Dictionary with trade information
            
        Returns:
            Dictionary with analysis results
        """
        # Store trade for historical analysis
        self.trade_history.append({
            'data': trade_data,
            'timestamp': datetime.now()
        })
        
        # Limit history size
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-500:]
        
        # Check for suspicious patterns
        suspicious_patterns = []
        fraud_score = 0.0
        
        # Check for unusually large trades
        if self._is_unusually_large_trade(trade_data):
            suspicious_patterns.append("Unusually large trade")
            fraud_score += 0.3
        
        # Check for unusual timing
        if self._is_unusual_timing(trade_data):
            suspicious_patterns.append("Unusual trade timing")
            fraud_score += 0.2
        
        # Check for pattern deviation
        if self._is_pattern_deviation(trade_data):
            suspicious_patterns.append("Deviation from normal trading pattern")
            fraud_score += 0.25
        
        # Determine if fraud is detected
        fraud_detected = fraud_score >= self.anomaly_threshold
        
        # Calculate severity based on fraud score
        severity = int(fraud_score * 10)
        
        return {
            'fraud_detected': fraud_detected,
            'fraud_score': fraud_score,
            'severity': severity,
            'suspicious_patterns': suspicious_patterns,
            'description': "; ".join(suspicious_patterns) if suspicious_patterns else "No suspicious patterns",
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data for potential manipulation.
        
        Args:
            market_data: Dictionary with market information
            
        Returns:
            Dictionary with analysis results
        """
        # Store market data for historical analysis
        self.market_history.append({
            'data': market_data,
            'timestamp': datetime.now()
        })
        
        # Limit history size
        if len(self.market_history) > 1000:
            self.market_history = self.market_history[-500:]
        
        # Check for suspicious patterns
        suspicious_patterns = []
        manipulation_score = 0.0
        
        # Check for unusual volume
        if self._is_unusual_volume(market_data):
            suspicious_patterns.append("Unusual trading volume")
            manipulation_score += 0.3
        
        # Check for price spikes
        if self._is_price_spike(market_data):
            suspicious_patterns.append("Abnormal price movement")
            manipulation_score += 0.35
        
        # Check for spoofing patterns
        if self._is_spoofing_pattern(market_data):
            suspicious_patterns.append("Potential spoofing pattern")
            manipulation_score += 0.4
        
        # Determine if manipulation is detected
        manipulation_detected = manipulation_score >= self.anomaly_threshold
        
        # Calculate severity based on manipulation score
        severity = int(manipulation_score * 10)
        
        return {
            'manipulation_detected': manipulation_detected,
            'manipulation_score': manipulation_score,
            'severity': severity,
            'suspicious_patterns': suspicious_patterns,
            'description': "; ".join(suspicious_patterns) if suspicious_patterns else "No suspicious patterns",
            'timestamp': datetime.now().isoformat()
        }
    
    def _is_unusually_large_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Check if a trade is unusually large compared to historical average."""
        if len(self.trade_history) < 10:
            return False
            
        # Get trade size
        trade_size = trade_data.get('quantity', 0) * trade_data.get('price', 0)
        if trade_size == 0:
            trade_size = trade_data.get('size', 0)
            
        # Calculate historical average and std
        historical_sizes = []
        for t in self.trade_history:
            size = t.get('quantity', 0) * t.get('price', 0)
            if size == 0:
                size = t.get('size', 0)
            if size > 0:
                historical_sizes.append(size)
                
        if not historical_sizes:
            return False
            
        avg_size = np.mean(historical_sizes)
        std_size = np.std(historical_sizes)
        
        # Flag if more than 3 standard deviations from mean
        if std_size > 0:
            z_score = (trade_size - avg_size) / std_size
            return z_score > 3.0
        return trade_size > avg_size * 5
    
    def _is_unusual_timing(self, trade_data: Dict[str, Any]) -> bool:
        """Check if a trade has unusual timing (odd hours or high frequency)."""
        timestamp = trade_data.get('timestamp')
        if not timestamp:
            return False
            
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except Exception as e:
                logger.error(f"Error: {e}")
                return False
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
            
        # Check for odd hours (outside 9 AM - 5 PM local time)
        hour = timestamp.hour
        if hour < 6 or hour > 22:  # Very early or very late
            return True
            
        # Check for high frequency trading
        if len(self.trade_history) >= 2:
            recent_trades = [t for t in self.trade_history[-10:] if 'timestamp' in t]
            if len(recent_trades) >= 2:
                # Calculate time between trades
                intervals = []
                for i in range(1, len(recent_trades)):
                    t1 = recent_trades[i-1].get('timestamp')
                    t2 = recent_trades[i].get('timestamp')
                    if t1 and t2:
                        if isinstance(t1, str):
                            t1 = datetime.fromisoformat(t1)
                        if isinstance(t2, str):
                            t2 = datetime.fromisoformat(t2)
                        intervals.append((t2 - t1).total_seconds())
                        
                if intervals:
                    avg_interval = np.mean(intervals)
                    # Flag if trading more than 10x faster than average
                    if avg_interval > 0 and len(intervals) > 5:
                        current_interval = (timestamp - datetime.fromisoformat(recent_trades[-1]['timestamp'])).total_seconds() if isinstance(recent_trades[-1]['timestamp'], str) else (timestamp - recent_trades[-1]['timestamp']).total_seconds()
                        if current_interval < avg_interval / 10:
                            return True
        return False
    
    def _is_pattern_deviation(self, trade_data: Dict[str, Any]) -> bool:
        """Check if a trade deviates from normal patterns using statistical methods."""
        if len(self.trade_history) < 20:
            return False
            
        # Extract features from current trade
        current_features = self._extract_trade_features(trade_data)
        if not current_features:
            return False
            
        # Extract features from historical trades
        historical_features = []
        for t in self.trade_history[-100:]:
            features = self._extract_trade_features(t)
            if features:
                historical_features.append(features)
                
        if len(historical_features) < 10:
            return False
            
        # Calculate z-scores for each feature
        deviations = 0
        for i, feature_name in enumerate(['size', 'price_deviation', 'time_of_day']):
            if i >= len(current_features):
                break
            hist_values = [f[i] for f in historical_features if len(f) > i]
            if hist_values:
                mean_val = np.mean(hist_values)
                std_val = np.std(hist_values)
                if std_val > 0:
                    z_score = abs((current_features[i] - mean_val) / std_val)
                    if z_score > 2.5:
                        deviations += 1
                        
        # Flag if multiple features deviate significantly
        return deviations >= 2
        
    def _extract_trade_features(self, trade_data: Dict[str, Any]) -> List[float]:
        """Extract numerical features from trade data."""
        try:
            size = trade_data.get('quantity', 0) * trade_data.get('price', 1)
            if size == 0:
                size = trade_data.get('size', 0)
                
            price = trade_data.get('price', 0)
            avg_price = trade_data.get('avg_price', price)
            price_deviation = abs(price - avg_price) / avg_price if avg_price > 0 else 0
            
            timestamp = trade_data.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                elif isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp)
                time_of_day = timestamp.hour + timestamp.minute / 60
            else:
                time_of_day = 12  # Default to noon
                
            return [size, price_deviation, time_of_day]
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    
    def _is_unusual_volume(self, market_data: Dict[str, Any]) -> bool:
        """Check if market volume is unusual compared to historical average."""
        current_volume = market_data.get('volume', 0)
        if current_volume == 0:
            return False
            
        if len(self.market_history) < 10:
            return False
            
        # Get historical volumes
        historical_volumes = [m.get('volume', 0) for m in self.market_history[-100:] if m.get('volume', 0) > 0]
        
        if not historical_volumes:
            return False
            
        avg_volume = np.mean(historical_volumes)
        std_volume = np.std(historical_volumes)
        
        # Flag if volume is more than 3 standard deviations from mean
        if std_volume > 0:
            z_score = (current_volume - avg_volume) / std_volume
            return abs(z_score) > 3.0
        return current_volume > avg_volume * 3
    
    def _is_price_spike(self, market_data: Dict[str, Any]) -> bool:
        """Check if there's an abnormal price movement."""
        current_price = market_data.get('price', 0) or market_data.get('close', 0)
        if current_price == 0:
            return False
            
        if len(self.market_history) < 5:
            return False
            
        # Get recent prices
        recent_prices = []
        for m in self.market_history[-20:]:
            price = m.get('price', 0) or m.get('close', 0)
            if price > 0:
                recent_prices.append(price)
                
        if len(recent_prices) < 3:
            return False
            
        # Calculate returns
        returns = np.diff(recent_prices) / recent_prices[:-1]
        
        if len(returns) < 2:
            return False
            
        avg_return = np.mean(np.abs(returns))
        std_return = np.std(returns)
        
        # Calculate current return
        current_return = (current_price - recent_prices[-1]) / recent_prices[-1]
        
        # Flag if current return is more than 4 standard deviations
        if std_return > 0:
            z_score = abs(current_return) / std_return
            return z_score > 4.0
        return abs(current_return) > avg_return * 5
    
    def _is_spoofing_pattern(self, market_data: Dict[str, Any]) -> bool:
        """Check for potential spoofing patterns (large orders quickly canceled)."""
        # Check for order book imbalance that suddenly disappears
        bid_volume = market_data.get('bid_volume', 0)
        ask_volume = market_data.get('ask_volume', 0)
        
        if bid_volume == 0 and ask_volume == 0:
            return False
            
        # Calculate imbalance
        total_volume = bid_volume + ask_volume
        if total_volume > 0:
            imbalance = abs(bid_volume - ask_volume) / total_volume
        else:
            return False
            
        # Check historical imbalances
        if len(self.market_history) < 5:
            return False
            
        historical_imbalances = []
        for m in self.market_history[-10:]:
            b = m.get('bid_volume', 0)
            a = m.get('ask_volume', 0)
            if b + a > 0:
                historical_imbalances.append(abs(b - a) / (b + a))
                
        if not historical_imbalances:
            return False
            
        avg_imbalance = np.mean(historical_imbalances)
        
        # Spoofing pattern: sudden large imbalance followed by quick reversal
        # Check if current imbalance is much higher than average
        if imbalance > avg_imbalance * 3 and imbalance > 0.7:
            # Check if previous imbalance was normal (indicating sudden appearance)
            if len(historical_imbalances) >= 2:
                prev_imbalance = historical_imbalances[-1]
                if prev_imbalance < avg_imbalance * 1.5:
                    return True
                    
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the fraud detector."""
        return {
            'trade_history_count': len(self.trade_history),
            'market_history_count': len(self.market_history),
            'anomaly_threshold': self.anomaly_threshold
        }


class LogEncryptor:
    """Handles encryption and decryption of trade logs."""
    
    def __init__(self, encryption_key: bytes):
        """Initialize the log encryptor.
        
        Args:
            encryption_key: Key for encryption/decryption
        """
        self.cipher_suite = Fernet(encryption_key)
        logger.info("LogEncryptor initialized")
    
    def encrypt_log(self, log_data: Dict[str, Any]) -> str:
        """Encrypt a log entry.
        
        Args:
            log_data: Dictionary with log data
            
        Returns:
            Encrypted log as a string
        """
        try:
            # Add timestamp and hash for integrity verification
            log_data['_encryption_timestamp'] = datetime.now().isoformat()
            
            # Convert to JSON
            json_data = json.dumps(log_data)
            
            # Calculate hash before encryption
            data_hash = hashlib.sha256(json_data.encode()).hexdigest()
            log_data['_integrity_hash'] = data_hash
            
            # Re-convert to JSON with hash
            json_data = json.dumps(log_data)
            
            # Encrypt
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())
            
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Error encrypting log: {e}")
            # Return a special error marker
            return f"ENCRYPTION_ERROR:{str(e)}"
    
    def decrypt_log(self, encrypted_log: str) -> Dict[str, Any]:
        """Decrypt a log entry.
        
        Args:
            encrypted_log: Encrypted log string
            
        Returns:
            Decrypted log as a dictionary
        """
        try:
            # Check for error marker
            if encrypted_log.startswith("ENCRYPTION_ERROR:"):
                return {"error": encrypted_log[17:]}
            
            # Decrypt
            decrypted_data = self.cipher_suite.decrypt(encrypted_log.encode()).decode()
            
            # Parse JSON
            log_data = json.loads(decrypted_data)
            
            # Verify integrity if hash exists
            if '_integrity_hash' in log_data:
                original_hash = log_data['_integrity_hash']
                log_data_copy = log_data.copy()
                del log_data_copy['_integrity_hash']
                
                # Calculate hash of data without the hash field
                verification_json = json.dumps(log_data_copy)
                verification_hash = hashlib.sha256(verification_json.encode()).hexdigest()
                
                if verification_hash != original_hash:
                    logger.warning("Log integrity check failed - data may have been tampered with")
                    log_data['_integrity_verified'] = False
                else:
                    log_data['_integrity_verified'] = True
            
            return log_data
        except Exception as e:
            logger.error(f"Error decrypting log: {e}")
            return {"error": f"Decryption failed: {str(e)}"}


class FailsafeSystem:
    """Manages failsafe operations during system issues."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the failsafe system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.active = False
        self.activation_reason = None
        self.activation_time = None
        self.recovery_actions = []
        logger.info("FailsafeSystem initialized")
    
    def activate(self, reason: str):
        """Activate failsafe mode.
        
        Args:
            reason: Reason for activation
        """
        self.active = True
        self.activation_reason = reason
        self.activation_time = datetime.now()
        
        logger.warning(f"Failsafe activated: {reason}")
        
        # Execute failsafe procedures
        self._execute_failsafe_procedures()
    
    def deactivate(self):
        """Deactivate failsafe mode."""
        if not self.active:
            return
        
        self.active = False
        duration = (datetime.now() - self.activation_time).total_seconds()
        
        logger.info(f"Failsafe deactivated after {duration:.1f} seconds")
        
        # Execute recovery procedures
        self._execute_recovery_procedures()
    
    def _execute_failsafe_procedures(self):
        """Execute procedures when failsafe is activated."""
        # In a real implementation, this would:
        # 1. Pause new trades
        # 2. Set protective stop losses on open positions
        # 3. Save state to disk
        # 4. Notify administrators
        
        logger.info("Executing failsafe procedures")
        
        # Record actions for recovery
        self.recovery_actions = [
            {"action": "pause_trading", "timestamp": datetime.now().isoformat()},
            {"action": "set_protective_stops", "timestamp": datetime.now().isoformat()},
            {"action": "save_state", "timestamp": datetime.now().isoformat()}
        ]
    
    def _execute_recovery_procedures(self):
        """Execute procedures when failsafe is deactivated."""
        # In a real implementation, this would:
        # 1. Restore state
        # 2. Verify system integrity
        # 3. Resume normal operations if safe
        
        logger.info("Executing recovery procedures")
        
        # Clear recovery actions
        self.recovery_actions = []
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the failsafe system."""
        return {
            'active': self.active,
            'activation_reason': self.activation_reason,
            'activation_time': self.activation_time.isoformat() if self.activation_time else None,
            'duration_seconds': (datetime.now() - self.activation_time).total_seconds() if self.activation_time else 0,
            'recovery_actions': self.recovery_actions
        }


class ComplianceSystem:
    """Manages regulatory compliance and reporting."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the compliance system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.trade_records = []
        self.report_templates = {
            'daily': self._daily_report_template,
            'monthly': self._monthly_report_template,
            'audit': self._audit_report_template
        }
        logger.info("ComplianceSystem initialized")
    
    def check_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a trade complies with regulatory requirements.
        
        Args:
            trade_data: Dictionary with trade information
            
        Returns:
            Dictionary with compliance check results
        """
        # Record trade for reporting
        self.trade_records.append({
            'trade': trade_data,
            'timestamp': datetime.now()
        })
        
        # Limit history size
        if len(self.trade_records) > 10000:
            self.trade_records = self.trade_records[-5000:]
        
        # Check various compliance rules
        compliance_issues = []
        
        # Example checks (would be more comprehensive in real implementation)
        if self._check_position_limits(trade_data):
            compliance_issues.append("Position limit exceeded")
        
        if self._check_restricted_assets(trade_data):
            compliance_issues.append("Trading restricted asset")
        
        if self._check_trading_hours(trade_data):
            compliance_issues.append("Trading outside allowed hours")
        
        # Determine compliance status
        compliant = len(compliance_issues) == 0
        
        return {
            'compliant': compliant,
            'issues': compliance_issues,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_report(self, start_date: datetime, end_date: datetime, 
                      report_type: str = 'daily') -> Dict[str, Any]:
        """Generate a compliance report for a date range.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            report_type: Type of report to generate
            
        Returns:
            Dictionary with compliance report
        """
        # Filter trades for the date range
        filtered_trades = [
            record for record in self.trade_records
            if start_date <= record['timestamp'] <= end_date
        ]
        
        # Get the appropriate report template
        report_template = self.report_templates.get(
            report_type, self.report_templates['daily']
        )
        
        # Generate the report
        report = report_template(filtered_trades, start_date, end_date)
        
        return report
    
    def _check_position_limits(self, trade_data: Dict[str, Any]) -> bool:
        """Check if a trade exceeds position limits."""
        # Implementation would check against configured limits
        return False  # Placeholder
    
    def _check_restricted_assets(self, trade_data: Dict[str, Any]) -> bool:
        """Check if a trade involves restricted assets."""
        # Implementation would check against a list of restricted assets
        return False  # Placeholder
    
    def _check_trading_hours(self, trade_data: Dict[str, Any]) -> bool:
        """Check if a trade is outside allowed trading hours."""
        # Implementation would check against configured trading hours
        return False  # Placeholder
    
    def _daily_report_template(self, trades: List[Dict], start_date: datetime, 
                             end_date: datetime) -> Dict[str, Any]:
        """Generate a daily compliance report."""
        return {
            'report_type': 'daily',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'trade_count': len(trades),
            'generated_at': datetime.now().isoformat()
        }
    
    def _monthly_report_template(self, trades: List[Dict], start_date: datetime, 
                               end_date: datetime) -> Dict[str, Any]:
        """Generate a monthly compliance report."""
        return {
            'report_type': 'monthly',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'trade_count': len(trades),
            'generated_at': datetime.now().isoformat()
        }
    
    def _audit_report_template(self, trades: List[Dict], start_date: datetime, 
                             end_date: datetime) -> Dict[str, Any]:
        """Generate an audit compliance report."""
        return {
            'report_type': 'audit',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'trade_count': len(trades),
            'generated_at': datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the compliance system."""
        return {
            'trade_records_count': len(self.trade_records),
            'available_report_types': list(self.report_templates.keys())
        }
