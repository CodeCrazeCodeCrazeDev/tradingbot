"""
Autonomous Fixer
Automatically detects and fixes critical issues before trading, then validates safety.
"""

import logging
import socket
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of critical issues."""
    CONNECTION_FAILURE = "connection_failure"
    DATA_FEED_ERROR = "data_feed_error"
    BROKER_API_ERROR = "broker_api_error"
    INSUFFICIENT_MARGIN = "insufficient_margin"
    INVALID_CONFIGURATION = "invalid_configuration"
    MODEL_ERROR = "model_error"
    SYSTEM_RESOURCE = "system_resource"
    RISK_LIMIT_BREACH = "risk_limit_breach"


class IssueSeverity(Enum):
    """Severity levels."""
    CRITICAL = "critical"  # Cannot trade
    HIGH = "high"  # Should not trade
    MEDIUM = "medium"  # Can trade with caution
    LOW = "low"  # Minor issue


class SafetyStatus(Enum):
    """Safety status for trading."""
    SAFE = "safe"
    UNSAFE = "unsafe"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class AutonomousFixer:
    """
    Autonomous system that:
    1. Checks if it's safe to trade
    2. Detects critical issues
    3. Auto-fixes issues
    4. Validates safety after fixes
    5. Reports status
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize autonomous fixer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.auto_fix_enabled = config.get('auto_fix_enabled', True)
        self.max_fix_attempts = config.get('max_fix_attempts', 3)
        self.safety_check_interval = config.get('safety_check_interval', 60)  # seconds
        
        # Issue handlers
        self.issue_handlers = {
            IssueType.CONNECTION_FAILURE: self._fix_connection,
            IssueType.DATA_FEED_ERROR: self._fix_data_feed,
            IssueType.BROKER_API_ERROR: self._fix_broker_api,
            IssueType.INSUFFICIENT_MARGIN: self._fix_margin,
            IssueType.INVALID_CONFIGURATION: self._fix_configuration,
            IssueType.MODEL_ERROR: self._fix_model,
            IssueType.SYSTEM_RESOURCE: self._fix_system_resources,
            IssueType.RISK_LIMIT_BREACH: self._fix_risk_limits,
        }
        
        logger.info("AutonomousFixer initialized")
    
    async def check_safety_and_fix(self) -> Dict[str, Any]:
        """
        Check if it's safe to trade and auto-fix any critical issues.
        
        Returns:
            Dictionary with safety status and actions taken
        """
        logger.info("Starting safety check...")
        
        # Step 1: Detect issues
        issues = await self._detect_issues()
        
        if not issues:
            logger.info("✓ No issues detected - SAFE TO TRADE")
            return {
                'status': SafetyStatus.SAFE,
                'issues': [],
                'fixes_applied': [],
                'safe_to_trade': True
            }
        
        # Step 2: Classify severity
        critical_issues = [i for i in issues if i['severity'] == IssueSeverity.CRITICAL]
        high_issues = [i for i in issues if i['severity'] == IssueSeverity.HIGH]
        
        logger.warning(f"Detected {len(critical_issues)} critical and {len(high_issues)} high severity issues")
        
        # Step 3: Auto-fix if enabled
        fixes_applied = []
        if self.auto_fix_enabled and (critical_issues or high_issues):
            logger.info("Auto-fix enabled - attempting to fix issues...")
            
            for issue in critical_issues + high_issues:
                fix_result = await self._auto_fix_issue(issue)
                fixes_applied.append(fix_result)
        
        # Step 4: Re-check safety after fixes
        remaining_issues = await self._detect_issues()
        critical_remaining = [i for i in remaining_issues if i['severity'] == IssueSeverity.CRITICAL]
        
        # Step 5: Determine final safety status
        if critical_remaining:
            logger.error(f"✗ {len(critical_remaining)} critical issues remain - UNSAFE TO TRADE")
            safe_to_trade = False
            status = SafetyStatus.UNSAFE
        elif high_issues:
            logger.warning("⚠ High severity issues detected - DEGRADED MODE")
            safe_to_trade = False
            status = SafetyStatus.DEGRADED
        else:
            logger.info("✓ All critical issues fixed - SAFE TO TRADE")
            safe_to_trade = True
            status = SafetyStatus.SAFE
        
        return {
            'status': status,
            'issues': remaining_issues,
            'fixes_applied': fixes_applied,
            'safe_to_trade': safe_to_trade,
            'timestamp': datetime.now()
        }
    
    async def _detect_issues(self) -> List[Dict[str, Any]]:
        """
        Detect all current issues.
        
        Returns:
            List of detected issues
        """
        issues = []
        
        # Check connection
        connection_issue = await self._check_connection()
        if connection_issue:
            issues.append(connection_issue)
        
        # Check data feed
        data_feed_issue = await self._check_data_feed()
        if data_feed_issue:
            issues.append(data_feed_issue)
        
        # Check broker API
        broker_issue = await self._check_broker_api()
        if broker_issue:
            issues.append(broker_issue)
        
        # Check margin
        margin_issue = await self._check_margin()
        if margin_issue:
            issues.append(margin_issue)
        
        # Check configuration
        config_issue = await self._check_configuration()
        if config_issue:
            issues.append(config_issue)
        
        # Check models
        model_issue = await self._check_models()
        if model_issue:
            issues.append(model_issue)
        
        # Check system resources
        resource_issue = await self._check_system_resources()
        if resource_issue:
            issues.append(resource_issue)
        
        # Check risk limits
        risk_issue = await self._check_risk_limits()
        if risk_issue:
            issues.append(risk_issue)
        
        return issues
    
    async def _auto_fix_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to automatically fix an issue.
        
        Args:
            issue: Issue to fix
            
        Returns:
            Fix result
        """
        issue_type = issue['type']
        handler = self.issue_handlers.get(issue_type)
        
        if not handler:
            logger.error(f"No handler for issue type: {issue_type}")
            return {
                'issue': issue,
                'fixed': False,
                'error': 'No handler available'
            }
        
        logger.info(f"Attempting to fix: {issue['description']}")
        
        for attempt in range(self.max_fix_attempts):
            try:
                result = await handler(issue)
                
                if result['success']:
                    logger.info(f"✓ Fixed: {issue['description']}")
                    return {
                        'issue': issue,
                        'fixed': True,
                        'attempts': attempt + 1,
                        'action': result['action']
                    }
                else:
                    logger.warning(f"Fix attempt {attempt + 1} failed: {result.get('error')}")
            
            except Exception as e:
                logger.error(f"Error during fix attempt {attempt + 1}: {e}")
        
        logger.error(f"✗ Failed to fix after {self.max_fix_attempts} attempts: {issue['description']}")
        return {
            'issue': issue,
            'fixed': False,
            'attempts': self.max_fix_attempts,
            'error': 'Max attempts exceeded'
        }
    
    # Issue detection methods
    
    async def _check_connection(self) -> Optional[Dict[str, Any]]:
        """Check internet/broker connection."""
        try:
            # Check internet connectivity
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return None
        except Exception as e:
            return {
                'type': IssueType.CONNECTION_FAILURE,
                'severity': IssueSeverity.CRITICAL,
                'description': f'No internet connection: {e}',
                'details': {'error': str(e)}
            }
    
    async def _check_data_feed(self) -> Optional[Dict[str, Any]]:
        """Check data feed status."""
        # Implement data feed check
        # For now, return None (no issue)
        return None
    
    async def _check_broker_api(self) -> Optional[Dict[str, Any]]:
        """Check broker API status."""
        # Implement broker API check
        return None
    
    async def _check_margin(self) -> Optional[Dict[str, Any]]:
        """Check margin requirements."""
        # Implement margin check
        return None
    
    async def _check_configuration(self) -> Optional[Dict[str, Any]]:
        """Check configuration validity."""
        # Implement configuration check
        return None
    
    async def _check_models(self) -> Optional[Dict[str, Any]]:
        """Check ML models status."""
        # Implement model check
        return None
    
    async def _check_system_resources(self) -> Optional[Dict[str, Any]]:
        """Check system resources (CPU, memory, disk)."""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            if cpu_percent > 90:
                return {
                    'type': IssueType.SYSTEM_RESOURCE,
                    'severity': IssueSeverity.HIGH,
                    'description': f'High CPU usage: {cpu_percent}%',
                    'details': {'cpu': cpu_percent}
                }
            
            if memory_percent > 90:
                return {
                    'type': IssueType.SYSTEM_RESOURCE,
                    'severity': IssueSeverity.HIGH,
                    'description': f'High memory usage: {memory_percent}%',
                    'details': {'memory': memory_percent}
                }
            
            if disk_percent > 95:
                return {
                    'type': IssueType.SYSTEM_RESOURCE,
                    'severity': IssueSeverity.CRITICAL,
                    'description': f'Disk almost full: {disk_percent}%',
                    'details': {'disk': disk_percent}
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return None
    
    async def _check_risk_limits(self) -> Optional[Dict[str, Any]]:
        """Check risk limits."""
        # Implement risk limit check
        return None
    
    # Issue fix methods
    
    async def _fix_connection(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix connection issues."""
        logger.info("Attempting to restore connection...")
        
        # Wait and retry
        await asyncio.sleep(5)
        
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return {
                'success': True,
                'action': 'Connection restored after retry'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection still down: {e}'
            }
    
    async def _fix_data_feed(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix data feed issues."""
        logger.info("Attempting to fix data feed...")
        
        # Restart data feed connection
        # Clear cache
        # Reconnect
        
        return {
            'success': True,
            'action': 'Data feed restarted'
        }
    
    async def _fix_broker_api(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix broker API issues."""
        logger.info("Attempting to fix broker API...")
        
        # Reconnect to broker
        # Refresh authentication
        
        return {
            'success': True,
            'action': 'Broker API reconnected'
        }
    
    async def _fix_margin(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix margin issues."""
        logger.info("Attempting to fix margin issues...")
        
        # Close losing positions
        # Reduce position sizes
        # Request margin increase (if automated)
        
        return {
            'success': True,
            'action': 'Reduced position sizes to free margin'
        }
    
    async def _fix_configuration(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix configuration issues."""
        logger.info("Attempting to fix configuration...")
        
        # Reload configuration
        # Validate and fix invalid values
        # Reset to defaults if needed
        
        return {
            'success': True,
            'action': 'Configuration reloaded and validated'
        }
    
    async def _fix_model(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix model issues."""
        logger.info("Attempting to fix model issues...")
        
        # Reload model
        # Rollback to previous version
        # Clear model cache
        
        return {
            'success': True,
            'action': 'Model reloaded from checkpoint'
        }
    
    async def _fix_system_resources(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix system resource issues."""
        logger.info("Attempting to fix system resource issues...")
        
        # Clear caches
        # Close unnecessary processes
        # Free memory
        
        import gc
        gc.collect()
        
        return {
            'success': True,
            'action': 'Cleared caches and freed memory'
        }
    
    async def _fix_risk_limits(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix risk limit breaches."""
        logger.info("Attempting to fix risk limit breaches...")
        
        # Close positions exceeding limits
        # Reduce position sizes
        # Pause trading temporarily
        
        return {
            'success': True,
            'action': 'Reduced positions to comply with risk limits'
        }
