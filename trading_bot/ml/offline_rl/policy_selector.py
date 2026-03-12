"""
from typing import List, Set
Policy Selector

Compares and selects the best policy based on offline evaluation.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
import json
from pathlib import Path
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

try:
    from .ope import ImportanceSampling, DoublyRobust, FittedQEvaluation
except ImportError:
    logger.warning("OPE methods not available")


class PolicySelector:
    """
    Compares and selects the best policy based on offline evaluation.
    
    Uses multiple OPE methods for robust evaluation.
    """
    
    def __init__(
        self,
        methods: List[str] = ["is", "dr", "fqe"],
        discount: float = 0.99,
        log_dir: str = "logs/policy_selection"
    ):
        """
        Initialize policy selector.
        
        Args:
            methods: OPE methods to use
            discount: Reward discount factor
            log_dir: Directory for logs
        """
        self.methods = methods
        self.discount = discount
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OPE methods
        self.ope_methods = {}
        
        if "is" in methods:
            self.ope_methods["is"] = ImportanceSampling(discount=discount)
        
        if "dr" in methods:
            self.ope_methods["dr"] = DoublyRobust(discount=discount)
        
        if "fqe" in methods:
            self.ope_methods["fqe"] = FittedQEvaluation(discount=discount)
        
        logger.info(f"Policy selector initialized with methods: {', '.join(methods)}")
    
    def evaluate_policies(
        self,
        dataset,
        policies: Dict[str, Any],
        behavior_policy = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate multiple policies.
        
        Args:
            dataset: Dataset to evaluate on
            policies: Dictionary of policies to evaluate
            behavior_policy: Behavior policy that generated the data
        
        Returns:
            Dictionary of policy values by method
        """
        results = {}
        
        # Update behavior policy for IS and DR
        if behavior_policy and "is" in self.ope_methods:
            self.ope_methods["is"].behavior_policy = behavior_policy
        
        if behavior_policy and "dr" in self.ope_methods:
            self.ope_methods["dr"].behavior_policy = behavior_policy
        
        # Evaluate each policy
        for policy_name, policy in policies.items():
            logger.info(f"Evaluating policy: {policy_name}")
            
            policy_results = {}
            
            for method_name, method in self.ope_methods.items():
                value = method.evaluate(dataset, policy)
                policy_results[method_name] = value
            
            results[policy_name] = policy_results
            
            logger.info(f"Policy {policy_name} values: {policy_results}")
        
        # Save results
        self._save_results(results)
        
        return results
    
    def select_best_policy(self, results: Dict[str, Dict[str, float]]) -> str:
        """
        Select best policy based on evaluation results.
        
        Args:
            results: Evaluation results from evaluate_policies
        
        Returns:
            Name of best policy
        """
        # Compute average value across methods for each policy
        avg_values = {}
        
        for policy_name, policy_results in results.items():
            avg_values[policy_name] = np.mean(list(policy_results.values()))
        
        # Select best policy
        best_policy = max(avg_values, key=avg_values.get)
        
        logger.info(f"Best policy: {best_policy} with average value: {avg_values[best_policy]:.4f}")
        
        return best_policy
    
    def _save_results(self, results: Dict[str, Dict[str, float]]):
        """
        Save evaluation results.
        
        Args:
            results: Evaluation results
        """
        # Save as JSON
        with open(self.log_dir / "policy_evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Create visualization
        self._create_visualization(results)
    
    def _create_visualization(self, results: Dict[str, Dict[str, float]]):
        """
        Create visualization of evaluation results.
        
        Args:
            results: Evaluation results
        """
        try:
            # Extract data
            policies = list(results.keys())
            methods = list(next(iter(results.values())).keys())
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Set width of bars
            bar_width = 0.2
            index = np.arange(len(policies))
            
            # Plot bars for each method
            for i, method in enumerate(methods):
                values = [results[policy][method] for policy in policies]
                plt.bar(index + i * bar_width, values, bar_width, label=method.upper())
            
            # Add labels and legend
            plt.xlabel("Policy")
            plt.ylabel("Estimated Value")
            plt.title("Policy Evaluation Results")
            plt.xticks(index + bar_width * (len(methods) - 1) / 2, policies)
            plt.legend()
            
            # Save figure
            plt.tight_layout()
            plt.savefig(self.log_dir / "policy_evaluation_results.png")
            plt.close()
            
            logger.info(f"Visualization saved to {self.log_dir / 'policy_evaluation_results.png'}")
            
        except Exception as e:
            logger.error(f"Failed to create visualization: {e}")
    
    def generate_report(self, results: Dict[str, Dict[str, float]], best_policy: str):
        """
        Generate evaluation report.
        
        Args:
            results: Evaluation results
            best_policy: Name of best policy
        """
        report = {
            "best_policy": best_policy,
            "results": results,
            "summary": {
                "num_policies": len(results),
                "methods_used": list(self.methods),
                "best_policy_values": results[best_policy]
            }
        }
        
        # Save report
        with open(self.log_dir / "policy_selection_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        markdown = f"# Policy Selection Report\n\n"
        markdown += f"## Best Policy: {best_policy}\n\n"
        markdown += f"### Evaluation Results\n\n"
        
        # Create table
        markdown += "| Policy | " + " | ".join(self.methods) + " | Average |\n"
        markdown += "|--------|" + "|".join(["-----" for _ in self.methods]) + "|--------|\n"
        
        for policy_name, policy_results in results.items():
            avg_value = np.mean(list(policy_results.values()))
            values = [f"{policy_results.get(method, 0.0):.4f}" for method in self.methods]
            markdown += f"| {policy_name} | " + " | ".join(values) + f" | {avg_value:.4f} |\n"
        
        # Save markdown report
        with open(self.log_dir / "policy_selection_report.md", "w") as f:
            f.write(markdown)
        
        logger.info(f"Report saved to {self.log_dir / 'policy_selection_report.md'}")
        
        return report
