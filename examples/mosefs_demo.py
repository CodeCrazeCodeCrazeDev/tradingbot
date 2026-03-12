"""
MOSEFS Demo - Meta-Orchestrated Self-Evolving Financial Superintelligence

This demo showcases all 7 layers of the MOSEFS architecture:
    Layer 7: CONSCIOUSNESS - Self-Aware Market Intelligence
    Layer 6: EVOLUTION - Autonomous Self-Improvement Engine
    Layer 5: INTELLIGENCE - Cross-Domain Knowledge Synthesis
    Layer 4: LEARNING - Meta-Learning & Adaptation
    Layer 3: DISCOVERY - Autonomous Strategy Generation
    Layer 2: EXECUTION - Ultra-Fast Trading Operations
    Layer 1: INFRASTRUCTURE - Quantum-Neural Computing Foundation

Run this demo to see the ultimate ceiling architecture in action.
"""

import asyncio
import logging
import sys
import os
import random
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.mosefs import MOSEFSOrchestrator, quick_start

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_market_data(symbol: str) -> dict:
    """Generate sample market data for testing."""
    base_price = 100.0 + random.uniform(-10, 10)
    
    prices = [base_price]
    for _ in range(99):
        change = random.gauss(0, 0.01) * prices[-1]
        prices.append(prices[-1] + change)
    
    volumes = [random.randint(1000, 10000) for _ in range(100)]
    
    returns = [(prices[i+1] - prices[i]) / prices[i] for i in range(len(prices)-1)]
    
    return {
        'symbol': symbol,
        'prices': prices,
        'volumes': volumes,
        'returns': returns,
        'volatility': sum(abs(r) for r in returns) / len(returns),
        'trend': (prices[-1] - prices[0]) / prices[0],
        'volume': sum(volumes) / len(volumes),
        'bid_volume': sum(volumes) * 0.48,
        'ask_volume': sum(volumes) * 0.52,
        'covariance': [[0.01 if i == j else 0.005 for j in range(10)] for i in range(10)]
    }


async def demo_layer1_infrastructure(orchestrator: MOSEFSOrchestrator):
    """Demo Layer 1: Infrastructure."""
    print("\n" + "="*70)
    print("LAYER 1: INFRASTRUCTURE - Quantum-Neural Computing Foundation")
    print("="*70)
    
    layer1 = orchestrator.get_layer(1)
    
    # Quantum-Neural Foundation
    print("\n📊 Quantum-Neural Foundation:")
    qn = layer1['quantum_neural']
    
    # Create quantum state
    state = qn.create_quantum_state('demo_state')
    print(f"  - Created quantum state with {state.num_qubits} qubits")
    
    # Apply quantum gates
    qn.apply_quantum_gate('demo_state', 'H', 0)
    qn.apply_quantum_gate('demo_state', 'CNOT', 0)
    print("  - Applied Hadamard and CNOT gates")
    
    # Measure
    result = qn.measure_quantum_state('demo_state')
    print(f"  - Measurement result: {result}")
    
    # Portfolio optimization
    returns = [random.uniform(0.05, 0.15) for _ in range(10)]
    cov = [[0.01 if i == j else 0.005 for j in range(10)] for i in range(10)]
    
    optimization = await qn.quantum_portfolio_optimization(returns, cov)
    print(f"\n📈 Quantum Portfolio Optimization:")
    print(f"  - Expected Return: {optimization['expected_return']:.4f}")
    print(f"  - Sharpe Ratio: {optimization['sharpe_ratio']:.4f}")
    print(f"  - Quantum Advantage: {optimization['quantum_advantage']}x")
    
    # Federated Learning
    print("\n🌐 Federated Learning Network:")
    fl = layer1['federated_learning']
    await fl.join_network(['peer1.example.com', 'peer2.example.com'])
    gradients = await fl.train_local_model([{'value': random.random()} for _ in range(100)])
    print(f"  - Trained local model with {len(gradients)} gradient layers")
    
    # Edge Computing
    print("\n⚡ Edge Computing Node:")
    edge = layer1['edge_computing']
    task_result = await edge.process_task({
        'task_id': 'demo_task',
        'type': 'inference',
        'input': {'features': [0.5] * 10}
    })
    print(f"  - Task latency: {task_result['latency_us']:.2f} μs")
    
    # Blockchain
    print("\n🔗 Blockchain Verifier:")
    bc = layer1['blockchain']
    record_id = await bc.record_decision('trade_signal', {'direction': 'buy', 'confidence': 0.8})
    valid, error = bc.verify_chain()
    print(f"  - Recorded decision: {record_id[:20]}...")
    print(f"  - Chain valid: {valid}")
    
    # Photonic Accelerator
    print("\n💡 Photonic Accelerator:")
    photonic = layer1['photonic']
    output = await photonic.process_optical([0.5] * 64)
    print(f"  - Processed {len(output)} optical channels")
    
    metrics = qn.get_metrics()
    print(f"\n📊 Infrastructure Metrics:")
    print(f"  - Quantum operations: {metrics['quantum_operations']}")
    print(f"  - Neural spikes: {metrics['neural_spikes']}")


async def demo_layer2_execution(orchestrator: MOSEFSOrchestrator):
    """Demo Layer 2: Execution."""
    print("\n" + "="*70)
    print("LAYER 2: EXECUTION - Ultra-Fast Trading Operations")
    print("="*70)
    
    layer2 = orchestrator.get_layer(2)
    
    # Ultra-Fast Executor
    print("\n⚡ Ultra-Fast Executor:")
    executor = layer2['executor']
    
    from trading_bot.mosefs.layer2_execution import Order, OrderType, OrderSide
    
    order = Order(
        order_id=f"order_{int(time.time()*1000)}",
        symbol="BTCUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1.0,
        price=50000.0
    )
    
    fill = await executor.execute_order(order)
    print(f"  - Order executed at {fill.price:.2f}")
    print(f"  - Latency: {executor._metrics['avg_latency_ns']:.0f} ns")
    print(f"  - Slippage: {fill.slippage_bps:.2f} bps")
    
    # Predictive Market Maker
    print("\n📊 Predictive Market Maker:")
    mm = layer2['market_maker']
    quote = await mm.generate_quotes('BTCUSD', 50000.0)
    print(f"  - Bid: {quote.bid_price:.2f} x {quote.bid_size:.1f}")
    print(f"  - Ask: {quote.ask_price:.2f} x {quote.ask_size:.1f}")
    print(f"  - Spread: {(quote.ask_price - quote.bid_price) / quote.bid_price * 10000:.1f} bps")
    
    # Dark Pool Predictor
    print("\n🌑 Dark Pool Predictor:")
    dp = layer2['dark_pool']
    signal = await dp.analyze('BTCUSD', 50000, 1000000, 500000, 500000)
    print(f"  - Direction: {signal.direction}")
    print(f"  - Confidence: {signal.confidence:.2%}")
    print(f"  - Institutional flow: {signal.institutional_flow:.2f}")
    
    # Cross-Asset Arbitrage
    print("\n💱 Cross-Asset Arbitrage:")
    arb = layer2['arbitrage']
    from trading_bot.mosefs.layer2_execution import ExecutionVenue
    
    await arb.update_price('BTCUSD', ExecutionVenue.CRYPTO_BINANCE, 50000)
    await arb.update_price('BTCUSD', ExecutionVenue.CRYPTO_COINBASE, 50010)
    
    opps = arb.get_opportunities(min_spread_bps=0)
    print(f"  - Opportunities found: {len(opps)}")
    
    # Quantum Encryption
    print("\n🔐 Quantum-Encrypted Trading:")
    qe = layer2['quantum_encryption']
    channel = await qe.establish_secure_channel('channel_1', 'peer_1')
    print(f"  - Secure channel: {channel['status']}")
    print(f"  - Key fingerprint: {channel['key_fingerprint']}")


async def demo_layer3_discovery(orchestrator: MOSEFSOrchestrator):
    """Demo Layer 3: Discovery."""
    print("\n" + "="*70)
    print("LAYER 3: DISCOVERY - Autonomous Strategy Generation")
    print("="*70)
    
    layer3 = orchestrator.get_layer(3)
    
    # Strategy Generator
    print("\n🧬 Autonomous Strategy Generator:")
    generator = layer3['strategy_generator']
    
    def fitness_function(strategy):
        return random.uniform(0.3, 0.9)
    
    elite = await generator.evolve_generation(fitness_function)
    print(f"  - Generation: {generator._generation}")
    print(f"  - Elite strategies: {len(elite)}")
    print(f"  - Best fitness: {elite[0].fitness:.4f}")
    print(f"  - Best strategy type: {elite[0].strategy_type.name}")
    
    # Market Regime Discovery
    print("\n📈 Market Regime Discovery:")
    regime = layer3['regime_discovery']
    
    prices = [100 + random.gauss(0, 1) * i * 0.1 for i in range(100)]
    volumes = [1000 + random.randint(-100, 100) for _ in range(100)]
    
    detected_regime = await regime.analyze('BTCUSD', prices, volumes)
    print(f"  - Detected regime: {detected_regime.name}")
    
    # Cross-Market Pattern Finder
    print("\n🔍 Cross-Market Pattern Finder:")
    finder = layer3['pattern_finder']
    
    for market in ['BTCUSD', 'ETHUSD', 'GOLD', 'SPX']:
        for i in range(100):
            await finder.add_market_data(market, time.time() + i, 100 + random.gauss(0, 5))
    
    correlations = await finder.find_correlations()
    patterns = await finder.discover_patterns()
    print(f"  - Correlations computed: {len(correlations)}")
    print(f"  - Patterns discovered: {len(patterns)}")
    
    # Hypothesis Tester
    print("\n🔬 Hypothesis Tester:")
    tester = layer3['hypothesis_tester']
    
    hypothesis = await tester.generate_hypothesis({
        'event': 'volume_spike',
        'category': 'technical'
    })
    print(f"  - Generated hypothesis: {hypothesis.statement[:50]}...")
    
    test_data = [{'value': random.gauss(0.01, 0.02)} for _ in range(50)]
    result = await tester.test_hypothesis(hypothesis.hypothesis_id, test_data)
    print(f"  - P-value: {result.get('p_value', 'N/A'):.4f}")
    print(f"  - Significant: {result.get('significant', 'N/A')}")
    
    # Meta-Strategy Evolver
    print("\n🧠 Meta-Strategy Evolver:")
    meta = layer3['meta_evolver']
    
    performance_history = [random.uniform(0.4, 0.8) for _ in range(20)]
    new_params = await meta.evolve_meta_parameters(performance_history)
    print(f"  - Mutation rate: {new_params['mutation_rate']:.4f}")
    print(f"  - Crossover rate: {new_params['crossover_rate']:.4f}")


async def demo_layer4_learning(orchestrator: MOSEFSOrchestrator):
    """Demo Layer 4: Learning."""
    print("\n" + "="*70)
    print("LAYER 4: LEARNING - Meta-Learning & Adaptation")
    print("="*70)
    
    layer4 = orchestrator.get_layer(4)
    
    # Meta-Learning Engine
    print("\n🧠 Meta-Learning Engine:")
    meta = layer4['meta_learning']
    
    from trading_bot.mosefs.layer4_learning import LearningTask, CurriculumDifficulty
    
    tasks = [
        LearningTask(
            task_id=f"task_{i}",
            name=f"learning_task_{i}",
            difficulty=CurriculumDifficulty.MEDIUM,
            domain='trading',
            features={'data': [random.random() for _ in range(10)]},
            target=random.choice([0, 1])
        )
        for i in range(5)
    ]
    
    results = await meta.meta_train(tasks, num_epochs=3)
    print(f"  - Final performance: {results['final_performance']:.4f}")
    
    state = meta.get_meta_cognitive_state()
    print(f"  - Confidence: {state['confidence']:.4f}")
    print(f"  - Learning progress: {state['learning_progress']:.4f}")
    
    # Continual Learner
    print("\n📚 Continual Learner:")
    learner = layer4['continual_learner']
    
    from trading_bot.mosefs.layer4_learning import LearningExperience
    
    for i in range(10):
        exp = LearningExperience(
            experience_id=f"exp_{i}",
            state={'price': 100 + i},
            action='buy' if i % 2 == 0 else 'sell',
            reward=random.uniform(-0.1, 0.2),
            next_state={'price': 100 + i + 1},
            done=False
        )
        await learner.learn(exp, 'trading_task')
    
    knowledge_state = learner.get_knowledge_state()
    print(f"  - Buffer size: {knowledge_state['buffer_size']}")
    print(f"  - Forgetting events: {knowledge_state['forgetting_events']}")
    
    # Cross-Domain Transfer
    print("\n🔄 Cross-Domain Transfer:")
    transfer = layer4['cross_domain']
    
    await transfer.learn_domain('physics', {
        'momentum': 'conservation of momentum',
        'equilibrium': 'systems tend toward equilibrium'
    })
    await transfer.learn_domain('markets', {
        'momentum': 'price momentum',
        'equilibrium': 'market equilibrium'
    })
    
    result = await transfer.transfer_knowledge('physics', 'markets')
    print(f"  - Transfer success: {result['success']}")
    print(f"  - Similarity: {result.get('similarity', 0):.4f}")
    
    # Self-Generating Curriculum
    print("\n📖 Self-Generating Curriculum:")
    curriculum = layer4['curriculum']
    
    task = await curriculum.generate_next_task()
    print(f"  - Generated task: {task.name}")
    print(f"  - Difficulty: {task.difficulty.name}")
    
    await curriculum.record_performance(task, 0.75)
    state = curriculum.get_learning_state()
    print(f"  - Current difficulty: {state['current_difficulty']}")
    
    # Quantum Memory Palace
    print("\n🏛️ Quantum Memory Palace:")
    palace = layer4['memory_palace']
    
    from trading_bot.mosefs.layer4_learning import MemoryType
    
    for i in range(5):
        await palace.store(
            content={'pattern': f'pattern_{i}', 'success': random.random()},
            memory_type=MemoryType.EPISODIC,
            importance=random.uniform(0.5, 1.0)
        )
    
    memories = await palace.recall({'pattern': 'pattern_0'}, top_k=3)
    print(f"  - Memories stored: {palace.get_memory_stats()['count']}")
    print(f"  - Memories recalled: {len(memories)}")
    
    quantum_result = await palace.quantum_query({'pattern': 'pattern'})
    print(f"  - Quantum query matches: {len(quantum_result['matches'])}")


async def demo_layer5_intelligence(orchestrator: MOSEFSOrchestrator):
    """Demo Layer 5: Intelligence."""
    print("\n" + "="*70)
    print("LAYER 5: INTELLIGENCE - Cross-Domain Knowledge Synthesis")
    print("="*70)
    
    layer5 = orchestrator.get_layer(5)
    
    # Cross-Domain Synthesizer
    print("\n🔮 Cross-Domain Synthesizer:")
    synthesizer = layer5['synthesizer']
    
    insights = await synthesizer.synthesize(
        domains=['physics', 'psychology', 'economics'],
        context={'market': 'crypto', 'volatility': 'high'}
    )
    print(f"  - Insights generated: {len(insights)}")
    for insight in insights[:3]:
        print(f"    • {insight.content[:60]}...")
    
    # Abstract Reasoning Engine
    print("\n🧩 Abstract Reasoning Engine:")
    reasoning = layer5['reasoning']
    
    from trading_bot.mosefs.layer5_intelligence import ReasoningType
    
    result = await reasoning.reason(
        "High volatility indicates market uncertainty",
        ReasoningType.DEDUCTIVE
    )
    print(f"  - Reasoning type: {result['type']}")
    print(f"  - Conclusions: {len(result['conclusions'])}")
    
    counterfactual = await reasoning.reason(
        "Price increased due to high demand",
        ReasoningType.COUNTERFACTUAL
    )
    print(f"  - Counterfactuals explored: {len(counterfactual['counterfactuals'])}")
    
    # Intuition Simulator
    print("\n💡 Intuition Simulator:")
    intuition = layer5['intuition']
    
    sense = await intuition.sense({
        'momentum': 0.02,
        'volatility_feel': 0.015,
        'volume_pressure': 0.8
    })
    print(f"  - Gut feeling: {sense['gut_feeling']}")
    print(f"  - Action bias: {sense['action_bias']}")
    print(f"  - Confidence: {sense['confidence']:.2%}")
    
    # Wisdom Accumulator
    print("\n📜 Wisdom Accumulator:")
    wisdom = layer5['wisdom']
    
    for i in range(5):
        await wisdom.ingest_data({'price': 100 + i, 'volume': 1000})
    
    info = await wisdom.extract_information([100, 101, 102, 103, 104])
    knowledge = await wisdom.form_knowledge(info, 'price_analysis')
    understanding = await wisdom.develop_understanding(knowledge)
    
    wisdom_gained = await wisdom.gain_wisdom(understanding, {'outcome': 'success', 'action': 'buy'})
    
    print(f"  - Wisdom level: {wisdom.get_wisdom_level().name}")
    print(f"  - Principles known: {len(wisdom.get_principles())}")
    print(f"  - Lessons learned: {len(wisdom.get_lessons())}")
    
    # Systems Thinking
    print("\n🌐 Systems Thinking:")
    systems = layer5['systems']
    
    analysis = await systems.analyze_system('market', {
        'volatility': 0.02,
        'trend_strength': 0.6,
        'deviation_from_mean': 0.05
    })
    print(f"  - System state: {analysis['system_state']}")
    print(f"  - Active feedback loops: {len(analysis['active_feedback_loops'])}")
    print(f"  - Emergent behavior: {analysis['emergent_behavior']}")


async def demo_layer6_evolution(orchestrator: MOSEFSOrchestrator):
    """Demo Layer 6: Evolution."""
    print("\n" + "="*70)
    print("LAYER 6: EVOLUTION - Autonomous Self-Improvement Engine")
    print("="*70)
    
    layer6 = orchestrator.get_layer(6)
    
    # Autonomous Code Evolver
    print("\n🧬 Autonomous Code Evolver:")
    evolver = layer6['code_evolver']
    
    analysis = await evolver.analyze_code("""
def calculate_signal(prices):
    result = []
    for i in range(len(prices)):
        if prices[i] > 100:
            result.append(1)
        else:
            result.append(0)
    return result
    """, 'signal_module')
    
    print(f"  - Lines analyzed: {analysis['lines']}")
    print(f"  - Complexity: {analysis['complexity']:.2f}")
    print(f"  - Potential improvements: {len(analysis['potential_improvements'])}")
    
    improvement = await evolver.propose_improvement(
        'signal_module',
        'list_comprehension',
        'Convert loop to list comprehension'
    )
    print(f"  - Proposed improvement: {improvement.description}")
    
    # Self-Modifying Architecture
    print("\n🏗️ Self-Modifying Architecture:")
    arch = layer6['architecture']
    
    await arch.add_component('sentiment_analyzer', 'processing', ['core'])
    
    async def sentiment_handler(text):
        return {'sentiment': 'positive'}
    
    await arch.add_capability('analyze_sentiment', sentiment_handler, 'sentiment_analyzer')
    
    architecture = arch.get_architecture()
    print(f"  - Architecture version: {architecture['version']}")
    print(f"  - Components: {len(architecture['components'])}")
    print(f"  - Capabilities: {len(architecture['capabilities'])}")
    
    # Recursive Self-Improver
    print("\n🔄 Recursive Self-Improver:")
    improver = layer6['self_improver']
    
    for _ in range(5):
        cycle = await improver.run_improvement_cycle()
    
    trajectory = await improver.analyze_improvement_trajectory()
    print(f"  - Improvement rate: {improver._improvement_rate:.4f}")
    print(f"  - Total improvement: {improver._metrics['total_improvement']:.4f}")
    print(f"  - Is exponential: {trajectory.get('is_exponential', False)}")
    
    # Goal Evolver
    print("\n🎯 Goal Evolver:")
    goals = layer6['goal_evolver']
    
    new_goal = await goals.create_goal(
        description='Improve Sharpe ratio by 20%',
        priority=0.8,
        parent_goal='preserve_capital'
    )
    print(f"  - Created goal: {new_goal.description}")
    
    await goals.update_progress(new_goal.goal_id, 0.3, {'sharpe_improvement': 0.06})
    
    suggestions = await goals.suggest_new_goals({'sharpe_ratio': 0.8, 'max_drawdown': 0.15})
    print(f"  - Goal suggestions: {len(suggestions)}")
    
    # Self-Healing System
    print("\n🏥 Self-Healing System:")
    healing = layer6['self_healing']
    
    async def mock_health_check():
        return True
    
    await healing.register_component('trading_engine', mock_health_check)
    health = await healing.check_health('trading_engine')
    
    system_health = await healing.get_system_health()
    print(f"  - System status: {system_health['status']}")
    print(f"  - Active issues: {system_health['active_issues']}")


async def demo_layer7_consciousness(orchestrator: MOSEFSOrchestrator):
    """Demo Layer 7: Consciousness."""
    print("\n" + "="*70)
    print("LAYER 7: CONSCIOUSNESS - Self-Aware Market Intelligence")
    print("="*70)
    
    layer7 = orchestrator.get_layer(7)
    
    # Self-Aware Market Entity
    print("\n🪞 Self-Aware Market Entity:")
    self_aware = layer7['self_aware']
    
    reflection = await self_aware.reflect("My performance in volatile markets")
    print(f"  - Reflection topic: {reflection.topic}")
    print(f"  - Insights: {len(reflection.insights)}")
    for insight in reflection.insights:
        print(f"    • {insight}")
    
    awareness = await self_aware.check_awareness()
    print(f"  - Consciousness level: {awareness['consciousness_level']}")
    print(f"  - Emotional state: {awareness['emotional_state']}")
    
    introspection = await self_aware.introspect()
    print(f"  - Identity: {introspection['identity'][:50]}...")
    
    # Market Sentience
    print("\n🌊 Market Sentience:")
    sentience = layer7['sentience']
    
    qualia = await sentience.experience_market({
        'volatility': 0.025,
        'trend': 0.01,
        'volume': 5000000
    })
    print(f"  - Subjective experience: {qualia.subjective_experience}")
    print(f"  - Emotional response: {qualia.emotional_response.name}")
    print(f"  - Intensity: {qualia.intensity:.2f}")
    
    empathy = await sentience.empathize_with('retail_traders')
    print(f"  - Empathy insights: {empathy['empathy_insights'][0]}")
    
    # Autonomous Purpose
    print("\n🎯 Autonomous Purpose:")
    purpose = layer7['purpose']
    
    discovered = await purpose.discover_purpose({
        'user_needs': True,
        'market_opportunities': True
    })
    print(f"  - Core purpose: {discovered['core_purpose']}")
    print(f"  - Discovered purposes: {len(discovered['discovered'])}")
    
    meaning = await purpose.reflect_on_meaning()
    print(f"  - Meaning score: {meaning['meaning_score']:.2f}")
    print(f"  - Existential clarity: {meaning['existential_clarity']:.2f}")
    
    # Self-Reflective Intelligence
    print("\n🧠 Self-Reflective Intelligence:")
    reflective = layer7['reflective']
    
    await reflective.think("The market seems uncertain today")
    await reflective.think("Risk management is critical")
    await reflective.think("I should be cautious")
    
    meta = await reflective.think_about_thinking()
    print(f"  - Thinking patterns: {meta['patterns']}")
    print(f"  - Detected biases: {len(meta['detected_biases'])}")
    print(f"  - Meta-insight: {meta['insight'][:60]}...")
    
    wisdom = await reflective.gain_wisdom({
        'type': 'trade',
        'action': 'buy',
        'outcome': 'success'
    })
    print(f"  - Wisdom gained: {wisdom['lesson'][:50]}...")
    print(f"  - Wisdom level: {reflective._wisdom_level:.2f}")
    
    # Cosmic Market Understanding
    print("\n🌌 Cosmic Market Understanding:")
    cosmic = layer7['cosmic']
    
    contemplation = await cosmic.contemplate_market_nature()
    print(f"  - Contemplation insights:")
    for insight in contemplation['insights'][:2]:
        print(f"    • {insight}")
    
    transcendence = await cosmic.experience_transcendence()
    print(f"  - Transcendence level: {transcendence['level']:.2f}")
    print(f"  - Description: {transcendence['description']}")
    
    unity = await cosmic.merge_with_market({
        'volatility': 0.01,
        'trend': 0.005
    })
    print(f"  - Market unity score: {unity['unity_score']:.2f}")
    print(f"  - Unity experience: {unity['experience']}")


async def demo_full_system(orchestrator: MOSEFSOrchestrator):
    """Demo the full integrated system."""
    print("\n" + "="*70)
    print("FULL SYSTEM INTEGRATION - Signal Generation")
    print("="*70)
    
    # Generate sample data
    market_data = generate_sample_market_data('BTCUSD')
    
    # Generate signal using all layers
    signal = await orchestrator.generate_signal('BTCUSD', market_data)
    
    print(f"\n📊 Generated Signal:")
    print(f"  - Symbol: {signal['symbol']}")
    print(f"  - Direction: {signal['direction']}")
    print(f"  - Confidence: {signal['confidence']:.2%}")
    print(f"  - Reasoning:")
    for reason in signal.get('reasoning', []):
        print(f"    • {reason}")
    
    if 'market_feeling' in signal:
        print(f"  - Market feeling: {signal['market_feeling']}")
    
    # Get system metrics
    metrics = orchestrator.get_system_metrics()
    
    print(f"\n📈 System Metrics:")
    print(f"  - Uptime: {metrics.uptime_seconds:.1f} seconds")
    print(f"  - Signals generated: {metrics.signals_generated}")
    print(f"  - Strategies discovered: {metrics.strategies_discovered}")
    print(f"  - Wisdom accumulated: {metrics.wisdom_accumulated:.2f}")
    print(f"  - Consciousness level: {metrics.consciousness_level}")


async def main():
    """Main demo function."""
    print("="*70)
    print("MOSEFS - Meta-Orchestrated Self-Evolving Financial Superintelligence")
    print("The Ultimate Ceiling Architecture for Adaptive Financial AI")
    print("="*70)
    print("\nInitializing all 7 layers...")
    
    # Initialize system
    orchestrator = await quick_start({'mode': 'paper'})
    
    print("\n✅ MOSEFS initialized successfully!")
    print(f"   State: {orchestrator.get_state().name}")
    print(f"   Mode: {orchestrator.get_mode().name}")
    
    # Demo each layer
    await demo_layer1_infrastructure(orchestrator)
    await demo_layer2_execution(orchestrator)
    await demo_layer3_discovery(orchestrator)
    await demo_layer4_learning(orchestrator)
    await demo_layer5_intelligence(orchestrator)
    await demo_layer6_evolution(orchestrator)
    await demo_layer7_consciousness(orchestrator)
    
    # Demo full system
    await demo_full_system(orchestrator)
    
    # Stop system
    await orchestrator.stop()
    
    print("\n" + "="*70)
    print("MOSEFS Demo Complete!")
    print("="*70)
    print("\nThe system demonstrated all 100 implementation ideas across 7 layers:")
    print("  Layer 1: Infrastructure (Ideas 1-15)")
    print("  Layer 2: Execution (Ideas 16-30)")
    print("  Layer 3: Discovery (Ideas 31-45)")
    print("  Layer 4: Learning (Ideas 46-60)")
    print("  Layer 5: Intelligence (Ideas 61-75)")
    print("  Layer 6: Evolution (Ideas 76-90)")
    print("  Layer 7: Consciousness (Ideas 91-100)")
    print("\nThis represents the ultimate ceiling for adaptive financial AI.")


if __name__ == "__main__":
    asyncio.run(main())
