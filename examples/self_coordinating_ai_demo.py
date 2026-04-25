"""
Self-Coordinating AI Core - Comprehensive Demo

Demonstrates all coordination capabilities:
1. Task Decomposition
2. Agent Negotiation
3. Resource Allocation
4. Failure Recovery
5. Coordination Layer
6. Shared Memory
7. Governance
8. Learning Loop
9. Dynamic Sub-Agent Creation

All following DeepMind, OpenAI, and Anthropic patterns.
"""

import asyncio
import logging
from trading_bot.core_agent_system import (
    IntegratedAgentSystem,
    SelfCoordinatingCore,
    TaskType,
    TaskPriority,
    AgentArchetype
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_basic_coordination():
    """Demo 1: Basic task coordination"""
    print("\n" + "=" * 70)
    print("DEMO 1: BASIC TASK COORDINATION")
    print("=" * 70)
    
    # Create integrated system
    system = IntegratedAgentSystem({
        'storage_path': 'demo_data',
        'safety_threshold': 0.7
    })
    
    await system.initialize()
    
    # Create coordination core
    coord_core = SelfCoordinatingCore(
        policy_network=system.policy_network,
        value_network=system.value_network,
        react_loop=system.react_loop,
        constitutional_layer=system.constitutional_layer,
        memory_system=system.memory_system,
        tool_registry=system.tool_registry,
        agent_registry=system.agent_registry
    )
    
    await coord_core.initialize()
    
    # Execute a simple task
    result = await coord_core.execute_task(
        task_name="Analyze Market Conditions",
        task_type=TaskType.ANALYSIS,
        description="Analyze current market conditions for EURUSD",
        priority=TaskPriority.HIGH,
        required_capabilities=['analysis', 'market_data'],
        metadata={'symbol': 'EURUSD'}
    )
    
    print(f"\nTask Result:")
    print(f"  Success: {result['success']}")
    print(f"  Duration: {result.get('duration', 0):.2f}s")
    print(f"  Efficiency: {result.get('efficiency', 0):.2%}")
    print(f"  Subtasks: {result.get('subtasks_completed', 0)}")
    
    # Get status
    status = coord_core.get_comprehensive_status()
    print(f"\nCoordination Status:")
    print(f"  Total Tasks: {status['metrics']['total_tasks']}")
    print(f"  Success Rate: {status['metrics']['success_rate']:.2%}")
    print(f"  Active Agents: {status['agent_factory']['active_agents']}")
    
    await coord_core.shutdown()
    await system.shutdown()


async def demo_dynamic_agent_creation():
    """Demo 2: Dynamic sub-agent creation"""
    print("\n" + "=" * 70)
    print("DEMO 2: DYNAMIC SUB-AGENT CREATION")
    print("=" * 70)
    
    system = IntegratedAgentSystem({'storage_path': 'demo_data'})
    await system.initialize()
    
    coord_core = SelfCoordinatingCore(
        policy_network=system.policy_network,
        value_network=system.value_network,
        react_loop=system.react_loop,
        constitutional_layer=system.constitutional_layer,
        memory_system=system.memory_system,
        tool_registry=system.tool_registry,
        agent_registry=system.agent_registry
    )
    
    await coord_core.initialize()
    
    # Create specialized agents on-demand
    print("\nCreating specialized agents...")
    
    # 1. AlphaGo-style decision agent
    alphago_agent = await coord_core.create_sub_agent(
        archetype=AgentArchetype.ALPHAGO_PLAYER,
        name="AlphaTrader",
        capabilities=['decision_making', 'strategy', 'risk_assessment']
    )
    print(f"  ✓ Created: {alphago_agent.name} ({alphago_agent.archetype.value})")
    
    # 2. ReAct reasoning agent
    react_agent = await coord_core.create_sub_agent(
        archetype=AgentArchetype.REACT_REASONER,
        name="MarketReasoner",
        capabilities=['reasoning', 'analysis', 'tool_use']
    )
    print(f"  ✓ Created: {react_agent.name} ({react_agent.archetype.value})")
    
    # 3. Constitutional safety agent
    safety_agent = await coord_core.create_sub_agent(
        archetype=AgentArchetype.CONSTITUTIONAL_GUARDIAN,
        name="SafetyOverseer",
        capabilities=['safety_verification', 'compliance']
    )
    print(f"  ✓ Created: {safety_agent.name} ({safety_agent.archetype.value})")
    
    # 4. Research agent
    research_agent = await coord_core.create_sub_agent(
        archetype=AgentArchetype.RESEARCHER,
        name="StrategyResearcher",
        capabilities=['research', 'experimentation', 'backtesting']
    )
    print(f"  ✓ Created: {research_agent.name} ({research_agent.archetype.value})")
    
    # 5. Optimizer agent
    optimizer_agent = await coord_core.create_sub_agent(
        archetype=AgentArchetype.OPTIMIZER,
        name="ParameterOptimizer",
        capabilities=['optimization', 'tuning']
    )
    print(f"  ✓ Created: {optimizer_agent.name} ({optimizer_agent.archetype.value})")
    
    print(f"\nTotal agents created: {len(coord_core.agent_factory.agents)}")
    
    # Show agent factory status
    factory_status = coord_core.agent_factory.get_status()
    print(f"\nAgent Factory Status:")
    print(f"  Active Agents: {factory_status['active_agents']}")
    print(f"  Average Success Rate: {factory_status['average_success_rate']:.2%}")
    print(f"  Agents by Archetype:")
    for archetype, count in factory_status['agents_by_archetype'].items():
        print(f"    - {archetype}: {count}")
    
    await coord_core.shutdown()
    await system.shutdown()


async def demo_multi_agent_coordination():
    """Demo 3: Multi-agent coordination patterns"""
    print("\n" + "=" * 70)
    print("DEMO 3: MULTI-AGENT COORDINATION PATTERNS")
    print("=" * 70)
    
    system = IntegratedAgentSystem({'storage_path': 'demo_data'})
    await system.initialize()
    
    coord_core = SelfCoordinatingCore(
        policy_network=system.policy_network,
        value_network=system.value_network,
        react_loop=system.react_loop,
        constitutional_layer=system.constitutional_layer,
        memory_system=system.memory_system,
        tool_registry=system.tool_registry,
        agent_registry=system.agent_registry
    )
    
    await coord_core.initialize()
    
    # Parallel coordination
    print("\n1. PARALLEL COORDINATION")
    print("   Multiple agents working simultaneously")
    
    parallel_result = await coord_core.coordinate_multi_agent_task(
        task_name="Parallel Market Analysis",
        subtasks=[
            {
                'name': 'Analyze EURUSD',
                'type': 'ANALYSIS',
                'description': 'Analyze EURUSD market',
                'capabilities': ['analysis']
            },
            {
                'name': 'Analyze GBPUSD',
                'type': 'ANALYSIS',
                'description': 'Analyze GBPUSD market',
                'capabilities': ['analysis']
            },
            {
                'name': 'Analyze USDJPY',
                'type': 'ANALYSIS',
                'description': 'Analyze USDJPY market',
                'capabilities': ['analysis']
            }
        ],
        coordination_pattern='parallel'
    )
    
    print(f"   Result: {parallel_result['success']}")
    print(f"   Duration: {parallel_result['duration']:.2f}s")
    print(f"   Subtasks: {parallel_result['subtasks_completed']}")
    
    # Sequential coordination
    print("\n2. SEQUENTIAL COORDINATION")
    print("   Agents working in sequence (pipeline)")
    
    sequential_result = await coord_core.coordinate_multi_agent_task(
        task_name="Sequential Strategy Development",
        subtasks=[
            {
                'name': 'Research Phase',
                'type': 'RESEARCH',
                'description': 'Research new strategy ideas',
                'capabilities': ['research']
            },
            {
                'name': 'Development Phase',
                'type': 'ANALYSIS',
                'description': 'Develop strategy logic',
                'capabilities': ['analysis']
            },
            {
                'name': 'Testing Phase',
                'type': 'RESEARCH',
                'description': 'Backtest strategy',
                'capabilities': ['backtesting']
            }
        ],
        coordination_pattern='sequential'
    )
    
    print(f"   Result: {sequential_result['success']}")
    print(f"   Duration: {sequential_result['duration']:.2f}s")
    print(f"   Subtasks: {sequential_result['subtasks_completed']}")
    
    # Show learning from coordination
    learning_stats = coord_core.learning_loop.get_learning_stats()
    print(f"\n3. LEARNING FROM COORDINATION")
    print(f"   Total Experiences: {learning_stats['total_experiences']}")
    print(f"   Patterns Learned: {learning_stats['patterns_learned']}")
    if learning_stats['pattern_stats']:
        print(f"   Pattern Performance:")
        for pattern, stats in learning_stats['pattern_stats'].items():
            success_rate = stats['successes'] / max(stats['total_uses'], 1)
            print(f"     - {pattern}: {success_rate:.2%} success, "
                  f"{stats['avg_quality']:.2f} quality")
    
    await coord_core.shutdown()
    await system.shutdown()


async def demo_failure_recovery():
    """Demo 4: Failure recovery mechanisms"""
    print("\n" + "=" * 70)
    print("DEMO 4: FAILURE RECOVERY")
    print("=" * 70)
    
    system = IntegratedAgentSystem({'storage_path': 'demo_data'})
    await system.initialize()
    
    coord_core = SelfCoordinatingCore(
        policy_network=system.policy_network,
        value_network=system.value_network,
        react_loop=system.react_loop,
        constitutional_layer=system.constitutional_layer,
        memory_system=system.memory_system,
        tool_registry=system.tool_registry,
        agent_registry=system.agent_registry
    )
    
    await coord_core.initialize()
    
    print("\nFailure Recovery Strategies:")
    print("  1. Retry with exponential backoff")
    print("  2. Task reassignment to different agent")
    print("  3. Rollback to checkpoint")
    print("  4. Graceful degradation")
    print("  5. Escalation to supervisor")
    
    # Execute task (may fail and recover)
    result = await coord_core.execute_task(
        task_name="High-Risk Operation",
        task_type=TaskType.EXECUTION,
        description="Execute a potentially failing operation",
        priority=TaskPriority.MEDIUM,
        required_capabilities=['execution']
    )
    
    print(f"\nTask Result: {result['success']}")
    
    # Show failure statistics
    failure_stats = coord_core.failure_recovery.get_failure_stats()
    print(f"\nFailure Recovery Stats:")
    print(f"  Total Failures: {failure_stats['total_failures']}")
    if failure_stats['total_failures'] > 0:
        print(f"  By Type:")
        for ftype, count in failure_stats.get('by_type', {}).items():
            print(f"    - {ftype}: {count}")
    
    await coord_core.shutdown()
    await system.shutdown()


async def demo_governance_and_safety():
    """Demo 5: Governance and Constitutional AI safety"""
    print("\n" + "=" * 70)
    print("DEMO 5: GOVERNANCE AND SAFETY")
    print("=" * 70)
    
    system = IntegratedAgentSystem({
        'storage_path': 'demo_data',
        'safety_threshold': 0.8  # Stricter safety
    })
    await system.initialize()
    
    coord_core = SelfCoordinatingCore(
        policy_network=system.policy_network,
        value_network=system.value_network,
        react_loop=system.react_loop,
        constitutional_layer=system.constitutional_layer,
        memory_system=system.memory_system,
        tool_registry=system.tool_registry,
        agent_registry=system.agent_registry
    )
    
    await coord_core.initialize()
    
    print("\nGovernance Policies Active:")
    print("  ✓ Constitutional Safety Check (Anthropic pattern)")
    print("  ✓ Resource Usage Limits")
    print("  ✓ Action Rate Limiting")
    print("  ✓ Audit Logging")
    
    # Execute task with governance
    result = await coord_core.execute_task(
        task_name="Governed Trading Decision",
        task_type=TaskType.EXECUTION,
        description="Make a trading decision with full governance",
        priority=TaskPriority.HIGH,
        required_capabilities=['execution', 'safety_verification']
    )
    
    print(f"\nTask Result: {result['success']}")
    
    # Show governance report
    governance_report = coord_core.governance.get_compliance_report()
    print(f"\nGovernance Compliance Report:")
    print(f"  Total Checks: {governance_report['total_checks']}")
    print(f"  Compliance Rate: {governance_report['compliance_rate']:.2%}")
    print(f"  Safety Checks Passed: {coord_core.metrics.safety_checks_passed}")
    print(f"  Violations: {governance_report['total_violations']}")
    
    if governance_report['total_violations'] > 0:
        print(f"  Violations by Severity:")
        for severity, count in governance_report['violations_by_severity'].items():
            if count > 0:
                print(f"    - {severity}: {count}")
    
    await coord_core.shutdown()
    await system.shutdown()


async def demo_comprehensive_system():
    """Demo 6: Full system integration"""
    print("\n" + "=" * 70)
    print("DEMO 6: COMPREHENSIVE SYSTEM INTEGRATION")
    print("=" * 70)
    
    system = IntegratedAgentSystem({
        'storage_path': 'demo_data',
        'safety_threshold': 0.7,
        'games_per_iteration': 10
    })
    
    await system.initialize()
    
    coord_core = SelfCoordinatingCore(
        policy_network=system.policy_network,
        value_network=system.value_network,
        react_loop=system.react_loop,
        constitutional_layer=system.constitutional_layer,
        memory_system=system.memory_system,
        tool_registry=system.tool_registry,
        agent_registry=system.agent_registry
    )
    
    await coord_core.initialize()
    
    print("\nExecuting complex multi-stage task...")
    print("  Stage 1: Market Research")
    print("  Stage 2: Strategy Development")
    print("  Stage 3: Risk Assessment")
    print("  Stage 4: Execution Planning")
    
    # Complex task requiring multiple capabilities
    result = await coord_core.execute_task(
        task_name="Complete Trading Workflow",
        task_type=TaskType.COORDINATION,
        description="Execute full trading workflow from research to execution",
        priority=TaskPriority.CRITICAL,
        required_capabilities=[
            'research', 'analysis', 'strategy',
            'risk_assessment', 'execution', 'monitoring'
        ],
        metadata={
            'symbol': 'EURUSD',
            'timeframe': '1H',
            'max_risk': 0.02
        }
    )
    
    print(f"\nWorkflow Result:")
    print(f"  Success: {result['success']}")
    print(f"  Duration: {result.get('duration', 0):.2f}s")
    print(f"  Efficiency: {result.get('efficiency', 0):.2%}")
    
    # Comprehensive status
    status = coord_core.get_comprehensive_status()
    
    print(f"\n" + "=" * 70)
    print("COMPREHENSIVE SYSTEM STATUS")
    print("=" * 70)
    
    print(f"\n📊 METRICS")
    print(f"  Total Tasks: {status['metrics']['total_tasks']}")
    print(f"  Completed: {status['metrics']['completed_tasks']}")
    print(f"  Success Rate: {status['metrics']['success_rate']:.2%}")
    print(f"  Avg Duration: {status['metrics']['avg_task_duration']:.2f}s")
    print(f"  Avg Efficiency: {status['metrics']['avg_efficiency']:.2%}")
    
    print(f"\n🤖 AGENTS")
    print(f"  Total Created: {status['agent_factory']['total_agents_created']}")
    print(f"  Active: {status['agent_factory']['active_agents']}")
    print(f"  Success Rate: {status['agent_factory']['average_success_rate']:.2%}")
    print(f"  Tasks Completed: {status['agent_factory']['total_tasks_completed']}")
    
    print(f"\n💾 RESOURCES")
    for res_type, res_info in status['resource_allocator']['resources'].items():
        print(f"  {res_type.upper()}:")
        print(f"    Total: {res_info['total']} {res_info['unit']}")
        print(f"    Available: {res_info['available']} {res_info['unit']}")
        print(f"    Utilization: {res_info['utilization']:.1%}")
    
    print(f"\n🔒 GOVERNANCE")
    print(f"  Compliance Rate: {status['governance']['compliance_rate']:.2%}")
    print(f"  Safety Checks: {status['metrics']['safety_checks_passed']}")
    print(f"  Violations: {status['governance']['total_violations']}")
    
    print(f"\n🧠 LEARNING")
    print(f"  Experiences: {status['learning_loop']['total_experiences']}")
    print(f"  Patterns Learned: {status['learning_loop']['patterns_learned']}")
    
    print(f"\n📡 COORDINATION")
    print(f"  Pending Messages: {status['coordination_layer']['pending_messages']}")
    print(f"  Active Subscriptions: {status['coordination_layer']['active_subscriptions']}")
    
    print(f"\n💭 SHARED MEMORY")
    print(f"  Total Entries: {status['shared_memory']['total_entries']}")
    print(f"  Teams: {status['shared_memory']['teams']}")
    
    await coord_core.shutdown()
    await system.shutdown()


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("SELF-COORDINATING AI CORE - COMPREHENSIVE DEMONSTRATION")
    print("=" * 70)
    print("\nPatterns Implemented:")
    print("  ✓ DeepMind: AlphaGo/AlphaZero (Policy/Value Networks, Self-Play)")
    print("  ✓ OpenAI: GPT-4 Agents (ReAct Loop, Function Calling)")
    print("  ✓ Anthropic: Constitutional AI (Safety Verification)")
    print("\nCapabilities:")
    print("  1. Task Decomposition (HTN Planning)")
    print("  2. Agent Negotiation (Contract Net Protocol)")
    print("  3. Resource Allocation (Priority Scheduling)")
    print("  4. Failure Recovery (Retry, Reassign, Rollback)")
    print("  5. Coordination Layer (Message Passing)")
    print("  6. Shared Memory (Collaborative Workspace)")
    print("  7. Governance (Constitutional Oversight)")
    print("  8. Learning Loop (Experience → Knowledge)")
    print("  9. Dynamic Sub-Agent Creation (On-Demand Specialization)")
    
    try:
        await demo_basic_coordination()
        await demo_dynamic_agent_creation()
        await demo_multi_agent_coordination()
        await demo_failure_recovery()
        await demo_governance_and_safety()
        await demo_comprehensive_system()
        
        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
