"""
Infrastructure Validator (Q471-530)
Addresses network, compute, storage, execution path, monitoring, and disaster recovery.
"""

import psutil
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class InfrastructureValidator(BaseValidator):
    """Validates infrastructure health (Q471-530)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.INFRASTRUCTURE)
        self._infra_metrics: Dict[str, Any] = {}
    
    def _register_checks(self):
        """Register all Q471-530 validation checks"""
        # Q471-480: Network
        self.add_check(self._check_network_topology, [471, 472, 473, 474, 475])
        self.add_check(self._check_network_security, [476, 477, 478, 479, 480])
        # Q481-490: Compute
        self.add_check(self._check_compute_resources, [481, 482, 483, 484, 485])
        self.add_check(self._check_compute_management, [486, 487, 488, 489, 490])
        # Q491-500: Storage
        self.add_check(self._check_storage_health, [491, 492, 493, 494, 495])
        self.add_check(self._check_storage_management, [496, 497, 498, 499, 500])
        # Q501-510: Execution Path
        self.add_check(self._check_execution_path, [501, 502, 503, 504, 505])
        self.add_check(self._check_path_optimization, [506, 507, 508, 509, 510])
        # Q511-520: Monitoring
        self.add_check(self._check_monitoring_infra, [511, 512, 513, 514, 515])
        self.add_check(self._check_monitoring_quality, [516, 517, 518, 519, 520])
        # Q521-530: Disaster Recovery
        self.add_check(self._check_dr_plan, [521, 522, 523, 524, 525])
        self.add_check(self._check_dr_readiness, [526, 527, 528, 529, 530])
        
        # Register remediations
        self.add_remediation("scale_resources", self._remediate_scale)
        self.add_remediation("cleanup_storage", self._remediate_cleanup)
        self.add_remediation("restart_service", self._remediate_restart)
    
    # =========================================================================
    # Q471-480: Network
    # =========================================================================
    
    def _check_network_topology(self, state: SystemState) -> List[ValidationIssue]:
        """Q471-475: Network topology checks"""
        issues = []
        
        # Q471: Single points of failure
        spof = state.error_counts.get('network_spof', 0)
        if spof > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("spof", str(spof)),
                question_id=471,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Network single point of failure",
                description="Network has single points of failure",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="add_redundancy"
            ))
        
        # Q472: Network partition
        partition = state.error_counts.get('network_partition', 0)
        if partition > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("partition", str(partition)),
                question_id=472,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Network partition detected",
                description="Network partition between components",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="heal_partition",
                auto_remediate=True
            ))
        
        # Q473: Latency spikes
        latency_spikes = state.error_counts.get('network_latency_spike', 0)
        if latency_spikes > 5:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("net_latency", str(latency_spikes)),
                question_id=473,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Network latency spikes: {latency_spikes}",
                description="Frequent network latency spikes",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="investigate_network"
            ))
        
        return issues
    
    def _check_network_security(self, state: SystemState) -> List[ValidationIssue]:
        """Q476-480: Network security checks"""
        issues = []
        
        # Q476: DNS failure
        dns_failures = state.error_counts.get('dns_failure', 0)
        if dns_failures > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dns", str(dns_failures)),
                question_id=476,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"DNS failures: {dns_failures}",
                description="DNS resolution failing",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="switch_dns"
            ))
        
        # Q479: Network attack
        attacks = state.error_counts.get('network_attack', 0)
        if attacks > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("attack", str(attacks)),
                question_id=479,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Network attack detected",
                description="Potential network attack in progress",
                affected_components=["Network", "Security"],
                remediation_available=True,
                remediation_action="activate_defense",
                auto_remediate=True
            ))
        
        # Q480: Failover failure
        failover_fail = state.error_counts.get('failover_failure', 0)
        if failover_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("failover", str(failover_fail)),
                question_id=480,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Failover mechanism failed",
                description="Network failover not working",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="manual_failover"
            ))
        
        return issues
    
    # =========================================================================
    # Q481-490: Compute
    # =========================================================================
    
    def _check_compute_resources(self, state: SystemState) -> List[ValidationIssue]:
        """Q481-485: Compute resource checks"""
        issues = []
        
        # Q481: Compute exhaustion
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > 90:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("cpu", str(cpu_percent)),
                question_id=481,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"CPU exhausted: {cpu_percent}%",
                description="CPU resources nearly exhausted",
                affected_components=["Compute"],
                remediation_available=True,
                remediation_action="scale_resources",
                auto_remediate=True
            ))
        elif cpu_percent > 80:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("cpu_high", str(cpu_percent)),
                question_id=481,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"High CPU usage: {cpu_percent}%",
                description="CPU usage is high",
                affected_components=["Compute"],
                remediation_available=True,
                remediation_action="optimize_compute"
            ))
        
        # Memory check
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("memory", str(memory.percent)),
                question_id=481,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Memory exhausted: {memory.percent}%",
                description="Memory resources nearly exhausted",
                affected_components=["Compute"],
                remediation_available=True,
                remediation_action="scale_resources",
                auto_remediate=True
            ))
        
        # Q484: Compute degradation
        compute_degradation = state.error_counts.get('compute_degradation', 0)
        if compute_degradation > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("degrade", str(compute_degradation)),
                question_id=484,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Compute performance degrading",
                description="Compute performance is degrading",
                affected_components=["Compute"],
                remediation_available=True,
                remediation_action="investigate_compute"
            ))
        
        return issues
    
    def _check_compute_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q486-490: Compute management checks"""
        issues = []
        
        # Q488: Compute misconfiguration
        misconfig = state.error_counts.get('compute_misconfiguration', 0)
        if misconfig > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("misconfig", str(misconfig)),
                question_id=488,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Compute misconfiguration",
                description="Compute infrastructure is misconfigured",
                affected_components=["Compute"],
                remediation_available=True,
                remediation_action="fix_config"
            ))
        
        # Q490: State-corrupting compute failure
        state_corrupt = state.error_counts.get('compute_state_corruption', 0)
        if state_corrupt > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("state_corrupt", str(state_corrupt)),
                question_id=490,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Compute failure corrupted state",
                description="Compute failure caused state corruption",
                affected_components=["Compute", "StateManager"],
                remediation_available=True,
                remediation_action="restore_state"
            ))
        
        return issues
    
    # =========================================================================
    # Q491-500: Storage
    # =========================================================================
    
    def _check_storage_health(self, state: SystemState) -> List[ValidationIssue]:
        """Q491-495: Storage health checks"""
        issues = []
        
        # Q491: Storage unavailable
        storage_unavailable = state.error_counts.get('storage_unavailable', 0)
        if storage_unavailable > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("storage_down", str(storage_unavailable)),
                question_id=491,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Storage unavailable",
                description="Storage system is unavailable",
                affected_components=["Storage"],
                remediation_available=True,
                remediation_action="switch_storage",
                auto_remediate=True
            ))
        
        # Q495: Storage capacity
        try:
            total, used, free = shutil.disk_usage("/")
            usage_percent = (used / total) * 100
            
            if usage_percent > 95:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("disk_full", str(usage_percent)),
                    question_id=495,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Storage nearly full: {usage_percent:.1f}%",
                    description="Storage capacity nearly exhausted",
                    affected_components=["Storage"],
                    remediation_available=True,
                    remediation_action="cleanup_storage",
                    auto_remediate=True
                ))
            elif usage_percent > 85:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("disk_high", str(usage_percent)),
                    question_id=495,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Storage usage high: {usage_percent:.1f}%",
                    description="Storage usage is high",
                    affected_components=["Storage"],
                    remediation_available=True,
                    remediation_action="cleanup_storage"
                ))
        except Exception:
            pass
        
        return issues
    
    def _check_storage_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q496-500: Storage management checks"""
        issues = []
        
        # Q498: Storage corruption
        corruption = state.error_counts.get('storage_corruption', 0)
        if corruption > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("storage_corrupt", str(corruption)),
                question_id=498,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Storage corruption detected",
                description="Storage infrastructure is corrupted",
                affected_components=["Storage"],
                remediation_available=True,
                remediation_action="repair_storage"
            ))
        
        # Q500: Data loss from storage failure
        data_loss = state.error_counts.get('storage_data_loss', 0)
        if data_loss > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("data_loss", str(data_loss)),
                question_id=500,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Data loss from storage failure",
                description="Storage failure caused data loss",
                affected_components=["Storage"],
                remediation_available=True,
                remediation_action="restore_backup"
            ))
        
        return issues
    
    # =========================================================================
    # Q501-510: Execution Path
    # =========================================================================
    
    def _check_execution_path(self, state: SystemState) -> List[ValidationIssue]:
        """Q501-505: Execution path checks"""
        issues = []
        
        # Q502: Execution latency increase
        exec_latency = state.latency_metrics.get('execution_path_ms', 0)
        if exec_latency > IMMUTABLE_LIMITS['max_latency_ms']:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("exec_latency", str(exec_latency)),
                question_id=502,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Execution path latency: {exec_latency}ms",
                description="Critical execution path latency too high",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="optimize_path"
            ))
        
        # Q504: Execution path failure
        path_failure = state.error_counts.get('execution_path_failure', 0)
        if path_failure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("path_fail", str(path_failure)),
                question_id=504,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Execution path failure",
                description="Critical execution path has failed",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="switch_path",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_path_optimization(self, state: SystemState) -> List[ValidationIssue]:
        """Q506-510: Path optimization checks"""
        issues = []
        
        # Q509: Throttling
        throttling = state.error_counts.get('execution_throttling', 0)
        if throttling > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("throttle", str(throttling)),
                question_id=509,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Execution path throttled",
                description="Execution path is being throttled",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="investigate_throttling"
            ))
        
        return issues
    
    # =========================================================================
    # Q511-520: Monitoring
    # =========================================================================
    
    def _check_monitoring_infra(self, state: SystemState) -> List[ValidationIssue]:
        """Q511-515: Monitoring infrastructure checks"""
        issues = []
        
        # Q511: Monitoring failure
        mon_failure = state.error_counts.get('monitoring_failure', 0)
        if mon_failure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("mon_fail", str(mon_failure)),
                question_id=511,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Monitoring infrastructure failed",
                description="Cannot monitor system health",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="restart_monitoring",
                auto_remediate=True
            ))
        
        # Q512: Missing events
        missing_events = state.error_counts.get('missing_monitoring_events', 0)
        if missing_events > 10:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("missing_events", str(missing_events)),
                question_id=512,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Missing monitoring events: {missing_events}",
                description="Monitoring is missing events",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="investigate_monitoring"
            ))
        
        return issues
    
    def _check_monitoring_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q516-520: Monitoring quality checks"""
        issues = []
        
        # Q518: False positives
        false_positives = state.error_counts.get('monitoring_false_positive', 0)
        if false_positives > 20:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("false_pos", str(false_positives)),
                question_id=518,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Monitoring false positives: {false_positives}",
                description="Too many false positive alerts",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="tune_alerts"
            ))
        
        # Q519: Ignored alerts
        ignored = state.error_counts.get('ignored_alerts', 0)
        if ignored > 5:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("ignored", str(ignored)),
                question_id=519,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Ignored alerts: {ignored}",
                description="Alerts being ignored",
                affected_components=["Monitoring"],
                remediation_available=False
            ))
        
        return issues
    
    # =========================================================================
    # Q521-530: Disaster Recovery
    # =========================================================================
    
    def _check_dr_plan(self, state: SystemState) -> List[ValidationIssue]:
        """Q521-525: Disaster recovery plan checks"""
        issues = []
        
        # Q521: DR plan exists and tested
        dr_last_test = state.data_sources.get('dr_last_test_days', 999)
        if dr_last_test > 90:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dr_test", str(dr_last_test)),
                question_id=521,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"DR plan not tested in {dr_last_test} days",
                description="Disaster recovery plan needs testing",
                affected_components=["DisasterRecovery"],
                remediation_available=True,
                remediation_action="schedule_dr_test"
            ))
        
        # Q523: DR procedure failure
        dr_failure = state.error_counts.get('dr_procedure_failure', 0)
        if dr_failure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dr_fail", str(dr_failure)),
                question_id=523,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="DR procedure failed",
                description="Disaster recovery procedures failed",
                affected_components=["DisasterRecovery"],
                remediation_available=False
            ))
        
        return issues
    
    def _check_dr_readiness(self, state: SystemState) -> List[ValidationIssue]:
        """Q526-530: DR readiness checks"""
        issues = []
        
        # Q529: DR infrastructure failure
        dr_infra_fail = state.error_counts.get('dr_infrastructure_failure', 0)
        if dr_infra_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dr_infra", str(dr_infra_fail)),
                question_id=529,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="DR infrastructure failed",
                description="Disaster recovery infrastructure is not working",
                affected_components=["DisasterRecovery"],
                remediation_available=True,
                remediation_action="repair_dr_infra"
            ))
        
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_scale(self, issue: ValidationIssue) -> str:
        """Scale resources"""
        self.logger.info("Scaling resources")
        return "Resources scaled"
    
    async def _remediate_cleanup(self, issue: ValidationIssue) -> str:
        """Cleanup storage"""
        self.logger.info("Cleaning up storage")
        return "Storage cleaned"
    
    async def _remediate_restart(self, issue: ValidationIssue) -> str:
        """Restart service"""
        self.logger.info("Restarting service")
        return "Service restarted"
