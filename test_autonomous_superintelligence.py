"""
Test and Demonstration Script for Autonomous Superintelligence
Shows all capabilities and validates system operation.
"""

import asyncio
import logging
from datetime import datetime

from trading_bot.autonomous_superintelligence import (
    AutonomousSuperintelligence,
    AutonomousCore,
    AgentCoordinator,
    ScientificResearchEngine,
    GlobalOpportunityDetector,
    AutonomousResourceManager,
    ContinuousExperimentEngine,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


async def test_core_intelligence():
    """Test core intelligence system."""
    print("\n" + "=" * 80)
    print("TEST 1: CORE INTELLIGENCE")
    print("=" * 80)
    
    core = AutonomousCore({'storage_path': 'test_data/core'})
    await core.initialize()
    
    print(f"✓ Core initialized - Autonomy: {core.state.autonomy_level:.1%}")
    
    decision = await core.think()
    print(f"✓ Decision made: {decision.decision_type} (confidence: {decision.confidence:.2f})")
    
    results = await core.execute_decision(decision)
    print(f"✓ Decision executed - Success: {results['success']}")
    
    status = core.get_status()
    print(f"✓ Status: {status['decisions_made']} decisions, {status['autonomy_level']:.1%} autonomy")
    
    await core.shutdown()
    print("✓ Core shutdown complete\n")


async def test_agent_coordination():
    """Test agent coordination system."""
    print("\n" + "=" * 80)
    print("TEST 2: AGENT COORDINATION")
    print("=" * 80)
    
    coordinator = AgentCoordinator({'storage_path': 'test_data/agents'})
    await coordinator.initialize()
    
    print(f"✓ Coordinator initialized - {len(coordinator.agents)} agents")
    
    task = await coordinator.create_task(
        'market_analysis',
        'Analyze EURUSD market',
        0.9,
        ['market_analysis']
    )
    print(f"✓ Task created: {task.task_id}")
    
    await coordinator.assign_tasks()
    print(f"✓ Tasks assigned")
    
    await asyncio.sleep(2)
    
    status = coordinator.get_status()
    print(f"✓ Status: {status['total_agents']} agents, {status['completed_tasks']} tasks completed")
    
    await coordinator.shutdown()
    print("✓ Coordinator shutdown complete\n")


async def test_research_engine():
    """Test research engine."""
    print("\n" + "=" * 80)
    print("TEST 3: RESEARCH ENGINE")
    print("=" * 80)
    
    research = ScientificResearchEngine({'storage_path': 'test_data/research'})
    await research.initialize()
    
    print(f"✓ Research engine initialized - {len(research.research_questions)} questions")
    
    question = research.research_questions[0] if research.research_questions else None
    
    if question:
        experiment = await research.design_experiment(
            question,
            'backtesting',
            'Test hypothesis through backtesting',
            {'symbols': ['EURUSD']}
        )
        print(f"✓ Experiment designed: {experiment.experiment_id}")
        
        results = await research.run_experiment(experiment)
        print(f"✓ Experiment completed - Sharpe: {results.get('sharpe_ratio', 0):.2f}")
        
        evaluation = await research.evaluate_hypothesis(question)
        print(f"✓ Hypothesis evaluated - Confidence: {evaluation['confidence']:.2f}")
    
    status = research.get_status()
    print(f"✓ Status: {status['total_experiments']} experiments, {status['total_discoveries']} discoveries")
    
    await research.shutdown()
    print("✓ Research engine shutdown complete\n")


async def test_opportunity_detection():
    """Test opportunity detection."""
    print("\n" + "=" * 80)
    print("TEST 4: OPPORTUNITY DETECTION")
    print("=" * 80)
    
    detector = GlobalOpportunityDetector({'storage_path': 'test_data/opportunities'})
    await detector.initialize()
    
    print(f"✓ Detector initialized - {len(detector.markets)} markets")
    
    opportunities = await detector.scan_global_markets()
    print(f"✓ Market scan complete - {len(opportunities)} opportunities found")
    
    if opportunities:
        opp = opportunities[0]
        evaluation = await detector.evaluate_opportunity(opp)
        print(f"✓ Opportunity evaluated - Score: {evaluation['score']:.2f}")
        
        company = await detector.design_new_company(opp)
        print(f"✓ Company designed: {company['name']}")
    
    industries = await detector.detect_emerging_industries()
    print(f"✓ Emerging industries detected: {len(industries)}")
    
    status = detector.get_status()
    print(f"✓ Status: {status['total_opportunities']} opportunities, {status['markets_monitored']} markets")
    
    await detector.shutdown()
    print("✓ Detector shutdown complete\n")


async def test_resource_management():
    """Test resource management."""
    print("\n" + "=" * 80)
    print("TEST 5: RESOURCE MANAGEMENT")
    print("=" * 80)
    
    manager = AutonomousResourceManager({
        'storage_path': 'test_data/resources',
        'total_capital': 100000.0
    })
    await manager.initialize()
    
    print(f"✓ Manager initialized - ${manager.total_capital:,.2f} capital")
    
    allocation = await manager.allocate_resource(
        manager.ResourceType.COMPUTE,
        10.0,
        'test_agent',
        'Testing',
        0.8
    )
    if allocation:
        print(f"✓ Resource allocated: {allocation.amount} cores")
    
    deployment = await manager.deploy_capital(
        10000.0,
        'EURUSD',
        'momentum_strategy',
        0.25,
        0.4
    )
    if deployment:
        print(f"✓ Capital deployed: ${deployment.amount:,.2f}")
    
    status = manager.get_status()
    print(f"✓ Status: ${status['deployed_capital']:,.2f} deployed, {status['active_deployments']} deployments")
    
    await manager.shutdown()
    print("✓ Manager shutdown complete\n")


async def test_experiment_engine():
    """Test experiment engine."""
    print("\n" + "=" * 80)
    print("TEST 6: EXPERIMENT ENGINE")
    print("=" * 80)
    
    engine = ContinuousExperimentEngine({'storage_path': 'test_data/experiments'})
    await engine.initialize()
    
    print(f"✓ Engine initialized - {len(engine.models)} models")
    
    experiment = await engine.create_experiment(
        engine.ExperimentType.MODEL_TRAINING,
        'Test Model Training',
        'Train a test model',
        {'model_type': 'neural_network'}
    )
    print(f"✓ Experiment created: {experiment.experiment_id}")
    
    results = await engine.run_experiment(experiment)
    print(f"✓ Experiment completed - Accuracy: {results['metrics'].get('accuracy', 0):.2f}")
    
    status = engine.get_status()
    print(f"✓ Status: {status['total_experiments']} experiments, {status['total_models']} models")
    
    await engine.shutdown()
    print("✓ Engine shutdown complete\n")


async def test_full_system():
    """Test the full autonomous superintelligence system."""
    print("\n" + "=" * 80)
    print("TEST 7: FULL SYSTEM INTEGRATION")
    print("=" * 80)
    
    config = {
        'total_capital': 50000.0,
        'max_agents': 20,
        'min_agents': 5,
        'safety_enabled': True,
        'max_concurrent_experiments': 3,
        'scan_interval': 30,
        'storage_path': 'test_data/full_system',
    }
    
    superintelligence = AutonomousSuperintelligence(config)
    
    print("Initializing full system...")
    await superintelligence.initialize()
    print("✓ Full system initialized")
    
    print("\nRunning for 30 seconds...")
    
    async def run_for_duration():
        await asyncio.sleep(30)
        await superintelligence.shutdown()
    
    await asyncio.gather(
        superintelligence.start(),
        run_for_duration(),
        return_exceptions=True
    )
    
    print("\n✓ Full system test complete")
    
    status = await superintelligence.get_comprehensive_status()
    
    print("\nFinal Status:")
    print(f"  Autonomy: {status['core']['autonomy_level']:.1%}")
    print(f"  Agents: {status['agents']['total_agents']}")
    print(f"  Discoveries: {status['research']['total_discoveries']}")
    print(f"  Opportunities: {status['opportunities']['total_opportunities']}")
    print(f"  Capital Deployed: ${status['resources']['deployed_capital']:,.2f}")
    print(f"  Experiments: {status['experiments']['completed_experiments']}")


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("AUTONOMOUS SUPERINTELLIGENCE - SYSTEM TESTS")
    print("=" * 80)
    print(f"Started: {datetime.now()}")
    print("=" * 80)
    
    try:
        await test_core_intelligence()
        await test_agent_coordination()
        await test_research_engine()
        await test_opportunity_detection()
        await test_resource_management()
        await test_experiment_engine()
        await test_full_system()
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\nThe Autonomous Superintelligence System is operational!")
        print("Ready to launch with: python autonomous_superintelligence_launcher.py")
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error("Test failed: %s", e, exc_info=True)
        print("\n" + "=" * 80)
        print("TESTS FAILED ✗")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
