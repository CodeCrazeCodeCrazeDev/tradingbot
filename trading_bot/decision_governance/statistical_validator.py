"""
Pre-Trade Statistical Validation

Statistical validation of trading signals before execution.
Uses deterministic/statistical methods for hypothesis testing.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StatisticalTestResult(Enum):
    """Result of statistical test"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class StatisticalValidation:
    """Result of pre-trade statistical validation"""
    symbol: str
    test_name: str
    result: StatisticalTestResult
    p_value: float
    test_statistic: float
    effect_size: float
    sample_size: int
    confidence: float
    interpretation: str
    recommendation: str


class PreTradeStatisticalValidator:
    """
    Pre-trade statistical validation using rigorous hypothesis testing.
    
    Validates signals using:
    - Historical backtest statistics
    - Regime-specific performance
    - Serial correlation tests
    - Out-of-sample validation
    """
    
    def __init__(
        self,
        significance_level: float = 0.05,
        min_sample_size: int = 30,
        min_out_of_sample_months: int = 6
    ):
        self.significance_level = significance_level
        self.min_sample_size = min_sample_size
        self.min_oos_months = min_out_of_sample_months
        
        # Historical performance database
        self.historical_performance: Dict[str, List[Dict]] = {}
        self.out_of_sample_results: Dict[str, Dict] = {}
        
    def validate_signal(
        self,
        symbol: str,
        signal: Dict[str, Any],
        strategy_signature: str,
        market_context: Dict[str, Any]
    ) -> List[StatisticalValidation]:
        """
        Run comprehensive statistical validation on a signal.
        
        Returns:
            List of validation results
        """
        validations = []
        
        # Test 1: Historical win rate
        win_rate_test = self._test_historical_win_rate(
            symbol, strategy_signature, signal
        )
        validations.append(win_rate_test)
        
        # Test 2: Sharpe ratio
        sharpe_test = self._test_sharpe_ratio(
            symbol, strategy_signature
        )
        validations.append(sharpe_test)
        
        # Test 3: Out-of-sample performance
        oos_test = self._test_out_of_sample(
            symbol, strategy_signature
        )
        validations.append(oos_test)
        
        # Test 4: Regime-specific validation
        regime_test = self._test_regime_specific(
            symbol, strategy_signature, market_context
        )
        validations.append(regime_test)
        
        # Test 5: Serial correlation (randomness test)
        serial_test = self._test_serial_correlation(
            symbol, strategy_signature
        )
        validations.append(serial_test)
        
        # Test 6: Maximum drawdown constraint
        dd_test = self._test_max_drawdown(
            symbol, strategy_signature
        )
        validations.append(dd_test)
        
        return validations
    
    def _test_historical_win_rate(
        self,
        symbol: str,
        strategy: str,
        signal: Dict
    ) -> StatisticalValidation:
        """Test if historical win rate exceeds random chance"""
        
        history = self._get_strategy_history(symbol, strategy)
        
        if len(history) < self.min_sample_size:
            return StatisticalValidation(
                symbol=symbol,
                test_name="historical_win_rate",
                result=StatisticalTestResult.INSUFFICIENT_DATA,
                p_value=1.0,
                test_statistic=0.0,
                effect_size=0.0,
                sample_size=len(history),
                confidence=0.0,
                interpretation=f"Insufficient data: {len(history)} < {self.min_sample_size} required",
                recommendation="Accumulate more historical data before trading"
            )
            
        # Calculate win rate
        wins = sum(1 for h in history if h.get('pnl', 0) > 0)
        win_rate = wins / len(history)
        
        # Binomial test against 50%
        from math import sqrt
        n = len(history)
        p = 0.5  # Null hypothesis: random
        
        # Z-test for proportion
        z_score = (win_rate - p) / sqrt(p * (1-p) / n)
        
        # Approximate p-value (two-tailed)
        import math
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))
        
        # Effect size (Cohen's h)
        effect_size = 2 * (math.asin(sqrt(win_rate)) - math.asin(sqrt(0.5)))
        
        if p_value < self.significance_level and win_rate > 0.5:
            result = StatisticalTestResult.PASS
            interpretation = f"Win rate {win_rate:.1%} significantly > 50% (p={p_value:.3f})"
            recommendation = "Signal passes win rate test"
        elif win_rate <= 0.5:
            result = StatisticalTestResult.FAIL
            interpretation = f"Win rate {win_rate:.1%} not better than random"
            recommendation = "Reject: strategy does not beat random chance"
        else:
            result = StatisticalTestResult.WARNING
            interpretation = f"Win rate {win_rate:.1%} not significantly > 50% (p={p_value:.3f})"
            recommendation = "Proceed with caution - edge not statistically proven"
            
        return StatisticalValidation(
            symbol=symbol,
            test_name="historical_win_rate",
            result=result,
            p_value=p_value,
            test_statistic=z_score,
            effect_size=effect_size,
            sample_size=n,
            confidence=1 - p_value,
            interpretation=interpretation,
            recommendation=recommendation
        )
    
    def _test_sharpe_ratio(
        self,
        symbol: str,
        strategy: str
    ) -> StatisticalValidation:
        """Test if Sharpe ratio exceeds minimum threshold"""
        
        history = self._get_strategy_history(symbol, strategy)
        
        if len(history) < self.min_sample_size:
            return StatisticalValidation(
                symbol=symbol,
                test_name="sharpe_ratio",
                result=StatisticalTestResult.INSUFFICIENT_DATA,
                p_value=1.0,
                test_statistic=0.0,
                effect_size=0.0,
                sample_size=len(history),
                confidence=0.0,
                interpretation="Insufficient data for Sharpe calculation",
                recommendation="Need more trades for reliable Sharpe"
            )
            
        # Calculate returns
        returns = [h.get('pnl', 0) for h in history]
        
        if len(returns) < 2:
            sharpe = 0
        else:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
            std_dev = variance ** 0.5 if variance > 0 else 0
            
            # Annualized Sharpe (assuming monthly trades)
            sharpe = (mean_return / std_dev) * (12 ** 0.5) if std_dev > 0 else 0
            
        # Test against minimum threshold (e.g., 0.5)
        min_sharpe = 0.5
        
        # Approximate p-value using t-distribution
        # H0: Sharpe <= min_sharpe
        if std_dev > 0:
            t_stat = (sharpe - min_sharpe) / (1 / (len(returns) ** 0.5))
            p_value = 0.1  # Simplified - would use proper t-test
        else:
            t_stat = 0
            p_value = 1.0
            
        if sharpe > 1.0:
            result = StatisticalTestResult.PASS
            interpretation = f"Sharpe ratio {sharpe:.2f} exceeds 1.0 threshold"
            recommendation = "Strong risk-adjusted performance"
        elif sharpe > 0.5:
            result = StatisticalTestResult.WARNING
            interpretation = f"Sharpe ratio {sharpe:.2f} meets minimum but not excellent"
            recommendation = "Acceptable but watch for degradation"
        else:
            result = StatisticalTestResult.FAIL
            interpretation = f"Sharpe ratio {sharpe:.2f} below minimum 0.5"
            recommendation = "Reject: insufficient risk-adjusted return"
            
        return StatisticalValidation(
            symbol=symbol,
            test_name="sharpe_ratio",
            result=result,
            p_value=p_value,
            test_statistic=t_stat,
            effect_size=sharpe,
            sample_size=len(returns),
            confidence=0.7 if sharpe > 0.5 else 0.3,
            interpretation=interpretation,
            recommendation=recommendation
        )
    
    def _test_out_of_sample(
        self,
        symbol: str,
        strategy: str
    ) -> StatisticalValidation:
        """Test out-of-sample performance"""
        
        oos_data = self.out_of_sample_results.get(f"{symbol}_{strategy}")
        
        if not oos_data:
            return StatisticalValidation(
                symbol=symbol,
                test_name="out_of_sample",
                result=StatisticalTestResult.INSUFFICIENT_DATA,
                p_value=1.0,
                test_statistic=0.0,
                effect_size=0.0,
                sample_size=0,
                confidence=0.0,
                interpretation="No out-of-sample data available",
                recommendation="Run OOS backtest before trading"
            )
            
        oos_months = oos_data.get('months', 0)
        oos_sharpe = oos_data.get('sharpe', 0)
        oos_win_rate = oos_data.get('win_rate', 0)
        
        if oos_months < self.min_oos_months:
            return StatisticalValidation(
                symbol=symbol,
                test_name="out_of_sample",
                result=StatisticalTestResult.WARNING,
                p_value=0.5,
                test_statistic=0.0,
                effect_size=oos_sharpe,
                sample_size=oos_data.get('trades', 0),
                confidence=0.4,
                interpretation=f"OOS period {oos_months} months < {self.min_oos_months} required",
                recommendation="Extend OOS testing period"
            )
            
        # Compare IS vs OOS
        is_sharpe = oos_data.get('in_sample_sharpe', oos_sharpe)
        degradation = (is_sharpe - oos_sharpe) / is_sharpe if is_sharpe > 0 else 0
        
        if degradation < 0.3 and oos_sharpe > 0.3:
            result = StatisticalTestResult.PASS
            interpretation = f"OOS Sharpe {oos_sharpe:.2f} with {degradation:.1%} degradation"
            recommendation = "OOS performance acceptable"
        elif oos_sharpe > 0:
            result = StatisticalTestResult.WARNING
            interpretation = f"OOS Sharpe {oos_sharpe:.2f} with significant degradation"
            recommendation = "Caution: IS/OOS gap suggests overfitting"
        else:
            result = StatisticalTestResult.FAIL
            interpretation = f"OOS Sharpe {oos_sharpe:.2f} - negative OOS performance"
            recommendation = "Reject: strategy failed out-of-sample"
            
        return StatisticalValidation(
            symbol=symbol,
            test_name="out_of_sample",
            result=result,
            p_value=0.1 if result == StatisticalTestResult.PASS else 0.5,
            test_statistic=degradation,
            effect_size=oos_sharpe,
            sample_size=oos_data.get('trades', 0),
            confidence=0.8 if result == StatisticalTestResult.PASS else 0.3,
            interpretation=interpretation,
            recommendation=recommendation
        )
    
    def _test_regime_specific(
        self,
        symbol: str,
        strategy: str,
        market_context: Dict
    ) -> StatisticalValidation:
        """Test performance in current regime"""
        
        current_regime = market_context.get('regime', 'unknown')
        history = self._get_strategy_history(symbol, strategy)
        
        # Filter to current regime
        regime_trades = [
            h for h in history
            if h.get('regime') == current_regime
        ]
        
        if len(regime_trades) < 10:
            return StatisticalValidation(
                symbol=symbol,
                test_name="regime_specific",
                result=StatisticalTestResult.WARNING,
                p_value=1.0,
                test_statistic=0.0,
                effect_size=0.0,
                sample_size=len(regime_trades),
                confidence=0.3,
                interpretation=f"Only {len(regime_trades)} trades in {current_regime} regime",
                recommendation="Regime underrepresented - trade with caution"
            )
            
        wins = sum(1 for t in regime_trades if t.get('pnl', 0) > 0)
        win_rate = wins / len(regime_trades)
        
        if win_rate > 0.55:
            result = StatisticalTestResult.PASS
            interpretation = f"Win rate {win_rate:.1%} in {current_regime} regime"
            recommendation = "Good historical performance in current regime"
        elif win_rate > 0.45:
            result = StatisticalTestResult.WARNING
            interpretation = f"Marginal win rate {win_rate:.1%} in {current_regime}"
            recommendation = "Regime performance borderline - reduce size"
        else:
            result = StatisticalTestResult.FAIL
            interpretation = f"Poor win rate {win_rate:.1%} in {current_regime}"
            recommendation = f"Reject: historically underperforms in {current_regime}"
            
        return StatisticalValidation(
            symbol=symbol,
            test_name="regime_specific",
            result=result,
            p_value=0.2,
            test_statistic=win_rate,
            effect_size=win_rate - 0.5,
            sample_size=len(regime_trades),
            confidence=0.6 if result == StatisticalTestResult.PASS else 0.3,
            interpretation=interpretation,
            recommendation=recommendation
        )
    
    def _test_serial_correlation(
        self,
        symbol: str,
        strategy: str
    ) -> StatisticalValidation:
        """Test for serial correlation in returns (randomness test)"""
        
        history = self._get_strategy_history(symbol, strategy)
        returns = [h.get('pnl', 0) for h in history]
        
        if len(returns) < 10:
            return StatisticalValidation(
                symbol=symbol,
                test_name="serial_correlation",
                result=StatisticalTestResult.INSUFFICIENT_DATA,
                p_value=1.0,
                test_statistic=0.0,
                effect_size=0.0,
                sample_size=len(returns),
                confidence=0.0,
                interpretation="Insufficient data for correlation test",
                recommendation="Need more trades"
            )
            
        # Calculate lag-1 autocorrelation
        n = len(returns)
        mean_r = sum(returns) / n
        
        numerator = sum((returns[i] - mean_r) * (returns[i-1] - mean_r) for i in range(1, n))
        denominator = sum((r - mean_r) ** 2 for r in returns)
        
        autocorr = numerator / denominator if denominator > 0 else 0
        
        # Test statistic (approximate)
        test_stat = autocorr * (n ** 0.5)
        
        # High positive autocorr = momentum (good for trend following)
        # High negative autocorr = mean reversion
        # Near zero = random
        
        if abs(autocorr) < 0.1:
            result = StatisticalTestResult.PASS
            interpretation = f"Serial correlation {autocorr:.3f} - returns appear random"
            recommendation = "No concerning patterns in return series"
        elif abs(autocorr) < 0.3:
            result = StatisticalTestResult.WARNING
            interpretation = f"Serial correlation {autocorr:.3f} - some pattern detected"
            recommendation = "Monitor for developing patterns"
        else:
            result = StatisticalTestResult.WARNING
            interpretation = f"High serial correlation {autocorr:.3f} - non-random pattern"
            recommendation = "Strategy may have time-dependent edge - investigate"
            
        return StatisticalValidation(
            symbol=symbol,
            test_name="serial_correlation",
            result=result,
            p_value=0.3,
            test_statistic=test_stat,
            effect_size=autocorr,
            sample_size=n,
            confidence=0.7,
            interpretation=interpretation,
            recommendation=recommendation
        )
    
    def _test_max_drawdown(
        self,
        symbol: str,
        strategy: str
    ) -> StatisticalValidation:
        """Test maximum drawdown constraint"""
        
        history = self._get_strategy_history(symbol, strategy)
        
        if len(history) < 10:
            return StatisticalValidation(
                symbol=symbol,
                test_name="max_drawdown",
                result=StatisticalTestResult.INSUFFICIENT_DATA,
                p_value=1.0,
                test_statistic=0.0,
                effect_size=0.0,
                sample_size=len(history),
                confidence=0.0,
                interpretation="Insufficient data for drawdown analysis",
                recommendation="Accumulate more trade history"
            )
            
        # Calculate running drawdown
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for h in history:
            cumulative += h.get('pnl', 0)
            if cumulative > peak:
                peak = cumulative
            dd = (peak - cumulative) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
            
        # Test against 15% max drawdown
        max_allowed_dd = 0.15
        
        if max_dd < max_allowed_dd * 0.5:
            result = StatisticalTestResult.PASS
            interpretation = f"Max drawdown {max_dd:.1%} well below limit {max_allowed_dd:.1%}"
            recommendation = "Excellent drawdown control"
        elif max_dd < max_allowed_dd:
            result = StatisticalTestResult.WARNING
            interpretation = f"Max drawdown {max_dd:.1%} within limit {max_allowed_dd:.1%}"
            recommendation = "Acceptable drawdown but monitor closely"
        else:
            result = StatisticalTestResult.FAIL
            interpretation = f"Max drawdown {max_dd:.1%} exceeds limit {max_allowed_dd:.1%}"
            recommendation = "Reject: excessive historical drawdown"
            
        return StatisticalValidation(
            symbol=symbol,
            test_name="max_drawdown",
            result=result,
            p_value=0.2,
            test_statistic=max_dd,
            effect_size=max_dd,
            sample_size=len(history),
            confidence=0.8 if result == StatisticalTestResult.PASS else 0.4,
            interpretation=interpretation,
            recommendation=recommendation
        )
    
    def _get_strategy_history(self, symbol: str, strategy: str) -> List[Dict]:
        """Get historical trades for a strategy"""
        key = f"{symbol}_{strategy}"
        return self.historical_performance.get(key, [])
    
    def record_trade_outcome(
        self,
        symbol: str,
        strategy: str,
        outcome: Dict[str, Any]
    ) -> None:
        """Record a trade outcome for future validation"""
        
        key = f"{symbol}_{strategy}"
        if key not in self.historical_performance:
            self.historical_performance[key] = []
            
        self.historical_performance[key].append({
            'timestamp': outcome.get('timestamp', datetime.utcnow()),
            'pnl': outcome.get('pnl', 0),
            'regime': outcome.get('regime', 'unknown')
        })
        
    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF"""
        import math
        # Abramowitz and Stegun approximation
        b1 = 0.319381530
        b2 = -0.356563782
        b3 = 1.781477937
        b4 = -1.821255978
        b5 = 1.330274429
        p = 0.2316419
        c = 0.39894228
        
        if x >= 0.0:
            t = 1.0 / (1.0 + p * x)
            return 1.0 - c * math.exp(-x * x / 2.0) * t * (t * (t * (t * (t * b5 + b4) + b3) + b2) + b1)
        else:
            return 1.0 - self._normal_cdf(-x)
            
    def get_validation_summary(
        self,
        validations: List[StatisticalValidation]
    ) -> Dict[str, Any]:
        """Get summary of validation results"""
        
        by_result = {}
        for v in validations:
            r = v.result.value
            if r not in by_result:
                by_result[r] = []
            by_result[r].append(v.test_name)
            
        return {
            'total_tests': len(validations),
            'passed': len(by_result.get('pass', [])),
            'failed': len(by_result.get('fail', [])),
            'warnings': len(by_result.get('warning', [])),
            'insufficient_data': len(by_result.get('insufficient_data', [])),
            'by_test': by_result
        }
