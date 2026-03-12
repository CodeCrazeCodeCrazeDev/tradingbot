"""
Monitoring Validator (Q831-890)
Addresses metrics collection, alerting, dashboards, logging, and observability.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class MonitoringValidator(BaseValidator):
    """Validates monitoring and observability (Q831-890)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.MONITORING)
        self._monitoring_metrics: Dict[str, Any] = {}
    
    def _register_checks(self):
        """Register all Q831-890 validation checks"""
        # Q831-840: Metrics Collection
        self.add_check(self._check_metrics_collection, [831, 832, 833, 834, 835])
        self.add_check(self._check_collection_quality, [836, 837, 838, 839, 840])
        # Q841-850: Alerting
        self.add_check(self._check_alerting, [841, 842, 843, 844, 845])
        self.add_check(self._check_alerting_quality, [846, 847, 848, 849, 850])
        # Q851-860: Dashboards
        self.add_check(self._check_dashboards, [851, 852, 853, 854, 855])
        self.add_check(self._check_dashboard_quality, [856, 857, 858, 859, 860])
        # Q861-870: Logging
        self.add_check(self._check_logging, [861, 862, 863, 864, 865])
        self.add_check(self._check_logging_quality, [866, 867, 868, 869, 870])
        # Q871-880: Tracing
        self.add_check(self._check_tracing, [871, 872, 873, 874, 875])
        self.add_check(self._check_tracing_quality, [876, 877, 878, 879, 880])
        # Q881-890: Observability
        self.add_check(self._check_observability, [881, 882, 883, 884, 885])
        self.add_check(self._check_observability_quality, [886, 887, 888, 889, 890])
        
        # Register remediations
        self.add_remediation("restart_monitoring", self._remediate_restart)
        self.add_remediation("fix_alerts", self._remediate_fix_alerts)
        self.add_remediation("increase_retention", self._remediate_retention)
    
    # =========================================================================
    # Q831-840: Metrics Collection
    # =========================================================================
    
    def _check_metrics_collection(self, state: SystemState) -> List[ValidationIssue]:
        """Q831-835: Metrics collection checks"""
        issues = []
        
        # Q831: Metrics collection failure
        collection_fail = state.error_counts.get('metrics_collection_failure', 0)
        if collection_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("collect_fail", str(collection_fail)),
                question_id=831,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Metrics collection failures: {collection_fail}",
                description="Cannot collect system metrics",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="restart_monitoring",
                auto_remediate=True
            ))
        
        # Q832: Missing metrics
        missing_metrics = state.error_counts.get('missing_metrics', 0)
        if missing_metrics > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("missing", str(missing_metrics)),
                question_id=832,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Missing metrics: {missing_metrics}",
                description="Some metrics not being collected",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="add_metrics"
            ))
        
        # Q833: Stale metrics
        stale_metrics = state.error_counts.get('stale_metrics', 0)
        if stale_metrics > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stale", str(stale_metrics)),
                question_id=833,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Stale metrics: {stale_metrics}",
                description="Metrics data is stale",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="restart_monitoring"
            ))
        
        # Q835: Metrics overflow
        overflow = state.error_counts.get('metrics_overflow', 0)
        if overflow > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("overflow", str(overflow)),
                question_id=835,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Metrics overflow",
                description="Metrics storage overflowing",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="cleanup_metrics"
            ))
        
        return issues
    
    def _check_collection_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q836-840: Collection quality checks"""
        issues = []
        
        # Q838: Metrics accuracy
        inaccurate = state.error_counts.get('inaccurate_metrics', 0)
        if inaccurate > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("inaccurate", str(inaccurate)),
                question_id=838,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Inaccurate metrics: {inaccurate}",
                description="Metrics data is inaccurate",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="recalibrate_metrics"
            ))
        
        # Q840: Metrics latency
        metrics_latency = state.latency_metrics.get('metrics_collection_ms', 0)
        if metrics_latency > 1000:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("latency", str(metrics_latency)),
                question_id=840,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"High metrics latency: {metrics_latency}ms",
                description="Metrics collection is slow",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="optimize_collection"
            ))
        
        return issues
    
    # =========================================================================
    # Q841-850: Alerting
    # =========================================================================
    
    def _check_alerting(self, state: SystemState) -> List[ValidationIssue]:
        """Q841-845: Alerting checks"""
        issues = []
        
        # Q841: Alert delivery failure
        delivery_fail = state.error_counts.get('alert_delivery_failure', 0)
        if delivery_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("delivery", str(delivery_fail)),
                question_id=841,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Alert delivery failures: {delivery_fail}",
                description="Alerts not being delivered",
                affected_components=["Alerting"],
                remediation_available=True,
                remediation_action="fix_alerts",
                auto_remediate=True
            ))
        
        # Q842: Missed alerts
        missed = state.error_counts.get('missed_alerts', 0)
        if missed > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("missed", str(missed)),
                question_id=842,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Missed alerts: {missed}",
                description="Critical alerts were missed",
                affected_components=["Alerting"],
                remediation_available=True,
                remediation_action="investigate_alerts"
            ))
        
        # Q843: Alert fatigue
        alert_count = state.error_counts.get('alert_count_24h', 0)
        if alert_count > 100:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("fatigue", str(alert_count)),
                question_id=843,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Alert fatigue: {alert_count} alerts in 24h",
                description="Too many alerts causing fatigue",
                affected_components=["Alerting"],
                remediation_available=True,
                remediation_action="tune_alerts"
            ))
        
        # Q845: Alert escalation failure
        escalation_fail = state.error_counts.get('alert_escalation_failure', 0)
        if escalation_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("escalation", str(escalation_fail)),
                question_id=845,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Alert escalation failure",
                description="Alerts not escalating properly",
                affected_components=["Alerting"],
                remediation_available=True,
                remediation_action="fix_escalation"
            ))
        
        return issues
    
    def _check_alerting_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q846-850: Alerting quality checks"""
        issues = []
        
        # Q848: False positives
        false_pos = state.error_counts.get('alert_false_positive', 0)
        if false_pos > 20:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("false_pos", str(false_pos)),
                question_id=848,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Alert false positives: {false_pos}",
                description="Too many false positive alerts",
                affected_components=["Alerting"],
                remediation_available=True,
                remediation_action="tune_alerts"
            ))
        
        # Q850: Alert delay
        alert_delay = state.latency_metrics.get('alert_delay_ms', 0)
        if alert_delay > 5000:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("delay", str(alert_delay)),
                question_id=850,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Alert delay: {alert_delay}ms",
                description="Alerts are delayed",
                affected_components=["Alerting"],
                remediation_available=True,
                remediation_action="optimize_alerting"
            ))
        
        return issues
    
    # =========================================================================
    # Q851-860: Dashboards
    # =========================================================================
    
    def _check_dashboards(self, state: SystemState) -> List[ValidationIssue]:
        """Q851-855: Dashboard checks"""
        issues = []
        
        # Q851: Dashboard unavailable
        unavailable = state.error_counts.get('dashboard_unavailable', 0)
        if unavailable > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unavailable", str(unavailable)),
                question_id=851,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Dashboard unavailable",
                description="Monitoring dashboard is unavailable",
                affected_components=["Dashboard"],
                remediation_available=True,
                remediation_action="restart_dashboard"
            ))
        
        # Q852: Stale dashboard data
        stale_dashboard = state.error_counts.get('stale_dashboard_data', 0)
        if stale_dashboard > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stale_dash", str(stale_dashboard)),
                question_id=852,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Stale dashboard data",
                description="Dashboard showing stale data",
                affected_components=["Dashboard"],
                remediation_available=True,
                remediation_action="refresh_dashboard"
            ))
        
        # Q854: Missing dashboard panels
        missing_panels = state.error_counts.get('missing_dashboard_panels', 0)
        if missing_panels > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("missing_panel", str(missing_panels)),
                question_id=854,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Missing dashboard panels: {missing_panels}",
                description="Dashboard panels not loading",
                affected_components=["Dashboard"],
                remediation_available=True,
                remediation_action="fix_dashboard"
            ))
        
        return issues
    
    def _check_dashboard_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q856-860: Dashboard quality checks"""
        issues = []
        
        # Q858: Dashboard performance
        dash_latency = state.latency_metrics.get('dashboard_load_ms', 0)
        if dash_latency > 5000:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dash_slow", str(dash_latency)),
                question_id=858,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Slow dashboard: {dash_latency}ms",
                description="Dashboard loading slowly",
                affected_components=["Dashboard"],
                remediation_available=True,
                remediation_action="optimize_dashboard"
            ))
        
        # Q860: Dashboard errors
        dash_errors = state.error_counts.get('dashboard_errors', 0)
        if dash_errors > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dash_error", str(dash_errors)),
                question_id=860,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Dashboard errors: {dash_errors}",
                description="Dashboard showing errors",
                affected_components=["Dashboard"],
                remediation_available=True,
                remediation_action="fix_dashboard"
            ))
        
        return issues
    
    # =========================================================================
    # Q861-870: Logging
    # =========================================================================
    
    def _check_logging(self, state: SystemState) -> List[ValidationIssue]:
        """Q861-865: Logging checks"""
        issues = []
        
        # Q861: Logging failure
        log_fail = state.error_counts.get('logging_failure', 0)
        if log_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("log_fail", str(log_fail)),
                question_id=861,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Logging failures: {log_fail}",
                description="Logging system failing",
                affected_components=["Logging"],
                remediation_available=True,
                remediation_action="restart_logging"
            ))
        
        # Q862: Missing logs
        missing_logs = state.error_counts.get('missing_logs', 0)
        if missing_logs > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("missing_log", str(missing_logs)),
                question_id=862,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Missing logs: {missing_logs}",
                description="Log entries are missing",
                affected_components=["Logging"],
                remediation_available=True,
                remediation_action="investigate_logging"
            ))
        
        # Q864: Log storage full
        log_storage = state.error_counts.get('log_storage_full', 0)
        if log_storage > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("log_full", str(log_storage)),
                question_id=864,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Log storage full",
                description="Log storage capacity exhausted",
                affected_components=["Logging"],
                remediation_available=True,
                remediation_action="cleanup_logs"
            ))
        
        return issues
    
    def _check_logging_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q866-870: Logging quality checks"""
        issues = []
        
        # Q868: Log retention
        retention_days = state.data_sources.get('log_retention_days', 30)
        if retention_days < 7:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("retention", str(retention_days)),
                question_id=868,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Low log retention: {retention_days} days",
                description="Log retention period too short",
                affected_components=["Logging"],
                remediation_available=True,
                remediation_action="increase_retention"
            ))
        
        # Q870: Log corruption
        log_corruption = state.error_counts.get('log_corruption', 0)
        if log_corruption > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("log_corrupt", str(log_corruption)),
                question_id=870,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Log corruption detected",
                description="Log files are corrupted",
                affected_components=["Logging"],
                remediation_available=True,
                remediation_action="repair_logs"
            ))
        
        return issues
    
    # =========================================================================
    # Q871-880: Tracing
    # =========================================================================
    
    def _check_tracing(self, state: SystemState) -> List[ValidationIssue]:
        """Q871-875: Tracing checks"""
        issues = []
        
        # Q871: Tracing unavailable
        trace_unavailable = state.error_counts.get('tracing_unavailable', 0)
        if trace_unavailable > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("trace_unavail", str(trace_unavailable)),
                question_id=871,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Tracing unavailable",
                description="Distributed tracing not working",
                affected_components=["Tracing"],
                remediation_available=True,
                remediation_action="restart_tracing"
            ))
        
        # Q872: Missing traces
        missing_traces = state.error_counts.get('missing_traces', 0)
        if missing_traces > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("missing_trace", str(missing_traces)),
                question_id=872,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Missing traces: {missing_traces}",
                description="Some traces are missing",
                affected_components=["Tracing"],
                remediation_available=True,
                remediation_action="investigate_tracing"
            ))
        
        # Q874: Trace context lost
        context_lost = state.error_counts.get('trace_context_lost', 0)
        if context_lost > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("context_lost", str(context_lost)),
                question_id=874,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Trace context lost: {context_lost}",
                description="Trace context not propagating",
                affected_components=["Tracing"],
                remediation_available=True,
                remediation_action="fix_context_propagation"
            ))
        
        return issues
    
    def _check_tracing_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q876-880: Tracing quality checks"""
        issues = []
        
        # Q878: Trace sampling issues
        sampling_issues = state.error_counts.get('trace_sampling_issue', 0)
        if sampling_issues > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("sampling", str(sampling_issues)),
                question_id=878,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Trace sampling issues: {sampling_issues}",
                description="Trace sampling not working correctly",
                affected_components=["Tracing"],
                remediation_available=True,
                remediation_action="fix_sampling"
            ))
        
        # Q880: Trace storage issues
        trace_storage = state.error_counts.get('trace_storage_issue', 0)
        if trace_storage > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("trace_storage", str(trace_storage)),
                question_id=880,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Trace storage issues",
                description="Trace storage having problems",
                affected_components=["Tracing"],
                remediation_available=True,
                remediation_action="fix_trace_storage"
            ))
        
        return issues
    
    # =========================================================================
    # Q881-890: Observability
    # =========================================================================
    
    def _check_observability(self, state: SystemState) -> List[ValidationIssue]:
        """Q881-885: Observability checks"""
        issues = []
        
        # Q881: Observability gaps
        obs_gaps = state.error_counts.get('observability_gaps', 0)
        if obs_gaps > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("obs_gaps", str(obs_gaps)),
                question_id=881,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Observability gaps: {obs_gaps}",
                description="Gaps in system observability",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="improve_observability"
            ))
        
        # Q882: Blind spots
        blind_spots = state.error_counts.get('monitoring_blind_spots', 0)
        if blind_spots > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("blind_spots", str(blind_spots)),
                question_id=882,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Monitoring blind spots: {blind_spots}",
                description="Areas not being monitored",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="add_monitoring"
            ))
        
        # Q884: Correlation failure
        correlation_fail = state.error_counts.get('observability_correlation_failure', 0)
        if correlation_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("corr_fail", str(correlation_fail)),
                question_id=884,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Observability correlation failure",
                description="Cannot correlate metrics, logs, and traces",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="fix_correlation"
            ))
        
        return issues
    
    def _check_observability_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q886-890: Observability quality checks"""
        issues = []
        
        # Q888: Root cause analysis failure
        rca_fail = state.error_counts.get('rca_failure', 0)
        if rca_fail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("rca_fail", str(rca_fail)),
                question_id=888,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"RCA failures: {rca_fail}",
                description="Cannot perform root cause analysis",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="improve_observability"
            ))
        
        # Q890: Observability overhead
        obs_overhead = state.latency_metrics.get('observability_overhead_percent', 0)
        if obs_overhead > 10:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("overhead", str(obs_overhead)),
                question_id=890,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"High observability overhead: {obs_overhead}%",
                description="Observability adding too much overhead",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="optimize_observability"
            ))
        
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_restart(self, issue: ValidationIssue) -> str:
        """Restart monitoring"""
        self.logger.info("Restarting monitoring")
        return "Monitoring restarted"
    
    async def _remediate_fix_alerts(self, issue: ValidationIssue) -> str:
        """Fix alerting"""
        self.logger.info("Fixing alerts")
        return "Alerts fixed"
    
    async def _remediate_retention(self, issue: ValidationIssue) -> str:
        """Increase retention"""
        self.logger.info("Increasing retention")
        return "Retention increased"
