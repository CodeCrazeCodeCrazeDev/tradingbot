"""
12-Domain Hedge Fund Architecture Demo
========================================

Demonstrates the 12-domain architecture that organizes the entire
trading bot system into professional hedge fund domains.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.domains import (
    ALL_DOMAINS,
    get_domain_orchestrator,
)


async def demo_domain_architecture():
    """Demonstrate the 12-domain architecture."""
    
    print("=" * 70)
    print("   12-DOMAIN HEDGE FUND ARCHITECTURE DEMO")
    print("   Mirroring Renaissance Technologies, Two Sigma, Citadel")
    print("=" * 70)
    print()
    
    # Create orchestrator
    DomainOrchestrator = get_domain_orchestrator()
    orchestrator = DomainOrchestrator()
    
    # Initialize all domains
    print("Initializing 12-domain architecture...")
    print("-" * 70)
    
    success = await orchestrator.initialize()
    
    if not success:
        print("Failed to initialize orchestrator!")
        return
    
    print()
    print("=" * 70)
    print("   DOMAIN STATUS")
    print("=" * 70)
    
    # Show all domains
    status = orchestrator.get_status()
    
    for domain_id, info in status['domains'].items():
        priority_icon = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢',
        }.get(info['priority'], '⚪')
        
        status_icon = '✅' if info['initialized'] else '❌'
        
        print(f"  {priority_icon} {info['name']:<30} {status_icon} {info['status']}")
    
    print()
    print("=" * 70)
    print("   DOMAIN CAPABILITIES")
    print("=" * 70)
    
    capabilities = orchestrator.get_capabilities()
    
    for domain_id, caps in capabilities.items():
        domain = orchestrator.get_domain(domain_id)
        if domain:
            print(f"\n  📦 {domain.domain_name}")
            print(f"     Capabilities: {', '.join(caps[:5])}...")
    
    print()
    print("=" * 70)
    print("   SYSTEM HEALTH")
    print("=" * 70)
    
    health = orchestrator.get_system_health()
    print(f"  State: {health['state']}")
    print(f"  Uptime: {health['uptime_seconds']:.1f} seconds")
    print(f"  Total Domains: {health['total_domains']}")
    print(f"  Healthy: {health['healthy_domains']}")
    print(f"  Degraded: {health['degraded_domains']}")
    
    print()
    print("=" * 70)
    print("   INTER-DOMAIN WORKFLOW DEMO")
    print("=" * 70)
    
    # Demonstrate signal generation workflow
    print("\n  Executing: Generate Signal → Risk Check → Compliance → Execute")
    print()
    
    result = await orchestrator.generate_and_execute_signal("EURUSD", "1H")
    
    for step in result.get('steps', []):
        step_name = step['step'].replace('_', ' ').title()
        print(f"    ✓ {step_name}")
    
    if result.get('success'):
        print(f"\n  ✅ Workflow completed successfully!")
    else:
        print(f"\n  ⚠️ Workflow stopped: {result.get('reason', 'Unknown')}")
    
    print()
    print("=" * 70)
    print("   MODULE MAPPINGS (Sample)")
    print("=" * 70)
    
    # Show sample module mappings
    mappings = orchestrator.get_module_mappings()
    
    for domain_id in ['alpha_generation', 'risk_management', 'execution']:
        domain = orchestrator.get_domain(domain_id)
        if domain:
            domain_mappings = mappings.get(domain_id, {})
            print(f"\n  📦 {domain.domain_name} ({len(domain_mappings)} modules)")
            for name in list(domain_mappings.keys())[:3]:
                print(f"     - {name}")
            if len(domain_mappings) > 3:
                print(f"     ... and {len(domain_mappings) - 3} more")
    
    print()
    print("=" * 70)
    print("   ARCHITECTURE SUMMARY")
    print("=" * 70)
    
    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │                    12-DOMAIN ARCHITECTURE                       │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
    │  │   ALPHA     │  │   QUANT     │  │    RISK     │  CRITICAL   │
    │  │ GENERATION  │──│  RESEARCH   │──│ MANAGEMENT  │             │
    │  └─────────────┘  └─────────────┘  └─────────────┘             │
    │         │                │                │                     │
    │         ▼                ▼                ▼                     │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
    │  │  EXECUTION  │  │    DATA     │  │   MACHINE   │  HIGH       │
    │  │             │──│INFRASTRUCTURE│──│  LEARNING   │             │
    │  └─────────────┘  └─────────────┘  └─────────────┘             │
    │         │                │                │                     │
    │         ▼                ▼                ▼                     │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
    │  │ TECHNOLOGY  │  │ COMPLIANCE  │  │ OPERATIONS  │  MEDIUM     │
    │  │INFRASTRUCTURE│──│             │──│             │             │
    │  └─────────────┘  └─────────────┘  └─────────────┘             │
    │         │                │                │                     │
    │         ▼                ▼                ▼                     │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
    │  │  RESEARCH   │  │  PORTFOLIO  │  │ GOVERNANCE  │  LOW        │
    │  │     & DEV   │──│  ANALYTICS  │──│  & CONTROL  │             │
    │  └─────────────┘  └─────────────┘  └─────────────┘             │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    """)
    
    # Shutdown
    print("\nShutting down domains...")
    await orchestrator.shutdown()
    print("✅ Demo complete!")


async def quick_status():
    """Quick status check."""
    DomainOrchestrator = get_domain_orchestrator()
    orchestrator = DomainOrchestrator()
    await orchestrator.initialize()
    
    print("\n12-Domain Architecture Status:")
    print("-" * 40)
    
    for domain_id, domain in orchestrator.get_all_domains().items():
        status = "✅" if domain.is_initialized else "❌"
        print(f"  {status} {domain.domain_name}")
    
    await orchestrator.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="12-Domain Architecture Demo")
    parser.add_argument("--quick", action="store_true", help="Quick status check")
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_status())
    else:
        asyncio.run(demo_domain_architecture())
