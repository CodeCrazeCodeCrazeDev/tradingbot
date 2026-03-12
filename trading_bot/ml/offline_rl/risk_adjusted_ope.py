"""
Risk-Adjusted Offline Policy Evaluation

Evaluates policies using CVaR (Conditional Value at Risk) and other risk metrics.
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
try:
    from scipy import stats
except ImportError:
    scipy = None
import numpy

logger = logging.getLogger(__name__)


class CVaRPolicyEvaluator:
    """
    CVaR-based policy evaluation for risk-adjusted performance.
    
    CVaR measures the expected loss in the worst α% of cases.
    """
    
    def __init__(self, alpha: float = 0.05, discount: float = 0.99):
        """
        Initialize CVaR evaluator.
        
        Args:
            alpha: Confidence level (0.05 = worst 5%)
            discount: Reward discount factor
        """
        self.alpha = alpha
        self.discount = discount
        
        logger.info(f"CVaR evaluator initialized with alpha={alpha}")
    
    def evaluate(self, dataset, policy) -> Dict[str, float]:
        """
        Evaluate policy with CVaR and other risk metrics.
        
        Args:
            dataset: Dataset to evaluate on
            policy: Policy to evaluate
        
        Returns:
            Dictionary of risk metrics
        """
        # Get episode returns
        episode_returns = self._compute_episode_returns(dataset, policy)
        
        if len(episode_returns) == 0:
            logger.warning("No episodes found in dataset")
            return {
                'mean_return': 0.0,
                'cvar': 0.0,
                'var': 0.0,
                'std': 0.0,
                'sharpe': 0.0,
                'sortino': 0.0,
                'max_drawdown': 0.0
            }
        
        # Compute metrics
        mean_return = np.mean(episode_returns)
        std_return = np.std(episode_returns)
        
        # Value at Risk (VaR)
        var = np.percentile(episode_returns, self.alpha * 100)
        
        # Conditional Value at Risk (CVaR)
        cvar = np.mean(episode_returns[episode_returns <= var])
        
        # Sharpe ratio (assuming risk-free rate = 0)
        sharpe = mean_return / std_return if std_return > 0 else 0.0
        
        # Sortino ratio (downside deviation)
        downside_returns = episode_returns[episode_returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1e-8
        sortino = mean_return / downside_std
        
        # Maximum drawdown
        cumulative_returns = np.cumsum(episode_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / (running_max + 1e-8)
        max_drawdown = np.min(drawdown)
        
        metrics = {
            'mean_return': float(mean_return),
            'cvar': float(cvar),
            'var': float(var),
            'std': float(std_return),
            'sharpe': float(sharpe),
            'sortino': float(sortino),
            'max_drawdown': float(max_drawdown),
            'min_return': float(np.min(episode_returns)),
            'max_return': float(np.max(episode_returns)),
            'median_return': float(np.median(episode_returns))
        }
        
        logger.info(f"Policy evaluation: Mean={mean_return:.4f}, CVaR={cvar:.4f}, Sharpe={sharpe:.4f}")
        
        return metrics
    
    def _compute_episode_returns(self, dataset, policy) -> np.ndarray:
        """
        Compute episode returns under policy.
        
        Args:
            dataset: Dataset to evaluate on
            policy: Policy to evaluate
        
        Returns:
            Array of episode returns
        """
        states = dataset.states
        actions = dataset.actions
        rewards = dataset.rewards
        dones = dataset.dones
        
        # Get policy actions
        policy_actions = policy.predict_batch(states)
        
        # Compute returns for episodes where policy matches behavior
        episode_returns = []
        current_return = 0.0
        discount_factor = 1.0
        
        for i in range(len(states)):
            # Only count if policy would take same action
            if policy_actions[i] == actions[i]:
                current_return += discount_factor * rewards[i]
                discount_factor *= self.discount
            
            if dones[i]:
                if current_return != 0.0:  # Only add if policy was followed
                    episode_returns.append(current_return)
                current_return = 0.0
                discount_factor = 1.0
        
        return np.array(episode_returns)
    
    def is_safe_policy(
        self,
        metrics: Dict[str, float],
        min_mean_return: float = 0.0,
        max_cvar: float = -0.1,
        min_sharpe: float = 0.5,
        max_drawdown: float = -0.2
    ) -> Tuple[bool, List[str]]:
        """
        Check if policy meets safety criteria.
        
        Args:
            metrics: Policy metrics from evaluate()
            min_mean_return: Minimum acceptable mean return
            max_cvar: Maximum acceptable CVaR (negative value)
            min_sharpe: Minimum acceptable Sharpe ratio
            max_drawdown: Maximum acceptable drawdown (negative value)
        
        Returns:
            Tuple of (is_safe, list of violations)
        """
        violations = []
        
        if metrics['mean_return'] < min_mean_return:
            violations.append(f"Mean return {metrics['mean_return']:.4f} < {min_mean_return}")
        
        if metrics['cvar'] < max_cvar:
            violations.append(f"CVaR {metrics['cvar']:.4f} < {max_cvar}")
        
        if metrics['sharpe'] < min_sharpe:
            violations.append(f"Sharpe {metrics['sharpe']:.4f} < {min_sharpe}")
        
        if metrics['max_drawdown'] < max_drawdown:
            violations.append(f"Max drawdown {metrics['max_drawdown']:.4f} < {max_drawdown}")
        
        is_safe = len(violations) == 0
        
        if is_safe:
            logger.info("✅ Policy passed all safety checks")
        else:
            logger.warning(f"❌ Policy failed safety checks: {', '.join(violations)}")
        
        return is_safe, violations


class RiskAdjustedPolicySelector:
    """
    Selects best policy based on risk-adjusted metrics.
    
    Combines multiple risk metrics with configurable weights.
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        alpha: float = 0.05
    ):
        """
        Initialize risk-adjusted selector.
        
        Args:
            weights: Weights for each metric (default: equal weights)
            alpha: CVaR confidence level
        """
        self.weights = weights or {
            'mean_return': 0.3,
            'sharpe': 0.3,
            'sortino': 0.2,
            'cvar': 0.2  # Negative, so higher (less negative) is better
        }
        
        self.evaluator = CVaRPolicyEvaluator(alpha=alpha)
        
        logger.info(f"Risk-adjusted selector initialized with weights: {self.weights}")
    
    def select_best_policy(
        self,
        dataset,
        policies: Dict[str, Any],
        safety_thresholds: Optional[Dict[str, float]] = None
    ) -> Tuple[str, Dict[str, Dict[str, float]]]:
        """
        Select best policy based on risk-adjusted score.
        
        Args:
            dataset: Dataset to evaluate on
            policies: Dictionary of policies
            safety_thresholds: Safety thresholds for filtering
        
        Returns:
            Tuple of (best_policy_name, all_metrics)
        """
        all_metrics = {}
        safe_policies = {}
        
        # Evaluate all policies
        for policy_name, policy in policies.items():
            logger.info(f"Evaluating policy: {policy_name}")
            
            metrics = self.evaluator.evaluate(dataset, policy)
            all_metrics[policy_name] = metrics
            
            # Check safety
            if safety_thresholds:
                is_safe, violations = self.evaluator.is_safe_policy(metrics, **safety_thresholds)
                
                if is_safe:
                    safe_policies[policy_name] = metrics
                else:
                    logger.warning(f"Policy {policy_name} excluded due to safety violations")
            else:
                safe_policies[policy_name] = metrics
        
        if len(safe_policies) == 0:
            logger.error("No safe policies found!")
            return None, all_metrics
        
        # Compute risk-adjusted scores
        scores = {}
        
        for policy_name, metrics in safe_policies.items():
            score = 0.0
            
            for metric_name, weight in self.weights.items():
                if metric_name in metrics:
                    # Normalize metric (simple z-score across policies)
                    values = [m[metric_name] for m in safe_policies.values()]
                    mean_val = np.mean(values)
                    std_val = np.std(values) if np.std(values) > 0 else 1.0
                    
                    normalized = (metrics[metric_name] - mean_val) / std_val
                    score += weight * normalized
            
            scores[policy_name] = score
        
        # Select best
        best_policy = max(scores, key=scores.get)
        
        logger.info(f"✅ Best policy selected: {best_policy} (score: {scores[best_policy]:.4f})")
        logger.info(f"   Metrics: {safe_policies[best_policy]}")
        
        return best_policy, all_metrics
    
    def compare_policies(
        self,
        all_metrics: Dict[str, Dict[str, float]]
    ) -> str:
        """
        Generate comparison report.
        
        Args:
            all_metrics: Metrics for all policies
        
        Returns:
            Markdown report
        """
        report = "# Risk-Adjusted Policy Comparison\n\n"
        report += "## Metrics Summary\n\n"
        
        # Create table
        metrics_list = ['mean_return', 'cvar', 'sharpe', 'sortino', 'max_drawdown']
        
        report += "| Policy | " + " | ".join(metrics_list) + " |\n"
        report += "|--------|" + "|".join(["-------" for _ in metrics_list]) + "|\n"
        
        for policy_name, metrics in all_metrics.items():
            values = [f"{metrics.get(m, 0.0):.4f}" for m in metrics_list]
            report += f"| {policy_name} | " + " | ".join(values) + " |\n"
        
        report += "\n## Risk Analysis\n\n"
        
        for policy_name, metrics in all_metrics.items():
            report += f"### {policy_name}\n\n"
            report += f"- **Mean Return**: {metrics['mean_return']:.4f}\n"
            report += f"- **CVaR (5%)**: {metrics['cvar']:.4f}\n"
            report += f"- **Sharpe Ratio**: {metrics['sharpe']:.4f}\n"
            report += f"- **Sortino Ratio**: {metrics['sortino']:.4f}\n"
            report += f"- **Max Drawdown**: {metrics['max_drawdown']:.4f}\n\n"
        
        return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    logger.info("RISK-ADJUSTED POLICY EVALUATION DEMO")
    print("="*60)
    
    # Create mock dataset
    class MockDataset:
        def __init__(self):
            self.states = np.random.randn(1000, 10)
            self.actions = np.random.randint(0, 3, 1000)
            self.rewards = np.random.randn(1000) * 0.1
            self.dones = np.random.rand(1000) < 0.1
    
    # Create mock policy
    class MockPolicy:
        def predict_batch(self, states):
            return np.random.randint(0, 3, len(states))
    
    dataset = MockDataset()
    policy = MockPolicy()
    
    # Evaluate policy
    evaluator = CVaRPolicyEvaluator(alpha=0.05)
    metrics = evaluator.evaluate(dataset, policy)
    
    logger.info("\nPolicy Metrics:")
    for key, value in metrics.items():
        logger.info(f"  {key}: {value:.4f}")
    
    # Check safety
    is_safe, violations = evaluator.is_safe_policy(
        metrics,
        min_mean_return=-0.1,
        max_cvar=-0.5,
        min_sharpe=0.0,
        max_drawdown=-0.5
    )
    
    logger.info(f"\nSafety Check: {'✅ PASS' if is_safe else '❌ FAIL'}")
    if violations:
        logger.info("Violations:")
        for v in violations:
            logger.info(f"  - {v}")
    
    print("\n" + "="*60)
    logger.info("RISK-ADJUSTED OPE COMPLETE!")
    print("="*60)
