"""
Theory Validator - Testing Academic Theories in Markets
==========================================================

Validates academic theories and research findings by:
1. Testing theories against market data
2. Measuring predictive accuracy
3. Assessing practical applicability
4. Identifying theory limitations
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status of theory validation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATED = "validated"
    PARTIALLY_VALIDATED = "partially_validated"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class TheoryType(Enum):
    """Types of theories"""
    ASSET_PRICING = "asset_pricing"
    MARKET_MICROSTRUCTURE = "market_microstructure"
    BEHAVIORAL = "behavioral"
    RISK_MODEL = "risk_model"
    ECONOMIC = "economic"
    STATISTICAL = "statistical"


@dataclass
class Theory:
    """An academic theory to validate"""
    theory_id: str
    name: str
    description: str
    theory_type: TheoryType
    
    # Source
    source_paper: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    
    # Hypothesis
    hypothesis: str = ""
    predictions: List[str] = field(default_factory=list)
    
    # Validation
    status: ValidationStatus = ValidationStatus.PENDING
    validation_results: List[Dict] = field(default_factory=list)
    
    # Metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    
    # Applicability
    applicable_assets: List[str] = field(default_factory=list)
    time_horizons: List[str] = field(default_factory=list)
    market_conditions: List[str] = field(default_factory=list)
    
    # Metadata
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    validated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'theory_id': self.theory_id,
            'name': self.name,
            'type': self.theory_type.value,
            'status': self.status.value,
            'accuracy': self.accuracy,
            'applicable_assets': self.applicable_assets
        }


@dataclass
class ValidationTest:
    """A specific test for a theory"""
    test_id: str
    theory_id: str
    
    # Test definition
    test_name: str
    test_description: str
    test_function: Optional[Callable] = None
    
    # Data requirements
    required_data: List[str] = field(default_factory=list)
    time_period: Optional[Tuple[datetime, datetime]] = None
    
    # Results
    passed: Optional[bool] = None
    score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    executed_at: Optional[datetime] = None


class TheoryValidator:
    """
    Theory Validator
    
    Validates academic theories by testing them against
    real market data and measuring their predictive power.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Theories
        self.theories: Dict[str, Theory] = {}
        self.pending_validation: List[str] = []
        
        # Validation tests
        self.test_templates: Dict[str, Callable] = {}
        self.test_results: Dict[str, List[ValidationTest]] = defaultdict(list)
        
        # Market data cache (simplified)
        self.market_data: Dict[str, np.ndarray] = {}
        
        # Statistics
        self.stats = {
            'theories_submitted': 0,
            'theories_validated': 0,
            'tests_executed': 0,
            'avg_validation_time_hours': 0.0
        }
        
        # Register default tests
        self._register_default_tests()
        
        logger.info("Theory Validator initialized")
    
    def _register_default_tests(self):
        """Register default validation test templates"""
        self.test_templates['directional_accuracy'] = self._test_directional_accuracy
        self.test_templates['return_prediction'] = self._test_return_prediction
        self.test_templates['risk_prediction'] = self._test_risk_prediction
        self.test_templates['market_timing'] = self._test_market_timing
        self.test_templates['cross_sectional'] = self._test_cross_sectional
    
    def submit_theory(
        self,
        name: str,
        description: str,
        theory_type: TheoryType,
        hypothesis: str,
        predictions: List[str],
        source_paper: Optional[str] = None,
        authors: Optional[List[str]] = None
    ) -> Theory:
        """Submit a theory for validation"""
        theory = Theory(
            theory_id=f"theory_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(self.theories)}",
            name=name,
            description=description,
            theory_type=theory_type,
            source_paper=source_paper,
            authors=authors or [],
            hypothesis=hypothesis,
            predictions=predictions
        )
        
        self.theories[theory.theory_id] = theory
        self.pending_validation.append(theory.theory_id)
        self.stats['theories_submitted'] += 1
        
        logger.info(f"Theory submitted for validation: {name}")
        
        return theory
    
    def validate_theory(
        self,
        theory_id: str,
        market_data: Optional[Dict[str, np.ndarray]] = None
    ) -> ValidationStatus:
        """Validate a theory against market data"""
        if theory_id not in self.theories:
            return ValidationStatus.PENDING
        
        theory = self.theories[theory_id]
        theory.status = ValidationStatus.IN_PROGRESS
        
        # Use provided data or cached data
        data = market_data or self.market_data
        
        if not data:
            logger.warning(f"No market data available for validation of {theory_id}")
            theory.status = ValidationStatus.INCONCLUSIVE
            return theory.status
        
        # Run appropriate tests based on theory type
        test_results = []
        
        if theory.theory_type == TheoryType.ASSET_PRICING:
            test_results.append(self._run_test(theory_id, 'return_prediction', data))
            test_results.append(self._run_test(theory_id, 'cross_sectional', data))
        
        elif theory.theory_type == TheoryType.MARKET_MICROSTRUCTURE:
            test_results.append(self._run_test(theory_id, 'directional_accuracy', data))
            test_results.append(self._run_test(theory_id, 'market_timing', data))
        
        elif theory.theory_type == TheoryType.RISK_MODEL:
            test_results.append(self._run_test(theory_id, 'risk_prediction', data))
        
        else:
            # Generic validation
            test_results.append(self._run_test(theory_id, 'directional_accuracy', data))
        
        # Calculate overall scores
        scores = [t.score for t in test_results if t.score is not None]
        if scores:
            theory.accuracy = np.mean(scores)
            theory.precision = np.mean([t.score for t in test_results[:len(test_results)//2]]) if len(test_results) > 1 else scores[0]
            theory.recall = np.mean([t.score for t in test_results[len(test_results)//2:]]) if len(test_results) > 1 else scores[0]
        
        # Determine status
        passed_tests = sum(1 for t in test_results if t.passed)
        total_tests = len(test_results)
        
        if total_tests == 0:
            theory.status = ValidationStatus.INCONCLUSIVE
        elif passed_tests == total_tests:
            theory.status = ValidationStatus.VALIDATED
        elif passed_tests >= total_tests * 0.5:
            theory.status = ValidationStatus.PARTIALLY_VALIDATED
        else:
            theory.status = ValidationStatus.REJECTED
        
        theory.validated_at = datetime.utcnow()
        theory.validation_results = [t.__dict__ for t in test_results]
        
        if theory_id in self.pending_validation:
            self.pending_validation.remove(theory_id)
        
        self.stats['theories_validated'] += 1
        self.stats['tests_executed'] += total_tests
        
        logger.info(f"Theory {theory_id} validation complete: {theory.status.value}")
        
        return theory.status
    
    def _run_test(
        self,
        theory_id: str,
        test_type: str,
        data: Dict[str, np.ndarray]
    ) -> ValidationTest:
        """Run a specific validation test"""
        test = ValidationTest(
            test_id=f"test_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            theory_id=theory_id,
            test_name=test_type,
            test_description=f"Test {test_type} for theory {theory_id}"
        )
        
        # Execute test
        if test_type in self.test_templates:
            try:
                result = self.test_templates[test_type](data, self.theories[theory_id])
                test.passed = result['passed']
                test.score = result['score']
                test.details = result.get('details', {})
            except Exception as e:
                logger.error(f"Test execution error: {e}")
                test.passed = False
                test.score = 0.0
                test.details = {'error': str(e)}
        
        test.executed_at = datetime.utcnow()
        self.test_results[theory_id].append(test)
        
        return test
    
    def _test_directional_accuracy(
        self,
        data: Dict[str, np.ndarray],
        theory: Theory
    ) -> Dict:
        """Test directional prediction accuracy"""
        # Simulate directional accuracy test
        # In production, this would use actual predictions
        
        if 'returns' not in data:
            return {'passed': False, 'score': 0.0, 'details': {'error': 'No returns data'}}
        
        returns = data['returns']
        
        # Simulate predictions (random for demo)
        predictions = np.random.choice([-1, 1], size=len(returns))
        actual_directions = np.sign(returns)
        
        # Calculate accuracy
        correct = np.sum(predictions == actual_directions)
        accuracy = correct / len(returns) if len(returns) > 0 else 0.0
        
        # Theory passes if accuracy > 55% (better than random)
        passed = accuracy > 0.55
        
        return {
            'passed': passed,
            'score': accuracy,
            'details': {
                'correct_predictions': int(correct),
                'total_predictions': len(returns),
                'accuracy_pct': accuracy * 100
            }
        }
    
    def _test_return_prediction(
        self,
        data: Dict[str, np.ndarray],
        theory: Theory
    ) -> Dict:
        """Test return prediction accuracy"""
        if 'returns' not in data or 'predicted_returns' not in data:
            return {'passed': False, 'score': 0.0}
        
        actual = data['returns']
        predicted = data['predicted_returns']
        
        # Calculate R-squared
        if len(actual) == len(predicted) and len(actual) > 0:
            ss_res = np.sum((actual - predicted) ** 2)
            ss_tot = np.sum((actual - np.mean(actual)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        else:
            r_squared = 0.0
        
        passed = r_squared > 0.1  # At least 10% variance explained
        
        return {
            'passed': passed,
            'score': max(0.0, r_squared),
            'details': {'r_squared': r_squared}
        }
    
    def _test_risk_prediction(
        self,
        data: Dict[str, np.ndarray],
        theory: Theory
    ) -> Dict:
        """Test risk prediction accuracy"""
        if 'volatility' not in data or 'predicted_volatility' not in data:
            return {'passed': False, 'score': 0.0}
        
        actual_vol = data['volatility']
        predicted_vol = data['predicted_volatility']
        
        # Calculate correlation
        if len(actual_vol) == len(predicted_vol) and len(actual_vol) > 1:
            correlation = np.corrcoef(actual_vol, predicted_vol)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
        else:
            correlation = 0.0
        
        passed = correlation > 0.3
        
        return {
            'passed': passed,
            'score': max(0.0, (correlation + 1) / 2),  # Normalize to 0-1
            'details': {'correlation': correlation}
        }
    
    def _test_market_timing(
        self,
        data: Dict[str, np.ndarray],
        theory: Theory
    ) -> Dict:
        """Test market timing ability"""
        # Simulate timing test using entry/exit signals
        if 'signals' not in data or 'prices' not in data:
            return {'passed': False, 'score': 0.0}
        
        signals = data['signals']
        prices = data['prices']
        
        # Calculate returns from following signals
        returns = []
        position = 0
        
        for i in range(len(signals) - 1):
            if signals[i] == 1:  # Buy signal
                position = 1
            elif signals[i] == -1:  # Sell signal
                position = 0
            
            if position == 1:
                ret = (prices[i + 1] - prices[i]) / prices[i]
                returns.append(ret)
        
        if not returns:
            return {'passed': False, 'score': 0.0}
        
        avg_return = np.mean(returns)
        sharpe = avg_return / (np.std(returns) + 1e-10) * np.sqrt(252)
        
        passed = sharpe > 0.5
        
        return {
            'passed': passed,
            'score': min(1.0, max(0.0, (sharpe + 2) / 4)),  # Normalize
            'details': {
                'sharpe_ratio': sharpe,
                'avg_return': avg_return,
                'trades': len(returns)
            }
        }
    
    def _test_cross_sectional(
        self,
        data: Dict[str, np.ndarray],
        theory: Theory
    ) -> Dict:
        """Test cross-sectional prediction ability"""
        # Test if theory ranks assets correctly
        if 'rankings' not in data or 'actual_returns' not in data:
            return {'passed': False, 'score': 0.0}
        
        predicted_rank = data['rankings']
        actual_returns = data['actual_returns']
        
        # Calculate rank correlation
        from scipy import stats
        
        if len(predicted_rank) == len(actual_returns) and len(predicted_rank) > 1:
            correlation, _ = stats.spearmanr(predicted_rank, actual_returns)
            if np.isnan(correlation):
                correlation = 0.0
        else:
            correlation = 0.0
        
        passed = correlation > 0.2
        
        return {
            'passed': passed,
            'score': max(0.0, (correlation + 1) / 2),
            'details': {'rank_correlation': correlation}
        }
    
    def get_validation_summary(self, theory_id: str) -> Optional[Dict]:
        """Get validation summary for a theory"""
        if theory_id not in self.theories:
            return None
        
        theory = self.theories[theory_id]
        tests = self.test_results.get(theory_id, [])
        
        return {
            'theory': theory.to_dict(),
            'tests_executed': len(tests),
            'tests_passed': sum(1 for t in tests if t.passed),
            'average_score': np.mean([t.score for t in tests]) if tests else 0.0,
            'validation_results': [{
                'test_name': t.test_name,
                'passed': t.passed,
                'score': t.score,
                'details': t.details
            } for t in tests]
        }
    
    def get_validated_theories(
        self,
        theory_type: Optional[TheoryType] = None,
        min_accuracy: float = 0.0
    ) -> List[Theory]:
        """Get theories that have been validated"""
        validated = [
            t for t in self.theories.values()
            if t.status in [ValidationStatus.VALIDATED, ValidationStatus.PARTIALLY_VALIDATED]
            and t.accuracy >= min_accuracy
        ]
        
        if theory_type:
            validated = [t for t in validated if t.theory_type == theory_type]
        
        validated.sort(key=lambda t: t.accuracy, reverse=True)
        
        return validated
    
    def get_applicable_trading_strategies(self, theory_id: str) -> List[Dict]:
        """Generate trading strategies from validated theory"""
        if theory_id not in self.theories:
            return []
        
        theory = self.theories[theory_id]
        
        if theory.status not in [ValidationStatus.VALIDATED, ValidationStatus.PARTIALLY_VALIDATED]:
            return []
        
        strategies = []
        
        # Generate strategies based on theory type
        if theory.theory_type == TheoryType.ASSET_PRICING:
            strategies.append({
                'name': f"{theory.name}_Factor_Strategy",
                'type': 'factor_investing',
                'description': f"Trade based on {theory.name} factor predictions",
                'expected_accuracy': theory.accuracy
            })
        
        elif theory.theory_type == TheoryType.MARKET_MICROSTRUCTURE:
            strategies.append({
                'name': f"{theory.name}_Timing_Strategy",
                'type': 'market_timing',
                'description': f"Use {theory.name} for entry/exit timing",
                'expected_accuracy': theory.accuracy
            })
        
        elif theory.theory_type == TheoryType.RISK_MODEL:
            strategies.append({
                'name': f"{theory.name}_Risk_Management",
                'type': 'risk_management',
                'description': f"Apply {theory.name} for position sizing",
                'expected_accuracy': theory.accuracy
            })
        
        return strategies
    
    def get_statistics(self) -> Dict:
        """Get validator statistics"""
        status_counts = defaultdict(int)
        for theory in self.theories.values():
            status_counts[theory.status.value] += 1
        
        return {
            **self.stats,
            'theories_by_status': dict(status_counts),
            'pending_validation': len(self.pending_validation),
            'avg_accuracy': np.mean([t.accuracy for t in self.theories.values()]) if self.theories else 0.0,
            'validated_theories': len([t for t in self.theories.values() 
                                     if t.status == ValidationStatus.VALIDATED])
        }
