"""
Unified Analyzer - Consolidated analysis interface across all analysis subsystems.

Delegates to specialized analysis modules and aggregates results into a single
coherent analysis output.
"""

import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of analysis available."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    MICROSTRUCTURE = "microstructure"
    REGIME = "regime"
    VOLUME_PROFILE = "volume_profile"
    ORDER_FLOW = "order_flow"
    PATTERN = "pattern"
    MULTI_TIMEFRAME = "multi_timeframe"
    CORRELATION = "correlation"
    VOLATILITY = "volatility"
    COMPREHENSIVE = "comprehensive"


@dataclass
class AnalysisResult:
    """Result from a unified analysis run."""
    analysis_id: str
    symbol: str
    timestamp: datetime
    analysis_types: List[AnalysisType]
    direction: str = "neutral"  # bullish, bearish, neutral
    confidence: float = 0.0
    strength: float = 0.0
    regime: str = "unknown"
    volatility_state: str = "normal"
    key_levels: Dict[str, float] = field(default_factory=dict)
    signals: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)
    sub_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedAnalyzer:
    """
    Consolidated analysis interface that delegates to specialized modules.
    
    Integrates outputs from:
    - trading_bot/analysis/ (technical, pattern, volume, etc.)
    - trading_bot/analytics/ (growth, attribution, psychological)
    - trading_bot/market_intelligence/ (market intel)
    - trading_bot/deepchart/ (chart intelligence)
    - trading_bot/indicators/ (technical indicators)
    """

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._analyzers: Dict[AnalysisType, Any] = {}
        self._analysis_count = 0
        self._initialize_analyzers()
        logger.info("UnifiedAnalyzer initialized")

    def _initialize_analyzers(self) -> None:
        """Initialize available analysis sub-modules."""
        # Technical analysis
        try:
            from trading_bot.analysis import market_analysis
            self._analyzers[AnalysisType.TECHNICAL] = market_analysis
            logger.debug("Technical analysis module loaded")
        except (ImportError, AttributeError):
            logger.debug("Technical analysis module not available")

        # Regime detection
        try:
            from trading_bot.analysis import regime_detector
            self._analyzers[AnalysisType.REGIME] = regime_detector
            logger.debug("Regime detection module loaded")
        except (ImportError, AttributeError):
            logger.debug("Regime detection module not available")

        # Volume profile
        try:
            from trading_bot.analysis import volume_profile
            self._analyzers[AnalysisType.VOLUME_PROFILE] = volume_profile
            logger.debug("Volume profile module loaded")
        except (ImportError, AttributeError):
            logger.debug("Volume profile module not available")

        # Sentiment
        try:
            from trading_bot.sentiment import sentiment_analyzer
            self._analyzers[AnalysisType.SENTIMENT] = sentiment_analyzer
            logger.debug("Sentiment analysis module loaded")
        except (ImportError, AttributeError):
            logger.debug("Sentiment analysis module not available")

    def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        analysis_types: Optional[List[AnalysisType]] = None,
    ) -> AnalysisResult:
        """
        Run unified analysis on a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT', 'EURUSD')
            market_data: Dictionary containing OHLCV and other market data
            analysis_types: Specific analysis types to run (None = all available)
            
        Returns:
            AnalysisResult with aggregated findings
        """
        self._analysis_count += 1
        analysis_id = f"UA-{self._analysis_count:06d}"

        if analysis_types is None:
            analysis_types = [AnalysisType.COMPREHENSIVE]

        if AnalysisType.COMPREHENSIVE in analysis_types:
            analysis_types = list(self._analyzers.keys())

        sub_results = {}
        all_signals = []
        all_reasoning = []
        directions = []
        confidences = []

        for atype in analysis_types:
            try:
                result = self._run_sub_analysis(atype, symbol, market_data)
                if result:
                    sub_results[atype.value] = result
                    if "direction" in result:
                        directions.append(result["direction"])
                    if "confidence" in result:
                        confidences.append(result["confidence"])
                    if "signals" in result:
                        all_signals.extend(result["signals"])
                    if "reasoning" in result:
                        all_reasoning.append(result["reasoning"])
            except Exception as e:
                logger.warning("Sub-analysis %s failed: %s", atype.value, e)
                sub_results[atype.value] = {"error": str(e)}

        # Aggregate direction
        direction = self._aggregate_direction(directions)
        confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return AnalysisResult(
            analysis_id=analysis_id,
            symbol=symbol,
            timestamp=datetime.utcnow(),
            analysis_types=analysis_types,
            direction=direction,
            confidence=confidence,
            strength=confidence,
            signals=all_signals,
            reasoning=all_reasoning,
            sub_results=sub_results,
            metadata={"analyzers_available": len(self._analyzers)},
        )

    def _run_sub_analysis(
        self, atype: AnalysisType, symbol: str, market_data: Dict
    ) -> Optional[Dict]:
        """Run a specific sub-analysis type."""
        analyzer = self._analyzers.get(atype)
        if not analyzer:
            return None

        # Each analyzer may have different interfaces; wrap generically
        try:
            if hasattr(analyzer, "analyze"):
                return analyzer.analyze(symbol, market_data)
            elif hasattr(analyzer, "run"):
                return analyzer.run(symbol, market_data)
            else:
                return {"status": "analyzer_loaded", "type": atype.value}
        except Exception as e:
            logger.warning("Error in %s analysis: %s", atype.value, e)
            return {"error": str(e)}

    def _aggregate_direction(self, directions: List[str]) -> str:
        """Aggregate multiple directional signals into consensus."""
        if not directions:
            return "neutral"

        bullish = sum(1 for d in directions if d in ("bullish", "buy", "long"))
        bearish = sum(1 for d in directions if d in ("bearish", "sell", "short"))
        total = len(directions)

        if bullish > total * 0.6:
            return "bullish"
        elif bearish > total * 0.6:
            return "bearish"
        return "neutral"

    def get_available_analyses(self) -> List[str]:
        """Get list of available analysis types."""
        return [atype.value for atype in self._analyzers.keys()]

    def get_status(self) -> Dict:
        """Get analyzer status."""
        return {
            "analyzers_loaded": len(self._analyzers),
            "available_types": self.get_available_analyses(),
            "total_analyses_run": self._analysis_count,
        }
