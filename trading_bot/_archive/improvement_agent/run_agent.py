"""
Run Improvement Agent
=====================

Main entry point for running the autonomous improvement agent.

Usage:
    python -m trading_bot.improvement_agent.run_agent [options]
    
Options:
    --mode [observe|propose|supervised|autonomous]
    --focus <module_or_category>
    --skip <module_or_category>
    --interactive
    --report-only
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trading_bot.improvement_agent import (
    ImprovementAgent,
    AgentConfig,
    AgentMode,
    AgentState,
    AgentInterface,
    AnalysisDepth,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'improvement_agent_{datetime.now().strftime("%Y%m%d")}.log'),
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print the agent banner (ASCII-safe)."""
    banner = """
============================================================
   AUTONOMOUS IMPROVEMENT AGENT - Making Your Code Better
============================================================
"""
    print(banner)


def print_help():
    """Print detailed help."""
    help_text = """
AUTONOMOUS IMPROVEMENT AGENT
============================

This agent analyzes your codebase, identifies weaknesses, proposes improvements,
generates tests, and applies approved changes.

MODES:
------
  observe     - Only analyze and report, no proposals
  propose     - Analyze and generate proposals for review
  supervised  - Apply only human-approved changes (DEFAULT)
  autonomous  - Auto-apply safe changes (non-protected files only)

COMMANDS (Interactive Mode):
----------------------------
  start       - Run full improvement cycle
  analyze     - Analyze codebase only
  detect      - Detect weaknesses
  propose     - Generate improvements
  approve     - Approve changes (id=X or all=True)
  reject      - Reject changes (id=X, reason=Y)
  apply       - Apply approved changes
  rollback    - Rollback applied changes
  focus       - Focus on specific area
  skip        - Skip specific area
  status      - Show current status
  report      - Generate report
  help        - Show this help
  quit        - Exit

EXAMPLES:
---------
  # Run in observe mode (analysis only)
  python run_agent.py --mode observe

  # Focus on risk management
  python run_agent.py --focus risk

  # Interactive review session
  python run_agent.py --interactive

  # Generate report only
  python run_agent.py --report-only
"""
    print(help_text)


def run_interactive(interface: AgentInterface):
    """Run in interactive mode."""
    print("\nEntering interactive mode. Type 'help' for commands, 'quit' to exit.\n")
    
    while True:
        try:
            cmd_input = input("agent> ").strip()
            
            if not cmd_input:
                continue
            
            parts = cmd_input.split()
            command = parts[0].lower()
            
            if command == 'quit' or command == 'exit':
                print("Goodbye!")
                break
            
            if command == 'review':
                interface.interactive_review()
                continue
            
            if command == 'status':
                interface.print_status()
                continue
            
            # Parse arguments
            args = {}
            for part in parts[1:]:
                if '=' in part:
                    key, value = part.split('=', 1)
                    # Handle boolean
                    if value.lower() in ['true', 'yes', '1']:
                        value = True
                    elif value.lower() in ['false', 'no', '0']:
                        value = False
                    args[key] = value
                else:
                    # Positional argument
                    if 'target' not in args:
                        args['target'] = part
                    elif 'id' not in args:
                        args['id'] = part
            
            # Execute command
            response = interface.execute_command(command, args)
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
            
            if response.data:
                import json
                print(json.dumps(response.data, indent=2, default=str))
                
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Improvement Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        '--mode',
        choices=['observe', 'propose', 'supervised', 'autonomous'],
        default='supervised',
        help='Agent operating mode (default: supervised)',
    )
    
    parser.add_argument(
        '--path',
        default=None,
        help='Path to codebase (default: current directory)',
    )
    
    parser.add_argument(
        '--focus',
        action='append',
        default=[],
        help='Focus on specific modules or categories (can be repeated)',
    )
    
    parser.add_argument(
        '--skip',
        action='append',
        default=[],
        help='Skip specific modules or categories (can be repeated)',
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode',
    )
    
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report without making changes',
    )
    
    parser.add_argument(
        '--depth',
        choices=['quick', 'standard', 'deep'],
        default='deep',
        help='Analysis depth (default: deep)',
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output',
    )
    
    args = parser.parse_args()
    
    # Print banner
    if not args.quiet:
        print_banner()
    
    # Determine root path
    if args.path:
        root_path = Path(args.path).resolve()
    else:
        # Default to trading_bot directory
        root_path = Path(__file__).parent.parent
    
    if not root_path.exists():
        print(f"Error: Path does not exist: {root_path}")
        sys.exit(1)
    
    print(f"\nAnalyzing: {root_path}")
    print(f"Mode: {args.mode}")
    print(f"Depth: {args.depth}")
    
    # Create config
    depth_map = {
        'quick': AnalysisDepth.SHALLOW,
        'standard': AnalysisDepth.STANDARD,
        'deep': AnalysisDepth.DEEP,
    }
    
    config = AgentConfig(
        mode=AgentMode(args.mode),
        analysis_depth=depth_map[args.depth],
        focus_modules=args.focus,
        skip_modules=args.skip,
    )
    
    # Create agent and interface
    agent = ImprovementAgent(str(root_path), config)
    interface = AgentInterface(agent)
    
    # Add focus/skip directives
    for focus in args.focus:
        agent.focus_on(focus)
        print(f"  Focus: {focus}")
    
    for skip in args.skip:
        agent.skip(skip)
        print(f"  Skip: {skip}")
    
    print()
    
    # Run based on mode
    if args.interactive:
        run_interactive(interface)
    
    elif args.report_only:
        print("Running analysis...")
        agent.analyze_codebase()
        agent.detect_weaknesses()
        
        print("\n" + agent.get_summary_report())
        
        # Save report
        report_path = root_path / f"improvement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path.write_text(agent.get_summary_report(), encoding='utf-8')
        print(f"\nReport saved to: {report_path}")
    
    else:
        print("Starting improvement cycle...")
        
        try:
            run = agent.run_full_cycle()
            
            print("\n" + "=" * 60)
            print("IMPROVEMENT CYCLE COMPLETE")
            print("=" * 60)
            print(f"Run ID: {run.id}")
            print(f"Files Analyzed: {run.files_analyzed}")
            print(f"Weaknesses Found: {run.weaknesses_found}")
            print(f"Improvements Proposed: {run.improvements_proposed}")
            print(f"Tests Generated: {run.tests_generated}")
            print(f"Changes Applied: {run.changes_applied}")
            
            # Show pending changes
            pending = interface.get_pending_for_review()
            if pending:
                print(f"\n{len(pending)} changes awaiting your review.")
                print("Run with --interactive to review and approve changes.")
            
        except Exception as e:
            print(f"\nError during improvement cycle: {e}")
            logger.exception("Improvement cycle failed")
            sys.exit(1)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
