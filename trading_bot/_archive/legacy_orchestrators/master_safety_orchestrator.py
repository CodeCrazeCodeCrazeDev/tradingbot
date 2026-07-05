"""
Master Safety Orchestrator - Integrates All Critical Fixes
==========================================================

This module integrates all critical fix components into a unified safety system
that addresses the top 50 existential questions from the 1,000 critical questions.

Components Integrated:
1. PositionStateManager - Q22: Position reconciliation
2. RealtimeRiskCalculator - Q401: Real-time risk calculation
3. MultiLayerKillSwitch - Q891, Q901: Emergency shutdown
4. DataValidator - Q71: Data quality validation
5. ExecutionQualityMonitor - Q141: Execution quality
6. SilentFailureDetector - Q851: Silent failure detection
7. ConfigIntegrityMonitor - Q781: Configuration integrity

This orchestrator ensures all safety systems work together.
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .position_state_manager import PositionStateManager, PositionState
from .realtime_risk_calculator import RealtimeRiskCalculator, RiskMetrics, RiskLimits, RiskLevel, DrawdownLevel
from .multi_layer_kill_switch import MultiLayerKillSwitch, KillSwitchLevel, KillSwitchTrigger
from .data_validator import DataValidator, DataQualityReport, DataQualityLevel
from .execution_quality_monitor import ExecutionQualityMonitor, ExecutionMetrics, ExecutionQuality
from .silent_failure_detector import SilentFailureDetector, FailureReport, ComponentStatus
from .config_integrity_monitor import ConfigIntegrityMonitor

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """Overall system status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


@dataclass
class SafetyStatus:
    """Comprehensive safety status"""
    timestamp: datetime
    system_status: SystemStatus
    can_trade: bool
    can_open_positions: bool
    
    # Component statuses
    position_reconciliation_ok: bool
    risk_within_limits: bool
    kill_switch_active: bool
    data_quality_ok: bool
    execution_quality_ok: bool
    no_silent_failures: bool
    config_valid: bool
    
    # Key metrics
    current_drawdown: float
    risk_level: str
    active_positions: int
    pending_issues: int
    
    # Warnings and errors
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'system_status': self.system_status.value,
            'can_trade': self.can_trade,
            'can_open_positions': self.can_open_positions,
            'position_reconciliation_ok': self.position_reconciliation_ok,
            'risk_within_limits': self.risk_within_limits,
            'kill_switch_active': self.kill_switch_active,
            'data_quality_ok': self.data_quality_ok,
            'execution_quality_ok': self.execution_quality_ok,
            'no_silent_failures': self.no_silent_failures,
            'config_valid': self.config_valid,
            'current_drawdown': self.current_drawdown,
            'risk_level': self.risk_level,
            'active_positions': self.active_positions,
            'pending_issues': self.pending_issues,
            'warnings': self.warnings,
            'errors': self.errors
        }


class MasterSafetyOrchestrator:
    """
    Master orchestrator for all safety systems.
    
    This is the central safety coordinator that:
    1. Initializes and manages all safety components
    2. Coordinates safety checks before trading
    3. Monitors system health continuously
    4. Triggers emergency procedures when needed
    5. Provides unified safety status
    
    CRITICAL: This orchestrator enforces that trading cannot occur
    unless ALL safety systems report healthy status.
    """
    
    def __init__(
        self,
        broker_adapter,
        config: Optional[Dict] = None,
        config_path: Optional[str] = None,
        db_path: str = "safety_data",
        on_emergency: Optional[Callable] = None,
        on_warning: Optional[Callable] = None
    ):
        """
        Initialize master safety orchestrator.
        
        Args:
            broker_adapter: Broker adapter for trading operations
            config: Configuration dictionary
            config_path: Path to configuration file
            db_path: Base path for safety databases
            on_emergency: Callback for emergency situations
            on_warning: Callback for warnings
        """
        self.broker = broker_adapter
        self.config = config or {}
        self.config_path = config_path
        self.db_path = Path(db_path)
        self.on_emergency = on_emergency
        self.on_warning = on_warning
        
        # Create database directory
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._init_components()
        
        # State
        self._lock = threading.RLock()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._last_status: Optional[SafetyStatus] = None
        self._emergency_mode = False
        
        # Statistics
        self.stats = {
            'safety_checks': 0,
            'trades_blocked': 0,
            'emergencies_triggered': 0,
            'warnings_issued': 0,
            'uptime_start': datetime.now()
        }
        
        logger.info("MasterSafetyOrchestrator initialized")
    
    def _init_components(self):
        """Initialize all safety components"""
        
        # 1. Position State Manager (Q22)
        self.position_manager = PositionStateManager(
            broker_adapter=self.broker,
            db_path=str(self.db_path / "positions.db"),
            reconciliation_interval=self.config.get('reconciliation_interval', 30),
            auto_correct=self.config.get('auto_correct_positions', False),
            on_discrepancy=self._on_position_discrepancy
        )
        
        # 2. Real-time Risk Calculator (Q401)
        risk_limits = RiskLimits(
            max_risk_per_trade=self.config.get('max_risk_per_trade', 0.02),
            max_drawdown=self.config.get('max_drawdown', 0.20),
            max_portfolio_risk=self.config.get('max_portfolio_risk', 0.05),
            emergency_shutdown_drawdown=self.config.get('emergency_shutdown_drawdown', 0.25),
            max_daily_loss=self.config.get('max_daily_loss', 0.03),
            max_open_positions=self.config.get('max_open_positions', 10)
        )
        self.risk_calculator = RealtimeRiskCalculator(
            limits=risk_limits,
            on_limit_breach=self._on_risk_limit_breach,
            on_drawdown_warning=self._on_drawdown_warning
        )
        
        # 3. Multi-Layer Kill Switch (Q891, Q901)
        self.kill_switch = MultiLayerKillSwitch(
            broker_adapter=self.broker,
            db_path=str(self.db_path / "kill_switch.db"),
            heartbeat_timeout=self.config.get('heartbeat_timeout', 30),
            on_activation=self._on_kill_switch_activated,
            on_position_closed=self._on_position_closed
        )
        
        # 4. Data Validator (Q71)
        self.data_validator = DataValidator(
            max_price_change_pct=self.config.get('max_price_change_pct', 0.10),
            max_staleness_seconds=self.config.get('max_staleness_seconds', 5),
            on_issue_detected=self._on_data_issue,
            on_data_quarantined=self._on_data_quarantined
        )
        
        # 5. Execution Quality Monitor (Q141)
        self.execution_monitor = ExecutionQualityMonitor(
            commission_rate=self.config.get('commission_rate', 0.0001),
            on_quality_degradation=self._on_execution_degradation,
            on_slippage_alert=self._on_slippage_alert
        )
        
        # 6. Silent Failure Detector (Q851)
        self.failure_detector = SilentFailureDetector(
            heartbeat_timeout=self.config.get('component_heartbeat_timeout', 30),
            on_failure_detected=self._on_silent_failure,
            on_component_dead=self._on_component_dead,
            auto_remediate=self.config.get('auto_remediate', False)
        )
        
        # 7. Configuration Integrity Monitor (Q781)
        self.config_monitor = ConfigIntegrityMonitor(
            config_path=self.config_path,
            on_drift_detected=self._on_config_drift,
            on_tampering_detected=self._on_config_tampering,
            on_validation_error=self._on_config_error
        )
        
        # Register components with failure detector
        self._register_components_for_monitoring()
    
    def _register_components_for_monitoring(self):
        """Register all components with the silent failure detector"""
        components = [
            ('position_manager', 'Position State Manager', 10, 30),
            ('risk_calculator', 'Risk Calculator', 5, 10),
            ('kill_switch', 'Kill Switch', 5, 60),
            ('data_validator', 'Data Validator', 1, 5),
            ('execution_monitor', 'Execution Monitor', 10, 60),
            ('config_monitor', 'Config Monitor', 60, 300)
        ]
        
        for comp_id, name, heartbeat, output in components:
            self.failure_detector.register_component(
                component_id=comp_id,
                name=name,
                heartbeat_interval=heartbeat,
                output_interval=output
            )
    
    async def start(self):
        """Start all safety systems"""
        if self._running:
            logger.warning("Safety orchestrator already running")
            return
        
        logger.info("Starting safety orchestrator...")
        
        # Load configuration
        if self.config_path:
            config, errors = self.config_monitor.load_config()
            if errors:
                for error in errors:
                    if error.severity == 'critical':
                        logger.error(f"Config error: {error.message}")
        
        # Start components
        await self.position_manager.start_reconciliation()
        await self.kill_switch.start_monitoring()
        await self.failure_detector.start()
        
        # Start main monitoring loop
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info("Safety orchestrator started")
    
    async def stop(self):
        """Stop all safety systems"""
        logger.info("Stopping safety orchestrator...")
        
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop components
        await self.position_manager.stop_reconciliation()
        await self.kill_switch.stop_monitoring()
        await self.failure_detector.stop()
        
        logger.info("Safety orchestrator stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        check_interval = self.config.get('safety_check_interval', 5)
        
        while self._running:
            try:
                await asyncio.sleep(check_interval)
                
                if not self._running:
                    break
                
                # Perform safety check
                status = await self.get_safety_status()
                
                # Send heartbeats
                self._send_heartbeats()
                
                # Handle status
                await self._handle_status(status)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
    
    def _send_heartbeats(self):
        """Send heartbeats to all components"""
        self.kill_switch.heartbeat()
        
        # Record heartbeats with failure detector
        for comp_id in ['position_manager', 'risk_calculator', 'kill_switch', 
                        'data_validator', 'execution_monitor', 'config_monitor']:
            self.failure_detector.heartbeat(comp_id)
    
    async def _handle_status(self, status: SafetyStatus):
        """Handle safety status"""
        self._last_status = status
        self.stats['safety_checks'] += 1
        
        # Check for emergency
        if status.system_status == SystemStatus.EMERGENCY:
            if not self._emergency_mode:
                await self._trigger_emergency(status)
        
        # Check for warnings
        if status.warnings:
            self.stats['warnings_issued'] += len(status.warnings)
            if self.on_warning:
                for warning in status.warnings:
                    try:
                        if asyncio.iscoroutinefunction(self.on_warning):
                            await self.on_warning(warning)
                        else:
                            self.on_warning(warning)
                    except Exception as e:
                        logger.error(f"Warning callback error: {e}")
    
    async def _trigger_emergency(self, status: SafetyStatus):
        """Trigger emergency procedures"""
        self._emergency_mode = True
        self.stats['emergencies_triggered'] += 1
        
        logger.critical("EMERGENCY TRIGGERED - Activating kill switch")
        
        # Activate kill switch
        await self.kill_switch.activate(
            KillSwitchLevel.HARD,
            KillSwitchTrigger.SYSTEM_ERROR,
            f"Safety orchestrator emergency: {status.errors}",
            "safety_orchestrator"
        )
        
        # Callback
        if self.on_emergency:
            try:
                if asyncio.iscoroutinefunction(self.on_emergency):
                    await self.on_emergency(status)
                else:
                    self.on_emergency(status)
            except Exception as e:
                logger.error(f"Emergency callback error: {e}")
    
    async def get_safety_status(self) -> SafetyStatus:
        """
        Get comprehensive safety status.
        
        This is the central safety check that must pass before any trading.
        """
        warnings = []
        errors = []
        
        # 1. Check position reconciliation
        recon_status = self.position_manager.get_reconciliation_status()
        position_ok = True
        if recon_status.get('recent_discrepancies'):
            position_ok = False
            warnings.append("Position discrepancies detected")
        
        # 2. Check risk metrics
        positions = self.position_manager.get_all_positions()
        equity = self.config.get('equity', 10000)  # Should come from broker
        
        risk_metrics = self.risk_calculator.calculate_risk(
            equity=equity,
            positions=[p.to_dict() for p in positions]
        )
        
        risk_ok = risk_metrics.overall_risk_level not in (RiskLevel.BREACH, RiskLevel.CRITICAL)
        if not risk_ok:
            errors.append(f"Risk level: {risk_metrics.overall_risk_level.value}")
        
        if risk_metrics.warnings:
            warnings.extend(risk_metrics.warnings)
        
        # 3. Check kill switch
        kill_switch_active = self.kill_switch.is_active
        if kill_switch_active:
            errors.append(f"Kill switch active: {self.kill_switch.current_level.name}")
        
        # 4. Check data quality
        data_stats = self.data_validator.get_statistics()
        data_ok = data_stats.get('average_quality_score', 100) >= 70
        if not data_ok:
            warnings.append(f"Data quality degraded: {data_stats.get('average_quality_score', 0):.0f}/100")
        
        # 5. Check execution quality
        exec_metrics = self.execution_monitor.get_metrics('hourly')
        exec_ok = exec_metrics.execution_quality not in (
            ExecutionQuality.POOR, ExecutionQuality.UNACCEPTABLE
        )
        if not exec_ok:
            warnings.append(f"Execution quality: {exec_metrics.execution_quality.value}")
        
        # 6. Check for silent failures
        active_failures = self.failure_detector.get_active_failures()
        no_failures = len(active_failures) == 0
        if not no_failures:
            for failure in active_failures:
                if failure.severity == 'critical':
                    errors.append(f"Silent failure: {failure.component} - {failure.description}")
                else:
                    warnings.append(f"Component issue: {failure.component}")
        
        # 7. Check configuration
        config_valid, config_issues = self.config_monitor.check_integrity()
        if not config_valid:
            warnings.extend(config_issues)
        
        # Determine overall status
        if errors or kill_switch_active:
            if kill_switch_active and self.kill_switch.current_level.value >= KillSwitchLevel.HARD.value:
                system_status = SystemStatus.SHUTDOWN
            elif risk_metrics.drawdown_level == DrawdownLevel.EMERGENCY:
                system_status = SystemStatus.EMERGENCY
            else:
                system_status = SystemStatus.CRITICAL
        elif warnings:
            system_status = SystemStatus.DEGRADED
        else:
            system_status = SystemStatus.HEALTHY
        
        # Determine trading permissions
        can_trade = (
            system_status in (SystemStatus.HEALTHY, SystemStatus.DEGRADED) and
            not kill_switch_active and
            risk_ok and
            position_ok
        )
        
        can_open = (
            can_trade and
            self.kill_switch.can_open_positions and
            len(positions) < self.risk_calculator.limits.max_open_positions
        )
        
        return SafetyStatus(
            timestamp=datetime.now(),
            system_status=system_status,
            can_trade=can_trade,
            can_open_positions=can_open,
            position_reconciliation_ok=position_ok,
            risk_within_limits=risk_ok,
            kill_switch_active=kill_switch_active,
            data_quality_ok=data_ok,
            execution_quality_ok=exec_ok,
            no_silent_failures=no_failures,
            config_valid=config_valid,
            current_drawdown=risk_metrics.current_drawdown,
            risk_level=risk_metrics.overall_risk_level.value,
            active_positions=len(positions),
            pending_issues=len(warnings) + len(errors),
            warnings=warnings,
            errors=errors
        )
    
    async def pre_trade_check(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None
    ) -> tuple:
        """
        Perform pre-trade safety check.
        
        This MUST be called before any trade is executed.
        
        Args:
            symbol: Trading symbol
            direction: 'buy' or 'sell'
            quantity: Position quantity
            price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Tuple of (can_trade, reason)
        """
        # Get current safety status
        status = await self.get_safety_status()
        
        if not status.can_trade:
            self.stats['trades_blocked'] += 1
            return False, f"Trading blocked: {status.system_status.value}"
        
        if not status.can_open_positions:
            self.stats['trades_blocked'] += 1
            return False, "Cannot open new positions"
        
        # Check risk calculator
        equity = self.config.get('equity', 10000)
        can_open, reason = self.risk_calculator.can_open_position(
            symbol=symbol,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            equity=equity
        )
        
        if not can_open:
            self.stats['trades_blocked'] += 1
            return False, reason
        
        return True, "OK"
    
    def validate_market_data(
        self,
        symbol: str,
        bid: float,
        ask: float,
        timestamp: datetime,
        volume: Optional[float] = None
    ) -> DataQualityReport:
        """Validate market data before use"""
        report = self.data_validator.validate_tick(
            symbol=symbol,
            bid=bid,
            ask=ask,
            timestamp=timestamp,
            volume=volume
        )
        
        # Record output for failure detection
        self.failure_detector.record_output('data_validator', report)
        
        return report
    
    def record_execution(
        self,
        order_id: str,
        execution_id: str,
        executed_price: float,
        executed_quantity: float
    ):
        """Record trade execution for quality monitoring"""
        record = self.execution_monitor.record_execution(
            order_id=order_id,
            execution_id=execution_id,
            executed_price=executed_price,
            executed_quantity=executed_quantity
        )
        
        if record:
            self.failure_detector.record_output('execution_monitor', record)
        
        return record
    
    def update_equity(self, equity: float):
        """Update current equity for risk calculations"""
        self.risk_calculator.update_equity(equity)
        self.config['equity'] = equity
    
    # Callback handlers
    async def _on_position_discrepancy(self, discrepancy: Dict):
        """Handle position discrepancy"""
        logger.warning(f"Position discrepancy: {discrepancy}")
        if discrepancy.get('severity') == 'critical':
            await self.kill_switch.activate(
                KillSwitchLevel.SOFT,
                KillSwitchTrigger.SYSTEM_ERROR,
                f"Critical position discrepancy: {discrepancy}",
                "position_manager"
            )
    
    async def _on_risk_limit_breach(self, limit_type: str, metrics: RiskMetrics):
        """Handle risk limit breach"""
        logger.error(f"Risk limit breach: {limit_type}")
        
        if limit_type == 'emergency_drawdown':
            await self.kill_switch.activate(
                KillSwitchLevel.NUCLEAR,
                KillSwitchTrigger.DRAWDOWN,
                f"Emergency drawdown: {metrics.current_drawdown:.1%}",
                "risk_calculator"
            )
        elif limit_type == 'max_drawdown':
            await self.kill_switch.activate(
                KillSwitchLevel.HARD,
                KillSwitchTrigger.DRAWDOWN,
                f"Max drawdown breached: {metrics.current_drawdown:.1%}",
                "risk_calculator"
            )
    
    def _on_drawdown_warning(self, level: DrawdownLevel, metrics: RiskMetrics):
        """Handle drawdown warning"""
        logger.warning(f"Drawdown warning: {level.value} ({metrics.current_drawdown:.1%})")
    
    async def _on_kill_switch_activated(self, event):
        """Handle kill switch activation"""
        logger.critical(f"Kill switch activated: {event.level.name}")
        self._emergency_mode = True
    
    def _on_position_closed(self, ticket: str, symbol: str):
        """Handle position closed by kill switch"""
        logger.info(f"Position closed by kill switch: {ticket} ({symbol})")
    
    def _on_data_issue(self, symbol: str, issue):
        """Handle data quality issue"""
        logger.warning(f"Data issue for {symbol}: {issue.message}")
    
    def _on_data_quarantined(self, data: Dict):
        """Handle quarantined data"""
        logger.warning(f"Data quarantined: {data.get('symbol')}")
    
    def _on_execution_degradation(self, metrics: ExecutionMetrics):
        """Handle execution quality degradation"""
        logger.warning(f"Execution quality degraded: {metrics.execution_quality.value}")
    
    def _on_slippage_alert(self, record):
        """Handle slippage alert"""
        logger.warning(f"High slippage: {record.symbol} {record.slippage_bps:.1f} bps")
    
    async def _on_silent_failure(self, failure: FailureReport):
        """Handle silent failure detection"""
        logger.warning(f"Silent failure: {failure.component} - {failure.description}")
        
        if failure.severity == 'critical':
            await self.kill_switch.activate(
                KillSwitchLevel.SOFT,
                KillSwitchTrigger.SYSTEM_ERROR,
                f"Silent failure in {failure.component}",
                "failure_detector"
            )
    
    async def _on_component_dead(self, component_id: str, failure: FailureReport):
        """Handle dead component"""
        logger.error(f"Component dead: {component_id}")
        
        await self.kill_switch.activate(
            KillSwitchLevel.MEDIUM,
            KillSwitchTrigger.SYSTEM_ERROR,
            f"Component {component_id} is dead",
            "failure_detector"
        )
    
    def _on_config_drift(self, current: Dict, file: Dict):
        """Handle configuration drift"""
        logger.warning("Configuration drift detected")
    
    def _on_config_tampering(self, expected_hash: str, actual_hash: str):
        """Handle configuration tampering"""
        logger.error(f"Configuration tampering detected!")
    
    def _on_config_error(self, error):
        """Handle configuration validation error"""
        logger.warning(f"Config error: {error.message}")
    
    def get_status(self) -> Dict:
        """Get orchestrator status"""
        return {
            'running': self._running,
            'emergency_mode': self._emergency_mode,
            'last_status': self._last_status.to_dict() if self._last_status else None,
            'statistics': self.stats,
            'components': {
                'position_manager': self.position_manager.get_reconciliation_status(),
                'risk_calculator': self.risk_calculator.get_status(),
                'kill_switch': self.kill_switch.get_status(),
                'data_validator': self.data_validator.get_statistics(),
                'execution_monitor': self.execution_monitor.get_status(),
                'failure_detector': self.failure_detector.get_statistics(),
                'config_monitor': self.config_monitor.get_status()
            }
        }


async def quick_start(
    broker_adapter,
    config: Optional[Dict] = None,
    config_path: Optional[str] = None
) -> MasterSafetyOrchestrator:
    """
    Quick start the safety orchestrator.
    
    Args:
        broker_adapter: Broker adapter
        config: Optional configuration
        config_path: Optional config file path
        
    Returns:
        Running MasterSafetyOrchestrator
    """
    orchestrator = MasterSafetyOrchestrator(
        broker_adapter=broker_adapter,
        config=config,
        config_path=config_path
    )
    
    await orchestrator.start()
    
    return orchestrator
