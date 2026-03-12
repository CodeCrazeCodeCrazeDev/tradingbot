"""
Enhanced Security System

This module implements enhanced security features for the Elite Trading Bot,
including two-factor authentication, API key rotation, and intrusion detection.
"""

import os
import time
import json
import hmac
import base64
import hashlib
import logging
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    pyotp = None
    PYOTP_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    qrcode = None
    QRCODE_AVAILABLE = False

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Set


class EnhancedSecurity:
    """Enhanced security system for the Elite Trading Bot"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize enhanced security system"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.security_config = config.get('security', {})
        
        # Initialize encryption
        self._init_encryption()
        
        # Initialize 2FA
        self.totp_secrets = {}
        self._load_totp_secrets()
        
        # Initialize API key management
        self.api_keys = {}
        self._load_api_keys()
        
        # Initialize intrusion detection
        self.access_log = []
        self.suspicious_activity = []
        self.ip_blacklist = set()
        self._load_security_data()
        
        # Initialize rate limiting
        self.request_counts = {}
        self.rate_limits = self.security_config.get('rate_limits', {
            'max_requests_per_second': 10,
            'max_orders_per_minute': 30
        })
    
    def _init_encryption(self):
        """Initialize encryption for secure data storage"""
        key_file = self.security_config.get('key_file')
        
        if key_file and os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            # Generate a new key
            self.key = Fernet.generate_key()
            
            # Save the key
            if key_file:
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                with open(key_file, 'wb') as f:
                    f.write(self.key)
        
        self.cipher = Fernet(self.key)
    
    def _load_totp_secrets(self):
        """Load TOTP secrets from secure storage"""
        totp_file = self.security_config.get('totp_secrets_file')
        
        if totp_file and os.path.exists(totp_file):
            try:
                with open(totp_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = self.cipher.decrypt(encrypted_data)
                self.totp_secrets = json.loads(decrypted_data.decode())
                
                self.logger.info("TOTP secrets loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading TOTP secrets: {e}")
                self.totp_secrets = {}
    
    def _save_totp_secrets(self):
        """Save TOTP secrets to secure storage"""
        totp_file = self.security_config.get('totp_secrets_file')
        
        if totp_file:
            try:
                # Encrypt data
                encrypted_data = self.cipher.encrypt(json.dumps(self.totp_secrets).encode())
                
                # Save to file
                os.makedirs(os.path.dirname(totp_file), exist_ok=True)
                with open(totp_file, 'wb') as f:
                    f.write(encrypted_data)
                
                self.logger.info("TOTP secrets saved successfully")
            except Exception as e:
                self.logger.error(f"Error saving TOTP secrets: {e}")
    
    def _load_api_keys(self):
        """Load API keys from secure storage"""
        api_keys_file = self.security_config.get('api_keys_file')
        
        if api_keys_file and os.path.exists(api_keys_file):
            try:
                with open(api_keys_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = self.cipher.decrypt(encrypted_data)
                self.api_keys = json.loads(decrypted_data.decode())
                
                self.logger.info("API keys loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading API keys: {e}")
                self.api_keys = {}
    
    def _save_api_keys(self):
        """Save API keys to secure storage"""
        api_keys_file = self.security_config.get('api_keys_file')
        
        if api_keys_file:
            try:
                # Encrypt data
                encrypted_data = self.cipher.encrypt(json.dumps(self.api_keys).encode())
                
                # Save to file
                os.makedirs(os.path.dirname(api_keys_file), exist_ok=True)
                with open(api_keys_file, 'wb') as f:
                    f.write(encrypted_data)
                
                self.logger.info("API keys saved successfully")
            except Exception as e:
                self.logger.error(f"Error saving API keys: {e}")
    
    def _load_security_data(self):
        """Load security data from secure storage"""
        security_data_file = self.security_config.get('security_data_file')
        
        if security_data_file and os.path.exists(security_data_file):
            try:
                with open(security_data_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = self.cipher.decrypt(encrypted_data)
                security_data = json.loads(decrypted_data.decode())
                
                self.ip_blacklist = set(security_data.get('ip_blacklist', []))
                
                self.logger.info("Security data loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading security data: {e}")
    
    def _save_security_data(self):
        """Save security data to secure storage"""
        security_data_file = self.security_config.get('security_data_file')
        
        if security_data_file:
            try:
                # Prepare data
                security_data = {
                    'ip_blacklist': list(self.ip_blacklist),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Encrypt data
                encrypted_data = self.cipher.encrypt(json.dumps(security_data).encode())
                
                # Save to file
                os.makedirs(os.path.dirname(security_data_file), exist_ok=True)
                with open(security_data_file, 'wb') as f:
                    f.write(encrypted_data)
                
                self.logger.info("Security data saved successfully")
            except Exception as e:
                self.logger.error(f"Error saving security data: {e}")
    
    async def setup_two_factor_auth(self, user_id: str) -> Dict[str, Any]:
        """Set up two-factor authentication for a user"""
        try:
            # Generate a random secret key
            secret = pyotp.random_base32()
            
            # Create a TOTP object
            totp = pyotp.TOTP(secret)
            
            # Generate a QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # Add data to QR code
            provisioning_uri = totp.provisioning_uri(
                name=f"EliteTradingBot:{user_id}",
                issuer_name="EliteTradingBot"
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Save the secret
            self.totp_secrets[user_id] = {
                'secret': secret,
                'created_at': datetime.now().isoformat(),
                'last_used': None,
                'enabled': False
            }
            
            # Save TOTP secrets
            self._save_totp_secrets()
            
            # Return setup information
            return {
                'secret': secret,
                'provisioning_uri': provisioning_uri,
                'qr_code': qr.make_image(fill_color="black", back_color="white")
            }
            
        except Exception as e:
            self.logger.exception(f"Error setting up 2FA: {e}")
            return {'error': str(e)}
    
    def verify_two_factor_auth(self, user_id: str, token: str) -> bool:
        """Verify a two-factor authentication token"""
        try:
            # Check if user has 2FA set up
            if user_id not in self.totp_secrets:
                self.logger.warning(f"2FA not set up for user {user_id}")
                return False
            
            # Get user's secret
            user_secret = self.totp_secrets[user_id]
            
            # Create a TOTP object
            totp = pyotp.TOTP(user_secret['secret'])
            
            # Verify token
            is_valid = totp.verify(token)
            
            if is_valid:
                # Update last used timestamp
                self.totp_secrets[user_id]['last_used'] = datetime.now().isoformat()
                self._save_totp_secrets()
            else:
                # Log failed attempt
                self.logger.warning(f"Failed 2FA attempt for user {user_id}")
                self._log_security_event('failed_2fa', {'user_id': user_id})
            
            return is_valid
            
        except Exception as e:
            self.logger.exception(f"Error verifying 2FA: {e}")
            return False
    
    def enable_two_factor_auth(self, user_id: str) -> bool:
        """Enable two-factor authentication for a user"""
        try:
            # Check if user has 2FA set up
            if user_id not in self.totp_secrets:
                self.logger.warning(f"2FA not set up for user {user_id}")
                return False
            
            # Enable 2FA
            self.totp_secrets[user_id]['enabled'] = True
            self._save_totp_secrets()
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error enabling 2FA: {e}")
            return False
    
    def disable_two_factor_auth(self, user_id: str) -> bool:
        """Disable two-factor authentication for a user"""
        try:
            # Check if user has 2FA set up
            if user_id not in self.totp_secrets:
                self.logger.warning(f"2FA not set up for user {user_id}")
                return False
            
            # Disable 2FA
            self.totp_secrets[user_id]['enabled'] = False
            self._save_totp_secrets()
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error disabling 2FA: {e}")
            return False
    
    async def rotate_api_key(self, service: str) -> Dict[str, Any]:
        """Rotate API key for a service"""
        try:
            # Check if service exists
            if service not in self.api_keys:
                self.logger.warning(f"Service {service} not found in API keys")
                return {'error': f"Service {service} not found"}
            
            # Get current key info
            current_key = self.api_keys[service]
            
            # Generate new API key
            new_api_key = secrets.token_hex(32)
            new_api_secret = secrets.token_hex(32)
            
            # Update key info
            self.api_keys[service] = {
                'api_key': new_api_key,
                'api_secret': new_api_secret,
                'created_at': datetime.now().isoformat(),
                'last_rotated': datetime.now().isoformat(),
                'previous_key': current_key.get('api_key'),
                'previous_secret': current_key.get('api_secret'),
                'previous_expiry': (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            # Save API keys
            self._save_api_keys()
            
            # Log key rotation
            self.logger.info(f"API key rotated for service {service}")
            self._log_security_event('api_key_rotation', {'service': service})
            
            return {
                'service': service,
                'api_key': new_api_key,
                'api_secret': new_api_secret,
                'previous_expiry': self.api_keys[service]['previous_expiry']
            }
            
        except Exception as e:
            self.logger.exception(f"Error rotating API key: {e}")
            return {'error': str(e)}
    
    def get_api_key(self, service: str) -> Dict[str, Any]:
        """Get API key for a service"""
        try:
            # Check if service exists
            if service not in self.api_keys:
                self.logger.warning(f"Service {service} not found in API keys")
                return {'error': f"Service {service} not found"}
            
            # Get key info
            key_info = self.api_keys[service]
            
            return {
                'service': service,
                'api_key': key_info['api_key'],
                'api_secret': key_info['api_secret'],
                'created_at': key_info['created_at'],
                'last_rotated': key_info.get('last_rotated')
            }
            
        except Exception as e:
            self.logger.exception(f"Error getting API key: {e}")
            return {'error': str(e)}
    
    def add_api_key(self, service: str, api_key: str, api_secret: str) -> bool:
        """Add a new API key for a service"""
        try:
            # Add key info
            self.api_keys[service] = {
                'api_key': api_key,
                'api_secret': api_secret,
                'created_at': datetime.now().isoformat()
            }
            
            # Save API keys
            self._save_api_keys()
            
            # Log key addition
            self.logger.info(f"API key added for service {service}")
            self._log_security_event('api_key_added', {'service': service})
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error adding API key: {e}")
            return False
    
    def remove_api_key(self, service: str) -> bool:
        """Remove API key for a service"""
        try:
            # Check if service exists
            if service not in self.api_keys:
                self.logger.warning(f"Service {service} not found in API keys")
                return False
            
            # Remove key
            del self.api_keys[service]
            
            # Save API keys
            self._save_api_keys()
            
            # Log key removal
            self.logger.info(f"API key removed for service {service}")
            self._log_security_event('api_key_removed', {'service': service})
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error removing API key: {e}")
            return False
    
    def check_rate_limit(self, request_type: str, client_id: str) -> bool:
        """Check if a request exceeds rate limits"""
        try:
            current_time = time.time()
            
            # Initialize request counts if needed
            if client_id not in self.request_counts:
                self.request_counts[client_id] = {}
            
            if request_type not in self.request_counts[client_id]:
                self.request_counts[client_id][request_type] = []
            
            # Clean up old requests
            if request_type == 'order':
                # Keep requests from the last minute
                cutoff = current_time - 60
                max_requests = self.rate_limits.get('max_orders_per_minute', 30)
            else:
                # Keep requests from the last second
                cutoff = current_time - 1
                max_requests = self.rate_limits.get('max_requests_per_second', 10)
            
            # Remove old requests
            self.request_counts[client_id][request_type] = [
                t for t in self.request_counts[client_id][request_type] if t > cutoff
            ]
            
            # Check if limit exceeded
            if len(self.request_counts[client_id][request_type]) >= max_requests:
                self.logger.warning(f"Rate limit exceeded for {client_id}: {request_type}")
                self._log_security_event('rate_limit_exceeded', {
                    'client_id': client_id,
                    'request_type': request_type,
                    'count': len(self.request_counts[client_id][request_type])
                })
                return False
            
            # Add current request
            self.request_counts[client_id][request_type].append(current_time)
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error checking rate limit: {e}")
            return True  # Allow request on error
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log a security event"""
        try:
            # Create event
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'details': details
            }
            
            # Add to access log
            self.access_log.append(event)
            
            # Check for suspicious activity
            if event_type in ['failed_2fa', 'rate_limit_exceeded', 'unauthorized_access']:
                self.suspicious_activity.append(event)
                
                # Check if IP should be blacklisted
                if 'ip_address' in details:
                    ip = details['ip_address']
                    
                    # Count recent events from this IP
                    recent_events = [
                        e for e in self.suspicious_activity
                        if e['details'].get('ip_address') == ip
                        and datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(hours=1)
                    ]
                    
                    # Blacklist IP if too many suspicious events
                    if len(recent_events) >= 5:
                        self.ip_blacklist.add(ip)
                        self.logger.warning(f"IP {ip} blacklisted due to suspicious activity")
                        self._save_security_data()
            
            # Trim access log if too large
            if len(self.access_log) > 1000:
                self.access_log = self.access_log[-1000:]
            
            # Trim suspicious activity log if too large
            if len(self.suspicious_activity) > 500:
                self.suspicious_activity = self.suspicious_activity[-500:]
            
        except Exception as e:
            self.logger.exception(f"Error logging security event: {e}")
    
    def is_ip_blacklisted(self, ip_address: str) -> bool:
        """Check if an IP address is blacklisted"""
        return ip_address in self.ip_blacklist
    
    def remove_from_blacklist(self, ip_address: str) -> bool:
        """Remove an IP address from the blacklist"""
        try:
            if ip_address in self.ip_blacklist:
                self.ip_blacklist.remove(ip_address)
                self._save_security_data()
                self.logger.info(f"IP {ip_address} removed from blacklist")
                return True
            return False
        except Exception as e:
            self.logger.exception(f"Error removing IP from blacklist: {e}")
            return False
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get a security report"""
        try:
            # Count events by type
            event_counts = {}
            for event in self.access_log:
                event_type = event['event_type']
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Count suspicious events by type
            suspicious_counts = {}
            for event in self.suspicious_activity:
                event_type = event['event_type']
                suspicious_counts[event_type] = suspicious_counts.get(event_type, 0) + 1
            
            # Generate report
            report = {
                'timestamp': datetime.now().isoformat(),
                'event_counts': event_counts,
                'suspicious_counts': suspicious_counts,
                'blacklisted_ips': len(self.ip_blacklist),
                'api_keys': len(self.api_keys),
                'totp_users': len(self.totp_secrets)
            }
            
            return report
            
        except Exception as e:
            self.logger.exception(f"Error generating security report: {e}")
            return {'error': str(e)}
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a value using Fernet"""
        if not value:
            return value
        try:
        
            encrypted = self.cipher.encrypt(value.encode())
            return encrypted.decode()
        except Exception as e:
            self.logger.exception(f"Error encrypting value: {e}")
            return value
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a value using Fernet"""
        if not encrypted_value:
            return encrypted_value
        try:
        
            decrypted = self.cipher.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            self.logger.exception(f"Error decrypting value: {e}")
            return encrypted_value
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure random password"""
        if length < 8:
            length = 8  # Minimum length for security
        
        # Define character sets
        lowercase = 'abcdefghijklmnopqrstuvwxyz'
        uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        special = '!@#$%^&*()-_=+[]{}|;:,.<>?'
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest with random characters
        all_chars = lowercase + uppercase + digits + special
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """Hash a password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)
        
        # Create KDF
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        
        # Hash password
        key = base64.b64encode(kdf.derive(password.encode()))
        
        return key.decode(), salt
    
    def verify_password(self, password: str, hashed_password: str, salt: bytes) -> bool:
        """Verify a password against a hash"""
        # Hash the password with the same salt
        new_hash, _ = self.hash_password(password, salt)
        
        # Compare hashes
        return new_hash == hashed_password
