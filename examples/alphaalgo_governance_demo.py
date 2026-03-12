"""
AlphaAlgo Governance System Demo

Demonstrates the complete G0/G1/G2 governance hierarchy:
    pass
- G0: Human Authority (approves/rejects major changes)
- G1: Central Controller (coordinates modules)
- G2: Mini-AIs (specialized helpers)

IDENTITY: The AI is the student → The market is the teacher.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.alphaalgo_core import (
    AlphaAlgoOrchestrator,
    AlphaAlgoConfig,
    BrokerType,
    DataType,
    ChangeCategory,
    TradingMode,
    SystemHealth,
    MiniAIRole,
)


def print_header(title: str):
    pass
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title: str):
    pass
    """Print a section header"""
    print(f"\n--- {title} ---")


async def demo_initialization():
    pass
    """Demo: System Initialization"""
    print_header("ALPHAALGO INITIALIZATION")
    
    # Create AlphaAlgo with custom config
    config = AlphaAlgoConfig(
        data_path="alphaalgo_demo_data",
        auto_connect_simulation=True,
        enable_mini_ais=True,
    )
    
    alphaalgo = AlphaAlgoOrchestrator(config)
    
    # Initialize with master password
    print("\nInitializing AlphaAlgo...")
    success, message = await alphaalgo.initialize(master_password="demo_password_123")
    print(f"Result: {message}")
    
    # Show identity
    print_section("AlphaAlgo Identity")
    identity = alphaalgo.get_identity()
    print(f"Name: {identity['name']}")
    print(f"Role: {identity['role']}")
    print(f"Identity: {identity['identity']}")
    print(f"Governance: {identity['governance']}")
    print("Principles:")
    for principle in identity['principles']:
    pass
        print(f"  - {principle}")
    
    return alphaalgo


async def demo_system_status(alphaalgo: AlphaAlgoOrchestrator):
    pass
    """Demo: System Status"""
    print_header("SYSTEM STATUS")
    
    status = alphaalgo.get_system_status()
    
    print_section("Trading Status")
    print(f"Mode: {status['trading']['mode']}")
    print(f"Health: {status['trading']['health']}")
    print(f"Can Trade: {status['trading']['can_trade']}")
    if status['trading']['issues']:
    pass
        print("Issues:")
        for issue in status['trading']['issues']:
    pass
            print(f"  - {issue}")
    
    print_section("Governance Status")
    gov = status['governance']
    print(f"Pending Approvals: {gov['g0_pending_approvals']}")
    print(f"Mini-AIs Active: {gov['g2_active_mini_ais']}/{gov['g2_mini_ais']}")
    
    print_section("Data Sources")
    for name, src in status['data_sources'].items():
    pass
        print(f"  {name}: {src['status']}")
    
    print_section("Security Status")
    sec = status['security']
    print(f"Status: {sec['status']}")
    print(f"Encryption: {'Available' if sec['encryption_available'] else 'Not Available'}")


async def demo_can_trade(alphaalgo: AlphaAlgoOrchestrator):
    pass
    """Demo: Trading Permission Check"""
    print_header("TRADING PERMISSION CHECK")
    
    can_trade, reason = await alphaalgo.can_trade()
    
    print(f"\nCan Trade: {can_trade}")
    print(f"Reason: {reason}")
    
    if not can_trade:
    pass
        print("\n[AlphaAlgo says: 'I refuse to trade until conditions are safe.']")


async def demo_broker_connection(alphaalgo: AlphaAlgoOrchestrator):
    pass
    """Demo: Broker Connection"""
    print_header("BROKER CONNECTION")
    
    # Show credential template
    print_section("MT5 Credential Template (for human to fill)")
    template = alphaalgo.get_broker_template(BrokerType.MT5)
    for key, value in template.items():
    pass
        print(f"  {key}: {value}")
    
    # Connect to simulation (no approval needed)
    print_section("Connecting to Simulation Broker")
    success, message = await alphaalgo.connect_broker(BrokerType.SIMULATION)
    print(f"Result: {message}")
    
    # Try to connect to live broker (requires approval)
    print_section("Attempting Live Broker Connection")
    success, message = await alphaalgo.connect_broker(BrokerType.MT5)
    print(f"Result: {message}")
    
    # Show pending approvals
    approvals = alphaalgo.get_pending_approvals()
    if approvals:
    pass
        print_section("Pending Approvals")
        for approval in approvals:
    pass
            print(f"  [{approval['request_id']}] {approval['description']}")
            print(f"    Status: {approval['status']}")
            print(f"    Requested by: {approval['requested_by']}")


async def demo_data_fetching(alphaalgo: AlphaAlgoOrchestrator):
    pass
    """Demo: Data Fetching"""
    print_header("DATA FETCHING")
    
    # Fetch different data types
    data_types = [
        (DataType.OHLCV, "EURUSD"),
        (DataType.FEAR_GREED, "MARKET"),
    ]
    
    for data_type, symbol in data_types:
    pass
        print_section(f"Fetching {data_type.value} for {symbol}")
        data = await alphaalgo.fetch_data(data_type, symbol)
        if data:
    pass
            print(f"  Data received: {data}")
        else:
    pass
            print("  No data available")


async def demo_propose_change(alphaalgo: AlphaAlgoOrchestrator):
    pass
    """Demo: Proposing Changes"""
    print_header("PROPOSING CHANGES")
    
    print("\nFollowing the rule: Propose → Test → Human Approve → Deploy")
    
    # Propose a strategy change
    print_section("Proposing Strategy Enhancement")
    change = alphaalgo.propose_change(
        category=ChangeCategory.STRATEGY_LOGIC,
        title="Add Multi-Timeframe Confirmation",
        description="Require M15, H1, and H4 trend alignment before entry",
        rationale="Reduces false signals by filtering against higher timeframes",
        expected_impact="Estimated 30% reduction in false signals, 15% improvement in win rate",
        risk_assessment="Low risk - additive change, does not modify existing logic",
        rollback_plan="Remove timeframe confirmation check, revert to single timeframe",
    )
    
    print(f"Change ID: {change['change_id']}")
    print(f"Title: {change['title']}")
    print(f"Category: {change['category']}")
    print(f"Status: {change['status']}")
    
    # Show pending changes
    pending = alphaalgo.get_pending_changes()
    print_section(f"Pending Changes ({len(pending)})")
    for p in pending:
    pass
        print(f"  [{p['change_id']}] {p['title']}")
        print(f"    Category: {p['category']}")
        print(f"    Requires Human Approval: {p['category'] in ['risk', 'position', 'execution', 'security']}")


async def demo_human_approval(alphaalgo: AlphaAlgoOrchestrator):
    pass
    """Demo: Human Approval Process"""
    print_header("HUMAN APPROVAL PROCESS")
    
    # Get pending approvals
    approvals = alphaalgo.get_pending_approvals()
    
    if approvals:
    pass
        print_section("Simulating Human Approval")
        approval = approvals[0]
        print(f"Approving request: {approval['request_id']}")
        print(f"Description: {approval['description']}")
        
        # Simulate human approval
        result = alphaalgo.approve_request(approval['request_id'], "demo_human")
        print(f"Approval result: {'Success' if result else 'Failed'}")
    else:
    pass
        print("\nNo pending approvals to demonstrate.")
    
    # Get pending changes
    changes = alphaalgo.get_pending_changes()
    
    if changes:
    pass
        print_section("Simulating Change Approval")
        change = changes[0]
        print(f"Approving change: {change['change_id']}")
        print(f"Title: {change['title']}")
        
        # Simulate human approval
        result = alphaalgo.approve_change(change['change_id'], "demo_human")
        print(f"Approval result: {'Success' if result else 'Failed'}")


async def demo_architecture_scan(alphaalgo: AlphaAlgoOrchestrator):
    pass
    """Demo: Architecture Scanning"""
    print_header("ARCHITECTURE SCANNING")
    
    print("\nScanning codebase for issues...")
    result = alphaalgo.scan_architecture()
    
    print_section("Analysis Summary")
    summary = result['summary']
    print(f"Files Analyzed: {summary.get('files_analyzed', 0)}")
    print(f"Total Issues: {summary.get('total_issues', 0)}")
    
    if summary.get('by_severity'):
    pass
        print("\nBy Severity:")
        for sev, count in summary['by_severity'].items():
    pass
            print(f"  {sev}: {count}")
    
    if result['proposals']:
    pass
        print_section(f"Repair Proposals ({len(result['proposals'])})")
        for p in result['proposals'][:5]:  # Show first 5
            print(f"  [{p['id']}] {p['title']}")
            print(f"    Type: {p['type']}, Risk: {p['risk']}")


async def demo_mini_ais(alphaalgo: AlphaAlgoOrchestrator):
    pass
    """Demo: Mini-AI System"""
    print_header("MINI-AI SYSTEM (G2)")
    
    status = alphaalgo.mini_ai_factory.get_status_report()
    
    print(f"\nTotal Mini-AIs: {status['total']}")
    print(f"Active: {status['active']}")
    
    print_section("Mini-AI Details")
    for ai in status['mini_ais']:
    pass
        print(f"\n  {ai['mini_ai_id']}")
        print(f"    Role: {ai['role']}")
        print(f"    Active: {ai['is_active']}")
        print(f"    Capabilities: {', '.join(ai['capabilities'][:3])}...")


async def demo_emergency_stop(alphaalgo: AlphaAlgoOrchestrator):
    pass
    """Demo: Emergency Stop"""
    print_header("EMERGENCY STOP")
    
    print("\n[!] Simulating emergency stop...")
    print("    Reason: Demo - Testing emergency procedures")
    
    # Don't actually call emergency_stop in demo
    # alphaalgo.emergency_stop("Demo emergency")
    
    print("\n[AlphaAlgo would enter NO_TRADE mode immediately]")
    print("[All Mini-AIs would be deactivated]")
    print("[Human approval required to resume trading]")


async def main():
    pass
    """Run the complete demo"""
    print("\n" + "=" * 60)
    print("  ALPHAALGO GOVERNANCE SYSTEM DEMO")
    print("  The AI is the student → The market is the teacher")
    print("=" * 60)
    
    try:
    pass
        # Initialize
        alphaalgo = await demo_initialization()
        
        # Run demos
        await demo_system_status(alphaalgo)
        await demo_can_trade(alphaalgo)
        await demo_broker_connection(alphaalgo)
        await demo_data_fetching(alphaalgo)
        await demo_propose_change(alphaalgo)
        await demo_human_approval(alphaalgo)
        await demo_architecture_scan(alphaalgo)
        await demo_mini_ais(alphaalgo)
        await demo_emergency_stop(alphaalgo)
        
        # Final status
        print_header("FINAL STATUS")
        status = alphaalgo.get_system_status()
        print(f"\nTrading Mode: {status['trading']['mode']}")
        print(f"System Health: {status['trading']['health']}")
        print(f"Pending Approvals: {status['pending_approvals']}")
        print(f"Pending Changes: {status['pending_changes']}")
        
        print("\n" + "=" * 60)
        print("  DEMO COMPLETE")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("  1. All major changes require human approval (G0)")
        print("  2. System refuses to trade when conditions are unsafe")
        print("  3. Every change follows: Propose → Test → Approve → Deploy")
        print("  4. Mini-AIs handle specialized tasks under G1 control")
        print("  5. Security is enforced at every level")
        print("\n")
        
    except Exception as e:
    pass
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    pass
    asyncio.run(main())
