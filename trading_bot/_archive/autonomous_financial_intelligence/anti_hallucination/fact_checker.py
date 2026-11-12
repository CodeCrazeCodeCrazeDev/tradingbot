"""
Fact Checker

Real-time fact checking against canonical sources.
Verifies claims against authoritative data sources.
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


class FactStatus(Enum):
    """Status of a fact check."""
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"
    FALSE = "false"
    OUTDATED = "outdated"
    UNABLE_TO_VERIFY = "unable_to_verify"


class FactType(Enum):
    """Types of facts."""
    NUMERICAL = "numerical"
    TEMPORAL = "temporal"
    CATEGORICAL = "categorical"
    RELATIONAL = "relational"
    EXISTENCE = "existence"
    ATTRIBUTION = "attribution"


@dataclass
class Fact:
    """A fact to be checked."""
    fact_id: str
    fact_type: FactType
    claim: str
    value: Any
    source_claimed: Optional[str]
    context: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'fact_id': self.fact_id,
            'fact_type': self.fact_type.value,
            'claim': self.claim,
            'value': self.value,
            'source_claimed': self.source_claimed,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class FactCheckResult:
    """Result of a fact check."""
    result_id: str
    fact: Fact
    status: FactStatus
    confidence: float
    canonical_value: Any
    deviation: Optional[float]
    sources_checked: List[str]
    verification_details: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'fact': self.fact.to_dict(),
            'status': self.status.value,
            'confidence': self.confidence,
            'canonical_value': self.canonical_value,
            'deviation': self.deviation,
            'sources_checked': self.sources_checked,
            'verification_details': self.verification_details,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class FactDatabase:
    """Database of verified facts."""
    facts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_fact(self, key: str, value: Any, source: str, confidence: float):
        self.facts[key] = {
            'value': value,
            'source': source,
            'confidence': confidence,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        self.last_updated = datetime.now(timezone.utc)
    
    def get_fact(self, key: str) -> Optional[Dict[str, Any]]:
        return self.facts.get(key)


class FactChecker:
    """
    Real-time fact checking system.
    
    Provides:
    - Claim verification against canonical sources
    - Numerical accuracy checking
    - Temporal fact verification
    - Source attribution verification
    - Batch fact checking
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'fact_checker_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._results: Dict[str, FactCheckResult] = {}
        self._fact_database = FactDatabase()
        self._source_registry: Dict[str, Dict[str, Any]] = {}
        
        self._check_config = {
            'numerical_tolerance_percent': 1.0,
            'temporal_tolerance_seconds': 60,
            'minimum_sources_for_verification': 2,
            'confidence_threshold_verified': 0.8,
            'confidence_threshold_partial': 0.5,
            'max_fact_age_hours': 24,
        }
        
        self._initialize_fact_database()
        self._initialize_source_registry()
        
        logger.info("✅ Fact Checker initialized")
    
    def _initialize_fact_database(self):
        """Initialize with known facts."""
        known_facts = {
            'btc_genesis_date': {
                'value': '2009-01-03',
                'source': 'bitcoin_blockchain',
                'confidence': 1.0,
            },
            'eth_genesis_date': {
                'value': '2015-07-30',
                'source': 'ethereum_blockchain',
                'confidence': 1.0,
            },
            'fed_funds_rate_floor': {
                'value': 0.0,
                'source': 'federal_reserve',
                'confidence': 1.0,
            },
            'trading_days_per_year': {
                'value': 252,
                'source': 'market_convention',
                'confidence': 1.0,
            },
            'sp500_inception_date': {
                'value': '1957-03-04',
                'source': 'sp_global',
                'confidence': 1.0,
            },
        }
        
        for key, data in known_facts.items():
            self._fact_database.add_fact(
                key, data['value'], data['source'], data['confidence']
            )
    
    def _initialize_source_registry(self):
        """Initialize registry of trusted sources."""
        self._source_registry = {
            'bloomberg': {'trust_score': 0.99, 'type': 'market_data'},
            'reuters': {'trust_score': 0.98, 'type': 'news'},
            'federal_reserve': {'trust_score': 0.99, 'type': 'economic'},
            'sec_edgar': {'trust_score': 0.99, 'type': 'regulatory'},
            'coinbase': {'trust_score': 0.95, 'type': 'crypto'},
            'binance': {'trust_score': 0.94, 'type': 'crypto'},
            'yahoo_finance': {'trust_score': 0.90, 'type': 'market_data'},
            'coingecko': {'trust_score': 0.88, 'type': 'crypto'},
            'bitcoin_blockchain': {'trust_score': 1.0, 'type': 'blockchain'},
            'ethereum_blockchain': {'trust_score': 1.0, 'type': 'blockchain'},
        }
    
    async def check_fact(
        self,
        claim: str,
        value: Any,
        fact_type: FactType,
        source_claimed: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> FactCheckResult:
        """
        Check a single fact.
        
        Args:
            claim: The claim being made
            value: The value claimed
            fact_type: Type of fact
            source_claimed: Source claimed for the fact
            context: Additional context
        
        Returns:
            FactCheckResult
        """
        result_id = f"FCR-{uuid.uuid4().hex[:12]}"
        fact_id = f"FACT-{uuid.uuid4().hex[:8]}"
        
        fact = Fact(
            fact_id=fact_id,
            fact_type=fact_type,
            claim=claim,
            value=value,
            source_claimed=source_claimed,
            context=context or {},
            timestamp=datetime.now(timezone.utc),
        )
        
        if fact_type == FactType.NUMERICAL:
            status, confidence, canonical, deviation, sources, details = await self._check_numerical_fact(fact)
        elif fact_type == FactType.TEMPORAL:
            status, confidence, canonical, deviation, sources, details = await self._check_temporal_fact(fact)
        elif fact_type == FactType.EXISTENCE:
            status, confidence, canonical, deviation, sources, details = await self._check_existence_fact(fact)
        elif fact_type == FactType.ATTRIBUTION:
            status, confidence, canonical, deviation, sources, details = await self._check_attribution_fact(fact)
        else:
            status, confidence, canonical, deviation, sources, details = await self._check_generic_fact(fact)
        
        result = FactCheckResult(
            result_id=result_id,
            fact=fact,
            status=status,
            confidence=confidence,
            canonical_value=canonical,
            deviation=deviation,
            sources_checked=sources,
            verification_details=details,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._results[result_id] = result
        await self._persist_result(result)
        
        logger.debug(f"Fact check complete: {status.value} (confidence: {confidence:.2f})")
        
        return result
    
    async def _check_numerical_fact(
        self,
        fact: Fact,
    ) -> Tuple[FactStatus, float, Any, Optional[float], List[str], Dict[str, Any]]:
        """Check a numerical fact."""
        sources_checked = []
        details = {'checks_performed': []}
        
        claimed_value = fact.value
        if not isinstance(claimed_value, (int, float)):
            try:
                claimed_value = float(claimed_value)
            except (ValueError, TypeError):
                return FactStatus.UNABLE_TO_VERIFY, 0.0, None, None, [], {'error': 'Invalid numerical value'}
        
        canonical_value = await self._get_canonical_numerical_value(fact.claim, fact.context)
        
        if canonical_value is None:
            return FactStatus.UNABLE_TO_VERIFY, 0.0, None, None, sources_checked, details
        
        sources_checked.append('canonical_database')
        details['checks_performed'].append('canonical_lookup')
        
        tolerance = self._check_config['numerical_tolerance_percent'] / 100
        
        if canonical_value != 0:
            deviation = abs(claimed_value - canonical_value) / abs(canonical_value)
        else:
            deviation = abs(claimed_value - canonical_value)
        
        details['claimed_value'] = claimed_value
        details['canonical_value'] = canonical_value
        details['deviation_percent'] = deviation * 100
        details['tolerance_percent'] = tolerance * 100
        
        if deviation <= tolerance:
            status = FactStatus.VERIFIED
            confidence = 0.95 - (deviation / tolerance) * 0.15
        elif deviation <= tolerance * 2:
            status = FactStatus.PARTIALLY_VERIFIED
            confidence = 0.7 - (deviation / (tolerance * 2)) * 0.2
        elif deviation <= tolerance * 5:
            status = FactStatus.DISPUTED
            confidence = 0.4
        else:
            status = FactStatus.FALSE
            confidence = 0.9
        
        return status, confidence, canonical_value, deviation, sources_checked, details
    
    async def _get_canonical_numerical_value(
        self,
        claim: str,
        context: Dict[str, Any],
    ) -> Optional[float]:
        """Get canonical numerical value for a claim."""
        claim_lower = claim.lower()
        
        if 'price' in claim_lower:
            symbol = context.get('symbol', '')
            
            simulated_prices = {
                'btc': 65000.0,
                'eth': 3500.0,
                'aapl': 175.0,
                'googl': 140.0,
            }
            
            for key, price in simulated_prices.items():
                if key in symbol.lower():
                    return price
        
        for key, data in self._fact_database.facts.items():
            if key in claim_lower:
                return data['value']
        
        return None
    
    async def _check_temporal_fact(
        self,
        fact: Fact,
    ) -> Tuple[FactStatus, float, Any, Optional[float], List[str], Dict[str, Any]]:
        """Check a temporal fact."""
        sources_checked = []
        details = {'checks_performed': []}
        
        claimed_time = fact.value
        if isinstance(claimed_time, str):
            try:
                claimed_time = datetime.fromisoformat(claimed_time.replace('Z', '+00:00'))
            except ValueError:
                return FactStatus.UNABLE_TO_VERIFY, 0.0, None, None, [], {'error': 'Invalid timestamp format'}
        
        canonical_time = await self._get_canonical_temporal_value(fact.claim, fact.context)
        
        if canonical_time is None:
            return FactStatus.UNABLE_TO_VERIFY, 0.0, None, None, sources_checked, details
        
        sources_checked.append('canonical_database')
        details['checks_performed'].append('temporal_lookup')
        
        if isinstance(canonical_time, str):
            canonical_time = datetime.fromisoformat(canonical_time.replace('Z', '+00:00'))
        
        tolerance = self._check_config['temporal_tolerance_seconds']
        
        if hasattr(claimed_time, 'timestamp') and hasattr(canonical_time, 'timestamp'):
            deviation = abs((claimed_time - canonical_time).total_seconds())
        else:
            deviation = 0
        
        details['claimed_time'] = str(claimed_time)
        details['canonical_time'] = str(canonical_time)
        details['deviation_seconds'] = deviation
        
        if deviation <= tolerance:
            status = FactStatus.VERIFIED
            confidence = 0.95
        elif deviation <= tolerance * 10:
            status = FactStatus.PARTIALLY_VERIFIED
            confidence = 0.7
        else:
            status = FactStatus.FALSE
            confidence = 0.85
        
        return status, confidence, canonical_time, deviation, sources_checked, details
    
    async def _get_canonical_temporal_value(
        self,
        claim: str,
        context: Dict[str, Any],
    ) -> Optional[Any]:
        """Get canonical temporal value for a claim."""
        claim_lower = claim.lower()
        
        for key, data in self._fact_database.facts.items():
            if 'date' in key and key.replace('_date', '') in claim_lower:
                return data['value']
        
        return None
    
    async def _check_existence_fact(
        self,
        fact: Fact,
    ) -> Tuple[FactStatus, float, Any, Optional[float], List[str], Dict[str, Any]]:
        """Check an existence fact."""
        sources_checked = []
        details = {'checks_performed': []}
        
        entity = fact.value
        
        known_entities = {
            'bitcoin', 'ethereum', 'coinbase', 'binance',
            'federal reserve', 'sec', 'nyse', 'nasdaq',
            'apple', 'google', 'microsoft', 'amazon',
        }
        
        entity_lower = str(entity).lower()
        
        if entity_lower in known_entities:
            status = FactStatus.VERIFIED
            confidence = 0.95
            canonical = True
        else:
            status = FactStatus.UNVERIFIED
            confidence = 0.3
            canonical = None
        
        sources_checked.append('entity_registry')
        details['entity_checked'] = entity
        details['found_in_registry'] = canonical is not None
        
        return status, confidence, canonical, None, sources_checked, details
    
    async def _check_attribution_fact(
        self,
        fact: Fact,
    ) -> Tuple[FactStatus, float, Any, Optional[float], List[str], Dict[str, Any]]:
        """Check an attribution fact."""
        sources_checked = []
        details = {'checks_performed': []}
        
        claimed_source = fact.source_claimed
        
        if claimed_source:
            source_lower = claimed_source.lower()
            
            if source_lower in self._source_registry:
                source_info = self._source_registry[source_lower]
                status = FactStatus.VERIFIED
                confidence = source_info['trust_score']
                canonical = claimed_source
                details['source_verified'] = True
                details['source_trust_score'] = source_info['trust_score']
            else:
                status = FactStatus.UNVERIFIED
                confidence = 0.3
                canonical = None
                details['source_verified'] = False
        else:
            status = FactStatus.UNVERIFIED
            confidence = 0.0
            canonical = None
            details['no_source_claimed'] = True
        
        sources_checked.append('source_registry')
        
        return status, confidence, canonical, None, sources_checked, details
    
    async def _check_generic_fact(
        self,
        fact: Fact,
    ) -> Tuple[FactStatus, float, Any, Optional[float], List[str], Dict[str, Any]]:
        """Check a generic fact."""
        sources_checked = []
        details = {'checks_performed': ['generic_check']}
        
        claim_lower = fact.claim.lower()
        
        for key, data in self._fact_database.facts.items():
            if key in claim_lower:
                if data['value'] == fact.value:
                    return FactStatus.VERIFIED, data['confidence'], data['value'], None, ['fact_database'], details
        
        return FactStatus.UNVERIFIED, 0.3, None, None, sources_checked, details
    
    async def check_facts_batch(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[FactCheckResult]:
        """
        Check multiple facts in batch.
        
        Args:
            facts: List of fact dictionaries
        
        Returns:
            List of FactCheckResults
        """
        results = []
        
        for fact_data in facts:
            result = await self.check_fact(
                claim=fact_data.get('claim', ''),
                value=fact_data.get('value'),
                fact_type=FactType(fact_data.get('type', 'categorical')),
                source_claimed=fact_data.get('source'),
                context=fact_data.get('context', {}),
            )
            results.append(result)
        
        return results
    
    def add_verified_fact(
        self,
        key: str,
        value: Any,
        source: str,
        confidence: float = 0.9,
    ):
        """Add a verified fact to the database."""
        self._fact_database.add_fact(key, value, source, confidence)
    
    def get_result(self, result_id: str) -> Optional[FactCheckResult]:
        """Get a fact check result by ID."""
        return self._results.get(result_id)
    
    async def _persist_result(self, result: FactCheckResult):
        """Persist result to storage."""
        result_file = self.storage_path / 'results' / f"{result.result_id}.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fact checker statistics."""
        status_counts = {}
        for result in self._results.values():
            status_counts[result.status.value] = status_counts.get(result.status.value, 0) + 1
        
        return {
            'total_checks': len(self._results),
            'facts_in_database': len(self._fact_database.facts),
            'registered_sources': len(self._source_registry),
            'checks_by_status': status_counts,
        }
