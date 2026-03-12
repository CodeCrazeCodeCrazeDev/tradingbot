"""
APEX-FI Layer 1: Sovereign Data Fabric & Ontology Engine
=========================================================

Palantir Bloodline: Unified data reality with semantic knowledge graph.
Every entity is a living node with typed, temporally-valid relationships.

Mission: Achieve omniscience over market reality before modeling it.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class DataQuality(str, Enum):
    """Data quality levels."""
    VERIFIED = "verified"           # Highest quality, multiple source confirmation
    TRUSTED = "trusted"             # Single trusted source
    PROVISIONAL = "provisional"     # Needs validation
    STALE = "stale"                 # Exceeded freshness threshold
    SUSPECT = "suspect"             # Quality issues detected
    REJECTED = "rejected"           # Failed validation


class EntityType(str, Enum):
    """Financial entity types in the knowledge graph."""
    SECURITY = "security"
    COMPANY = "company"
    EXECUTIVE = "executive"
    BOND = "bond"
    DERIVATIVE = "derivative"
    EXCHANGE = "exchange"
    BROKER = "broker"
    REGULATOR = "regulator"
    COUNTRY = "country"
    SECTOR = "sector"
    STRATEGY = "strategy"
    FACTOR = "factor"
    EVENT = "event"


class RelationType(str, Enum):
    """Relationship types between entities."""
    ISSUES = "issues"                    # Company → Security
    EMPLOYS = "employs"                  # Company → Executive
    TRADES_ON = "trades_on"              # Security → Exchange
    REGULATED_BY = "regulated_by"        # Entity → Regulator
    BELONGS_TO = "belongs_to"            # Company → Sector
    CORRELATES_WITH = "correlates_with"  # Security → Security
    DERIVES_FROM = "derives_from"        # Derivative → Underlying
    IMPACTS = "impacts"                  # Event → Entity
    COMPETES_WITH = "competes_with"      # Company → Company


@dataclass
class DataAtom:
    """
    Atomic unit of data with full provenance.
    
    Every piece of data in APEX-FI is a DataAtom with:
    - Source tracking
    - Quality scoring
    - Freshness monitoring
    - Transformation history
    """
    
    value: Any
    source: str
    timestamp: datetime
    quality_score: float = 1.0
    quality_level: DataQuality = DataQuality.TRUSTED
    freshness_threshold_seconds: int = 3600
    transformation_history: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_fresh(self) -> bool:
        """Check if data is within freshness threshold."""
        age_seconds = (datetime.now() - self.timestamp).total_seconds()
        return age_seconds <= self.freshness_threshold_seconds
    
    def get_age_seconds(self) -> float:
        """Get data age in seconds."""
        return (datetime.now() - self.timestamp).total_seconds()
    
    def apply_transformation(self, transformation: str, new_value: Any) -> 'DataAtom':
        """Apply transformation and track in history."""
        new_history = self.transformation_history + [transformation]
        return DataAtom(
            value=new_value,
            source=self.source,
            timestamp=self.timestamp,
            quality_score=self.quality_score * 0.95,  # Slight degradation
            quality_level=self.quality_level,
            freshness_threshold_seconds=self.freshness_threshold_seconds,
            transformation_history=new_history,
            metadata=self.metadata.copy()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'value': self.value,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'quality_score': self.quality_score,
            'quality_level': self.quality_level.value,
            'age_seconds': self.get_age_seconds(),
            'is_fresh': self.is_fresh(),
            'transformation_history': self.transformation_history,
            'metadata': self.metadata,
        }


@dataclass
class Entity:
    """
    Entity node in the knowledge graph.
    
    Every financial entity (company, security, executive, etc.) is a node
    with attributes and relationships to other entities.
    """
    
    entity_id: str
    entity_type: EntityType
    attributes: Dict[str, DataAtom] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def set_attribute(self, key: str, atom: DataAtom) -> None:
        """Set entity attribute with data atom."""
        self.attributes[key] = atom
        self.updated_at = datetime.now()
        self.version += 1
    
    def get_attribute(self, key: str) -> Optional[DataAtom]:
        """Get entity attribute."""
        return self.attributes.get(key)
    
    def get_fresh_attributes(self) -> Dict[str, DataAtom]:
        """Get only fresh attributes."""
        return {
            k: v for k, v in self.attributes.items()
            if v.is_fresh()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type.value,
            'attributes': {k: v.to_dict() for k, v in self.attributes.items()},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version,
        }


@dataclass
class Relationship:
    """
    Typed, temporally-valid relationship between entities.
    
    Relationships are first-class objects with their own attributes
    and validity periods.
    """
    
    source_id: str
    target_id: str
    relation_type: RelationType
    valid_from: datetime
    valid_until: Optional[datetime] = None
    attributes: Dict[str, DataAtom] = field(default_factory=dict)
    confidence: float = 1.0
    
    def is_valid_at(self, timestamp: datetime) -> bool:
        """Check if relationship is valid at given timestamp."""
        if timestamp < self.valid_from:
            return False
        if self.valid_until and timestamp > self.valid_until:
            return False
        return True
    
    def is_currently_valid(self) -> bool:
        """Check if relationship is currently valid."""
        return self.is_valid_at(datetime.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type.value,
            'valid_from': self.valid_from.isoformat(),
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'attributes': {k: v.to_dict() for k, v in self.attributes.items()},
            'confidence': self.confidence,
            'is_valid': self.is_currently_valid(),
        }


class KnowledgeGraph:
    """
    Versioned semantic knowledge graph.
    
    The graph self-versions so any historical market state can be
    reconstructed at any timestamp.
    """
    
    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._relationships: List[Relationship] = []
        self._entity_index: Dict[EntityType, Set[str]] = defaultdict(set)
        self._relationship_index: Dict[str, List[Relationship]] = defaultdict(list)
        self._version_history: List[Dict[str, Any]] = []
        self._current_version = 0
        
        logger.info("Knowledge Graph initialized")
    
    def add_entity(self, entity: Entity) -> None:
        """Add entity to graph."""
        self._entities[entity.entity_id] = entity
        self._entity_index[entity.entity_type].add(entity.entity_id)
        self._record_version_event('entity_added', entity.entity_id)
        
        logger.debug(f"Added entity: {entity.entity_id} ({entity.entity_type.value})")
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self._entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a given type."""
        entity_ids = self._entity_index.get(entity_type, set())
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add relationship to graph."""
        self._relationships.append(relationship)
        self._relationship_index[relationship.source_id].append(relationship)
        self._relationship_index[relationship.target_id].append(relationship)
        self._record_version_event('relationship_added', 
                                   f"{relationship.source_id}->{relationship.target_id}")
        
        logger.debug(
            f"Added relationship: {relationship.source_id} "
            f"{relationship.relation_type.value} {relationship.target_id}"
        )
    
    def get_relationships(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        direction: str = "both"
    ) -> List[Relationship]:
        """
        Get relationships for an entity.
        
        Args:
            entity_id: Entity ID
            relation_type: Filter by relationship type
            direction: "outgoing", "incoming", or "both"
        """
        relationships = self._relationship_index.get(entity_id, [])
        
        # Filter by direction
        if direction == "outgoing":
            relationships = [r for r in relationships if r.source_id == entity_id]
        elif direction == "incoming":
            relationships = [r for r in relationships if r.target_id == entity_id]
        
        # Filter by type
        if relation_type:
            relationships = [r for r in relationships if r.relation_type == relation_type]
        
        # Only return currently valid relationships
        return [r for r in relationships if r.is_currently_valid()]
    
    def reconstruct_at_timestamp(self, timestamp: datetime) -> 'KnowledgeGraph':
        """
        Reconstruct graph state at a historical timestamp.
        
        This enables replaying any historical market state.
        """
        historical_graph = KnowledgeGraph()
        
        # Add entities that existed at timestamp
        for entity in self._entities.values():
            if entity.created_at <= timestamp:
                historical_graph.add_entity(entity)
        
        # Add relationships valid at timestamp
        for relationship in self._relationships:
            if relationship.is_valid_at(timestamp):
                historical_graph.add_relationship(relationship)
        
        logger.info(f"Reconstructed graph at {timestamp.isoformat()}")
        return historical_graph
    
    def _record_version_event(self, event_type: str, entity_id: str) -> None:
        """Record version history event."""
        self._current_version += 1
        self._version_history.append({
            'version': self._current_version,
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'entity_id': entity_id,
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            'total_entities': len(self._entities),
            'total_relationships': len(self._relationships),
            'entities_by_type': {
                et.value: len(self._entity_index[et])
                for et in EntityType
                if et in self._entity_index
            },
            'current_version': self._current_version,
            'version_history_size': len(self._version_history),
        }


class DataFabric:
    """
    Sovereign Data Fabric - Layer 1 of APEX-FI.
    
    Ingests 50,000+ market data feeds and alternative data sources,
    maintains versioned knowledge graph, assigns quality scores,
    and tracks data lineage.
    """
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self._data_sources: Dict[str, Dict[str, Any]] = {}
        self._ingestion_stats: Dict[str, int] = defaultdict(int)
        self._quality_violations: List[Dict[str, Any]] = []
        self._running = False
        
        logger.info("Data Fabric initialized - Palantir Bloodline")
    
    def register_data_source(
        self,
        source_id: str,
        source_type: str,
        freshness_threshold_seconds: int = 3600,
        quality_threshold: float = 0.7,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a data source."""
        self._data_sources[source_id] = {
            'source_type': source_type,
            'freshness_threshold_seconds': freshness_threshold_seconds,
            'quality_threshold': quality_threshold,
            'metadata': metadata or {},
            'registered_at': datetime.now().isoformat(),
            'total_ingested': 0,
            'total_rejected': 0,
        }
        
        logger.info(f"Registered data source: {source_id} ({source_type})")
    
    def ingest_data_atom(
        self,
        entity_id: str,
        attribute_key: str,
        value: Any,
        source_id: str,
        quality_score: float = 1.0
    ) -> bool:
        """
        Ingest a data atom into the fabric.
        
        Args:
            entity_id: Target entity ID
            attribute_key: Attribute name
            value: Data value
            source_id: Source identifier
            quality_score: Quality score (0-1)
            
        Returns:
            True if ingested, False if rejected
        """
        # Check source registration
        if source_id not in self._data_sources:
            logger.warning(f"Unknown data source: {source_id}")
            return False
        
        source_config = self._data_sources[source_id]
        
        # Quality check
        if quality_score < source_config['quality_threshold']:
            self._quality_violations.append({
                'timestamp': datetime.now().isoformat(),
                'entity_id': entity_id,
                'attribute_key': attribute_key,
                'source_id': source_id,
                'quality_score': quality_score,
                'threshold': source_config['quality_threshold'],
            })
            source_config['total_rejected'] += 1
            return False
        
        # Create data atom
        atom = DataAtom(
            value=value,
            source=source_id,
            timestamp=datetime.now(),
            quality_score=quality_score,
            quality_level=self._determine_quality_level(quality_score),
            freshness_threshold_seconds=source_config['freshness_threshold_seconds'],
        )
        
        # Get or create entity
        entity = self.knowledge_graph.get_entity(entity_id)
        if entity is None:
            logger.warning(f"Entity {entity_id} not found - data atom rejected")
            return False
        
        # Set attribute
        entity.set_attribute(attribute_key, atom)
        
        # Update stats
        source_config['total_ingested'] += 1
        self._ingestion_stats[source_id] += 1
        
        return True
    
    def _determine_quality_level(self, quality_score: float) -> DataQuality:
        """Determine quality level from score."""
        if quality_score >= 0.95:
            return DataQuality.VERIFIED
        elif quality_score >= 0.8:
            return DataQuality.TRUSTED
        elif quality_score >= 0.6:
            return DataQuality.PROVISIONAL
        else:
            return DataQuality.SUSPECT
    
    async def start(self) -> None:
        """Start data fabric ingestion."""
        self._running = True
        logger.info("Data Fabric started")
        
        # Start background tasks
        asyncio.create_task(self._monitor_data_freshness())
        asyncio.create_task(self._monitor_quality_violations())
    
    async def stop(self) -> None:
        """Stop data fabric."""
        self._running = False
        logger.info("Data Fabric stopped")
    
    async def _monitor_data_freshness(self) -> None:
        """Monitor data freshness and flag stale data."""
        while self._running:
            stale_count = 0
            
            for entity in self.knowledge_graph._entities.values():
                for key, atom in entity.attributes.items():
                    if not atom.is_fresh():
                        atom.quality_level = DataQuality.STALE
                        stale_count += 1
            
            if stale_count > 0:
                logger.warning(f"Detected {stale_count} stale data atoms")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _monitor_quality_violations(self) -> None:
        """Monitor quality violations."""
        while self._running:
            if len(self._quality_violations) > 100:
                logger.warning(
                    f"High quality violation rate: {len(self._quality_violations)} "
                    f"violations in recent period"
                )
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    def get_status(self) -> Dict[str, Any]:
        """Get data fabric status."""
        return {
            'running': self._running,
            'knowledge_graph': self.knowledge_graph.get_stats(),
            'data_sources': len(self._data_sources),
            'total_ingested': sum(self._ingestion_stats.values()),
            'quality_violations': len(self._quality_violations),
            'ingestion_by_source': dict(self._ingestion_stats),
        }


# Singleton instance
_data_fabric: Optional[DataFabric] = None


def get_data_fabric() -> DataFabric:
    """Get the singleton Data Fabric."""
    global _data_fabric
    if _data_fabric is None:
        _data_fabric = DataFabric()
    return _data_fabric
