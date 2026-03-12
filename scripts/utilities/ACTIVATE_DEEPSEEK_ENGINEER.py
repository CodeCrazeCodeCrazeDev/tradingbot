"""
DeepSeek-Coder-6.7B Activation Script
Initializes and activates the autonomous AI engineer for AlphaAlgo

This script:
1. Loads Windsurf context
2. Initializes DeepSeek inference connection
3. Runs initial audit
4. Starts autonomous engineering cycles
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.ai_engineer import (
    AutonomousOrchestrator,
    DeepSeekConfig,
    InferenceBackend,
    IntegratedSafeguardSystem
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'deepseek' / f'activation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print activation banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              🤖 DeepSeek-Coder-6.7B Autonomous Engineer 🤖                   ║
║                                                                              ║
║                    AlphaAlgo AI Trading Bot System                           ║
║                                                                              ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║  Role: Full-Stack AI Engineer                                               ║
║  Mission: Autonomous code optimization, testing, and maintenance            ║
║  Continuity: Seamless handoff from Windsurf                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_deepseek_server():
    """Check if DeepSeek inference server is running"""
    import requests
    
    endpoints = [
        ("Ollama", "http://localhost:11434/api/tags"),
        ("LM Studio", "http://localhost:1234/v1/models"),
        ("TextGen WebUI", "http://localhost:5000/api/v1/model"),
    ]
    
    print("\n🔍 Checking for DeepSeek inference servers...")
    
    for name, endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=2)
            if response.status_code == 200:
                print(f"  ✅ {name} detected at {endpoint}")
                return endpoint
        except:
            print(f"  ❌ {name} not found at {endpoint}")
    
    print("\n⚠️  WARNING: No DeepSeek inference server detected!")
    print("Please start one of the following:")
    print("  • Ollama: ollama serve")
    print("  • LM Studio: Start LM Studio and load deepseek-coder-6.7b")
    print("  • TextGen WebUI: python server.py")
    
    response = input("\nContinue anyway? (y/n): ")
    if response.lower() != 'y':
        sys.exit(1)
    
    return "http://localhost:11434/api/generate"  # Default to Ollama


async def main():
    """Main activation function"""
    print_banner()
    
    # Check server
    endpoint = check_deepseek_server()
    
    # Configuration
    print("\n⚙️  Configuration:")
    print(f"  • Project Root: {project_root}")
    print(f"  • Inference Endpoint: {endpoint}")
    print(f"  • Model: deepseek-coder-6.7b")
    
    # Ask about safeguards mode
    print("\n🛡️  Safeguards Configuration:")
    print("  1. Production Mode (Sandbox ON, Human approval for critical changes)")
    print("  2. Development Mode (Sandbox OFF, Auto-apply safe changes)")
    print("  3. Review Only (Sandbox ON, No changes applied)")
    
    safeguard_choice = input("\nSelect safeguards mode (1-3, default=1): ").strip() or "1"
    
    if safeguard_choice == "1":
        sandbox_enabled = True
        require_approval = True
        mode_desc = "Production (Sandbox ON, Approval required)"
    elif safeguard_choice == "2":
        sandbox_enabled = False
        require_approval = False
        mode_desc = "Development (Sandbox OFF, Auto-apply)"
    else:
        sandbox_enabled = True
        require_approval = True
        mode_desc = "Review Only (Sandbox ON, No changes)"
    
    print(f"  • Mode: {mode_desc}")
    
    # Ask about AI role mode
    print("\n🤖 AI Role Configuration:")
    print("  1. Engineer Mode (Code modifications only)")
    print("  2. Architect Mode (Design proposals + code)")
    print("  3. Read-Only Mode (Analysis only, no changes)")
    
    role_choice = input("\nSelect AI role (1-3, default=1): ").strip() or "1"
    
    if role_choice == "1":
        ai_mode = "engineer"
        role_desc = "Engineer (Code only)"
    elif role_choice == "2":
        ai_mode = "architect"
        role_desc = "Architect (Design + Code)"
    else:
        ai_mode = "read_only"
        role_desc = "Read-Only (Analysis only)"
    
    print(f"  • AI Role: {role_desc}")
    
    # Create DeepSeek config
    config = DeepSeekConfig(
        backend=InferenceBackend.OLLAMA,
        endpoint=endpoint,
        model_name="deepseek-coder-6.7b",
        temperature=0.2,
        max_tokens=4096,
        sandbox_mode=sandbox_enabled,
        require_approval=require_approval,
        auto_commit_safe_changes=not require_approval
    )
    
    # Initialize safeguards
    print("\n🛡️  Initializing Integrated Safeguard System...")
    safeguards = IntegratedSafeguardSystem(
        base_dir=project_root / "logs" / "safeguards",
        sandbox_enabled=sandbox_enabled,
        mode=ai_mode
    )
    print(f"  ✅ Safeguards initialized (Sandbox: {sandbox_enabled}, Role: {ai_mode})")
    
    # Create initial rollback snapshot
    print("\n📸 Creating initial rollback snapshot...")
    snapshot_id = safeguards.create_rollback_snapshot("Initial state before DeepSeek activation")
    print(f"  ✅ Snapshot created: {snapshot_id}")
    
    # Mark critical files as read-only
    print("\n🔒 Protecting critical files...")
    critical_files = [
        "trading_bot/risk/risk_manager.py",
        "trading_bot/execution/order_execution.py",
        "trading_bot/cognitive_architecture/cognitive_core.py"
    ]
    for file in critical_files:
        safeguards.rbac.set_read_only(file)
    print(f"  ✅ {len(critical_files)} critical files protected")
    
    # Create orchestrator
    print("\n🚀 Initializing Autonomous Orchestrator...")
    orchestrator = AutonomousOrchestrator(
        project_root=project_root,
        context_dir=project_root / "alphaalgo_context",
        deepseek_config=config
    )
    
    # Initialize
    print("\n📊 Loading Windsurf context and performing initial audit...")
    await orchestrator.initialize()
    
    # Show status
    status = orchestrator.get_status()
    print("\n📈 System Status:")
    print(f"  • Windsurf Reports Loaded: {status['windsurf_context']['reports']}")
    print(f"  • Pending Tasks from Windsurf: {status['windsurf_context']['pending_tasks']}")
    print(f"  • Tasks in Queue: {status['engineer_status']['queue_size']}")
    
    # Show safeguards status
    safeguard_status = safeguards.get_status()
    print("\n🛡️  Safeguards Status:")
    print(f"  • Sandbox Enabled: {safeguard_status['sandbox_enabled']}")
    print(f"  • RBAC Mode: {safeguard_status['rbac_mode']}")
    print(f"  • Total Changes Logged: {safeguard_status['total_changes']}")
    print(f"  • Pending Approval: {safeguard_status['pending_approval']}")
    print(f"  • Pending Critical: {safeguard_status['pending_critical']}")
    print(f"  • Active Sessions: {safeguard_status['active_sessions']}")
    print(f"  • Total Checkpoints: {safeguard_status['total_checkpoints']}")
    print(f"  • Active Branches: {safeguard_status['active_branches']}")
    print(f"  • Min Test Coverage: {safeguard_status['min_test_coverage']:.0%}")
    print(f"  • Read-Only Files: {safeguard_status['read_only_files']}")
    
    if status['last_audit']:
        audit = status['last_audit']
        print(f"\n🔍 Initial Audit Results:")
        print(f"  • Total Files Scanned: {audit['total_files']}")
        print(f"  • Files with Issues: {audit['files_with_issues']}")
        print(f"  • Critical Issues: {audit['critical_issues']}")
        print(f"  • High Priority Issues: {audit['high_priority_issues']}")
        print(f"  • TODO Markers: {len(audit['todo_markers'])}")
        print(f"  • Missing Tests: {len(audit['missing_tests'])}")
        print(f"  • Circular Imports: {len(audit['circular_imports'])}")
    
    # Ask user for mode
    print("\n🎯 Execution Mode:")
    print("  1. Single Cycle (run one audit/fix cycle)")
    print("  2. Continuous (run cycles every 24 hours)")
    print("  3. Custom Continuous (specify interval)")
    print("  4. Status Only (show status and exit)")
    
    choice = input("\nSelect mode (1-4): ").strip()
    
    if choice == '1':
        print("\n▶️  Running single autonomous cycle...")
        result = await orchestrator.run_autonomous_cycle(max_tasks_per_cycle=10)
        
        print("\n✅ Cycle Complete!")
        print(f"  • Status: {result['status']}")
        print(f"  • Duration: {result.get('duration_seconds', 0):.2f}s")
        print(f"  • Tasks Processed: {result['phases']['processing']['processed']}")
        print(f"  • Tasks Completed: {result['phases']['processing']['completed']}")
        print(f"  • Tasks Failed: {result['phases']['processing']['failed']}")
        print(f"  • Tests Passed: {result['phases']['testing'].get('passed', 'N/A')}")
        
    elif choice == '2':
        print("\n♾️  Starting continuous operation (24-hour cycles)...")
        print("Press Ctrl+C to stop")
        try:
            await orchestrator.run_continuous(cycle_interval_hours=24)
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping continuous operation...")
            
    elif choice == '3':
        hours = int(input("Enter hours between cycles: "))
        max_cycles = input("Maximum cycles (leave empty for unlimited): ").strip()
        max_cycles = int(max_cycles) if max_cycles else None
        
        print(f"\n♾️  Starting continuous operation ({hours}-hour cycles, max: {max_cycles or 'unlimited'})...")
        print("Press Ctrl+C to stop")
        try:
            await orchestrator.run_continuous(
                cycle_interval_hours=hours,
                max_cycles=max_cycles
            )
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping continuous operation...")
            
    elif choice == '4':
        print("\n📊 Status displayed above. Exiting...")
    
    else:
        print("\n❌ Invalid choice. Exiting...")
    
    # Final status
    final_status = orchestrator.get_status()
    print("\n" + "=" * 80)
    print("FINAL STATUS")
    print("=" * 80)
    print(f"Total Cycles Run: {final_status['total_cycles']}")
    print(f"Tasks Completed: {final_status['engineer_status']['completed']}")
    print(f"Tasks Failed: {final_status['engineer_status']['failed']}")
    print(f"Tasks Remaining: {final_status['engineer_status']['queue_size']}")
    print("=" * 80)
    
    print("\n✨ DeepSeek Autonomous Engineer session complete!")
    print(f"📁 Logs saved to: {project_root / 'logs' / 'deepseek'}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user. Exiting gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
