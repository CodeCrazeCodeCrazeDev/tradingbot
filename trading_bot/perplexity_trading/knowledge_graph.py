"""
Perplexity Knowledge Graph
===========================

A connected intelligence system for trading knowledge:
- Entity extraction and linking
- Relationship mapping
- Semantic connections
- Temporal knowledge tracking
- Inference and reasoning over graph
- Knowledge consolidation
- Query answering via graph traversal

Creates a web of interconnected knowledge that enables
sophisticated reasoning about markets and trading.
"""

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import hashlib
import json

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities in the knowledge graph"""
    ASSET = "asset"               # Stocks, currencies, commodities
    INDICATOR = "indicator"       # Technical indicators
    PATTERN = "pattern"           # Chart patterns
    EVENT = "event"               # Market events
    PERSON = "person"             # Key figures (CEOs, analysts)
    ORGANIZATION = "organization" # Companies, institutions
    CONCEPT = "concept"           # Trading concepts
    STRATEGY = "strategy"         # Trading strategies
    SIGNAL = "signal"             # Trading signals
    REGIME = "regime"             # Market regimes
    SECTOR = "sector"             # Market sectors
    TIMEFRAME = "timeframe"       # Time periods


class RelationType(Enum):
    """Types of relationships between entities"""
    # Causal
    CAUSES = "causes"
    CAUSED_BY = "caused_by"
    INFLUENCES = "influences"
    INFLUENCED_BY = "influenced_by"
    
    # Temporal
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    CONCURRENT_WITH = "concurrent_with"
    
    # Hierarchical
    PART_OF = "part_of"
    CONTAINS = "contains"
    INSTANCE_OF = "instance_of"
    
    # Associative
    RELATED_TO = "related_to"
    SIMILAR_TO = "similar_to"
    OPPOSITE_OF = "opposite_of"
    CORRELATED_WITH = "correlated_with"
    
    # Trading specific
    SIGNALS = "signals"
    CONFIRMS = "confirms"
    CONTRADICTS = "contradicts"
    PREDICTS = "predicts"
    INDICATES = "indicates"


@dataclass
class Entity:
    """An entity in the knowledge graph"""
    entity_id: str
    entity_type: EntityType
    name: str
    
    # Properties
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    source: Optional[str] = None
    
    # Graph connections (populated by graph)
    incoming_relations: List[str] = field(default_factory=list)
    outgoing_relations: List[str] = field(default_factory=list)
    
    def get_degree(self) -> int:
        """Get total number of connections"""
        return len(self.incoming_relations) + len(self.outgoing_relations)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "properties": self.properties,
            "confidence": self.confidence,
            "degree": self.get_degree(),
        }


@dataclass
class Relation:
    """A relationship between entities"""
    relation_id: str
    relation_type: RelationType
    source_id: str
    target_id: str
    
    # Properties
    weight: float = 1.0
    confidence: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Temporal
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    evidence: List[str] = field(default_factory=list)
    
    def is_valid(self, at_time: Optional[datetime] = None) -> bool:
        """Check if relation is valid at given time"""
        at_time = at_time or datetime.utcnow()
        
        if self.valid_from and at_time < self.valid_from:
            return False
        if self.valid_until and at_time > self.valid_until:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "weight": self.weight,
            "confidence": self.confidence,
        }


@dataclass
class GraphQuery:
    """A query against the knowledge graph"""
    query_id: str
    query_text: str
    
    # Query parameters
    start_entities: List[str] = field(default_factory=list)
    target_types: List[EntityType] = field(default_factory=list)
    relation_types: List[RelationType] = field(default_factory=list)
    max_depth: int = 3
    
    # Results
    results: List[Dict[str, Any]] = field(default_factory=list)
    paths_found: List[List[str]] = field(default_factory=list)


class KnowledgeGraph:
    """
    Knowledge Graph for Trading Intelligence
    
    A graph database of trading knowledge with:
    - Entities (assets, indicators, patterns, etc.)
    - Relations (causes, signals, correlates, etc.)
    - Inference capabilities
    - Temporal reasoning
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        
        # Indices
        self.entities_by_type: Dict[EntityType, Set[str]] = {t: set() for t in EntityType}
        self.entities_by_name: Dict[str, str] = {}
        self.relations_by_type: Dict[RelationType, Set[str]] = {t: set() for t in RelationType}
        
        # Statistics
        self.total_queries = 0
        self.total_inferences = 0
        
        logger.info("KnowledgeGraph initialized")
    
    def add_entity(
        self,
        entity_type: EntityType,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        source: Optional[str] = None,
    ) -> Entity:
        """Add an entity to the graph"""
        entity_id = f"entity_{entity_type.value}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        
        # Check if exists
        if entity_id in self.entities:
            # Update existing
            entity = self.entities[entity_id]
            if properties:
                entity.properties.update(properties)
            entity.updated_at = datetime.utcnow()
            return entity
        
        entity = Entity(
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            properties=properties or {},
            confidence=confidence,
            source=source,
        )
        
        self.entities[entity_id] = entity
        self.entities_by_type[entity_type].add(entity_id)
        self.entities_by_name[name.lower()] = entity_id
        
        return entity
    
    def add_relation(
        self,
        relation_type: RelationType,
        source_id: str,
        target_id: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[str]] = None,
    ) -> Optional[Relation]:
        """Add a relation between entities"""
        if source_id not in self.entities or target_id not in self.entities:
            logger.warning(f"Cannot create relation: entities not found")
            return None
        
        relation_id = f"rel_{source_id}_{relation_type.value}_{target_id}"
        
        # Check if exists
        if relation_id in self.relations:
            # Update existing
            relation = self.relations[relation_id]
            relation.weight = weight
            relation.confidence = confidence
            if properties:
                relation.properties.update(properties)
            return relation
        
        relation = Relation(
            relation_id=relation_id,
            relation_type=relation_type,
            source_id=source_id,
            target_id=target_id,
            weight=weight,
            confidence=confidence,
            properties=properties or {},
            evidence=evidence or [],
        )
        
        self.relations[relation_id] = relation
        self.relations_by_type[relation_type].add(relation_id)
        
        # Update entity connections
        self.entities[source_id].outgoing_relations.append(relation_id)
        self.entities[target_id].incoming_relations.append(relation_id)
        
        return relation
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Get entity by name"""
        entity_id = self.entities_by_name.get(name.lower())
        if entity_id:
            return self.entities.get(entity_id)
        return None
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a type"""
        entity_ids = self.entities_by_type.get(entity_type, set())
        return [self.entities[eid] for eid in entity_ids if eid in self.entities]
    
    def get_neighbors(
        self,
        entity_id: str,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both"  # "outgoing", "incoming", "both"
    ) -> List[Tuple[Entity, Relation]]:
        """Get neighboring entities"""
        entity = self.entities.get(entity_id)
        if not entity:
            return []
        
        neighbors = []
        
        if direction in ("outgoing", "both"):
            for rel_id in entity.outgoing_relations:
                relation = self.relations.get(rel_id)
                if relation and (not relation_types or relation.relation_type in relation_types):
                    target = self.entities.get(relation.target_id)
                    if target:
                        neighbors.append((target, relation))
        
        if direction in ("incoming", "both"):
            for rel_id in entity.incoming_relations:
                relation = self.relations.get(rel_id)
                if relation and (not relation_types or relation.relation_type in relation_types):
                    source = self.entities.get(relation.source_id)
                    if source:
                        neighbors.append((source, relation))
        
        return neighbors
    
    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
        relation_types: Optional[List[RelationType]] = None,
    ) -> Optional[List[Tuple[Entity, Relation]]]:
        """Find shortest path between entities"""
        if start_id not in self.entities or end_id not in self.entities:
            return None
        
        # BFS
        visited = {start_id}
        queue = [(start_id, [])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) >= max_depth:
                continue
            
            for neighbor, relation in self.get_neighbors(current_id, relation_types, "outgoing"):
                if neighbor.entity_id == end_id:
                    return path + [(neighbor, relation)]
                
                if neighbor.entity_id not in visited:
                    visited.add(neighbor.entity_id)
                    queue.append((neighbor.entity_id, path + [(neighbor, relation)]))
        
        return None
    
    def find_all_paths(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 4,
    ) -> List[List[Tuple[Entity, Relation]]]:
        """Find all paths between entities"""
        if start_id not in self.entities or end_id not in self.entities:
            return []
        
        all_paths = []
        
        def dfs(current_id: str, path: List[Tuple[Entity, Relation]], visited: Set[str]):
            if len(path) > max_depth:
                return
            
            if current_id == end_id:
                all_paths.append(path.copy())
                return
            
            for neighbor, relation in self.get_neighbors(current_id, direction="outgoing"):
                if neighbor.entity_id not in visited:
                    visited.add(neighbor.entity_id)
                    path.append((neighbor, relation))
                    dfs(neighbor.entity_id, path, visited)
                    path.pop()
                    visited.remove(neighbor.entity_id)
        
        dfs(start_id, [], {start_id})
        return all_paths
    
    def infer_relations(self) -> List[Relation]:
        """Infer new relations from existing ones"""
        inferred = []
        
        # Transitivity: A causes B, B causes C => A causes C (with reduced confidence)
        for rel1_id in self.relations_by_type.get(RelationType.CAUSES, set()):
            rel1 = self.relations.get(rel1_id)
            if not rel1:
                continue
            
            for rel2_id in self.relations_by_type.get(RelationType.CAUSES, set()):
                rel2 = self.relations.get(rel2_id)
                if not rel2:
                    continue
                
                if rel1.target_id == rel2.source_id:
                    # Transitive relation
                    new_rel = self.add_relation(
                        RelationType.CAUSES,
                        rel1.source_id,
                        rel2.target_id,
                        weight=rel1.weight * rel2.weight * 0.8,
                        confidence=rel1.confidence * rel2.confidence * 0.7,
                        evidence=[f"Inferred from {rel1_id} and {rel2_id}"],
                    )
                    if new_rel:
                        inferred.append(new_rel)
        
        # Correlation symmetry: A correlated_with B => B correlated_with A
        for rel_id in self.relations_by_type.get(RelationType.CORRELATED_WITH, set()):
            rel = self.relations.get(rel_id)
            if not rel:
                continue
            
            reverse_id = f"rel_{rel.target_id}_{RelationType.CORRELATED_WITH.value}_{rel.source_id}"
            if reverse_id not in self.relations:
                new_rel = self.add_relation(
                    RelationType.CORRELATED_WITH,
                    rel.target_id,
                    rel.source_id,
                    weight=rel.weight,
                    confidence=rel.confidence,
                    evidence=[f"Symmetric to {rel_id}"],
                )
                if new_rel:
                    inferred.append(new_rel)
        
        self.total_inferences += len(inferred)
        return inferred
    
    def query(
        self,
        query_text: str,
        start_entity: Optional[str] = None,
        target_types: Optional[List[EntityType]] = None,
        max_depth: int = 3,
    ) -> GraphQuery:
        """Query the knowledge graph"""
        query_id = f"query_{datetime.utcnow().strftime('%H%M%S%f')}"
        
        graph_query = GraphQuery(
            query_id=query_id,
            query_text=query_text,
            target_types=target_types or [],
            max_depth=max_depth,
        )
        
        self.total_queries += 1
        
        # Find starting entity
        if start_entity:
            entity = self.get_entity_by_name(start_entity)
            if entity:
                graph_query.start_entities = [entity.entity_id]
        else:
            # Extract entities from query text
            for name, entity_id in self.entities_by_name.items():
                if name in query_text.lower():
                    graph_query.start_entities.append(entity_id)
        
        # Traverse from starting entities
        for start_id in graph_query.start_entities:
            results = self._traverse(start_id, target_types, max_depth)
            graph_query.results.extend(results)
        
        return graph_query
    
    def _traverse(
        self,
        start_id: str,
        target_types: Optional[List[EntityType]],
        max_depth: int,
    ) -> List[Dict[str, Any]]:
        """Traverse graph from starting entity"""
        results = []
        visited = {start_id}
        queue = [(start_id, 0, [])]
        
        while queue:
            current_id, depth, path = queue.pop(0)
            
            if depth > max_depth:
                continue
            
            entity = self.entities.get(current_id)
            if not entity:
                continue
            
            # Check if matches target type
            if target_types and entity.entity_type in target_types:
                results.append({
                    "entity": entity.to_dict(),
                    "path": path,
                    "depth": depth,
                })
            
            # Continue traversal
            for neighbor, relation in self.get_neighbors(current_id, direction="both"):
                if neighbor.entity_id not in visited:
                    visited.add(neighbor.entity_id)
                    new_path = path + [relation.to_dict()]
                    queue.append((neighbor.entity_id, depth + 1, new_path))
        
        return results
    
    def get_subgraph(
        self,
        center_id: str,
        radius: int = 2,
    ) -> Dict[str, Any]:
        """Get subgraph around an entity"""
        if center_id not in self.entities:
            return {"entities": [], "relations": []}
        
        entities = {}
        relations = {}
        
        visited = {center_id}
        queue = [(center_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            entity = self.entities.get(current_id)
            if entity:
                entities[current_id] = entity.to_dict()
            
            if depth >= radius:
                continue
            
            for neighbor, relation in self.get_neighbors(current_id, direction="both"):
                relations[relation.relation_id] = relation.to_dict()
                
                if neighbor.entity_id not in visited:
                    visited.add(neighbor.entity_id)
                    queue.append((neighbor.entity_id, depth + 1))
        
        return {
            "entities": list(entities.values()),
            "relations": list(relations.values()),
        }
    
    def get_most_connected(self, n: int = 10) -> List[Entity]:
        """Get most connected entities"""
        sorted_entities = sorted(
            self.entities.values(),
            key=lambda e: e.get_degree(),
            reverse=True
        )
        return sorted_entities[:n]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entities_by_type": {
                t.value: len(ids) for t, ids in self.entities_by_type.items()
            },
            "relations_by_type": {
                t.value: len(ids) for t, ids in self.relations_by_type.items()
            },
            "avg_degree": (
                sum(e.get_degree() for e in self.entities.values()) / len(self.entities)
                if self.entities else 0
            ),
            "total_queries": self.total_queries,
            "total_inferences": self.total_inferences,
        }
    
    def populate_trading_knowledge(self) -> None:
        """Populate with basic trading knowledge"""
        # Assets
        assets = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "SPY", "QQQ", "GOLD"]
        for asset in assets:
            self.add_entity(EntityType.ASSET, asset, {"tradeable": True})
        
        # Indicators
        indicators = [
            ("RSI", {"type": "momentum", "range": [0, 100]}),
            ("MACD", {"type": "trend", "components": ["macd", "signal", "histogram"]}),
            ("SMA", {"type": "trend", "parameters": ["period"]}),
            ("EMA", {"type": "trend", "parameters": ["period"]}),
            ("Bollinger Bands", {"type": "volatility", "components": ["upper", "middle", "lower"]}),
            ("ATR", {"type": "volatility", "use": "stop_loss"}),
        ]
        for name, props in indicators:
            self.add_entity(EntityType.INDICATOR, name, props)
        
        # Patterns
        patterns = [
            "Head and Shoulders", "Double Top", "Double Bottom",
            "Triangle", "Flag", "Wedge", "Cup and Handle"
        ]
        for pattern in patterns:
            self.add_entity(EntityType.PATTERN, pattern, {"type": "chart_pattern"})
        
        # Concepts
        concepts = [
            "Support", "Resistance", "Trend", "Breakout",
            "Pullback", "Reversal", "Continuation", "Momentum"
        ]
        for concept in concepts:
            self.add_entity(EntityType.CONCEPT, concept)
        
        # Regimes
        regimes = ["Trending", "Ranging", "Volatile", "Quiet"]
        for regime in regimes:
            self.add_entity(EntityType.REGIME, regime)
        
        # Add some relations
        rsi = self.get_entity_by_name("RSI")
        macd = self.get_entity_by_name("MACD")
        momentum = self.get_entity_by_name("Momentum")
        
        if rsi and momentum:
            self.add_relation(RelationType.INDICATES, rsi.entity_id, momentum.entity_id)
        
        if macd and momentum:
            self.add_relation(RelationType.INDICATES, macd.entity_id, momentum.entity_id)
        
        # Patterns signal reversals
        reversal = self.get_entity_by_name("Reversal")
        for pattern_name in ["Head and Shoulders", "Double Top", "Double Bottom"]:
            pattern = self.get_entity_by_name(pattern_name)
            if pattern and reversal:
                self.add_relation(RelationType.SIGNALS, pattern.entity_id, reversal.entity_id)
        
        logger.info(f"Populated knowledge graph with {len(self.entities)} entities and {len(self.relations)} relations")


class KnowledgeGraphReasoner:
    """
    Reasoner that uses the knowledge graph for inference
    """
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question using the knowledge graph"""
        # Extract key terms
        terms = question.lower().split()
        
        # Find relevant entities
        relevant_entities = []
        for term in terms:
            entity = self.graph.get_entity_by_name(term)
            if entity:
                relevant_entities.append(entity)
        
        if not relevant_entities:
            return {
                "answer": "No relevant knowledge found",
                "confidence": 0,
                "entities": [],
            }
        
        # Get related information
        related_info = []
        for entity in relevant_entities:
            neighbors = self.graph.get_neighbors(entity.entity_id)
            for neighbor, relation in neighbors:
                related_info.append({
                    "entity": entity.name,
                    "relation": relation.relation_type.value,
                    "related_to": neighbor.name,
                    "confidence": relation.confidence,
                })
        
        # Generate answer
        if related_info:
            answer_parts = []
            for info in related_info[:5]:  # Top 5
                answer_parts.append(
                    f"{info['entity']} {info['relation']} {info['related_to']}"
                )
            answer = "; ".join(answer_parts)
        else:
            answer = f"Found entities: {', '.join(e.name for e in relevant_entities)}"
        
        return {
            "answer": answer,
            "confidence": sum(e.confidence for e in relevant_entities) / len(relevant_entities),
            "entities": [e.to_dict() for e in relevant_entities],
            "related_info": related_info,
        }
    
    def find_trading_signals(self, asset: str) -> List[Dict[str, Any]]:
        """Find trading signals for an asset"""
        asset_entity = self.graph.get_entity_by_name(asset)
        if not asset_entity:
            return []
        
        signals = []
        
        # Find all signal relations
        for neighbor, relation in self.graph.get_neighbors(
            asset_entity.entity_id,
            relation_types=[RelationType.SIGNALS, RelationType.INDICATES, RelationType.PREDICTS]
        ):
            signals.append({
                "signal_source": neighbor.name,
                "signal_type": relation.relation_type.value,
                "confidence": relation.confidence,
                "weight": relation.weight,
            })
        
        return sorted(signals, key=lambda s: s["confidence"], reverse=True)
    
    def explain_relationship(self, entity1: str, entity2: str) -> Dict[str, Any]:
        """Explain the relationship between two entities"""
        e1 = self.graph.get_entity_by_name(entity1)
        e2 = self.graph.get_entity_by_name(entity2)
        
        if not e1 or not e2:
            return {"explanation": "Entities not found", "paths": []}
        
        # Find paths
        paths = self.graph.find_all_paths(e1.entity_id, e2.entity_id, max_depth=4)
        
        explanations = []
        for path in paths:
            path_desc = [entity1]
            for entity, relation in path:
                path_desc.append(f"--[{relation.relation_type.value}]-->")
                path_desc.append(entity.name)
            explanations.append(" ".join(path_desc))
        
        return {
            "entity1": entity1,
            "entity2": entity2,
            "num_paths": len(paths),
            "explanations": explanations[:5],  # Top 5 paths
        }


# Factory function
def create_knowledge_graph(
    populate: bool = True,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[KnowledgeGraph, KnowledgeGraphReasoner]:
    """Create knowledge graph with reasoner"""
    graph = KnowledgeGraph(config)
    
    if populate:
        graph.populate_trading_knowledge()
    
    reasoner = KnowledgeGraphReasoner(graph)
    
    return graph, reasoner
