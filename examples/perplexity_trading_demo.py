"""
Perplexity Trading Architecture Demo
============================================================

Demonstrates the Perplexity Computer-style multi-model
orchestration system for AlphaAlgo trading decisions.

This demo shows:
1. Query decomposition into subtasks
2. Multi-model routing to specialized agents
3. Parallel data retrieval with citations
4. Task graph execution
5. Result assembly with QA verification
6. Human approval workflow
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.perplexity_trading import (
    PerplexityTradingOrchestrator,
    OrchestratorConfig,
    TradingQuery,
    TaskDecomposer,
    ModelRouter,
    AgentType,
    quick_start,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


async def demo_task_decomposition():
    """Demo 1: Task Decomposition"""
    print("\n" + "=" * 60)
    print("DEMO 1: TASK DECOMPOSITION")
    print("=" * 60)
    
    decomposer = TaskDecomposer()
    
    # Example queries
    queries = [
        "Should I buy EURUSD?",
        "Research EURUSD fundamentals, analyze the 4H chart, and prepare an entry",
        "What's the risk/reward for a long position on GBPJPY at current levels?",
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 50)
        
        graph = decomposer.decompose_simple(query)
        
        print(f"   Subtasks: {len(graph.subtasks)}")
        print(f"   Execution batches: {len(graph.execution_order)}")
        
        for i, batch in enumerate(graph.execution_order):
            print(f"   Batch {i+1}: {batch}")
        
        print("\n   Task Details:")
        for task_id, task in list(graph.subtasks.items())[:5]:
            print(f"   - [{task_id}] {task.agent_type.value}: {task.description[:50]}...")


async def demo_model_routing():
    """Demo 2: Multi-Model Routing"""
    print("\n" + "=" * 60)
    print("DEMO 2: MULTI-MODEL ROUTING")
    print("=" * 60)
    
    router = ModelRouter()
    decomposer = TaskDecomposer()
    
    # Decompose a query
    graph = decomposer.decompose_simple("Analyze EURUSD for entry opportunity")
    
    # Route all tasks
    routing_decisions = router.route_batch(list(graph.subtasks.values()))
    
    print("\n📊 Routing Decisions:")
    print("-" * 50)
    
    for task_id, decision in routing_decisions.items():
        task = graph.subtasks[task_id]
        print(f"\n   Task: {task_id}")
        print(f"   Type: {task.task_type.name}")
        print(f"   Routed to: {decision.selected_agent.value}")
        print(f"   Confidence: {decision.confidence:.0%}")
        print(f"   Est. Latency: {decision.estimated_latency_ms:.0f}ms")
    
    # Show agent stats
    print("\n📈 Agent Statistics:")
    print("-" * 50)
    stats = router.get_agent_stats()
    for agent, info in list(stats.items())[:5]:
        print(f"   {agent}: quality={info['quality_score']:.0%}, reliability={info['reliability']:.0%}")


async def demo_full_analysis():
    """Demo 3: Full Analysis Pipeline"""
    print("\n" + "=" * 60)
    print("DEMO 3: FULL ANALYSIS PIPELINE")
    print("=" * 60)
    
    # Create orchestrator with auto-approve for demo
    config = {
        'require_approval_for_trades': False,  # Auto-approve for demo
        'verbose': True,
    }
    
    orchestrator = await quick_start(config)
    
    # Run analysis
    query = "Should I buy EURUSD? Analyze the technical setup and calculate position size for 1% risk."
    
    print(f"\n📝 Query: {query}")
    print("-" * 50)
    
    decision = await orchestrator.analyze(
        query=query,
        symbol="EURUSD",
        timeframe="H4",
        require_approval=False,
    )
    
    # Display results
    print("\n" + decision.get_summary())
    
    # Show citations
    print(f"\n📚 Citations ({len(decision.citations)}):")
    for citation in decision.citations[:5]:
        print(f"   - [{citation.source_type.value}] {citation.data_point[:60]}...")
    
    # Show QA results
    print(f"\n✅ QA Checks ({len(decision.qa_results)}):")
    for qa in decision.qa_results:
        status = "✓" if qa.passed else "✗"
        print(f"   {status} {qa.method}: {qa.issues if qa.issues else 'Passed'}")
    
    # Show stats
    print(f"\n📊 Processing Stats:")
    print(f"   Total time: {decision.processing_time_ms:.0f}ms")
    print(f"   Data freshness: {decision.data_freshness_seconds:.1f}s")
    
    return decision


async def demo_complex_query():
    """Demo 4: Complex Multi-Step Query"""
    print("\n" + "=" * 60)
    print("DEMO 4: COMPLEX MULTI-STEP QUERY")
    print("=" * 60)
    
    orchestrator = await quick_start({'require_approval_for_trades': False})
    
    # Complex query that requires multiple agents
    query = """
    Research the current macroeconomic outlook for EUR and USD.
    Analyze the EURUSD 4H chart for technical signals.
    Check market sentiment and positioning data.
    Calculate optimal position size for 1.5% risk.
    Identify key support and resistance levels.
    Provide a trading recommendation with entry, stop loss, and take profit.
    """
    
    print(f"\n📝 Complex Query:")
    print(query.strip())
    print("-" * 50)
    
    decision = await orchestrator.analyze(
        query=query,
        symbol="EURUSD",
        require_approval=False,
    )
    
    # Display reasoning chain
    print("\n🧠 Reasoning Chain:")
    for i, step in enumerate(decision.reasoning_chain, 1):
        print(f"   {i}. {step[:80]}...")
    
    # Display decision
    print(f"\n📊 Final Decision:")
    print(f"   Action: {decision.action}")
    print(f"   Confidence: {decision.confidence:.1%}")
    print(f"   Entry: {decision.entry_price}")
    print(f"   Stop Loss: {decision.stop_loss}")
    print(f"   Take Profit: {decision.take_profit}")
    print(f"   Position Size: {decision.position_size}")


async def demo_approval_workflow():
    """Demo 5: Human Approval Workflow"""
    print("\n" + "=" * 60)
    print("DEMO 5: HUMAN APPROVAL WORKFLOW")
    print("=" * 60)
    
    # Create orchestrator with approval required
    orchestrator = await quick_start({
        'require_approval_for_trades': True,
        'approval_timeout_seconds': 5.0,  # Short timeout for demo
    })
    
    print("\n📝 Simulating trade that requires approval...")
    print("-" * 50)
    
    # Start analysis in background
    async def run_analysis():
        return await orchestrator.analyze(
            query="Buy EURUSD at market",
            symbol="EURUSD",
            require_approval=True,
        )
    
    # Run analysis
    analysis_task = asyncio.create_task(run_analysis())
    
    # Wait a moment for approval request
    await asyncio.sleep(1.0)
    
    # Check for pending approvals
    pending = orchestrator.get_pending_approvals()
    if pending:
        print(f"\n⏳ Pending Approvals: {len(pending)}")
        for req in pending:
            print(orchestrator.approval_gate.format_request_for_display(req))
            
            # Auto-approve for demo
            print("\n   [AUTO-APPROVING FOR DEMO]")
            orchestrator.approve_request(req.id, "Approved in demo")
    
    # Wait for result
    decision = await analysis_task
    
    print(f"\n📊 Result:")
    print(f"   Action: {decision.action}")
    print(f"   Approval Status: {decision.approval_status.value}")
    print(f"   Approval Reason: {decision.approval_reason}")


async def demo_memory_system():
    """Demo 6: Persistent Memory"""
    print("\n" + "=" * 60)
    print("DEMO 6: PERSISTENT MEMORY SYSTEM")
    print("=" * 60)
    
    orchestrator = await quick_start({'require_approval_for_trades': False})
    
    # Store user preferences
    print("\n💾 Storing user preferences...")
    orchestrator.store_user_preference('risk_tolerance', 'moderate')
    orchestrator.store_user_preference('preferred_timeframe', 'H4')
    orchestrator.store_user_preference('max_risk_per_trade', 0.02)
    
    # Run analysis (will use preferences)
    decision = await orchestrator.analyze(
        query="Should I trade GBPUSD?",
        symbol="GBPUSD",
        require_approval=False,
    )
    
    # Show memory stats
    print("\n📊 Memory Statistics:")
    stats = orchestrator.memory.get_stats()
    print(f"   Short-term entries: {stats['short_term_count']}")
    print(f"   Level counts: {stats['level_counts']}")
    print(f"   Category counts: {stats['category_counts']}")
    print(f"   Knowledge nodes: {stats['knowledge_nodes']}")


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("PERPLEXITY TRADING ARCHITECTURE DEMO")
    print("=" * 60)
    print("""
This demo showcases the Perplexity Computer-style architecture
for AlphaAlgo trading decisions.

Key Features:
- Multi-model routing (8 specialized agents)
- Task decomposition into dependency graphs
- Parallel data retrieval with citations
- QA verification and confidence scoring
- Human-in-the-loop approval
- Persistent memory across sessions
    """)
    
    try:
        # Run demos
        await demo_task_decomposition()
        await demo_model_routing()
        await demo_full_analysis()
        await demo_complex_query()
        await demo_approval_workflow()
        await demo_memory_system()
        
        print("\n" + "=" * 60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
