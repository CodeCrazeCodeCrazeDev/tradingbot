"""
Master System Supervisor
Coordinates all phases of self-healing AI system
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from enum import Enum

from .internet_health_validator import InternetHealthValidator, ConnectionHealth
from .module_monitor import ModuleMonitor, ModuleStatus
from .auto_repair_system import AutoRepairSystem, FailureType
from .data_validator import DataValidator, DataIntegrity

logger = logging.getLogger(__name__)


class SystemHealth(Enum):
    """Overall system health"""
    EXCELLENT = "excellent"  # > 95%
    GOOD = "good"            # 85-95%
    ACCEPTABLE = "acceptable"  # 70-85%
    DEGRADED = "degraded"    # 50-70%
    CRITICAL = "critical"    # < 50%


class TradingMode(Enum):
    """Trading operation modes"""
    LIVE = "live"
    PAPER = "paper"
    SAFE_PAPER = "safe_paper"
    OFFLINE = "offline"
    DISABLED = "disabled"


@dataclass
class SystemStatus:
    """Complete system status"""
    timestamp: datetime
    health: SystemHealth
    trading_mode: TradingMode
    internet_health: float
    modules_healthy: int
    modules_total: int
    data_validity_pct: float
    uptime_pct: float
    critical_warnings: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'health': self.health.value,
            'trading_mode': self.trading_mode.value,
            'internet_health': round(self.internet_health, 2),
            'modules_healthy': self.modules_healthy,
            'modules_total': self.modules_total,
            'data_validity_pct': round(self.data_validity_pct, 2),
            'uptime_pct': round(self.uptime_pct, 2),
            'critical_warnings': self.critical_warnings
        }


class SystemSupervisor:
    """
    Master AI System Supervisor for AlphaAlgo.
    Coordinates all self-healing and monitoring phases.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Initialize all subsystems
        logger.info("[INIT] Initializing AI System Supervisor...")
        
        self.internet_validator = InternetHealthValidator(config.get('internet', {}))
        self.module_monitor = ModuleMonitor(config.get('modules', {}))
        self.auto_repair = AutoRepairSystem(config.get('repair', {}))
        self.data_validator = DataValidator(config.get('data_validation', {}))
        
        # System state
        self.trading_mode = TradingMode.DISABLED
        self.system_start_time = datetime.now()
        self.last_health_check = None
        self.is_running = False
        
        # Monitoring tasks
        self.supervisor_task: Optional[asyncio.Task] = None
        
        # Status history
        self.status_history: List[SystemStatus] = []
        
        # Logs
        self.status_log_path = Path(config.get('status_log', 'logs/system_status.log'))
        self.status_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("[OK] AI System Supervisor initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the system and perform startup checks.
        """
        logger.info("=" * 80)
        logger.info("[START] ALPHAALGO AI SYSTEM SUPERVISOR - INITIALIZATION")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Internet Health Validation
            logger.info("\n[PHASE 1] Internet Health Validation")
            logger.info("-" * 80)
            
            is_stable, metrics = await self.internet_validator.validate_with_retry()
            
            if not is_stable:
                logger.critical("[ERROR] Internet connection unstable - cannot start")
                return False
            
            logger.info("[OK] Internet health validated")
            
            # Phase 2: Start Module Monitoring
            logger.info("\n[PHASE 2] Module Monitoring")
            logger.info("-" * 80)
            
            await self.module_monitor.start_monitoring()
            
            # Wait for initial module check
            await asyncio.sleep(5)
            
            all_healthy, unhealthy = self.module_monitor.all_modules_healthy()
            
            if not all_healthy:
                logger.warning(f"[WARNING] Some modules unhealthy: {unhealthy}")
                logger.warning("Attempting repairs...")
                
                for module in unhealthy:
                    await self.module_monitor.handle_module_failure(module)
            
            logger.info("[OK] Module monitoring active")
            
            # Phase 3: System Health Check
            logger.info("\n[PHASE 3] System Health Check")
            logger.info("-" * 80)
            
            status = await self.get_system_status()
            
            logger.info(f"System Health: {status.health.value.upper()}")
            logger.info(f"Modules: {status.modules_healthy}/{status.modules_total} healthy")
            logger.info(f"Data Validity: {status.data_validity_pct:.1f}%")
            
            # Determine if trading is safe
            if status.health in [SystemHealth.EXCELLENT, SystemHealth.GOOD]:
                self.trading_mode = TradingMode.LIVE
                logger.info("[OK] System ready for LIVE trading")
            elif status.health == SystemHealth.ACCEPTABLE:
                self.trading_mode = TradingMode.PAPER
                logger.warning("[WARNING] System in PAPER trading mode")
            else:
                self.trading_mode = TradingMode.DISABLED
                logger.error("[ERROR] Trading DISABLED due to system health")
                return False
            
            logger.info("\n" + "=" * 80)
            logger.info("[OK] SYSTEM INITIALIZATION COMPLETE")
            logger.info("=" * 80 + "\n")
            
            return True
        
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False
    
    async def get_system_status(self) -> SystemStatus:
        """
        Get comprehensive system status.
        """
        # Internet health
        internet_report = self.internet_validator.get_health_report()
        internet_health_pct = 100.0 if internet_report.get('meets_thresholds') else 50.0
        
        # Module health
        module_report = self.module_monitor.get_status_report()
        modules_healthy = sum(
            1 for m in module_report['modules'].values()
            if m['is_healthy']
        )
        modules_total = len(module_report['modules'])
        
        # Data validity
        data_stats = self.data_validator.get_validation_stats()
        data_validity_pct = data_stats.get('valid_pct', 0.0)
        
        # Calculate overall health score
        health_score = (
            internet_health_pct * 0.3 +
            (modules_healthy / modules_total * 100) * 0.4 +
            data_validity_pct * 0.3
        )
        
        # Determine health level
        if health_score > 95:
            health = SystemHealth.EXCELLENT
        elif health_score > 85:
            health = SystemHealth.GOOD
        elif health_score > 70:
            health = SystemHealth.ACCEPTABLE
        elif health_score > 50:
            health = SystemHealth.DEGRADED
        else:
            health = SystemHealth.CRITICAL
        
        # Collect critical warnings
        warnings = []
        
        if not internet_report.get('meets_thresholds'):
            warnings.append("Internet connection unstable")
        
        if modules_healthy < modules_total:
            warnings.append(f"{modules_total - modules_healthy} modules unhealthy")
        
        if data_validity_pct < 90:
            warnings.append(f"Data validity low: {data_validity_pct:.1f}%")
        
        # Calculate uptime
        uptime = (datetime.now() - self.system_start_time).total_seconds()
        uptime_pct = 100.0  # Simplified - would track actual downtime
        
        status = SystemStatus(
            timestamp=datetime.now(),
            health=health,
            trading_mode=self.trading_mode,
            internet_health=internet_health_pct,
            modules_healthy=modules_healthy,
            modules_total=modules_total,
            data_validity_pct=data_validity_pct,
            uptime_pct=uptime_pct,
            critical_warnings=warnings
        )
        
        self.status_history.append(status)
        self.last_health_check = datetime.now()
        
        return status
    
    async def continuous_supervision(self):
        """
        Continuously supervise system health and take corrective actions.
        """
        logger.info("🔍 Starting continuous system supervision...")
        self.is_running = True
        
        check_interval = self.config.get('check_interval', 60)  # 60 seconds
        
        while self.is_running:
            try:
                # Get current status
                status = await self.get_system_status()
                
                # Log status
                self._log_status(status)
                
                # Check if trading mode needs adjustment
                await self._adjust_trading_mode(status)
                
                # Handle critical warnings
                if status.critical_warnings:
                    logger.warning("⚠️ CRITICAL WARNINGS:")
                    for warning in status.critical_warnings:
                        logger.warning(f"   - {warning}")
                
                # Check if system degraded mid-session
                if status.health in [SystemHealth.DEGRADED, SystemHealth.CRITICAL]:
                    logger.error("🚨 SYSTEM DEGRADED - Switching to Safe Paper Mode")
                    await self._enter_safe_mode()
                
                # Wait before next check
                await asyncio.sleep(check_interval)
            
            except Exception as e:
                logger.error(f"Error in continuous supervision: {e}")
                await asyncio.sleep(10)
    
    async def _adjust_trading_mode(self, status: SystemStatus):
        """Adjust trading mode based on system health"""
        previous_mode = self.trading_mode
        
        # Determine appropriate mode
        if status.health == SystemHealth.EXCELLENT:
            new_mode = TradingMode.LIVE
        elif status.health == SystemHealth.GOOD:
            new_mode = TradingMode.LIVE if status.internet_health > 90 else TradingMode.PAPER
        elif status.health == SystemHealth.ACCEPTABLE:
            new_mode = TradingMode.PAPER
        elif status.health == SystemHealth.DEGRADED:
            new_mode = TradingMode.SAFE_PAPER
        else:
            new_mode = TradingMode.DISABLED
        
        # Update mode if changed
        if new_mode != previous_mode:
            logger.warning(f"🔄 Trading mode changed: {previous_mode.value} → {new_mode.value}")
            self.trading_mode = new_mode
            
            # Log mode change
            self._log_mode_change(previous_mode, new_mode, status)
    
    async def _enter_safe_mode(self):
        """Enter safe paper trading mode"""
        logger.warning("⚠️ Entering SAFE PAPER MODE")
        
        self.trading_mode = TradingMode.SAFE_PAPER
        
        # Activate offline mode in failover manager
        await self.auto_repair.failover_manager.activate_offline_mode()
        
        logger.info("System will use cached data only")
        logger.info("Real trading disabled until recovery validated")
    
    async def validate_recovery(self) -> bool:
        """Validate system recovery before resuming trading"""
        logger.info("🔍 Validating system recovery...")
        
        # Check for 15 minutes of stability
        stability_checks = 5
        check_interval = 180  # 3 minutes
        
        for i in range(stability_checks):
            logger.info(f"Stability check {i+1}/{stability_checks}...")
            
            status = await self.get_system_status()
            
            if status.health in [SystemHealth.DEGRADED, SystemHealth.CRITICAL]:
                logger.warning("System still degraded")
                return False
            
            if status.critical_warnings:
                logger.warning(f"Critical warnings present: {status.critical_warnings}")
                return False
            
            if i < stability_checks - 1:
                await asyncio.sleep(check_interval)
        
        logger.info("✅ System recovery validated")
        return True
    
    async def resume_live_trading(self):
        """Resume live trading after recovery"""
        logger.info("🔄 Resuming live trading...")
        
        # Validate recovery
        is_recovered = await self.validate_recovery()
        
        if not is_recovered:
            logger.error("❌ Recovery validation failed - staying in safe mode")
            return False
        
        # Deactivate offline mode
        await self.auto_repair.failover_manager.deactivate_offline_mode()
        
        # Update trading mode
        self.trading_mode = TradingMode.LIVE
        
        logger.info("✅ Live trading resumed")
        return True
    
    def _log_status(self, status: SystemStatus):
        """Log status to file"""
        try:
            with open(self.status_log_path, 'a') as f:
                f.write(json.dumps(status.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Error logging status: {e}")
    
    def _log_mode_change(self, old_mode: TradingMode, new_mode: TradingMode, status: SystemStatus):
        """Log trading mode change"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'event': 'trading_mode_change',
                'old_mode': old_mode.value,
                'new_mode': new_mode.value,
                'system_health': status.health.value,
                'reason': status.critical_warnings
            }
            
            with open(self.status_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error logging mode change: {e}")
    
    async def start(self):
        """Start the system supervisor"""
        # Initialize
        initialized = await self.initialize()
        
        if not initialized:
            logger.critical("❌ System initialization failed")
            return False
        
        # Start supervision
        self.supervisor_task = asyncio.create_task(self.continuous_supervision())
        
        logger.info("✅ System Supervisor started")
        return True
    
    async def stop(self):
        """Stop the system supervisor"""
        logger.info("🛑 Stopping System Supervisor...")
        
        self.is_running = False
        
        # Stop all subsystems
        await self.module_monitor.stop_monitoring()
        
        # Cancel supervision task
        if self.supervisor_task:
            self.supervisor_task.cancel()
            try:
                await self.supervisor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ System Supervisor stopped")
    
    def get_comprehensive_report(self) -> Dict:
        """Generate comprehensive system report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'trading_mode': self.trading_mode.value,
            'uptime_seconds': (datetime.now() - self.system_start_time).total_seconds(),
            'internet_health': self.internet_validator.get_health_report(),
            'module_health': self.module_monitor.get_status_report(),
            'data_validation': self.data_validator.get_validation_stats(),
            'repair_history': self.auto_repair.get_repair_history(),
            'recent_status': [s.to_dict() for s in self.status_history[-10:]]
        }
    
    def save_report(self, filepath: str = 'system_supervisor_report.json'):
        """Save comprehensive report to file"""
        try:
            report = self.get_comprehensive_report()
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"System report saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
