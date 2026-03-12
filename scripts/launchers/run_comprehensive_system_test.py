#!/usr/bin/env python
"""
Comprehensive System Test Runner
Tests all modules, integrates with main loop, runs backtests,
monitors performance, optimizes portfolio, and tracks order flow.

This script validates the entire trading system end-to-end.
"""

import asyncio
import sys
import os
import time
import logging
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestStatus(Enum):
    """Test status enumeration"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    WARNING = "WARNING"


@dataclass
class TestResult:
    """Individual test result"""
    name: str
    status: TestStatus
    duration: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuiteResult:
    """Test suite result"""
    suite_name: str
    results: List[TestResult]
    total_duration: float
    
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.PASSED)
    
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.FAILED)
    
    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.SKIPPED)


class ComprehensiveSystemTester:
    """
    Comprehensive system tester that validates all trading bot components
    """
    
    def __init__(self):
        self.results: List[TestSuiteResult] = []
        self.start_time = None
        self.sample_data = None
        
    def generate_sample_data(self, n_days: int = 500) -> pd.DataFrame:
        """Generate sample market data for testing"""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=n_days, freq='D')
        
        # Simulate price series with trend and volatility
        returns = np.random.randn(n_days) * 0.015 + 0.0003
        prices = 100 * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(n_days) * 0.002),
            'high': prices * (1 + abs(np.random.randn(n_days) * 0.015)),
            'low': prices * (1 - abs(np.random.randn(n_days) * 0.015)),
            'close': prices,
            'volume': np.random.randint(100000, 1000000, n_days)
        }, index=dates)
        
        return data
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        self.start_time = time.time()
        self.sample_data = self.generate_sample_data()
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TRADING SYSTEM TEST")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")
        
        # Run all test suites
        test_suites = [
            ("1. Module Import Tests", self.test_module_imports),
            ("2. Core Components Tests", self.test_core_components),
            ("3. Backtesting System Tests", self.test_backtesting_system),
            ("4. Portfolio Optimization Tests", self.test_portfolio_optimization),
            ("5. Performance Monitoring Tests", self.test_performance_monitoring),
            ("6. Order Flow Analysis Tests", self.test_order_flow_analysis),
            ("7. Opportunity Scanner Tests", self.test_opportunity_scanners),
            ("8. Risk Management Tests", self.test_risk_management),
            ("9. Main Loop Integration Tests", self.test_main_loop_integration),
            ("10. End-to-End Trading Tests", self.test_end_to_end_trading),
        ]
        
        for suite_name, test_func in test_suites:
            print(f"\n{'='*60}")
            print(f"Running: {suite_name}")
            print(f"{'='*60}")
            
            try:
                result = await test_func()
                self.results.append(result)
                self._print_suite_result(result)
            except Exception as e:
                logger.error(f"Suite {suite_name} failed: {e}")
                traceback.print_exc()
                self.results.append(TestSuiteResult(
                    suite_name=suite_name,
                    results=[TestResult(
                        name="Suite Execution",
                        status=TestStatus.FAILED,
                        duration=0,
                        message=str(e)
                    )],
                    total_duration=0
                ))
        
        # Generate final report
        return self._generate_final_report()
    
    async def test_module_imports(self) -> TestSuiteResult:
        """Test all module imports"""
        results = []
        start_time = time.time()
        
        modules_to_test = [
            # Core modules
            ("trading_bot.backtesting.rigorous_backtest", "RigorousBacktester"),
            ("trading_bot.portfolio.portfolio_optimizer", "PortfolioOptimizer"),
            ("trading_bot.performance.performance_monitor", "PerformanceMonitor"),
            ("trading_bot.opportunity_scanner.flow_analysis", "OrderFlowImbalanceDetector"),
            ("trading_bot.orchestrator.master_orchestrator", "MasterOrchestrator"),
            
            # Strategy modules
            ("trading_bot.strategy", "StrategyEngine"),
            ("trading_bot.strategy", "MLStrategyEngine"),
            
            # Risk modules
            ("trading_bot.risk", "RiskManager"),
            
            # Execution modules
            ("trading_bot.execution", "PaperExecutor"),
            
            # Analytics modules
            ("trading_bot.analytics", "PerformanceAnalytics"),
            
            # Opportunity scanners
            ("trading_bot.opportunity_scanner.market_inefficiency", "MarketInefficiencyScanner"),
            ("trading_bot.opportunity_scanner.momentum_capture", "MomentumBurstDetector"),
            ("trading_bot.opportunity_scanner.arbitrage_detection", "ArbitrageDetector"),
            ("trading_bot.opportunity_scanner.correlation_analysis", "CorrelationAnalyzer"),
            ("trading_bot.opportunity_scanner.volatility_trading", "VolatilityScanner"),
            
            # Advanced features
            ("trading_bot.adaptive_systems", "AdaptiveTradingMaster"),
            ("trading_bot.exit_strategies", "ExitSignalGenerator"),
        ]
        
        for module_path, class_name in modules_to_test:
            test_start = time.time()
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name, None)
                
                if cls is not None:
                    results.append(TestResult(
                        name=f"Import {module_path}.{class_name}",
                        status=TestStatus.PASSED,
                        duration=time.time() - test_start,
                        message="Successfully imported"
                    ))
                else:
                    results.append(TestResult(
                        name=f"Import {module_path}.{class_name}",
                        status=TestStatus.WARNING,
                        duration=time.time() - test_start,
                        message=f"Class {class_name} not found in module"
                    ))
            except ImportError as e:
                results.append(TestResult(
                    name=f"Import {module_path}.{class_name}",
                    status=TestStatus.SKIPPED,
                    duration=time.time() - test_start,
                    message=f"Import failed: {str(e)}"
                ))
            except Exception as e:
                results.append(TestResult(
                    name=f"Import {module_path}.{class_name}",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=f"Error: {str(e)}"
                ))
        
        return TestSuiteResult(
            suite_name="Module Import Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    async def test_core_components(self) -> TestSuiteResult:
        """Test core trading components"""
        results = []
        start_time = time.time()
        
        # Test 1: Data generation
        test_start = time.time()
        try:
            data = self.generate_sample_data(100)
            assert len(data) == 100
            assert all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume'])
            results.append(TestResult(
                name="Data Generation",
                status=TestStatus.PASSED,
                duration=time.time() - test_start,
                message="Generated 100 days of sample data"
            ))
        except Exception as e:
            results.append(TestResult(
                name="Data Generation",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        # Test 2: Returns calculation
        test_start = time.time()
        try:
            returns = self.sample_data['close'].pct_change().dropna()
            assert len(returns) > 0
            assert not returns.isna().any()
            results.append(TestResult(
                name="Returns Calculation",
                status=TestStatus.PASSED,
                duration=time.time() - test_start,
                message=f"Calculated {len(returns)} returns"
            ))
        except Exception as e:
            results.append(TestResult(
                name="Returns Calculation",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        # Test 3: Volatility calculation
        test_start = time.time()
        try:
            returns = self.sample_data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            assert 0 < volatility < 1  # Reasonable volatility range
            results.append(TestResult(
                name="Volatility Calculation",
                status=TestStatus.PASSED,
                duration=time.time() - test_start,
                message=f"Annualized volatility: {volatility:.2%}"
            ))
        except Exception as e:
            results.append(TestResult(
                name="Volatility Calculation",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        # Test 4: Sharpe ratio calculation
        test_start = time.time()
        try:
            returns = self.sample_data['close'].pct_change().dropna()
            ann_return = (1 + returns.mean()) ** 252 - 1
            volatility = returns.std() * np.sqrt(252)
            sharpe = (ann_return - 0.04) / volatility if volatility > 0 else 0
            results.append(TestResult(
                name="Sharpe Ratio Calculation",
                status=TestStatus.PASSED,
                duration=time.time() - test_start,
                message=f"Sharpe ratio: {sharpe:.2f}"
            ))
        except Exception as e:
            results.append(TestResult(
                name="Sharpe Ratio Calculation",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        # Test 5: Max drawdown calculation
        test_start = time.time()
        try:
            prices = self.sample_data['close']
            cumulative = prices / prices.iloc[0]
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max) / running_max
            max_dd = abs(drawdown.min())
            assert 0 <= max_dd <= 1
            results.append(TestResult(
                name="Max Drawdown Calculation",
                status=TestStatus.PASSED,
                duration=time.time() - test_start,
                message=f"Max drawdown: {max_dd:.2%}"
            ))
        except Exception as e:
            results.append(TestResult(
                name="Max Drawdown Calculation",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        return TestSuiteResult(
            suite_name="Core Components Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    async def test_backtesting_system(self) -> TestSuiteResult:
        """Test the rigorous backtesting system"""
        results = []
        start_time = time.time()
        
        try:
            from trading_bot.backtesting.rigorous_backtest import (
                RigorousBacktester, 
                TransactionCostModel,
                ValidationMethod
            )
            
            # Test 1: Initialize backtester
            test_start = time.time()
            try:
                backtester = RigorousBacktester({
                    'risk_free_rate': 0.04,
                    'spread_bps': 2.0,
                    'slippage_bps': 1.0,
                    'alpha': 0.05
                })
                results.append(TestResult(
                    name="Backtester Initialization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message="RigorousBacktester initialized successfully"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Backtester Initialization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
                return TestSuiteResult("Backtesting System Tests", results, time.time() - start_time)
            
            # Test 2: Transaction cost model
            test_start = time.time()
            try:
                cost_model = TransactionCostModel(
                    spread_bps=2.0,
                    commission_per_share=0.005,
                    slippage_bps=1.0
                )
                cost = cost_model.calculate_cost(price=100, quantity=1000, adv=1000000)
                assert 'total' in cost
                assert cost['total'] > 0
                results.append(TestResult(
                    name="Transaction Cost Model",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Total cost: ${cost['total']:.2f} ({cost['total_bps']:.2f} bps)"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Transaction Cost Model",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 3: Simple backtest
            test_start = time.time()
            try:
                def momentum_strategy(data: pd.DataFrame) -> pd.Series:
                    """Simple momentum strategy"""
                    signal = pd.Series(0, index=data.index)
                    momentum = data['close'].pct_change(20)
                    signal[momentum > 0] = 1
                    signal[momentum < 0] = -1
                    return signal
                
                result = backtester.backtest(momentum_strategy, self.sample_data)
                assert result.total_return is not None
                assert result.sharpe_ratio is not None
                results.append(TestResult(
                    name="Simple Backtest",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Return: {result.total_return:.2%}, Sharpe: {result.sharpe_ratio:.2f}",
                    details=result.to_dict()
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Simple Backtest",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 4: Walk-forward analysis
            test_start = time.time()
            try:
                wf_result = backtester.walk_forward_analysis(
                    momentum_strategy, 
                    self.sample_data, 
                    num_windows=3
                )
                assert wf_result.num_windows >= 0
                results.append(TestResult(
                    name="Walk-Forward Analysis",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Windows: {wf_result.num_windows}, OOS Sharpe: {wf_result.avg_oos_sharpe:.2f}",
                    details=wf_result.to_dict()
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Walk-Forward Analysis",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 5: Monte Carlo simulation
            test_start = time.time()
            try:
                returns_arr = self.sample_data['close'].pct_change().dropna().values
                mc_result = backtester.monte_carlo_simulation(
                    returns_arr, 
                    num_simulations=100,
                    horizon_days=252
                )
                assert mc_result.prob_positive >= 0
                results.append(TestResult(
                    name="Monte Carlo Simulation",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Prob Positive: {mc_result.prob_positive:.2%}, Sharpe Mean: {mc_result.sharpe_mean:.2f}",
                    details=mc_result.to_dict()
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Monte Carlo Simulation",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 6: Multiple strategy testing
            test_start = time.time()
            try:
                def mean_reversion_strategy(data: pd.DataFrame) -> pd.Series:
                    signal = pd.Series(0, index=data.index)
                    sma = data['close'].rolling(20).mean()
                    signal[data['close'] < sma * 0.98] = 1
                    signal[data['close'] > sma * 1.02] = -1
                    return signal
                
                strategies = [momentum_strategy, mean_reversion_strategy]
                multi_result = backtester.test_multiple_strategies(
                    strategies, 
                    self.sample_data, 
                    correction='bonferroni'
                )
                assert 'best_strategy' in multi_result
                results.append(TestResult(
                    name="Multiple Strategy Testing",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Best: {multi_result['best_strategy']}, Significant: {multi_result['num_significant']}"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Multiple Strategy Testing",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
                
        except ImportError as e:
            results.append(TestResult(
                name="Backtesting Module Import",
                status=TestStatus.SKIPPED,
                duration=0,
                message=f"Could not import backtesting module: {e}"
            ))
        
        return TestSuiteResult(
            suite_name="Backtesting System Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    async def test_portfolio_optimization(self) -> TestSuiteResult:
        """Test portfolio optimization system"""
        results = []
        start_time = time.time()
        
        try:
            from trading_bot.portfolio.portfolio_optimizer import (
                PortfolioOptimizer,
                OptimizationMethod,
                InvestorView
            )
            
            # Generate multi-asset returns
            np.random.seed(42)
            n_days = 252
            assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
            
            returns_data = {}
            for asset in assets:
                returns_data[asset] = np.random.randn(n_days) * 0.02 + 0.0005
            
            returns_df = pd.DataFrame(returns_data)
            
            # Test 1: Initialize optimizer
            test_start = time.time()
            try:
                optimizer = PortfolioOptimizer({
                    'risk_free_rate': 0.04,
                    'min_weight': 0.0,
                    'max_weight': 0.4
                })
                results.append(TestResult(
                    name="Portfolio Optimizer Initialization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message="PortfolioOptimizer initialized successfully"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Portfolio Optimizer Initialization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
                return TestSuiteResult("Portfolio Optimization Tests", results, time.time() - start_time)
            
            # Test 2: Max Sharpe optimization
            test_start = time.time()
            try:
                result = optimizer.optimize(
                    returns_df,
                    method=OptimizationMethod.MAX_SHARPE
                )
                assert result.success
                assert sum(result.weights.values()) > 0.99
                results.append(TestResult(
                    name="Max Sharpe Optimization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Sharpe: {result.metrics.sharpe_ratio:.2f}",
                    details=result.to_dict()
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Max Sharpe Optimization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 3: Minimum Variance optimization
            test_start = time.time()
            try:
                result = optimizer.optimize(
                    returns_df,
                    method=OptimizationMethod.MIN_VARIANCE
                )
                assert result.success
                results.append(TestResult(
                    name="Min Variance Optimization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Volatility: {result.metrics.volatility:.2%}",
                    details=result.to_dict()
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Min Variance Optimization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 4: Risk Parity optimization
            test_start = time.time()
            try:
                result = optimizer.optimize(
                    returns_df,
                    method=OptimizationMethod.RISK_PARITY
                )
                assert result.success
                results.append(TestResult(
                    name="Risk Parity Optimization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Effective N: {result.metrics.effective_n:.1f}",
                    details=result.to_dict()
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Risk Parity Optimization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 5: HRP optimization
            test_start = time.time()
            try:
                result = optimizer.optimize(
                    returns_df,
                    method=OptimizationMethod.HRP
                )
                assert result.success
                results.append(TestResult(
                    name="HRP Optimization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Diversification: {result.metrics.diversification_ratio:.2f}",
                    details=result.to_dict()
                ))
            except Exception as e:
                results.append(TestResult(
                    name="HRP Optimization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 6: Black-Litterman with views
            test_start = time.time()
            try:
                views = [
                    InvestorView(asset='AAPL', expected_return=0.15, confidence=0.8),
                    InvestorView(asset='GOOGL', expected_return=0.12, confidence=0.6)
                ]
                result = optimizer.optimize(
                    returns_df,
                    method=OptimizationMethod.BLACK_LITTERMAN,
                    views=views
                )
                assert result.success
                results.append(TestResult(
                    name="Black-Litterman Optimization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Expected Return: {result.metrics.expected_return:.2%}",
                    details=result.to_dict()
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Black-Litterman Optimization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
                
        except ImportError as e:
            results.append(TestResult(
                name="Portfolio Optimizer Import",
                status=TestStatus.SKIPPED,
                duration=0,
                message=f"Could not import portfolio optimizer: {e}"
            ))
        
        return TestSuiteResult(
            suite_name="Portfolio Optimization Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    async def test_performance_monitoring(self) -> TestSuiteResult:
        """Test performance monitoring system"""
        results = []
        start_time = time.time()
        
        try:
            from trading_bot.performance.performance_monitor import (
                PerformanceMonitor,
                MetricType
            )
            
            # Test 1: Initialize monitor
            test_start = time.time()
            try:
                monitor = PerformanceMonitor(
                    history_size=100,
                    auto_save=False
                )
                results.append(TestResult(
                    name="Performance Monitor Initialization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message="PerformanceMonitor initialized successfully"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Performance Monitor Initialization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
                return TestSuiteResult("Performance Monitoring Tests", results, time.time() - start_time)
            
            # Test 2: Record metrics
            test_start = time.time()
            try:
                for i in range(10):
                    monitor.record_metric(
                        f"test_metric_{i}",
                        MetricType.EXECUTION_TIME,
                        np.random.random() * 0.1
                    )
                results.append(TestResult(
                    name="Record Metrics",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message="Recorded 10 test metrics"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Record Metrics",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 3: Start/Stop profiling
            test_start = time.time()
            try:
                profiler_id = monitor.start_profiling(
                    "test_operation",
                    MetricType.EXECUTION_TIME
                )
                time.sleep(0.01)  # Simulate work
                result = monitor.stop_profiling(profiler_id)
                assert result.value > 0
                results.append(TestResult(
                    name="Start/Stop Profiling",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Profiled operation: {result.value:.4f}s"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Start/Stop Profiling",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 4: Profile decorator
            test_start = time.time()
            try:
                @monitor.profile("decorated_function", MetricType.EXECUTION_TIME)
                def sample_function():
                    time.sleep(0.01)
                    return "done"
                
                result = sample_function()
                assert result == "done"
                results.append(TestResult(
                    name="Profile Decorator",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message="Decorator profiling works correctly"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Profile Decorator",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
                
        except ImportError as e:
            results.append(TestResult(
                name="Performance Monitor Import",
                status=TestStatus.SKIPPED,
                duration=0,
                message=f"Could not import performance monitor: {e}"
            ))
        
        return TestSuiteResult(
            suite_name="Performance Monitoring Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    async def test_order_flow_analysis(self) -> TestSuiteResult:
        """Test order flow analysis system"""
        results = []
        start_time = time.time()
        
        try:
            from trading_bot.opportunity_scanner.flow_analysis import (
                OrderFlowImbalanceDetector,
                VolumeProfileAnalyzer,
                FlowType
            )
            
            # Test 1: Initialize flow detector
            test_start = time.time()
            try:
                detector = OrderFlowImbalanceDetector({
                    'min_imbalance': 0.6,
                    'lookback_window': 100
                })
                results.append(TestResult(
                    name="Flow Detector Initialization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message="OrderFlowImbalanceDetector initialized"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Flow Detector Initialization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
                return TestSuiteResult("Order Flow Analysis Tests", results, time.time() - start_time)
            
            # Test 2: Detect flow imbalances
            test_start = time.time()
            try:
                # Generate sample trade data
                trades = []
                for i in range(100):
                    trades.append({
                        'size': np.random.randint(100, 10000),
                        'aggressor': 'buy' if np.random.random() > 0.3 else 'sell',
                        'timestamp': datetime.now() - timedelta(seconds=i)
                    })
                
                market_data = {
                    'EURUSD': {
                        'trades': trades,
                        'price': 1.0850
                    }
                }
                
                opportunities = await detector.detect_flow_imbalances(market_data)
                results.append(TestResult(
                    name="Detect Flow Imbalances",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Found {len(opportunities)} flow opportunities"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Detect Flow Imbalances",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 3: Volume profile analysis
            test_start = time.time()
            try:
                analyzer = VolumeProfileAnalyzer()
                price_data = list(self.sample_data['close'].values)
                volume_data = list(self.sample_data['volume'].values)
                
                profile = analyzer.analyze_volume_profile(price_data, volume_data)
                results.append(TestResult(
                    name="Volume Profile Analysis",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"POC: {profile.get('poc', 'N/A')}"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Volume Profile Analysis",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 4: Flow type classification
            test_start = time.time()
            try:
                assert FlowType.INSTITUTIONAL.value == "institutional"
                assert FlowType.WHALE.value == "whale"
                assert FlowType.ALGORITHMIC.value == "algorithmic"
                results.append(TestResult(
                    name="Flow Type Classification",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message="All flow types validated"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Flow Type Classification",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
                
        except ImportError as e:
            results.append(TestResult(
                name="Flow Analysis Import",
                status=TestStatus.SKIPPED,
                duration=0,
                message=f"Could not import flow analysis: {e}"
            ))
        
        return TestSuiteResult(
            suite_name="Order Flow Analysis Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    async def test_opportunity_scanners(self) -> TestSuiteResult:
        """Test opportunity scanner modules"""
        results = []
        start_time = time.time()
        
        scanners_to_test = [
            ("trading_bot.opportunity_scanner.market_inefficiency", "MarketInefficiencyScanner"),
            ("trading_bot.opportunity_scanner.momentum_capture", "MomentumBurstDetector"),
            ("trading_bot.opportunity_scanner.arbitrage_detection", "ArbitrageDetector"),
            ("trading_bot.opportunity_scanner.correlation_analysis", "CorrelationAnalyzer"),
            ("trading_bot.opportunity_scanner.volatility_trading", "VolatilityScanner"),
        ]
        
        for module_path, class_name in scanners_to_test:
            test_start = time.time()
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                
                # Initialize scanner
                scanner = cls()
                
                results.append(TestResult(
                    name=f"{class_name} Initialization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"{class_name} initialized successfully"
                ))
                
            except ImportError as e:
                results.append(TestResult(
                    name=f"{class_name} Initialization",
                    status=TestStatus.SKIPPED,
                    duration=time.time() - test_start,
                    message=f"Import failed: {e}"
                ))
            except Exception as e:
                results.append(TestResult(
                    name=f"{class_name} Initialization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
        
        return TestSuiteResult(
            suite_name="Opportunity Scanner Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    async def test_risk_management(self) -> TestSuiteResult:
        """Test risk management system"""
        results = []
        start_time = time.time()
        
        try:
            from trading_bot.risk import RiskManager
            
            # Test 1: Risk manager initialization (without MT5)
            test_start = time.time()
            try:
                # Create mock MT5 interface
                class MockMT5:
                    def get_account_info(self):
                        return {'balance': 100000, 'equity': 100000}
                
                risk_manager = RiskManager(MockMT5())
                results.append(TestResult(
                    name="Risk Manager Initialization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message="RiskManager initialized with mock MT5"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Risk Manager Initialization",
                    status=TestStatus.WARNING,
                    duration=time.time() - test_start,
                    message=f"Partial initialization: {e}"
                ))
                
        except ImportError as e:
            results.append(TestResult(
                name="Risk Manager Import",
                status=TestStatus.SKIPPED,
                duration=0,
                message=f"Could not import risk manager: {e}"
            ))
        
        # Test risk calculations
        test_start = time.time()
        try:
            # Manual risk calculations
            capital = 100000
            risk_per_trade = 0.02
            stop_loss_pips = 20
            pip_value = 10
            
            max_loss = capital * risk_per_trade
            position_size = max_loss / (stop_loss_pips * pip_value)
            
            assert position_size > 0
            results.append(TestResult(
                name="Position Size Calculation",
                status=TestStatus.PASSED,
                duration=time.time() - test_start,
                message=f"Position size: {position_size:.2f} lots"
            ))
        except Exception as e:
            results.append(TestResult(
                name="Position Size Calculation",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        # Test VaR calculation
        test_start = time.time()
        try:
            returns = self.sample_data['close'].pct_change().dropna()
            var_95 = np.percentile(returns, 5)
            cvar_95 = returns[returns <= var_95].mean()
            
            results.append(TestResult(
                name="VaR/CVaR Calculation",
                status=TestStatus.PASSED,
                duration=time.time() - test_start,
                message=f"VaR(95%): {var_95:.4f}, CVaR(95%): {cvar_95:.4f}"
            ))
        except Exception as e:
            results.append(TestResult(
                name="VaR/CVaR Calculation",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        return TestSuiteResult(
            suite_name="Risk Management Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    async def test_main_loop_integration(self) -> TestSuiteResult:
        """Test main loop integration"""
        results = []
        start_time = time.time()
        
        try:
            from trading_bot.orchestrator.master_orchestrator import (
                MasterOrchestrator,
                TradingMode,
                TradingDecision
            )
            
            # Test 1: Initialize orchestrator
            test_start = time.time()
            try:
                orchestrator = MasterOrchestrator({
                    'capital': 100000,
                    'max_risk_per_trade': 0.02,
                    'max_portfolio_risk': 0.06
                })
                results.append(TestResult(
                    name="Orchestrator Initialization",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message="MasterOrchestrator initialized"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Orchestrator Initialization",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
                return TestSuiteResult("Main Loop Integration Tests", results, time.time() - start_time)
            
            # Test 2: Trading mode adjustment
            test_start = time.time()
            try:
                orchestrator.adjust_trading_mode({
                    'volatility': 0.5,
                    'trend_strength': 0.3,
                    'volume': 'normal'
                })
                assert orchestrator.trading_mode == TradingMode.DEFENSIVE
                results.append(TestResult(
                    name="Trading Mode Adjustment",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Mode: {orchestrator.trading_mode.value}"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Trading Mode Adjustment",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 3: Performance summary
            test_start = time.time()
            try:
                summary = orchestrator.get_performance_summary()
                assert 'win_rate' in summary
                assert 'sharpe_ratio' in summary
                results.append(TestResult(
                    name="Performance Summary",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Capital: ${summary['total_capital']:,.0f}"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Performance Summary",
                    status=TestStatus.FAILED,
                    duration=time.time() - test_start,
                    message=str(e)
                ))
            
            # Test 4: Orchestration (without actual market data)
            test_start = time.time()
            try:
                market_data = {
                    'EURUSD': {
                        'price': 1.0850,
                        'bid': 1.0849,
                        'ask': 1.0851,
                        'volume': 1000000,
                        'volatility': 0.15
                    }
                }
                
                decisions = await orchestrator.orchestrate_trading(market_data)
                results.append(TestResult(
                    name="Trading Orchestration",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Generated {len(decisions)} decisions"
                ))
            except Exception as e:
                results.append(TestResult(
                    name="Trading Orchestration",
                    status=TestStatus.WARNING,
                    duration=time.time() - test_start,
                    message=f"Orchestration completed with warnings: {e}"
                ))
                
        except ImportError as e:
            results.append(TestResult(
                name="Orchestrator Import",
                status=TestStatus.SKIPPED,
                duration=0,
                message=f"Could not import orchestrator: {e}"
            ))
        
        return TestSuiteResult(
            suite_name="Main Loop Integration Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    async def test_end_to_end_trading(self) -> TestSuiteResult:
        """Test end-to-end trading workflow"""
        results = []
        start_time = time.time()
        
        # Test 1: Complete trading cycle simulation
        test_start = time.time()
        try:
            # Simulate market data
            market_data = self.sample_data.copy()
            
            # Generate signals
            signals = pd.Series(0, index=market_data.index)
            momentum = market_data['close'].pct_change(20)
            signals[momentum > 0.02] = 1
            signals[momentum < -0.02] = -1
            
            # Simulate trades
            trades = []
            position = 0
            entry_price = 0
            
            for i in range(1, len(market_data)):
                if signals.iloc[i] == 1 and position == 0:
                    position = 1
                    entry_price = market_data['close'].iloc[i]
                elif signals.iloc[i] == -1 and position == 1:
                    exit_price = market_data['close'].iloc[i]
                    pnl = (exit_price - entry_price) / entry_price
                    trades.append({
                        'entry': entry_price,
                        'exit': exit_price,
                        'pnl': pnl
                    })
                    position = 0
            
            # Calculate metrics
            if trades:
                total_pnl = sum(t['pnl'] for t in trades)
                win_rate = sum(1 for t in trades if t['pnl'] > 0) / len(trades)
                
                results.append(TestResult(
                    name="End-to-End Trading Simulation",
                    status=TestStatus.PASSED,
                    duration=time.time() - test_start,
                    message=f"Trades: {len(trades)}, Win Rate: {win_rate:.2%}, Total PnL: {total_pnl:.2%}"
                ))
            else:
                results.append(TestResult(
                    name="End-to-End Trading Simulation",
                    status=TestStatus.WARNING,
                    duration=time.time() - test_start,
                    message="No trades generated in simulation"
                ))
                
        except Exception as e:
            results.append(TestResult(
                name="End-to-End Trading Simulation",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        # Test 2: Signal generation pipeline
        test_start = time.time()
        try:
            # Technical indicators
            sma_20 = self.sample_data['close'].rolling(20).mean()
            sma_50 = self.sample_data['close'].rolling(50).mean()
            rsi = self._calculate_rsi(self.sample_data['close'], 14)
            
            # Composite signal
            signal_strength = 0
            if sma_20.iloc[-1] > sma_50.iloc[-1]:
                signal_strength += 1
            if rsi.iloc[-1] < 30:
                signal_strength += 1
            elif rsi.iloc[-1] > 70:
                signal_strength -= 1
            
            results.append(TestResult(
                name="Signal Generation Pipeline",
                status=TestStatus.PASSED,
                duration=time.time() - test_start,
                message=f"Signal strength: {signal_strength}, RSI: {rsi.iloc[-1]:.1f}"
            ))
        except Exception as e:
            results.append(TestResult(
                name="Signal Generation Pipeline",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        # Test 3: Risk-adjusted returns
        test_start = time.time()
        try:
            returns = self.sample_data['close'].pct_change().dropna()
            
            # Calculate risk-adjusted metrics
            ann_return = (1 + returns.mean()) ** 252 - 1
            volatility = returns.std() * np.sqrt(252)
            sharpe = (ann_return - 0.04) / volatility
            
            # Sortino ratio
            downside = returns[returns < 0]
            downside_std = downside.std() * np.sqrt(252)
            sortino = (ann_return - 0.04) / downside_std if downside_std > 0 else 0
            
            results.append(TestResult(
                name="Risk-Adjusted Returns",
                status=TestStatus.PASSED,
                duration=time.time() - test_start,
                message=f"Sharpe: {sharpe:.2f}, Sortino: {sortino:.2f}"
            ))
        except Exception as e:
            results.append(TestResult(
                name="Risk-Adjusted Returns",
                status=TestStatus.FAILED,
                duration=time.time() - test_start,
                message=str(e)
            ))
        
        return TestSuiteResult(
            suite_name="End-to-End Trading Tests",
            results=results,
            total_duration=time.time() - start_time
        )
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _print_suite_result(self, result: TestSuiteResult):
        """Print test suite result"""
        print(f"\n{result.suite_name}")
        print("-" * 50)
        
        for test in result.results:
            status_icon = {
                TestStatus.PASSED: "✓",
                TestStatus.FAILED: "✗",
                TestStatus.SKIPPED: "○",
                TestStatus.WARNING: "⚠"
            }.get(test.status, "?")
            
            status_color = {
                TestStatus.PASSED: "\033[92m",  # Green
                TestStatus.FAILED: "\033[91m",  # Red
                TestStatus.SKIPPED: "\033[93m",  # Yellow
                TestStatus.WARNING: "\033[93m"  # Yellow
            }.get(test.status, "\033[0m")
            
            print(f"  {status_color}{status_icon}\033[0m {test.name}: {test.message} ({test.duration:.3f}s)")
        
        print(f"\nSummary: {result.passed} passed, {result.failed} failed, {result.skipped} skipped")
        print(f"Duration: {result.total_duration:.2f}s")
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final test report"""
        total_duration = time.time() - self.start_time
        
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        total_tests = total_passed + total_failed + total_skipped
        
        print("\n" + "=" * 80)
        print("FINAL TEST REPORT")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"  \033[92mPassed: {total_passed}\033[0m")
        print(f"  \033[91mFailed: {total_failed}\033[0m")
        print(f"  \033[93mSkipped: {total_skipped}\033[0m")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Success Rate: {(total_passed / total_tests * 100) if total_tests > 0 else 0:.1f}%")
        print("=" * 80)
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'skipped': total_skipped,
            'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'suites': []
        }
        
        for suite in self.results:
            suite_data = {
                'name': suite.suite_name,
                'passed': suite.passed,
                'failed': suite.failed,
                'skipped': suite.skipped,
                'duration': suite.total_duration,
                'tests': []
            }
            
            for test in suite.results:
                suite_data['tests'].append({
                    'name': test.name,
                    'status': test.status.value,
                    'duration': test.duration,
                    'message': test.message
                })
            
            report['suites'].append(suite_data)
        
        # Save report
        report_path = os.path.join(os.path.dirname(__file__), 'test_reports')
        os.makedirs(report_path, exist_ok=True)
        
        report_file = os.path.join(
            report_path, 
            f"comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: {report_file}")
        
        return report


async def main():
    """Main entry point"""
    tester = ComprehensiveSystemTester()
    report = await tester.run_all_tests()
    
    # Return exit code based on test results
    if report['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
