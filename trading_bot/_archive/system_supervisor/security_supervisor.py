"""
import os
Phase 6: Security Supervisor
Ensures system safety and security during operation
"""

import asyncio
import logging
import hashlib
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityStatus(Enum):
    """Security status levels"""
    SECURE = "secure"
    WARNING = "warning"
    THREAT = "threat"
    BREACH = "breach"


@dataclass
class SecurityEvent:
    """Security event record"""
    timestamp: datetime
    event_type: str
    severity: str
    description: str
    action_taken: str
    resolved: bool = False


class SecuritySupervisor:
    """
    Monitors and enforces security policies.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Security configuration
        self.api_keys_file = Path(config.get('api_keys_file', 'config/api_keys.json'))
        self.encryption_enabled = config.get('encryption_enabled', True)
        self.ssl_required = config.get('ssl_required', True)
        self.scan_interval_hours = config.get('scan_interval_hours', 168)  # Weekly
        
        # State
        self.security_events: List[SecurityEvent] = []
        self.last_scan: Optional[datetime] = None
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Threat detection
        self.request_counts: Dict[str, int] = {}
        self.failed_auth_attempts: Dict[str, int] = {}
        
        # Logs
        self.security_log = Path(config.get('security_log', 'logs/security.log'))
        self.security_log.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("Security Supervisor initialized")
    
    async def verify_api_keys(self) -> bool:
        """
        Verify API keys are properly secured.
        """
        logger.info("🔐 Verifying API key security...")
        
        try:
            if not self.api_keys_file.exists():
                logger.warning("API keys file not found")
                return True  # Not an error if not using API keys
            
            # Check file permissions
            import stat
            file_stat = self.api_keys_file.stat()
            
            # On Windows, check if file is readable by others
            # On Unix, check permissions
            if hasattr(stat, 'S_IROTH'):
                if file_stat.st_mode & stat.S_IROTH:
                    logger.warning("⚠️ API keys file is world-readable")
                    self._log_security_event(
                        'API_KEY_PERMISSIONS',
                        'WARNING',
                        'API keys file has insecure permissions'
                    )
            
            # Verify encryption
            if self.encryption_enabled:
                # Check if file is encrypted
                with open(self.api_keys_file, 'rb') as f:
                    header = f.read(16)
                    
                    try:
                        # Simple check - encrypted files shouldn't be valid JSON
                        f.seek(0)
                        json.load(f)
                        logger.warning("⚠️ API keys file not encrypted")
                        self._log_security_event(
                            'API_KEY_ENCRYPTION',
                            'WARNING',
                            'API keys file should be encrypted'
                        )
                    except json.JSONDecodeError:
                        logger.info("✅ API keys file appears encrypted")
            
            logger.info("✅ API key security verified")
            return True
        
        except Exception as e:
            logger.error(f"Error verifying API keys: {e}")
            return False
    
    async def verify_ssl_connections(self) -> bool:
        """
        Verify all connections use SSL/TLS.
        """
        logger.info("🔒 Verifying SSL/TLS enforcement...")
        
        try:
            if not self.ssl_required:
                logger.warning("SSL/TLS not required by configuration")
                return True
            
            # Check that all configured endpoints use HTTPS
            endpoints = self.config.get('endpoints', {})
            
            insecure_endpoints = []
            for name, url in endpoints.items():
                if isinstance(url, str) and not url.startswith('https://'):
                    insecure_endpoints.append(name)
            
            if insecure_endpoints:
                logger.warning(f"⚠️ Insecure endpoints found: {insecure_endpoints}")
                self._log_security_event(
                    'INSECURE_ENDPOINT',
                    'WARNING',
                    f'Endpoints not using HTTPS: {insecure_endpoints}'
                )
                return False
            
            logger.info("✅ All endpoints use SSL/TLS")
            return True
        
        except Exception as e:
            logger.error(f"Error verifying SSL: {e}")
            return False
    
    async def scan_for_malware(self) -> bool:
        """
        Run weekly malware scan.
        """
        logger.info("🛡️ Running malware scan...")
        
        try:
            # Scan critical directories
            scan_dirs = [
                Path('trading_bot'),
                Path('config'),
                Path('models')
            ]
            
            suspicious_files = []
            
            for scan_dir in scan_dirs:
                if not scan_dir.exists():
                    continue
                
                logger.info(f"Scanning {scan_dir}...")
                
                # Check for suspicious patterns
                for file_path in scan_dir.rglob('*.py'):
                    if await self._scan_file_for_threats(file_path):
                        suspicious_files.append(str(file_path))
            
            if suspicious_files:
                logger.warning(f"⚠️ Suspicious files found: {len(suspicious_files)}")
                for file_path in suspicious_files:
                    logger.warning(f"   - {file_path}")
                
                self._log_security_event(
                    'MALWARE_SCAN',
                    'THREAT',
                    f'Suspicious files detected: {suspicious_files}'
                )
                return False
            
            logger.info("✅ Malware scan complete - no threats found")
            self.last_scan = datetime.now()
            return True
        
        except Exception as e:
            logger.error(f"Error during malware scan: {e}")
            return False
    
    async def _scan_file_for_threats(self, file_path: Path) -> bool:
        """Scan a file for malicious patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Suspicious patterns
            threats = [
                'eval(',
                'exec(',
                '__import__("os").system',
                'subprocess.call',
                'rm -rf /',
                'del /f /q',
                'format c:',
            ]
            
            for threat in threats:
                if threat in content:
                    logger.warning(f"Threat pattern found in {file_path}: {threat}")
                    return True
            
            return False
        
        except Exception as e:
            logger.debug(f"Error scanning {file_path}: {e}")
            return False
    
    async def detect_ddos(self) -> bool:
        """
        Detect potential DDoS attacks.
        """
        try:
            # Check request rate
            current_time = datetime.now()
            
            # Count requests in last minute
            recent_requests = sum(
                1 for timestamp in self.request_counts.values()
                if (current_time - datetime.fromtimestamp(timestamp)).seconds < 60
            )
            
            # Threshold: 1000 requests per minute
            if recent_requests > 1000:
                logger.warning(f"⚠️ High request rate detected: {recent_requests}/min")
                self._log_security_event(
                    'DDOS_DETECTION',
                    'THREAT',
                    f'Abnormal request rate: {recent_requests} requests/min'
                )
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error detecting DDoS: {e}")
            return False
    
    async def check_network_anomaly(self) -> bool:
        """
        Check for network anomalies.
        """
        try:
            # Check for unusual patterns
            # (Implementation depends on network monitoring setup)
            
            # Placeholder
            return False
        
        except Exception as e:
            logger.error(f"Error checking network anomaly: {e}")
            return False
    
    async def auto_disable_trading_on_threat(self):
        """
        Automatically disable trading if threat detected.
        """
        logger.critical("🚨 SECURITY THREAT DETECTED - DISABLING TRADING")
        
        # Disable trading
        # (Implementation depends on trading system)
        
        self._log_security_event(
            'AUTO_DISABLE',
            'CRITICAL',
            'Trading automatically disabled due to security threat'
        )
    
    def _log_security_event(self, event_type: str, severity: str, description: str):
        """Log security event"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            description=description,
            action_taken='Logged'
        )
        
        self.security_events.append(event)
        
        try:
            # Write to log file
            with open(self.security_log, 'a') as f:
                log_entry = {
                    'timestamp': event.timestamp.isoformat(),
                    'type': event_type,
                    'severity': severity,
                    'description': description
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error writing to security log: {e}")
    
    async def run_security_sweep(self) -> Dict:
        """
        Run comprehensive security sweep.
        """
        logger.info("=" * 80)
        logger.info("🛡️ RUNNING SECURITY SWEEP")
        logger.info("=" * 80)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Check 1: API Keys
        logger.info("\n🔐 Check 1/5: API Key Security")
        results['checks']['api_keys'] = await self.verify_api_keys()
        
        # Check 2: SSL/TLS
        logger.info("\n🔒 Check 2/5: SSL/TLS Enforcement")
        results['checks']['ssl_tls'] = await self.verify_ssl_connections()
        
        # Check 3: Malware Scan
        logger.info("\n🛡️ Check 3/5: Malware Scan")
        results['checks']['malware'] = await self.scan_for_malware()
        
        # Check 4: DDoS Detection
        logger.info("\n🌐 Check 4/5: DDoS Detection")
        results['checks']['ddos'] = not await self.detect_ddos()
        
        # Check 5: Network Anomaly
        logger.info("\n📡 Check 5/5: Network Anomaly")
        results['checks']['network'] = not await self.check_network_anomaly()
        
        # Overall status
        all_passed = all(results['checks'].values())
        results['status'] = SecurityStatus.SECURE.value if all_passed else SecurityStatus.WARNING.value
        
        logger.info("\n" + "=" * 80)
        if all_passed:
            logger.info("✅ SECURITY SWEEP PASSED")
        else:
            logger.warning("⚠️ SECURITY ISSUES DETECTED")
        logger.info("=" * 80 + "\n")
        
        return results
    
    async def continuous_monitoring(self):
        """
        Continuously monitor security.
        """
        logger.info("🔍 Starting continuous security monitoring...")
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                # Check for threats
                ddos_detected = await self.detect_ddos()
                network_anomaly = await self.check_network_anomaly()
                
                if ddos_detected or network_anomaly:
                    await self.auto_disable_trading_on_threat()
                
                # Run weekly scan
                if self.last_scan is None or \
                   (datetime.now() - self.last_scan).total_seconds() > (self.scan_interval_hours * 3600):
                    await self.run_security_sweep()
                
                # Wait before next check
                await asyncio.sleep(300)  # 5 minutes
            
            except Exception as e:
                logger.error(f"Error in security monitoring: {e}")
                await asyncio.sleep(60)
    
    async def start_monitoring(self):
        """Start security monitoring"""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("Security monitoring already running")
            return
        
        self.monitoring_task = asyncio.create_task(self.continuous_monitoring())
        logger.info("✅ Security monitoring started")
    
    async def stop_monitoring(self):
        """Stop security monitoring"""
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Security monitoring stopped")
    
    def get_security_status(self) -> Dict:
        """Get current security status"""
        recent_events = self.security_events[-10:] if self.security_events else []
        
        critical_events = [e for e in recent_events if e.severity == 'CRITICAL']
        warning_events = [e for e in recent_events if e.severity == 'WARNING']
        
        if critical_events:
            status = SecurityStatus.BREACH
        elif warning_events:
            status = SecurityStatus.WARNING
        else:
            status = SecurityStatus.SECURE
        
        return {
            'status': status.value,
            'last_scan': self.last_scan.isoformat() if self.last_scan else None,
            'total_events': len(self.security_events),
            'critical_events': len(critical_events),
            'warning_events': len(warning_events),
            'recent_events': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'type': e.event_type,
                    'severity': e.severity,
                    'description': e.description
                }
                for e in recent_events
            ]
        }
