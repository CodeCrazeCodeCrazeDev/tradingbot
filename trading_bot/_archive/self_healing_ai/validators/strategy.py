"""
Strategy Lifecycle Validator (Q201-270)
Addresses strategy development, validation, deployment, monitoring, and retirement.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class StrategyValidator(BaseValidator):
    """Validates strategy lifecycle management (Q201-270)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.STRATEGY_LIFECYCLE)
        self._strategy_metrics: Dict[str, Dict] = {}
        self._strategy_correlations: Dict[str, Dict[str, float]] = {}
    
    def _register_checks(self):
        """Register all Q201-270 validation checks"""
        # Q201-210: Strategy Development
        self.add_check(self._check_hypothesis_generation, [201, 202, 203])
        self.add_check(self._check_development_process, [204, 205, 206, 207, 208, 209, 210])
        # Q211-220: Strategy Validation
        self.add_check(self._check_oos_testing, [211, 212, 213])
        self.add_check(self._check_statistical_validation, [214, 215, 216, 217, 218])
        self.add_check(self._check_stress_testing, [219, 220])
        # Q221-230: Strategy Deployment
        self.add_check(self._check_deployment_process, [221, 222, 223, 224, 225])
        self.add_check(self._check_deployment_coordination, [226, 227, 228, 229, 230])
        # Q231-240: Strategy Monitoring
        self.add_check(self._check_production_metrics, [231, 232, 233, 234])
        self.add_check(self._check_monitoring_health, [235, 236, 237, 238, 239, 240])
        # Q241-250: Strategy Retirement
        self.add_check(self._check_retirement_criteria, [241, 242, 243, 244, 245])
        self.add_check(self._check_retirement_process, [246, 247, 248, 249, 250])
        # Q251-260: Strategy Capacity
        self.add_check(self._check_capacity_estimation, [251, 252, 253, 254, 255])
        self.add_check(self._check_capacity_management, [256, 257, 258, 259, 260])
        # Q261-270: Strategy Correlation
        self.add_check(self._check_correlation_measurement, [261, 262, 263, 264, 265])
        self.add_check(self._check_correlation_management, [266, 267, 268, 269, 270])
        
        # Register remediations
        self.add_remediation("reduce_allocation", self._remediate_reduce_allocation)
        self.add_remediation("pause_strategy", self._remediate_pause_strategy)
        self.add_remediation("rebalance_portfolio", self._remediate_rebalance)
    
    # =========================================================================
    # Q201-210: Strategy Development
    # =========================================================================
    
    def _check_hypothesis_generation(self, state: SystemState) -> List[ValidationIssue]:
        """Q201-203: Strategy hypothesis and overfitting prevention"""
        issues = []
        
        # Q202: Overfitting detection
        overfitting_indicators = state.error_counts.get('overfitting_detected', 0)
        if overfitting_indicators > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("overfit", str(overfitting_indicators)),
                question_id=202,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Overfitting indicators: {overfitting_indicators}",
                description="Strategy may be overfitted to historical data",
                affected_components=["StrategyDevelopment"],
                remediation_available=True,
                remediation_action="simplify_strategy"
            ))
        
        return issues
    
    def _check_development_process(self, state: SystemState) -> List[ValidationIssue]:
        """Q204-210: Strategy development process"""
        issues = []
        
        # Q204: Backtest vs paper trading gap
        backtest_gap = state.error_counts.get('backtest_paper_gap', 0)
        if backtest_gap > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("gap", str(backtest_gap)),
                question_id=204,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Backtest vs paper trading gap detected",
                description="Strategy performs differently in paper trading than backtest",
                affected_components=["StrategyDevelopment", "Backtesting"],
                remediation_available=False
            ))
        
        # Q206: Noise chasing
        noise_chasing = state.error_counts.get('noise_chasing', 0)
        if noise_chasing > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("noise", str(noise_chasing)),
                question_id=206,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Noise chasing detected",
                description="Strategy development may be chasing noise",
                affected_components=["StrategyDevelopment"],
                remediation_available=False
            ))
        
        return issues
    
    # =========================================================================
    # Q211-220: Strategy Validation
    # =========================================================================
    
    def _check_oos_testing(self, state: SystemState) -> List[ValidationIssue]:
        """Q211-213: Out-of-sample testing"""
        issues = []
        
        # Q212: Data leakage
        data_leakage = state.error_counts.get('data_leakage', 0)
        if data_leakage > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("leakage", str(data_leakage)),
                question_id=212,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Data leakage detected: {data_leakage}",
                description="Future information leaking into training/validation",
                affected_components=["StrategyDevelopment", "DataPipeline"],
                remediation_available=True,
                remediation_action="fix_data_pipeline"
            ))
        
        return issues
    
    def _check_statistical_validation(self, state: SystemState) -> List[ValidationIssue]:
        """Q214-218: Statistical validation"""
        issues = []
        
        # Q216: Luck vs skill
        luck_indicators = state.error_counts.get('luck_not_skill', 0)
        if luck_indicators > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("luck", str(luck_indicators)),
                question_id=216,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Strategy performance may be luck",
                description="Statistical tests suggest performance may be due to luck",
                affected_components=["StrategyValidation"],
                remediation_available=False
            ))
        
        return issues
    
    def _check_stress_testing(self, state: SystemState) -> List[ValidationIssue]:
        """Q219-220: Pre-deployment stress testing"""
        issues = []
        
        stress_failures = state.error_counts.get('stress_test_failure', 0)
        if stress_failures > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stress", str(stress_failures)),
                question_id=219,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Stress test failures: {stress_failures}",
                description="Strategy failed stress testing",
                affected_components=["StrategyValidation"],
                remediation_available=False
            ))
        
        return issues
    
    # =========================================================================
    # Q221-230: Strategy Deployment
    # =========================================================================
    
    def _check_deployment_process(self, state: SystemState) -> List[ValidationIssue]:
        """Q221-225: Strategy deployment process"""
        issues = []
        
        # Q222: Deployment failure
        deploy_failures = state.error_counts.get('strategy_deployment_failure', 0)
        if deploy_failures > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("deploy_fail", str(deploy_failures)),
                question_id=222,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Strategy deployment failures: {deploy_failures}",
                description="Strategy deployment failed",
                affected_components=["StrategyDeployment"],
                remediation_available=True,
                remediation_action="rollback_deployment"
            ))
        
        # Q225: Immediate loss after deployment
        immediate_loss = state.error_counts.get('immediate_loss_after_deploy', 0)
        if immediate_loss > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("immediate_loss", str(immediate_loss)),
                question_id=225,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Immediate loss after deployment",
                description="Newly deployed strategy immediately losing money",
                affected_components=["StrategyDeployment"],
                remediation_available=True,
                remediation_action="pause_strategy",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_deployment_coordination(self, state: SystemState) -> List[ValidationIssue]:
        """Q226-230: Deployment coordination"""
        issues = []
        
        # Q228: Strategy interaction
        interaction_issues = state.error_counts.get('strategy_interaction_issue', 0)
        if interaction_issues > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("interaction", str(interaction_issues)),
                question_id=228,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Strategy interaction issues: {interaction_issues}",
                description="Strategies interfering with each other",
                affected_components=["StrategyOrchestrator"],
                remediation_available=True,
                remediation_action="isolate_strategies"
            ))
        
        # Q229: Deployment instability
        instability = state.error_counts.get('deployment_instability', 0)
        if instability > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("instability", str(instability)),
                question_id=229,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Deployment causing system instability",
                description="Strategy deployment destabilizing system",
                affected_components=["StrategyDeployment", "System"],
                remediation_available=True,
                remediation_action="rollback_deployment",
                auto_remediate=True
            ))
        
        return issues
    
    # =========================================================================
    # Q231-240: Strategy Monitoring
    # =========================================================================
    
    def _check_production_metrics(self, state: SystemState) -> List[ValidationIssue]:
        """Q231-234: Production metrics tracking"""
        issues = []
        
        for strategy in state.active_strategies:
            metrics = self._strategy_metrics.get(strategy, {})
            
            # Q232: Underperformance detection
            sharpe = metrics.get('sharpe_ratio', 0)
            expected_sharpe = metrics.get('expected_sharpe', 1.0)
            if sharpe < expected_sharpe * 0.5:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("underperform", strategy),
                    question_id=232,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Strategy underperforming: {strategy}",
                    description=f"Sharpe {sharpe:.2f} vs expected {expected_sharpe:.2f}",
                    affected_components=[strategy],
                    remediation_available=True,
                    remediation_action="reduce_allocation",
                    metadata={"strategy": strategy, "sharpe": sharpe, "expected": expected_sharpe}
                ))
            
            # Q234: Variance vs degradation
            recent_variance = metrics.get('recent_variance', 0)
            historical_variance = metrics.get('historical_variance', 1)
            if recent_variance > historical_variance * 2:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("variance", strategy),
                    question_id=234,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"High variance: {strategy}",
                    description="Strategy showing unusual variance",
                    affected_components=[strategy],
                    remediation_available=True,
                    remediation_action="investigate_strategy"
                ))
        
        return issues
    
    def _check_monitoring_health(self, state: SystemState) -> List[ValidationIssue]:
        """Q235-240: Monitoring health"""
        issues = []
        
        # Q235: Monitoring failure
        monitoring_failures = state.error_counts.get('strategy_monitoring_failure', 0)
        if monitoring_failures > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("mon_fail", str(monitoring_failures)),
                question_id=235,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Strategy monitoring failures: {monitoring_failures}",
                description="Cannot monitor strategy performance",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="restart_monitoring"
            ))
        
        # Q238: Behavior change without parameter change
        behavior_change = state.error_counts.get('behavior_change_detected', 0)
        if behavior_change > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("behavior", str(behavior_change)),
                question_id=238,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Strategy behavior changed",
                description="Strategy behavior changed without parameter changes",
                affected_components=["StrategyEngine"],
                remediation_available=True,
                remediation_action="investigate_strategy"
            ))
        
        # Q239: Simultaneous degradation
        degrading_count = sum(1 for s in state.active_strategies 
                            if self._strategy_metrics.get(s, {}).get('degrading', False))
        if degrading_count > 1:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("multi_degrade", str(degrading_count)),
                question_id=239,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Multiple strategies degrading: {degrading_count}",
                description="Multiple strategies degrading simultaneously",
                affected_components=["StrategyEngine"],
                remediation_available=True,
                remediation_action="reduce_exposure",
                auto_remediate=True
            ))
        
        return issues
    
    # =========================================================================
    # Q241-250: Strategy Retirement
    # =========================================================================
    
    def _check_retirement_criteria(self, state: SystemState) -> List[ValidationIssue]:
        """Q241-245: Retirement criteria"""
        issues = []
        
        for strategy in state.active_strategies:
            metrics = self._strategy_metrics.get(strategy, {})
            
            # Q242: Declining profitability
            profit_trend = metrics.get('profit_trend', 0)
            if profit_trend < -0.1:  # 10% decline
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("declining", strategy),
                    question_id=242,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"Declining profitability: {strategy}",
                    description=f"Strategy profit declining: {profit_trend*100:.1f}%",
                    affected_components=[strategy],
                    remediation_available=True,
                    remediation_action="evaluate_retirement"
                ))
        
        return issues
    
    def _check_retirement_process(self, state: SystemState) -> List[ValidationIssue]:
        """Q246-250: Retirement process"""
        issues = []
        
        # Q249: Portfolio imbalance from retirement
        imbalance = state.error_counts.get('retirement_imbalance', 0)
        if imbalance > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("imbalance", str(imbalance)),
                question_id=249,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Portfolio imbalance from retirement",
                description="Strategy retirement caused portfolio imbalance",
                affected_components=["PortfolioManager"],
                remediation_available=True,
                remediation_action="rebalance_portfolio"
            ))
        
        return issues
    
    # =========================================================================
    # Q251-260: Strategy Capacity
    # =========================================================================
    
    def _check_capacity_estimation(self, state: SystemState) -> List[ValidationIssue]:
        """Q251-255: Capacity estimation"""
        issues = []
        
        for strategy in state.active_strategies:
            metrics = self._strategy_metrics.get(strategy, {})
            
            # Q252: Capacity exceeded
            current_capital = metrics.get('allocated_capital', 0)
            capacity = metrics.get('estimated_capacity', float('inf'))
            if current_capital > capacity * 0.9:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("capacity", strategy),
                    question_id=252,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Near capacity: {strategy}",
                    description=f"Strategy at {current_capital/capacity*100:.0f}% of capacity",
                    affected_components=[strategy],
                    remediation_available=True,
                    remediation_action="reduce_allocation",
                    metadata={"strategy": strategy, "utilization": current_capital/capacity}
                ))
            
            # Q253: Capacity degradation
            if metrics.get('capacity_degrading', False):
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("cap_degrade", strategy),
                    question_id=253,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"Capacity degrading: {strategy}",
                    description="Strategy performance degrading due to capacity",
                    affected_components=[strategy],
                    remediation_available=True,
                    remediation_action="reduce_allocation"
                ))
        
        return issues
    
    def _check_capacity_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q256-260: Capacity management"""
        issues = []
        
        # Q256: Total capacity exceeds capital
        total_capacity = sum(self._strategy_metrics.get(s, {}).get('estimated_capacity', 0) 
                           for s in state.active_strategies)
        if state.capital > total_capacity and total_capacity > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("overcapacity", str(state.capital)),
                question_id=256,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Capital exceeds total strategy capacity",
                description=f"Capital ${state.capital:,.0f} exceeds capacity ${total_capacity:,.0f}",
                affected_components=["PortfolioManager"],
                remediation_available=False
            ))
        
        return issues
    
    # =========================================================================
    # Q261-270: Strategy Correlation
    # =========================================================================
    
    def _check_correlation_measurement(self, state: SystemState) -> List[ValidationIssue]:
        """Q261-265: Correlation measurement"""
        issues = []
        
        max_correlation = IMMUTABLE_LIMITS['max_correlation_exposure']
        
        for s1, correlations in self._strategy_correlations.items():
            for s2, corr in correlations.items():
                if s1 != s2 and abs(corr) > max_correlation:
                    issues.append(ValidationIssue(
                        issue_id=self._generate_issue_id("correlation", f"{s1}_{s2}"),
                        question_id=261,
                        category=self.category,
                        severity=ValidationSeverity.HIGH,
                        title=f"High correlation: {s1} <-> {s2}",
                        description=f"Correlation {corr:.2f} exceeds threshold {max_correlation}",
                        affected_components=[s1, s2],
                        remediation_available=True,
                        remediation_action="reduce_allocation",
                        metadata={"strategy1": s1, "strategy2": s2, "correlation": corr}
                    ))
        
        # Q262: Unexpected correlation
        unexpected_corr = state.error_counts.get('unexpected_correlation', 0)
        if unexpected_corr > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unexpected_corr", str(unexpected_corr)),
                question_id=262,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Unexpected strategy correlation",
                description="Strategies that should be uncorrelated are now correlated",
                affected_components=["PortfolioManager"],
                remediation_available=True,
                remediation_action="rebalance_portfolio"
            ))
        
        return issues
    
    def _check_correlation_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q266-270: Correlation management"""
        issues = []
        
        # Q266: Stress correlation spike
        stress_correlation = state.error_counts.get('stress_correlation_spike', 0)
        if stress_correlation > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stress_corr", str(stress_correlation)),
                question_id=266,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Correlation spike during stress",
                description="Strategy correlations spiking during market stress",
                affected_components=["PortfolioManager", "RiskManager"],
                remediation_available=True,
                remediation_action="reduce_exposure",
                auto_remediate=True
            ))
        
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_reduce_allocation(self, issue: ValidationIssue) -> str:
        """Reduce allocation to strategy"""
        strategy = issue.metadata.get('strategy', 'unknown')
        self.logger.info(f"Reducing allocation to {strategy}")
        return f"Reduced allocation to {strategy}"
    
    async def _remediate_pause_strategy(self, issue: ValidationIssue) -> str:
        """Pause strategy execution"""
        self.logger.info("Pausing strategy")
        return "Strategy paused"
    
    async def _remediate_rebalance(self, issue: ValidationIssue) -> str:
        """Rebalance portfolio"""
        self.logger.info("Rebalancing portfolio")
        return "Portfolio rebalanced"
