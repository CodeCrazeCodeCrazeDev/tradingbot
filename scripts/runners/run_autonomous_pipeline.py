"""
Autonomous Pipeline - Main Entry Point

This script runs the complete autonomous workflow:
1. Discovers new data sources and models
2. Sandboxes them for isolated testing
3. Runs automated tests
4. Requests human approval
5. Deploys approved items to live production

Usage:
    python run_autonomous_pipeline.py [options]

Options:
    --discover-only     Only run discovery phase
    --test-only         Only run testing phase
    --deploy-only       Only run deployment phase
    --auto-approve      Auto-approve low-risk items
    --no-gradual        Skip gradual deployment

Author: AlphaAlgo Trading System
"""

import asyncio
import argparse
import logging
from pathlib import Path

from trading_bot.autonomous_pipeline import (
    AutonomousPipelineOrchestrator,
    PipelineConfig,
    quick_start
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autonomous_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    AUTONOMOUS PIPELINE SYSTEM                                 ║
║                                                                                ║
║  Discover → Sandbox → Test → Approve → Deploy                                ║
║                                                                                ║
║  Automatically finds, tests, and deploys new data sources and models          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def run_full_pipeline(args):
    """Run complete autonomous pipeline"""
    print_banner()
    
    # Create configuration
    config = PipelineConfig(
        enable_data_discovery=True,
        enable_model_discovery=True,
        require_human_approval=not args.auto_approve,
        auto_approve_low_risk=args.auto_approve,
        gradual_deployment=not args.no_gradual
    )
    
    # Create pipeline
    pipeline = AutonomousPipelineOrchestrator(config)
    
    try:
        # Run pipeline
        run = await pipeline.run_pipeline()
        
        # Print results
        print("\n" + "=" * 80)
        print("PIPELINE RUN COMPLETE")
        print("=" * 80)
        print(f"Run ID: {run.run_id}")
        print(f"Status: {run.status.value}")
        print(f"\nResults:")
        print(f"  Discovered: {run.items_discovered}")
        print(f"  Tested: {run.items_tested}")
        print(f"  Approved: {run.items_approved}")
        print(f"  Deployed: {run.items_deployed}")
        print(f"  Failed: {run.items_failed}")
        
        # Show pending approvals
        pending = pipeline.get_pending_approvals()
        if pending:
            print(f"\n⚠️  {len(pending)} items awaiting human approval")
            print(f"Review approval requests in: {pipeline.approval_system.approval_dir}")
            print("\nTo approve items, use:")
            print("  python approve_items.py")
        
        # Show statistics
        stats = pipeline.get_statistics()
        print(f"\nOverall Statistics:")
        print(f"  Total Runs: {stats['total_runs']}")
        print(f"  Total Discovered: {stats['total_discovered']}")
        print(f"  Total Deployed: {stats['total_deployed']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")
        
        print("=" * 80)
        
    finally:
        await pipeline.cleanup()


async def run_discovery_only(args):
    """Run discovery phase only"""
    print_banner()
    print("Running DISCOVERY phase only...\n")
    
    from trading_bot.autonomous_pipeline import DiscoveryEngine
    
    engine = DiscoveryEngine()
    items = await engine.discover_everything()
    
    print(f"\nDiscovered {len(items)} items:")
    for item in items[:20]:  # Show top 20
        print(f"  - {item.name} ({item.item_type.value}) - Score: {item.quality_score:.2f}")
    
    # Save results
    engine.save_discoveries("discoveries.json")
    print(f"\nResults saved to: discoveries.json")


async def run_testing_only(args):
    """Run testing phase only"""
    print_banner()
    print("Running TESTING phase only...\n")
    
    from trading_bot.autonomous_pipeline import AutomatedTester
    
    tester = AutomatedTester()
    
    # Load discoveries
    import json
    with open("discoveries.json", 'r') as f:
        discoveries = json.load(f)
    
    print(f"Testing {len(discoveries)} items...\n")
    
    for item_data in discoveries[:10]:  # Test top 10
        item_name = item_data['name']
        print(f"Testing: {item_name}")
        
        # Run tests
        suite = await tester.test_data_source(item_name, None)
        
        status = "✓ PASSED" if suite.status.value == "passed" else "✗ FAILED"
        print(f"  {status} - Score: {suite.overall_score:.2f}\n")


async def run_deployment_only(args):
    """Run deployment phase only"""
    print_banner()
    print("Running DEPLOYMENT phase only...\n")
    
    from trading_bot.autonomous_pipeline import DeploymentPipeline
    
    pipeline = DeploymentPipeline()
    
    # Get approved items
    print("Deploying approved items...")
    
    # In production, would get actual approved items
    print("No approved items found. Run full pipeline first.")


async def interactive_mode():
    """Interactive mode for managing pipeline"""
    print_banner()
    
    pipeline = await quick_start()
    
    while True:
        print("\n" + "=" * 80)
        print("AUTONOMOUS PIPELINE - INTERACTIVE MODE")
        print("=" * 80)
        print("\nOptions:")
        print("  [1] Run full pipeline")
        print("  [2] View pending approvals")
        print("  [3] Approve item")
        print("  [4] Reject item")
        print("  [5] View statistics")
        print("  [6] View deployment status")
        print("  [Q] Quit")
        print()
        
        choice = input("Select option: ").strip().upper()
        
        if choice == '1':
            print("\nRunning pipeline...")
            run = await pipeline.run_pipeline()
            print(f"\nPipeline complete: {run.status.value}")
            
        elif choice == '2':
            pending = pipeline.get_pending_approvals()
            print(f"\nPending approvals: {len(pending)}")
            for i, request in enumerate(pending, 1):
                print(f"\n{i}. {request.item_name}")
                print(f"   Type: {request.item_type}")
                print(f"   Test Score: {request.test_score:.1%}")
                print(f"   Risk Level: {request.risk_level}")
                print(f"   Request ID: {request.request_id}")
            
        elif choice == '3':
            request_id = input("Enter request ID to approve: ").strip()
            comments = input("Comments (optional): ").strip() or None
            
            if pipeline.approve_item(request_id, comments=comments):
                print("✓ Item approved")
            else:
                print("✗ Failed to approve")
            
        elif choice == '4':
            request_id = input("Enter request ID to reject: ").strip()
            comments = input("Reason for rejection: ").strip() or None
            
            if pipeline.reject_item(request_id, comments=comments):
                print("✓ Item rejected")
            else:
                print("✗ Failed to reject")
            
        elif choice == '5':
            stats = pipeline.get_statistics()
            print("\nPipeline Statistics:")
            print(f"  Total Runs: {stats['total_runs']}")
            print(f"  Total Discovered: {stats['total_discovered']}")
            print(f"  Total Tested: {stats['total_tested']}")
            print(f"  Total Approved: {stats['total_approved']}")
            print(f"  Total Deployed: {stats['total_deployed']}")
            print(f"  Success Rate: {stats['success_rate']:.1%}")
            
        elif choice == '6':
            status = pipeline.get_pipeline_status()
            print("\nPipeline Status:")
            print(f"  Current Status: {status['status']}")
            print(f"  Total Runs: {status['total_runs']}")
            print(f"  Pending Approvals: {status['pending_approvals']}")
            print(f"  Active Deployments: {status['active_deployments']}")
            
        elif choice == 'Q':
            print("\nShutting down...")
            await pipeline.cleanup()
            break
        
        else:
            print("Invalid option")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Autonomous Pipeline System')
    parser.add_argument('--discover-only', action='store_true', help='Only run discovery')
    parser.add_argument('--test-only', action='store_true', help='Only run testing')
    parser.add_argument('--deploy-only', action='store_true', help='Only run deployment')
    parser.add_argument('--auto-approve', action='store_true', help='Auto-approve low-risk items')
    parser.add_argument('--no-gradual', action='store_true', help='Skip gradual deployment')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    try:
        if args.interactive:
            await interactive_mode()
        elif args.discover_only:
            await run_discovery_only(args)
        elif args.test_only:
            await run_testing_only(args)
        elif args.deploy_only:
            await run_deployment_only(args)
        else:
            await run_full_pipeline(args)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
