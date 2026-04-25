"""
Experiment Designer - Automated Research Experiment Design
============================================================

Implements automated experiment design for hypothesis testing:
1. Experimental design patterns (A/B, factorial, etc.)
2. Sample size calculation
3. Control variable selection
4. Metric definition
5. Statistical test selection

Based on the Foundation Agents paper (arXiv:2504.01990) research systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class ExperimentType(Enum):
    """Types of experiments"""
    AB_TEST = "ab_test"                  # Simple A/B comparison
    MULTIVARIATE = "multivariate"        # Multiple variables
    FACTORIAL = "factorial"              # Full factorial design
    FRACTIONAL_FACTORIAL = "fractional_factorial"
    TIME_SERIES = "time_series"          # Time-based experiment
    CROSS_SECTIONAL = "cross_sectional"  # Cross-asset comparison
    BACKTESTING = "backtesting"          # Historical simulation
    PAPER_TRADING = "paper_trading"      # Forward simulation
    LIVE_TRADING = "live_trading"        # Real trading


class StatisticalTest(Enum):
    """Statistical tests for hypothesis evaluation"""
    T_TEST = "t_test"
    WELCH_T_TEST = "welch_t_test"
    MANN_WHITNEY = "mann_whitney"
    ANOVA = "anova"
    CHI_SQUARE = "chi_square"
    REGRESSION = "regression"
    GRANGER_CAUSALITY = "granger_causality"
    COINTEGRATION = "cointegration"
    BOOTSTRAP = "bootstrap"
    PERMUTATION = "permutation"


class ExperimentStatus(Enum):
    """Status of an experiment"""
    DESIGNED = "designed"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    ANALYZING = "analyzing"
    CONCLUDED = "concluded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExperimentVariable:
    """A variable in an experiment"""
    name: str
    variable_type: str  # independent, dependent, control, confounding
    data_type: str      # continuous, categorical, binary
    
    # For independent variables
    levels: Optional[List[Any]] = None
    
    # For dependent variables
    measurement_method: Optional[str] = None
    
    # Constraints
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'variable_type': self.variable_type,
            'data_type': self.data_type,
            'levels': self.levels
        }


@dataclass
class ExperimentMetric:
    """A metric to measure in the experiment"""
    name: str
    description: str
    calculation: str  # How to calculate
    
    # Statistical properties
    expected_effect_size: float = 0.1
    minimum_detectable_effect: float = 0.05
    
    # Thresholds
    success_threshold: Optional[float] = None
    failure_threshold: Optional[float] = None
    
    # Priority
    primary: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'primary': self.primary,
            'expected_effect_size': self.expected_effect_size
        }


@dataclass
class ExperimentDesign:
    """Complete experiment design"""
    experiment_id: str
    name: str
    description: str
    
    # Hypothesis
    hypothesis_id: str
    hypothesis_statement: str
    
    # Type
    experiment_type: ExperimentType
    
    # Variables
    independent_vars: List[ExperimentVariable] = field(default_factory=list)
    dependent_vars: List[ExperimentVariable] = field(default_factory=list)
    control_vars: List[ExperimentVariable] = field(default_factory=list)
    
    # Metrics
    metrics: List[ExperimentMetric] = field(default_factory=list)
    primary_metric: Optional[str] = None
    
    # Sample
    sample_size: int = 100
    sample_method: str = "random"
    
    # Statistical
    statistical_test: StatisticalTest = StatisticalTest.T_TEST
    significance_level: float = 0.05
    power: float = 0.8
    
    # Duration
    duration: timedelta = field(default_factory=lambda: timedelta(days=30))
    warmup_period: timedelta = field(default_factory=lambda: timedelta(days=7))
    
    # Status
    status: ExperimentStatus = ExperimentStatus.DESIGNED
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    results: Dict[str, Any] = field(default_factory=dict)
    conclusion: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'hypothesis_id': self.hypothesis_id,
            'experiment_type': self.experiment_type.value,
            'status': self.status.value,
            'sample_size': self.sample_size,
            'statistical_test': self.statistical_test.value,
            'significance_level': self.significance_level,
            'duration_days': self.duration.days,
            'metrics': [m.to_dict() for m in self.metrics],
            'created_at': self.created_at.isoformat()
        }


class SampleSizeCalculator:
    """Calculate required sample sizes"""
    
    def calculate_for_t_test(
        self,
        effect_size: float,
        alpha: float = 0.05,
        power: float = 0.8,
        two_sided: bool = True
    ) -> int:
        """Calculate sample size for t-test"""
        from scipy import stats
        
        # Z-scores
        z_alpha = stats.norm.ppf(1 - alpha / (2 if two_sided else 1))
        z_beta = stats.norm.ppf(power)
        
        # Sample size per group
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        
        return int(np.ceil(n))
    
    def calculate_for_proportion(
        self,
        p1: float,
        p2: float,
        alpha: float = 0.05,
        power: float = 0.8
    ) -> int:
        """Calculate sample size for proportion comparison"""
        from scipy import stats
        
        p_pooled = (p1 + p2) / 2
        effect_size = abs(p1 - p2) / np.sqrt(p_pooled * (1 - p_pooled))
        
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        
        return int(np.ceil(n))
    
    def calculate_for_regression(
        self,
        r_squared: float,
        num_predictors: int,
        alpha: float = 0.05,
        power: float = 0.8
    ) -> int:
        """Calculate sample size for regression"""
        from scipy import stats
        
        f_squared = r_squared / (1 - r_squared)
        
        # Approximation
        z_alpha = stats.norm.ppf(1 - alpha)
        z_beta = stats.norm.ppf(power)
        
        n = ((z_alpha + z_beta) ** 2) / f_squared + num_predictors + 1
        
        return int(np.ceil(n))


class TestSelector:
    """Select appropriate statistical test"""
    
    def select_test(
        self,
        dependent_var_type: str,
        independent_var_type: str,
        num_groups: int = 2,
        paired: bool = False,
        normality_assumed: bool = True
    ) -> StatisticalTest:
        """Select appropriate statistical test"""
        
        if dependent_var_type == "continuous":
            if independent_var_type == "categorical":
                if num_groups == 2:
                    if normality_assumed:
                        return StatisticalTest.WELCH_T_TEST if not paired else StatisticalTest.T_TEST
                    else:
                        return StatisticalTest.MANN_WHITNEY
                else:
                    return StatisticalTest.ANOVA
            elif independent_var_type == "continuous":
                return StatisticalTest.REGRESSION
        
        elif dependent_var_type == "categorical":
            return StatisticalTest.CHI_SQUARE
        
        elif dependent_var_type == "time_series":
            if independent_var_type == "time_series":
                return StatisticalTest.GRANGER_CAUSALITY
        
        # Default
        return StatisticalTest.BOOTSTRAP


class ExperimentDesigner:
    """
    Experiment Designer
    
    Designs experiments to test hypotheses with proper
    statistical rigor and controls.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.sample_calculator = SampleSizeCalculator()
        self.test_selector = TestSelector()
        
        # Storage
        self.designs: Dict[str, ExperimentDesign] = {}
        self.design_history: List[ExperimentDesign] = []
        
        # Templates
        self.templates = self._initialize_templates()
        
        # Statistics
        self.stats = {
            'experiments_designed': 0,
            'experiments_completed': 0,
            'hypotheses_supported': 0,
            'hypotheses_rejected': 0
        }
        
        logger.info("Experiment Designer initialized")
    
    def _initialize_templates(self) -> Dict[str, Dict]:
        """Initialize experiment templates"""
        return {
            'alpha_test': {
                'experiment_type': ExperimentType.BACKTESTING,
                'metrics': [
                    ExperimentMetric(
                        name='sharpe_ratio',
                        description='Risk-adjusted returns',
                        calculation='mean(returns) / std(returns) * sqrt(252)',
                        primary=True
                    ),
                    ExperimentMetric(
                        name='total_return',
                        description='Total return over period',
                        calculation='sum(returns)'
                    ),
                    ExperimentMetric(
                        name='max_drawdown',
                        description='Maximum drawdown',
                        calculation='max(peak - trough)'
                    )
                ],
                'duration': timedelta(days=252),  # 1 year
                'statistical_test': StatisticalTest.BOOTSTRAP
            },
            'regime_detection': {
                'experiment_type': ExperimentType.TIME_SERIES,
                'metrics': [
                    ExperimentMetric(
                        name='regime_accuracy',
                        description='Accuracy of regime detection',
                        calculation='correct_predictions / total_predictions',
                        primary=True
                    ),
                    ExperimentMetric(
                        name='transition_detection',
                        description='Accuracy of transition detection',
                        calculation='detected_transitions / actual_transitions'
                    )
                ],
                'duration': timedelta(days=365),
                'statistical_test': StatisticalTest.CHI_SQUARE
            },
            'factor_analysis': {
                'experiment_type': ExperimentType.CROSS_SECTIONAL,
                'metrics': [
                    ExperimentMetric(
                        name='factor_return',
                        description='Return attributable to factor',
                        calculation='regression_coefficient',
                        primary=True
                    ),
                    ExperimentMetric(
                        name='information_ratio',
                        description='Factor information ratio',
                        calculation='alpha / tracking_error'
                    )
                ],
                'duration': timedelta(days=252),
                'statistical_test': StatisticalTest.REGRESSION
            }
        }
    
    def design_experiment(
        self,
        hypothesis_id: str,
        hypothesis_statement: str,
        hypothesis_type: str,
        independent_vars: List[str],
        dependent_vars: List[str],
        template: Optional[str] = None,
        custom_metrics: Optional[List[ExperimentMetric]] = None,
        duration_days: Optional[int] = None
    ) -> ExperimentDesign:
        """Design an experiment for a hypothesis"""
        
        # Get template if specified
        template_config = self.templates.get(template, {})
        
        # Determine experiment type
        experiment_type = template_config.get(
            'experiment_type',
            self._infer_experiment_type(hypothesis_type)
        )
        
        # Create variables
        ind_vars = [
            ExperimentVariable(
                name=var,
                variable_type='independent',
                data_type='continuous'
            )
            for var in independent_vars
        ]
        
        dep_vars = [
            ExperimentVariable(
                name=var,
                variable_type='dependent',
                data_type='continuous'
            )
            for var in dependent_vars
        ]
        
        # Get metrics
        metrics = custom_metrics or template_config.get('metrics', [])
        if not metrics:
            metrics = self._generate_default_metrics(dependent_vars)
        
        primary_metric = next(
            (m.name for m in metrics if m.primary),
            metrics[0].name if metrics else None
        )
        
        # Select statistical test
        statistical_test = template_config.get(
            'statistical_test',
            self.test_selector.select_test(
                dependent_var_type='continuous',
                independent_var_type='continuous' if len(independent_vars) == 1 else 'categorical'
            )
        )
        
        # Calculate sample size
        sample_size = self.sample_calculator.calculate_for_t_test(
            effect_size=0.3,  # Medium effect
            alpha=0.05,
            power=0.8
        )
        
        # Duration
        duration = timedelta(days=duration_days) if duration_days else template_config.get(
            'duration',
            timedelta(days=30)
        )
        
        # Create design
        design = ExperimentDesign(
            experiment_id=f"exp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(hypothesis_id.encode()).hexdigest()[:8]}",
            name=f"Experiment for {hypothesis_id}",
            description=f"Testing: {hypothesis_statement}",
            hypothesis_id=hypothesis_id,
            hypothesis_statement=hypothesis_statement,
            experiment_type=experiment_type,
            independent_vars=ind_vars,
            dependent_vars=dep_vars,
            metrics=metrics,
            primary_metric=primary_metric,
            sample_size=sample_size,
            statistical_test=statistical_test,
            duration=duration,
            tags=[hypothesis_type, template or 'custom']
        )
        
        # Store
        self.designs[design.experiment_id] = design
        self.design_history.append(design)
        self.stats['experiments_designed'] += 1
        
        logger.info(f"Designed experiment: {design.experiment_id}")
        
        return design
    
    def _infer_experiment_type(self, hypothesis_type: str) -> ExperimentType:
        """Infer experiment type from hypothesis type"""
        type_mapping = {
            'causal': ExperimentType.TIME_SERIES,
            'predictive': ExperimentType.BACKTESTING,
            'correlational': ExperimentType.CROSS_SECTIONAL,
            'comparative': ExperimentType.AB_TEST,
            'exploratory': ExperimentType.MULTIVARIATE
        }
        return type_mapping.get(hypothesis_type, ExperimentType.BACKTESTING)
    
    def _generate_default_metrics(self, dependent_vars: List[str]) -> List[ExperimentMetric]:
        """Generate default metrics for dependent variables"""
        metrics = []
        
        for i, var in enumerate(dependent_vars):
            metric = ExperimentMetric(
                name=f"{var}_effect",
                description=f"Effect on {var}",
                calculation=f"measure({var})",
                primary=(i == 0)
            )
            metrics.append(metric)
        
        return metrics
    
    def design_ab_test(
        self,
        hypothesis_id: str,
        treatment_description: str,
        control_description: str,
        primary_metric: str,
        expected_effect: float = 0.1,
        duration_days: int = 14
    ) -> ExperimentDesign:
        """Design a simple A/B test"""
        
        # Calculate sample size
        sample_size = self.sample_calculator.calculate_for_t_test(
            effect_size=expected_effect,
            alpha=0.05,
            power=0.8
        )
        
        design = ExperimentDesign(
            experiment_id=f"ab_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=f"A/B Test: {treatment_description[:50]}",
            description=f"Treatment: {treatment_description}\nControl: {control_description}",
            hypothesis_id=hypothesis_id,
            hypothesis_statement=f"Treatment ({treatment_description}) outperforms control",
            experiment_type=ExperimentType.AB_TEST,
            independent_vars=[
                ExperimentVariable(
                    name='treatment',
                    variable_type='independent',
                    data_type='binary',
                    levels=['control', 'treatment']
                )
            ],
            dependent_vars=[
                ExperimentVariable(
                    name=primary_metric,
                    variable_type='dependent',
                    data_type='continuous'
                )
            ],
            metrics=[
                ExperimentMetric(
                    name=primary_metric,
                    description=f"Primary metric: {primary_metric}",
                    calculation=f"measure({primary_metric})",
                    expected_effect_size=expected_effect,
                    primary=True
                )
            ],
            primary_metric=primary_metric,
            sample_size=sample_size,
            statistical_test=StatisticalTest.WELCH_T_TEST,
            duration=timedelta(days=duration_days),
            tags=['ab_test']
        )
        
        self.designs[design.experiment_id] = design
        self.stats['experiments_designed'] += 1
        
        return design
    
    def design_backtest(
        self,
        hypothesis_id: str,
        strategy_description: str,
        benchmark: str = "buy_and_hold",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        assets: Optional[List[str]] = None
    ) -> ExperimentDesign:
        """Design a backtesting experiment"""
        
        duration = timedelta(days=252)  # Default 1 year
        if start_date and end_date:
            duration = end_date - start_date
        
        design = ExperimentDesign(
            experiment_id=f"bt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=f"Backtest: {strategy_description[:50]}",
            description=f"Strategy: {strategy_description}\nBenchmark: {benchmark}",
            hypothesis_id=hypothesis_id,
            hypothesis_statement=f"Strategy outperforms {benchmark}",
            experiment_type=ExperimentType.BACKTESTING,
            independent_vars=[
                ExperimentVariable(
                    name='strategy',
                    variable_type='independent',
                    data_type='categorical',
                    levels=['strategy', benchmark]
                )
            ],
            dependent_vars=[
                ExperimentVariable(
                    name='returns',
                    variable_type='dependent',
                    data_type='continuous'
                )
            ],
            metrics=[
                ExperimentMetric(
                    name='sharpe_ratio',
                    description='Risk-adjusted returns',
                    calculation='mean(returns) / std(returns) * sqrt(252)',
                    primary=True
                ),
                ExperimentMetric(
                    name='total_return',
                    description='Total return',
                    calculation='prod(1 + returns) - 1'
                ),
                ExperimentMetric(
                    name='max_drawdown',
                    description='Maximum drawdown',
                    calculation='max(cummax(equity) - equity) / cummax(equity)'
                ),
                ExperimentMetric(
                    name='win_rate',
                    description='Percentage of winning trades',
                    calculation='sum(returns > 0) / count(returns)'
                )
            ],
            primary_metric='sharpe_ratio',
            sample_size=int(duration.days),
            statistical_test=StatisticalTest.BOOTSTRAP,
            duration=duration,
            warmup_period=timedelta(days=30),
            tags=['backtest', benchmark],
            metadata={
                'benchmark': benchmark,
                'assets': assets or [],
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        )
        
        self.designs[design.experiment_id] = design
        self.stats['experiments_designed'] += 1
        
        return design
    
    def get_experiment(self, experiment_id: str) -> Optional[ExperimentDesign]:
        """Get experiment by ID"""
        return self.designs.get(experiment_id)
    
    def update_status(
        self,
        experiment_id: str,
        status: ExperimentStatus,
        results: Optional[Dict] = None,
        conclusion: Optional[str] = None
    ):
        """Update experiment status"""
        if experiment_id not in self.designs:
            return
        
        design = self.designs[experiment_id]
        design.status = status
        
        if status == ExperimentStatus.RUNNING:
            design.started_at = datetime.utcnow()
        elif status == ExperimentStatus.COMPLETED:
            design.completed_at = datetime.utcnow()
            self.stats['experiments_completed'] += 1
        
        if results:
            design.results = results
        
        if conclusion:
            design.conclusion = conclusion
            if 'supported' in conclusion.lower():
                self.stats['hypotheses_supported'] += 1
            elif 'rejected' in conclusion.lower():
                self.stats['hypotheses_rejected'] += 1
    
    def get_experiments_by_status(self, status: ExperimentStatus) -> List[ExperimentDesign]:
        """Get experiments by status"""
        return [d for d in self.designs.values() if d.status == status]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get designer statistics"""
        return {
            **self.stats,
            'by_type': {
                et.value: len([d for d in self.designs.values() if d.experiment_type == et])
                for et in ExperimentType
            },
            'by_status': {
                es.value: len([d for d in self.designs.values() if d.status == es])
                for es in ExperimentStatus
            },
            'avg_sample_size': np.mean([d.sample_size for d in self.designs.values()]) if self.designs else 0
        }
