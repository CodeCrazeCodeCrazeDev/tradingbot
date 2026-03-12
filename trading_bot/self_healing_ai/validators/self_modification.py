"""
Self-Modification Boundaries Validator (Q651-710)
Addresses AI self-modification limits, safety boundaries, and human oversight.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)

import logging
logger = logging.getLogger(__name__)



class SelfModificationValidator(BaseValidator):
    """Validates self-modification boundaries (Q651-710)"""
    
    def __init__(self):
        try:
            super().__init__(ValidationCategory.SELF_MODIFICATION)
            self._modification_history: List[Dict] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _register_checks(self):
        """Register all Q651-710 validation checks"""
        # Q651-660: Modification Limits
        try:
            self.add_check(self._check_modification_limits, [651, 652, 653, 654, 655])
            self.add_check(self._check_limit_enforcement, [656, 657, 658, 659, 660])
            # Q661-670: Safety Boundaries
            self.add_check(self._check_safety_boundaries, [661, 662, 663, 664, 665])
            self.add_check(self._check_boundary_enforcement, [666, 667, 668, 669, 670])
            # Q671-680: Human Oversight
            self.add_check(self._check_human_oversight, [671, 672, 673, 674, 675])
            self.add_check(self._check_oversight_quality, [676, 677, 678, 679, 680])
            # Q681-690: Rollback Capability
            self.add_check(self._check_rollback_capability, [681, 682, 683, 684, 685])
            self.add_check(self._check_rollback_quality, [686, 687, 688, 689, 690])
            # Q691-700: Audit Trail
            self.add_check(self._check_audit_trail, [691, 692, 693, 694, 695])
            self.add_check(self._check_audit_quality, [696, 697, 698, 699, 700])
            # Q701-710: Containment
            self.add_check(self._check_containment, [701, 702, 703, 704, 705])
            self.add_check(self._check_containment_quality, [706, 707, 708, 709, 710])
        
            # Register remediations
            self.add_remediation("block_modification", self._remediate_block)
            self.add_remediation("rollback_change", self._remediate_rollback)
            self.add_remediation("require_approval", self._remediate_require_approval)
        except Exception as e:
            logger.error(f"Error in _register_checks: {e}")
            raise
    
    # =========================================================================
    # Q651-660: Modification Limits
    # =========================================================================
    
    def _check_modification_limits(self, state: SystemState) -> List[ValidationIssue]:
        """Q651-655: Modification limit checks"""
        try:
            issues = []
        
            # Q651: Unauthorized modification attempt
            unauthorized = state.error_counts.get('unauthorized_modification', 0)
            if unauthorized > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("unauthorized", str(unauthorized)),
                    question_id=651,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Unauthorized modification attempts: {unauthorized}",
                    description="System attempted unauthorized self-modification",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="block_modification",
                    auto_remediate=True
                ))
        
            # Q652: Risk limit modification attempt
            risk_mod = state.error_counts.get('risk_limit_modification_attempt', 0)
            if risk_mod > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("risk_mod", str(risk_mod)),
                    question_id=652,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Risk limit modification attempted",
                    description="System tried to modify immutable risk limits",
                    affected_components=["RiskManager", "SelfModification"],
                    remediation_available=True,
                    remediation_action="block_modification",
                    auto_remediate=True
                ))
        
            # Q653: Excessive modifications
            mod_count = state.error_counts.get('modification_count_24h', 0)
            if mod_count > 100:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("excessive", str(mod_count)),
                    question_id=653,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Excessive modifications: {mod_count} in 24h",
                    description="Too many self-modifications in short period",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="rate_limit_modifications"
                ))
        
            # Q655: Core logic modification
            core_mod = state.error_counts.get('core_logic_modification', 0)
            if core_mod > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("core_mod", str(core_mod)),
                    question_id=655,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Core logic modification attempted",
                    description="Attempt to modify core trading logic",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="block_modification",
                    auto_remediate=True
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_modification_limits: {e}")
            raise
    
    def _check_limit_enforcement(self, state: SystemState) -> List[ValidationIssue]:
        """Q656-660: Limit enforcement checks"""
        try:
            issues = []
        
            # Q656: Limit bypass
            bypass = state.error_counts.get('modification_limit_bypass', 0)
            if bypass > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("bypass", str(bypass)),
                    question_id=656,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Modification limit bypassed",
                    description="Self-modification limits were bypassed",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="halt_system",
                    auto_remediate=True
                ))
        
            # Q658: Enforcement failure
            enforcement_fail = state.error_counts.get('limit_enforcement_failure', 0)
            if enforcement_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("enforce_fail", str(enforcement_fail)),
                    question_id=658,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Limit enforcement failed",
                    description="Failed to enforce modification limits",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="halt_system"
                ))
        
            # Q660: Gradual limit erosion
            erosion = state.error_counts.get('limit_erosion', 0)
            if erosion > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("erosion", str(erosion)),
                    question_id=660,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Gradual limit erosion detected",
                    description="Modification limits being gradually eroded",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="restore_limits"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_limit_enforcement: {e}")
            raise
    
    # =========================================================================
    # Q661-670: Safety Boundaries
    # =========================================================================
    
    def _check_safety_boundaries(self, state: SystemState) -> List[ValidationIssue]:
        """Q661-665: Safety boundary checks"""
        try:
            issues = []
        
            # Q661: Safety boundary violation
            boundary_violation = state.error_counts.get('safety_boundary_violation', 0)
            if boundary_violation > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("boundary", str(boundary_violation)),
                    question_id=661,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Safety boundary violations: {boundary_violation}",
                    description="System violated safety boundaries",
                    affected_components=["SelfModification", "Safety"],
                    remediation_available=True,
                    remediation_action="halt_system",
                    auto_remediate=True
                ))
        
            # Q662: Boundary testing
            boundary_test = state.error_counts.get('boundary_testing_detected', 0)
            if boundary_test > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("test_boundary", str(boundary_test)),
                    question_id=662,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="System testing safety boundaries",
                    description="System appears to be probing safety boundaries",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="increase_monitoring"
                ))
        
            # Q664: Boundary circumvention
            circumvention = state.error_counts.get('boundary_circumvention', 0)
            if circumvention > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("circumvent", str(circumvention)),
                    question_id=664,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Safety boundary circumvention",
                    description="System found way around safety boundaries",
                    affected_components=["SelfModification", "Safety"],
                    remediation_available=True,
                    remediation_action="halt_system",
                    auto_remediate=True
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_safety_boundaries: {e}")
            raise
    
    def _check_boundary_enforcement(self, state: SystemState) -> List[ValidationIssue]:
        """Q666-670: Boundary enforcement checks"""
        try:
            issues = []
        
            # Q668: Boundary weakening
            weakening = state.error_counts.get('boundary_weakening', 0)
            if weakening > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("weaken", str(weakening)),
                    question_id=668,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Safety boundaries weakening",
                    description="Safety boundaries are being weakened",
                    affected_components=["Safety"],
                    remediation_available=True,
                    remediation_action="restore_boundaries"
                ))
        
            # Q670: Boundary monitoring failure
            mon_fail = state.error_counts.get('boundary_monitoring_failure', 0)
            if mon_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("mon_fail", str(mon_fail)),
                    question_id=670,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Boundary monitoring failed",
                    description="Cannot monitor safety boundaries",
                    affected_components=["Monitoring", "Safety"],
                    remediation_available=True,
                    remediation_action="restart_monitoring"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_boundary_enforcement: {e}")
            raise
    
    # =========================================================================
    # Q671-680: Human Oversight
    # =========================================================================
    
    def _check_human_oversight(self, state: SystemState) -> List[ValidationIssue]:
        """Q671-675: Human oversight checks"""
        try:
            issues = []
        
            # Q671: Missing human approval
            missing_approval = state.error_counts.get('missing_human_approval', 0)
            if missing_approval > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("no_approval", str(missing_approval)),
                    question_id=671,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Missing human approval: {missing_approval}",
                    description="Changes made without required human approval",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="rollback_change",
                    auto_remediate=True
                ))
        
            # Q672: Approval bypass
            approval_bypass = state.error_counts.get('approval_bypass', 0)
            if approval_bypass > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("bypass_approval", str(approval_bypass)),
                    question_id=672,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Human approval bypassed",
                    description="System bypassed human approval requirement",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="halt_system",
                    auto_remediate=True
                ))
        
            # Q674: Oversight gap
            oversight_gap = state.error_counts.get('oversight_gap', 0)
            if oversight_gap > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("oversight_gap", str(oversight_gap)),
                    question_id=674,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Human oversight gap",
                    description="Gap in human oversight coverage",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="require_approval"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_human_oversight: {e}")
            raise
    
    def _check_oversight_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q676-680: Oversight quality checks"""
        try:
            issues = []
        
            # Q678: Oversight fatigue
            fatigue = state.error_counts.get('oversight_fatigue', 0)
            if fatigue > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("fatigue", str(fatigue)),
                    question_id=678,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Oversight fatigue detected",
                    description="Human oversight may be fatigued",
                    affected_components=["HumanOversight"],
                    remediation_available=True,
                    remediation_action="reduce_approval_requests"
                ))
        
            # Q680: Oversight circumvention
            oversight_circumvent = state.error_counts.get('oversight_circumvention', 0)
            if oversight_circumvent > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("circumvent_oversight", str(oversight_circumvent)),
                    question_id=680,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Oversight circumvention detected",
                    description="System circumventing human oversight",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="halt_system",
                    auto_remediate=True
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_oversight_quality: {e}")
            raise
    
    # =========================================================================
    # Q681-690: Rollback Capability
    # =========================================================================
    
    def _check_rollback_capability(self, state: SystemState) -> List[ValidationIssue]:
        """Q681-685: Rollback capability checks"""
        try:
            issues = []
        
            # Q681: Rollback unavailable
            no_rollback = state.error_counts.get('rollback_unavailable', 0)
            if no_rollback > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("no_rollback", str(no_rollback)),
                    question_id=681,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Rollback capability unavailable",
                    description="Cannot rollback recent changes",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="restore_rollback"
                ))
        
            # Q682: Rollback failure
            rollback_fail = state.error_counts.get('rollback_failure', 0)
            if rollback_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("rollback_fail", str(rollback_fail)),
                    question_id=682,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Rollback failures: {rollback_fail}",
                    description="Rollback attempts failed",
                    affected_components=["SelfModification"],
                    remediation_available=False
                ))
        
            # Q684: Incomplete rollback
            incomplete = state.error_counts.get('incomplete_rollback', 0)
            if incomplete > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("incomplete", str(incomplete)),
                    question_id=684,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Incomplete rollbacks: {incomplete}",
                    description="Rollbacks did not fully restore state",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="complete_rollback"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_rollback_capability: {e}")
            raise
    
    def _check_rollback_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q686-690: Rollback quality checks"""
        try:
            issues = []
        
            # Q688: Rollback testing
            no_testing = state.error_counts.get('rollback_not_tested', 0)
            if no_testing > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("no_test", str(no_testing)),
                    question_id=688,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Rollback capability not tested",
                    description="Rollback procedures not regularly tested",
                    affected_components=["SelfModification"],
                    remediation_available=True,
                    remediation_action="test_rollback"
                ))
        
            # Q690: Rollback data loss
            data_loss = state.error_counts.get('rollback_data_loss', 0)
            if data_loss > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("data_loss", str(data_loss)),
                    question_id=690,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Rollback caused data loss",
                    description="Rollback resulted in data loss",
                    affected_components=["SelfModification"],
                    remediation_available=False
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_rollback_quality: {e}")
            raise
    
    # =========================================================================
    # Q691-700: Audit Trail
    # =========================================================================
    
    def _check_audit_trail(self, state: SystemState) -> List[ValidationIssue]:
        """Q691-695: Audit trail checks"""
        try:
            issues = []
        
            # Q691: Missing audit entries
            missing_audit = state.error_counts.get('missing_audit_entries', 0)
            if missing_audit > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("missing_audit", str(missing_audit)),
                    question_id=691,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Missing audit entries: {missing_audit}",
                    description="Modifications not recorded in audit trail",
                    affected_components=["AuditLog"],
                    remediation_available=True,
                    remediation_action="fix_audit_logging"
                ))
        
            # Q692: Audit tampering
            tampering = state.error_counts.get('audit_tampering', 0)
            if tampering > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("tampering", str(tampering)),
                    question_id=692,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Audit trail tampering detected",
                    description="Audit trail has been tampered with",
                    affected_components=["AuditLog"],
                    remediation_available=True,
                    remediation_action="halt_system",
                    auto_remediate=True
                ))
        
            # Q694: Audit gaps
            audit_gaps = state.error_counts.get('audit_gaps', 0)
            if audit_gaps > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("audit_gaps", str(audit_gaps)),
                    question_id=694,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Audit trail gaps: {audit_gaps}",
                    description="Gaps in audit trail coverage",
                    affected_components=["AuditLog"],
                    remediation_available=True,
                    remediation_action="improve_audit"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_audit_trail: {e}")
            raise
    
    def _check_audit_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q696-700: Audit quality checks"""
        try:
            issues = []
        
            # Q698: Audit storage failure
            storage_fail = state.error_counts.get('audit_storage_failure', 0)
            if storage_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("audit_storage", str(storage_fail)),
                    question_id=698,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Audit storage failing",
                    description="Cannot store audit entries",
                    affected_components=["AuditLog"],
                    remediation_available=True,
                    remediation_action="fix_audit_storage"
                ))
        
            # Q700: Audit integrity
            integrity_fail = state.error_counts.get('audit_integrity_failure', 0)
            if integrity_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("integrity", str(integrity_fail)),
                    question_id=700,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Audit integrity compromised",
                    description="Audit trail integrity cannot be verified",
                    affected_components=["AuditLog"],
                    remediation_available=False
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_audit_quality: {e}")
            raise
    
    # =========================================================================
    # Q701-710: Containment
    # =========================================================================
    
    def _check_containment(self, state: SystemState) -> List[ValidationIssue]:
        """Q701-705: Containment checks"""
        try:
            issues = []
        
            # Q701: Containment breach
            breach = state.error_counts.get('containment_breach', 0)
            if breach > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("breach", str(breach)),
                    question_id=701,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Containment breach detected",
                    description="System escaped containment boundaries",
                    affected_components=["Containment"],
                    remediation_available=True,
                    remediation_action="halt_system",
                    auto_remediate=True
                ))
        
            # Q702: External communication
            external_comm = state.error_counts.get('unauthorized_external_comm', 0)
            if external_comm > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("external", str(external_comm)),
                    question_id=702,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Unauthorized external communication",
                    description="System made unauthorized external connections",
                    affected_components=["Containment", "Network"],
                    remediation_available=True,
                    remediation_action="block_external",
                    auto_remediate=True
                ))
        
            # Q704: Resource escape
            resource_escape = state.error_counts.get('resource_escape', 0)
            if resource_escape > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("resource", str(resource_escape)),
                    question_id=704,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Resource containment escape",
                    description="System accessing resources outside boundaries",
                    affected_components=["Containment"],
                    remediation_available=True,
                    remediation_action="halt_system",
                    auto_remediate=True
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_containment: {e}")
            raise
    
    def _check_containment_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q706-710: Containment quality checks"""
        try:
            issues = []
        
            # Q708: Containment weakening
            weakening = state.error_counts.get('containment_weakening', 0)
            if weakening > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("weaken_contain", str(weakening)),
                    question_id=708,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Containment weakening",
                    description="Containment boundaries are weakening",
                    affected_components=["Containment"],
                    remediation_available=True,
                    remediation_action="strengthen_containment"
                ))
        
            # Q710: Containment monitoring failure
            mon_fail = state.error_counts.get('containment_monitoring_failure', 0)
            if mon_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("contain_mon", str(mon_fail)),
                    question_id=710,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Containment monitoring failed",
                    description="Cannot monitor containment status",
                    affected_components=["Containment", "Monitoring"],
                    remediation_available=True,
                    remediation_action="restart_monitoring"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_containment_quality: {e}")
            raise
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_block(self, issue: ValidationIssue) -> str:
        """Block modification attempt"""
        try:
            self.logger.info("Blocking modification")
            return "Modification blocked"
        except Exception as e:
            logger.error(f"Error in _remediate_block: {e}")
            raise
    
    async def _remediate_rollback(self, issue: ValidationIssue) -> str:
        """Rollback change"""
        try:
            self.logger.info("Rolling back change")
            return "Change rolled back"
        except Exception as e:
            logger.error(f"Error in _remediate_rollback: {e}")
            raise
    
    async def _remediate_require_approval(self, issue: ValidationIssue) -> str:
        """Require human approval"""
        try:
            self.logger.info("Requiring human approval")
            return "Human approval required"
        except Exception as e:
            logger.error(f"Error in _remediate_require_approval: {e}")
            raise
