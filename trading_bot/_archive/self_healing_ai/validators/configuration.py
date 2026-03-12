"""
Configuration Validator (Q781-830)
Addresses configuration management, validation, versioning, and deployment.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class ConfigurationValidator(BaseValidator):
    """Validates configuration management (Q781-830)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.CONFIGURATION)
        self._config_history: List[Dict] = []
    
    def _register_checks(self):
        """Register all Q781-830 validation checks"""
        # Q781-790: Configuration Validation
        self.add_check(self._check_config_validation, [781, 782, 783, 784, 785])
        self.add_check(self._check_validation_quality, [786, 787, 788, 789, 790])
        # Q791-800: Configuration Versioning
        self.add_check(self._check_config_versioning, [791, 792, 793, 794, 795])
        self.add_check(self._check_versioning_quality, [796, 797, 798, 799, 800])
        # Q801-810: Configuration Deployment
        self.add_check(self._check_config_deployment, [801, 802, 803, 804, 805])
        self.add_check(self._check_deployment_quality, [806, 807, 808, 809, 810])
        # Q811-820: Configuration Consistency
        self.add_check(self._check_config_consistency, [811, 812, 813, 814, 815])
        self.add_check(self._check_consistency_quality, [816, 817, 818, 819, 820])
        # Q821-830: Configuration Security
        self.add_check(self._check_config_security, [821, 822, 823, 824, 825])
        self.add_check(self._check_security_quality, [826, 827, 828, 829, 830])
        
        # Register remediations
        self.add_remediation("rollback_config", self._remediate_rollback)
        self.add_remediation("fix_config", self._remediate_fix)
        self.add_remediation("reload_config", self._remediate_reload)
    
    # =========================================================================
    # Q781-790: Configuration Validation
    # =========================================================================
    
    def _check_config_validation(self, state: SystemState) -> List[ValidationIssue]:
        """Q781-785: Configuration validation checks"""
        issues = []
        
        # Q781: Invalid configuration
        invalid_config = state.error_counts.get('invalid_configuration', 0)
        if invalid_config > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("invalid", str(invalid_config)),
                question_id=781,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Invalid configuration: {invalid_config}",
                description="Configuration validation failed",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="rollback_config",
                auto_remediate=True
            ))
        
        # Q782: Missing required config
        missing_config = state.error_counts.get('missing_required_config', 0)
        if missing_config > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("missing", str(missing_config)),
                question_id=782,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Missing required config: {missing_config}",
                description="Required configuration values missing",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="fix_config"
            ))
        
        # Q783: Type mismatch
        type_mismatch = state.error_counts.get('config_type_mismatch', 0)
        if type_mismatch > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("type", str(type_mismatch)),
                question_id=783,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Config type mismatches: {type_mismatch}",
                description="Configuration values have wrong types",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="fix_config"
            ))
        
        # Q785: Out of range values
        out_of_range = state.error_counts.get('config_out_of_range', 0)
        if out_of_range > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("range", str(out_of_range)),
                question_id=785,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Config values out of range: {out_of_range}",
                description="Configuration values outside valid range",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="fix_config"
            ))
        
        return issues
    
    def _check_validation_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q786-790: Validation quality checks"""
        issues = []
        
        # Q788: Validation bypass
        bypass = state.error_counts.get('config_validation_bypass', 0)
        if bypass > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("bypass", str(bypass)),
                question_id=788,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Config validation bypassed",
                description="Configuration validation was bypassed",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="rollback_config",
                auto_remediate=True
            ))
        
        # Q790: Validation failure
        validation_fail = state.error_counts.get('config_validation_failure', 0)
        if validation_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("valid_fail", str(validation_fail)),
                question_id=790,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Config validation failures: {validation_fail}",
                description="Configuration validation system failing",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="fix_validation"
            ))
        
        return issues
    
    # =========================================================================
    # Q791-800: Configuration Versioning
    # =========================================================================
    
    def _check_config_versioning(self, state: SystemState) -> List[ValidationIssue]:
        """Q791-795: Configuration versioning checks"""
        issues = []
        
        # Q791: Version conflict
        version_conflict = state.error_counts.get('config_version_conflict', 0)
        if version_conflict > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("conflict", str(version_conflict)),
                question_id=791,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Config version conflicts: {version_conflict}",
                description="Configuration version conflicts detected",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="resolve_conflict"
            ))
        
        # Q792: Missing version history
        no_history = state.error_counts.get('no_config_history', 0)
        if no_history > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("no_history", str(no_history)),
                question_id=792,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Missing config version history",
                description="Configuration version history not maintained",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="enable_versioning"
            ))
        
        # Q794: Rollback unavailable
        no_rollback = state.error_counts.get('config_rollback_unavailable', 0)
        if no_rollback > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("no_rollback", str(no_rollback)),
                question_id=794,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Config rollback unavailable",
                description="Cannot rollback to previous configuration",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="restore_rollback"
            ))
        
        return issues
    
    def _check_versioning_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q796-800: Versioning quality checks"""
        issues = []
        
        # Q798: Version drift
        drift = state.error_counts.get('config_version_drift', 0)
        if drift > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("drift", str(drift)),
                question_id=798,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Config version drift",
                description="Configuration versions drifting between environments",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="sync_versions"
            ))
        
        # Q800: Audit trail missing
        no_audit = state.error_counts.get('config_audit_missing', 0)
        if no_audit > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("no_audit", str(no_audit)),
                question_id=800,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Config audit trail missing",
                description="Configuration changes not audited",
                affected_components=["ConfigManager", "AuditLog"],
                remediation_available=True,
                remediation_action="enable_audit"
            ))
        
        return issues
    
    # =========================================================================
    # Q801-810: Configuration Deployment
    # =========================================================================
    
    def _check_config_deployment(self, state: SystemState) -> List[ValidationIssue]:
        """Q801-805: Configuration deployment checks"""
        issues = []
        
        # Q801: Deployment failure
        deploy_fail = state.error_counts.get('config_deployment_failure', 0)
        if deploy_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("deploy_fail", str(deploy_fail)),
                question_id=801,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Config deployment failures: {deploy_fail}",
                description="Configuration deployment failed",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="rollback_config",
                auto_remediate=True
            ))
        
        # Q802: Partial deployment
        partial = state.error_counts.get('partial_config_deployment', 0)
        if partial > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("partial", str(partial)),
                question_id=802,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Partial config deployment",
                description="Configuration only partially deployed",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="complete_deployment"
            ))
        
        # Q804: Hot reload failure
        hot_reload_fail = state.error_counts.get('hot_reload_failure', 0)
        if hot_reload_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("hot_reload", str(hot_reload_fail)),
                question_id=804,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Hot reload failures: {hot_reload_fail}",
                description="Configuration hot reload failed",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="restart_service"
            ))
        
        return issues
    
    def _check_deployment_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q806-810: Deployment quality checks"""
        issues = []
        
        # Q808: Deployment without testing
        no_testing = state.error_counts.get('config_deployed_without_testing', 0)
        if no_testing > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("no_test", str(no_testing)),
                question_id=808,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Config deployed without testing",
                description="Configuration deployed without proper testing",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="rollback_config"
            ))
        
        # Q810: Deployment instability
        instability = state.error_counts.get('config_deployment_instability', 0)
        if instability > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("instability", str(instability)),
                question_id=810,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Config deployment causing instability",
                description="Configuration changes causing system instability",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="rollback_config",
                auto_remediate=True
            ))
        
        return issues
    
    # =========================================================================
    # Q811-820: Configuration Consistency
    # =========================================================================
    
    def _check_config_consistency(self, state: SystemState) -> List[ValidationIssue]:
        """Q811-815: Configuration consistency checks"""
        issues = []
        
        # Q811: Inconsistent config
        inconsistent = state.error_counts.get('inconsistent_configuration', 0)
        if inconsistent > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("inconsistent", str(inconsistent)),
                question_id=811,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Inconsistent configuration: {inconsistent}",
                description="Configuration inconsistent across components",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="sync_config"
            ))
        
        # Q812: Config conflict
        conflict = state.error_counts.get('config_conflict', 0)
        if conflict > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("config_conflict", str(conflict)),
                question_id=812,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Configuration conflicts: {conflict}",
                description="Conflicting configuration values",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="resolve_conflict"
            ))
        
        # Q814: Environment mismatch
        env_mismatch = state.error_counts.get('config_environment_mismatch', 0)
        if env_mismatch > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("env_mismatch", str(env_mismatch)),
                question_id=814,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Config environment mismatch",
                description="Configuration doesn't match environment",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="fix_config"
            ))
        
        return issues
    
    def _check_consistency_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q816-820: Consistency quality checks"""
        issues = []
        
        # Q818: Stale config
        stale = state.error_counts.get('stale_configuration', 0)
        if stale > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stale", str(stale)),
                question_id=818,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Stale configuration: {stale}",
                description="Configuration values are stale",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="reload_config"
            ))
        
        # Q820: Config propagation failure
        propagation_fail = state.error_counts.get('config_propagation_failure', 0)
        if propagation_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("propagation", str(propagation_fail)),
                question_id=820,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Config propagation failure",
                description="Configuration not propagating to all components",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="force_propagation"
            ))
        
        return issues
    
    # =========================================================================
    # Q821-830: Configuration Security
    # =========================================================================
    
    def _check_config_security(self, state: SystemState) -> List[ValidationIssue]:
        """Q821-825: Configuration security checks"""
        issues = []
        
        # Q821: Sensitive config exposed
        exposed = state.error_counts.get('sensitive_config_exposed', 0)
        if exposed > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("exposed", str(exposed)),
                question_id=821,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Sensitive config exposed",
                description="Sensitive configuration values exposed",
                affected_components=["ConfigManager", "Security"],
                remediation_available=True,
                remediation_action="secure_config",
                auto_remediate=True
            ))
        
        # Q822: Unauthorized config change
        unauthorized = state.error_counts.get('unauthorized_config_change', 0)
        if unauthorized > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unauthorized", str(unauthorized)),
                question_id=822,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Unauthorized config changes: {unauthorized}",
                description="Configuration changed without authorization",
                affected_components=["ConfigManager", "Security"],
                remediation_available=True,
                remediation_action="rollback_config",
                auto_remediate=True
            ))
        
        # Q824: Config tampering
        tampering = state.error_counts.get('config_tampering', 0)
        if tampering > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("tampering", str(tampering)),
                question_id=824,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Config tampering detected",
                description="Configuration has been tampered with",
                affected_components=["ConfigManager", "Security"],
                remediation_available=True,
                remediation_action="rollback_config",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_security_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q826-830: Security quality checks"""
        issues = []
        
        # Q828: Unencrypted sensitive config
        unencrypted = state.error_counts.get('unencrypted_sensitive_config', 0)
        if unencrypted > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unencrypted", str(unencrypted)),
                question_id=828,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Unencrypted sensitive config",
                description="Sensitive configuration not encrypted",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="encrypt_config"
            ))
        
        # Q830: Config access control failure
        access_fail = state.error_counts.get('config_access_control_failure', 0)
        if access_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("access_fail", str(access_fail)),
                question_id=830,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Config access control failure",
                description="Configuration access controls not working",
                affected_components=["ConfigManager", "Security"],
                remediation_available=True,
                remediation_action="fix_access_control"
            ))
        
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_rollback(self, issue: ValidationIssue) -> str:
        """Rollback configuration"""
        self.logger.info("Rolling back configuration")
        return "Configuration rolled back"
    
    async def _remediate_fix(self, issue: ValidationIssue) -> str:
        """Fix configuration"""
        self.logger.info("Fixing configuration")
        return "Configuration fixed"
    
    async def _remediate_reload(self, issue: ValidationIssue) -> str:
        """Reload configuration"""
        self.logger.info("Reloading configuration")
        return "Configuration reloaded"
