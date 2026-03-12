"""
Paper Trading Mode Validator
Ensures paper trading is properly isolated from live trading
"""

import logging
from typing import Dict, Optional, Any, List
from enum import Enum
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading modes"""
    SIMULATION = "simulation"
    PAPER = "paper"
    LIVE = "live"


class ValidationResult(Enum):
    """Validation result"""
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


@dataclass
class ValidationCheck:
    """Validation check result"""
    check_name: str
    passed: bool
    message: str
    severity: str = "info"


class PaperTradingValidator:
    """
    Paper Trading Mode Validator
    
    Ensures paper trading cannot accidentally execute live trades.
    Validates broker connections, API keys, and execution paths.
    """
    
    def __init__(self, mode: TradingMode = TradingMode.PAPER):
        """
        Initialize paper trading validator
        
        Args:
            mode: Current trading mode
        """
        try:
            self.mode = mode
            self.live_execution_blocked = (mode != TradingMode.LIVE)
            self.validation_history: List[ValidationCheck] = []
            self._lock = threading.RLock()
        
            # Dangerous operations that should be blocked in paper mode
            self.blocked_operations = {
                'submit_order',
                'cancel_order',
                'modify_order',
                'close_position',
                'withdraw_funds',
                'transfer_funds'
            }
        
            logger.info(f"PaperTradingValidator initialized in {mode.value} mode")
        
            if mode == TradingMode.LIVE:
                logger.critical("⚠️  LIVE TRADING MODE ACTIVE - REAL MONEY AT RISK ⚠️")
            else:
                logger.info(f"✓ Safe mode active: {mode.value}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_execution(
        self,
        operation: str,
        broker_name: Optional[str] = None,
        api_credentials: Optional[Dict[str, str]] = None
    ) -> ValidationResult:
        """
        Validate if execution is allowed
        
        Args:
            operation: Operation name (e.g., 'submit_order')
            broker_name: Broker name
            api_credentials: API credentials being used
            
        Returns:
            ValidationResult indicating if operation is safe
        """
        try:
            checks = []
        
            # Check 1: Mode validation
            if self.mode == TradingMode.LIVE:
                checks.append(ValidationCheck(
                    check_name="mode_check",
                    passed=True,
                    message="Live trading mode - execution allowed",
                    severity="critical"
                ))
            else:
                if operation in self.blocked_operations:
                    checks.append(ValidationCheck(
                        check_name="mode_check",
                        passed=False,
                        message=f"Operation '{operation}' blocked in {self.mode.value} mode",
                        severity="info"
                    ))
                else:
                    checks.append(ValidationCheck(
                        check_name="mode_check",
                        passed=True,
                        message=f"Operation allowed in {self.mode.value} mode",
                        severity="info"
                    ))
        
            # Check 2: Broker validation
            if broker_name:
                if self.mode != TradingMode.LIVE and broker_name.lower() not in ['simulation', 'paper', 'mock']:
                    checks.append(ValidationCheck(
                        check_name="broker_check",
                        passed=False,
                        message=f"Real broker '{broker_name}' detected in {self.mode.value} mode",
                        severity="critical"
                    ))
                else:
                    checks.append(ValidationCheck(
                        check_name="broker_check",
                        passed=True,
                        message=f"Broker '{broker_name}' appropriate for mode",
                        severity="info"
                    ))
        
            # Check 3: API credentials validation
            if api_credentials and self.mode != TradingMode.LIVE:
                # Check if credentials look like production keys
                suspicious_keys = ['prod', 'live', 'real', 'main']
                for key, value in api_credentials.items():
                    if any(s in str(value).lower() for s in suspicious_keys):
                        checks.append(ValidationCheck(
                            check_name="credentials_check",
                            passed=False,
                            message=f"Production-like credentials detected in {self.mode.value} mode",
                            severity="critical"
                        ))
                        break
                else:
                    checks.append(ValidationCheck(
                        check_name="credentials_check",
                        passed=True,
                        message="Credentials appear safe for paper trading",
                        severity="info"
                    ))
        
            # Store validation history
            with self._lock:
                self.validation_history.extend(checks)
                # Keep only last 1000 checks
                if len(self.validation_history) > 1000:
                    self.validation_history = self.validation_history[-1000:]
        
            # Determine overall result
            critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
            failures = [c for c in checks if not c.passed]
        
            if critical_failures:
                logger.error(f"EXECUTION BLOCKED: {critical_failures[0].message}")
                return ValidationResult.BLOCKED
            elif failures:
                logger.warning(f"EXECUTION WARNING: {failures[0].message}")
                return ValidationResult.WARNING
            else:
                return ValidationResult.SAFE
        except Exception as e:
            logger.error(f"Error in validate_execution: {e}")
            raise
    
    def validate_broker_connection(
        self,
        broker_config: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate broker connection configuration
        
        Args:
            broker_config: Broker configuration dictionary
            
        Returns:
            ValidationResult
        """
        try:
            checks = []
        
            broker_name = broker_config.get('name', '').lower()
        
            # In paper/simulation mode, only allow paper brokers
            if self.mode != TradingMode.LIVE:
                safe_brokers = ['simulation', 'paper', 'mock', 'demo', 'sandbox']
            
                if not any(safe in broker_name for safe in safe_brokers):
                    checks.append(ValidationCheck(
                        check_name="broker_type",
                        passed=False,
                        message=f"Real broker '{broker_name}' not allowed in {self.mode.value} mode",
                        severity="critical"
                    ))
                else:
                    checks.append(ValidationCheck(
                        check_name="broker_type",
                        passed=True,
                        message=f"Paper broker '{broker_name}' approved",
                        severity="info"
                    ))
        
            # Check for live API endpoints
            endpoint = broker_config.get('endpoint', '').lower()
            if endpoint and self.mode != TradingMode.LIVE:
                live_indicators = ['api.', 'live.', 'prod.', 'production.']
                if any(ind in endpoint for ind in live_indicators):
                    checks.append(ValidationCheck(
                        check_name="endpoint_check",
                        passed=False,
                        message=f"Live API endpoint detected: {endpoint}",
                        severity="critical"
                    ))
        
            with self._lock:
                self.validation_history.extend(checks)
        
            critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
        
            if critical_failures:
                logger.error(f"BROKER CONNECTION BLOCKED: {critical_failures[0].message}")
                return ValidationResult.BLOCKED
            else:
                return ValidationResult.SAFE
        except Exception as e:
            logger.error(f"Error in validate_broker_connection: {e}")
            raise
    
    def require_live_mode(self, operation: str) -> bool:
        """
        Check if operation requires live mode
        
        Args:
            operation: Operation name
            
        Returns:
            True if allowed, False if blocked
        """
        try:
            if self.mode == TradingMode.LIVE:
                return True
        
            if operation in self.blocked_operations:
                logger.error(
                    f"Operation '{operation}' requires LIVE mode. "
                    f"Current mode: {self.mode.value}"
                )
                return False
        
            return True
        except Exception as e:
            logger.error(f"Error in require_live_mode: {e}")
            raise
    
    def get_mode_banner(self) -> str:
        """Get mode banner for display"""
        try:
            if self.mode == TradingMode.LIVE:
                return """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ⚠️  LIVE TRADING MODE - REAL MONEY AT RISK  ⚠️          ║
    ║                                                           ║
    ║   All trades will be executed with real capital          ║
    ║   Losses are REAL and PERMANENT                          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
            elif self.mode == TradingMode.PAPER:
                return """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   📝 PAPER TRADING MODE - SIMULATION ONLY                ║
    ║                                                           ║
    ║   No real money at risk                                  ║
    ║   All trades are simulated                               ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
            else:
                return """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🧪 SIMULATION MODE - TESTING ONLY                      ║
    ║                                                           ║
    ║   Completely isolated from real markets                  ║
    ║   No broker connections                                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
        except Exception as e:
            logger.error(f"Error in get_mode_banner: {e}")
            raise
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        try:
            with self._lock:
                total = len(self.validation_history)
                passed = sum(1 for c in self.validation_history if c.passed)
                failed = total - passed
            
                by_severity = {}
                for check in self.validation_history:
                    by_severity[check.severity] = by_severity.get(check.severity, 0) + 1
            
                return {
                    'mode': self.mode.value,
                    'total_checks': total,
                    'passed': passed,
                    'failed': failed,
                    'by_severity': by_severity,
                    'live_execution_blocked': self.live_execution_blocked
                }
        except Exception as e:
            logger.error(f"Error in get_validation_stats: {e}")
            raise
    
    def get_recent_checks(self, limit: int = 10) -> List[ValidationCheck]:
        """Get recent validation checks"""
        try:
            with self._lock:
                return self.validation_history[-limit:]
        except Exception as e:
            logger.error(f"Error in get_recent_checks: {e}")
            raise


# Singleton instance
_paper_trading_validator: Optional[PaperTradingValidator] = None


def get_paper_trading_validator(mode: Optional[TradingMode] = None) -> PaperTradingValidator:
    """Get or create paper trading validator singleton"""
    try:
        global _paper_trading_validator
    
        if _paper_trading_validator is None:
            if mode is None:
                mode = TradingMode.PAPER
            _paper_trading_validator = PaperTradingValidator(mode)
    
        return _paper_trading_validator
    except Exception as e:
        logger.error(f"Error in get_paper_trading_validator: {e}")
        raise


def validate_execution(operation: str, **kwargs) -> ValidationResult:
    """Convenience function to validate execution"""
    try:
        validator = get_paper_trading_validator()
        return validator.validate_execution(operation, **kwargs)
    except Exception as e:
        logger.error(f"Error in validate_execution: {e}")
        raise


def require_live_mode(operation: str) -> bool:
    """Convenience function to check if operation requires live mode"""
    try:
        validator = get_paper_trading_validator()
        return validator.require_live_mode(operation)
    except Exception as e:
        logger.error(f"Error in require_live_mode: {e}")
        raise
