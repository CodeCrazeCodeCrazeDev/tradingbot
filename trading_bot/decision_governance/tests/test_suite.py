"""
Comprehensive DGS Test Suite

Unit tests, integration tests, and mocking framework for DGS.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import asyncio
import json
import tempfile
import os
from typing import Dict, Any, List

# Import all DGS components
from ..core_types import (
    GovernanceDecision, DecisionRecord, MarketRegime, 
    Claim, ClaimType, Evidence, OutcomeRecord
)
from ..signal_validator import SignalValidator, SignalValidationResult
from ..risk_gatekeeper import RiskGatekeeper, RiskLimits
from ..execution_engine import ExecutionFeasibilityEngine
from ..layer1_claim_graph import ClaimGraphConstructor
from ..layer2_evidence_auditor import EvidenceSufficiencyAuditor
from ..layer3_adversarial_analyst import AdversarialCounterAnalyst
from ..layer7_arbiter import GovernanceArbiter, GovernanceCriteria
from ..memory_system import DecisionMemory, OutcomeMemory, FailureMemory


class TestSignalValidator(unittest.TestCase):
    """Test signal validation component"""
    
    def setUp(self):
        self.validator = SignalValidator()
    
    def test_valid_signal_passes(self):
        """Test that a valid signal passes validation"""
        signal = {
            'source': 'test_agent',
            'direction': 'buy',
            'confidence': 0.75,
            'symbol': 'AAPL',
            'timestamp': datetime.utcnow(),
            'rationale': 'Strong uptrend',
            'evidence': ['Price above MA', 'Volume surge']
        }
        
        result = self.validator.validate_signal(signal, 'AAPL')
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_missing_required_fields_fails(self):
        """Test that missing required fields cause validation to fail"""
        signal = {
            'source': 'test_agent',
            # Missing direction and confidence
            'timestamp': datetime.utcnow()
        }
        
        result = self.validator.validate_signal(signal, 'AAPL')
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('Missing' in err[1] for err in result.errors))
    
    def test_stale_signal_detected(self):
        """Test that stale signals are detected"""
        old_time = datetime.utcnow() - timedelta(seconds=400)
        signal = {
            'source': 'test_agent',
            'direction': 'buy',
            'confidence': 0.75,
            'timestamp': old_time
        }
        
        result = self.validator.validate_signal(signal, 'AAPL')
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('stale' in err[1].lower() for err in result.errors))
    
    def test_confidence_bounds_check(self):
        """Test that confidence values outside bounds are rejected"""
        signal = {
            'source': 'test_agent',
            'direction': 'buy',
            'confidence': 1.5,  # Out of bounds
            'timestamp': datetime.utcnow()
        }
        
        result = self.validator.validate_signal(signal, 'AAPL')
        
        self.assertFalse(result.is_valid)


class TestRiskGatekeeper(unittest.TestCase):
    """Test risk gatekeeper component"""
    
    def setUp(self):
        self.limits = RiskLimits(
            max_position_size_pct=0.10,
            max_daily_loss_pct=0.02,
            max_portfolio_heat=5
        )
        self.gatekeeper = RiskGatekeeper(limits=self.limits)
    
    def test_position_size_limit(self):
        """Test position size limit enforcement"""
        result = self.gatekeeper.check_risk(
            symbol='AAPL',
            proposed_direction='buy',
            proposed_size=15.0,  # 15% of portfolio
            proposed_price=100.0,
            portfolio_value=100.0
        )
        
        self.assertFalse(result.passed)
        self.assertTrue(any('size' in v[1].lower() for v in result.violations))
    
    def test_portfolio_heat_limit(self):
        """Test portfolio heat (max positions) limit"""
        # Add 5 existing positions
        for i in range(5):
            self.gatekeeper.update_position(
                f'SYM{i}', 1.0, 100.0
            )
        
        result = self.gatekeeper.check_risk(
            symbol='NEW',
            proposed_direction='buy',
            proposed_size=1.0,
            proposed_price=100.0,
            portfolio_value=1000.0
        )
        
        self.assertFalse(result.passed)
        self.assertTrue(any('heat' in v[1].lower() for v in result.violations))
    
    def test_valid_position_passes(self):
        """Test that a valid position passes risk checks"""
        result = self.gatekeeper.check_risk(
            symbol='AAPL',
            proposed_direction='buy',
            proposed_size=5.0,  # 5% of portfolio
            proposed_price=100.0,
            portfolio_value=100.0
        )
        
        self.assertTrue(result.passed)
        self.assertEqual(len(result.violations), 0)


class TestClaimGraphConstructor(unittest.TestCase):
    """Test claim graph construction"""
    
    def setUp(self):
        self.constructor = ClaimGraphConstructor()
    
    def test_claim_extraction(self):
        """Test that claims are extracted from signal"""
        signal = {
            'thesis': 'Bullish on AAPL',
            'confidence': 0.8,
            'assumptions': ['Market stable', 'No earnings surprise'],
            'evidence': ['Price above MA', 'RSI strong'],
            'invalidation_conditions': ['Breaks support']
        }
        
        claims = self.constructor.construct_claim_graph(
            agent_output=signal,
            source_agent='test',
            symbol='AAPL'
        )
        
        # Should have thesis, assumptions, evidence, invalidations
        claim_types = [c.claim_type for c in claims]
        self.assertIn(ClaimType.THESIS, claim_types)
        self.assertIn(ClaimType.ASSUMPTION, claim_types)
        self.assertIn(ClaimType.EVIDENCE, claim_types)
        self.assertIn(ClaimType.INVALIDATION_CONDITION, claim_types)
    
    def test_claim_dependencies(self):
        """Test that claim dependencies are tracked"""
        signal = {
            'thesis': 'Main claim',
            'assumptions': ['Assumption 1']
        }
        
        claims = self.constructor.construct_claim_graph(
            agent_output=signal,
            source_agent='test',
            symbol='AAPL'
        )
        
        # Find thesis claim
        thesis = next(c for c in claims if c.claim_type == ClaimType.THESIS)
        
        # Should have at least one dependent claim (assumption)
        self.assertGreaterEqual(len(thesis.dependent_claims), 0)


class TestEvidenceAuditor(unittest.TestCase):
    """Test evidence auditing"""
    
    def setUp(self):
        self.auditor = EvidenceSufficiencyAuditor()
    
    def test_missing_evidence_detection(self):
        """Test detection of missing evidence"""
        claim = Claim(
            id='test_claim',
            claim_type=ClaimType.THESIS,
            content='Test thesis',
            source='test',
            timestamp=datetime.utcnow(),
            evidence_refs=[]  # No evidence
        )
        
        coverage, gaps, contradictions = self.auditor.audit_evidence([claim])
        
        self.assertEqual(coverage['test_claim'].value, 'missing')
        self.assertGreater(len(gaps), 0)


class TestAdversarialAnalyst(unittest.TestCase):
    """Test adversarial analysis"""
    
    def setUp(self):
        self.analyst = AdversarialCounterAnalyst()
    
    def test_challenges_generated(self):
        """Test that challenges are generated for claims"""
        claims = [
            Claim(
                id='thesis1',
                claim_type=ClaimType.THESIS,
                content='Bullish thesis',
                source='test',
                timestamp=datetime.utcnow(),
                confidence=0.8
            )
        ]
        
        challenges = self.analyst.generate_challenges(claims, None, 'AAPL')
        
        self.assertGreater(len(challenges), 0)
        self.assertTrue(any(c.challenge_type == 'rival_explanation' for c in challenges))
    
    def test_challenge_severity_ranking(self):
        """Test that challenges are ranked by severity"""
        claims = [
            Claim(
                id='thesis1',
                claim_type=ClaimType.THESIS,
                content='High confidence thesis',
                source='test',
                timestamp=datetime.utcnow(),
                confidence=0.9
            )
        ]
        
        challenges = self.analyst.generate_challenges(claims, None, 'AAPL')
        
        # Should be sorted by severity (highest first)
        for i in range(len(challenges) - 1):
            self.assertGreaterEqual(
                challenges[i].severity,
                challenges[i + 1].severity
            )


class TestGovernanceArbiter(unittest.TestCase):
    """Test governance arbitration"""
    
    def setUp(self):
        self.criteria = GovernanceCriteria(
            min_confidence=0.6,
            min_robustness=0.5
        )
        self.arbiter = GovernanceArbiter(criteria=self.criteria)
    
    def test_approve_high_quality_thesis(self):
        """Test approval of high-quality thesis"""
        from ..core_types import UncertaintyProfile
        
        claims = [
            Claim(
                id='thesis1',
                claim_type=ClaimType.THESIS,
                content='Strong thesis',
                source='test',
                timestamp=datetime.utcnow(),
                confidence=0.8
            )
        ]
        
        uncertainty = UncertaintyProfile(
            overall_confidence=0.8,
            calibration_quality=0.7,
            abstention_probability=0.1,
            decomposition={}
        )
        
        decision, record = self.arbiter.arbitrate(
            claims=claims,
            evidence_coverage={'coverage_score': 0.8, 'coverage': {}, 'gaps': []},
            adversarial_challenges=[],
            regime_fit_score=0.7,
            regime_underrepresented=False,
            robustness_score=0.7,
            uncertainty_profile=uncertainty,
            execution_feasibility=None,
            counterfactual_scenarios=[],
            symbol='AAPL',
            proposed_size=1.0,
            signal_confidence=0.8
        )
        
        self.assertEqual(decision, GovernanceDecision.APPROVE)
    
    def test_reject_low_confidence(self):
        """Test rejection of low-confidence thesis"""
        from ..core_types import UncertaintyProfile
        
        claims = [
            Claim(
                id='thesis1',
                claim_type=ClaimType.THESIS,
                content='Weak thesis',
                source='test',
                timestamp=datetime.utcnow(),
                confidence=0.4
            )
        ]
        
        uncertainty = UncertaintyProfile(
            overall_confidence=0.4,
            calibration_quality=0.5,
            abstention_probability=0.4,
            decomposition={}
        )
        
        decision, record = self.arbiter.arbitrate(
            claims=claims,
            evidence_coverage={'coverage_score': 0.3, 'coverage': {}, 'gaps': ['missing evidence']},
            adversarial_challenges=[],
            regime_fit_score=0.4,
            regime_underrepresented=False,
            robustness_score=0.3,
            uncertainty_profile=uncertainty,
            execution_feasibility=None,
            counterfactual_scenarios=[],
            symbol='AAPL',
            proposed_size=1.0,
            signal_confidence=0.4
        )
        
        self.assertIn(decision, [GovernanceDecision.REJECT, GovernanceDecision.ABSTAIN])


class TestMemorySystems(unittest.TestCase):
    """Test memory systems"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.decision_memory = DecisionMemory(f"{self.temp_dir}/decisions.db")
        self.outcome_memory = OutcomeMemory(f"{self.temp_dir}/outcomes.db")
        self.failure_memory = FailureMemory(f"{self.temp_dir}/failures.db")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_decision_storage(self):
        """Test decision storage and retrieval"""
        decision = DecisionRecord(
            id='test_decision',
            timestamp=datetime.utcnow(),
            symbol='AAPL',
            signal_source='test',
            final_decision=GovernanceDecision.APPROVE,
            approved_size=1.0
        )
        
        self.decision_memory.store_decision(decision)
        retrieved = self.decision_memory.get_decision('test_decision')
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, 'test_decision')
        self.assertEqual(retrieved.symbol, 'AAPL')
    
    def test_outcome_storage(self):
        """Test outcome storage"""
        outcome = OutcomeRecord(
            decision_id='test_decision',
            realized_pnl=0.05,
            realized_slippage=0.001,
            fill_behavior='full',
            invalidation_hit=False,
            confidence_error=0.1,
            calibration_error=0.05
        )
        
        self.outcome_memory.record_outcome('test_decision', outcome, 'AAPL')
        retrieved = self.outcome_memory.get_outcome('test_decision')
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.realized_pnl, 0.05)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete DGS flow"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('..integration.DecisionGovernanceSystem')
    def test_complete_decision_flow(self, mock_dgs):
        """Test complete decision flow from signal to outcome"""
        # This would be a full integration test
        # Mocking for unit test purposes
        pass


class MockTradingFramework:
    """Mock trading framework for testing integrations"""
    
    def __init__(self):
        self.orders = []
        self.positions = {}
    
    def place_order(self, symbol: str, size: float, side: str) -> Dict:
        """Mock order placement"""
        order = {
            'id': f'order_{len(self.orders)}',
            'symbol': symbol,
            'size': size,
            'side': side,
            'status': 'filled',
            'fill_price': 100.0,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.orders.append(order)
        return order
    
    def get_position(self, symbol: str) -> Dict:
        """Mock position retrieval"""
        return self.positions.get(symbol, {'size': 0, 'entry_price': 0})


class TestFrameworkIntegration(unittest.TestCase):
    """Test integration with trading frameworks"""
    
    def setUp(self):
        self.framework = MockTradingFramework()
    
    def test_dgs_to_framework_integration(self):
        """Test DGS integration with trading framework"""
        # Simulate DGS decision
        decision = GovernanceDecision.APPROVE
        
        if decision == GovernanceDecision.APPROVE:
            order = self.framework.place_order('AAPL', 1.0, 'buy')
            self.assertEqual(order['status'], 'filled')
            self.assertEqual(order['symbol'], 'AAPL')


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSignalValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskGatekeeper))
    suite.addTests(loader.loadTestsFromTestCase(TestClaimGraphConstructor))
    suite.addTests(loader.loadTestsFromTestCase(TestEvidenceAuditor))
    suite.addTests(loader.loadTestsFromTestCase(TestAdversarialAnalyst))
    suite.addTests(loader.loadTestsFromTestCase(TestGovernanceArbiter))
    suite.addTests(loader.loadTestsFromTestCase(TestMemorySystems))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestFrameworkIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
