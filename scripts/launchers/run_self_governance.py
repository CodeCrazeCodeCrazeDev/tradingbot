"""
Self-Governance Meta-Agent Runner
Executes autonomous governance cycles and outputs actionable JSON results.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from self_governance_agent import SelfGovernanceMetaAgent


async def run_continuous_governance(interval_minutes: int = 60):
    """Run governance cycles continuously"""
    agent = SelfGovernanceMetaAgent()
    
    print("=" * 80)
    print("SELF-GOVERNANCE META-AGENT - CONTINUOUS MODE")
    print("=" * 80)
    print(f"Cycle Interval: {interval_minutes} minutes")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)
    print()
    
    cycle_count = 0
    
    while True:
        try:
            cycle_count += 1
            print(f"\n{'='*80}")
            print(f"GOVERNANCE CYCLE #{cycle_count} - {datetime.now().isoformat()}")
            print(f"{'='*80}\n")
            
            # Run governance cycle
            results = await agent.run_governance_cycle()
            
            # Save results with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"governance_cycle_{timestamp}.json"
            agent.save_results(results, output_file)
            
            # Print summary
            print_cycle_summary(results)
            
            # Check for critical issues
            if results.get("status") == "ESCALATED":
                print("\n[!] CRITICAL: Governance cycle ESCALATED - Human intervention required!")
                print(f"Reason: {results.get('escalation_reason')}")
                break
            
            if results.get("human_review_required"):
                print("\n[!] Human review required for this cycle")
            
            # Wait for next cycle
            print(f"\nNext cycle in {interval_minutes} minutes...")
            await asyncio.sleep(interval_minutes * 60)
            
        except KeyboardInterrupt:
            print("\n\nGovernance agent stopped by user")
            break
        except Exception as e:
            print(f"\n[X] Error in governance cycle: {e}")
            print("Retrying in 5 minutes...")
            await asyncio.sleep(300)


def print_cycle_summary(results: Dict):
    """Print human-readable summary of governance cycle"""
    print("\n" + "="*80)
    print("CYCLE SUMMARY")
    print("="*80)
    
    # Status
    status = results.get("status", "UNKNOWN")
    status_symbol = "[OK]" if status == "COMPLETED" else "[FAIL]"
    print(f"\nStatus: {status_symbol} {status}")
    print(f"Cycle ID: {results.get('cycle_id')}")
    print(f"Duration: {results.get('cycle_duration_seconds', 0):.2f}s")
    
    # System State
    if "phase1_state" in results.get("phases", {}):
        state = results["phases"]["phase1_state"]
        print(f"\nSYSTEM STATE:")
        print(f"  Model: {state.get('model_version')}")
        print(f"  P/L 24h: {state.get('pnl_24h', 0):.2f}%")
        print(f"  P/L 7d: {state.get('pnl_7d', 0):.2f}%")
        print(f"  P/L 30d: {state.get('pnl_30d', 0):.2f}%")
        print(f"  CPU: {state.get('cpu_percent', 0):.1f}%")
        print(f"  Memory: {state.get('memory_percent', 0):.1f}%")
        print(f"  Latency: {state.get('latency_ms', 0):.1f}ms")
        
        if state.get('flags'):
            print(f"  [!] Flags: {', '.join(state['flags'])}")
    
    # Mood
    if "phase5_mood" in results.get("phases", {}):
        mood_data = results["phases"]["phase5_mood"]
        mood = mood_data.get("mood", "unknown")
        mood_symbol = "[GREEN]" if mood == "green" else ("[YELLOW]" if mood == "yellow" else "[RED]")
        print(f"\n{mood_symbol} MOOD: {mood.upper()}")
        print(f"  Aggressiveness: {mood_data.get('aggressiveness_multiplier', 1.0):.0%}")
    
    # Circuit Breaker
    if "phase15_circuit_breaker" in results.get("phases", {}):
        breaker = results["phases"]["phase15_circuit_breaker"]
        if breaker.get("circuit_breaker_active"):
            print(f"\n[ALERT] CIRCUIT BREAKER ACTIVE:")
            for action in breaker.get("actions_triggered", []):
                print(f"  - {action}")
    
    # Actions
    actions = results.get("actions", [])
    if actions:
        print(f"\nACTIONS REQUIRED: {len(actions)}")
        for i, action in enumerate(actions, 1):
            priority = action.get("priority", "NORMAL")
            requires_human = action.get("requires_human", False)
            human_flag = " [HUMAN REQUIRED]" if requires_human else ""
            print(f"  {i}. [{priority}] {action.get('action')}{human_flag}")
    
    # Benchmarking
    if "phase8_benchmark" in results.get("phases", {}):
        bench = results["phases"]["phase8_benchmark"]
        print(f"\nPERFORMANCE:")
        print(f"  Current Sharpe: {bench.get('current_sharpe', 0):.2f}")
        print(f"  Baseline Sharpe: {bench.get('baseline_sharpe', 0):.2f}")
        print(f"  Outperformance: {bench.get('outperformance', 0):.2f}")
    
    # Critique
    if "phase24_critique" in results.get("phases", {}):
        critique = results["phases"]["phase24_critique"]
        print(f"\nDAILY CRITIQUE:")
        print(f"  What Worked: {len(critique.get('what_worked', []))} items")
        print(f"  What Failed: {len(critique.get('what_failed', []))} items")
        print(f"  Improvements: {len(critique.get('improvements', []))} items")
    
    print("\n" + "="*80)


async def run_single_cycle():
    """Run a single governance cycle"""
    agent = SelfGovernanceMetaAgent()
    
    print("=" * 80)
    print("SELF-GOVERNANCE META-AGENT - SINGLE CYCLE")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)
    print()
    
    results = await agent.run_governance_cycle()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"governance_cycle_{timestamp}.json"
    agent.save_results(results, output_file)
    
    # Print summary
    print_cycle_summary(results)
    
    print(f"\n[OK] Results saved to: {output_file}")
    
    return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Self-Governance Meta-Agent")
    parser.add_argument("--mode", choices=["single", "continuous"], default="single",
                       help="Run mode: single cycle or continuous")
    parser.add_argument("--interval", type=int, default=60,
                       help="Interval between cycles in minutes (continuous mode)")
    
    args = parser.parse_args()
    
    if args.mode == "single":
        asyncio.run(run_single_cycle())
    else:
        asyncio.run(run_continuous_governance(args.interval))


if __name__ == "__main__":
    main()
