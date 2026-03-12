"""
Skill #92: A/B Testing Framework
================================

Framework for A/B testing trading strategies.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class ABTestResult:
    """A/B test result."""
    test_name: str
    variant_a_performance: float
    variant_b_performance: float
    winner: str
    statistical_significance: float
    trading_signal: str


class ABTestingFramework:
    """A/B testing for strategies."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tests: Dict[str, Dict] = {}
        logger.info("ABTestingFramework initialized")
    
    def create_test(self, name: str, variant_a: str, variant_b: str):
        """Create an A/B test."""
        self.tests[name] = {
            'variant_a': variant_a, 'variant_b': variant_b,
            'results_a': [], 'results_b': []
        }
    
    def record_result(self, test_name: str, variant: str, result: float):
        """Record a test result."""
        if test_name in self.tests:
            key = 'results_a' if variant == 'a' else 'results_b'
            self.tests[test_name][key].append(result)
    
    def analyze(self, test_name: str) -> ABTestResult:
        """Analyze A/B test results."""
        if test_name not in self.tests:
            return ABTestResult(test_name, 0, 0, "", 0, "Test not found")
        
        test = self.tests[test_name]
        results_a = test['results_a']
        results_b = test['results_b']
        
        if not results_a or not results_b:
            return ABTestResult(test_name, 0, 0, "", 0, "Insufficient data")
        
        perf_a = np.mean(results_a)
        perf_b = np.mean(results_b)
        
        # Simple t-test approximation
        pooled_std = np.sqrt((np.var(results_a) + np.var(results_b)) / 2)
        t_stat = abs(perf_a - perf_b) / (pooled_std / np.sqrt(len(results_a)) + 1e-10)
        significance = min(0.99, t_stat / 3)
        
        winner = 'A' if perf_a > perf_b else 'B'
        
        return ABTestResult(
            test_name=test_name, variant_a_performance=perf_a, variant_b_performance=perf_b,
            winner=winner, statistical_significance=significance,
            trading_signal=f"A/B TEST: {winner} wins ({significance:.0%} significance)"
        )
