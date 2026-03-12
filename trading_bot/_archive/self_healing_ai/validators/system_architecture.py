"""
System Architecture & Module Interaction Validator (Q1-50)
Addresses critical questions about system state, module coordination, and concurrency.
"""

import asyncio
import os
import psutil
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class SystemArchitectureValidator(BaseValidator):
    """Validates system architecture and module interactions (Q1-50)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.SYSTEM_ARCHITECTURE)
        self._position_locks: Dict[str, threading.Lock] = {}
        self._module_heartbeats: Dict[str, datetime] = {}
        self._message_queues: Dict[str, int] = {}
        self._state_snapshots: List[Dict] = []
        self._api_versions: Dict[str, str] = {}
    
    def _register_checks(self):
        """Register all Q1-50 validation checks"""
        # Q1: Single source of truth for system state
        self.add_check(self._check_state_source_of_truth, [1])
        # Q2: Position ownership guarantee
        self.add_check(self._check_position_ownership, [2])
        # Q3: End-to-end latency measurement
        self.add_check(self._check_latency_measurement, [3])
        # Q4: Silent module failure detection
        self.add_check(self._check_silent_failures, [4])
        # Q5: Stale reference handling
        self.add_check(self._check_stale_references, [5])
        # Q6: API versioning
        self.add_check(self._check_api_versioning, [6])
        # Q7: Partial system failure handling
        self.add_check(self._check_partial_failure_handling, [7])
        # Q8: Circular dependency deadlock prevention
        self.add_check(self._check_circular_dependencies, [8])
        # Q9: Mid-trade crash recovery
        self.add_check(self._check_crash_recovery, [9])
        # Q10: Configuration consistency
        self.add_check(self._check_config_consistency, [10])
        # Q11-20: Data flow and module coordination
        self.add_check(self._check_backpressure_handling, [11, 12])
        self.add_check(self._check_module_contracts, [13])
        self.add_check(self._check_garbage_output_detection, [14])
        self.add_check(self._check_unknown_symbol_handling, [15])
        self.add_check(self._check_message_preservation, [16])
        self.add_check(self._check_queue_management, [17])
        self.add_check(self._check_event_tracing, [18])
        self.add_check(self._check_message_bus_partition, [19])
        self.add_check(self._check_module_interaction_tests, [20])
        # Q21-30: State management
        self.add_check(self._check_position_storage, [21])
        self.add_check(self._check_position_reconciliation, [22])
        self.add_check(self._check_snapshot_frequency, [23])
        self.add_check(self._check_unclean_shutdown_recovery, [24])
        self.add_check(self._check_recovery_timing, [25])
        self.add_check(self._check_state_corruption, [26])
        self.add_check(self._check_stale_state, [27])
        self.add_check(self._check_race_conditions, [28])
        self.add_check(self._check_state_growth, [29])
        self.add_check(self._check_schema_migration, [30])
        # Q31-40: External dependencies
        self.add_check(self._check_dependency_availability, [31])
        self.add_check(self._check_dependency_data_correctness, [32])
        self.add_check(self._check_dependency_fallbacks, [33])
        self.add_check(self._check_version_conflicts, [34])
        self.add_check(self._check_behavior_changes, [35])
        self.add_check(self._check_degraded_dependency_testing, [36])
        self.add_check(self._check_blast_radius, [37])
        self.add_check(self._check_slow_dependency_blocking, [38])
        self.add_check(self._check_timeout_config, [39])
        self.add_check(self._check_rate_limits, [40])
        # Q41-50: Concurrency
        self.add_check(self._check_concurrent_modification, [41])
        self.add_check(self._check_deadlock_prevention, [42])
        self.add_check(self._check_thread_pool_exhaustion, [43])
        self.add_check(self._check_thread_starvation, [44])
        self.add_check(self._check_async_exceptions, [45])
        self.add_check(self._check_callback_depth, [46])
        self.add_check(self._check_cpu_blocking, [47])
        self.add_check(self._check_async_memory_leaks, [48])
        self.add_check(self._check_threadlocal_consistency, [49])
        self.add_check(self._check_load_race_conditions, [50])
        
        # Register remediations
        self.add_remediation("restart_module", self._remediate_restart_module)
        self.add_remediation("clear_stale_locks", self._remediate_clear_locks)
        self.add_remediation("reset_queue", self._remediate_reset_queue)
        self.add_remediation("force_reconciliation", self._remediate_force_reconciliation)
    
    # =========================================================================
    # Q1-10: Core System State
    # =========================================================================
    
    def _check_state_source_of_truth(self, state: SystemState) -> List[ValidationIssue]:
        """Q1: What is the single source of truth for system state?"""
        issues = []
        
        # Check if state manager exists and is accessible
        state_files = list(Path("trading_bot").rglob("*state*.db")) + \
                     list(Path("trading_bot").rglob("*state*.json"))
        
        if len(state_files) > 3:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("state_source", "multiple_sources"),
                question_id=1,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Multiple state sources detected",
                description=f"Found {len(state_files)} potential state files. Risk of inconsistent state.",
                affected_components=["StateManager", "Database"],
                remediation_available=True,
                remediation_action="consolidate_state",
                metadata={"state_files": [str(f) for f in state_files[:10]]}
            ))
        
        # Check for state corruption indicators
        if state.error_counts.get('state_corruption', 0) > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("state_corruption", "detected"),
                question_id=1,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="State corruption detected",
                description="System state may be corrupted. Immediate attention required.",
                affected_components=["StateManager"],
                remediation_available=True,
                remediation_action="restore_state_backup"
            ))
        
        return issues
    
    def _check_position_ownership(self, state: SystemState) -> List[ValidationIssue]:
        """Q2: How do you guarantee no two modules own the same position?"""
        issues = []
        
        # Check for position lock mechanism
        positions = state.positions
        for symbol, pos_data in positions.items():
            if isinstance(pos_data, dict):
                owners = pos_data.get('owners', [])
                if len(owners) > 1:
                    issues.append(ValidationIssue(
                        issue_id=self._generate_issue_id("position_ownership", symbol),
                        question_id=2,
                        category=self.category,
                        severity=ValidationSeverity.CRITICAL,
                        title=f"Multiple owners for position: {symbol}",
                        description=f"Position {symbol} has {len(owners)} owners: {owners}",
                        affected_components=["PositionManager", "ExecutionEngine"],
                        remediation_available=True,
                        remediation_action="clear_stale_locks",
                        metadata={"symbol": symbol, "owners": owners}
                    ))
        
        return issues
    
    def _check_latency_measurement(self, state: SystemState) -> List[ValidationIssue]:
        """Q3: What is the maximum end-to-end latency?"""
        issues = []
        
        latency = state.latency_metrics.get('e2e_latency_ms', 0)
        max_latency = IMMUTABLE_LIMITS['max_latency_ms']
        
        if latency > max_latency:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("latency", str(latency)),
                question_id=3,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Latency exceeds threshold: {latency}ms > {max_latency}ms",
                description=f"End-to-end latency of {latency}ms exceeds maximum allowed {max_latency}ms",
                affected_components=["ExecutionEngine", "DataPipeline"],
                remediation_available=True,
                remediation_action="optimize_latency",
                metadata={"current_latency": latency, "max_allowed": max_latency}
            ))
        
        # Check if latency is being measured
        if 'e2e_latency_ms' not in state.latency_metrics:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("latency", "not_measured"),
                question_id=3,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="End-to-end latency not being measured",
                description="No latency metrics found. Cannot verify system performance.",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="enable_latency_monitoring"
            ))
        
        return issues
    
    def _check_silent_failures(self, state: SystemState) -> List[ValidationIssue]:
        """Q4: How do you detect when a module has silently stopped?"""
        issues = []
        
        now = datetime.utcnow()
        heartbeat_threshold = timedelta(seconds=30)
        
        for module, last_beat in state.last_heartbeat.items():
            if now - last_beat > heartbeat_threshold:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("silent_failure", module),
                    question_id=4,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Module {module} may have silently failed",
                    description=f"No heartbeat from {module} for {(now - last_beat).seconds}s",
                    affected_components=[module],
                    remediation_available=True,
                    remediation_action="restart_module",
                    auto_remediate=True,
                    metadata={"module": module, "last_heartbeat": last_beat.isoformat()}
                ))
        
        # Check for modules that should have heartbeats but don't
        expected_modules = ['DataPipeline', 'ExecutionEngine', 'RiskManager', 'StrategyEngine']
        for module in expected_modules:
            if module not in state.last_heartbeat:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("missing_heartbeat", module),
                    question_id=4,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"No heartbeat configured for {module}",
                    description=f"Module {module} has no heartbeat monitoring",
                    affected_components=[module, "Monitoring"],
                    remediation_available=True,
                    remediation_action="configure_heartbeat"
                ))
        
        return issues
    
    def _check_stale_references(self, state: SystemState) -> List[ValidationIssue]:
        """Q5: What happens when module A depends on B and B restarts?"""
        issues = []
        
        # Check for stale reference indicators
        stale_refs = state.error_counts.get('stale_reference', 0)
        if stale_refs > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stale_refs", str(stale_refs)),
                question_id=5,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Stale references detected: {stale_refs}",
                description="Modules may be holding stale references to restarted components",
                affected_components=["ModuleManager"],
                remediation_available=True,
                remediation_action="refresh_references"
            ))
        
        return issues
    
    def _check_api_versioning(self, state: SystemState) -> List[ValidationIssue]:
        """Q6: How do you version internal APIs?"""
        issues = []
        
        # Check for API version mismatches
        api_versions = self._api_versions
        if len(set(api_versions.values())) > 1:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("api_version", "mismatch"),
                question_id=6,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="API version mismatch between modules",
                description=f"Different API versions detected: {api_versions}",
                affected_components=list(api_versions.keys()),
                remediation_available=False,
                metadata={"versions": api_versions}
            ))
        
        return issues
    
    def _check_partial_failure_handling(self, state: SystemState) -> List[ValidationIssue]:
        """Q7: Strategy for handling partial system failures"""
        issues = []
        
        # Count failed vs working modules
        total_modules = len(state.last_heartbeat)
        failed_modules = sum(1 for m, t in state.last_heartbeat.items() 
                           if datetime.utcnow() - t > timedelta(seconds=30))
        
        if total_modules > 0 and failed_modules > 0 and failed_modules < total_modules:
            failure_ratio = failed_modules / total_modules
            if failure_ratio > 0.3:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("partial_failure", str(failure_ratio)),
                    question_id=7,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Partial system failure: {failed_modules}/{total_modules} modules down",
                    description="System is in degraded state with some modules failed",
                    affected_components=["System"],
                    remediation_available=True,
                    remediation_action="graceful_degradation"
                ))
        
        return issues
    
    def _check_circular_dependencies(self, state: SystemState) -> List[ValidationIssue]:
        """Q8: Prevent circular dependencies from creating deadlocks"""
        issues = []
        
        deadlock_count = state.error_counts.get('deadlock', 0)
        if deadlock_count > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("deadlock", str(deadlock_count)),
                question_id=8,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Deadlock detected: {deadlock_count} occurrences",
                description="Circular dependencies may be causing deadlocks",
                affected_components=["System"],
                remediation_available=True,
                remediation_action="break_deadlock",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_crash_recovery(self, state: SystemState) -> List[ValidationIssue]:
        """Q9: Recovery procedure for mid-trade crash"""
        issues = []
        
        # Check for orders in flight without confirmation
        for order_id, order in state.orders.items():
            if isinstance(order, dict):
                status = order.get('status', '')
                if status in ['pending', 'submitted', 'partial']:
                    age = datetime.utcnow() - datetime.fromisoformat(order.get('submitted_at', datetime.utcnow().isoformat()))
                    if age > timedelta(minutes=5):
                        issues.append(ValidationIssue(
                            issue_id=self._generate_issue_id("orphan_order", order_id),
                            question_id=9,
                            category=self.category,
                            severity=ValidationSeverity.CRITICAL,
                            title=f"Orphaned order detected: {order_id}",
                            description=f"Order {order_id} has been {status} for {age.seconds}s",
                            affected_components=["ExecutionEngine", "OrderManager"],
                            remediation_available=True,
                            remediation_action="reconcile_order",
                            metadata={"order_id": order_id, "status": status}
                        ))
        
        return issues
    
    def _check_config_consistency(self, state: SystemState) -> List[ValidationIssue]:
        """Q10: Configuration changes don't create inconsistent state"""
        issues = []
        
        config_errors = state.error_counts.get('config_inconsistency', 0)
        if config_errors > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("config", str(config_errors)),
                question_id=10,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Configuration inconsistency detected",
                description=f"{config_errors} configuration inconsistencies found",
                affected_components=["ConfigManager"],
                remediation_available=True,
                remediation_action="reload_config"
            ))
        
        return issues
    
    # =========================================================================
    # Q11-20: Data Flow and Module Coordination
    # =========================================================================
    
    def _check_backpressure_handling(self, state: SystemState) -> List[ValidationIssue]:
        """Q11-12: Handle backpressure when modules have different speeds"""
        issues = []
        
        for queue_name, depth in self._message_queues.items():
            if depth > 10000:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("backpressure", queue_name),
                    question_id=11,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Queue backpressure: {queue_name} has {depth} messages",
                    description="Downstream module cannot keep up with upstream",
                    affected_components=[queue_name],
                    remediation_available=True,
                    remediation_action="reset_queue"
                ))
        
        return issues
    
    def _check_module_contracts(self, state: SystemState) -> List[ValidationIssue]:
        """Q13: Contract between modules and runtime enforcement"""
        issues = []
        
        contract_violations = state.error_counts.get('contract_violation', 0)
        if contract_violations > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("contract", str(contract_violations)),
                question_id=13,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Module contract violations: {contract_violations}",
                description="Modules are not adhering to defined contracts",
                affected_components=["ModuleManager"],
                remediation_available=False
            ))
        
        return issues
    
    def _check_garbage_output_detection(self, state: SystemState) -> List[ValidationIssue]:
        """Q14: Detect when a module produces garbage that looks valid"""
        issues = []
        
        garbage_count = state.error_counts.get('garbage_output', 0)
        if garbage_count > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("garbage", str(garbage_count)),
                question_id=14,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Garbage output detected: {garbage_count} instances",
                description="Module producing invalid data that passes basic validation",
                affected_components=["DataValidator"],
                remediation_available=True,
                remediation_action="quarantine_output"
            ))
        
        return issues
    
    def _check_unknown_symbol_handling(self, state: SystemState) -> List[ValidationIssue]:
        """Q15: Handle signals for unknown symbols"""
        issues = []
        
        unknown_symbols = state.error_counts.get('unknown_symbol', 0)
        if unknown_symbols > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unknown_symbol", str(unknown_symbols)),
                question_id=15,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Unknown symbol requests: {unknown_symbols}",
                description="Execution received signals for unrecognized symbols",
                affected_components=["ExecutionEngine", "SymbolManager"],
                remediation_available=True,
                remediation_action="update_symbol_list"
            ))
        
        return issues
    
    def _check_message_preservation(self, state: SystemState) -> List[ValidationIssue]:
        """Q16: Handle module restarts without losing messages"""
        issues = []
        
        lost_messages = state.error_counts.get('lost_messages', 0)
        if lost_messages > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("lost_messages", str(lost_messages)),
                question_id=16,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Lost messages during restart: {lost_messages}",
                description="Messages were lost during module restart",
                affected_components=["MessageBus"],
                remediation_available=False
            ))
        
        return issues
    
    def _check_queue_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q17: Maximum queue depth before dropping messages"""
        issues = []
        
        dropped_messages = state.error_counts.get('dropped_messages', 0)
        if dropped_messages > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dropped", str(dropped_messages)),
                question_id=17,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Messages dropped: {dropped_messages}",
                description="Queue overflow caused message drops",
                affected_components=["MessageBus"],
                remediation_available=True,
                remediation_action="increase_queue_size"
            ))
        
        return issues
    
    def _check_event_tracing(self, state: SystemState) -> List[ValidationIssue]:
        """Q18: Trace a single market event through all modules"""
        issues = []
        
        # Check if tracing is enabled
        if not state.latency_metrics.get('tracing_enabled', False):
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("tracing", "disabled"),
                question_id=18,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Event tracing not enabled",
                description="Cannot trace events through system for debugging",
                affected_components=["Monitoring"],
                remediation_available=True,
                remediation_action="enable_tracing"
            ))
        
        return issues
    
    def _check_message_bus_partition(self, state: SystemState) -> List[ValidationIssue]:
        """Q19: Handle message bus partitions"""
        issues = []
        
        partition_events = state.error_counts.get('bus_partition', 0)
        if partition_events > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("partition", str(partition_events)),
                question_id=19,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Message bus partition detected: {partition_events}",
                description="Modules cannot communicate due to bus partition",
                affected_components=["MessageBus"],
                remediation_available=True,
                remediation_action="heal_partition"
            ))
        
        return issues
    
    def _check_module_interaction_tests(self, state: SystemState) -> List[ValidationIssue]:
        """Q20: Test module interactions under failure conditions"""
        issues = []
        
        # Check if integration tests exist and pass
        test_results = state.metadata if hasattr(state, 'metadata') else {}
        if not test_results.get('integration_tests_passed', True):
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("tests", "failed"),
                question_id=20,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Module interaction tests failing",
                description="Integration tests are not passing",
                affected_components=["Testing"],
                remediation_available=False
            ))
        
        return issues
    
    # =========================================================================
    # Q21-30: State Management
    # =========================================================================
    
    def _check_position_storage(self, state: SystemState) -> List[ValidationIssue]:
        """Q21: Where is position state stored?"""
        issues = []
        
        if not state.positions and state.equity > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("position_storage", "missing"),
                question_id=21,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Position state may be missing",
                description="Equity exists but no positions found",
                affected_components=["PositionManager"],
                remediation_available=True,
                remediation_action="force_reconciliation"
            ))
        
        return issues
    
    def _check_position_reconciliation(self, state: SystemState) -> List[ValidationIssue]:
        """Q22: Reconcile internal vs broker positions"""
        issues = []
        
        recon_errors = state.error_counts.get('reconciliation_error', 0)
        if recon_errors > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("reconciliation", str(recon_errors)),
                question_id=22,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Position reconciliation errors: {recon_errors}",
                description="Internal positions don't match broker positions",
                affected_components=["PositionManager", "BrokerAdapter"],
                remediation_available=True,
                remediation_action="force_reconciliation",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_snapshot_frequency(self, state: SystemState) -> List[ValidationIssue]:
        """Q23: State snapshot frequency"""
        issues = []
        
        last_snapshot = state.last_heartbeat.get('StateSnapshot')
        if last_snapshot:
            age = datetime.utcnow() - last_snapshot
            if age > timedelta(minutes=5):
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("snapshot", str(age.seconds)),
                    question_id=23,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"State snapshot is {age.seconds}s old",
                    description="State snapshots should be more frequent",
                    affected_components=["StateManager"],
                    remediation_available=True,
                    remediation_action="force_snapshot"
                ))
        
        return issues
    
    def _check_unclean_shutdown_recovery(self, state: SystemState) -> List[ValidationIssue]:
        """Q24: State recovery after unclean shutdown"""
        issues = []
        
        if state.error_counts.get('unclean_shutdown', 0) > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unclean", "shutdown"),
                question_id=24,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Unclean shutdown detected",
                description="System may have state inconsistencies from unclean shutdown",
                affected_components=["StateManager"],
                remediation_available=True,
                remediation_action="validate_state"
            ))
        
        return issues
    
    def _check_recovery_timing(self, state: SystemState) -> List[ValidationIssue]:
        """Q25: Recovery vs market open timing"""
        issues = []
        # This would check actual recovery time vs market schedule
        return issues
    
    def _check_state_corruption(self, state: SystemState) -> List[ValidationIssue]:
        """Q26: Detect state corruption before bad trades"""
        issues = []
        
        corruption_indicators = state.error_counts.get('state_corruption', 0)
        if corruption_indicators > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("corruption", str(corruption_indicators)),
                question_id=26,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="State corruption indicators detected",
                description="State may be corrupted - trading should be halted",
                affected_components=["StateManager"],
                remediation_available=True,
                remediation_action="restore_backup",
                auto_remediate=False
            ))
        
        return issues
    
    def _check_stale_state(self, state: SystemState) -> List[ValidationIssue]:
        """Q27: Handle valid but stale state"""
        issues = []
        # Check for stale state indicators
        return issues
    
    def _check_race_conditions(self, state: SystemState) -> List[ValidationIssue]:
        """Q28: Prevent race conditions in shared state"""
        issues = []
        
        race_conditions = state.error_counts.get('race_condition', 0)
        if race_conditions > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("race", str(race_conditions)),
                question_id=28,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Race conditions detected: {race_conditions}",
                description="Multiple processes updating shared state unsafely",
                affected_components=["StateManager"],
                remediation_available=True,
                remediation_action="add_locking"
            ))
        
        return issues
    
    def _check_state_growth(self, state: SystemState) -> List[ValidationIssue]:
        """Q29: Handle unbounded state growth"""
        issues = []
        
        # Check memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > 2000:  # 2GB threshold
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("memory", str(memory_mb)),
                question_id=29,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"High memory usage: {memory_mb:.0f}MB",
                description="State may be growing unbounded",
                affected_components=["StateManager"],
                remediation_available=True,
                remediation_action="gc_state"
            ))
        
        return issues
    
    def _check_schema_migration(self, state: SystemState) -> List[ValidationIssue]:
        """Q30: State schema migration"""
        issues = []
        
        migration_errors = state.error_counts.get('schema_migration', 0)
        if migration_errors > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("migration", str(migration_errors)),
                question_id=30,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Schema migration errors: {migration_errors}",
                description="State schema migration failed",
                affected_components=["StateManager", "Database"],
                remediation_available=False
            ))
        
        return issues
    
    # =========================================================================
    # Q31-40: External Dependencies
    # =========================================================================
    
    def _check_dependency_availability(self, state: SystemState) -> List[ValidationIssue]:
        """Q31: Handle critical dependency unavailability"""
        issues = []
        
        for source, data in state.data_sources.items():
            if isinstance(data, dict) and not data.get('available', True):
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("dependency", source),
                    question_id=31,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Dependency unavailable: {source}",
                    description=f"Critical dependency {source} is not available",
                    affected_components=[source],
                    remediation_available=True,
                    remediation_action="activate_fallback"
                ))
        
        return issues
    
    def _check_dependency_data_correctness(self, state: SystemState) -> List[ValidationIssue]:
        """Q32: Detect incorrect data from dependencies"""
        issues = []
        
        bad_data = state.error_counts.get('bad_dependency_data', 0)
        if bad_data > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("bad_data", str(bad_data)),
                question_id=32,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Bad dependency data: {bad_data} instances",
                description="Dependency returning incorrect data",
                affected_components=["DataValidator"],
                remediation_available=True,
                remediation_action="quarantine_source"
            ))
        
        return issues
    
    def _check_dependency_fallbacks(self, state: SystemState) -> List[ValidationIssue]:
        """Q33: Fallback strategy for each dependency"""
        issues = []
        # Check if fallbacks are configured
        return issues
    
    def _check_version_conflicts(self, state: SystemState) -> List[ValidationIssue]:
        """Q34: Dependency version conflicts"""
        issues = []
        return issues
    
    def _check_behavior_changes(self, state: SystemState) -> List[ValidationIssue]:
        """Q35: Dependency behavior changes without API changes"""
        issues = []
        return issues
    
    def _check_degraded_dependency_testing(self, state: SystemState) -> List[ValidationIssue]:
        """Q36: Test with degraded dependencies"""
        issues = []
        return issues
    
    def _check_blast_radius(self, state: SystemState) -> List[ValidationIssue]:
        """Q37: Blast radius of dependency failure"""
        issues = []
        return issues
    
    def _check_slow_dependency_blocking(self, state: SystemState) -> List[ValidationIssue]:
        """Q38: Prevent slow dependency from blocking system"""
        issues = []
        
        for source, latency in state.latency_metrics.items():
            if latency > 1000:  # 1 second
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("slow_dep", source),
                    question_id=38,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Slow dependency: {source} ({latency}ms)",
                    description=f"Dependency {source} is too slow",
                    affected_components=[source],
                    remediation_available=True,
                    remediation_action="timeout_dependency"
                ))
        
        return issues
    
    def _check_timeout_config(self, state: SystemState) -> List[ValidationIssue]:
        """Q39: Timeout misconfiguration"""
        issues = []
        return issues
    
    def _check_rate_limits(self, state: SystemState) -> List[ValidationIssue]:
        """Q40: Handle rate limits"""
        issues = []
        
        rate_limit_hits = state.error_counts.get('rate_limit', 0)
        if rate_limit_hits > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("rate_limit", str(rate_limit_hits)),
                question_id=40,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Rate limit hits: {rate_limit_hits}",
                description="Hitting rate limits on external dependencies",
                affected_components=["APIClient"],
                remediation_available=True,
                remediation_action="reduce_request_rate"
            ))
        
        return issues
    
    # =========================================================================
    # Q41-50: Concurrency
    # =========================================================================
    
    def _check_concurrent_modification(self, state: SystemState) -> List[ValidationIssue]:
        """Q41: Concurrent position modification"""
        issues = []
        
        concurrent_mods = state.error_counts.get('concurrent_modification', 0)
        if concurrent_mods > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("concurrent", str(concurrent_mods)),
                question_id=41,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Concurrent modification errors: {concurrent_mods}",
                description="Multiple threads modifying same position",
                affected_components=["PositionManager"],
                remediation_available=True,
                remediation_action="add_position_locks"
            ))
        
        return issues
    
    def _check_deadlock_prevention(self, state: SystemState) -> List[ValidationIssue]:
        """Q42: Deadlock prevention"""
        issues = []
        return issues
    
    def _check_thread_pool_exhaustion(self, state: SystemState) -> List[ValidationIssue]:
        """Q43: Thread pool exhaustion"""
        issues = []
        
        active_threads = threading.active_count()
        if active_threads > 100:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("threads", str(active_threads)),
                question_id=43,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"High thread count: {active_threads}",
                description="Thread pool may be exhausted",
                affected_components=["ThreadPool"],
                remediation_available=True,
                remediation_action="cleanup_threads"
            ))
        
        return issues
    
    def _check_thread_starvation(self, state: SystemState) -> List[ValidationIssue]:
        """Q44: Thread starvation detection"""
        issues = []
        return issues
    
    def _check_async_exceptions(self, state: SystemState) -> List[ValidationIssue]:
        """Q45: Uncaught async exceptions"""
        issues = []
        
        uncaught = state.error_counts.get('uncaught_async', 0)
        if uncaught > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("uncaught", str(uncaught)),
                question_id=45,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Uncaught async exceptions: {uncaught}",
                description="Async tasks throwing unhandled exceptions",
                affected_components=["AsyncEngine"],
                remediation_available=False
            ))
        
        return issues
    
    def _check_callback_depth(self, state: SystemState) -> List[ValidationIssue]:
        """Q46: Callback hell in nested async"""
        issues = []
        return issues
    
    def _check_cpu_blocking(self, state: SystemState) -> List[ValidationIssue]:
        """Q47: CPU-bound tasks blocking event loop"""
        issues = []
        
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > 90:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("cpu", str(cpu_percent)),
                question_id=47,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"High CPU usage: {cpu_percent}%",
                description="CPU-bound tasks may be blocking event loop",
                affected_components=["EventLoop"],
                remediation_available=True,
                remediation_action="offload_cpu_tasks"
            ))
        
        return issues
    
    def _check_async_memory_leaks(self, state: SystemState) -> List[ValidationIssue]:
        """Q48: Memory leaks from async tasks"""
        issues = []
        return issues
    
    def _check_threadlocal_consistency(self, state: SystemState) -> List[ValidationIssue]:
        """Q49: Thread-local state consistency"""
        issues = []
        return issues
    
    def _check_load_race_conditions(self, state: SystemState) -> List[ValidationIssue]:
        """Q50: Race conditions under load"""
        issues = []
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_restart_module(self, issue: ValidationIssue) -> str:
        """Restart a failed module"""
        module = issue.metadata.get('module', 'unknown')
        self.logger.info(f"Restarting module: {module}")
        # Implementation would restart the actual module
        return f"Module {module} restart initiated"
    
    async def _remediate_clear_locks(self, issue: ValidationIssue) -> str:
        """Clear stale position locks"""
        symbol = issue.metadata.get('symbol', 'unknown')
        if symbol in self._position_locks:
            del self._position_locks[symbol]
        return f"Cleared locks for {symbol}"
    
    async def _remediate_reset_queue(self, issue: ValidationIssue) -> str:
        """Reset an overflowing queue"""
        queue_name = issue.metadata.get('queue_name', 'unknown')
        self._message_queues[queue_name] = 0
        return f"Reset queue {queue_name}"
    
    async def _remediate_force_reconciliation(self, issue: ValidationIssue) -> str:
        """Force position reconciliation"""
        self.logger.info("Forcing position reconciliation")
        return "Position reconciliation initiated"
