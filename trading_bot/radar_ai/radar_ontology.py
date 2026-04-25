"""
Financial Ontology - Palantir-Inspired Semantic Knowledge Graph
================================================================

Maps financial entities, relationships, and actions into a semantic layer
that enables AI agents to UNDERSTAND markets, not just predict them.

Based on Palantir's Ontology architecture:
- Object Types: Financial entities (Assets, Institutions, Markets, Events)
- Link Types: Relationships (Correlations, Causations, Influences)
- Actions: Operations (Buy, Sell, Hedge, Analyze)
- Interfaces: Polymorphic object type shapes
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid

logger = logging.getLogger(__name__)


class ObjectType(Enum):
    """Financial ontology object types"""
    # Core Financial Entities
    ASSET = "asset"
    INSTITUTION = "institution"
    MARKET = "market"
    EXCHANGE = "exchange"
    PORTFOLIO = "portfolio"
    POSITION = "position"
    ORDER = "order"
    TRADE = "trade"
    
    # Economic Entities
    ECONOMY = "economy"
    SECTOR = "sector"
    INDUSTRY = "industry"
    COUNTRY = "country"
    REGION = "region"
    
    # Events & Signals
    EVENT = "event"
    NEWS = "news"
    EARNINGS = "earnings"
    ECONOMIC_RELEASE = "economic_release"
    SIGNAL = "signal"
    ALERT = "alert"
    
    # Indicators & Metrics
    INDICATOR = "indicator"
    METRIC = "metric"
    RISK_FACTOR = "risk_factor"
    ALPHA_FACTOR = "alpha_factor"
    
    # Agents & Strategies
    AGENT = "agent"
    STRATEGY = "strategy"
    MODEL = "model"
    RULE = "rule"


class LinkType(Enum):
    """Relationship types between objects"""
    # Ownership & Composition
    OWNS = "owns"
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    PART_OF = "part_of"
    
    # Trading Relationships
    TRADES = "trades"
    LISTED_ON = "listed_on"
    EXECUTES = "executes"
    GENERATES = "generates"
    
    # Causal & Influence
    CAUSES = "causes"
    INFLUENCES = "influences"
    AFFECTS = "affects"
    PREDICTS = "predicts"
    LEADS = "leads"
    LAGS = "lags"
    
    # Statistical Relationships
    CORRELATES_WITH = "correlates_with"
    COINTEGRATES_WITH = "cointegrates_with"
    HEDGES = "hedges"
    DIVERSIFIES = "diversifies"
    
    # Semantic Relationships
    SIMILAR_TO = "similar_to"
    COMPETES_WITH = "competes_with"
    SUPPLIES_TO = "supplies_to"
    DEPENDS_ON = "depends_on"


class ActionType(Enum):
    """Actions that can be performed on objects"""
    # Trading Actions
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    HEDGE = "hedge"
    REBALANCE = "rebalance"
    CLOSE = "close"
    
    # Analysis Actions
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    PREDICT = "predict"
    SIMULATE = "simulate"
    BACKTEST = "backtest"
    
    # Monitoring Actions
    MONITOR = "monitor"
    ALERT = "alert"
    TRACK = "track"
    REPORT = "report"
    
    # Learning Actions
    LEARN = "learn"
    ADAPT = "adapt"
    OPTIMIZE = "optimize"
    EVOLVE = "evolve"


@dataclass
class OntologyObject:
    """A semantic object in the financial ontology"""
    object_id: str
    object_type: ObjectType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'object_id': self.object_id,
            'object_type': self.object_type.value,
            'name': self.name,
            'properties': self.properties,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    def get_property(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)
    
    def set_property(self, key: str, value: Any):
        self.properties[key] = value
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class OntologyLink:
    """A relationship between two objects"""
    link_id: str
    link_type: LinkType
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0  # Relationship strength (0-1)
    confidence: float = 1.0  # Confidence in the relationship
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'link_id': self.link_id,
            'link_type': self.link_type.value,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'properties': self.properties,
            'strength': self.strength,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class OntologyAction:
    """An action that can be performed"""
    action_id: str
    action_type: ActionType
    target_object_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    effects: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'target_object_id': self.target_object_id,
            'parameters': self.parameters,
            'preconditions': self.preconditions,
            'effects': self.effects,
        }


class FinancialOntology:
    """
    The Financial Ontology - A semantic knowledge graph for financial intelligence.
    
    Inspired by Palantir's Ontology, this provides:
    1. Object Types: Semantic entities representing financial concepts
    2. Link Types: Relationships between entities
    3. Actions: Operations that can be performed
    4. Interfaces: Polymorphic type shapes
    5. Functions: Business logic for ontology operations
    """
    
    def __init__(self, ontology_id: Optional[str] = None):
        self.ontology_id = ontology_id or f"ONT-{uuid.uuid4().hex[:8]}"
        
        # Object storage
        self._objects: Dict[str, OntologyObject] = {}
        self._objects_by_type: Dict[ObjectType, Set[str]] = {t: set() for t in ObjectType}
        
        # Link storage
        self._links: Dict[str, OntologyLink] = {}
        self._outgoing_links: Dict[str, Set[str]] = {}  # source_id -> link_ids
        self._incoming_links: Dict[str, Set[str]] = {}  # target_id -> link_ids
        
        # Action registry
        self._actions: Dict[str, OntologyAction] = {}
        self._action_handlers: Dict[ActionType, List[Callable]] = {t: [] for t in ActionType}
        
        # Indexes for fast lookup
        self._name_index: Dict[str, str] = {}  # name -> object_id
        self._property_index: Dict[str, Dict[Any, Set[str]]] = {}  # property_key -> value -> object_ids
        
        # Change tracking
        self._change_log: List[Dict[str, Any]] = []
        
        logger.info(f"FinancialOntology initialized: {self.ontology_id}")
    
    # ==================== OBJECT OPERATIONS ====================
    
    def create_object(
        self,
        object_type: ObjectType,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        object_id: Optional[str] = None,
    ) -> OntologyObject:
        """Create a new object in the ontology"""
        obj_id = object_id or f"{object_type.value}-{uuid.uuid4().hex[:8]}"
        
        obj = OntologyObject(
            object_id=obj_id,
            object_type=object_type,
            name=name,
            properties=properties or {},
            metadata=metadata or {},
        )
        
        self._objects[obj_id] = obj
        self._objects_by_type[object_type].add(obj_id)
        self._name_index[name.lower()] = obj_id
        self._outgoing_links[obj_id] = set()
        self._incoming_links[obj_id] = set()
        
        # Index properties
        for key, value in obj.properties.items():
            self._index_property(obj_id, key, value)
        
        self._log_change('CREATE_OBJECT', obj.to_dict())
        
        return obj
    
    def get_object(self, object_id: str) -> Optional[OntologyObject]:
        """Get an object by ID"""
        return self._objects.get(object_id)
    
    def get_objects_by_type(self, object_type: ObjectType) -> List[OntologyObject]:
        """Get all objects of a specific type"""
        return [self._objects[oid] for oid in self._objects_by_type[object_type]]
    
    def find_object_by_name(self, name: str) -> Optional[OntologyObject]:
        """Find an object by name"""
        obj_id = self._name_index.get(name.lower())
        return self._objects.get(obj_id) if obj_id else None
    
    def query_objects(
        self,
        object_type: Optional[ObjectType] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[OntologyObject]:
        """Query objects with filters"""
        candidates = set(self._objects.keys())
        
        if object_type:
            candidates &= self._objects_by_type[object_type]
        
        if properties:
            for key, value in properties.items():
                if key in self._property_index and value in self._property_index[key]:
                    candidates &= self._property_index[key][value]
                else:
                    candidates = set()
                    break
        
        return [self._objects[oid] for oid in list(candidates)[:limit]]
    
    def _index_property(self, object_id: str, key: str, value: Any):
        """Index a property for fast lookup"""
        if key not in self._property_index:
            self._property_index[key] = {}
        if value not in self._property_index[key]:
            self._property_index[key][value] = set()
        self._property_index[key][value].add(object_id)
    
    # ==================== LINK OPERATIONS ====================
    
    def create_link(
        self,
        link_type: LinkType,
        source_id: str,
        target_id: str,
        properties: Optional[Dict[str, Any]] = None,
        strength: float = 1.0,
        confidence: float = 1.0,
    ) -> Optional[OntologyLink]:
        """Create a link between two objects"""
        if source_id not in self._objects or target_id not in self._objects:
            logger.warning(f"Cannot create link: objects not found")
            return None
        
        link_id = f"LINK-{uuid.uuid4().hex[:8]}"
        
        link = OntologyLink(
            link_id=link_id,
            link_type=link_type,
            source_id=source_id,
            target_id=target_id,
            properties=properties or {},
            strength=strength,
            confidence=confidence,
        )
        
        self._links[link_id] = link
        self._outgoing_links[source_id].add(link_id)
        self._incoming_links[target_id].add(link_id)
        
        self._log_change('CREATE_LINK', link.to_dict())
        
        return link
    
    def get_outgoing_links(self, object_id: str, link_type: Optional[LinkType] = None) -> List[OntologyLink]:
        """Get all outgoing links from an object"""
        link_ids = self._outgoing_links.get(object_id, set())
        links = [self._links[lid] for lid in link_ids]
        
        if link_type:
            links = [l for l in links if l.link_type == link_type]
        
        return links
    
    def get_incoming_links(self, object_id: str, link_type: Optional[LinkType] = None) -> List[OntologyLink]:
        """Get all incoming links to an object"""
        link_ids = self._incoming_links.get(object_id, set())
        links = [self._links[lid] for lid in link_ids]
        
        if link_type:
            links = [l for l in links if l.link_type == link_type]
        
        return links
    
    def get_related_objects(
        self,
        object_id: str,
        link_type: Optional[LinkType] = None,
        direction: str = 'both',
    ) -> List[OntologyObject]:
        """Get objects related to a given object"""
        related_ids = set()
        
        if direction in ('out', 'both'):
            for link in self.get_outgoing_links(object_id, link_type):
                related_ids.add(link.target_id)
        
        if direction in ('in', 'both'):
            for link in self.get_incoming_links(object_id, link_type):
                related_ids.add(link.source_id)
        
        return [self._objects[oid] for oid in related_ids if oid in self._objects]
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> Optional[List[str]]:
        """Find a path between two objects using BFS"""
        if source_id not in self._objects or target_id not in self._objects:
            return None
        
        if source_id == target_id:
            return [source_id]
        
        visited = {source_id}
        queue = [(source_id, [source_id])]
        
        while queue and len(queue[0][1]) <= max_depth:
            current_id, path = queue.pop(0)
            
            for link in self.get_outgoing_links(current_id):
                next_id = link.target_id
                if next_id == target_id:
                    return path + [next_id]
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))
        
        return None
    
    # ==================== ACTION OPERATIONS ====================
    
    def register_action(
        self,
        action_type: ActionType,
        target_object_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        preconditions: Optional[List[str]] = None,
        effects: Optional[List[str]] = None,
    ) -> OntologyAction:
        """Register an action in the ontology"""
        action_id = f"ACT-{uuid.uuid4().hex[:8]}"
        
        action = OntologyAction(
            action_id=action_id,
            action_type=action_type,
            target_object_id=target_object_id,
            parameters=parameters or {},
            preconditions=preconditions or [],
            effects=effects or [],
        )
        
        self._actions[action_id] = action
        
        return action
    
    def register_action_handler(self, action_type: ActionType, handler: Callable):
        """Register a handler for an action type"""
        self._action_handlers[action_type].append(handler)
    
    async def execute_action(self, action_id: str) -> Dict[str, Any]:
        """Execute a registered action"""
        action = self._actions.get(action_id)
        if not action:
            return {'success': False, 'error': 'Action not found'}
        
        handlers = self._action_handlers.get(action.action_type, [])
        if not handlers:
            return {'success': False, 'error': 'No handlers registered'}
        
        results = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(action)
                else:
                    result = handler(action)
                results.append(result)
            except Exception as e:
                logger.error(f"Action handler error: {e}")
                results.append({'error': str(e)})
        
        self._log_change('EXECUTE_ACTION', {'action_id': action_id, 'results': results})
        
        return {'success': True, 'results': results}
    
    # ==================== KNOWLEDGE GRAPH OPERATIONS ====================
    
    def get_subgraph(
        self,
        center_id: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """Get a subgraph centered on an object"""
        objects = {}
        links = {}
        
        def traverse(obj_id: str, current_depth: int):
            if current_depth > depth or obj_id in objects:
                return
            
            obj = self._objects.get(obj_id)
            if obj:
                objects[obj_id] = obj.to_dict()
                
                for link in self.get_outgoing_links(obj_id):
                    links[link.link_id] = link.to_dict()
                    traverse(link.target_id, current_depth + 1)
                
                for link in self.get_incoming_links(obj_id):
                    links[link.link_id] = link.to_dict()
                    traverse(link.source_id, current_depth + 1)
        
        traverse(center_id, 0)
        
        return {'objects': objects, 'links': links}
    
    def compute_centrality(self, object_id: str) -> float:
        """Compute the centrality of an object in the graph"""
        if object_id not in self._objects:
            return 0.0
        
        outgoing = len(self._outgoing_links.get(object_id, set()))
        incoming = len(self._incoming_links.get(object_id, set()))
        total_links = len(self._links)
        
        if total_links == 0:
            return 0.0
        
        return (outgoing + incoming) / (2 * total_links)
    
    def find_influential_objects(self, object_type: Optional[ObjectType] = None, top_k: int = 10) -> List[Tuple[str, float]]:
        """Find the most influential objects"""
        candidates = self._objects.keys()
        if object_type:
            candidates = self._objects_by_type[object_type]
        
        scores = [(oid, self.compute_centrality(oid)) for oid in candidates]
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]
    
    # ==================== UTILITY METHODS ====================
    
    def _log_change(self, change_type: str, data: Dict[str, Any]):
        """Log a change to the ontology"""
        self._change_log.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': change_type,
            'data': data,
        })
        
        # Trim log
        if len(self._change_log) > 10000:
            self._change_log = self._change_log[-5000:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ontology statistics"""
        return {
            'ontology_id': self.ontology_id,
            'total_objects': len(self._objects),
            'total_links': len(self._links),
            'total_actions': len(self._actions),
            'objects_by_type': {t.value: len(ids) for t, ids in self._objects_by_type.items() if ids},
            'change_log_size': len(self._change_log),
        }
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export the entire ontology to a dictionary"""
        return {
            'ontology_id': self.ontology_id,
            'objects': {oid: obj.to_dict() for oid, obj in self._objects.items()},
            'links': {lid: link.to_dict() for lid, link in self._links.items()},
            'actions': {aid: action.to_dict() for aid, action in self._actions.items()},
            'statistics': self.get_statistics(),
        }
