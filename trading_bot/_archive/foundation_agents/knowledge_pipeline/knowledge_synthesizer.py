"""
Knowledge Synthesizer - Integrating Knowledge from Multiple Sources
====================================================================

Implements knowledge synthesis and integration:
1. Combine insights from papers, anomalies, and cross-domain mappings
2. Build coherent knowledge structures
3. Identify knowledge gaps
4. Generate actionable trading insights

Based on the Foundation Agents paper (arXiv:2504.01990) knowledge systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Types of knowledge"""
    FACTUAL = "factual"              # Facts and data
    PROCEDURAL = "procedural"        # How to do things
    CONCEPTUAL = "conceptual"        # Understanding concepts
    METACOGNITIVE = "metacognitive"  # Knowledge about knowledge
    CAUSAL = "causal"                # Cause-effect relationships
    PREDICTIVE = "predictive"        # Predictions and forecasts
    STRATEGIC = "strategic"          # Trading strategies


class KnowledgeSource(Enum):
    """Sources of knowledge"""
    RESEARCH_PAPER = "research_paper"
    MARKET_DATA = "market_data"
    ANOMALY = "anomaly"
    HYPOTHESIS = "hypothesis"
    CROSS_DOMAIN = "cross_domain"
    EXPERIMENT = "experiment"
    EXPERT = "expert"
    SELF_DISCOVERY = "self_discovery"


class ConfidenceLevel(Enum):
    """Confidence in knowledge"""
    VERY_HIGH = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    VERY_LOW = 1


@dataclass
class KnowledgeItem:
    """A piece of knowledge"""
    knowledge_id: str
    knowledge_type: KnowledgeType
    source: KnowledgeSource
    
    # Content
    title: str
    content: str
    summary: Optional[str] = None
    
    # Structure
    concepts: List[str] = field(default_factory=list)
    relationships: List[Dict[str, str]] = field(default_factory=list)
    
    # Quality
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    evidence_count: int = 0
    contradiction_count: int = 0
    
    # Applicability
    applicable_to: List[str] = field(default_factory=list)  # Assets, strategies, etc.
    conditions: List[str] = field(default_factory=list)     # When applicable
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_validated: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # References
    source_ids: List[str] = field(default_factory=list)
    related_knowledge: List[str] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if knowledge is still valid"""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def reliability_score(self) -> float:
        """Calculate reliability score"""
        base = self.confidence.value / 5
        evidence_bonus = min(0.3, self.evidence_count * 0.05)
        contradiction_penalty = min(0.3, self.contradiction_count * 0.1)
        return max(0, min(1, base + evidence_bonus - contradiction_penalty))
    
    def to_dict(self) -> Dict:
        return {
            'knowledge_id': self.knowledge_id,
            'knowledge_type': self.knowledge_type.value,
            'source': self.source.value,
            'title': self.title,
            'summary': self.summary or self.content[:200],
            'concepts': self.concepts,
            'confidence': self.confidence.value,
            'reliability_score': self.reliability_score(),
            'applicable_to': self.applicable_to,
            'tags': self.tags
        }


@dataclass
class KnowledgeGap:
    """An identified gap in knowledge"""
    gap_id: str
    description: str
    
    # What's missing
    missing_concepts: List[str] = field(default_factory=list)
    missing_relationships: List[str] = field(default_factory=list)
    
    # Impact
    importance: float = 0.5
    blocking: List[str] = field(default_factory=list)  # What this gap blocks
    
    # Resolution
    suggested_sources: List[str] = field(default_factory=list)
    research_questions: List[str] = field(default_factory=list)
    
    # Status
    resolved: bool = False
    resolution_knowledge_id: Optional[str] = None


@dataclass
class SynthesizedInsight:
    """An insight synthesized from multiple knowledge sources"""
    insight_id: str
    title: str
    description: str
    
    # Sources
    source_knowledge: List[str] = field(default_factory=list)
    synthesis_method: str = ""
    
    # Quality
    confidence: float = 0.5
    novelty: float = 0.5
    actionability: float = 0.5
    
    # Trading relevance
    trading_implication: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)
    
    # Validation
    validated: bool = False
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    def overall_score(self) -> float:
        return (self.confidence + self.novelty + self.actionability) / 3
    
    def to_dict(self) -> Dict:
        return {
            'insight_id': self.insight_id,
            'title': self.title,
            'description': self.description,
            'confidence': self.confidence,
            'novelty': self.novelty,
            'actionability': self.actionability,
            'overall_score': self.overall_score(),
            'trading_implication': self.trading_implication,
            'suggested_actions': self.suggested_actions
        }


class KnowledgeGraph:
    """Graph structure for knowledge relationships"""
    
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}  # concept -> properties
        self.edges: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)  # concept -> [(related, relation, weight)]
    
    def add_node(self, concept: str, properties: Optional[Dict] = None):
        """Add a concept node"""
        self.nodes[concept] = properties or {}
    
    def add_edge(self, concept1: str, concept2: str, relation: str, weight: float = 1.0):
        """Add a relationship edge"""
        self.edges[concept1].append((concept2, relation, weight))
        self.edges[concept2].append((concept1, f"inverse_{relation}", weight))
    
    def get_related(self, concept: str, max_depth: int = 2) -> List[Tuple[str, float]]:
        """Get related concepts with relevance scores"""
        if concept not in self.nodes:
            return []
        
        visited = {concept}
        related = []
        current_level = [(concept, 1.0)]
        
        for depth in range(max_depth):
            next_level = []
            decay = 0.5 ** depth
            
            for node, score in current_level:
                for neighbor, relation, weight in self.edges.get(node, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        new_score = score * weight * decay
                        related.append((neighbor, new_score))
                        next_level.append((neighbor, new_score))
            
            current_level = next_level
        
        related.sort(key=lambda x: x[1], reverse=True)
        return related
    
    def find_path(self, concept1: str, concept2: str) -> Optional[List[str]]:
        """Find path between two concepts"""
        if concept1 not in self.nodes or concept2 not in self.nodes:
            return None
        
        # BFS
        queue = [(concept1, [concept1])]
        visited = {concept1}
        
        while queue:
            current, path = queue.pop(0)
            
            if current == concept2:
                return path
            
            for neighbor, _, _ in self.edges.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None


class SynthesisEngine:
    """Engine for synthesizing knowledge"""
    
    def synthesize_from_papers(
        self,
        papers: List[Dict],
        topic: str
    ) -> SynthesizedInsight:
        """Synthesize insight from multiple papers"""
        # Extract common themes
        all_concepts = []
        all_methods = []
        
        for paper in papers:
            all_concepts.extend(paper.get('key_concepts', []))
            if paper.get('methodology'):
                all_methods.append(paper['methodology'])
        
        # Find consensus
        concept_counts = defaultdict(int)
        for concept in all_concepts:
            concept_counts[concept] += 1
        
        common_concepts = [c for c, count in concept_counts.items() if count >= 2]
        
        # Generate insight
        insight = SynthesizedInsight(
            insight_id=f"synth_{topic}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            title=f"Synthesized insight on {topic}",
            description=f"Analysis of {len(papers)} papers reveals common themes: {', '.join(common_concepts[:5])}",
            source_knowledge=[p.get('arxiv_id', '') for p in papers],
            synthesis_method="paper_aggregation",
            confidence=min(0.9, 0.5 + len(papers) * 0.1),
            novelty=0.6,
            actionability=0.5
        )
        
        # Add trading implications
        if 'prediction' in common_concepts or 'forecasting' in common_concepts:
            insight.trading_implication = "Predictive models may improve alpha generation"
            insight.suggested_actions.append("Implement and backtest predictive approach")
        
        if 'risk' in common_concepts:
            insight.trading_implication = "Risk management improvements possible"
            insight.suggested_actions.append("Review and enhance risk models")
        
        return insight
    
    def synthesize_from_anomalies(
        self,
        anomalies: List[Dict],
        context: Optional[Dict] = None
    ) -> SynthesizedInsight:
        """Synthesize insight from anomaly patterns"""
        # Analyze anomaly patterns
        anomaly_types = [a.get('anomaly_type', '') for a in anomalies]
        assets = [a.get('asset', '') for a in anomalies if a.get('asset')]
        
        type_counts = defaultdict(int)
        for t in anomaly_types:
            type_counts[t] += 1
        
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "unknown"
        
        insight = SynthesizedInsight(
            insight_id=f"synth_anomaly_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            title=f"Pattern in {dominant_type} anomalies",
            description=f"Detected {len(anomalies)} anomalies with dominant type '{dominant_type}' across {len(set(assets))} assets",
            source_knowledge=[a.get('anomaly_id', '') for a in anomalies],
            synthesis_method="anomaly_pattern_analysis",
            confidence=0.6,
            novelty=0.7,
            actionability=0.6
        )
        
        # Trading implications
        if dominant_type == 'volatility':
            insight.trading_implication = "Volatility regime may be changing"
            insight.suggested_actions.append("Adjust position sizes")
            insight.suggested_actions.append("Review volatility forecasts")
        elif dominant_type == 'correlation':
            insight.trading_implication = "Correlation structure may be breaking down"
            insight.suggested_actions.append("Review portfolio diversification")
        
        return insight
    
    def synthesize_cross_domain(
        self,
        domain_mapping: Dict,
        target_application: str
    ) -> SynthesizedInsight:
        """Synthesize insight from cross-domain mapping"""
        source_domain = domain_mapping.get('source_domain', '')
        target_domain = domain_mapping.get('target_domain', '')
        mappings = domain_mapping.get('concept_mappings', [])
        
        insight = SynthesizedInsight(
            insight_id=f"synth_xdomain_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            title=f"Cross-domain insight: {source_domain} → {target_domain}",
            description=f"Mapped {len(mappings)} concepts from {source_domain} to {target_domain} for {target_application}",
            source_knowledge=[m.get('mapping_id', '') for m in mappings],
            synthesis_method="cross_domain_transfer",
            confidence=0.5,
            novelty=0.8,
            actionability=0.4
        )
        
        # Extract trading applications
        applications = domain_mapping.get('trading_applications', [])
        if applications:
            insight.trading_implication = f"Potential applications: {', '.join(applications[:3])}"
            for app in applications[:2]:
                insight.suggested_actions.append(f"Explore {app}")
        
        return insight


class KnowledgeSynthesizer:
    """
    Knowledge Synthesizer
    
    Central system for synthesizing and integrating knowledge
    from multiple sources into actionable insights.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Storage
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.knowledge_graph = KnowledgeGraph()
        self.insights: Dict[str, SynthesizedInsight] = {}
        self.gaps: Dict[str, KnowledgeGap] = {}
        
        # Synthesis engine
        self.synthesis_engine = SynthesisEngine()
        
        # Indices
        self.by_type: Dict[KnowledgeType, Set[str]] = defaultdict(set)
        self.by_source: Dict[KnowledgeSource, Set[str]] = defaultdict(set)
        self.by_concept: Dict[str, Set[str]] = defaultdict(set)
        self.by_tag: Dict[str, Set[str]] = defaultdict(set)
        
        # Statistics
        self.stats = {
            'knowledge_items': 0,
            'insights_generated': 0,
            'gaps_identified': 0,
            'gaps_resolved': 0
        }
        
        logger.info("Knowledge Synthesizer initialized")
    
    def add_knowledge(self, item: KnowledgeItem) -> str:
        """Add knowledge to the base"""
        self.knowledge_base[item.knowledge_id] = item
        
        # Update indices
        self.by_type[item.knowledge_type].add(item.knowledge_id)
        self.by_source[item.source].add(item.knowledge_id)
        
        for concept in item.concepts:
            self.by_concept[concept].add(item.knowledge_id)
            self.knowledge_graph.add_node(concept)
        
        for tag in item.tags:
            self.by_tag[tag].add(item.knowledge_id)
        
        # Add relationships to graph
        for rel in item.relationships:
            if 'from' in rel and 'to' in rel:
                self.knowledge_graph.add_edge(
                    rel['from'],
                    rel['to'],
                    rel.get('type', 'related'),
                    rel.get('weight', 1.0)
                )
        
        self.stats['knowledge_items'] += 1
        logger.debug(f"Added knowledge: {item.title}")
        
        return item.knowledge_id
    
    def create_knowledge(
        self,
        title: str,
        content: str,
        knowledge_type: KnowledgeType,
        source: KnowledgeSource,
        concepts: Optional[List[str]] = None,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        applicable_to: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> KnowledgeItem:
        """Create and add knowledge item"""
        item = KnowledgeItem(
            knowledge_id=f"know_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(title.encode()).hexdigest()[:8]}",
            knowledge_type=knowledge_type,
            source=source,
            title=title,
            content=content,
            concepts=concepts or [],
            confidence=confidence,
            applicable_to=applicable_to or [],
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.add_knowledge(item)
        return item
    
    def synthesize_from_papers(
        self,
        papers: List[Dict],
        topic: str
    ) -> SynthesizedInsight:
        """Synthesize insight from research papers"""
        insight = self.synthesis_engine.synthesize_from_papers(papers, topic)
        self.insights[insight.insight_id] = insight
        self.stats['insights_generated'] += 1
        
        # Create knowledge item from insight
        self.create_knowledge(
            title=insight.title,
            content=insight.description,
            knowledge_type=KnowledgeType.CONCEPTUAL,
            source=KnowledgeSource.RESEARCH_PAPER,
            concepts=topic.split(),
            confidence=ConfidenceLevel(min(5, int(insight.confidence * 5) + 1)),
            tags=['synthesized', 'from_papers', topic]
        )
        
        return insight
    
    def synthesize_from_anomalies(
        self,
        anomalies: List[Dict],
        context: Optional[Dict] = None
    ) -> SynthesizedInsight:
        """Synthesize insight from anomalies"""
        insight = self.synthesis_engine.synthesize_from_anomalies(anomalies, context)
        self.insights[insight.insight_id] = insight
        self.stats['insights_generated'] += 1
        
        # Create knowledge item
        self.create_knowledge(
            title=insight.title,
            content=insight.description,
            knowledge_type=KnowledgeType.PREDICTIVE,
            source=KnowledgeSource.ANOMALY,
            confidence=ConfidenceLevel(min(5, int(insight.confidence * 5) + 1)),
            tags=['synthesized', 'from_anomalies']
        )
        
        return insight
    
    def synthesize_cross_domain(
        self,
        domain_mapping: Dict,
        target_application: str
    ) -> SynthesizedInsight:
        """Synthesize insight from cross-domain mapping"""
        insight = self.synthesis_engine.synthesize_cross_domain(
            domain_mapping, target_application
        )
        self.insights[insight.insight_id] = insight
        self.stats['insights_generated'] += 1
        
        # Create knowledge item
        self.create_knowledge(
            title=insight.title,
            content=insight.description,
            knowledge_type=KnowledgeType.CONCEPTUAL,
            source=KnowledgeSource.CROSS_DOMAIN,
            confidence=ConfidenceLevel(min(5, int(insight.confidence * 5) + 1)),
            tags=['synthesized', 'cross_domain', target_application]
        )
        
        return insight
    
    def identify_gaps(self) -> List[KnowledgeGap]:
        """Identify gaps in knowledge"""
        gaps = []
        
        # Find isolated concepts (not well connected)
        for concept in self.knowledge_graph.nodes:
            related = self.knowledge_graph.get_related(concept, max_depth=1)
            if len(related) < 2:
                gap = KnowledgeGap(
                    gap_id=f"gap_{concept}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    description=f"Concept '{concept}' is poorly connected",
                    missing_relationships=[f"relationships for {concept}"],
                    importance=0.5,
                    research_questions=[f"What relates to {concept}?"]
                )
                gaps.append(gap)
                self.gaps[gap.gap_id] = gap
        
        # Find knowledge types with low coverage
        type_counts = {kt: len(ids) for kt, ids in self.by_type.items()}
        avg_count = np.mean(list(type_counts.values())) if type_counts else 0
        
        for kt, count in type_counts.items():
            if count < avg_count * 0.5:
                gap = KnowledgeGap(
                    gap_id=f"gap_type_{kt.value}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    description=f"Low coverage of {kt.value} knowledge",
                    importance=0.6,
                    research_questions=[f"What {kt.value} knowledge is missing?"]
                )
                gaps.append(gap)
                self.gaps[gap.gap_id] = gap
        
        self.stats['gaps_identified'] += len(gaps)
        return gaps
    
    def query_knowledge(
        self,
        concepts: Optional[List[str]] = None,
        knowledge_type: Optional[KnowledgeType] = None,
        source: Optional[KnowledgeSource] = None,
        tags: Optional[List[str]] = None,
        min_confidence: Optional[ConfidenceLevel] = None,
        limit: int = 20
    ) -> List[KnowledgeItem]:
        """Query knowledge base"""
        candidates = set(self.knowledge_base.keys())
        
        # Filter by concepts
        if concepts:
            concept_matches = set()
            for concept in concepts:
                concept_matches.update(self.by_concept.get(concept, set()))
            candidates &= concept_matches
        
        # Filter by type
        if knowledge_type:
            candidates &= self.by_type.get(knowledge_type, set())
        
        # Filter by source
        if source:
            candidates &= self.by_source.get(source, set())
        
        # Filter by tags
        if tags:
            for tag in tags:
                candidates &= self.by_tag.get(tag, set())
        
        # Get items and filter by confidence
        items = [self.knowledge_base[kid] for kid in candidates]
        
        if min_confidence:
            items = [i for i in items if i.confidence.value >= min_confidence.value]
        
        # Filter valid items
        items = [i for i in items if i.is_valid()]
        
        # Sort by reliability
        items.sort(key=lambda i: i.reliability_score(), reverse=True)
        
        return items[:limit]
    
    def get_related_knowledge(
        self,
        knowledge_id: str,
        max_results: int = 10
    ) -> List[Tuple[KnowledgeItem, float]]:
        """Get knowledge related to a given item"""
        if knowledge_id not in self.knowledge_base:
            return []
        
        item = self.knowledge_base[knowledge_id]
        related_scores: Dict[str, float] = defaultdict(float)
        
        # Find through concepts
        for concept in item.concepts:
            graph_related = self.knowledge_graph.get_related(concept)
            for related_concept, score in graph_related:
                for kid in self.by_concept.get(related_concept, set()):
                    if kid != knowledge_id:
                        related_scores[kid] += score
        
        # Find through tags
        for tag in item.tags:
            for kid in self.by_tag.get(tag, set()):
                if kid != knowledge_id:
                    related_scores[kid] += 0.3
        
        # Sort and return
        sorted_related = sorted(related_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for kid, score in sorted_related[:max_results]:
            if kid in self.knowledge_base:
                results.append((self.knowledge_base[kid], score))
        
        return results
    
    def validate_knowledge(
        self,
        knowledge_id: str,
        evidence: Dict[str, Any],
        supports: bool
    ):
        """Validate or contradict knowledge with evidence"""
        if knowledge_id not in self.knowledge_base:
            return
        
        item = self.knowledge_base[knowledge_id]
        
        if supports:
            item.evidence_count += 1
            if item.confidence.value < 5:
                item.confidence = ConfidenceLevel(min(5, item.confidence.value + 1))
        else:
            item.contradiction_count += 1
            if item.confidence.value > 1:
                item.confidence = ConfidenceLevel(max(1, item.confidence.value - 1))
        
        item.last_validated = datetime.utcnow()
        item.metadata['last_evidence'] = evidence
    
    def get_actionable_insights(
        self,
        min_actionability: float = 0.5,
        limit: int = 10
    ) -> List[SynthesizedInsight]:
        """Get actionable insights"""
        actionable = [
            i for i in self.insights.values()
            if i.actionability >= min_actionability
        ]
        actionable.sort(key=lambda i: i.overall_score(), reverse=True)
        return actionable[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get synthesizer statistics"""
        return {
            **self.stats,
            'by_type': {kt.value: len(ids) for kt, ids in self.by_type.items()},
            'by_source': {ks.value: len(ids) for ks, ids in self.by_source.items()},
            'graph_nodes': len(self.knowledge_graph.nodes),
            'graph_edges': sum(len(e) for e in self.knowledge_graph.edges.values()),
            'active_insights': len([i for i in self.insights.values() if not i.validated]),
            'unresolved_gaps': len([g for g in self.gaps.values() if not g.resolved])
        }
