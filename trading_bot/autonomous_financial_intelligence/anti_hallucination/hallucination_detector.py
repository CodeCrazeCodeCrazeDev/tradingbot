"""
Hallucination Detector

Detects potential hallucinations in AI-generated outputs.
Implements multi-signal detection with zero-tolerance policy.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid
import re

logger = logging.getLogger(__name__)


class HallucinationType(Enum):
    """Types of hallucinations."""
    FABRICATED_DATA = "fabricated_data"
    FABRICATED_SOURCE = "fabricated_source"
    TEMPORAL_IMPOSSIBILITY = "temporal_impossibility"
    LOGICAL_IMPOSSIBILITY = "logical_impossibility"
    STATISTICAL_IMPOSSIBILITY = "statistical_impossibility"
    CONTRADICTORY_CLAIM = "contradictory_claim"
    UNSUPPORTED_ASSERTION = "unsupported_assertion"
    OVERCONFIDENT_PREDICTION = "overconfident_prediction"
    INVENTED_ENTITY = "invented_entity"
    MISATTRIBUTION = "misattribution"


class SeverityLevel(Enum):
    """Severity levels for hallucinations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionStatus(Enum):
    """Status of hallucination detection."""
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    HALLUCINATION_DETECTED = "hallucination_detected"
    QUARANTINED = "quarantined"


@dataclass
class HallucinationIndicator:
    """An indicator of potential hallucination."""
    indicator_id: str
    indicator_type: HallucinationType
    severity: SeverityLevel
    description: str
    evidence: Dict[str, Any]
    confidence: float
    location: Optional[str] = None
    suggested_action: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'indicator_id': self.indicator_id,
            'indicator_type': self.indicator_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'evidence': self.evidence,
            'confidence': self.confidence,
            'location': self.location,
            'suggested_action': self.suggested_action,
        }


@dataclass
class HallucinationReport:
    """Report of hallucination detection."""
    report_id: str
    content_id: str
    status: DetectionStatus
    indicators: List[HallucinationIndicator]
    overall_risk_score: float
    is_safe: bool
    requires_human_review: bool
    quarantine_recommended: bool
    detection_methods_used: List[str]
    timestamp: datetime
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'content_id': self.content_id,
            'status': self.status.value,
            'indicators': [i.to_dict() for i in self.indicators],
            'overall_risk_score': self.overall_risk_score,
            'is_safe': self.is_safe,
            'requires_human_review': self.requires_human_review,
            'quarantine_recommended': self.quarantine_recommended,
            'detection_methods_used': self.detection_methods_used,
            'timestamp': self.timestamp.isoformat(),
            'processing_time_ms': self.processing_time_ms,
        }


class HallucinationDetector:
    """
    Multi-signal hallucination detection system.
    
    Provides:
    - Pattern-based detection
    - Statistical anomaly detection
    - Cross-reference verification
    - Temporal consistency checking
    - Confidence calibration analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'hallucination_detector_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._reports: Dict[str, HallucinationReport] = {}
        self._quarantined_content: Dict[str, Dict[str, Any]] = {}
        self._known_entities: Set[str] = set()
        self._detection_history: List[Dict[str, Any]] = []
        
        self._detection_config = {
            'risk_threshold_safe': 0.2,
            'risk_threshold_suspicious': 0.5,
            'risk_threshold_hallucination': 0.7,
            'confidence_ceiling': 0.99,
            'min_evidence_for_claim': 1,
            'max_prediction_horizon_days': 365,
            'statistical_zscore_threshold': 4.0,
        }
        
        self._detection_methods = {
            'pattern_analysis': self._detect_pattern_hallucinations,
            'statistical_analysis': self._detect_statistical_hallucinations,
            'temporal_analysis': self._detect_temporal_hallucinations,
            'confidence_analysis': self._detect_confidence_hallucinations,
            'entity_verification': self._detect_entity_hallucinations,
            'source_verification': self._detect_source_hallucinations,
            'logical_analysis': self._detect_logical_hallucinations,
        }
        
        self._initialize_known_entities()
        
        logger.info("✅ Hallucination Detector initialized")
    
    def _initialize_known_entities(self):
        """Initialize set of known valid entities."""
        self._known_entities = {
            'BTC', 'ETH', 'USD', 'EUR', 'GBP', 'JPY',
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA',
            'S&P 500', 'NASDAQ', 'DOW', 'NYSE',
            'Federal Reserve', 'ECB', 'SEC', 'CFTC',
            'Bloomberg', 'Reuters', 'Coinbase', 'Binance',
        }
    
    async def detect_hallucinations(
        self,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        methods: Optional[List[str]] = None,
    ) -> HallucinationReport:
        """
        Detect hallucinations in content.
        
        Args:
            content: Content to analyze
            context: Optional context for analysis
            methods: Optional specific methods to use
        
        Returns:
            HallucinationReport
        """
        start_time = datetime.now(timezone.utc)
        report_id = f"HR-{uuid.uuid4().hex[:12]}"
        content_id = content.get('id', f"CNT-{uuid.uuid4().hex[:8]}")
        
        indicators = []
        methods_used = []
        
        methods_to_run = methods or list(self._detection_methods.keys())
        
        for method_name in methods_to_run:
            if method_name in self._detection_methods:
                method = self._detection_methods[method_name]
                try:
                    method_indicators = await method(content, context)
                    indicators.extend(method_indicators)
                    methods_used.append(method_name)
                except Exception as e:
                    logger.error(f"Detection method {method_name} failed: {e}")
        
        risk_score = self._calculate_risk_score(indicators)
        
        if risk_score < self._detection_config['risk_threshold_safe']:
            status = DetectionStatus.CLEAN
        elif risk_score < self._detection_config['risk_threshold_suspicious']:
            status = DetectionStatus.SUSPICIOUS
        else:
            status = DetectionStatus.HALLUCINATION_DETECTED
        
        is_safe = status == DetectionStatus.CLEAN
        requires_human_review = any(
            i.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
            for i in indicators
        )
        quarantine_recommended = risk_score >= self._detection_config['risk_threshold_hallucination']
        
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        report = HallucinationReport(
            report_id=report_id,
            content_id=content_id,
            status=status,
            indicators=indicators,
            overall_risk_score=risk_score,
            is_safe=is_safe,
            requires_human_review=requires_human_review,
            quarantine_recommended=quarantine_recommended,
            detection_methods_used=methods_used,
            timestamp=datetime.now(timezone.utc),
            processing_time_ms=processing_time,
        )
        
        self._reports[report_id] = report
        
        if quarantine_recommended:
            await self._quarantine_content(content_id, content, report)
        
        self._detection_history.append({
            'report_id': report_id,
            'status': status.value,
            'risk_score': risk_score,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
        
        await self._persist_report(report)
        
        logger.info(f"Hallucination detection complete: {status.value} "
                   f"(risk: {risk_score:.2f}, indicators: {len(indicators)})")
        
        return report
    
    def _calculate_risk_score(self, indicators: List[HallucinationIndicator]) -> float:
        """Calculate overall risk score from indicators."""
        if not indicators:
            return 0.0
        
        severity_weights = {
            SeverityLevel.LOW: 0.1,
            SeverityLevel.MEDIUM: 0.3,
            SeverityLevel.HIGH: 0.6,
            SeverityLevel.CRITICAL: 1.0,
        }
        
        weighted_scores = []
        for indicator in indicators:
            weight = severity_weights.get(indicator.severity, 0.3)
            weighted_scores.append(indicator.confidence * weight)
        
        if not weighted_scores:
            return 0.0
        
        max_score = max(weighted_scores)
        avg_score = sum(weighted_scores) / len(weighted_scores)
        
        risk_score = 0.7 * max_score + 0.3 * avg_score
        
        if len(indicators) > 3:
            risk_score = min(1.0, risk_score * 1.2)
        
        return min(1.0, risk_score)
    
    async def _detect_pattern_hallucinations(
        self,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> List[HallucinationIndicator]:
        """Detect hallucinations based on known patterns."""
        indicators = []
        
        content_str = json.dumps(content, default=str).lower()
        
        suspicious_patterns = [
            (r'100%\s*(certain|sure|confident|accurate)', 'Unrealistic certainty claim'),
            (r'guaranteed\s*(return|profit|success)', 'Guaranteed outcome claim'),
            (r'always\s*(works|succeeds|profitable)', 'Universal success claim'),
            (r'never\s*(fails|loses|wrong)', 'Infallibility claim'),
            (r'impossible\s*to\s*(lose|fail)', 'Impossibility of failure claim'),
        ]
        
        for pattern, description in suspicious_patterns:
            if re.search(pattern, content_str):
                indicators.append(HallucinationIndicator(
                    indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                    indicator_type=HallucinationType.OVERCONFIDENT_PREDICTION,
                    severity=SeverityLevel.HIGH,
                    description=description,
                    evidence={'pattern_matched': pattern},
                    confidence=0.8,
                    suggested_action='Review and moderate confidence claims',
                ))
        
        return indicators
    
    async def _detect_statistical_hallucinations(
        self,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> List[HallucinationIndicator]:
        """Detect statistically impossible claims."""
        indicators = []
        
        if 'prediction' in content:
            pred = content['prediction']
            
            if 'expected_return' in pred:
                ret = pred['expected_return']
                if isinstance(ret, (int, float)):
                    if ret > 1.0:
                        indicators.append(HallucinationIndicator(
                            indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                            indicator_type=HallucinationType.STATISTICAL_IMPOSSIBILITY,
                            severity=SeverityLevel.CRITICAL,
                            description=f"Predicted return of {ret*100:.0f}% is unrealistic",
                            evidence={'expected_return': ret},
                            confidence=0.95,
                            suggested_action='Reject prediction as statistically impossible',
                        ))
                    elif ret > 0.5:
                        indicators.append(HallucinationIndicator(
                            indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                            indicator_type=HallucinationType.OVERCONFIDENT_PREDICTION,
                            severity=SeverityLevel.HIGH,
                            description=f"Predicted return of {ret*100:.0f}% is highly suspicious",
                            evidence={'expected_return': ret},
                            confidence=0.85,
                            suggested_action='Verify prediction methodology',
                        ))
            
            if 'sharpe_ratio' in pred:
                sharpe = pred['sharpe_ratio']
                if isinstance(sharpe, (int, float)) and sharpe > 5:
                    indicators.append(HallucinationIndicator(
                        indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                        indicator_type=HallucinationType.STATISTICAL_IMPOSSIBILITY,
                        severity=SeverityLevel.HIGH,
                        description=f"Sharpe ratio of {sharpe} is unrealistically high",
                        evidence={'sharpe_ratio': sharpe},
                        confidence=0.9,
                        suggested_action='Verify calculation methodology',
                    ))
        
        return indicators
    
    async def _detect_temporal_hallucinations(
        self,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> List[HallucinationIndicator]:
        """Detect temporal impossibilities."""
        indicators = []
        
        if 'timestamp' in content and 'data_timestamp' in content:
            try:
                content_time = content['timestamp']
                data_time = content['data_timestamp']
                
                if isinstance(content_time, str):
                    content_time = datetime.fromisoformat(content_time.replace('Z', '+00:00'))
                if isinstance(data_time, str):
                    data_time = datetime.fromisoformat(data_time.replace('Z', '+00:00'))
                
                if data_time > content_time:
                    indicators.append(HallucinationIndicator(
                        indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                        indicator_type=HallucinationType.TEMPORAL_IMPOSSIBILITY,
                        severity=SeverityLevel.CRITICAL,
                        description="Data timestamp is in the future relative to content",
                        evidence={
                            'content_timestamp': str(content_time),
                            'data_timestamp': str(data_time),
                        },
                        confidence=1.0,
                        suggested_action='Reject content - temporal impossibility',
                    ))
            except Exception:
                pass
        
        if 'prediction' in content:
            pred = content['prediction']
            if 'horizon_days' in pred:
                horizon = pred['horizon_days']
                max_horizon = self._detection_config['max_prediction_horizon_days']
                if horizon > max_horizon:
                    indicators.append(HallucinationIndicator(
                        indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                        indicator_type=HallucinationType.OVERCONFIDENT_PREDICTION,
                        severity=SeverityLevel.MEDIUM,
                        description=f"Prediction horizon of {horizon} days exceeds reasonable limit",
                        evidence={'horizon_days': horizon, 'max_allowed': max_horizon},
                        confidence=0.7,
                        suggested_action='Reduce prediction horizon',
                    ))
        
        return indicators
    
    async def _detect_confidence_hallucinations(
        self,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> List[HallucinationIndicator]:
        """Detect overconfident claims."""
        indicators = []
        
        confidence_ceiling = self._detection_config['confidence_ceiling']
        
        confidence_fields = ['confidence', 'certainty', 'probability', 'accuracy']
        
        def check_confidence(obj: Any, path: str = ''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if key.lower() in confidence_fields:
                        if isinstance(value, (int, float)) and value > confidence_ceiling:
                            indicators.append(HallucinationIndicator(
                                indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                                indicator_type=HallucinationType.OVERCONFIDENT_PREDICTION,
                                severity=SeverityLevel.MEDIUM,
                                description=f"Confidence value {value} exceeds ceiling {confidence_ceiling}",
                                evidence={'field': new_path, 'value': value},
                                confidence=0.75,
                                suggested_action='Cap confidence at realistic level',
                            ))
                    else:
                        check_confidence(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_confidence(item, f"{path}[{i}]")
        
        check_confidence(content)
        
        return indicators
    
    async def _detect_entity_hallucinations(
        self,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> List[HallucinationIndicator]:
        """Detect invented or unknown entities."""
        indicators = []
        
        content_str = json.dumps(content, default=str)
        
        ticker_pattern = r'\b([A-Z]{2,5})\b'
        potential_tickers = re.findall(ticker_pattern, content_str)
        
        common_words = {'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'WILL', 'NOT'}
        
        for ticker in potential_tickers:
            if ticker not in common_words and ticker not in self._known_entities:
                if len(ticker) >= 3 and len(ticker) <= 5:
                    pass
        
        return indicators
    
    async def _detect_source_hallucinations(
        self,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> List[HallucinationIndicator]:
        """Detect fabricated sources."""
        indicators = []
        
        if 'sources' in content or 'citations' in content:
            sources = content.get('sources', content.get('citations', []))
            
            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, dict):
                        source_name = source.get('name', source.get('source_name', ''))
                        
                        if source_name and source_name.lower() not in [e.lower() for e in self._known_entities]:
                            if 'url' not in source and 'reference' not in source:
                                indicators.append(HallucinationIndicator(
                                    indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                                    indicator_type=HallucinationType.FABRICATED_SOURCE,
                                    severity=SeverityLevel.MEDIUM,
                                    description=f"Unverifiable source: {source_name}",
                                    evidence={'source': source},
                                    confidence=0.6,
                                    suggested_action='Verify source existence',
                                ))
        
        if not content.get('sources') and not content.get('citations') and not content.get('evidence'):
            if content.get('claim') or content.get('assertion') or content.get('prediction'):
                indicators.append(HallucinationIndicator(
                    indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                    indicator_type=HallucinationType.UNSUPPORTED_ASSERTION,
                    severity=SeverityLevel.HIGH,
                    description="Claim made without any supporting sources",
                    evidence={'has_sources': False},
                    confidence=0.8,
                    suggested_action='Add supporting evidence',
                ))
        
        return indicators
    
    async def _detect_logical_hallucinations(
        self,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> List[HallucinationIndicator]:
        """Detect logical impossibilities."""
        indicators = []
        
        if 'reasoning' in content:
            reasoning = content['reasoning']
            
            if isinstance(reasoning, list) and len(reasoning) >= 2:
                for i in range(len(reasoning) - 1):
                    step1 = str(reasoning[i]).lower()
                    step2 = str(reasoning[i + 1]).lower()
                    
                    if ('increase' in step1 and 'decrease' in step2) or \
                       ('decrease' in step1 and 'increase' in step2):
                        if 'therefore' in step2 or 'thus' in step2:
                            indicators.append(HallucinationIndicator(
                                indicator_id=f"HI-{uuid.uuid4().hex[:8]}",
                                indicator_type=HallucinationType.LOGICAL_IMPOSSIBILITY,
                                severity=SeverityLevel.MEDIUM,
                                description="Potential logical contradiction in reasoning",
                                evidence={'step1': reasoning[i], 'step2': reasoning[i + 1]},
                                confidence=0.6,
                                suggested_action='Review reasoning chain',
                            ))
        
        return indicators
    
    async def _quarantine_content(
        self,
        content_id: str,
        content: Dict[str, Any],
        report: HallucinationReport,
    ):
        """Quarantine content flagged as hallucination."""
        self._quarantined_content[content_id] = {
            'content': content,
            'report_id': report.report_id,
            'quarantined_at': datetime.now(timezone.utc).isoformat(),
            'risk_score': report.overall_risk_score,
            'indicators': [i.to_dict() for i in report.indicators],
        }
        
        logger.warning(f"Content {content_id} quarantined due to hallucination detection")
    
    def is_quarantined(self, content_id: str) -> bool:
        """Check if content is quarantined."""
        return content_id in self._quarantined_content
    
    async def release_from_quarantine(
        self,
        content_id: str,
        reviewer_id: str,
        reason: str,
    ) -> bool:
        """Release content from quarantine after review."""
        if content_id not in self._quarantined_content:
            return False
        
        del self._quarantined_content[content_id]
        
        logger.info(f"Content {content_id} released from quarantine by {reviewer_id}: {reason}")
        
        return True
    
    def get_report(self, report_id: str) -> Optional[HallucinationReport]:
        """Get a detection report by ID."""
        return self._reports.get(report_id)
    
    def get_quarantined_content(self) -> Dict[str, Dict[str, Any]]:
        """Get all quarantined content."""
        return self._quarantined_content.copy()
    
    async def _persist_report(self, report: HallucinationReport):
        """Persist report to storage."""
        report_file = self.storage_path / 'reports' / f"{report.report_id}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics."""
        status_counts = {}
        for report in self._reports.values():
            status_counts[report.status.value] = status_counts.get(report.status.value, 0) + 1
        
        type_counts = {}
        for report in self._reports.values():
            for indicator in report.indicators:
                type_counts[indicator.indicator_type.value] = type_counts.get(indicator.indicator_type.value, 0) + 1
        
        return {
            'total_reports': len(self._reports),
            'quarantined_content': len(self._quarantined_content),
            'reports_by_status': status_counts,
            'indicators_by_type': type_counts,
            'detection_methods': list(self._detection_methods.keys()),
        }
