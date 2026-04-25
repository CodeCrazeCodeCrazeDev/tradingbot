"""
Signal Validator

Validates raw signals before they enter the governance pipeline.
Checks for signal integrity, data quality, and basic sanity constraints.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalValidationError(Enum):
    """Types of signal validation errors"""
    MISSING_DATA = "missing_data"
    STALE_DATA = "stale_data"
    INVALID_CONFIDENCE = "invalid_confidence"
    CONTRADICTORY_SIGNALS = "contradictory_signals"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    DATA_ANOMALY = "data_anomaly"
    SOURCE_UNRELIABLE = "source_unreliable"


@dataclass
class SignalValidationResult:
    """Result of signal validation"""
    is_valid: bool
    errors: List[Tuple[SignalValidationError, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_signal: Optional[Dict[str, Any]] = None
    confidence_penalty: float = 0.0


class SignalValidator:
    """
    Validates trading signals for integrity before governance processing.
    
    Checks:
    - Required fields present
    - Confidence bounds valid
    - Data freshness
    - Signal-source reliability
    - Basic sanity checks
    """
    
    def __init__(
        self,
        max_signal_age_seconds: float = 300.0,  # 5 minutes
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
        required_fields: Optional[List[str]] = None
    ):
        self.max_signal_age = max_signal_age_seconds
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.required_fields = required_fields or [
            'direction', 'confidence', 'symbol'
        ]
        
        # Source reliability tracking
        self.source_reliability: Dict[str, float] = {}
        self.source_history: Dict[str, List[Dict]] = {}
        
    def validate_signal(
        self,
        signal: Dict[str, Any],
        symbol: str,
        current_time: Optional[datetime] = None
    ) -> SignalValidationResult:
        """
        Validate a trading signal.
        
        Args:
            signal: The signal to validate
            symbol: Trading symbol
            current_time: Current timestamp
            
        Returns:
            SignalValidationResult with errors and warnings
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        errors = []
        warnings = []
        confidence_penalty = 0.0
        
        # Check required fields
        missing_fields = self._check_required_fields(signal)
        if missing_fields:
            errors.append((
                SignalValidationError.MISSING_DATA,
                f"Missing required fields: {missing_fields}"
            ))
            
        # Check confidence bounds
        confidence = signal.get('confidence', 0.5)
        if not self._is_valid_confidence(confidence):
            errors.append((
                SignalValidationError.INVALID_CONFIDENCE,
                f"Confidence {confidence} outside valid range [{self.min_confidence}, {self.max_confidence}]"
            ))
            
        # Check signal freshness
        signal_time = signal.get('timestamp')
        if signal_time:
            age_seconds = (current_time - signal_time).total_seconds()
            if age_seconds > self.max_signal_age:
                errors.append((
                    SignalValidationError.STALE_DATA,
                    f"Signal age {age_seconds:.0f}s exceeds max {self.max_signal_age:.0f}s"
                ))
                confidence_penalty += 0.1
        else:
            warnings.append("Signal has no timestamp - assuming current time")
            
        # Check source reliability
        source = signal.get('source', 'unknown')
        reliability = self._get_source_reliability(source)
        if reliability < 0.5:
            warnings.append(f"Source '{source}' has low reliability: {reliability:.2f}")
            confidence_penalty += 0.15
            
        # Check for data anomalies
        anomalies = self._detect_anomalies(signal)
        if anomalies:
            for anomaly in anomalies:
                errors.append((
                    SignalValidationError.DATA_ANOMALY,
                    anomaly
                ))
                
        # Create sanitized signal
        sanitized = self._sanitize_signal(signal, symbol)
        
        is_valid = len([e for e in errors if e[0] != SignalValidationError.DATA_ANOMALY]) == 0
        
        return SignalValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sanitized_signal=sanitized if is_valid else None,
            confidence_penalty=confidence_penalty
        )
    
    def validate_multiple_signals(
        self,
        signals: List[Dict[str, Any]],
        symbol: str
    ) -> Tuple[bool, List[SignalValidationResult], float]:
        """
        Validate multiple signals and check for contradictions.
        
        Returns:
            Tuple of (all_valid, results, ensemble_confidence)
        """
        results = []
        valid_count = 0
        
        for signal in signals:
            result = self.validate_signal(signal, symbol)
            results.append(result)
            if result.is_valid:
                valid_count += 1
                
        # Check for contradictions
        directions = [s.get('direction') for s in signals if s.get('direction')]
        if 'buy' in directions and 'sell' in directions:
            for i, result in enumerate(results):
                result.errors.append((
                    SignalValidationError.CONTRADICTORY_SIGNALS,
                    f"Signal contradicts other signals: {directions}"
                ))
                result.is_valid = False
                
        all_valid = valid_count == len(signals) and not any(
            e[0] == SignalValidationError.CONTRADICTORY_SIGNALS
            for r in results for e in r.errors
        )
        
        # Calculate ensemble confidence
        avg_confidence = sum(
            r.sanitized_signal.get('confidence', 0) for r in results if r.sanitized_signal
        ) / len(results) if results else 0
        
        return all_valid, results, avg_confidence
    
    def _check_required_fields(self, signal: Dict[str, Any]) -> List[str]:
        """Check for missing required fields"""
        return [f for f in self.required_fields if f not in signal]
    
    def _is_valid_confidence(self, confidence: float) -> bool:
        """Check if confidence value is within valid range"""
        return self.min_confidence <= confidence <= self.max_confidence
    
    def _get_source_reliability(self, source: str) -> float:
        """Get reliability score for a signal source"""
        return self.source_reliability.get(source, 0.7)  # Default moderate reliability
    
    def _detect_anomalies(self, signal: Dict[str, Any]) -> List[str]:
        """Detect data anomalies in signal"""
        anomalies = []
        
        # Check for extreme confidence without justification
        confidence = signal.get('confidence', 0)
        rationale = signal.get('rationale') or signal.get('reasoning')
        
        if confidence > 0.9 and not rationale:
            anomalies.append("Extreme confidence (>0.9) without rationale")
            
        # Check for unrealistic position sizes
        size = signal.get('size', 1.0)
        if size > 5.0:
            anomalies.append(f"Unusually large position size: {size}")
        elif size < 0.01:
            anomalies.append(f"Unusually small position size: {size}")
            
        # Check for missing evidence on strong signals
        evidence = signal.get('evidence', [])
        if confidence > 0.8 and len(evidence) < 2:
            anomalies.append("Strong confidence with insufficient evidence items")
            
        return anomalies
    
    def _sanitize_signal(
        self,
        signal: Dict[str, Any],
        symbol: str
    ) -> Dict[str, Any]:
        """Create sanitized version of signal"""
        sanitized = {
            'symbol': symbol,
            'direction': signal.get('direction', 'hold'),
            'confidence': max(self.min_confidence, 
                           min(self.max_confidence, signal.get('confidence', 0.5))),
            'source': signal.get('source', 'unknown'),
            'timestamp': signal.get('timestamp', datetime.utcnow()),
            'size': signal.get('size', 1.0),
            'rationale': signal.get('rationale') or signal.get('reasoning', ''),
            'evidence': signal.get('evidence', []),
            'assumptions': signal.get('assumptions', []),
            'timeframe': signal.get('timeframe', '1d'),
            'invalidation_conditions': signal.get('invalidation_conditions', [])
        }
        
        return sanitized
    
    def update_source_reliability(
        self,
        source: str,
        outcome: Dict[str, Any]
    ) -> None:
        """Update reliability score based on outcome"""
        if source not in self.source_history:
            self.source_history[source] = []
            
        self.source_history[source].append({
            'timestamp': datetime.utcnow(),
            'pnl': outcome.get('pnl', 0),
            'confidence_error': outcome.get('confidence_error', 0)
        })
        
        # Keep only recent history
        cutoff = datetime.utcnow().timestamp() - 30 * 24 * 3600  # 30 days
        self.source_history[source] = [
            h for h in self.source_history[source]
            if h['timestamp'].timestamp() > cutoff
        ]
        
        # Calculate reliability
        if len(self.source_history[source]) >= 5:
            recent = self.source_history[source][-20:]  # Last 20 signals
            win_rate = sum(1 for h in recent if h['pnl'] > 0) / len(recent)
            avg_conf_error = sum(h['confidence_error'] for h in recent) / len(recent)
            
            # Reliability is win rate penalized by calibration error
            self.source_reliability[source] = max(0, win_rate - avg_conf_error)
        else:
            self.source_reliability[source] = 0.5  # Neutral if insufficient data
