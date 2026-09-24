"""
Module-Specific Evolution Rules
================================

Defines what each module CAN and CANNOT evolve.
Each module has its own evolution boundaries and constraints.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, FrozenSet
from enum import Enum


class ModuleName(Enum):
    """All modules that can evolve"""
    STRATEGY = "strategy"
    RISK = "risk"
    EXECUTION = "execution"
    ML = "ml"
    DATA = "data"
    ANALYSIS = "analysis"
    BROKER = "broker"
    PORTFOLIO = "portfolio"
    SIGNALS = "signals"
    BACKTESTING = "backtesting"
    MONITORING = "monitoring"
    PERFORMANCE = "performance"
    BRAIN = "brain"
    ALPHAALGO = "alphaalgo"
    MARKET_STUDENT = "market_student"
    INTELLIGENCE_CORE = "intelligence_core"
    HEDGE_FUND = "hedge_fund"
    ELITE_AI = "elite_ai"
    QUANTUM = "quantum"
    BLOCKCHAIN = "blockchain"


@dataclass(frozen=True)
class ModuleEvolutionRules:
    """Evolution rules for a specific module"""
    module_name: str
    can_evolve: FrozenSet[str]
    requires_approval: FrozenSet[str]
    forbidden: FrozenSet[str]
    max_change_frequency_hours: int
    max_changes_per_day: int
    testing_required: bool
    rollback_required: bool


class ModuleEvolutionBoundaries:
    """
    Defines evolution boundaries for each module.
    
    Each module has specific rules about what it can evolve.
    """
    
    # ==================== STRATEGY MODULE ====================
    STRATEGY_RULES = ModuleEvolutionRules(
        module_name="strategy",
        can_evolve=frozenset({
            "indicator_parameters",
            "entry_thresholds",
            "exit_thresholds",
            "timeframe_weights",
            "signal_combinations",
            "pattern_recognition",
            "trend_detection_params",
            "momentum_params",
            "volatility_params",
            "strategy_weights",
            "filter_conditions",
            "confirmation_rules"
        }),
        requires_approval=frozenset({
            "strategy_activation",
            "strategy_deactivation",
            "new_strategy_addition",
            "strategy_removal",
            "core_logic_changes"
        }),
        forbidden=frozenset({
            "risk_per_trade",
            "max_position_size",
            "stop_loss_bypass",
            "emergency_exit_disable"
        }),
        max_change_frequency_hours=4,
        max_changes_per_day=6,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== RISK MODULE ====================
    RISK_RULES = ModuleEvolutionRules(
        module_name="risk",
        can_evolve=frozenset({
            "position_sizing_formula",
            "correlation_thresholds",
            "volatility_scaling",
            "kelly_fraction",
            "risk_parity_weights",
            "diversification_params"
        }),
        requires_approval=frozenset({
            "risk_limit_adjustments",
            "leverage_changes",
            "drawdown_threshold_changes",
            "position_size_limit_changes",
            "exposure_limit_changes",
            "var_calculation_method",
            "risk_model_changes"
        }),
        forbidden=frozenset({
            "max_risk_per_trade",  # ABSOLUTE 2%
            "max_daily_loss",      # ABSOLUTE 5%
            "max_drawdown",        # ABSOLUTE 20%
            "max_leverage",        # ABSOLUTE 5x
            "max_position_size",   # ABSOLUTE 10%
            "emergency_stop",
            "circuit_breakers",
            "risk_override"
        }),
        max_change_frequency_hours=24,  # Risk changes are infrequent
        max_changes_per_day=2,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== EXECUTION MODULE ====================
    EXECUTION_RULES = ModuleEvolutionRules(
        module_name="execution",
        can_evolve=frozenset({
            "order_routing_logic",
            "venue_selection",
            "execution_timing",
            "order_splitting",
            "iceberg_parameters",
            "twap_parameters",
            "vwap_parameters",
            "slippage_tolerance",
            "fill_timeout",
            "retry_logic",
            "latency_optimization"
        }),
        requires_approval=frozenset({
            "new_venue_addition",
            "venue_removal",
            "execution_algorithm_changes",
            "order_type_changes"
        }),
        forbidden=frozenset({
            "order_validation_bypass",
            "risk_check_bypass",
            "compliance_check_bypass",
            "manual_override_disable"
        }),
        max_change_frequency_hours=2,
        max_changes_per_day=12,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== ML MODULE ====================
    ML_RULES = ModuleEvolutionRules(
        module_name="ml",
        can_evolve=frozenset({
            "model_architectures",
            "hyperparameters",
            "feature_engineering",
            "feature_selection",
            "training_parameters",
            "validation_methods",
            "ensemble_weights",
            "learning_rate",
            "batch_size",
            "epochs",
            "regularization",
            "dropout_rate",
            "optimizer_choice",
            "loss_function"
        }),
        requires_approval=frozenset({
            "model_deployment",
            "model_replacement",
            "training_data_changes",
            "feature_set_changes"
        }),
        forbidden=frozenset({
            "data_leakage_introduction",
            "overfitting_allowance",
            "validation_bypass",
            "bias_introduction"
        }),
        max_change_frequency_hours=6,
        max_changes_per_day=4,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== DATA MODULE ====================
    DATA_RULES = ModuleEvolutionRules(
        module_name="data",
        can_evolve=frozenset({
            "data_cleaning_methods",
            "outlier_detection",
            "missing_data_handling",
            "normalization_methods",
            "feature_transformations",
            "aggregation_methods",
            "sampling_strategies",
            "data_validation_rules"
        }),
        requires_approval=frozenset({
            "data_source_changes",
            "data_schema_changes",
            "storage_changes",
            "retention_policy_changes"
        }),
        forbidden=frozenset({
            "data_deletion_without_backup",
            "audit_trail_modification",
            "data_integrity_bypass",
            "compliance_data_removal"
        }),
        max_change_frequency_hours=8,
        max_changes_per_day=3,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== ANALYSIS MODULE ====================
    ANALYSIS_RULES = ModuleEvolutionRules(
        module_name="analysis",
        can_evolve=frozenset({
            "regime_detection_params",
            "pattern_recognition_params",
            "correlation_methods",
            "volatility_estimation",
            "trend_detection",
            "support_resistance_calc",
            "indicator_combinations",
            "analysis_timeframes"
        }),
        requires_approval=frozenset({
            "new_analysis_method",
            "analysis_method_removal",
            "core_algorithm_changes"
        }),
        forbidden=frozenset({
            "analysis_bypass",
            "validation_skip",
            "quality_check_disable"
        }),
        max_change_frequency_hours=4,
        max_changes_per_day=6,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== BROKER MODULE ====================
    BROKER_RULES = ModuleEvolutionRules(
        module_name="broker",
        can_evolve=frozenset({
            "connection_retry_logic",
            "timeout_parameters",
            "reconnection_strategy",
            "heartbeat_interval",
            "buffer_sizes"
        }),
        requires_approval=frozenset({
            "broker_addition",
            "broker_removal",
            "credential_changes",
            "api_version_changes",
            "connection_parameters"
        }),
        forbidden=frozenset({
            "credential_exposure",
            "authentication_bypass",
            "encryption_disable",
            "security_downgrade",
            "auto_credential_modification"
        }),
        max_change_frequency_hours=24,
        max_changes_per_day=1,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== PORTFOLIO MODULE ====================
    PORTFOLIO_RULES = ModuleEvolutionRules(
        module_name="portfolio",
        can_evolve=frozenset({
            "rebalancing_frequency",
            "rebalancing_thresholds",
            "allocation_optimization",
            "diversification_targets",
            "correlation_targets"
        }),
        requires_approval=frozenset({
            "allocation_limits",
            "concentration_limits",
            "sector_limits",
            "asset_class_limits",
            "rebalancing_strategy_changes"
        }),
        forbidden=frozenset({
            "concentration_limit_removal",
            "diversification_bypass",
            "risk_aggregation_disable"
        }),
        max_change_frequency_hours=12,
        max_changes_per_day=2,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== BRAIN MODULE ====================
    BRAIN_RULES = ModuleEvolutionRules(
        module_name="brain",
        can_evolve=frozenset({
            "decision_weights",
            "confidence_thresholds",
            "learning_parameters",
            "memory_retention",
            "pattern_matching_params",
            "reasoning_depth",
            "exploration_rate"
        }),
        requires_approval=frozenset({
            "core_reasoning_changes",
            "decision_framework_changes",
            "learning_algorithm_changes"
        }),
        forbidden=frozenset({
            "safety_reasoning_bypass",
            "risk_awareness_disable",
            "human_override_ignore",
            "goal_modification"
        }),
        max_change_frequency_hours=6,
        max_changes_per_day=4,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== ALPHAALGO MODULE ====================
    ALPHAALGO_RULES = ModuleEvolutionRules(
        module_name="alphaalgo",
        can_evolve=frozenset({
            "learning_curriculum",
            "lesson_extraction",
            "pattern_recognition",
            "market_observation_params",
            "feedback_processing",
            "hypothesis_generation"
        }),
        requires_approval=frozenset({
            "core_identity_changes",
            "learning_cycle_changes",
            "reward_system_changes",
            "governance_changes"
        }),
        forbidden=frozenset({
            "identity_removal",
            "safety_rules_modification",
            "human_approval_bypass",
            "self_improvement_principles_change"
        }),
        max_change_frequency_hours=8,
        max_changes_per_day=3,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== MARKET STUDENT MODULE ====================
    MARKET_STUDENT_RULES = ModuleEvolutionRules(
        module_name="market_student",
        can_evolve=frozenset({
            "study_curriculum",
            "learning_perspectives",
            "observation_methods",
            "lesson_database_structure",
            "pattern_learning",
            "failure_analysis"
        }),
        requires_approval=frozenset({
            "core_philosophy_changes",
            "teacher_student_relationship",
            "learning_roles_modification"
        }),
        forbidden=frozenset({
            "market_teacher_replacement",
            "learning_bypass",
            "experience_deletion",
            "lesson_forgetting"
        }),
        max_change_frequency_hours=12,
        max_changes_per_day=2,
        testing_required=True,
        rollback_required=True
    )
    
    # ==================== INTELLIGENCE CORE MODULE ====================
    INTELLIGENCE_CORE_RULES = ModuleEvolutionRules(
        module_name="intelligence_core",
        can_evolve=frozenset({
            "hypothesis_generation",
            "testing_procedures",
            "structural_memory",
            "failure_detection_params",
            "adversarial_scenarios",
            "robustness_testing"
        }),
        requires_approval=frozenset({
            "governance_boundaries",
            "capability_limits",
            "audit_procedures",
            "self_audit_changes"
        }),
        forbidden=frozenset({
            "governance_bypass",
            "capability_expansion_unauthorized",
            "audit_trail_modification",
            "boundary_removal"
        }),
        max_change_frequency_hours=24,
        max_changes_per_day=1,
        testing_required=True,
        rollback_required=True
    )
    
    @classmethod
    def get_module_rules(cls, module_name: str) -> ModuleEvolutionRules:
        """Get evolution rules for a specific module"""
        rules_map = {
            "strategy": cls.STRATEGY_RULES,
            "risk": cls.RISK_RULES,
            "execution": cls.EXECUTION_RULES,
            "ml": cls.ML_RULES,
            "data": cls.DATA_RULES,
            "analysis": cls.ANALYSIS_RULES,
            "broker": cls.BROKER_RULES,
            "portfolio": cls.PORTFOLIO_RULES,
            "brain": cls.BRAIN_RULES,
            "alphaalgo": cls.ALPHAALGO_RULES,
            "market_student": cls.MARKET_STUDENT_RULES,
            "intelligence_core": cls.INTELLIGENCE_CORE_RULES,
        }
        
        return rules_map.get(module_name.lower())
    
    @classmethod
    def can_module_evolve(cls, module_name: str, component: str) -> tuple[bool, str]:
        """
        Check if a module can evolve a specific component.
        
        Returns:
            (allowed, reason)
        """
        rules = cls.get_module_rules(module_name)
        
        if not rules:
            return False, f"Unknown module: {module_name}"
        
        if component in rules.forbidden:
            return False, f"FORBIDDEN: {component} cannot be evolved in {module_name}"
        
        if component in rules.requires_approval:
            return True, f"REQUIRES APPROVAL: {component} in {module_name}"
        
        if component in rules.can_evolve:
            return True, f"ALLOWED: {component} can evolve in {module_name}"
        
        # Unknown component - require approval by default
        return True, f"UNKNOWN COMPONENT: {component} requires approval in {module_name}"
    
    @classmethod
    def get_all_module_summaries(cls) -> Dict[str, Dict[str, any]]:
        """Get summary of evolution rules for all modules"""
        modules = [
            "strategy", "risk", "execution", "ml", "data", "analysis",
            "broker", "portfolio", "brain", "alphaalgo", "market_student",
            "intelligence_core"
        ]
        
        summaries = {}
        for module in modules:
            rules = cls.get_module_rules(module)
            if rules:
                summaries[module] = {
                    "can_evolve_count": len(rules.can_evolve),
                    "requires_approval_count": len(rules.requires_approval),
                    "forbidden_count": len(rules.forbidden),
                    "max_change_frequency_hours": rules.max_change_frequency_hours,
                    "max_changes_per_day": rules.max_changes_per_day,
                    "testing_required": rules.testing_required
                }
        
        return summaries


def get_module_evolution_guide(module_name: str) -> Dict[str, any]:
    """Get comprehensive evolution guide for a module"""
    rules = ModuleEvolutionBoundaries.get_module_rules(module_name)
    
    if not rules:
        return {"error": f"Unknown module: {module_name}"}
    
    return {
        "module": module_name,
        "can_evolve": sorted(list(rules.can_evolve)),
        "requires_approval": sorted(list(rules.requires_approval)),
        "forbidden": sorted(list(rules.forbidden)),
        "constraints": {
            "max_change_frequency_hours": rules.max_change_frequency_hours,
            "max_changes_per_day": rules.max_changes_per_day,
            "testing_required": rules.testing_required,
            "rollback_required": rules.rollback_required
        }
    }
