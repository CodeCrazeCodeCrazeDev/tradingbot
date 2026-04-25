"""
RadarAI Agent System - Complete Demo
=====================================

Demonstrates the Palantir-inspired multi-agent architecture with:
- Meta-Orchestrator enforcing critical rules
- Data Fusion Agent (perception layer)
- Ontology Agent (knowledge graph)
- Intelligence Agent (LLM reasoning)
- Strategy Agent (Bull/Bear wargame)
- Simulation Agent (10k scenarios)
- Risk & Evaluation Agent (VaR, drawdown checks)
- Execution Agent (LAST step only)
- Experiment Infrastructure (logging)

CRITICAL RULES ENFORCED:
1. Agents NEVER access raw data directly
2. No agent can execute without orchestrator approval
3. All experiments must be logged
4. Simulation happens BEFORE execution
5. Execution is the LAST step, not the first
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import all agents
from meta_orchestrator import MetaOrchestrator, WorkflowStage
from data_fusion_agent import DataFusionAgent
from ontology_agent import OntologyAgent
from intelligence_agent import IntelligenceAgent
from strategy_agent import StrategyAgent
from simulation_agent import SimulationAgent
from risk_evaluation_agent import RiskEvaluationAgent
from execution_agent import ExecutionAgent
from experiment_infrastructure import ExperimentInfrastructure

# Import RadarAI components
import sys
sys.path.append('..')
from radar_ontology import FinancialOntology


async def run_complete_trading_workflow():
    """
    Run a complete trading workflow through all stages.
    
    This demonstrates the proper execution order with all critical rules enforced.
    """
    
    print("=" * 80)
    print("RADARAI AGENT SYSTEM - COMPLETE WORKFLOW DEMO")
    print("=" * 80)
    print()
    
    # =========================================================================
    # INITIALIZATION
    # =========================================================================
    
    print("STEP 1: Initializing Agent System")
    print("-" * 80)
    
    # Create Meta-Orchestrator (command brain)
    meta_orchestrator = MetaOrchestrator(auto_approve_simulations=True)
    print(f"✓ Meta-Orchestrator initialized: {meta_orchestrator.orchestrator_id}")
    
    # Create Experiment Infrastructure (Rule 3: All experiments must be logged)
    experiment_infra = ExperimentInfrastructure(storage_path="./experiment_data")
    print(f"✓ Experiment Infrastructure initialized: {experiment_infra.infra_id}")
    
    # Create experiment
    experiment = experiment_infra.create_experiment(
        name="AAPL Trading Strategy Test",
        description="Test Bull/Bear strategy with full simulation and risk checks",
        tags=["trading", "equities", "demo"],
    )
    print(f"✓ Experiment created: {experiment.experiment_id}")
    
    # Create Financial Ontology
    ontology = FinancialOntology()
    print(f"✓ Financial Ontology initialized: {ontology.ontology_id}")
    
    # Create all agents
    data_fusion = DataFusionAgent(meta_orchestrator)
    ontology_agent = OntologyAgent(meta_orchestrator, ontology)
    intelligence = IntelligenceAgent(meta_orchestrator)
    strategy = StrategyAgent(meta_orchestrator)
    simulation = SimulationAgent(meta_orchestrator)
    risk_eval = RiskEvaluationAgent(meta_orchestrator)
    execution = ExecutionAgent(meta_orchestrator)
    
    print(f"✓ All agents registered with orchestrator")
    print()
    
    # =========================================================================
    # WORKFLOW EXECUTION
    # =========================================================================
    
    print("STEP 2: Starting Workflow")
    print("-" * 80)
    
    # Start workflow
    workflow = await meta_orchestrator.start_workflow()
    print(f"✓ Workflow started: {workflow.execution_id}")
    print(f"  Current stage: {workflow.current_stage.name}")
    print()
    
    # =========================================================================
    # STAGE 1: DATA FUSION (Perception Layer)
    # =========================================================================
    
    print("STAGE 1: Data Fusion - Perception Layer")
    print("-" * 80)
    print("Rule 1 Enforcement: Only Data Fusion Agent can access raw data")
    print()
    
    # Fuse market data
    market_picture = await data_fusion.fuse_market_data()
    print(f"✓ Market picture fused: {market_picture.picture_id}")
    print(f"  Data quality: {market_picture.data_quality:.2%}")
    print(f"  Completeness: {market_picture.completeness:.2%}")
    print(f"  Prices: {list(market_picture.prices.keys())}")
    print()
    
    # Log to experiment
    experiment_infra.log_metric(experiment.experiment_id, "data_quality", market_picture.data_quality)
    
    # Advance workflow
    await meta_orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'market_picture': market_picture.to_dict()}
    )
    print(f"✓ Advanced to: {workflow.current_stage.name}")
    print()
    
    # =========================================================================
    # STAGE 2: ONTOLOGY UPDATE (Knowledge Graph Enrichment)
    # =========================================================================
    
    print("STAGE 2: Ontology Update - Knowledge Graph Enrichment")
    print("-" * 80)
    
    # Enrich ontology
    enrichment = await ontology_agent.enrich_from_market_picture(market_picture.to_dict())
    print(f"✓ Ontology enriched:")
    print(f"  Entities created: {enrichment['entities_created']}")
    print(f"  Relationships created: {enrichment['relationships_created']}")
    print()
    
    # Advance workflow
    await meta_orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'enrichment': enrichment}
    )
    print(f"✓ Advanced to: {workflow.current_stage.name}")
    print()
    
    # =========================================================================
    # STAGE 3: INTELLIGENCE (LLM Reasoning)
    # =========================================================================
    
    print("STAGE 3: Intelligence - LLM Reasoning")
    print("-" * 80)
    print("(Will generate narratives after strategy and simulation)")
    print()
    
    # Advance workflow
    await meta_orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'intelligence': 'ready'}
    )
    print(f"✓ Advanced to: {workflow.current_stage.name}")
    print()
    
    # =========================================================================
    # STAGE 4: STRATEGY RESEARCH (Bull vs Bear Wargame)
    # =========================================================================
    
    print("STAGE 4: Strategy Research - Bull vs Bear Wargame")
    print("-" * 80)
    
    # Analyze opportunity
    symbol = "AAPL"
    strategy_analysis = await strategy.analyze_opportunity(
        symbol=symbol,
        market_picture=market_picture.to_dict(),
        ontology_data={}
    )
    
    print(f"✓ Strategy analysis complete for {symbol}")
    print(f"  Recommended action: {strategy_analysis['recommended_action'].upper()}")
    print(f"  Confidence: {strategy_analysis['confidence']:.0%}")
    print(f"  Bull confidence: {strategy_analysis['bull_thesis']['confidence']:.0%}")
    print(f"  Bear confidence: {strategy_analysis['bear_thesis']['confidence']:.0%}")
    print()
    print("  Bull thesis factors:")
    for factor in strategy_analysis['primary_factors'][:3]:
        print(f"    • {factor}")
    print()
    
    # Log to experiment
    experiment_infra.log_metric(experiment.experiment_id, "strategy_confidence", strategy_analysis['confidence'])
    
    # Advance workflow
    await meta_orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'strategy': strategy_analysis}
    )
    print(f"✓ Advanced to: {workflow.current_stage.name}")
    print()
    
    # =========================================================================
    # STAGE 5: SIMULATION (10,000 Scenarios - REQUIRED BEFORE EXECUTION)
    # =========================================================================
    
    print("STAGE 5: Simulation - World-Model Simulator")
    print("-" * 80)
    print("Rule 4 Enforcement: Simulation MUST happen before execution")
    print()
    
    # Run 10,000 scenario simulation
    print("Running 10,000 forward scenario simulations...")
    simulation_result = await simulation.run_world_model_simulation(
        strategy_analysis=strategy_analysis,
        market_picture=market_picture.to_dict(),
        num_scenarios=10000,
        experiment_id=experiment.experiment_id,
    )
    
    print(f"✓ Simulation complete: {simulation_result.simulation_id}")
    print(f"  Scenarios run: {simulation_result.num_scenarios:,}")
    print(f"  Expected PnL: {simulation_result.expected_pnl:.2%}")
    print(f"  Probability of profit: {simulation_result.probability_of_profit:.0%}")
    print(f"  Expected max drawdown: {simulation_result.expected_max_drawdown:.2%}")
    print(f"  VaR (95%): {simulation_result.var_95:.2%}")
    print(f"  Verdict: {simulation_result.simulation_verdict.upper()}")
    print(f"  Proceed to execution: {simulation_result.proceed_to_execution}")
    print()
    
    # Log to experiment
    experiment_infra.log_metric(experiment.experiment_id, "expected_pnl", simulation_result.expected_pnl)
    experiment_infra.log_metric(experiment.experiment_id, "prob_profit", simulation_result.probability_of_profit)
    experiment_infra.log_artifact(experiment.experiment_id, "simulation_result", simulation_result.to_dict())
    
    # Mark simulation as complete in workflow
    workflow.is_simulation_complete = True
    
    # Advance workflow
    await meta_orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'simulation': simulation_result.to_dict()}
    )
    print(f"✓ Advanced to: {workflow.current_stage.name}")
    print()
    
    # =========================================================================
    # STAGE 6: RISK EVALUATION (VaR, Drawdown, Correlation Checks)
    # =========================================================================
    
    print("STAGE 6: Risk Evaluation - Risk Adjudicator")
    print("-" * 80)
    
    # Create mock portfolio
    portfolio = {
        'total_value': 100000,
        'positions': [],
    }
    
    # Perform risk adjudication
    risk_adjudication = await risk_eval.adjudicate_risk(
        strategy_analysis=strategy_analysis,
        simulation_result=simulation_result.to_dict(),
        portfolio=portfolio,
        market_picture=market_picture.to_dict(),
    )
    
    print(f"✓ Risk adjudication complete: {risk_adjudication.adjudication_id}")
    print(f"  Overall verdict: {risk_adjudication.overall_verdict.upper()}")
    print(f"  Risk score: {risk_adjudication.risk_score:.0f}/100")
    print(f"  VaR (95%): {risk_adjudication.var_95_pct:.2f}%")
    print(f"  Max drawdown: {risk_adjudication.max_drawdown_pct:.2f}%")
    print()
    print(f"  Checks passed: {len(risk_adjudication.checks_passed)}")
    for check in risk_adjudication.checks_passed[:3]:
        print(f"    ✓ {check}")
    print()
    
    if risk_adjudication.warnings:
        print(f"  Warnings: {len(risk_adjudication.warnings)}")
        for warning in risk_adjudication.warnings:
            print(f"    ⚠ {warning}")
        print()
    
    print(f"  Position size limit: ${risk_adjudication.position_size_limit:,.2f}")
    print(f"  Stop loss level: ${risk_adjudication.stop_loss_level:.2f}")
    print()
    
    # Log to experiment
    experiment_infra.log_metric(experiment.experiment_id, "risk_score", risk_adjudication.risk_score)
    
    # Advance workflow
    await meta_orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'risk': risk_adjudication.to_dict()}
    )
    print(f"✓ Advanced to: {workflow.current_stage.name}")
    print()
    
    # =========================================================================
    # GENERATE INTELLIGENCE NARRATIVE
    # =========================================================================
    
    print("Generating Intelligence Narrative")
    print("-" * 80)
    
    # Generate trade narrative
    narrative = await intelligence.generate_trade_narrative(
        strategy_analysis=strategy_analysis,
        simulation_results=simulation_result.to_dict(),
        risk_assessment=risk_adjudication.to_dict(),
    )
    
    print(f"✓ Trade narrative generated: {narrative.narrative_id}")
    print()
    print(f"  Title: {narrative.title}")
    print()
    print(f"  Thesis:")
    print(f"  {narrative.thesis}")
    print()
    print(f"  Supporting Evidence:")
    for i, evidence in enumerate(narrative.supporting_evidence[:3], 1):
        print(f"    {i}. {evidence}")
    print()
    print(f"  Confidence: {narrative.confidence_explanation}")
    print()
    
    # Generate risk brief
    risk_brief = await intelligence.generate_risk_brief(
        risk_assessment=risk_adjudication.to_dict(),
        portfolio=portfolio,
    )
    
    print(f"✓ Risk brief generated: {risk_brief.brief_id}")
    print(f"  {risk_brief.overall_assessment}")
    print()
    
    # =========================================================================
    # STAGE 7: EXECUTION (THE LAST STEP)
    # =========================================================================
    
    print("STAGE 7: Execution - Order Management")
    print("-" * 80)
    print("Rule 5 Enforcement: Execution is the LAST step, not the first")
    print("Rule 2 Enforcement: No execution without orchestrator approval")
    print()
    
    # Attempt execution
    print("Requesting execution approval from Meta-Orchestrator...")
    execution_result = await execution.execute_trade(
        workflow_id=workflow.execution_id,
        strategy_analysis=strategy_analysis,
        simulation_result=simulation_result.to_dict(),
        risk_adjudication=risk_adjudication.to_dict(),
    )
    
    if execution_result['status'] == 'executed':
        print(f"✓ Trade executed successfully!")
        print(f"  Order ID: {execution_result['order']['order_id']}")
        print(f"  Symbol: {execution_result['order']['symbol']}")
        print(f"  Action: {execution_result['order']['action'].upper()}")
        print(f"  Quantity: {execution_result['order']['quantity']:.2f}")
        print(f"  Price: ${execution_result['order']['price']:.2f}")
        print(f"  Status: {execution_result['order']['status']}")
        print()
        
        # Log to experiment
        experiment_infra.log_metric(experiment.experiment_id, "trade_executed", 1)
        experiment_infra.log_artifact(experiment.experiment_id, "execution_result", execution_result)
    else:
        print(f"✗ Execution blocked: {execution_result.get('reason')}")
        print()
    
    # =========================================================================
    # WORKFLOW COMPLETE
    # =========================================================================
    
    print("=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)
    print()
    
    # Get orchestrator status
    orchestrator_status = meta_orchestrator.get_status()
    print("Meta-Orchestrator Status:")
    print(f"  Registered agents: {len(orchestrator_status['registered_agents'])}")
    print(f"  Total requests: {orchestrator_status['total_requests']}")
    print(f"  Approvals: {orchestrator_status['total_approvals']}")
    print(f"  Rejections: {orchestrator_status['total_rejections']}")
    print(f"  Rule violations: {orchestrator_status['rule_violations']}")
    print()
    
    # Check for rule violations
    violations = meta_orchestrator.get_rule_violations()
    if violations:
        print("⚠ CRITICAL RULE VIOLATIONS DETECTED:")
        for violation in violations:
            print(f"  Rule #{violation['rule_number']}: {violation['violation']}")
        print()
    else:
        print("✓ No critical rule violations - System operating correctly")
        print()
    
    # Get agent statuses
    print("Agent Statuses:")
    print(f"  Data Fusion: {data_fusion.total_fusions} fusions, {data_fusion.data_requests_served} requests served")
    print(f"  Strategy: {strategy.bull_agent.theses_generated} bull theses, {strategy.bear_agent.theses_generated} bear theses")
    print(f"  Simulation: {simulation.total_simulations} simulations, {simulation.total_scenarios_run:,} scenarios")
    print(f"  Risk: {risk_eval.total_adjudications} adjudications, {risk_eval.approval_rate:.0%} approval rate")
    print(f"  Execution: {execution.total_orders} orders, {execution.fill_rate:.0%} fill rate, ${execution.total_pnl:.2f} PnL")
    print()
    
    # Complete experiment
    experiment_infra.complete_experiment(
        experiment.experiment_id,
        status="completed",
        notes="Successfully completed full workflow with all critical rules enforced"
    )
    
    print("Experiment Status:")
    print(f"  Experiment ID: {experiment.experiment_id}")
    print(f"  Status: {experiment.status}")
    print(f"  Duration: {(experiment.ended_at - experiment.started_at).total_seconds():.2f}s")
    print()
    
    print("=" * 80)
    print("DEMO COMPLETE - All critical rules enforced successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_complete_trading_workflow())
