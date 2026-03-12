"""
Trade Documentation - Automated trade documentation and report generation.

Provides structured documentation for every trade, decision, and system event
with audit trail management.
"""

import logging
import json
import os
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DocumentationType(Enum):
    """Types of documentation entries."""
    TRADE_ENTRY = "trade_entry"
    TRADE_EXIT = "trade_exit"
    SIGNAL_GENERATED = "signal_generated"
    RISK_CHECK = "risk_check"
    SYSTEM_EVENT = "system_event"
    STRATEGY_CHANGE = "strategy_change"
    ERROR_REPORT = "error_report"
    PERFORMANCE_REPORT = "performance_report"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_SUMMARY = "weekly_summary"


@dataclass
class TradeReport:
    """Structured trade documentation entry."""
    report_id: str
    doc_type: DocumentationType
    timestamp: datetime
    symbol: str = ""
    direction: str = ""
    quantity: float = 0.0
    price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    reasoning: str = ""
    strategy: str = ""
    confidence: float = 0.0
    risk_score: float = 0.0
    market_regime: str = ""
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        d = asdict(self)
        d["doc_type"] = self.doc_type.value
        d["timestamp"] = self.timestamp.isoformat()
        return d


class TradeDocumenter:
    """
    Automated trade documentation and audit trail system.

    Records every trade, decision, and system event with structured
    documentation for compliance, analysis, and learning.
    """

    def __init__(self, output_dir: str = "trade_documentation", config: Optional[Dict] = None):
        self._config = config or {}
        self._output_dir = output_dir
        self._reports: List[TradeReport] = []
        self._report_counter = 0
        self._daily_stats: Dict[str, Any] = {
            "trades": 0, "wins": 0, "losses": 0,
            "total_pnl": 0.0, "signals": 0,
        }

        os.makedirs(output_dir, exist_ok=True)
        logger.info("TradeDocumenter initialized, output: %s", output_dir)

    def document_trade_entry(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        strategy: str = "",
        confidence: float = 0.0,
        reasoning: str = "",
        risk_score: float = 0.0,
        market_regime: str = "",
        metadata: Optional[Dict] = None,
    ) -> TradeReport:
        """Document a trade entry."""
        report = self._create_report(
            doc_type=DocumentationType.TRADE_ENTRY,
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            price=price,
            strategy=strategy,
            confidence=confidence,
            reasoning=reasoning,
            risk_score=risk_score,
            market_regime=market_regime,
            metadata=metadata,
        )
        self._daily_stats["trades"] += 1
        logger.info("Documented trade entry: %s %s %s @ %.4f",
                     direction, quantity, symbol, price)
        return report

    def document_trade_exit(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        pnl: float = 0.0,
        pnl_pct: float = 0.0,
        exit_reason: str = "",
        metadata: Optional[Dict] = None,
    ) -> TradeReport:
        """Document a trade exit."""
        report = self._create_report(
            doc_type=DocumentationType.TRADE_EXIT,
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            price=price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            reasoning=exit_reason,
            metadata=metadata,
        )
        self._daily_stats["total_pnl"] += pnl
        if pnl > 0:
            self._daily_stats["wins"] += 1
        elif pnl < 0:
            self._daily_stats["losses"] += 1
        logger.info("Documented trade exit: %s %s P&L=%.2f (%.2f%%)",
                     symbol, direction, pnl, pnl_pct * 100)
        return report

    def document_signal(
        self,
        symbol: str,
        direction: str,
        confidence: float,
        strategy: str = "",
        reasoning: str = "",
        metadata: Optional[Dict] = None,
    ) -> TradeReport:
        """Document a generated signal."""
        report = self._create_report(
            doc_type=DocumentationType.SIGNAL_GENERATED,
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            strategy=strategy,
            reasoning=reasoning,
            metadata=metadata,
        )
        self._daily_stats["signals"] += 1
        return report

    def document_risk_check(
        self,
        symbol: str,
        passed: bool,
        risk_score: float,
        details: str = "",
        metadata: Optional[Dict] = None,
    ) -> TradeReport:
        """Document a risk check result."""
        return self._create_report(
            doc_type=DocumentationType.RISK_CHECK,
            symbol=symbol,
            risk_score=risk_score,
            reasoning=f"{'PASSED' if passed else 'FAILED'}: {details}",
            metadata=metadata,
        )

    def document_system_event(
        self,
        event_type: str,
        description: str,
        metadata: Optional[Dict] = None,
    ) -> TradeReport:
        """Document a system event."""
        return self._create_report(
            doc_type=DocumentationType.SYSTEM_EVENT,
            reasoning=f"{event_type}: {description}",
            metadata=metadata,
        )

    def generate_daily_summary(self) -> TradeReport:
        """Generate and document a daily summary."""
        win_rate = (
            self._daily_stats["wins"] / self._daily_stats["trades"] * 100
            if self._daily_stats["trades"] > 0 else 0
        )
        summary = (
            f"Trades: {self._daily_stats['trades']}, "
            f"Wins: {self._daily_stats['wins']}, "
            f"Losses: {self._daily_stats['losses']}, "
            f"Win Rate: {win_rate:.1f}%, "
            f"Total P&L: {self._daily_stats['total_pnl']:.2f}, "
            f"Signals: {self._daily_stats['signals']}"
        )
        report = self._create_report(
            doc_type=DocumentationType.DAILY_SUMMARY,
            reasoning=summary,
            pnl=self._daily_stats["total_pnl"],
            metadata=dict(self._daily_stats),
        )

        # Reset daily stats
        self._daily_stats = {
            "trades": 0, "wins": 0, "losses": 0,
            "total_pnl": 0.0, "signals": 0,
        }

        return report

    def save_reports(self, filename: Optional[str] = None) -> str:
        """Save all reports to a JSON file."""
        if filename is None:
            filename = f"reports_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = os.path.join(self._output_dir, filename)
        data = [r.to_dict() for r in self._reports]

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info("Saved %d reports to %s", len(data), filepath)
        return filepath

    def get_reports(
        self,
        doc_type: Optional[DocumentationType] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List[TradeReport]:
        """Query reports with optional filters."""
        results = self._reports
        if doc_type:
            results = [r for r in results if r.doc_type == doc_type]
        if symbol:
            results = [r for r in results if r.symbol == symbol]
        return results[-limit:]

    def get_status(self) -> Dict:
        """Get documenter status."""
        return {
            "total_reports": len(self._reports),
            "daily_stats": dict(self._daily_stats),
            "output_dir": self._output_dir,
            "report_types": {
                dt.value: sum(1 for r in self._reports if r.doc_type == dt)
                for dt in DocumentationType
            },
        }

    def _create_report(self, **kwargs) -> TradeReport:
        """Create and store a new report."""
        self._report_counter += 1
        report = TradeReport(
            report_id=f"DOC-{self._report_counter:06d}",
            timestamp=datetime.utcnow(),
            **kwargs,
        )
        self._reports.append(report)

        # Keep memory bounded
        if len(self._reports) > 10000:
            self._reports = self._reports[-5000:]

        return report
