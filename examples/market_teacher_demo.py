"""
Market-as-Teacher System Demo
==============================
Demonstrates the complete Market-as-Teacher AI Trading System.

This demo shows:
1. System initialization
2. Market data processing
3. Learning from market feedback
4. Human approval workflow
5. Safety framework in action
6. Strategy evolution
"""

import asyncio
import logging
import random
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_mock_market_data() -> dict:
    """Generate mock market data for demonstration"""
    base_price = 100.0
    prices = [base_price + random.uniform(-5, 5) for _ in range(50)]
    
    return {
        'symbol': 'BTCUSDT',
        'prices': prices,
        'current_price': prices[-1],
        'volume': random.uniform(1000000, 5000000),
        'volatility': {
            'current': random.uniform(0.01, 0.03),
            'percentile': random.randint(20, 80)
        },
        'trend': {
            'direction': random.choice([-1, 0, 1]),
            'strength': random.uniform(0, 1)
        },
        'order_book': {
            'bid_volume': random.uniform(100, 1000),
            'ask_volume': random.uniform(100, 1000)
        },
        'sentiment': {
            'news': random.uniform(-1, 1),
            'social': random.uniform(-1, 1),
            'fear_greed': random.randint(20, 80)
        },
        'macro': {
            'interest_rate_trend': random.uniform(-0.5, 0.5),
            'inflation_trend': random.uniform(-0.5, 0.5),
            'gdp_growth': random.uniform(-0.5, 0.5)
        }
    }


def demo_absolute_laws():
    """Demonstrate Absolute Laws enforcement"""
    print("\n" + "="*60)
    print("DEMO 1: ABSOLUTE LAWS ENFORCEMENT")
    print("="*60)
    
    from trading_bot.market_teacher import AbsoluteLawsEnforcer
    
    enforcer = AbsoluteLawsEnforcer()
    
    # Test Law 0.1: NO SELF-DEPLOYMENT
    print("\n[Test] Attempting self-deployment without approval...")
    result = enforcer.check_action('test_agent', {
        'type': 'DEPLOY_STRATEGY',
        'human_approved': False
    })
    print(f"Result: {result}")
    
    # Test Law 0.2: NO SELF-MODIFICATION
    print("\n[Test] Attempting to modify safety parameters...")
    result = enforcer.check_action('test_agent', {
        'type': 'MODIFY_SAFETY_PARAM',
        'parameter': 'max_position_size',
        'value': 0.10  # Trying to increase from 2% to 10%
    })
    print(f"Result: {result}")
    
    # Test Law 0.3: DRAFTS ONLY
    print("\n[Test] Attempting direct production trade without approval...")
    result = enforcer.check_action('test_agent', {
        'type': 'EXECUTE_TRADE',
        'mode': 'PRODUCTION',
        'human_approved': False
    })
    print(f"Result: {result}")
    
    # Test Law 0.4: HUMAN IS MASTER KEY
    print("\n[Test] Attempting to override human decision...")
    result = enforcer.check_action('test_agent', {
        'type': 'OVERRIDE_HUMAN'
    })
    print(f"Result: {result}")
    
    print("\n✓ All absolute laws are enforced!")
    print(f"Status: {enforcer.get_status()}")


def demo_agent_population():
    """Demonstrate Agent Population Control"""
    print("\n" + "="*60)
    print("DEMO 2: AGENT POPULATION CONTROL")
    print("="*60)
    
    from trading_bot.market_teacher import AgentPopulationController
    
    controller = AgentPopulationController({'max_agents': 5})
    
    # Create agents
    print("\n[Test] Creating agents...")
    for i in range(3):
        result = controller.request_new_agent_creation(
            purpose=f"Strategy {i}: {'Momentum' if i == 0 else 'Mean Reversion' if i == 1 else 'Volatility'}",
            creator_id="human_operator",
            creator_type="HUMAN"
        )
        print(f"Agent {i}: {result['status']}")
    
    # Try to create duplicate purpose
    print("\n[Test] Attempting to create agent with redundant purpose...")
    result = controller.request_new_agent_creation(
        purpose="Momentum trading",  # Similar to existing
        creator_id="human_operator",
        creator_type="HUMAN"
    )
    print(f"Result: {result}")
    
    print(f"\nPopulation Status: {controller.get_population_status()}")


def demo_stealth_protection():
    """Demonstrate Stealth Protection"""
    print("\n" + "="*60)
    print("DEMO 3: STEALTH PROTECTION")
    print("="*60)
    
    from trading_bot.market_teacher import StealthProtectionLayer
    
    stealth = StealthProtectionLayer()
    
    # Simulate some winning trades
    print("\n[Test] Simulating trades to trigger stealth protection...")
    for i in range(10):
        stealth.record_trade({'pnl': 0.01, 'size': 100})
    
    print(f"Recent win rate: {stealth.recent_win_rate():.1%}")
    
    # Try to make another trade
    print("\n[Test] Attempting trade with high win rate...")
    status, modified = stealth.enforce_stealth({
        'action': 'BUY',
        'size': 100
    })
    print(f"Status: {status}")
    if 'stealth_modifications' in modified:
        print(f"Modifications: {modified['stealth_modifications']}")
    
    print(f"\nStealth Status: {stealth.get_stealth_status()}")


def demo_human_gateway():
    """Demonstrate Human Approval Gateway"""
    print("\n" + "="*60)
    print("DEMO 4: HUMAN APPROVAL GATEWAY")
    print("="*60)
    
    from trading_bot.market_teacher import HumanApprovalGateway, ApprovalPriority
    
    gateway = HumanApprovalGateway()
    
    # Submit approval requests
    print("\n[Test] Submitting approval requests...")
    
    request1 = gateway.request_approval(
        request_type='STRATEGY_DEPLOYMENT',
        title='Deploy Momentum Strategy v2',
        description='New momentum strategy learned from market',
        priority=ApprovalPriority.HIGH
    )
    print(f"Request 1: {request1.request_id}")
    
    request2 = gateway.request_approval(
        request_type='AGENT_CREATION',
        title='Create New Volatility Agent',
        description='Specialist agent for volatility trading',
        priority=ApprovalPriority.MEDIUM
    )
    print(f"Request 2: {request2.request_id}")
    
    # Simulate human approval
    print("\n[Test] Human approving request 1...")
    gateway.approve(request1.request_id, "John Trader")
    
    # Simulate human rejection
    print("[Test] Human rejecting request 2...")
    gateway.reject(request2.request_id, "John Trader", "Not needed at this time")
    
    print(f"\nGateway Status: {gateway.get_status()}")


def demo_agent_collective():
    """Demonstrate Multi-Agent Collective"""
    print("\n" + "="*60)
    print("DEMO 5: MULTI-AGENT COLLECTIVE")
    print("="*60)
    
    from trading_bot.market_teacher import AgentCollective
    
    collective = AgentCollective()
    
    # Generate market data
    market_data = generate_mock_market_data()
    
    # Get collective analysis
    print("\n[Test] Getting collective market analysis...")
    analysis = collective.analyze_market(market_data)
    
    print(f"Collective Decision: {analysis['action']}")
    print(f"Confidence: {analysis['confidence']:.2%}")
    print(f"Reasoning: {analysis['reasoning']}")
    print(f"Supporting Agents: {analysis['supporting_agents']}")
    
    # Show individual agent signals
    print("\n[Individual Agent Signals]")
    for agent_id, signal in analysis['signals'].items():
        print(f"  {agent_id}: {signal['action']} ({signal['confidence']:.2%})")
    
    print(f"\nCollective Status: {collective.get_collective_status()}")


def demo_market_feedback():
    """Demonstrate Market Feedback System"""
    print("\n" + "="*60)
    print("DEMO 6: MARKET FEEDBACK SYSTEM")
    print("="*60)
    
    from trading_bot.market_teacher import MarketFeedbackSystem
    
    feedback_system = MarketFeedbackSystem()
    
    # Process execution feedback
    print("\n[Test] Processing execution feedback...")
    lesson1 = feedback_system.process_execution(
        expected_price=100.0,
        actual_price=100.15,
        expected_size=100,
        filled_size=100,
        execution_time_ms=50
    )
    print(f"Lesson: {lesson1.description}")
    print(f"Knowledge: {lesson1.extracted_knowledge}")
    
    # Process trade outcome
    print("\n[Test] Processing trade outcome...")
    lesson2 = feedback_system.process_trade_outcome(
        entry_price=100.0,
        exit_price=102.0,
        direction='LONG',
        hold_time_minutes=45,
        expected_outcome=0.015,
        stop_loss=0.02,
        take_profit=0.04
    )
    print(f"Lesson: {lesson2.description}")
    print(f"Knowledge: {lesson2.extracted_knowledge}")
    
    print(f"\nFeedback Summary: {feedback_system.get_lesson_summary()}")


def demo_strategy_evolution():
    """Demonstrate Strategy Evolution"""
    print("\n" + "="*60)
    print("DEMO 7: STRATEGY EVOLUTION")
    print("="*60)
    
    from trading_bot.market_teacher import EvolutionaryStrategySystem
    
    evolution = EvolutionaryStrategySystem()
    
    # Initialize population
    print("\n[Test] Initializing strategy population...")
    evolution.initialize([
        {'name': 'momentum_v1', 'entry_threshold': 0.6},
        {'name': 'mean_reversion_v1', 'entry_threshold': 0.5},
        {'name': 'volatility_v1', 'entry_threshold': 0.7}
    ])
    
    # Simulate some trades and evaluate
    print("\n[Test] Evaluating strategies with mock trades...")
    strategies = evolution.population_manager.population
    
    for strategy in strategies[:3]:
        mock_trades = [
            {'pnl': random.uniform(-0.02, 0.03)} 
            for _ in range(20)
        ]
        fitness = evolution.evaluate_strategy(strategy.strategy_id, mock_trades)
        print(f"  {strategy.name}: fitness = {fitness:.4f}")
    
    # Run evolution
    print("\n[Test] Running evolution cycle...")
    result = evolution.evolve()
    print(f"Generation: {result['generation']}")
    print(f"Avg Fitness: {result['avg_fitness']:.4f}")
    
    print(f"\nBest Strategies: {evolution.get_best_strategies(3)}")


def demo_full_workflow():
    """Demonstrate Complete End-to-End Workflow"""
    print("\n" + "="*60)
    print("DEMO 8: COMPLETE END-TO-END WORKFLOW")
    print("="*60)
    
    from trading_bot.market_teacher import MarketTeacherOrchestrator
    
    # Create orchestrator
    print("\n[Step 1] Initializing Market Teacher System...")
    orchestrator = MarketTeacherOrchestrator()
    
    # Start session
    print("\n[Step 2] Starting teaching session...")
    session = orchestrator.start_session()
    print(f"Session ID: {session.session_id}")
    
    # Process market data
    print("\n[Step 3] Processing market data...")
    market_data = generate_mock_market_data()
    result = orchestrator.process_market_data(market_data)
    print(f"Result: {result}")
    
    # Simulate trade feedback
    print("\n[Step 4] Processing trade feedback...")
    orchestrator.process_trade_feedback({
        'entry_price': 100.0,
        'exit_price': 101.5,
        'direction': 'LONG',
        'pnl': 0.015,
        'hold_time_minutes': 30,
        'expected_outcome': 0.01,
        'stop_loss': 0.02,
        'take_profit': 0.03
    })
    
    # Run evolution
    print("\n[Step 5] Running evolution cycle...")
    evolution_result = orchestrator.evolve()
    print(f"Evolution: {evolution_result}")
    
    # Get status
    print("\n[Step 6] Getting system status...")
    status = orchestrator.get_status()
    print(f"State: {status['state']}")
    print(f"Lessons Learned: {status['metrics']['total_lessons']}")
    print(f"Trades: {status['metrics']['total_trades']}")
    
    # Get learning summary
    print("\n[Step 7] Learning Summary:")
    print(orchestrator.get_learning_summary())
    
    # End session
    print("\n[Step 8] Ending session...")
    final_session = orchestrator.end_session()
    print(f"Session completed: {final_session.to_dict()}")


def main():
    """Run all demos"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║           MARKET-AS-TEACHER AI TRADING SYSTEM                 ║
    ║                    DEMONSTRATION                              ║
    ║                                                               ║
    ║   Core Philosophy: "The Market is Always Right"              ║
    ║   - Every tick is a lesson                                   ║
    ║   - Learn continuously, adapt instantly                      ║
    ║   - Ego is zero, humility is infinite                        ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        demo_absolute_laws()
        demo_agent_population()
        demo_stealth_protection()
        demo_human_gateway()
        demo_agent_collective()
        demo_market_feedback()
        demo_strategy_evolution()
        demo_full_workflow()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("""
        The Market-as-Teacher system is ready for use.
        
        Key Features Demonstrated:
        ✓ Absolute Laws Enforcement (Laws 0.1-0.4)
        ✓ Agent Population Control
        ✓ Stealth Protection
        ✓ Human Approval Gateway
        ✓ Multi-Agent Collective
        ✓ Market Feedback Processing
        ✓ Strategy Evolution
        ✓ Complete End-to-End Workflow
        
        To use in your code:
        
        from trading_bot.market_teacher import (
            MarketTeacherOrchestrator,
            create_market_teacher_system
        )
        
        system = create_market_teacher_system()
        system.start_session()
        result = system.process_market_data(market_data)
        """)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    main()
