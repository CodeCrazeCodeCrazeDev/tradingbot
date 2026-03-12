"""
Trade Journal and Audit Logging System

Provides comprehensive trade logging for compliance, analysis, and debugging.
All trades, decisions, and system events are logged with full context.
"""

import asyncio
import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import uuid

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events to log"""
    TRADE_SIGNAL = "trade_signal"
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_MODIFIED = "position_modified"
    RISK_CHECK_PASSED = "risk_check_passed"
    RISK_CHECK_FAILED = "risk_check_failed"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    SYSTEM_ERROR = "system_error"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"
    CONFIG_CHANGE = "config_change"
    MANUAL_INTERVENTION = "manual_intervention"
    MARKET_DATA_ERROR = "market_data_error"
    BROKER_DISCONNECT = "broker_disconnect"
    BROKER_RECONNECT = "broker_reconnect"


@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    symbol: Optional[str]
    details: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    checksum: str = ""
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate integrity checksum for the event"""
        data = f"{self.event_id}:{self.event_type.value}:{self.timestamp.isoformat()}:{self.symbol}:{json.dumps(self.details, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'details': self.details,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'checksum': self.checksum
        }


@dataclass
class TradeRecord:
    """Complete trade record for journal"""
    trade_id: str
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime = None
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    commission: float = 0.0
    slippage_bps: float = 0.0
    strategy: str = ""
    signal_source: str = ""
    signal_confidence: float = 0.0
    risk_reward_ratio: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.entry_time is None:
            self.entry_time = datetime.now()
        if not self.trade_id:
            self.trade_id = str(uuid.uuid4())
    
    def calculate_pnl(self):
        """Calculate P&L if exit price is set"""
        if self.exit_price is not None:
            if self.side == 'buy':
                self.pnl = (self.exit_price - self.entry_price) * self.quantity - self.commission
            else:
                self.pnl = (self.entry_price - self.exit_price) * self.quantity - self.commission
            
            if self.entry_price > 0:
                self.pnl_percent = self.pnl / (self.entry_price * self.quantity) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'trade_id': self.trade_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'commission': self.commission,
            'slippage_bps': self.slippage_bps,
            'strategy': self.strategy,
            'signal_source': self.signal_source,
            'signal_confidence': self.signal_confidence,
            'risk_reward_ratio': self.risk_reward_ratio,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'notes': self.notes,
            'tags': self.tags,
            'metadata': self.metadata
        }


class TradeJournal:
    """
    Comprehensive trade journal for logging all trading activity.
    
    Features:
    - SQLite database for persistent storage
    - JSON file backup
    - Integrity checksums
    - Query capabilities
    - Export to CSV/JSON
    - Performance analytics
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for trade journal"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize trade journal"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.config = config or {}
        
        # Database path
        self.db_path = Path(self.config.get('db_path', 'data/trade_journal.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # JSON backup path
        self.json_backup_path = Path(self.config.get('json_backup_path', 'data/trade_journal_backup.json'))
        
        # Session ID
        self.session_id = str(uuid.uuid4())[:8]
        
        # Initialize database
        self._init_database()
        
        # In-memory cache
        self._trade_cache: Dict[str, TradeRecord] = {}
        self._event_cache: List[AuditEvent] = []
        self._cache_max_size = self.config.get('cache_max_size', 1000)
        
        # Background flush
        self._flush_interval = self.config.get('flush_interval', 60)  # seconds
        self._last_flush = datetime.now()
        
        self._initialized = True
        logger.info(f"Trade journal initialized - Session: {self.session_id}")
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # Create tables
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    order_id TEXT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT,
                    pnl REAL DEFAULT 0,
                    pnl_percent REAL DEFAULT 0,
                    commission REAL DEFAULT 0,
                    slippage_bps REAL DEFAULT 0,
                    strategy TEXT,
                    signal_source TEXT,
                    signal_confidence REAL,
                    risk_reward_ratio REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    notes TEXT,
                    tags TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    symbol TEXT,
                    details TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    checksum TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
                CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);
                CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy);
                CREATE INDEX IF NOT EXISTS idx_events_type ON audit_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON audit_events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_session ON audit_events(session_id);
            """)
            
            self.conn.commit()
            logger.info(f"Trade journal database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize trade journal database: {e}")
            raise
    
    def log_trade(self, trade: TradeRecord) -> str:
        """
        Log a trade to the journal.
        
        Args:
            trade: TradeRecord to log
            
        Returns:
            Trade ID
        """
        try:
            # Calculate P&L if not set
            if trade.exit_price is not None and trade.pnl == 0:
                trade.calculate_pnl()
            
            # Add to cache
            self._trade_cache[trade.trade_id] = trade
            
            # Insert into database
            self.conn.execute("""
                INSERT OR REPLACE INTO trades (
                    trade_id, order_id, symbol, side, quantity, entry_price, exit_price,
                    entry_time, exit_time, pnl, pnl_percent, commission, slippage_bps,
                    strategy, signal_source, signal_confidence, risk_reward_ratio,
                    stop_loss, take_profit, notes, tags, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.trade_id, trade.order_id, trade.symbol, trade.side, trade.quantity,
                trade.entry_price, trade.exit_price,
                trade.entry_time.isoformat() if trade.entry_time else None,
                trade.exit_time.isoformat() if trade.exit_time else None,
                trade.pnl, trade.pnl_percent, trade.commission, trade.slippage_bps,
                trade.strategy, trade.signal_source, trade.signal_confidence,
                trade.risk_reward_ratio, trade.stop_loss, trade.take_profit,
                trade.notes, json.dumps(trade.tags), json.dumps(trade.metadata)
            ))
            
            self.conn.commit()
            
            logger.info(f"Trade logged: {trade.trade_id} - {trade.symbol} {trade.side} {trade.quantity}")
            
            # Also log as audit event
            self.log_event(
                EventType.POSITION_OPENED if trade.exit_price is None else EventType.POSITION_CLOSED,
                trade.symbol,
                trade.to_dict()
            )
            
            return trade.trade_id
            
        except Exception as e:
            logger.error(f"Failed to log trade: {e}")
            raise
    
    def update_trade(self, trade_id: str, **updates) -> bool:
        """
        Update an existing trade record.
        
        Args:
            trade_id: Trade ID to update
            **updates: Fields to update
            
        Returns:
            True if successful
        """
        try:
            # Build update query
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key in ['tags', 'metadata']:
                    value = json.dumps(value)
                elif key in ['entry_time', 'exit_time'] and isinstance(value, datetime):
                    value = value.isoformat()
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            if not set_clauses:
                return False
            
            values.append(trade_id)
            
            self.conn.execute(
                f"UPDATE trades SET {', '.join(set_clauses)} WHERE trade_id = ?",
                values
            )
            self.conn.commit()
            
            # Update cache
            if trade_id in self._trade_cache:
                for key, value in updates.items():
                    setattr(self._trade_cache[trade_id], key, value)
            
            logger.info(f"Trade updated: {trade_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update trade: {e}")
            return False
    
    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: Optional[datetime] = None,
        commission: float = 0.0,
        notes: str = ""
    ) -> Optional[TradeRecord]:
        """
        Close an open trade.
        
        Args:
            trade_id: Trade ID to close
            exit_price: Exit price
            exit_time: Exit time (defaults to now)
            commission: Additional commission
            notes: Closing notes
            
        Returns:
            Updated TradeRecord or None
        """
        try:
            # Get existing trade
            trade = self.get_trade(trade_id)
            if not trade:
                logger.warning(f"Trade not found: {trade_id}")
                return None
            
            # Update trade
            trade.exit_price = exit_price
            trade.exit_time = exit_time or datetime.now()
            trade.commission += commission
            if notes:
                trade.notes = f"{trade.notes}\n{notes}" if trade.notes else notes
            
            # Calculate P&L
            trade.calculate_pnl()
            
            # Save
            self.log_trade(trade)
            
            logger.info(f"Trade closed: {trade_id} - P&L: {trade.pnl:.2f} ({trade.pnl_percent:.2f}%)")
            
            return trade
            
        except Exception as e:
            logger.error(f"Failed to close trade: {e}")
            return None
    
    def log_event(
        self,
        event_type: EventType,
        symbol: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            symbol: Related symbol (optional)
            details: Event details
            user_id: User ID (optional)
            
        Returns:
            Event ID
        """
        try:
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                timestamp=datetime.now(),
                symbol=symbol,
                details=details or {},
                user_id=user_id,
                session_id=self.session_id
            )
            
            # Add to cache
            self._event_cache.append(event)
            if len(self._event_cache) > self._cache_max_size:
                self._event_cache = self._event_cache[-self._cache_max_size:]
            
            # Insert into database
            self.conn.execute("""
                INSERT INTO audit_events (
                    event_id, event_type, timestamp, symbol, details,
                    user_id, session_id, checksum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.event_type.value, event.timestamp.isoformat(),
                event.symbol, json.dumps(event.details), event.user_id,
                event.session_id, event.checksum
            ))
            
            self.conn.commit()
            
            logger.debug(f"Event logged: {event.event_type.value} - {event.symbol or 'N/A'}")
            
            return event.event_id
            
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            raise
    
    def get_trade(self, trade_id: str) -> Optional[TradeRecord]:
        """Get a trade by ID"""
        # Check cache first
        if trade_id in self._trade_cache:
            return self._trade_cache[trade_id]
        
        # Query database
        cursor = self.conn.execute(
            "SELECT * FROM trades WHERE trade_id = ?",
            (trade_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return self._row_to_trade(row)
        return None
    
    def get_trades(
        self,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        side: Optional[str] = None,
        limit: int = 100
    ) -> List[TradeRecord]:
        """
        Query trades with filters.
        
        Args:
            symbol: Filter by symbol
            strategy: Filter by strategy
            start_date: Start date filter
            end_date: End date filter
            side: Filter by side ('buy' or 'sell')
            limit: Maximum results
            
        Returns:
            List of TradeRecords
        """
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)
        
        if start_date:
            query += " AND entry_time >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND entry_time <= ?"
            params.append(end_date.isoformat())
        
        if side:
            query += " AND side = ?"
            params.append(side)
        
        query += " ORDER BY entry_time DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.execute(query, params)
        
        return [self._row_to_trade(row) for row in cursor.fetchall()]
    
    def get_events(
        self,
        event_type: Optional[EventType] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Query audit events with filters"""
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.execute(query, params)
        
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def get_performance_stats(
        self,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        trades = self.get_trades(
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'max_win': 0.0,
                'max_loss': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'sharpe_ratio': 0.0
            }
        
        # Filter closed trades
        closed_trades = [t for t in trades if t.exit_price is not None]
        
        if not closed_trades:
            return {
                'total_trades': len(trades),
                'open_trades': len(trades),
                'closed_trades': 0,
                'total_pnl': 0.0
            }
        
        # Calculate stats
        pnls = [t.pnl for t in closed_trades]
        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p < 0]
        
        total_wins = sum(winning) if winning else 0
        total_losses = abs(sum(losing)) if losing else 0
        
        return {
            'total_trades': len(trades),
            'closed_trades': len(closed_trades),
            'open_trades': len(trades) - len(closed_trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': len(winning) / len(closed_trades) * 100 if closed_trades else 0,
            'total_pnl': sum(pnls),
            'avg_pnl': sum(pnls) / len(pnls) if pnls else 0,
            'max_win': max(pnls) if pnls else 0,
            'max_loss': min(pnls) if pnls else 0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else float('inf'),
            'avg_win': sum(winning) / len(winning) if winning else 0,
            'avg_loss': sum(losing) / len(losing) if losing else 0,
            'total_commission': sum(t.commission for t in closed_trades),
            'avg_slippage_bps': sum(t.slippage_bps for t in closed_trades) / len(closed_trades) if closed_trades else 0
        }
    
    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """Export all data to JSON file"""
        filepath = filepath or str(self.json_backup_path)
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'session_id': self.session_id,
            'trades': [t.to_dict() for t in self.get_trades(limit=100000)],
            'events': [e.to_dict() for e in self.get_events(limit=100000)]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Trade journal exported to: {filepath}")
        return filepath
    
    def export_to_csv(self, filepath: str) -> str:
        """Export trades to CSV file"""
        import csv
        
        trades = self.get_trades(limit=100000)
        
        if not trades:
            logger.warning("No trades to export")
            return filepath
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=trades[0].to_dict().keys())
            writer.writeheader()
            for trade in trades:
                writer.writerow(trade.to_dict())
        
        logger.info(f"Trades exported to CSV: {filepath}")
        return filepath
    
    def _row_to_trade(self, row: sqlite3.Row) -> TradeRecord:
        """Convert database row to TradeRecord"""
        return TradeRecord(
            trade_id=row['trade_id'],
            order_id=row['order_id'],
            symbol=row['symbol'],
            side=row['side'],
            quantity=row['quantity'],
            entry_price=row['entry_price'],
            exit_price=row['exit_price'],
            entry_time=datetime.fromisoformat(row['entry_time']) if row['entry_time'] else None,
            exit_time=datetime.fromisoformat(row['exit_time']) if row['exit_time'] else None,
            pnl=row['pnl'] or 0,
            pnl_percent=row['pnl_percent'] or 0,
            commission=row['commission'] or 0,
            slippage_bps=row['slippage_bps'] or 0,
            strategy=row['strategy'] or '',
            signal_source=row['signal_source'] or '',
            signal_confidence=row['signal_confidence'] or 0,
            risk_reward_ratio=row['risk_reward_ratio'] or 0,
            stop_loss=row['stop_loss'],
            take_profit=row['take_profit'],
            notes=row['notes'] or '',
            tags=json.loads(row['tags']) if row['tags'] else [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def _row_to_event(self, row: sqlite3.Row) -> AuditEvent:
        """Convert database row to AuditEvent"""
        return AuditEvent(
            event_id=row['event_id'],
            event_type=EventType(row['event_type']),
            timestamp=datetime.fromisoformat(row['timestamp']),
            symbol=row['symbol'],
            details=json.loads(row['details']) if row['details'] else {},
            user_id=row['user_id'],
            session_id=row['session_id'],
            checksum=row['checksum']
        )
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logger.info("Trade journal closed")


# Singleton accessor
def get_trade_journal(config: Optional[Dict[str, Any]] = None) -> TradeJournal:
    """Get the singleton trade journal instance"""
    return TradeJournal(config)


# Convenience functions
def log_trade_signal(
    symbol: str,
    direction: str,
    confidence: float,
    source: str,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Log a trade signal event"""
    journal = get_trade_journal()
    return journal.log_event(
        EventType.TRADE_SIGNAL,
        symbol,
        {
            'direction': direction,
            'confidence': confidence,
            'source': source,
            **(details or {})
        }
    )


def log_order_placed(
    order_id: str,
    symbol: str,
    side: str,
    quantity: float,
    price: Optional[float] = None,
    order_type: str = 'market',
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Log an order placed event"""
    journal = get_trade_journal()
    return journal.log_event(
        EventType.ORDER_PLACED,
        symbol,
        {
            'order_id': order_id,
            'side': side,
            'quantity': quantity,
            'price': price,
            'order_type': order_type,
            **(details or {})
        }
    )


def log_system_event(
    event_type: EventType,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Log a system event"""
    journal = get_trade_journal()
    return journal.log_event(event_type, None, details)
