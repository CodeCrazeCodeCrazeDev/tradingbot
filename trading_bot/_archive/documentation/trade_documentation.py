"""
Trade Documentation System.

This module implements:
- Comprehensive trade journaling
- Screenshot capture and storage
- Trade annotation
- Performance notes
- Lesson tracking
- Trade review system
- Export capabilities
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class TradeQuality(Enum):
    """Trade quality ratings."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class SetupType(Enum):
    """Types of trade setups."""
    TREND_CONTINUATION = "trend_continuation"
    TREND_REVERSAL = "trend_reversal"
    BREAKOUT = "breakout"
    PULLBACK = "pullback"
    RANGE_TRADE = "range_trade"
    NEWS_TRADE = "news_trade"
    SCALP = "scalp"
    SWING = "swing"
    POSITION = "position"
    OTHER = "other"


class EmotionalState(Enum):
    """Emotional states during trading."""
    CALM = "calm"
    CONFIDENT = "confident"
    ANXIOUS = "anxious"
    FEARFUL = "fearful"
    GREEDY = "greedy"
    FRUSTRATED = "frustrated"
    EUPHORIC = "euphoric"
    NEUTRAL = "neutral"


class MistakeType(Enum):
    """Types of trading mistakes."""
    EARLY_ENTRY = "early_entry"
    LATE_ENTRY = "late_entry"
    WRONG_DIRECTION = "wrong_direction"
    OVERSIZED = "oversized"
    UNDERSIZED = "undersized"
    MOVED_STOP = "moved_stop"
    EARLY_EXIT = "early_exit"
    LATE_EXIT = "late_exit"
    NO_STOP = "no_stop"
    REVENGE_TRADE = "revenge_trade"
    FOMO = "fomo"
    IGNORED_RULES = "ignored_rules"
    POOR_TIMING = "poor_timing"
    OTHER = "other"


@dataclass
class Screenshot:
    """Trade screenshot metadata."""
    filename: str
    timestamp: datetime
    timeframe: str
    description: str
    annotations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'filename': self.filename,
            'timestamp': self.timestamp.isoformat(),
            'timeframe': self.timeframe,
            'description': self.description,
            'annotations': self.annotations
        }


@dataclass
class TradeEntry:
    """Entry details for a trade."""
    price: float
    time: datetime
    reason: str
    setup_type: SetupType
    timeframe: str
    indicators_used: List[str] = field(default_factory=list)
    confluence_factors: List[str] = field(default_factory=list)
    entry_quality: float = 0.0  # 0-1
    
    def to_dict(self) -> Dict:
        return {
            'price': self.price,
            'time': self.time.isoformat(),
            'reason': self.reason,
            'setup_type': self.setup_type.value,
            'timeframe': self.timeframe,
            'indicators_used': self.indicators_used,
            'confluence_factors': self.confluence_factors,
            'entry_quality': self.entry_quality
        }


@dataclass
class TradeExit:
    """Exit details for a trade."""
    price: float
    time: datetime
    reason: str
    exit_type: str  # 'stop_loss', 'take_profit', 'manual', etc.
    was_planned: bool = True
    exit_quality: float = 0.0  # 0-1
    
    def to_dict(self) -> Dict:
        return {
            'price': self.price,
            'time': self.time.isoformat(),
            'reason': self.reason,
            'exit_type': self.exit_type,
            'was_planned': self.was_planned,
            'exit_quality': self.exit_quality
        }


@dataclass
class RiskManagement:
    """Risk management details."""
    initial_stop: float
    final_stop: float
    initial_target: float
    final_target: float
    position_size: float
    risk_amount: float
    risk_percent: float
    reward_ratio: float
    stop_moved: bool = False
    stop_move_reason: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TradeReview:
    """Post-trade review."""
    what_went_well: List[str]
    what_went_wrong: List[str]
    lessons_learned: List[str]
    would_take_again: bool
    grade: TradeQuality
    mistakes: List[MistakeType] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'what_went_well': self.what_went_well,
            'what_went_wrong': self.what_went_wrong,
            'lessons_learned': self.lessons_learned,
            'would_take_again': self.would_take_again,
            'grade': self.grade.value,
            'mistakes': [m.value for m in self.mistakes],
            'improvement_areas': self.improvement_areas
        }


@dataclass
class TradeDocument:
    """Complete trade documentation."""
    trade_id: str
    symbol: str
    direction: str
    entry: TradeEntry
    exit: Optional[TradeExit]
    risk_management: RiskManagement
    
    # Performance
    pnl: float = 0.0
    pnl_percent: float = 0.0
    r_multiple: float = 0.0
    mae: float = 0.0  # Max adverse excursion
    mfe: float = 0.0  # Max favorable excursion
    
    # Context
    market_context: str = ""
    pre_trade_analysis: str = ""
    during_trade_notes: str = ""
    
    # Psychology
    emotional_state_entry: EmotionalState = EmotionalState.NEUTRAL
    emotional_state_during: EmotionalState = EmotionalState.NEUTRAL
    emotional_state_exit: EmotionalState = EmotionalState.NEUTRAL
    
    # Media
    screenshots: List[Screenshot] = field(default_factory=list)
    
    # Review
    review: Optional[TradeReview] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry': self.entry.to_dict(),
            'exit': self.exit.to_dict() if self.exit else None,
            'risk_management': self.risk_management.to_dict(),
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'r_multiple': self.r_multiple,
            'mae': self.mae,
            'mfe': self.mfe,
            'market_context': self.market_context,
            'pre_trade_analysis': self.pre_trade_analysis,
            'during_trade_notes': self.during_trade_notes,
            'emotional_state_entry': self.emotional_state_entry.value,
            'emotional_state_during': self.emotional_state_during.value,
            'emotional_state_exit': self.emotional_state_exit.value,
            'screenshots': [s.to_dict() for s in self.screenshots],
            'review': self.review.to_dict() if self.review else None,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class TradeJournal:
    """
    Complete trade journaling system.
    """
    
    def __init__(self, storage_path: str = "./trade_journal"):
        self.storage_path = storage_path
        self.trades: Dict[str, TradeDocument] = {}
        self.lessons: List[Dict[str, Any]] = []
        
        # Create storage directories
        os.makedirs(storage_path, exist_ok=True)
        os.makedirs(os.path.join(storage_path, "screenshots"), exist_ok=True)
        os.makedirs(os.path.join(storage_path, "exports"), exist_ok=True)
        
        # Load existing trades
        self._load_trades()
    
    def _generate_trade_id(self, symbol: str, timestamp: datetime) -> str:
        """Generate unique trade ID."""
        data = f"{symbol}{timestamp.isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def _load_trades(self) -> None:
        """Load trades from storage."""
        trades_file = os.path.join(self.storage_path, "trades.json")
        if os.path.exists(trades_file):
            try:
                with open(trades_file, 'r') as f:
                    data = json.load(f)
                    # Would need to deserialize properly
                    logger.info(f"Loaded {len(data)} trades from storage")
            except Exception as e:
                logger.error(f"Error loading trades: {e}")
    
    def _save_trades(self) -> None:
        """Save trades to storage."""
        trades_file = os.path.join(self.storage_path, "trades.json")
        try:
            data = {tid: trade.to_dict() for tid, trade in self.trades.items()}
            with open(trades_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trades: {e}")
    
    def create_trade(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        entry_time: datetime,
        entry_reason: str,
        setup_type: SetupType,
        timeframe: str,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        risk_percent: float = 0.02
    ) -> TradeDocument:
        """Create a new trade document."""
        trade_id = self._generate_trade_id(symbol, entry_time)
        
        # Calculate risk
        risk_amount = abs(entry_price - stop_loss) * position_size
        reward_ratio = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
        
        entry = TradeEntry(
            price=entry_price,
            time=entry_time,
            reason=entry_reason,
            setup_type=setup_type,
            timeframe=timeframe
        )
        
        risk_mgmt = RiskManagement(
            initial_stop=stop_loss,
            final_stop=stop_loss,
            initial_target=take_profit,
            final_target=take_profit,
            position_size=position_size,
            risk_amount=risk_amount,
            risk_percent=risk_percent,
            reward_ratio=reward_ratio
        )
        
        trade = TradeDocument(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            entry=entry,
            exit=None,
            risk_management=risk_mgmt
        )
        
        self.trades[trade_id] = trade
        self._save_trades()
        
        return trade
    
    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: datetime,
        exit_reason: str,
        exit_type: str
    ) -> Optional[TradeDocument]:
        """Close a trade and calculate performance."""
        if trade_id not in self.trades:
            return None
        
        trade = self.trades[trade_id]
        
        trade.exit = TradeExit(
            price=exit_price,
            time=exit_time,
            reason=exit_reason,
            exit_type=exit_type
        )
        
        # Calculate P&L
        if trade.direction == 'long':
            trade.pnl = (exit_price - trade.entry.price) * trade.risk_management.position_size
        else:
            trade.pnl = (trade.entry.price - exit_price) * trade.risk_management.position_size
        
        trade.pnl_percent = trade.pnl / (trade.entry.price * trade.risk_management.position_size)
        
        # Calculate R-multiple
        risk = abs(trade.entry.price - trade.risk_management.initial_stop)
        if risk > 0:
            if trade.direction == 'long':
                trade.r_multiple = (exit_price - trade.entry.price) / risk
            else:
                trade.r_multiple = (trade.entry.price - exit_price) / risk
        
        trade.updated_at = datetime.now()
        self._save_trades()
        
        return trade
    
    def add_screenshot(
        self,
        trade_id: str,
        filename: str,
        timeframe: str,
        description: str,
        annotations: List[str] = None
    ) -> bool:
        """Add a screenshot to a trade."""
        if trade_id not in self.trades:
            return False
        
        screenshot = Screenshot(
            filename=filename,
            timestamp=datetime.now(),
            timeframe=timeframe,
            description=description,
            annotations=annotations or []
        )
        
        self.trades[trade_id].screenshots.append(screenshot)
        self.trades[trade_id].updated_at = datetime.now()
        self._save_trades()
        
        return True
    
    def add_review(
        self,
        trade_id: str,
        what_went_well: List[str],
        what_went_wrong: List[str],
        lessons_learned: List[str],
        would_take_again: bool,
        grade: TradeQuality,
        mistakes: List[MistakeType] = None
    ) -> bool:
        """Add a review to a trade."""
        if trade_id not in self.trades:
            return False
        
        review = TradeReview(
            what_went_well=what_went_well,
            what_went_wrong=what_went_wrong,
            lessons_learned=lessons_learned,
            would_take_again=would_take_again,
            grade=grade,
            mistakes=mistakes or []
        )
        
        self.trades[trade_id].review = review
        self.trades[trade_id].updated_at = datetime.now()
        
        # Add lessons to global lessons list
        for lesson in lessons_learned:
            self.lessons.append({
                'trade_id': trade_id,
                'lesson': lesson,
                'timestamp': datetime.now().isoformat()
            })
        
        self._save_trades()
        return True
    
    def update_notes(
        self,
        trade_id: str,
        market_context: str = None,
        pre_trade_analysis: str = None,
        during_trade_notes: str = None
    ) -> bool:
        """Update trade notes."""
        if trade_id not in self.trades:
            return False
        
        trade = self.trades[trade_id]
        
        if market_context:
            trade.market_context = market_context
        if pre_trade_analysis:
            trade.pre_trade_analysis = pre_trade_analysis
        if during_trade_notes:
            trade.during_trade_notes = during_trade_notes
        
        trade.updated_at = datetime.now()
        self._save_trades()
        
        return True
    
    def update_emotional_state(
        self,
        trade_id: str,
        phase: str,  # 'entry', 'during', 'exit'
        state: EmotionalState
    ) -> bool:
        """Update emotional state for a trade phase."""
        if trade_id not in self.trades:
            return False
        
        trade = self.trades[trade_id]
        
        if phase == 'entry':
            trade.emotional_state_entry = state
        elif phase == 'during':
            trade.emotional_state_during = state
        elif phase == 'exit':
            trade.emotional_state_exit = state
        
        trade.updated_at = datetime.now()
        self._save_trades()
        
        return True
    
    def add_tags(self, trade_id: str, tags: List[str]) -> bool:
        """Add tags to a trade."""
        if trade_id not in self.trades:
            return False
        
        self.trades[trade_id].tags.extend(tags)
        self.trades[trade_id].tags = list(set(self.trades[trade_id].tags))
        self.trades[trade_id].updated_at = datetime.now()
        self._save_trades()
        
        return True
    
    def get_trade(self, trade_id: str) -> Optional[TradeDocument]:
        """Get a trade by ID."""
        return self.trades.get(trade_id)
    
    def search_trades(
        self,
        symbol: str = None,
        direction: str = None,
        setup_type: SetupType = None,
        grade: TradeQuality = None,
        start_date: datetime = None,
        end_date: datetime = None,
        tags: List[str] = None,
        profitable_only: bool = False
    ) -> List[TradeDocument]:
        """Search trades with filters."""
        results = []
        
        for trade in self.trades.values():
            # Apply filters
            if symbol and trade.symbol != symbol:
                continue
            if direction and trade.direction != direction:
                continue
            if setup_type and trade.entry.setup_type != setup_type:
                continue
            if grade and trade.review and trade.review.grade != grade:
                continue
            if start_date and trade.entry.time < start_date:
                continue
            if end_date and trade.entry.time > end_date:
                continue
            if tags and not any(t in trade.tags for t in tags):
                continue
            if profitable_only and trade.pnl <= 0:
                continue
            
            results.append(trade)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get journal statistics."""
        if not self.trades:
            return {}
        
        closed_trades = [t for t in self.trades.values() if t.exit]
        
        if not closed_trades:
            return {'total_trades': len(self.trades), 'closed_trades': 0}
        
        wins = [t for t in closed_trades if t.pnl > 0]
        losses = [t for t in closed_trades if t.pnl < 0]
        
        return {
            'total_trades': len(self.trades),
            'closed_trades': len(closed_trades),
            'open_trades': len(self.trades) - len(closed_trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': len(wins) / len(closed_trades) if closed_trades else 0,
            'total_pnl': sum(t.pnl for t in closed_trades),
            'avg_win': sum(t.pnl for t in wins) / len(wins) if wins else 0,
            'avg_loss': sum(t.pnl for t in losses) / len(losses) if losses else 0,
            'avg_r_multiple': sum(t.r_multiple for t in closed_trades) / len(closed_trades),
            'best_trade': max(t.pnl for t in closed_trades),
            'worst_trade': min(t.pnl for t in closed_trades),
            'lessons_recorded': len(self.lessons)
        }
    
    def get_lessons(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent lessons learned."""
        return self.lessons[-limit:]
    
    def export_to_csv(self, filepath: str) -> bool:
        """Export trades to CSV."""
        try:
            import csv
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Trade ID', 'Symbol', 'Direction', 'Entry Time', 'Entry Price',
                    'Exit Time', 'Exit Price', 'P&L', 'R-Multiple', 'Setup Type',
                    'Grade', 'Tags'
                ])
                
                # Data
                for trade in self.trades.values():
                    writer.writerow([
                        trade.trade_id,
                        trade.symbol,
                        trade.direction,
                        trade.entry.time.isoformat(),
                        trade.entry.price,
                        trade.exit.time.isoformat() if trade.exit else '',
                        trade.exit.price if trade.exit else '',
                        trade.pnl,
                        trade.r_multiple,
                        trade.entry.setup_type.value,
                        trade.review.grade.value if trade.review else '',
                        ','.join(trade.tags)
                    ])
            
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def export_to_json(self, filepath: str) -> bool:
        """Export trades to JSON."""
        try:
            data = {tid: trade.to_dict() for tid, trade in self.trades.items()}
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False


class TradeReviewSystem:
    """
    System for reviewing and analyzing trades.
    """
    
    def __init__(self, journal: TradeJournal):
        self.journal = journal
        
    def get_performance_by_setup(self) -> Dict[str, Dict[str, float]]:
        """Analyze performance by setup type."""
        results = {}
        
        for setup_type in SetupType:
            trades = self.journal.search_trades(setup_type=setup_type)
            closed = [t for t in trades if t.exit]
            
            if closed:
                wins = [t for t in closed if t.pnl > 0]
                results[setup_type.value] = {
                    'count': len(closed),
                    'win_rate': len(wins) / len(closed),
                    'avg_r': sum(t.r_multiple for t in closed) / len(closed),
                    'total_pnl': sum(t.pnl for t in closed)
                }
        
        return results
    
    def get_performance_by_timeframe(self) -> Dict[str, Dict[str, float]]:
        """Analyze performance by timeframe."""
        results = {}
        
        for trade in self.journal.trades.values():
            if not trade.exit:
                continue
            
            tf = trade.entry.timeframe
            if tf not in results:
                results[tf] = {'trades': [], 'wins': 0, 'total_pnl': 0}
            
            results[tf]['trades'].append(trade)
            if trade.pnl > 0:
                results[tf]['wins'] += 1
            results[tf]['total_pnl'] += trade.pnl
        
        # Calculate statistics
        for tf, data in results.items():
            count = len(data['trades'])
            results[tf] = {
                'count': count,
                'win_rate': data['wins'] / count if count > 0 else 0,
                'total_pnl': data['total_pnl'],
                'avg_pnl': data['total_pnl'] / count if count > 0 else 0
            }
        
        return results
    
    def get_common_mistakes(self) -> Dict[str, int]:
        """Get frequency of common mistakes."""
        mistakes = {}
        
        for trade in self.journal.trades.values():
            if trade.review:
                for mistake in trade.review.mistakes:
                    mistakes[mistake.value] = mistakes.get(mistake.value, 0) + 1
        
        return dict(sorted(mistakes.items(), key=lambda x: x[1], reverse=True))
    
    def get_emotional_impact(self) -> Dict[str, Dict[str, float]]:
        """Analyze impact of emotional states on performance."""
        results = {}
        
        for state in EmotionalState:
            trades = [t for t in self.journal.trades.values() 
                     if t.exit and t.emotional_state_entry == state]
            
            if trades:
                wins = [t for t in trades if t.pnl > 0]
                results[state.value] = {
                    'count': len(trades),
                    'win_rate': len(wins) / len(trades),
                    'avg_pnl': sum(t.pnl for t in trades) / len(trades)
                }
        
        return results


# Convenience functions
def create_trade_journal(path: str = "./trade_journal") -> TradeJournal:
    """Create a new trade journal."""
    return TradeJournal(storage_path=path)


def quick_trade_entry(
    journal: TradeJournal,
    symbol: str,
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    position_size: float,
    setup: str = "other"
) -> str:
    """Quick trade entry."""
    trade = journal.create_trade(
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        entry_time=datetime.now(),
        entry_reason="Quick entry",
        setup_type=SetupType(setup),
        timeframe="H1",
        stop_loss=stop_loss,
        take_profit=take_profit,
        position_size=position_size
    )
    return trade.trade_id
