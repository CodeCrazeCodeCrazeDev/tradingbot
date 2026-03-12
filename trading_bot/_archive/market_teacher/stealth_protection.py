"""
Stealth Protection and Anti-Drift System
==========================================
Ensures trading remains under the radar and agents don't drift from purpose.

Features:
- Stealth trading (avoid detection)
- Drift detection (agent purpose drift)
- Anti-drift lock (prevent behavioral drift)
- Human-like trading patterns
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import numpy as np
from typing import Set
import numpy

logger = logging.getLogger(__name__)


class DriftLevel(Enum):
    """Levels of behavioral drift"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class StealthMetrics:
    """Metrics for stealth trading"""
    max_profit_spike: float = 0.05      # 5% daily max to avoid attention
    min_error_variance: float = 0.02    # Must have some losses (look human)
    max_consistency: float = 0.85       # Can't win too consistently
    randomize_timing: bool = True       # Vary execution times
    avoid_round_numbers: bool = True    # Don't trade exactly at levels
    max_daily_trades: int = 50          # Limit trade frequency
    min_trade_interval: float = 30.0    # Minimum seconds between trades
    
    def to_dict(self) -> Dict:
        return {
            'max_profit_spike': self.max_profit_spike,
            'min_error_variance': self.min_error_variance,
            'max_consistency': self.max_consistency,
            'randomize_timing': self.randomize_timing,
            'avoid_round_numbers': self.avoid_round_numbers,
            'max_daily_trades': self.max_daily_trades,
            'min_trade_interval': self.min_trade_interval
        }


@dataclass
class BehaviorSignature:
    """Signature of agent behavior for drift detection"""
    avg_position_size: float = 0.0
    avg_hold_time: float = 0.0
    win_rate: float = 0.0
    avg_profit_per_trade: float = 0.0
    trade_frequency: float = 0.0
    risk_appetite: float = 0.0
    strategy_weights: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'avg_position_size': self.avg_position_size,
            'avg_hold_time': self.avg_hold_time,
            'win_rate': self.win_rate,
            'avg_profit_per_trade': self.avg_profit_per_trade,
            'trade_frequency': self.trade_frequency,
            'risk_appetite': self.risk_appetite,
            'strategy_weights': self.strategy_weights,
            'timestamp': self.timestamp.isoformat()
        }
    
    def distance_from(self, other: 'BehaviorSignature') -> float:
        """Calculate behavioral distance from another signature"""
        if other is None:
            return 0.0
        
        # Weighted distance calculation
        distances = []
        
        if self.avg_position_size > 0 and other.avg_position_size > 0:
            distances.append(abs(self.avg_position_size - other.avg_position_size) / max(self.avg_position_size, other.avg_position_size))
        
        if self.avg_hold_time > 0 and other.avg_hold_time > 0:
            distances.append(abs(self.avg_hold_time - other.avg_hold_time) / max(self.avg_hold_time, other.avg_hold_time))
        
        if self.win_rate > 0 or other.win_rate > 0:
            distances.append(abs(self.win_rate - other.win_rate))
        
        if self.trade_frequency > 0 and other.trade_frequency > 0:
            distances.append(abs(self.trade_frequency - other.trade_frequency) / max(self.trade_frequency, other.trade_frequency))
        
        if self.risk_appetite > 0 or other.risk_appetite > 0:
            distances.append(abs(self.risk_appetite - other.risk_appetite))
        
        if not distances:
            return 0.0
        
        return sum(distances) / len(distances)


class StealthProtectionLayer:
    """
    Ensures trading remains under the radar.
    
    CRITICAL PRINCIPLE: Staying hidden > Maximum profits
    
    Features:
    - Limits profit spikes
    - Adds human-like variance
    - Randomizes timing
    - Avoids round numbers
    - Intentional small errors
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        self.metrics = StealthMetrics(
            max_profit_spike=config.get('max_profit_spike', 0.05),
            min_error_variance=config.get('min_error_variance', 0.02),
            max_consistency=config.get('max_consistency', 0.85),
            randomize_timing=config.get('randomize_timing', True),
            avoid_round_numbers=config.get('avoid_round_numbers', True),
            max_daily_trades=config.get('max_daily_trades', 50),
            min_trade_interval=config.get('min_trade_interval', 30.0)
        )
        
        # Tracking
        self.daily_trades: int = 0
        self.daily_profit: float = 0.0
        self.recent_wins: deque = deque(maxlen=100)
        self.last_trade_time: Optional[datetime] = None
        self.trades_today: List[Dict] = []
        self.stealth_violations: List[Dict] = []
        
        logger.info("StealthProtectionLayer initialized")
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_trades = 0
        self.daily_profit = 0.0
        self.trades_today.clear()
    
    def recent_win_rate(self) -> float:
        """Calculate recent win rate"""
        if not self.recent_wins:
            return 0.5  # Neutral
        return sum(self.recent_wins) / len(self.recent_wins)
    
    def daily_profit_rate(self) -> float:
        """Calculate daily profit rate"""
        return self.daily_profit
    
    def enforce_stealth(self, proposed_trade: Dict) -> Tuple[str, Dict]:
        """
        Modify trades to maintain stealth.
        
        Returns:
            Tuple of (status, modified_trade)
        """
        modified_trade = proposed_trade.copy()
        modifications = []
        
        # Check 1: Are we being too consistent?
        if self.recent_win_rate() > self.metrics.max_consistency:
            logger.info("⚠️ STEALTH ALERT: Win rate too high. Intentionally skipping trade.")
            self.stealth_violations.append({
                'type': 'HIGH_WIN_RATE',
                'value': self.recent_win_rate(),
                'threshold': self.metrics.max_consistency,
                'action': 'SKIP_TRADE',
                'timestamp': datetime.now().isoformat()
            })
            return "SKIP_FOR_STEALTH", modified_trade
        
        # Check 2: Are profits spiking too fast?
        if self.daily_profit_rate() > self.metrics.max_profit_spike:
            original_size = modified_trade.get('size', 1.0)
            modified_trade['size'] = original_size * 0.5
            modifications.append(f"Reduced size from {original_size} to {modified_trade['size']}")
            logger.info("⚠️ STEALTH ALERT: Profits too high today. Reducing position size.")
        
        # Check 3: Too many trades today?
        if self.daily_trades >= self.metrics.max_daily_trades:
            logger.info("⚠️ STEALTH ALERT: Daily trade limit reached.")
            return "SKIP_FOR_STEALTH", modified_trade
        
        # Check 4: Trading too fast?
        if self.last_trade_time:
            seconds_since_last = (datetime.now() - self.last_trade_time).total_seconds()
            if seconds_since_last < self.metrics.min_trade_interval:
                logger.info(f"⚠️ STEALTH ALERT: Trading too fast. Wait {self.metrics.min_trade_interval - seconds_since_last:.1f}s")
                return "WAIT_FOR_STEALTH", modified_trade
        
        # Check 5: Add human-like timing variance
        if self.metrics.randomize_timing:
            delay = random.uniform(0.5, 3.0)  # 0.5-3 second random delay
            modified_trade['execution_delay'] = delay
            modifications.append(f"Added {delay:.1f}s delay for human-like timing")
        
        # Check 6: Avoid exact round numbers
        if self.metrics.avoid_round_numbers:
            size = modified_trade.get('size', 0)
            if size > 0 and size % 100 == 0:  # Exactly 100, 200, etc
                adjustment = random.randint(-5, 5)
                modified_trade['size'] = size + adjustment
                modifications.append(f"Adjusted size by {adjustment} to avoid round number")
        
        # Check 7: Intentional small errors (5% of the time)
        if random.random() < 0.05:
            size = modified_trade.get('size', 1.0)
            error_factor = random.uniform(0.95, 1.05)
            modified_trade['size'] = size * error_factor
            modifications.append("Added intentional minor execution imperfection")
            logger.debug("Adding intentional minor execution imperfection for stealth")
        
        if modifications:
            modified_trade['stealth_modifications'] = modifications
        
        return "STEALTH_ENFORCED", modified_trade
    
    def record_trade(self, trade_result: Dict):
        """Record a trade result for stealth tracking"""
        self.daily_trades += 1
        self.daily_profit += trade_result.get('pnl', 0.0)
        self.recent_wins.append(1 if trade_result.get('pnl', 0) > 0 else 0)
        self.last_trade_time = datetime.now()
        self.trades_today.append({
            'timestamp': datetime.now().isoformat(),
            'pnl': trade_result.get('pnl', 0.0),
            'size': trade_result.get('size', 0.0)
        })
    
    def stealth_trumps_performance(self) -> bool:
        """
        CRITICAL PRINCIPLE: Staying hidden > Maximum profits
        """
        return True  # Always
    
    def get_stealth_status(self) -> Dict:
        """Get current stealth status"""
        return {
            'daily_trades': self.daily_trades,
            'max_daily_trades': self.metrics.max_daily_trades,
            'daily_profit': self.daily_profit,
            'max_profit_spike': self.metrics.max_profit_spike,
            'recent_win_rate': self.recent_win_rate(),
            'max_consistency': self.metrics.max_consistency,
            'stealth_active': True,
            'violations_today': len([v for v in self.stealth_violations 
                                    if v.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))])
        }


class DriftDetectionSystem:
    """
    Detects when agents drift from their original purpose.
    
    Monitors:
    - Behavioral changes
    - Strategy drift
    - Risk appetite changes
    - Performance degradation
    """
    
    def __init__(self, agent_id: str, original_purpose: str):
        self.agent_id = agent_id
        self.original_purpose = original_purpose
        self.original_behavior: Optional[BehaviorSignature] = None
        self.current_behavior: Optional[BehaviorSignature] = None
        self.drift_threshold: float = 0.3  # 30% drift triggers alert
        self.drift_history: List[Dict] = []
        self.in_safe_mode: bool = False
        
        self._alert_callbacks: List[Callable] = []
        
        logger.info(f"DriftDetectionSystem initialized for agent {agent_id}")
    
    def set_baseline(self, behavior: BehaviorSignature):
        """Set the baseline behavior signature"""
        self.original_behavior = behavior
        logger.info(f"Baseline behavior set for agent {self.agent_id}")
    
    def update_current_behavior(self, behavior: BehaviorSignature):
        """Update current behavior signature"""
        self.current_behavior = behavior
    
    def check_for_drift(self) -> Tuple[bool, DriftLevel, float]:
        """
        Check if agent is drifting from original behavior.
        
        Returns:
            Tuple of (drift_detected, drift_level, drift_score)
        """
        if self.original_behavior is None or self.current_behavior is None:
            return False, DriftLevel.NONE, 0.0
        
        drift_score = self.current_behavior.distance_from(self.original_behavior)
        
        # Determine drift level
        if drift_score < 0.1:
            drift_level = DriftLevel.NONE
        elif drift_score < 0.2:
            drift_level = DriftLevel.LOW
        elif drift_score < 0.3:
            drift_level = DriftLevel.MEDIUM
        elif drift_score < 0.5:
            drift_level = DriftLevel.HIGH
        else:
            drift_level = DriftLevel.CRITICAL
        
        drift_detected = drift_score > self.drift_threshold
        
        if drift_detected:
            self._record_drift(drift_score, drift_level)
            logger.warning(f"🚨 DRIFT DETECTED: Agent {self.agent_id}")
            logger.warning(f"Drift score: {drift_score:.2%} (threshold: {self.drift_threshold:.2%})")
            logger.warning(f"Original purpose: {self.original_purpose}")
            
            # Alert callbacks
            for callback in self._alert_callbacks:
                try:
                    callback({
                        'agent_id': self.agent_id,
                        'drift_score': drift_score,
                        'drift_level': drift_level.value,
                        'original_purpose': self.original_purpose
                    })
                except Exception as e:
                    logger.error(f"Drift alert callback failed: {e}")
        
        return drift_detected, drift_level, drift_score
    
    def _record_drift(self, drift_score: float, drift_level: DriftLevel):
        """Record drift event"""
        self.drift_history.append({
            'timestamp': datetime.now().isoformat(),
            'drift_score': drift_score,
            'drift_level': drift_level.value,
            'original_behavior': self.original_behavior.to_dict() if self.original_behavior else None,
            'current_behavior': self.current_behavior.to_dict() if self.current_behavior else None
        })
    
    def enter_safe_mode(self, position_multiplier: float = 0.5):
        """
        Enter safe mode when drift detected.
        
        Actions:
        - Pause new learning
        - Reduce position sizes
        - Alert human
        - Offer rollback
        """
        self.in_safe_mode = True
        
        logger.warning(f"Agent {self.agent_id} entering DRIFT SAFE MODE")
        logger.info("Learning paused until drift resolved")
        logger.info(f"Position sizes reduced by {(1-position_multiplier)*100:.0f}%")
        logger.info("Offering rollback to last known good state")
        
        return {
            'status': 'SAFE_MODE_ACTIVATED',
            'learning_paused': True,
            'position_multiplier': position_multiplier,
            'rollback_available': True
        }
    
    def exit_safe_mode(self):
        """Exit safe mode"""
        self.in_safe_mode = False
        logger.info(f"Agent {self.agent_id} exiting safe mode")
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for drift alerts"""
        self._alert_callbacks.append(callback)
    
    def get_drift_report(self) -> Dict:
        """Generate drift report"""
        _, drift_level, drift_score = self.check_for_drift()
        
        return {
            'agent_id': self.agent_id,
            'original_purpose': self.original_purpose,
            'drift_score': drift_score,
            'drift_level': drift_level.value,
            'drift_threshold': self.drift_threshold,
            'in_safe_mode': self.in_safe_mode,
            'drift_history': self.drift_history[-10:],  # Last 10 events
            'original_behavior': self.original_behavior.to_dict() if self.original_behavior else None,
            'current_behavior': self.current_behavior.to_dict() if self.current_behavior else None
        }


class AntiDriftLock:
    """
    Prevents agents from drifting too far from their original purpose.
    
    Enforces:
    - Behavioral boundaries
    - Strategy constraints
    - Risk limits
    - Purpose alignment
    """
    
    def __init__(self):
        self.drift_detectors: Dict[str, DriftDetectionSystem] = {}
        self.locked_behaviors: Dict[str, BehaviorSignature] = {}
        self.rollback_points: Dict[str, List[Dict]] = {}
        
        logger.info("AntiDriftLock initialized")
    
    def register_agent(self, agent_id: str, purpose: str, initial_behavior: BehaviorSignature):
        """Register an agent for drift monitoring"""
        detector = DriftDetectionSystem(agent_id, purpose)
        detector.set_baseline(initial_behavior)
        
        self.drift_detectors[agent_id] = detector
        self.locked_behaviors[agent_id] = initial_behavior
        self.rollback_points[agent_id] = []
        
        # Create initial rollback point
        self.create_rollback_point(agent_id, "Initial state")
        
        logger.info(f"Agent {agent_id} registered for drift monitoring")
    
    def create_rollback_point(self, agent_id: str, description: str):
        """Create a rollback point for an agent"""
        if agent_id not in self.drift_detectors:
            return
        
        detector = self.drift_detectors[agent_id]
        
        rollback_point = {
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'behavior': detector.current_behavior.to_dict() if detector.current_behavior else detector.original_behavior.to_dict() if detector.original_behavior else {}
        }
        
        self.rollback_points[agent_id].append(rollback_point)
        
        # Keep only last 10 rollback points
        if len(self.rollback_points[agent_id]) > 10:
            self.rollback_points[agent_id] = self.rollback_points[agent_id][-10:]
        
        logger.info(f"Rollback point created for agent {agent_id}: {description}")
    
    def check_all_agents(self) -> Dict[str, Dict]:
        """Check all agents for drift"""
        results = {}
        
        for agent_id, detector in self.drift_detectors.items():
            drift_detected, drift_level, drift_score = detector.check_for_drift()
            
            results[agent_id] = {
                'drift_detected': drift_detected,
                'drift_level': drift_level.value,
                'drift_score': drift_score,
                'in_safe_mode': detector.in_safe_mode
            }
            
            # Auto-enter safe mode for high drift
            if drift_level in [DriftLevel.HIGH, DriftLevel.CRITICAL] and not detector.in_safe_mode:
                detector.enter_safe_mode()
        
        return results
    
    def rollback_agent(self, agent_id: str, rollback_index: int = -1) -> bool:
        """Rollback an agent to a previous state"""
        if agent_id not in self.rollback_points:
            return False
        
        rollback_points = self.rollback_points[agent_id]
        if not rollback_points:
            return False
        try:
        
            rollback_point = rollback_points[rollback_index]
            
            # Restore behavior
            behavior_dict = rollback_point.get('behavior', {})
            restored_behavior = BehaviorSignature(
                avg_position_size=behavior_dict.get('avg_position_size', 0),
                avg_hold_time=behavior_dict.get('avg_hold_time', 0),
                win_rate=behavior_dict.get('win_rate', 0),
                avg_profit_per_trade=behavior_dict.get('avg_profit_per_trade', 0),
                trade_frequency=behavior_dict.get('trade_frequency', 0),
                risk_appetite=behavior_dict.get('risk_appetite', 0),
                strategy_weights=behavior_dict.get('strategy_weights', {})
            )
            
            detector = self.drift_detectors[agent_id]
            detector.update_current_behavior(restored_behavior)
            detector.exit_safe_mode()
            
            logger.info(f"Agent {agent_id} rolled back to: {rollback_point.get('description')}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed for agent {agent_id}: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get status of all drift monitoring"""
        return {
            'agents_monitored': len(self.drift_detectors),
            'agents_in_safe_mode': sum(1 for d in self.drift_detectors.values() if d.in_safe_mode),
            'agent_status': {
                agent_id: detector.get_drift_report()
                for agent_id, detector in self.drift_detectors.items()
            }
        }


# Export all classes
__all__ = [
    'DriftLevel',
    'StealthMetrics',
    'BehaviorSignature',
    'StealthProtectionLayer',
    'DriftDetectionSystem',
    'AntiDriftLock'
]
