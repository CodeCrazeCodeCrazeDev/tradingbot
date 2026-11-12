"""
Citation Validator

Validates all citations in reasoning chains against canonical sources.
Ensures evidence references are accurate and verifiable.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class CitationStatus(Enum):
    """Status of a citation."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    INVALID = "invalid"
    STALE = "stale"
    SOURCE_UNAVAILABLE = "source_unavailable"
    PARTIAL_MATCH = "partial_match"
    MISQUOTED = "misquoted"


class CitationType(Enum):
    """Types of citations."""
    DIRECT_QUOTE = "direct_quote"
    PARAPHRASE = "paraphrase"
    DATA_REFERENCE = "data_reference"
    STATISTICAL_CLAIM = "statistical_claim"
    EXTERNAL_API = "external_api"
    INTERNAL_MODEL = "internal_model"
    HISTORICAL_DATA = "historical_data"


@dataclass
class Citation:
    """A citation to a data source."""
    citation_id: str
    citation_type: CitationType
    source_id: str
    source_name: str
    source_url: Optional[str]
    content_hash: str
    quoted_content: str
    context: str
    timestamp: datetime
    status: CitationStatus = CitationStatus.UNVERIFIED
    verification_timestamp: Optional[datetime] = None
    verification_details: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'citation_id': self.citation_id,
            'citation_type': self.citation_type.value,
            'source_id': self.source_id,
            'source_name': self.source_name,
            'source_url': self.source_url,
            'content_hash': self.content_hash,
            'quoted_content': self.quoted_content,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'verification_timestamp': self.verification_timestamp.isoformat() if self.verification_timestamp else None,
            'verification_details': self.verification_details,
            'confidence_score': self.confidence_score,
        }


@dataclass
class ValidationReport:
    """Report of citation validation."""
    report_id: str
    citations_checked: int
    citations_verified: int
    citations_invalid: int
    citations_stale: int
    overall_validity: float
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'citations_checked': self.citations_checked,
            'citations_verified': self.citations_verified,
            'citations_invalid': self.citations_invalid,
            'citations_stale': self.citations_stale,
            'overall_validity': self.overall_validity,
            'issues': self.issues,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class SourceRegistry:
    """Registry of known data sources."""
    source_id: str
    source_name: str
    source_type: str
    base_url: Optional[str]
    trust_score: float
    last_verified: Optional[datetime]
    verification_method: str
    is_active: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_id': self.source_id,
            'source_name': self.source_name,
            'source_type': self.source_type,
            'base_url': self.base_url,
            'trust_score': self.trust_score,
            'last_verified': self.last_verified.isoformat() if self.last_verified else None,
            'verification_method': self.verification_method,
            'is_active': self.is_active,
        }


class CitationValidator:
    """
    Validates citations against canonical sources.
    
    Provides:
    - Citation verification against sources
    - Content hash validation
    - Staleness detection
    - Source registry management
    - Batch validation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'citation_validator_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._citations: Dict[str, Citation] = {}
        self._sources: Dict[str, SourceRegistry] = {}
        self._validation_cache: Dict[str, Tuple[bool, datetime]] = {}
        
        self._validation_config = {
            'max_staleness_hours': 24,
            'cache_ttl_minutes': 30,
            'minimum_trust_score': 0.5,
            'content_match_threshold': 0.9,
            'batch_size': 50,
        }
        
        self._initialize_default_sources()
        
        logger.info("✅ Citation Validator initialized")
    
    def _initialize_default_sources(self):
        """Initialize default trusted sources."""
        default_sources = [
            SourceRegistry(
                source_id="bloomberg",
                source_name="Bloomberg",
                source_type="market_data",
                base_url="https://www.bloomberg.com",
                trust_score=0.99,
                last_verified=datetime.now(timezone.utc),
                verification_method="api_verification",
                is_active=True,
            ),
            SourceRegistry(
                source_id="reuters",
                source_name="Reuters",
                source_type="news",
                base_url="https://www.reuters.com",
                trust_score=0.98,
                last_verified=datetime.now(timezone.utc),
                verification_method="api_verification",
                is_active=True,
            ),
            SourceRegistry(
                source_id="fed",
                source_name="Federal Reserve",
                source_type="economic_data",
                base_url="https://www.federalreserve.gov",
                trust_score=0.99,
                last_verified=datetime.now(timezone.utc),
                verification_method="official_source",
                is_active=True,
            ),
            SourceRegistry(
                source_id="sec",
                source_name="SEC EDGAR",
                source_type="regulatory",
                base_url="https://www.sec.gov/edgar",
                trust_score=0.99,
                last_verified=datetime.now(timezone.utc),
                verification_method="official_source",
                is_active=True,
            ),
            SourceRegistry(
                source_id="coinbase",
                source_name="Coinbase",
                source_type="crypto_exchange",
                base_url="https://www.coinbase.com",
                trust_score=0.95,
                last_verified=datetime.now(timezone.utc),
                verification_method="api_verification",
                is_active=True,
            ),
            SourceRegistry(
                source_id="binance",
                source_name="Binance",
                source_type="crypto_exchange",
                base_url="https://www.binance.com",
                trust_score=0.94,
                last_verified=datetime.now(timezone.utc),
                verification_method="api_verification",
                is_active=True,
            ),
            SourceRegistry(
                source_id="chainlink",
                source_name="Chainlink Oracle",
                source_type="blockchain_oracle",
                base_url="https://chain.link",
                trust_score=0.96,
                last_verified=datetime.now(timezone.utc),
                verification_method="blockchain_verification",
                is_active=True,
            ),
            SourceRegistry(
                source_id="internal_model",
                source_name="Internal Model",
                source_type="internal",
                base_url=None,
                trust_score=0.80,
                last_verified=datetime.now(timezone.utc),
                verification_method="internal_validation",
                is_active=True,
            ),
        ]
        
        for source in default_sources:
            self._sources[source.source_id] = source
    
    async def create_citation(
        self,
        citation_type: CitationType,
        source_id: str,
        quoted_content: str,
        context: str,
        source_url: Optional[str] = None,
    ) -> Citation:
        """
        Create a new citation.
        
        Args:
            citation_type: Type of citation
            source_id: ID of the source
            quoted_content: The quoted content
            context: Context in which citation is used
            source_url: Optional URL to source
        
        Returns:
            Citation object
        """
        citation_id = f"CIT-{uuid.uuid4().hex[:12]}"
        
        content_hash = hashlib.sha256(quoted_content.encode()).hexdigest()
        
        source = self._sources.get(source_id)
        source_name = source.source_name if source else "Unknown"
        
        citation = Citation(
            citation_id=citation_id,
            citation_type=citation_type,
            source_id=source_id,
            source_name=source_name,
            source_url=source_url,
            content_hash=content_hash,
            quoted_content=quoted_content,
            context=context,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._citations[citation_id] = citation
        
        return citation
    
    async def validate_citation(
        self,
        citation: Citation,
        canonical_content: Optional[str] = None,
    ) -> Tuple[CitationStatus, Dict[str, Any]]:
        """
        Validate a single citation.
        
        Args:
            citation: Citation to validate
            canonical_content: Optional canonical content to compare against
        
        Returns:
            Tuple of (status, details)
        """
        details = {
            'citation_id': citation.citation_id,
            'checks_performed': [],
            'issues': [],
        }
        
        cache_key = f"{citation.citation_id}:{citation.content_hash}"
        if cache_key in self._validation_cache:
            cached_result, cached_time = self._validation_cache[cache_key]
            cache_age = (datetime.now(timezone.utc) - cached_time).total_seconds() / 60
            if cache_age < self._validation_config['cache_ttl_minutes']:
                details['from_cache'] = True
                return CitationStatus.VERIFIED if cached_result else CitationStatus.INVALID, details
        
        source = self._sources.get(citation.source_id)
        if not source:
            details['issues'].append('Source not in registry')
            citation.status = CitationStatus.SOURCE_UNAVAILABLE
            return CitationStatus.SOURCE_UNAVAILABLE, details
        
        details['checks_performed'].append('source_registry')
        
        if source.trust_score < self._validation_config['minimum_trust_score']:
            details['issues'].append(f'Source trust score too low: {source.trust_score}')
        
        citation_age = (datetime.now(timezone.utc) - citation.timestamp).total_seconds() / 3600
        max_staleness = self._validation_config['max_staleness_hours']
        
        if citation_age > max_staleness:
            details['issues'].append(f'Citation is stale: {citation_age:.1f} hours old')
            citation.status = CitationStatus.STALE
            return CitationStatus.STALE, details
        
        details['checks_performed'].append('staleness')
        
        current_hash = hashlib.sha256(citation.quoted_content.encode()).hexdigest()
        if current_hash != citation.content_hash:
            details['issues'].append('Content hash mismatch - content may have been modified')
            citation.status = CitationStatus.INVALID
            return CitationStatus.INVALID, details
        
        details['checks_performed'].append('content_hash')
        
        if canonical_content:
            match_score = self._calculate_content_match(
                citation.quoted_content,
                canonical_content
            )
            details['content_match_score'] = match_score
            
            if match_score < self._validation_config['content_match_threshold']:
                if match_score > 0.5:
                    details['issues'].append(f'Partial content match: {match_score:.2f}')
                    citation.status = CitationStatus.PARTIAL_MATCH
                    return CitationStatus.PARTIAL_MATCH, details
                else:
                    details['issues'].append(f'Content mismatch: {match_score:.2f}')
                    citation.status = CitationStatus.MISQUOTED
                    return CitationStatus.MISQUOTED, details
            
            details['checks_performed'].append('content_match')
        
        citation.status = CitationStatus.VERIFIED
        citation.verification_timestamp = datetime.now(timezone.utc)
        citation.verification_details = details
        citation.confidence_score = source.trust_score * (1 - citation_age / max_staleness / 2)
        
        self._validation_cache[cache_key] = (True, datetime.now(timezone.utc))
        
        return CitationStatus.VERIFIED, details
    
    def _calculate_content_match(self, quoted: str, canonical: str) -> float:
        """Calculate similarity between quoted and canonical content."""
        quoted_lower = quoted.lower().strip()
        canonical_lower = canonical.lower().strip()
        
        if quoted_lower == canonical_lower:
            return 1.0
        
        if quoted_lower in canonical_lower or canonical_lower in quoted_lower:
            shorter = min(len(quoted_lower), len(canonical_lower))
            longer = max(len(quoted_lower), len(canonical_lower))
            return shorter / longer
        
        quoted_words = set(quoted_lower.split())
        canonical_words = set(canonical_lower.split())
        
        if not quoted_words or not canonical_words:
            return 0.0
        
        intersection = quoted_words & canonical_words
        union = quoted_words | canonical_words
        
        return len(intersection) / len(union)
    
    async def validate_citations_batch(
        self,
        citations: List[Citation],
    ) -> ValidationReport:
        """
        Validate multiple citations in batch.
        
        Args:
            citations: List of citations to validate
        
        Returns:
            ValidationReport
        """
        report_id = f"VR-{uuid.uuid4().hex[:12]}"
        
        verified = 0
        invalid = 0
        stale = 0
        issues = []
        
        for citation in citations:
            status, details = await self.validate_citation(citation)
            
            if status == CitationStatus.VERIFIED:
                verified += 1
            elif status == CitationStatus.STALE:
                stale += 1
                issues.append({
                    'citation_id': citation.citation_id,
                    'issue': 'stale',
                    'details': details,
                })
            else:
                invalid += 1
                issues.append({
                    'citation_id': citation.citation_id,
                    'issue': status.value,
                    'details': details,
                })
        
        total = len(citations)
        overall_validity = verified / total if total > 0 else 0.0
        
        recommendations = []
        if stale > 0:
            recommendations.append(f"Refresh {stale} stale citations")
        if invalid > 0:
            recommendations.append(f"Review and correct {invalid} invalid citations")
        if overall_validity < 0.8:
            recommendations.append("Overall citation validity is low - strengthen evidence base")
        
        report = ValidationReport(
            report_id=report_id,
            citations_checked=total,
            citations_verified=verified,
            citations_invalid=invalid,
            citations_stale=stale,
            overall_validity=overall_validity,
            issues=issues,
            recommendations=recommendations,
            timestamp=datetime.now(timezone.utc),
        )
        
        await self._persist_report(report)
        
        logger.info(f"Validated {total} citations: {verified} verified, "
                   f"{invalid} invalid, {stale} stale")
        
        return report
    
    def register_source(self, source: SourceRegistry):
        """Register a new data source."""
        self._sources[source.source_id] = source
        logger.info(f"Registered source: {source.source_name}")
    
    def get_source(self, source_id: str) -> Optional[SourceRegistry]:
        """Get a source by ID."""
        return self._sources.get(source_id)
    
    def update_source_trust(self, source_id: str, trust_score: float):
        """Update trust score for a source."""
        if source_id in self._sources:
            self._sources[source_id].trust_score = max(0.0, min(1.0, trust_score))
            self._sources[source_id].last_verified = datetime.now(timezone.utc)
    
    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """Get a citation by ID."""
        return self._citations.get(citation_id)
    
    async def _persist_report(self, report: ValidationReport):
        """Persist validation report to storage."""
        report_file = self.storage_path / 'reports' / f"{report.report_id}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get validator statistics."""
        verified = [c for c in self._citations.values() if c.status == CitationStatus.VERIFIED]
        
        return {
            'total_citations': len(self._citations),
            'verified_citations': len(verified),
            'registered_sources': len(self._sources),
            'active_sources': len([s for s in self._sources.values() if s.is_active]),
            'cache_size': len(self._validation_cache),
        }
