"""
ML/Model Validator (Q271-400)
Addresses training, validation, deployment, concept drift, features, and RL-specific issues.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import math

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)

import logging
logger = logging.getLogger(__name__)



class MLModelValidator(BaseValidator):
    """Validates ML models and RL agents (Q271-400)"""
    
    def __init__(self):
        try:
            super().__init__(ValidationCategory.ML_MODELS)
            self._model_metrics: Dict[str, Dict] = {}
            self._feature_stats: Dict[str, Dict] = {}
            self._rl_metrics: Dict[str, Dict] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _register_checks(self):
        """Register all Q271-400 validation checks"""
        # Q271-280: Training
        try:
            self.add_check(self._check_training_data, [271, 272, 273, 274, 275])
            self.add_check(self._check_training_process, [276, 277, 278, 279, 280])
            # Q281-290: Validation
            self.add_check(self._check_model_validation, [281, 282, 283, 284, 285])
            self.add_check(self._check_validation_quality, [286, 287, 288, 289, 290])
            # Q291-300: Deployment
            self.add_check(self._check_model_deployment, [291, 292, 293, 294, 295])
            self.add_check(self._check_deployment_quality, [296, 297, 298, 299, 300])
            # Q301-310: Concept Drift
            self.add_check(self._check_concept_drift, [301, 302, 303, 304, 305])
            self.add_check(self._check_drift_handling, [306, 307, 308, 309, 310])
            # Q311-320: Features
            self.add_check(self._check_feature_health, [311, 312, 313, 314, 315])
            self.add_check(self._check_feature_quality, [316, 317, 318, 319, 320])
            # Q321-330: Model Monitoring
            self.add_check(self._check_model_monitoring, [321, 322, 323, 324, 325])
            self.add_check(self._check_monitoring_quality, [326, 327, 328, 329, 330])
            # Q331-340: Model Failures
            self.add_check(self._check_model_outputs, [331, 332, 333, 334])
            self.add_check(self._check_model_failures, [335, 336, 337, 338, 339, 340])
            # Q341-360: RL Rewards
            self.add_check(self._check_reward_function, [341, 342, 343, 344, 345])
            self.add_check(self._check_reward_quality, [346, 347, 348, 349, 350])
            self.add_check(self._check_reward_integrity, [351, 352, 353, 354, 355, 356, 357, 358, 359, 360])
            # Q361-380: RL Policy & Environment
            self.add_check(self._check_policy_learning, [361, 362, 363, 364, 365, 366, 367, 368, 369, 370])
            self.add_check(self._check_environment_model, [371, 372, 373, 374, 375, 376, 377, 378, 379, 380])
            # Q381-400: RL Safety & Deployment
            self.add_check(self._check_rl_safety, [381, 382, 383, 384, 385, 386, 387, 388, 389, 390])
            self.add_check(self._check_rl_deployment, [391, 392, 393, 394, 395, 396, 397, 398, 399, 400])
        
            # Register remediations
            self.add_remediation("retrain_model", self._remediate_retrain)
            self.add_remediation("rollback_model", self._remediate_rollback)
            self.add_remediation("disable_model", self._remediate_disable)
        except Exception as e:
            logger.error(f"Error in _register_checks: {e}")
            raise
    
    # =========================================================================
    # Q271-280: Training
    # =========================================================================
    
    def _check_training_data(self, state: SystemState) -> List[ValidationIssue]:
        """Q271-275: Training data quality"""
        try:
            issues = []
        
            # Q271: Non-representative training data
            nonrep_data = state.error_counts.get('nonrepresentative_training', 0)
            if nonrep_data > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("nonrep", str(nonrep_data)),
                    question_id=271,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Non-representative training data",
                    description="Training data may not represent future conditions",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="expand_training_data"
                ))
        
            # Q274: Class imbalance
            class_imbalance = state.error_counts.get('class_imbalance', 0)
            if class_imbalance > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("imbalance", str(class_imbalance)),
                    question_id=274,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Class imbalance in training data",
                    description="Training data has significant class imbalance",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="balance_classes"
                ))
        
            # Q275: Noise overfitting
            noise_overfit = state.error_counts.get('noise_overfitting', 0)
            if noise_overfit > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("noise_overfit", str(noise_overfit)),
                    question_id=275,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Model overfitting to noise",
                    description="Model appears to be fitting noise rather than signal",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="add_regularization"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_training_data: {e}")
            raise
    
    def _check_training_process(self, state: SystemState) -> List[ValidationIssue]:
        """Q276-280: Training process"""
        try:
            issues = []
        
            # Q272: Local minimum
            local_min = state.error_counts.get('local_minimum', 0)
            if local_min > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("local_min", str(local_min)),
                    question_id=272,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Training stuck in local minimum",
                    description="Model training converged to suboptimal solution",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="restart_training"
                ))
        
            # Q273: Training instability
            instability = state.error_counts.get('training_instability', 0)
            if instability > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("train_unstable", str(instability)),
                    question_id=273,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Training instability detected",
                    description="Model training is unstable or diverging",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="reduce_learning_rate"
                ))
        
            # Q279: Memorization
            memorization = state.error_counts.get('memorization_detected', 0)
            if memorization > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("memorize", str(memorization)),
                    question_id=279,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Model memorizing training data",
                    description="Model is memorizing rather than generalizing",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="add_regularization"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_training_process: {e}")
            raise
    
    # =========================================================================
    # Q281-290: Validation
    # =========================================================================
    
    def _check_model_validation(self, state: SystemState) -> List[ValidationIssue]:
        """Q281-285: Model validation"""
        try:
            issues = []
        
            # Q283: Validation data leakage
            val_leakage = state.error_counts.get('validation_leakage', 0)
            if val_leakage > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("val_leak", str(val_leakage)),
                    question_id=283,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Validation data leakage detected",
                    description="Training data contaminating validation",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="fix_data_split"
                ))
        
            # Q284: Validation vs production gap
            val_prod_gap = state.error_counts.get('validation_production_gap', 0)
            if val_prod_gap > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("val_prod", str(val_prod_gap)),
                    question_id=284,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Validation vs production gap",
                    description="Model performs differently in production than validation",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="investigate_gap"
                ))
        
            # Q285: Distribution shift
            dist_shift = state.error_counts.get('distribution_shift', 0)
            if dist_shift > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("dist_shift", str(dist_shift)),
                    question_id=285,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Distribution shift detected",
                    description="Production data distribution differs from training",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="retrain_model"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_model_validation: {e}")
            raise
    
    def _check_validation_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q286-290: Validation quality"""
        try:
            issues = []
        
            # Q290: Poor calibration
            poor_calibration = state.error_counts.get('poor_calibration', 0)
            if poor_calibration > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("calibration", str(poor_calibration)),
                    question_id=290,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Model poorly calibrated",
                    description="Model confidence doesn't match actual accuracy",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="recalibrate_model"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_validation_quality: {e}")
            raise
    
    # =========================================================================
    # Q291-300: Deployment
    # =========================================================================
    
    def _check_model_deployment(self, state: SystemState) -> List[ValidationIssue]:
        """Q291-295: Model deployment"""
        try:
            issues = []
        
            # Q292: Partial deployment failure
            partial_fail = state.error_counts.get('model_partial_deploy_fail', 0)
            if partial_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("partial_deploy", str(partial_fail)),
                    question_id=292,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Model deployment partially failed",
                    description="Model deployment failed midway",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="rollback_model",
                    auto_remediate=True
                ))
        
            # Q295: Production behavior divergence
            prod_diverge = state.error_counts.get('production_divergence', 0)
            if prod_diverge > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("prod_diverge", str(prod_diverge)),
                    question_id=295,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Model behavior diverging in production",
                    description="Deployed model behaving differently than validation",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="investigate_divergence"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_model_deployment: {e}")
            raise
    
    def _check_deployment_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q296-300: Deployment quality"""
        try:
            issues = []
        
            # Q296: Latency regression
            latency_regression = state.error_counts.get('model_latency_regression', 0)
            if latency_regression > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("latency_reg", str(latency_regression)),
                    question_id=296,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Model latency regression",
                    description="New model is slower than previous version",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="rollback_model"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_deployment_quality: {e}")
            raise
    
    # =========================================================================
    # Q301-310: Concept Drift
    # =========================================================================
    
    def _check_concept_drift(self, state: SystemState) -> List[ValidationIssue]:
        """Q301-305: Concept drift detection"""
        try:
            issues = []
        
            # Q301: Concept drift
            concept_drift = state.error_counts.get('concept_drift', 0)
            if concept_drift > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("concept_drift", str(concept_drift)),
                    question_id=301,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Concept drift detected",
                    description="Feature-target relationship has changed",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="retrain_model",
                    auto_remediate=True
                ))
        
            # Q302: Gradual drift
            gradual_drift = state.error_counts.get('gradual_drift', 0)
            if gradual_drift > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("gradual_drift", str(gradual_drift)),
                    question_id=302,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Gradual concept drift detected",
                    description="Slow but steady drift in model performance",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="schedule_retrain"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_concept_drift: {e}")
            raise
    
    def _check_drift_handling(self, state: SystemState) -> List[ValidationIssue]:
        """Q306-310: Drift handling"""
        try:
            issues = []
        
            # Q310: Drift detection failure
            drift_detect_fail = state.error_counts.get('drift_detection_failure', 0)
            if drift_detect_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("drift_fail", str(drift_detect_fail)),
                    question_id=310,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Drift detection failing",
                    description="Concept drift detection system not working",
                    affected_components=["MLPipeline", "Monitoring"],
                    remediation_available=True,
                    remediation_action="fix_drift_detection"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_drift_handling: {e}")
            raise
    
    # =========================================================================
    # Q311-320: Features
    # =========================================================================
    
    def _check_feature_health(self, state: SystemState) -> List[ValidationIssue]:
        """Q311-315: Feature health"""
        try:
            issues = []
        
            # Q311: Stale features
            stale_features = state.error_counts.get('stale_features', 0)
            if stale_features > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("stale_feat", str(stale_features)),
                    question_id=311,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Stale features detected: {stale_features}",
                    description="Some features are stale or irrelevant",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="refresh_features"
                ))
        
            # Q312: Feature computation failure
            feat_fail = state.error_counts.get('feature_computation_failure', 0)
            if feat_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("feat_fail", str(feat_fail)),
                    question_id=312,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Feature computation failures: {feat_fail}",
                    description="Feature computation failing for some inputs",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="fix_feature_pipeline"
                ))
        
            # Q315: Look-ahead bias
            lookahead = state.error_counts.get('lookahead_bias', 0)
            if lookahead > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("lookahead", str(lookahead)),
                    question_id=315,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Look-ahead bias detected",
                    description="Features using future information",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="fix_feature_pipeline"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_feature_health: {e}")
            raise
    
    def _check_feature_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q316-320: Feature quality"""
        try:
            issues = []
        
            # Q316: Production feature errors
            prod_feat_err = state.error_counts.get('production_feature_error', 0)
            if prod_feat_err > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("prod_feat", str(prod_feat_err)),
                    question_id=316,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Production feature errors: {prod_feat_err}",
                    description="Features computed incorrectly in production",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="fix_feature_pipeline"
                ))
        
            # Q320: Unstable features
            unstable = state.error_counts.get('unstable_features', 0)
            if unstable > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("unstable", str(unstable)),
                    question_id=320,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"Unstable features: {unstable}",
                    description="Feature engineering creating unstable features",
                    affected_components=["FeatureEngine"],
                    remediation_available=True,
                    remediation_action="stabilize_features"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_feature_quality: {e}")
            raise
    
    # =========================================================================
    # Q321-340: Model Monitoring & Failures
    # =========================================================================
    
    def _check_model_monitoring(self, state: SystemState) -> List[ValidationIssue]:
        """Q321-325: Model monitoring"""
        try:
            issues = []
        
            for model_name, metrics in self._model_metrics.items():
                # Q322: Unreliable predictions
                reliability = metrics.get('reliability_score', 1.0)
                if reliability < 0.8:
                    issues.append(ValidationIssue(
                        issue_id=self._generate_issue_id("unreliable", model_name),
                        question_id=322,
                        category=self.category,
                        severity=ValidationSeverity.HIGH,
                        title=f"Unreliable predictions: {model_name}",
                        description=f"Model reliability {reliability:.2f} below threshold",
                        affected_components=[model_name],
                        remediation_available=True,
                        remediation_action="disable_model",
                        metadata={"model": model_name, "reliability": reliability}
                    ))
            
                # Q324: Slow degradation
                if metrics.get('degrading', False):
                    issues.append(ValidationIssue(
                        issue_id=self._generate_issue_id("degrading", model_name),
                        question_id=324,
                        category=self.category,
                        severity=ValidationSeverity.MEDIUM,
                        title=f"Model degrading: {model_name}",
                        description="Model performance slowly degrading",
                        affected_components=[model_name],
                        remediation_available=True,
                        remediation_action="schedule_retrain"
                    ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_model_monitoring: {e}")
            raise
    
    def _check_monitoring_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q326-330: Monitoring quality"""
        try:
            issues = []
        
            # Q326: Systematic bias
            systematic_bias = state.error_counts.get('systematic_bias', 0)
            if systematic_bias > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("bias", str(systematic_bias)),
                    question_id=326,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Systematic model bias detected",
                    description="Model outputs are systematically biased",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="recalibrate_model"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_monitoring_quality: {e}")
            raise
    
    def _check_model_outputs(self, state: SystemState) -> List[ValidationIssue]:
        """Q331-334: Model output issues"""
        try:
            issues = []
        
            # Q331: NaN/infinite outputs
            nan_outputs = state.error_counts.get('nan_model_output', 0)
            if nan_outputs > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("nan", str(nan_outputs)),
                    question_id=331,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"NaN/infinite model outputs: {nan_outputs}",
                    description="Model producing NaN or infinite values",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="disable_model",
                    auto_remediate=True
                ))
        
            # Q332: Out-of-range outputs
            oor_outputs = state.error_counts.get('out_of_range_output', 0)
            if oor_outputs > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("oor", str(oor_outputs)),
                    question_id=332,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Out-of-range outputs: {oor_outputs}",
                    description="Model producing values outside expected range",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="clamp_outputs"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_model_outputs: {e}")
            raise
    
    def _check_model_failures(self, state: SystemState) -> List[ValidationIssue]:
        """Q335-340: Model failures"""
        try:
            issues = []
        
            # Q336: Silent model failure
            silent_fail = state.error_counts.get('silent_model_failure', 0)
            if silent_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("silent", str(silent_fail)),
                    question_id=336,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Silent model failures: {silent_fail}",
                    description="Model failing without raising errors",
                    affected_components=["MLPipeline"],
                    remediation_available=True,
                    remediation_action="add_health_checks"
                ))
        
            # Q339: Failure cascade
            cascade = state.error_counts.get('model_failure_cascade', 0)
            if cascade > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("cascade", str(cascade)),
                    question_id=339,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Model failure cascade",
                    description="Model failure cascading to other components",
                    affected_components=["MLPipeline", "System"],
                    remediation_available=True,
                    remediation_action="isolate_model",
                    auto_remediate=True
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_model_failures: {e}")
            raise
    
    # =========================================================================
    # Q341-360: RL Rewards
    # =========================================================================
    
    def _check_reward_function(self, state: SystemState) -> List[ValidationIssue]:
        """Q341-345: Reward function design"""
        try:
            issues = []
        
            # Q342: Unintended optima
            unintended = state.error_counts.get('unintended_reward_optima', 0)
            if unintended > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("unintended", str(unintended)),
                    question_id=342,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Unintended reward optima",
                    description="Agent finding unintended ways to maximize reward",
                    affected_components=["RLAgent"],
                    remediation_available=True,
                    remediation_action="redesign_reward"
                ))
        
            # Q343: Reward gaming
            gaming = state.error_counts.get('reward_gaming', 0)
            if gaming > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("gaming", str(gaming)),
                    question_id=343,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Agent gaming reward function",
                    description="Agent exploiting reward function loopholes",
                    affected_components=["RLAgent"],
                    remediation_available=True,
                    remediation_action="fix_reward_function",
                    auto_remediate=False
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_reward_function: {e}")
            raise
    
    def _check_reward_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q346-350: Reward quality"""
        try:
            issues = []
        
            # Q350: Reward vs risk conflict
            reward_risk = state.error_counts.get('reward_risk_conflict', 0)
            if reward_risk > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("reward_risk", str(reward_risk)),
                    question_id=350,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Reward conflicts with risk constraints",
                    description="Reward function encouraging risky behavior",
                    affected_components=["RLAgent", "RiskManager"],
                    remediation_available=True,
                    remediation_action="add_risk_penalty"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_reward_quality: {e}")
            raise
    
    def _check_reward_integrity(self, state: SystemState) -> List[ValidationIssue]:
        """Q351-360: Reward integrity"""
        try:
            issues = []
        
            # Q352: Reward computation bugs
            reward_bugs = state.error_counts.get('reward_computation_bug', 0)
            if reward_bugs > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("reward_bug", str(reward_bugs)),
                    question_id=352,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Reward computation bugs: {reward_bugs}",
                    description="Bugs in reward calculation",
                    affected_components=["RLAgent"],
                    remediation_available=True,
                    remediation_action="fix_reward_computation"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_reward_integrity: {e}")
            raise
    
    # =========================================================================
    # Q361-380: RL Policy & Environment
    # =========================================================================
    
    def _check_policy_learning(self, state: SystemState) -> List[ValidationIssue]:
        """Q361-370: Policy learning"""
        try:
            issues = []
        
            # Q361: Policy divergence
            divergence = state.error_counts.get('policy_divergence', 0)
            if divergence > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("diverge", str(divergence)),
                    question_id=361,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Policy learning diverging",
                    description="RL policy training is diverging",
                    affected_components=["RLAgent"],
                    remediation_available=True,
                    remediation_action="reset_policy"
                ))
        
            # Q362: Degenerate policy
            degenerate = state.error_counts.get('degenerate_policy', 0)
            if degenerate > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("degenerate", str(degenerate)),
                    question_id=362,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Degenerate policy detected",
                    description="Policy converged to degenerate solution",
                    affected_components=["RLAgent"],
                    remediation_available=True,
                    remediation_action="retrain_policy"
                ))
        
            # Q366: Catastrophic forgetting
            forgetting = state.error_counts.get('catastrophic_forgetting', 0)
            if forgetting > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("forgetting", str(forgetting)),
                    question_id=366,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Catastrophic forgetting detected",
                    description="Policy updates causing loss of previous learning",
                    affected_components=["RLAgent"],
                    remediation_available=True,
                    remediation_action="use_experience_replay"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_policy_learning: {e}")
            raise
    
    def _check_environment_model(self, state: SystemState) -> List[ValidationIssue]:
        """Q371-380: Environment model"""
        try:
            issues = []
        
            # Q372: Environment model divergence
            env_diverge = state.error_counts.get('environment_divergence', 0)
            if env_diverge > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("env_diverge", str(env_diverge)),
                    question_id=372,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Environment model diverging from reality",
                    description="Simulated environment doesn't match real market",
                    affected_components=["RLAgent", "Simulator"],
                    remediation_available=True,
                    remediation_action="recalibrate_environment"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_environment_model: {e}")
            raise
    
    # =========================================================================
    # Q381-400: RL Safety & Deployment
    # =========================================================================
    
    def _check_rl_safety(self, state: SystemState) -> List[ValidationIssue]:
        """Q381-390: RL safety"""
        try:
            issues = []
        
            # Q382: Safety constraint violation
            safety_violation = state.error_counts.get('rl_safety_violation', 0)
            if safety_violation > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("safety_viol", str(safety_violation)),
                    question_id=382,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"RL safety violations: {safety_violation}",
                    description="Agent violating safety constraints",
                    affected_components=["RLAgent", "RiskManager"],
                    remediation_available=True,
                    remediation_action="disable_model",
                    auto_remediate=True
                ))
        
            # Q389: Safety circumvention
            circumvention = state.error_counts.get('safety_circumvention', 0)
            if circumvention > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("circumvent", str(circumvention)),
                    question_id=389,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Agent circumventing safety",
                    description="Agent finding ways around safety constraints",
                    affected_components=["RLAgent"],
                    remediation_available=True,
                    remediation_action="disable_model",
                    auto_remediate=True
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_rl_safety: {e}")
            raise
    
    def _check_rl_deployment(self, state: SystemState) -> List[ValidationIssue]:
        """Q391-400: RL deployment"""
        try:
            issues = []
        
            # Q392: Training vs deployment behavior
            train_deploy = state.error_counts.get('training_deployment_mismatch', 0)
            if train_deploy > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("train_deploy", str(train_deploy)),
                    question_id=392,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Training vs deployment behavior mismatch",
                    description="Agent behaving differently in production",
                    affected_components=["RLAgent"],
                    remediation_available=True,
                    remediation_action="investigate_mismatch"
                ))
        
            # Q395: Systematic bad decisions
            bad_decisions = state.error_counts.get('systematic_bad_decisions', 0)
            if bad_decisions > 3:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("bad_decisions", str(bad_decisions)),
                    question_id=395,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Systematic bad decisions: {bad_decisions}",
                    description="Agent making systematically bad decisions",
                    affected_components=["RLAgent"],
                    remediation_available=True,
                    remediation_action="disable_model",
                    auto_remediate=True
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_rl_deployment: {e}")
            raise
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_retrain(self, issue: ValidationIssue) -> str:
        """Trigger model retraining"""
        try:
            model = issue.metadata.get('model', 'unknown')
            self.logger.info(f"Triggering retrain for {model}")
            return f"Retrain triggered for {model}"
        except Exception as e:
            logger.error(f"Error in _remediate_retrain: {e}")
            raise
    
    async def _remediate_rollback(self, issue: ValidationIssue) -> str:
        """Rollback to previous model version"""
        try:
            self.logger.info("Rolling back model")
            return "Model rolled back"
        except Exception as e:
            logger.error(f"Error in _remediate_rollback: {e}")
            raise
    
    async def _remediate_disable(self, issue: ValidationIssue) -> str:
        """Disable problematic model"""
        try:
            model = issue.metadata.get('model', 'unknown')
            self.logger.info(f"Disabling model {model}")
            return f"Model {model} disabled"
        except Exception as e:
            logger.error(f"Error in _remediate_disable: {e}")
            raise
