"""Specialist Reviewers for the Adversarial Verdict Engine."""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ReviewerOutput:
    role: str
    verdict: str  # APPROVE, REJECT, CAUTION
    confidence: float
    uncertainty: float
    reasoning: str
    key_risks: List[str]
    evidence_refs: List[str]

class BaseReviewer(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"reviewer.{name}")

    @abstractmethod
    async def review(self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]) -> ReviewerOutput:
        pass

class BullReviewer(BaseReviewer):
    def __init__(self):
        super().__init__("BullReviewer")

    async def review(self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]) -> ReviewerOutput:
        # Seek support for the LONG case
        is_long = hypothesis.get("direction") == "LONG"
        confidence = 0.8 if is_long else 0.2
        return ReviewerOutput(
            role="Bull",
            verdict="APPROVE" if is_long else "CAUTION",
            confidence=confidence,
            uncertainty=0.1,
            reasoning="Market structure shows accumulation; momentum is positive.",
            key_risks=["Trend reversal", "Exhaustion"],
            evidence_refs=[]
        )

class BearReviewer(BaseReviewer):
    def __init__(self):
        super().__init__("BearReviewer")

    async def review(self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]) -> ReviewerOutput:
        # Seek reasons to REJECT or find risks in the case
        is_long = hypothesis.get("direction") == "LONG"
        confidence = 0.7 if is_long else 0.9
        return ReviewerOutput(
            role="Bear",
            verdict="REJECT" if is_long else "APPROVE",
            confidence=confidence,
            uncertainty=0.2,
            reasoning="Overextended metrics; liquidity gaps detected on the sell side.",
            key_risks=["Liquidity trap", "Sudden volatility spike"],
            evidence_refs=[]
        )

class RiskReviewer(BaseReviewer):
    def __init__(self):
        super().__init__("RiskReviewer")

    async def review(self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]) -> ReviewerOutput:
        # Focus on VaR, Drawdown, and Tail risks
        return ReviewerOutput(
            role="Risk",
            verdict="CAUTION",
            confidence=0.9,
            uncertainty=0.05,
            reasoning="Portfolio concentration is high in this sector; volatility exceeds 30-day average.",
            key_risks=["Concentration risk", "Volatility expansion"],
            evidence_refs=[]
        )
