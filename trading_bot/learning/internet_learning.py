"""
Internet Learning System - knowledge acquisition from external sources.

Learns trading knowledge (sentiment, strategies, indicators) from trusted
internet sources, with cross-verification across multiple sources before
knowledge is admitted to the store.
"""

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SourceType(Enum):
    FINANCIAL_NEWS = "financial_news"
    RESEARCH_PAPER = "research_paper"
    MARKET_DATA = "market_data"
    ECONOMIC_INDICATOR = "economic_indicator"


class VerificationStatus(Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    REJECTED = "rejected"
    CONFLICTING = "conflicting"


@dataclass
class TrustedSource:
    name: str
    url: str
    source_type: SourceType
    reliability_score: float = 0.7


@dataclass
class LearnedKnowledge:
    id: str
    source_type: SourceType
    source_url: str
    content: str
    extracted_data: Dict[str, Any]
    timestamp: datetime
    verification_status: VerificationStatus
    confidence_score: float
    verification_sources: List[str] = field(default_factory=list)
    hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


_DEFAULT_SOURCES = [
    TrustedSource("Reuters Markets", "https://reuters.com/markets", SourceType.FINANCIAL_NEWS, 0.9),
    TrustedSource("Bloomberg", "https://bloomberg.com", SourceType.FINANCIAL_NEWS, 0.9),
    TrustedSource("arXiv Quant-Fin", "https://arxiv.org/list/q-fin/recent", SourceType.RESEARCH_PAPER, 0.8),
    TrustedSource("SSRN", "https://ssrn.com", SourceType.RESEARCH_PAPER, 0.75),
    TrustedSource("FRED", "https://fred.stlouisfed.org", SourceType.ECONOMIC_INDICATOR, 0.95),
    TrustedSource("ECB Statistics", "https://ecb.europa.eu/stats", SourceType.ECONOMIC_INDICATOR, 0.9),
    TrustedSource("Yahoo Finance", "https://finance.yahoo.com", SourceType.MARKET_DATA, 0.7),
]


class InternetLearningSystem:
    """Acquires and verifies trading knowledge from trusted internet sources."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.config = config
        self.verification_threshold = config.get("verification_threshold", 0.7)
        self.min_sources_for_verification = config.get("min_sources", 2)
        self.storage_path = config.get("storage_path", "data/learned_knowledge")
        self.trusted_sources: List[TrustedSource] = list(_DEFAULT_SOURCES)
        self.knowledge_base: List[LearnedKnowledge] = []
        self._content_hashes: Dict[str, str] = {}
        logger.info(
            f"InternetLearningSystem initialized "
            f"(threshold={self.verification_threshold}, sources={len(self.trusted_sources)})"
        )

    def _extract_financial_data(self, content: str) -> Dict[str, Any]:
        """Extract numbers, currency pairs, and sentiment from text."""
        data: Dict[str, Any] = {}
        numbers = re.findall(r"\d+\.?\d*%?", content)
        if numbers:
            data["numbers"] = numbers
        pairs = re.findall(r"\b[A-Z]{3}[/_]?[A-Z]{3}\b", content)
        pairs = [p for p in pairs if len(p) in (6, 7)]
        if pairs:
            data["currency_pairs"] = pairs
        bullish = len(re.findall(r"bullish|rally|rallied|momentum|surge|gains?", content, re.I))
        bearish = len(re.findall(r"bearish|fell|decline|drop|selloff|loss", content, re.I))
        data["sentiment"] = {"bullish": bullish, "bearish": bearish}
        return data

    def _extract_strategy_data(self, content: str) -> Dict[str, Any]:
        """Extract strategy names and performance metrics from research text."""
        data: Dict[str, Any] = {}
        strategies = re.findall(
            r"(momentum|mean[- ]reversion|breakout|trend[- ]following|scalping|carry|arbitrage|grid|martingale)[a-z -]*",
            content,
            re.I,
        )
        if strategies:
            data["strategies"] = [s.strip().lower() for s in strategies]
        metrics = re.findall(
            r"(sharpe|sortino|drawdown|win[- ]rate|profit[- ]factor|calmar|alpha|beta)[a-z ]*(?:ratio|of)?\s*(?:of\s*)?(\d+\.?\d*)?",
            content,
            re.I,
        )
        if metrics:
            data["metrics"] = [f"{m[0].strip().lower()} {m[1]}".strip() for m in metrics]
        return data

    def _hash_content(self, content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _generate_id(self, url: str) -> str:
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def _calculate_similarity(self, item1: LearnedKnowledge, item2: LearnedKnowledge) -> float:
        """Similarity via shared extracted-data values and source type."""
        if item1.hash and item1.hash == item2.hash:
            return 1.0
        score = 0.0
        if item1.source_type == item2.source_type:
            score += 0.3
        d1, d2 = item1.extracted_data, item2.extracted_data
        shared_keys = set(d1) & set(d2)
        if shared_keys:
            matches = sum(1 for k in shared_keys if d1[k] == d2[k])
            score += 0.7 * (matches / len(shared_keys))
        return min(score, 1.0)

    async def _cross_verify_knowledge(self, items: List[LearnedKnowledge]) -> List[LearnedKnowledge]:
        """Group items by hash/similarity; items corroborated by enough sources verify."""
        verified: List[LearnedKnowledge] = []
        groups: Dict[str, LearnedKnowledge] = {}
        for item in items:
            key = item.hash or item.id
            if key in groups:
                primary = groups[key]
                for src in item.verification_sources:
                    if src not in primary.verification_sources:
                        primary.verification_sources.append(src)
            else:
                groups[key] = item
                verified.append(item)
        for item in verified:
            if len(item.verification_sources) >= self.min_sources_for_verification:
                item.verification_status = VerificationStatus.VERIFIED
            elif len(item.verification_sources) < 1:
                item.verification_status = VerificationStatus.REJECTED
        return verified

    async def learn_from_internet(self, topics: Optional[List[str]] = None) -> List[LearnedKnowledge]:
        """Fetch and learn from trusted sources (network access required)."""
        logger.info(f"learn_from_internet called for topics={topics}")
        return []

    def get_learning_stats(self) -> Dict[str, Any]:
        items = self.knowledge_base
        verified = sum(1 for i in items if i.verification_status == VerificationStatus.VERIFIED)
        pending = sum(1 for i in items if i.verification_status == VerificationStatus.PENDING)
        rejected = sum(1 for i in items if i.verification_status == VerificationStatus.REJECTED)
        avg_conf = sum(i.confidence_score for i in items) / len(items) if items else 0.0
        return {
            "total_items": len(items),
            "verified": verified,
            "pending": pending,
            "rejected": rejected,
            "verification_rate": verified / len(items) if items else 0.0,
            "trusted_sources": len(self.trusted_sources),
            "avg_confidence": avg_conf,
        }


class AdaptiveLearningAgent:
    """Applies internet-learned knowledge to strategy recommendations."""

    def __init__(self, learning_system: InternetLearningSystem):
        self.learning_system = learning_system
        self.learned_strategies: List[Dict[str, Any]] = []

    def get_strategy_recommendations(self, market_condition: str) -> List[Dict[str, Any]]:
        """Return learned strategies relevant to a market condition."""
        condition = (market_condition or "").lower()
        recs = [
            s for s in self.learned_strategies
            if condition in str(s.get("market_condition", "")).lower()
        ]
        if not recs:
            recs = [
                s for s in self.learned_strategies
                if any(condition in str(t).lower() for t in s.get("techniques", []))
            ]
        return sorted(recs, key=lambda s: s.get("confidence", 0), reverse=True)


__all__ = [
    "SourceType",
    "VerificationStatus",
    "TrustedSource",
    "LearnedKnowledge",
    "InternetLearningSystem",
    "AdaptiveLearningAgent",
]
