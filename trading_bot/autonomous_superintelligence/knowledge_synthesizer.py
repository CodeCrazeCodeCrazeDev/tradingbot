"""
Knowledge Synthesis System
Synthesizes knowledge across all systems and discovers emergent insights.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeNode:
    node_id: str
    domain: str
    content: str
    confidence: float
    sources: List[str]
    connections: List[str]
    created_at: datetime
    importance: float = 0.5


@dataclass
class Insight:
    insight_id: str
    title: str
    description: str
    knowledge_nodes: List[str]
    significance: float
    actionable: bool
    discovered_at: datetime


class KnowledgeSynthesizer:
    """
    Synthesizes knowledge from all systems to discover emergent insights.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.knowledge_graph: Dict[str, KnowledgeNode] = {}
        self.insights: List[Insight] = []
        
        self.running = False
        
        self.storage_path = Path(config.get('storage_path', 'knowledge_synthesis_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Knowledge Synthesizer initialized")
    
    async def initialize(self):
        """Initialize knowledge synthesizer."""
        logger.info("Initializing Knowledge Synthesizer")
        
        await self._load_knowledge_graph()
        
        self.running = True
        logger.info("Knowledge Synthesizer ready - %d nodes", len(self.knowledge_graph))
    
    async def _load_knowledge_graph(self):
        """Load knowledge graph."""
        kg_file = self.storage_path / 'knowledge_graph.json'
        if kg_file.exists():
            with open(kg_file, 'r') as f:
                data = json.load(f)
                for node_data in data:
                    node = KnowledgeNode(
                        node_id=node_data['node_id'],
                        domain=node_data['domain'],
                        content=node_data['content'],
                        confidence=node_data['confidence'],
                        sources=node_data['sources'],
                        connections=node_data['connections'],
                        created_at=datetime.fromisoformat(node_data['created_at']),
                        importance=node_data.get('importance', 0.5),
                    )
                    self.knowledge_graph[node.node_id] = node
    
    async def add_knowledge(
        self,
        domain: str,
        content: str,
        confidence: float,
        sources: List[str]
    ) -> KnowledgeNode:
        """Add new knowledge to the graph."""
        node = KnowledgeNode(
            node_id=f"node_{datetime.now().timestamp()}",
            domain=domain,
            content=content,
            confidence=confidence,
            sources=sources,
            connections=[],
            created_at=datetime.now(),
        )
        
        self.knowledge_graph[node.node_id] = node
        
        await self._connect_knowledge(node)
        
        return node
    
    async def _connect_knowledge(self, new_node: KnowledgeNode):
        """Connect new knowledge to existing nodes."""
        for node in self.knowledge_graph.values():
            if node.node_id == new_node.node_id:
                continue
            
            if node.domain == new_node.domain:
                similarity = np.random.random()
                if similarity > 0.7:
                    new_node.connections.append(node.node_id)
                    node.connections.append(new_node.node_id)
    
    async def synthesize_insights(self) -> List[Insight]:
        """Synthesize insights from knowledge graph."""
        insights = []
        
        clusters = await self._find_knowledge_clusters()
        
        for cluster in clusters:
            if len(cluster) >= 3:
                insight = await self._generate_insight_from_cluster(cluster)
                if insight:
                    insights.append(insight)
                    self.insights.append(insight)
        
        logger.info("Synthesized %d new insights", len(insights))
        
        return insights
    
    async def _find_knowledge_clusters(self) -> List[List[str]]:
        """Find clusters of related knowledge."""
        clusters = []
        visited = set()
        
        for node_id in self.knowledge_graph.keys():
            if node_id not in visited:
                cluster = await self._expand_cluster(node_id, visited)
                if len(cluster) > 1:
                    clusters.append(cluster)
        
        return clusters
    
    async def _expand_cluster(self, start_node: str, visited: Set[str]) -> List[str]:
        """Expand a knowledge cluster."""
        cluster = [start_node]
        visited.add(start_node)
        
        node = self.knowledge_graph.get(start_node)
        if not node:
            return cluster
        
        for connected_id in node.connections:
            if connected_id not in visited:
                cluster.extend(await self._expand_cluster(connected_id, visited))
        
        return cluster
    
    async def _generate_insight_from_cluster(self, cluster: List[str]) -> Optional[Insight]:
        """Generate an insight from a knowledge cluster."""
        nodes = [self.knowledge_graph[nid] for nid in cluster if nid in self.knowledge_graph]
        
        if not nodes:
            return None
        
        avg_confidence = np.mean([n.confidence for n in nodes])
        
        if avg_confidence < 0.6:
            return None
        
        insight = Insight(
            insight_id=f"insight_{datetime.now().timestamp()}",
            title=f"Emergent insight from {nodes[0].domain}",
            description=f"Synthesized from {len(nodes)} knowledge nodes",
            knowledge_nodes=cluster,
            significance=avg_confidence * len(nodes) / 10,
            actionable=True,
            discovered_at=datetime.now(),
        )
        
        return insight
    
    async def synthesis_loop(self):
        """Main synthesis loop."""
        logger.info("Starting knowledge synthesis loop")
        
        while self.running:
            try:
                insights = await self.synthesize_insights()
                
                for insight in insights:
                    if insight.significance > 0.7:
                        logger.info("HIGH-SIGNIFICANCE INSIGHT: %s", insight.title)
                
                await self._persist_state()
                
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error("Error in synthesis loop: %s", e)
                await asyncio.sleep(120)
    
    async def _persist_state(self):
        """Persist knowledge state."""
        kg_file = self.storage_path / 'knowledge_graph.json'
        kg_data = [
            {
                'node_id': n.node_id,
                'domain': n.domain,
                'content': n.content,
                'confidence': n.confidence,
                'sources': n.sources,
                'connections': n.connections,
                'created_at': n.created_at.isoformat(),
                'importance': n.importance,
            }
            for n in self.knowledge_graph.values()
        ]
        
        with open(kg_file, 'w') as f:
            json.dump(kg_data, f, indent=2)
        
        insights_file = self.storage_path / 'insights.json'
        insights_data = [
            {
                'insight_id': i.insight_id,
                'title': i.title,
                'description': i.description,
                'knowledge_nodes': i.knowledge_nodes,
                'significance': i.significance,
                'actionable': i.actionable,
                'discovered_at': i.discovered_at.isoformat(),
            }
            for i in self.insights
        ]
        
        with open(insights_file, 'w') as f:
            json.dump(insights_data, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Get synthesizer status."""
        return {
            'knowledge_nodes': len(self.knowledge_graph),
            'insights_generated': len(self.insights),
            'avg_node_confidence': np.mean([n.confidence for n in self.knowledge_graph.values()]) if self.knowledge_graph else 0.0,
            'high_significance_insights': sum(1 for i in self.insights if i.significance > 0.7),
        }
    
    async def shutdown(self):
        """Shutdown knowledge synthesizer."""
        logger.info("Shutting down Knowledge Synthesizer")
        self.running = False
        await self._persist_state()
