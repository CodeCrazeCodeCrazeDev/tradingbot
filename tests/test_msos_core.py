"""
Tests for AlphaAlgo MSOS - Market Survival Operating System

Tests the core functionality of the MSOS system including:
- Immutable constraints
- System hierarchy
- Decision making
- Component integration

Author: AlphaAlgo MSOS
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.msos.core import (
    MSOSCore,
    MSOSConfig,
    MSOSDecision,
    MSOSState,
    SystemHierarchy,
    HierarchyLevel,
    ImmutableConstraints,
    ConstraintType,
    DecisionType,
    ABSOLUTE_AXIOMS,
    AXIOM_HASH
)


class TestAbsoluteAxioms:
    """Test absolute axioms integrity"""
    
    def test_axioms_exist(self):
        """Test that axioms are defined"""
        assert len(ABSOLUTE_AXIOMS) == 10
    
    def test_axioms_immutable(self):
        """Test that axioms are frozen"""
        assert isinstance(ABSOLUTE_AXIOMS, frozenset)
    
    def test_axiom_hash_valid(self):
        """Test axiom hash integrity"""
        import hashlib
        current_hash = hashlib.sha256(str(sorted(ABSOLUTE_AXIOMS)).encode()).hexdigest()
        assert current_hash == AXIOM_HASH
    
    def test_key_axioms_present(self):
        """Test key axioms are present"""
        assert "Capital is non-renewable" in ABSOLUTE_AXIOMS
        assert "Survival dominates performance" in ABSOLUTE_AXIOMS
        assert "Being flat is a valid position" in ABSOLUTE_AXIOMS


class TestImmutableConstraints:
    """Test immutable constraints"""
    
    def test_constraints_exist(self):
        """Test that constraints are defined"""
        constraints = ImmutableConstraints()
        assert len(constraints.all_constraints) == 12
    
    def test_constraints_frozen(self):
        """Test that constraints are frozen"""
        constraints = ImmutableConstraints()
        assert isinstance(constraints.all_constraints, frozenset)
    
    def test_get_constraint(self):
        """Test getting specific constraint"""
        constraints = ImmutableConstraints()
        
        max_risk = constraints.get_constraint(ConstraintType.MAX_RISK_PER_TRADE)
        assert max_risk is not None
        assert max_risk.value == 0.02  # 2%
    
    def test_constraint_violation_detection(self):
        """Test constraint violation detection"""
        constraints = ImmutableConstraints()
        
        # Test MAX constraint violation
        max_risk = constraints.get_constraint(ConstraintType.MAX_RISK_PER_TRADE)
        assert max_risk.is_violated(0.05)  # 5% > 2%
        assert not max_risk.is_violated(0.01)  # 1% < 2%
        
        # Test MIN constraint violation
        min_liquidity = constraints.get_constraint(ConstraintType.MIN_LIQUIDITY)
        assert min_liquidity.is_violated(0.1)  # 10% < 30%
        assert not min_liquidity.is_violated(0.5)  # 50% > 30%
    
    def test_check_all_constraints(self):
        """Test checking all constraints"""
        constraints = ImmutableConstraints()
        
        values = {
            ConstraintType.MAX_RISK_PER_TRADE: 0.01,
            ConstraintType.MAX_DAILY_LOSS: 0.02,
            ConstraintType.MIN_LIQUIDITY: 0.5,
        }
        
        results = constraints.check_all(values)
        assert len(results) == 3
        
        # All should pass
        for constraint, violated in results:
            assert not violated
    
    def test_get_violations(self):
        """Test getting violations"""
        constraints = ImmutableConstraints()
        
        values = {
            ConstraintType.MAX_RISK_PER_TRADE: 0.10,  # Violated
            ConstraintType.MAX_DAILY_LOSS: 0.02,      # OK
            ConstraintType.MIN_LIQUIDITY: 0.1,        # Violated
        }
        
        violations = constraints.get_violations(values)
        assert len(violations) == 2


class TestSystemHierarchy:
    """Test system hierarchy enforcement"""
    
    def test_hierarchy_levels(self):
        """Test hierarchy level ordering"""
        assert HierarchyLevel.CONSTRAINTS.value < HierarchyLevel.CONTROL.value
        assert HierarchyLevel.CONTROL.value < HierarchyLevel.EXPOSURE.value
        assert HierarchyLevel.EXPOSURE.value < HierarchyLevel.STRATEGY.value
        assert HierarchyLevel.STRATEGY.value < HierarchyLevel.INTELLIGENCE.value
        assert HierarchyLevel.INTELLIGENCE.value < HierarchyLevel.PREDICTION.value
    
    def test_can_override(self):
        """Test override permissions"""
        hierarchy = SystemHierarchy()
        
        # Higher can override lower
        assert hierarchy.can_override(HierarchyLevel.CONSTRAINTS, HierarchyLevel.CONTROL)
        assert hierarchy.can_override(HierarchyLevel.CONTROL, HierarchyLevel.EXPOSURE)
        
        # Lower cannot override higher
        assert not hierarchy.can_override(HierarchyLevel.PREDICTION, HierarchyLevel.CONSTRAINTS)
        assert not hierarchy.can_override(HierarchyLevel.STRATEGY, HierarchyLevel.CONTROL)
    
    def test_set_decision(self):
        """Test setting decisions"""
        hierarchy = SystemHierarchy()
        
        # Set constraint decision
        result = hierarchy.set_decision(
            HierarchyLevel.CONSTRAINTS,
            DecisionType.TRADE_FORBIDDEN,
            "Constraint violated"
        )
        assert result
        
        # Lower layer cannot override
        result = hierarchy.set_decision(
            HierarchyLevel.STRATEGY,
            DecisionType.TRADE_ALLOWED,
            "Strategy says OK"
        )
        assert not result  # Should fail
    
    def test_get_final_decision(self):
        """Test getting final decision"""
        hierarchy = SystemHierarchy()
        
        hierarchy.set_decision(
            HierarchyLevel.CONTROL,
            DecisionType.EXPOSURE_REDUCED,
            "Control layer decision"
        )
        
        decision, reason, layer = hierarchy.get_final_decision()
        assert decision == DecisionType.EXPOSURE_REDUCED
        assert layer == HierarchyLevel.CONTROL


class TestMSOSCore:
    """Test MSOS core functionality"""
    
    def test_core_initialization(self):
        """Test core initialization"""
        core = MSOSCore()
        
        assert core.constraints is not None
        assert core.hierarchy is not None
        assert core.state is not None
    
    def test_evaluate_good_conditions(self):
        """Test evaluation with good conditions"""
        core = MSOSCore()
        
        values = {
            ConstraintType.MIN_MARKET_VALIDITY: 0.8,
            ConstraintType.MAX_UNCERTAINTY: 0.3,
            ConstraintType.MAX_VOLATILITY: 0.02,
            ConstraintType.MAX_DRAWDOWN: 0.05,
        }
        
        decision = core.evaluate("test_strategy", "EURUSD", values)
        
        assert decision.is_trade_allowed()
        assert decision.max_exposure > 0
    
    def test_evaluate_bad_conditions(self):
        """Test evaluation with bad conditions"""
        core = MSOSCore()
        
        values = {
            ConstraintType.MIN_MARKET_VALIDITY: 0.2,  # Too low
            ConstraintType.MAX_UNCERTAINTY: 0.9,      # Too high
            ConstraintType.MAX_VOLATILITY: 0.15,      # Too high
            ConstraintType.MAX_DRAWDOWN: 0.25,        # Violated
        }
        
        decision = core.evaluate("test_strategy", "EURUSD", values)
        
        assert not decision.is_trade_allowed()
        assert decision.max_exposure == 0
    
    def test_force_flat(self):
        """Test force flat functionality"""
        core = MSOSCore()
        
        core.force_flat("Emergency")
        
        assert core.state.exposure_multiplier == 0
    
    def test_freeze_learning(self):
        """Test learning freeze"""
        core = MSOSCore()
        
        core.freeze_learning("Stress detected")
        
        assert core.state.learning_frozen


class TestMSOSDecision:
    """Test MSOS decision structure"""
    
    def test_decision_creation(self):
        """Test decision creation"""
        decision = MSOSDecision(
            decision_type=DecisionType.TRADE_ALLOWED,
            reason="All checks passed",
            authority_layer=HierarchyLevel.EXPOSURE,
            max_exposure=0.05,
            constraints_checked=[ConstraintType.MAX_RISK_PER_TRADE],
            constraints_violated=[],
            state=MSOSState()
        )
        
        assert decision.is_trade_allowed()
        assert decision.max_exposure == 0.05
    
    def test_decision_to_dict(self):
        """Test decision serialization"""
        decision = MSOSDecision(
            decision_type=DecisionType.TRADE_FORBIDDEN,
            reason="Constraint violated",
            authority_layer=HierarchyLevel.CONSTRAINTS,
            max_exposure=0.0,
            constraints_checked=[ConstraintType.MAX_RISK_PER_TRADE],
            constraints_violated=[ConstraintType.MAX_RISK_PER_TRADE],
            state=MSOSState()
        )
        
        d = decision.to_dict()
        
        assert d['decision_type'] == 'TRADE_FORBIDDEN'
        assert d['authority_layer'] == 'CONSTRAINTS'
        assert d['is_trade_allowed'] == False


class TestMSOSState:
    """Test MSOS state"""
    
    def test_state_defaults(self):
        """Test state default values"""
        state = MSOSState()
        
        assert state.market_validity == 0.0
        assert state.uncertainty_level == 1.0
        assert state.exposure_multiplier == 1.0
        assert not state.learning_frozen
    
    def test_is_tradable(self):
        """Test tradability check"""
        state = MSOSState()
        
        # Default state is not tradable (market_validity = 0)
        assert not state.is_tradable()
        
        # Set valid state
        state.market_validity = 0.7
        state.violated_constraints = []
        state.exposure_multiplier = 1.0
        
        assert state.is_tradable()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
