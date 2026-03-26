"""
AlphaAlgo Trading Bot - Main Entry Point
=========================================

Event-driven trading bot with service-oriented architecture.
Integrates AAMIS V3, Adaptive Systems, Advanced AI, and Advanced Analysis.

Architecture:
- Event Bus: Central pub/sub for service communication
- Service Registry: Service discovery and lifecycle management
- Background Services: Market data, AI analysis, risk monitoring
- Workflow Engine: Event-driven workflow execution
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Run startup checks before importing other modules
try:
    from trading_bot.core.startup_checks import run_startup_checks
    if not run_startup_checks(auto_fix=True):
        print("\n❌ Startup checks failed. Please fix the issues above.")
        print("Run CHECK_AND_INSTALL_DEPENDENCIES.bat to install missing packages.\n")
        sys.exit(1)
except ImportError:
    print("[WARNING] Startup checks module not available, continuing without checks...")
except Exception as e:
    print(f"[WARNING] Startup checks failed: {e}")
    print("Continuing anyway...")

# Core infrastructure
from trading_bot.core.event_bus import (
    Event, EventBus, EventPriority, EventTypes,
    get_event_bus, create_event_bus
)
from trading_bot.core.service_registry import (
    BaseService, ServiceHealth, ServicePriority, ServiceState,
    ServiceRegistry, get_service_registry, create_service_registry
)
from trading_bot.core.service_factory import (
    ServiceFactory, create_service_factory
)
from trading_bot.background import (
    BackgroundManager, create_background_manager,
    MarketDataService, AIAnalysisService, RiskMonitorService,
    AdaptiveLearningService, SystemHealthService,
    WorkflowEngine, Workflow, WorkflowStep
)
from trading_bot.runtime import load_runtime_config, RuntimeStateStore, RuntimeHealth

logger = logging.getLogger(__name__)

# Setup logging
def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """Configure logging based on config"""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    
    # Create logs directory
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = []
    
    # Console handler
    if log_config.get('console', {}).get('enabled', True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)
    
    # File handler with rotation to prevent disk exhaustion
    if log_config.get('file', {}).get('enabled', True):
        from logging.handlers import RotatingFileHandler
        log_file = log_dir / f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB per file
            backupCount=5  # Keep 5 backup files
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    return logging.getLogger('AlphaAlgo')


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load config from base + environment override with env-var substitution."""
    return load_runtime_config(config_path=config_path)


def get_default_config() -> Dict[str, Any]:
    """Get default configuration"""
    return {
        'app': {
            'name': 'AlphaAlgo Trading Bot',
            'version': '2.0.0',
            'environment': 'development',
        },
        'trading': {
            'mode': 'paper',
            'symbols': ['BTCUSDT', 'ETHUSDT'],
            'timeframes': ['1h', '4h'],
            'max_concurrent_positions': 3,
        },
        'risk': {
            'max_risk_per_trade': 0.02,
            'max_daily_loss': 0.05,
            'max_drawdown': 0.20,
            'max_position_size_pct': 0.10,
        },
        'logging': {
            'level': 'INFO',
            'console': {'enabled': True},
            'file': {'enabled': True},
        }
    }


class TradingBot:
    """
    Main Trading Bot - Event-Driven Architecture
    
    Orchestrates all services through the event bus:
    - Market Data Service: Real-time price streaming
    - AI Analysis Service: AAMIS V3, Adaptive Systems, Advanced AI
    - Risk Monitor Service: Real-time risk checks
    - Adaptive Learning Service: Continuous model improvement
    - System Health Service: Infrastructure monitoring
    
    TIER 1 Services (Core Trading System):
    - MSOS: Market Survival Operating System (VETO power)
    - Risk: Position sizing, drawdown protection
    - Execution: Order routing, fill tracking
    - Signals: Signal generation and validation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('AlphaAlgo.Bot')
        self.running = False
        
        # Event-driven infrastructure
        self.event_bus: Optional[EventBus] = None
        self.registry: Optional[ServiceRegistry] = None
        self.service_factory: Optional[ServiceFactory] = None
        self.background_manager: Optional[BackgroundManager] = None
        
        # Statistics
        self.start_time: Optional[datetime] = None
        self.trades_executed = 0
        self.total_pnl = 0.0
        self.initial_capital = config.get('account', {}).get('initial_capital', 
                                                             config.get('trading', {}).get('initial_capital', 10000.0))
        self.trading_halted = False
        
        # Service integration flags
        self.use_tier1_services = config.get('services', {}).get('enable_tier1', True)
        self.use_tier2_services = config.get('services', {}).get('enable_tier2', False)
        self.use_tier3_services = config.get('services', {}).get('enable_tier3', False)
        self.use_tier4_services = config.get('services', {}).get('enable_tier4', False)
        self.use_tier5_services = config.get('services', {}).get('enable_tier5', False)
        self.state_store = RuntimeStateStore(path=config.get("state", {}).get("runtime_file", "state/runtime_state.json"))
        self.health_server: Optional[RuntimeHealth] = None
        self._restore_state()

    def _restore_state(self) -> None:
        state = self.state_store.load()
        self.trades_executed = int(state.get("trades_executed", self.trades_executed))
        self.total_pnl = float(state.get("total_pnl", self.total_pnl))

    def _persist_state(self) -> None:
        self.state_store.save(
            {
                "running": self.running,
                "trades_executed": self.trades_executed,
                "total_pnl": self.total_pnl,
                "trading_halted": self.trading_halted,
            }
        )
        
    async def initialize(self):
        """Initialize all components and services"""
        self.logger.info("=" * 60)
        self.logger.info("INITIALIZING ALPHAALGO TRADING BOT")
        self.logger.info("Event-Driven Service Architecture")
        self.logger.info("=" * 60)
        
        # Initialize event bus
        self.logger.info("Initializing Event Bus...")
        self.event_bus = get_event_bus()
        
        # Initialize service registry
        self.logger.info("Initializing Service Registry...")
        self.registry = get_service_registry()
        self.registry.set_event_bus(self.event_bus)
        
        # Initialize service factory and create TIER 1/2 services
        self.logger.info("Initializing Service Factory...")
        self.service_factory = create_service_factory(
            registry=self.registry,
            event_bus=self.event_bus,
            config=self.config
        )
        
        # Create TIER 1 services (core trading system)
        if self.use_tier1_services:
            self.logger.info("Creating TIER 1 Services (Core Trading System)...")
            tier1_services = self.service_factory.create_tier1_services()
            self.logger.info(f"  ✓ Created {len(tier1_services)} TIER 1 services")
            
            # Log critical services
            critical_services = ['msos', 'risk', 'execution', 'broker', 'database']
            for svc in critical_services:
                if svc in tier1_services:
                    self.logger.info(f"    ✓ {svc.upper()} service ready")
                else:
                    self.logger.warning(f"    ✗ {svc.upper()} service NOT loaded")
        
        # Create TIER 2 services (enhanced features)
        if self.use_tier2_services:
            self.logger.info("Creating TIER 2 Services (Enhanced Features)...")
            tier2_services = self.service_factory.create_tier2_services()
            self.logger.info(f"  [OK] Created {len(tier2_services)} TIER 2 services")
        
        # Create TIER 3 services (additional modules)
        if self.use_tier3_services:
            self.logger.info("Creating TIER 3 Services (Additional Modules)...")
            tier3_services = self.service_factory.create_tier3_services()
            self.logger.info(f"  [OK] Created {len(tier3_services)} TIER 3 services")
        
        # Create TIER 4 services (complete system)
        if self.use_tier4_services:
            self.logger.info("Creating TIER 4 Services (Complete System)...")
            tier4_services = self.service_factory.create_tier4_services()
            self.logger.info(f"  [OK] Created {len(tier4_services)} TIER 4 services")
        
        # Create TIER 5 services (complete ecosystem)
        if self.use_tier5_services:
            self.logger.info("Creating TIER 5 Services (Complete Ecosystem)...")
            tier5_services = self.service_factory.create_tier5_services()
            self.logger.info(f"  [OK] Created {len(tier5_services)} TIER 5 services")
        
        # Log service creation report
        report = self.service_factory.get_creation_report()
        if report['failed']:
            self.logger.warning(f"Failed to create {len(report['failed'])} services:")
            for name, reason in report['failed'].items():
                self.logger.warning(f"  - {name}: {reason}")
        
        # Initialize background manager with services
        self.logger.info("Initializing Background Services...")
        self.background_manager = create_background_manager(self._get_service_config())
        
        # Subscribe to critical events
        self._setup_event_handlers()
        
        self.logger.info("Initialization complete")
        self.logger.info(f"Services registered: {len(self.registry.get_all_services())}")
        
    def _get_service_config(self) -> Dict[str, Any]:
        """Build service configuration from main config"""
        symbols = self.config.get('trading', {}).get('symbols', ['EURUSD', 'GBPUSD'])
        
        return {
            'market_data': {
                'symbols': symbols,
                'interval': self.config.get('trading', {}).get('tick_interval', 1.0)
            },
            'ai_analysis': {
                'interval': self.config.get('ai', {}).get('analysis_interval', 60)
            },
            'risk_monitor': {
                'interval': self.config.get('risk', {}).get('check_interval', 10),
                'limits': {
                    'max_daily_loss': self.config.get('risk', {}).get('max_daily_loss', 0.05),
                    'max_drawdown': self.config.get('risk', {}).get('max_drawdown', 0.20),
                }
            },
            'adaptive_learning': {
                'interval': self.config.get('ai', {}).get('learning_interval', 300)
            },
            'system_health': {
                'interval': self.config.get('monitoring', {}).get('health_interval', 30)
            }
        }
    
    def _setup_event_handlers(self) -> None:
        """Setup handlers for critical events"""
        # Risk limit breach handler
        self.event_bus.subscribe(
            'main_bot',
            [EventTypes.RISK_LIMIT_BREACH],
            self._on_risk_breach,
            priority=100  # High priority
        )
        
        # Trade execution handler
        self.event_bus.subscribe(
            'main_bot',
            [EventTypes.TRADE_EXECUTED],
            self._on_trade_executed
        )
        
        # AI analysis handler
        self.event_bus.subscribe(
            'main_bot',
            [EventTypes.AI_ANALYSIS_COMPLETE],
            self._on_ai_analysis
        )
        
        # System error handler
        self.event_bus.subscribe(
            'main_bot',
            [EventTypes.SYSTEM_ERROR],
            self._on_system_error,
            priority=100
        )
    
    async def _on_risk_breach(self, event: Event) -> None:
        """Handle risk limit breach"""
        self.logger.critical(f"🚨 RISK BREACH: {event.payload}")
        self.trading_halted = True
        
        # Publish halt event
        await self.event_bus.publish(Event(
            event_type=EventTypes.SYSTEM_ERROR,
            payload={'reason': 'Risk limit breach', 'details': event.payload},
            source='main_bot',
            priority=EventPriority.CRITICAL
        ))
    
    async def _on_trade_executed(self, event: Event) -> None:
        """Handle trade execution"""
        self.trades_executed += 1
        pnl = event.payload.get('pnl', 0)
        self.total_pnl += pnl
        self.logger.info(f"Trade executed: {event.payload.get('symbol')} PnL: ${pnl:,.2f}")
    
    async def _on_ai_analysis(self, event: Event) -> None:
        """Handle AI analysis completion"""
        analyses = event.payload.get('analyses', {})
        self.logger.debug(f"AI Analysis complete: {list(analyses.keys())}")
    
    async def _on_system_error(self, event: Event) -> None:
        """Handle system errors"""
        self.logger.error(f"System error: {event.payload}")
        
    async def start(self):
        """Start the trading bot and all services"""
        self.running = True
        self.start_time = datetime.now()
        
        mode = self.config.get('trading', {}).get('mode', 'paper')
        symbols = self.config.get('trading', {}).get('symbols', [])
        
        self.logger.info("=" * 60)
        self.logger.info(f"STARTING TRADING BOT - {mode.upper()} MODE")
        self.logger.info(f"Symbols: {', '.join(symbols)}")
        self.logger.info("Architecture: Event-Driven Services")
        self.logger.info("=" * 60)
        
        if mode == 'live':
            self.logger.warning("⚠️  LIVE TRADING MODE - REAL MONEY AT RISK!")
            await asyncio.sleep(5)
        
        try:
            # Start runtime health endpoint
            monitoring_cfg = self.config.get("monitoring", {})
            self.health_server = RuntimeHealth(
                self.get_status,
                host=monitoring_cfg.get("health_host", "0.0.0.0"),
                port=int(monitoring_cfg.get("health_port", 8080)),
            )
            await self.health_server.start()

            # Start background services
            await self.background_manager.start()
            
            # Run main control loop
            await self._main_loop()
            
        except asyncio.CancelledError:
            self.logger.info("Trading bot cancelled")
        except Exception as e:
            self.logger.error(f"Trading bot error: {e}")
            raise
        finally:
            await self.shutdown()
            
    async def _main_loop(self):
        """Main control loop - monitors services and handles commands"""
        status_interval = self.config.get('monitoring', {}).get('status_interval', 60)
        iteration = 0
        
        while self.running:
            iteration += 1
            
            try:
                # Check if trading is halted
                if self.trading_halted:
                    self.logger.warning("Trading halted - waiting for manual review")
                    await asyncio.sleep(60)
                    continue
                
                # Log status periodically
                if iteration % (status_interval // 10) == 0:
                    await self._log_status()
                    self._persist_state()
                
                # Check service health
                health_report = self.registry.get_health_report()
                unhealthy = health_report['summary'].get('unhealthy', 0)
                if unhealthy > 0:
                    self.logger.warning(f"Unhealthy services: {unhealthy}")
                
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                self.logger.info("Main loop cancelled")
                break
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self._persist_state()
                await asyncio.sleep(5)
                
    async def _log_status(self):
        """Log current status"""
        uptime = datetime.now() - self.start_time if self.start_time else None
        
        # Get service status
        health = self.registry.get_health_report()
        event_stats = self.event_bus.get_stats()
        
        self.logger.info("\n" + "=" * 50)
        self.logger.info("📊 STATUS REPORT")
        self.logger.info("=" * 50)
        self.logger.info(f"⏱️  Uptime: {uptime}")
        self.logger.info(f"📈 Trades: {self.trades_executed}")
        self.logger.info(f"💰 P&L: ${self.total_pnl:,.2f}")
        self.logger.info(f"🔧 Services: {health['summary']['running']}/{health['summary']['total']} running")
        self.logger.info(f"📨 Events processed: {event_stats['history_size']}")
        self.logger.info(f"⚠️  Dead letters: {event_stats['dead_letter_count']}")
        self.logger.info("=" * 50 + "\n")
        
    async def shutdown(self):
        """Shutdown the trading bot and all services"""
        self.logger.info("Shutting down trading bot...")
        self.running = False
        
        # Stop background services
        if self.background_manager:
            await self.background_manager.stop()
        if self.health_server:
            await self.health_server.stop()
        self._persist_state()
        
        # Unsubscribe from events
        if self.event_bus:
            self.event_bus.unsubscribe('main_bot')
            
        self.logger.info("Trading bot shutdown complete")
        
    def stop(self):
        """Signal the bot to stop"""
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive bot status"""
        return {
            'running': self.running,
            'trading_halted': self.trading_halted,
            'uptime': str(datetime.now() - self.start_time) if self.start_time else None,
            'trades': self.trades_executed,
            'pnl': self.total_pnl,
            'services': self.registry.get_health_report() if self.registry else {},
            'events': self.event_bus.get_stats() if self.event_bus else {},
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='AlphaAlgo Trading Bot - Event-Driven Architecture'
    )
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper',
                       help='Trading mode (default: paper)')
    parser.add_argument('--symbols', nargs='+', help='Symbols to trade')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--status', action='store_true', help='Show system status and exit')
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Override with command line args
    if args.mode:
        config.setdefault('trading', {})['mode'] = args.mode
    if args.symbols:
        config.setdefault('trading', {})['symbols'] = args.symbols
    if args.debug:
        config.setdefault('logging', {})['level'] = 'DEBUG'
        
    # Setup logging
    log = setup_logging(config)
    
    # Print banner
    print_banner(log)
    
    # Create bot
    bot = TradingBot(config)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        log.info("Received shutdown signal")
        bot.stop()
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        log.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.excepthook = global_exception_handler

    try:
        # Run bot
        asyncio.run(run_bot(bot))
    except KeyboardInterrupt:
        log.info("Keyboard interrupt received")
    except Exception as e:
        log.error(f"Fatal error: {e}")
        import traceback
        log.debug(traceback.format_exc())
        sys.exit(1)
        
    log.info("AlphaAlgo Trading Bot exited")


def print_banner(log: logging.Logger) -> None:
    """Print startup banner"""
    print("\n" + "=" * 60)
    log.info("    █████╗ ██╗     ██████╗ ██╗  ██╗ █████╗ ")
    log.info("   ██╔══██╗██║     ██╔══██╗██║  ██║██╔══██╗")
    log.info("   ███████║██║     ██████╔╝███████║███████║")
    log.info("   ██╔══██║██║     ██╔═══╝ ██╔══██║██╔══██║")
    log.info("   ██║  ██║███████╗██║     ██║  ██║██║  ██║")
    log.info("   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝")
    log.info("      ALGORITHMIC TRADING BOT v3.0")
    log.info("      Event-Driven Service Architecture")
    log.info("=" * 60)
    log.info("")
    log.info("Core Services:")
    log.info("  • Market Data Service - Real-time price streaming")
    log.info("  • AI Analysis Service - AAMIS V3, Adaptive Systems")
    log.info("  • Risk Monitor Service - Real-time risk checks")
    log.info("  • Adaptive Learning Service - Continuous improvement")
    log.info("  • System Health Service - Infrastructure monitoring")
    log.info("")
    log.info("Advanced Services:")
    log.info("  • Advanced Features - Quantum, Blockchain, Digital Twin")
    log.info("  • Advanced ML - MAML, Few-Shot, Transfer Learning, NAS")
    log.info("  • Adversarial Systems - Red Team / Blue Team validation")
    log.info("  • Adversarial Curriculum - Anti-cheat, Progressive training")
    log.info("  • Adversarial Decision - Confidence vectors, Decision gates")
    log.info("")
    log.info("Agent & AI Services:")
    log.info("  • Agents - Multi-agent debate system")
    log.info("  • Agents2 - Multi-agent coordination")
    log.info("  • AI - Autonomous tuning, optimization")
    log.info("  • AI Core - Central AI orchestration")
    log.info("  • AI Engineer - Autonomous orchestration with safeguards")
    log.info("")
    log.info("Alpha & Trading Services:")
    log.info("  • Alpha Engine - Core alpha generation, multi-brain")
    log.info("  • Alpha Research - Feature mining, unified alpha brain")
    log.info("  • AlphaAlgo Core - Central governance (G0/G1/G2)")
    log.info("  • AlphaAlgo Institutional - 7-layer institutional framework")
    log.info("  • AlphaAlgo V2 - Next-gen trading system")
    log.info("")
    log.info("Data & Analytics Services:")
    log.info("  • Alerts - Alert management and notifications")
    log.info("  • Alternative Data - Satellite, sentiment analysis")
    log.info("  • Analysis - Market intelligence, HFT defense")
    log.info("  • Analytics - Performance attribution")
    log.info("")
    log.info("Infrastructure Services:")
    log.info("  • API - REST API, rate limiting")
    log.info("  • Approval - Human-in-the-loop approval")
    log.info("  • Arbitrage - Cross-exchange, triangular arbitrage")
    log.info("  • Audit - Trade journal, audit trail")
    log.info("  • Auto Optimizer - Strategy optimization")
    log.info("")
    log.info("Autonomous Services:")
    log.info("  • Autonomous - Self-healing, self-optimization")
    log.info("  • Autonomous Learner - Continuous learning")
    log.info("  • Autonomous Pipeline - Deployment, discovery")
    log.info("")
    log.info("Trading Infrastructure:")
    log.info("  • Backtesting - Strategy testing, walk-forward")
    log.info("  • Blockchain - DeFi, cross-chain arbitrage")
    log.info("  • Brain - Elite brain trading system")
    log.info("  • Bridges - System integration bridges")
    log.info("  • Broker - Broker interface (Binance, IB)")
    log.info("  • Brokers - Multi-broker management")
    log.info("  • Calendar - Session management")
    log.info("  • Cloud Deployer - Auto-deploy to cloud")
    log.info("")
    log.info("Cognitive & Compliance Services:")
    log.info("  • Cognitive Architecture - Multi-layer cognitive system")
    log.info("  • Compliance - Regulatory monitoring")
    log.info("  • Config - Configuration management, feature flags")
    log.info("  • Connectivity - Network, WebSocket, auth management")
    log.info("  • Connectors - Exchange abstraction")
    log.info("")
    log.info("Core & Data Services:")
    log.info("  • Core Systems - Trading orchestrator, circuit breaker")
    log.info("  • Core API - System events, interfaces")
    log.info("  • Critical Fixes - Safety, position management")
    log.info("  • Crypto - DeFi, yield optimization")
    log.info("  • Dashboard - UI panels, performance attribution")
    log.info("  • Data - Data management, Level 2")
    log.info("  • Data Feeds - Real-time WebSocket streaming")
    log.info("  • Data Sources - Yahoo, CoinGecko, FRED providers")
    log.info("  • Database - Database, cache, persistence")
    log.info("")
    log.info("Decision & Analysis Services:")
    log.info("  • Decision Layer - Innovative decision engine")
    log.info("  • DeepChart - Advanced chart analysis, inference")
    log.info("  • Deployment - Multi-symbol management")
    log.info("  • Derivatives - Options, futures, roll management")
    log.info("  • DevOps - CI/CD, changelog generation")
    log.info("  • Diagnostics - System validation, health reports")
    log.info("  • Distributed - Parallel backtesting")
    log.info("")


async def run_bot(bot: TradingBot):
    """Run the trading bot"""
    loop = asyncio.get_running_loop()

    def loop_exception_handler(_loop, context):
        bot.logger.error(f"Global async exception: {context.get('message')}")
        if context.get("exception"):
            bot.logger.exception(context["exception"])

    loop.set_exception_handler(loop_exception_handler)
    await bot.initialize()
    await bot.start()


# ============================================================
# QUICK START FUNCTIONS
# ============================================================

async def quick_start(config: Optional[Dict[str, Any]] = None) -> TradingBot:
    """Quick start function for programmatic use"""
    config = config or get_default_config()
    bot = TradingBot(config)
    await bot.initialize()
    return bot


def create_bot(config: Optional[Dict[str, Any]] = None) -> TradingBot:
    """Create bot instance without starting"""
    config = config or get_default_config()
    return TradingBot(config)


if __name__ == '__main__':
    main()
