"""
Auto-Pause Manager

Coordinates all pause triggers and manages trading pause state.
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from enum import auto

logger = logging.getLogger(__name__)


class PauseReason(Enum):
    """Reasons for auto-pause."""
    DRIFT_DETECTED = "drift_detected"
    HIGH_LATENCY = "high_latency"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    MANUAL = "manual"
    NONE = "none"


@dataclass
class PauseState:
    """Current pause state."""
    is_paused: bool
    reason: PauseReason
    paused_at: Optional[datetime]
    resume_at: Optional[datetime]
    pause_count: int
    message: str


class AutoPauseManager:
    """
    Manages automatic trading pauses from multiple triggers.
    
    Pause triggers:
    - Drift detection (2+ features)
    - High latency (circuit breaker)
    - High CPU/memory (resource watchdog)
    - Consecutive losses (kill switch)
    - Manual pause file
    """
    
    def __init__(
        self,
        drift_cooldown_minutes: int = 120,
        latency_cooldown_minutes: int = 30,
        resource_cooldown_minutes: int = 60,
        manual_pause_file: str = "PAUSE_TRADING.txt"
    ):
        """
        Initialize auto-pause manager.
        
        Args:
            drift_cooldown_minutes: Cooldown after drift detection
            latency_cooldown_minutes: Cooldown after latency issues
            resource_cooldown_minutes: Cooldown after resource issues
            manual_pause_file: File to check for manual pause
        """
        try:
            self.drift_cooldown = timedelta(minutes=drift_cooldown_minutes)
            self.latency_cooldown = timedelta(minutes=latency_cooldown_minutes)
            self.resource_cooldown = timedelta(minutes=resource_cooldown_minutes)
            self.manual_pause_file = Path(manual_pause_file)
        
            self.is_paused = False
            self.current_reason = PauseReason.NONE
            self.paused_at: Optional[datetime] = None
            self.resume_at: Optional[datetime] = None
            self.pause_count = 0
            self.drift_alerts = 0
        
            logger.info(f"Auto-Pause Manager initialized:")
            logger.info(f"  Drift cooldown: {drift_cooldown_minutes} min")
            logger.info(f"  Latency cooldown: {latency_cooldown_minutes} min")
            logger.info(f"  Resource cooldown: {resource_cooldown_minutes} min")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check_drift_trigger(self, drifted_features: List[str]) -> bool:
        """
        Check if drift should trigger pause.
        
        Args:
            drifted_features: List of features with detected drift
        
        Returns:
            True if pause triggered
        """
        try:
            if len(drifted_features) >= 2:
                self.drift_alerts += 1
                logger.warning(f"Drift alert #{self.drift_alerts}: {len(drifted_features)} features")
            
                if self.drift_alerts >= 2:
                    self._trigger_pause(
                        PauseReason.DRIFT_DETECTED,
                        self.drift_cooldown,
                        f"Drift detected in {len(drifted_features)} features: {', '.join(drifted_features)}"
                    )
                    return True
            else:
                self.drift_alerts = 0
        
            return False
        except Exception as e:
            logger.error(f"Error in check_drift_trigger: {e}")
            raise
    
    def check_latency_trigger(self, latency_ms: float, threshold: float) -> bool:
        """
        Check if latency should trigger pause.
        
        Args:
            latency_ms: Current latency
            threshold: Latency threshold
        
        Returns:
            True if pause triggered
        """
        try:
            if latency_ms > threshold * 2:  # Critical latency
                self._trigger_pause(
                    PauseReason.HIGH_LATENCY,
                    self.latency_cooldown,
                    f"Critical latency: {latency_ms:.0f}ms (threshold: {threshold:.0f}ms)"
                )
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in check_latency_trigger: {e}")
            raise
    
    def check_resource_trigger(self, cpu_percent: float, memory_percent: float) -> bool:
        """
        Check if resources should trigger pause.
        
        Args:
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
        
        Returns:
            True if pause triggered
        """
        try:
            if cpu_percent > 90 or memory_percent > 90:
                reason = PauseReason.HIGH_CPU if cpu_percent > 90 else PauseReason.HIGH_MEMORY
                self._trigger_pause(
                    reason,
                    self.resource_cooldown,
                    f"Critical resources: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%"
                )
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in check_resource_trigger: {e}")
            raise
    
    def check_manual_trigger(self) -> bool:
        """
        Check if manual pause file exists.
        
        Returns:
            True if pause triggered
        """
        try:
            if self.manual_pause_file.exists():
                if not self.is_paused or self.current_reason != PauseReason.MANUAL:
                    self._trigger_pause(
                        PauseReason.MANUAL,
                        None,  # No auto-resume for manual pause
                        f"Manual pause file detected: {self.manual_pause_file}"
                    )
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in check_manual_trigger: {e}")
            raise
    
    def _trigger_pause(
        self,
        reason: PauseReason,
        cooldown: Optional[timedelta],
        message: str
    ):
        """Trigger a pause."""
        try:
            if self.is_paused and self.current_reason == reason:
                return  # Already paused for this reason
        
            self.is_paused = True
            self.current_reason = reason
            self.paused_at = datetime.utcnow()
            self.pause_count += 1
        
            if cooldown:
                self.resume_at = self.paused_at + cooldown
            else:
                self.resume_at = None
        
            logger.warning("=" * 80)
            logger.warning(f"⏸️  AUTO-PAUSE TRIGGERED (#{self.pause_count})")
            logger.warning(f"Reason: {reason.value}")
            logger.warning(f"Message: {message}")
            if self.resume_at:
                logger.warning(f"Auto-resume at: {self.resume_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            else:
                logger.warning("Manual resume required")
            logger.warning("=" * 80)
        except Exception as e:
            logger.error(f"Error in _trigger_pause: {e}")
            raise
    
    def check_auto_resume(self) -> bool:
        """
        Check if auto-resume conditions are met.
        
        Returns:
            True if resumed
        """
        try:
            if not self.is_paused:
                return False
        
            # Manual pause requires manual resume
            if self.current_reason == PauseReason.MANUAL:
                if not self.manual_pause_file.exists():
                    self._resume("Manual pause file removed")
                    return True
                return False
        
            # Check cooldown
            if self.resume_at and datetime.utcnow() >= self.resume_at:
                self._resume(f"Cooldown period expired ({self.current_reason.value})")
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in check_auto_resume: {e}")
            raise
    
    def _resume(self, message: str):
        """Resume trading."""
        try:
            logger.info("=" * 80)
            logger.info("▶️  AUTO-RESUME")
            logger.info(f"Message: {message}")
            logger.info(f"Was paused for: {self.current_reason.value}")
            logger.info("=" * 80)
        
            self.is_paused = False
            self.current_reason = PauseReason.NONE
            self.paused_at = None
            self.resume_at = None
            self.drift_alerts = 0
        except Exception as e:
            logger.error(f"Error in _resume: {e}")
            raise
    
    def force_resume(self):
        """Force resume (use with caution)."""
        try:
            if self.is_paused:
                logger.warning("Forcing resume from pause state")
                self._resume("Forced resume")
            
                # Remove manual pause file if exists
                if self.manual_pause_file.exists():
                    self.manual_pause_file.unlink()
                    logger.info(f"Removed manual pause file: {self.manual_pause_file}")
        except Exception as e:
            logger.error(f"Error in force_resume: {e}")
            raise
    
    def get_state(self) -> PauseState:
        """Get current pause state."""
        return PauseState(
            is_paused=self.is_paused,
            reason=self.current_reason,
            paused_at=self.paused_at,
            resume_at=self.resume_at,
            pause_count=self.pause_count,
            message=self._get_status_message()
        )
    
    def _get_status_message(self) -> str:
        """Get human-readable status message."""
        try:
            if not self.is_paused:
                return "Trading active"
        
            msg = f"Trading paused: {self.current_reason.value}"
        
            if self.resume_at:
                remaining = (self.resume_at - datetime.utcnow()).total_seconds() / 60
                if remaining > 0:
                    msg += f" (resume in {remaining:.0f} min)"
                else:
                    msg += " (ready to resume)"
            else:
                msg += " (manual resume required)"
        
            return msg
        except Exception as e:
            logger.error(f"Error in _get_status_message: {e}")
            raise
    
    def should_allow_trading(self) -> bool:
        """
        Check if trading should be allowed.
        
        Returns:
            True if trading allowed, False if paused
        """
        # Check auto-resume
        try:
            self.check_auto_resume()
        
            # Check manual trigger
            self.check_manual_trigger()
        
            return not self.is_paused
        except Exception as e:
            logger.error(f"Error in should_allow_trading: {e}")
            raise
