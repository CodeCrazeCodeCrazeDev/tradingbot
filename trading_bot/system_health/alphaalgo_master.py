"""
AlphaAlgo Master Controller
PHASE 5: Final validation and launch control with safety protocols.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path
import json

from .health_monitor import SystemHealthMonitor, HealthStatus, ComponentStatus
from .auto_repair import AutoRepairEngine
from .stability_tester import StabilityTester
from .intelligent_learner import IntelligentLearner

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading modes."""
    DISABLED = "disabled"
    PAPER_TRADING = "paper_trading"
    SAFE_MODE = "safe_mode"
    LIVE_TRADING = "live_trading"


class AlphaAlgoMaster:
    """
    AlphaAlgo Master Controller
    
    Orchestrates all 5 phases:
    1. System Diagnostics
    2. Auto-Fix & Validation
    3. Performance Stability Test
    4. Intelligent Self-Improvement
    5. Final Validation & Launch
    
    Ensures the bot is self-healing, safe, and adaptive.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AlphaAlgo master controller."""
        self.config = config
        
        # Initialize all components
        self.health_monitor = SystemHealthMonitor(config.get('health_monitor', {}))
        self.auto_repair = AutoRepairEngine(config.get('auto_repair', {}))
        self.stability_tester = StabilityTester(config.get('stability_tester', {}))
        self.intelligent_learner = IntelligentLearner(config.get('intelligent_learner', {}))
        
        # State
        self.current_mode = TradingMode.DISABLED
        self.all_checks_passed = False
        self.system_health_percent = 0.0
        self.last_validation_time = None
        
        # Safety thresholds
        self.min_health_for_live = config.get('min_health_for_live', 95.0)
        self.revalidation_interval_hours = config.get('revalidation_interval_hours', 1)
        
        # Paths
        self.log_dir = Path(config.get('log_dir', 'diagnostics/system_health'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("=" * 80)
        logger.info("AlphaAlgo Master Controller Initialized")
        logger.info("=" * 80)
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """
        Run complete 5-phase validation sequence.
        
        Returns:
            Validation results and trading mode recommendation
        """
        logger.info("\n" + "=" * 80)
        logger.info("ALPHAALGO FULL SYSTEM VALIDATION")
        logger.info("=" * 80)
        logger.info(f"Timestamp: {datetime.now()}")
        logger.info("=" * 80)
        
        validation_results = {
            'timestamp': datetime.now(),
            'phases': {},
            'all_checks_passed': False,
            'recommended_mode': TradingMode.DISABLED,
            'system_health': 0.0
        }
        
        try:
            # PHASE 1: System Diagnostics
            logger.info("\n🔍 Starting Phase 1: System Diagnostics...")
            diagnostics = await self.health_monitor.run_full_diagnostics()
            validation_results['phases']['diagnostics'] = diagnostics
            
            # PHASE 2: Auto-Fix & Validation
            logger.info("\n🛠️ Starting Phase 2: Auto-Fix & Validation...")
            repair_results = await self.auto_repair.repair_all_issues(diagnostics)
            validation_results['phases']['repairs'] = repair_results
            
            # Re-run diagnostics after repairs
            logger.info("\n🔍 Re-validating after repairs...")
            post_repair_diagnostics = await self.health_monitor.run_full_diagnostics()
            validation_results['phases']['post_repair_diagnostics'] = post_repair_diagnostics
            
            # PHASE 3: Performance Stability Test
            logger.info("\n🧩 Starting Phase 3: Performance Stability Test...")
            stability_results = await self.stability_tester.run_stability_test()
            validation_results['phases']['stability'] = stability_results
            
            # Verify backtest data
            backtest_verification = await self.stability_tester.verify_backtest_data()
            validation_results['phases']['backtest_data'] = backtest_verification
            
            # PHASE 4: Enable Learning Mode
            logger.info("\n🧠 Phase 4: Intelligent Self-Improvement Enabled")
            logger.info("  Learning mode: ACTIVE")
            logger.info("  Performance tracking: ENABLED")
            validation_results['phases']['learning'] = {
                'enabled': True,
                'performance_summary': self.intelligent_learner.get_performance_summary()
            }
            
            # PHASE 5: Final Validation & Launch Decision
            logger.info("\n✅ Starting Phase 5: Final Validation & Launch Decision...")
            final_decision = self._make_launch_decision(validation_results)
            validation_results.update(final_decision)
            
            # Update state
            self.all_checks_passed = validation_results['all_checks_passed']
            self.system_health_percent = validation_results['system_health']
            self.current_mode = validation_results['recommended_mode']
            self.last_validation_time = datetime.now()
            
            # Log results
            self._log_validation_results(validation_results)
            
            # Display final status
            self._display_final_status(validation_results)
            
            return validation_results
        
        except Exception as e:
            logger.error(f"Critical error during validation: {e}", exc_info=True)
            validation_results['error'] = str(e)
            validation_results['recommended_mode'] = TradingMode.DISABLED
            return validation_results
    
    def _make_launch_decision(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make final decision on trading mode based on all validation results.
        
        Returns:
            Decision with mode recommendation and reasoning
        """
        decision = {
            'all_checks_passed': False,
            'recommended_mode': TradingMode.DISABLED,
            'system_health': 0.0,
            'reasons': [],
            'critical_issues': []
        }
        
        # Get latest diagnostics
        diagnostics = validation_results['phases'].get('post_repair_diagnostics', {})
        stability = validation_results['phases'].get('stability', {})
        
        # Calculate system health
        system_health = diagnostics.get('overall_health', 0.0)
        
        # Adjust for stability
        if stability.get('stability_score', 0) < 90:
            system_health *= 0.9
            decision['reasons'].append(f"Stability score {stability.get('stability_score', 0):.1f}% below 90%")
        
        # Adjust for errors
        if stability.get('errors'):
            system_health -= len(stability['errors']) * 2
            decision['reasons'].append(f"{len(stability['errors'])} errors during stability test")
        
        decision['system_health'] = max(0.0, system_health)
        
        # Check for critical component failures
        for component_name, component_data in diagnostics.get('components', {}).items():
            if component_data['status'] == ComponentStatus.FAILED:
                decision['critical_issues'].append(f"{component_name} FAILED")
        
        # Make decision
        if decision['critical_issues']:
            # Critical failures - enter safe mode
            decision['recommended_mode'] = TradingMode.SAFE_MODE
            decision['all_checks_passed'] = False
            decision['reasons'].append("Critical component failures detected")
            logger.warning("⚠️  CRITICAL FAILURES - Entering SAFE MODE")
        
        elif decision['system_health'] >= self.min_health_for_live:
            # All systems healthy - allow live trading
            decision['recommended_mode'] = TradingMode.LIVE_TRADING
            decision['all_checks_passed'] = True
            decision['reasons'].append(f"System health {decision['system_health']:.1f}% >= {self.min_health_for_live}%")
            logger.info("✅ ALL CHECKS PASSED - LIVE TRADING AUTHORIZED")
        
        elif decision['system_health'] >= 80:
            # Good health but not perfect - paper trading
            decision['recommended_mode'] = TradingMode.PAPER_TRADING
            decision['all_checks_passed'] = False
            decision['reasons'].append(f"System health {decision['system_health']:.1f}% below {self.min_health_for_live}%")
            logger.warning("⚠️  DEGRADED PERFORMANCE - Paper Trading Mode")
        
        else:
            # Poor health - safe mode only
            decision['recommended_mode'] = TradingMode.SAFE_MODE
            decision['all_checks_passed'] = False
            decision['reasons'].append(f"System health {decision['system_health']:.1f}% too low")
            logger.error("❌ POOR SYSTEM HEALTH - Safe Mode Only")
        
        return decision
    
    def _display_final_status(self, validation_results: Dict[str, Any]):
        """Display final validation status."""
        logger.info("\n" + "=" * 80)
        logger.info("FINAL VALIDATION STATUS")
        logger.info("=" * 80)
        
        logger.info(f"System Health: {validation_results['system_health']:.1f}%")
        logger.info(f"All Checks Passed: {validation_results['all_checks_passed']}")
        logger.info(f"Recommended Mode: {validation_results['recommended_mode'].value.upper()}")
        
        if validation_results['reasons']:
            logger.info("\nReasons:")
            for reason in validation_results['reasons']:
                logger.info(f"  • {reason}")
        
        if validation_results['critical_issues']:
            logger.error("\nCritical Issues:")
            for issue in validation_results['critical_issues']:
                logger.error(f"  ❌ {issue}")
        
        logger.info("\n" + "=" * 80)
        
        # Safety reminder
        if validation_results['recommended_mode'] != TradingMode.LIVE_TRADING:
            logger.warning("⚠️  LIVE TRADING NOT AUTHORIZED")
            logger.warning("⚠️  System must achieve 95%+ health for live trading")
        else:
            logger.info("✅ LIVE TRADING AUTHORIZED")
            logger.info("✅ All safety checks passed")
    
    def _log_validation_results(self, validation_results: Dict[str, Any]):
        """Log validation results to file."""
        log_file = self.log_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert to JSON-serializable format
        log_data = {
            'timestamp': validation_results['timestamp'].isoformat(),
            'system_health': validation_results['system_health'],
            'all_checks_passed': validation_results['all_checks_passed'],
            'recommended_mode': validation_results['recommended_mode'].value,
            'reasons': validation_results['reasons'],
            'critical_issues': validation_results['critical_issues'],
            'phases': {}
        }
        
        # Add phase results (simplified)
        for phase_name, phase_data in validation_results['phases'].items():
            if isinstance(phase_data, dict):
                log_data['phases'][phase_name] = {
                    k: v for k, v in phase_data.items()
                    if k not in ['components', 'actions']  # Exclude large nested data
                }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        logger.info(f"\nValidation results logged to: {log_file}")
    
    async def continuous_monitoring(self):
        """
        Run continuous monitoring and re-validation.
        Re-validates every hour automatically.
        """
        logger.info("Starting continuous monitoring...")
        logger.info(f"Re-validation interval: {self.revalidation_interval_hours} hour(s)")
        
        while True:
            try:
                # Wait for revalidation interval
                await asyncio.sleep(self.revalidation_interval_hours * 3600)
                
                logger.info("\n" + "=" * 80)
                logger.info("SCHEDULED RE-VALIDATION")
                logger.info("=" * 80)
                
                # Run validation
                results = await self.run_full_validation()
                
                # Check if mode changed
                if results['recommended_mode'] != self.current_mode:
                    logger.warning(f"⚠️  MODE CHANGE: {self.current_mode.value} → {results['recommended_mode'].value}")
                    self.current_mode = results['recommended_mode']
                    
                    # Alert developer if downgrade
                    if results['recommended_mode'] in [TradingMode.SAFE_MODE, TradingMode.DISABLED]:
                        await self._alert_developer(results)
            
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _alert_developer(self, validation_results: Dict[str, Any]):
        """Alert developer with diagnostic report."""
        logger.error("\n" + "=" * 80)
        logger.error("🚨 DEVELOPER ALERT")
        logger.error("=" * 80)
        logger.error(f"System health degraded to {validation_results['system_health']:.1f}%")
        logger.error(f"Mode: {validation_results['recommended_mode'].value}")
        
        if validation_results['critical_issues']:
            logger.error("\nCritical Issues:")
            for issue in validation_results['critical_issues']:
                logger.error(f"  ❌ {issue}")
        
        logger.error("\nRecommendations:")
        for reason in validation_results['reasons']:
            logger.error(f"  • {reason}")
        
        logger.error("=" * 80)
        
        # In production: send email/SMS/Telegram alert
    
    async def record_trade_loss(self, trade: Dict[str, Any]):
        """
        Record a losing trade for learning.
        
        Args:
            trade: Trade data
        """
        await self.intelligent_learner.record_trade_loss(trade)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'current_mode': self.current_mode.value,
            'all_checks_passed': self.all_checks_passed,
            'system_health': self.system_health_percent,
            'last_validation': self.last_validation_time.isoformat() if self.last_validation_time else None,
            'strategy_weights': self.intelligent_learner.get_current_weights(),
            'performance_summary': self.intelligent_learner.get_performance_summary()
        }
    
    def can_trade_live(self) -> bool:
        """Check if live trading is authorized."""
        return self.all_checks_passed and self.current_mode == TradingMode.LIVE_TRADING
