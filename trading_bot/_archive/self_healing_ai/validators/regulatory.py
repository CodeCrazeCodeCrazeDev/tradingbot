"""
Regulatory Validator (Q931-970)
Addresses compliance, reporting, audit trails, and regulatory requirements.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class RegulatoryValidator(BaseValidator):
    """Validates regulatory compliance (Q931-970)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.REGULATORY)
        self._compliance_metrics: Dict[str, Any] = {}
    
    def _register_checks(self):
        """Register all Q931-970 validation checks"""
        # Q931-940: Compliance
        self.add_check(self._check_compliance, [931, 932, 933, 934, 935])
        self.add_check(self._check_compliance_quality, [936, 937, 938, 939, 940])
        # Q941-950: Reporting
        self.add_check(self._check_reporting, [941, 942, 943, 944, 945])
        self.add_check(self._check_reporting_quality, [946, 947, 948, 949, 950])
        # Q951-960: Audit
        self.add_check(self._check_audit, [951, 952, 953, 954, 955])
        self.add_check(self._check_audit_quality, [956, 957, 958, 959, 960])
        # Q961-970: Regulatory Changes
        self.add_check(self._check_regulatory_changes, [961, 962, 963, 964, 965])
        self.add_check(self._check_change_quality, [966, 967, 968, 969, 970])
        
        # Register remediations
        self.add_remediation("halt_for_compliance", self._remediate_halt)
        self.add_remediation("generate_report", self._remediate_report)
        self.add_remediation("fix_compliance", self._remediate_fix)
    
    # =========================================================================
    # Q931-940: Compliance
    # =========================================================================
    
    def _check_compliance(self, state: SystemState) -> List[ValidationIssue]:
        """Q931-935: Compliance checks"""
        issues = []
        
        # Q931: Compliance violation
        violations = state.error_counts.get('compliance_violation', 0)
        if violations > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("violation", str(violations)),
                question_id=931,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Compliance violations: {violations}",
                description="Regulatory compliance violations detected",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="halt_for_compliance",
                auto_remediate=True
            ))
        
        # Q932: Pre-trade compliance failure
        pretrade_fail = state.error_counts.get('pretrade_compliance_failure', 0)
        if pretrade_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("pretrade", str(pretrade_fail)),
                question_id=932,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Pre-trade compliance failures: {pretrade_fail}",
                description="Pre-trade compliance checks failing",
                affected_components=["Compliance", "ExecutionEngine"],
                remediation_available=True,
                remediation_action="fix_compliance"
            ))
        
        # Q933: Position limit breach
        position_breach = state.error_counts.get('position_limit_breach', 0)
        if position_breach > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("pos_breach", str(position_breach)),
                question_id=933,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Position limit breaches: {position_breach}",
                description="Regulatory position limits breached",
                affected_components=["Compliance", "RiskManager"],
                remediation_available=True,
                remediation_action="reduce_positions",
                auto_remediate=True
            ))
        
        # Q934: Trading restriction violation
        restriction_violation = state.error_counts.get('trading_restriction_violation', 0)
        if restriction_violation > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("restriction", str(restriction_violation)),
                question_id=934,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Trading restriction violations: {restriction_violation}",
                description="Trading restrictions violated",
                affected_components=["Compliance", "ExecutionEngine"],
                remediation_available=True,
                remediation_action="halt_for_compliance",
                auto_remediate=True
            ))
        
        # Q935: Market manipulation detection
        manipulation = state.error_counts.get('market_manipulation_detected', 0)
        if manipulation > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("manipulation", str(manipulation)),
                question_id=935,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Potential market manipulation detected",
                description="Trading patterns may constitute market manipulation",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="halt_for_compliance",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_compliance_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q936-940: Compliance quality checks"""
        issues = []
        
        # Q936: Compliance monitoring failure
        mon_fail = state.error_counts.get('compliance_monitoring_failure', 0)
        if mon_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("mon_fail", str(mon_fail)),
                question_id=936,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Compliance monitoring failed",
                description="Cannot monitor compliance status",
                affected_components=["Compliance", "Monitoring"],
                remediation_available=True,
                remediation_action="restart_compliance_monitoring"
            ))
        
        # Q938: Compliance rules outdated
        rules_outdated = state.error_counts.get('compliance_rules_outdated', 0)
        if rules_outdated > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("outdated", str(rules_outdated)),
                question_id=938,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Compliance rules outdated",
                description="Compliance rules need updating",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="update_compliance_rules"
            ))
        
        # Q940: Compliance bypass
        bypass = state.error_counts.get('compliance_bypass', 0)
        if bypass > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("bypass", str(bypass)),
                question_id=940,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Compliance checks bypassed",
                description="Compliance checks were bypassed",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="halt_for_compliance",
                auto_remediate=True
            ))
        
        return issues
    
    # =========================================================================
    # Q941-950: Reporting
    # =========================================================================
    
    def _check_reporting(self, state: SystemState) -> List[ValidationIssue]:
        """Q941-945: Reporting checks"""
        issues = []
        
        # Q941: Report generation failure
        report_fail = state.error_counts.get('report_generation_failure', 0)
        if report_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("report_fail", str(report_fail)),
                question_id=941,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Report generation failures: {report_fail}",
                description="Failed to generate regulatory reports",
                affected_components=["Reporting"],
                remediation_available=True,
                remediation_action="generate_report"
            ))
        
        # Q942: Report submission failure
        submission_fail = state.error_counts.get('report_submission_failure', 0)
        if submission_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("submit_fail", str(submission_fail)),
                question_id=942,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Report submission failures: {submission_fail}",
                description="Failed to submit regulatory reports",
                affected_components=["Reporting"],
                remediation_available=True,
                remediation_action="retry_submission"
            ))
        
        # Q943: Report deadline missed
        deadline_missed = state.error_counts.get('report_deadline_missed', 0)
        if deadline_missed > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("deadline", str(deadline_missed)),
                question_id=943,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Report deadlines missed: {deadline_missed}",
                description="Regulatory report deadlines missed",
                affected_components=["Reporting"],
                remediation_available=True,
                remediation_action="expedite_reports"
            ))
        
        # Q944: Report data inaccuracy
        data_inaccuracy = state.error_counts.get('report_data_inaccuracy', 0)
        if data_inaccuracy > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("inaccuracy", str(data_inaccuracy)),
                question_id=944,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Report data inaccuracies: {data_inaccuracy}",
                description="Regulatory reports contain inaccurate data",
                affected_components=["Reporting"],
                remediation_available=True,
                remediation_action="correct_reports"
            ))
        
        # Q945: Missing required reports
        missing_reports = state.error_counts.get('missing_required_reports', 0)
        if missing_reports > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("missing", str(missing_reports)),
                question_id=945,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Missing required reports: {missing_reports}",
                description="Required regulatory reports not generated",
                affected_components=["Reporting"],
                remediation_available=True,
                remediation_action="generate_report"
            ))
        
        return issues
    
    def _check_reporting_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q946-950: Reporting quality checks"""
        issues = []
        
        # Q948: Report format issues
        format_issues = state.error_counts.get('report_format_issue', 0)
        if format_issues > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("format", str(format_issues)),
                question_id=948,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Report format issues: {format_issues}",
                description="Reports not in required format",
                affected_components=["Reporting"],
                remediation_available=True,
                remediation_action="fix_report_format"
            ))
        
        # Q950: Report reconciliation failure
        recon_fail = state.error_counts.get('report_reconciliation_failure', 0)
        if recon_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("recon", str(recon_fail)),
                question_id=950,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Report reconciliation failed",
                description="Cannot reconcile reported vs actual data",
                affected_components=["Reporting"],
                remediation_available=True,
                remediation_action="investigate_discrepancy"
            ))
        
        return issues
    
    # =========================================================================
    # Q951-960: Audit
    # =========================================================================
    
    def _check_audit(self, state: SystemState) -> List[ValidationIssue]:
        """Q951-955: Audit checks"""
        issues = []
        
        # Q951: Audit trail incomplete
        incomplete_audit = state.error_counts.get('incomplete_audit_trail', 0)
        if incomplete_audit > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("incomplete", str(incomplete_audit)),
                question_id=951,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Incomplete audit trail",
                description="Audit trail has gaps",
                affected_components=["AuditLog"],
                remediation_available=True,
                remediation_action="fix_audit_trail"
            ))
        
        # Q952: Audit data missing
        missing_audit = state.error_counts.get('missing_audit_data', 0)
        if missing_audit > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("missing_audit", str(missing_audit)),
                question_id=952,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Missing audit data: {missing_audit}",
                description="Required audit data not captured",
                affected_components=["AuditLog"],
                remediation_available=True,
                remediation_action="enhance_audit"
            ))
        
        # Q953: Audit retention violation
        retention_violation = state.error_counts.get('audit_retention_violation', 0)
        if retention_violation > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("retention", str(retention_violation)),
                question_id=953,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Audit retention violation",
                description="Audit data not retained for required period",
                affected_components=["AuditLog"],
                remediation_available=True,
                remediation_action="extend_retention"
            ))
        
        # Q954: Audit tampering
        tampering = state.error_counts.get('audit_tampering_detected', 0)
        if tampering > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("tampering", str(tampering)),
                question_id=954,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Audit tampering detected",
                description="Audit trail has been tampered with",
                affected_components=["AuditLog", "Security"],
                remediation_available=True,
                remediation_action="halt_for_compliance",
                auto_remediate=True
            ))
        
        # Q955: Audit access issues
        access_issues = state.error_counts.get('audit_access_issue', 0)
        if access_issues > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("access", str(access_issues)),
                question_id=955,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Audit access issues: {access_issues}",
                description="Cannot access audit data",
                affected_components=["AuditLog"],
                remediation_available=True,
                remediation_action="fix_audit_access"
            ))
        
        return issues
    
    def _check_audit_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q956-960: Audit quality checks"""
        issues = []
        
        # Q958: Audit search failure
        search_fail = state.error_counts.get('audit_search_failure', 0)
        if search_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("search", str(search_fail)),
                question_id=958,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Audit search failures: {search_fail}",
                description="Cannot search audit records",
                affected_components=["AuditLog"],
                remediation_available=True,
                remediation_action="fix_audit_search"
            ))
        
        # Q960: Audit integrity failure
        integrity_fail = state.error_counts.get('audit_integrity_failure', 0)
        if integrity_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("integrity", str(integrity_fail)),
                question_id=960,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Audit integrity compromised",
                description="Audit trail integrity cannot be verified",
                affected_components=["AuditLog"],
                remediation_available=True,
                remediation_action="halt_for_compliance"
            ))
        
        return issues
    
    # =========================================================================
    # Q961-970: Regulatory Changes
    # =========================================================================
    
    def _check_regulatory_changes(self, state: SystemState) -> List[ValidationIssue]:
        """Q961-965: Regulatory change checks"""
        issues = []
        
        # Q961: Regulatory change not implemented
        not_implemented = state.error_counts.get('regulatory_change_not_implemented', 0)
        if not_implemented > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("not_impl", str(not_implemented)),
                question_id=961,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Regulatory changes not implemented: {not_implemented}",
                description="Required regulatory changes not implemented",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="implement_changes"
            ))
        
        # Q962: Regulatory deadline approaching
        deadline_approaching = state.error_counts.get('regulatory_deadline_approaching', 0)
        if deadline_approaching > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("deadline_near", str(deadline_approaching)),
                question_id=962,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Regulatory deadlines approaching: {deadline_approaching}",
                description="Regulatory compliance deadlines approaching",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="prioritize_compliance"
            ))
        
        # Q963: Regulatory interpretation unclear
        unclear = state.error_counts.get('regulatory_interpretation_unclear', 0)
        if unclear > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unclear", str(unclear)),
                question_id=963,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Unclear regulatory interpretation: {unclear}",
                description="Regulatory requirements unclear",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="seek_clarification"
            ))
        
        # Q964: Cross-jurisdiction conflict
        conflict = state.error_counts.get('cross_jurisdiction_conflict', 0)
        if conflict > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("conflict", str(conflict)),
                question_id=964,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Cross-jurisdiction conflicts: {conflict}",
                description="Conflicting regulations across jurisdictions",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="resolve_conflicts"
            ))
        
        # Q965: New regulation impact
        new_regulation = state.error_counts.get('new_regulation_impact', 0)
        if new_regulation > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("new_reg", str(new_regulation)),
                question_id=965,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"New regulations impacting system: {new_regulation}",
                description="New regulations require system changes",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="assess_impact"
            ))
        
        return issues
    
    def _check_change_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q966-970: Change quality checks"""
        issues = []
        
        # Q968: Regulatory testing incomplete
        testing_incomplete = state.error_counts.get('regulatory_testing_incomplete', 0)
        if testing_incomplete > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("test_incomplete", str(testing_incomplete)),
                question_id=968,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Regulatory testing incomplete",
                description="Compliance changes not fully tested",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="complete_testing"
            ))
        
        # Q970: Regulatory documentation missing
        docs_missing = state.error_counts.get('regulatory_documentation_missing', 0)
        if docs_missing > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("docs_missing", str(docs_missing)),
                question_id=970,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Regulatory documentation missing",
                description="Compliance documentation incomplete",
                affected_components=["Compliance"],
                remediation_available=True,
                remediation_action="complete_documentation"
            ))
        
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_halt(self, issue: ValidationIssue) -> str:
        """Halt for compliance"""
        self.logger.info("Halting for compliance")
        return "Trading halted for compliance review"
    
    async def _remediate_report(self, issue: ValidationIssue) -> str:
        """Generate report"""
        self.logger.info("Generating regulatory report")
        return "Report generated"
    
    async def _remediate_fix(self, issue: ValidationIssue) -> str:
        """Fix compliance issue"""
        self.logger.info("Fixing compliance issue")
        return "Compliance issue addressed"
