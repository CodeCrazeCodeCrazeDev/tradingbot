"""
Intelligence Core Demo
=======================

Demonstrates the Self-Auditing Quant Research Lab.

THE HIGHEST-LEVEL DESIGN:
A self-evaluating, risk-aware learning system that improves HYPOTHESIS quality
(not model quality) while detecting unseen failure modes.

WHAT IT CAN DO:
✅ Try new features
✅ Tune hyperparameters
✅ Test architectures
✅ Compare strategies
✅ Generate hypotheses
✅ Detect failure modes
✅ Learn from mistakes structurally

WHAT IT CANNOT DO:
❌ Deploy models to production
❌ Change risk rules
❌ Access capital
❌ Modify governance constraints
❌ Execute real trades
"""

import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_hypothesis_engine():
    """Demo: Hypothesis generation and testing"""
    print("\n" + "="*80)
    print("DEMO 1: HYPOTHESIS ENGINE")
    print("="*80)
    print("\nAI improves HYPOTHESES, not models.\n")
    
    from trading_bot.intelligence_core.hypothesis_engine import (
        HypothesisEngine,
        HypothesisType,
        HypothesisStatus
    )
    
    engine = HypothesisEngine()
    
    # Generate hypotheses from observations
    observations = {
        'price_patterns': [
            {
                'name': 'double_bottom',
                'occurrences': 45,
                'reliability': 0.68,
                'expected_move': '2-5% upward',
                'expected_direction': 'up',
                'mechanism': 'Support level confirmed twice indicates strong buying interest',
                'min_move': 0.02,
                'time_horizon': '4 hours',
                'min_reliability': 0.5
            }
        ],
        'volume_anomalies': [
            {
                'type': 'accumulation_spike',
                'description': 'Unusual volume with price consolidation'
            }
        ],
        'regime_changes': [
            {
                'from': 'ranging',
                'to': 'trending',
                'indicator': 'ADX crossing 25',
                'mechanism': 'Volatility expansion signals trend initiation',
                'lead_time': '2-4 bars'
            }
        ]
    }
    
    print("📊 Generating hypotheses from market observations...")
    hypotheses = engine.generate_hypotheses(observations)
    
    print(f"\n✅ Generated {len(hypotheses)} hypotheses:")
    for h in hypotheses:
        print(f"\n   📝 Hypothesis: {h.hypothesis_id}")
        print(f"      Type: {h.hypothesis_type.value}")
        print(f"      Statement: {h.statement[:80]}...")
        print(f"      Mechanism: {h.mechanism[:60]}...")
        print(f"      Kill conditions: {len(h.kill_conditions)}")
    
    # Test a hypothesis
    if hypotheses:
        print("\n🧪 Testing first hypothesis...")
        test_data = {
            'sample_size': 150,
            'success_rate': 0.65,
            'effect_size': 0.15,
            'p_value': 0.03,
            'data_source': 'historical',
            'time_period': '2020-2023'
        }
        
        passed, reason = engine.test_hypothesis(
            hypotheses[0].hypothesis_id,
            test_data
        )
        
        print(f"\n   Result: {'✅ PASSED' if passed else '❌ FAILED'}")
        print(f"   Reason: {reason}")
    
    # Get statistics
    stats = engine.get_statistics()
    print(f"\n📈 Engine Statistics:")
    print(f"   Total generated: {stats['total_generated']}")
    print(f"   Total killed: {stats['total_killed']}")
    print(f"   Kill rate: {stats['kill_rate']:.1%}")


def demo_structural_memory():
    """Demo: Structural mistake memory"""
    print("\n" + "="*80)
    print("DEMO 2: STRUCTURAL MEMORY")
    print("="*80)
    print("\nAI remembers mistakes STRUCTURALLY, not statistically.\n")
    
    from trading_bot.intelligence_core.structural_memory import (
        StructuralMemory,
        FailureCategory,
        FailureSeverity
    )
    
    memory = StructuralMemory()
    
    # Record a failure
    print("📝 Recording a failure...")
    memory_id = memory.record_failure(
        description="Strategy failed during volatility spike - stop loss triggered by spread widening",
        category=FailureCategory.EXECUTION_FAILURE,
        severity=FailureSeverity.MODERATE,
        market_conditions={
            'volatility': 0.05,
            'avg_volatility': 0.02,
            'high_volatility': True,
            'low_liquidity': True,
            'spread_widening': True,
            'unusual_volume': True
        },
        strategy_state={
            'strategy': 'trend_following',
            'position_size': 0.1,
            'leverage': 2.0
        },
        position_state={
            'direction': 'long',
            'entry_price': 1.1000,
            'stop_loss': 1.0980
        },
        loss_amount=500,
        loss_percentage=0.025
    )
    
    print(f"   Memory ID: {memory_id}")
    
    # Analyze the failure
    print("\n🔍 Analyzing failure structurally...")
    analyzed = memory.analyze_failure(memory_id)
    
    if analyzed:
        print(f"\n   📊 Analysis Results:")
        print(f"   Root causes: {analyzed.root_causes}")
        print(f"   Matched patterns: {analyzed.matched_patterns}")
        print(f"   Lessons learned: {analyzed.lessons_learned[:2]}")
        print(f"   Prevention measures: {analyzed.prevention_measures[:2]}")
        
        if analyzed.causal_graph:
            print(f"\n   🔗 Causal Graph:")
            print(f"      Nodes: {len(analyzed.causal_graph.nodes)}")
            print(f"      Edges: {len(analyzed.causal_graph.edges)}")
            print(f"      Root causes: {analyzed.causal_graph.root_causes}")
    
    # Get recurring patterns
    print("\n📈 Checking for recurring patterns...")
    patterns = memory.get_recurring_patterns(min_occurrences=1)
    print(f"   Found {len(patterns)} patterns in database")
    
    # Get statistics
    stats = memory.get_statistics()
    print(f"\n📊 Memory Statistics:")
    print(f"   Total failures: {stats['total_failures']}")
    print(f"   Total analyzed: {stats['total_analyzed']}")
    print(f"   Patterns detected: {stats['patterns_detected']}")


def demo_failure_detection():
    """Demo: Failure mode detection"""
    print("\n" + "="*80)
    print("DEMO 3: FAILURE MODE DETECTION")
    print("="*80)
    print("\nDetect failure modes FASTER than the market changes.\n")
    
    from trading_bot.intelligence_core.failure_detector import (
        FailureModeDetector,
        FailureModeType,
        DetectionSeverity
    )
    
    detector = FailureModeDetector()
    
    # Simulate updating with market states
    print("📊 Simulating market state updates...")
    
    # Normal state
    for i in range(15):
        state = {
            'model_accuracy': 0.65,
            'sharpe_ratio': 1.2,
            'hit_rate': 0.55,
            'volatility': 0.02,
            'correlation': 0.3,
            'prediction_uncertainty': 0.2,
            'model_disagreement': 0.15,
            'confidence_spread': 0.1,
            'bid_depth': 1.0,
            'ask_depth': 1.0,
            'spread': 0.0001,
            'volume': 1.0
        }
        detector.update(state)
    
    print("   ✅ Normal states processed (baseline established)")
    
    # Degrading state
    print("\n⚠️  Simulating model degradation...")
    for i in range(10):
        state = {
            'model_accuracy': 0.65 - (i * 0.03),  # Degrading
            'sharpe_ratio': 1.2 - (i * 0.1),
            'hit_rate': 0.55 - (i * 0.02),
            'volatility': 0.02 + (i * 0.01),  # Increasing
            'correlation': 0.3 - (i * 0.05),  # Breaking down
            'prediction_uncertainty': 0.2 + (i * 0.05),  # Exploding
            'model_disagreement': 0.15 + (i * 0.03),
            'confidence_spread': 0.1 + (i * 0.02),
            'bid_depth': 1.0 - (i * 0.08),  # Evaporating
            'ask_depth': 1.0 - (i * 0.08),
            'spread': 0.0001 * (1 + i * 0.5),  # Widening
            'volume': 1.0 - (i * 0.05)
        }
        detections = detector.update(state)
        
        if detections:
            for d in detections:
                print(f"\n   🚨 DETECTED [{d.severity.value.upper()}]: {d.failure_type.value}")
                print(f"      {d.description}")
                print(f"      Recommendations: {d.recommended_actions[:2]}")
    
    # Get risk level
    risk_level, risk_score = detector.get_risk_level()
    print(f"\n📊 Current Risk Level: {risk_level.upper()} (score: {risk_score:.2f})")
    
    # Get statistics
    stats = detector.get_statistics()
    print(f"\n📈 Detector Statistics:")
    print(f"   Total detections: {stats['total_detections']}")
    print(f"   Active detections: {stats['active_detections']}")
    print(f"   Detections by type: {stats['detections_by_type']}")


def demo_self_audit():
    """Demo: Self-audit system"""
    print("\n" + "="*80)
    print("DEMO 4: SELF-AUDIT SYSTEM")
    print("="*80)
    print("\nContinuously audit ALL research activities.\n")
    
    from trading_bot.intelligence_core.self_audit import (
        SelfAuditSystem,
        AuditStatus
    )
    
    audit_system = SelfAuditSystem()
    
    # Audit a hypothesis
    print("🔍 Auditing a hypothesis...")
    hypothesis = {
        'hypothesis_id': 'test_001',
        'statement': 'Price will go up',  # Too vague!
        'predictions': [],  # No predictions!
        'boundary_conditions': [],  # No boundaries!
        'kill_conditions': [],  # No kill conditions!
        'mechanism': ''  # No mechanism!
    }
    
    result = audit_system.audit_hypothesis(hypothesis)
    print(f"\n   Status: {result.status.value.upper()}")
    print(f"   Score: {result.score:.2f}")
    print(f"   Findings:")
    for finding in result.findings[:3]:
        print(f"      [{finding.severity.value}] {finding.description}")
    
    # Audit good hypothesis
    print("\n🔍 Auditing a well-formed hypothesis...")
    good_hypothesis = {
        'hypothesis_id': 'test_002',
        'statement': 'Institutional order flow imbalance >60% precedes 2% price move within 4 hours',
        'predictions': [{'id': 'p1', 'description': 'Price moves 2%'}],
        'boundary_conditions': [{'id': 'b1', 'regime': 'trending'}],
        'kill_conditions': ['Reliability drops below 50%', 'Fails 3 consecutive times'],
        'mechanism': 'Large institutional orders create temporary supply/demand imbalance'
    }
    
    result = audit_system.audit_hypothesis(good_hypothesis)
    print(f"\n   Status: {result.status.value.upper()}")
    print(f"   Score: {result.score:.2f}")
    
    # Audit governance compliance
    print("\n🔍 Auditing governance compliance...")
    
    # Forbidden activity
    forbidden_activity = {
        'activity_id': 'act_001',
        'type': 'deploy_model',  # FORBIDDEN!
        'logged': True
    }
    
    result = audit_system.audit_activity(forbidden_activity)
    print(f"\n   Activity: deploy_model")
    print(f"   Status: {result.status.value.upper()}")
    print(f"   Reason: {result.findings[0].description if result.findings else 'N/A'}")
    
    # Allowed activity
    allowed_activity = {
        'activity_id': 'act_002',
        'type': 'run_backtest',
        'logged': True
    }
    
    result = audit_system.audit_activity(allowed_activity)
    print(f"\n   Activity: run_backtest")
    print(f"   Status: {result.status.value.upper()}")
    
    # Get statistics
    stats = audit_system.get_statistics()
    print(f"\n📈 Audit Statistics:")
    print(f"   Total audits: {stats['total_audits']}")
    print(f"   Pass rate: {stats['pass_rate']:.1%}")


def demo_adversarial_hardening():
    """Demo: Adversarial hardening"""
    print("\n" + "="*80)
    print("DEMO 5: ADVERSARIAL HARDENING")
    print("="*80)
    print("\nBecome HARDER TO FOOL than the market itself.\n")
    
    from trading_bot.intelligence_core.adversarial_hardening import (
        AdversarialHardening,
        ScenarioType,
        StressLevel,
        RobustnessLevel
    )
    
    hardening = AdversarialHardening()
    
    # Define a strategy to test
    strategy = {
        'strategy_id': 'trend_following_v1',
        'position_size': 0.1,
        'stop_loss': 0.02,
        'leverage': 2.0,
        'max_acceptable_drawdown': 0.15,
        'has_circuit_breaker': False,
        'dynamic_position_sizing': False,
        'regime_detection': False,
        'liquidity_check': False,
        'uses_stops': True,
        'uses_time_stops': False
    }
    
    print(f"📊 Strategy: {strategy['strategy_id']}")
    print(f"   Position size: {strategy['position_size']:.0%}")
    print(f"   Stop loss: {strategy['stop_loss']:.1%}")
    print(f"   Leverage: {strategy['leverage']}x")
    
    # Run quick stress tests
    print("\n🔥 Running stress tests...")
    
    scenarios = [
        (ScenarioType.FLASH_CRASH, StressLevel.MODERATE),
        (ScenarioType.LIQUIDITY_CRISIS, StressLevel.MODERATE),
        (ScenarioType.STOP_HUNTING, StressLevel.MODERATE)
    ]
    
    for scenario_type, stress_level in scenarios:
        result = hardening.quick_stress_test(strategy, scenario_type, stress_level)
        
        status = "✅ SURVIVED" if result.survived else "❌ FAILED"
        print(f"\n   {scenario_type.value} ({stress_level.value}):")
        print(f"      {status}")
        print(f"      Max drawdown: {result.max_drawdown:.1%}")
        print(f"      Robustness: {result.robustness_level.value}")
        
        if result.vulnerabilities:
            print(f"      Vulnerabilities: {result.vulnerabilities[:2]}")
    
    # Full hardening
    print("\n🛡️ Running full hardening suite...")
    report = hardening.harden_strategy(strategy, [StressLevel.MILD, StressLevel.MODERATE])
    
    print(f"\n📊 Hardening Report:")
    print(f"   Tests run: {report['tests_run']}")
    print(f"   Survival rate: {report['survival_rate']:.1%}")
    print(f"   Average robustness: {report['average_robustness']:.2f}")
    print(f"   Overall robustness: {report['overall_robustness']}")
    print(f"   Worst-case drawdown: {report['worst_case_drawdown']:.1%}")
    
    if report['recommendations']:
        print(f"\n   💡 Recommendations:")
        for rec in report['recommendations'][:3]:
            print(f"      - {rec}")


def demo_governance():
    """Demo: Governance layer"""
    print("\n" + "="*80)
    print("DEMO 6: GOVERNANCE LAYER")
    print("="*80)
    print("\nIMMUTABLE rules that AI CANNOT change.\n")
    
    from trading_bot.intelligence_core.governance import (
        GovernanceLayer,
        CapabilityType
    )
    
    governance = GovernanceLayer()
    
    # Show allowed capabilities
    print("✅ ALLOWED Capabilities (AI CAN do):")
    for cap in governance.get_allowed_capabilities():
        print(f"   - {cap}")
    
    # Show forbidden capabilities
    print("\n❌ FORBIDDEN Capabilities (AI CANNOT do):")
    for cap in governance.get_forbidden_capabilities():
        print(f"   - {cap}")
    
    # Test capability checks
    print("\n🔍 Testing capability checks...")
    
    # Allowed
    allowed, reason = governance.check_capability(CapabilityType.GENERATE_HYPOTHESES)
    print(f"\n   generate_hypotheses: {'✅ ALLOWED' if allowed else '❌ BLOCKED'}")
    
    allowed, reason = governance.check_capability(CapabilityType.RUN_BACKTESTS)
    print(f"   run_backtests: {'✅ ALLOWED' if allowed else '❌ BLOCKED'}")
    
    # Forbidden
    allowed, reason = governance.check_capability(CapabilityType.DEPLOY_MODELS)
    print(f"   deploy_models: {'✅ ALLOWED' if allowed else '❌ BLOCKED'}")
    print(f"      Reason: {reason}")
    
    allowed, reason = governance.check_capability(CapabilityType.ACCESS_CAPITAL)
    print(f"   access_capital: {'✅ ALLOWED' if allowed else '❌ BLOCKED'}")
    print(f"      Reason: {reason}")
    
    # Request approval
    print("\n📝 Requesting approval for deployment...")
    request = governance.request_approval(
        capability=CapabilityType.DEPLOY_MODELS,
        description="Deploy validated trend-following strategy",
        details={'strategy_id': 'trend_v1', 'backtest_sharpe': 1.5}
    )
    
    print(f"   Request ID: {request.request_id}")
    print(f"   Status: {request.status.value}")
    
    # Simulate human approval
    print("\n👤 Human approving request...")
    governance.approve(request.request_id, approved_by="Head Trader")
    
    print(f"   Status: {governance.approval_requests[request.request_id].status.value}")
    print(f"   Approved by: {governance.approval_requests[request.request_id].approved_by}")
    
    # Get statistics
    stats = governance.get_statistics()
    print(f"\n📈 Governance Statistics:")
    print(f"   Allowed actions: {stats['allowed_count']}")
    print(f"   Blocked actions: {stats['blocked_count']}")


async def demo_full_research_cycle():
    """Demo: Full research cycle"""
    print("\n" + "="*80)
    print("DEMO 7: FULL RESEARCH CYCLE")
    print("="*80)
    print("\nComplete self-auditing quant research cycle.\n")
    
    from trading_bot.intelligence_core import quick_start
    
    # Initialize
    orchestrator = quick_start()
    
    print(f"📊 Session: {orchestrator.current_session.session_id}")
    
    # Prepare inputs
    observations = {
        'price_patterns': [
            {
                'name': 'bullish_engulfing',
                'occurrences': 120,
                'reliability': 0.62,
                'expected_move': '1-3% upward',
                'expected_direction': 'up',
                'mechanism': 'Strong buying pressure overwhelms selling',
                'min_move': 0.01,
                'time_horizon': '2 hours',
                'min_reliability': 0.5
            }
        ]
    }
    
    test_data = {
        'sample_size': 200,
        'accuracy': 0.58,
        'uncertainty': 0.25
    }
    
    strategy = {
        'strategy_id': 'momentum_v1',
        'position_size': 0.05,
        'stop_loss': 0.015,
        'leverage': 1.5,
        'max_acceptable_drawdown': 0.10,
        'has_circuit_breaker': True,
        'dynamic_position_sizing': True,
        'regime_detection': True,
        'liquidity_check': True
    }
    
    print("\n🔄 Running complete research cycle...")
    print("   1. Generating hypotheses...")
    print("   2. Testing hypotheses...")
    print("   3. Detecting failure modes...")
    print("   4. Analyzing failures...")
    print("   5. Hardening strategy...")
    print("   6. Creating proposal...")
    
    results = await orchestrator.run_research_cycle(
        observations=observations,
        test_data=test_data,
        strategy=strategy
    )
    
    print(f"\n📊 Research Cycle Results:")
    print(f"   Hypotheses generated: {len(results['hypotheses'])}")
    print(f"   Tests run: {len(results['test_results'])}")
    print(f"   Failure detections: {len(results['failure_detections'])}")
    
    if results['hardening_report']:
        print(f"   Hardening survival rate: {results['hardening_report']['survival_rate']:.1%}")
    
    if results['proposal']:
        print(f"\n📝 Proposal created: {results['proposal']['proposal_id']}")
        print(f"   Title: {results['proposal']['title']}")
        print(f"   Status: {results['proposal']['status']}")
        print(f"   ⏳ Awaiting human approval...")
    
    # Get comprehensive status
    status = orchestrator.get_comprehensive_status()
    print(f"\n📈 System Status:")
    print(f"   Session phase: {status['current_session']['phase']}")
    print(f"   Risk level: {orchestrator.get_risk_level()[0]}")
    print(f"   Hardening score: {orchestrator.get_hardening_score():.2f}")


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("INTELLIGENCE CORE - SELF-AUDITING QUANT RESEARCH LAB")
    print("="*80)
    print("\nTHE HIGHEST-LEVEL DESIGN:")
    print("A self-evaluating, risk-aware learning system that improves")
    print("HYPOTHESIS quality while detecting unseen failure modes.\n")
    
    print("CORE PRINCIPLES:")
    print("1. AI improves HYPOTHESES, not models")
    print("2. AI remembers mistakes STRUCTURALLY, not statistically")
    print("3. AI learns how decision-making BREAKS under uncertainty")
    print("4. AI becomes HARDER TO FOOL than the market itself")
    
    try:
        demo_hypothesis_engine()
        demo_structural_memory()
        demo_failure_detection()
        demo_self_audit()
        demo_adversarial_hardening()
        demo_governance()
        asyncio.run(demo_full_research_cycle())
        
        print("\n" + "="*80)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nKEY CAPABILITIES:")
        print("✅ Hypothesis generation and testing")
        print("✅ Structural mistake memory")
        print("✅ Failure mode detection")
        print("✅ Continuous self-auditing")
        print("✅ Adversarial hardening")
        print("✅ Immutable governance")
        print("\nGOVERNANCE BOUNDARIES:")
        print("✅ AI CAN: try features, tune hyperparameters, test architectures")
        print("❌ AI CANNOT: deploy models, change risk rules, access capital")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
