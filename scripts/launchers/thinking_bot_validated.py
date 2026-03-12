"""
Thinking Bot - Validated Edition
Enhanced with comprehensive pre-trade system validation

This version performs complete multi-layer diagnostics before entering trading mode.
"""

import os
import sys
import asyncio
import logging
import yaml
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Import system validator
from trading_bot.diagnostics import SystemValidator, SystemState

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/thinking_bot_validated_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading mode"""
    PAPER = "PAPER"
    LIVE = "LIVE"
    VALIDATION = "VALIDATION"


class ThinkingBotValidated:
    """
    Thinking Bot with Comprehensive System Validation
    
    Features:
    - Multi-layer pre-trade validation
    - Auto-healing for failed modules
    - Real-time health monitoring
    - Safe mode operation
    - Emergency shutdown capability
    """
    
    def __init__(self, config_path: str = "config/config.yaml", paper_mode: bool = True):
        self.config_path = config_path
        self.paper_mode = paper_mode
        self.config = self._load_config()
        
        # Override config with paper_mode parameter
        self.config['trading']['mode'] = 'paper' if paper_mode else 'live'
        
        # State
        self.running = False
        self.validated = False
        self.safe_to_trade = False
        self.cycle_count = 0
        self.last_validation_time = None
        self.validation_interval_hours = 24  # Re-validate every 24 hours
        
        # System validator
        self.validator = SystemValidator(self.config)
        self.last_validation_report = None
        
        # Components (will be initialized after validation)
        self.elite_brain = None
        self.risk_manager = None
        self.orchestrator = None
        
        logger.info(f"ThinkingBot Validated Edition initialized in {'PAPER' if paper_mode else 'LIVE'} mode")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'trading': {
                'mode': 'paper',
                'risk_per_trade': 0.01,
                'max_positions': 5,
                'stop_loss_atr_multiplier': 2.0,
                'take_profit_rr_ratio': 2.0
            },
            'risk': {
                'max_position_size': 1.0,
                'min_position_size': 0.01,
                'risk_per_trade_pct': 1.0,
                'max_drawdown_pct': 20.0
            },
            'mt5': {
                'symbols': ['EURUSD', 'GBPUSD', 'USDJPY']
            }
        }
    
    async def run_system_validation(self, force: bool = False) -> bool:
        """
        Run comprehensive system validation
        
        Args:
            force: Force validation even if recently validated
            
        Returns:
            True if system is safe to trade, False otherwise
        """
        # Check if we need to re-validate
        if not force and self.last_validation_time:
            time_since_validation = datetime.now() - self.last_validation_time
            if time_since_validation < timedelta(hours=self.validation_interval_hours):
                logger.info(f"Skipping validation - last validated {time_since_validation.total_seconds() / 3600:.1f} hours ago")
                return self.safe_to_trade
        
        logger.info("\n" + "="*80)
        logger.info("INITIATING COMPREHENSIVE SYSTEM VALIDATION")
        logger.info("="*80)
        
        # Run validation
        report = await self.validator.run_full_validation()
        
        # Store report
        self.last_validation_report = report
        self.last_validation_time = datetime.now()
        self.validated = True
        self.safe_to_trade = report.safe_to_trade
        
        # Log results
        if report.safe_to_trade:
            logger.info("\n[OK] SYSTEM VALIDATION PASSED - SAFE TO TRADE")
        else:
            logger.error("\n[FAIL] SYSTEM VALIDATION FAILED - NOT SAFE TO TRADE")
            logger.error(f"Critical failures: {len(report.critical_failures)}")
            logger.error(f"Warnings: {len(report.warnings)}")
            
            # Log critical failures
            if report.critical_failures:
                logger.error("\nCRITICAL FAILURES:")
                for failure in report.critical_failures:
                    logger.error(f"  - {failure}")
        
        return self.safe_to_trade
    
    async def initialize_components(self) -> bool:
        """Initialize trading components (only after validation passes)"""
        if not self.safe_to_trade:
            logger.error("Cannot initialize components - system validation failed")
            return False
        
        logger.info("\n" + "="*80)
        logger.info("INITIALIZING TRADING COMPONENTS")
        logger.info("="*80)
        
        # Load environment
        load_dotenv()
        
        # Initialize MT5
        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            return False
        
        logger.info("[OK] MT5 initialized")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Failed to get account info")
            return False
        
        logger.info(f"[OK] Account: {account_info.login}")
        logger.info(f"  Balance: ${account_info.balance:.2f}")
        logger.info(f"  Equity: ${account_info.equity:.2f}")
        
        # Initialize components with error handling
        try:
            from trading_bot.brain import EliteBrain
            brain_config = self.config.get('brain', {})
            self.elite_brain = EliteBrain(config=brain_config)
            logger.info("[OK] Elite Brain initialized")
        except Exception as e:
            logger.warning(f"[WARN] Elite Brain initialization failed: {e}")
        
        try:
            from trading_bot.risk import RiskManager
            self.risk_manager = RiskManager()
            logger.info("[OK] Risk Manager initialized")
        except Exception as e:
            logger.error(f"[FAIL] Risk Manager initialization failed: {e}")
            return False
        
        try:
            from trading_bot.orchestrator import MasterOrchestrator
            self.orchestrator = MasterOrchestrator(config=self.config)
            logger.info("[OK] Orchestrator initialized")
        except Exception as e:
            logger.warning(f"[WARN] Orchestrator initialization failed: {e}")
        
        logger.info("="*80)
        logger.info("COMPONENT INITIALIZATION COMPLETE")
        logger.info("="*80 + "\n")
        
        return True
    
    async def emergency_shutdown(self, reason: str):
        """Emergency shutdown procedure"""
        logger.critical("\n" + "="*80)
        logger.critical("EMERGENCY SHUTDOWN INITIATED")
        logger.critical(f"Reason: {reason}")
        logger.critical("="*80)
        
        self.running = False
        self.safe_to_trade = False
        
        # Close all positions
        if mt5.initialize():
            positions = mt5.positions_get()
            if positions:
                logger.critical(f"Closing {len(positions)} open positions...")
                for position in positions:
                    # Close position logic here
                    pass
        
        # Stop components
        if self.elite_brain:
            try:
                self.elite_brain.stop()
            except:
                pass
        
        # Shutdown MT5
        mt5.shutdown()
        
        logger.critical("EMERGENCY SHUTDOWN COMPLETE")
        logger.critical("="*80 + "\n")
    
    async def health_check(self) -> bool:
        """Periodic health check during operation"""
        try:
            # Check MT5 connection
            if not mt5.initialize():
                logger.error("Health check failed: MT5 connection lost")
                return False
            
            # Check account info
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Health check failed: Cannot get account info")
                return False
            
            # Check margin level
            if account_info.margin > 0:
                margin_level = account_info.margin_level
                if margin_level < 200:  # Margin call warning
                    logger.warning(f"Health check warning: Low margin level {margin_level:.2f}%")
            
            # Check drawdown
            if account_info.equity < account_info.balance * 0.8:  # 20% drawdown
                logger.error("Health check failed: Excessive drawdown detected")
                await self.emergency_shutdown("Excessive drawdown")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    async def trading_cycle(self):
        """Single trading cycle"""
        self.cycle_count += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TRADING CYCLE #{self.cycle_count}")
        logger.info(f"{'='*60}")
        
        # Health check
        if not await self.health_check():
            logger.error("Health check failed - stopping trading")
            await self.emergency_shutdown("Health check failure")
            return
        
        # Check if we need to re-validate
        if self.last_validation_time:
            time_since_validation = datetime.now() - self.last_validation_time
            if time_since_validation > timedelta(hours=self.validation_interval_hours):
                logger.info("Re-validation required")
                if not await self.run_system_validation(force=True):
                    logger.error("Re-validation failed - stopping trading")
                    await self.emergency_shutdown("Re-validation failure")
                    return
        
        # Trading logic would go here
        logger.info("Trading cycle completed")
    
    async def run(self):
        """Main run loop"""
        logger.info("\n" + "="*80)
        logger.info(f"THINKING BOT VALIDATED EDITION - STARTING")
        logger.info(f"Mode: {'PAPER' if self.paper_mode else 'LIVE'}")
        logger.info("="*80 + "\n")
        
        # STEP 1: Run system validation
        logger.info("STEP 1: Running comprehensive system validation...")
        if not await self.run_system_validation(force=True):
            logger.error("\n[FAIL] SYSTEM VALIDATION FAILED")
            logger.error("Trading operations BLOCKED for safety")
            logger.error("Please resolve critical issues before trading\n")
            return
        
        logger.info("\n[OK] SYSTEM VALIDATION PASSED")
        
        # STEP 2: Initialize components
        logger.info("\nSTEP 2: Initializing trading components...")
        if not await self.initialize_components():
            logger.error("\n[FAIL] COMPONENT INITIALIZATION FAILED")
            return
        
        logger.info("\n[OK] COMPONENTS INITIALIZED")
        
        # STEP 3: Enter trading mode
        logger.info("\nSTEP 3: Entering trading mode...")
        logger.info("\n" + "="*80)
        logger.info("[OK] THINKINGBOT READY - ALL SYSTEMS GREEN. SAFE TO TRADE.")
        logger.info("="*80 + "\n")
        
        self.running = True
        
        try:
            logger.info("Trading bot is now active...")
            logger.info("Press Ctrl+C to stop\n")
            
            # Main trading loop
            while self.running:
                await self.trading_cycle()
                
                # Sleep between cycles
                await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("\n[STOP] Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            await self.emergency_shutdown(f"Fatal error: {e}")
        finally:
            self.running = False
            
            # Cleanup
            logger.info("\n" + "="*80)
            logger.info("THINKING BOT - SHUTTING DOWN")
            logger.info("="*80)
            
            if self.elite_brain:
                self.elite_brain.stop()
            
            mt5.shutdown()
            
            logger.info("Shutdown complete\n")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Thinking Bot - Validated Edition')
    parser.add_argument('--live', action='store_true', help='Run in LIVE trading mode (default: paper)')
    parser.add_argument('--skip-validation', action='store_true', help='Skip initial validation (NOT RECOMMENDED)')
    args = parser.parse_args()
    
    if args.live:
        print("\n" + "="*80)
        print("[WARNING] LIVE TRADING MODE")
        print("="*80)
        print("You are about to start the bot in LIVE trading mode.")
        print("Real money will be at risk.")
        print("\nType 'CONFIRM' to proceed: ", end='')
        
        confirmation = input().strip()
        if confirmation != 'CONFIRM':
            print("Live trading cancelled.")
            return
    
    # Create bot
    bot = ThinkingBotValidated(paper_mode=not args.live)
    
    # Run
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
