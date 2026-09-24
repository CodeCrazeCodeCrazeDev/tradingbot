from superintelligence.self_optimizing_core import SelfOptimizingCore
from superintelligence.superintelligence_orchestrator import SuperintelligenceOrchestrator


def test_optimizer_promotes_positive_experiment_and_evolves_architecture():
    core = SelfOptimizingCore()
    result = core.optimize_system(
        {
            "experiment_name": "new-allocator",
            "baseline_metric": 1.0,
            "candidate_metric": 1.2,
        }
    )

    assert result["architecture_changed"] is True
    assert core.current_architecture["meta_controller"] == "hierarchical-self-play"


def test_orchestrator_spawns_agents_and_expands_domains():
    orchestrator = SuperintelligenceOrchestrator({"opportunity_threshold": 0.5})
    output = orchestrator.process(
        {
            "compute_budget": 120,
            "opportunity_signals": [
                {
                    "domain": "synthetic_biology_markets",
                    "thesis": "Cross-border demand inflection",
                    "score": 0.9,
                    "suggested_agents": ["market-scout", "bioecon-lab"],
                }
            ],
            "baseline_metric": 0.9,
            "candidate_metric": 1.1,
        }
    )

    active_agents = output["coordination"]["active_agents"]
    domains = output["coordination"]["research_domains"]
    deployments = output["infrastructure"].agent_deployments

    assert "bioecon-lab" in active_agents
    assert "synthetic_biology_markets" in domains
    assert any(d["domain"] == "synthetic_biology_markets" for d in deployments)
