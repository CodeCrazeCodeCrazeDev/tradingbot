"""
Perplexity Deep Research Engine
================================

Advanced research engine inspired by Perplexity's approach:
- Multi-source information gathering
- Cross-referencing and verification
- Citation tracking and provenance
- Confidence scoring based on source quality
- Iterative refinement of findings
- Synthesis of disparate information
- Contradiction detection and resolution

This enables deep, thorough research on any trading topic
with full transparency on sources and confidence.
"""

import asyncio
import logging
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import json

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Types of information sources"""
    MARKET_DATA = "market_data"
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    ECONOMIC = "economic"
    REGULATORY = "regulatory"
    EXPERT_OPINION = "expert_opinion"
    HISTORICAL = "historical"
    ALTERNATIVE = "alternative"


class SourceReliability(Enum):
    """Reliability levels of sources"""
    AUTHORITATIVE = "authoritative"  # Official sources, exchanges
    HIGH = "high"                    # Major news outlets, verified data
    MEDIUM = "medium"                # General news, social influencers
    LOW = "low"                      # Unverified, rumors
    UNKNOWN = "unknown"              # New/unrated sources


class ResearchDepth(Enum):
    """Depth of research"""
    QUICK = "quick"           # Surface level, fast
    STANDARD = "standard"     # Normal depth
    DEEP = "deep"             # Thorough investigation
    EXHAUSTIVE = "exhaustive" # Leave no stone unturned


@dataclass
class Citation:
    """A citation for a piece of information"""
    citation_id: str
    source_type: SourceType
    source_name: str
    source_url: Optional[str]
    reliability: SourceReliability
    timestamp: datetime
    content_hash: str
    
    # Verification
    verified: bool = False
    verification_method: Optional[str] = None
    cross_references: List[str] = field(default_factory=list)
    
    def get_reliability_score(self) -> float:
        """Get numeric reliability score"""
        scores = {
            SourceReliability.AUTHORITATIVE: 1.0,
            SourceReliability.HIGH: 0.8,
            SourceReliability.MEDIUM: 0.5,
            SourceReliability.LOW: 0.2,
            SourceReliability.UNKNOWN: 0.3,
        }
        base_score = scores.get(self.reliability, 0.3)
        
        # Boost if verified
        if self.verified:
            base_score = min(1.0, base_score + 0.1)
        
        # Boost if cross-referenced
        if len(self.cross_references) > 0:
            base_score = min(1.0, base_score + 0.05 * len(self.cross_references))
        
        return base_score


@dataclass
class ResearchFinding:
    """A finding from research"""
    finding_id: str
    topic: str
    content: str
    finding_type: str  # "fact", "opinion", "prediction", "analysis"
    
    # Evidence
    citations: List[Citation]
    confidence: float
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    contradictions: List[str] = field(default_factory=list)
    supporting_findings: List[str] = field(default_factory=list)
    
    def get_evidence_strength(self) -> float:
        """Calculate strength of evidence"""
        if not self.citations:
            return 0.0
        
        # Average reliability of citations
        avg_reliability = sum(c.get_reliability_score() for c in self.citations) / len(self.citations)
        
        # Factor in number of sources
        source_factor = min(1.0, len(self.citations) / 3)  # Max boost at 3+ sources
        
        # Factor in contradictions
        contradiction_penalty = 0.1 * len(self.contradictions)
        
        return max(0, avg_reliability * source_factor - contradiction_penalty)


@dataclass
class ResearchQuery:
    """A research query"""
    query_id: str
    query_text: str
    depth: ResearchDepth
    focus_areas: List[SourceType]
    
    # Constraints
    max_sources: int = 20
    time_limit_seconds: float = 60.0
    min_reliability: SourceReliability = SourceReliability.LOW
    
    # Results
    findings: List[ResearchFinding] = field(default_factory=list)
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SourceRegistry:
    """
    Registry of information sources with reliability tracking
    """
    
    def __init__(self):
        self.sources: Dict[str, Dict[str, Any]] = {}
        self._init_default_sources()
    
    def _init_default_sources(self) -> None:
        """Initialize default source configurations"""
        default_sources = [
            # Market Data
            {"name": "exchange_data", "type": SourceType.MARKET_DATA, "reliability": SourceReliability.AUTHORITATIVE},
            {"name": "bloomberg", "type": SourceType.MARKET_DATA, "reliability": SourceReliability.AUTHORITATIVE},
            {"name": "reuters", "type": SourceType.NEWS, "reliability": SourceReliability.HIGH},
            
            # News
            {"name": "financial_times", "type": SourceType.NEWS, "reliability": SourceReliability.HIGH},
            {"name": "wsj", "type": SourceType.NEWS, "reliability": SourceReliability.HIGH},
            {"name": "cnbc", "type": SourceType.NEWS, "reliability": SourceReliability.MEDIUM},
            
            # Social
            {"name": "twitter_verified", "type": SourceType.SOCIAL_MEDIA, "reliability": SourceReliability.MEDIUM},
            {"name": "reddit_wsb", "type": SourceType.SOCIAL_MEDIA, "reliability": SourceReliability.LOW},
            
            # Fundamental
            {"name": "sec_filings", "type": SourceType.FUNDAMENTAL, "reliability": SourceReliability.AUTHORITATIVE},
            {"name": "company_reports", "type": SourceType.FUNDAMENTAL, "reliability": SourceReliability.HIGH},
            
            # Economic
            {"name": "fed_data", "type": SourceType.ECONOMIC, "reliability": SourceReliability.AUTHORITATIVE},
            {"name": "bls_data", "type": SourceType.ECONOMIC, "reliability": SourceReliability.AUTHORITATIVE},
            
            # Technical
            {"name": "tradingview", "type": SourceType.TECHNICAL, "reliability": SourceReliability.MEDIUM},
            {"name": "technical_analysis", "type": SourceType.TECHNICAL, "reliability": SourceReliability.MEDIUM},
        ]
        
        for source in default_sources:
            self.register_source(
                source["name"],
                source["type"],
                source["reliability"]
            )
    
    def register_source(
        self,
        name: str,
        source_type: SourceType,
        reliability: SourceReliability,
        url: Optional[str] = None,
    ) -> None:
        """Register a new source"""
        self.sources[name] = {
            "name": name,
            "type": source_type,
            "reliability": reliability,
            "url": url,
            "usage_count": 0,
            "accuracy_history": [],
        }
    
    def get_source(self, name: str) -> Optional[Dict[str, Any]]:
        """Get source information"""
        return self.sources.get(name)
    
    def update_accuracy(self, name: str, was_accurate: bool) -> None:
        """Update source accuracy history"""
        if name in self.sources:
            self.sources[name]["accuracy_history"].append(was_accurate)
            # Keep last 100
            if len(self.sources[name]["accuracy_history"]) > 100:
                self.sources[name]["accuracy_history"] = self.sources[name]["accuracy_history"][-100:]
    
    def get_sources_by_type(self, source_type: SourceType) -> List[Dict[str, Any]]:
        """Get all sources of a type"""
        return [s for s in self.sources.values() if s["type"] == source_type]
    
    def get_reliable_sources(self, min_reliability: SourceReliability) -> List[Dict[str, Any]]:
        """Get sources meeting minimum reliability"""
        reliability_order = [
            SourceReliability.UNKNOWN,
            SourceReliability.LOW,
            SourceReliability.MEDIUM,
            SourceReliability.HIGH,
            SourceReliability.AUTHORITATIVE,
        ]
        min_index = reliability_order.index(min_reliability)
        
        return [
            s for s in self.sources.values()
            if reliability_order.index(s["reliability"]) >= min_index
        ]


class InformationSynthesizer:
    """
    Synthesizes information from multiple sources
    """
    
    def __init__(self):
        self.synthesis_history: List[Dict[str, Any]] = []
    
    def synthesize(self, findings: List[ResearchFinding]) -> Dict[str, Any]:
        """Synthesize multiple findings into coherent summary"""
        if not findings:
            return {"summary": "No findings to synthesize", "confidence": 0}
        
        # Group by topic
        by_topic: Dict[str, List[ResearchFinding]] = {}
        for finding in findings:
            if finding.topic not in by_topic:
                by_topic[finding.topic] = []
            by_topic[finding.topic].append(finding)
        
        # Synthesize each topic
        topic_summaries = []
        total_confidence = 0
        
        for topic, topic_findings in by_topic.items():
            # Get consensus
            contents = [f.content for f in topic_findings]
            confidences = [f.confidence for f in topic_findings]
            
            # Weight by confidence
            weighted_confidence = sum(
                f.confidence * f.get_evidence_strength()
                for f in topic_findings
            ) / len(topic_findings)
            
            topic_summaries.append({
                "topic": topic,
                "findings_count": len(topic_findings),
                "avg_confidence": sum(confidences) / len(confidences),
                "weighted_confidence": weighted_confidence,
                "key_points": contents[:3],  # Top 3 points
            })
            
            total_confidence += weighted_confidence
        
        synthesis = {
            "summary": f"Synthesized {len(findings)} findings across {len(by_topic)} topics",
            "topics": topic_summaries,
            "overall_confidence": total_confidence / len(by_topic) if by_topic else 0,
            "total_citations": sum(len(f.citations) for f in findings),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.synthesis_history.append(synthesis)
        
        return synthesis
    
    def detect_contradictions(self, findings: List[ResearchFinding]) -> List[Dict[str, Any]]:
        """Detect contradictions between findings"""
        contradictions = []
        
        # Simple keyword-based contradiction detection
        contradiction_pairs = [
            ("bullish", "bearish"),
            ("buy", "sell"),
            ("increase", "decrease"),
            ("positive", "negative"),
            ("growth", "decline"),
            ("strong", "weak"),
        ]
        
        for i, f1 in enumerate(findings):
            for f2 in findings[i + 1:]:
                if f1.topic != f2.topic:
                    continue
                
                content1 = f1.content.lower()
                content2 = f2.content.lower()
                
                for word1, word2 in contradiction_pairs:
                    if (word1 in content1 and word2 in content2) or \
                       (word2 in content1 and word1 in content2):
                        contradictions.append({
                            "finding1_id": f1.finding_id,
                            "finding2_id": f2.finding_id,
                            "topic": f1.topic,
                            "type": f"{word1} vs {word2}",
                            "confidence_diff": abs(f1.confidence - f2.confidence),
                        })
                        break
        
        return contradictions
    
    def resolve_contradiction(
        self,
        finding1: ResearchFinding,
        finding2: ResearchFinding
    ) -> ResearchFinding:
        """Resolve contradiction by choosing more reliable finding"""
        strength1 = finding1.get_evidence_strength()
        strength2 = finding2.get_evidence_strength()
        
        if strength1 >= strength2:
            winner = finding1
            loser = finding2
        else:
            winner = finding2
            loser = finding1
        
        # Add contradiction note
        winner.contradictions.append(loser.finding_id)
        
        return winner


class DeepResearchEngine:
    """
    Deep Research Engine
    
    Conducts thorough, multi-source research with:
    - Parallel source querying
    - Cross-referencing and verification
    - Citation tracking
    - Contradiction detection
    - Confidence scoring
    - Iterative refinement
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.source_registry = SourceRegistry()
        self.synthesizer = InformationSynthesizer()
        
        # Research state
        self.active_queries: Dict[str, ResearchQuery] = {}
        self.completed_queries: List[ResearchQuery] = []
        
        # Cache
        self.finding_cache: Dict[str, ResearchFinding] = {}
        self.cache_ttl_hours = self.config.get('cache_ttl_hours', 1)
        
        # Statistics
        self.total_queries = 0
        self.total_findings = 0
        self.total_citations = 0
        
        logger.info("DeepResearchEngine initialized")
    
    async def research(
        self,
        query_text: str,
        depth: ResearchDepth = ResearchDepth.STANDARD,
        focus_areas: Optional[List[SourceType]] = None,
    ) -> ResearchQuery:
        """Conduct research on a topic"""
        query_id = f"query_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        query = ResearchQuery(
            query_id=query_id,
            query_text=query_text,
            depth=depth,
            focus_areas=focus_areas or list(SourceType),
            started_at=datetime.utcnow(),
        )
        
        self.active_queries[query_id] = query
        self.total_queries += 1
        
        try:
            # Gather information from sources
            findings = await self._gather_information(query)
            
            # Cross-reference findings
            findings = self._cross_reference(findings)
            
            # Detect and resolve contradictions
            contradictions = self.synthesizer.detect_contradictions(findings)
            if contradictions:
                findings = self._resolve_contradictions(findings, contradictions)
            
            # Calculate final confidence scores
            for finding in findings:
                finding.confidence = finding.get_evidence_strength()
            
            query.findings = findings
            query.status = "completed"
            query.completed_at = datetime.utcnow()
            
            self.total_findings += len(findings)
            self.total_citations += sum(len(f.citations) for f in findings)
            
        except Exception as e:
            query.status = f"error: {str(e)}"
            logger.error(f"Research error: {e}")
        
        finally:
            del self.active_queries[query_id]
            self.completed_queries.append(query)
        
        return query
    
    async def _gather_information(self, query: ResearchQuery) -> List[ResearchFinding]:
        """Gather information from multiple sources"""
        findings = []
        
        # Determine sources to query based on focus areas
        sources_to_query = []
        for focus in query.focus_areas:
            sources_to_query.extend(self.source_registry.get_sources_by_type(focus))
        
        # Filter by reliability
        sources_to_query = [
            s for s in sources_to_query
            if self._meets_reliability(s["reliability"], query.min_reliability)
        ]
        
        # Limit sources
        sources_to_query = sources_to_query[:query.max_sources]
        
        # Query each source (simulated)
        for source in sources_to_query:
            finding = await self._query_source(source, query)
            if finding:
                findings.append(finding)
                
                # Cache finding
                self.finding_cache[finding.finding_id] = finding
        
        return findings
    
    async def _query_source(
        self,
        source: Dict[str, Any],
        query: ResearchQuery
    ) -> Optional[ResearchFinding]:
        """Query a single source (simulated)"""
        # Simulate source query
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Generate simulated finding based on source type
        source_type = source["type"]
        
        content = self._generate_simulated_content(source_type, query.query_text)
        if not content:
            return None
        
        # Create citation
        citation = Citation(
            citation_id=f"cite_{hashlib.md5(f'{source["name"]}_{datetime.utcnow()}'.encode()).hexdigest()[:8]}",
            source_type=source_type,
            source_name=source["name"],
            source_url=source.get("url"),
            reliability=source["reliability"],
            timestamp=datetime.utcnow(),
            content_hash=hashlib.md5(content.encode()).hexdigest(),
        )
        
        # Create finding
        finding = ResearchFinding(
            finding_id=f"finding_{datetime.utcnow().strftime('%H%M%S%f')}_{source['name']}",
            topic=self._extract_topic(query.query_text),
            content=content,
            finding_type=self._determine_finding_type(source_type),
            citations=[citation],
            confidence=citation.get_reliability_score(),
        )
        
        return finding
    
    def _generate_simulated_content(self, source_type: SourceType, query: str) -> str:
        """Generate simulated content based on source type"""
        import random
        
        templates = {
            SourceType.MARKET_DATA: [
                f"Current price shows {random.choice(['bullish', 'bearish', 'neutral'])} momentum",
                f"Volume is {random.choice(['above', 'below', 'at'])} average",
                f"Price action indicates {random.choice(['accumulation', 'distribution', 'consolidation'])}",
            ],
            SourceType.NEWS: [
                f"Recent developments suggest {random.choice(['positive', 'negative', 'mixed'])} outlook",
                f"Market participants are {random.choice(['optimistic', 'cautious', 'uncertain'])}",
                f"Key events may impact {random.choice(['short-term', 'medium-term', 'long-term'])} trajectory",
            ],
            SourceType.TECHNICAL: [
                f"Technical indicators show {random.choice(['overbought', 'oversold', 'neutral'])} conditions",
                f"Support level at {random.randint(90, 110)}%, resistance at {random.randint(110, 130)}%",
                f"Trend is {random.choice(['strongly bullish', 'weakly bullish', 'neutral', 'weakly bearish', 'strongly bearish'])}",
            ],
            SourceType.FUNDAMENTAL: [
                f"Fundamentals indicate {random.choice(['undervalued', 'fairly valued', 'overvalued'])} status",
                f"Earnings growth is {random.choice(['accelerating', 'stable', 'decelerating'])}",
                f"Balance sheet shows {random.choice(['strong', 'moderate', 'weak'])} position",
            ],
            SourceType.SENTIMENT: [
                f"Sentiment is {random.choice(['extremely bullish', 'bullish', 'neutral', 'bearish', 'extremely bearish'])}",
                f"Social media activity is {random.choice(['increasing', 'stable', 'decreasing'])}",
                f"Institutional positioning is {random.choice(['long', 'neutral', 'short'])}",
            ],
        }
        
        if source_type in templates:
            return random.choice(templates[source_type])
        
        return f"Analysis for {query}: {random.choice(['positive', 'negative', 'neutral'])} outlook"
    
    def _extract_topic(self, query: str) -> str:
        """Extract main topic from query"""
        # Simple extraction - first few words
        words = query.split()[:3]
        return " ".join(words)
    
    def _determine_finding_type(self, source_type: SourceType) -> str:
        """Determine finding type based on source"""
        type_mapping = {
            SourceType.MARKET_DATA: "fact",
            SourceType.NEWS: "fact",
            SourceType.TECHNICAL: "analysis",
            SourceType.FUNDAMENTAL: "analysis",
            SourceType.SOCIAL_MEDIA: "opinion",
            SourceType.EXPERT_OPINION: "opinion",
            SourceType.ECONOMIC: "fact",
        }
        return type_mapping.get(source_type, "analysis")
    
    def _meets_reliability(
        self,
        source_reliability: SourceReliability,
        min_reliability: SourceReliability
    ) -> bool:
        """Check if source meets minimum reliability"""
        order = [
            SourceReliability.UNKNOWN,
            SourceReliability.LOW,
            SourceReliability.MEDIUM,
            SourceReliability.HIGH,
            SourceReliability.AUTHORITATIVE,
        ]
        return order.index(source_reliability) >= order.index(min_reliability)
    
    def _cross_reference(self, findings: List[ResearchFinding]) -> List[ResearchFinding]:
        """Cross-reference findings to verify"""
        # Group findings by topic
        by_topic: Dict[str, List[ResearchFinding]] = {}
        for finding in findings:
            if finding.topic not in by_topic:
                by_topic[finding.topic] = []
            by_topic[finding.topic].append(finding)
        
        # Cross-reference within topics
        for topic, topic_findings in by_topic.items():
            if len(topic_findings) < 2:
                continue
            
            for i, f1 in enumerate(topic_findings):
                for f2 in topic_findings[i + 1:]:
                    # Check for similar content
                    if self._content_similar(f1.content, f2.content):
                        # Add cross-references
                        for c1 in f1.citations:
                            c1.cross_references.append(f2.finding_id)
                            c1.verified = True
                            c1.verification_method = "cross_reference"
                        for c2 in f2.citations:
                            c2.cross_references.append(f1.finding_id)
                            c2.verified = True
                            c2.verification_method = "cross_reference"
                        
                        f1.supporting_findings.append(f2.finding_id)
                        f2.supporting_findings.append(f1.finding_id)
        
        return findings
    
    def _content_similar(self, content1: str, content2: str) -> bool:
        """Check if two contents are similar"""
        # Simple word overlap check
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        overlap = len(words1 & words2)
        total = len(words1 | words2)
        
        return overlap / total > 0.3 if total > 0 else False
    
    def _resolve_contradictions(
        self,
        findings: List[ResearchFinding],
        contradictions: List[Dict[str, Any]]
    ) -> List[ResearchFinding]:
        """Resolve contradictions in findings"""
        findings_dict = {f.finding_id: f for f in findings}
        
        for contradiction in contradictions:
            f1 = findings_dict.get(contradiction["finding1_id"])
            f2 = findings_dict.get(contradiction["finding2_id"])
            
            if f1 and f2:
                winner = self.synthesizer.resolve_contradiction(f1, f2)
                # Mark loser as contradicted
                loser_id = f2.finding_id if winner == f1 else f1.finding_id
                if loser_id in findings_dict:
                    findings_dict[loser_id].confidence *= 0.5  # Reduce confidence
        
        return list(findings_dict.values())
    
    def get_synthesis(self, query_id: str) -> Dict[str, Any]:
        """Get synthesized results for a query"""
        # Find query
        query = None
        for q in self.completed_queries:
            if q.query_id == query_id:
                query = q
                break
        
        if not query:
            return {"error": "Query not found"}
        
        return self.synthesizer.synthesize(query.findings)
    
    def get_report(self) -> Dict[str, Any]:
        """Get research engine report"""
        return {
            "total_queries": self.total_queries,
            "total_findings": self.total_findings,
            "total_citations": self.total_citations,
            "active_queries": len(self.active_queries),
            "completed_queries": len(self.completed_queries),
            "cached_findings": len(self.finding_cache),
            "registered_sources": len(self.source_registry.sources),
        }


# Factory function
def create_deep_research_engine(
    config: Optional[Dict[str, Any]] = None
) -> DeepResearchEngine:
    """Create deep research engine"""
    return DeepResearchEngine(config)
