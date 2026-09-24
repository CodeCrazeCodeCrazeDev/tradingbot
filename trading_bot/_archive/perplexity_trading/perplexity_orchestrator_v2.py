"""
Perplexity Trading Orchestrator V2 - Ultimate Intelligence System
==================================================================

Master orchestrator integrating all advanced Perplexity systems:
- Deep Research Engine (multi-source synthesis)
- Reasoning Chains (step-by-step logic)
- Knowledge Graph (connected intelligence)
- Task Decomposition (complex query handling)
- Multi-Agent Coordination (specialized agents)

Creates a Perplexity-style AI that can research, reason, and
decide on trading actions with full transparency and citations.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .deep_research_engine import (
    DeepResearchEngine,
    create_deep_research_engine,
    ResearchDepth,
    SourceType,
)
from .reasoning_chains import (
    ReasoningChainEngine,
    create_reasoning_chain_engine,
    ReasoningChain,
    ReasoningType,
)
from .knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphReasoner,
    create_knowledge_graph,
    EntityType,
    RelationType,
)

logger = logging.getLogger(__name__)


class PerplexityMode(Enum):
    """Operating modes"""
    IDLE = "idle"
    RESEARCHING = "researching"
    REASONING = "reasoning"
    SYNTHESIZING = "synthesizing"
    DECIDING = "deciding"
    EXPLAINING = "explaining"


class QueryComplexity(Enum):
    """Complexity levels of queries"""
    SIMPLE = "simple"       # Single-step answer
    MODERATE = "moderate"   # Multi-step reasoning
    COMPLEX = "complex"     # Deep research + reasoning
    EXPERT = "expert"       # Full system engagement


@dataclass
class PerplexityState:
    """Current state of the Perplexity system"""
    mode: PerplexityMode = PerplexityMode.IDLE
    
    # Component states
    research_active: bool = False
    reasoning_active: bool = False
    knowledge_active: bool = False
    
    # Metrics
    total_queries: int = 0
    total_decisions: int = 0
    avg_confidence: float = 0.0
    
    # Activity
    current_query: Optional[str] = None
    started_at: Optional[datetime] = None
    last_query_at: Optional[datetime] = None


@dataclass
class PerplexityConfig:
    """Configuration for Perplexity system"""
    # Research settings
    default_research_depth: ResearchDepth = ResearchDepth.STANDARD
    max_sources: int = 15
    
    # Reasoning settings
    use_tree_of_thoughts: bool = True
    max_reasoning_depth: int = 5
    
    # Knowledge settings
    populate_knowledge: bool = True
    enable_inference: bool = True
    
    # Decision settings
    min_confidence_threshold: float = 0.5
    require_citations: bool = True
    
    # Timeouts
    research_timeout_seconds: float = 60.0
    reasoning_timeout_seconds: float = 30.0


@dataclass
class Citation:
    """A citation for a claim"""
    source: str
    content: str
    reliability: float
    timestamp: datetime


@dataclass
class PerplexityDecision:
    """A decision made by the Perplexity system"""
    decision_id: str
    query: str
    
    # Decision
    action: str
    confidence: float
    
    # Supporting information
    research_summary: Dict[str, Any]
    reasoning_chain: List[str]
    knowledge_context: Dict[str, Any]
    
    # Citations
    citations: List[Citation]
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0
    complexity: QueryComplexity = QueryComplexity.MODERATE
    
    def get_explanation(self) -> str:
        """Get full explanation of decision"""
        lines = [
            f"Query: {self.query}",
            f"Decision: {self.action.upper()} (Confidence: {self.confidence:.1%})",
            "",
            "Reasoning:",
        ]
        
        for i, step in enumerate(self.reasoning_chain, 1):
            lines.append(f"  {i}. {step}")
        
        lines.append("")
        lines.append("Citations:")
        for citation in self.citations[:5]:
            lines.append(f"  - [{citation.source}] {citation.content[:100]}...")
        
        return "\n".join(lines)


class PerplexityOrchestratorV2:
    """
    Perplexity Trading Orchestrator V2
    
    A comprehensive intelligence system that combines:
    - Deep research across multiple sources
    - Step-by-step reasoning with verification
    - Knowledge graph for connected intelligence
    - Full citation and explanation capabilities
    
    Like Perplexity AI, but specialized for trading decisions.
    """
    
    def __init__(self, config: Optional[PerplexityConfig] = None):
        self.config = config or PerplexityConfig()
        
        # State
        self.state = PerplexityState()
        self._running = False
        
        # Components (lazy initialization)
        self._research: Optional[DeepResearchEngine] = None
        self._reasoning: Optional[ReasoningChainEngine] = None
        self._knowledge: Optional[KnowledgeGraph] = None
        self._reasoner: Optional[KnowledgeGraphReasoner] = None
        
        # History
        self.decision_history: List[PerplexityDecision] = []
        self.query_history: List[Dict[str, Any]] = []
        
        # Callbacks
        self.on_decision: Optional[Callable[[PerplexityDecision], None]] = None
        self.on_research_complete: Optional[Callable[[Dict[str, Any]], None]] = None
        
        logger.info("PerplexityOrchestratorV2 initialized")
    
    # ==================== INITIALIZATION ====================
    
    def _init_research(self) -> DeepResearchEngine:
        """Initialize deep research engine"""
        if self._research is None:
            self._research = create_deep_research_engine()
            self.state.research_active = True
            logger.info("Deep Research Engine initialized")
        return self._research
    
    def _init_reasoning(self) -> ReasoningChainEngine:
        """Initialize reasoning chain engine"""
        if self._reasoning is None:
            self._reasoning = create_reasoning_chain_engine()
            self.state.reasoning_active = True
            logger.info("Reasoning Chain Engine initialized")
        return self._reasoning
    
    def _init_knowledge(self) -> Tuple[KnowledgeGraph, KnowledgeGraphReasoner]:
        """Initialize knowledge graph"""
        if self._knowledge is None:
            self._knowledge, self._reasoner = create_knowledge_graph(
                populate=self.config.populate_knowledge
            )
            self.state.knowledge_active = True
            logger.info("Knowledge Graph initialized")
        return self._knowledge, self._reasoner
    
    async def initialize(self) -> None:
        """Initialize all components"""
        self._init_research()
        self._init_reasoning()
        self._init_knowledge()
        
        self._running = True
        self.state.started_at = datetime.utcnow()
        
        logger.info("PerplexityOrchestratorV2 fully initialized")
    
    # ==================== QUERY PROCESSING ====================
    
    def _assess_complexity(self, query: str) -> QueryComplexity:
        """Assess the complexity of a query"""
        query_lower = query.lower()
        
        # Simple queries
        simple_patterns = ["what is", "define", "price of", "current"]
        if any(p in query_lower for p in simple_patterns) and len(query.split()) < 10:
            return QueryComplexity.SIMPLE
        
        # Expert queries
        expert_patterns = ["analyze", "research", "investigate", "comprehensive", "deep dive"]
        if any(p in query_lower for p in expert_patterns):
            return QueryComplexity.EXPERT
        
        # Complex queries
        complex_patterns = ["why", "how", "explain", "compare", "strategy"]
        if any(p in query_lower for p in complex_patterns):
            return QueryComplexity.COMPLEX
        
        return QueryComplexity.MODERATE
    
    async def query(
        self,
        query_text: str,
        context: Optional[Dict[str, Any]] = None,
        force_depth: Optional[ResearchDepth] = None,
    ) -> PerplexityDecision:
        """Process a query through the full Perplexity pipeline"""
        start_time = datetime.utcnow()
        self.state.current_query = query_text
        self.state.total_queries += 1
        self.state.last_query_at = start_time
        
        # Assess complexity
        complexity = self._assess_complexity(query_text)
        
        # Determine research depth
        if force_depth:
            research_depth = force_depth
        elif complexity == QueryComplexity.SIMPLE:
            research_depth = ResearchDepth.QUICK
        elif complexity == QueryComplexity.EXPERT:
            research_depth = ResearchDepth.DEEP
        else:
            research_depth = self.config.default_research_depth
        
        # Initialize components
        research = self._init_research()
        reasoning = self._init_reasoning()
        knowledge, reasoner = self._init_knowledge()
        
        # Step 1: Knowledge Graph Context
        self.state.mode = PerplexityMode.RESEARCHING
        knowledge_context = self._get_knowledge_context(query_text, reasoner)
        
        # Step 2: Deep Research
        research_result = await research.research(
            query_text,
            depth=research_depth,
            focus_areas=self._determine_focus_areas(query_text),
        )
        
        research_summary = research.get_synthesis(research_result.query_id)
        
        if self.on_research_complete:
            self.on_research_complete(research_summary)
        
        # Step 3: Reasoning
        self.state.mode = PerplexityMode.REASONING
        reasoning_chain = await reasoning.reason(
            query_text,
            context={
                "research": research_summary,
                "knowledge": knowledge_context,
                **(context or {}),
            },
            use_tree=self.config.use_tree_of_thoughts,
        )
        
        # Step 4: Synthesize Decision
        self.state.mode = PerplexityMode.SYNTHESIZING
        decision = self._synthesize_decision(
            query_text,
            research_result,
            research_summary,
            reasoning_chain,
            knowledge_context,
            complexity,
        )
        
        # Calculate processing time
        end_time = datetime.utcnow()
        decision.processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Store and callback
        self.decision_history.append(decision)
        self.state.total_decisions += 1
        self._update_avg_confidence(decision.confidence)
        self.state.mode = PerplexityMode.IDLE
        self.state.current_query = None
        
        if self.on_decision:
            self.on_decision(decision)
        
        # Update knowledge graph with new information
        if self.config.enable_inference:
            self._update_knowledge_from_decision(decision)
        
        logger.info(f"Query processed: {decision.action} (confidence: {decision.confidence:.1%})")
        return decision
    
    def _get_knowledge_context(
        self,
        query: str,
        reasoner: KnowledgeGraphReasoner
    ) -> Dict[str, Any]:
        """Get relevant context from knowledge graph"""
        # Answer question using knowledge graph
        answer = reasoner.answer_question(query)
        
        # Find related entities
        related_entities = []
        for entity in answer.get("entities", []):
            related_entities.append(entity)
        
        return {
            "answer": answer.get("answer", ""),
            "confidence": answer.get("confidence", 0),
            "entities": related_entities,
            "related_info": answer.get("related_info", []),
        }
    
    def _determine_focus_areas(self, query: str) -> List[SourceType]:
        """Determine which source types to focus on"""
        query_lower = query.lower()
        focus_areas = []
        
        # Technical analysis
        if any(w in query_lower for w in ["chart", "pattern", "indicator", "technical", "rsi", "macd"]):
            focus_areas.append(SourceType.TECHNICAL)
        
        # Fundamental analysis
        if any(w in query_lower for w in ["earnings", "revenue", "fundamental", "valuation", "pe"]):
            focus_areas.append(SourceType.FUNDAMENTAL)
        
        # News
        if any(w in query_lower for w in ["news", "event", "announcement", "report"]):
            focus_areas.append(SourceType.NEWS)
        
        # Sentiment
        if any(w in query_lower for w in ["sentiment", "social", "twitter", "reddit"]):
            focus_areas.append(SourceType.SOCIAL_MEDIA)
        
        # Economic
        if any(w in query_lower for w in ["economic", "fed", "interest", "inflation", "gdp"]):
            focus_areas.append(SourceType.ECONOMIC)
        
        # Default to broad coverage
        if not focus_areas:
            focus_areas = [
                SourceType.MARKET_DATA,
                SourceType.NEWS,
                SourceType.TECHNICAL,
            ]
        
        return focus_areas
    
    def _synthesize_decision(
        self,
        query: str,
        research_result,
        research_summary: Dict[str, Any],
        reasoning_chain: ReasoningChain,
        knowledge_context: Dict[str, Any],
        complexity: QueryComplexity,
    ) -> PerplexityDecision:
        """Synthesize all information into a decision"""
        # Extract action from reasoning conclusion
        action = self._extract_action(reasoning_chain.conclusion or "")
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            research_summary,
            reasoning_chain,
            knowledge_context,
        )
        
        # Build citations
        citations = self._build_citations(research_result)
        
        # Build reasoning chain explanation
        reasoning_steps = [
            step.description for step in reasoning_chain.steps
        ]
        
        decision = PerplexityDecision(
            decision_id=f"decision_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            query=query,
            action=action,
            confidence=confidence,
            research_summary=research_summary,
            reasoning_chain=reasoning_steps,
            knowledge_context=knowledge_context,
            citations=citations,
            complexity=complexity,
        )
        
        return decision
    
    def _extract_action(self, conclusion: str) -> str:
        """Extract trading action from conclusion"""
        conclusion_lower = conclusion.lower()
        
        # Look for explicit actions
        if any(w in conclusion_lower for w in ["buy", "long", "bullish", "positive"]):
            return "buy"
        elif any(w in conclusion_lower for w in ["sell", "short", "bearish", "negative"]):
            return "sell"
        else:
            return "hold"
    
    def _calculate_confidence(
        self,
        research_summary: Dict[str, Any],
        reasoning_chain: ReasoningChain,
        knowledge_context: Dict[str, Any],
    ) -> float:
        """Calculate overall confidence"""
        confidences = []
        
        # Research confidence
        research_conf = research_summary.get("overall_confidence", 0.5)
        confidences.append(research_conf)
        
        # Reasoning confidence
        reasoning_conf = reasoning_chain.final_confidence
        confidences.append(reasoning_conf)
        
        # Knowledge confidence
        knowledge_conf = knowledge_context.get("confidence", 0.5)
        confidences.append(knowledge_conf)
        
        # Weighted average
        weights = [0.4, 0.4, 0.2]  # Research, Reasoning, Knowledge
        weighted_conf = sum(c * w for c, w in zip(confidences, weights))
        
        return min(1.0, max(0.0, weighted_conf))
    
    def _build_citations(self, research_result) -> List[Citation]:
        """Build citations from research findings"""
        citations = []
        
        for finding in research_result.findings:
            for cite in finding.citations:
                citations.append(Citation(
                    source=cite.source_name,
                    content=finding.content,
                    reliability=cite.get_reliability_score(),
                    timestamp=cite.timestamp,
                ))
        
        # Sort by reliability
        citations.sort(key=lambda c: c.reliability, reverse=True)
        
        return citations[:10]  # Top 10 citations
    
    def _update_avg_confidence(self, new_confidence: float) -> None:
        """Update running average confidence"""
        n = self.state.total_decisions
        old_avg = self.state.avg_confidence
        self.state.avg_confidence = ((n - 1) * old_avg + new_confidence) / n
    
    def _update_knowledge_from_decision(self, decision: PerplexityDecision) -> None:
        """Update knowledge graph with new information"""
        if not self._knowledge:
            return
        
        # Add decision as an event
        self._knowledge.add_entity(
            EntityType.EVENT,
            f"Decision_{decision.decision_id[:8]}",
            properties={
                "action": decision.action,
                "confidence": decision.confidence,
                "query": decision.query,
            }
        )
        
        # Run inference
        if self.config.enable_inference:
            self._knowledge.infer_relations()
    
    # ==================== SPECIALIZED QUERIES ====================
    
    async def analyze_asset(self, symbol: str) -> PerplexityDecision:
        """Comprehensive analysis of an asset"""
        query = f"Provide comprehensive analysis of {symbol} including technical, fundamental, and sentiment factors. What is the trading recommendation?"
        return await self.query(query, force_depth=ResearchDepth.DEEP)
    
    async def explain_concept(self, concept: str) -> Dict[str, Any]:
        """Explain a trading concept"""
        self.state.mode = PerplexityMode.EXPLAINING
        
        knowledge, reasoner = self._init_knowledge()
        
        # Get from knowledge graph
        answer = reasoner.answer_question(f"What is {concept}?")
        
        # Get related concepts
        entity = knowledge.get_entity_by_name(concept)
        related = []
        if entity:
            neighbors = knowledge.get_neighbors(entity.entity_id)
            related = [
                {"name": n.name, "relation": r.relation_type.value}
                for n, r in neighbors[:5]
            ]
        
        self.state.mode = PerplexityMode.IDLE
        
        return {
            "concept": concept,
            "explanation": answer.get("answer", "Concept not found in knowledge base"),
            "confidence": answer.get("confidence", 0),
            "related_concepts": related,
        }
    
    async def compare_assets(self, asset1: str, asset2: str) -> Dict[str, Any]:
        """Compare two assets"""
        query = f"Compare {asset1} and {asset2} for trading. Which is better and why?"
        decision = await self.query(query, force_depth=ResearchDepth.STANDARD)
        
        return {
            "asset1": asset1,
            "asset2": asset2,
            "recommendation": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning_chain,
            "citations": [
                {"source": c.source, "content": c.content[:100]}
                for c in decision.citations[:5]
            ],
        }
    
    # ==================== REPORTING ====================
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive system report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "state": {
                "mode": self.state.mode.value,
                "running": self._running,
                "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
            },
            "metrics": {
                "total_queries": self.state.total_queries,
                "total_decisions": self.state.total_decisions,
                "avg_confidence": self.state.avg_confidence,
            },
            "components": {
                "research_active": self.state.research_active,
                "reasoning_active": self.state.reasoning_active,
                "knowledge_active": self.state.knowledge_active,
            },
        }
        
        # Add component reports
        if self._research:
            report["research"] = self._research.get_report()
        
        if self._reasoning:
            report["reasoning"] = self._reasoning.get_report()
        
        if self._knowledge:
            report["knowledge"] = self._knowledge.get_statistics()
        
        return report
    
    def human_override(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Human override - ALWAYS works"""
        params = params or {}
        result = {"action": action, "success": True, "message": ""}
        
        if action == "FORCE_ACTION":
            forced_action = params.get("action", "hold")
            result["message"] = f"Action forced to {forced_action}"
        
        elif action == "ADD_KNOWLEDGE":
            entity_type = EntityType(params.get("type", "concept"))
            name = params.get("name", "Unknown")
            if self._knowledge:
                self._knowledge.add_entity(entity_type, name, params.get("properties", {}))
            result["message"] = f"Added {name} to knowledge graph"
        
        elif action == "GET_STATUS":
            result["status"] = self.get_comprehensive_report()
            result["message"] = "Status retrieved"
        
        elif action == "CLEAR_HISTORY":
            self.decision_history.clear()
            self.query_history.clear()
            result["message"] = "History cleared"
        
        else:
            result["success"] = False
            result["message"] = f"Unknown action: {action}"
        
        logger.info(f"Human override: {action} - {result['message']}")
        return result


# Factory functions
def create_perplexity_v2(config: Optional[PerplexityConfig] = None) -> PerplexityOrchestratorV2:
    """Create Perplexity orchestrator V2"""
    return PerplexityOrchestratorV2(config)


async def quick_start_perplexity_v2(config: Optional[PerplexityConfig] = None) -> PerplexityOrchestratorV2:
    """Quick start Perplexity system"""
    orchestrator = create_perplexity_v2(config)
    await orchestrator.initialize()
    return orchestrator
