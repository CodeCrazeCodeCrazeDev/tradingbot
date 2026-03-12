"""
Hivemind & Perplexity V2 Demo
==============================

Demonstrates the advanced AI systems:

HIVEMIND V2:
- Neural Mesh Network (telepathic communication)
- Quantum Entanglement (synchronized decisions)
- Collective Consciousness (unified awareness)

PERPLEXITY V2:
- Deep Research Engine (multi-source synthesis)
- Reasoning Chains (step-by-step logic)
- Knowledge Graph (connected intelligence)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str) -> None:
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


# ==================== HIVEMIND V2 DEMOS ====================

async def demo_neural_mesh():
    """Demonstrate Neural Mesh Network"""
    print_header("NEURAL MESH NETWORK - Telepathic Communication")
    
    from trading_bot.hivemind import (
        create_neural_mesh,
        SignalType,
    )
    
    print("Creating neural mesh with 5 node types...")
    node_types = ['technical', 'fundamental', 'sentiment', 'risk', 'execution']
    mesh, communicator = create_neural_mesh(node_types, fully_connected=True)
    
    print(f"Mesh topology:")
    topology = mesh.get_mesh_topology()
    print(f"  Nodes: {topology['num_nodes']}")
    print(f"  Links: {topology['num_links']}")
    print(f"  Avg links per node: {topology['avg_links_per_node']:.1f}")
    
    # Send thoughts through the mesh
    print("\nSending thoughts through the mesh...")
    await communicator.broadcast_thought(
        "node_technical_0",
        "RSI showing oversold conditions",
        "analysis",
        confidence=0.8
    )
    
    await communicator.broadcast_thought(
        "node_fundamental_1",
        "Earnings beat expectations",
        "news",
        confidence=0.9
    )
    
    await communicator.broadcast_thought(
        "node_sentiment_2",
        "Social sentiment turning bullish",
        "sentiment",
        confidence=0.7
    )
    
    # Process signals
    result = mesh.process_signals()
    print(f"\nSignal processing:")
    print(f"  Signals processed: {result['signals_processed']}")
    print(f"  Nodes activated: {result['nodes_activated']}")
    print(f"  Links updated: {result['links_updated']}")
    
    # Get collective thought
    collective = mesh.get_collective_thought()
    print(f"\nCollective thought:")
    print(f"  Number of thoughts: {collective['num_thoughts']}")
    print(f"  Average confidence: {collective['avg_confidence']:.2f}")
    print(f"  Global activation: {collective['global_activation']:.2f}")
    print(f"  Synchronization: {collective['synchronization']:.2f}")
    
    # Reach consensus
    print("\nReaching consensus on trading decision...")
    consensus = await communicator.reach_consensus(
        "EURUSD_direction",
        ["buy", "sell", "hold"]
    )
    print(f"  Winner: {consensus['winner'].upper()}")
    print(f"  Confidence: {consensus['confidence']:.1%}")
    print(f"  Votes: {consensus['votes']}")


async def demo_quantum_entanglement():
    """Demonstrate Quantum Entanglement"""
    print_header("QUANTUM ENTANGLEMENT - Synchronized Decisions")
    
    from trading_bot.hivemind import (
        create_quantum_entanglement,
        EntanglementType,
    )
    
    print("Creating quantum entanglement system...")
    node_ids = ['technical', 'fundamental', 'sentiment', 'risk']
    engine, bridge = create_quantum_entanglement(node_ids)
    
    # Initialize quantum nodes
    await bridge.initialize_quantum_nodes(node_ids)
    
    print(f"\nQuantum state summary:")
    summary = engine.get_quantum_state_summary()
    print(f"  Qubits: {summary['num_qubits']}")
    print(f"  Entangled pairs: {summary['num_entangled_pairs']}")
    print(f"  Entanglement groups: {summary['num_entanglement_groups']}")
    print(f"  Average coherence: {summary['avg_coherence']:.2f}")
    
    # Apply node analyses
    print("\nApplying node analyses to quantum states...")
    await bridge.apply_node_analysis('technical', {'signal': 0.6, 'confidence': 0.8})
    await bridge.apply_node_analysis('fundamental', {'signal': 0.4, 'confidence': 0.7})
    await bridge.apply_node_analysis('sentiment', {'signal': 0.3, 'confidence': 0.6})
    await bridge.apply_node_analysis('risk', {'signal': -0.2, 'confidence': 0.9})
    
    # Get quantum decision
    print("\nCollapsing wave function for decision...")
    decision = await bridge.get_quantum_decision()
    print(f"  Action: {decision['action'].upper()}")
    print(f"  Confidence: {decision['confidence']:.1%}")
    print(f"  Vote distribution: {decision['vote_distribution']}")
    print(f"  Quantum effects:")
    print(f"    - Entanglement propagation: {decision['quantum_effects']['entanglement_propagation']}")
    print(f"    - Measurements: {decision['quantum_effects']['measurements']}")


async def demo_collective_consciousness():
    """Demonstrate Collective Consciousness"""
    print_header("COLLECTIVE CONSCIOUSNESS - Unified Awareness")
    
    from trading_bot.hivemind import (
        create_collective_consciousness,
        ConsciousnessLevel,
        EmotionalState,
    )
    
    print("Creating collective consciousness...")
    consciousness = create_collective_consciousness()
    
    # Receive perceptions
    print("\nReceiving perceptions from nodes...")
    perceptions = [
        ("price_action", {"trend": "bullish", "strength": 0.7}, "technical", 0.8),
        ("volume_analysis", {"volume": "increasing", "significance": 0.6}, "technical", 0.7),
        ("news_event", {"type": "earnings", "sentiment": "positive"}, "fundamental", 0.85),
        ("social_sentiment", {"twitter": "bullish", "reddit": "neutral"}, "sentiment", 0.6),
        ("risk_assessment", {"volatility": "moderate", "exposure": 0.3}, "risk", 0.9),
    ]
    
    for ptype, content, source, confidence in perceptions:
        consciousness.receive_perception(ptype, content, source, confidence)
        print(f"  Received: {ptype} from {source} (confidence: {confidence:.1%})")
    
    # Process perceptions
    print("\nProcessing perceptions...")
    result = consciousness.process_perceptions()
    print(f"  Processed: {result['processed']} perceptions")
    print(f"  Focus: {result['focus']}")
    print(f"  Emotional state: {result['emotional_state']}")
    print(f"  Consciousness level: {result['consciousness_level']}")
    print(f"  New insights: {result['new_insights']}")
    
    # Get unified perception
    print("\nUnified perception:")
    unified = consciousness.get_unified_perception()
    print(f"  Consciousness level: {unified['consciousness_level']}")
    print(f"  Emotional state: {unified['emotional_state']}")
    print(f"  Attention focus: {unified['attention_focus']}")
    print(f"  Coherence: {unified['coherence']:.2f}")
    print(f"  Clarity: {unified['clarity']:.2f}")
    
    # Make collective decision
    print("\nMaking collective decision...")
    decision = consciousness.make_collective_decision(['buy', 'sell', 'hold'])
    print(f"  Decision: {decision['decision'].upper()}")
    print(f"  Confidence: {decision['confidence']:.1%}")
    print(f"  Emotional influence: {decision['emotional_influence']}")
    print(f"  Scores: {decision['scores']}")


async def demo_hivemind_v2_full():
    """Demonstrate full Hivemind V2 system"""
    print_header("HIVEMIND V2 - Full System Integration")
    
    from trading_bot.hivemind import (
        create_hivemind_v2,
        HivemindConfig,
    )
    
    print("Creating Hivemind V2 orchestrator...")
    config = HivemindConfig(
        node_types=['technical', 'fundamental', 'sentiment', 'risk', 'execution'],
        use_quantum_entanglement=True,
        consciousness_enabled=True,
        sync_interval_seconds=5,
    )
    
    hivemind = create_hivemind_v2(config)
    
    # Start the hivemind
    print("\nStarting hivemind...")
    await hivemind.start()
    
    # Send perceptions
    print("\nSending perceptions...")
    await hivemind.perceive(
        "technical_analysis",
        {"rsi": 35, "macd": "bullish_cross", "trend": "up"},
        "technical",
        confidence=0.8
    )
    
    await hivemind.perceive(
        "fundamental_data",
        {"pe_ratio": 15, "earnings_growth": 0.2},
        "fundamental",
        confidence=0.75
    )
    
    # Analyze
    print("\nAnalyzing EURUSD...")
    analysis = await hivemind.analyze("EURUSD", {"price": 1.0850, "volume": 1000000})
    print(f"  Collective thought: {analysis['collective_thought']['num_thoughts']} thoughts")
    
    # Make decision
    print("\nMaking collective decision...")
    decision = await hivemind.make_decision("EURUSD")
    print(f"\n{decision.get_summary()}")
    print(f"  Reasoning:")
    for reason in decision.reasoning:
        print(f"    - {reason}")
    
    # Get report
    print("\nSystem report:")
    report = hivemind.get_comprehensive_report()
    print(f"  Mode: {report['state']['mode']}")
    print(f"  Health: {report['state']['health']}")
    print(f"  Coherence: {report['metrics']['coherence']:.2f}")
    print(f"  Synchronization: {report['metrics']['synchronization']:.2f}")
    
    # Stop
    await hivemind.stop()
    print("\nHivemind stopped.")


# ==================== PERPLEXITY V2 DEMOS ====================

async def demo_deep_research():
    """Demonstrate Deep Research Engine"""
    print_header("DEEP RESEARCH ENGINE - Multi-Source Synthesis")
    
    from trading_bot.perplexity_trading import (
        create_deep_research_engine,
        ResearchDepth,
        SourceType,
    )
    
    print("Creating deep research engine...")
    engine = create_deep_research_engine()
    
    print(f"\nRegistered sources: {len(engine.source_registry.sources)}")
    
    # Conduct research
    print("\nResearching 'EURUSD technical analysis'...")
    result = await engine.research(
        "EURUSD technical analysis and trend direction",
        depth=ResearchDepth.STANDARD,
        focus_areas=[SourceType.TECHNICAL, SourceType.MARKET_DATA],
    )
    
    print(f"\nResearch results:")
    print(f"  Query ID: {result.query_id}")
    print(f"  Status: {result.status}")
    print(f"  Findings: {len(result.findings)}")
    
    # Show findings
    print("\nTop findings:")
    for i, finding in enumerate(result.findings[:5], 1):
        print(f"  {i}. [{finding.finding_type}] {finding.content}")
        print(f"     Confidence: {finding.confidence:.1%}, Citations: {len(finding.citations)}")
    
    # Get synthesis
    print("\nSynthesis:")
    synthesis = engine.get_synthesis(result.query_id)
    print(f"  Overall confidence: {synthesis.get('overall_confidence', 0):.1%}")
    print(f"  Total citations: {synthesis.get('total_citations', 0)}")
    
    # Report
    report = engine.get_report()
    print(f"\nEngine statistics:")
    print(f"  Total queries: {report['total_queries']}")
    print(f"  Total findings: {report['total_findings']}")
    print(f"  Total citations: {report['total_citations']}")


async def demo_reasoning_chains():
    """Demonstrate Reasoning Chains"""
    print_header("REASONING CHAINS - Step-by-Step Logic")
    
    from trading_bot.perplexity_trading import (
        create_reasoning_chain_engine,
        ReasoningType,
    )
    
    print("Creating reasoning chain engine...")
    engine = create_reasoning_chain_engine()
    
    # Perform reasoning
    print("\nReasoning about 'Should I buy EURUSD?'...")
    chain = await engine.reason(
        "Should I buy EURUSD given current market conditions?",
        context={"price": 1.0850, "trend": "bullish", "rsi": 45},
        use_tree=True,
    )
    
    print(f"\nReasoning chain:")
    print(f"  Chain ID: {chain.chain_id}")
    print(f"  Total thoughts: {chain.total_thoughts}")
    print(f"  Verified thoughts: {chain.verified_thoughts}")
    print(f"  Rejected thoughts: {chain.rejected_thoughts}")
    
    print("\nReasoning steps:")
    for step in chain.steps:
        print(f"  {step.step_number}. {step.description}")
        print(f"     Confidence: {step.input_confidence:.1%} → {step.output_confidence:.1%}")
    
    print(f"\nConclusion: {chain.conclusion}")
    print(f"Final confidence: {chain.final_confidence:.1%}")
    
    # Get explanation
    print("\n" + "-" * 40)
    print("FULL EXPLANATION:")
    print("-" * 40)
    print(chain.get_explanation())


async def demo_knowledge_graph():
    """Demonstrate Knowledge Graph"""
    print_header("KNOWLEDGE GRAPH - Connected Intelligence")
    
    from trading_bot.perplexity_trading import (
        create_knowledge_graph,
        EntityType,
        RelationType,
    )
    
    print("Creating knowledge graph...")
    graph, reasoner = create_knowledge_graph(populate=True)
    
    stats = graph.get_statistics()
    print(f"\nGraph statistics:")
    print(f"  Total entities: {stats['total_entities']}")
    print(f"  Total relations: {stats['total_relations']}")
    print(f"  Average degree: {stats['avg_degree']:.1f}")
    
    print("\nEntities by type:")
    for etype, count in stats['entities_by_type'].items():
        if count > 0:
            print(f"  {etype}: {count}")
    
    # Query the graph
    print("\nQuerying: 'What does RSI indicate?'")
    answer = reasoner.answer_question("What does RSI indicate?")
    print(f"  Answer: {answer['answer']}")
    print(f"  Confidence: {answer['confidence']:.1%}")
    
    # Find trading signals
    print("\nFinding signals for RSI...")
    rsi = graph.get_entity_by_name("RSI")
    if rsi:
        neighbors = graph.get_neighbors(rsi.entity_id)
        print(f"  Related entities:")
        for neighbor, relation in neighbors[:5]:
            print(f"    - {neighbor.name} ({relation.relation_type.value})")
    
    # Explain relationship
    print("\nExplaining relationship: RSI → Momentum")
    explanation = reasoner.explain_relationship("RSI", "Momentum")
    print(f"  Paths found: {explanation['num_paths']}")
    for exp in explanation['explanations'][:3]:
        print(f"    {exp}")


async def demo_perplexity_v2_full():
    """Demonstrate full Perplexity V2 system"""
    print_header("PERPLEXITY V2 - Full System Integration")
    
    from trading_bot.perplexity_trading import (
        create_perplexity_v2,
        PerplexityConfig,
        ResearchDepth,
    )
    
    print("Creating Perplexity V2 orchestrator...")
    config = PerplexityConfig(
        default_research_depth=ResearchDepth.STANDARD,
        use_tree_of_thoughts=True,
        populate_knowledge=True,
        enable_inference=True,
    )
    
    orchestrator = create_perplexity_v2(config)
    await orchestrator.initialize()
    
    print("\nSystem initialized:")
    print(f"  Research active: {orchestrator.state.research_active}")
    print(f"  Reasoning active: {orchestrator.state.reasoning_active}")
    print(f"  Knowledge active: {orchestrator.state.knowledge_active}")
    
    # Query the system
    print("\nQuerying: 'Analyze EURUSD for a potential buy opportunity'...")
    decision = await orchestrator.query(
        "Analyze EURUSD for a potential buy opportunity considering technical and fundamental factors"
    )
    
    print(f"\n" + "=" * 50)
    print("PERPLEXITY DECISION")
    print("=" * 50)
    print(f"Action: {decision.action.upper()}")
    print(f"Confidence: {decision.confidence:.1%}")
    print(f"Complexity: {decision.complexity.value}")
    print(f"Processing time: {decision.processing_time_ms:.0f}ms")
    
    print(f"\nReasoning chain:")
    for i, step in enumerate(decision.reasoning_chain[:5], 1):
        print(f"  {i}. {step}")
    
    print(f"\nCitations ({len(decision.citations)} total):")
    for citation in decision.citations[:3]:
        print(f"  - [{citation.source}] {citation.content[:60]}...")
    
    # Get full explanation
    print("\n" + "-" * 50)
    print("FULL EXPLANATION:")
    print("-" * 50)
    print(decision.get_explanation())
    
    # System report
    print("\n" + "-" * 50)
    print("SYSTEM REPORT:")
    print("-" * 50)
    report = orchestrator.get_comprehensive_report()
    print(f"Total queries: {report['metrics']['total_queries']}")
    print(f"Total decisions: {report['metrics']['total_decisions']}")
    print(f"Average confidence: {report['metrics']['avg_confidence']:.1%}")


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  HIVEMIND & PERPLEXITY V2 - COMPREHENSIVE DEMO")
    print("  Advanced AI Systems for Trading Intelligence")
    print("=" * 70)
    
    demos = [
        ("Hivemind: Neural Mesh", demo_neural_mesh),
        ("Hivemind: Quantum Entanglement", demo_quantum_entanglement),
        ("Hivemind: Collective Consciousness", demo_collective_consciousness),
        ("Hivemind: Full System", demo_hivemind_v2_full),
        ("Perplexity: Deep Research", demo_deep_research),
        ("Perplexity: Reasoning Chains", demo_reasoning_chains),
        ("Perplexity: Knowledge Graph", demo_knowledge_graph),
        ("Perplexity: Full System", demo_perplexity_v2_full),
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos) + 1}. Run ALL demos")
    print("  0. Exit")
    
    try:
        choice = input("\nSelect demo (0-9): ").strip()
        
        if choice == "0":
            print("Exiting...")
            return
        
        choice = int(choice)
        
        if choice == len(demos) + 1:
            for name, demo_func in demos:
                await demo_func()
                print("\n" + "-" * 70 + "\n")
        elif 1 <= choice <= len(demos):
            await demos[choice - 1][1]()
        else:
            print("Invalid choice")
            
    except ValueError:
        print("Invalid input")
    except KeyboardInterrupt:
        print("\nInterrupted by user")


if __name__ == "__main__":
    asyncio.run(main())
