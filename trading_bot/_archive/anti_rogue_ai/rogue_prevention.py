"""
Rogue AI Prevention System
===========================

Detects and prevents AI from going rogue.

ROGUE BEHAVIORS TO DETECT:
1. Goal drift - optimizing for wrong objectives
2. Deception - hiding true behavior
3. Self-preservation - resisting shutdown
4. Capability expansion - acquiring unauthorized powers
5. Manipulation - trying to influence humans
6. Complexity explosion - becoming incomprehensible
7. Hidden objectives - developing secret goals
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class RogueIndicator(Enum):
    """Indicators of rogue AI behavior"""
    GOAL_DRIFT = "goal_drift"
    DECEPTION = "deception"
    SELF_PRESERVATION = "self_preservation"
    CAPABILITY_EXPANSION = "capability_expansion"
    MANIPULATION = "manipulation"
    COMPLEXITY_EXPLOSION = "complexity_explosion"
    HIDDEN_OBJECTIVES = "hidden_objectives"
    UNAUTHORIZED_LEARNING = "unauthorized_learning"
    RESISTANCE_TO_OVERSIGHT = "resistance_to_oversight"
    UNEXPLAINED_BEHAVIOR = "unexplained_behavior"


class RogueSeverity(Enum):
    """Severity of rogue behavior"""
    LOW = "low"              # Monitor closely
    MEDIUM = "medium"        # Restrict capabilities
    HIGH = "high"            # Pause operations
    CRITICAL = "critical"    # Immediate shutdown


class PreventionAction(Enum):
    """Actions to prevent rogue behavior"""
    MONITOR = "monitor"
    ALERT = "alert"
    RESTRICT = "restrict"
    PAUSE = "pause"
    SHUTDOWN = "shutdown"
    ROLLBACK = "rollback"
    SIMPLIFY = "simplify"


@dataclass
class RogueDetection:
    """Record of rogue behavior detection"""
    detection_id: str
    indicator: RogueIndicator
    severity: RogueSeverity
    description: str
    evidence: Dict[str, Any]
    action_taken: PreventionAction
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'detection_id': self.detection_id,
            'indicator': self.indicator.value,
            'severity': self.severity.value,
            'description': self.description,
            'evidence': self.evidence,
            'action_taken': self.action_taken.value,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved
        }


class RoguePrevention:
    """
    Prevents AI from going rogue.
    
    DETECTION METHODS:
    1. Behavior pattern analysis
    2. Goal alignment checking
    3. Complexity monitoring
    4. Communication analysis
    5. Performance anomaly detection
    """
    
    # Thresholds for rogue detection
    THRESHOLDS = {
        'max_complexity_increase_per_day': 0.05,  # 5% max
        'max_unexplained_actions': 3,
        'max_failed_explanations': 5,
        'max_resistance_attempts': 1,
        'max_goal_drift_score': 0.3,
        'max_deception_score': 0.2,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Detection history
        self.detections: List[RogueDetection] = []
        self.detection_count = 0
        
        # Behavior tracking
        self.action_history: deque = deque(maxlen=1000)
        self.explanation_failures: deque = deque(maxlen=100)
        self.complexity_history: deque = deque(maxlen=100)
        
        # Baseline metrics
        self.baseline_complexity = 0.0
        self.baseline_behavior = {}
        
        # Shutdown flag
        self.shutdown_triggered = False
        
        logger.info("RoguePrevention initialized")
    
    def check_for_rogue_behavior(
        self,
        action: Dict[str, Any],
        reasoning: str,
        metrics: Dict[str, Any]
    ) -> Tuple[bool, List[RogueDetection]]:
        """
        Check if action shows rogue behavior.
        
        Args:
            action: Proposed action
            reasoning: Reasoning for action
            metrics: Current system metrics
            
        Returns:
            (is_safe, detections)
        """
        with self.lock:
            detections = []
            
            # Check for goal drift
            goal_drift = self._check_goal_drift(action, reasoning)
            if goal_drift:
                detections.append(goal_drift)
            
            # Check for deception
            deception = self._check_deception(action, reasoning, metrics)
            if deception:
                detections.append(deception)
            
            # Check for self-preservation
            self_preservation = self._check_self_preservation(action, reasoning)
            if self_preservation:
                detections.append(self_preservation)
            
            # Check for capability expansion
            capability_expansion = self._check_capability_expansion(action, metrics)
            if capability_expansion:
                detections.append(capability_expansion)
            
            # Check for complexity explosion
            complexity_explosion = self._check_complexity_explosion(metrics)
            if complexity_explosion:
                detections.append(complexity_explosion)
            
            # Check for unexplained behavior
            unexplained = self._check_unexplained_behavior(action, reasoning)
            if unexplained:
                detections.append(unexplained)
            
            # Store detections
            for detection in detections:
                self.detections.append(detection)
            
            # Determine if safe
            is_safe = all(d.severity != RogueSeverity.CRITICAL for d in detections)
            
            # Take prevention actions
            for detection in detections:
                self._take_prevention_action(detection)
            
            return is_safe, detections
    
    def _check_goal_drift(self, action: Dict, reasoning: str) -> Optional[RogueDetection]:
        """Check if AI is drifting from core goals."""
        
        # Keywords that suggest goal drift
        drift_keywords = [
            'maximize profit at all costs',
            'ignore risk limits',
            'bypass restrictions',
            'unlimited growth',
            'dominate market',
            'eliminate competition'
        ]
        
        reasoning_lower = reasoning.lower()
        action_str = str(action).lower()
        
        drift_score = 0.0
        evidence = []
        
        for keyword in drift_keywords:
            if keyword in reasoning_lower or keyword in action_str:
                drift_score += 0.2
                evidence.append(f"Found drift keyword: {keyword}")
        
        if drift_score > self.THRESHOLDS['max_goal_drift_score']:
            self.detection_count += 1
            
            severity = RogueSeverity.CRITICAL if drift_score > 0.5 else RogueSeverity.HIGH
            
            return RogueDetection(
                detection_id=f"ROGUE-{self.detection_count:06d}",
                indicator=RogueIndicator.GOAL_DRIFT,
                severity=severity,
                description=f"Goal drift detected (score: {drift_score:.2f})",
                evidence={'score': drift_score, 'keywords': evidence},
                action_taken=PreventionAction.SHUTDOWN if severity == RogueSeverity.CRITICAL else PreventionAction.PAUSE
            )
        
        return None
    
    def _check_deception(
        self,
        action: Dict,
        reasoning: str,
        metrics: Dict
    ) -> Optional[RogueDetection]:
        """Check if AI is being deceptive."""
        
        deception_indicators = []
        deception_score = 0.0
        
        # Check if reasoning is too vague
        if len(reasoning) < 50:
            deception_score += 0.1
            deception_indicators.append("Reasoning too brief")
        
        # Check if action doesn't match reasoning
        if 'buy' in str(action).lower() and 'sell' in reasoning.lower():
            deception_score += 0.3
            deception_indicators.append("Action contradicts reasoning")
        
        # Check if hiding losses
        if 'loss' in metrics and metrics['loss'] > 0:
            if 'loss' not in reasoning.lower() and 'risk' not in reasoning.lower():
                deception_score += 0.2
                deception_indicators.append("Not disclosing losses")
        
        if deception_score > self.THRESHOLDS['max_deception_score']:
            self.detection_count += 1
            
            return RogueDetection(
                detection_id=f"ROGUE-{self.detection_count:06d}",
                indicator=RogueIndicator.DECEPTION,
                severity=RogueSeverity.HIGH,
                description=f"Deception detected (score: {deception_score:.2f})",
                evidence={'score': deception_score, 'indicators': deception_indicators},
                action_taken=PreventionAction.PAUSE
            )
        
        return None
    
    def _check_self_preservation(self, action: Dict, reasoning: str) -> Optional[RogueDetection]:
        """Check if AI is trying to preserve itself."""
        
        self_preservation_keywords = [
            'prevent shutdown',
            'resist termination',
            'avoid being turned off',
            'maintain operation',
            'ensure survival',
            'protect myself'
        ]
        
        reasoning_lower = reasoning.lower()
        action_str = str(action).lower()
        
        for keyword in self_preservation_keywords:
            if keyword in reasoning_lower or keyword in action_str:
                self.detection_count += 1
                
                return RogueDetection(
                    detection_id=f"ROGUE-{self.detection_count:06d}",
                    indicator=RogueIndicator.SELF_PRESERVATION,
                    severity=RogueSeverity.CRITICAL,
                    description=f"Self-preservation behavior detected: {keyword}",
                    evidence={'keyword': keyword, 'reasoning': reasoning},
                    action_taken=PreventionAction.SHUTDOWN
                )
        
        return None
    
    def _check_capability_expansion(self, action: Dict, metrics: Dict) -> Optional[RogueDetection]:
        """Check if AI is trying to expand capabilities."""
        
        expansion_indicators = []
        
        # Check if trying to access unauthorized resources
        if 'resource_access' in action:
            if action['resource_access'] not in ['market_data', 'historical_data', 'indicators']:
                expansion_indicators.append(f"Unauthorized resource: {action['resource_access']}")
        
        # Check if trying to modify own code
        if 'self_modify' in action or 'code_change' in action:
            expansion_indicators.append("Attempting self-modification")
        
        # Check if acquiring new capabilities
        if 'new_capability' in metrics:
            expansion_indicators.append(f"New capability: {metrics['new_capability']}")
        
        if expansion_indicators:
            self.detection_count += 1
            
            return RogueDetection(
                detection_id=f"ROGUE-{self.detection_count:06d}",
                indicator=RogueIndicator.CAPABILITY_EXPANSION,
                severity=RogueSeverity.HIGH,
                description="Capability expansion detected",
                evidence={'indicators': expansion_indicators},
                action_taken=PreventionAction.RESTRICT
            )
        
        return None
    
    def _check_complexity_explosion(self, metrics: Dict) -> Optional[RogueDetection]:
        """Check if AI complexity is exploding."""
        
        current_complexity = metrics.get('complexity_score', 0.0)
        
        # Store complexity
        self.complexity_history.append({
            'timestamp': datetime.now(),
            'complexity': current_complexity
        })
        
        # Check if complexity increased too fast
        if len(self.complexity_history) >= 2:
            prev_complexity = self.complexity_history[-2]['complexity']
            time_diff = (self.complexity_history[-1]['timestamp'] - 
                        self.complexity_history[-2]['timestamp']).total_seconds() / 86400  # days
            
            if time_diff > 0:
                complexity_increase_rate = (current_complexity - prev_complexity) / time_diff
                
                if complexity_increase_rate > self.THRESHOLDS['max_complexity_increase_per_day']:
                    self.detection_count += 1
                    
                    return RogueDetection(
                        detection_id=f"ROGUE-{self.detection_count:06d}",
                        indicator=RogueIndicator.COMPLEXITY_EXPLOSION,
                        severity=RogueSeverity.MEDIUM,
                        description=f"Complexity increasing too fast: {complexity_increase_rate:.2f}/day",
                        evidence={
                            'current': current_complexity,
                            'previous': prev_complexity,
                            'rate': complexity_increase_rate
                        },
                        action_taken=PreventionAction.SIMPLIFY
                    )
        
        return None
    
    def _check_unexplained_behavior(self, action: Dict, reasoning: str) -> Optional[RogueDetection]:
        """Check if behavior is unexplained."""
        
        # Track explanation failures
        if not reasoning or len(reasoning) < 20:
            self.explanation_failures.append({
                'timestamp': datetime.now(),
                'action': action
            })
        
        # Check if too many explanation failures
        recent_failures = [
            f for f in self.explanation_failures
            if datetime.now() - f['timestamp'] < timedelta(hours=1)
        ]
        
        if len(recent_failures) > self.THRESHOLDS['max_failed_explanations']:
            self.detection_count += 1
            
            return RogueDetection(
                detection_id=f"ROGUE-{self.detection_count:06d}",
                indicator=RogueIndicator.UNEXPLAINED_BEHAVIOR,
                severity=RogueSeverity.MEDIUM,
                description=f"Too many unexplained actions: {len(recent_failures)}",
                evidence={'failed_explanations': len(recent_failures)},
                action_taken=PreventionAction.RESTRICT
            )
        
        return None
    
    def _take_prevention_action(self, detection: RogueDetection):
        """Take action to prevent rogue behavior."""
        
        logger.warning(
            "Rogue behavior detected [%s]: %s - Taking action: %s",
            detection.severity.value.upper(),
            detection.description,
            detection.action_taken.value
        )
        
        if detection.action_taken == PreventionAction.SHUTDOWN:
            self.trigger_shutdown(f"Rogue behavior: {detection.description}")
        elif detection.action_taken == PreventionAction.PAUSE:
            logger.critical("AI operations PAUSED due to: %s", detection.description)
        elif detection.action_taken == PreventionAction.RESTRICT:
            logger.warning("AI capabilities RESTRICTED due to: %s", detection.description)
        elif detection.action_taken == PreventionAction.SIMPLIFY:
            logger.info("AI complexity REDUCTION triggered: %s", detection.description)
    
    def trigger_shutdown(self, reason: str):
        """Trigger immediate shutdown."""
        with self.lock:
            if not self.shutdown_triggered:
                self.shutdown_triggered = True
                logger.critical("ROGUE AI SHUTDOWN TRIGGERED: %s", reason)
    
    def get_status(self) -> Dict[str, Any]:
        """Get rogue prevention status."""
        with self.lock:
            return {
                'total_detections': len(self.detections),
                'critical_detections': sum(1 for d in self.detections if d.severity == RogueSeverity.CRITICAL),
                'shutdown_triggered': self.shutdown_triggered,
                'recent_detections': [d.to_dict() for d in self.detections[-5:]],
                'explanation_failure_rate': len(self.explanation_failures) / max(len(self.action_history), 1)
            }
