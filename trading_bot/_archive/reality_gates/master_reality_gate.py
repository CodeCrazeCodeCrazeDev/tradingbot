"""
Master Reality Gate - The Ultimate Guardian Against AI Stupidity

This is the master orchestrator that combines ALL reality gates into
a single, unified defense system against trading delusions.

PHILOSOPHY:
"AI is a genius in backtest, an idiot in live trading.
This gate ensures the idiot never gets to trade."

GATES ORCHESTRATED:
1. Data Integrity Gate - No bad data
2. Walk-Forward Gate - No unvalidated strategies
3. Execution Realism Gate - No fantasy execution
4. Multiple Testing Gate - No p-hacking
5. Drift Detection Gate - No stale models
6. Kill Switch Gate - No catastrophic losses

RULE: "ALL gates must pass. One failure = No trade."

Author: AlphaAlgo Reality Check System
"""

import logging
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

from .data_integrity_gate import DataIntegrityGate, DataQualityScore
from .walk_forward_gate import WalkForwardGate, ValidationResult, WalkForwardConfig
from .execution_realism_gate import ExecutionRealismGate, ExecutionAssumptions, RealismAdjustment
from .multiple_testing_gate import MultipleTestingGate, TestingCorrection, OverfitScore
from .drift_detection_gate import DriftDetectionGate, DriftStatus, DriftAlert
from .kill_switch_gate import KillSwitchGate, KillSwitchConfig, KillSwitchStatus, KillReason

logger = logging.getLogger(__name__)


class GateStatus(Enum):
    """Status of individual gates"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class GateResult:
    """Result from a single gate"""
    gate_name: str
    status: GateStatus
    confidence_multiplier: float  # 0-1, how much to trust the signal
    position_size_multiplier: float  # 0-1, how much to reduce size
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RealityCheckResult:
    """Complete result from all reality gates"""
    # Overall decision
    is_approved: bool
    should_trade: bool
    
    # Multipliers (apply to signal)
    final_confidence_multiplier: float
    final_position_size_multiplier: float
    
    # Individual gate results
    gate_results: List[GateResult]
    
    # Blocking reasons (if any)
    blocking_gates: List[str]
    blocking_reasons: List[str]
    
    # Warnings (non-blocking)
    warnings: List[str]
    
    # Timing
    checked_at: datetime = field(default_factory=datetime.utcnow)
    check_duration_ms: float = 0.0
    
    def __str__(self):
        status = "APPROVED" if self.is_approved else "BLOCKED"
        return (
            f"RealityCheck: {status} | "
            f"Confidence: {self.final_confidence_multiplier:.2f} | "
            f"Size: {self.final_position_size_multiplier:.2f} | "
            f"Blockers: {len(self.blocking_gates)} | "
            f"Warnings: {len(self.warnings)}"
        )


class MasterRealityGate:
    """
    MASTER GATE: Orchestrates All Reality Checks
    
    This is the single entry point for all reality validation.
    Every trading decision MUST pass through this gate.
    
    Process:
    1. Check kill switch (immediate halt if triggered)
    2. Validate data integrity
    3. Check strategy validation status
    4. Apply execution realism adjustments
    5. Check for drift
    6. Verify multiple testing corrections
    7. Aggregate all results
    8. Return final decision
    
    ALL gates must pass for trading to be allowed.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize all gates
        self.data_gate = DataIntegrityGate(self.config.get('data_integrity', {}))
        self.walk_forward_gate = WalkForwardGate(
            WalkForwardConfig(**self.config.get('walk_forward', {}))
        )
        self.execution_gate = ExecutionRealismGate(
            ExecutionAssumptions(**self.config.get('execution', {}))
        )
        self.testing_gate = MultipleTestingGate(self.config.get('multiple_testing', {}))
        self.drift_gate = DriftDetectionGate(self.config.get('drift_detection', {}))
        self.kill_switch = KillSwitchGate(
            KillSwitchConfig(**self.config.get('kill_switch', {}))
        )
        
        # Statistics
        self.total_checks = 0
        self.total_approved = 0
        self.total_blocked = 0
        
        logger.info("=" * 60)
        logger.info("MASTER REALITY GATE INITIALIZED")
        logger.info("ALL TRADING DECISIONS MUST PASS THROUGH THIS GATE")
        logger.info("=" * 60)
    
    def check(
        self,
        # Market data
        market_data: Dict[str, Any],
        
        # Strategy info
        strategy_id: str,
        
        # Trade details
        symbol: str,
        side: str,
        size: float,
        price: float,
        expected_return: float,
        
        # Context
        current_equity: float,
        current_volatility: float,
        avg_daily_volume: float,
        spread: float,
        
        # Optional
        features: Optional[Dict[str, float]] = None,
        prediction: Optional[float] = None,
        actual: Optional[float] = None,
        trade_result: Optional[Dict] = None,
        correlations: Optional[Dict[str, float]] = None,
        current_regime: Optional[str] = None,
    ) -> RealityCheckResult:
        """
        Run ALL reality checks on a trading decision.
        
        This is the main entry point. Every trade must pass through here.
        
        Returns:
            RealityCheckResult with approval status and adjustments
        """
        start_time = datetime.utcnow()
        self.total_checks += 1
        
        gate_results = []
        blocking_gates = []
        blocking_reasons = []
        warnings = []
        
        confidence_multipliers = []
        size_multipliers = []
        
        # ============================================================
        # GATE 1: KILL SWITCH (Highest Priority)
        # ============================================================
        is_trading_allowed, kill_reasons = self.kill_switch.check(
            current_equity=current_equity,
            current_return=market_data.get('return'),
            current_volatility=current_volatility,
            trade_result=trade_result,
            market_data=market_data
        )
        
        if not is_trading_allowed:
            gate_results.append(GateResult(
                gate_name="Kill Switch",
                status=GateStatus.FAILED,
                confidence_multiplier=0.0,
                position_size_multiplier=0.0,
                message=f"Kill switch triggered: {[r.value for r in kill_reasons]}",
                details={'reasons': [r.value for r in kill_reasons]}
            ))
            blocking_gates.append("Kill Switch")
            blocking_reasons.extend([r.value for r in kill_reasons])
            
            # Kill switch = immediate rejection
            return self._create_blocked_result(
                gate_results, blocking_gates, blocking_reasons, warnings, start_time
            )
        else:
            gate_results.append(GateResult(
                gate_name="Kill Switch",
                status=GateStatus.PASSED,
                confidence_multiplier=1.0,
                position_size_multiplier=1.0,
                message="Kill switch armed and clear"
            ))
        
        # ============================================================
        # GATE 2: DATA INTEGRITY
        # ============================================================
        data_quality = self.data_gate.validate(market_data, data_type='ohlcv')
        
        if not data_quality.is_usable:
            gate_results.append(GateResult(
                gate_name="Data Integrity",
                status=GateStatus.FAILED,
                confidence_multiplier=0.0,
                position_size_multiplier=0.0,
                message=f"Data quality insufficient: {data_quality.score:.2f}",
                details={'anomalies': [str(a) for a in data_quality.anomalies[:5]]}
            ))
            blocking_gates.append("Data Integrity")
            blocking_reasons.append(f"Data quality score {data_quality.score:.2f} < 0.5")
        else:
            gate_results.append(GateResult(
                gate_name="Data Integrity",
                status=GateStatus.PASSED if data_quality.score > 0.8 else GateStatus.WARNING,
                confidence_multiplier=data_quality.confidence_multiplier,
                position_size_multiplier=data_quality.score,
                message=f"Data quality: {data_quality.score:.2f}"
            ))
            confidence_multipliers.append(data_quality.confidence_multiplier)
            size_multipliers.append(data_quality.score)
            
            if data_quality.anomalies:
                warnings.extend([str(a) for a in data_quality.anomalies[:3]])
        
        # ============================================================
        # GATE 3: WALK-FORWARD VALIDATION
        # ============================================================
        is_validated, validation_msg = self.walk_forward_gate.is_strategy_approved(strategy_id)
        
        if not is_validated:
            gate_results.append(GateResult(
                gate_name="Walk-Forward Validation",
                status=GateStatus.FAILED,
                confidence_multiplier=0.0,
                position_size_multiplier=0.0,
                message=validation_msg
            ))
            blocking_gates.append("Walk-Forward Validation")
            blocking_reasons.append(validation_msg)
        else:
            validation = self.walk_forward_gate.validation_cache.get(strategy_id)
            conf_mult = validation.confidence_multiplier if validation else 0.8
            
            gate_results.append(GateResult(
                gate_name="Walk-Forward Validation",
                status=GateStatus.PASSED,
                confidence_multiplier=conf_mult,
                position_size_multiplier=1.0,
                message=f"Strategy validated: OOS Sharpe={validation.avg_oos_sharpe:.2f}" if validation else "Validated"
            ))
            confidence_multipliers.append(conf_mult)
        
        # ============================================================
        # GATE 4: EXECUTION REALISM
        # ============================================================
        execution_result = self.execution_gate.analyze_trade(
            symbol=symbol,
            side=side,
            size=size,
            price=price,
            expected_return=expected_return,
            volatility=current_volatility,
            spread=spread,
            avg_daily_volume=avg_daily_volume
        )
        
        if not execution_result.is_viable:
            gate_results.append(GateResult(
                gate_name="Execution Realism",
                status=GateStatus.FAILED,
                confidence_multiplier=0.0,
                position_size_multiplier=0.0,
                message=f"Not viable after costs: {execution_result.adjusted_return:.2f}%",
                details={
                    'original_return': expected_return,
                    'adjusted_return': execution_result.adjusted_return,
                    'total_cost': execution_result.total_cost
                }
            ))
            blocking_gates.append("Execution Realism")
            blocking_reasons.append(f"Expected return {expected_return:.2f}% -> {execution_result.adjusted_return:.2f}% after costs")
        else:
            # Adjust expected return for costs
            return_ratio = execution_result.adjusted_return / expected_return if expected_return > 0 else 1.0
            
            gate_results.append(GateResult(
                gate_name="Execution Realism",
                status=GateStatus.PASSED if return_ratio > 0.7 else GateStatus.WARNING,
                confidence_multiplier=min(1.0, return_ratio),
                position_size_multiplier=1.0,
                message=f"Adjusted return: {execution_result.adjusted_return:.2f}% (cost: {execution_result.total_cost*100:.2f}%)"
            ))
            confidence_multipliers.append(min(1.0, return_ratio))
            
            if execution_result.warnings:
                warnings.extend(execution_result.warnings)
        
        # ============================================================
        # GATE 5: DRIFT DETECTION
        # ============================================================
        drift_status = self.drift_gate.check_drift(
            features=features or {},
            prediction=prediction,
            actual=actual,
            current_return=market_data.get('return'),
            current_volatility=current_volatility,
            current_regime=current_regime,
            correlations=correlations
        )
        
        if drift_status.should_halt_trading:
            gate_results.append(GateResult(
                gate_name="Drift Detection",
                status=GateStatus.FAILED,
                confidence_multiplier=0.0,
                position_size_multiplier=0.0,
                message=f"Severe drift detected: {len(drift_status.active_alerts)} alerts",
                details={'alerts': [str(a) for a in drift_status.active_alerts]}
            ))
            blocking_gates.append("Drift Detection")
            blocking_reasons.extend([str(a) for a in drift_status.active_alerts])
        else:
            gate_results.append(GateResult(
                gate_name="Drift Detection",
                status=GateStatus.PASSED if drift_status.is_stable else GateStatus.WARNING,
                confidence_multiplier=1.0 - drift_status.overall_drift_score,
                position_size_multiplier=drift_status.position_size_multiplier,
                message=f"Drift score: {drift_status.overall_drift_score:.2f}"
            ))
            confidence_multipliers.append(1.0 - drift_status.overall_drift_score)
            size_multipliers.append(drift_status.position_size_multiplier)
            
            if drift_status.active_alerts:
                warnings.extend([str(a) for a in drift_status.active_alerts])
        
        # ============================================================
        # GATE 6: MULTIPLE TESTING (if strategy was tested)
        # ============================================================
        if strategy_id in self.testing_gate.test_registry:
            # Get correction if available
            test_info = self.testing_gate.test_registry[strategy_id]
            
            # Check overfit score
            validation = self.walk_forward_gate.validation_cache.get(strategy_id)
            if validation:
                overfit = self.testing_gate.calculate_overfit_score(
                    strategy_id=strategy_id,
                    model_complexity=test_info.get('num_parameters', 5),
                    in_sample_sharpe=validation.avg_oos_sharpe * 1.5,  # Estimate
                    out_of_sample_sharpe=validation.avg_oos_sharpe
                )
                
                if not overfit.is_acceptable:
                    gate_results.append(GateResult(
                        gate_name="Multiple Testing",
                        status=GateStatus.FAILED,
                        confidence_multiplier=0.0,
                        position_size_multiplier=0.0,
                        message=f"High overfit risk: {overfit.score:.2f}",
                        details={'recommendations': overfit.recommendations}
                    ))
                    blocking_gates.append("Multiple Testing")
                    blocking_reasons.append(f"Overfit score {overfit.score:.2f} too high")
                else:
                    gate_results.append(GateResult(
                        gate_name="Multiple Testing",
                        status=GateStatus.PASSED if overfit.score < 0.3 else GateStatus.WARNING,
                        confidence_multiplier=1.0 - overfit.score,
                        position_size_multiplier=1.0,
                        message=f"Overfit score: {overfit.score:.2f}"
                    ))
                    confidence_multipliers.append(1.0 - overfit.score)
        else:
            gate_results.append(GateResult(
                gate_name="Multiple Testing",
                status=GateStatus.SKIPPED,
                confidence_multiplier=0.8,  # Penalty for not being registered
                position_size_multiplier=1.0,
                message="Strategy not registered for testing correction"
            ))
            confidence_multipliers.append(0.8)
            warnings.append("Strategy not registered for multiple testing correction")
        
        # ============================================================
        # AGGREGATE RESULTS
        # ============================================================
        
        # If any blocking gates, reject
        if blocking_gates:
            return self._create_blocked_result(
                gate_results, blocking_gates, blocking_reasons, warnings, start_time
            )
        
        # Calculate final multipliers
        final_confidence = 1.0
        for mult in confidence_multipliers:
            final_confidence *= mult
        
        final_size = 1.0
        for mult in size_multipliers:
            final_size *= mult
        
        # Ensure minimums
        final_confidence = max(0.1, final_confidence)
        final_size = max(0.1, final_size)
        
        self.total_approved += 1
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        result = RealityCheckResult(
            is_approved=True,
            should_trade=True,
            final_confidence_multiplier=final_confidence,
            final_position_size_multiplier=final_size,
            gate_results=gate_results,
            blocking_gates=[],
            blocking_reasons=[],
            warnings=warnings,
            check_duration_ms=duration_ms
        )
        
        logger.info(f"REALITY CHECK PASSED: {result}")
        
        return result
    
    def _create_blocked_result(
        self,
        gate_results: List[GateResult],
        blocking_gates: List[str],
        blocking_reasons: List[str],
        warnings: List[str],
        start_time: datetime
    ) -> RealityCheckResult:
        """Create a blocked result"""
        self.total_blocked += 1
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        result = RealityCheckResult(
            is_approved=False,
            should_trade=False,
            final_confidence_multiplier=0.0,
            final_position_size_multiplier=0.0,
            gate_results=gate_results,
            blocking_gates=blocking_gates,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            check_duration_ms=duration_ms
        )
        
        logger.warning(f"REALITY CHECK BLOCKED: {blocking_gates} - {blocking_reasons[:3]}")
        
        return result
    
    def quick_check(
        self,
        market_data: Dict[str, Any],
        current_equity: float,
        current_volatility: float
    ) -> Tuple[bool, str]:
        """
        Quick check for basic trading permission.
        
        Use this for fast checks before detailed analysis.
        """
        # Check kill switch
        is_allowed, reasons = self.kill_switch.check(
            current_equity=current_equity,
            current_volatility=current_volatility
        )
        
        if not is_allowed:
            return False, f"Kill switch: {[r.value for r in reasons]}"
        
        # Check data quality
        data_quality = self.data_gate.validate(market_data)
        if not data_quality.is_usable:
            return False, f"Data quality: {data_quality.score:.2f}"
        
        # Check drift
        drift_status = self.drift_gate.check_drift(
            features={},
            current_volatility=current_volatility
        )
        if drift_status.should_halt_trading:
            return False, f"Drift detected: {len(drift_status.active_alerts)} alerts"
        
        return True, "Quick check passed"
    
    def register_strategy(
        self,
        strategy_id: str,
        num_parameters: int,
        parameter_ranges: Dict[str, Tuple[float, float]],
        data_hash: str,
        walk_forward_results: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Register and validate a strategy.
        
        Call this before using a strategy in live trading.
        """
        # Register for multiple testing
        self.testing_gate.register_test(
            strategy_id=strategy_id,
            num_parameters=num_parameters,
            parameter_ranges=parameter_ranges,
            data_hash=data_hash
        )
        
        # Validate with walk-forward
        validation = self.walk_forward_gate.validate_strategy(
            strategy_id=strategy_id,
            walk_results=walk_forward_results
        )
        
        if validation.is_approved:
            return True, f"Strategy approved: OOS Sharpe={validation.avg_oos_sharpe:.2f}"
        else:
            return False, f"Strategy rejected: {validation.failure_reasons}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all gates"""
        return {
            'master_gate': {
                'total_checks': self.total_checks,
                'total_approved': self.total_approved,
                'total_blocked': self.total_blocked,
                'approval_rate': self.total_approved / max(self.total_checks, 1)
            },
            'data_integrity': self.data_gate.get_statistics(),
            'walk_forward': self.walk_forward_gate.get_statistics(),
            'execution_realism': self.execution_gate.get_statistics(),
            'multiple_testing': self.testing_gate.get_statistics(),
            'drift_detection': self.drift_gate.get_statistics(),
            'kill_switch': self.kill_switch.get_statistics()
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive reality gate report"""
        stats = self.get_statistics()
        
        report = [
            "=" * 60,
            "MASTER REALITY GATE REPORT",
            "=" * 60,
            "",
            "=== Overall Statistics ===",
            f"Total Checks: {stats['master_gate']['total_checks']}",
            f"Approved: {stats['master_gate']['total_approved']}",
            f"Blocked: {stats['master_gate']['total_blocked']}",
            f"Approval Rate: {stats['master_gate']['approval_rate']:.1%}",
            "",
            "=== Gate Statistics ===",
            "",
            f"Data Integrity:",
            f"  - Checks: {stats['data_integrity']['total_checks']}",
            f"  - Block Rate: {stats['data_integrity']['block_rate']:.1%}",
            "",
            f"Walk-Forward Validation:",
            f"  - Strategies Validated: {stats['walk_forward']['strategies_validated']}",
            f"  - Approval Rate: {stats['walk_forward']['approval_rate']:.1%}",
            "",
            f"Execution Realism:",
            f"  - Trades Analyzed: {stats['execution_realism']['trades_analyzed']}",
            f"  - Block Rate: {stats['execution_realism']['block_rate']:.1%}",
            "",
            f"Multiple Testing:",
            f"  - Tests Performed: {stats['multiple_testing']['total_tests_performed']}",
            f"  - Block Rate: {stats['multiple_testing']['block_rate']:.1%}",
            "",
            f"Drift Detection:",
            f"  - Checks: {stats['drift_detection']['checks_performed']}",
            f"  - Drift Rate: {stats['drift_detection']['drift_rate']:.1%}",
            "",
            f"Kill Switch:",
            f"  - Status: {stats['kill_switch']['current_status']}",
            f"  - Total Triggers: {stats['kill_switch']['total_triggers']}",
            "",
            "=" * 60,
        ]
        
        return "\n".join(report)


def create_reality_gate(config: Optional[Dict] = None) -> MasterRealityGate:
    """Factory function to create the master reality gate"""
    return MasterRealityGate(config)
