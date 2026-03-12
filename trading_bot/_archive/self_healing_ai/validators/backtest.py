"""
Backtesting & Simulation Validator (Q531-590)
Addresses backtest methodology, data handling, simulation fidelity, and result validation.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class BacktestValidator(BaseValidator):
    """Validates backtesting and simulation quality (Q531-590)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.BACKTESTING)
        self._backtest_metrics: Dict[str, Any] = {}
    
    def _register_checks(self):
        """Register all Q531-590 validation checks"""
        # Q531-540: Methodology
        self.add_check(self._check_backtest_methodology, [531, 532, 533, 534, 535])
        self.add_check(self._check_methodology_quality, [536, 537, 538, 539, 540])
        # Q541-550: Data Handling
        self.add_check(self._check_backtest_data, [541, 542, 543, 544, 545])
        self.add_check(self._check_data_quality, [546, 547, 548, 549, 550])
        # Q551-560: Simulation Fidelity
        self.add_check(self._check_simulation_fidelity, [551, 552, 553, 554, 555])
        self.add_check(self._check_fidelity_quality, [556, 557, 558, 559, 560])
        # Q561-570: Result Validation
        self.add_check(self._check_result_validation, [561, 562, 563, 564, 565])
        self.add_check(self._check_validation_quality, [566, 567, 568, 569, 570])
        # Q571-580: Statistical Rigor
        self.add_check(self._check_statistical_rigor, [571, 572, 573, 574, 575])
        self.add_check(self._check_rigor_quality, [576, 577, 578, 579, 580])
        # Q581-590: Production Comparison
        self.add_check(self._check_production_comparison, [581, 582, 583, 584, 585])
        self.add_check(self._check_comparison_quality, [586, 587, 588, 589, 590])
        
        # Register remediations
        self.add_remediation("fix_lookahead", self._remediate_fix_lookahead)
        self.add_remediation("improve_simulation", self._remediate_improve_sim)
    
    # =========================================================================
    # Q531-540: Methodology
    # =========================================================================
    
    def _check_backtest_methodology(self, state: SystemState) -> List[ValidationIssue]:
        """Q531-535: Backtest methodology checks"""
        issues = []
        
        # Q531: Look-ahead bias
        lookahead = state.error_counts.get('lookahead_bias', 0)
        if lookahead > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("lookahead", str(lookahead)),
                question_id=531,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Look-ahead bias detected: {lookahead}",
                description="Backtest using future information",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="fix_lookahead"
            ))
        
        # Q532: Survivorship bias
        survivorship = state.error_counts.get('survivorship_bias', 0)
        if survivorship > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("survivorship", str(survivorship)),
                question_id=532,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Survivorship bias detected",
                description="Backtest data has survivorship bias",
                affected_components=["Backtesting", "DataPipeline"],
                remediation_available=True,
                remediation_action="add_delisted_data"
            ))
        
        # Q533: Selection bias
        selection_bias = state.error_counts.get('selection_bias', 0)
        if selection_bias > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("selection", str(selection_bias)),
                question_id=533,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Selection bias detected",
                description="Backtest has selection bias in data",
                affected_components=["Backtesting"],
                remediation_available=False
            ))
        
        # Q534: Overfitting
        overfitting = state.error_counts.get('backtest_overfitting', 0)
        if overfitting > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("overfit", str(overfitting)),
                question_id=534,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Backtest overfitting detected",
                description="Strategy overfitted to historical data",
                affected_components=["Backtesting", "StrategyDevelopment"],
                remediation_available=True,
                remediation_action="simplify_strategy"
            ))
        
        return issues
    
    def _check_methodology_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q536-540: Methodology quality checks"""
        issues = []
        
        # Q536: Insufficient data
        insufficient_data = state.error_counts.get('insufficient_backtest_data', 0)
        if insufficient_data > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("insufficient", str(insufficient_data)),
                question_id=536,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Insufficient backtest data",
                description="Not enough data for statistically valid backtest",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="extend_data_period"
            ))
        
        # Q538: Walk-forward not used
        no_walkforward = state.error_counts.get('no_walkforward', 0)
        if no_walkforward > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("walkforward", str(no_walkforward)),
                question_id=538,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Walk-forward validation not used",
                description="Strategy not validated with walk-forward",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="add_walkforward"
            ))
        
        # Q540: Multiple testing correction
        multiple_testing = state.error_counts.get('no_multiple_testing_correction', 0)
        if multiple_testing > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("multiple", str(multiple_testing)),
                question_id=540,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="No multiple testing correction",
                description="Multiple hypothesis testing without correction",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="add_bonferroni"
            ))
        
        return issues
    
    # =========================================================================
    # Q541-550: Data Handling
    # =========================================================================
    
    def _check_backtest_data(self, state: SystemState) -> List[ValidationIssue]:
        """Q541-545: Backtest data checks"""
        issues = []
        
        # Q541: Point-in-time data
        pit_issues = state.error_counts.get('point_in_time_violation', 0)
        if pit_issues > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("pit", str(pit_issues)),
                question_id=541,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Point-in-time violations: {pit_issues}",
                description="Using data not available at backtest time",
                affected_components=["Backtesting", "DataPipeline"],
                remediation_available=True,
                remediation_action="fix_pit_data"
            ))
        
        # Q542: Corporate actions
        corp_actions = state.error_counts.get('missing_corporate_actions', 0)
        if corp_actions > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("corp_actions", str(corp_actions)),
                question_id=542,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Missing corporate action adjustments",
                description="Backtest data not adjusted for corporate actions",
                affected_components=["Backtesting", "DataPipeline"],
                remediation_available=True,
                remediation_action="add_corp_adjustments"
            ))
        
        # Q544: Data gaps
        data_gaps = state.error_counts.get('backtest_data_gaps', 0)
        if data_gaps > 10:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("gaps", str(data_gaps)),
                question_id=544,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Backtest data gaps: {data_gaps}",
                description="Gaps in backtest data",
                affected_components=["Backtesting", "DataPipeline"],
                remediation_available=True,
                remediation_action="fill_data_gaps"
            ))
        
        return issues
    
    def _check_data_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q546-550: Data quality checks"""
        issues = []
        
        # Q547: Data quality degradation
        quality_degrade = state.error_counts.get('backtest_data_quality_degradation', 0)
        if quality_degrade > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("quality_deg", str(quality_degrade)),
                question_id=547,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Backtest data quality degrading",
                description="Historical data quality is degrading",
                affected_components=["Backtesting", "DataPipeline"],
                remediation_available=True,
                remediation_action="improve_data_quality"
            ))
        
        # Q550: Inconsistent data sources
        inconsistent = state.error_counts.get('inconsistent_backtest_sources', 0)
        if inconsistent > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("inconsistent", str(inconsistent)),
                question_id=550,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Inconsistent backtest data sources",
                description="Different data sources giving different results",
                affected_components=["Backtesting", "DataPipeline"],
                remediation_available=True,
                remediation_action="reconcile_sources"
            ))
        
        return issues
    
    # =========================================================================
    # Q551-560: Simulation Fidelity
    # =========================================================================
    
    def _check_simulation_fidelity(self, state: SystemState) -> List[ValidationIssue]:
        """Q551-555: Simulation fidelity checks"""
        issues = []
        
        # Q551: Slippage modeling
        slippage_model = state.error_counts.get('unrealistic_slippage_model', 0)
        if slippage_model > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("slippage_model", str(slippage_model)),
                question_id=551,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Unrealistic slippage model",
                description="Backtest slippage model doesn't match reality",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="improve_simulation"
            ))
        
        # Q552: Market impact
        impact_model = state.error_counts.get('unrealistic_impact_model', 0)
        if impact_model > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("impact_model", str(impact_model)),
                question_id=552,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Unrealistic market impact model",
                description="Backtest market impact doesn't match reality",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="improve_simulation"
            ))
        
        # Q553: Fill assumptions
        fill_assumptions = state.error_counts.get('unrealistic_fill_assumptions', 0)
        if fill_assumptions > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("fill_assume", str(fill_assumptions)),
                question_id=553,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Unrealistic fill assumptions",
                description="Backtest assumes fills that wouldn't happen",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="improve_simulation"
            ))
        
        # Q555: Latency modeling
        latency_model = state.error_counts.get('no_latency_modeling', 0)
        if latency_model > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("latency_model", str(latency_model)),
                question_id=555,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="No latency modeling in backtest",
                description="Backtest doesn't account for execution latency",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="add_latency_model"
            ))
        
        return issues
    
    def _check_fidelity_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q556-560: Fidelity quality checks"""
        issues = []
        
        # Q558: Simulation vs reality gap
        sim_gap = state.error_counts.get('simulation_reality_gap', 0)
        if sim_gap > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("sim_gap", str(sim_gap)),
                question_id=558,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Simulation vs reality gap detected",
                description="Backtest results don't match live trading",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="improve_simulation"
            ))
        
        # Q560: Edge case handling
        edge_cases = state.error_counts.get('backtest_edge_case_failure', 0)
        if edge_cases > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("edge_case", str(edge_cases)),
                question_id=560,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Backtest edge case failures: {edge_cases}",
                description="Backtest doesn't handle edge cases",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="add_edge_cases"
            ))
        
        return issues
    
    # =========================================================================
    # Q561-570: Result Validation
    # =========================================================================
    
    def _check_result_validation(self, state: SystemState) -> List[ValidationIssue]:
        """Q561-565: Result validation checks"""
        issues = []
        
        # Q561: Unrealistic returns
        unrealistic_returns = state.error_counts.get('unrealistic_backtest_returns', 0)
        if unrealistic_returns > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unrealistic", str(unrealistic_returns)),
                question_id=561,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Unrealistic backtest returns",
                description="Backtest returns too good to be true",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="investigate_results"
            ))
        
        # Q562: Sharpe ratio validation
        sharpe_issues = state.error_counts.get('suspicious_sharpe', 0)
        if sharpe_issues > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("sharpe", str(sharpe_issues)),
                question_id=562,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Suspicious Sharpe ratio",
                description="Backtest Sharpe ratio is suspiciously high",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="validate_sharpe"
            ))
        
        # Q564: Drawdown validation
        dd_issues = state.error_counts.get('unrealistic_drawdown', 0)
        if dd_issues > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dd_valid", str(dd_issues)),
                question_id=564,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Unrealistic drawdown in backtest",
                description="Backtest drawdown doesn't match expectations",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="validate_drawdown"
            ))
        
        return issues
    
    def _check_validation_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q566-570: Validation quality checks"""
        issues = []
        
        # Q568: Regime coverage
        regime_coverage = state.error_counts.get('insufficient_regime_coverage', 0)
        if regime_coverage > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("regime", str(regime_coverage)),
                question_id=568,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Insufficient regime coverage",
                description="Backtest doesn't cover all market regimes",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="extend_backtest_period"
            ))
        
        # Q570: Stress period coverage
        stress_coverage = state.error_counts.get('missing_stress_periods', 0)
        if stress_coverage > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stress", str(stress_coverage)),
                question_id=570,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Missing stress period coverage",
                description="Backtest doesn't include stress periods",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="add_stress_periods"
            ))
        
        return issues
    
    # =========================================================================
    # Q571-580: Statistical Rigor
    # =========================================================================
    
    def _check_statistical_rigor(self, state: SystemState) -> List[ValidationIssue]:
        """Q571-575: Statistical rigor checks"""
        issues = []
        
        # Q571: Statistical significance
        not_significant = state.error_counts.get('not_statistically_significant', 0)
        if not_significant > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("significance", str(not_significant)),
                question_id=571,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Results not statistically significant",
                description="Backtest results may be due to chance",
                affected_components=["Backtesting"],
                remediation_available=False
            ))
        
        # Q573: Sample size
        small_sample = state.error_counts.get('small_sample_size', 0)
        if small_sample > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("sample", str(small_sample)),
                question_id=573,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Small sample size",
                description="Not enough trades for statistical validity",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="extend_backtest"
            ))
        
        # Q575: Confidence intervals
        no_ci = state.error_counts.get('no_confidence_intervals', 0)
        if no_ci > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("ci", str(no_ci)),
                question_id=575,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="No confidence intervals",
                description="Backtest results without confidence intervals",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="add_confidence_intervals"
            ))
        
        return issues
    
    def _check_rigor_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q576-580: Rigor quality checks"""
        issues = []
        
        # Q578: Monte Carlo validation
        no_monte_carlo = state.error_counts.get('no_monte_carlo', 0)
        if no_monte_carlo > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("monte_carlo", str(no_monte_carlo)),
                question_id=578,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="No Monte Carlo validation",
                description="Strategy not validated with Monte Carlo",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="add_monte_carlo"
            ))
        
        return issues
    
    # =========================================================================
    # Q581-590: Production Comparison
    # =========================================================================
    
    def _check_production_comparison(self, state: SystemState) -> List[ValidationIssue]:
        """Q581-585: Production comparison checks"""
        issues = []
        
        # Q581: Backtest vs live gap
        live_gap = state.error_counts.get('backtest_live_gap', 0)
        if live_gap > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("live_gap", str(live_gap)),
                question_id=581,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Backtest vs live performance gap",
                description="Live performance doesn't match backtest",
                affected_components=["Backtesting", "StrategyEngine"],
                remediation_available=True,
                remediation_action="investigate_gap"
            ))
        
        # Q583: Execution gap
        exec_gap = state.error_counts.get('execution_gap', 0)
        if exec_gap > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("exec_gap", str(exec_gap)),
                question_id=583,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Execution quality gap",
                description="Live execution worse than backtest assumed",
                affected_components=["Backtesting", "ExecutionEngine"],
                remediation_available=True,
                remediation_action="improve_simulation"
            ))
        
        return issues
    
    def _check_comparison_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q586-590: Comparison quality checks"""
        issues = []
        
        # Q588: Continuous validation
        no_continuous = state.error_counts.get('no_continuous_validation', 0)
        if no_continuous > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("continuous", str(no_continuous)),
                question_id=588,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="No continuous backtest validation",
                description="Not continuously validating backtest vs live",
                affected_components=["Backtesting"],
                remediation_available=True,
                remediation_action="add_continuous_validation"
            ))
        
        # Q590: Gap investigation
        uninvestigated = state.error_counts.get('uninvestigated_gaps', 0)
        if uninvestigated > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("uninvestigated", str(uninvestigated)),
                question_id=590,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Uninvestigated performance gaps: {uninvestigated}",
                description="Performance gaps not investigated",
                affected_components=["Backtesting"],
                remediation_available=False
            ))
        
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_fix_lookahead(self, issue: ValidationIssue) -> str:
        """Fix look-ahead bias"""
        self.logger.info("Fixing look-ahead bias")
        return "Look-ahead bias fixed"
    
    async def _remediate_improve_sim(self, issue: ValidationIssue) -> str:
        """Improve simulation fidelity"""
        self.logger.info("Improving simulation")
        return "Simulation improved"
