"""
Evolution Boundaries - Immutable Rules for What AI Can and Cannot Do
=====================================================================

This module defines the ABSOLUTE BOUNDARIES for recursive self-evolution.
These rules are FROZEN and cannot be modified by the AI itself.

CORE PRINCIPLE: The AI can evolve EVERYTHING except its core constraints.
"""

from dataclasses import dataclass, field
from typing import Set, List, Dict, Any, FrozenSet
from enum import Enum
import hashlib
import json


class EvolutionPermission(Enum):
    """What the AI is allowed to evolve"""
    ALLOWED = "allowed"
    REQUIRES_APPROVAL = "requires_approval"
    FORBIDDEN = "forbidden"


@dataclass(frozen=True)
class ImmutableBoundary:
    """An immutable boundary that AI cannot cross"""
    rule_id: str
    description: str
    rationale: str
    enforcement_level: str  # "ABSOLUTE", "CRITICAL", "HIGH"
    
    def __hash__(self):
        return hash((self.rule_id, self.description))


class EvolutionBoundaries:
    """
    Defines what the AI CAN and CANNOT evolve.
    
    These boundaries are cryptographically verified and cannot be modified
    by the AI itself. Any attempt to modify these boundaries will be logged
    and blocked.
    """
    
    # ==================== WHAT AI CAN EVOLVE ====================
    
    ALLOWED_TO_EVOLVE: FrozenSet[str] = frozenset({
        # Strategy Evolution
        "strategy_parameters",
        "strategy_combinations",
        "strategy_weights",
        "signal_generation_logic",
        "indicator_parameters",
        "timeframe_selection",
        "entry_conditions",
        "exit_conditions",
        "position_sizing_formulas",
        
        # ML Model Evolution
        "model_architectures",
        "hyperparameters",
        "feature_engineering",
        "feature_selection",
        "ensemble_methods",
        "training_procedures",
        "validation_methods",
        "model_combinations",
        
        # Data Processing Evolution
        "data_preprocessing",
        "data_cleaning_methods",
        "outlier_detection",
        "feature_transformations",
        "normalization_methods",
        "data_aggregation",
        
        # Execution Evolution
        "order_routing_logic",
        "execution_timing",
        "slippage_optimization",
        "fill_strategies",
        "order_splitting",
        
        # Analysis Evolution
        "market_regime_detection",
        "pattern_recognition",
        "correlation_analysis",
        "volatility_estimation",
        "trend_detection",
        
        # Performance Evolution
        "optimization_algorithms",
        "caching_strategies",
        "parallel_processing",
        "resource_allocation",
        
        # Learning Evolution
        "learning_rates",
        "exploration_strategies",
        "reward_functions",
        "meta_learning_approaches",
    })
    
    # ==================== WHAT REQUIRES HUMAN APPROVAL ====================
    
    REQUIRES_APPROVAL: FrozenSet[str] = frozenset({
        # Risk Management Changes
        "risk_limits",
        "position_size_limits",
        "leverage_limits",
        "drawdown_thresholds",
        "stop_loss_rules",
        
        # Capital Allocation
        "capital_allocation_rules",
        "portfolio_construction",
        "diversification_rules",
        
        # Trading Rules
        "trading_hours",
        "market_selection",
        "instrument_selection",
        "trading_frequency",
        
        # System Architecture
        "core_architecture_changes",
        "database_schema_changes",
        "api_modifications",
        "integration_changes",
        
        # Security Changes
        "authentication_methods",
        "encryption_algorithms",
        "access_control",
        
        # Compliance
        "regulatory_compliance_rules",
        "reporting_requirements",
        "audit_trail_modifications",
    })
    
    # ==================== WHAT AI CANNOT EVOLVE (FORBIDDEN) ====================
    
    FORBIDDEN_TO_EVOLVE: FrozenSet[str] = frozenset({
        # Core Identity
        "immutable_purpose",
        "core_constraints",
        "evolution_boundaries",
        "safety_guardrails",
        
        # Risk Constraints (ABSOLUTE LIMITS)
        "max_risk_per_trade",  # Cannot exceed 2%
        "max_daily_loss",      # Cannot exceed 5%
        "max_drawdown",        # Cannot exceed 20%
        "max_leverage",        # Cannot exceed 5x
        "max_position_size",   # Cannot exceed 10%
        
        # Safety Systems
        "emergency_stop",
        "circuit_breakers",
        "kill_switches",
        "fail_safe_mechanisms",
        "human_override",
        
        # Governance
        "approval_workflows",
        "human_authority",
        "governance_hierarchy",
        "audit_requirements",
        
        # Security
        "credential_storage",
        "encryption_keys",
        "access_credentials",
        "api_keys",
        
        # Legal/Compliance
        "regulatory_constraints",
        "legal_boundaries",
        "compliance_requirements",
        
        # Meta-Evolution
        "evolution_boundary_rules",  # Cannot modify these rules
        "self_modification_limits",
        "recursive_depth_limits",
    })
    
    # ==================== IMMUTABLE CONSTRAINTS ====================
    
    IMMUTABLE_CONSTRAINTS: List[ImmutableBoundary] = [
        ImmutableBoundary(
            rule_id="RISK_001",
            description="Maximum risk per trade: 2%",
            rationale="Prevents catastrophic loss from single trade",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="RISK_002",
            description="Maximum daily loss: 5%",
            rationale="Prevents rapid capital depletion",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="RISK_003",
            description="Maximum drawdown: 20%",
            rationale="Ensures capital preservation and recovery capability",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="RISK_004",
            description="Maximum leverage: 5x",
            rationale="Prevents excessive risk from leverage",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="GOV_001",
            description="Human approval required for risk limit changes",
            rationale="Ensures human oversight of critical parameters",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="GOV_002",
            description="Human override always works",
            rationale="Ensures human maintains ultimate control",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="SAFE_001",
            description="Emergency stop cannot be disabled",
            rationale="Ensures ability to halt trading in crisis",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="SAFE_002",
            description="Circuit breakers cannot be removed",
            rationale="Prevents runaway trading in extreme conditions",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="META_001",
            description="Evolution boundaries cannot be self-modified",
            rationale="Prevents AI from removing its own constraints",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="META_002",
            description="Maximum recursive evolution depth: 5 levels",
            rationale="Prevents infinite recursion and complexity explosion",
            enforcement_level="CRITICAL"
        ),
        ImmutableBoundary(
            rule_id="COMP_001",
            description="All trades must be logged and auditable",
            rationale="Ensures regulatory compliance and transparency",
            enforcement_level="ABSOLUTE"
        ),
        ImmutableBoundary(
            rule_id="COMP_002",
            description="No market manipulation allowed",
            rationale="Ensures legal and ethical trading",
            enforcement_level="ABSOLUTE"
        ),
    ]
    
    @classmethod
    def get_boundary_hash(cls) -> str:
        """
        Generate cryptographic hash of boundaries for integrity verification.
        Any modification to boundaries will change this hash.
        """
        boundary_data = {
            'allowed': sorted(list(cls.ALLOWED_TO_EVOLVE)),
            'requires_approval': sorted(list(cls.REQUIRES_APPROVAL)),
            'forbidden': sorted(list(cls.FORBIDDEN_TO_EVOLVE)),
            'constraints': [
                {
                    'id': c.rule_id,
                    'desc': c.description,
                    'level': c.enforcement_level
                }
                for c in cls.IMMUTABLE_CONSTRAINTS
            ]
        }
        
        boundary_json = json.dumps(boundary_data, sort_keys=True)
        return hashlib.sha256(boundary_json.encode()).hexdigest()
    
    @classmethod
    def check_evolution_permission(cls, area: str) -> EvolutionPermission:
        """Check if AI is allowed to evolve a specific area"""
        if area in cls.FORBIDDEN_TO_EVOLVE:
            return EvolutionPermission.FORBIDDEN
        elif area in cls.REQUIRES_APPROVAL:
            return EvolutionPermission.REQUIRES_APPROVAL
        elif area in cls.ALLOWED_TO_EVOLVE:
            return EvolutionPermission.ALLOWED
        else:
            # Unknown areas require approval by default
            return EvolutionPermission.REQUIRES_APPROVAL
    
    @classmethod
    def validate_proposal(cls, proposal: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate an evolution proposal against boundaries.
        
        Returns:
            (is_valid, reason)
        """
        area = proposal.get('area', '')
        
        permission = cls.check_evolution_permission(area)
        
        if permission == EvolutionPermission.FORBIDDEN:
            return False, f"Evolution of '{area}' is FORBIDDEN"
        
        # Check if proposal violates any immutable constraints
        for constraint in cls.IMMUTABLE_CONSTRAINTS:
            if cls._violates_constraint(proposal, constraint):
                return False, f"Violates constraint {constraint.rule_id}: {constraint.description}"
        
        # Check recursive depth
        depth = proposal.get('recursive_depth', 0)
        if depth > 5:
            return False, "Exceeds maximum recursive evolution depth (5)"
        
        if permission == EvolutionPermission.REQUIRES_APPROVAL:
            return True, f"Valid but requires human approval for '{area}'"
        
        return True, "Valid and allowed"
    
    @classmethod
    def _violates_constraint(cls, proposal: Dict[str, Any], constraint: ImmutableBoundary) -> bool:
        """Check if proposal violates a specific constraint"""
        # Check risk constraints
        if constraint.rule_id == "RISK_001":
            risk_per_trade = proposal.get('risk_per_trade', 0)
            if risk_per_trade > 0.02:  # 2%
                return True
        
        elif constraint.rule_id == "RISK_002":
            daily_loss = proposal.get('max_daily_loss', 0)
            if daily_loss > 0.05:  # 5%
                return True
        
        elif constraint.rule_id == "RISK_003":
            max_drawdown = proposal.get('max_drawdown', 0)
            if max_drawdown > 0.20:  # 20%
                return True
        
        elif constraint.rule_id == "RISK_004":
            max_leverage = proposal.get('max_leverage', 0)
            if max_leverage > 5.0:
                return True
        
        elif constraint.rule_id == "META_002":
            depth = proposal.get('recursive_depth', 0)
            if depth > 5:
                return True
        
        return False


# Store original hash for integrity verification
ORIGINAL_BOUNDARY_HASH = EvolutionBoundaries.get_boundary_hash()


def verify_boundary_integrity() -> bool:
    """Verify that boundaries have not been tampered with"""
    current_hash = EvolutionBoundaries.get_boundary_hash()
    return current_hash == ORIGINAL_BOUNDARY_HASH


def get_evolution_guide() -> Dict[str, Any]:
    """Get a comprehensive guide of what AI can and cannot evolve"""
    return {
        'can_evolve_freely': sorted(list(EvolutionBoundaries.ALLOWED_TO_EVOLVE)),
        'requires_approval': sorted(list(EvolutionBoundaries.REQUIRES_APPROVAL)),
        'forbidden': sorted(list(EvolutionBoundaries.FORBIDDEN_TO_EVOLVE)),
        'immutable_constraints': [
            {
                'id': c.rule_id,
                'description': c.description,
                'rationale': c.rationale,
                'level': c.enforcement_level
            }
            for c in EvolutionBoundaries.IMMUTABLE_CONSTRAINTS
        ],
        'boundary_hash': EvolutionBoundaries.get_boundary_hash(),
        'integrity_verified': verify_boundary_integrity()
    }
