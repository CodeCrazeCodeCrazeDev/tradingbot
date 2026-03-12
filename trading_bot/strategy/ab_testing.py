"""
A/B Strategy Testing
Randomized strategy assignment with statistical significance testing
"""

import asyncio
import logging
import random
import hashlib
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from scipy import stats

try:
    from statsmodels.stats.power import TTestIndPower
except ImportError:
    TTestIndPower = None

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """A/B test status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WinnerSelection(Enum):
    """Winner selection criteria"""
    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    MAX_DRAWDOWN = "max_drawdown"
    RISK_ADJUSTED = "risk_adjusted"


@dataclass
class StrategyVariant:
    """Strategy variant in A/B test"""
    variant_id: str
    name: str
    strategy_config: Dict[str, Any]
    allocation_pct: float = 0.5
    trades: List[Dict[str, Any]] = field(default_factory=list)
    returns: List[float] = field(default_factory=list)
    
    @property
    def total_return(self) -> float:
        return sum(self.returns) if self.returns else 0
    
    @property
    def win_rate(self) -> float:
        if not self.returns:
            return 0
        wins = sum(1 for r in self.returns if r > 0)
        return wins / len(self.returns)
    
    @property
    def sharpe_ratio(self) -> float:
        if not self.returns or len(self.returns) < 2:
            return 0
        mean_return = np.mean(self.returns)
        std_return = np.std(self.returns)
        return mean_return / std_return * np.sqrt(252) if std_return > 0 else 0
    
    @property
    def profit_factor(self) -> float:
        if not self.returns:
            return 0
        gross_profit = sum(r for r in self.returns if r > 0)
        gross_loss = abs(sum(r for r in self.returns if r < 0))
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    @property
    def max_drawdown(self) -> float:
        if not self.returns:
            return 0
        cumulative = np.cumsum(self.returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        return np.max(drawdown) if len(drawdown) > 0 else 0
    
    def get_metrics(self) -> Dict[str, float]:
        return {
            'total_return': self.total_return,
            'win_rate': self.win_rate,
            'sharpe_ratio': self.sharpe_ratio,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'trade_count': len(self.trades),
            'avg_return': np.mean(self.returns) if self.returns else 0
        }


@dataclass
class ABTestResult:
    """Result of A/B test analysis"""
    test_id: str
    control: StrategyVariant
    treatment: StrategyVariant
    metric: str
    control_value: float
    treatment_value: float
    difference: float
    difference_pct: float
    p_value: float
    confidence_level: float
    is_significant: bool
    winner: Optional[str]
    sample_size_control: int
    sample_size_treatment: int
    power: float
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_id': self.test_id,
            'control': self.control.name,
            'treatment': self.treatment.name,
            'metric': self.metric,
            'control_value': self.control_value,
            'treatment_value': self.treatment_value,
            'difference': self.difference,
            'difference_pct': self.difference_pct,
            'p_value': self.p_value,
            'confidence_level': self.confidence_level,
            'is_significant': self.is_significant,
            'winner': self.winner,
            'recommendation': self.recommendation
        }


@dataclass
class ABTest:
    """A/B test definition"""
    test_id: str
    name: str
    description: str
    control: StrategyVariant
    treatment: StrategyVariant
    status: TestStatus = TestStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    min_samples: int = 100
    max_duration_days: int = 30
    significance_level: float = 0.05
    winner_criteria: WinnerSelection = WinnerSelection.SHARPE_RATIO
    auto_select_winner: bool = True
    result: Optional[ABTestResult] = None


class ABTestingFramework:
    """
    A/B testing framework for trading strategies
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Active tests
        self.tests: Dict[str, ABTest] = {}
        self.completed_tests: List[ABTest] = []
        
        # Assignment tracking
        self.assignments: Dict[str, str] = {}  # trade_id -> variant_id
        
        # Configuration
        self.default_significance = self.config.get('significance_level', 0.05)
        self.min_effect_size = self.config.get('min_effect_size', 0.1)  # 10% improvement
        self.default_min_samples = self.config.get('min_samples', 100)
        
        logger.info("A/B testing framework initialized")
        
    def create_test(
        self,
        name: str,
        control_config: Dict[str, Any],
        treatment_config: Dict[str, Any],
        description: str = "",
        min_samples: int = None,
        significance_level: float = None,
        winner_criteria: WinnerSelection = WinnerSelection.SHARPE_RATIO
    ) -> ABTest:
        """
        Create a new A/B test
        """
        test_id = hashlib.md5(f"{name}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        control = StrategyVariant(
            variant_id=f"{test_id}_control",
            name=f"{name}_control",
            strategy_config=control_config
        )
        
        treatment = StrategyVariant(
            variant_id=f"{test_id}_treatment",
            name=f"{name}_treatment",
            strategy_config=treatment_config
        )
        
        test = ABTest(
            test_id=test_id,
            name=name,
            description=description,
            control=control,
            treatment=treatment,
            min_samples=min_samples or self.default_min_samples,
            significance_level=significance_level or self.default_significance,
            winner_criteria=winner_criteria
        )
        
        self.tests[test_id] = test
        logger.info(f"Created A/B test: {name} ({test_id})")
        
        return test
    
    def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        test = self.tests.get(test_id)
        if not test:
            return False
            
        if test.status != TestStatus.DRAFT:
            logger.warning(f"Test {test_id} is not in draft status")
            return False
            
        test.status = TestStatus.RUNNING
        test.started_at = datetime.now()
        
        logger.info(f"Started A/B test: {test.name}")
        return True
    
    def pause_test(self, test_id: str) -> bool:
        """Pause an A/B test"""
        test = self.tests.get(test_id)
        if not test or test.status != TestStatus.RUNNING:
            return False
            
        test.status = TestStatus.PAUSED
        logger.info(f"Paused A/B test: {test.name}")
        return True
    
    def resume_test(self, test_id: str) -> bool:
        """Resume a paused test"""
        test = self.tests.get(test_id)
        if not test or test.status != TestStatus.PAUSED:
            return False
            
        test.status = TestStatus.RUNNING
        logger.info(f"Resumed A/B test: {test.name}")
        return True
    
    def assign_variant(self, test_id: str, trade_id: str = None) -> Optional[StrategyVariant]:
        """
        Randomly assign a variant for a trade
        
        Args:
            test_id: Test to assign from
            trade_id: Optional trade ID for consistent assignment
        """
        test = self.tests.get(test_id)
        if not test or test.status != TestStatus.RUNNING:
            return None
            
        # Check if already assigned
        if trade_id and trade_id in self.assignments:
            variant_id = self.assignments[trade_id]
            if variant_id == test.control.variant_id:
                return test.control
            return test.treatment
            
        # Random assignment based on allocation
        if random.random() < test.control.allocation_pct:
            variant = test.control
        else:
            variant = test.treatment
            
        if trade_id:
            self.assignments[trade_id] = variant.variant_id
            
        return variant
    
    def record_trade(
        self,
        test_id: str,
        variant_id: str,
        trade_data: Dict[str, Any],
        return_pct: float
    ):
        """
        Record a trade result for a variant
        """
        test = self.tests.get(test_id)
        if not test:
            return
            
        if variant_id == test.control.variant_id:
            variant = test.control
        elif variant_id == test.treatment.variant_id:
            variant = test.treatment
        else:
            return
            
        variant.trades.append(trade_data)
        variant.returns.append(return_pct)
        
        # Check if test should be completed
        self._check_test_completion(test)
    
    def _check_test_completion(self, test: ABTest):
        """Check if test has enough data to complete"""
        if test.status != TestStatus.RUNNING:
            return
            
        control_n = len(test.control.returns)
        treatment_n = len(test.treatment.returns)
        
        # Check minimum samples
        if control_n >= test.min_samples and treatment_n >= test.min_samples:
            # Check for early stopping with significance
            result = self.analyze_test(test.test_id)
            if result and result.is_significant:
                if test.auto_select_winner:
                    self.complete_test(test.test_id)
                    
        # Check max duration
        if test.started_at:
            duration = (datetime.now() - test.started_at).days
            if duration >= test.max_duration_days:
                self.complete_test(test.test_id)
    
    def analyze_test(self, test_id: str) -> Optional[ABTestResult]:
        """
        Perform statistical analysis on test results
        """
        test = self.tests.get(test_id)
        if not test:
            return None
            
        control = test.control
        treatment = test.treatment
        
        if len(control.returns) < 2 or len(treatment.returns) < 2:
            return None
            
        # Get metric values based on winner criteria
        metric = test.winner_criteria.value
        control_metrics = control.get_metrics()
        treatment_metrics = treatment.get_metrics()
        
        control_value = control_metrics.get(metric, control.total_return)
        treatment_value = treatment_metrics.get(metric, treatment.total_return)
        
        # Perform t-test on returns
        t_stat, p_value = stats.ttest_ind(control.returns, treatment.returns)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(
            (np.var(control.returns) + np.var(treatment.returns)) / 2
        )
        effect_size = (np.mean(treatment.returns) - np.mean(control.returns)) / pooled_std if pooled_std > 0 else 0
        
        # Calculate statistical power
        power = self._calculate_power(
            len(control.returns), len(treatment.returns),
            effect_size, test.significance_level
        )
        
        # Determine significance
        is_significant = p_value < test.significance_level
        
        # Determine winner
        winner = None
        if is_significant:
            if treatment_value > control_value:
                winner = treatment.name
            else:
                winner = control.name
                
        # Generate recommendation
        recommendation = self._generate_recommendation(
            is_significant, winner, p_value, effect_size, power,
            len(control.returns), len(treatment.returns), test.min_samples
        )
        
        difference = treatment_value - control_value
        difference_pct = difference / abs(control_value) * 100 if control_value != 0 else 0
        
        result = ABTestResult(
            test_id=test_id,
            control=control,
            treatment=treatment,
            metric=metric,
            control_value=control_value,
            treatment_value=treatment_value,
            difference=difference,
            difference_pct=difference_pct,
            p_value=p_value,
            confidence_level=1 - p_value,
            is_significant=is_significant,
            winner=winner,
            sample_size_control=len(control.returns),
            sample_size_treatment=len(treatment.returns),
            power=power,
            recommendation=recommendation
        )
        
        test.result = result
        return result
    
    def _calculate_power(
        self,
        n1: int,
        n2: int,
        effect_size: float,
        alpha: float
    ) -> float:
        """Calculate statistical power"""
        try:
            analysis = TTestIndPower()
            power = analysis.solve_power(
                effect_size=abs(effect_size),
                nobs1=n1,
                ratio=n2/n1 if n1 > 0 else 1,
                alpha=alpha
            )
            return min(1.0, max(0.0, power))
        except Exception:
            # Approximate power calculation
            se = np.sqrt(2 / ((n1 + n2) / 2))
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            z_power = abs(effect_size) / se - z_alpha
            return stats.norm.cdf(z_power)
    
    def _generate_recommendation(
        self,
        is_significant: bool,
        winner: Optional[str],
        p_value: float,
        effect_size: float,
        power: float,
        n_control: int,
        n_treatment: int,
        min_samples: int
    ) -> str:
        """Generate recommendation based on analysis"""
        if n_control < min_samples or n_treatment < min_samples:
            return f"Continue test: Need more samples (control: {n_control}/{min_samples}, treatment: {n_treatment}/{min_samples})"
            
        if power < 0.8:
            return f"Continue test: Statistical power too low ({power:.1%}). Need more samples for reliable results."
            
        if is_significant:
            if abs(effect_size) >= self.min_effect_size:
                return f"ADOPT {winner}: Statistically significant with meaningful effect size ({effect_size:.2f})"
            else:
                return f"CONSIDER {winner}: Significant but small effect size ({effect_size:.2f}). May not be practically meaningful."
        else:
            if p_value < 0.1:
                return "Continue test: Approaching significance. More data may reveal a winner."
            else:
                return "No significant difference. Consider stopping test or trying different variants."
    
    def complete_test(self, test_id: str) -> Optional[ABTestResult]:
        """Complete a test and determine winner"""
        test = self.tests.get(test_id)
        if not test:
            return None
            
        result = self.analyze_test(test_id)
        
        test.status = TestStatus.COMPLETED
        test.ended_at = datetime.now()
        
        # Move to completed
        self.completed_tests.append(test)
        
        logger.info(f"Completed A/B test: {test.name}, Winner: {result.winner if result else 'None'}")
        
        return result
    
    def cancel_test(self, test_id: str):
        """Cancel a test"""
        test = self.tests.get(test_id)
        if test:
            test.status = TestStatus.CANCELLED
            test.ended_at = datetime.now()
            logger.info(f"Cancelled A/B test: {test.name}")
    
    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get current test status"""
        test = self.tests.get(test_id)
        if not test:
            return None
            
        control_metrics = test.control.get_metrics()
        treatment_metrics = test.treatment.get_metrics()
        
        return {
            'test_id': test_id,
            'name': test.name,
            'status': test.status.value,
            'started_at': test.started_at.isoformat() if test.started_at else None,
            'control': {
                'name': test.control.name,
                'samples': len(test.control.returns),
                **control_metrics
            },
            'treatment': {
                'name': test.treatment.name,
                'samples': len(test.treatment.returns),
                **treatment_metrics
            },
            'progress': {
                'control_pct': len(test.control.returns) / test.min_samples * 100,
                'treatment_pct': len(test.treatment.returns) / test.min_samples * 100
            }
        }
    
    def get_all_tests(self) -> List[Dict[str, Any]]:
        """Get all tests summary"""
        return [
            {
                'test_id': t.test_id,
                'name': t.name,
                'status': t.status.value,
                'control_samples': len(t.control.returns),
                'treatment_samples': len(t.treatment.returns),
                'winner': t.result.winner if t.result else None
            }
            for t in list(self.tests.values()) + self.completed_tests
        ]
    
    def calculate_required_sample_size(
        self,
        baseline_return: float,
        min_detectable_effect: float,
        baseline_std: float,
        alpha: float = 0.05,
        power: float = 0.8
    ) -> int:
        """
        Calculate required sample size for desired power
        """
        try:
            analysis = TTestIndPower()
            
            effect_size = min_detectable_effect / baseline_std if baseline_std > 0 else 0.5
            
            sample_size = analysis.solve_power(
                effect_size=effect_size,
                power=power,
                alpha=alpha,
                ratio=1.0
            )
            
            return int(np.ceil(sample_size))
        except Exception:
            # Approximate calculation
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            z_beta = stats.norm.ppf(power)
            effect_size = min_detectable_effect / baseline_std if baseline_std > 0 else 0.5
            
            n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
            return int(np.ceil(n))
