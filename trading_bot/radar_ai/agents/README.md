# RadarAI Agent System - Palantir-Inspired Multi-Agent Architecture

## Overview

The RadarAI Agent System is a Palantir-inspired multi-agent architecture for autonomous financial intelligence. It implements a strict workflow with critical rules enforcement to ensure safe, auditable, and effective trading decisions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        META-ORCHESTRATOR                                │
│                    (Command Brain - Rules Enforcer)                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ Data Fusion   │────────▶│   Ontology    │────────▶│ Intelligence  │
│     Agent     │         │     Agent     │         │     Agent     │
│ (Perception)  │         │ (Knowledge    │         │ (LLM          │
│               │         │  Graph)       │         │  Reasoning)   │
└───────────────┘         └───────────────┘         └───────────────┘
        │                                                     │
        │                                                     │
        ▼                                                     ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│   Strategy    │────────▶│  Simulation   │────────▶│ Risk & Eval   │
│     Agent     │         │     Agent     │         │     Agent     │
│ (Bull/Bear)   │         │ (10k          │         │ (VaR,         │
│               │         │  Scenarios)   │         │  Drawdown)    │
└───────────────┘         └───────────────┘         └───────────────┘
                                    │
                                    │
                                    ▼
                          ┌───────────────┐
                          │  Execution    │
                          │     Agent     │
                          │ (LAST STEP)   │
                          └───────────────┘
                                    │
                                    ▼
                          ┌───────────────┐
                          │  Experiment   │
                          │Infrastructure │
                          │  (Logging)    │
                          └───────────────┘
```

## Critical Rules (System Fails if Violated)

### Rule 1: Agents NEVER Access Raw Data Directly
**Only** the Data Fusion Agent can access raw market data. All other agents must request data through the Data Fusion Agent.

**Enforcement**: `CriticalRulesEnforcer.check_rule_1_no_direct_data_access()`

### Rule 2: No Agent Can Execute Without Orchestrator Approval
All critical actions (especially execution) require explicit approval from the Meta-Orchestrator.

**Enforcement**: `CriticalRulesEnforcer.check_rule_2_orchestrator_approval()`

### Rule 3: All Experiments Must Be Logged
Every experiment, simulation, and test must be logged in the Experiment Infrastructure.

**Enforcement**: `CriticalRulesEnforcer.check_rule_3_experiment_logging()`

### Rule 4: Simulation Happens BEFORE Execution
The Simulation Agent must complete 10,000+ scenario runs before execution is allowed.

**Enforcement**: `CriticalRulesEnforcer.check_rule_4_simulation_before_execution()`

### Rule 5: Execution is the LAST Step, Not the First
Execution can only happen after all prior stages complete: Data Fusion → Ontology → Intelligence → Strategy → Simulation → Risk Evaluation → **Execution**

**Enforcement**: `CriticalRulesEnforcer.check_rule_5_execution_is_last()`

## Workflow Stages

The system enforces a strict sequential workflow:

1. **DATA_FUSION** - Perception layer fuses all data sources
2. **ONTOLOGY_UPDATE** - Knowledge graph enrichment
3. **INTELLIGENCE** - LLM reasoning and narrative generation
4. **STRATEGY_RESEARCH** - Bull vs Bear wargame analysis
5. **SIMULATION** - 10,000+ forward scenario simulations (REQUIRED)
6. **RISK_EVALUATION** - VaR, drawdown, correlation checks
7. **EXECUTION** - Order management (LAST STEP)

## Agent Descriptions

### Meta-Orchestrator
**Role**: Command brain that coordinates all agents and enforces critical rules.

**Responsibilities**:
- Register and manage all agents
- Approve/reject agent requests
- Manage workflow stages
- Enforce critical rules
- Track violations

**Key Methods**:
- `submit_request()` - Submit agent request for approval
- `approve_request()` - Approve pending request
- `start_workflow()` - Start new workflow
- `advance_workflow_stage()` - Move to next stage

### Data Fusion Agent
**Role**: Perception layer - the ONLY agent allowed to access raw data.

**Responsibilities**:
- Fuse market feeds, news, sentiment, alternative data
- Create unified market picture
- Serve data to other agents
- Assess data quality

**Key Methods**:
- `fuse_market_data()` - Fuse all data sources
- `get_market_picture()` - Provide data to requesting agent

### Ontology Agent
**Role**: Knowledge graph manager.

**Responsibilities**:
- Entity resolution
- Relationship mapping
- Real-time enrichment
- Semantic graph updates

**Key Methods**:
- `enrich_from_market_picture()` - Enrich ontology with market data
- `query_relationships()` - Query entity relationships

### Intelligence Agent
**Role**: LLM reasoning layer for human-readable explanations.

**Responsibilities**:
- Generate trade narratives
- Create risk briefs
- Explain decisions
- Provide audit trail

**Key Methods**:
- `generate_trade_narrative()` - Create comprehensive trade narrative
- `generate_risk_brief()` - Generate risk assessment brief
- `explain_decision()` - Explain decision in human terms

### Strategy Agent
**Role**: Bull vs Bear wargame coordinator.

**Sub-Agents**:
- **BullAgent** - Finds entry opportunities
- **BearAgent** - Finds invalidation cases

**Responsibilities**:
- Run competing analyses
- Generate opposing theses
- Synthesize recommendations
- Wargame outputs

**Key Methods**:
- `analyze_opportunity()` - Run Bull vs Bear analysis

### Simulation Agent
**Role**: World-model simulator running 10,000+ scenarios.

**Responsibilities**:
- Monte Carlo simulations
- Scenario analysis
- Calculate expected outcomes
- Determine simulation verdict

**Key Methods**:
- `run_world_model_simulation()` - Run 10k+ scenarios

**Output Metrics**:
- Expected PnL
- Probability of profit
- VaR (95%)
- Expected max drawdown
- Simulation verdict (favorable/neutral/unfavorable)

### Risk & Evaluation Agent
**Role**: Risk adjudicator - final gatekeeper before execution.

**Responsibilities**:
- VaR calculations
- Drawdown analysis
- Correlation checks
- Liquidity assessment
- Position sizing

**Key Methods**:
- `adjudicate_risk()` - Comprehensive risk assessment

**Risk Limits**:
- Max VaR (95%): 3.0%
- Max Drawdown: 15.0%
- Max Concentration: 25.0%
- Max Correlation: 0.85
- Min Liquidity: 5 days

### Execution Agent
**Role**: Order management - THE LAST STEP.

**Responsibilities**:
- Order submission
- Position tracking
- Performance attribution
- Outcome feedback loop
- Retraining signals

**Key Methods**:
- `execute_trade()` - Execute trade (requires full workflow completion)
- `close_position()` - Close position and record outcome
- `get_retraining_signals()` - Get outcomes requiring retraining

### Experiment Infrastructure
**Role**: Logging, versioning, and reproducibility.

**Responsibilities**:
- Experiment tracking
- Metrics logging
- Artifact storage
- Version control
- Audit trail

**Key Methods**:
- `create_experiment()` - Create new experiment
- `log_metric()` - Log metric
- `log_artifact()` - Save artifact
- `complete_experiment()` - Mark experiment complete

## Quick Start

```python
import asyncio
from trading_bot.radar_ai.agents import (
    MetaOrchestrator,
    DataFusionAgent,
    OntologyAgent,
    IntelligenceAgent,
    StrategyAgent,
    SimulationAgent,
    RiskEvaluationAgent,
    ExecutionAgent,
    ExperimentInfrastructure,
)
from trading_bot.radar_ai import FinancialOntology

async def main():
    # Initialize orchestrator
    orchestrator = MetaOrchestrator()
    
    # Initialize experiment infrastructure
    experiment_infra = ExperimentInfrastructure()
    experiment = experiment_infra.create_experiment(
        name="My Trading Strategy",
        description="Test strategy with full workflow"
    )
    
    # Initialize ontology
    ontology = FinancialOntology()
    
    # Initialize all agents
    data_fusion = DataFusionAgent(orchestrator)
    ontology_agent = OntologyAgent(orchestrator, ontology)
    intelligence = IntelligenceAgent(orchestrator)
    strategy = StrategyAgent(orchestrator)
    simulation = SimulationAgent(orchestrator)
    risk_eval = RiskEvaluationAgent(orchestrator)
    execution = ExecutionAgent(orchestrator)
    
    # Start workflow
    workflow = await orchestrator.start_workflow()
    
    # Stage 1: Data Fusion
    market_picture = await data_fusion.fuse_market_data()
    await orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'market_picture': market_picture.to_dict()}
    )
    
    # Stage 2: Ontology Update
    enrichment = await ontology_agent.enrich_from_market_picture(
        market_picture.to_dict()
    )
    await orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'enrichment': enrichment}
    )
    
    # Stage 3: Intelligence (skip for now)
    await orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'intelligence': 'ready'}
    )
    
    # Stage 4: Strategy Research
    strategy_analysis = await strategy.analyze_opportunity(
        symbol="AAPL",
        market_picture=market_picture.to_dict(),
        ontology_data={}
    )
    await orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'strategy': strategy_analysis}
    )
    
    # Stage 5: Simulation (REQUIRED)
    simulation_result = await simulation.run_world_model_simulation(
        strategy_analysis=strategy_analysis,
        market_picture=market_picture.to_dict(),
        num_scenarios=10000,
        experiment_id=experiment.experiment_id,
    )
    workflow.is_simulation_complete = True
    await orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'simulation': simulation_result.to_dict()}
    )
    
    # Stage 6: Risk Evaluation
    portfolio = {'total_value': 100000, 'positions': []}
    risk_adjudication = await risk_eval.adjudicate_risk(
        strategy_analysis=strategy_analysis,
        simulation_result=simulation_result.to_dict(),
        portfolio=portfolio,
        market_picture=market_picture.to_dict(),
    )
    await orchestrator.advance_workflow_stage(
        workflow.execution_id,
        {'risk': risk_adjudication.to_dict()}
    )
    
    # Stage 7: Execution (LAST STEP)
    execution_result = await execution.execute_trade(
        workflow_id=workflow.execution_id,
        strategy_analysis=strategy_analysis,
        simulation_result=simulation_result.to_dict(),
        risk_adjudication=risk_adjudication.to_dict(),
    )
    
    print(f"Execution result: {execution_result['status']}")
    
    # Check for violations
    violations = orchestrator.get_rule_violations()
    if violations:
        print(f"⚠ Rule violations detected: {len(violations)}")
    else:
        print("✓ No rule violations - System operating correctly")

if __name__ == "__main__":
    asyncio.run(main())
```

## Running the Demo

```bash
cd trading_bot/radar_ai/agents
python AGENT_SYSTEM_DEMO.py
```

The demo will:
1. Initialize all agents
2. Run complete workflow through all 7 stages
3. Enforce all 5 critical rules
4. Generate trade narrative and risk brief
5. Execute trade (if approved)
6. Log everything to experiment infrastructure
7. Report any rule violations

## Key Features

### 1. Strict Rule Enforcement
All critical rules are enforced at runtime. Violations are logged and can block execution.

### 2. Complete Audit Trail
Every action, decision, and outcome is logged for full traceability.

### 3. Simulation-First Approach
10,000+ scenario simulations run before any execution, providing statistical confidence.

### 4. Multi-Agent Consensus
Bull and Bear agents provide competing analyses, reducing bias.

### 5. Human-Readable Explanations
Intelligence Agent generates narratives explaining WHY decisions are made.

### 6. Risk-Aware Execution
Comprehensive risk checks (VaR, drawdown, correlation, liquidity) before execution.

### 7. Feedback Loop
Execution outcomes feed back for model retraining and improvement.

## Palantir Mapping

| Palantir Component | RadarAI Equivalent |
|-------------------|-------------------|
| Foundry | Data Fusion Agent |
| Ontology | Ontology Agent + FinancialOntology |
| AIP (AI Platform) | Intelligence Agent + Strategy Agent |
| Apollo | Meta-Orchestrator |
| Agent Studio | Strategy Agent (Bull/Bear sub-agents) |
| AIP Logic | Meta-Orchestrator (workflow rules) |
| AIP Evals | Risk & Evaluation Agent |
| AIP Automate | Execution Agent |

## Safety Features

1. **No Direct Data Access** - Only Data Fusion Agent touches raw data
2. **Orchestrator Approval** - All critical actions require approval
3. **Mandatory Logging** - All experiments logged automatically
4. **Simulation Required** - Cannot execute without simulation
5. **Sequential Workflow** - Execution only after all stages complete
6. **Risk Limits** - Hard limits on VaR, drawdown, concentration
7. **Violation Tracking** - All rule violations logged and reported

## Version

1.0.0 - Initial Palantir-inspired multi-agent architecture

## License

Proprietary - RadarAI Financial Intelligence System
