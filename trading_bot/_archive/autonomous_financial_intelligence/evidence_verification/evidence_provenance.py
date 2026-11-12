"""
Evidence Provenance System

Cryptographic provenance chains linking every decision to immutable data sources.
Provides complete audit trails and verification of evidence authenticity.
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
import hmac
import secrets

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Types of evidence that can be recorded."""
    MARKET_DATA = "market_data"
    PRICE_QUOTE = "price_quote"
    ORDER_BOOK = "order_book"
    TRADE_EXECUTION = "trade_execution"
    NEWS_EVENT = "news_event"
    ECONOMIC_INDICATOR = "economic_indicator"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TECHNICAL_INDICATOR = "technical_indicator"
    MODEL_PREDICTION = "model_prediction"
    AGENT_DECISION = "agent_decision"
    EXTERNAL_API = "external_api"
    BLOCKCHAIN_DATA = "blockchain_data"
    REGULATORY_FILING = "regulatory_filing"
    RESEARCH_FINDING = "research_finding"


class VerificationStatus(Enum):
    """Status of evidence verification."""
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"


@dataclass
class EvidenceRecord:
    """
    Immutable record of a piece of evidence.
    Contains cryptographic hash for integrity verification.
    """
    evidence_id: str
    evidence_type: EvidenceType
    source_id: str
    source_name: str
    timestamp: datetime
    data_hash: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    signature: str
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    parent_evidence_ids: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    expiry_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'evidence_id': self.evidence_id,
            'evidence_type': self.evidence_type.value,
            'source_id': self.source_id,
            'source_name': self.source_name,
            'timestamp': self.timestamp.isoformat(),
            'data_hash': self.data_hash,
            'content': self.content,
            'metadata': self.metadata,
            'signature': self.signature,
            'verification_status': self.verification_status.value,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by': self.verified_by,
            'parent_evidence_ids': self.parent_evidence_ids,
            'confidence_score': self.confidence_score,
            'expiry_time': self.expiry_time.isoformat() if self.expiry_time else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceRecord':
        return cls(
            evidence_id=data['evidence_id'],
            evidence_type=EvidenceType(data['evidence_type']),
            source_id=data['source_id'],
            source_name=data['source_name'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            data_hash=data['data_hash'],
            content=data['content'],
            metadata=data['metadata'],
            signature=data['signature'],
            verification_status=VerificationStatus(data['verification_status']),
            verified_at=datetime.fromisoformat(data['verified_at']) if data.get('verified_at') else None,
            verified_by=data.get('verified_by'),
            parent_evidence_ids=data.get('parent_evidence_ids', []),
            confidence_score=data.get('confidence_score', 1.0),
            expiry_time=datetime.fromisoformat(data['expiry_time']) if data.get('expiry_time') else None,
        )


@dataclass
class ProvenanceChain:
    """
    Chain of evidence linking a decision to its source data.
    Provides complete audit trail from decision to raw data.
    """
    chain_id: str
    decision_id: str
    created_at: datetime
    evidence_records: List[EvidenceRecord]
    chain_hash: str
    is_complete: bool = False
    validation_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chain_id': self.chain_id,
            'decision_id': self.decision_id,
            'created_at': self.created_at.isoformat(),
            'evidence_records': [e.to_dict() for e in self.evidence_records],
            'chain_hash': self.chain_hash,
            'is_complete': self.is_complete,
            'validation_score': self.validation_score,
        }


class EvidenceProvenance:
    """
    Manages cryptographic provenance chains for all evidence.
    Ensures every decision can be traced back to verifiable data sources.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'evidence_provenance_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._secret_key = self._load_or_generate_secret_key()
        self._evidence_store: Dict[str, EvidenceRecord] = {}
        self._provenance_chains: Dict[str, ProvenanceChain] = {}
        self._source_trust_scores: Dict[str, float] = {}
        
        self._initialize_trusted_sources()
        
        logger.info("✅ Evidence Provenance System initialized")
    
    def _load_or_generate_secret_key(self) -> bytes:
        """Load or generate secret key for HMAC signatures."""
        key_file = self.storage_path / '.evidence_key'
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = secrets.token_bytes(32)
            key_file.write_bytes(key)
            return key
    
    def _initialize_trusted_sources(self):
        """Initialize trust scores for known data sources."""
        self._source_trust_scores = {
            'bloomberg': 0.99,
            'reuters': 0.98,
            'coinbase': 0.95,
            'binance': 0.94,
            'kraken': 0.94,
            'chainlink': 0.96,
            'coingecko': 0.90,
            'yahoo_finance': 0.92,
            'alpha_vantage': 0.88,
            'polygon_io': 0.91,
            'internal_model': 0.85,
            'agent_analysis': 0.80,
            'unknown': 0.50,
        }
    
    def _compute_hash(self, data: Any) -> str:
        """Compute SHA-256 hash of data."""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _compute_signature(self, data: str) -> str:
        """Compute HMAC signature for data integrity."""
        return hmac.new(self._secret_key, data.encode(), hashlib.sha256).hexdigest()
    
    def _verify_signature(self, data: str, signature: str) -> bool:
        """Verify HMAC signature."""
        expected = self._compute_signature(data)
        return hmac.compare_digest(expected, signature)
    
    async def create_evidence_record(
        self,
        evidence_type: EvidenceType,
        source_id: str,
        source_name: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        parent_evidence_ids: Optional[List[str]] = None,
        expiry_hours: Optional[int] = None,
    ) -> EvidenceRecord:
        """
        Create a new evidence record with cryptographic integrity.
        
        Args:
            evidence_type: Type of evidence
            source_id: Unique identifier for the data source
            source_name: Human-readable source name
            content: The actual evidence data
            metadata: Additional metadata about the evidence
            parent_evidence_ids: IDs of evidence this derives from
            expiry_hours: Hours until evidence expires (None = never)
        
        Returns:
            Immutable EvidenceRecord with cryptographic signature
        """
        evidence_id = f"EVD-{uuid.uuid4().hex[:16]}"
        timestamp = datetime.now(timezone.utc)
        
        data_hash = self._compute_hash(content)
        
        metadata = metadata or {}
        metadata['creation_timestamp'] = timestamp.isoformat()
        metadata['source_trust_score'] = self._source_trust_scores.get(
            source_name.lower(), 
            self._source_trust_scores['unknown']
        )
        
        signature_data = f"{evidence_id}:{data_hash}:{timestamp.isoformat()}"
        signature = self._compute_signature(signature_data)
        
        expiry_time = None
        if expiry_hours:
            from datetime import timedelta
            expiry_time = timestamp + timedelta(hours=expiry_hours)
        
        confidence_score = metadata['source_trust_score']
        if parent_evidence_ids:
            parent_scores = [
                self._evidence_store[pid].confidence_score 
                for pid in parent_evidence_ids 
                if pid in self._evidence_store
            ]
            if parent_scores:
                confidence_score = min(confidence_score, min(parent_scores) * 0.95)
        
        record = EvidenceRecord(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            source_id=source_id,
            source_name=source_name,
            timestamp=timestamp,
            data_hash=data_hash,
            content=content,
            metadata=metadata,
            signature=signature,
            parent_evidence_ids=parent_evidence_ids or [],
            confidence_score=confidence_score,
            expiry_time=expiry_time,
        )
        
        self._evidence_store[evidence_id] = record
        
        await self._persist_evidence(record)
        
        logger.debug(f"Created evidence record: {evidence_id} ({evidence_type.value})")
        
        return record
    
    async def verify_evidence(self, evidence_id: str) -> Tuple[bool, str]:
        """
        Verify the integrity of an evidence record.
        
        Args:
            evidence_id: ID of evidence to verify
        
        Returns:
            Tuple of (is_valid, reason)
        """
        if evidence_id not in self._evidence_store:
            return False, "Evidence not found"
        
        record = self._evidence_store[evidence_id]
        
        if record.expiry_time and datetime.now(timezone.utc) > record.expiry_time:
            record.verification_status = VerificationStatus.EXPIRED
            return False, "Evidence has expired"
        
        current_hash = self._compute_hash(record.content)
        if current_hash != record.data_hash:
            record.verification_status = VerificationStatus.INVALIDATED
            return False, "Data hash mismatch - evidence has been tampered with"
        
        signature_data = f"{record.evidence_id}:{record.data_hash}:{record.timestamp.isoformat()}"
        if not self._verify_signature(signature_data, record.signature):
            record.verification_status = VerificationStatus.INVALIDATED
            return False, "Signature verification failed"
        
        for parent_id in record.parent_evidence_ids:
            if parent_id in self._evidence_store:
                parent_valid, _ = await self.verify_evidence(parent_id)
                if not parent_valid:
                    record.verification_status = VerificationStatus.INVALIDATED
                    return False, f"Parent evidence {parent_id} is invalid"
        
        record.verification_status = VerificationStatus.VERIFIED
        record.verified_at = datetime.now(timezone.utc)
        record.verified_by = "evidence_provenance_system"
        
        return True, "Evidence verified successfully"
    
    async def create_provenance_chain(
        self,
        decision_id: str,
        evidence_ids: List[str],
    ) -> ProvenanceChain:
        """
        Create a provenance chain linking a decision to its evidence.
        
        Args:
            decision_id: ID of the decision being documented
            evidence_ids: List of evidence IDs supporting the decision
        
        Returns:
            ProvenanceChain with complete audit trail
        """
        chain_id = f"PVC-{uuid.uuid4().hex[:16]}"
        
        evidence_records = []
        all_evidence_ids = set(evidence_ids)
        
        for eid in evidence_ids:
            if eid in self._evidence_store:
                record = self._evidence_store[eid]
                evidence_records.append(record)
                all_evidence_ids.update(record.parent_evidence_ids)
        
        for eid in all_evidence_ids - set(evidence_ids):
            if eid in self._evidence_store:
                evidence_records.append(self._evidence_store[eid])
        
        evidence_records.sort(key=lambda x: x.timestamp)
        
        chain_data = {
            'chain_id': chain_id,
            'decision_id': decision_id,
            'evidence_hashes': [e.data_hash for e in evidence_records],
        }
        chain_hash = self._compute_hash(chain_data)
        
        validation_scores = [e.confidence_score for e in evidence_records]
        validation_score = min(validation_scores) if validation_scores else 0.0
        
        is_complete = all(
            e.verification_status == VerificationStatus.VERIFIED 
            for e in evidence_records
        )
        
        chain = ProvenanceChain(
            chain_id=chain_id,
            decision_id=decision_id,
            created_at=datetime.now(timezone.utc),
            evidence_records=evidence_records,
            chain_hash=chain_hash,
            is_complete=is_complete,
            validation_score=validation_score,
        )
        
        self._provenance_chains[chain_id] = chain
        
        await self._persist_chain(chain)
        
        logger.info(f"Created provenance chain: {chain_id} for decision {decision_id} "
                   f"with {len(evidence_records)} evidence records")
        
        return chain
    
    async def validate_provenance_chain(self, chain_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate an entire provenance chain.
        
        Args:
            chain_id: ID of the chain to validate
        
        Returns:
            Tuple of (is_valid, validation_report)
        """
        if chain_id not in self._provenance_chains:
            return False, {'error': 'Chain not found'}
        
        chain = self._provenance_chains[chain_id]
        
        report = {
            'chain_id': chain_id,
            'decision_id': chain.decision_id,
            'total_evidence': len(chain.evidence_records),
            'verified_evidence': 0,
            'failed_evidence': [],
            'validation_score': 0.0,
            'is_complete': False,
            'issues': [],
        }
        
        for record in chain.evidence_records:
            is_valid, reason = await self.verify_evidence(record.evidence_id)
            if is_valid:
                report['verified_evidence'] += 1
            else:
                report['failed_evidence'].append({
                    'evidence_id': record.evidence_id,
                    'reason': reason,
                })
        
        chain_data = {
            'chain_id': chain.chain_id,
            'decision_id': chain.decision_id,
            'evidence_hashes': [e.data_hash for e in chain.evidence_records],
        }
        expected_hash = self._compute_hash(chain_data)
        
        if expected_hash != chain.chain_hash:
            report['issues'].append('Chain hash mismatch - chain may have been modified')
        
        if report['total_evidence'] > 0:
            report['validation_score'] = report['verified_evidence'] / report['total_evidence']
        
        report['is_complete'] = (
            report['validation_score'] == 1.0 and 
            len(report['issues']) == 0
        )
        
        chain.is_complete = report['is_complete']
        chain.validation_score = report['validation_score']
        
        return report['is_complete'], report
    
    async def get_evidence_lineage(self, evidence_id: str) -> List[EvidenceRecord]:
        """
        Get the complete lineage of an evidence record.
        
        Args:
            evidence_id: ID of evidence to trace
        
        Returns:
            List of all ancestor evidence records
        """
        lineage = []
        visited = set()
        
        async def trace_lineage(eid: str):
            if eid in visited or eid not in self._evidence_store:
                return
            visited.add(eid)
            
            record = self._evidence_store[eid]
            lineage.append(record)
            
            for parent_id in record.parent_evidence_ids:
                await trace_lineage(parent_id)
        
        await trace_lineage(evidence_id)
        
        lineage.sort(key=lambda x: x.timestamp)
        
        return lineage
    
    def get_source_trust_score(self, source_name: str) -> float:
        """Get trust score for a data source."""
        return self._source_trust_scores.get(
            source_name.lower(), 
            self._source_trust_scores['unknown']
        )
    
    def update_source_trust_score(self, source_name: str, score: float):
        """Update trust score for a data source."""
        score = max(0.0, min(1.0, score))
        self._source_trust_scores[source_name.lower()] = score
        logger.info(f"Updated trust score for {source_name}: {score:.2f}")
    
    async def _persist_evidence(self, record: EvidenceRecord):
        """Persist evidence record to storage."""
        evidence_file = self.storage_path / 'evidence' / f"{record.evidence_id}.json"
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(evidence_file, 'w') as f:
            json.dump(record.to_dict(), f, indent=2, default=str)
    
    async def _persist_chain(self, chain: ProvenanceChain):
        """Persist provenance chain to storage."""
        chain_file = self.storage_path / 'chains' / f"{chain.chain_id}.json"
        chain_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(chain_file, 'w') as f:
            json.dump(chain.to_dict(), f, indent=2, default=str)
    
    async def load_from_storage(self):
        """Load all evidence and chains from storage."""
        evidence_dir = self.storage_path / 'evidence'
        if evidence_dir.exists():
            for evidence_file in evidence_dir.glob('*.json'):
                with open(evidence_file, 'r') as f:
                    data = json.load(f)
                    record = EvidenceRecord.from_dict(data)
                    self._evidence_store[record.evidence_id] = record
        
        logger.info(f"Loaded {len(self._evidence_store)} evidence records from storage")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the evidence store."""
        verified_count = sum(
            1 for e in self._evidence_store.values() 
            if e.verification_status == VerificationStatus.VERIFIED
        )
        
        type_counts = {}
        for e in self._evidence_store.values():
            type_name = e.evidence_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            'total_evidence': len(self._evidence_store),
            'verified_evidence': verified_count,
            'total_chains': len(self._provenance_chains),
            'evidence_by_type': type_counts,
            'trusted_sources': len(self._source_trust_scores),
        }
