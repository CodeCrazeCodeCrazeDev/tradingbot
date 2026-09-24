"""
Systems AI Orchestrator
============================================================

Evidence-collection and hypothesis-generation layer used by the
CSC hub: accepts SignalRequest observations, produces directional
hypotheses with confidence.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SystemMode(Enum):
    PAPER = "paper"
    LIVE = "live"
    BACKTEST = "backtest"
    RESEARCH = "research"


@dataclass
class SystemConfig:
    mode: SystemMode = SystemMode.PAPER
    confidence_floor: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalRequest:
    request_id: str
    symbol: str
    timestamp: datetime
    features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalHypothesis:
    request_id: str
    symbol: str
    direction: int          # +1 long, -1 short, 0 flat
    confidence: float       # 0..1
    rationale: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class SystemsAIOrchestrator:
    """Generates hypotheses from SignalRequests.

    The evidence layer is intentionally conservative: without a
    registered hypothesis engine it returns a flat (direction=0)
    hypothesis at zero confidence rather than fabricating a view.
    """

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()
        self._engines: List[Any] = []
        self._history: List[SignalHypothesis] = []
        logger.info(f"SystemsAIOrchestrator initialized (mode={self.config.mode.value})")

    def register_engine(self, engine: Any) -> None:
        self._engines.append(engine)

    def generate_signal(self, request: SignalRequest) -> SignalHypothesis:
        direction, confidence, rationale = 0, 0.0, "no hypothesis engine registered"
        for eng in self._engines:
            fn = getattr(eng, "hypothesize", None) or getattr(eng, "generate", None)
            if callable(fn):
                try:
                    res = fn(request)
                    direction = int(getattr(res, "direction", res.get("direction", 0) if isinstance(res, dict) else 0))
                    confidence = float(getattr(res, "confidence", res.get("confidence", 0.0) if isinstance(res, dict) else 0.0))
                    rationale = getattr(res, "rationale", res.get("rationale", "") if isinstance(res, dict) else "")
                    break
                except Exception as e:
                    logger.warning(f"SystemsAI engine failed: {e}")
        hyp = SignalHypothesis(
            request_id=request.request_id,
            symbol=request.symbol,
            direction=direction,
            confidence=confidence,
            rationale=rationale,
        )
        self._history.append(hyp)
        return hyp

    def status(self) -> Dict[str, Any]:
        return {"mode": self.config.mode.value,
                "engines": len(self._engines),
                "hypotheses": len(self._history)}
