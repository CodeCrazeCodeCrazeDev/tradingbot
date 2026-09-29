"""
AlphaAlgo Trading System - Unified AI Brain Architecture

This package integrates ALL 2900+ files into ONE coherent AI system.

"Many modules, ONE mind. Many features, ONE purpose. Many files, ONE AI."

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED AI BRAIN                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CONSCIOUSNESS LAYER                               │   │
│  │  • Decision Making  • Learning  • Self-Improvement  • Memory        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    COGNITIVE LAYER                                   │   │
│  │  • Pattern Recognition  • Reasoning  • Prediction  • Analysis       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    OPERATIONAL LAYER                                 │   │
│  │  • Data Ingestion  • Signal Generation  • Execution  • Risk         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SAFETY LAYER (IMMUTABLE)                          │   │
│  │  • Risk Limits  • Circuit Breakers  • Human Override  • Fail-Safe   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

QUICK START:
    from trading_bot import UnifiedAIBrain, BrainConfig

    brain = UnifiedAIBrain(BrainConfig(mode="paper"))
    await brain.awaken()
    thought = await brain.think("BTCUSDT", market_data)
    await brain.run()

IMMUTABLE PRINCIPLES:
1. RISK FIRST: Safety layer has VETO power over all decisions
2. HUMAN CONTROL: Human override ALWAYS works
3. FAIL-SAFE: Default to NO TRADE when uncertain
4. SURVIVAL: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."

"""

import importlib as _importlib
import logging
import sys

# ── Lazy export surface (PEP 562) ────────────────────────────────────────────
# Every public name maps to (submodule, attribute). Nothing imports at package
# init: the old eager chain dragged sklearn/aiohttp/pandas into *every*
# ``import trading_bot`` (~60s on this box). First attribute access pays the
# cost for just the names actually used.

_LAZY = {
    # Infrastructure & orchestration
    "SystemOrchestrator": (".infrastructure.orchestration", "SystemOrchestrator"),
    "ConfigManager": (".infrastructure.config", "InfrastructureConfigManager"),
    "setup_logging": (".reporting.logger", "init_logger"),
    "MasterOrchestrator": (".orchestration", "MasterOrchestrator"),
    "OrchestratorConfig": (".orchestration", "OrchestratorConfig"),
    "get_orchestrator": (".orchestration", "get_orchestrator"),
    "initialize_orchestrator": (".orchestration", "initialize_orchestrator"),
    "ModuleRegistry": (".registry", "ModuleRegistry"),
    "get_registry": (".registry", "get_registry"),
    "initialize_registry": (".registry", "initialize_registry"),
    "BaseEvent": (".events", "BaseEvent"),
    "MarketEvent": (".events", "MarketEvent"),
    "PriceUpdateEvent": (".events", "PriceUpdateEvent"),
    "SignalEvent": (".events", "SignalEvent"),
    "OrderEvent": (".events", "OrderEvent"),
    "EventHandler": (".events", "EventHandler"),
    "VERSION_STRING": (".constants", "VERSION_STRING"),
    "DEFAULT_RISK_PERCENTAGE": (".constants", "DEFAULT_RISK_PERCENTAGE"),
    "MAX_DRAWDOWN_PERCENTAGE": (".constants", "MAX_DRAWDOWN_PERCENTAGE"),
    "DEFAULT_STOP_LOSS_PIPS": (".constants", "DEFAULT_STOP_LOSS_PIPS"),
    "DEFAULT_TAKE_PROFIT_PIPS": (".constants", "DEFAULT_TAKE_PROFIT_PIPS"),
    # Unified AI Brain
    "UnifiedAIBrain": (".unified_ai_brain", "UnifiedAIBrain"),
    "BrainConfig": (".unified_ai_brain", "BrainConfig"),
    "BrainState": (".unified_ai_brain", "BrainState"),
    "BrainStatus": (".unified_ai_brain", "BrainStatus"),
    "Thought": (".unified_ai_brain", "Thought"),
    "Memory": (".unified_ai_brain", "Memory"),
    "DecisionType": (".unified_ai_brain", "DecisionType"),
    "ConfidenceLevel": (".unified_ai_brain", "ConfidenceLevel"),
    "SubsystemCategory": (".unified_ai_brain", "SubsystemCategory"),
    "create_brain": (".unified_ai_brain", "create_brain"),
    "quick_start": (".unified_ai_brain", "quick_start"),
    "SUBSYSTEM_REGISTRY": (".unified_ai_brain", "SUBSYSTEM_REGISTRY"),
    # Integration layer
    "MasterIntegrationEngine": (".integration", "MasterIntegrationEngine"),
    "EngineConfig": (".integration", "EngineConfig"),
    "EngineState": (".integration", "EngineState"),
    "get_engine": (".integration", "get_engine"),
    "reset_engine": (".integration", "reset_engine"),
    "VerificationPipeline": (".integration", "VerificationPipeline"),
    "get_module_registry": (".integration", "get_module_registry"),
    "MasterIntegrator": (".integration", "MasterIntegrator"),
    "IntegrationPhase": (".integration", "IntegrationPhase"),
    "get_master_integrator": (".integration", "get_master_integrator"),
    # Meta-governance
    "MetaAgentGovernanceLayer": (".meta_governance", "MetaAgentGovernanceLayer"),
    "AgentType": (".meta_governance", "AgentType"),
    "ChangeCategory": (".meta_governance", "ChangeCategory"),
    "ChangeType": (".meta_governance", "ChangeType"),
    "UnderperformanceType": (".meta_governance", "UnderperformanceType"),
    "AgentPerformance": (".meta_governance", "AgentPerformance"),
    "ForbiddenChangeAttempt": (".meta_governance", "ForbiddenChangeAttempt"),
    "CandidateUpgrade": (".meta_governance", "CandidateUpgrade"),
    "ValidationCriteria": (".meta_governance", "ValidationCriteria"),
    "ValidationResult": (".meta_governance", "ValidationResult"),
    "create_meta_agent_governance_layer": (".meta_governance", "create_meta_agent_governance_layer"),
    # Golden path
    "AccountContext": (".golden_path", "AccountContext"),
    "AgentTrapDefenseConfig": (".golden_path", "AgentTrapDefenseConfig"),
    "AgentTrapScanner": (".golden_path", "AgentTrapScanner"),
    "DecisionGateConfig": (".golden_path", "DecisionGateConfig"),
    "GoldenPathTradingRunner": (".golden_path", "GoldenPathTradingRunner"),
    "MarketContext": (".golden_path", "MarketContext"),
    "ModelPerformanceMonitor": (".golden_path", "ModelPerformanceMonitor"),
    "ModelVote": (".golden_path", "ModelVote"),
    "PredictionSample": (".golden_path", "PredictionSample"),
    "RiskContext": (".golden_path", "RiskContext"),
    "TradeDecision": (".golden_path", "TradeDecision"),
    "TradeDecisionValidator": (".golden_path", "TradeDecisionValidator"),
    "TradeIntent": (".golden_path", "TradeIntent"),
    "TradingMode": (".golden_path", "TradingMode"),
    "TrapCategory": (".golden_path", "TrapCategory"),
    "audit_local_secrets": (".golden_path", "audit_local_secrets"),
    # AEAN meta-intelligence
    "AEANConstraints": (".aean_meta_intelligence_layer", "AEANConstraints"),
    "AEANMetaIntelligenceLayer": (".aean_meta_intelligence_layer", "AEANMetaIntelligenceLayer"),
    "AEANBenchmarkResult": (".aean_meta_intelligence_layer", "BenchmarkResult"),
    "AEANBenchmarkTask": (".aean_meta_intelligence_layer", "BenchmarkTask"),
    "AEANCapabilityCandidate": (".aean_meta_intelligence_layer", "CapabilityCandidate"),
    "AEANDeploymentDecision": (".aean_meta_intelligence_layer", "DeploymentDecision"),
    "FrontierObservation": (".aean_meta_intelligence_layer", "FrontierObservation"),
    "AEANMonitoringResult": (".aean_meta_intelligence_layer", "MonitoringResult"),
    "AEANValidationResult": (".aean_meta_intelligence_layer", "ValidationResult"),
    "create_aean_meta_intelligence_layer": (".aean_meta_intelligence_layer", "create_aean_meta_intelligence_layer"),
    # Universal Action Layer
    "ActionIntent": (".universal_action_layer", "ActionIntent"),
    "ActionPolicy": (".universal_action_layer", "ActionPolicy"),
    "ActionResult": (".universal_action_layer", "ActionResult"),
    "ActionRiskTier": (".universal_action_layer", "ActionRiskTier"),
    "ActionStatus": (".universal_action_layer", "ActionStatus"),
    "ActionType": (".universal_action_layer", "ActionType"),
    "CommandActionAdapter": (".universal_action_layer", "CommandActionAdapter"),
    "DecisionBundle": (".universal_action_layer", "DecisionBundle"),
    "DecisionConstraints": (".universal_action_layer", "DecisionConstraints"),
    "ExecutionStatus": (".universal_action_layer", "ExecutionStatus"),
    "FeedbackReport": (".universal_action_layer", "FeedbackReport"),
    "FunctionActionAdapter": (".universal_action_layer", "FunctionActionAdapter"),
    "GovernanceSignature": (".universal_action_layer", "GovernanceSignature"),
    "GovernanceReceipt": (".universal_action_layer", "GovernanceReceipt"),
    "UniversalActionLayer": (".universal_action_layer", "UniversalActionLayer"),
    "WorkflowActionAdapter": (".universal_action_layer", "WorkflowActionAdapter"),
    "sign_decision_bundle": (".universal_action_layer", "sign_decision_bundle"),
    "create_universal_action_layer": (".universal_action_layer", "create_universal_action_layer"),
}

# Names that previously None-shimmed when their layer was absent
# (unified_ai_brain / integration / meta_governance / golden_path / aean /
# universal_action_layer except-blocks all assigned None on failure).
_OPTIONAL_PREFIXES = (
    ".unified_ai_brain", ".integration", ".meta_governance",
    ".golden_path", ".aean_meta_intelligence_layer", ".universal_action_layer",
)


def _unavailable(what):
    def _raiser(*args, **kwargs):
        raise RuntimeError(f"{what} not available")
    return _raiser


def __getattr__(name):
    entry = _LAZY.get(name)
    if entry is None:
        if name == "integrate_all_modules":
            return _integrate_all_modules
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod, attr = entry
    try:
        return getattr(_importlib.import_module(mod, __name__), attr)
    except Exception as e:
        if mod in _OPTIONAL_PREFIXES:
            logging.getLogger(__name__).info(f"{mod} layer not available: {e}")
            return None
        # infrastructure/orchestration helpers: preserve old raising-stub semantics
        if name in ("get_orchestrator", "initialize_orchestrator",
                    "get_registry", "initialize_registry"):
            return _unavailable(name)
        raise


async def _integrate_all_modules(config=None):
    """Integrate trading_bot modules using the professional integration engine."""
    raw_config = config or {}
    integration = _importlib.import_module(".integration", __name__)
    engine_config = integration.EngineConfig(
        health_check_interval_s=raw_config.get('health_check_interval_s', 30.0),
        health_check_timeout_s=raw_config.get('health_check_timeout_s', 5.0),
        fail_fast_on_tier_a=raw_config.get('fail_fast_on_tier_a', True),
        max_start_retries=raw_config.get('max_start_retries', 2),
        retry_delay_s=raw_config.get('retry_delay_s', 2.0),
        block_direct_impact_without_risk=raw_config.get('block_direct_impact_without_risk', True),
        state_file=raw_config.get('state_file', 'alphaalgo_data/engine_state.json'),
        startup_wave_order=raw_config.get('startup_wave_order', [0, 1, 4, 5, 2, 3, 6, 7]),
    )
    integration.reset_engine()
    engine = integration.get_engine(config=engine_config)
    module_limit = raw_config.get('module_limit')
    bootstrap_summary = await engine.bootstrap_hierarchical(max_modules=module_limit)
    if raw_config.get('run_verification', False):
        verifier = integration.VerificationPipeline()
        verification_report = await verifier.run_full_verification(engine)
        return {'engine': engine, 'bootstrap': bootstrap_summary,
                'verification': verification_report}
    return {'engine': engine, 'bootstrap': bootstrap_summary}


# Global counter to track legacy dynamic redirector usage
_redirector_usage_counts = {}

# Enable backward-compatible dynamic imports for utility submodules with explicit warnings
class UtilityImportRedirector:
    def __init__(self, package_name, submodules, target_package):
        self.package_name = package_name
        self.submodules = submodules
        self.target_package = target_package

    def find_spec(self, fullname, path, target=None):
        if fullname.startswith(self.package_name + "."):
            sub = fullname[len(self.package_name) + 1:]
            if sub in self.submodules:
                target_fullname = f"{self.target_package}.{sub}"
                try:
                    import importlib
                    import warnings
                    _redirector_usage_counts[fullname] = _redirector_usage_counts.get(fullname, 0) + 1
                    warnings.warn(
                        f"Legacy import path '{fullname}' is deprecated. Please migrate to '{target_fullname}'.",
                        DeprecationWarning,
                        stacklevel=2
                    )
                    logging.getLogger(__name__).warning(
                        f"MIGRATION METRICS: Deprecated import '{fullname}' redirected to '{target_fullname}'. Usage count: {_redirector_usage_counts[fullname]}"
                    )
                    mod = importlib.import_module(target_fullname)
                    sys.modules[fullname] = mod
                    return mod.__spec__
                except Exception:
                    pass
        return None

utils_submodules = [
    "api_cache", "api_rate_limiter", "bounded_collections", "candle_tracker",
    "data_manager", "data_validator", "debug_tools", "logger", "profiler",
    "rate_limiter", "retry_policy", "risk_controller", "risk_management",
    "safe_access", "safe_write", "validation"
]
sys.meta_path.append(UtilityImportRedirector("trading_bot", utils_submodules, "trading_bot.utils"))


class ModuleMapRedirector:
    """Redirects flat ``trading_bot.X`` imports to their consolidated
    subpackage homes for modules relocated by merges."""

    def __init__(self, package_name, redirects):
        self.package_name = package_name
        self.redirects = redirects  # flat name -> fully-qualified target

    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith(self.package_name + "."):
            return None
        sub = fullname[len(self.package_name) + 1:]
        target_fullname = self.redirects.get(sub)
        if not target_fullname:
            return None
        try:
            import importlib
            import warnings
            _redirector_usage_counts[fullname] = _redirector_usage_counts.get(fullname, 0) + 1
            warnings.warn(
                f"Legacy import path '{fullname}' is deprecated. Please migrate to '{target_fullname}'.",
                DeprecationWarning,
                stacklevel=2
            )
            logging.getLogger(__name__).warning(
                f"MIGRATION METRICS: Deprecated import '{fullname}' redirected to '{target_fullname}'. Usage count: {_redirector_usage_counts[fullname]}"
            )
            mod = importlib.import_module(target_fullname)
            sys.modules[fullname] = mod
            return mod.__spec__
        except Exception:
            return None


_consolidated_modules = {
    "backup": "trading_bot.tools.backup",
    "core_engine": "trading_bot.ultimate_production.core_engine",
    "live_monitor": "trading_bot.ultimate_production.live_monitor",
    "ml_prediction_engine": "trading_bot.ultimate_production.ml_prediction_engine",
    "risk_fortress": "trading_bot.ultimate_production.risk_fortress",
    "self_learner": "trading_bot.ultimate_production.self_learner",
    "smart_executor": "trading_bot.ultimate_production.smart_executor",
    "strategy_ensemble": "trading_bot.ultimate_production.strategy_ensemble",
    "circuit_breaker": "trading_bot.core.circuit_breaker",
    "fail_safe": "trading_bot.safety.fail_safe",
    "trade_validator": "trading_bot.validation.trade_validator",
    "ensemble": "trading_bot.alpha_engine.ensemble",
    "chainofthoughtreasoner": "trading_bot.core.chainofthoughtreasoner",
}
sys.meta_path.append(ModuleMapRedirector("trading_bot", _consolidated_modules))

__all__ = [
    # Unified AI Brain (PRIMARY)
    'UnifiedAIBrain', 'BrainConfig', 'BrainState', 'BrainStatus', 'Thought',
    'Memory', 'DecisionType', 'ConfidenceLevel', 'SubsystemCategory',
    'create_brain', 'quick_start', 'SUBSYSTEM_REGISTRY',
    # Module integration
    'MasterIntegrationEngine', 'EngineConfig', 'EngineState', 'get_engine',
    'reset_engine', 'VerificationPipeline', 'MasterIntegrator',
    'IntegrationPhase', 'get_master_integrator', 'integrate_all_modules',
    # Unified Orchestration System
    'MasterOrchestrator', 'OrchestratorConfig', 'get_orchestrator',
    'initialize_orchestrator', 'ModuleRegistry', 'get_registry',
    'initialize_registry',
    'BaseEvent', 'MarketEvent', 'PriceUpdateEvent', 'SignalEvent',
    'OrderEvent', 'EventHandler',
    # Legacy orchestration
    'SystemOrchestrator', 'ConfigManager', 'setup_logging',
    'VERSION_STRING', 'DEFAULT_RISK_PERCENTAGE', 'MAX_DRAWDOWN_PERCENTAGE',
    # Meta-Agent Governance Layer
    'MetaAgentGovernanceLayer', 'AgentType', 'ChangeCategory', 'ChangeType',
    'UnderperformanceType', 'AgentPerformance', 'ForbiddenChangeAttempt',
    'CandidateUpgrade', 'ValidationCriteria', 'ValidationResult',
    'create_meta_agent_governance_layer',
    # Production golden path
    'AccountContext', 'AgentTrapDefenseConfig', 'AgentTrapScanner',
    'DecisionGateConfig', 'GoldenPathTradingRunner', 'MarketContext',
    'ModelPerformanceMonitor', 'ModelVote', 'PredictionSample', 'RiskContext',
    'TradeDecision', 'TradeDecisionValidator', 'TradeIntent', 'TradingMode',
    'TrapCategory', 'audit_local_secrets',
    # AEAN governed meta-intelligence
    'AEANConstraints', 'AEANMetaIntelligenceLayer', 'AEANBenchmarkResult',
    'AEANBenchmarkTask', 'AEANCapabilityCandidate', 'AEANDeploymentDecision',
    'FrontierObservation', 'AEANMonitoringResult', 'AEANValidationResult',
    'create_aean_meta_intelligence_layer',
    # Universal Action Layer / Claw
    'ActionIntent', 'ActionPolicy', 'ActionResult', 'ActionRiskTier',
    'ActionStatus', 'ActionType', 'CommandActionAdapter', 'DecisionBundle',
    'DecisionConstraints', 'ExecutionStatus', 'FeedbackReport',
    'FunctionActionAdapter', 'GovernanceSignature', 'GovernanceReceipt',
    'UniversalActionLayer', 'WorkflowActionAdapter', 'sign_decision_bundle',
    'create_universal_action_layer',
]


def __dir__():
    return sorted(__all__)


# Layer access documentation
__doc__ += """

LAYER ACCESS PATTERNS:
- Layer 1 (Data): from trading_bot.data import DataManager
- Layer 2 (Signals): from trading_bot.signals import SignalEngine
- Layer 3 (Strategy): from trading_bot.strategy import StrategyController
- Layer 4 (Risk): from trading_bot.risk import RiskManager
- Layer 5 (Execution): from trading_bot.execution import ExecutionEngine
- Layer 6 (Monitoring): from trading_bot.monitoring import MonitoringSystem
- Layer 7 (Orchestration): from trading_bot import SystemOrchestrator

FORBIDDEN PATTERNS:
- Cross-layer imports (e.g., signals importing from execution)
- Circular dependencies between any layers
- Direct instantiation of lower layers from higher layers
"""
