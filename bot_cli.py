"""
Bot Command Line Interface
Interactive CLI for the trading bot with self-awareness
"""

import sys
import argparse
from trading_bot.core.self_awareness import BotSelfAwareness


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AlphaAlgo Trading Bot - Self-Aware CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py bot_cli.py --help deploy      # Get deployment help
  py bot_cli.py --help upgrade     # Get upgrade help
  py bot_cli.py --status           # Show bot status
  py bot_cli.py --capabilities     # Show capabilities
  py bot_cli.py --docs             # Show documentation index
        """
    )
    
    parser.add_argument('--help-topic', '--help', dest='help_topic',
                       help='Get help on specific topic (deploy, upgrade, test, config)')
    
    parser.add_argument('--status', action='store_true',
                       help='Show bot status report')
    
    parser.add_argument('--capabilities', action='store_true',
                       help='Show bot capabilities')
    
    parser.add_argument('--docs', action='store_true',
                       help='Show documentation index')
    
    parser.add_argument('--save-report', action='store_true',
                       help='Save status report to JSON')
    
    args = parser.parse_args()
    
    # Create self-aware bot
    bot = BotSelfAwareness()
    
    # Handle commands
    if args.help_topic:
        print(bot.help(args.help_topic))
    
    elif args.status:
        import json
        report = bot.get_status_report()
        print(json.dumps(report, indent=2))
    
    elif args.capabilities:
        print(bot.get_capabilities_summary())
    
    elif args.docs:
        print(bot.get_documentation_index())
    
    elif args.save_report:
        result = bot.save_status_report()
        print(result)
    
    else:
        # Default: show general help
        print(bot.help())


if __name__ == '__main__':
    main()
