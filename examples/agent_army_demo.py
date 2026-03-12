"""
Agent Army Demo
================

Demonstrates the 60-Agent Army for the Intelligence Core.

60 specialized agents organized into 6 brigades:
- HYPOTHESIS BRIGADE (10 agents) - Generate and test hypotheses
- MARKET BRIGADE (10 agents) - Analyze market conditions  
- RISK BRIGADE (10 agents) - Assess and manage risk
- STRATEGY BRIGADE (10 agents) - Develop trading strategies
- DATA BRIGADE (10 agents) - Validate data quality
- AUDIT BRIGADE (10 agents) - Verify compliance and correctness
"""

import logging
from trading_bot.intelligence_core import quick_start_army
from trading_bot.intelligence_core.agent_army import Brigade, AgentType

logging.basicConfig(level=logging.INFO)


def demo_army_overview():
    """Demo: Overview of the 60-Agent Army"""
    print("\n" + "="*80)
    print("60-AGENT ARMY - INTELLIGENCE CORE")
    print("="*80)
    print("\nAn army of 60 specialized AI agents working together as a swarm")
    print("for the Intelligence Core quant research lab.\n")
    
    army = quick_start_army()
    
    print(f"✅ Total Agents Deployed: {len(army.get_all_agents())}")
    print(f"✅ Brigades: 6")
    print(f"✅ Agents per Brigade: 10")
    
    print("\n📋 BRIGADE STRUCTURE:")
    print("-" * 40)
    
    for brigade in Brigade:
        agents = army.get_brigade(brigade)
        print(f"\n🔹 {brigade.value.upper()} BRIGADE ({len(agents)} agents)")
        for agent in agents[:5]:  # Show first 5
            print(f"   {agent.agent_number:2d}. {agent.name}")
        if len(agents) > 5:
            print(f"   ... and {len(agents) - 5} more")
    
    return army


def demo_agent_tasks(army):
    """Demo: Assign tasks to specific agents"""
    print("\n" + "="*80)
    print("AGENT TASK ASSIGNMENT")
    print("="*80)
    print("\nAssigning tasks to specialized agents...\n")
    
    # Pattern Hunter
    result = army.assign_task(
        AgentType.PATTERN_HUNTER,
        "find_patterns",
        {'market_data': 'EURUSD', 'timeframe': 'H1'}
    )
    print(f"🔍 {result['agent_type']}:")
    print(f"   Found {result['result']['patterns_found']} patterns")
    print(f"   Average reliability: {result['result']['reliability']:.1%}")
    
    # Regime Spotter
    result = army.assign_task(
        AgentType.REGIME_SPOTTER,
        "detect_regime",
        {'symbol': 'BTCUSDT'}
    )
    print(f"\n📊 {result['agent_type']}:")
    print(f"   Current regime: {result['result']['current_regime']}")
    print(f"   Confidence: {result['result']['confidence']:.1%}")
    
    # Position Sizer
    result = army.assign_task(
        AgentType.POSITION_SIZER,
        "calculate_position",
        {'account_size': 100000, 'risk_per_trade': 0.01}
    )
    print(f"\n💰 {result['agent_type']}:")
    print(f"   Optimal position size: {result['result']['optimal_size']:.2%}")
    print(f"   Risk per trade: {result['result']['risk_per_trade']:.2%}")
    
    # Entry Optimizer
    result = army.assign_task(
        AgentType.ENTRY_OPTIMIZER,
        "find_entry",
        {'price': 1.0850, 'direction': 'long'}
    )
    print(f"\n🎯 {result['agent_type']}:")
    print(f"   Suggested entry: {result['result']['entry_price']:.5f}")
    print(f"   Confidence: {result['result']['confidence']:.1%}")
    
    # Data Validator
    result = army.assign_task(
        AgentType.DATA_VALIDATOR,
        "validate_data",
        {'dataset': 'historical_prices', 'size': 10000}
    )
    print(f"\n✓ {result['agent_type']}:")
    print(f"   Data valid: {result['result']['valid']}")
    if result['result']['issues']:
        print(f"   Issues found: {result['result']['issues']}")
    
    # Chief Audit Officer
    result = army.assign_task(
        AgentType.CHIEF_AUDIT_OFFICER,
        "comprehensive_audit",
        {'strategy_id': 'trend_v1'}
    )
    print(f"\n👮 {result['agent_type']}:")
    print(f"   Audit passed: {result['result']['audit_passed']}")


def demo_brigade_consensus(army):
    """Demo: Brigade-level consensus voting"""
    print("\n" + "="*80)
    print("BRIGADE CONSENSUS VOTING")
    print("="*80)
    print("\nGetting consensus from each brigade on a new hypothesis...\n")
    
    hypothesis = {
        'statement': 'Double bottom pattern with >65% reliability',
        'mechanism': 'Support level tested twice'
    }
    
    for brigade in Brigade:
        print(f"\n🗳️  {brigade.value.upper()} BRIGADE Voting:")
        consensus = army.brigade_consensus(
            brigade,
            f"Approve hypothesis: {hypothesis['statement']}",
            hypothesis
        )
        
        print(f"   Decision: {consensus.decision.upper()}")
        print(f"   Confidence: {consensus.confidence:.1%}")
        print(f"   Votes: {consensus.votes_for} for, {consensus.votes_against} against, {consensus.votes_neutral} neutral")
        
        # Show brigade tendencies
        if brigade == Brigade.RISK or brigade == Brigade.AUDIT:
            if consensus.decision == 'rejected':
                print(f"   ⚠️  {brigade.value.title()} brigade is strict - often rejects proposals")
        elif brigade == Brigade.HYPOTHESIS:
            if consensus.decision == 'approved':
                print(f"   ✓ {brigade.value.title()} brigade is creative - often approves new ideas")


def demo_full_army_consensus(army):
    """Demo: Full army consensus (all 60 agents)"""
    print("\n" + "="*80)
    print("FULL ARMY CONSENSUS (ALL 60 AGENTS)")
    print("="*80)
    print("\nDeploying all 60 agents to vote on strategy deployment...\n")
    
    strategy = {
        'name': 'Momentum Strategy v2.1',
        'sharpe': 1.8,
        'max_drawdown': 0.12,
        'win_rate': 0.58
    }
    
    print("📊 Strategy Stats:")
    print(f"   Sharpe Ratio: {strategy['sharpe']}")
    print(f"   Max Drawdown: {strategy['max_drawdown']:.1%}")
    print(f"   Win Rate: {strategy['win_rate']:.1%}")
    
    print("\n🗳️  All 60 agents voting...")
    consensus = army.full_army_consensus(
        f"Deploy strategy: {strategy['name']}",
        strategy
    )
    
    print(f"\n📋 CONSENSUS RESULT:")
    print(f"   Decision: {consensus.decision.upper()}")
    print(f"   Overall Confidence: {consensus.confidence:.1%}")
    print(f"   Total Votes: {consensus.total_votes}")
    print(f"   For: {consensus.votes_for} | Against: {consensus.votes_against} | Neutral: {consensus.votes_neutral}")
    
    print(f"\n📊 By Brigade:")
    for brigade_name, votes in consensus.by_brigade.items():
        print(f"   {brigade_name:12s}: {votes['for']:2d} for, {votes['against']:2d} against, {votes['neutral']:2d} neutral")
    
    if consensus.decision == 'approved':
        print("\n✅ STRATEGY APPROVED FOR DEPLOYMENT")
    elif consensus.decision == 'rejected':
        print("\n❌ STRATEGY REJECTED")
        print("\n⚠️  The army has spoken. Strategy needs improvement.")
    else:
        print("\n⚖️  NO CONSENSUS - Requires human review")


def demo_army_statistics(army):
    """Demo: Army statistics and performance"""
    print("\n" + "="*80)
    print("ARMY STATISTICS")
    print("="*80)
    
    stats = army.get_army_statistics()
    
    print(f"\n📈 OVERALL PERFORMANCE:")
    print(f"   Total Agents: {stats['total_agents']}")
    print(f"   Tasks Completed: {stats['total_tasks_completed']}")
    print(f"   Consensus Votes: {stats['total_consensus_votes']}")
    
    print(f"\n📊 BRIGADE PERFORMANCE:")
    for brigade_name, data in stats['brigades'].items():
        print(f"   {brigade_name:12s}: {data['agent_count']} agents, {data['tasks_completed']} tasks")
    
    print(f"\n🏆 TOP PERFORMERS (by reputation):")
    for i, agent in enumerate(stats['top_performers'][:5], 1):
        print(f"   {i}. {agent['name']:25s} (Brigade: {agent['brigade']}, Score: {agent['reputation_score']:.2f})")
    
    if stats['recent_consensus']:
        print(f"\n📋 RECENT CONSENSUS DECISIONS:")
        for consensus in stats['recent_consensus'][-3:]:
            print(f"   • {consensus['topic'][:40]}... → {consensus['decision'].upper()}")


def demo_multi_agent_research(army):
    """Demo: Multi-agent collaborative research"""
    print("\n" + "="*80)
    print("MULTI-AGENT COLLABORATIVE RESEARCH")
    print("="*80)
    print("\nSimulating a full research cycle with multiple agents...\n")
    
    # Step 1: Pattern Hunter finds a pattern
    print("🔍 Step 1: Pattern Hunter searches for patterns...")
    pattern_result = army.assign_task(
        AgentType.PATTERN_HUNTER,
        "find_patterns",
        {'market_data': 'EURUSD', 'lookback': 1000}
    )
    print(f"   Found: Double bottom pattern with {pattern_result['result']['reliability']:.1%} reliability")
    
    # Step 2: Regime Spotter checks market conditions
    print("\n📊 Step 2: Regime Spotter analyzes market...")
    regime_result = army.assign_task(
        AgentType.REGIME_SPOTTER,
        "detect_regime",
        {'symbol': 'EURUSD'}
    )
    print(f"   Current regime: {regime_result['result']['current_regime']}")
    
    # Step 3: Hypothesis Validator checks validity
    print("\n✓ Step 3: Hypothesis Validator checks hypothesis...")
    hypothesis = {
        'pattern': 'double_bottom',
        'reliability': pattern_result['result']['reliability'],
        'regime': regime_result['result']['current_regime']
    }
    validation_result = army.assign_task(
        AgentType.HYPOTHESIS_VALIDATOR,
        "validate_hypothesis",
        hypothesis
    )
    print(f"   Valid: {validation_result['result']['valid']}")
    
    # Step 4: Risk Brigade assesses risk
    print("\n⚠️  Step 4: Risk Brigade assesses risk...")
    drawdown_result = army.assign_task(
        AgentType.DRAWDOWN_GUARDIAN,
        "assess_drawdown",
        {'strategy': 'double_bottom_entry'}
    )
    print(f"   Current drawdown: {drawdown_result['result']['current_drawdown']:.2%}")
    print(f"   Safe to proceed: {drawdown_result['result']['safe']}")
    
    # Step 5: Position Sizer calculates size
    print("\n💰 Step 5: Position Sizer calculates optimal size...")
    sizing_result = army.assign_task(
        AgentType.POSITION_SIZER,
        "calculate_position",
        {'account': 100000, 'volatility': 0.015}
    )
    print(f"   Optimal size: {sizing_result['result']['optimal_size']:.2%}")
    
    # Step 6: Entry Optimizer finds entry
    print("\n🎯 Step 6: Entry Optimizer finds entry point...")
    entry_result = army.assign_task(
        AgentType.ENTRY_OPTIMIZER,
        "find_entry",
        {'price': 1.0850, 'pattern': 'double_bottom'}
    )
    print(f"   Recommended entry: {entry_result['result']['entry_price']:.5f}")
    
    # Step 7: Data Brigade validates
    print("\n✓ Step 7: Data Brigade validates data quality...")
    data_result = army.assign_task(
        AgentType.DATA_VALIDATOR,
        "validate_data",
        {'dataset': 'pattern_backtest'}
    )
    print(f"   Data valid: {data_result['result']['valid']}")
    
    # Step 8: Audit Brigade final check
    print("\n👮 Step 8: Chief Audit Officer final review...")
    audit_result = army.assign_task(
        AgentType.CHIEF_AUDIT_OFFICER,
        "final_audit",
        {'proposal': 'double_bottom_strategy'}
    )
    print(f"   Audit passed: {audit_result['result']['audit_passed']}")
    
    # Final Consensus
    print("\n🗳️  Final: Full Army Consensus on strategy deployment...")
    final_consensus = army.full_army_consensus(
        "Deploy Double Bottom Strategy",
        {'pattern': 'double_bottom', 'reliability': pattern_result['result']['reliability']}
    )
    
    if final_consensus.decision == 'approved':
        print("\n✅ STRATEGY APPROVED - All brigades in agreement!")
    else:
        print(f"\n⚠️  STRATEGY STATUS: {final_consensus.decision.upper()}")
        print("   Review required before deployment")


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("AGENT ARMY - 60 SPECIALIZED RESEARCH AGENTS")
    print("="*80)
    print("\nThe Intelligence Core now has an army of 60 specialized agents")
    print("organized into 6 brigades, working together as a swarm for")
    print("quantitative research and strategy development.")
    
    # Initialize army
    army = demo_army_overview()
    
    # Run demos
    demo_agent_tasks(army)
    demo_brigade_consensus(army)
    demo_full_army_consensus(army)
    demo_multi_agent_research(army)
    demo_army_statistics(army)
    
    # Summary
    print("\n" + "="*80)
    print("✅ AGENT ARMY DEMO COMPLETE")
    print("="*80)
    print("\n📊 SUMMARY:")
    print(f"   • 60 specialized agents deployed")
    print(f"   • 6 brigades organized by function")
    print(f"   • Individual agent task assignment")
    print(f"   • Brigade-level consensus voting")
    print(f"   • Full army consensus (60 agents)")
    print(f"   • Multi-agent collaborative research")
    print(f"   • Performance tracking and reputation")
    
    print("\n🎯 KEY CAPABILITIES:")
    print("   ✅ Distributed hypothesis generation")
    print("   ✅ Parallel market analysis")
    print("   ✅ Multi-perspective risk assessment")
    print("   ✅ Consensus-based decisions")
    print("   ✅ Specialized agent collaboration")
    print("   ✅ Collective intelligence for research")
    
    print("\nThe Agent Army is ready for duty! 🎖️")


if __name__ == "__main__":
    main()
