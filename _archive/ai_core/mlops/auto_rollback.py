"""
Automatic Rollback System for ML models
"""

import logging
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from typing import Set

logger = logging.getLogger(__name__)


@dataclass
class RollbackEvent:
    """Rollback event record."""
    timestamp: str
    model_id: str
    from_version: str
    to_version: str
    reason: str
    trigger_metric: str
    trigger_value: float


class AutoRollback:
    """
    Automatic rollback system for ML models.
    
    Features:
    - Automatic model rollback on performance degradation
    - Configurable rollback triggers
    - Rollback history tracking
    - Integration with performance monitoring
    """
    
    def __init__(
        self,
        model_registry: Any,
        performance_monitor: Any,
        rollback_triggers: Optional[Dict[str, float]] = None
    ):
        self.model_registry = model_registry
        self.performance_monitor = performance_monitor
        
        # Default rollback triggers
        self.rollback_triggers = rollback_triggers or {
            'accuracy_drop': 0.15,      # 15% accuracy drop
            'error_rate': 0.10,          # 10% error rate
            'latency_increase': 2.0,     # 2x latency increase
            'critical_alerts': 5         # 5 critical alerts
        }
        
        self.rollback_history: list[RollbackEvent] = []
        self.current_version: Optional[str] = None
        self.previous_version: Optional[str] = None
        
        logger.info("AutoRollback system initialized")
    
    def set_current_version(self, model_id: str, version: str):
        """Set the current model version."""
        self.previous_version = self.current_version
        self.current_version = f"{model_id}:{version}"
        logger.info(f"Current version set to {self.current_version}")
    
    def check_rollback_conditions(self, model_id: str) -> bool:
        """
        Check if rollback conditions are met.
        
        Args:
            model_id: Model identifier
        
        Returns:
            True if rollback should be triggered
        """
        stats = self.performance_monitor.get_statistics()
        
        # Check accuracy drop
        if 'accuracy' in stats:
            baseline = stats['accuracy'].get('baseline')
            current = stats['accuracy'].get('current')
            if baseline and current:
                accuracy_drop = baseline - current
                if accuracy_drop > self.rollback_triggers['accuracy_drop']:
                    logger.warning(
                        f"Accuracy drop {accuracy_drop:.2%} exceeds threshold "
                        f"{self.rollback_triggers['accuracy_drop']:.2%}"
                    )
                    return True
        
        # Check critical alerts
        if 'alerts' in stats:
            critical_count = stats['alerts'].get('critical', 0)
            if critical_count >= self.rollback_triggers['critical_alerts']:
                logger.warning(
                    f"Critical alerts {critical_count} exceeds threshold "
                    f"{self.rollback_triggers['critical_alerts']}"
                )
                return True
        
        # Check latency increase
        if 'latency' in stats:
            mean_latency = stats['latency'].get('mean', 0)
            # Compare with baseline (simplified - should track baseline)
            if mean_latency > 1000:  # Simple threshold
                logger.warning(f"High latency detected: {mean_latency:.2f}ms")
                return True
        
        return False
    
    def execute_rollback(
        self,
        model_id: str,
        reason: str,
        trigger_metric: str,
        trigger_value: float
    ) -> bool:
        """
        Execute model rollback to previous version.
        
        Args:
            model_id: Model identifier
            reason: Reason for rollback
            trigger_metric: Metric that triggered rollback
            trigger_value: Value of trigger metric
        
        Returns:
            True if rollback successful
        """
        if not self.previous_version:
            logger.error("No previous version available for rollback")
            return False
        try:
        
            # Extract version from previous_version string
            prev_model_id, prev_version = self.previous_version.split(':')
            
            # Load previous model
            previous_model = self.model_registry.load_model(prev_model_id, prev_version)
            
            # Record rollback event
            event = RollbackEvent(
                timestamp=datetime.now().isoformat(),
                model_id=model_id,
                from_version=self.current_version,
                to_version=self.previous_version,
                reason=reason,
                trigger_metric=trigger_metric,
                trigger_value=trigger_value
            )
            
            self.rollback_history.append(event)
            
            # Update current version
            self.current_version = self.previous_version
            
            logger.critical(
                f"ROLLBACK EXECUTED: {model_id} rolled back from "
                f"{event.from_version} to {event.to_version}. "
                f"Reason: {reason}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def monitor_and_rollback(self, model_id: str) -> bool:
        """
        Monitor performance and execute rollback if needed.
        
        Args:
            model_id: Model identifier
        
        Returns:
            True if rollback was executed
        """
        if self.check_rollback_conditions(model_id):
            stats = self.performance_monitor.get_statistics()
            
            # Determine trigger
            trigger_metric = "performance_degradation"
            trigger_value = 0.0
            
            if 'accuracy' in stats:
                baseline = stats['accuracy'].get('baseline', 0)
                current = stats['accuracy'].get('current', 0)
                trigger_metric = "accuracy_drop"
                trigger_value = baseline - current
            
            return self.execute_rollback(
                model_id=model_id,
                reason="Automatic rollback due to performance degradation",
                trigger_metric=trigger_metric,
                trigger_value=trigger_value
            )
        
        return False
    
    def get_rollback_history(self, limit: int = 10) -> list[RollbackEvent]:
        """Get recent rollback history."""
        return self.rollback_history[-limit:]
    
    def clear_history(self):
        """Clear rollback history."""
        self.rollback_history.clear()
        logger.info("Rollback history cleared")
