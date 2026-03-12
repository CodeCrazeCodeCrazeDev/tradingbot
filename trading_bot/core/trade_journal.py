"""
Trade Journal System
Persistent logging of all trades with detailed metadata
"""

import sqlite3
import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class TradeType(Enum):
    """Trade type"""
    LONG = "long"
    SHORT = "short"


class TradeStatus(Enum):
    """Trade status"""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


@dataclass
class TradeEntry:
    """Trade journal entry"""
    trade_id: str
    symbol: str
    trade_type: TradeType
    entry_time: datetime
    entry_price: float
    quantity: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    commission: float = 0.0
    slippage: float = 0.0
    status: TradeStatus = TradeStatus.OPEN
    strategy: Optional[str] = None
    signal_confidence: Optional[float] = None
    market_regime: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        try:
            d = asdict(self)
            d['trade_type'] = self.trade_type.value
            d['status'] = self.status.value
            d['entry_time'] = self.entry_time.isoformat()
            if self.exit_time:
                d['exit_time'] = self.exit_time.isoformat()
            if self.metadata:
                d['metadata'] = json.dumps(self.metadata)
            return d
        except Exception as e:
            logger.error(f"Error in to_dict: {e}")
            raise


class TradeJournal:
    """
    Trade Journal
    
    Persistent storage of all trades with rich metadata.
    Enables performance analysis and trade review.
    """
    
    def __init__(self, db_path: str = "trade_journal.db"):
        """
        Initialize trade journal
        
        Args:
            db_path: Path to SQLite database
        """
        try:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
            self._init_database()
        
            logger.info(f"TradeJournal initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_database(self):
        """Initialize database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        trade_id TEXT PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        trade_type TEXT NOT NULL,
                        entry_time TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        quantity REAL NOT NULL,
                        stop_loss REAL,
                        take_profit REAL,
                        exit_time TEXT,
                        exit_price REAL,
                        pnl REAL,
                        pnl_percent REAL,
                        commission REAL DEFAULT 0,
                        slippage REAL DEFAULT 0,
                        status TEXT NOT NULL,
                        strategy TEXT,
                        signal_confidence REAL,
                        market_regime TEXT,
                        notes TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON trades(symbol)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_entry_time ON trades(entry_time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON trades(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy ON trades(strategy)")
            
                conn.commit()
        except Exception as e:
            logger.error(f"Error in _init_database: {e}")
            raise
    
    def log_trade_entry(
        self,
        trade_id: str,
        symbol: str,
        trade_type: TradeType,
        entry_price: float,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        strategy: Optional[str] = None,
        signal_confidence: Optional[float] = None,
        market_regime: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TradeEntry:
        """
        Log trade entry
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading symbol
            trade_type: LONG or SHORT
            entry_price: Entry price
            quantity: Position quantity
            stop_loss: Stop loss price
            take_profit: Take profit price
            strategy: Strategy name
            signal_confidence: Signal confidence score
            market_regime: Market regime at entry
            notes: Additional notes
            metadata: Additional metadata
            
        Returns:
            TradeEntry object
        """
        try:
            entry = TradeEntry(
                trade_id=trade_id,
                symbol=symbol,
                trade_type=trade_type,
                entry_time=datetime.now(),
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy=strategy,
                signal_confidence=signal_confidence,
                market_regime=market_regime,
                notes=notes,
                metadata=metadata or {}
            )
        
            with sqlite3.connect(self.db_path) as conn:
                data = entry.to_dict()
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
            
                conn.execute(
                    f"INSERT INTO trades ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                conn.commit()
        
            logger.info(
                f"Trade entry logged: {trade_id} {symbol} {trade_type.value} "
                f"{quantity} @ {entry_price}"
            )
        
            return entry
        except Exception as e:
            logger.error(f"Error in log_trade_entry: {e}")
            raise
    
    def log_trade_exit(
        self,
        trade_id: str,
        exit_price: float,
        commission: float = 0.0,
        slippage: float = 0.0,
        notes: Optional[str] = None
    ) -> Optional[TradeEntry]:
        """
        Log trade exit
        
        Args:
            trade_id: Trade identifier
            exit_price: Exit price
            commission: Total commission paid
            slippage: Slippage percentage
            notes: Exit notes
            
        Returns:
            Updated TradeEntry or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get trade
                cursor = conn.execute(
                    "SELECT * FROM trades WHERE trade_id = ?",
                    (trade_id,)
                )
                row = cursor.fetchone()
            
                if not row:
                    logger.warning(f"Trade {trade_id} not found")
                    return None
            
                # Calculate P&L
                entry_price = row[4]
                quantity = row[5]
                trade_type = row[2]
            
                if trade_type == TradeType.LONG.value:
                    pnl = (exit_price - entry_price) * quantity - commission
                else:
                    pnl = (entry_price - exit_price) * quantity - commission
            
                pnl_percent = (pnl / (entry_price * quantity)) * 100 if entry_price * quantity > 0 else 0
            
                # Update trade
                exit_time = datetime.now()
                conn.execute("""
                    UPDATE trades
                    SET exit_time = ?,
                        exit_price = ?,
                        pnl = ?,
                        pnl_percent = ?,
                        commission = ?,
                        slippage = ?,
                        status = ?,
                        notes = COALESCE(notes || ' | ', '') || ?
                    WHERE trade_id = ?
                """, (
                    exit_time.isoformat(),
                    exit_price,
                    pnl,
                    pnl_percent,
                    commission,
                    slippage,
                    TradeStatus.CLOSED.value,
                    notes or '',
                    trade_id
                ))
                conn.commit()
        
            logger.info(
                f"Trade exit logged: {trade_id} @ {exit_price} "
                f"P&L: ${pnl:.2f} ({pnl_percent:.2f}%)"
            )
        
            return self.get_trade(trade_id)
        except Exception as e:
            logger.error(f"Error in log_trade_exit: {e}")
            raise
    
    def get_trade(self, trade_id: str) -> Optional[TradeEntry]:
        """Get trade by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM trades WHERE trade_id = ?",
                    (trade_id,)
                )
                row = cursor.fetchone()
            
                if not row:
                    return None
            
                return self._row_to_entry(row)
        except Exception as e:
            logger.error(f"Error in get_trade: {e}")
            raise
    
    def get_open_trades(self) -> List[TradeEntry]:
        """Get all open trades"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM trades WHERE status = ? ORDER BY entry_time DESC",
                    (TradeStatus.OPEN.value,)
                )
                return [self._row_to_entry(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_open_trades: {e}")
            raise
    
    def get_trades_by_symbol(self, symbol: str, limit: int = 100) -> List[TradeEntry]:
        """Get trades for a symbol"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM trades WHERE symbol = ? ORDER BY entry_time DESC LIMIT ?",
                    (symbol, limit)
                )
                return [self._row_to_entry(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_trades_by_symbol: {e}")
            raise
    
    def get_trades_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[TradeEntry]:
        """Get trades within date range"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM trades WHERE entry_time BETWEEN ? AND ? ORDER BY entry_time",
                    (start_date.isoformat(), end_date.isoformat())
                )
                return [self._row_to_entry(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_trades_by_date_range: {e}")
            raise
    
    def get_performance_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get performance statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance statistics dictionary
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
        
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        MAX(pnl) as max_win,
                        MIN(pnl) as max_loss,
                        AVG(pnl_percent) as avg_pnl_percent,
                        SUM(commission) as total_commission,
                        AVG(slippage) as avg_slippage
                    FROM trades
                    WHERE status = ? AND entry_time >= ?
                """, (TradeStatus.CLOSED.value, cutoff.isoformat()))
            
                row = cursor.fetchone()
            
                total_trades = row[0] or 0
                winning_trades = row[1] or 0
                losing_trades = row[2] or 0
            
                stats = {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
                    'total_pnl': row[3] or 0,
                    'avg_pnl': row[4] or 0,
                    'max_win': row[5] or 0,
                    'max_loss': row[6] or 0,
                    'avg_pnl_percent': row[7] or 0,
                    'total_commission': row[8] or 0,
                    'avg_slippage': row[9] or 0,
                    'period_days': days
                }
            
                # Calculate profit factor
                if losing_trades > 0:
                    cursor = conn.execute("""
                        SELECT SUM(pnl) FROM trades
                        WHERE status = ? AND pnl > 0 AND entry_time >= ?
                    """, (TradeStatus.CLOSED.value, cutoff.isoformat()))
                    gross_profit = cursor.fetchone()[0] or 0
                
                    cursor = conn.execute("""
                        SELECT SUM(ABS(pnl)) FROM trades
                        WHERE status = ? AND pnl < 0 AND entry_time >= ?
                    """, (TradeStatus.CLOSED.value, cutoff.isoformat()))
                    gross_loss = cursor.fetchone()[0] or 0
                
                    stats['profit_factor'] = (gross_profit / gross_loss) if gross_loss > 0 else 0
                else:
                    stats['profit_factor'] = 0
        
            return stats
        except Exception as e:
            logger.error(f"Error in get_performance_stats: {e}")
            raise
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance by strategy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        strategy,
                        COUNT(*) as trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(pnl) as total_pnl,
                        AVG(pnl_percent) as avg_return
                    FROM trades
                    WHERE status = ? AND strategy IS NOT NULL
                    GROUP BY strategy
                """, (TradeStatus.CLOSED.value,))
            
                results = {}
                for row in cursor.fetchall():
                    strategy = row[0]
                    trades = row[1]
                    wins = row[2]
                
                    results[strategy] = {
                        'trades': trades,
                        'wins': wins,
                        'win_rate': (wins / trades * 100) if trades > 0 else 0,
                        'total_pnl': row[3] or 0,
                        'avg_return': row[4] or 0
                    }
            
                return results
        except Exception as e:
            logger.error(f"Error in get_strategy_performance: {e}")
            raise
    
    def _row_to_entry(self, row: sqlite3.Row) -> TradeEntry:
        """Convert database row to TradeEntry"""
        try:
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
            return TradeEntry(
                trade_id=row['trade_id'],
                symbol=row['symbol'],
                trade_type=TradeType(row['trade_type']),
                entry_time=datetime.fromisoformat(row['entry_time']),
                entry_price=row['entry_price'],
                quantity=row['quantity'],
                stop_loss=row['stop_loss'],
                take_profit=row['take_profit'],
                exit_time=datetime.fromisoformat(row['exit_time']) if row['exit_time'] else None,
                exit_price=row['exit_price'],
                pnl=row['pnl'],
                pnl_percent=row['pnl_percent'],
                commission=row['commission'],
                slippage=row['slippage'],
                status=TradeStatus(row['status']),
                strategy=row['strategy'],
                signal_confidence=row['signal_confidence'],
                market_regime=row['market_regime'],
                notes=row['notes'],
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error in _row_to_entry: {e}")
            raise
    
    def export_to_csv(self, output_path: str, days: int = 30):
        """Export trades to CSV"""
        try:
            import csv
        
            cutoff = datetime.now() - timedelta(days=days)
            trades = self.get_trades_by_date_range(cutoff, datetime.now())
        
            with open(output_path, 'w', newline='') as f:
                if not trades:
                    return
            
                writer = csv.DictWriter(f, fieldnames=trades[0].to_dict().keys())
                writer.writeheader()
            
                for trade in trades:
                    writer.writerow(trade.to_dict())
        
            logger.info(f"Exported {len(trades)} trades to {output_path}")
        except Exception as e:
            logger.error(f"Error in export_to_csv: {e}")
            raise


# Singleton instance
_trade_journal: Optional[TradeJournal] = None


def get_trade_journal(db_path: str = "trade_journal.db") -> TradeJournal:
    """Get or create trade journal singleton"""
    try:
        global _trade_journal
    
        if _trade_journal is None:
            _trade_journal = TradeJournal(db_path)
    
        return _trade_journal
    except Exception as e:
        logger.error(f"Error in get_trade_journal: {e}")
        raise
