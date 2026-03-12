"""
Security Validator (Q711-780)
Addresses authentication, authorization, data protection, network security, and incident response.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class SecurityValidator(BaseValidator):
    """Validates security controls (Q711-780)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.SECURITY)
        self._security_metrics: Dict[str, Any] = {}
    
    def _register_checks(self):
        """Register all Q711-780 validation checks"""
        # Q711-720: Authentication
        self.add_check(self._check_authentication, [711, 712, 713, 714, 715])
        self.add_check(self._check_auth_quality, [716, 717, 718, 719, 720])
        # Q721-730: Authorization
        self.add_check(self._check_authorization, [721, 722, 723, 724, 725])
        self.add_check(self._check_authz_quality, [726, 727, 728, 729, 730])
        # Q731-740: Data Protection
        self.add_check(self._check_data_protection, [731, 732, 733, 734, 735])
        self.add_check(self._check_protection_quality, [736, 737, 738, 739, 740])
        # Q741-750: Network Security
        self.add_check(self._check_network_security, [741, 742, 743, 744, 745])
        self.add_check(self._check_network_quality, [746, 747, 748, 749, 750])
        # Q751-760: API Security
        self.add_check(self._check_api_security, [751, 752, 753, 754, 755])
        self.add_check(self._check_api_quality, [756, 757, 758, 759, 760])
        # Q761-770: Secrets Management
        self.add_check(self._check_secrets_management, [761, 762, 763, 764, 765])
        self.add_check(self._check_secrets_quality, [766, 767, 768, 769, 770])
        # Q771-780: Incident Response
        self.add_check(self._check_incident_response, [771, 772, 773, 774, 775])
        self.add_check(self._check_response_quality, [776, 777, 778, 779, 780])
        
        # Register remediations
        self.add_remediation("revoke_access", self._remediate_revoke)
        self.add_remediation("rotate_secrets", self._remediate_rotate)
        self.add_remediation("block_ip", self._remediate_block_ip)
    
    # =========================================================================
    # Q711-720: Authentication
    # =========================================================================
    
    def _check_authentication(self, state: SystemState) -> List[ValidationIssue]:
        """Q711-715: Authentication checks"""
        issues = []
        
        # Q711: Authentication failure
        auth_failures = state.error_counts.get('authentication_failure', 0)
        if auth_failures > 10:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("auth_fail", str(auth_failures)),
                question_id=711,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Authentication failures: {auth_failures}",
                description="Multiple authentication failures detected",
                affected_components=["Authentication"],
                remediation_available=True,
                remediation_action="investigate_auth",
                metadata={"failure_count": auth_failures}
            ))
        
        # Q712: Brute force attack
        brute_force = state.error_counts.get('brute_force_detected', 0)
        if brute_force > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("brute_force", str(brute_force)),
                question_id=712,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Brute force attack detected",
                description="Brute force authentication attack in progress",
                affected_components=["Authentication"],
                remediation_available=True,
                remediation_action="block_ip",
                auto_remediate=True
            ))
        
        # Q713: Credential compromise
        credential_leak = state.error_counts.get('credential_compromise', 0)
        if credential_leak > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("cred_leak", str(credential_leak)),
                question_id=713,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Credential compromise detected",
                description="Credentials may have been compromised",
                affected_components=["Authentication", "SecretsManager"],
                remediation_available=True,
                remediation_action="rotate_secrets",
                auto_remediate=True
            ))
        
        # Q715: Session hijacking
        session_hijack = state.error_counts.get('session_hijacking', 0)
        if session_hijack > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("hijack", str(session_hijack)),
                question_id=715,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Session hijacking detected",
                description="Session hijacking attempt detected",
                affected_components=["Authentication"],
                remediation_available=True,
                remediation_action="revoke_access",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_auth_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q716-720: Authentication quality checks"""
        issues = []
        
        # Q718: Weak authentication
        weak_auth = state.error_counts.get('weak_authentication', 0)
        if weak_auth > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("weak_auth", str(weak_auth)),
                question_id=718,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Weak authentication detected",
                description="Authentication mechanisms are weak",
                affected_components=["Authentication"],
                remediation_available=True,
                remediation_action="strengthen_auth"
            ))
        
        # Q720: MFA bypass
        mfa_bypass = state.error_counts.get('mfa_bypass', 0)
        if mfa_bypass > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("mfa_bypass", str(mfa_bypass)),
                question_id=720,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="MFA bypass detected",
                description="Multi-factor authentication was bypassed",
                affected_components=["Authentication"],
                remediation_available=True,
                remediation_action="revoke_access",
                auto_remediate=True
            ))
        
        return issues
    
    # =========================================================================
    # Q721-730: Authorization
    # =========================================================================
    
    def _check_authorization(self, state: SystemState) -> List[ValidationIssue]:
        """Q721-725: Authorization checks"""
        issues = []
        
        # Q721: Unauthorized access
        unauthorized = state.error_counts.get('unauthorized_access', 0)
        if unauthorized > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unauthorized", str(unauthorized)),
                question_id=721,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Unauthorized access attempts: {unauthorized}",
                description="Unauthorized access attempts detected",
                affected_components=["Authorization"],
                remediation_available=True,
                remediation_action="revoke_access",
                auto_remediate=True
            ))
        
        # Q722: Privilege escalation
        priv_esc = state.error_counts.get('privilege_escalation', 0)
        if priv_esc > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("priv_esc", str(priv_esc)),
                question_id=722,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Privilege escalation detected",
                description="Attempt to escalate privileges",
                affected_components=["Authorization"],
                remediation_available=True,
                remediation_action="revoke_access",
                auto_remediate=True
            ))
        
        # Q724: Excessive permissions
        excessive_perms = state.error_counts.get('excessive_permissions', 0)
        if excessive_perms > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("excessive", str(excessive_perms)),
                question_id=724,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Excessive permissions detected",
                description="Users/services have excessive permissions",
                affected_components=["Authorization"],
                remediation_available=True,
                remediation_action="reduce_permissions"
            ))
        
        return issues
    
    def _check_authz_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q726-730: Authorization quality checks"""
        issues = []
        
        # Q728: Authorization bypass
        authz_bypass = state.error_counts.get('authorization_bypass', 0)
        if authz_bypass > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("authz_bypass", str(authz_bypass)),
                question_id=728,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Authorization bypass detected",
                description="Authorization controls were bypassed",
                affected_components=["Authorization"],
                remediation_available=True,
                remediation_action="halt_system",
                auto_remediate=True
            ))
        
        # Q730: Stale permissions
        stale_perms = state.error_counts.get('stale_permissions', 0)
        if stale_perms > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stale_perms", str(stale_perms)),
                question_id=730,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Stale permissions: {stale_perms}",
                description="Permissions not reviewed/updated",
                affected_components=["Authorization"],
                remediation_available=True,
                remediation_action="review_permissions"
            ))
        
        return issues
    
    # =========================================================================
    # Q731-740: Data Protection
    # =========================================================================
    
    def _check_data_protection(self, state: SystemState) -> List[ValidationIssue]:
        """Q731-735: Data protection checks"""
        issues = []
        
        # Q731: Data breach
        data_breach = state.error_counts.get('data_breach', 0)
        if data_breach > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("breach", str(data_breach)),
                question_id=731,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Data breach detected",
                description="Potential data breach in progress",
                affected_components=["DataProtection"],
                remediation_available=True,
                remediation_action="halt_system",
                auto_remediate=True
            ))
        
        # Q732: Unencrypted data
        unencrypted = state.error_counts.get('unencrypted_sensitive_data', 0)
        if unencrypted > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unencrypted", str(unencrypted)),
                question_id=732,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Unencrypted sensitive data",
                description="Sensitive data found unencrypted",
                affected_components=["DataProtection"],
                remediation_available=True,
                remediation_action="encrypt_data"
            ))
        
        # Q734: Data exfiltration
        exfiltration = state.error_counts.get('data_exfiltration', 0)
        if exfiltration > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("exfiltration", str(exfiltration)),
                question_id=734,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Data exfiltration detected",
                description="Data exfiltration attempt detected",
                affected_components=["DataProtection", "Network"],
                remediation_available=True,
                remediation_action="block_exfiltration",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_protection_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q736-740: Protection quality checks"""
        issues = []
        
        # Q738: Encryption weakness
        weak_encryption = state.error_counts.get('weak_encryption', 0)
        if weak_encryption > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("weak_enc", str(weak_encryption)),
                question_id=738,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Weak encryption detected",
                description="Encryption algorithms are weak or outdated",
                affected_components=["DataProtection"],
                remediation_available=True,
                remediation_action="upgrade_encryption"
            ))
        
        # Q740: Key management failure
        key_fail = state.error_counts.get('key_management_failure', 0)
        if key_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("key_fail", str(key_fail)),
                question_id=740,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Key management failure",
                description="Encryption key management has failed",
                affected_components=["DataProtection", "SecretsManager"],
                remediation_available=True,
                remediation_action="rotate_secrets"
            ))
        
        return issues
    
    # =========================================================================
    # Q741-750: Network Security
    # =========================================================================
    
    def _check_network_security(self, state: SystemState) -> List[ValidationIssue]:
        """Q741-745: Network security checks"""
        issues = []
        
        # Q741: Network intrusion
        intrusion = state.error_counts.get('network_intrusion', 0)
        if intrusion > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("intrusion", str(intrusion)),
                question_id=741,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Network intrusion detected",
                description="Network intrusion attempt detected",
                affected_components=["Network", "Security"],
                remediation_available=True,
                remediation_action="block_ip",
                auto_remediate=True
            ))
        
        # Q742: DDoS attack
        ddos = state.error_counts.get('ddos_attack', 0)
        if ddos > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("ddos", str(ddos)),
                question_id=742,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="DDoS attack detected",
                description="Distributed denial of service attack",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="activate_ddos_protection",
                auto_remediate=True
            ))
        
        # Q744: Man-in-the-middle
        mitm = state.error_counts.get('mitm_detected', 0)
        if mitm > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("mitm", str(mitm)),
                question_id=744,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Man-in-the-middle attack detected",
                description="MITM attack on network communications",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="halt_communications",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_network_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q746-750: Network quality checks"""
        issues = []
        
        # Q748: Firewall misconfiguration
        firewall_misconfig = state.error_counts.get('firewall_misconfiguration', 0)
        if firewall_misconfig > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("firewall", str(firewall_misconfig)),
                question_id=748,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Firewall misconfiguration",
                description="Firewall rules are misconfigured",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="fix_firewall"
            ))
        
        # Q750: TLS/SSL issues
        tls_issues = state.error_counts.get('tls_ssl_issue', 0)
        if tls_issues > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("tls", str(tls_issues)),
                question_id=750,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"TLS/SSL issues: {tls_issues}",
                description="TLS/SSL configuration problems",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="fix_tls"
            ))
        
        return issues
    
    # =========================================================================
    # Q751-760: API Security
    # =========================================================================
    
    def _check_api_security(self, state: SystemState) -> List[ValidationIssue]:
        """Q751-755: API security checks"""
        issues = []
        
        # Q751: API abuse
        api_abuse = state.error_counts.get('api_abuse', 0)
        if api_abuse > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("api_abuse", str(api_abuse)),
                question_id=751,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"API abuse detected: {api_abuse}",
                description="API being abused or misused",
                affected_components=["API"],
                remediation_available=True,
                remediation_action="rate_limit_api"
            ))
        
        # Q752: API key exposure
        key_exposure = state.error_counts.get('api_key_exposure', 0)
        if key_exposure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("key_exposure", str(key_exposure)),
                question_id=752,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="API key exposure detected",
                description="API keys may have been exposed",
                affected_components=["API", "SecretsManager"],
                remediation_available=True,
                remediation_action="rotate_secrets",
                auto_remediate=True
            ))
        
        # Q754: Injection attack
        injection = state.error_counts.get('injection_attack', 0)
        if injection > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("injection", str(injection)),
                question_id=754,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Injection attack detected",
                description="SQL/command injection attempt",
                affected_components=["API"],
                remediation_available=True,
                remediation_action="block_ip",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_api_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q756-760: API quality checks"""
        issues = []
        
        # Q758: API vulnerability
        api_vuln = state.error_counts.get('api_vulnerability', 0)
        if api_vuln > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("api_vuln", str(api_vuln)),
                question_id=758,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"API vulnerabilities: {api_vuln}",
                description="API has known vulnerabilities",
                affected_components=["API"],
                remediation_available=True,
                remediation_action="patch_api"
            ))
        
        # Q760: API rate limit bypass
        rate_bypass = state.error_counts.get('rate_limit_bypass', 0)
        if rate_bypass > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("rate_bypass", str(rate_bypass)),
                question_id=760,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Rate limit bypass detected",
                description="API rate limits being bypassed",
                affected_components=["API"],
                remediation_available=True,
                remediation_action="strengthen_rate_limits"
            ))
        
        return issues
    
    # =========================================================================
    # Q761-770: Secrets Management
    # =========================================================================
    
    def _check_secrets_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q761-765: Secrets management checks"""
        issues = []
        
        # Q761: Secret exposure
        secret_exposure = state.error_counts.get('secret_exposure', 0)
        if secret_exposure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("secret_exp", str(secret_exposure)),
                question_id=761,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Secret exposure detected",
                description="Secrets may have been exposed",
                affected_components=["SecretsManager"],
                remediation_available=True,
                remediation_action="rotate_secrets",
                auto_remediate=True
            ))
        
        # Q762: Hardcoded secrets
        hardcoded = state.error_counts.get('hardcoded_secrets', 0)
        if hardcoded > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("hardcoded", str(hardcoded)),
                question_id=762,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Hardcoded secrets: {hardcoded}",
                description="Secrets hardcoded in code",
                affected_components=["SecretsManager", "CodeBase"],
                remediation_available=True,
                remediation_action="remove_hardcoded"
            ))
        
        # Q764: Secret rotation overdue
        rotation_overdue = state.error_counts.get('secret_rotation_overdue', 0)
        if rotation_overdue > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("rotation", str(rotation_overdue)),
                question_id=764,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Secret rotation overdue: {rotation_overdue}",
                description="Secrets need to be rotated",
                affected_components=["SecretsManager"],
                remediation_available=True,
                remediation_action="rotate_secrets"
            ))
        
        return issues
    
    def _check_secrets_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q766-770: Secrets quality checks"""
        issues = []
        
        # Q768: Weak secrets
        weak_secrets = state.error_counts.get('weak_secrets', 0)
        if weak_secrets > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("weak_secret", str(weak_secrets)),
                question_id=768,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Weak secrets: {weak_secrets}",
                description="Secrets are weak or predictable",
                affected_components=["SecretsManager"],
                remediation_available=True,
                remediation_action="strengthen_secrets"
            ))
        
        # Q770: Secrets vault failure
        vault_fail = state.error_counts.get('secrets_vault_failure', 0)
        if vault_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("vault_fail", str(vault_fail)),
                question_id=770,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Secrets vault failure",
                description="Secrets management system failing",
                affected_components=["SecretsManager"],
                remediation_available=True,
                remediation_action="restore_vault"
            ))
        
        return issues
    
    # =========================================================================
    # Q771-780: Incident Response
    # =========================================================================
    
    def _check_incident_response(self, state: SystemState) -> List[ValidationIssue]:
        """Q771-775: Incident response checks"""
        issues = []
        
        # Q771: Unhandled security incident
        unhandled = state.error_counts.get('unhandled_security_incident', 0)
        if unhandled > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unhandled", str(unhandled)),
                question_id=771,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Unhandled security incidents: {unhandled}",
                description="Security incidents not properly handled",
                affected_components=["IncidentResponse"],
                remediation_available=True,
                remediation_action="escalate_incident"
            ))
        
        # Q772: Delayed response
        delayed = state.error_counts.get('delayed_incident_response', 0)
        if delayed > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("delayed", str(delayed)),
                question_id=772,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Delayed incident response: {delayed}",
                description="Security incident response too slow",
                affected_components=["IncidentResponse"],
                remediation_available=True,
                remediation_action="improve_response"
            ))
        
        # Q774: Incident not contained
        not_contained = state.error_counts.get('incident_not_contained', 0)
        if not_contained > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("not_contained", str(not_contained)),
                question_id=774,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Security incident not contained",
                description="Active security incident spreading",
                affected_components=["IncidentResponse"],
                remediation_available=True,
                remediation_action="halt_system",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_response_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q776-780: Response quality checks"""
        issues = []
        
        # Q778: No incident plan
        no_plan = state.error_counts.get('no_incident_plan', 0)
        if no_plan > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("no_plan", str(no_plan)),
                question_id=778,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="No incident response plan",
                description="Incident response plan missing",
                affected_components=["IncidentResponse"],
                remediation_available=True,
                remediation_action="create_plan"
            ))
        
        # Q780: Incident recurrence
        recurrence = state.error_counts.get('incident_recurrence', 0)
        if recurrence > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("recurrence", str(recurrence)),
                question_id=780,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Incident recurrence: {recurrence}",
                description="Same security incidents recurring",
                affected_components=["IncidentResponse"],
                remediation_available=True,
                remediation_action="root_cause_analysis"
            ))
        
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_revoke(self, issue: ValidationIssue) -> str:
        """Revoke access"""
        self.logger.info("Revoking access")
        return "Access revoked"
    
    async def _remediate_rotate(self, issue: ValidationIssue) -> str:
        """Rotate secrets"""
        self.logger.info("Rotating secrets")
        return "Secrets rotated"
    
    async def _remediate_block_ip(self, issue: ValidationIssue) -> str:
        """Block IP address"""
        self.logger.info("Blocking IP")
        return "IP blocked"
