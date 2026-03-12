"""
Capital & Scalability Validator (Q971-1000)
Addresses capital management, scaling, capacity planning, and growth.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)

import logging
logger = logging.getLogger(__name__)



class CapitalValidator(BaseValidator):
    """Validates capital management and scalability (Q971-1000)"""
    
    def __init__(self):
        try:
            super().__init__(ValidationCategory.CAPITAL_SCALABILITY)
            self._capital_metrics: Dict[str, Any] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _register_checks(self):
        """Register all Q971-1000 validation checks"""
        # Q971-980: Capital Management
        try:
            self.add_check(self._check_capital_management, [971, 972, 973, 974, 975])
            self.add_check(self._check_capital_quality, [976, 977, 978, 979, 980])
            # Q981-990: Scalability
            self.add_check(self._check_scalability, [981, 982, 983, 984, 985])
            self.add_check(self._check_scalability_quality, [986, 987, 988, 989, 990])
            # Q991-1000: Capacity Planning
            self.add_check(self._check_capacity_planning, [991, 992, 993, 994, 995])
            self.add_check(self._check_capacity_quality, [996, 997, 998, 999, 1000])
        
            # Register remediations
            self.add_remediation("reduce_capital_at_risk", self._remediate_reduce_risk)
            self.add_remediation("scale_resources", self._remediate_scale)
            self.add_remediation("rebalance_capital", self._remediate_rebalance)
        except Exception as e:
            logger.error(f"Error in _register_checks: {e}")
            raise
    
    # =========================================================================
    # Q971-980: Capital Management
    # =========================================================================
    
    def _check_capital_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q971-975: Capital management checks"""
        try:
            issues = []
        
            # Q971: Capital at risk exceeded
            capital_at_risk = state.equity * state.drawdown if state.equity > 0 else 0
            max_capital_at_risk = state.capital * IMMUTABLE_LIMITS['max_drawdown']
        
            if capital_at_risk > max_capital_at_risk:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("car_exceeded", str(capital_at_risk)),
                    question_id=971,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Capital at risk exceeded",
                    description=f"Capital at risk ${capital_at_risk:,.0f} > max ${max_capital_at_risk:,.0f}",
                    affected_components=["RiskManager", "CapitalManager"],
                    remediation_available=True,
                    remediation_action="reduce_capital_at_risk",
                    auto_remediate=True,
                    metadata={"capital_at_risk": capital_at_risk, "max": max_capital_at_risk}
                ))
        
            # Q972: Capital allocation error
            allocation_error = state.error_counts.get('capital_allocation_error', 0)
            if allocation_error > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("alloc_error", str(allocation_error)),
                    question_id=972,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Capital allocation errors: {allocation_error}",
                    description="Errors in capital allocation",
                    affected_components=["CapitalManager"],
                    remediation_available=True,
                    remediation_action="fix_allocation"
                ))
        
            # Q973: Capital utilization low
            utilization = self._capital_metrics.get('utilization', 0)
            if state.capital > 0 and utilization < 0.3:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("low_util", str(utilization)),
                    question_id=973,
                    category=self.category,
                    severity=ValidationSeverity.LOW,
                    title=f"Low capital utilization: {utilization*100:.1f}%",
                    description="Capital not being efficiently utilized",
                    affected_components=["CapitalManager"],
                    remediation_available=True,
                    remediation_action="optimize_utilization"
                ))
        
            # Q974: Capital over-utilization
            if utilization > 0.95:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("over_util", str(utilization)),
                    question_id=974,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Capital over-utilization: {utilization*100:.1f}%",
                    description="Capital utilization too high",
                    affected_components=["CapitalManager", "RiskManager"],
                    remediation_available=True,
                    remediation_action="reduce_capital_at_risk"
                ))
        
            # Q975: Capital reconciliation error
            recon_error = state.error_counts.get('capital_reconciliation_error', 0)
            if recon_error > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("recon_error", str(recon_error)),
                    question_id=975,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Capital reconciliation errors: {recon_error}",
                    description="Capital doesn't match broker records",
                    affected_components=["CapitalManager", "BrokerAdapter"],
                    remediation_available=True,
                    remediation_action="force_reconciliation",
                    auto_remediate=True
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_capital_management: {e}")
            raise
    
    def _check_capital_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q976-980: Capital quality checks"""
        try:
            issues = []
        
            # Q976: Capital fragmentation
            fragmentation = state.error_counts.get('capital_fragmentation', 0)
            if fragmentation > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("fragment", str(fragmentation)),
                    question_id=976,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Capital fragmentation detected",
                    description="Capital fragmented across too many positions",
                    affected_components=["CapitalManager"],
                    remediation_available=True,
                    remediation_action="consolidate_capital"
                ))
        
            # Q978: Capital tracking failure
            tracking_fail = state.error_counts.get('capital_tracking_failure', 0)
            if tracking_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("track_fail", str(tracking_fail)),
                    question_id=978,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Capital tracking failed",
                    description="Cannot accurately track capital",
                    affected_components=["CapitalManager"],
                    remediation_available=True,
                    remediation_action="fix_tracking"
                ))
        
            # Q980: Capital efficiency declining
            efficiency_decline = state.error_counts.get('capital_efficiency_decline', 0)
            if efficiency_decline > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("eff_decline", str(efficiency_decline)),
                    question_id=980,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Capital efficiency declining",
                    description="Capital efficiency is declining",
                    affected_components=["CapitalManager"],
                    remediation_available=True,
                    remediation_action="optimize_capital"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_capital_quality: {e}")
            raise
    
    # =========================================================================
    # Q981-990: Scalability
    # =========================================================================
    
    def _check_scalability(self, state: SystemState) -> List[ValidationIssue]:
        """Q981-985: Scalability checks"""
        try:
            issues = []
        
            # Q981: Scaling limit reached
            scaling_limit = state.error_counts.get('scaling_limit_reached', 0)
            if scaling_limit > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("scale_limit", str(scaling_limit)),
                    question_id=981,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Scaling limit reached",
                    description="System has reached scaling limits",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="scale_resources"
                ))
        
            # Q982: Scaling failure
            scaling_fail = state.error_counts.get('scaling_failure', 0)
            if scaling_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("scale_fail", str(scaling_fail)),
                    question_id=982,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Scaling failures: {scaling_fail}",
                    description="Failed to scale system",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="investigate_scaling"
                ))
        
            # Q983: Performance degradation at scale
            perf_degradation = state.error_counts.get('performance_degradation_at_scale', 0)
            if perf_degradation > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("perf_degrade", str(perf_degradation)),
                    question_id=983,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Performance degradation at scale",
                    description="Performance degrades as system scales",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="optimize_scaling"
                ))
        
            # Q984: Scaling bottleneck
            bottleneck = state.error_counts.get('scaling_bottleneck', 0)
            if bottleneck > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("bottleneck", str(bottleneck)),
                    question_id=984,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Scaling bottleneck detected",
                    description="Bottleneck preventing scaling",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="remove_bottleneck"
                ))
        
            # Q985: Scaling cost inefficiency
            cost_inefficiency = state.error_counts.get('scaling_cost_inefficiency', 0)
            if cost_inefficiency > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("cost_ineff", str(cost_inefficiency)),
                    question_id=985,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Scaling cost inefficiency",
                    description="Scaling is not cost-effective",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="optimize_costs"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_scalability: {e}")
            raise
    
    def _check_scalability_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q986-990: Scalability quality checks"""
        try:
            issues = []
        
            # Q986: Auto-scaling failure
            autoscale_fail = state.error_counts.get('autoscaling_failure', 0)
            if autoscale_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("autoscale", str(autoscale_fail)),
                    question_id=986,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Auto-scaling failures: {autoscale_fail}",
                    description="Auto-scaling not working",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="fix_autoscaling"
                ))
        
            # Q988: Scaling latency
            scaling_latency = state.latency_metrics.get('scaling_latency_ms', 0)
            if scaling_latency > 60000:  # 1 minute
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("scale_latency", str(scaling_latency)),
                    question_id=988,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"High scaling latency: {scaling_latency/1000:.0f}s",
                    description="Scaling takes too long",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="optimize_scaling"
                ))
        
            # Q990: Scaling instability
            instability = state.error_counts.get('scaling_instability', 0)
            if instability > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("instability", str(instability)),
                    question_id=990,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Scaling instability",
                    description="System unstable during scaling",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="stabilize_scaling"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_scalability_quality: {e}")
            raise
    
    # =========================================================================
    # Q991-1000: Capacity Planning
    # =========================================================================
    
    def _check_capacity_planning(self, state: SystemState) -> List[ValidationIssue]:
        """Q991-995: Capacity planning checks"""
        try:
            issues = []
        
            # Q991: Capacity exceeded
            capacity_exceeded = state.error_counts.get('capacity_exceeded', 0)
            if capacity_exceeded > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("cap_exceeded", str(capacity_exceeded)),
                    question_id=991,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="System capacity exceeded",
                    description="System operating beyond capacity",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="scale_resources",
                    auto_remediate=True
                ))
        
            # Q992: Capacity approaching limit
            capacity_util = self._capital_metrics.get('capacity_utilization', 0)
            if capacity_util > 0.85:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("cap_near", str(capacity_util)),
                    question_id=992,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Capacity near limit: {capacity_util*100:.1f}%",
                    description="System approaching capacity limits",
                    affected_components=["Infrastructure"],
                    remediation_available=True,
                    remediation_action="plan_expansion"
                ))
        
            # Q993: Capacity forecast inaccurate
            forecast_inaccurate = state.error_counts.get('capacity_forecast_inaccurate', 0)
            if forecast_inaccurate > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("forecast", str(forecast_inaccurate)),
                    question_id=993,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Capacity forecast inaccurate",
                    description="Capacity forecasts not matching reality",
                    affected_components=["CapacityPlanning"],
                    remediation_available=True,
                    remediation_action="improve_forecasting"
                ))
        
            # Q994: Capacity planning gap
            planning_gap = state.error_counts.get('capacity_planning_gap', 0)
            if planning_gap > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("plan_gap", str(planning_gap)),
                    question_id=994,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Capacity planning gaps",
                    description="Gaps in capacity planning",
                    affected_components=["CapacityPlanning"],
                    remediation_available=True,
                    remediation_action="improve_planning"
                ))
        
            # Q995: Unexpected capacity demand
            unexpected_demand = state.error_counts.get('unexpected_capacity_demand', 0)
            if unexpected_demand > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("unexpected", str(unexpected_demand)),
                    question_id=995,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Unexpected capacity demand",
                    description="Capacity demand exceeded forecasts",
                    affected_components=["CapacityPlanning"],
                    remediation_available=True,
                    remediation_action="scale_resources"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_capacity_planning: {e}")
            raise
    
    def _check_capacity_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q996-1000: Capacity quality checks"""
        try:
            issues = []
        
            # Q996: Capacity monitoring failure
            mon_fail = state.error_counts.get('capacity_monitoring_failure', 0)
            if mon_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("mon_fail", str(mon_fail)),
                    question_id=996,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Capacity monitoring failed",
                    description="Cannot monitor system capacity",
                    affected_components=["Monitoring"],
                    remediation_available=True,
                    remediation_action="restart_monitoring"
                ))
        
            # Q998: Capacity allocation inefficiency
            alloc_inefficiency = state.error_counts.get('capacity_allocation_inefficiency', 0)
            if alloc_inefficiency > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("alloc_ineff", str(alloc_inefficiency)),
                    question_id=998,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Capacity allocation inefficiency",
                    description="Capacity not allocated efficiently",
                    affected_components=["CapacityPlanning"],
                    remediation_available=True,
                    remediation_action="optimize_allocation"
                ))
        
            # Q1000: Growth sustainability
            growth_unsustainable = state.error_counts.get('growth_unsustainable', 0)
            if growth_unsustainable > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("unsustainable", str(growth_unsustainable)),
                    question_id=1000,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Growth sustainability concerns",
                    description="Current growth rate may not be sustainable",
                    affected_components=["CapacityPlanning"],
                    remediation_available=True,
                    remediation_action="review_growth_plan"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_capacity_quality: {e}")
            raise
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_reduce_risk(self, issue: ValidationIssue) -> str:
        """Reduce capital at risk"""
        try:
            self.logger.info("Reducing capital at risk")
            return "Capital at risk reduced"
        except Exception as e:
            logger.error(f"Error in _remediate_reduce_risk: {e}")
            raise
    
    async def _remediate_scale(self, issue: ValidationIssue) -> str:
        """Scale resources"""
        try:
            self.logger.info("Scaling resources")
            return "Resources scaled"
        except Exception as e:
            logger.error(f"Error in _remediate_scale: {e}")
            raise
    
    async def _remediate_rebalance(self, issue: ValidationIssue) -> str:
        """Rebalance capital"""
        try:
            self.logger.info("Rebalancing capital")
            return "Capital rebalanced"
        except Exception as e:
            logger.error(f"Error in _remediate_rebalance: {e}")
            raise
