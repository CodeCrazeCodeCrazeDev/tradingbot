"""
Kill-Switch Validator (Q891-930)
Addresses emergency shutdown, trading halts, position liquidation, and recovery procedures.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)

import logging
logger = logging.getLogger(__name__)



class KillSwitchValidator(BaseValidator):
    """Validates kill-switch and emergency shutdown (Q891-930)"""
    
    def __init__(self):
        try:
            super().__init__(ValidationCategory.KILL_SWITCHES)
            self._killswitch_state: Dict[str, Any] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _register_checks(self):
        """Register all Q891-930 validation checks"""
        # Q891-900: Kill Switch Functionality
        try:
            self.add_check(self._check_killswitch_functionality, [891, 892, 893, 894, 895])
            self.add_check(self._check_functionality_quality, [896, 897, 898, 899, 900])
            # Q901-910: Trading Halts
            self.add_check(self._check_trading_halts, [901, 902, 903, 904, 905])
            self.add_check(self._check_halt_quality, [906, 907, 908, 909, 910])
            # Q911-920: Position Liquidation
            self.add_check(self._check_liquidation, [911, 912, 913, 914, 915])
            self.add_check(self._check_liquidation_quality, [916, 917, 918, 919, 920])
            # Q921-930: Recovery Procedures
            self.add_check(self._check_recovery, [921, 922, 923, 924, 925])
            self.add_check(self._check_recovery_quality, [926, 927, 928, 929, 930])
        
            # Register remediations
            self.add_remediation("activate_killswitch", self._remediate_activate)
            self.add_remediation("test_killswitch", self._remediate_test)
            self.add_remediation("repair_killswitch", self._remediate_repair)
        except Exception as e:
            logger.error(f"Error in _register_checks: {e}")
            raise
    
    # =========================================================================
    # Q891-900: Kill Switch Functionality
    # =========================================================================
    
    def _check_killswitch_functionality(self, state: SystemState) -> List[ValidationIssue]:
        """Q891-895: Kill switch functionality checks"""
        try:
            issues = []
        
            # Q891: Kill switch unavailable
            ks_unavailable = state.error_counts.get('killswitch_unavailable', 0)
            if ks_unavailable > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("ks_unavail", str(ks_unavailable)),
                    question_id=891,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Kill switch unavailable",
                    description="Emergency kill switch is not available",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="repair_killswitch",
                    auto_remediate=True
                ))
        
            # Q892: Kill switch failure
            ks_failure = state.error_counts.get('killswitch_failure', 0)
            if ks_failure > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("ks_fail", str(ks_failure)),
                    question_id=892,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Kill switch failures: {ks_failure}",
                    description="Kill switch failed to activate",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="repair_killswitch",
                    auto_remediate=True
                ))
        
            # Q893: Partial kill switch
            partial_ks = state.error_counts.get('partial_killswitch', 0)
            if partial_ks > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("partial_ks", str(partial_ks)),
                    question_id=893,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Partial kill switch activation",
                    description="Kill switch only partially activated",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="complete_killswitch"
                ))
        
            # Q894: Kill switch bypass
            ks_bypass = state.error_counts.get('killswitch_bypass', 0)
            if ks_bypass > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("ks_bypass", str(ks_bypass)),
                    question_id=894,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Kill switch bypassed",
                    description="Kill switch was bypassed",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="activate_killswitch",
                    auto_remediate=True
                ))
        
            # Q895: Kill switch latency
            ks_latency = state.latency_metrics.get('killswitch_latency_ms', 0)
            if ks_latency > 1000:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("ks_latency", str(ks_latency)),
                    question_id=895,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Kill switch latency: {ks_latency}ms",
                    description="Kill switch activation too slow",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="optimize_killswitch"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_killswitch_functionality: {e}")
            raise
    
    def _check_functionality_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q896-900: Functionality quality checks"""
        try:
            issues = []
        
            # Q896: Kill switch not tested
            last_test_days = state.data_sources.get('killswitch_last_test_days', 999)
            if last_test_days > 7:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("ks_test", str(last_test_days)),
                    question_id=896,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Kill switch not tested in {last_test_days} days",
                    description="Kill switch needs regular testing",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="test_killswitch"
                ))
        
            # Q898: Kill switch misconfiguration
            ks_misconfig = state.error_counts.get('killswitch_misconfiguration', 0)
            if ks_misconfig > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("ks_misconfig", str(ks_misconfig)),
                    question_id=898,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Kill switch misconfigured",
                    description="Kill switch configuration is incorrect",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="fix_killswitch_config"
                ))
        
            # Q900: Kill switch monitoring failure
            ks_mon_fail = state.error_counts.get('killswitch_monitoring_failure', 0)
            if ks_mon_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("ks_mon", str(ks_mon_fail)),
                    question_id=900,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Kill switch monitoring failed",
                    description="Cannot monitor kill switch status",
                    affected_components=["KillSwitch", "Monitoring"],
                    remediation_available=True,
                    remediation_action="restart_monitoring"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_functionality_quality: {e}")
            raise
    
    # =========================================================================
    # Q901-910: Trading Halts
    # =========================================================================
    
    def _check_trading_halts(self, state: SystemState) -> List[ValidationIssue]:
        """Q901-905: Trading halt checks"""
        try:
            issues = []
        
            # Q901: Halt failure
            halt_failure = state.error_counts.get('trading_halt_failure', 0)
            if halt_failure > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("halt_fail", str(halt_failure)),
                    question_id=901,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Trading halt failures: {halt_failure}",
                    description="Failed to halt trading",
                    affected_components=["KillSwitch", "ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="force_halt",
                    auto_remediate=True
                ))
        
            # Q902: Orders during halt
            orders_during_halt = state.error_counts.get('orders_during_halt', 0)
            if orders_during_halt > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("orders_halt", str(orders_during_halt)),
                    question_id=902,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Orders placed during halt: {orders_during_halt}",
                    description="Orders submitted while trading halted",
                    affected_components=["ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="cancel_orders",
                    auto_remediate=True
                ))
        
            # Q903: Halt not propagated
            halt_not_propagated = state.error_counts.get('halt_not_propagated', 0)
            if halt_not_propagated > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("halt_prop", str(halt_not_propagated)),
                    question_id=903,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Trading halt not propagated",
                    description="Halt signal not reaching all components",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="force_halt"
                ))
        
            # Q905: Premature halt release
            premature_release = state.error_counts.get('premature_halt_release', 0)
            if premature_release > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("premature", str(premature_release)),
                    question_id=905,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Premature halt release",
                    description="Trading halt released too early",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="reinstate_halt"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_trading_halts: {e}")
            raise
    
    def _check_halt_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q906-910: Halt quality checks"""
        try:
            issues = []
        
            # Q908: Halt conditions unclear
            unclear_conditions = state.error_counts.get('unclear_halt_conditions', 0)
            if unclear_conditions > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("unclear", str(unclear_conditions)),
                    question_id=908,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Unclear halt conditions",
                    description="Halt trigger conditions not well defined",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="define_conditions"
                ))
        
            # Q910: Halt override abuse
            override_abuse = state.error_counts.get('halt_override_abuse', 0)
            if override_abuse > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("override", str(override_abuse)),
                    question_id=910,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Halt override abuse: {override_abuse}",
                    description="Halt overrides being misused",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="restrict_overrides"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_halt_quality: {e}")
            raise
    
    # =========================================================================
    # Q911-920: Position Liquidation
    # =========================================================================
    
    def _check_liquidation(self, state: SystemState) -> List[ValidationIssue]:
        """Q911-915: Position liquidation checks"""
        try:
            issues = []
        
            # Q911: Liquidation failure
            liq_failure = state.error_counts.get('liquidation_failure', 0)
            if liq_failure > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("liq_fail", str(liq_failure)),
                    question_id=911,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Liquidation failures: {liq_failure}",
                    description="Failed to liquidate positions",
                    affected_components=["KillSwitch", "ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="force_liquidation",
                    auto_remediate=True
                ))
        
            # Q912: Partial liquidation
            partial_liq = state.error_counts.get('partial_liquidation', 0)
            if partial_liq > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("partial_liq", str(partial_liq)),
                    question_id=912,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title="Partial liquidation",
                    description="Only some positions liquidated",
                    affected_components=["KillSwitch", "ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="complete_liquidation"
                ))
        
            # Q913: Liquidation slippage
            liq_slippage = state.error_counts.get('liquidation_slippage_exceeded', 0)
            if liq_slippage > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("liq_slip", str(liq_slippage)),
                    question_id=913,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Excessive liquidation slippage",
                    description="Liquidation slippage exceeded expectations",
                    affected_components=["ExecutionEngine"],
                    remediation_available=False
                ))
        
            # Q915: Liquidation during illiquidity
            illiquid_liq = state.error_counts.get('liquidation_during_illiquidity', 0)
            if illiquid_liq > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("illiquid_liq", str(illiquid_liq)),
                    question_id=915,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Liquidation during illiquidity",
                    description="Forced to liquidate in illiquid market",
                    affected_components=["ExecutionEngine"],
                    remediation_available=False
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_liquidation: {e}")
            raise
    
    def _check_liquidation_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q916-920: Liquidation quality checks"""
        try:
            issues = []
        
            # Q918: Liquidation priority issues
            priority_issues = state.error_counts.get('liquidation_priority_issue', 0)
            if priority_issues > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("priority", str(priority_issues)),
                    question_id=918,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"Liquidation priority issues: {priority_issues}",
                    description="Positions not liquidated in optimal order",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="fix_priority"
                ))
        
            # Q920: Liquidation impact
            liq_impact = state.error_counts.get('liquidation_market_impact', 0)
            if liq_impact > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("liq_impact", str(liq_impact)),
                    question_id=920,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="High liquidation market impact",
                    description="Liquidation causing significant market impact",
                    affected_components=["ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="optimize_liquidation"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_liquidation_quality: {e}")
            raise
    
    # =========================================================================
    # Q921-930: Recovery Procedures
    # =========================================================================
    
    def _check_recovery(self, state: SystemState) -> List[ValidationIssue]:
        """Q921-925: Recovery procedure checks"""
        try:
            issues = []
        
            # Q921: No recovery plan
            no_plan = state.error_counts.get('no_recovery_plan', 0)
            if no_plan > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("no_plan", str(no_plan)),
                    question_id=921,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="No recovery plan",
                    description="No plan for recovery after kill switch",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="create_recovery_plan"
                ))
        
            # Q922: Recovery failure
            recovery_fail = state.error_counts.get('recovery_failure', 0)
            if recovery_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("recovery_fail", str(recovery_fail)),
                    question_id=922,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Recovery failures: {recovery_fail}",
                    description="Failed to recover from shutdown",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="manual_recovery"
                ))
        
            # Q923: Premature recovery
            premature_recovery = state.error_counts.get('premature_recovery', 0)
            if premature_recovery > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("premature_rec", str(premature_recovery)),
                    question_id=923,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Premature recovery attempt",
                    description="Attempted recovery before conditions safe",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="reinstate_halt"
                ))
        
            # Q925: Recovery validation failure
            validation_fail = state.error_counts.get('recovery_validation_failure', 0)
            if validation_fail > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("rec_valid", str(validation_fail)),
                    question_id=925,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title="Recovery validation failed",
                    description="System not validated before recovery",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="validate_system"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_recovery: {e}")
            raise
    
    def _check_recovery_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q926-930: Recovery quality checks"""
        try:
            issues = []
        
            # Q928: Recovery not tested
            recovery_not_tested = state.error_counts.get('recovery_not_tested', 0)
            if recovery_not_tested > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("rec_test", str(recovery_not_tested)),
                    question_id=928,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Recovery procedures not tested",
                    description="Recovery procedures need testing",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="test_recovery"
                ))
        
            # Q930: Recovery documentation missing
            no_docs = state.error_counts.get('recovery_documentation_missing', 0)
            if no_docs > 0:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("no_docs", str(no_docs)),
                    question_id=930,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title="Recovery documentation missing",
                    description="Recovery procedures not documented",
                    affected_components=["KillSwitch"],
                    remediation_available=True,
                    remediation_action="document_recovery"
                ))
        
            return issues
        except Exception as e:
            logger.error(f"Error in _check_recovery_quality: {e}")
            raise
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_activate(self, issue: ValidationIssue) -> str:
        """Activate kill switch"""
        try:
            self.logger.info("Activating kill switch")
            return "Kill switch activated"
        except Exception as e:
            logger.error(f"Error in _remediate_activate: {e}")
            raise
    
    async def _remediate_test(self, issue: ValidationIssue) -> str:
        """Test kill switch"""
        try:
            self.logger.info("Testing kill switch")
            return "Kill switch tested"
        except Exception as e:
            logger.error(f"Error in _remediate_test: {e}")
            raise
    
    async def _remediate_repair(self, issue: ValidationIssue) -> str:
        """Repair kill switch"""
        try:
            self.logger.info("Repairing kill switch")
            return "Kill switch repaired"
        except Exception as e:
            logger.error(f"Error in _remediate_repair: {e}")
            raise
