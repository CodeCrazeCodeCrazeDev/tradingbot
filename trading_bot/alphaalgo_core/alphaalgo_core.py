"""
AlphaAlgo Core - Main Integration Module

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYSTEM CONSTITUTION — IMMUTABLE LAWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Capital protection supersedes all learning objectives.
2. No component may modify its own execution boundary.
3. Every structural change must pass 5 validation gates before promotion.

These laws cannot be overridden by performance gains, regime changes,
or meta-agent instructions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIVE IMMUTABLE ZONES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ZONE A: EXECUTION ENGINE (FROZEN — READ-ONLY AT RUNTIME)
ZONE B: BOUNDED ADAPTATION LAYER (ONLINE — TIGHTLY CONSTRAINED)
ZONE C: STRATEGY POOL (ISOLATED CONTAINERS — NO CROSS-CONTAMINATION)
ZONE D: EVOLUTION ENGINE (FULLY OFFLINE — AIR-GAPPED FROM PRODUCTION)
ZONE E: META-AGENT (READ + PROPOSE ONLY — CANNOT EXECUTE)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import hashlib
import json
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import copy

import numpy as np
import pandas as pd

from .capital_governance import (
    CapitalGovernanceSystem,
    CapitalGovernanceResult,
    MarketPhysicsResult,
    StrategyZooResult,
    AssumptionDecompilerResult,
    RegimeHostilityResult,
    ExposureControllerResult,
    AntiLearningResult,
    ValidationMonitorResult
)

from .market_physics_filter import MarketPhysicsFilter
from .strategy_zoo import StrategyZoo
from .assumption_decompiler import AssumptionDecompiler
from .regime_hostility_engine import RegimeHostilityEngine
from .exposure_controller import ExposureController
from .anti_learning_firewall import AntiLearningFirewall
from .continuous_validity_monitor import ContinuousValidityMonitor

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM CONSTITUTION ENUMS AND CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class IsolationZone(Enum):
    """The five immutable isolation zones"""
    ZONE_A_EXECUTION = "execution_engine"      # FROZEN — READ-ONLY AT RUNTIME
    ZONE_B_ADAPTATION = "adaptation_layer"     # ONLINE — TIGHTLY CONSTRAINED
    ZONE_C_STRATEGY = "strategy_pool"          # ISOLATED CONTAINERS
    ZONE_D_EVOLUTION = "evolution_engine"      # FULLY OFFLINE — AIR-GAPPED
    ZONE_E_META_AGENT = "meta_agent"           # READ + PROPOSE ONLY


class RegimeLabel(Enum):
    """Market regime classification labels"""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    CRISIS = "crisis"
    UNCERTAIN = "uncertain"


class FreezeReason(Enum):
    """Reasons for learning freeze"""
    DRAWDOWN_SPIKE = "drawdown_spike"
    REGIME_UNCERTAINTY = "regime_uncertainty"
    EXECUTION_ALPHA_DEGRADATION = "execution_alpha_degradation"
    PARAMETER_DRIFT_CEILING = "parameter_drift_ceiling"
    DATA_QUALITY_FAILURE = "data_quality_failure"
    LATENCY_SPIKE = "latency_spike"


class ReversionLevel(Enum):
    """Reversion severity levels"""
    SOFT_REVERT = 1      # Revert Zone B parameters
    STRATEGY_REVERT = 2  # Disable underperforming strategies
    FULL_SYSTEM_REVERT = 3  # Full parameter revert, halt learning


class StrategyLifecycle(Enum):
    """Strategy lifecycle states"""
    PROBATION = "probation"
    ACTIVE = "active"
    DEGRADED = "degraded"
    RETIRED = "retired"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMMUTABLE SYSTEM CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONSTITUTION_CONSTANTS = {
    # Bounded Adaptation Limits (Zone B)
    "MAX_DELTA_PER_UPDATE": 0.005,        # 0.5% per update cycle
    "MAX_CUMULATIVE_DRIFT": 0.05,         # 5% before mandatory re-anchoring
    "PARAMETER_SNAPSHOT_DEPTH": 50,       # Versioned snapshot stack depth
    
    # Learning Freeze Thresholds
    "DRAWDOWN_FREEZE_RATIO": 0.6,         # Freeze at 60% of max allowed drawdown
    "REGIME_CONFIDENCE_FREEZE": 0.55,     # Freeze below 55% confidence
    "REGIME_CONFIDENCE_UNFREEZE": 0.70,   # Unfreeze above 70% confidence
    "EXECUTION_ALPHA_DEGRADATION": 0.70,  # 7d < 30d * 0.70 triggers freeze
    "DATA_QUALITY_FAILURE_RATE": 0.02,    # 2% tick validation failure
    "LATENCY_SLA_MULTIPLIER": 1.5,        # p99 > SLA * 1.5 triggers freeze
    
    # Unfreeze Requirements
    "MIN_OBSERVATION_WINDOW": 500,        # Minimum bars post-resolution
    "SHADOW_AGREEMENT_THRESHOLD": 0.80,   # Shadow model agreement rate
    
    # Shadow Model Thresholds
    "SHADOW_PROMOTION_SHARPE_RATIO": 1.05,  # Shadow > Production * 1.05
    "SHADOW_PROMOTION_MIN_BARS": 200,       # Sustained for 200 bars
    "SHADOW_DIVERGENCE_ALERT": 0.15,        # 15% signal divergence
    
    # Strategy Pool Rules
    "MIN_ACTIVE_STRATEGIES": 3,
    "MAX_STRATEGY_CORRELATION": 0.70,
    "MIN_STRATEGY_SHARPE": 0.3,
    "MIN_STRATEGY_AGE_BARS": 200,
    
    # Evolution Gates
    "GATE_MIN_OOS_OBSERVATIONS": 1000,
    "GATE_P_VALUE_THRESHOLD": 0.01,
    "GATE_MAX_REGIME_ALPHA_SHARE": 0.60,
    "GATE_NOISE_INJECTION_PCT": 0.02,
    "GATE_MAX_CORRELATION_WITH_POOL": 0.65,
    "GATE_MAX_KILL_SWITCH_RATE": 0.005,
    
    # Reversion Thresholds
    "SOFT_REVERT_DEGRADATION": 0.10,      # 10% vs 30d baseline
    "SOFT_REVERT_DAYS": 3,
    "STRATEGY_REVERT_SHARPE_DROP": 0.20,  # 20% Sharpe drop
    "STRATEGY_REVERT_WINDOW_DAYS": 5,
    
    # Data Integrity
    "MAX_SPREAD_MULTIPLIER": 5.0,
    "MAX_FEATURE_ZSCORE": 4.0,
    "MAX_FORWARD_FILL_TICKS": 3,
    
    # Snapshot Configuration
    "SNAPSHOT_FREQUENCY_HOURS": 6,
    "SNAPSHOT_RETENTION_DAYS": 30,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ZONE BOUNDARY HASH VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ZoneBoundaryState:
    """Tracks the integrity state of each zone boundary"""
    zone: IsolationZone
    hash_value: str
    timestamp: float
    is_valid: bool = True
    
    
class ZoneBoundaryValidator:
    """Validates zone boundary integrity via hash checking"""
    
    def __init__(self):
        self._zone_hashes: Dict[IsolationZone, str] = {}
        self._lock = threading.Lock()
        
    def register_zone_state(self, zone: IsolationZone, state_data: Any) -> str:
        """Register initial zone state and compute hash"""
        state_json = json.dumps(state_data, sort_keys=True, default=str)
        hash_value = hashlib.sha256(state_json.encode()).hexdigest()
        with self._lock:
            self._zone_hashes[zone] = hash_value
        return hash_value
    
    def validate_zone_integrity(self, zone: IsolationZone, current_state: Any) -> bool:
        """Validate that zone state hasn't been tampered with"""
        current_json = json.dumps(current_state, sort_keys=True, default=str)
        current_hash = hashlib.sha256(current_json.encode()).hexdigest()
        with self._lock:
            expected_hash = self._zone_hashes.get(zone)
        if expected_hash is None:
            return True  # Not yet registered
        return current_hash == expected_hash
    
    def update_zone_hash(self, zone: IsolationZone, new_state: Any) -> str:
        """Update zone hash after authorized modification"""
        state_json = json.dumps(new_state, sort_keys=True, default=str)
        hash_value = hashlib.sha256(state_json.encode()).hexdigest()
        with self._lock:
            self._zone_hashes[zone] = hash_value
        return hash_value


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PARAMETER SNAPSHOT SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ParameterSnapshot:
    """Versioned parameter snapshot"""
    version: int
    timestamp: float
    parameters: Dict[str, Any]
    hash_value: str
    trigger_condition: str
    
    
class ParameterSnapshotStack:
    """Maintains versioned parameter snapshots with rollback capability"""
    
    def __init__(self, max_depth: int = 50):
        self.max_depth = max_depth
        self._snapshots: deque = deque(maxlen=max_depth)
        self._version_counter = 0
        self._lock = threading.Lock()
        
    def push(self, parameters: Dict[str, Any], trigger: str) -> ParameterSnapshot:
        """Push a new snapshot onto the stack"""
        with self._lock:
            self._version_counter += 1
            params_json = json.dumps(parameters, sort_keys=True, default=str)
            hash_value = hashlib.sha256(params_json.encode()).hexdigest()
            snapshot = ParameterSnapshot(
                version=self._version_counter,
                timestamp=time.time(),
                parameters=copy.deepcopy(parameters),
                hash_value=hash_value,
                trigger_condition=trigger
            )
            self._snapshots.append(snapshot)
            return snapshot
    
    def get_latest(self) -> Optional[ParameterSnapshot]:
        """Get the most recent snapshot"""
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None
    
    def get_by_version(self, version: int) -> Optional[ParameterSnapshot]:
        """Get snapshot by version number"""
        with self._lock:
            for snapshot in self._snapshots:
                if snapshot.version == version:
                    return snapshot
            return None
    
    def rollback_to(self, version: int) -> Optional[Dict[str, Any]]:
        """Rollback to a specific version and return parameters"""
        snapshot = self.get_by_version(version)
        if snapshot:
            return copy.deepcopy(snapshot.parameters)
        return None
    
    def get_clean_checkpoint(self, max_age_hours: int = 48) -> Optional[ParameterSnapshot]:
        """Get the last clean checkpoint within age limit"""
        cutoff = time.time() - (max_age_hours * 3600)
        with self._lock:
            for snapshot in reversed(self._snapshots):
                if snapshot.timestamp >= cutoff:
                    return snapshot
            return self._snapshots[-1] if self._snapshots else None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LEARNING FREEZE CONTROLLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class FreezeState:
    """Current learning freeze state"""
    is_frozen: bool = False
    reason: Optional[FreezeReason] = None
    frozen_at: Optional[float] = None
    duration: Optional[str] = None
    trigger_value: Optional[float] = None
    
    
class LearningFreezeController:
    """Controls learning freeze triggers and unfreeze protocol"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.freeze_state = FreezeState()
        self._freeze_history: List[Dict] = []
        self._lock = threading.Lock()
        
        # Thresholds from constitution
        self.max_allowed_drawdown = self.config.get("max_allowed_drawdown", 0.15)
        self.sla_latency = self.config.get("sla_latency_ms", 100)
        
    def check_freeze_triggers(
        self,
        current_drawdown: float,
        regime_confidence: float,
        execution_alpha_7d: float,
        execution_alpha_30d: float,
        cumulative_drift: float,
        tick_validation_failure_rate: float,
        p99_latency: float
    ) -> Optional[FreezeReason]:
        """Check all freeze triggers and return reason if triggered"""
        
        # FREEZE TRIGGER 1 — DRAWDOWN SPIKE
        if current_drawdown > self.max_allowed_drawdown * CONSTITUTION_CONSTANTS["DRAWDOWN_FREEZE_RATIO"]:
            return FreezeReason.DRAWDOWN_SPIKE
        
        # FREEZE TRIGGER 2 — REGIME UNCERTAINTY
        if regime_confidence < CONSTITUTION_CONSTANTS["REGIME_CONFIDENCE_FREEZE"]:
            return FreezeReason.REGIME_UNCERTAINTY
        
        # FREEZE TRIGGER 3 — EXECUTION ALPHA DEGRADATION
        if execution_alpha_30d > 0:
            if execution_alpha_7d < execution_alpha_30d * CONSTITUTION_CONSTANTS["EXECUTION_ALPHA_DEGRADATION"]:
                return FreezeReason.EXECUTION_ALPHA_DEGRADATION
        
        # FREEZE TRIGGER 4 — PARAMETER DRIFT CEILING HIT
        if cumulative_drift >= CONSTITUTION_CONSTANTS["MAX_CUMULATIVE_DRIFT"]:
            return FreezeReason.PARAMETER_DRIFT_CEILING
        
        # FREEZE TRIGGER 5 — DATA QUALITY FAILURE
        if tick_validation_failure_rate > CONSTITUTION_CONSTANTS["DATA_QUALITY_FAILURE_RATE"]:
            return FreezeReason.DATA_QUALITY_FAILURE
        
        # FREEZE TRIGGER 6 — LATENCY SPIKE
        if p99_latency > self.sla_latency * CONSTITUTION_CONSTANTS["LATENCY_SLA_MULTIPLIER"]:
            return FreezeReason.LATENCY_SPIKE
        
        return None
    
    def activate_freeze(self, reason: FreezeReason, trigger_value: float = None):
        """Activate learning freeze"""
        with self._lock:
            self.freeze_state = FreezeState(
                is_frozen=True,
                reason=reason,
                frozen_at=time.time(),
                duration=self._get_freeze_duration(reason),
                trigger_value=trigger_value
            )
            self._freeze_history.append({
                "reason": reason.value,
                "frozen_at": self.freeze_state.frozen_at,
                "trigger_value": trigger_value
            })
            logger.critical(f"LEARNING FREEZE ACTIVATED: {reason.value}")
    
    def _get_freeze_duration(self, reason: FreezeReason) -> str:
        """Get freeze duration based on reason"""
        durations = {
            FreezeReason.DRAWDOWN_SPIKE: "until_recovery_confirmation",
            FreezeReason.REGIME_UNCERTAINTY: "until_confidence > 0.70",
            FreezeReason.EXECUTION_ALPHA_DEGRADATION: "48h minimum",
            FreezeReason.PARAMETER_DRIFT_CEILING: "until_re-anchoring_complete",
            FreezeReason.DATA_QUALITY_FAILURE: "immediate_until_resolved",
            FreezeReason.LATENCY_SPIKE: "until_latency_normalized",
        }
        return durations.get(reason, "indefinite")
    
    def check_unfreeze_conditions(
        self,
        trigger_resolved: bool,
        bars_since_resolution: int,
        shadow_agreement_rate: float
    ) -> bool:
        """Check if unfreeze conditions are met"""
        if not self.freeze_state.is_frozen:
            return True
            
        # All conditions must be met
        if not trigger_resolved:
            return False
        if bars_since_resolution < CONSTITUTION_CONSTANTS["MIN_OBSERVATION_WINDOW"]:
            return False
        if shadow_agreement_rate < CONSTITUTION_CONSTANTS["SHADOW_AGREEMENT_THRESHOLD"]:
            return False
            
        return True
    
    def deactivate_freeze(self):
        """Deactivate learning freeze"""
        with self._lock:
            if self.freeze_state.is_frozen:
                logger.info(f"LEARNING FREEZE DEACTIVATED after {self.freeze_state.reason.value}")
                self.freeze_state = FreezeState()
    
    @property
    def is_frozen(self) -> bool:
        return self.freeze_state.is_frozen


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXECUTION ALPHA MONITOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ExecutionMetrics:
    """Execution alpha metrics"""
    execution_alpha_7d: float = 0.0
    execution_alpha_30d: float = 0.0
    slippage_ewma_fast: float = 0.0
    slippage_ewma_slow: float = 0.0
    slippage_drift: float = 0.0
    historical_slippage_std: float = 0.0
    latency_impact: float = 0.0
    fill_probability: float = 1.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    

class ExecutionAlphaMonitor:
    """Monitors execution quality and alpha degradation"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.metrics = ExecutionMetrics()
        self._fill_slippages: deque = deque(maxlen=10000)
        self._latencies: deque = deque(maxlen=10000)
        self._fill_count = 0
        self._lock = threading.Lock()
        
    def record_fill(
        self,
        expected_price: float,
        actual_price: float,
        position_direction: int,  # 1 for long, -1 for short
        latency_ms: float
    ):
        """Record a fill for execution alpha calculation"""
        with self._lock:
            slippage = actual_price - expected_price
            self._fill_slippages.append({
                "slippage": slippage,
                "direction": position_direction,
                "timestamp": time.time()
            })
            self._latencies.append(latency_ms)
            self._fill_count += 1
            
            # Update metrics every 500 fills
            if self._fill_count % 500 == 0:
                self._update_metrics()
    
    def _update_metrics(self):
        """Update execution alpha metrics (Loop 6)"""
        if len(self._fill_slippages) < 20:
            return
            
        slippages = [f["slippage"] for f in self._fill_slippages]
        directions = [f["direction"] for f in self._fill_slippages]
        timestamps = [f["timestamp"] for f in self._fill_slippages]
        
        # Calculate execution alpha
        weighted_slippages = [s * d for s, d in zip(slippages, directions)]
        
        # 7-day and 30-day windows
        now = time.time()
        day_7_cutoff = now - (7 * 24 * 3600)
        day_30_cutoff = now - (30 * 24 * 3600)
        
        slippages_7d = [ws for ws, ts in zip(weighted_slippages, timestamps) if ts >= day_7_cutoff]
        slippages_30d = [ws for ws, ts in zip(weighted_slippages, timestamps) if ts >= day_30_cutoff]
        
        self.metrics.execution_alpha_7d = np.mean(slippages_7d) if slippages_7d else 0.0
        self.metrics.execution_alpha_30d = np.mean(slippages_30d) if slippages_30d else 0.0
        
        # EWMA slippage
        slippage_array = np.array(slippages)
        self.metrics.slippage_ewma_fast = self._ewma(slippage_array, span=20)
        self.metrics.slippage_ewma_slow = self._ewma(slippage_array, span=100)
        self.metrics.slippage_drift = self.metrics.slippage_ewma_fast - self.metrics.slippage_ewma_slow
        self.metrics.historical_slippage_std = np.std(slippages)
        
        # Latency percentiles
        latencies = list(self._latencies)
        if latencies:
            self.metrics.p50_latency = np.percentile(latencies, 50)
            self.metrics.p95_latency = np.percentile(latencies, 95)
            self.metrics.p99_latency = np.percentile(latencies, 99)
            
            # Latency impact correlation
            if len(slippages) == len(latencies):
                self.metrics.latency_impact = np.corrcoef(latencies[-len(slippages):], slippages)[0, 1]
    
    def _ewma(self, data: np.ndarray, span: int) -> float:
        """Calculate exponentially weighted moving average"""
        if len(data) == 0:
            return 0.0
        alpha = 2 / (span + 1)
        weights = (1 - alpha) ** np.arange(len(data))[::-1]
        return np.sum(weights * data) / np.sum(weights)
    
    def check_alerts(self) -> List[str]:
        """Check for execution alpha alerts"""
        alerts = []
        
        # Slippage drift alert
        if self.metrics.historical_slippage_std > 0:
            drift_ratio = abs(self.metrics.slippage_drift) / self.metrics.historical_slippage_std
            if drift_ratio > 1.5:
                alerts.append(f"ALERT: Slippage drift {drift_ratio:.2f}σ")
            if drift_ratio > 3.0:
                alerts.append(f"HARD STOP: Slippage drift {drift_ratio:.2f}σ exceeds 3σ limit")
        
        return alerts


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SHADOW MODEL SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ShadowModelMetrics:
    """Shadow model comparison metrics"""
    prediction_confidence_delta: float = 0.0
    signal_agreement_rate: float = 1.0
    expected_pnl_delta: float = 0.0
    feature_importance_drift: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    bars_sustained: int = 0


class ShadowModelSystem:
    """Manages shadow model for A/B comparison"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.shadow_metrics = ShadowModelMetrics()
        self.production_metrics = ShadowModelMetrics()
        self._signal_history: deque = deque(maxlen=100)
        self._promotion_candidate = False
        self._lock = threading.Lock()
        
    def record_signals(
        self,
        shadow_signal: float,
        production_signal: float,
        shadow_confidence: float,
        production_confidence: float
    ):
        """Record signals from both models"""
        with self._lock:
            agreement = 1.0 if np.sign(shadow_signal) == np.sign(production_signal) else 0.0
            self._signal_history.append({
                "shadow": shadow_signal,
                "production": production_signal,
                "agreement": agreement,
                "confidence_delta": shadow_confidence - production_confidence,
                "timestamp": time.time()
            })
            
            # Update rolling metrics
            self._update_comparison_metrics()
    
    def _update_comparison_metrics(self):
        """Update shadow vs production comparison metrics"""
        if len(self._signal_history) < 10:
            return
            
        agreements = [s["agreement"] for s in self._signal_history]
        conf_deltas = [s["confidence_delta"] for s in self._signal_history]
        
        self.shadow_metrics.signal_agreement_rate = np.mean(agreements)
        self.shadow_metrics.prediction_confidence_delta = np.mean(conf_deltas)
    
    def check_promotion_eligibility(self) -> Tuple[bool, str]:
        """Check if shadow model is eligible for promotion"""
        # Promotion trigger conditions
        if self.shadow_metrics.sharpe_ratio <= self.production_metrics.sharpe_ratio * CONSTITUTION_CONSTANTS["SHADOW_PROMOTION_SHARPE_RATIO"]:
            return False, "Shadow Sharpe ratio not sufficiently higher"
        
        if self.shadow_metrics.max_drawdown >= self.production_metrics.max_drawdown:
            return False, "Shadow max drawdown not lower"
        
        if self.shadow_metrics.bars_sustained < CONSTITUTION_CONSTANTS["SHADOW_PROMOTION_MIN_BARS"]:
            return False, f"Need {CONSTITUTION_CONSTANTS['SHADOW_PROMOTION_MIN_BARS']} bars sustained"
        
        # Shadow model is NEVER promoted automatically
        self._promotion_candidate = True
        return True, "Eligible for promotion - requires gate passage + human audit"
    
    def check_divergence_alert(self) -> Optional[str]:
        """Check for shadow divergence alert"""
        if self.shadow_metrics.signal_agreement_rate < (1 - CONSTITUTION_CONSTANTS["SHADOW_DIVERGENCE_ALERT"]):
            return f"Shadow divergence: {1 - self.shadow_metrics.signal_agreement_rate:.1%} > 15%"
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HARD REVERSION SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HardReversionSystem:
    """Manages hard reversion triggers and rollback"""
    
    def __init__(self, snapshot_stack: ParameterSnapshotStack, config: Dict[str, Any] = None):
        self.config = config or {}
        self.snapshot_stack = snapshot_stack
        self._reversion_history: List[Dict] = []
        self._current_reversion_level: Optional[ReversionLevel] = None
        self._lock = threading.Lock()
        
    def check_reversion_triggers(
        self,
        performance_vs_30d_baseline: float,
        days_degraded: int,
        strategy_pool_sharpe_5d: float,
        strategy_pool_sharpe_baseline: float,
        system_drawdown: float,
        kill_switch_threshold: float
    ) -> Optional[ReversionLevel]:
        """Check all reversion triggers"""
        
        # REVERSION LEVEL 1 — SOFT REVERT
        if performance_vs_30d_baseline < -CONSTITUTION_CONSTANTS["SOFT_REVERT_DEGRADATION"]:
            if days_degraded >= CONSTITUTION_CONSTANTS["SOFT_REVERT_DAYS"]:
                return ReversionLevel.SOFT_REVERT
        
        # REVERSION LEVEL 2 — STRATEGY REVERT
        if strategy_pool_sharpe_baseline > 0:
            sharpe_drop = (strategy_pool_sharpe_baseline - strategy_pool_sharpe_5d) / strategy_pool_sharpe_baseline
            if sharpe_drop > CONSTITUTION_CONSTANTS["STRATEGY_REVERT_SHARPE_DROP"]:
                return ReversionLevel.STRATEGY_REVERT
        
        # REVERSION LEVEL 3 — FULL SYSTEM REVERT
        if system_drawdown >= kill_switch_threshold:
            return ReversionLevel.FULL_SYSTEM_REVERT
        
        return None
    
    def execute_reversion(self, level: ReversionLevel) -> Dict[str, Any]:
        """Execute reversion at specified level"""
        with self._lock:
            self._current_reversion_level = level
            result = {"level": level.value, "timestamp": time.time(), "actions": []}
            
            if level == ReversionLevel.SOFT_REVERT:
                # Revert Zone B parameters to last stable checkpoint (T-48h)
                checkpoint = self.snapshot_stack.get_clean_checkpoint(max_age_hours=48)
                if checkpoint:
                    result["actions"].append(f"Reverted to checkpoint v{checkpoint.version}")
                    result["parameters"] = checkpoint.parameters
                result["freeze_duration_hours"] = 72
                
            elif level == ReversionLevel.STRATEGY_REVERT:
                # Disable underperforming strategies, activate baseline fallback
                result["actions"].append("Disabled underperforming strategies")
                result["actions"].append("Activated baseline fallback pool")
                result["shadow_takeover"] = True
                
            elif level == ReversionLevel.FULL_SYSTEM_REVERT:
                # Full parameter revert, halt all learning
                latest = self.snapshot_stack.get_latest()
                if latest:
                    result["actions"].append(f"Full revert to v{latest.version}")
                    result["parameters"] = latest.parameters
                result["actions"].append("ALL learning halted indefinitely")
                result["actions"].append("Capital reduced to minimum hedge position")
                result["manual_review_required"] = True
            
            self._reversion_history.append(result)
            logger.critical(f"REVERSION EXECUTED: Level {level.value}")
            return result
    
    def can_re_advance(self) -> bool:
        """Check if system can re-advance after reversion"""
        # A reversion cannot be "undone" by re-applying the reverted state
        # Post-reversion re-advancement must pass all 5 Verification Gates
        return False  # Always requires full gate passage


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MARKET STATE ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class RegimeClassification:
    """Market regime classification output"""
    label: RegimeLabel
    confidence: float
    stability: float
    transition_probability: float
    ensemble_agreement: float


class MarketStateEngine:
    """Classifies market regime with ensemble voting"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._regime_history: deque = deque(maxlen=50)
        self._ensemble_models = 3  # Fixed architecture
        
    def classify_regime(self, market_data: Dict[str, Any]) -> RegimeClassification:
        """Classify current market regime"""
        # Ensemble of 3 regime models must agree > 60%
        votes = self._get_ensemble_votes(market_data)
        
        # Count votes
        vote_counts = {}
        for vote in votes:
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        # Get majority vote
        majority_label = max(vote_counts, key=vote_counts.get)
        agreement = vote_counts[majority_label] / len(votes)
        
        # Calculate confidence
        confidence = self._calculate_confidence(market_data, majority_label)
        
        # Calculate stability (rolling consistency)
        stability = self._calculate_stability()
        
        # Calculate transition probability
        transition_prob = self._calculate_transition_probability(market_data)
        
        classification = RegimeClassification(
            label=majority_label,
            confidence=confidence,
            stability=stability,
            transition_probability=transition_prob,
            ensemble_agreement=agreement
        )
        
        self._regime_history.append(classification)
        return classification
    
    def _get_ensemble_votes(self, market_data: Dict[str, Any]) -> List[RegimeLabel]:
        """Get votes from ensemble models"""
        votes = []
        
        # Model 1: Trend-based classification
        trend = market_data.get("trend", 0)
        volatility = market_data.get("volatility", 0)
        
        if volatility > 0.5:
            votes.append(RegimeLabel.CRISIS)
        elif trend > 0.3:
            votes.append(RegimeLabel.TRENDING_BULL)
        elif trend < -0.3:
            votes.append(RegimeLabel.TRENDING_BEAR)
        else:
            votes.append(RegimeLabel.RANGING)
        
        # Model 2: Volatility-based classification
        vol_percentile = market_data.get("volatility_percentile", 50)
        if vol_percentile > 90:
            votes.append(RegimeLabel.CRISIS)
        elif vol_percentile > 70:
            votes.append(RegimeLabel.UNCERTAIN)
        else:
            votes.append(votes[0] if votes else RegimeLabel.RANGING)
        
        # Model 3: Momentum-based classification
        momentum = market_data.get("momentum", 0)
        if abs(momentum) < 0.1:
            votes.append(RegimeLabel.RANGING)
        elif momentum > 0:
            votes.append(RegimeLabel.TRENDING_BULL)
        else:
            votes.append(RegimeLabel.TRENDING_BEAR)
        
        return votes
    
    def _calculate_confidence(self, market_data: Dict[str, Any], label: RegimeLabel) -> float:
        """Calculate regime classification confidence"""
        base_confidence = 0.7
        
        # Adjust based on volatility
        volatility = market_data.get("volatility", 0)
        if volatility > 0.3:
            base_confidence -= 0.2
        
        # Adjust based on data quality
        data_quality = market_data.get("data_quality", 1.0)
        base_confidence *= data_quality
        
        return max(0.0, min(1.0, base_confidence))
    
    def _calculate_stability(self) -> float:
        """Calculate regime stability from history"""
        if len(self._regime_history) < 10:
            return 0.5
        
        recent = [r.label for r in list(self._regime_history)[-10:]]
        most_common = max(set(recent), key=recent.count)
        return recent.count(most_common) / len(recent)
    
    def _calculate_transition_probability(self, market_data: Dict[str, Any]) -> float:
        """Calculate probability of regime change"""
        volatility = market_data.get("volatility", 0)
        momentum_change = abs(market_data.get("momentum_change", 0))
        
        base_prob = 0.1
        base_prob += volatility * 0.3
        base_prob += momentum_change * 0.2
        
        return max(0.0, min(1.0, base_prob))
    
    def should_use_fallback(self, classification: RegimeClassification) -> bool:
        """Check if fallback allocation should be used"""
        if classification.confidence < CONSTITUTION_CONSTANTS["REGIME_CONFIDENCE_FREEZE"]:
            return True
        if classification.ensemble_agreement < 0.6:
            return True
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EVOLUTION VALIDATION GATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class GateResult:
    """Result from a validation gate"""
    gate_name: str
    passed: bool
    score: float
    reason: str
    metrics: Dict[str, Any] = field(default_factory=dict)


class EvolutionValidationGates:
    """5 mandatory validation gates for evolution promotion"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
    async def validate_all_gates(
        self,
        candidate: Dict[str, Any],
        backtest_results: Dict[str, Any],
        existing_pool: List[Dict[str, Any]]
    ) -> Tuple[bool, List[GateResult]]:
        """Run all 5 validation gates - ALL must pass"""
        results = []
        
        # Gate 1: Statistical Validity
        gate1 = await self._gate_statistical_validity(candidate, backtest_results)
        results.append(gate1)
        
        # Gate 2: Stability
        gate2 = await self._gate_stability(candidate, backtest_results)
        results.append(gate2)
        
        # Gate 3: Execution Realism
        gate3 = await self._gate_execution_realism(candidate, backtest_results)
        results.append(gate3)
        
        # Gate 4: Robustness
        gate4 = await self._gate_robustness(candidate, backtest_results)
        results.append(gate4)
        
        # Gate 5: Capital Safety
        gate5 = await self._gate_capital_safety(candidate, backtest_results, existing_pool)
        results.append(gate5)
        
        # ALL 5 gates must pass
        all_passed = all(r.passed for r in results)
        
        if not all_passed:
            failed = [r.gate_name for r in results if not r.passed]
            logger.warning(f"Evolution candidate REJECTED: Failed gates {failed}")
        
        return all_passed, results
    
    async def _gate_statistical_validity(
        self,
        candidate: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> GateResult:
        """Gate 1: Statistical Validity"""
        oos_observations = backtest_results.get("oos_observations", 0)
        p_value = backtest_results.get("p_value", 1.0)
        effect_size = backtest_results.get("effect_size", 0)
        
        passed = (
            oos_observations >= CONSTITUTION_CONSTANTS["GATE_MIN_OOS_OBSERVATIONS"] and
            p_value < CONSTITUTION_CONSTANTS["GATE_P_VALUE_THRESHOLD"] and
            effect_size > 0.01  # Economically meaningful
        )
        
        return GateResult(
            gate_name="Statistical Validity",
            passed=passed,
            score=1.0 - p_value if passed else 0.0,
            reason=f"OOS={oos_observations}, p={p_value:.4f}, effect={effect_size:.4f}",
            metrics={"oos_observations": oos_observations, "p_value": p_value, "effect_size": effect_size}
        )
    
    async def _gate_stability(
        self,
        candidate: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> GateResult:
        """Gate 2: Stability across regimes"""
        regime_performance = backtest_results.get("regime_performance", {})
        
        if not regime_performance:
            return GateResult(
                gate_name="Stability",
                passed=False,
                score=0.0,
                reason="No regime performance data"
            )
        
        # Check consistency across 3 regime types
        regime_alphas = list(regime_performance.values())
        total_alpha = sum(regime_alphas)
        
        # No single regime accounts for > 60% of total alpha
        max_regime_share = max(regime_alphas) / total_alpha if total_alpha > 0 else 1.0
        
        passed = (
            len(regime_performance) >= 3 and
            max_regime_share < CONSTITUTION_CONSTANTS["GATE_MAX_REGIME_ALPHA_SHARE"]
        )
        
        return GateResult(
            gate_name="Stability",
            passed=passed,
            score=1.0 - max_regime_share if passed else 0.0,
            reason=f"Max regime share: {max_regime_share:.1%}",
            metrics={"regime_performance": regime_performance, "max_regime_share": max_regime_share}
        )
    
    async def _gate_execution_realism(
        self,
        candidate: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> GateResult:
        """Gate 3: Execution Realism"""
        used_dynamic_slippage = backtest_results.get("used_dynamic_slippage", False)
        used_fill_probability = backtest_results.get("used_fill_probability", False)
        used_latency_simulation = backtest_results.get("used_latency_simulation", False)
        tested_missing_data = backtest_results.get("tested_missing_data", False)
        
        passed = all([
            used_dynamic_slippage,
            used_fill_probability,
            used_latency_simulation,
            tested_missing_data
        ])
        
        return GateResult(
            gate_name="Execution Realism",
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=f"Slippage={used_dynamic_slippage}, Fill={used_fill_probability}, Latency={used_latency_simulation}, Missing={tested_missing_data}"
        )
    
    async def _gate_robustness(
        self,
        candidate: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> GateResult:
        """Gate 4: Robustness"""
        noise_test_passed = backtest_results.get("noise_injection_passed", False)
        adversarial_test_passed = backtest_results.get("adversarial_regime_passed", False)
        temporal_cv_passed = backtest_results.get("temporal_cv_passed", False)
        cross_regime_passed = backtest_results.get("cross_regime_passed", False)
        
        passed = all([
            noise_test_passed,
            adversarial_test_passed,
            temporal_cv_passed,
            cross_regime_passed
        ])
        
        return GateResult(
            gate_name="Robustness",
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=f"Noise={noise_test_passed}, Adversarial={adversarial_test_passed}, Temporal={temporal_cv_passed}, CrossRegime={cross_regime_passed}"
        )
    
    async def _gate_capital_safety(
        self,
        candidate: Dict[str, Any],
        backtest_results: Dict[str, Any],
        existing_pool: List[Dict[str, Any]]
    ) -> GateResult:
        """Gate 5: Capital Safety"""
        max_drawdown = backtest_results.get("max_drawdown", 1.0)
        hard_drawdown_limit = self.config.get("hard_drawdown_limit", 0.15)
        
        # Correlation with existing pool
        correlations = backtest_results.get("pool_correlations", [])
        max_correlation = max(correlations) if correlations else 0.0
        
        # Kill-switch trigger rate
        kill_switch_rate = backtest_results.get("kill_switch_trigger_rate", 1.0)
        
        passed = (
            max_drawdown < hard_drawdown_limit and
            max_correlation < CONSTITUTION_CONSTANTS["GATE_MAX_CORRELATION_WITH_POOL"] and
            kill_switch_rate < CONSTITUTION_CONSTANTS["GATE_MAX_KILL_SWITCH_RATE"]
        )
        
        return GateResult(
            gate_name="Capital Safety",
            passed=passed,
            score=1.0 - max_drawdown if passed else 0.0,
            reason=f"MaxDD={max_drawdown:.1%}, MaxCorr={max_correlation:.2f}, KillRate={kill_switch_rate:.3%}",
            metrics={"max_drawdown": max_drawdown, "max_correlation": max_correlation, "kill_switch_rate": kill_switch_rate}
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA INTEGRITY PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DataIntegrityPipeline:
    """Validates data integrity before processing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._validation_failures = 0
        self._total_validations = 0
        
    def validate_tick(
        self,
        tick: Dict[str, Any],
        historical_spread: float,
        last_timestamp: float
    ) -> Tuple[bool, str]:
        """Validate a single tick"""
        self._total_validations += 1
        
        # Check spread
        spread = tick.get("spread", 0)
        if spread > CONSTITUTION_CONSTANTS["MAX_SPREAD_MULTIPLIER"] * historical_spread:
            self._validation_failures += 1
            return False, f"Spread {spread} > {CONSTITUTION_CONSTANTS['MAX_SPREAD_MULTIPLIER']}x historical"
        
        # Check timestamp gap
        timestamp = tick.get("timestamp", 0)
        gap_threshold = self.config.get("max_timestamp_gap", 60)
        if last_timestamp > 0 and (timestamp - last_timestamp) > gap_threshold:
            self._validation_failures += 1
            return False, f"Timestamp gap {timestamp - last_timestamp}s > {gap_threshold}s"
        
        return True, "Valid"
    
    def validate_feature(self, feature_name: str, value: float, mean: float, std: float) -> Tuple[bool, str]:
        """Validate a computed feature"""
        if std > 0:
            z_score = abs((value - mean) / std)
            if z_score > CONSTITUTION_CONSTANTS["MAX_FEATURE_ZSCORE"]:
                return False, f"Feature {feature_name} Z-score {z_score:.2f} > {CONSTITUTION_CONSTANTS['MAX_FEATURE_ZSCORE']}"
        return True, "Valid"
    
    def get_failure_rate(self) -> float:
        """Get current validation failure rate"""
        if self._total_validations == 0:
            return 0.0
        return self._validation_failures / self._total_validations
    
    def check_stale_signal(self, signal_timestamp: float, latency_threshold: float) -> bool:
        """Check if signal is stale"""
        age = time.time() - signal_timestamp
        return age > latency_threshold


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALETHEIA-INSPIRED COMPONENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class DataSample:
    """Training data sample with metadata"""
    timestamp: float
    features: Dict[str, float]
    label: Optional[float]
    regime: RegimeLabel
    quality_score: float
    counterfactual_validated: bool = False
    inclusion_probability: float = 1.0


@dataclass
class CounterfactualResult:
    """Result from counterfactual validation"""
    sample_id: str
    actual_outcome: float
    counterfactual_outcome: float
    causal_effect: float
    confidence: float
    passed: bool


class ConstrainedDataCurationEngine:
    """
    Aletheia-inspired data curation engine with strict quality gates.
    
    Principles:
    - Only high-quality, regime-balanced data enters training
    - Counterfactual validation for causal inference
    - Automatic outlier and anomaly rejection
    - Regime-aware sampling to prevent overfitting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._data_buffer: deque = deque(maxlen=100000)
        self._regime_counts: Dict[RegimeLabel, int] = {}
        self._quality_threshold = self.config.get("quality_threshold", 0.7)
        self._max_regime_imbalance = self.config.get("max_regime_imbalance", 2.0)
        self._lock = threading.Lock()
        
        # Initialize regime counts
        for regime in RegimeLabel:
            self._regime_counts[regime] = 0
    
    def curate_sample(
        self,
        sample: DataSample,
        current_regime_distribution: Dict[RegimeLabel, float]
    ) -> Tuple[bool, str]:
        """
        Curate a data sample through quality gates.
        
        Args:
            sample: Data sample to curate
            current_regime_distribution: Current distribution of regimes in buffer
            
        Returns:
            Tuple of (accepted, reason)
        """
        # Gate 1: Quality score threshold
        if sample.quality_score < self._quality_threshold:
            return False, f"Quality score {sample.quality_score:.2f} < {self._quality_threshold}"
        
        # Gate 2: Regime balance check
        if not self._check_regime_balance(sample.regime, current_regime_distribution):
            return False, f"Regime {sample.regime.value} overrepresented"
        
        # Gate 3: Feature sanity checks
        for feature_name, value in sample.features.items():
            if not np.isfinite(value):
                return False, f"Feature {feature_name} is not finite"
            if abs(value) > 1e6:
                return False, f"Feature {feature_name} magnitude too large"
        
        # Gate 4: Counterfactual validation requirement
        if not sample.counterfactual_validated:
            # Sample must pass counterfactual validation before inclusion
            return False, "Awaiting counterfactual validation"
        
        # Accept sample
        with self._lock:
            self._data_buffer.append(sample)
            self._regime_counts[sample.regime] += 1
        
        return True, "Sample accepted"
    
    def _check_regime_balance(
        self,
        regime: RegimeLabel,
        current_distribution: Dict[RegimeLabel, float]
    ) -> bool:
        """Check if adding sample maintains regime balance"""
        if not current_distribution:
            return True
        
        # Calculate what the new distribution would be
        total_samples = sum(self._regime_counts.values())
        if total_samples == 0:
            return True
        
        regime_proportion = self._regime_counts.get(regime, 0) / total_samples
        
        # Check if this regime is already overrepresented
        target_proportion = current_distribution.get(regime, 0.2)
        if regime_proportion > target_proportion * self._max_regime_imbalance:
            return False
        
        return True
    
    def get_regime_balanced_batch(
        self,
        batch_size: int,
        target_distribution: Dict[RegimeLabel, float]
    ) -> List[DataSample]:
        """
        Get a regime-balanced batch for training.
        
        Args:
            batch_size: Number of samples to retrieve
            target_distribution: Target regime distribution
            
        Returns:
            List of balanced samples
        """
        with self._lock:
            # Calculate samples needed per regime
            samples_per_regime = {}
            for regime, proportion in target_distribution.items():
                samples_per_regime[regime] = int(batch_size * proportion)
            
            # Collect samples
            batch = []
            buffer_list = list(self._data_buffer)
            
            for regime, count in samples_per_regime.items():
                regime_samples = [s for s in buffer_list if s.regime == regime]
                if len(regime_samples) >= count:
                    batch.extend(np.random.choice(regime_samples, count, replace=False))
                else:
                    batch.extend(regime_samples)
            
            return batch
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get curation statistics"""
        with self._lock:
            total = sum(self._regime_counts.values())
            return {
                "total_samples": total,
                "regime_distribution": {
                    regime.value: count / total if total > 0 else 0
                    for regime, count in self._regime_counts.items()
                },
                "buffer_utilization": len(self._data_buffer) / self._data_buffer.maxlen
            }


class CounterfactualValidator:
    """
    Validates training samples using counterfactual reasoning.
    
    Ensures that learned patterns are causal, not spurious correlations.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._validation_history: deque = deque(maxlen=10000)
        self._causal_effect_threshold = self.config.get("causal_effect_threshold", 0.01)
        self._confidence_threshold = self.config.get("confidence_threshold", 0.7)
    
    async def validate_counterfactual(
        self,
        sample: DataSample,
        model: Any,
        intervention: Dict[str, float]
    ) -> CounterfactualResult:
        """
        Validate a sample using counterfactual intervention.
        
        Args:
            sample: Data sample to validate
            model: Prediction model
            intervention: Feature interventions to test
            
        Returns:
            CounterfactualResult with validation outcome
        """
        # Get actual prediction
        actual_outcome = await self._predict(model, sample.features)
        
        # Create counterfactual by intervening on features
        counterfactual_features = sample.features.copy()
        counterfactual_features.update(intervention)
        
        # Get counterfactual prediction
        counterfactual_outcome = await self._predict(model, counterfactual_features)
        
        # Calculate causal effect
        causal_effect = abs(counterfactual_outcome - actual_outcome)
        
        # Estimate confidence (simplified - would use more sophisticated method)
        confidence = min(1.0, causal_effect / (abs(actual_outcome) + 1e-6))
        
        # Validate: causal effect should be meaningful
        passed = (
            causal_effect >= self._causal_effect_threshold and
            confidence >= self._confidence_threshold
        )
        
        result = CounterfactualResult(
            sample_id=str(sample.timestamp),
            actual_outcome=actual_outcome,
            counterfactual_outcome=counterfactual_outcome,
            causal_effect=causal_effect,
            confidence=confidence,
            passed=passed
        )
        
        self._validation_history.append(result)
        return result
    
    async def _predict(self, model: Any, features: Dict[str, float]) -> float:
        """Make prediction with model"""
        # Placeholder - would integrate with actual model
        return 0.0
    
    def get_validation_rate(self) -> float:
        """Get percentage of samples passing counterfactual validation"""
        if not self._validation_history:
            return 0.0
        passed = sum(1 for r in self._validation_history if r.passed)
        return passed / len(self._validation_history)


@dataclass
class PerformanceMetrics:
    """Multi-metric performance sensing"""
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    tail_ratio: float = 0.0
    stability: float = 0.0
    regime_consistency: float = 0.0


class MultiMetricPerformanceSensor:
    """
    Multi-metric performance sensing system.
    
    Tracks comprehensive performance metrics across multiple dimensions
    to detect degradation early and prevent overfitting.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._returns_history: deque = deque(maxlen=10000)
        self._metrics_history: deque = deque(maxlen=1000)
        self._baseline_metrics: Optional[PerformanceMetrics] = None
        self._lock = threading.Lock()
    
    def record_return(self, return_value: float, regime: RegimeLabel):
        """Record a return for metric calculation"""
        with self._lock:
            self._returns_history.append({
                "return": return_value,
                "regime": regime,
                "timestamp": time.time()
            })
    
    def compute_metrics(self, lookback_window: int = 1000) -> PerformanceMetrics:
        """Compute comprehensive performance metrics"""
        with self._lock:
            if len(self._returns_history) < 20:
                return PerformanceMetrics()
            
            returns = [r["return"] for r in list(self._returns_history)[-lookback_window:]]
            returns_array = np.array(returns)
            
            # Sharpe ratio
            sharpe = np.mean(returns_array) / (np.std(returns_array) + 1e-6) * np.sqrt(252)
            
            # Sortino ratio (downside deviation)
            downside_returns = returns_array[returns_array < 0]
            downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1e-6
            sortino = np.mean(returns_array) / downside_std * np.sqrt(252)
            
            # Max drawdown
            cumulative = np.cumprod(1 + returns_array)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_dd = abs(np.min(drawdown))
            
            # Win rate
            win_rate = np.sum(returns_array > 0) / len(returns_array)
            
            # Profit factor
            gross_profit = np.sum(returns_array[returns_array > 0])
            gross_loss = abs(np.sum(returns_array[returns_array < 0]))
            profit_factor = gross_profit / (gross_loss + 1e-6)
            
            # Calmar ratio
            calmar = (np.mean(returns_array) * 252) / (max_dd + 1e-6)
            
            # Tail ratio (95th percentile / 5th percentile)
            tail_ratio = abs(np.percentile(returns_array, 95) / (np.percentile(returns_array, 5) + 1e-6))
            
            # Stability (consistency of returns)
            stability = 1.0 - (np.std(returns_array) / (abs(np.mean(returns_array)) + 1e-6))
            
            # Regime consistency
            regime_consistency = self._calculate_regime_consistency()
            
            metrics = PerformanceMetrics(
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                max_drawdown=max_dd,
                win_rate=win_rate,
                profit_factor=profit_factor,
                calmar_ratio=calmar,
                information_ratio=sharpe,  # Simplified
                tail_ratio=tail_ratio,
                stability=max(0.0, min(1.0, stability)),
                regime_consistency=regime_consistency
            )
            
            self._metrics_history.append(metrics)
            return metrics
    
    def _calculate_regime_consistency(self) -> float:
        """Calculate consistency across regimes"""
        if len(self._returns_history) < 50:
            return 0.5
        
        # Group returns by regime
        regime_returns = {}
        for entry in self._returns_history:
            regime = entry["regime"]
            if regime not in regime_returns:
                regime_returns[regime] = []
            regime_returns[regime].append(entry["return"])
        
        # Calculate mean return per regime
        regime_means = {r: np.mean(returns) for r, returns in regime_returns.items() if len(returns) > 5}
        
        if len(regime_means) < 2:
            return 0.5
        
        # Consistency = 1 - coefficient of variation of regime means
        means_array = np.array(list(regime_means.values()))
        cv = np.std(means_array) / (abs(np.mean(means_array)) + 1e-6)
        consistency = max(0.0, min(1.0, 1.0 - cv))
        
        return consistency
    
    def set_baseline(self, metrics: PerformanceMetrics):
        """Set baseline metrics for comparison"""
        self._baseline_metrics = metrics
    
    def detect_degradation(
        self,
        current_metrics: PerformanceMetrics,
        threshold: float = 0.15
    ) -> Tuple[bool, List[str]]:
        """
        Detect performance degradation across multiple metrics.
        
        Args:
            current_metrics: Current performance metrics
            threshold: Degradation threshold (15% default)
            
        Returns:
            Tuple of (degraded, reasons)
        """
        if not self._baseline_metrics:
            return False, []
        
        degraded = False
        reasons = []
        
        # Check Sharpe ratio
        if current_metrics.sharpe_ratio < self._baseline_metrics.sharpe_ratio * (1 - threshold):
            degraded = True
            reasons.append(f"Sharpe degraded: {current_metrics.sharpe_ratio:.2f} < {self._baseline_metrics.sharpe_ratio:.2f}")
        
        # Check max drawdown
        if current_metrics.max_drawdown > self._baseline_metrics.max_drawdown * (1 + threshold):
            degraded = True
            reasons.append(f"Drawdown increased: {current_metrics.max_drawdown:.2%} > {self._baseline_metrics.max_drawdown:.2%}")
        
        # Check win rate
        if current_metrics.win_rate < self._baseline_metrics.win_rate * (1 - threshold):
            degraded = True
            reasons.append(f"Win rate degraded: {current_metrics.win_rate:.2%} < {self._baseline_metrics.win_rate:.2%}")
        
        # Check stability
        if current_metrics.stability < self._baseline_metrics.stability * (1 - threshold):
            degraded = True
            reasons.append(f"Stability degraded: {current_metrics.stability:.2f} < {self._baseline_metrics.stability:.2f}")
        
        # Check regime consistency
        if current_metrics.regime_consistency < self._baseline_metrics.regime_consistency * (1 - threshold):
            degraded = True
            reasons.append(f"Regime consistency degraded: {current_metrics.regime_consistency:.2f} < {self._baseline_metrics.regime_consistency:.2f}")
        
        return degraded, reasons


class DeterministicLearningModeController:
    """
    Deterministic learning mode controller with strict gating.
    
    Controls when and how learning occurs, ensuring all updates are:
    1. Counterfactually validated
    2. Bounded in magnitude
    3. Regime-balanced
    4. Performance-gated
    """
    
    def __init__(
        self,
        curation_engine: ConstrainedDataCurationEngine,
        counterfactual_validator: CounterfactualValidator,
        performance_sensor: MultiMetricPerformanceSensor,
        config: Dict[str, Any] = None
    ):
        self.config = config or {}
        self.curation_engine = curation_engine
        self.counterfactual_validator = counterfactual_validator
        self.performance_sensor = performance_sensor
        
        # Learning mode state
        self._learning_enabled = True
        self._learning_mode: str = "conservative"  # conservative, normal, aggressive
        self._update_count = 0
        self._last_update_time = time.time()
        self._lock = threading.Lock()
        
        # Gating thresholds
        self._min_samples_for_update = self.config.get("min_samples_for_update", 1000)
        self._min_counterfactual_pass_rate = self.config.get("min_counterfactual_pass_rate", 0.7)
        self._max_updates_per_hour = self.config.get("max_updates_per_hour", 4)
    
    async def gate_learning_update(
        self,
        proposed_update: Dict[str, Any],
        current_metrics: PerformanceMetrics
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Gate a proposed learning update through all validation checks.
        
        Args:
            proposed_update: Proposed parameter update
            current_metrics: Current performance metrics
            
        Returns:
            Tuple of (approved, bounded_update, reason)
        """
        with self._lock:
            # Gate 1: Learning must be enabled
            if not self._learning_enabled:
                return False, {}, "Learning disabled"
            
            # Gate 2: Sufficient data quality
            curation_stats = self.curation_engine.get_statistics()
            if curation_stats["total_samples"] < self._min_samples_for_update:
                return False, {}, f"Insufficient samples: {curation_stats['total_samples']} < {self._min_samples_for_update}"
            
            # Gate 3: Counterfactual validation rate
            cf_rate = self.counterfactual_validator.get_validation_rate()
            if cf_rate < self._min_counterfactual_pass_rate:
                return False, {}, f"Counterfactual pass rate too low: {cf_rate:.2%} < {self._min_counterfactual_pass_rate:.0%}"
            
            # Gate 4: Update rate limiting
            time_since_last = time.time() - self._last_update_time
            if time_since_last < (3600 / self._max_updates_per_hour):
                return False, {}, f"Update rate limit: {time_since_last:.0f}s < {3600/self._max_updates_per_hour:.0f}s"
            
            # Gate 5: Performance degradation check
            degraded, reasons = self.performance_sensor.detect_degradation(current_metrics)
            if degraded:
                return False, {}, f"Performance degraded: {'; '.join(reasons)}"
            
            # Gate 6: Bound the update magnitude
            bounded_update = self._bound_update(proposed_update)
            
            # All gates passed
            self._update_count += 1
            self._last_update_time = time.time()
            
            return True, bounded_update, "Update approved"
    
    def _bound_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Bound update magnitude based on learning mode"""
        mode_bounds = {
            "conservative": 0.001,  # 0.1% max change
            "normal": 0.005,        # 0.5% max change
            "aggressive": 0.01      # 1.0% max change
        }
        
        max_change = mode_bounds.get(self._learning_mode, 0.005)
        
        bounded = {}
        for key, value in update.items():
            if isinstance(value, (int, float)):
                bounded[key] = max(-max_change, min(max_change, value))
            else:
                bounded[key] = value
        
        return bounded
    
    def set_learning_mode(self, mode: str):
        """Set learning mode: conservative, normal, or aggressive"""
        if mode in ["conservative", "normal", "aggressive"]:
            with self._lock:
                self._learning_mode = mode
                logger.info(f"Learning mode set to: {mode}")
    
    def disable_learning(self, reason: str):
        """Disable learning"""
        with self._lock:
            self._learning_enabled = False
            logger.warning(f"Learning DISABLED: {reason}")
    
    def enable_learning(self):
        """Enable learning"""
        with self._lock:
            self._learning_enabled = True
            logger.info("Learning ENABLED")
    
    def get_status(self) -> Dict[str, Any]:
        """Get learning controller status"""
        with self._lock:
            return {
                "learning_enabled": self._learning_enabled,
                "learning_mode": self._learning_mode,
                "update_count": self._update_count,
                "time_since_last_update": time.time() - self._last_update_time,
                "curation_stats": self.curation_engine.get_statistics(),
                "counterfactual_pass_rate": self.counterfactual_validator.get_validation_rate()
            }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OBSERVABILITY SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class SystemEvent:
    """System event for logging"""
    timestamp: float
    zone_origin: IsolationZone
    event_type: str
    trigger_condition: str
    delta_applied: Optional[Dict[str, Any]]
    current_state_hash: str
    operator_id: str  # "automated" or human ID


class ObservabilitySystem:
    """Non-negotiable observability for all system events"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._event_log: deque = deque(maxlen=100000)
        self._alerts: List[Dict] = []
        self._lock = threading.Lock()
        
    def log_event(self, event: SystemEvent):
        """Log a system event"""
        with self._lock:
            self._event_log.append(event)
            logger.info(f"[{event.zone_origin.value}] {event.event_type}: {event.trigger_condition}")
    
    def add_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """Add an alert"""
        with self._lock:
            alert = {
                "timestamp": time.time(),
                "type": alert_type,
                "message": message,
                "severity": severity
            }
            self._alerts.append(alert)
            
            if severity == "critical":
                logger.critical(f"ALERT: {alert_type} - {message}")
            else:
                logger.warning(f"ALERT: {alert_type} - {message}")
    
    def get_dashboard_state(
        self,
        zone_validator: ZoneBoundaryValidator,
        freeze_controller: LearningFreezeController,
        shadow_system: ShadowModelSystem,
        execution_monitor: ExecutionAlphaMonitor,
        market_engine: MarketStateEngine,
        snapshot_stack: ParameterSnapshotStack
    ) -> Dict[str, Any]:
        """Get real-time dashboard state"""
        return {
            "zone_boundary_integrity": {
                zone.value: zone_validator.validate_zone_integrity(zone, {})
                for zone in IsolationZone
            },
            "active_freeze_triggers": {
                "is_frozen": freeze_controller.is_frozen,
                "reason": freeze_controller.freeze_state.reason.value if freeze_controller.freeze_state.reason else None
            },
            "shadow_vs_production": {
                "signal_agreement_rate": shadow_system.shadow_metrics.signal_agreement_rate,
                "divergence_alert": shadow_system.check_divergence_alert()
            },
            "execution_alpha": {
                "7d": execution_monitor.metrics.execution_alpha_7d,
                "30d": execution_monitor.metrics.execution_alpha_30d,
                "slippage_drift": execution_monitor.metrics.slippage_drift
            },
            "cumulative_drift_pct": 0.0,  # Would be tracked by adaptation layer
            "regime": {
                "confidence": 0.0,
                "stability": 0.0
            },
            "rollback_availability": {
                "last_snapshot_age_hours": (time.time() - snapshot_stack.get_latest().timestamp) / 3600 if snapshot_stack.get_latest() else None
            },
            "alerts": self._alerts[-10:]  # Last 10 alerts
        }


class AlphaAlgoCore:
    """
    AlphaAlgo Core - Capital Governance System
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    SYSTEM CONSTITUTION — IMMUTABLE LAWS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    1. Capital protection supersedes all learning objectives.
    2. No component may modify its own execution boundary.
    3. Every structural change must pass 5 validation gates before promotion.
    
    A survival-first capital governance system that enforces strict rules
    regarding market tradability, strategy assumptions, adversarial testing,
    exposure control, anti-learning, and continuous validity monitoring.
    
    This system prioritizes survival over performance and operates as a gated
    control system with irreversible barriers.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the AlphaAlgo Core system.
        
        Args:
            config: Configuration dictionary for the system and its layers
        """
        self.config = config or {}
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # ZONE BOUNDARY ENFORCEMENT
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.zone_validator = ZoneBoundaryValidator()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PARAMETER SNAPSHOT SYSTEM (Zone B rollback capability)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.snapshot_stack = ParameterSnapshotStack(
            max_depth=CONSTITUTION_CONSTANTS["PARAMETER_SNAPSHOT_DEPTH"]
        )
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # LEARNING FREEZE CONTROLLER
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.freeze_controller = LearningFreezeController(self.config)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # EXECUTION ALPHA MONITOR (Loop 6)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.execution_monitor = ExecutionAlphaMonitor(self.config)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # SHADOW MODEL SYSTEM (Live A/B comparison)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.shadow_system = ShadowModelSystem(self.config)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # HARD REVERSION SYSTEM
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.reversion_system = HardReversionSystem(self.snapshot_stack, self.config)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # MARKET STATE ENGINE (Regime Classification)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.market_state_engine = MarketStateEngine(self.config)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # EVOLUTION VALIDATION GATES (5 mandatory gates)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.evolution_gates = EvolutionValidationGates(self.config)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # DATA INTEGRITY PIPELINE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.data_integrity = DataIntegrityPipeline(self.config)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # OBSERVABILITY SYSTEM (Non-negotiable logging)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.observability = ObservabilitySystem(self.config)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # ALETHEIA-INSPIRED LEARNING SYSTEM
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.data_curation = ConstrainedDataCurationEngine(self.config)
        self.counterfactual_validator = CounterfactualValidator(self.config)
        self.performance_sensor = MultiMetricPerformanceSensor(self.config)
        self.learning_controller = DeterministicLearningModeController(
            curation_engine=self.data_curation,
            counterfactual_validator=self.counterfactual_validator,
            performance_sensor=self.performance_sensor,
            config=self.config
        )
        
        # Create the capital governance system
        self.governance = CapitalGovernanceSystem(self.config)
        
        # Initialize all layers
        self._initialize_layers()
        
        # Strategy registry with lifecycle tracking
        self.strategies: Dict[str, Dict[str, Any]] = {}
        self.strategy_lifecycle: Dict[str, StrategyLifecycle] = {}
        
        # Bounded adaptation state (Zone B)
        self._cumulative_drift: float = 0.0
        self._last_anchor_time: float = time.time()
        self._adaptation_parameters: Dict[str, float] = {}
        
        # Performance tracking
        self._performance_baseline_30d: float = 0.0
        self._days_degraded: int = 0
        self._strategy_pool_sharpe_baseline: float = 0.0
        
        # Register initial zone states
        self._register_zone_boundaries()
        
        # Take initial parameter snapshot
        self.snapshot_stack.push(self._get_current_parameters(), "initialization")
        
        logger.info("AlphaAlgo Core initialized with CONSTITUTION enforcement")
    
    def _register_zone_boundaries(self):
        """Register initial zone boundary states for integrity checking"""
        # Zone A: Execution Engine (FROZEN)
        zone_a_state = {
            "capital_accounting": "immutable",
            "order_routing": "immutable", 
            "position_sizing": "immutable",
            "risk_limits": self.config.get("risk_limits", {}),
            "kill_switch_thresholds": self.config.get("kill_switch", {})
        }
        self.zone_validator.register_zone_state(IsolationZone.ZONE_A_EXECUTION, zone_a_state)
        
        # Zone B: Adaptation Layer (bounded)
        zone_b_state = {
            "max_delta_per_update": CONSTITUTION_CONSTANTS["MAX_DELTA_PER_UPDATE"],
            "max_cumulative_drift": CONSTITUTION_CONSTANTS["MAX_CUMULATIVE_DRIFT"],
            "current_drift": 0.0
        }
        self.zone_validator.register_zone_state(IsolationZone.ZONE_B_ADAPTATION, zone_b_state)
        
        # Zone C: Strategy Pool (isolated)
        zone_c_state = {
            "strategies": [],
            "isolation_enforced": True
        }
        self.zone_validator.register_zone_state(IsolationZone.ZONE_C_STRATEGY, zone_c_state)
        
        # Zone D: Evolution Engine (offline)
        zone_d_state = {
            "air_gapped": True,
            "gates_required": 5
        }
        self.zone_validator.register_zone_state(IsolationZone.ZONE_D_EVOLUTION, zone_d_state)
        
        # Zone E: Meta-Agent (read-only)
        zone_e_state = {
            "can_read": True,
            "can_propose": True,
            "can_execute": False
        }
        self.zone_validator.register_zone_state(IsolationZone.ZONE_E_META_AGENT, zone_e_state)
    
    def _get_current_parameters(self) -> Dict[str, Any]:
        """Get current system parameters for snapshotting"""
        return {
            "adaptation_parameters": copy.deepcopy(self._adaptation_parameters),
            "cumulative_drift": self._cumulative_drift,
            "strategy_lifecycle": {k: v.value for k, v in self.strategy_lifecycle.items()},
            "timestamp": time.time()
        }
    
    def _initialize_layers(self):
        """Initialize all layers of the capital governance system"""
        # Layer 0: Market Physics Filter
        market_physics_config = self.config.get("market_physics_filter", {})
        self.market_physics_filter = MarketPhysicsFilter(market_physics_config)
        self.governance.add_layer("market_physics_filter", self.market_physics_filter)
        
        # Layer 1: Strategy Zoo
        strategy_zoo_config = self.config.get("strategy_zoo", {})
        self.strategy_zoo = StrategyZoo(strategy_zoo_config)
        self.governance.add_layer("strategy_zoo", self.strategy_zoo)
        
        # Layer 2: Assumption Decompiler
        assumption_decompiler_config = self.config.get("assumption_decompiler", {})
        self.assumption_decompiler = AssumptionDecompiler(assumption_decompiler_config)
        self.governance.add_layer("assumption_decompiler", self.assumption_decompiler)
        
        # Layer 3: Regime Hostility Engine
        regime_hostility_config = self.config.get("regime_hostility_engine", {})
        self.regime_hostility_engine = RegimeHostilityEngine(regime_hostility_config)
        self.governance.add_layer("regime_hostility_engine", self.regime_hostility_engine)
        
        # Layer 4: Exposure Controller
        exposure_controller_config = self.config.get("exposure_controller", {})
        self.exposure_controller = ExposureController(exposure_controller_config)
        self.governance.add_layer("exposure_controller", self.exposure_controller)
        
        # Layer 5: Anti-Learning Firewall
        anti_learning_config = self.config.get("anti_learning_firewall", {})
        self.anti_learning_firewall = AntiLearningFirewall(anti_learning_config)
        self.governance.add_layer("anti_learning_firewall", self.anti_learning_firewall)
        
        # Layer 6: Continuous Validity Monitor
        validation_monitor_config = self.config.get("validation_monitor", {})
        self.validation_monitor = ContinuousValidityMonitor(validation_monitor_config)
        self.governance.add_layer("validation_monitor", self.validation_monitor)
    
    def register_strategy(self, strategy_id: str, strategy_config: Dict[str, Any]) -> bool:
        """
        Register a strategy with the AlphaAlgo Core system.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_config: Strategy configuration including assumptions
            
        Returns:
            bool: True if registration was successful
        """
        # Register with Strategy Zoo
        if not self.strategy_zoo.register_strategy(strategy_id, strategy_config):
            logger.warning(f"Failed to register strategy {strategy_id} with Strategy Zoo")
            return False
        
        # Store strategy configuration
        self.strategies[strategy_id] = strategy_config
        logger.info(f"Strategy {strategy_id} registered with AlphaAlgo Core")
        return True
    
    async def evaluate_tradability(
        self,
        strategy_id: str,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> CapitalGovernanceResult:
        """
        Evaluate if a strategy can trade and what exposure is permitted.
        
        This is the main entry point for the capital governance system.
        
        Args:
            strategy_id: Unique identifier for the strategy
            symbol: The market symbol
            market_data: Current market data
            
        Returns:
            CapitalGovernanceResult with tradability determination
        """
        # Check if strategy is registered
        if strategy_id not in self.strategies:
            logger.warning(f"Strategy {strategy_id} not registered with AlphaAlgo Core")
            return CapitalGovernanceResult(
                strategy_id=strategy_id,
                symbol=symbol,
                is_tradable=False,
                max_exposure=0.0,
                reason="Strategy not registered with AlphaAlgo Core"
            )
        
        # Get strategy configuration
        strategy_config = self.strategies[strategy_id]
        
        # Evaluate tradability through the governance system
        result = await self.governance.evaluate_tradability(
            strategy_id=strategy_id,
            symbol=symbol,
            market_data=market_data,
            strategy_config=strategy_config
        )
        
        return result
    
    async def process_market_event(self, event: Dict[str, Any]) -> bool:
        """
        Process a market event through the anti-learning firewall.
        
        Args:
            event: Market event data
            
        Returns:
            bool: True if the event should be included in learning, False if it should be excluded
        """
        return await self.governance.process_market_event(event)
    
    async def update_behavior(
        self,
        strategy_id: str,
        behavior_data: Dict[str, Any]
    ) -> None:
        """
        Update behavior data for continuous validity monitoring.
        
        Args:
            strategy_id: Unique identifier for the strategy
            behavior_data: Dictionary of behavior metrics
        """
        self.validation_monitor.update_behavior_history(strategy_id, behavior_data)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the AlphaAlgo Core system.
        
        Returns:
            Dict with system status information
        """
        return {
            "governance": self.governance.get_status(),
            "registered_strategies": list(self.strategies.keys()),
            "freeze_state": {
                "is_frozen": self.freeze_controller.is_frozen,
                "reason": self.freeze_controller.freeze_state.reason.value if self.freeze_controller.freeze_state.reason else None
            },
            "cumulative_drift": self._cumulative_drift,
            "execution_metrics": {
                "alpha_7d": self.execution_monitor.metrics.execution_alpha_7d,
                "alpha_30d": self.execution_monitor.metrics.execution_alpha_30d,
                "slippage_drift": self.execution_monitor.metrics.slippage_drift
            },
            "timestamp": time.time()
        }
    
    def record_execution_fill(
        self,
        expected_price: float,
        actual_price: float,
        position_direction: int,
        latency_ms: float
    ):
        """Record execution fill for alpha monitoring (Loop 6)"""
        self.execution_monitor.record_fill(
            expected_price=expected_price,
            actual_price=actual_price,
            position_direction=position_direction,
            latency_ms=latency_ms
        )
    
    def record_shadow_signals(
        self,
        shadow_signal: float,
        production_signal: float,
        shadow_confidence: float,
        production_confidence: float
    ):
        """Record signals from shadow and production models for comparison"""
        self.shadow_system.record_signals(
            shadow_signal=shadow_signal,
            production_signal=production_signal,
            shadow_confidence=shadow_confidence,
            production_confidence=production_confidence
        )
    
    def validate_tick_data(
        self,
        tick: Dict[str, Any],
        historical_spread: float,
        last_timestamp: float
    ) -> Tuple[bool, str]:
        """Validate tick data through data integrity pipeline"""
        return self.data_integrity.validate_tick(tick, historical_spread, last_timestamp)
    
    def get_dashboard_state(self) -> Dict[str, Any]:
        """Get real-time dashboard state for observability"""
        return self.observability.get_dashboard_state(
            zone_validator=self.zone_validator,
            freeze_controller=self.freeze_controller,
            shadow_system=self.shadow_system,
            execution_monitor=self.execution_monitor,
            market_engine=self.market_state_engine,
            snapshot_stack=self.snapshot_stack
        )
    
    async def enforce_constitution(
        self,
        current_drawdown: float,
        market_data: Dict[str, Any],
        strategy_pool_sharpe_5d: float = 0.0
    ) -> Dict[str, Any]:
        """
        Main constitution enforcement loop - checks all triggers and takes action.
        
        WHEN IN DOUBT: FREEZE, LOG, REVERT.
        
        Args:
            current_drawdown: Current system drawdown
            market_data: Current market data for regime classification
            strategy_pool_sharpe_5d: 5-day rolling Sharpe of strategy pool
            
        Returns:
            Dict with enforcement actions taken
        """
        actions = {"timestamp": time.time(), "actions_taken": []}
        
        # 1. Classify current regime
        regime = self.market_state_engine.classify_regime(market_data)
        
        # 2. Check learning freeze triggers
        freeze_reason = self.freeze_controller.check_freeze_triggers(
            current_drawdown=current_drawdown,
            regime_confidence=regime.confidence,
            execution_alpha_7d=self.execution_monitor.metrics.execution_alpha_7d,
            execution_alpha_30d=self.execution_monitor.metrics.execution_alpha_30d,
            cumulative_drift=self._cumulative_drift,
            tick_validation_failure_rate=self.data_integrity.get_failure_rate(),
            p99_latency=self.execution_monitor.metrics.p99_latency
        )
        
        if freeze_reason and not self.freeze_controller.is_frozen:
            self.freeze_controller.activate_freeze(freeze_reason)
            actions["actions_taken"].append(f"FREEZE_ACTIVATED: {freeze_reason.value}")
            
            self.observability.log_event(SystemEvent(
                timestamp=time.time(),
                zone_origin=IsolationZone.ZONE_B_ADAPTATION,
                event_type="LEARNING_FREEZE",
                trigger_condition=freeze_reason.value,
                delta_applied=None,
                current_state_hash=self.snapshot_stack.get_latest().hash_value if self.snapshot_stack.get_latest() else "",
                operator_id="automated"
            ))
        
        # 3. Check reversion triggers
        kill_switch_threshold = self.config.get("kill_switch", {}).get("max_drawdown", 0.15)
        reversion_level = self.reversion_system.check_reversion_triggers(
            performance_vs_30d_baseline=self._get_performance_vs_baseline(),
            days_degraded=self._days_degraded,
            strategy_pool_sharpe_5d=strategy_pool_sharpe_5d,
            strategy_pool_sharpe_baseline=self._strategy_pool_sharpe_baseline,
            system_drawdown=current_drawdown,
            kill_switch_threshold=kill_switch_threshold
        )
        
        if reversion_level:
            reversion_result = self.reversion_system.execute_reversion(reversion_level)
            actions["actions_taken"].append(f"REVERSION_EXECUTED: Level {reversion_level.value}")
            actions["reversion_result"] = reversion_result
            
            if "parameters" in reversion_result:
                self._apply_parameters(reversion_result["parameters"])
            
            self.observability.add_alert(
                "HARD_REVERSION",
                f"Level {reversion_level.value} reversion executed",
                severity="critical"
            )
        
        # 4. Check execution alpha alerts
        exec_alerts = self.execution_monitor.check_alerts()
        for alert in exec_alerts:
            actions["actions_taken"].append(alert)
            if "HARD STOP" in alert:
                self.freeze_controller.activate_freeze(FreezeReason.EXECUTION_ALPHA_DEGRADATION)
        
        # 5. Check shadow model divergence
        shadow_alert = self.shadow_system.check_divergence_alert()
        if shadow_alert:
            actions["actions_taken"].append(shadow_alert)
            self.observability.add_alert("SHADOW_DIVERGENCE", shadow_alert)
        
        # 6. Check zone boundary integrity
        for zone in IsolationZone:
            if not self.zone_validator.validate_zone_integrity(zone, {}):
                actions["actions_taken"].append(f"ZONE_INTEGRITY_VIOLATION: {zone.value}")
                self.observability.add_alert(
                    "ZONE_BOUNDARY_VIOLATION",
                    f"Zone {zone.value} integrity check failed",
                    severity="critical"
                )
        
        return actions
    
    def _get_performance_vs_baseline(self) -> float:
        """Calculate current performance vs 30-day baseline"""
        if self._performance_baseline_30d == 0:
            return 0.0
        return 0.0
    
    def _apply_parameters(self, parameters: Dict[str, Any]):
        """Apply parameters from a snapshot"""
        if "adaptation_parameters" in parameters:
            self._adaptation_parameters = copy.deepcopy(parameters["adaptation_parameters"])
        if "cumulative_drift" in parameters:
            self._cumulative_drift = parameters["cumulative_drift"]
        logger.info("Parameters applied from snapshot")
    
    async def bounded_parameter_update(
        self,
        parameter_name: str,
        proposed_delta: float
    ) -> Tuple[bool, float, str]:
        """
        Zone B: Bounded online adaptation with strict limits.
        
        Rules:
        - Max Δ per update cycle: 0.5%
        - Max cumulative drift from anchor: 5%
        - Mandatory re-anchoring when drift ceiling hit
        
        Args:
            parameter_name: Name of parameter to update
            proposed_delta: Proposed change amount
            
        Returns:
            Tuple of (accepted, actual_delta, reason)
        """
        if self.freeze_controller.is_frozen:
            return False, 0.0, f"Learning frozen: {self.freeze_controller.freeze_state.reason.value}"
        
        max_delta = CONSTITUTION_CONSTANTS["MAX_DELTA_PER_UPDATE"]
        actual_delta = max(-max_delta, min(max_delta, proposed_delta))
        
        new_cumulative = self._cumulative_drift + abs(actual_delta)
        if new_cumulative >= CONSTITUTION_CONSTANTS["MAX_CUMULATIVE_DRIFT"]:
            self._trigger_re_anchoring()
            return False, 0.0, "Cumulative drift ceiling hit - re-anchoring triggered"
        
        current_value = self._adaptation_parameters.get(parameter_name, 0.0)
        self._adaptation_parameters[parameter_name] = current_value + actual_delta
        self._cumulative_drift = new_cumulative
        
        last_snapshot = self.snapshot_stack.get_latest()
        if last_snapshot:
            hours_since = (time.time() - last_snapshot.timestamp) / 3600
            if hours_since >= CONSTITUTION_CONSTANTS["SNAPSHOT_FREQUENCY_HOURS"]:
                self.snapshot_stack.push(
                    self._get_current_parameters(),
                    f"scheduled_snapshot_{parameter_name}"
                )
        
        self.observability.log_event(SystemEvent(
            timestamp=time.time(),
            zone_origin=IsolationZone.ZONE_B_ADAPTATION,
            event_type="PARAMETER_UPDATE",
            trigger_condition=f"{parameter_name}: {actual_delta:+.4f}",
            delta_applied={"parameter": parameter_name, "delta": actual_delta},
            current_state_hash=self.snapshot_stack.get_latest().hash_value if self.snapshot_stack.get_latest() else "",
            operator_id="automated"
        ))
        
        return True, actual_delta, "Update accepted within bounds"
    
    def _trigger_re_anchoring(self):
        """Trigger mandatory re-anchoring when drift ceiling is hit"""
        self.snapshot_stack.push(self._get_current_parameters(), "pre_reanchor")
        self._cumulative_drift = 0.0
        self._last_anchor_time = time.time()
        self.freeze_controller.activate_freeze(FreezeReason.PARAMETER_DRIFT_CEILING)
        logger.warning("Re-anchoring triggered due to drift ceiling")
    
    async def validate_evolution_candidate(
        self,
        candidate: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> Tuple[bool, List[GateResult]]:
        """
        Zone D: Validate evolution candidate through 5 mandatory gates.
        
        ALL 5 gates must pass. No exceptions.
        
        Args:
            candidate: Evolution candidate configuration
            backtest_results: Results from offline backtesting
            
        Returns:
            Tuple of (all_passed, gate_results)
        """
        existing_pool = list(self.strategies.values())
        
        all_passed, results = await self.evolution_gates.validate_all_gates(
            candidate=candidate,
            backtest_results=backtest_results,
            existing_pool=existing_pool
        )
        
        for result in results:
            self.observability.log_event(SystemEvent(
                timestamp=time.time(),
                zone_origin=IsolationZone.ZONE_D_EVOLUTION,
                event_type=f"GATE_{result.gate_name.upper().replace(' ', '_')}",
                trigger_condition=f"{'PASSED' if result.passed else 'FAILED'}: {result.reason}",
                delta_applied=None,
                current_state_hash="",
                operator_id="automated"
            ))
        
        if all_passed:
            logger.info("Evolution candidate PASSED all 5 gates - eligible for human review")
        else:
            failed = [r.gate_name for r in results if not r.passed]
            logger.warning(f"Evolution candidate REJECTED - failed gates: {failed}")
        
        return all_passed, results
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ALETHEIA-INSPIRED LEARNING METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async def curate_training_sample(
        self,
        features: Dict[str, float],
        label: Optional[float],
        regime: RegimeLabel,
        quality_score: float
    ) -> Tuple[bool, str]:
        """
        Curate a training sample through Aletheia-inspired quality gates.
        
        Args:
            features: Feature dictionary
            label: Target label (if supervised)
            regime: Current market regime
            quality_score: Quality score [0-1]
            
        Returns:
            Tuple of (accepted, reason)
        """
        # Create data sample
        sample = DataSample(
            timestamp=time.time(),
            features=features,
            label=label,
            regime=regime,
            quality_score=quality_score,
            counterfactual_validated=False
        )
        
        # Get current regime distribution
        curation_stats = self.data_curation.get_statistics()
        current_distribution = curation_stats.get("regime_distribution", {})
        regime_dist = {RegimeLabel(k): v for k, v in current_distribution.items()}
        
        # Curate sample
        accepted, reason = self.data_curation.curate_sample(sample, regime_dist)
        
        if accepted:
            self.observability.log_event(SystemEvent(
                timestamp=time.time(),
                zone_origin=IsolationZone.ZONE_B_ADAPTATION,
                event_type="SAMPLE_CURATED",
                trigger_condition=f"Regime={regime.value}, Quality={quality_score:.2f}",
                delta_applied=None,
                current_state_hash="",
                operator_id="automated"
            ))
        
        return accepted, reason
    
    async def validate_sample_counterfactually(
        self,
        sample: DataSample,
        model: Any,
        intervention: Dict[str, float]
    ) -> CounterfactualResult:
        """
        Validate a training sample using counterfactual reasoning.
        
        Args:
            sample: Data sample to validate
            model: Prediction model
            intervention: Feature interventions to test causality
            
        Returns:
            CounterfactualResult with validation outcome
        """
        result = await self.counterfactual_validator.validate_counterfactual(
            sample=sample,
            model=model,
            intervention=intervention
        )
        
        # Update sample validation status
        sample.counterfactual_validated = result.passed
        
        # Log result
        self.observability.log_event(SystemEvent(
            timestamp=time.time(),
            zone_origin=IsolationZone.ZONE_B_ADAPTATION,
            event_type="COUNTERFACTUAL_VALIDATION",
            trigger_condition=f"{'PASSED' if result.passed else 'FAILED'}: Causal effect={result.causal_effect:.4f}",
            delta_applied=None,
            current_state_hash="",
            operator_id="automated"
        ))
        
        return result
    
    def get_regime_balanced_training_batch(
        self,
        batch_size: int,
        target_distribution: Optional[Dict[RegimeLabel, float]] = None
    ) -> List[DataSample]:
        """
        Get a regime-balanced batch for training.
        
        Args:
            batch_size: Number of samples
            target_distribution: Target regime distribution (defaults to uniform)
            
        Returns:
            List of balanced training samples
        """
        if target_distribution is None:
            # Default to uniform distribution
            target_distribution = {regime: 0.2 for regime in RegimeLabel}
        
        return self.data_curation.get_regime_balanced_batch(batch_size, target_distribution)
    
    async def propose_learning_update(
        self,
        proposed_update: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Propose a learning update through deterministic gating.
        
        All updates must pass:
        1. Counterfactual validation (70%+ pass rate)
        2. Sufficient curated samples (1000+)
        3. Rate limiting (max 4/hour)
        4. Performance degradation check
        5. Bounded magnitude
        
        Args:
            proposed_update: Proposed parameter update
            
        Returns:
            Tuple of (approved, bounded_update, reason)
        """
        # Compute current performance metrics
        current_metrics = self.performance_sensor.compute_metrics()
        
        # Gate the update
        approved, bounded_update, reason = await self.learning_controller.gate_learning_update(
            proposed_update=proposed_update,
            current_metrics=current_metrics
        )
        
        if approved:
            self.observability.log_event(SystemEvent(
                timestamp=time.time(),
                zone_origin=IsolationZone.ZONE_B_ADAPTATION,
                event_type="LEARNING_UPDATE_APPROVED",
                trigger_condition=reason,
                delta_applied=bounded_update,
                current_state_hash=self.snapshot_stack.get_latest().hash_value if self.snapshot_stack.get_latest() else "",
                operator_id="automated"
            ))
            logger.info(f"Learning update APPROVED: {reason}")
        else:
            self.observability.add_alert(
                "LEARNING_UPDATE_REJECTED",
                f"Update rejected: {reason}",
                severity="warning"
            )
            logger.warning(f"Learning update REJECTED: {reason}")
        
        return approved, bounded_update, reason
    
    def record_trading_return(self, return_value: float, regime: RegimeLabel):
        """
        Record a trading return for multi-metric performance sensing.
        
        Args:
            return_value: Return value (e.g., 0.01 for 1% return)
            regime: Market regime during this return
        """
        self.performance_sensor.record_return(return_value, regime)
    
    def compute_performance_metrics(self) -> PerformanceMetrics:
        """
        Compute comprehensive performance metrics.
        
        Returns:
            PerformanceMetrics with all computed metrics
        """
        return self.performance_sensor.compute_metrics()
    
    def set_performance_baseline(self, metrics: PerformanceMetrics):
        """
        Set baseline performance metrics for degradation detection.
        
        Args:
            metrics: Baseline performance metrics
        """
        self.performance_sensor.set_baseline(metrics)
        logger.info(f"Performance baseline set: Sharpe={metrics.sharpe_ratio:.2f}, MaxDD={metrics.max_drawdown:.2%}")
    
    def set_learning_mode(self, mode: str):
        """
        Set learning mode: conservative (0.1%), normal (0.5%), or aggressive (1.0%).
        
        Args:
            mode: Learning mode string
        """
        self.learning_controller.set_learning_mode(mode)
    
    def get_aletheia_status(self) -> Dict[str, Any]:
        """
        Get status of Aletheia-inspired learning system.
        
        Returns:
            Dict with learning system status
        """
        return {
            "learning_controller": self.learning_controller.get_status(),
            "curation_stats": self.data_curation.get_statistics(),
            "counterfactual_pass_rate": self.counterfactual_validator.get_validation_rate(),
            "current_metrics": self.performance_sensor.compute_metrics().__dict__,
            "timestamp": time.time()
        }


# Factory function for creating AlphaAlgo Core instances
def create_alphaalgo_core(config_path: Optional[str] = None) -> AlphaAlgoCore:
    """
    Create an AlphaAlgo Core instance with configuration from a file.
    
    Args:
        config_path: Path to configuration file (JSON)
        
    Returns:
        AlphaAlgoCore instance
    """
    config = {}
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            logger.info("Using default configuration")
    
    return AlphaAlgoCore(config)
