"""
GETS Command Line Interface

Management and operational CLI for GETS:
- System initialization and shutdown
- Health checks
- Model management
- Champion promotion
- Backtesting
- Configuration management
"""

import argparse
import json
import logging
import sys
from typing import Optional

from . import create_gets
from .types import GETSConfig, ForecastHorizon
from .integration import MarketDataAdapter

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_init(args):
    """Initialize GETS system."""
    print("Initializing GETS...")
    
    config = GETSConfig()
    if args.config:
        # Load config from file
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
            config = GETSConfig(**config_dict)
    
    gets = create_gets(config)
    success = gets.initialize()
    
    if success:
        print("✓ GETS initialized successfully")
        print(f"  Models: Kronos={config.kronos_enabled}, TimesFM={config.timesfm_enabled}, "
              f"Moirai={config.moirai_enabled}, TTM={config.ttm_enabled}")
        
        if args.daemon:
            print("Running in daemon mode (press Ctrl+C to stop)...")
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                print("\nShutting down...")
                gets.shutdown()
    else:
        print("✗ Initialization failed")
        sys.exit(1)


def cmd_health(args):
    """Check system health."""
    print("Checking GETS health...")
    
    gets = create_gets()
    if not gets.initialize():
        print("✗ Failed to initialize")
        sys.exit(1)
    
    status = gets.get_system_status()
    
    print("\nSystem Status:")
    for layer, state in status.items():
        icon = "✓" if state == "INITIALIZED" else "✗"
        print(f"  {icon} {layer}: {state}")
    
    gets.shutdown()


def cmd_signal(args):
    """Generate trading signal."""
    print(f"Generating signal for {args.symbol}...")
    
    gets = create_gets()
    if not gets.initialize():
        print("✗ Failed to initialize")
        sys.exit(1)
    
    # Create market data
    market_data = MarketDataAdapter.from_price_dict(
        price_data={
            'open': args.price * 0.99,
            'high': args.price * 1.01,
            'low': args.price * 0.99,
            'close': args.price,
            'volume': args.volume or 1000000,
            'spread': args.spread or 0.001,
            'volatility': args.volatility or 0.2
        },
        symbol=args.symbol
    )
    
    horizon_map = {
        '1m': ForecastHorizon.IMMEDIATE,
        '5m': ForecastHorizon.SHORT,
        '1h': ForecastHorizon.MEDIUM,
        '1d': ForecastHorizon.LONG,
        '1w': ForecastHorizon.EXTENDED
    }
    horizon = horizon_map.get(args.horizon, ForecastHorizon.SHORT)
    
    signal = gets.generate_signal(market_data, horizon)
    
    print("\nSignal Generated:")
    print(f"  Direction: {signal.direction} ({'BUY' if signal.direction > 0 else 'SELL' if signal.direction < 0 else 'NEUTRAL'})")
    print(f"  Confidence: {signal.confidence:.2%}")
    print(f"  Expected Edge: {signal.expected_edge:.4f} ({signal.expected_edge*10000:.1f} bps)")
    print(f"  Governance: {signal.governance_decision.name}")
    print(f"  Abstain: {signal.abstain_recommended}")
    
    if signal.abstain_reason:
        print(f"  Reason: {signal.abstain_reason}")
    
    print(f"\nDisagreement Geometry:")
    geom = signal.disagreement_geometry
    print(f"  Consensus: {geom.forecast_consensus_score:.2%}")
    print(f"  Entropy: {geom.disagreement_entropy:.2%}")
    if geom.disagreement_pattern:
        print(f"  Pattern: {geom.disagreement_pattern.name}")
    
    gets.shutdown()


def cmd_backtest(args):
    """Run backtest."""
    print("Running backtest...")
    
    gets = create_gets()
    if not gets.initialize():
        print("✗ Failed to initialize")
        sys.exit(1)
    
    print(f"Backtest would run on data from {args.data}")
    print("(Full backtest implementation requires data loader)")
    
    gets.shutdown()


def cmd_evolution(args):
    """Evolution layer commands."""
    gets = create_gets()
    if not gets.initialize():
        print("✗ Failed to initialize")
        sys.exit(1)
    
    if args.subcommand == "status":
        status = gets.get_evolution_status()
        
        print("\nEvolution Status:")
        print(f"  Failure Clusters: {status['failure_clusters']}")
        print(f"  Pending Champions: {status['pending_champions']}")
        print(f"  Sandbox State: {status['sandbox_state']}")
    
    elif args.subcommand == "propose":
        print("Proposing mutations...")
        candidates = gets.layer4_evolution.propose_mutations(gets.config)
        print(f"  Proposed {len(candidates)} mutations")
        
        for c in candidates:
            print(f"    - {c.candidate_id}: {c.mutation_type}")
    
    gets.shutdown()


def cmd_champion(args):
    """Champion management."""
    print(f"Champion command: {args.subcommand}")
    
    if args.subcommand == "list":
        print("Listing champions...")
        # Would integrate with champion registry
        print("  (Champion registry integration pending)")
    
    elif args.subcommand == "promote":
        print(f"Promoting champion: {args.champion_id}")
        # Would trigger Layer 5 governance
        print("  (Promotion requires governance approval)")


def cmd_config(args):
    """Configuration management."""
    if args.subcommand == "show":
        config = GETSConfig()
        print("\nCurrent Configuration:")
        print(json.dumps(config.__dict__, indent=2, default=str))
    
    elif args.subcommand == "save":
        print(f"Saving configuration to {args.file}")
        config = GETSConfig()
        with open(args.file, 'w') as f:
            json.dump(config.__dict__, f, indent=2, default=str)
        print("✓ Configuration saved")
    
    elif args.subcommand == "load":
        print(f"Loading configuration from {args.file}")
        with open(args.file, 'r') as f:
            config_dict = json.load(f)
        print("✓ Configuration loaded")
        print(json.dumps(config_dict, indent=2))


def cmd_serve(args):
    """Run API server."""
    print(f"Starting GETS API server on {args.host}:{args.port}")
    
    try:
        from .api import run_api_server
        run_api_server(host=args.host, port=args.port)
    except ImportError as e:
        print(f"✗ Cannot start server: {e}")
        print("  Install FastAPI: pip install fastapi uvicorn")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='gets',
        description='GETS - Governed Evolving Time-Series Foundation System CLI'
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version='GETS 0.1.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize GETS')
    init_parser.add_argument('--config', help='Configuration file')
    init_parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    # health command
    health_parser = subparsers.add_parser('health', help='Check system health')
    
    # signal command
    signal_parser = subparsers.add_parser('signal', help='Generate trading signal')
    signal_parser.add_argument('symbol', help='Trading symbol')
    signal_parser.add_argument('price', type=float, help='Current price')
    signal_parser.add_argument('--horizon', default='5m', help='Forecast horizon (1m, 5m, 1h, 1d, 1w)')
    signal_parser.add_argument('--volume', type=float, help='Volume')
    signal_parser.add_argument('--spread', type=float, help='Bid-ask spread')
    signal_parser.add_argument('--volatility', type=float, help='Volatility')
    
    # backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest')
    backtest_parser.add_argument('data', help='Path to historical data')
    backtest_parser.add_argument('--output', help='Output file for results')
    
    # evolution command
    evolution_parser = subparsers.add_parser('evolution', help='Evolution layer management')
    evolution_sub = evolution_parser.add_subparsers(dest='subcommand')
    evolution_sub.add_parser('status', help='Show evolution status')
    evolution_sub.add_parser('propose', help='Propose mutations')
    
    # champion command
    champion_parser = subparsers.add_parser('champion', help='Champion management')
    champion_sub = champion_parser.add_subparsers(dest='subcommand')
    champion_sub.add_parser('list', help='List champions')
    promote_parser = champion_sub.add_parser('promote', help='Promote champion')
    promote_parser.add_argument('champion_id', help='Champion ID to promote')
    
    # config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_sub = config_parser.add_subparsers(dest='subcommand')
    config_sub.add_parser('show', help='Show current config')
    save_parser = config_sub.add_parser('save', help='Save config to file')
    save_parser.add_argument('file', help='Output file')
    load_parser = config_sub.add_parser('load', help='Load config from file')
    load_parser.add_argument('file', help='Input file')
    
    # serve command
    serve_parser = subparsers.add_parser('serve', help='Run API server')
    serve_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    serve_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    setup_logging(args.verbose)
    
    # Route to command handler
    commands = {
        'init': cmd_init,
        'health': cmd_health,
        'signal': cmd_signal,
        'backtest': cmd_backtest,
        'evolution': cmd_evolution,
        'champion': cmd_champion,
        'config': cmd_config,
        'serve': cmd_serve
    }
    
    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
