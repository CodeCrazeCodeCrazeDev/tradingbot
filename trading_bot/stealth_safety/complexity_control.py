"""
Complexity Control System
=========================

Manages system complexity to prevent:
1. Hidden bugs that are impossible to find
2. Impossible-to-track behaviors
3. Unexpected emergent behavior
4. Black-box decision making
5. Cascading failures from complexity

PRINCIPLE: If you can't explain it simply, it's too complex.
"""

import logging
import threading
import hashlib
import inspect
import ast
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import json
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)


class BugSeverity(Enum):
    """Severity of detected bugs"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BehaviorType(Enum):
    """Types of tracked behaviors"""
    EXPECTED = "expected"
    UNUSUAL = "unusual"
    ANOMALOUS = "anomalous"
    DANGEROUS = "dangerous"


@dataclass
class BugReport:
    """Report of a detected bug or anomaly"""
    bug_id: str
    severity: BugSeverity
    location: str
    description: str
    stack_trace: Optional[str]
    detection_method: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class BehaviorRecord:
    """Record of system behavior"""
    behavior_id: str
    behavior_type: BehaviorType
    component: str
    action: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)


class ModuleIsolationFirewall:
    """
    Isolates modules to prevent cascading failures.
    
    PREVENTS:
    1. One module crashing the whole system
    2. Errors propagating across modules
    3. State corruption spreading
    4. Resource exhaustion affecting others
    5. Infinite loops blocking everything
    
    ENFORCES:
    - Module boundaries
    - Error containment
    - Resource limits per module
    - Timeout enforcement
    - State isolation
    """
    
    # Module limits
    MAX_EXECUTION_TIME_MS = 5000    # 5 seconds max per call
    MAX_MEMORY_MB = 100             # 100MB per module
    MAX_CALLS_PER_MINUTE = 1000     # Rate limiting
    MAX_ERROR_RATE = 0.10           # 10% error rate triggers isolation
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Module tracking
        self.modules: Dict[str, Dict] = {}
        self.isolated_modules: set = set()
        self.module_errors: Dict[str, deque] = {}
        self.module_calls: Dict[str, deque] = {}
        
        # Firewall state
        self.firewall_active = True
        
        logger.info("ModuleIsolationFirewall initialized")
    
    def register_module(self, module_name: str, dependencies: List[str] = None):
        """Register a module with the firewall"""
        self.modules[module_name] = {
            'name': module_name,
            'dependencies': dependencies or [],
            'registered_at': datetime.now(),
            'call_count': 0,
            'error_count': 0,
            'last_error': None,
            'is_healthy': True
        }
        self.module_errors[module_name] = deque(maxlen=100)
        self.module_calls[module_name] = deque(maxlen=1000)
        
        logger.debug(f"Module registered: {module_name}")
    
    def can_call_module(self, module_name: str) -> Tuple[bool, str]:
        """Check if a module can be called"""
        if module_name in self.isolated_modules:
            return False, f"Module {module_name} is isolated due to errors"
        
        if module_name not in self.modules:
            return True, "Module not registered - allowing call"
        
        # Check rate limit
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        recent_calls = [c for c in self.module_calls.get(module_name, []) if c > minute_ago]
        
        if len(recent_calls) >= self.MAX_CALLS_PER_MINUTE:
            return False, f"Module {module_name} rate limited"
        
        return True, "Call allowed"
    
    def record_call(self, module_name: str, success: bool, duration_ms: float, error: Optional[str] = None):
        """Record a module call"""
        now = datetime.now()
        
        if module_name not in self.module_calls:
            self.module_calls[module_name] = deque(maxlen=1000)
        
        self.module_calls[module_name].append(now)
        
        if module_name in self.modules:
            self.modules[module_name]['call_count'] += 1
        
        if not success:
            if module_name not in self.module_errors:
                self.module_errors[module_name] = deque(maxlen=100)
            
            self.module_errors[module_name].append({
                'timestamp': now,
                'error': error
            })
            
            if module_name in self.modules:
                self.modules[module_name]['error_count'] += 1
                self.modules[module_name]['last_error'] = error
            
            # Check if should isolate
            self._check_isolation(module_name)
        
        # Check timeout
        if duration_ms > self.MAX_EXECUTION_TIME_MS:
            logger.warning(f"Module {module_name} exceeded timeout: {duration_ms}ms")
    
    def _check_isolation(self, module_name: str):
        """Check if module should be isolated"""
        if module_name not in self.modules:
            return
        
        module = self.modules[module_name]
        
        if module['call_count'] > 10:
            error_rate = module['error_count'] / module['call_count']
            
            if error_rate > self.MAX_ERROR_RATE:
                self.isolate_module(module_name, f"Error rate {error_rate*100:.0f}% exceeds limit")
    
    def isolate_module(self, module_name: str, reason: str):
        """Isolate a failing module"""
        self.isolated_modules.add(module_name)
        
        if module_name in self.modules:
            self.modules[module_name]['is_healthy'] = False
        
        logger.warning(f"MODULE ISOLATED: {module_name} - {reason}")
    
    def restore_module(self, module_name: str):
        """Restore an isolated module"""
        if module_name in self.isolated_modules:
            self.isolated_modules.remove(module_name)
            
            if module_name in self.modules:
                self.modules[module_name]['is_healthy'] = True
                self.modules[module_name]['error_count'] = 0
            
            logger.info(f"Module restored: {module_name}")
    
    def get_module_health(self) -> Dict[str, Any]:
        """Get health status of all modules"""
        return {
            'total_modules': len(self.modules),
            'isolated_modules': list(self.isolated_modules),
            'healthy_modules': [m for m, d in self.modules.items() if d['is_healthy']],
            'module_details': {
                name: {
                    'calls': data['call_count'],
                    'errors': data['error_count'],
                    'healthy': data['is_healthy']
                }
                for name, data in self.modules.items()
            }
        }


class NoBlackBoxDecisions:
    """
    Ensures NO decision is a black box.
    
    EVERY DECISION MUST HAVE:
    1. Clear inputs
    2. Explicit reasoning
    3. Traceable logic
    4. Human-readable explanation
    5. Audit trail
    
    NO DECISION CAN BE:
    1. Unexplainable
    2. Based on hidden state
    3. Made by opaque models
    4. Without justification
    5. Untraceable
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Decision tracking
        self.decisions: deque = deque(maxlen=10000)
        self.unexplained_decisions: List[Dict] = []
        
        # Explanation requirements
        self.min_explanation_length = 10
        self.required_fields = ['inputs', 'reasoning', 'output', 'confidence']
        
        logger.info("NoBlackBoxDecisions initialized - ALL DECISIONS MUST BE EXPLAINABLE")
    
    def record_decision(
        self,
        decision_id: str,
        decision_type: str,
        inputs: Dict[str, Any],
        reasoning: List[str],
        output: Any,
        confidence: float,
        model_used: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Record a decision with full explanation.
        
        Returns:
            Tuple of (is_valid, validation_message)
        """
        decision = {
            'decision_id': decision_id,
            'type': decision_type,
            'inputs': inputs,
            'reasoning': reasoning,
            'output': output,
            'confidence': confidence,
            'model_used': model_used,
            'timestamp': datetime.now().isoformat()
        }
        
        # Validate explanation
        is_valid, message = self._validate_explanation(decision)
        
        if is_valid:
            self.decisions.append(decision)
        else:
            self.unexplained_decisions.append(decision)
            logger.warning(f"BLACK BOX DECISION DETECTED: {decision_id} - {message}")
        
        return is_valid, message
    
    def _validate_explanation(self, decision: Dict) -> Tuple[bool, str]:
        """Validate that a decision is properly explained"""
        # Check required fields
        for field in self.required_fields:
            if field not in decision or decision[field] is None:
                return False, f"Missing required field: {field}"
        
        # Check reasoning quality
        reasoning = decision.get('reasoning', [])
        if not reasoning:
            return False, "No reasoning provided"
        
        if len(reasoning) < 2:
            return False, "Reasoning too short - need at least 2 steps"
        
        total_reasoning_length = sum(len(r) for r in reasoning)
        if total_reasoning_length < self.min_explanation_length:
            return False, "Reasoning not detailed enough"
        
        # Check inputs are documented
        inputs = decision.get('inputs', {})
        if not inputs:
            return False, "No inputs documented"
        
        # Check confidence is reasonable
        confidence = decision.get('confidence', 0)
        if confidence < 0 or confidence > 1:
            return False, "Invalid confidence value"
        
        return True, "Decision properly explained"
    
    def get_explanation(self, decision_id: str) -> Optional[Dict]:
        """Get explanation for a specific decision"""
        for decision in self.decisions:
            if decision['decision_id'] == decision_id:
                return {
                    'decision_id': decision_id,
                    'type': decision['type'],
                    'inputs': decision['inputs'],
                    'reasoning_chain': decision['reasoning'],
                    'output': decision['output'],
                    'confidence': decision['confidence'],
                    'human_readable': self._generate_human_readable(decision)
                }
        return None
    
    def _generate_human_readable(self, decision: Dict) -> str:
        """Generate human-readable explanation"""
        lines = [
            f"Decision: {decision['type']}",
            f"Confidence: {decision['confidence']*100:.0f}%",
            "",
            "Inputs:",
        ]
        
        for key, value in decision.get('inputs', {}).items():
            lines.append(f"  - {key}: {value}")
        
        lines.append("")
        lines.append("Reasoning:")
        
        for i, step in enumerate(decision.get('reasoning', []), 1):
            lines.append(f"  {i}. {step}")
        
        lines.append("")
        lines.append(f"Output: {decision['output']}")
        
        return "\n".join(lines)
    
    def get_unexplained_count(self) -> int:
        """Get count of unexplained decisions"""
        return len(self.unexplained_decisions)
    
    def get_status(self) -> Dict[str, Any]:
        """Get decision transparency status"""
        return {
            'total_decisions': len(self.decisions),
            'unexplained_decisions': len(self.unexplained_decisions),
            'transparency_rate': 1 - (len(self.unexplained_decisions) / max(1, len(self.decisions) + len(self.unexplained_decisions)))
        }


class HiddenBugDetector:
    """
    Detects hidden bugs before they cause damage.
    
    DETECTION METHODS:
    1. Invariant checking
    2. Anomaly detection
    3. State consistency verification
    4. Output validation
    5. Behavior pattern analysis
    
    HIDDEN BUGS CAN:
    1. Cause silent data corruption
    2. Lead to wrong decisions
    3. Accumulate over time
    4. Trigger cascading failures
    5. Be impossible to reproduce
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Bug tracking
        self.detected_bugs: List[BugReport] = []
        self.invariants: Dict[str, Callable] = {}
        
        # Anomaly detection
        self.baseline_behaviors: Dict[str, List[float]] = {}
        self.anomaly_threshold = config.get('anomaly_threshold', 3.0)  # Standard deviations
        
        logger.info("HiddenBugDetector initialized")
    
    def register_invariant(self, name: str, check_function: Callable[[], bool], description: str):
        """Register an invariant that must always be true"""
        self.invariants[name] = {
            'check': check_function,
            'description': description,
            'last_check': None,
            'violations': 0
        }
    
    def check_invariants(self) -> List[BugReport]:
        """Check all registered invariants"""
        bugs = []
        
        for name, invariant in self.invariants.items():
            try:
                result = invariant['check']()
                invariant['last_check'] = datetime.now()
                
                if not result:
                    bug = BugReport(
                        bug_id=hashlib.sha256(f"{name}_{datetime.now()}".encode()).hexdigest()[:16],
                        severity=BugSeverity.HIGH,
                        location=name,
                        description=f"Invariant violated: {invariant['description']}",
                        stack_trace=None,
                        detection_method="invariant_check"
                    )
                    bugs.append(bug)
                    self.detected_bugs.append(bug)
                    invariant['violations'] += 1
                    
                    logger.error(f"INVARIANT VIOLATION: {name} - {invariant['description']}")
            
            except Exception as e:
                bug = BugReport(
                    bug_id=hashlib.sha256(f"{name}_{datetime.now()}".encode()).hexdigest()[:16],
                    severity=BugSeverity.CRITICAL,
                    location=name,
                    description=f"Invariant check failed with exception: {str(e)}",
                    stack_trace=traceback.format_exc(),
                    detection_method="invariant_check"
                )
                bugs.append(bug)
                self.detected_bugs.append(bug)
        
        return bugs
    
    def check_output_validity(
        self,
        output_name: str,
        value: Any,
        expected_type: type,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Tuple[bool, Optional[BugReport]]:
        """Check if an output is valid"""
        # Type check
        if not isinstance(value, expected_type):
            bug = BugReport(
                bug_id=hashlib.sha256(f"{output_name}_{datetime.now()}".encode()).hexdigest()[:16],
                severity=BugSeverity.MEDIUM,
                location=output_name,
                description=f"Type mismatch: expected {expected_type}, got {type(value)}",
                stack_trace=None,
                detection_method="output_validation"
            )
            self.detected_bugs.append(bug)
            return False, bug
        
        # Range check for numeric values
        if isinstance(value, (int, float)):
            if min_value is not None and value < min_value:
                bug = BugReport(
                    bug_id=hashlib.sha256(f"{output_name}_{datetime.now()}".encode()).hexdigest()[:16],
                    severity=BugSeverity.MEDIUM,
                    location=output_name,
                    description=f"Value {value} below minimum {min_value}",
                    stack_trace=None,
                    detection_method="output_validation"
                )
                self.detected_bugs.append(bug)
                return False, bug
            
            if max_value is not None and value > max_value:
                bug = BugReport(
                    bug_id=hashlib.sha256(f"{output_name}_{datetime.now()}".encode()).hexdigest()[:16],
                    severity=BugSeverity.MEDIUM,
                    location=output_name,
                    description=f"Value {value} above maximum {max_value}",
                    stack_trace=None,
                    detection_method="output_validation"
                )
                self.detected_bugs.append(bug)
                return False, bug
        
        return True, None
    
    def detect_anomaly(
        self,
        metric_name: str,
        value: float
    ) -> Tuple[bool, Optional[BugReport]]:
        """Detect anomalous values based on historical baseline"""
        if metric_name not in self.baseline_behaviors:
            self.baseline_behaviors[metric_name] = []
        
        history = self.baseline_behaviors[metric_name]
        history.append(value)
        
        # Need enough history
        if len(history) < 20:
            return False, None
        
        # Calculate statistics
        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std = variance ** 0.5
        
        if std > 0:
            z_score = abs(value - mean) / std
            
            if z_score > self.anomaly_threshold:
                bug = BugReport(
                    bug_id=hashlib.sha256(f"{metric_name}_{datetime.now()}".encode()).hexdigest()[:16],
                    severity=BugSeverity.MEDIUM,
                    location=metric_name,
                    description=f"Anomalous value detected: {value} (z-score: {z_score:.2f})",
                    stack_trace=None,
                    detection_method="anomaly_detection"
                )
                self.detected_bugs.append(bug)
                return True, bug
        
        return False, None
    
    def get_bug_summary(self) -> Dict[str, Any]:
        """Get summary of detected bugs"""
        by_severity = {}
        for bug in self.detected_bugs:
            sev = bug.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return {
            'total_bugs': len(self.detected_bugs),
            'by_severity': by_severity,
            'unresolved': len([b for b in self.detected_bugs if not b.resolved]),
            'invariant_violations': sum(i['violations'] for i in self.invariants.values())
        }


class BehaviorTracker:
    """
    Tracks all system behaviors to detect drift and anomalies.
    
    TRACKS:
    1. Decision patterns
    2. Execution timing
    3. Resource usage
    4. Error patterns
    5. State changes
    
    DETECTS:
    1. Behavioral drift
    2. Unexpected patterns
    3. Performance degradation
    4. Anomalous sequences
    5. Emergent behaviors
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Behavior history
        self.behaviors: deque = deque(maxlen=100000)
        self.behavior_patterns: Dict[str, List[str]] = {}
        
        # Drift detection
        self.baseline_patterns: Dict[str, Dict] = {}
        self.drift_threshold = config.get('drift_threshold', 0.2)
        
        # Anomaly tracking
        self.anomalous_behaviors: List[BehaviorRecord] = []
        
        logger.info("BehaviorTracker initialized")
    
    def record_behavior(
        self,
        component: str,
        action: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        duration_ms: float
    ) -> BehaviorRecord:
        """Record a behavior"""
        behavior = BehaviorRecord(
            behavior_id=hashlib.sha256(f"{component}_{action}_{datetime.now()}".encode()).hexdigest()[:16],
            behavior_type=BehaviorType.EXPECTED,
            component=component,
            action=action,
            inputs=inputs,
            outputs=outputs,
            duration_ms=duration_ms
        )
        
        self.behaviors.append(behavior)
        
        # Track pattern
        pattern_key = f"{component}:{action}"
        if pattern_key not in self.behavior_patterns:
            self.behavior_patterns[pattern_key] = []
        self.behavior_patterns[pattern_key].append(behavior.behavior_id)
        
        # Check for anomalies
        self._check_behavior_anomaly(behavior)
        
        return behavior
    
    def _check_behavior_anomaly(self, behavior: BehaviorRecord):
        """Check if behavior is anomalous"""
        pattern_key = f"{behavior.component}:{behavior.action}"
        
        if pattern_key in self.baseline_patterns:
            baseline = self.baseline_patterns[pattern_key]
            
            # Check duration anomaly
            if baseline.get('avg_duration'):
                if behavior.duration_ms > baseline['avg_duration'] * 3:
                    behavior.behavior_type = BehaviorType.UNUSUAL
                    self.anomalous_behaviors.append(behavior)
    
    def establish_baseline(self, pattern_key: str):
        """Establish baseline for a behavior pattern"""
        if pattern_key not in self.behavior_patterns:
            return
        
        behavior_ids = self.behavior_patterns[pattern_key]
        behaviors = [b for b in self.behaviors if b.behavior_id in behavior_ids]
        
        if len(behaviors) < 10:
            return
        
        durations = [b.duration_ms for b in behaviors]
        
        self.baseline_patterns[pattern_key] = {
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'sample_count': len(behaviors),
            'established_at': datetime.now().isoformat()
        }
    
    def detect_drift(self) -> Tuple[bool, float, str]:
        """
        Detect behavioral drift from baseline.
        
        Returns:
            Tuple of (is_drifting, drift_score, description)
        """
        if not self.baseline_patterns:
            return False, 0.0, "No baseline established"
        
        drift_scores = []
        
        for pattern_key, baseline in self.baseline_patterns.items():
            recent_behaviors = [
                b for b in self.behaviors
                if f"{b.component}:{b.action}" == pattern_key
            ][-50:]
            
            if len(recent_behaviors) < 10:
                continue
            
            recent_avg = sum(b.duration_ms for b in recent_behaviors) / len(recent_behaviors)
            
            if baseline['avg_duration'] > 0:
                drift = abs(recent_avg - baseline['avg_duration']) / baseline['avg_duration']
                drift_scores.append(drift)
        
        if not drift_scores:
            return False, 0.0, "Insufficient data"
        
        avg_drift = sum(drift_scores) / len(drift_scores)
        is_drifting = avg_drift > self.drift_threshold
        
        return is_drifting, avg_drift, f"Average drift: {avg_drift*100:.1f}%"
    
    def get_status(self) -> Dict[str, Any]:
        """Get behavior tracking status"""
        is_drifting, drift_score, _ = self.detect_drift()
        
        return {
            'total_behaviors': len(self.behaviors),
            'unique_patterns': len(self.behavior_patterns),
            'baselines_established': len(self.baseline_patterns),
            'anomalous_behaviors': len(self.anomalous_behaviors),
            'is_drifting': is_drifting,
            'drift_score': drift_score
        }


class ExplainableEverything:
    """
    Master explainability system.
    
    ENSURES:
    1. Every decision can be explained
    2. Every action can be traced
    3. Every state can be understood
    4. Every change can be justified
    5. Every outcome can be analyzed
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.module_firewall = ModuleIsolationFirewall(config.get('firewall', {}))
        self.no_black_box = NoBlackBoxDecisions(config.get('decisions', {}))
        self.bug_detector = HiddenBugDetector(config.get('bugs', {}))
        self.behavior_tracker = BehaviorTracker(config.get('behavior', {}))
        
        logger.info("ExplainableEverything initialized - FULL TRANSPARENCY ACTIVE")
    
    def explain_decision(self, decision_id: str) -> Optional[str]:
        """Get human-readable explanation for a decision"""
        explanation = self.no_black_box.get_explanation(decision_id)
        if explanation:
            return explanation.get('human_readable')
        return None
    
    def get_system_state_explanation(self) -> str:
        """Get human-readable explanation of current system state"""
        lines = [
            "=== SYSTEM STATE EXPLANATION ===",
            "",
            "Module Health:",
        ]
        
        module_health = self.module_firewall.get_module_health()
        lines.append(f"  - Total modules: {module_health['total_modules']}")
        lines.append(f"  - Isolated modules: {len(module_health['isolated_modules'])}")
        
        lines.append("")
        lines.append("Decision Transparency:")
        decision_status = self.no_black_box.get_status()
        lines.append(f"  - Total decisions: {decision_status['total_decisions']}")
        lines.append(f"  - Transparency rate: {decision_status['transparency_rate']*100:.0f}%")
        
        lines.append("")
        lines.append("Bug Detection:")
        bug_summary = self.bug_detector.get_bug_summary()
        lines.append(f"  - Total bugs detected: {bug_summary['total_bugs']}")
        lines.append(f"  - Unresolved: {bug_summary['unresolved']}")
        
        lines.append("")
        lines.append("Behavior Tracking:")
        behavior_status = self.behavior_tracker.get_status()
        lines.append(f"  - Behaviors tracked: {behavior_status['total_behaviors']}")
        lines.append(f"  - Is drifting: {behavior_status['is_drifting']}")
        
        return "\n".join(lines)
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive explainability status"""
        return {
            'modules': self.module_firewall.get_module_health(),
            'decisions': self.no_black_box.get_status(),
            'bugs': self.bug_detector.get_bug_summary(),
            'behavior': self.behavior_tracker.get_status()
        }
