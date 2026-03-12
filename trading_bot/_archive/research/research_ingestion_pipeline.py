"""
Research Paper / GitHub / Literature Ingestion Pipeline

9-Stage Pipeline:
1. Paper/GitHub Repos Ingestion
2. Relevance Filtering
3. Claim Extraction
4. Feasibility Scoring
5. Sandbox Implementation
6. Backtest & Stress Test
7. Capital Impact Estimation
8. Human / Policy Gate
9. Production Deployment

Monitors new literature, maps ideas to AlphaAlgo constraints,
proposes bounded experiments, ranks ideas by ROI, and generates test harnesses.
"""

import asyncio
import hashlib
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ============================================================================
# PIPELINE STAGE DEFINITIONS
# ============================================================================

class PipelineStage(Enum):
    """The 9 stages of the research ingestion pipeline."""
    INGESTION = 1
    RELEVANCE_FILTERING = 2
    CLAIM_EXTRACTION = 3
    FEASIBILITY_SCORING = 4
    SANDBOX_IMPLEMENTATION = 5
    BACKTEST_STRESS_TEST = 6
    CAPITAL_IMPACT_ESTIMATION = 7
    HUMAN_POLICY_GATE = 8
    PRODUCTION_DEPLOYMENT = 9


class SourceType(Enum):
    """Types of research sources."""
    ARXIV_PAPER = auto()
    JOURNAL_PAPER = auto()
    CONFERENCE_PAPER = auto()
    GITHUB_REPO = auto()
    BLOG_POST = auto()
    BOOK_CHAPTER = auto()
    PATENT = auto()
    PREPRINT = auto()
    THESIS = auto()
    TECHNICAL_REPORT = auto()


class RelevanceCategory(Enum):
    """Categories for relevance classification."""
    HIGHLY_RELEVANT = auto()
    RELEVANT = auto()
    MARGINALLY_RELEVANT = auto()
    NOT_RELEVANT = auto()


class FeasibilityLevel(Enum):
    """Feasibility levels for implementation."""
    TRIVIAL = auto()       # Can implement in hours
    EASY = auto()          # Can implement in days
    MODERATE = auto()      # Requires weeks
    HARD = auto()          # Requires months
    INFEASIBLE = auto()    # Cannot implement with current resources


@dataclass
class ResearchSource:
    """A research source (paper, repo, etc.)."""
    id: str
    source_type: SourceType
    title: str
    authors: List[str]
    url: str
    abstract: str
    full_text: str = ""
    publication_date: Optional[datetime] = None
    venue: str = ""
    citations: int = 0
    tags: List[str] = field(default_factory=list)
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    current_stage: PipelineStage = PipelineStage.INGESTION
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedClaim:
    """A claim extracted from a research source."""
    id: str
    source_id: str
    claim_text: str
    claim_type: str  # 'performance', 'method', 'finding', 'hypothesis'
    evidence_strength: float  # 0-1
    quantitative_results: Dict[str, float] = field(default_factory=dict)
    conditions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    alphaalgo_mapping: Optional[str] = None
    feasibility: Optional[FeasibilityLevel] = None


@dataclass
class BoundedExperiment:
    """A bounded experiment proposed from research insights."""
    id: str
    source_ids: List[str]
    claim_ids: List[str]
    name: str
    hypothesis: str
    methodology: str
    parameters: Dict[str, Any]
    success_criteria: Dict[str, float]
    risk_budget: float  # Max capital at risk
    time_budget_days: int
    compute_budget_hours: float
    estimated_roi: float
    priority_score: float
    status: str = "proposed"  # proposed, approved, running, completed, rejected
    results: Optional[Dict[str, Any]] = None
    test_harness_code: str = ""


@dataclass
class PipelineResult:
    """Result of processing a source through the pipeline."""
    source_id: str
    stage: PipelineStage
    passed: bool
    score: float
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""


# ============================================================================
# RELEVANCE KEYWORDS AND PATTERNS
# ============================================================================

TRADING_KEYWORDS = {
    'high_relevance': [
        'algorithmic trading', 'quantitative trading', 'market microstructure',
        'order execution', 'portfolio optimization', 'risk management',
        'alpha generation', 'factor investing', 'momentum', 'mean reversion',
        'statistical arbitrage', 'pairs trading', 'market making',
        'high frequency trading', 'optimal execution', 'transaction costs',
        'volatility forecasting', 'regime detection', 'drawdown',
        'sharpe ratio', 'kelly criterion', 'position sizing',
        'reinforcement learning trading', 'deep learning finance',
        'time series forecasting', 'financial machine learning',
        'backtesting', 'walk-forward', 'cross-validation finance',
    ],
    'medium_relevance': [
        'time series', 'anomaly detection', 'change point detection',
        'online learning', 'meta-learning', 'transfer learning',
        'ensemble methods', 'bayesian optimization', 'genetic algorithm',
        'neural architecture search', 'attention mechanism',
        'transformer', 'lstm', 'gru', 'recurrent neural network',
        'reinforcement learning', 'multi-agent', 'game theory',
        'optimization', 'stochastic', 'monte carlo',
        'signal processing', 'feature engineering', 'feature selection',
        'dimensionality reduction', 'clustering', 'classification',
        'regression', 'prediction', 'forecasting',
        'natural language processing', 'sentiment analysis',
    ],
    'low_relevance': [
        'machine learning', 'deep learning', 'neural network',
        'data science', 'statistics', 'probability',
        'optimization algorithm', 'evolutionary computation',
    ],
}

ALPHAALGO_CONSTRAINT_MAP = {
    'max_position_size': 0.10,
    'max_daily_loss': 0.05,
    'max_drawdown': 0.25,
    'max_leverage': 5.0,
    'min_sharpe_for_live': 1.0,
    'min_backtest_months': 6,
    'min_paper_trade_days': 30,
    'max_correlation_between_strategies': 0.7,
    'min_trades_for_significance': 100,
    'max_model_complexity_params': 1000000,
    'max_inference_latency_ms': 100,
    'supported_assets': ['forex', 'crypto', 'stocks', 'commodities'],
    'supported_timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
}


# ============================================================================
# PIPELINE STAGES
# ============================================================================

class Stage1_Ingestion:
    """Stage 1: Paper/GitHub Repos Ingestion"""

    def __init__(self):
        self.sources: Dict[str, ResearchSource] = {}
        self.ingestion_queue: List[str] = []

    def ingest_arxiv_paper(self, paper_data: Dict[str, Any]) -> ResearchSource:
        """Ingest a paper from arXiv."""
        source_id = f"arxiv-{paper_data.get('arxiv_id', hashlib.md5(paper_data.get('title', '').encode()).hexdigest()[:12])}"

        source = ResearchSource(
            id=source_id,
            source_type=SourceType.ARXIV_PAPER,
            title=paper_data.get('title', ''),
            authors=paper_data.get('authors', []),
            url=paper_data.get('url', f"https://arxiv.org/abs/{paper_data.get('arxiv_id', '')}"),
            abstract=paper_data.get('abstract', ''),
            full_text=paper_data.get('full_text', ''),
            publication_date=paper_data.get('published'),
            venue='arXiv',
            citations=paper_data.get('citations', 0),
            tags=paper_data.get('categories', []),
        )

        self.sources[source_id] = source
        logger.info(f"Ingested arXiv paper: {source.title[:80]}")
        return source

    def ingest_github_repo(self, repo_data: Dict[str, Any]) -> ResearchSource:
        """Ingest a GitHub repository."""
        repo_name = repo_data.get('full_name', repo_data.get('name', 'unknown'))
        source_id = f"github-{hashlib.md5(repo_name.encode()).hexdigest()[:12]}"

        source = ResearchSource(
            id=source_id,
            source_type=SourceType.GITHUB_REPO,
            title=repo_data.get('name', ''),
            authors=[repo_data.get('owner', 'unknown')],
            url=repo_data.get('html_url', f"https://github.com/{repo_name}"),
            abstract=repo_data.get('description', ''),
            full_text=repo_data.get('readme', ''),
            tags=repo_data.get('topics', []),
            metadata={
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'language': repo_data.get('language', ''),
                'last_updated': repo_data.get('updated_at', ''),
            }
        )

        self.sources[source_id] = source
        logger.info(f"Ingested GitHub repo: {repo_name}")
        return source

    def ingest_generic_paper(self, paper_data: Dict[str, Any]) -> ResearchSource:
        """Ingest a generic research paper."""
        title = paper_data.get('title', '')
        source_id = f"paper-{hashlib.md5(title.encode()).hexdigest()[:12]}"

        source = ResearchSource(
            id=source_id,
            source_type=SourceType.JOURNAL_PAPER,
            title=title,
            authors=paper_data.get('authors', []),
            url=paper_data.get('url', ''),
            abstract=paper_data.get('abstract', ''),
            full_text=paper_data.get('full_text', ''),
            publication_date=paper_data.get('published'),
            venue=paper_data.get('venue', ''),
            citations=paper_data.get('citations', 0),
            tags=paper_data.get('tags', []),
        )

        self.sources[source_id] = source
        logger.info(f"Ingested paper: {title[:80]}")
        return source


class Stage2_RelevanceFilter:
    """Stage 2: Relevance Filtering"""

    def __init__(self):
        self.filter_results: Dict[str, PipelineResult] = {}

    def filter(self, source: ResearchSource) -> PipelineResult:
        """Filter source by relevance to trading/AlphaAlgo."""
        text = f"{source.title} {source.abstract} {' '.join(source.tags)}".lower()

        # Score based on keyword matches
        high_matches = sum(1 for kw in TRADING_KEYWORDS['high_relevance'] if kw in text)
        medium_matches = sum(1 for kw in TRADING_KEYWORDS['medium_relevance'] if kw in text)
        low_matches = sum(1 for kw in TRADING_KEYWORDS['low_relevance'] if kw in text)

        # Weighted score
        score = (high_matches * 3.0 + medium_matches * 1.5 + low_matches * 0.5)
        max_possible = len(TRADING_KEYWORDS['high_relevance']) * 3.0
        normalized_score = min(score / max(max_possible * 0.1, 1), 1.0)

        # Determine category
        if high_matches >= 3 or normalized_score > 0.7:
            category = RelevanceCategory.HIGHLY_RELEVANT
            passed = True
        elif high_matches >= 1 or medium_matches >= 3 or normalized_score > 0.3:
            category = RelevanceCategory.RELEVANT
            passed = True
        elif medium_matches >= 1 or low_matches >= 2:
            category = RelevanceCategory.MARGINALLY_RELEVANT
            passed = True
        else:
            category = RelevanceCategory.NOT_RELEVANT
            passed = False

        # Boost for GitHub repos with high stars
        if source.source_type == SourceType.GITHUB_REPO:
            stars = source.metadata.get('stars', 0)
            if stars > 1000:
                normalized_score = min(normalized_score + 0.2, 1.0)
                if not passed:
                    passed = True
                    category = RelevanceCategory.MARGINALLY_RELEVANT

        # Boost for highly cited papers
        if source.citations > 100:
            normalized_score = min(normalized_score + 0.15, 1.0)

        result = PipelineResult(
            source_id=source.id,
            stage=PipelineStage.RELEVANCE_FILTERING,
            passed=passed,
            score=normalized_score,
            details={
                'category': category.name,
                'high_keyword_matches': high_matches,
                'medium_keyword_matches': medium_matches,
                'low_keyword_matches': low_matches,
                'matched_keywords': [
                    kw for kw in TRADING_KEYWORDS['high_relevance'] if kw in text
                ][:10],
            }
        )

        self.filter_results[source.id] = result
        return result


class Stage3_ClaimExtraction:
    """Stage 3: Claim Extraction"""

    def __init__(self):
        self.claims: Dict[str, List[ExtractedClaim]] = {}
        self._claim_counter = 0

    def extract_claims(self, source: ResearchSource) -> List[ExtractedClaim]:
        """Extract testable claims from a research source."""
        claims = []
        text = f"{source.abstract} {source.full_text}"

        # Extract performance claims
        perf_claims = self._extract_performance_claims(source.id, text)
        claims.extend(perf_claims)

        # Extract method claims
        method_claims = self._extract_method_claims(source.id, text)
        claims.extend(method_claims)

        # Extract finding claims
        finding_claims = self._extract_finding_claims(source.id, text)
        claims.extend(finding_claims)

        # Map claims to AlphaAlgo constraints
        for claim in claims:
            claim.alphaalgo_mapping = self._map_to_alphaalgo(claim)

        self.claims[source.id] = claims
        return claims

    def _extract_performance_claims(self, source_id: str, text: str) -> List[ExtractedClaim]:
        """Extract quantitative performance claims."""
        claims = []

        # Pattern: "achieves X% return/accuracy/improvement"
        patterns = [
            r'achiev\w*\s+(\d+\.?\d*)\s*%?\s*(return|accuracy|improvement|sharpe|alpha)',
            r'(\d+\.?\d*)\s*%?\s*(return|accuracy|improvement|outperformance)',
            r'sharpe\s*(?:ratio)?\s*(?:of)?\s*(\d+\.?\d*)',
            r'(?:reduces?|decreases?)\s+(?:drawdown|risk|loss)\s+(?:by)?\s*(\d+\.?\d*)\s*%',
            r'(?:improves?|increases?)\s+(?:return|performance|profit)\s+(?:by)?\s*(\d+\.?\d*)\s*%',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                self._claim_counter += 1
                claim_text = text[max(0, match.start()-100):match.end()+100].strip()

                claims.append(ExtractedClaim(
                    id=f"CLAIM-{self._claim_counter:06d}",
                    source_id=source_id,
                    claim_text=claim_text[:500],
                    claim_type='performance',
                    evidence_strength=0.5,
                    quantitative_results={'value': float(match.group(1)) if match.group(1) else 0},
                ))

        return claims[:10]  # Limit to top 10 performance claims

    def _extract_method_claims(self, source_id: str, text: str) -> List[ExtractedClaim]:
        """Extract method/technique claims."""
        claims = []

        method_patterns = [
            r'(?:we\s+)?propos\w+\s+(?:a\s+)?(?:novel\s+)?(\w+(?:\s+\w+){1,5})\s+(?:method|approach|algorithm|technique|framework|model)',
            r'(?:our\s+)?(?:method|approach|algorithm)\s+(?:called|named|termed)\s+(\w+(?:\s+\w+){0,3})',
            r'(?:introduce|present)\s+(\w+(?:\s+\w+){1,5})\s+(?:for|to)\s+(?:trading|portfolio|risk|prediction)',
        ]

        for pattern in method_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                self._claim_counter += 1
                claim_text = text[max(0, match.start()-50):match.end()+200].strip()

                claims.append(ExtractedClaim(
                    id=f"CLAIM-{self._claim_counter:06d}",
                    source_id=source_id,
                    claim_text=claim_text[:500],
                    claim_type='method',
                    evidence_strength=0.4,
                ))

        return claims[:5]

    def _extract_finding_claims(self, source_id: str, text: str) -> List[ExtractedClaim]:
        """Extract research findings."""
        claims = []

        finding_patterns = [
            r'(?:we\s+)?(?:find|show|demonstrate|observe|discover)\s+that\s+(.{20,200}?)(?:\.|$)',
            r'(?:results?\s+)?(?:indicate|suggest|confirm|reveal)\s+that\s+(.{20,200}?)(?:\.|$)',
            r'(?:our\s+)?(?:analysis|experiment|study)\s+(?:shows?|reveals?|demonstrates?)\s+(.{20,200}?)(?:\.|$)',
        ]

        for pattern in finding_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                self._claim_counter += 1

                claims.append(ExtractedClaim(
                    id=f"CLAIM-{self._claim_counter:06d}",
                    source_id=source_id,
                    claim_text=match.group(1).strip()[:500],
                    claim_type='finding',
                    evidence_strength=0.6,
                ))

        return claims[:5]

    def _map_to_alphaalgo(self, claim: ExtractedClaim) -> str:
        """Map a claim to AlphaAlgo constraint categories."""
        text = claim.claim_text.lower()

        mappings = {
            'position_sizing': ['position size', 'kelly', 'bet size', 'allocation'],
            'risk_management': ['risk', 'drawdown', 'stop loss', 'var', 'cvar'],
            'signal_generation': ['signal', 'alpha', 'factor', 'indicator', 'prediction'],
            'execution': ['execution', 'slippage', 'market impact', 'order'],
            'portfolio': ['portfolio', 'diversification', 'correlation', 'allocation'],
            'regime_detection': ['regime', 'market state', 'volatility clustering'],
            'feature_engineering': ['feature', 'representation', 'embedding'],
            'model_architecture': ['model', 'network', 'architecture', 'transformer', 'lstm'],
        }

        for category, keywords in mappings.items():
            if any(kw in text for kw in keywords):
                return category

        return 'general'


class Stage4_FeasibilityScoring:
    """Stage 4: Feasibility Scoring"""

    def score(self, claim: ExtractedClaim, source: ResearchSource) -> PipelineResult:
        """Score the feasibility of implementing a claim."""
        scores = {}

        # Data availability (do we have the required data?)
        scores['data_availability'] = self._score_data_availability(claim)

        # Compute requirements
        scores['compute_feasibility'] = self._score_compute_requirements(claim)

        # Implementation complexity
        scores['implementation_complexity'] = self._score_implementation_complexity(claim, source)

        # AlphaAlgo constraint compatibility
        scores['constraint_compatibility'] = self._score_constraint_compatibility(claim)

        # Evidence quality
        scores['evidence_quality'] = claim.evidence_strength

        # Overall feasibility score
        weights = {
            'data_availability': 0.25,
            'compute_feasibility': 0.15,
            'implementation_complexity': 0.25,
            'constraint_compatibility': 0.20,
            'evidence_quality': 0.15,
        }

        overall = sum(scores[k] * weights[k] for k in weights)

        # Determine feasibility level
        if overall > 0.8:
            level = FeasibilityLevel.TRIVIAL
        elif overall > 0.6:
            level = FeasibilityLevel.EASY
        elif overall > 0.4:
            level = FeasibilityLevel.MODERATE
        elif overall > 0.2:
            level = FeasibilityLevel.HARD
        else:
            level = FeasibilityLevel.INFEASIBLE

        claim.feasibility = level

        return PipelineResult(
            source_id=claim.source_id,
            stage=PipelineStage.FEASIBILITY_SCORING,
            passed=overall > 0.3,
            score=overall,
            details={
                'sub_scores': scores,
                'feasibility_level': level.name,
                'claim_id': claim.id,
            }
        )

    def _score_data_availability(self, claim: ExtractedClaim) -> float:
        """Score data availability for implementing the claim."""
        text = claim.claim_text.lower()

        # Check if claim requires exotic data
        exotic_data = ['satellite', 'credit card', 'social media', 'web scraping', 'alternative data']
        if any(d in text for d in exotic_data):
            return 0.3

        # Standard market data
        standard_data = ['price', 'volume', 'ohlc', 'tick', 'order book', 'level 2']
        if any(d in text for d in standard_data):
            return 0.9

        return 0.6

    def _score_compute_requirements(self, claim: ExtractedClaim) -> float:
        """Score compute feasibility."""
        text = claim.claim_text.lower()

        heavy_compute = ['gpu', 'distributed', 'cluster', 'large-scale', 'billion parameter']
        if any(c in text for c in heavy_compute):
            return 0.2

        moderate_compute = ['deep learning', 'neural network', 'training', 'fine-tune']
        if any(c in text for c in moderate_compute):
            return 0.5

        return 0.8

    def _score_implementation_complexity(self, claim: ExtractedClaim, source: ResearchSource) -> float:
        """Score implementation complexity."""
        # GitHub repos are easier to implement (code available)
        if source.source_type == SourceType.GITHUB_REPO:
            return 0.8

        # Methods with clear algorithms
        if claim.claim_type == 'method':
            return 0.5

        # Performance claims need verification
        if claim.claim_type == 'performance':
            return 0.6

        return 0.5

    def _score_constraint_compatibility(self, claim: ExtractedClaim) -> float:
        """Score compatibility with AlphaAlgo constraints."""
        mapping = claim.alphaalgo_mapping or 'general'

        # Direct mappings to existing systems score higher
        direct_mappings = ['signal_generation', 'risk_management', 'execution', 'regime_detection']
        if mapping in direct_mappings:
            return 0.9

        indirect_mappings = ['portfolio', 'feature_engineering', 'position_sizing']
        if mapping in indirect_mappings:
            return 0.7

        return 0.5


class Stage5_SandboxImplementation:
    """Stage 5: Sandbox Implementation"""

    def __init__(self):
        self.sandbox_experiments: Dict[str, BoundedExperiment] = {}
        self._experiment_counter = 0

    def create_experiment(
        self,
        claims: List[ExtractedClaim],
        source: ResearchSource,
        feasibility_score: float
    ) -> BoundedExperiment:
        """Create a bounded experiment from claims."""
        self._experiment_counter += 1

        # Generate test harness code
        test_harness = self._generate_test_harness(claims, source)

        experiment = BoundedExperiment(
            id=f"EXP-{self._experiment_counter:06d}",
            source_ids=[source.id],
            claim_ids=[c.id for c in claims],
            name=f"Test: {source.title[:60]}",
            hypothesis=claims[0].claim_text[:200] if claims else "No specific hypothesis",
            methodology=self._generate_methodology(claims, source),
            parameters=self._extract_parameters(claims),
            success_criteria={
                'min_sharpe': ALPHAALGO_CONSTRAINT_MAP['min_sharpe_for_live'],
                'max_drawdown': ALPHAALGO_CONSTRAINT_MAP['max_drawdown'],
                'min_trades': ALPHAALGO_CONSTRAINT_MAP['min_trades_for_significance'],
                'improvement_over_baseline': 0.05,
            },
            risk_budget=0.01,  # 1% of capital max
            time_budget_days=14,
            compute_budget_hours=24,
            estimated_roi=feasibility_score * 0.1,
            priority_score=feasibility_score,
            test_harness_code=test_harness,
        )

        self.sandbox_experiments[experiment.id] = experiment
        return experiment

    def _generate_test_harness(self, claims: List[ExtractedClaim], source: ResearchSource) -> str:
        """Generate a test harness for the experiment."""
        claim_descriptions = "\n".join(f"    # Claim: {c.claim_text[:100]}" for c in claims[:3])
        mapping = claims[0].alphaalgo_mapping if claims else 'general'

        return f'''"""
Auto-generated test harness for: {source.title[:80]}
Source: {source.url}
Generated: {datetime.utcnow().isoformat()}
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Claims being tested:
{claim_descriptions}

class ExperimentTestHarness:
    """Test harness for experiment based on {source.title[:60]}"""

    def __init__(self, config=None):
        self.config = config or {{}}
        self.results = {{}}
        self.mapping = "{mapping}"

    def setup(self, market_data: pd.DataFrame):
        """Setup the experiment with market data."""
        self.data = market_data
        self.train_data = market_data.iloc[:int(len(market_data)*0.7)]
        self.test_data = market_data.iloc[int(len(market_data)*0.7):]

    def run_baseline(self) -> dict:
        """Run baseline strategy for comparison."""
        # Simple buy-and-hold baseline
        returns = self.test_data["close"].pct_change().dropna()
        return {{
            "sharpe": float(returns.mean() / max(returns.std(), 1e-8) * np.sqrt(252)),
            "total_return": float(returns.sum()),
            "max_drawdown": float((returns.cumsum() - returns.cumsum().cummax()).min()),
            "trades": 1,
        }}

    def run_experiment(self) -> dict:
        """Run the experimental strategy."""
        # TODO: Implement the strategy from the research paper
        # This is a placeholder - actual implementation depends on the claim
        returns = self.test_data["close"].pct_change().dropna()
        return {{
            "sharpe": 0.0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "trades": 0,
            "status": "needs_implementation",
        }}

    def evaluate(self) -> dict:
        """Compare experiment vs baseline."""
        baseline = self.run_baseline()
        experiment = self.run_experiment()

        return {{
            "baseline": baseline,
            "experiment": experiment,
            "improvement": {{
                "sharpe_delta": experiment.get("sharpe", 0) - baseline.get("sharpe", 0),
                "return_delta": experiment.get("total_return", 0) - baseline.get("total_return", 0),
                "drawdown_delta": experiment.get("max_drawdown", 0) - baseline.get("max_drawdown", 0),
            }},
            "passed_criteria": {{
                "min_sharpe": experiment.get("sharpe", 0) >= {ALPHAALGO_CONSTRAINT_MAP["min_sharpe_for_live"]},
                "max_drawdown": abs(experiment.get("max_drawdown", 1)) <= {ALPHAALGO_CONSTRAINT_MAP["max_drawdown"]},
                "min_trades": experiment.get("trades", 0) >= {ALPHAALGO_CONSTRAINT_MAP["min_trades_for_significance"]},
            }},
        }}


if __name__ == "__main__":
    harness = ExperimentTestHarness()
    # Load your market data here
    # harness.setup(market_data)
    # results = harness.evaluate()
    # print(results)
'''

    def _generate_methodology(self, claims: List[ExtractedClaim], source: ResearchSource) -> str:
        """Generate methodology description."""
        steps = [
            "1. Load historical market data (min 6 months)",
            "2. Split into train (70%) and test (30%) sets",
            "3. Implement the proposed method from the paper",
            "4. Train on training set",
            "5. Evaluate on test set using walk-forward validation",
            "6. Compare against baseline (buy-and-hold + existing strategy)",
            "7. Run stress tests across different market regimes",
            "8. Calculate risk-adjusted metrics (Sharpe, Sortino, max DD)",
        ]
        return "\n".join(steps)

    def _extract_parameters(self, claims: List[ExtractedClaim]) -> Dict[str, Any]:
        """Extract tunable parameters from claims."""
        params = {}
        for claim in claims:
            params.update(claim.quantitative_results)
        return params


class Stage6_BacktestStressTest:
    """Stage 6: Backtest & Stress Test"""

    def evaluate_experiment(self, experiment: BoundedExperiment) -> PipelineResult:
        """Evaluate an experiment through backtesting and stress testing."""
        results = {
            'backtest': self._run_backtest(experiment),
            'stress_test': self._run_stress_tests(experiment),
            'regime_analysis': self._run_regime_analysis(experiment),
        }

        # Overall score
        backtest_score = results['backtest'].get('score', 0)
        stress_score = results['stress_test'].get('score', 0)
        regime_score = results['regime_analysis'].get('score', 0)

        overall = backtest_score * 0.4 + stress_score * 0.35 + regime_score * 0.25
        passed = overall > 0.5 and backtest_score > 0.4

        return PipelineResult(
            source_id=experiment.source_ids[0] if experiment.source_ids else '',
            stage=PipelineStage.BACKTEST_STRESS_TEST,
            passed=passed,
            score=overall,
            details=results,
            notes=f"Backtest: {backtest_score:.2f}, Stress: {stress_score:.2f}, Regime: {regime_score:.2f}"
        )

    def _run_backtest(self, experiment: BoundedExperiment) -> Dict[str, Any]:
        """Run backtest on historical data."""
        # Placeholder - actual backtesting would use the test harness
        return {
            'score': 0.0,
            'sharpe_ratio': 0.0,
            'total_return': 0.0,
            'max_drawdown': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'status': 'needs_data',
        }

    def _run_stress_tests(self, experiment: BoundedExperiment) -> Dict[str, Any]:
        """Run stress tests across extreme scenarios."""
        scenarios = [
            'flash_crash', 'high_volatility', 'low_liquidity',
            'trend_reversal', 'gap_opening', 'news_shock',
        ]
        return {
            'score': 0.0,
            'scenarios_tested': scenarios,
            'scenarios_passed': [],
            'status': 'needs_implementation',
        }

    def _run_regime_analysis(self, experiment: BoundedExperiment) -> Dict[str, Any]:
        """Test across different market regimes."""
        regimes = ['trending_up', 'trending_down', 'ranging', 'volatile', 'calm']
        return {
            'score': 0.0,
            'regimes_tested': regimes,
            'regime_results': {},
            'status': 'needs_implementation',
        }


class Stage7_CapitalImpactEstimation:
    """Stage 7: Capital Impact Estimation"""

    def estimate(self, experiment: BoundedExperiment, backtest_result: PipelineResult) -> PipelineResult:
        """Estimate the capital impact of deploying this strategy."""
        backtest_details = backtest_result.details.get('backtest', {})

        sharpe = backtest_details.get('sharpe_ratio', 0)
        total_return = backtest_details.get('total_return', 0)
        max_dd = backtest_details.get('max_drawdown', 0)

        # Estimate annual return
        estimated_annual_return = total_return * 2  # Rough annualization

        # Risk-adjusted capital allocation (Kelly-inspired)
        if sharpe > 0:
            optimal_allocation = min(sharpe / 4, 0.25)  # Conservative Kelly
        else:
            optimal_allocation = 0.0

        # Estimated P&L impact
        estimated_pnl_impact = estimated_annual_return * optimal_allocation

        # ROI calculation
        implementation_cost_hours = {
            FeasibilityLevel.TRIVIAL: 4,
            FeasibilityLevel.EASY: 20,
            FeasibilityLevel.MODERATE: 80,
            FeasibilityLevel.HARD: 200,
            FeasibilityLevel.INFEASIBLE: 1000,
        }

        cost_hours = implementation_cost_hours.get(FeasibilityLevel.MODERATE, 80)
        roi = estimated_pnl_impact / max(cost_hours * 50, 1)  # $50/hour assumed

        passed = roi > 0.1 and estimated_pnl_impact > 0

        return PipelineResult(
            source_id=experiment.source_ids[0] if experiment.source_ids else '',
            stage=PipelineStage.CAPITAL_IMPACT_ESTIMATION,
            passed=passed,
            score=min(roi, 1.0),
            details={
                'estimated_annual_return': estimated_annual_return,
                'optimal_allocation': optimal_allocation,
                'estimated_pnl_impact': estimated_pnl_impact,
                'implementation_cost_hours': cost_hours,
                'roi': roi,
                'sharpe_used': sharpe,
            }
        )


class Stage8_HumanPolicyGate:
    """Stage 8: Human / Policy Gate"""

    def __init__(self):
        self.pending_approvals: List[Dict[str, Any]] = []
        self.approved: List[str] = []
        self.rejected: List[str] = []

    def submit_for_approval(
        self,
        experiment: BoundedExperiment,
        pipeline_results: List[PipelineResult]
    ) -> PipelineResult:
        """Submit experiment for human approval."""
        # Auto-approve if all criteria met and risk is low
        all_passed = all(r.passed for r in pipeline_results)
        avg_score = sum(r.score for r in pipeline_results) / max(len(pipeline_results), 1)
        low_risk = experiment.risk_budget <= 0.01

        if all_passed and avg_score > 0.7 and low_risk:
            # Auto-approve low-risk, high-confidence experiments
            self.approved.append(experiment.id)
            return PipelineResult(
                source_id=experiment.source_ids[0] if experiment.source_ids else '',
                stage=PipelineStage.HUMAN_POLICY_GATE,
                passed=True,
                score=avg_score,
                details={
                    'approval_type': 'auto_approved',
                    'reason': 'All criteria met, low risk',
                    'risk_budget': experiment.risk_budget,
                },
            )
        else:
            # Queue for human review
            self.pending_approvals.append({
                'experiment_id': experiment.id,
                'experiment_name': experiment.name,
                'avg_score': avg_score,
                'all_passed': all_passed,
                'risk_budget': experiment.risk_budget,
                'submitted_at': datetime.utcnow().isoformat(),
                'pipeline_results': [
                    {'stage': r.stage.name, 'passed': r.passed, 'score': r.score}
                    for r in pipeline_results
                ],
            })

            return PipelineResult(
                source_id=experiment.source_ids[0] if experiment.source_ids else '',
                stage=PipelineStage.HUMAN_POLICY_GATE,
                passed=False,
                score=avg_score,
                details={
                    'approval_type': 'pending_human_review',
                    'reason': 'Requires human approval',
                    'risk_budget': experiment.risk_budget,
                },
                notes="Queued for human review"
            )

    def approve(self, experiment_id: str) -> bool:
        """Human approves an experiment."""
        self.pending_approvals = [
            p for p in self.pending_approvals if p['experiment_id'] != experiment_id
        ]
        self.approved.append(experiment_id)
        logger.info(f"Experiment {experiment_id} approved by human")
        return True

    def reject(self, experiment_id: str, reason: str = "") -> bool:
        """Human rejects an experiment."""
        self.pending_approvals = [
            p for p in self.pending_approvals if p['experiment_id'] != experiment_id
        ]
        self.rejected.append(experiment_id)
        logger.info(f"Experiment {experiment_id} rejected: {reason}")
        return True


class Stage9_ProductionDeployment:
    """Stage 9: Production Deployment"""

    def __init__(self):
        self.deployed: List[Dict[str, Any]] = []

    def deploy(self, experiment: BoundedExperiment) -> PipelineResult:
        """Deploy an approved experiment to production."""
        deployment = {
            'experiment_id': experiment.id,
            'name': experiment.name,
            'deployed_at': datetime.utcnow().isoformat(),
            'initial_allocation': 0.01,  # Start with 1% allocation
            'ramp_up_schedule': {
                'week_1': 0.01,
                'week_2': 0.02,
                'week_4': 0.05,
                'week_8': 0.10,
            },
            'kill_criteria': {
                'max_drawdown': 0.05,
                'min_sharpe': 0.5,
                'max_consecutive_losses': 10,
            },
            'monitoring': {
                'check_interval_minutes': 60,
                'alert_on_drawdown': 0.03,
                'auto_kill_on_drawdown': 0.05,
            },
        }

        self.deployed.append(deployment)

        return PipelineResult(
            source_id=experiment.source_ids[0] if experiment.source_ids else '',
            stage=PipelineStage.PRODUCTION_DEPLOYMENT,
            passed=True,
            score=1.0,
            details=deployment,
            notes=f"Deployed with 1% initial allocation, ramping up over 8 weeks"
        )


# ============================================================================
# MASTER PIPELINE ORCHESTRATOR
# ============================================================================

class ResearchIngestionPipeline:
    """
    Master orchestrator for the 9-stage research ingestion pipeline.
    
    Pipeline Flow:
    1. Ingestion → 2. Relevance Filter → 3. Claim Extraction →
    4. Feasibility Scoring → 5. Sandbox Implementation →
    6. Backtest & Stress Test → 7. Capital Impact Estimation →
    8. Human/Policy Gate → 9. Production Deployment
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        # Initialize all stages
        self.stage1 = Stage1_Ingestion()
        self.stage2 = Stage2_RelevanceFilter()
        self.stage3 = Stage3_ClaimExtraction()
        self.stage4 = Stage4_FeasibilityScoring()
        self.stage5 = Stage5_SandboxImplementation()
        self.stage6 = Stage6_BacktestStressTest()
        self.stage7 = Stage7_CapitalImpactEstimation()
        self.stage8 = Stage8_HumanPolicyGate()
        self.stage9 = Stage9_ProductionDeployment()

        # Pipeline state
        self.pipeline_runs: List[Dict[str, Any]] = []
        self.ideas_ranked_by_roi: List[Dict[str, Any]] = []

        logger.info("ResearchIngestionPipeline initialized (9 stages)")

    async def process_source(self, source_data: Dict[str, Any], source_type: str = 'paper') -> Dict[str, Any]:
        """
        Process a single source through the entire pipeline.
        
        Args:
            source_data: Raw source data
            source_type: 'paper', 'arxiv', 'github', or 'generic'
            
        Returns:
            Pipeline results for this source
        """
        pipeline_results = []
        run_start = datetime.utcnow()

        # Stage 1: Ingestion
        if source_type == 'arxiv':
            source = self.stage1.ingest_arxiv_paper(source_data)
        elif source_type == 'github':
            source = self.stage1.ingest_github_repo(source_data)
        else:
            source = self.stage1.ingest_generic_paper(source_data)

        source.current_stage = PipelineStage.INGESTION
        logger.info(f"[Stage 1/9] Ingested: {source.title[:60]}")

        # Stage 2: Relevance Filtering
        relevance_result = self.stage2.filter(source)
        pipeline_results.append(relevance_result)
        source.current_stage = PipelineStage.RELEVANCE_FILTERING

        if not relevance_result.passed:
            logger.info(f"[Stage 2/9] FILTERED OUT: {source.title[:60]} (score={relevance_result.score:.2f})")
            return self._create_run_record(source, pipeline_results, 'filtered_relevance', run_start)

        logger.info(f"[Stage 2/9] Relevant: {relevance_result.details.get('category', 'unknown')}")

        # Stage 3: Claim Extraction
        claims = self.stage3.extract_claims(source)
        source.current_stage = PipelineStage.CLAIM_EXTRACTION

        if not claims:
            logger.info(f"[Stage 3/9] No claims extracted from: {source.title[:60]}")
            return self._create_run_record(source, pipeline_results, 'no_claims', run_start)

        logger.info(f"[Stage 3/9] Extracted {len(claims)} claims")

        # Stage 4: Feasibility Scoring
        feasibility_results = []
        for claim in claims:
            feas_result = self.stage4.score(claim, source)
            feasibility_results.append(feas_result)
            pipeline_results.append(feas_result)

        source.current_stage = PipelineStage.FEASIBILITY_SCORING

        feasible_claims = [
            (c, r) for c, r in zip(claims, feasibility_results) if r.passed
        ]

        if not feasible_claims:
            logger.info(f"[Stage 4/9] No feasible claims from: {source.title[:60]}")
            return self._create_run_record(source, pipeline_results, 'not_feasible', run_start)

        best_feasibility = max(r.score for _, r in feasible_claims)
        logger.info(f"[Stage 4/9] {len(feasible_claims)} feasible claims (best score={best_feasibility:.2f})")

        # Stage 5: Sandbox Implementation
        experiment = self.stage5.create_experiment(
            [c for c, _ in feasible_claims],
            source,
            best_feasibility
        )
        source.current_stage = PipelineStage.SANDBOX_IMPLEMENTATION
        logger.info(f"[Stage 5/9] Created experiment: {experiment.id}")

        # Stage 6: Backtest & Stress Test
        backtest_result = self.stage6.evaluate_experiment(experiment)
        pipeline_results.append(backtest_result)
        source.current_stage = PipelineStage.BACKTEST_STRESS_TEST
        logger.info(f"[Stage 6/9] Backtest score: {backtest_result.score:.2f}")

        # Stage 7: Capital Impact Estimation
        impact_result = self.stage7.estimate(experiment, backtest_result)
        pipeline_results.append(impact_result)
        source.current_stage = PipelineStage.CAPITAL_IMPACT_ESTIMATION
        logger.info(f"[Stage 7/9] ROI estimate: {impact_result.details.get('roi', 0):.2f}")

        # Stage 8: Human / Policy Gate
        gate_result = self.stage8.submit_for_approval(experiment, pipeline_results)
        pipeline_results.append(gate_result)
        source.current_stage = PipelineStage.HUMAN_POLICY_GATE
        logger.info(f"[Stage 8/9] Gate: {gate_result.details.get('approval_type', 'unknown')}")

        # Stage 9: Production Deployment (only if approved)
        if gate_result.passed:
            deploy_result = self.stage9.deploy(experiment)
            pipeline_results.append(deploy_result)
            source.current_stage = PipelineStage.PRODUCTION_DEPLOYMENT
            logger.info(f"[Stage 9/9] DEPLOYED: {experiment.name}")
        else:
            logger.info(f"[Stage 9/9] Pending approval for: {experiment.name}")

        # Rank by ROI
        self._update_roi_rankings(experiment, pipeline_results)

        return self._create_run_record(source, pipeline_results, 'completed', run_start)

    async def process_batch(self, sources: List[Dict[str, Any]], source_type: str = 'paper') -> Dict[str, Any]:
        """Process a batch of sources through the pipeline."""
        results = []
        for source_data in sources:
            result = await self.process_source(source_data, source_type)
            results.append(result)

        return {
            'total_processed': len(results),
            'passed_relevance': sum(1 for r in results if r.get('final_stage', '') != 'filtered_relevance'),
            'experiments_created': sum(1 for r in results if r.get('experiment_id')),
            'deployed': sum(1 for r in results if r.get('final_stage') == 'completed' and r.get('deployed')),
            'pending_approval': len(self.stage8.pending_approvals),
            'results': results,
        }

    def _create_run_record(
        self,
        source: ResearchSource,
        results: List[PipelineResult],
        final_stage: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create a pipeline run record."""
        record = {
            'source_id': source.id,
            'source_title': source.title,
            'source_type': source.source_type.name,
            'final_stage': final_stage,
            'stages_completed': len(results),
            'duration_seconds': (datetime.utcnow() - start_time).total_seconds(),
            'stage_results': [
                {
                    'stage': r.stage.name,
                    'passed': r.passed,
                    'score': r.score,
                }
                for r in results
            ],
        }
        self.pipeline_runs.append(record)
        return record

    def _update_roi_rankings(self, experiment: BoundedExperiment, results: List[PipelineResult]):
        """Update ROI rankings."""
        impact_results = [r for r in results if r.stage == PipelineStage.CAPITAL_IMPACT_ESTIMATION]
        if impact_results:
            roi = impact_results[0].details.get('roi', 0)
            self.ideas_ranked_by_roi.append({
                'experiment_id': experiment.id,
                'name': experiment.name,
                'roi': roi,
                'priority_score': experiment.priority_score,
                'timestamp': datetime.utcnow().isoformat(),
            })
            self.ideas_ranked_by_roi.sort(key=lambda x: x['roi'], reverse=True)

    def get_roi_rankings(self) -> List[Dict[str, Any]]:
        """Get ideas ranked by ROI."""
        return self.ideas_ranked_by_roi

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get experiments pending human approval."""
        return self.stage8.pending_approvals

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get comprehensive pipeline summary."""
        return {
            'total_sources_ingested': len(self.stage1.sources),
            'total_pipeline_runs': len(self.pipeline_runs),
            'sources_by_type': {
                st.name: sum(1 for s in self.stage1.sources.values() if s.source_type == st)
                for st in SourceType
                if any(s.source_type == st for s in self.stage1.sources.values())
            },
            'relevance_pass_rate': (
                sum(1 for r in self.stage2.filter_results.values() if r.passed) /
                max(len(self.stage2.filter_results), 1)
            ),
            'total_claims_extracted': sum(len(c) for c in self.stage3.claims.values()),
            'total_experiments': len(self.stage5.sandbox_experiments),
            'pending_approvals': len(self.stage8.pending_approvals),
            'approved': len(self.stage8.approved),
            'rejected': len(self.stage8.rejected),
            'deployed': len(self.stage9.deployed),
            'top_roi_ideas': self.ideas_ranked_by_roi[:10],
        }

    def save_state(self, path: str = None):
        """Save pipeline state."""
        if path is None:
            path = 'research_pipeline_data/pipeline_state.json'
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        state = self.get_pipeline_summary()
        state['pipeline_runs'] = self.pipeline_runs
        state['saved_at'] = datetime.utcnow().isoformat()

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, default=str)

        logger.info(f"Pipeline state saved to {path}")
