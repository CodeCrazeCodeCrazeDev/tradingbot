"""
Foundation Agents Demo
=======================

Demonstrates the autonomous research AI capabilities of the Foundation Agents system.

This demo shows:
1. Cognitive Core - Memory, world model, emotions
2. Curiosity Engine - Anomaly detection, hypothesis generation
3. Knowledge Pipeline - External knowledge integration
4. Research Orchestrator - Experiment design and execution
5. Causal Engine - Causal discovery and theory generation
6. Multi-Agent - Swarm collaboration and debate
7. Safety - Harm monitoring and human override
8. Master Orchestrator - Coordinating all modules
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_cognitive_core():
    """Demonstrate Cognitive Core capabilities"""
    print("\n" + "="*60)
    print("COGNITIVE CORE DEMO")
    print("="*60)
    
    from trading_bot.foundation_agents.cognitive_core.memory_system import MemorySystem
    from trading_bot.foundation_agents.cognitive_core.world_model import WorldModel
    from trading_bot.foundation_agents.cognitive_core.emotion_module import EmotionModule
    from trading_bot.foundation_agents.cognitive_core.goal_manager import GoalManager
    
    # Memory System
    print("\n--- Memory System ---")
    memory = MemorySystem()
    
    # Store episodic memory
    memory.store_episodic({
        'event': 'market_crash',
        'date': '2024-01-15',
        'impact': 'high',
        'lesson': 'Reduce exposure during high volatility'
    })
    
    # Store semantic memory
    memory.store_semantic({
        'concept': 'mean_reversion',
        'definition': 'Prices tend to return to average over time',
        'applicability': ['stocks', 'forex']
    })
    
    print(f"Memory statistics: {memory.get_statistics()}")
    
    # World Model
    print("\n--- World Model ---")
    world_model = WorldModel()
    
    # Update with market state
    market_state = {
        'spy_price': 450.0,
        'vix': 18.5,
        'trend': 'bullish',
        'volume': 'high'
    }
    world_model.update_state(market_state)
    
    # Make prediction
    prediction = world_model.predict_next_state({'time_horizon': '1d'})
    print(f"World model prediction: {prediction}")
    
    # Emotion Module
    print("\n--- Emotion Module ---")
    emotions = EmotionModule()
    
    # Process market events
    emotions.process_trigger('profit', {'amount': 1000, 'percentage': 0.05})
    emotions.process_trigger('volatility_spike', {'vix_change': 5.0})
    
    state = emotions.get_current_state()
    print(f"Emotional state: confidence={state.confidence:.2f}, risk_appetite={state.risk_appetite:.2f}")
    
    # Goal Manager
    print("\n--- Goal Manager ---")
    goals = GoalManager()
    
    # Add goals
    goals.add_goal(
        name="Maximize Sharpe Ratio",
        description="Achieve Sharpe ratio > 2.0",
        priority=1
    )
    goals.add_goal(
        name="Limit Drawdown",
        description="Keep max drawdown < 10%",
        priority=1
    )
    
    print(f"Goal statistics: {goals.get_statistics()}")


def demo_curiosity_engine():
    """Demonstrate Curiosity Engine capabilities"""
    print("\n" + "="*60)
    print("CURIOSITY ENGINE DEMO")
    print("="*60)
    
    from trading_bot.foundation_agents.curiosity_engine.anomaly_detector import AnomalyDetector
    from trading_bot.foundation_agents.curiosity_engine.surprise_scorer import SurpriseScorer
    from trading_bot.foundation_agents.curiosity_engine.hypothesis_generator import HypothesisGenerator
    from trading_bot.foundation_agents.curiosity_engine.interestingness_ranker import InterestingnessRanker
    
    # Generate sample data
    np.random.seed(42)
    normal_returns = np.random.normal(0.001, 0.02, 100)
    # Add anomaly
    normal_returns[50] = -0.15  # Large drop
    
    # Anomaly Detection
    print("\n--- Anomaly Detection ---")
    detector = AnomalyDetector()
    anomalies = detector.detect(normal_returns, asset='SPY')
    print(f"Detected {len(anomalies)} anomalies")
    for a in anomalies[:3]:
        print(f"  - {a.anomaly_type}: severity={a.severity}")
    
    # Surprise Scoring
    print("\n--- Surprise Scoring ---")
    scorer = SurpriseScorer()
    surprise = scorer.score(normal_returns[-1], normal_returns[:-1])
    print(f"Surprise score: {surprise.composite_score:.3f}")
    
    # Hypothesis Generation
    print("\n--- Hypothesis Generation ---")
    generator = HypothesisGenerator()
    
    if anomalies:
        hypothesis = generator.generate_from_anomaly(anomalies[0])
        print(f"Generated hypothesis: {hypothesis.statement}")
        print(f"  Type: {hypothesis.hypothesis_type}")
        print(f"  Priority: {hypothesis.priority}")
    
    # Interestingness Ranking
    print("\n--- Interestingness Ranking ---")
    ranker = InterestingnessRanker()
    
    if hypothesis:
        score = ranker.rank(hypothesis)
        print(f"Interestingness score: {score.overall_score:.3f}")
        print(f"  Novelty: {score.novelty:.3f}")
        print(f"  Impact: {score.impact:.3f}")
        print(f"  Feasibility: {score.feasibility:.3f}")


def demo_knowledge_pipeline():
    """Demonstrate Knowledge Pipeline capabilities"""
    print("\n" + "="*60)
    print("KNOWLEDGE PIPELINE DEMO")
    print("="*60)
    
    from trading_bot.foundation_agents.knowledge_pipeline.arxiv_connector import ArxivConnector
    from trading_bot.foundation_agents.knowledge_pipeline.cross_domain_mapper import CrossDomainMapper
    from trading_bot.foundation_agents.knowledge_pipeline.knowledge_synthesizer import KnowledgeSynthesizer
    
    # ArXiv Connector
    print("\n--- ArXiv Research Discovery ---")
    arxiv = ArxivConnector()
    papers = arxiv.search("reinforcement learning trading", max_results=3)
    print(f"Found {len(papers)} relevant papers")
    for p in papers[:2]:
        print(f"  - {p.get('title', 'Unknown')[:60]}...")
    
    # Cross-Domain Mapper
    print("\n--- Cross-Domain Mapping ---")
    mapper = CrossDomainMapper()
    
    # Map concepts from physics to finance
    mappings = mapper.map_concepts(
        source_domain='physics',
        target_domain='finance',
        concepts=['momentum', 'equilibrium', 'entropy']
    )
    print(f"Mapped {len(mappings)} concepts")
    for m in mappings:
        print(f"  - {m.source_concept} -> {m.target_concept}")
    
    # Knowledge Synthesizer
    print("\n--- Knowledge Synthesis ---")
    synthesizer = KnowledgeSynthesizer()
    
    # Synthesize from papers
    insight = synthesizer.synthesize_from_papers(papers, "algorithmic trading")
    print(f"Synthesized insight: {insight.title}")
    print(f"  Confidence: {insight.confidence:.2f}")
    print(f"  Actionability: {insight.actionability:.2f}")
    
    print(f"\nKnowledge statistics: {synthesizer.get_statistics()}")


def demo_research_orchestrator():
    """Demonstrate Research Orchestrator capabilities"""
    print("\n" + "="*60)
    print("RESEARCH ORCHESTRATOR DEMO")
    print("="*60)
    
    from trading_bot.foundation_agents.research_orchestrator.experiment_designer import ExperimentDesigner
    from trading_bot.foundation_agents.research_orchestrator.methodology_evolver import MethodologyEvolver
    from trading_bot.foundation_agents.research_orchestrator.research_loop import ResearchLoop
    
    # Experiment Designer
    print("\n--- Experiment Design ---")
    designer = ExperimentDesigner()
    
    # Design a backtest experiment
    experiment = designer.design_backtest(
        hypothesis_id="hyp_001",
        strategy_description="Mean reversion with RSI filter",
        benchmark="buy_and_hold",
        assets=['SPY', 'QQQ']
    )
    print(f"Designed experiment: {experiment.name}")
    print(f"  Type: {experiment.experiment_type.value}")
    print(f"  Duration: {experiment.duration.days} days")
    print(f"  Primary metric: {experiment.primary_metric}")
    
    # Methodology Evolver
    print("\n--- Methodology Evolution ---")
    evolver = MethodologyEvolver()
    
    # Record some outcomes
    evolver.record_outcome("meth_0", success=True, p_value=0.03, effect_size=0.15)
    evolver.record_outcome("meth_0", success=True, p_value=0.04, effect_size=0.12)
    evolver.record_outcome("meth_1", success=False, p_value=0.12, effect_size=0.05)
    
    top_methods = evolver.get_top_methodologies(3)
    print(f"Top methodologies:")
    for m in top_methods:
        print(f"  - {m.name}: fitness={m.fitness():.3f}")
    
    # Research Loop
    print("\n--- Research Loop ---")
    loop = ResearchLoop()
    print(f"Research loop status: {loop.get_status()}")


def demo_causal_engine():
    """Demonstrate Causal Engine capabilities"""
    print("\n" + "="*60)
    print("CAUSAL ENGINE DEMO")
    print("="*60)
    
    from trading_bot.foundation_agents.causal_engine.causal_discovery import CausalDiscovery
    from trading_bot.foundation_agents.causal_engine.economic_theory_gen import EconomicTheoryGenerator
    from trading_bot.foundation_agents.causal_engine.symbolic_reasoner import SymbolicReasoner
    
    # Generate sample data
    np.random.seed(42)
    n = 200
    x = np.random.randn(n)
    y = 0.5 * np.roll(x, 1) + 0.3 * np.random.randn(n)  # y depends on lagged x
    
    # Causal Discovery
    print("\n--- Causal Discovery ---")
    discovery = CausalDiscovery()
    
    edges = discovery.discover_pairwise(x, y, 'interest_rates', 'stock_returns')
    print(f"Discovered {len(edges)} causal edges")
    for e in edges:
        print(f"  - {e.source} -> {e.target} (strength={e.strength:.3f}, lag={e.lag})")
    
    # Economic Theory Generator
    print("\n--- Economic Theory Generation ---")
    generator = EconomicTheoryGenerator()
    
    # Generate theory from causal graph
    graph_dict = {
        'nodes': ['interest_rates', 'stock_returns', 'volatility'],
        'edges': [
            {'source': 'interest_rates', 'target': 'stock_returns', 'strength': 0.5, 'lag': 1},
            {'source': 'volatility', 'target': 'stock_returns', 'strength': -0.3, 'lag': 0}
        ]
    }
    
    theory = generator.generate_from_causal_graph(graph_dict)
    print(f"Generated theory: {theory.name}")
    print(f"  Type: {theory.theory_type.value}")
    print(f"  Mechanisms: {len(theory.mechanisms)}")
    print(f"  Predictions: {theory.predictions[:2]}")
    
    # Symbolic Reasoner
    print("\n--- Symbolic Reasoning ---")
    reasoner = SymbolicReasoner()
    
    # Add facts
    reasoner.add_fact('trend', ['SPY', 'up'])
    reasoner.add_fact('momentum', ['SPY', 'strong'])
    reasoner.add_fact('rsi', ['SPY', 25])  # Oversold
    
    # Run inference
    new_facts = reasoner.infer()
    print(f"Inferred {len(new_facts)} new facts")
    
    # Evaluate trading decision
    decision = reasoner.evaluate_trading_decision('SPY', {
        'trend': 'up',
        'momentum': 'strong',
        'rsi': 25
    })
    print(f"Trading recommendations: {decision.get('recommendations', [])}")


def demo_multi_agent():
    """Demonstrate Multi-Agent capabilities"""
    print("\n" + "="*60)
    print("MULTI-AGENT COLLABORATION DEMO")
    print("="*60)
    
    from trading_bot.foundation_agents.multi_agent.agent_swarm import AgentSwarm
    from trading_bot.foundation_agents.multi_agent.debate_protocol import DebateProtocol
    from trading_bot.foundation_agents.multi_agent.consensus_mechanism import ConsensusMechanism
    
    # Agent Swarm
    print("\n--- Agent Swarm ---")
    swarm = AgentSwarm()
    
    print(f"Swarm status: {swarm.get_swarm_status()}")
    
    # Create a collaborative task
    task = swarm.create_task(
        description="Analyze market conditions and recommend position",
        required_capabilities=['technical_analysis', 'risk_assessment']
    )
    print(f"Created task: {task.task_id}")
    print(f"  Assigned agents: {task.assigned_agents}")
    
    # Debate Protocol
    print("\n--- Debate Protocol ---")
    debate = DebateProtocol()
    
    # Create a debate
    d = debate.create_debate(
        topic="Should we increase equity exposure?",
        proposition_name="Increase Exposure",
        proposition_description="Market conditions favor risk-on positioning",
        opposition_name="Maintain Current",
        opposition_description="Uncertainty warrants caution"
    )
    
    # Add arguments
    debate.add_argument(
        d.debate_id,
        agent_id="analyst_1",
        position="proposition",
        claim="Technical indicators show strong momentum",
        evidence=["RSI trending up", "MACD bullish crossover"],
        confidence=0.8
    )
    
    debate.add_argument(
        d.debate_id,
        agent_id="risk_manager",
        position="opposition",
        claim="Volatility is elevated, increasing risk",
        evidence=["VIX above 20", "Correlation breakdown"],
        confidence=0.7
    )
    
    # Evaluate
    evaluation = debate.evaluate_debate(d.debate_id)
    print(f"Debate evaluation: {evaluation}")
    
    # Consensus Mechanism
    print("\n--- Consensus Mechanism ---")
    consensus = ConsensusMechanism()
    
    # Quick consensus
    result = consensus.quick_consensus(
        topic="Recommended position size",
        options=["conservative", "moderate", "aggressive"],
        agent_votes={
            "analyst_1": ("moderate", 0.8),
            "analyst_2": ("aggressive", 0.6),
            "risk_manager": ("conservative", 0.9),
            "strategist": ("moderate", 0.7)
        }
    )
    
    print(f"Consensus result: {result.decision}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Agreement level: {result.agreement_level:.2f}")


def demo_safety():
    """Demonstrate Safety capabilities"""
    print("\n" + "="*60)
    print("SAFETY & ALIGNMENT DEMO")
    print("="*60)
    
    from trading_bot.foundation_agents.safety.harm_monitor import HarmMonitor
    from trading_bot.foundation_agents.safety.alignment_checker import AlignmentChecker
    from trading_bot.foundation_agents.safety.human_override import HumanOverride
    
    # Harm Monitor
    print("\n--- Harm Monitor ---")
    monitor = HarmMonitor()
    
    # Update indicators
    monitor.update_indicator('portfolio_drawdown', 0.08)
    monitor.update_indicator('daily_loss', 0.02)
    monitor.update_indicator('leverage_ratio', 1.5)
    
    print(f"Indicator status: {monitor.get_indicator_status()}")
    print(f"Active alerts: {len(monitor.get_active_alerts())}")
    
    # Check constraints
    results = monitor.check_all_constraints({
        'position_size': 0.15,
        'leverage': 1.5,
        'cash_ratio': 0.10
    })
    print(f"Constraint checks: {results}")
    
    # Alignment Checker
    print("\n--- Alignment Checker ---")
    checker = AlignmentChecker()
    
    # Check action alignment
    action = {
        'action_type': 'trade',
        'indicators': ['risk_managed', 'explainable'],
        'violates': []
    }
    check = checker.check_action(action)
    print(f"Action alignment: {check.status.value} (score={check.score:.2f})")
    
    # Check decision alignment
    decision = {
        'decision_type': 'position_increase',
        'effects': ['positive_returns', 'controlled_drawdown']
    }
    check = checker.check_decision(decision)
    print(f"Decision alignment: {check.status.value} (score={check.score:.2f})")
    
    # Human Override
    print("\n--- Human Override ---")
    override = HumanOverride()
    
    print(f"Control level: {override.control_level.name}")
    print(f"Override status: {override.get_status()}")
    
    # Request approval
    request = override.request_approval(
        action_type="large_trade",
        description="Execute large position in volatile market",
        risk_level="high"
    )
    print(f"Approval request created: {request.request_id}")
    
    # Approve (simulating human action)
    override.approve_request(request.request_id, "admin", "Approved after review")
    print(f"Request approved")


async def demo_orchestrator():
    """Demonstrate the Master Orchestrator"""
    print("\n" + "="*60)
    print("FOUNDATION AGENT ORCHESTRATOR DEMO")
    print("="*60)
    
    from trading_bot.foundation_agents.foundation_agent_orchestrator import (
        FoundationAgentOrchestrator,
        OrchestratorConfig,
        OrchestratorMode
    )
    
    # Create orchestrator
    config = OrchestratorConfig(
        default_mode=OrchestratorMode.BALANCED,
        main_cycle_interval_seconds=5,
        curiosity_threshold=0.5
    )
    
    orchestrator = FoundationAgentOrchestrator(config)
    
    print(f"\nOrchestrator initialized")
    print(f"  State: {orchestrator.state.value}")
    print(f"  Mode: {orchestrator.mode.value}")
    
    # Run a single cycle
    print("\n--- Running Main Cycle ---")
    result = await orchestrator.run_main_cycle()
    print(f"Cycle completed: {result.cycle_id}")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    print(f"  Safety passed: {result.safety_checks_passed}")
    print(f"  Alignment score: {result.alignment_score:.2f}")
    
    # Get status
    print("\n--- Orchestrator Status ---")
    status = orchestrator.get_status()
    print(f"State: {status['state']}")
    print(f"Mode: {status['mode']}")
    print(f"Cycles completed: {status['stats']['cycles_completed']}")
    
    # Get comprehensive statistics
    print("\n--- Module Statistics ---")
    stats = orchestrator.get_statistics()
    print(f"Cognitive Core:")
    print(f"  Memory items: {stats['cognitive_core']['memory'].get('total_items', 0)}")
    print(f"Research:")
    print(f"  Experiments: {stats['research']['experiments'].get('experiments_designed', 0)}")
    print(f"Safety:")
    print(f"  Interventions: {stats['safety']['harm_monitor'].get('alerts_raised', 0)}")


def main():
    """Run all demos"""
    print("="*60)
    print("FOUNDATION AGENTS - AUTONOMOUS RESEARCH AI DEMO")
    print("="*60)
    print("\nThis demo showcases the capabilities of the Foundation Agents")
    print("system for autonomous research and trading AI.\n")
    
    try:
        # Run synchronous demos
        demo_cognitive_core()
        demo_curiosity_engine()
        demo_knowledge_pipeline()
        demo_research_orchestrator()
        demo_causal_engine()
        demo_multi_agent()
        demo_safety()
        
        # Run async orchestrator demo
        asyncio.run(demo_orchestrator())
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nThe Foundation Agents system provides:")
        print("  - Autonomous hypothesis generation and testing")
        print("  - External knowledge integration from research papers")
        print("  - Causal discovery and economic theory synthesis")
        print("  - Multi-agent collaboration and debate")
        print("  - Comprehensive safety and alignment monitoring")
        print("  - Human oversight and control mechanisms")
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        raise


if __name__ == "__main__":
    main()
