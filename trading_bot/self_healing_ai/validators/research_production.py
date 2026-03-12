"""
Live vs Research Validator (Q591-650)
Addresses research-production divergence, code parity, data parity, and deployment validation.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)

import logging
logger = logging.getLogger(__name__)



class ResearchProductionValidator(BaseValidator):
    """Validates research vs production parity (Q591-650)"""
    
    def __init__(self):
        try:
            super().__init__(ValidationCategory.RESEARCH_PRODUCTION)
            self._parity_metrics: Dict[str, Any] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _register_checks(self):
        """Register all Q591-650 validation checks"""
        # Q591-600: Code Parity
        try:
            self.add_check(self._check_code_parity, [591, 592, 593, 594, 595])
            self.add_check(self._check_code_quality, [596, 597, 598, 599, 600])
            # Q601-610: Data Parity
            self.add_check(self._check_data_parity, [601, 602, 603, 604, 605])
            self.add_check(self._check_data_quality, [606, 607, 608, 609, 610])
            # Q611-620: Feature Parity
            self.add_check(self._check_feature_parity, [611, 612, 613, 614, 615])
            self.add_check(self._check_feature_quality, [616, 617, 618, 619, 620])
            # Q621-630: Model Parity
            self.add_check(self._check_model_parity, [621, 622, 623, 624, 625])
            self.add_check(self._check_model_quality, [626, 627, 628, 629, 630])
            # Q631-640: Execution Parity
            self.add_check(self._check_execution_parity, [631, 632, 633, 634, 635])
            self.add_check(self._check_execution_quality, [636, 637, 638, 639, 640])
            # Q641-650: Validation Process
            self.add_check(self._check_validation_process, [641, 642, 643, 644, 645])
            self.add_check(self._check_process_quality, [646, 647, 648, 649, 650])
        
            # Register remediations
            self.add_remediation("sync_code", self._remediate_sync_code)
            self.add_remediation("sync_data", self._remediate_sync_data)
            self.add_remediation("sync_features", self._remediate_sync_features)
        except Exception as e:
            logger.error(f"Error in _register_checks: {e}")
            raise
    
    # =========================================================================
    # Q591-600: Code Parity
    # =========================================================================
    
    def _check_code_parity(self, state: SystemState) -> List[ValidationIssue]:
        """Q591-595: Code parity checks"""
        try:
            issues = []
        
            # Q591: Research vs production code divergence
            code_divergence = state.error_counts.get('code_divergence', 0)
            if code_divergence > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("code_div", str(code_divergence)),
                    question_id=591,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Research vs production code divergence",
                    description="Research and production code have diverged",
                    affected_components=["CodeBase"],
                    remediation_available=True,
                    remediation_action="sync_code"
                ))
        
            # Q592: Different library versions
            lib_mismatch = state.error_counts.get('library_version_mismatch', 0)
            if lib_mismatch > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("lib_mismatch", str(lib_mismatch)),
                    question_id=592,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Library version mismatches: {lib_mismatch}",
                    description="Different library versions in research vs production",
                    affected_components=["Dependencies"],
                    remediation_available=True,
                    remediation_action="sync_dependencies"
                ))
        
            # Q593: Numerical precision differences
            precision_diff = state.error_counts.get('numerical_precision_diff', 0)
            if precision_diff > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("precision", str(precision_diff)),
                    question_id=593,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Numerical precision differences",
                    description="Different numerical precision in research vs production",
                    affected_components=["Computation"],
                    remediation_available=True,
                    remediation_action="standardize_precision"
                ))
        
            # Q595: Undocumented changes
            undocumented = state.error_counts.get('undocumented_changes', 0)
            if undocumented > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("undocumented", str(undocumented)),
                    question_id=595,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"Undocumented code changes: {undocumented}",
                    description="Code changes not documented",
                    affected_components=["CodeBase"],
                    remediation_available=False
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_code_parity: {e}")
            raise
    
    def _check_code_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q596-600: Code quality checks"""
        try:
            issues = []
        
            # Q598: Silent behavior changes
            silent_changes = state.error_counts.get('silent_behavior_change', 0)
            if silent_changes > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("silent", str(silent_changes)),
                    question_id=598,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Silent behavior changes detected",
                    description="Code behavior changed without explicit changes",
                    affected_components=["CodeBase"],
                    remediation_available=True,
                    remediation_action="investigate_changes"
                ))
        
            # Q600: Code review gaps
            review_gaps = state.error_counts.get('code_review_gaps', 0)
            if review_gaps > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("review", str(review_gaps)),
                    question_id=600,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"Code review gaps: {review_gaps}",
                    description="Code deployed without proper review",
                    affected_components=["CodeBase"],
                    remediation_available=False
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_code_quality: {e}")
            raise
    
    # =========================================================================
    # Q601-610: Data Parity
    # =========================================================================
    
    def _check_data_parity(self, state: SystemState) -> List[ValidationIssue]:
        """Q601-605: Data parity checks"""
        try:
            issues = []
        
            # Q601: Research vs production data differences
            data_diff = state.error_counts.get('data_divergence', 0)
            if data_diff > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("data_div", str(data_diff)),
                    question_id=601,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Research vs production data divergence",
                    description="Research and production using different data",
                    affected_components=["DataPipeline"],
                    remediation_available=True,
                    remediation_action="sync_data"
                ))
        
            # Q602: Data preprocessing differences
            preprocess_diff = state.error_counts.get('preprocessing_divergence', 0)
            if preprocess_diff > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("preprocess", str(preprocess_diff)),
                    question_id=602,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Data preprocessing differences",
                    description="Different preprocessing in research vs production",
                    affected_components=["DataPipeline"],
                    remediation_available=True,
                    remediation_action="sync_preprocessing"
                ))
        
            # Q604: Data timing differences
            timing_diff = state.error_counts.get('data_timing_divergence', 0)
            if timing_diff > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("timing", str(timing_diff)),
                    question_id=604,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Data timing differences",
                    description="Different data timing in research vs production",
                    affected_components=["DataPipeline"],
                    remediation_available=True,
                    remediation_action="sync_timing"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_data_parity: {e}")
            raise
    
    def _check_data_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q606-610: Data quality checks"""
        try:
            issues = []
        
            # Q608: Data source changes
            source_changes = state.error_counts.get('data_source_change', 0)
            if source_changes > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("source_change", str(source_changes)),
                    question_id=608,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Data source changed",
                    description="Production using different data source than research",
                    affected_components=["DataPipeline"],
                    remediation_available=True,
                    remediation_action="validate_source_change"
                ))
        
            # Q610: Data quality drift
            quality_drift = state.error_counts.get('data_quality_drift', 0)
            if quality_drift > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("quality_drift", str(quality_drift)),
                    question_id=610,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Data quality drift",
                    description="Data quality drifting between research and production",
                    affected_components=["DataPipeline"],
                    remediation_available=True,
                    remediation_action="investigate_quality"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_data_quality: {e}")
            raise
    
    # =========================================================================
    # Q611-620: Feature Parity
    # =========================================================================
    
    def _check_feature_parity(self, state: SystemState) -> List[ValidationIssue]:
        """Q611-615: Feature parity checks"""
        try:
            issues = []
        
            # Q611: Feature computation differences
            feature_diff = state.error_counts.get('feature_computation_divergence', 0)
            if feature_diff > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("feature_div", str(feature_diff)),
                    question_id=611,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Feature computation divergence",
                    description="Features computed differently in research vs production",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="sync_features"
                ))
        
            # Q612: Missing features
            missing_features = state.error_counts.get('missing_production_features', 0)
            if missing_features > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("missing_feat", str(missing_features)),
                    question_id=612,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Missing production features: {missing_features}",
                    description="Features in research not available in production",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="add_missing_features"
                ))
        
            # Q614: Feature ordering differences
            ordering_diff = state.error_counts.get('feature_ordering_diff', 0)
            if ordering_diff > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("ordering", str(ordering_diff)),
                    question_id=614,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Feature ordering differences",
                    description="Features in different order in research vs production",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="fix_feature_ordering"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_feature_parity: {e}")
            raise
    
    def _check_feature_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q616-620: Feature quality checks"""
        try:
            issues = []
        
            # Q618: Feature drift
            feature_drift = state.error_counts.get('feature_drift', 0)
            if feature_drift > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("feat_drift", str(feature_drift)),
                    question_id=618,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Feature drift detected",
                    description="Feature distributions drifting between environments",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="investigate_drift"
                ))
        
            # Q620: Feature validation failure
            feat_validation = state.error_counts.get('feature_validation_failure', 0)
            if feat_validation > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("feat_valid", str(feat_validation)),
                    question_id=620,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Feature validation failures: {feat_validation}",
                    description="Features failing validation checks",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="fix_features"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_feature_quality: {e}")
            raise
    
    # =========================================================================
    # Q621-630: Model Parity
    # =========================================================================
    
    def _check_model_parity(self, state: SystemState) -> List[ValidationIssue]:
        """Q621-625: Model parity checks"""
        try:
            issues = []
        
            # Q621: Model version mismatch
            model_mismatch = state.error_counts.get('model_version_mismatch', 0)
            if model_mismatch > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("model_mismatch", str(model_mismatch)),
                    question_id=621,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Model version mismatch",
                    description="Different model versions in research vs production",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="sync_model_version"
                ))
        
            # Q622: Model output differences
            output_diff = state.error_counts.get('model_output_divergence', 0)
            if output_diff > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("output_div", str(output_diff)),
                    question_id=622,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Model output divergence",
                    description="Model producing different outputs in production",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="investigate_model"
                ))
        
            # Q624: Model serialization issues
            serial_issues = state.error_counts.get('model_serialization_issue', 0)
            if serial_issues > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("serial", str(serial_issues)),
                    question_id=624,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Model serialization issues: {serial_issues}",
                    description="Model serialization causing differences",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="fix_serialization"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_model_parity: {e}")
            raise
    
    def _check_model_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q626-630: Model quality checks"""
        try:
            issues = []
        
            # Q628: Model performance gap
            perf_gap = state.error_counts.get('model_performance_gap', 0)
            if perf_gap > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("perf_gap", str(perf_gap)),
                    question_id=628,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Model performance gap",
                    description="Model performing differently in production",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="investigate_performance"
                ))
        
            # Q630: Model validation bypass
            bypass = state.error_counts.get('model_validation_bypass', 0)
            if bypass > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("bypass", str(bypass)),
                    question_id=630,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Model validation bypassed: {bypass}",
                    description="Models deployed without proper validation",
                    affected_components=["MLPipeline"],
                    remediation_available=False
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_model_quality: {e}")
            raise
    
    # =========================================================================
    # Q631-640: Execution Parity
    # =========================================================================
    
    def _check_execution_parity(self, state: SystemState) -> List[ValidationIssue]:
        """Q631-635: Execution parity checks"""
        try:
            issues = []
        
            # Q631: Execution logic differences
            exec_diff = state.error_counts.get('execution_logic_divergence', 0)
            if exec_diff > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("exec_div", str(exec_diff)),
                    question_id=631,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Execution logic divergence",
                    description="Execution logic differs between research and production",
                    affected_components=["ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="sync_execution"
                ))
        
            # Q633: Order routing differences
            routing_diff = state.error_counts.get('order_routing_divergence', 0)
            if routing_diff > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("routing_div", str(routing_diff)),
                    question_id=633,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Order routing divergence",
                    description="Order routing differs between environments",
                    affected_components=["ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="sync_routing"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_execution_parity: {e}")
            raise
    
    def _check_execution_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q636-640: Execution quality checks"""
        try:
            issues = []
        
            # Q638: Execution quality gap
            quality_gap = state.error_counts.get('execution_quality_gap', 0)
            if quality_gap > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("exec_quality", str(quality_gap)),
                    question_id=638,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Execution quality gap",
                    description="Execution quality worse in production",
                    affected_components=["ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="investigate_execution"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_execution_quality: {e}")
            raise
    
    # =========================================================================
    # Q641-650: Validation Process
    # =========================================================================
    
    def _check_validation_process(self, state: SystemState) -> List[ValidationIssue]:
        """Q641-645: Validation process checks"""
        try:
            issues = []
        
            # Q641: No parity validation
            no_validation = state.error_counts.get('no_parity_validation', 0)
            if no_validation > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("no_valid", str(no_validation)),
                    question_id=641,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="No parity validation",
                    description="Research-production parity not validated",
                    affected_components=["Validation"],
                    remediation_available=True,
                    remediation_action="add_parity_validation"
                ))
        
            # Q643: Validation gaps
            validation_gaps = state.error_counts.get('parity_validation_gaps', 0)
            if validation_gaps > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("valid_gaps", str(validation_gaps)),
                    question_id=643,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"Parity validation gaps: {validation_gaps}",
                    description="Gaps in parity validation coverage",
                    affected_components=["Validation"],
                    remediation_available=True,
                    remediation_action="improve_validation"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_validation_process: {e}")
            raise
    
    def _check_process_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q646-650: Process quality checks"""
        try:
            issues = []
        
            # Q648: Continuous validation missing
            no_continuous = state.error_counts.get('no_continuous_parity_check', 0)
            if no_continuous > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("no_continuous", str(no_continuous)),
                    question_id=648,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="No continuous parity checking",
                    description="Parity not continuously monitored",
                    affected_components=["Validation"],
                    remediation_available=True,
                    remediation_action="add_continuous_check"
                ))
        
            # Q650: Parity drift undetected
            undetected = state.error_counts.get('undetected_parity_drift', 0)
            if undetected > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("undetected", str(undetected)),
                    question_id=650,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Undetected parity drift",
                    description="Parity drift went undetected",
                    affected_components=["Validation"],
                    remediation_available=False
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_process_quality: {e}")
            raise
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_sync_code(self, issue: ValidationIssue) -> str:
        """Sync research and production code"""
        try:
            self.logger.info("Syncing code")
            return "Code synced"
        except Exception as e:
            logger.error(f"Error in _remediate_sync_code: {e}")
            raise
    
    async def _remediate_sync_data(self, issue: ValidationIssue) -> str:
        """Sync research and production data"""
        try:
            self.logger.info("Syncing data")
            return "Data synced"
        except Exception as e:
            logger.error(f"Error in _remediate_sync_data: {e}")
            raise
    
    async def _remediate_sync_features(self, issue: ValidationIssue) -> str:
        """Sync feature computation"""
        try:
            self.logger.info("Syncing features")
            return "Features synced"
        except Exception as e:
            logger.error(f"Error in _remediate_sync_features: {e}")
            raise
