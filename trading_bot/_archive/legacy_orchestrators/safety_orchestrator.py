"""
Safety Orchestrator
Coordinates all safety systems for the trading bot.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SafetyStatus:
    """Overall safety status."""
    is_safe: bool
    timestamp: datetime = field(default_factory=datetime.now)
    active_warnings: List[str] = field(default_factory=list)
    active_blocks: List[str] = field(default_factory=list)
    message: str = ""


class SafetyOrchestrator:
    """
    Orchestrates all safety systems for the trading bot.
    Coordinates:
    - Auto Pause Manager
    - Emergency Kill Switch
    - Runtime Risk Monitor
    - Resource Watchdog
    - Pre-Trade Validator
    - Circuit Breaker
    - Connectivity Monitor
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize safety components
        self.auto_pause = None
        self.kill_switch = None
        self.risk_monitor = None
        self.resource_watchdog = None
        self.pre_trade_validator = None
        self.circuit_breaker = None
        self.connectivity_monitor = None
        
        # Status tracking
        self.is_initialized = False
        self.last_check_time = None
        self.safety_status = SafetyStatus(is_safe=True)
        
        self.logger.info("SafetyOrchestrator created")
    
    def initialize(self):
        """Initialize all safety components."""
        try:
            # Import and initialize components
            try:
                from .auto_pause import AutoPauseManager
                auto_pause_config = self.config.get('auto_pause', {})
                self.auto_pause = AutoPauseManager(
                    drift_cooldown_minutes=auto_pause_config.get('drift_cooldown_minutes', 120),
                    latency_cooldown_minutes=auto_pause_config.get('latency_cooldown_minutes', 30),
                    resource_cooldown_minutes=auto_pause_config.get('resource_cooldown_minutes', 60),
                    manual_pause_file=auto_pause_config.get('manual_pause_file', 'PAUSE_TRADING.txt')
                )
                self.logger.info("Auto Pause Manager initialized")
            except Exception as e:
                self.logger.warning(f"Auto Pause Manager not available: {e}")
            
            try:
                from .emergency_kill_switch import EmergencyKillSwitch
                kill_switch_config = self.config.get('kill_switch', {})
                self.kill_switch = EmergencyKillSwitch(
                    max_drawdown_pct=kill_switch_config.get('max_drawdown_pct', 15.0),
                    max_consecutive_losses=kill_switch_config.get('max_consecutive_losses', 5),
                    max_daily_loss_pct=kill_switch_config.get('max_daily_loss_pct', 5.0)
                )
                self.logger.info("Emergency Kill Switch initialized")
            except Exception as e:
                self.logger.warning(f"Emergency Kill Switch not available: {e}")
            
            try:
                from .runtime_risk_monitor import RuntimeRiskMonitor
                self.risk_monitor = RuntimeRiskMonitor(self.config.get('risk_monitor', {}))
                self.logger.info("Runtime Risk Monitor initialized")
            except Exception as e:
                self.logger.warning(f"Runtime Risk Monitor not available: {e}")
            
            try:
                from .resource_watchdog import ResourceWatchdog
                resource_config = self.config.get('resource_watchdog', {})
                self.resource_watchdog = ResourceWatchdog(
                    cpu_threshold_pct=resource_config.get('cpu_threshold_pct', 80.0),
                    memory_threshold_pct=resource_config.get('memory_threshold_pct', 85.0),
                    cpu_duration_seconds=resource_config.get('cpu_duration_seconds', 60)
                )
                self.logger.info("Resource Watchdog initialized")
            except Exception as e:
                self.logger.warning(f"Resource Watchdog not available: {e}")
            
            try:
                from .pre_trade_validator import PreTradeValidator
                self.pre_trade_validator = PreTradeValidator(self.config.get('pre_trade_validator', {}))
                self.logger.info("Pre-Trade Validator initialized")
            except Exception as e:
                self.logger.warning(f"Pre-Trade Validator not available: {e}")
            
            try:
                from .circuit_breaker import CircuitBreaker
                self.circuit_breaker = CircuitBreaker(self.config.get('circuit_breaker', {}))
                self.logger.info("Circuit Breaker initialized")
            except Exception as e:
                self.logger.warning(f"Circuit Breaker not available: {e}")
            
            try:
                from .connectivity_monitor import ConnectivityMonitor
                connectivity_config = self.config.get('connectivity_monitor', {})
                self.connectivity_monitor = ConnectivityMonitor(
                    max_retries=connectivity_config.get('max_retries', 5),
                    retry_delays=connectivity_config.get('retry_delays', [5, 15, 45, 135, 405])
                )
                self.logger.info("Connectivity Monitor initialized")
            except Exception as e:
                self.logger.warning(f"Connectivity Monitor not available: {e}")
            
            self.is_initialized = True
            self.logger.info("SafetyOrchestrator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing SafetyOrchestrator: {e}")
            raise
    
    def check_safety(self) -> SafetyStatus:
        """Check overall safety status."""
        if not self.is_initialized:
            self.initialize()
        
        warnings = []
        blocks = []
        is_safe = True
        
        # Check auto pause
        if self.auto_pause:
            try:
                pause_state = self.auto_pause.get_state()
                if pause_state.is_paused:
                    blocks.append(f"Auto Pause: {pause_state.reason.value}")
                    is_safe = False
            except Exception as e:
                self.logger.warning(f"Error checking auto pause: {e}")
        
        # Check kill switch
        if self.kill_switch:
            try:
                if hasattr(self.kill_switch, 'is_triggered') and self.kill_switch.is_triggered():
                    blocks.append("Emergency Kill Switch activated")
                    is_safe = False
            except Exception as e:
                self.logger.warning(f"Error checking kill switch: {e}")
        
        # Check circuit breaker
        if self.circuit_breaker:
            try:
                if hasattr(self.circuit_breaker, 'is_open') and self.circuit_breaker.is_open():
                    blocks.append("Circuit Breaker is OPEN")
                    is_safe = False
            except Exception as e:
                self.logger.warning(f"Error checking circuit breaker: {e}")
        
        # Check resource watchdog
        if self.resource_watchdog:
            try:
                resource_status = self.resource_watchdog.check_resources()
                if not resource_status.is_healthy:
                    warnings.append(f"Resource issue: {resource_status.message}")
            except Exception as e:
                self.logger.warning(f"Error checking resources: {e}")
        
        # Update status
        self.safety_status = SafetyStatus(
            is_safe=is_safe,
            timestamp=datetime.now(),
            active_warnings=warnings,
            active_blocks=blocks,
            message="; ".join(blocks + warnings) if (blocks or warnings) else "All safety checks passed"
        )
        
        self.last_check_time = datetime.now()
        return self.safety_status
    
    def validate_trade(self, trade_request: Dict[str, Any]) -> bool:
        """Validate a trade request through all safety checks."""
        if not self.is_initialized:
            self.initialize()
        
        # First check overall safety
        safety_status = self.check_safety()
        if not safety_status.is_safe:
            self.logger.warning(f"Trade blocked by safety checks: {safety_status.message}")
            return False
        
        # Then validate through pre-trade validator
        if self.pre_trade_validator:
            try:
                # Convert dict to TradeRequest if needed
                from .pre_trade_validator import TradeRequest
                if isinstance(trade_request, dict):
                    tr = TradeRequest(
                        symbol=trade_request.get('symbol', ''),
                        direction=trade_request.get('direction', ''),
                        quantity=trade_request.get('quantity', 0.0),
                        price=trade_request.get('price', 0.0),
                        stop_loss=trade_request.get('stop_loss'),
                        take_profit=trade_request.get('take_profit'),
                        order_type=trade_request.get('order_type', 'MARKET'),
                        metadata=trade_request.get('metadata', {})
                    )
                else:
                    tr = trade_request
                
                validation_report = self.pre_trade_validator.validate(tr)
                if validation_report.result.name != 'APPROVED':
                    self.logger.warning(f"Trade rejected: {validation_report.rejection_reason}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error in pre-trade validation: {e}")
                return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of all safety systems."""
        if not self.is_initialized:
            self.initialize()
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'is_initialized': self.is_initialized,
            'overall_safe': self.safety_status.is_safe,
            'active_warnings': self.safety_status.active_warnings,
            'active_blocks': self.safety_status.active_blocks,
            'components': {}
        }
        
        # Get status from each component
        if self.auto_pause:
            try:
                pause_state = self.auto_pause.get_state()
                status['components']['auto_pause'] = {
                    'is_paused': pause_state.is_paused,
                    'reason': pause_state.reason.value if pause_state.is_paused else None
                }
            except Exception as e:
                status['components']['auto_pause'] = {'error': str(e)}
        
        if self.kill_switch:
            try:
                status['components']['kill_switch'] = {
                    'is_triggered': self.kill_switch.is_triggered() if hasattr(self.kill_switch, 'is_triggered') else False
                }
            except Exception as e:
                status['components']['kill_switch'] = {'error': str(e)}
        
        if self.circuit_breaker:
            try:
                status['components']['circuit_breaker'] = {
                    'is_open': self.circuit_breaker.is_open() if hasattr(self.circuit_breaker, 'is_open') else False
                }
            except Exception as e:
                status['components']['circuit_breaker'] = {'error': str(e)}
        
        return status
    
    def emergency_stop(self, reason: str = "Manual emergency stop"):
        """Trigger emergency stop across all safety systems."""
        self.logger.critical(f"EMERGENCY STOP: {reason}")
        
        if self.kill_switch and hasattr(self.kill_switch, 'trigger'):
            self.kill_switch.trigger(reason)
        
        if self.auto_pause and hasattr(self.auto_pause, 'pause'):
            from .auto_pause import PauseReason
            self.auto_pause.pause(PauseReason.EMERGENCY_STOP, reason)
        
        if self.circuit_breaker and hasattr(self.circuit_breaker, 'trip'):
            self.circuit_breaker.trip(reason)
        
        self.safety_status = SafetyStatus(
            is_safe=False,
            timestamp=datetime.now(),
            active_blocks=[f"Emergency Stop: {reason}"],
            message=f"Emergency Stop: {reason}"
        )
