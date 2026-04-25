"""
Walk-Forward Validation Framework.

Implements rigorous out-of-sample testing to prevent overfitting:
- Rolling window validation
- Anchored window validation
- Expanding window validation
- Statistical significance testing
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta

from .strategy_genome import StrategyGenome
from .backtesting_engine import LeakageFreeBacktester, BacktestResult
from .fitness_evaluator import MultiObjectiveFitness, FitnessScore


@dataclass
class WalkForwardPeriod:
    """Single walk-forward period"""
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    
    train_result: Optional[BacktestResult] = None
    test_result: Optional[BacktestResult] = None
    train_fitness: Optional[FitnessScore] = None
    test_fitness: Optional[FitnessScore] = None


@dataclass
class WalkForwardResult:
    """Complete walk-forward validation results"""
    periods: List[WalkForwardPeriod]
    
    avg_train_fitness: float
    avg_test_fitness: float
    fitness_degradation: float
    
    train_sharpe: float
    test_sharpe: float
    
    train_max_dd: float
    test_max_dd: float
    
    consistency_score: float
    overfitting_score: float
    
    is_statistically_significant: bool
    p_value: float


class WalkForwardValidator:
    """
    Walk-forward validation for strategy evaluation.
    
    Prevents overfitting by testing strategies on truly out-of-sample data.
    """
    
    def __init__(
        self,
        train_period_days: int = 252,
        test_period_days: int = 63,
        step_days: int = 21,
        min_periods: int = 3,
        validation_type: str = 'rolling'
    ):
        """
        Initialize walk-forward validator.
        
        Args:
            train_period_days: Length of training period
            test_period_days: Length of test period
            step_days: Step size between periods
            min_periods: Minimum number of periods required
            validation_type: 'rolling', 'anchored', or 'expanding'
        """
        self.train_period_days = train_period_days
        self.test_period_days = test_period_days
        self.step_days = step_days
        self.min_periods = min_periods
        self.validation_type = validation_type
    
    def validate(
        self,
        genome: StrategyGenome,
        data: pd.DataFrame,
        fitness_evaluator: MultiObjectiveFitness
    ) -> WalkForwardResult:
        """
        Perform walk-forward validation on a strategy genome.
        
        Args:
            genome: Strategy genome to validate
            data: Complete market data
            fitness_evaluator: Fitness evaluator
        
        Returns:
            WalkForwardResult with all validation metrics
        """
        periods = self._create_periods(data)
        
        if len(periods) < self.min_periods:
            return self._create_invalid_result(periods)
        
        for period in periods:
            self._evaluate_period(period, genome, data, fitness_evaluator)
        
        result = self._aggregate_results(periods)
        
        return result
    
    def _create_periods(self, data: pd.DataFrame) -> List[WalkForwardPeriod]:
        """Create walk-forward periods based on validation type"""
        periods = []
        
        start_date = data.index[0]
        end_date = data.index[-1]
        
        if self.validation_type == 'rolling':
            periods = self._create_rolling_periods(start_date, end_date)
        
        elif self.validation_type == 'anchored':
            periods = self._create_anchored_periods(start_date, end_date)
        
        elif self.validation_type == 'expanding':
            periods = self._create_expanding_periods(start_date, end_date)
        
        else:
            raise ValueError(f"Unknown validation type: {self.validation_type}")
        
        return periods
    
    def _create_rolling_periods(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[WalkForwardPeriod]:
        """Create rolling window periods"""
        periods = []
        
        current_date = start_date
        
        while True:
            train_start = current_date
            train_end = train_start + timedelta(days=self.train_period_days)
            test_start = train_end
            test_end = test_start + timedelta(days=self.test_period_days)
            
            if test_end > end_date:
                break
            
            period = WalkForwardPeriod(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end
            )
            periods.append(period)
            
            current_date += timedelta(days=self.step_days)
        
        return periods
    
    def _create_anchored_periods(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[WalkForwardPeriod]:
        """Create anchored window periods (fixed start date)"""
        periods = []
        
        train_start = start_date
        current_date = start_date + timedelta(days=self.train_period_days)
        
        while True:
            train_end = current_date
            test_start = train_end
            test_end = test_start + timedelta(days=self.test_period_days)
            
            if test_end > end_date:
                break
            
            period = WalkForwardPeriod(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end
            )
            periods.append(period)
            
            current_date += timedelta(days=self.step_days)
        
        return periods
    
    def _create_expanding_periods(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[WalkForwardPeriod]:
        """Create expanding window periods"""
        periods = []
        
        train_start = start_date
        current_date = start_date + timedelta(days=self.train_period_days)
        
        while True:
            train_end = current_date
            test_start = train_end
            test_end = test_start + timedelta(days=self.test_period_days)
            
            if test_end > end_date:
                break
            
            period = WalkForwardPeriod(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end
            )
            periods.append(period)
            
            current_date += timedelta(days=self.step_days)
        
        return periods
    
    def _evaluate_period(
        self,
        period: WalkForwardPeriod,
        genome: StrategyGenome,
        data: pd.DataFrame,
        fitness_evaluator: MultiObjectiveFitness
    ):
        """Evaluate a single walk-forward period"""
        train_data = data.loc[period.train_start:period.train_end]
        test_data = data.loc[period.test_start:period.test_end]
        
        if len(train_data) < 50 or len(test_data) < 20:
            return
        
        train_backtester = LeakageFreeBacktester(train_data)
        period.train_result = train_backtester.backtest(genome)
        period.train_fitness = fitness_evaluator.evaluate(
            period.train_result,
            genome.get_complexity(),
            train_data
        )
        
        test_backtester = LeakageFreeBacktester(test_data)
        period.test_result = test_backtester.backtest(genome)
        period.test_fitness = fitness_evaluator.evaluate(
            period.test_result,
            genome.get_complexity(),
            test_data
        )
    
    def _aggregate_results(self, periods: List[WalkForwardPeriod]) -> WalkForwardResult:
        """Aggregate results across all periods"""
        valid_periods = [p for p in periods if p.train_fitness and p.test_fitness]
        
        if not valid_periods:
            return self._create_invalid_result(periods)
        
        train_fitnesses = [p.train_fitness.total_fitness for p in valid_periods]
        test_fitnesses = [p.test_fitness.total_fitness for p in valid_periods]
        
        avg_train_fitness = np.mean(train_fitnesses)
        avg_test_fitness = np.mean(test_fitnesses)
        
        fitness_degradation = (avg_train_fitness - avg_test_fitness) / (avg_train_fitness + 1e-6)
        
        train_sharpes = [p.train_fitness.sharpe_ratio for p in valid_periods]
        test_sharpes = [p.test_fitness.sharpe_ratio for p in valid_periods]
        
        train_sharpe = np.mean(train_sharpes)
        test_sharpe = np.mean(test_sharpes)
        
        train_dds = [p.train_fitness.max_drawdown for p in valid_periods]
        test_dds = [p.test_fitness.max_drawdown for p in valid_periods]
        
        train_max_dd = np.mean(train_dds)
        test_max_dd = np.mean(test_dds)
        
        consistency_score = self._calculate_consistency(test_fitnesses)
        
        overfitting_score = self._calculate_overfitting_score(
            train_fitnesses, test_fitnesses
        )
        
        is_significant, p_value = self._test_significance(test_fitnesses)
        
        return WalkForwardResult(
            periods=valid_periods,
            avg_train_fitness=avg_train_fitness,
            avg_test_fitness=avg_test_fitness,
            fitness_degradation=fitness_degradation,
            train_sharpe=train_sharpe,
            test_sharpe=test_sharpe,
            train_max_dd=train_max_dd,
            test_max_dd=test_max_dd,
            consistency_score=consistency_score,
            overfitting_score=overfitting_score,
            is_statistically_significant=is_significant,
            p_value=p_value
        )
    
    def _calculate_consistency(self, test_fitnesses: List[float]) -> float:
        """Calculate consistency of test period performance"""
        if len(test_fitnesses) < 2:
            return 0.0
        
        positive_periods = sum(1 for f in test_fitnesses if f > 0)
        consistency = positive_periods / len(test_fitnesses)
        
        stability = 1.0 - (np.std(test_fitnesses) / (abs(np.mean(test_fitnesses)) + 1.0))
        
        return 0.6 * consistency + 0.4 * max(0, stability)
    
    def _calculate_overfitting_score(
        self,
        train_fitnesses: List[float],
        test_fitnesses: List[float]
    ) -> float:
        """
        Calculate overfitting score.
        
        Lower is better. Measures how much performance degrades out-of-sample.
        """
        if not train_fitnesses or not test_fitnesses:
            return 1.0
        
        avg_train = np.mean(train_fitnesses)
        avg_test = np.mean(test_fitnesses)
        
        if avg_train <= 0:
            return 1.0
        
        degradation = (avg_train - avg_test) / avg_train
        
        overfitting_score = np.clip(degradation, 0.0, 1.0)
        
        return overfitting_score
    
    def _test_significance(self, test_fitnesses: List[float]) -> Tuple[bool, float]:
        """
        Test statistical significance of test period results.
        
        Uses one-sample t-test against null hypothesis of zero fitness.
        """
        if len(test_fitnesses) < 3:
            return False, 1.0
        
        from scipy import stats
        
        t_stat, p_value = stats.ttest_1samp(test_fitnesses, 0.0)
        
        is_significant = (p_value < 0.05) and (np.mean(test_fitnesses) > 0)
        
        return is_significant, p_value
    
    def _create_invalid_result(self, periods: List[WalkForwardPeriod]) -> WalkForwardResult:
        """Create result for invalid validation"""
        return WalkForwardResult(
            periods=periods,
            avg_train_fitness=0.0,
            avg_test_fitness=0.0,
            fitness_degradation=1.0,
            train_sharpe=0.0,
            test_sharpe=0.0,
            train_max_dd=0.0,
            test_max_dd=0.0,
            consistency_score=0.0,
            overfitting_score=1.0,
            is_statistically_significant=False,
            p_value=1.0
        )
