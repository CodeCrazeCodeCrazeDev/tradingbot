"""
AlphaAlgo Master Orchestrator
Coordinates all 5 phases of internet-empowered autonomous trading.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from .connection_validator import ConnectionValidator, ConnectionStatus
from .data_acquisition import DataAcquisitionEngine
from .intelligence_fusion import IntelligenceFusionEngine, FusedDecision
from .security_manager import SecurityManager
from .auto_updater import AutoUpdater

logger = logging.getLogger(__name__)


class AlphaAlgoOrchestrator:
    """
    Master orchestrator for AlphaAlgo's internet-empowered trading system.
    
    Coordinates:
    - Phase 1: Connection validation and monitoring
    - Phase 2: Multi-source data acquisition
    - Phase 3: Intelligence fusion and decision making
    - Phase 4: Security and privacy protection
    - Phase 5: Auto-update and self-learning
    """
    
    def __init__(self, config_path: str = 'config/internet_config.yaml'):
        self.config = self._load_config(config_path)
        
        # Initialize all components
        logger.info("🚀 Initializing AlphaAlgo Internet-Empowered System...")
        
        # Phase 4: Security (initialize first for API key loading)
        self.security = SecurityManager(self.config.get('security', {}))
        
        # Load API keys securely
        api_keys = self.security.load_api_keys()
        self.config['api_keys'] = api_keys
        
        # Phase 1: Connection Validation
        self.connection_validator = ConnectionValidator(self.config.get('connections', {}))
        
        # Phase 2: Data Acquisition
        self.data_engine = DataAcquisitionEngine(
            self.config.get('data_acquisition', {}),
            cache_dir=self.config.get('cache_dir', 'data_cache')
        )
        
        # Phase 3: Intelligence Fusion
        self.fusion_engine = IntelligenceFusionEngine(self.config.get('fusion', {}))
        
        # Phase 5: Auto-Updater
        self.auto_updater = AutoUpdater(self.config.get('auto_update', {}))
        
        # State
        self.is_running = False
        self.trading_enabled = False
        self.symbols = self.config.get('symbols', ['EURUSD', 'GBPUSD'])
        
        logger.info("✅ AlphaAlgo system initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        path = Path(config_path)
        
        if path.exists():
            try:
                import yaml
                with open(path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {config_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Return default configuration
        logger.warning("Using default configuration")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY'],
            'cache_dir': 'data_cache',
            'connections': {
                'endpoints': {
                    'broker_feed': {
                        'url': 'https://api.broker.com/feed',
                        'backup_url': 'https://backup.broker.com/feed'
                    },
                    'economic_api': {
                        'url': 'https://api.tradingeconomics.com/data'
                    },
                    'sentiment_api': {
                        'url': 'https://api.sentiment.com/v1/analyze'
                    },
                    'model_repo': {
                        'url': 'https://models.alphaalgo.com/latest'
                    }
                }
            },
            'data_acquisition': {
                'endpoints': {},
                'api_keys': {}
            },
            'fusion': {
                'fusion_weights': {
                    'technical': 0.60,
                    'sentiment': 0.25,
                    'news': 0.10,
                    'volatility': 0.05
                },
                'min_confidence': 0.6,
                'strong_confidence': 0.8
            },
            'security': {
                'secure_dir': 'secure',
                'known_hashes': {}
            },
            'auto_update': {
                'models_dir': 'models',
                'archive_dir': 'models/archive',
                'update_log': 'update_report.log',
                'update_interval_hours': 24,
                'min_performance': 0.70
            }
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the system and validate all connections.
        Returns True if system is ready for trading.
        """
        logger.info("=" * 80)
        logger.info("🌐 ALPHAALGO INTERNET-EMPOWERED SYSTEM INITIALIZATION")
        logger.info("=" * 80)
        
        # Phase 1: Validate connections
        logger.info("\n📡 PHASE 1: Connection Validation")
        logger.info("-" * 80)
        
        connection_valid = await self.connection_validator.validate_initial_connection()
        
        if not connection_valid:
            logger.critical("❌ Connection validation FAILED - Trading disabled")
            self.trading_enabled = False
            return False
        
        logger.info("✅ All critical connections validated")
        
        # Start connection monitoring
        await self.connection_validator.start_monitoring()
        
        # Phase 4: Security checks
        logger.info("\n🔒 PHASE 4: Security Validation")
        logger.info("-" * 80)
        
        # Verify SSL for critical endpoints
        for name, endpoint in self.connection_validator.endpoints.items():
            if endpoint.critical:
                is_valid, msg = self.security.verify_ssl_certificate(endpoint.url)
                if not is_valid:
                    logger.error(f"SSL validation failed for {name}: {msg}")
                    self.trading_enabled = False
                    return False
        
        logger.info("✅ Security validation passed")
        
        # System ready
        self.trading_enabled = True
        logger.info("\n" + "=" * 80)
        logger.info("✅ ALPHAALGO SYSTEM READY FOR TRADING")
        logger.info("=" * 80 + "\n")
        
        return True
    
    async def run_trading_cycle(self) -> Optional[FusedDecision]:
        """
        Execute a complete trading cycle:
        1. Check connection health
        2. Acquire data from all sources
        3. Fuse intelligence and make decision
        4. Return trading decision
        """
        # Check if trading is allowed
        allowed, reason = self.connection_validator.is_trading_allowed()
        
        if not allowed:
            logger.warning(f"🛑 Trading cycle skipped: {reason}")
            return None
        
        logger.info("\n" + "=" * 80)
        logger.info("🔄 STARTING TRADING CYCLE")
        logger.info("=" * 80)
        
        try:
            # Phase 2: Acquire data
            logger.info("\n📊 PHASE 2: Data Acquisition")
            logger.info("-" * 80)
            
            data_package = await self.data_engine.acquire_all_data(self.symbols)
            
            logger.info(f"✓ Market data: {len(data_package.get('market_data', {}))} timeframes")
            logger.info(f"✓ News: {len(data_package.get('news', []))} articles")
            logger.info(f"✓ Sentiment: {len(data_package.get('sentiment', {}))} symbols")
            logger.info(f"✓ Macro: {len(data_package.get('macro', {}))} indicators")
            
            # Phase 3: Intelligence fusion
            logger.info("\n🧠 PHASE 3: Intelligence Fusion")
            logger.info("-" * 80)
            
            decision = self.fusion_engine.process_data_package(
                data_package,
                symbol=self.symbols[0]
            )
            
            logger.info(f"\n{'=' * 80}")
            logger.info(f"📋 TRADING DECISION")
            logger.info(f"{'=' * 80}")
            logger.info(f"Symbol:     {decision.symbol}")
            logger.info(f"Action:     {decision.action}")
            logger.info(f"Confidence: {decision.confidence:.2%}")
            logger.info(f"Strength:   {decision.strength:.2f}")
            logger.info(f"Risk Score: {decision.risk_score:.2%}")
            logger.info(f"Reasoning:  {decision.reasoning}")
            logger.info(f"{'=' * 80}\n")
            
            return decision
        
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            return None
    
    async def start_autonomous_operation(self):
        """
        Start fully autonomous operation:
        - Continuous connection monitoring
        - Regular trading cycles
        - 24-hour auto-update cycles
        """
        if self.is_running:
            logger.warning("System already running")
            return
        
        logger.info("🚀 Starting autonomous operation...")
        
        # Initialize system
        if not await self.initialize():
            logger.critical("System initialization failed - cannot start")
            return
        
        self.is_running = True
        
        # Start auto-updater
        await self.auto_updater.start()
        
        # Main trading loop
        logger.info("\n🔄 Entering main trading loop...")
        
        trading_interval = self.config.get('trading_interval_minutes', 5)
        
        while self.is_running:
            try:
                # Run trading cycle
                decision = await self.run_trading_cycle()
                
                if decision and decision.action != 'HOLD':
                    logger.info(f"💡 Trading signal generated: {decision.action} {decision.symbol}")
                    # Here you would execute the trade via your broker
                
                # Wait for next cycle
                logger.info(f"⏰ Next cycle in {trading_interval} minutes...")
                await asyncio.sleep(trading_interval * 60)
            
            except asyncio.CancelledError:
                logger.info("Trading loop cancelled")
                break
            
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
        
        logger.info("Autonomous operation stopped")
    
    async def stop(self):
        """Stop all operations gracefully"""
        logger.info("🛑 Stopping AlphaAlgo system...")
        
        self.is_running = False
        
        # Stop all components
        await self.connection_validator.stop_monitoring()
        await self.auto_updater.stop()
        
        logger.info("✅ System stopped")
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'is_running': self.is_running,
            'trading_enabled': self.trading_enabled,
            'symbols': self.symbols,
            'connections': self.connection_validator.get_status_report(),
            'fusion_stats': self.fusion_engine.get_performance_stats(),
            'security': self.security.get_security_report(),
            'auto_updater': self.auto_updater.get_status_report()
        }
    
    def save_status_report(self, filepath: str = 'alphaalgo_status.json'):
        """Save system status to file"""
        try:
            status = self.get_system_status()
            
            with open(filepath, 'w') as f:
                json.dump(status, f, indent=2)
            
            logger.info(f"Status report saved to {filepath}")
        
        except Exception as e:
            logger.error(f"Failed to save status report: {e}")


async def main():
    """Main entry point for AlphaAlgo"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create orchestrator
    orchestrator = AlphaAlgoOrchestrator()
    
    try:
        # Start autonomous operation
        await orchestrator.start_autonomous_operation()
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ Keyboard interrupt received")
    
    finally:
        await orchestrator.stop()
        orchestrator.save_status_report()


if __name__ == '__main__':
    asyncio.run(main())
