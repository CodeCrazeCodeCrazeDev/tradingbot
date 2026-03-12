"""
APEX-FI Layer 1: Sovereign Data Fabric & Ontology Engine
=========================================================

Palantir-inspired unified data reality with semantic knowledge graph,
data quality scoring, lineage tracking, and versioned temporal validity.

Mission: Achieve omniscience over market reality before modeling it.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    SECURITY = "security"
    COMPANY = "company"
    EXECUTIVE = "executive"
    DERIVATIVE = "derivative"
    BOND = "bond"
    CURRENCY = "currency"
    COMMODITY = "commodity"
    INDEX = "index"
    REGULATORY_BODY = "regulatory_body"
    GEOPOLITICAL_ACTOR = "geopolitical_actor"
    EXCHANGE = "exchange"
    BROKER = "broker"
    FUND = "fund"


class RelationType(str, Enum):
    """Types of relationships in the knowledge graph."""
    OWNS = "owns"
    ISSUES = "issues"
    TRADES_ON = "trades_on"
    REGULATES = "regulates"
    CORRELATES_WITH = "correlates_with"
    DERIVES_FROM = "derives_from"
    COMPETES_WITH = "competes_with"
    SUPPLIES_TO = "supplies_to"
    EMPLOYED_BY = "employed_by"
    INFLUENCES = "influences"
    HEDGES = "hedges"


class DataSource(str, Enum):
    """Data source types."""
    MARKET_DATA = "market_data"
    ALTERNATIVE_DATA = "alternative_data"
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    SATELLITE = "satellite"
    CREDIT_CARD = "credit_card"
    JOB_POSTINGS = "job_postings"
    GEOLOCATION = "geolocation"
    REGULATORY_FILINGS = "regulatory_filings"
    EARNINGS_CALLS = "earnings_calls"
    PATENT_FILINGS = "patent_filings"
    SHIPPING_DATA = "shipping_data"


@dataclass
class DataQuality:
    """Data quality metrics."""
    trust_score: float  # 0.0 to 1.0
    quality_score: float  # 0.0 to 1.0
    freshness_seconds: float
    completeness: float  # 0.0 to 1.0
    accuracy_estimate: float  # 0.0 to 1.0
    source_reliability: float  # 0.0 to 1.0
    
    def overall_score(self) -> float:
        """Calculate weighted overall quality score."""
        return (
            0.25 * self.trust_score +
            0.20 * self.quality_score +
            0.20 * (1.0 - min(self.freshness_seconds / 3600, 1.0)) +
            0.15 * self.completeness +
            0.10 * self.accuracy_estimate +
            0.10 * self.source_reliability
        )


@dataclass
class DataLineage:
    """Data lineage tracking."""
    data_id: str
    source: DataSource
    ingestion_timestamp: datetime
    transformation_history: List[Dict[str, Any]] = field(default_factory=list)
    parent_data_ids: List[str] = field(default_factory=list)
    quality: Optional[DataQuality] = None
    
    def add_transformation(self, operation: str, metadata: Dict[str, Any]) -> None:
        """Record a transformation operation."""
        self.transformation_history.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'metadata': metadata,
        })
    
    def get_provenance_hash(self) -> str:
        """Generate cryptographic hash of full provenance."""
        provenance_data = {
            'data_id': self.data_id,
            'source': self.source.value,
            'ingestion_timestamp': self.ingestion_timestamp.isoformat(),
            'transformations': self.transformation_history,
            'parents': sorted(self.parent_data_ids),
        }
        
        provenance_json = json.dumps(provenance_data, sort_keys=True)
        return hashlib.sha256(provenance_json.encode()).hexdigest()


@dataclass
class EntityNode:
    """Node in the semantic knowledge graph."""
    entity_id: str
    entity_type: EntityType
    attributes: Dict[str, Any]
    valid_from: datetime
    valid_to: Optional[datetime] = None
    data_lineage: Optional[DataLineage] = None
    version: int = 1
    
    def is_valid_at(self, timestamp: datetime) -> bool:
        """Check if entity is valid at given timestamp."""
        if timestamp < self.valid_from:
            return False
        if self.valid_to and timestamp > self.valid_to:
            return False
        return True


@dataclass
class RelationshipEdge:
    """Edge in the semantic knowledge graph."""
    relationship_id: str
    relation_type: RelationType
    source_entity_id: str
    target_entity_id: str
    attributes: Dict[str, Any]
    valid_from: datetime
    valid_to: Optional[datetime] = None
    strength: float = 1.0  # 0.0 to 1.0
    data_lineage: Optional[DataLineage] = None
    
    def is_valid_at(self, timestamp: datetime) -> bool:
        """Check if relationship is valid at given timestamp."""
        if timestamp < self.valid_from:
            return False
        if self.valid_to and timestamp > self.valid_to:
            return False
        return True


class SemanticKnowledgeGraph:
    """
    Versioned semantic knowledge graph.
    
    Every entity and relationship is temporally valid.
    Graph can be reconstructed at any historical timestamp.
    """
    
    def __init__(self):
        self.entities: Dict[str, List[EntityNode]] = {}  # entity_id -> versions
        self.relationships: Dict[str, List[RelationshipEdge]] = {}  # relationship_id -> versions
        self.entity_index: Dict[EntityType, Set[str]] = {et: set() for et in EntityType}
        self.relationship_index: Dict[RelationType, Set[str]] = {rt: set() for rt in RelationType}
        self._version = 1
        
        logger.info("Semantic Knowledge Graph initialized")
    
    def add_entity(self, entity: EntityNode) -> None:
        """Add entity to graph."""
        if entity.entity_id not in self.entities:
            self.entities[entity.entity_id] = []
        
        entity.version = len(self.entities[entity.entity_id]) + 1
        self.entities[entity.entity_id].append(entity)
        self.entity_index[entity.entity_type].add(entity.entity_id)
        
        logger.debug(f"Added entity: {entity.entity_id} (type: {entity.entity_type.value}, version: {entity.version})")
    
    def add_relationship(self, relationship: RelationshipEdge) -> None:
        """Add relationship to graph."""
        if relationship.relationship_id not in self.relationships:
            self.relationships[relationship.relationship_id] = []
        
        self.relationships[relationship.relationship_id].append(relationship)
        self.relationship_index[relationship.relation_type].add(relationship.relationship_id)
        
        logger.debug(f"Added relationship: {relationship.relationship_id} (type: {relationship.relation_type.value})")
    
    def get_entity_at(self, entity_id: str, timestamp: datetime) -> Optional[EntityNode]:
        """Get entity valid at specific timestamp."""
        if entity_id not in self.entities:
            return None
        
        for entity in reversed(self.entities[entity_id]):
            if entity.is_valid_at(timestamp):
                return entity
        
        return None
    
    def get_relationships_for_entity(
        self,
        entity_id: str,
        timestamp: datetime,
        relation_type: Optional[RelationType] = None
    ) -> List[RelationshipEdge]:
        """Get all relationships for an entity at a specific timestamp."""
        results = []
        
        for rel_id, versions in self.relationships.items():
            for rel in reversed(versions):
                if not rel.is_valid_at(timestamp):
                    continue
                
                if rel.source_entity_id != entity_id and rel.target_entity_id != entity_id:
                    continue
                
                if relation_type and rel.relation_type != relation_type:
                    continue
                
                results.append(rel)
                break
        
        return results
    
    def query_entities_by_type(
        self,
        entity_type: EntityType,
        timestamp: datetime
    ) -> List[EntityNode]:
        """Query all entities of a specific type valid at timestamp."""
        results = []
        
        for entity_id in self.entity_index[entity_type]:
            entity = self.get_entity_at(entity_id, timestamp)
            if entity:
                results.append(entity)
        
        return results
    
    def reconstruct_at_timestamp(self, timestamp: datetime) -> Tuple[List[EntityNode], List[RelationshipEdge]]:
        """Reconstruct entire graph state at a specific timestamp."""
        entities = []
        relationships = []
        
        for entity_id in self.entities:
            entity = self.get_entity_at(entity_id, timestamp)
            if entity:
                entities.append(entity)
        
        for rel_id, versions in self.relationships.items():
            for rel in reversed(versions):
                if rel.is_valid_at(timestamp):
                    relationships.append(rel)
                    break
        
        logger.info(f"Reconstructed graph at {timestamp}: {len(entities)} entities, {len(relationships)} relationships")
        return entities, relationships


class DataQualityScorer:
    """
    Data quality scoring engine.
    
    Assigns trust and quality scores to every data atom.
    Scores propagate through the knowledge graph.
    """
    
    def __init__(self):
        self.source_reliability: Dict[DataSource, float] = {
            DataSource.MARKET_DATA: 0.95,
            DataSource.REGULATORY_FILINGS: 0.90,
            DataSource.ALTERNATIVE_DATA: 0.75,
            DataSource.NEWS: 0.70,
            DataSource.SOCIAL_MEDIA: 0.60,
            DataSource.SATELLITE: 0.80,
            DataSource.CREDIT_CARD: 0.85,
            DataSource.JOB_POSTINGS: 0.75,
            DataSource.GEOLOCATION: 0.80,
            DataSource.EARNINGS_CALLS: 0.85,
            DataSource.PATENT_FILINGS: 0.80,
            DataSource.SHIPPING_DATA: 0.75,
        }
        
        logger.info("Data Quality Scorer initialized")
    
    def score_data(
        self,
        source: DataSource,
        freshness_seconds: float,
        completeness: float,
        accuracy_estimate: Optional[float] = None
    ) -> DataQuality:
        """
        Score data quality.
        
        Args:
            source: Data source type
            freshness_seconds: Age of data in seconds
            completeness: Completeness ratio (0.0 to 1.0)
            accuracy_estimate: Optional accuracy estimate
            
        Returns:
            DataQuality object
        """
        source_reliability = self.source_reliability.get(source, 0.5)
        
        # Trust score based on source and freshness
        freshness_factor = max(0.0, 1.0 - (freshness_seconds / 3600))
        trust_score = source_reliability * (0.7 + 0.3 * freshness_factor)
        
        # Quality score based on completeness and accuracy
        if accuracy_estimate is None:
            accuracy_estimate = source_reliability
        
        quality_score = 0.6 * completeness + 0.4 * accuracy_estimate
        
        return DataQuality(
            trust_score=trust_score,
            quality_score=quality_score,
            freshness_seconds=freshness_seconds,
            completeness=completeness,
            accuracy_estimate=accuracy_estimate,
            source_reliability=source_reliability,
        )
    
    def propagate_quality(
        self,
        parent_qualities: List[DataQuality],
        transformation_complexity: float = 0.5
    ) -> DataQuality:
        """
        Propagate quality scores through transformations.
        
        Quality degrades through complex transformations.
        """
        if not parent_qualities:
            return DataQuality(0.5, 0.5, 0.0, 0.5, 0.5, 0.5)
        
        # Average parent qualities with degradation factor
        degradation = 1.0 - (0.1 * transformation_complexity)
        
        avg_trust = sum(q.trust_score for q in parent_qualities) / len(parent_qualities)
        avg_quality = sum(q.quality_score for q in parent_qualities) / len(parent_qualities)
        max_freshness = max(q.freshness_seconds for q in parent_qualities)
        avg_completeness = sum(q.completeness for q in parent_qualities) / len(parent_qualities)
        avg_accuracy = sum(q.accuracy_estimate for q in parent_qualities) / len(parent_qualities)
        avg_reliability = sum(q.source_reliability for q in parent_qualities) / len(parent_qualities)
        
        return DataQuality(
            trust_score=avg_trust * degradation,
            quality_score=avg_quality * degradation,
            freshness_seconds=max_freshness,
            completeness=avg_completeness * degradation,
            accuracy_estimate=avg_accuracy * degradation,
            source_reliability=avg_reliability,
        )


class DataLineageTracker:
    """
    Data lineage tracking system.
    
    Every model prediction can be traced back to exact data atoms.
    """
    
    def __init__(self):
        self.lineage_db: Dict[str, DataLineage] = {}
        logger.info("Data Lineage Tracker initialized")
    
    def create_lineage(
        self,
        data_id: str,
        source: DataSource,
        quality: Optional[DataQuality] = None
    ) -> DataLineage:
        """Create new data lineage record."""
        lineage = DataLineage(
            data_id=data_id,
            source=source,
            ingestion_timestamp=datetime.now(),
            quality=quality,
        )
        
        self.lineage_db[data_id] = lineage
        return lineage
    
    def add_derived_data(
        self,
        data_id: str,
        source: DataSource,
        parent_ids: List[str],
        transformation: str,
        metadata: Dict[str, Any],
        quality: Optional[DataQuality] = None
    ) -> DataLineage:
        """Create lineage for derived data."""
        lineage = DataLineage(
            data_id=data_id,
            source=source,
            ingestion_timestamp=datetime.now(),
            parent_data_ids=parent_ids,
            quality=quality,
        )
        
        lineage.add_transformation(transformation, metadata)
        self.lineage_db[data_id] = lineage
        
        return lineage
    
    def get_lineage(self, data_id: str) -> Optional[DataLineage]:
        """Get lineage for data ID."""
        return self.lineage_db.get(data_id)
    
    def trace_to_source(self, data_id: str) -> List[DataLineage]:
        """Trace data back to original sources."""
        lineage = self.get_lineage(data_id)
        if not lineage:
            return []
        
        trace = [lineage]
        
        for parent_id in lineage.parent_data_ids:
            trace.extend(self.trace_to_source(parent_id))
        
        return trace


class OntologyEngine:
    """
    Ontology Engine - manages the semantic structure of the knowledge graph.
    
    Defines entity types, relationship types, and validation rules.
    """
    
    def __init__(self):
        self.entity_schemas: Dict[EntityType, Dict[str, type]] = {}
        self.relationship_schemas: Dict[RelationType, Dict[str, Any]] = {}
        self._initialize_schemas()
        
        logger.info("Ontology Engine initialized")
    
    def _initialize_schemas(self) -> None:
        """Initialize entity and relationship schemas."""
        # Define required attributes for each entity type
        self.entity_schemas[EntityType.SECURITY] = {
            'ticker': str,
            'exchange': str,
            'sector': str,
            'market_cap': float,
        }
        
        self.entity_schemas[EntityType.COMPANY] = {
            'name': str,
            'industry': str,
            'country': str,
        }
        
        # Define relationship constraints
        self.relationship_schemas[RelationType.OWNS] = {
            'valid_sources': [EntityType.COMPANY, EntityType.FUND, EntityType.EXECUTIVE],
            'valid_targets': [EntityType.SECURITY, EntityType.COMPANY],
        }
        
        self.relationship_schemas[RelationType.TRADES_ON] = {
            'valid_sources': [EntityType.SECURITY],
            'valid_targets': [EntityType.EXCHANGE],
        }
    
    def validate_entity(self, entity: EntityNode) -> Tuple[bool, Optional[str]]:
        """Validate entity against schema."""
        if entity.entity_type not in self.entity_schemas:
            return True, None  # No schema defined, allow
        
        schema = self.entity_schemas[entity.entity_type]
        
        for attr_name, attr_type in schema.items():
            if attr_name not in entity.attributes:
                return False, f"Missing required attribute: {attr_name}"
            
            if not isinstance(entity.attributes[attr_name], attr_type):
                return False, f"Invalid type for {attr_name}: expected {attr_type.__name__}"
        
        return True, None
    
    def validate_relationship(
        self,
        relationship: RelationshipEdge,
        source_entity: EntityNode,
        target_entity: EntityNode
    ) -> Tuple[bool, Optional[str]]:
        """Validate relationship against schema."""
        if relationship.relation_type not in self.relationship_schemas:
            return True, None
        
        schema = self.relationship_schemas[relationship.relation_type]
        
        if 'valid_sources' in schema:
            if source_entity.entity_type not in schema['valid_sources']:
                return False, f"Invalid source entity type: {source_entity.entity_type.value}"
        
        if 'valid_targets' in schema:
            if target_entity.entity_type not in schema['valid_targets']:
                return False, f"Invalid target entity type: {target_entity.entity_type.value}"
        
        return True, None


class DataFabric:
    """
    Sovereign Data Fabric - Master coordinator for Layer 1.
    
    Integrates knowledge graph, quality scoring, and lineage tracking.
    Provides unified interface for data ingestion and querying.
    """
    
    def __init__(self):
        self.knowledge_graph = SemanticKnowledgeGraph()
        self.quality_scorer = DataQualityScorer()
        self.lineage_tracker = DataLineageTracker()
        self.ontology = OntologyEngine()
        
        self._ingestion_count = 0
        self._quality_threshold = 0.5
        
        logger.info("Data Fabric initialized - Layer 1 operational")
    
    def ingest_entity(
        self,
        entity_id: str,
        entity_type: EntityType,
        attributes: Dict[str, Any],
        source: DataSource,
        freshness_seconds: float = 0.0,
        completeness: float = 1.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Ingest entity into the data fabric.
        
        Returns:
            (success, error_message)
        """
        # Score data quality
        quality = self.quality_scorer.score_data(
            source=source,
            freshness_seconds=freshness_seconds,
            completeness=completeness,
        )
        
        # Check quality threshold
        if quality.overall_score() < self._quality_threshold:
            return False, f"Data quality {quality.overall_score():.2f} below threshold {self._quality_threshold}"
        
        # Create lineage
        data_id = f"{entity_id}_{datetime.now().timestamp()}"
        lineage = self.lineage_tracker.create_lineage(data_id, source, quality)
        
        # Create entity
        entity = EntityNode(
            entity_id=entity_id,
            entity_type=entity_type,
            attributes=attributes,
            valid_from=datetime.now(),
            data_lineage=lineage,
        )
        
        # Validate against ontology
        is_valid, error = self.ontology.validate_entity(entity)
        if not is_valid:
            return False, f"Ontology validation failed: {error}"
        
        # Add to knowledge graph
        self.knowledge_graph.add_entity(entity)
        self._ingestion_count += 1
        
        return True, None
    
    def ingest_relationship(
        self,
        relationship_id: str,
        relation_type: RelationType,
        source_entity_id: str,
        target_entity_id: str,
        attributes: Dict[str, Any],
        strength: float = 1.0
    ) -> Tuple[bool, Optional[str]]:
        """Ingest relationship into the data fabric."""
        # Get current entities
        now = datetime.now()
        source_entity = self.knowledge_graph.get_entity_at(source_entity_id, now)
        target_entity = self.knowledge_graph.get_entity_at(target_entity_id, now)
        
        if not source_entity:
            return False, f"Source entity not found: {source_entity_id}"
        if not target_entity:
            return False, f"Target entity not found: {target_entity_id}"
        
        # Create relationship
        relationship = RelationshipEdge(
            relationship_id=relationship_id,
            relation_type=relation_type,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            attributes=attributes,
            valid_from=now,
            strength=strength,
        )
        
        # Validate
        is_valid, error = self.ontology.validate_relationship(relationship, source_entity, target_entity)
        if not is_valid:
            return False, f"Relationship validation failed: {error}"
        
        # Add to graph
        self.knowledge_graph.add_relationship(relationship)
        
        return True, None
    
    def query_entity(self, entity_id: str, timestamp: Optional[datetime] = None) -> Optional[EntityNode]:
        """Query entity from knowledge graph."""
        if timestamp is None:
            timestamp = datetime.now()
        
        return self.knowledge_graph.get_entity_at(entity_id, timestamp)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get data fabric statistics."""
        return {
            'total_entities': len(self.knowledge_graph.entities),
            'total_relationships': len(self.knowledge_graph.relationships),
            'ingestion_count': self._ingestion_count,
            'quality_threshold': self._quality_threshold,
            'entity_types': {et.value: len(ids) for et, ids in self.knowledge_graph.entity_index.items()},
        }
