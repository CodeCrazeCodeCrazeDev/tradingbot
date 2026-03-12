"""
Trade Journal Manager
Automatically records all trades with analysis
"""

import logging
import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


@dataclass
class TradeNote:
    """Trade note"""
    timestamp: datetime
    note: str
    category: str  # entry, exit, observation, lesson
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'note': self.note,
            'category': self.category
        }


@dataclass
class JournalEntry:
    """Trade journal entry"""
    trade_id: str
    symbol: str
    direction: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    stop_loss: float
    take_profit: float
    position_size: float
    profit_loss: Optional[float]
    profit_pips: Optional[float]
    win: Optional[bool]
    strategy: str
    setup_quality: str
    market_conditions: Dict[str, Any]
    notes: List[TradeNote]
    screenshots: List[str]
    lessons_learned: List[str]
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_time': self.entry_time.isoformat(),
            'entry_price': self.entry_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'exit_price': self.exit_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'profit_loss': self.profit_loss,
            'profit_pips': self.profit_pips,
            'win': self.win,
            'strategy': self.strategy,
            'setup_quality': self.setup_quality,
            'market_conditions': self.market_conditions,
            'notes': [note.to_dict() for note in self.notes],
            'screenshots': self.screenshots,
            'lessons_learned': self.lessons_learned,
            'tags': self.tags
        }


class ScreenshotCapture:
    """Screenshot capture utility"""
    
    def __init__(self, save_dir: str = "screenshots"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
    
    def capture(self, trade_id: str, label: str = "entry") -> Optional[str]:
        """Capture screenshot"""
        try:
            from PIL import ImageGrab
            
            # Capture screen
            screenshot = ImageGrab.grab()
            
            # Save
            filename = f"{trade_id}_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.save_dir / filename
            screenshot.save(filepath)
            
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None


class PerformanceAnalyzer:
    """Analyze journal entries for insights"""
    
    def analyze_entries(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze journal entries"""
        if not entries:
            return {}
        
        # Calculate metrics
        total_trades = len(entries)
        winning_trades = sum(1 for e in entries if e.win)
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_profit = sum(e.profit_loss for e in entries if e.profit_loss)
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        # Analyze by strategy
        strategy_stats = {}
        for entry in entries:
            if entry.strategy not in strategy_stats:
                strategy_stats[entry.strategy] = {
                    'trades': 0,
                    'wins': 0,
                    'profit': 0
                }
            
            strategy_stats[entry.strategy]['trades'] += 1
            if entry.win:
                strategy_stats[entry.strategy]['wins'] += 1
            if entry.profit_loss:
                strategy_stats[entry.strategy]['profit'] += entry.profit_loss
        
        # Calculate win rates per strategy
        for strategy, stats in strategy_stats.items():
            stats['win_rate'] = stats['wins'] / stats['trades'] if stats['trades'] > 0 else 0
        
        # Common mistakes
        common_mistakes = self._identify_common_mistakes(entries)
        
        # Best setups
        best_setups = self._identify_best_setups(entries)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit': avg_profit,
            'strategy_stats': strategy_stats,
            'common_mistakes': common_mistakes,
            'best_setups': best_setups
        }
    
    def _identify_common_mistakes(self, entries: List[JournalEntry]) -> List[str]:
        """Identify common mistakes from losing trades"""
        mistakes = []
        
        losing_trades = [e for e in entries if e.win is False]
        
        if not losing_trades:
            return mistakes
        
        # Analyze patterns
        poor_setups = sum(1 for e in losing_trades if e.setup_quality == 'poor')
        if poor_setups / len(losing_trades) > 0.5:
            mistakes.append("Taking too many poor quality setups")
        
        return mistakes
    
    def _identify_best_setups(self, entries: List[JournalEntry]) -> List[Dict[str, Any]]:
        """Identify best performing setups"""
        winning_trades = [e for e in entries if e.win is True]
        
        if not winning_trades:
            return []
        
        # Group by strategy and setup quality
        setup_performance = {}
        for entry in winning_trades:
            key = f"{entry.strategy}_{entry.setup_quality}"
            if key not in setup_performance:
                setup_performance[key] = {
                    'strategy': entry.strategy,
                    'quality': entry.setup_quality,
                    'count': 0,
                    'avg_profit': 0,
                    'total_profit': 0
                }
            
            setup_performance[key]['count'] += 1
            if entry.profit_loss:
                setup_performance[key]['total_profit'] += entry.profit_loss
        
        # Calculate averages
        for setup in setup_performance.values():
            if setup['count'] > 0:
                setup['avg_profit'] = setup['total_profit'] / setup['count']
        
        # Sort by average profit
        best_setups = sorted(
            setup_performance.values(),
            key=lambda x: x['avg_profit'],
            reverse=True
        )[:5]
        
        return best_setups


class TradeJournal:
    """
    Automatic Trade Journal
    Records all trades with analysis and insights
    """
    
    def __init__(self, journal_dir: str = "trade_journal"):
        """Initialize trade journal"""
        self.journal_dir = Path(journal_dir)
        self.journal_dir.mkdir(exist_ok=True)
        
        self.entries: Dict[str, JournalEntry] = {}
        self.screenshot = ScreenshotCapture(str(self.journal_dir / "screenshots"))
        self.analyzer = PerformanceAnalyzer()
        
        # Load existing entries
        self._load_entries()
    
    def record_trade_entry(self,
                          trade_id: str,
                          symbol: str,
                          direction: str,
                          entry_price: float,
                          stop_loss: float,
                          take_profit: float,
                          position_size: float,
                          strategy: str,
                          setup_quality: str,
                          market_conditions: Dict[str, Any],
                          capture_screenshot: bool = True) -> JournalEntry:
        """Record trade entry"""
        
        # Create entry
        entry = JournalEntry(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            entry_time=datetime.now(),
            entry_price=entry_price,
            exit_time=None,
            exit_price=None,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            profit_loss=None,
            profit_pips=None,
            win=None,
            strategy=strategy,
            setup_quality=setup_quality,
            market_conditions=market_conditions,
            notes=[],
            screenshots=[],
            lessons_learned=[],
            tags=[]
        )
        
        # Capture screenshot
        if capture_screenshot:
            screenshot_path = self.screenshot.capture(trade_id, "entry")
            if screenshot_path:
                entry.screenshots.append(screenshot_path)
        
        # Store entry
        self.entries[trade_id] = entry
        self._save_entry(entry)
        
        logger.info(f"Trade entry recorded: {trade_id}")
        
        return entry
    
    def record_trade_exit(self,
                         trade_id: str,
                         exit_price: float,
                         profit_loss: float,
                         profit_pips: float,
                         capture_screenshot: bool = True):
        """Record trade exit"""
        
        if trade_id not in self.entries:
            logger.warning(f"Trade {trade_id} not found in journal")
            return
        
        entry = self.entries[trade_id]
        
        # Update entry
        entry.exit_time = datetime.now()
        entry.exit_price = exit_price
        entry.profit_loss = profit_loss
        entry.profit_pips = profit_pips
        entry.win = profit_loss > 0
        
        # Capture screenshot
        if capture_screenshot:
            screenshot_path = self.screenshot.capture(trade_id, "exit")
            if screenshot_path:
                entry.screenshots.append(screenshot_path)
        
        # Save
        self._save_entry(entry)
        
        logger.info(f"Trade exit recorded: {trade_id}, P/L: {profit_loss}")
    
    def add_note(self, trade_id: str, note: str, category: str = "observation"):
        """Add note to trade"""
        if trade_id not in self.entries:
            return
        
        trade_note = TradeNote(
            timestamp=datetime.now(),
            note=note,
            category=category
        )
        
        self.entries[trade_id].notes.append(trade_note)
        self._save_entry(self.entries[trade_id])
    
    def add_lesson(self, trade_id: str, lesson: str):
        """Add lesson learned"""
        if trade_id not in self.entries:
            return
        
        self.entries[trade_id].lessons_learned.append(lesson)
        self._save_entry(self.entries[trade_id])
    
    def add_tag(self, trade_id: str, tag: str):
        """Add tag to trade"""
        if trade_id not in self.entries:
            return
        
        if tag not in self.entries[trade_id].tags:
            self.entries[trade_id].tags.append(tag)
            self._save_entry(self.entries[trade_id])
    
    def get_entry(self, trade_id: str) -> Optional[JournalEntry]:
        """Get journal entry"""
        return self.entries.get(trade_id)
    
    def get_all_entries(self) -> List[JournalEntry]:
        """Get all entries"""
        return list(self.entries.values())
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze trading performance"""
        return self.analyzer.analyze_entries(self.get_all_entries())
    
    def export_to_csv(self, filepath: str):
        """Export journal to CSV"""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            if not self.entries:
                return
            
            fieldnames = list(self.entries[list(self.entries.keys())[0]].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in self.entries.values():
                row = entry.to_dict()
                # Convert lists to strings
                row['notes'] = json.dumps(row['notes'])
                row['screenshots'] = json.dumps(row['screenshots'])
                row['lessons_learned'] = json.dumps(row['lessons_learned'])
                row['tags'] = json.dumps(row['tags'])
                row['market_conditions'] = json.dumps(row['market_conditions'])
                writer.writerow(row)
        
        logger.info(f"Journal exported to {filepath}")
    
    def _save_entry(self, entry: JournalEntry):
        """Save entry to file"""
        filepath = self.journal_dir / f"{entry.trade_id}.json"
        
        with open(filepath, 'w') as f:
            json.dump(entry.to_dict(), f, indent=2)
    
    def _load_entries(self):
        """Load existing entries"""
        for filepath in self.journal_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    # Reconstruct entry (simplified)
                    self.entries[data['trade_id']] = data
            except Exception as e:
                logger.error(f"Failed to load entry {filepath}: {e}")


__all__ = [
    'TradeJournal',
    'JournalEntry',
    'TradeNote',
    'ScreenshotCapture',
    'PerformanceAnalyzer'
]
