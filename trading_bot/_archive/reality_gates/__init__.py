"""
Reality Gates - Preventing AI Stupidity in Live Trading

This module implements hard gates that prevent the bot from making
decisions based on unrealistic assumptions, bad data, or overfitted models.

GATES:
1. Data Integrity Gate - Validates all incoming data
2. Walk-Forward Validation Gate - Ensures proper out-of-sample testing
3. Execution Realism Gate - Accounts for real-world execution
4. Multiple-Testing Correction Gate - Prevents p-hacking and overfitting
5. Drift Detection Gate - Detects regime changes and concept drift
6. Kill-Switch Gate - Emergency stops based on anomalies

PHILOSOPHY:
"In backtest, we are geniuses. In live trading, we are humble."

Author: AlphaAlgo Reality Check System
"""

from .data_integrity_gate import (
    DataIntegrityGate,
    DataQualityScore,
    DataAnomaly,
)

from .walk_forward_gate import (
    WalkForwardGate,
    ValidationResult,
    WalkForwardConfig,
)

from .execution_realism_gate import (
    ExecutionRealismGate,
    ExecutionAssumptions,
    RealismAdjustment,
)

from .multiple_testing_gate import (
    MultipleTestingGate,
    TestingCorrection,
    OverfitScore,
)

from .drift_detection_gate import (
    DriftDetectionGate,
    DriftType,
    DriftAlert,
)

from .kill_switch_gate import (
    KillSwitchGate,
    KillReason,
    KillSwitchStatus,
)

from .master_reality_gate import (
    MasterRealityGate,
    RealityCheckResult,
    create_reality_gate,
)

__all__ = [
    # Data Integrity
    'DataIntegrityGate',
    'DataQualityScore',
    'DataAnomaly',
    # Walk-Forward
    'WalkForwardGate',
    'ValidationResult',
    'WalkForwardConfig',
    # Execution Realism
    'ExecutionRealismGate',
    'ExecutionAssumptions',
    'RealismAdjustment',
    # Multiple Testing
    'MultipleTestingGate',
    'TestingCorrection',
    'OverfitScore',
    # Drift Detection
    'DriftDetectionGate',
    'DriftType',
    'DriftAlert',
    # Kill Switch
    'KillSwitchGate',
    'KillReason',
    'KillSwitchStatus',
    # Master Gate
    'MasterRealityGate',
    'RealityCheckResult',
    'create_reality_gate',
]
