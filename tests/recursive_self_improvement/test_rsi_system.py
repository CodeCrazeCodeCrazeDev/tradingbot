import pytest
import asyncio
import shutil
import os
from trading_bot.recursive_self_improvement.memory import ImprovementMemory
from trading_bot.recursive_self_improvement.evaluation import EvaluationEngine
from trading_bot.recursive_self_improvement.experiment_manager import ExperimentManager
from trading_bot.recursive_self_improvement.rollback import RollbackManager
from trading_bot.recursive_self_improvement.engine import RecursiveSelfImprovementEngine
from trading_bot.recursive_self_improvement.loops.specialized_loops import (
    StrategyImprovementLoop,
    ModelImprovementLoop,
    AgentImprovementLoop,
    WorkflowImprovementLoop,
    FeatureImprovementLoop,
    DataImprovementLoop,
    ResearchImprovementLoop,
    PromptImprovementLoop,
    ResourceImprovementLoop
)
from trading_bot.recursive_self_improvement.meta_optimizer import ImprovementOptimizer
from trading_bot.recursive_self_improvement.governance_bridge import RSIGovernanceBridge
from trading_bot.core_agent_system.governance_system import GovernanceSystem

@pytest.fixture
def rsi_setup():
    test_dir = "test_rsi_pytest"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)

    memory = ImprovementMemory(db_path=f"{test_dir}/memory.db")
    evaluation = EvaluationEngine()
    exp_manager = ExperimentManager(memory, evaluation)
    rollback = RollbackManager(base_path=f"{test_dir}/backups/")
    gov_sys = GovernanceSystem()
    gov_bridge = RSIGovernanceBridge(gov_sys)

    optimizer = ImprovementOptimizer(memory)
    engine = RecursiveSelfImprovementEngine(memory, evaluation, exp_manager, rollback, optimizer=optimizer, governance=gov_bridge)

    yield engine, memory, evaluation, exp_manager, rollback, gov_bridge, optimizer

    shutil.rmtree(test_dir)

@pytest.mark.asyncio
async def test_full_improvement_cycle(rsi_setup):
    engine, memory, evaluation, exp_manager, rollback, gov_bridge, optimizer = rsi_setup

    # Register all loops
    engine.register_loop(StrategyImprovementLoop(engine))
    engine.register_loop(ModelImprovementLoop(engine))
    engine.register_loop(AgentImprovementLoop(engine))
    engine.register_loop(WorkflowImprovementLoop(engine))
    engine.register_loop(FeatureImprovementLoop(engine))
    engine.register_loop(DataImprovementLoop(engine))
    engine.register_loop(ResearchImprovementLoop(engine))
    engine.register_loop(PromptImprovementLoop(engine))
    engine.register_loop(ResourceImprovementLoop(engine))

    # Run full engine cycle
    engine.running = True
    # Manually run the inner loop once instead of starting background task
    meta_hypo = await engine.optimizer.generate_meta_hypothesis()
    assert "Meta-Hypothesis" in meta_hypo

    for loop in engine.loops:
        await loop.run_cycle()

    # Verify experiments were recorded
    experiments = memory.get_recent_experiments()
    assert len(experiments) >= 9
    domains = [e["domain"] for e in experiments]
    assert "strategy" in domains
    assert "resource" in domains

    # Verify deployment occurred (mock simulation returns improvement)
    deployments = []
    import sqlite3
    with sqlite3.connect(memory.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deployments")
        deployments = [dict(row) for row in cursor.fetchall()]

    assert len(deployments) > 0
    assert deployments[0]["domain"] == "strategy"

@pytest.mark.asyncio
async def test_meta_optimizer_learning(rsi_setup):
    engine, memory, evaluation, exp_manager, rollback, gov_bridge, optimizer = rsi_setup

    # Pre-populate some history
    memory.record_experiment("exp-1", "strategy", "Hypo 1", {}, None)
    memory.update_experiment_result("exp-1", "completed", 1.5, {"sharpe": 2.0})

    memory.record_experiment("exp-2", "model", "Hypo 2", {}, None)
    memory.update_experiment_result("exp-2", "failed", -0.5, {"sharpe": 0.5})

    report = await optimizer.analyze_meta_performance()
    assert "strategy" in report
    assert report["strategy"]["success_rate"] == 1.0
    assert report["model"]["success_rate"] == 0.0

    hypo = await optimizer.generate_meta_hypothesis()
    assert "Meta-Hypothesis" in hypo
    assert "model" in hypo # Should target the weakest domain
