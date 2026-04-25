"""
AADS MODULE 2 — GOTHAM: Market Intelligence Graph

A live Neo4j-style knowledge graph — a causal-ontological map of the
market as typed objects and directed relationships.

Ontology Objects:
- Asset, Company, Sector, MacroIndicator, EarningsEvent
- NewsArticle, GeopoliticalEvent, PolymarketContract
- TradeSignal, Position, Strategy, VisualSignal

Ontology Relationships:
- CORRELATED_WITH, CAUSES, SUPPLIES_TO, COMPETES_WITH
- EXPOSED_TO, HEDGES, MENTIONED_IN, PREDICTS
- CONTRADICTS, EVOLVED_FROM

Every incoming event triggers graph enrichment in real time.
Every agent query reads from this graph — never from raw data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from enum import Enum
import uuid
import logging
import json

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in the market intelligence graph"""
    ASSET = "Asset"
    COMPANY = "Company"
    SECTOR = "Sector"
    MACRO_INDICATOR = "MacroIndicator"
    EARNINGS_EVENT = "EarningsEvent"
    NEWS_ARTICLE = "NewsArticle"
    GEOPOLITICAL_EVENT = "GeopoliticalEvent"
    POLYMARKET_CONTRACT = "PolymarketContract"
    TRADE_SIGNAL = "TradeSignal"
    POSITION = "Position"
    STRATEGY = "Strategy"
    VISUAL_SIGNAL = "VisualSignal"
    ANALYST = "Analyst"
    EXECUTIVE = "Executive"
    PATENT = "Patent"


class RelationType(Enum):
    """Types of relationships in the graph"""
    CORRELATED_WITH = "CORRELATED_WITH"
    CAUSES = "CAUSES"
    SUPPLIES_TO = "SUPPLIES_TO"
    COMPETES_WITH = "COMPETES_WITH"
    EXPOSED_TO = "EXPOSED_TO"
    HEDGES = "HEDGES"
    MENTIONED_IN = "MENTIONED_IN"
    PREDICTS = "PREDICTS"
    CONTRADICTS = "CONTRADICTS"
    EVOLVED_FROM = "EVOLVED_FROM"
    BELONGS_TO = "BELONGS_TO"
    MANAGES = "MANAGES"
    OWNS = "OWNS"
    FILED_BY = "FILED_BY"
    AFFECTS = "AFFECTS"


@dataclass
class GraphNode:
    """A node in the market intelligence graph"""
    node_id: str
    node_type: NodeType
    properties: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def update(self, properties: Dict[str, Any]) -> None:
        """Update node properties"""
        self.properties.update(properties)
        self.updated_at = datetime.now()
        self.version += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'properties': self.properties,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version
        }


@dataclass
class GraphEdge:
    """A directed edge/relationship in the graph"""
    edge_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any]
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update(self, properties: Dict[str, Any]) -> None:
        """Update edge properties"""
        self.properties.update(properties)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'edge_id': self.edge_id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type.value,
            'properties': self.properties,
            'weight': self.weight,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class QueryResult:
    """Result of a graph query"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    paths: List[List[str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GothamKnowledgeGraph:
    """
    The Gotham Market Intelligence Graph.
    
    A causal-ontological map of the market as typed objects and
    directed relationships. Supports real-time enrichment and
    complex graph queries.
    """
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        
        # Indexes for fast lookup
        self.nodes_by_type: Dict[NodeType, Set[str]] = {t: set() for t in NodeType}
        self.edges_by_source: Dict[str, Set[str]] = {}
        self.edges_by_target: Dict[str, Set[str]] = {}
        self.edges_by_type: Dict[RelationType, Set[str]] = {t: set() for t in RelationType}
        
        # Initialize with core market structure
        self._initialize_core_structure()
        
        logger.info("GothamKnowledgeGraph initialized")
    
    def _initialize_core_structure(self) -> None:
        """Initialize core market structure nodes"""
        
        # Core sectors (GICS)
        sectors = [
            ("XLK", "Technology", {"gics_code": "45", "macro_sensitivity": "growth"}),
            ("XLF", "Financials", {"gics_code": "40", "macro_sensitivity": "rates"}),
            ("XLE", "Energy", {"gics_code": "10", "macro_sensitivity": "oil"}),
            ("XLV", "Healthcare", {"gics_code": "35", "macro_sensitivity": "defensive"}),
            ("XLY", "Consumer Discretionary", {"gics_code": "25", "macro_sensitivity": "consumer"}),
            ("XLP", "Consumer Staples", {"gics_code": "30", "macro_sensitivity": "defensive"}),
            ("XLI", "Industrials", {"gics_code": "20", "macro_sensitivity": "cyclical"}),
            ("XLB", "Materials", {"gics_code": "15", "macro_sensitivity": "cyclical"}),
            ("XLRE", "Real Estate", {"gics_code": "60", "macro_sensitivity": "rates"}),
            ("XLU", "Utilities", {"gics_code": "55", "macro_sensitivity": "rates"}),
            ("XLC", "Communication Services", {"gics_code": "50", "macro_sensitivity": "growth"}),
        ]
        
        for ticker, name, props in sectors:
            self.add_node(NodeType.SECTOR, {
                "ticker": ticker,
                "name": name,
                **props
            })
        
        # Core macro indicators
        macro_indicators = [
            ("FED_RATE", "Federal Funds Rate", {"unit": "percent", "frequency": "8x_yearly"}),
            ("CPI", "Consumer Price Index", {"unit": "percent_yoy", "frequency": "monthly"}),
            ("PCE", "Personal Consumption Expenditures", {"unit": "percent_yoy", "frequency": "monthly"}),
            ("NFP", "Non-Farm Payrolls", {"unit": "thousands", "frequency": "monthly"}),
            ("ISM_MFG", "ISM Manufacturing PMI", {"unit": "index", "frequency": "monthly"}),
            ("ISM_SVC", "ISM Services PMI", {"unit": "index", "frequency": "monthly"}),
            ("VIX", "CBOE Volatility Index", {"unit": "index", "frequency": "realtime"}),
            ("DXY", "US Dollar Index", {"unit": "index", "frequency": "realtime"}),
            ("US10Y", "10-Year Treasury Yield", {"unit": "percent", "frequency": "realtime"}),
            ("US2Y", "2-Year Treasury Yield", {"unit": "percent", "frequency": "realtime"}),
            ("CREDIT_IG", "Investment Grade Credit Spread", {"unit": "bps", "frequency": "daily"}),
            ("CREDIT_HY", "High Yield Credit Spread", {"unit": "bps", "frequency": "daily"}),
            ("OIL_WTI", "WTI Crude Oil", {"unit": "usd_barrel", "frequency": "realtime"}),
            ("GOLD", "Gold Spot", {"unit": "usd_oz", "frequency": "realtime"}),
            ("CHINA_PMI", "China Manufacturing PMI", {"unit": "index", "frequency": "monthly"}),
        ]
        
        for indicator_id, name, props in macro_indicators:
            self.add_node(NodeType.MACRO_INDICATOR, {
                "indicator_id": indicator_id,
                "name": name,
                **props
            })
        
        # Core causal relationships between macro indicators
        causal_relationships = [
            ("FED_RATE", "US10Y", "CAUSES", {"causal_strength": 0.8, "lag_days": 0}),
            ("FED_RATE", "US2Y", "CAUSES", {"causal_strength": 0.9, "lag_days": 0}),
            ("FED_RATE", "DXY", "CAUSES", {"causal_strength": 0.6, "lag_days": 5}),
            ("FED_RATE", "CREDIT_IG", "CAUSES", {"causal_strength": 0.5, "lag_days": 10}),
            ("CPI", "FED_RATE", "CAUSES", {"causal_strength": 0.7, "lag_days": 30}),
            ("OIL_WTI", "CPI", "CAUSES", {"causal_strength": 0.4, "lag_days": 30}),
            ("VIX", "CREDIT_HY", "CORRELATED_WITH", {"correlation": 0.75, "lag_days": 0}),
            ("DXY", "OIL_WTI", "CAUSES", {"causal_strength": -0.5, "lag_days": 0}),
            ("CHINA_PMI", "OIL_WTI", "CAUSES", {"causal_strength": 0.4, "lag_days": 5}),
        ]
        
        for source_id, target_id, rel_type, props in causal_relationships:
            source_node = self._find_node_by_property("indicator_id", source_id)
            target_node = self._find_node_by_property("indicator_id", target_id)
            if source_node and target_node:
                self.add_edge(
                    source_node.node_id,
                    target_node.node_id,
                    RelationType[rel_type],
                    props
                )
        
        logger.info(f"Initialized core structure: {len(self.nodes)} nodes, {len(self.edges)} edges")
    
    def _find_node_by_property(self, prop_name: str, prop_value: Any) -> Optional[GraphNode]:
        """Find a node by a property value"""
        for node in self.nodes.values():
            if node.properties.get(prop_name) == prop_value:
                return node
        return None
    
    def add_node(
        self,
        node_type: NodeType,
        properties: Dict[str, Any],
        node_id: Optional[str] = None
    ) -> GraphNode:
        """Add a node to the graph"""
        node_id = node_id or str(uuid.uuid4())
        
        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            properties=properties
        )
        
        self.nodes[node_id] = node
        self.nodes_by_type[node_type].add(node_id)
        
        logger.debug(f"Added node: {node_type.value} - {node_id[:8]}")
        return node
    
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        properties: Dict[str, Any],
        weight: float = 1.0
    ) -> Optional[GraphEdge]:
        """Add an edge to the graph"""
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"Cannot add edge: missing node(s)")
            return None
        
        edge_id = str(uuid.uuid4())
        
        edge = GraphEdge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=properties,
            weight=weight
        )
        
        self.edges[edge_id] = edge
        
        # Update indexes
        if source_id not in self.edges_by_source:
            self.edges_by_source[source_id] = set()
        self.edges_by_source[source_id].add(edge_id)
        
        if target_id not in self.edges_by_target:
            self.edges_by_target[target_id] = set()
        self.edges_by_target[target_id].add(edge_id)
        
        self.edges_by_type[relation_type].add(edge_id)
        
        logger.debug(f"Added edge: {relation_type.value} - {edge_id[:8]}")
        return edge
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        """Get an edge by ID"""
        return self.edges.get(edge_id)
    
    def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """Update a node's properties"""
        node = self.nodes.get(node_id)
        if node:
            node.update(properties)
            return True
        return False
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        """Get all nodes of a specific type"""
        node_ids = self.nodes_by_type.get(node_type, set())
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def get_outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all outgoing edges from a node"""
        edge_ids = self.edges_by_source.get(node_id, set())
        return [self.edges[eid] for eid in edge_ids if eid in self.edges]
    
    def get_incoming_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all incoming edges to a node"""
        edge_ids = self.edges_by_target.get(node_id, set())
        return [self.edges[eid] for eid in edge_ids if eid in self.edges]
    
    def get_neighbors(
        self,
        node_id: str,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both"
    ) -> List[GraphNode]:
        """Get neighboring nodes"""
        neighbors = set()
        
        if direction in ("out", "both"):
            for edge in self.get_outgoing_edges(node_id):
                if relation_types is None or edge.relation_type in relation_types:
                    neighbors.add(edge.target_id)
        
        if direction in ("in", "both"):
            for edge in self.get_incoming_edges(node_id):
                if relation_types is None or edge.relation_type in relation_types:
                    neighbors.add(edge.source_id)
        
        return [self.nodes[nid] for nid in neighbors if nid in self.nodes]
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find shortest path between two nodes using BFS"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        
        if source_id == target_id:
            return [source_id]
        
        visited = {source_id}
        queue = [(source_id, [source_id])]
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            for edge in self.get_outgoing_edges(current):
                next_node = edge.target_id
                if next_node == target_id:
                    return path + [next_node]
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))
        
        return None
    
    def find_contagion_paths(
        self,
        source_id: str,
        max_depth: int = 3,
        min_weight: float = 0.3
    ) -> Dict[str, List[List[str]]]:
        """Find all contagion paths from a source node"""
        paths = {}
        visited = {source_id}
        
        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            for edge in self.get_outgoing_edges(current):
                if edge.weight < min_weight:
                    continue
                
                next_node = edge.target_id
                new_path = path + [next_node]
                
                if next_node not in paths:
                    paths[next_node] = []
                paths[next_node].append(new_path)
                
                if next_node not in visited:
                    visited.add(next_node)
                    dfs(next_node, new_path, depth + 1)
        
        dfs(source_id, [source_id], 0)
        return paths
    
    def query_cypher_like(
        self,
        pattern: str,
        params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """
        Execute a Cypher-like query pattern.
        
        Supported patterns:
        - "MATCH (n:NodeType)" - Find all nodes of type
        - "MATCH (n)-[:REL_TYPE]->(m)" - Find relationships
        - "MATCH (n {prop: value})" - Find by property
        """
        nodes = []
        edges = []
        
        # Simple pattern matching (not full Cypher)
        if pattern.startswith("MATCH (n:"):
            # Extract node type
            node_type_str = pattern.split(":")[1].split(")")[0].strip()
            try:
                node_type = NodeType[node_type_str.upper()]
                nodes = self.get_nodes_by_type(node_type)
            except KeyError:
                pass
        
        elif "-[:" in pattern:
            # Relationship pattern
            rel_type_str = pattern.split("-[:")[1].split("]")[0].strip()
            try:
                rel_type = RelationType[rel_type_str.upper()]
                edge_ids = self.edges_by_type.get(rel_type, set())
                edges = [self.edges[eid] for eid in edge_ids]
                
                # Get connected nodes
                node_ids = set()
                for edge in edges:
                    node_ids.add(edge.source_id)
                    node_ids.add(edge.target_id)
                nodes = [self.nodes[nid] for nid in node_ids if nid in self.nodes]
            except KeyError:
                pass
        
        return QueryResult(nodes=nodes, edges=edges)
    
    # ========================================================================
    # Graph Enrichment Methods (Real-time event processing)
    # ========================================================================
    
    def enrich_earnings_event(
        self,
        ticker: str,
        eps_actual: float,
        eps_estimate: float,
        guidance: str,
        tone_score: float
    ) -> GraphNode:
        """
        Enrich graph with new earnings event.
        Updates EarningsEvent node and re-scores CORRELATED_WITH edges.
        """
        # Find or create asset node
        asset_node = self._find_node_by_property("ticker", ticker)
        if not asset_node:
            asset_node = self.add_node(NodeType.ASSET, {"ticker": ticker})
        
        # Create earnings event
        surprise = (eps_actual - eps_estimate) / abs(eps_estimate) if eps_estimate != 0 else 0
        
        event_node = self.add_node(NodeType.EARNINGS_EVENT, {
            "ticker": ticker,
            "eps_actual": eps_actual,
            "eps_estimate": eps_estimate,
            "surprise": surprise,
            "guidance": guidance,
            "tone_score": tone_score,
            "timestamp": datetime.now().isoformat()
        })
        
        # Link to asset
        self.add_edge(
            event_node.node_id,
            asset_node.node_id,
            RelationType.AFFECTS,
            {"impact_type": "earnings", "surprise": surprise}
        )
        
        # Update correlations with sector peers
        sector_edges = [e for e in self.get_outgoing_edges(asset_node.node_id)
                       if e.relation_type == RelationType.BELONGS_TO]
        
        for edge in sector_edges:
            sector_node = self.get_node(edge.target_id)
            if sector_node:
                # Re-score correlations based on earnings surprise
                self._update_sector_correlations(sector_node.node_id, surprise)
        
        logger.info(f"Enriched earnings event: {ticker} surprise={surprise:.2%}")
        return event_node
    
    def enrich_news_article(
        self,
        title: str,
        source: str,
        entities: List[str],
        sentiment_score: float,
        visual_hash: Optional[str] = None
    ) -> GraphNode:
        """
        Enrich graph with new news article.
        Extracts entities via NER, adds MENTIONED_IN edges.
        """
        article_node = self.add_node(NodeType.NEWS_ARTICLE, {
            "title": title,
            "source": source,
            "sentiment_score": sentiment_score,
            "visual_hash": visual_hash,
            "timestamp": datetime.now().isoformat()
        })
        
        # Link to mentioned entities
        for entity in entities:
            entity_node = self._find_node_by_property("ticker", entity)
            if not entity_node:
                entity_node = self._find_node_by_property("name", entity)
            
            if entity_node:
                self.add_edge(
                    entity_node.node_id,
                    article_node.node_id,
                    RelationType.MENTIONED_IN,
                    {"sentiment_score": sentiment_score}
                )
        
        logger.info(f"Enriched news article: {title[:50]}...")
        return article_node
    
    def enrich_polymarket_contract(
        self,
        contract_id: str,
        question: str,
        yes_price: float,
        no_price: float,
        volume: float,
        closes_at: datetime
    ) -> GraphNode:
        """
        Enrich graph with Polymarket contract.
        Links to GeopoliticalEvent or MacroIndicator via PREDICTS edges.
        """
        contract_node = self.add_node(NodeType.POLYMARKET_CONTRACT, {
            "contract_id": contract_id,
            "question": question,
            "yes_price": yes_price,
            "no_price": no_price,
            "implied_probability": yes_price,
            "volume": volume,
            "closes_at": closes_at.isoformat(),
            "timestamp": datetime.now().isoformat()
        })
        
        # Try to link to relevant macro indicators or events
        question_lower = question.lower()
        
        if "fed" in question_lower or "rate" in question_lower:
            fed_node = self._find_node_by_property("indicator_id", "FED_RATE")
            if fed_node:
                self.add_edge(
                    contract_node.node_id,
                    fed_node.node_id,
                    RelationType.PREDICTS,
                    {"calibration_brier": 0.0}  # Will be updated on resolution
                )
        
        if "inflation" in question_lower or "cpi" in question_lower:
            cpi_node = self._find_node_by_property("indicator_id", "CPI")
            if cpi_node:
                self.add_edge(
                    contract_node.node_id,
                    cpi_node.node_id,
                    RelationType.PREDICTS,
                    {"calibration_brier": 0.0}
                )
        
        logger.info(f"Enriched Polymarket contract: {question[:50]}...")
        return contract_node
    
    def enrich_visual_signal(
        self,
        image_hash: str,
        category: str,
        sentiment: str,
        confidence: float,
        affected_assets: List[str]
    ) -> GraphNode:
        """
        Enrich graph with visual signal from OpenCLIP.
        Links to affected Asset nodes via MENTIONED_IN.
        """
        signal_node = self.add_node(NodeType.VISUAL_SIGNAL, {
            "image_hash": image_hash,
            "category": category,
            "sentiment": sentiment,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })
        
        for ticker in affected_assets:
            asset_node = self._find_node_by_property("ticker", ticker)
            if not asset_node:
                asset_node = self.add_node(NodeType.ASSET, {"ticker": ticker})
            
            self.add_edge(
                signal_node.node_id,
                asset_node.node_id,
                RelationType.MENTIONED_IN,
                {"sentiment": sentiment, "confidence": confidence}
            )
        
        logger.info(f"Enriched visual signal: {category} -> {affected_assets}")
        return signal_node
    
    def enrich_trade_signal(
        self,
        hypothesis_id: str,
        asset: str,
        direction: str,
        confidence: float,
        generation: int,
        genome_id: Optional[str] = None
    ) -> GraphNode:
        """
        Enrich graph with trade signal from evolution engine.
        Links to Strategy via EVOLVED_FROM if genome provided.
        """
        signal_node = self.add_node(NodeType.TRADE_SIGNAL, {
            "hypothesis_id": hypothesis_id,
            "asset": asset,
            "direction": direction,
            "confidence": confidence,
            "generation": generation,
            "timestamp": datetime.now().isoformat()
        })
        
        # Link to asset
        asset_node = self._find_node_by_property("ticker", asset)
        if not asset_node:
            asset_node = self.add_node(NodeType.ASSET, {"ticker": asset})
        
        self.add_edge(
            signal_node.node_id,
            asset_node.node_id,
            RelationType.AFFECTS,
            {"direction": direction, "confidence": confidence}
        )
        
        # Link to strategy genome
        if genome_id:
            strategy_node = self._find_node_by_property("genome_id", genome_id)
            if strategy_node:
                self.add_edge(
                    signal_node.node_id,
                    strategy_node.node_id,
                    RelationType.EVOLVED_FROM,
                    {"generation": generation}
                )
        
        logger.info(f"Enriched trade signal: {asset} {direction} conf={confidence:.2%}")
        return signal_node
    
    def _update_sector_correlations(self, sector_id: str, surprise: float) -> None:
        """Update correlation scores within a sector based on earnings surprise"""
        # Get all assets in sector
        sector_assets = []
        for edge in self.get_incoming_edges(sector_id):
            if edge.relation_type == RelationType.BELONGS_TO:
                sector_assets.append(edge.source_id)
        
        # Update CORRELATED_WITH edges between sector peers
        for i, asset_a in enumerate(sector_assets):
            for asset_b in sector_assets[i+1:]:
                # Find existing correlation edge
                existing = None
                for edge in self.get_outgoing_edges(asset_a):
                    if edge.target_id == asset_b and edge.relation_type == RelationType.CORRELATED_WITH:
                        existing = edge
                        break
                
                if existing:
                    # Decay correlation slightly based on surprise divergence
                    new_corr = existing.properties.get("correlation", 0.5) * 0.99
                    existing.update({"correlation": new_corr})
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'nodes_by_type': {
                t.value: len(ids) for t, ids in self.nodes_by_type.items()
            },
            'edges_by_type': {
                t.value: len(ids) for t, ids in self.edges_by_type.items()
            }
        }


# Singleton instance
_gotham_instance: Optional[GothamKnowledgeGraph] = None


def get_gotham() -> GothamKnowledgeGraph:
    """Get the global Gotham instance"""
    global _gotham_instance
    if _gotham_instance is None:
        _gotham_instance = GothamKnowledgeGraph()
    return _gotham_instance
