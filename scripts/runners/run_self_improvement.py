#!/usr/bin/env python3
"""
AlphaAlgo Self-Improvement System
Interactive CLI for finding issues, proposing fixes, and applying approved changes.

Usage:
    python run_self_improvement.py [command]

Commands:
    scan      - Scan codebase for issues
    propose   - Generate fix proposals
    review    - Review pending proposals
    apply     - Apply approved changes
    status    - Show current status
    full      - Run full improvement cycle
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.self_improvement.self_improvement_orchestrator import (
    SelfImprovementOrchestrator,
    quick_start
)
from trading_bot.self_improvement.code_analyzer import IssueCategory, IssueSeverity

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print the banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     █████╗ ██╗     ██████╗ ██╗  ██╗ █████╗  █████╗ ██╗      ██████╗  ║
║    ██╔══██╗██║     ██╔══██╗██║  ██║██╔══██╗██╔══██╗██║     ██╔═══██╗ ║
║    ███████║██║     ██████╔╝███████║███████║███████║██║     ██║   ██║ ║
║    ██╔══██║██║     ██╔═══╝ ██╔══██║██╔══██║██╔══██║██║     ██║   ██║ ║
║    ██║  ██║███████╗██║     ██║  ██║██║  ██║██║  ██║███████╗╚██████╔╝ ║
║    ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ║
║                                                                      ║
║                    SELF-IMPROVEMENT SYSTEM                           ║
║                                                                      ║
║    Find Issues → Propose Fixes → Approve → Apply Changes             ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def interactive_menu(orchestrator: SelfImprovementOrchestrator):
    """Run interactive menu."""
    while True:
        print("\n" + "=" * 50)
        print("SELF-IMPROVEMENT MENU")
        print("=" * 50)
        print("\n1. 🔍 Scan codebase for issues")
        print("2. 📝 Generate fix proposals")
        print("3. 👀 Review pending proposals")
        print("4. ✅ Apply approved changes (dry run)")
        print("5. 🚀 Apply approved changes (REAL)")
        print("6. ↩️  Rollback a proposal")
        print("7. 📊 Show status")
        print("8. 💾 Save proposals for offline review")
        print("9. 🔄 Run full cycle")
        print("0. 🚪 Exit")
        print("\n" + "=" * 50)
        
        choice = input("\nSelect option: ").strip()
        
        try:
            if choice == '1':
                max_files = input("Max files to scan (default 100): ").strip()
                max_files = int(max_files) if max_files else 100
                orchestrator.scan(max_files)
                
            elif choice == '2':
                # Ask for filters
                print("\nFilter by severity:")
                print("  1. Critical & High only")
                print("  2. All severities")
                sev_choice = input("Choice (default 2): ").strip()
                
                severities = None
                if sev_choice == '1':
                    severities = [IssueSeverity.CRITICAL, IssueSeverity.HIGH]
                
                max_proposals = input("Max proposals (default 50): ").strip()
                max_proposals = int(max_proposals) if max_proposals else 50
                
                orchestrator.propose(severities=severities, max_proposals=max_proposals)
                
            elif choice == '3':
                orchestrator.review_interactive()
                
            elif choice == '4':
                print("\n[DRY RUN - No actual changes will be made]")
                orchestrator.apply(dry_run=True)
                
            elif choice == '5':
                print("\n⚠️  WARNING: This will modify actual files!")
                confirm = input("Type 'APPLY' to confirm: ").strip()
                if confirm == 'APPLY':
                    orchestrator.apply(dry_run=False)
                else:
                    print("Cancelled.")
                    
            elif choice == '6':
                proposal_id = input("Enter proposal ID to rollback: ").strip()
                if proposal_id:
                    orchestrator.rollback(proposal_id)
                    
            elif choice == '7':
                status = orchestrator.get_status()
                print("\n" + "=" * 50)
                print("CURRENT STATUS")
                print("=" * 50)
                print(f"Last Scan: {status['last_scan'] or 'Never'}")
                print(f"Total Issues: {status['total_issues']}")
                print(f"Total Proposals: {status['total_proposals']}")
                print(f"\nApproval Status:")
                for key, value in status['approval_status'].items():
                    print(f"  • {key}: {value}")
                print("=" * 50)
                
            elif choice == '8':
                path = orchestrator.save_for_offline_review()
                print(f"Saved to: {path}")
                
            elif choice == '9':
                print("\nFull Cycle Options:")
                print("  1. Dry run (safe - no changes)")
                print("  2. Real run (will modify files)")
                run_choice = input("Choice (default 1): ").strip()
                dry_run = run_choice != '2'
                
                if not dry_run:
                    confirm = input("⚠️  This will modify files. Type 'CONFIRM' to proceed: ").strip()
                    if confirm != 'CONFIRM':
                        print("Cancelled.")
                        continue
                
                orchestrator.run_full_cycle(dry_run=dry_run)
                
            elif choice == '0':
                print("\nGoodbye! 👋\n")
                break
                
            else:
                print("Invalid option. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\nInterrupted. Returning to menu...")
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AlphaAlgo Self-Improvement System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_self_improvement.py                  # Interactive mode
    python run_self_improvement.py scan             # Scan for issues
    python run_self_improvement.py propose          # Generate proposals
    python run_self_improvement.py review           # Review proposals
    python run_self_improvement.py apply --dry-run  # Test apply
    python run_self_improvement.py full             # Full cycle
        """
    )
    
    parser.add_argument('command', nargs='?', default='interactive',
                        choices=['interactive', 'scan', 'propose', 'review', 'apply', 'status', 'full'],
                        help='Command to run')
    parser.add_argument('--max-files', type=int, default=100,
                        help='Maximum files to scan')
    parser.add_argument('--max-proposals', type=int, default=50,
                        help='Maximum proposals to generate')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run (no actual changes)')
    parser.add_argument('--critical-only', action='store_true',
                        help='Only critical and high severity issues')
    parser.add_argument('--auto-approve-safe', action='store_true',
                        help='Auto-approve minimal risk proposals')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Initialize orchestrator
    base_path = str(Path(__file__).parent)
    orchestrator = SelfImprovementOrchestrator(base_path)
    
    if args.command == 'interactive':
        interactive_menu(orchestrator)
        
    elif args.command == 'scan':
        orchestrator.scan(args.max_files)
        
    elif args.command == 'propose':
        severities = None
        if args.critical_only:
            severities = [IssueSeverity.CRITICAL, IssueSeverity.HIGH]
        orchestrator.propose(severities=severities, max_proposals=args.max_proposals)
        
    elif args.command == 'review':
        orchestrator.review_interactive()
        
    elif args.command == 'apply':
        if not args.dry_run:
            confirm = input("⚠️  This will modify files. Type 'APPLY' to confirm: ").strip()
            if confirm != 'APPLY':
                print("Cancelled.")
                return
        orchestrator.apply(dry_run=args.dry_run)
        
    elif args.command == 'status':
        status = orchestrator.get_status()
        print("\n" + "=" * 50)
        print("CURRENT STATUS")
        print("=" * 50)
        for key, value in status.items():
            print(f"  {key}: {value}")
        print("=" * 50)
        
    elif args.command == 'full':
        orchestrator.run_full_cycle(
            max_files=args.max_files,
            auto_approve_minimal=args.auto_approve_safe,
            dry_run=args.dry_run if args.dry_run else True
        )


if __name__ == '__main__':
    main()
