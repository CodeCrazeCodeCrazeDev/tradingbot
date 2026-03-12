"""
AlphaAlgo Integrated System Runner
Runs the complete trading bot with all integrated systems enabled
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/integrated_system_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}


async def run_orchestrator_mode(args):
    """Run with orchestrator system."""
    logger.info("=" * 80)
    logger.info("ALPHAALGO - ORCHESTRATOR MODE")
    logger.info("=" * 80)
    
    try:
        from trading_bot import MasterOrchestrator, TradingMode
        from trading_bot.data import MT5Interface
        
        # Load configuration
        config = load_config('config/orchestrator_config.yaml')
        
        # Initialize MT5
        logger.info("Initializing MT5 connection...")
        mt5 = MT5Interface()
        
        # Map trading mode
        mode_map = {
            'aggressive': TradingMode.AGGRESSIVE,
            'balanced': TradingMode.BALANCED,
            'conservative': TradingMode.CONSERVATIVE,
            'defensive': TradingMode.DEFENSIVE,
            'scalping': TradingMode.SCALPING,
            'swing': TradingMode.SWING,
            'position': TradingMode.POSITION
        }
        
        trading_mode = mode_map.get(
            args.trading_mode or config.get('orchestrator', {}).get('trading_mode', 'balanced'),
            TradingMode.BALANCED
        )
        
        logger.info(f"Trading Mode: {trading_mode.value}")
        logger.info(f"Symbol: {args.symbol}")
        logger.info(f"Mode: {args.mode}")
        
        # Initialize orchestrator
        orchestrator = MasterOrchestrator(
            mt5_interface=mt5,
            symbol=args.symbol,
            trading_mode=trading_mode
        )
        
        logger.info("Orchestrator initialized successfully")
        logger.info("Starting trading loop...")
        
        # Run orchestrator
        await orchestrator.run()
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure all dependencies are installed")
        return False
    except Exception as e:
        logger.error(f"Error running orchestrator: {e}", exc_info=True)
        return False
    
    return True


async def run_with_scanners(args):
    """Run with opportunity scanners enabled."""
    logger.info("=" * 80)
    logger.info("ALPHAALGO - WITH OPPORTUNITY SCANNERS")
    logger.info("=" * 80)
    
    try:
        from trading_bot import (
            MasterOrchestrator,
            TradingMode,
            MarketInefficiencyScanner,
            MomentumBurstDetector
        )
        from trading_bot.data import MT5Interface
        
        # Load configurations
        orch_config = load_config('config/orchestrator_config.yaml')
        scanner_config = load_config('config/opportunity_scanner_config.yaml')
        
        # Initialize MT5
        mt5 = MT5Interface()
        
        # Initialize scanners
        scanners = []
        
        if scanner_config.get('market_inefficiency', {}).get('enabled', True):
            logger.info("Enabling Market Inefficiency Scanner")
            scanners.append(MarketInefficiencyScanner())
        
        if scanner_config.get('momentum', {}).get('enabled', True):
            logger.info("Enabling Momentum Burst Detector")
            scanners.append(MomentumBurstDetector())
        
        logger.info(f"Initialized {len(scanners)} opportunity scanners")
        
        # Initialize orchestrator with scanners
        orchestrator = MasterOrchestrator(
            mt5_interface=mt5,
            symbol=args.symbol,
            trading_mode=TradingMode.BALANCED,
            opportunity_scanners=scanners
        )
        
        logger.info("Starting trading with opportunity scanners...")
        await orchestrator.run()
        
    except Exception as e:
        logger.error(f"Error running with scanners: {e}", exc_info=True)
        return False
    
    return True


async def run_with_adaptive(args):
    """Run with adaptive systems enabled."""
    logger.info("=" * 80)
    logger.info("ALPHAALGO - WITH ADAPTIVE SYSTEMS")
    logger.info("=" * 80)
    
    try:
        from trading_bot import (
            MasterOrchestrator,
            TradingMode,
            AdaptiveTradingMaster
        )
        from trading_bot.data import MT5Interface
        
        # Load configurations
        adaptive_config = load_config('config/adaptive_systems_config.yaml')
        
        # Initialize MT5
        mt5 = MT5Interface()
        
        # Initialize adaptive systems
        logger.info("Initializing Adaptive Trading Master...")
        adaptive_master = AdaptiveTradingMaster()
        
        # Initialize orchestrator with adaptive systems
        orchestrator = MasterOrchestrator(
            mt5_interface=mt5,
            symbol=args.symbol,
            trading_mode=TradingMode.BALANCED,
            adaptive_master=adaptive_master
        )
        
        logger.info("Starting trading with adaptive systems...")
        await orchestrator.run()
        
    except Exception as e:
        logger.error(f"Error running with adaptive systems: {e}", exc_info=True)
        return False
    
    return True


async def run_full_integration(args):
    """Run with all integrated systems enabled."""
    logger.info("=" * 80)
    logger.info("ALPHAALGO - FULL INTEGRATION MODE")
    logger.info("=" * 80)
    logger.info("All integrated systems enabled:")
    logger.info("  ✓ Orchestrator")
    logger.info("  ✓ Opportunity Scanners")
    logger.info("  ✓ Advanced Exit Strategies")
    logger.info("  ✓ Adaptive Systems")
    logger.info("  ✓ Risk Management")
    logger.info("=" * 80)
    
    try:
        from trading_bot import (
            MasterOrchestrator,
            TradingMode,
            MarketInefficiencyScanner,
            MomentumBurstDetector,
            ExitSignalGenerator,
            ProfitMaximizer,
            AdaptiveTradingMaster,
            RiskEngine
        )
        from trading_bot.data import MT5Interface
        
        # Initialize MT5
        logger.info("Initializing MT5 connection...")
        mt5 = MT5Interface()
        
        # Initialize opportunity scanners
        logger.info("Initializing opportunity scanners...")
        scanners = [
            MarketInefficiencyScanner(),
            MomentumBurstDetector()
        ]
        
        # Initialize exit strategies
        logger.info("Initializing exit strategies...")
        exit_generator = ExitSignalGenerator(
            strategies=[ProfitMaximizer()]
        )
        
        # Initialize adaptive systems
        logger.info("Initializing adaptive systems...")
        adaptive_master = AdaptiveTradingMaster()
        
        # Initialize risk management
        logger.info("Initializing risk management...")
        risk_engine = RiskEngine()
        
        # Initialize orchestrator with all systems
        logger.info("Initializing master orchestrator...")
        orchestrator = MasterOrchestrator(
            mt5_interface=mt5,
            symbol=args.symbol,
            trading_mode=TradingMode.BALANCED,
            opportunity_scanners=scanners,
            exit_generator=exit_generator,
            adaptive_master=adaptive_master,
            risk_engine=risk_engine
        )
        
        logger.info("=" * 80)
        logger.info("All systems initialized successfully!")
        logger.info("Starting full integrated trading system...")
        logger.info("=" * 80)
        
        # Run the complete system
        await orchestrator.run()
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Some integrated modules may not be available")
        logger.info("Running validation to check integration status...")
        import subprocess
        subprocess.run([sys.executable, "validate_integrations.py"])
        return False
    except Exception as e:
        logger.error(f"Error running full integration: {e}", exc_info=True)
        return False
    
    return True


async def run_dashboard(args):
    """Run dashboard server."""
    logger.info("=" * 80)
    logger.info("ALPHAALGO - DASHBOARD SERVER")
    logger.info("=" * 80)
    
    try:
        from trading_bot import UnifiedDashboard
        
        logger.info("Initializing dashboard...")
        dashboard = UnifiedDashboard()
        
        port = args.dashboard_port or 8050
        logger.info(f"Starting dashboard on port {port}...")
        logger.info(f"Access dashboard at: http://localhost:{port}")
        
        await dashboard.start(port=port)
        
    except Exception as e:
        logger.error(f"Error running dashboard: {e}", exc_info=True)
        return False
    
    return True


async def run_backtest(args):
    """Run backtesting."""
    logger.info("=" * 80)
    logger.info("ALPHAALGO - BACKTESTING MODE")
    logger.info("=" * 80)
    
    try:
        from trading_bot import AdvancedBacktester, TestMode
        
        logger.info(f"Symbol: {args.symbol}")
        logger.info(f"Start Date: {args.start_date}")
        logger.info(f"End Date: {args.end_date}")
        
        # Initialize backtester
        backtester = AdvancedBacktester(
            strategy=None,  # Will use default strategy
            test_mode=TestMode.MONTE_CARLO
        )
        
        logger.info("Running backtest...")
        results = await backtester.run(
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        # Display results
        logger.info("=" * 80)
        logger.info("BACKTEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"Total Trades: {results.total_trades}")
        logger.info(f"Win Rate: {results.win_rate:.2%}")
        logger.info(f"Profit Factor: {results.profit_factor:.2f}")
        logger.info(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
        logger.info(f"Max Drawdown: {results.max_drawdown:.2%}")
        logger.info(f"Total Return: {results.total_return:.2%}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}", exc_info=True)
        return False
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AlphaAlgo Integrated Trading System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with orchestrator
  python run_integrated_system.py --symbol EURUSD --mode paper --orchestrator
  
  # Run with opportunity scanners
  python run_integrated_system.py --symbol EURUSD --mode paper --enable-scanners
  
  # Run with adaptive systems
  python run_integrated_system.py --symbol EURUSD --mode paper --adaptive
  
  # Run full integration
  python run_integrated_system.py --symbol EURUSD --mode paper --full-integration
  
  # Run dashboard
  python run_integrated_system.py --dashboard
  
  # Run backtest
  python run_integrated_system.py --symbol EURUSD --backtest --start-date 2024-01-01 --end-date 2024-12-31
        """
    )
    
    # Basic arguments
    parser.add_argument('--symbol', type=str, default='EURUSD',
                        help='Trading symbol (default: EURUSD)')
    parser.add_argument('--mode', type=str, choices=['paper', 'live'], default='paper',
                        help='Trading mode (default: paper)')
    
    # Integration modes
    parser.add_argument('--orchestrator', action='store_true',
                        help='Enable orchestrator mode')
    parser.add_argument('--enable-scanners', action='store_true',
                        help='Enable opportunity scanners')
    parser.add_argument('--advanced-exits', action='store_true',
                        help='Enable advanced exit strategies')
    parser.add_argument('--adaptive', action='store_true',
                        help='Enable adaptive systems')
    parser.add_argument('--full-integration', action='store_true',
                        help='Enable all integrated systems')
    
    # Dashboard
    parser.add_argument('--dashboard', action='store_true',
                        help='Run dashboard server')
    parser.add_argument('--dashboard-port', type=int, default=8050,
                        help='Dashboard port (default: 8050)')
    
    # Backtesting
    parser.add_argument('--backtest', action='store_true',
                        help='Run backtesting mode')
    parser.add_argument('--start-date', type=str,
                        help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                        help='Backtest end date (YYYY-MM-DD)')
    
    # Trading mode
    parser.add_argument('--trading-mode', type=str,
                        choices=['aggressive', 'balanced', 'conservative', 'defensive', 'scalping', 'swing', 'position'],
                        help='Trading mode strategy')
    
    # Configuration
    parser.add_argument('--config', type=str,
                        help='Custom configuration file')
    
    args = parser.parse_args()
    
    # Validate mode
    if args.mode == 'live':
        logger.warning("=" * 80)
        logger.warning("WARNING: LIVE TRADING MODE REQUESTED")
        logger.warning("=" * 80)
        response = input("Are you sure you want to enable LIVE trading? (type 'YES' to confirm): ")
        if response != 'YES':
            logger.info("Live trading cancelled. Switching to paper mode.")
            args.mode = 'paper'
        else:
            logger.warning("LIVE TRADING ENABLED - USE AT YOUR OWN RISK")
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Run appropriate mode
    try:
        if args.dashboard:
            asyncio.run(run_dashboard(args))
        elif args.backtest:
            if not args.start_date or not args.end_date:
                logger.error("Backtest requires --start-date and --end-date")
                sys.exit(1)
            asyncio.run(run_backtest(args))
        elif args.full_integration:
            asyncio.run(run_full_integration(args))
        elif args.adaptive:
            asyncio.run(run_with_adaptive(args))
        elif args.enable_scanners:
            asyncio.run(run_with_scanners(args))
        elif args.orchestrator:
            asyncio.run(run_orchestrator_mode(args))
        else:
            logger.info("No integration mode specified. Use --help for options.")
            logger.info("Recommended: --orchestrator or --full-integration")
            parser.print_help()
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
