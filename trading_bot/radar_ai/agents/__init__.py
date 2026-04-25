"""
RadarAI Agent System - Palantir-Inspired Multi-Agent Architecture
==================================================================

Agent hierarchy with critical rules enforcement:

1. Meta-Orchestrator Agent - Master controller
2. Data Fusion Agent - Perception layer
3. Ontology Agent - Knowledge graph
4. Intelligence Agent - LLM reasoning
5. Strategy/Research Agent - Bull/Bear thesis
6. Simulation Agent - World-model simulator
7. Risk & Evaluation Agent - VaR, drawdown checks
8. Execution Agent - LAST step only

CRITICAL RULES (System Fails if Violated):
1. Agents NEVER access raw data directly
2. No agent can execute without orchestrator approval
3. All experiments must be logged
4. Simulation happens BEFORE execution
5. Execution is the LAST step, not the first
"""

from .meta_orchestrator import MetaOrchestrator
from .data_fusion_agent import DataFusionAgent
from .ontology_agent import OntologyAgent
from .intelligence_agent import IntelligenceAgent
from .strategy_agent import StrategyAgent, BullAgent, BearAgent
from .simulation_agent import SimulationAgent
from .risk_evaluation_agent import RiskEvaluationAgent
from .execution_agent import ExecutionAgent
from .experiment_infrastructure import ExperimentInfrastructure

__all__ = [
    'MetaOrchestrator',
    'DataFusionAgent',
    'OntologyAgent',
    'IntelligenceAgent',
    'StrategyAgent',
    'BullAgent',
    'BearAgent',
    'SimulationAgent',
    'RiskEvaluationAgent',
    'ExecutionAgent',
    'ExperimentInfrastructure',
]
