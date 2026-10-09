"""
Relevance Filter

Filters ingested research papers and GitHub repos for relevance
to AlphaAlgo's trading constraints and current capabilities.
Maps ideas to our system's architecture and identifies gaps.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RelevanceLevel(Enum):
    """How relevant a piece of research is."""
    IRRELEVANT = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RelevanceScore:
    """Detailed relevance scoring for a research item."""
    item_id: str
    item_type: str  # 'paper' or 'repo'
    overall_score: float  # 0.0 to 1.0
    level: RelevanceLevel
    category_scores: Dict[str, float] = field(default_factory=dict)
    matching_keywords: List[str] = field(default_factory=list)
    applicable_layers: List[str] = field(default_factory=list)
    gaps_addressed: List[str] = field(default_factory=list)
    constraints_compatible: bool = True
    rejection_reasons: List[str] = field(default_factory=list)
    scored_at: datetime = field(default_factory=datetime.utcnow)


class RelevanceFilter:
    """
    Filters research for relevance to AlphaAlgo.
    
    Evaluates whether a paper/repo's ideas can be mapped to our
    system's 10-layer architecture and trading constraints.
    """

    # AlphaAlgo's current capabilities (used to find gaps)
    CURRENT_CAPABILITIES = {
        'ml_models': ['lstm', 'transformer', 'random_forest', 'xgboost', 'ensemble'],
        'rl_algorithms': ['dqn', 'ppo', 'cql', 'iql', 'bcq'],
        'risk_methods': ['kelly', 'var', 'cvar', 'fixed_fractional', 'optimal_f'],
        'execution_algos': ['twap', 'vwap', 'pov', 'adaptive', 'sniper'],
        'data_sources': ['ohlcv', 'order_book', 'news', 'sentiment', 'alternative'],
        'indicators': ['rsi', 'macd', 'bollinger', 'atr', 'volume_profile'],
        'regime_detection': ['hmm', 'change_point', 'volatility_regime'],
        'portfolio': ['mean_variance', 'risk_parity', 'black_litterman'],
    }

    # System layers that can receive improvements
    SYSTEM_LAYERS = [
        'Layer0_Infrastructure', 'Layer1_Observability', 'Layer2_Connectivity',
        'Layer3_DataFoundation', 'Layer4_Intelligence', 'Layer5_Signal',
        'Layer6_RiskSafety', 'Layer7_Decision', 'Layer8_Execution',
        'Layer9_Orchestration',
    ]

    # Hard constraints that filter out incompatible research
    HARD_CONSTRAINTS = {
        'max_position_size': 0.10,
        'max_daily_loss': 0.05,
        'max_drawdown': 0.25,
        'max_leverage': 5.0,
        'requires_stop_loss': True,
        'min_backtest_months': 6,
        'supported_languages': ['python'],
    }

    # Keywords that indicate high relevance
    HIGH_RELEVANCE_KEYWORDS = [
        'alpha', 'sharpe', 'drawdown', 'risk-adjusted', 'out-of-sample',
        'walk-forward', 'regime', 'adaptive', 'online learning',
        'transaction cost', 'slippage', 'market impact', 'execution',
        'portfolio optimization', 'position sizing', 'stop loss',
        'mean reversion', 'momentum', 'factor', 'sentiment',
    ]

    # Keywords that indicate low relevance or incompatibility
    LOW_RELEVANCE_KEYWORDS = [
        'theoretical only', 'no empirical', 'simulated data only',
        'requires proprietary', 'manual trading', 'fundamental only',
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.filter_history: List[RelevanceScore] = []
            self.min_relevance = self.config.get('min_relevance', 0.3)
            logger.info("RelevanceFilter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def score_paper(self, paper) -> RelevanceScore:
        """Score a research paper for relevance."""
        try:
            text = (paper.title + " " + paper.abstract).lower()
            return self._score_text(paper.id, 'paper', text, getattr(paper, 'categories', []))
        except Exception as e:
            logger.error(f"Error in score_paper: {e}")
            raise

    def score_repo(self, repo) -> RelevanceScore:
        """Score a GitHub repo for relevance."""
        try:
            text = (
                repo.name + " " + repo.description + " " +
                " ".join(repo.topics) + " " +
                " ".join([s.get('name', '') for s in repo.strategies_found]) + " " +
                " ".join([t.get('name', '') for t in repo.techniques_found])
            ).lower()
            return self._score_text(repo.id, 'repo', text, repo.categories)
        except Exception as e:
            logger.error(f"Error in score_repo: {e}")
            raise

    def _score_text(
        self, item_id: str, item_type: str, text: str, categories: list
    ) -> RelevanceScore:
        """Core scoring logic."""
        try:
            score = RelevanceScore(item_id=item_id, item_type=item_type, overall_score=0.0, level=RelevanceLevel.IRRELEVANT)

            # 1. Keyword matching
            high_matches = [kw for kw in self.HIGH_RELEVANCE_KEYWORDS if kw in text]
            low_matches = [kw for kw in self.LOW_RELEVANCE_KEYWORDS if kw in text]
            score.matching_keywords = high_matches

            keyword_score = min(len(high_matches) * 0.08, 0.4)
            penalty = len(low_matches) * 0.15
            score.category_scores['keywords'] = max(keyword_score - penalty, 0)

            # 2. Gap analysis — does this address something we DON'T have?
            gaps = self._identify_gaps(text)
            score.gaps_addressed = gaps
            score.category_scores['gap_filling'] = min(len(gaps) * 0.15, 0.3)

            # 3. Layer mapping — which layers could benefit?
            layers = self._map_to_layers(text)
            score.applicable_layers = layers
            score.category_scores['layer_mapping'] = min(len(layers) * 0.1, 0.2)

            # 4. Practical applicability
            practical_score = 0.0
            if any(w in text for w in ['backtest', 'empirical', 'out-of-sample', 'live trading']):
                practical_score += 0.15
            if any(w in text for w in ['python', 'code available', 'github', 'implementation']):
                practical_score += 0.1
            if any(w in text for w in ['transaction cost', 'slippage', 'realistic']):
                practical_score += 0.1
            score.category_scores['practical'] = min(practical_score, 0.25)

            # 5. Constraint compatibility check
            rejection_reasons = []
            if 'requires proprietary data' in text:
                rejection_reasons.append("Requires proprietary data we don't have")
            if 'high frequency' in text and 'microsecond' in text:
                rejection_reasons.append("Requires sub-millisecond latency")
            if any(lang in text for lang in ['c++ only', 'java only', 'rust only']):
                if 'python' not in text:
                    rejection_reasons.append("Not available in Python")

            score.rejection_reasons = rejection_reasons
            score.constraints_compatible = len(rejection_reasons) == 0

            # Calculate overall score
            if not score.constraints_compatible:
                score.overall_score = 0.1  # Still record but low score
            else:
                score.overall_score = sum(score.category_scores.values())

            # Determine level
            if score.overall_score >= 0.7:
                score.level = RelevanceLevel.CRITICAL
            elif score.overall_score >= 0.5:
                score.level = RelevanceLevel.HIGH
            elif score.overall_score >= 0.3:
                score.level = RelevanceLevel.MEDIUM
            elif score.overall_score >= 0.15:
                score.level = RelevanceLevel.LOW
            else:
                score.level = RelevanceLevel.IRRELEVANT

            self.filter_history.append(score)
            return score
        except Exception as e:
            logger.error(f"Error in _score_text: {e}")
            raise

    def _identify_gaps(self, text: str) -> List[str]:
        """Identify which gaps in our capabilities this research addresses."""
        try:
            gaps = []

            # Techniques we don't have yet
            novel_techniques = {
                'graph_neural_network': ['graph neural', 'gcn', 'gat', 'graph attention'],
                'diffusion_model': ['diffusion model', 'score matching', 'denoising'],
                'state_space_model': ['state space model', 'mamba', 's4'],
                'neural_ode': ['neural ode', 'continuous time'],
                'causal_inference': ['causal inference', 'do-calculus', 'counterfactual'],
                'conformal_prediction': ['conformal prediction', 'prediction interval'],
                'meta_learning': ['meta-learning', 'maml', 'few-shot'],
                'federated_learning': ['federated learning', 'distributed training'],
                'neuroevolution': ['neuroevolution', 'neat', 'evolving neural'],
                'symbolic_regression': ['symbolic regression', 'genetic programming'],
            }

            for technique, keywords in novel_techniques.items():
                if any(kw in text for kw in keywords):
                    gaps.append(technique)

            return gaps
        except Exception as e:
            logger.error(f"Error in _identify_gaps: {e}")
            raise

    def _map_to_layers(self, text: str) -> List[str]:
        """Map research content to applicable system layers."""
        try:
            layers = []

            layer_keywords = {
                'Layer3_DataFoundation': ['feature engineering', 'data processing', 'normalization'],
                'Layer4_Intelligence': ['model', 'prediction', 'neural network', 'learning'],
                'Layer5_Signal': ['signal', 'strategy', 'indicator', 'alpha'],
                'Layer6_RiskSafety': ['risk', 'position sizing', 'drawdown', 'stop loss'],
                'Layer7_Decision': ['ensemble', 'voting', 'consensus', 'multi-agent'],
                'Layer8_Execution': ['execution', 'slippage', 'market impact', 'order'],
            }

            for layer, keywords in layer_keywords.items():
                if any(kw in text for kw in keywords):
                    layers.append(layer)

            return layers
        except Exception as e:
            logger.error(f"Error in _map_to_layers: {e}")
            raise

    def filter_batch(self, items: list, item_type: str = 'paper') -> List[Tuple[Any, RelevanceScore]]:
        """Filter a batch of items, returning only relevant ones."""
        try:
            results = []
            for item in items:
                if item_type == 'paper':
                    score = self.score_paper(item)
                else:
                    score = self.score_repo(item)

                if score.overall_score >= self.min_relevance:
                    results.append((item, score))

            # Sort by relevance
            results.sort(key=lambda x: x[1].overall_score, reverse=True)
            logger.info(f"Filtered {len(items)} {item_type}s → {len(results)} relevant")
            return results
        except Exception as e:
            logger.error(f"Error in filter_batch: {e}")
            raise
