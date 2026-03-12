"""
Advanced AI Capability Registry
===============================

Catalog of advanced AI capabilities requested for the self-assembly
trading system.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class AdvancedAICapability:
    """Advanced capability available to the self-assembly AI."""

    capability_id: str
    name: str
    category: str
    description: str


# Requested capability set with duplicate entries normalized.
_DEFAULT_CAPABILITIES: Tuple[Tuple[str, str, str, str], ...] = (
    (
        "neural_architecture_search_strategy_evolution",
        "Neural Architecture Search (NAS) for Strategy Evolution",
        "strategy_evolution",
        "Search model architectures that adapt trading behavior to changing markets.",
    ),
    (
        "multi_armed_bandit_strategy_selection",
        "Multi-Armed Bandit for Strategy Selection",
        "strategy_evolution",
        "Allocate capital dynamically across strategies using exploration-exploitation.",
    ),
    (
        "meta_reinforcement_learning",
        "Meta-Reinforcement Learning",
        "strategy_evolution",
        "Learn policies that adapt faster across symbols and market regimes.",
    ),
    (
        "automated_feature_engineering",
        "Automated Feature Engineering",
        "strategy_evolution",
        "Generate and rank predictive signals from market and alternative data.",
    ),
    (
        "code_synthesis_natural_language",
        "Code Synthesis from Natural Language",
        "autonomous_engineering",
        "Translate high-level trading instructions into executable strategy code.",
    ),
    (
        "differential_programming_strategy_optimization",
        "Differential Programming for Strategy Optimization",
        "strategy_evolution",
        "Use differentiable objectives to optimize strategy parameters and rules.",
    ),
    (
        "self_modifying_neural_networks",
        "Self-Modifying Neural Networks",
        "advanced_computing",
        "Allow controlled structural changes to neural policies during training.",
    ),
    (
        "automated_code_refactoring",
        "Automated Code Refactoring",
        "autonomous_engineering",
        "Improve maintainability and runtime efficiency through safe refactors.",
    ),
    (
        "federated_self_improvement",
        "Federated Self-Improvement",
        "multi_agent_intelligence",
        "Share model updates across agents without centralizing sensitive data.",
    ),
    (
        "swarm_based_strategy_discovery",
        "Swarm-Based Strategy Discovery",
        "multi_agent_intelligence",
        "Discover strategies by coordinating multiple exploratory trading agents.",
    ),
    (
        "hierarchical_multi_agent_system",
        "Hierarchical Multi-Agent System",
        "multi_agent_intelligence",
        "Coordinate planner, executor, and risk agents with layered control.",
    ),
    (
        "adversarial_robustness_testing",
        "Adversarial Robustness Testing",
        "safety_and_risk",
        "Stress-test strategy behavior against adversarial and noisy inputs.",
    ),
    (
        "causal_inference_engine",
        "Causal Inference Engine",
        "reasoning_and_memory",
        "Estimate causal market drivers beyond pure correlation.",
    ),
    (
        "uncertainty_quantification",
        "Uncertainty Quantification",
        "safety_and_risk",
        "Measure forecast confidence and route uncertainty into position sizing.",
    ),
    (
        "formal_verification_trading_logic",
        "Formal Verification of Trading Logic",
        "safety_and_risk",
        "Validate strategy invariants and prove critical constraints hold.",
    ),
    (
        "working_memory_system",
        "Working Memory System",
        "reasoning_and_memory",
        "Retain short-horizon market context for sequential decisions.",
    ),
    (
        "attention_mechanisms_market_focus",
        "Attention Mechanisms for Market Focus",
        "reasoning_and_memory",
        "Focus model capacity on the highest-impact market signals.",
    ),
    (
        "reasoning_chain_visualization",
        "Reasoning Chain Visualization",
        "reasoning_and_memory",
        "Expose intermediate reasoning steps for debugging and auditability.",
    ),
    (
        "emotion_simulation_market_psychology",
        "Emotion Simulation for Market Psychology",
        "reasoning_and_memory",
        "Model fear/greed dynamics to capture crowd-driven market behavior.",
    ),
    (
        "knowledge_graph_construction",
        "Knowledge Graph Construction",
        "reasoning_and_memory",
        "Build entity and relation graphs across symbols, news, and events.",
    ),
    (
        "continual_learning_without_forgetting",
        "Continual Learning Without Forgetting",
        "strategy_evolution",
        "Update models online while preserving prior useful behaviors.",
    ),
    (
        "active_learning_data_efficiency",
        "Active Learning for Data Efficiency",
        "strategy_evolution",
        "Select highest-value samples to reduce labeling and training cost.",
    ),
    (
        "synthetic_data_generation",
        "Synthetic Data Generation",
        "simulation_and_data",
        "Create realistic market scenarios to augment sparse training data.",
    ),
    (
        "world_hivemind_model_learning",
        "World Hivemind Model Learning",
        "simulation_and_data",
        "Learn shared latent world models across coordinated trading agents.",
    ),
    (
        "digital_twin_trading_system",
        "Digital Twin of Trading System",
        "simulation_and_data",
        "Mirror live infrastructure and strategy behavior in a sandbox.",
    ),
    (
        "adversarial_market_simulator",
        "Adversarial Market Simulator",
        "simulation_and_data",
        "Generate hostile market conditions for resilience testing.",
    ),
    (
        "multi_fidelity_simulation",
        "Multi-Fidelity Simulation",
        "simulation_and_data",
        "Blend low and high fidelity simulations for faster research cycles.",
    ),
    (
        "predictive_maintenance_strategies",
        "Predictive Maintenance for Strategies",
        "infrastructure_and_ops",
        "Detect model drift and schedule retraining before failures.",
    ),
    (
        "anticipatory_risk_management",
        "Anticipatory Risk Management",
        "safety_and_risk",
        "Forecast and mitigate risk before exposure breaches occur.",
    ),
    (
        "market_regime_prediction",
        "Market Regime Prediction",
        "strategy_evolution",
        "Classify market regimes and switch strategy templates proactively.",
    ),
    (
        "causal_discovery_leading_indicators",
        "Causal Discovery for Leading Indicators",
        "strategy_evolution",
        "Identify causal leading signals for earlier entry and exit timing.",
    ),
    (
        "automated_dependency_management",
        "Automated Dependency Management",
        "autonomous_engineering",
        "Track, update, and validate package dependencies safely.",
    ),
    (
        "self_healing_infrastructure",
        "Self-Healing Infrastructure",
        "infrastructure_and_ops",
        "Detect infra faults and recover services with minimal downtime.",
    ),
    (
        "performance_profiling_optimization",
        "Performance Profiling and Optimization",
        "infrastructure_and_ops",
        "Continuously profile hot paths and optimize runtime bottlenecks.",
    ),
    (
        "automated_testing_generation",
        "Automated Testing Generation",
        "autonomous_engineering",
        "Generate regression and property tests for evolving modules.",
    ),
    (
        "quantum_inspired_optimization",
        "Quantum-Inspired Optimization",
        "advanced_computing",
        "Apply quantum-inspired heuristics to search large strategy spaces.",
    ),
    (
        "neuromorphic_computing_integration",
        "Neuromorphic Computing Integration",
        "advanced_computing",
        "Explore event-driven compute paths for low-latency inference.",
    ),
    (
        "blockchain_based_audit_trail",
        "Blockchain-Based Audit Trail",
        "privacy_and_audit",
        "Write immutable audit records for decisions and model changes.",
    ),
    (
        "homomorphic_encryption_privacy",
        "Homomorphic Encryption for Privacy",
        "privacy_and_audit",
        "Enable privacy-preserving computation on encrypted financial data.",
    ),
)


def get_default_advanced_ai_capabilities() -> List[AdvancedAICapability]:
    """Return default advanced AI capabilities."""

    return [
        AdvancedAICapability(
            capability_id=capability_id,
            name=name,
            category=category,
            description=description,
        )
        for capability_id, name, category, description in _DEFAULT_CAPABILITIES
    ]


def summarize_capabilities_by_category(
    capabilities: List[AdvancedAICapability],
) -> Dict[str, int]:
    """Summarize capabilities by category."""

    summary: Dict[str, int] = {}
    for capability in capabilities:
        summary[capability.category] = summary.get(capability.category, 0) + 1
    return dict(sorted(summary.items(), key=lambda item: item[0]))
