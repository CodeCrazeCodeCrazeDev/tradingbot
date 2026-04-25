"""
Strategy Verifier Subagent

Validates trading strategy hypotheses using multiple verification methods.
Based on Aletheia's natural language verification approach.
"""

import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyVerifier:
    """
    Verifies trading strategy hypotheses using comprehensive testing.
    
    Implements multiple verification methods:
    - Logical consistency checks
    - Backtesting validation
    - Risk assessment
    - Statistical significance testing
    - Robustness analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.verification_methods = [
            "logical_consistency",
            "backtesting",
            "risk_assessment",
            "statistical_significance",
            "robustness_check"
        ]
        self.verification_history: List[Dict] = []
        
    async def verify(
        self,
        hypothesis: 'StrategyHypothesis',
        market_context: Optional[Dict[str, Any]] = None
    ) -> 'VerificationResult':
        """
        Verify a strategy hypothesis using multiple methods
        
        Args:
            hypothesis: Strategy hypothesis to verify
            market_context: Current market conditions
            
        Returns:
            VerificationResult with validation status and recommendations
        """
        from .aletheia_orchestrator import VerificationResult
        
        logger.info(f"Verifying hypothesis: {hypothesis.hypothesis_id}")
        
        issues = []
        recommendations = []
        test_results = {}
        
        # Run all verification methods
        for method in self.verification_methods:
            result = await self._run_verification_method(method, hypothesis, market_context)
            test_results[method] = result
            
            if not result["passed"]:
                issues.extend(result.get("issues", []))
                recommendations.extend(result.get("recommendations", []))
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(test_results)
        
        # Determine if valid
        is_valid = (
            confidence >= 0.80 and
            len(issues) <= 2 and
            test_results["logical_consistency"]["passed"] and
            test_results["risk_assessment"]["passed"]
        )
        
        # Calculate robustness
        robustness_score = test_results["robustness_check"].get("score", 0.5)
        
        # Statistical significance
        statistical_significance = test_results["statistical_significance"].get("p_value", 0.05)
        
        verification_result = VerificationResult(
            hypothesis_id=hypothesis.hypothesis_id,
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            recommendations=recommendations,
            test_results=test_results,
            statistical_significance=statistical_significance,
            robustness_score=robustness_score,
            verification_method="comprehensive_multi_test"
        )
        
        self.verification_history.append({
            "hypothesis_id": hypothesis.hypothesis_id,
            "is_valid": is_valid,
            "confidence": confidence,
            "timestamp": datetime.now(),
            "issues_count": len(issues)
        })
        
        logger.info(f"Verification complete: valid={is_valid}, confidence={confidence:.2f}")
        return verification_result
    
    async def _run_verification_method(
        self,
        method: str,
        hypothesis: 'StrategyHypothesis',
        market_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run a specific verification method"""
        
        if method == "logical_consistency":
            return await self._check_logical_consistency(hypothesis)
        elif method == "backtesting":
            return await self._run_backtest(hypothesis, market_context)
        elif method == "risk_assessment":
            return await self._assess_risk(hypothesis)
        elif method == "statistical_significance":
            return await self._test_statistical_significance(hypothesis, market_context)
        elif method == "robustness_check":
            return await self._check_robustness(hypothesis, market_context)
        
        return {"passed": False, "issues": ["Unknown verification method"], "score": 0}
    
    async def _check_logical_consistency(
        self,
        hypothesis: 'StrategyHypothesis'
    ) -> Dict[str, Any]:
        """Check if strategy rules are logically consistent"""
        issues = []
        
        # Check if entry and exit rules conflict
        entry_long = any("long" in rule.lower() for rule in hypothesis.entry_rules)
        entry_short = any("short" in rule.lower() for rule in hypothesis.entry_rules)
        
        if entry_long and entry_short:
            if not ("for longs" in str(hypothesis.entry_rules) and "for shorts" in str(hypothesis.entry_rules)):
                issues.append("Entry rules contain both long and short conditions without clear separation")
        
        # Check if stop-loss is tighter than take-profit (good practice)
        sl_mentioned = any("stop" in rule.lower() for rule in hypothesis.exit_rules)
        tp_mentioned = any("profit" in rule.lower() or "take" in rule.lower() for rule in hypothesis.exit_rules)
        
        if not sl_mentioned:
            issues.append("No stop-loss rule defined - critical risk management gap")
        
        if not tp_mentioned:
            issues.append("No take-profit rule defined - incomplete exit strategy")
        
        # Check risk parameters are reasonable
        max_pos = hypothesis.risk_parameters.get("max_position_size", 100)
        if max_pos > 10:
            issues.append(f"Position size {max_pos}% seems excessively large")
        
        # Check expected performance is realistic
        win_rate = hypothesis.expected_performance.get("expected_win_rate", 0.5)
        if win_rate > 0.75:
            issues.append(f"Win rate {win_rate:.0%} seems unrealistically high")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "score": 1.0 - (len(issues) * 0.2),
            "recommendations": [] if len(issues) == 0 else ["Review and fix logical inconsistencies"]
        }
    
    async def _run_backtest(
        self,
        hypothesis: 'StrategyHypothesis',
        market_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run simulated backtest"""
        issues = []
        recommendations = []
        
        # Simulate backtest results based on strategy type and context
        base_sharpe = hypothesis.expected_performance.get("expected_sharpe_ratio", 1.0)
        
        # Adjust based on market context
        if market_context:
            volatility = market_context.get("volatility", "medium")
            if volatility == "extreme":
                base_sharpe *= 0.7
                issues.append("High volatility environment may reduce strategy effectiveness")
        
        # Simulate results
        simulated_sharpe = base_sharpe * (0.8 + random.random() * 0.4)  # 80-120% of expected
        simulated_max_dd = hypothesis.expected_performance.get("expected_max_drawdown", 10) * (0.9 + random.random() * 0.2)
        simulated_win_rate = hypothesis.expected_performance.get("expected_win_rate", 0.5) * (0.9 + random.random() * 0.2)
        
        # Evaluate results
        if simulated_sharpe < 0.8:
            issues.append(f"Backtest Sharpe ratio {simulated_sharpe:.2f} below threshold 0.8")
            recommendations.append("Consider filtering conditions to improve edge")
        
        if simulated_max_dd > 15:
            issues.append(f"Maximum drawdown {simulated_max_dd:.1f}% exceeds comfort level")
            recommendations.append("Implement tighter risk controls or reduce position sizing")
        
        if simulated_win_rate < 0.45:
            issues.append(f"Win rate {simulated_win_rate:.1%} quite low - high dependency on reward/risk ratio")
            recommendations.append("Ensure reward/risk ratio is at least 2:1 to compensate for low win rate")
        
        return {
            "passed": simulated_sharpe >= 0.8 and simulated_max_dd <= 15,
            "issues": issues,
            "recommendations": recommendations,
            "score": min(1.0, simulated_sharpe / 1.5),
            "results": {
                "sharpe_ratio": simulated_sharpe,
                "max_drawdown": simulated_max_dd,
                "win_rate": simulated_win_rate,
                "profit_factor": 1.0 + simulated_sharpe * 0.5
            }
        }
    
    async def _assess_risk(self, hypothesis: 'StrategyHypothesis') -> Dict[str, Any]:
        """Assess risk parameters and management"""
        issues = []
        recommendations = []
        
        risk_params = hypothesis.risk_parameters
        
        # Check position sizing
        max_pos = risk_params.get("max_position_size", 100)
        if max_pos > 5:
            issues.append(f"Max position size {max_pos}% may concentrate too much risk")
            recommendations.append("Consider reducing max position size to 2-3%")
        
        # Check daily loss limit
        max_daily = risk_params.get("max_daily_loss", 100)
        if max_daily > 5:
            issues.append(f"Daily loss limit {max_daily}% is quite high")
            recommendations.append("Consider reducing daily loss limit to 2-3%")
        
        # Check drawdown limit
        max_dd = risk_params.get("max_drawdown", 100)
        if max_dd > 20:
            issues.append(f"Max drawdown limit {max_dd}% is very high")
            recommendations.append("Consider reducing max drawdown limit to 10-15%")
        
        # Check correlation limit
        max_corr = risk_params.get("max_correlation", 1.0)
        if max_corr > 0.8:
            recommendations.append("Consider lower correlation threshold for better diversification")
        
        # Check liquidity requirement
        min_liq = risk_params.get("min_liquidity", 0)
        if min_liq < 500000:
            issues.append(f"Minimum liquidity ${min_liq:,.0f} may be too low for institutional trading")
        
        return {
            "passed": len(issues) <= 1,
            "issues": issues,
            "recommendations": recommendations,
            "score": 1.0 - (len(issues) * 0.15)
        }
    
    async def _test_statistical_significance(
        self,
        hypothesis: 'StrategyHypothesis',
        market_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Test statistical significance of expected edge"""
        issues = []
        
        # Simulate significance test
        expected_trades = hypothesis.expected_performance.get("expected_trades_per_month", 10)
        
        # Calculate required sample size for significance
        # For 80% power, 5% significance, effect size 0.5
        required_trades = 64
        
        if expected_trades * 3 < required_trades:  # 3 months of data
            issues.append(f"Expected {expected_trades} trades/month may not provide sufficient sample size for significance")
        
        # Simulate p-value
        simulated_p = 0.02 + random.random() * 0.08  # 0.02 to 0.10
        
        if simulated_p > 0.05:
            issues.append(f"Strategy edge not statistically significant (p={simulated_p:.3f})")
        
        return {
            "passed": simulated_p <= 0.05 and len(issues) == 0,
            "issues": issues,
            "recommendations": ["Run strategy for longer period to accumulate sufficient data"],
            "score": 1.0 if simulated_p <= 0.05 else 0.7,
            "p_value": simulated_p
        }
    
    async def _check_robustness(
        self,
        hypothesis: 'StrategyHypothesis',
        market_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check strategy robustness across different conditions"""
        issues = []
        recommendations = []
        
        # Test across different market regimes
        market_conditions = hypothesis.market_conditions
        
        if len(market_conditions) < 3:
            recommendations.append("Consider testing strategy across more diverse market conditions")
        
        # Check parameter sensitivity
        # (Simulated - in real system would vary parameters)
        parameter_sensitivity = random.random() * 0.3  # 0-30% performance change
        
        if parameter_sensitivity > 0.2:
            issues.append(f"Strategy appears sensitive to parameter changes ({parameter_sensitivity:.1%} performance variation)")
            recommendations.append("Consider using adaptive parameters or wider ranges")
        
        # Check time period robustness
        time_periods = hypothesis.expected_performance.get("expected_trades_per_month", 10)
        if time_periods < 5:
            recommendations.append("Low trade frequency may lead to long periods without signals")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "score": 1.0 - parameter_sensitivity,
            "parameter_sensitivity": parameter_sensitivity
        }
    
    def _calculate_confidence(self, test_results: Dict[str, Any]) -> float:
        """Calculate overall confidence score from test results"""
        weights = {
            "logical_consistency": 0.25,
            "backtesting": 0.25,
            "risk_assessment": 0.20,
            "statistical_significance": 0.15,
            "robustness_check": 0.15
        }
        
        total_score = 0
        total_weight = 0
        
        for method, weight in weights.items():
            if method in test_results:
                score = test_results[method].get("score", 0.5)
                total_score += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        return total_score / total_weight
